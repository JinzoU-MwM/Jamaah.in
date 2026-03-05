"""
Documents Router — /process-documents/ endpoint and /progress/ SSE.
Handles file upload validation and delegates to DocumentProcessor.
"""
import uuid
import time
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, UploadFile, HTTPException, Request, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas import (
    ProcessingPreviewResponse,
    ExtractedDataItem,
    FileResult,
)
from app.services.document_processor import (
    process_files,
    run_pipeline,
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
    MAX_FILES_PER_REQUEST,
    OCR_ENGINE,
    OCR_FALLBACK_ENABLED,
    CACHE_MODE_VALUES,
)
from app.services.gemini_ocr import (
    EXTRACT_PROMPT_VERSION,
    EXTRACT_TEXT_PROMPT_VERSION,
    GEMINI_API_KEY,
    GEMINI_CACHE_TTL_SECONDS,
    GEMINI_MODEL,
    GEMINI_TEXT_CACHE_TTL_SECONDS,
)
from app.services.progress import update_progress, create_progress_stream
from app.services.cache import ocr_cache
from app.services.ai_result_cache_repo import get_ai_cache_stats
from app.services import ocr_engine
from app.config import ALLOWED_EXTENSIONS
from app.database import get_db
from app.auth import get_current_user, check_access, record_usage
from app.models.user import User
from app.models.ocr_review import OcrProcessingLog, OcrReviewItem
from app.services.audit import record_audit_event

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["Documents"])
BYPASS_CACHE_MARKER = '"cache_mode": "bypass"'
try:
    OCR_BYPASS_MAX_FILES_PER_HOUR = int(os.getenv("OCR_BYPASS_MAX_FILES_PER_HOUR", "60"))
except ValueError:
    OCR_BYPASS_MAX_FILES_PER_HOUR = 60


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _count_recent_bypass_files(db: Session, user_id: int, window_hours: int = 1) -> int:
    since = utc_now() - timedelta(hours=max(1, window_hours))
    return (
        db.query(func.count(OcrProcessingLog.id))
        .filter(
            OcrProcessingLog.user_id == user_id,
            OcrProcessingLog.created_at >= since,
            OcrProcessingLog.provenance_json.contains(BYPASS_CACHE_MARKER),
        )
        .scalar()
        or 0
    )


class OcrReviewDecisionRequest(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    notes: str = ""


@router.get("/progress/{session_id}")
async def progress_stream(session_id: str):
    """SSE endpoint for real-time progress updates."""
    return await create_progress_stream(session_id)


@router.get("/ocr/status")
async def get_ocr_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return OCR engine runtime status and provider readiness.
    Useful for diagnosing provider config before running document scans.
    """
    try:
        ai_cache_stats = get_ai_cache_stats(db)
    except Exception:
        ai_cache_stats = {"total": -1, "active": -1, "expired": -1}

    return {
        "primary_engine": OCR_ENGINE,
        "fallback_enabled": OCR_FALLBACK_ENABLED,
        "providers": {
            "gemini": {
                "configured": bool(GEMINI_API_KEY),
                "model": GEMINI_MODEL,
                "prompt_version": EXTRACT_PROMPT_VERSION,
                "text_prompt_version": EXTRACT_TEXT_PROMPT_VERSION,
                "cache_ttl_seconds": GEMINI_CACHE_TTL_SECONDS,
                "text_cache_ttl_seconds": GEMINI_TEXT_CACHE_TTL_SECONDS,
                "bypass_max_files_per_hour": OCR_BYPASS_MAX_FILES_PER_HOUR,
            },
            "tesseract": {
                "available": bool(ocr_engine.TESSERACT_AVAILABLE),
            },
        },
        "cache": ocr_cache.stats,
        "ai_cache": ai_cache_stats,
        "requested_by": user.email,
    }


@router.get("/ocr/review-queue")
async def get_ocr_review_queue(
    status: str = "pending",
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return OCR manual review queue items for current user."""
    query = db.query(OcrReviewItem).filter(OcrReviewItem.user_id == user.id)
    if status != "all":
        query = query.filter(OcrReviewItem.status == status)
    items = (
        query.order_by(OcrReviewItem.created_at.desc())
        .offset(max(0, offset))
        .limit(min(max(1, limit), 200))
        .all()
    )
    return {
        "items": [
            {
                "id": item.id,
                "session_id": item.session_id,
                "filename": item.filename,
                "status": item.status,
                "reason": item.reason,
                "document_type": item.document_type,
                "error_category": item.error_category,
                "confidence_score": item.confidence_score,
                "notes": item.notes,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
                "reviewed_by": item.reviewed_by,
            }
            for item in items
        ],
        "count": len(items),
        "status_filter": status,
    }


@router.patch("/ocr/review-queue/{item_id}")
async def review_ocr_item(
    item_id: int,
    body: OcrReviewDecisionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Approve/reject an OCR manual review queue item."""
    item = db.query(OcrReviewItem).filter(
        OcrReviewItem.id == item_id,
        OcrReviewItem.user_id == user.id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")

    item.status = "approved" if body.action == "approve" else "rejected"
    item.notes = (body.notes or "").strip()
    item.reviewed_at = utc_now()
    item.reviewed_by = user.id
    record_audit_event(
        db,
        user_id=user.id,
        action="ocr_review_decision",
        resource_type="ocr_review_item",
        resource_id=item.id,
        details={
            "decision": item.status,
            "session_id": item.session_id,
            "filename": item.filename,
        },
    )
    db.commit()
    db.refresh(item)
    return {
        "id": item.id,
        "status": item.status,
        "notes": item.notes,
        "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
    }


@router.get("/ocr/dashboard")
async def get_ocr_dashboard(
    days: int = 7,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return OCR quality/performance metrics for dashboard cards/charts."""
    window_days = min(max(1, days), 90)
    since = utc_now() - timedelta(days=window_days)

    base = db.query(OcrProcessingLog).filter(
        OcrProcessingLog.user_id == user.id,
        OcrProcessingLog.created_at >= since,
    )
    total = base.count()
    success_count = base.filter(OcrProcessingLog.status == "success").count()
    failed_count = base.filter(OcrProcessingLog.status == "failed").count()
    partial_count = base.filter(OcrProcessingLog.status == "partial").count()

    avg_processing_ms = base.with_entities(func.avg(OcrProcessingLog.processing_ms)).scalar() or 0.0
    cached_count = base.filter(OcrProcessingLog.cached.is_(True)).count()

    error_rows = (
        base.with_entities(OcrProcessingLog.error_category, func.count(OcrProcessingLog.id))
        .filter(OcrProcessingLog.error_category != "")
        .group_by(OcrProcessingLog.error_category)
        .all()
    )
    pending_review = db.query(OcrReviewItem).filter(
        OcrReviewItem.user_id == user.id,
        OcrReviewItem.status == "pending",
    ).count()

    return {
        "window_days": window_days,
        "total_files": total,
        "success_count": success_count,
        "failed_count": failed_count,
        "partial_count": partial_count,
        "success_rate": (success_count / total) if total else 0.0,
        "cache_hit_rate": (cached_count / total) if total else 0.0,
        "avg_processing_ms": round(float(avg_processing_ms), 2),
        "pending_review_count": pending_review,
        "error_categories": [
            {"category": category, "count": count}
            for category, count in error_rows
        ],
    }


@router.post("/process-documents/", response_model=ProcessingPreviewResponse)
@limiter.limit("10/minute")
async def process_documents(
    request: Request,
    files: List[UploadFile] = File(..., description="Identity document images (KTP/KK, Passport, Visa)"),
    session_id: str = None,
    cache_mode: str = Query(
        "default",
        description="AI cache mode: default (read/write), refresh (skip read, write), bypass (skip read/write).",
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Process KTP/KK, Passport, and Visa documents and return extracted data as JSON for preview.
    
    Pipeline: Upload → Cache Check → OCR → Sanitize → Fuzzy Merge → Validate
    Rate limited to 10 requests/minute. Max 10MB per file, 50 files per request.
    Requires authentication. Free users limited to 50 total scans.
    """
    # --- ACCESS CHECK ---
    access = check_access(db, user)
    if not access["allowed"]:
        raise HTTPException(status_code=403, detail=access["message"])

    start_time = time.time()
    logger.info(f"User {user.email} uploading {len(files)} files")

    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    if len(files) > MAX_FILES_PER_REQUEST:
        raise HTTPException(
            status_code=400,
            detail=f"Maksimum {MAX_FILES_PER_REQUEST} file per upload. Anda mengirim {len(files)} file.",
        )
    cache_mode = (cache_mode or "default").strip().lower()
    if cache_mode not in CACHE_MODE_VALUES:
        allowed = ", ".join(sorted(CACHE_MODE_VALUES))
        raise HTTPException(
            status_code=400,
            detail=f"Invalid cache_mode '{cache_mode}'. Allowed values: {allowed}.",
        )
    if cache_mode == "bypass" and access.get("plan") != "pro":
        raise HTTPException(
            status_code=403,
            detail="cache_mode 'bypass' requires active Pro subscription.",
        )

    # Session ID for progress tracking (use client-provided or generate)
    if not session_id:
        session_id = str(uuid.uuid4())[:8]

    # 1. READ & VALIDATE ALL FILES (async I/O, fast)
    from app.schemas import ProcessingResult
    results = []
    file_results_early = []
    file_data = []

    for file in files:
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            results.append(ProcessingResult(
                filename=file.filename, success=False,
                error=f"Invalid file type: {file_ext}"
            ))
            file_results_early.append(FileResult(
                filename=file.filename, status="failed",
                error=f"Invalid file type: {file_ext}",
                error_category="invalid_file_type",
            ))
            continue

        content = await file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            size_mb = len(content) / (1024 * 1024)
            results.append(ProcessingResult(
                filename=file.filename, success=False,
                error=f"File too large: {size_mb:.1f}MB (max {MAX_FILE_SIZE_MB}MB)"
            ))
            file_results_early.append(FileResult(
                filename=file.filename, status="failed",
                error=f"File too large: {size_mb:.1f}MB (max {MAX_FILE_SIZE_MB}MB)",
                error_category="file_too_large",
            ))
            continue

        file_data.append((file.filename, file_ext, content))

    if cache_mode == "bypass" and OCR_BYPASS_MAX_FILES_PER_HOUR > 0:
        recent_bypass_files = _count_recent_bypass_files(db, user.id)
        projected_total = recent_bypass_files + len(file_data)
        if projected_total > OCR_BYPASS_MAX_FILES_PER_HOUR:
            remaining = max(OCR_BYPASS_MAX_FILES_PER_HOUR - recent_bypass_files, 0)
            raise HTTPException(
                status_code=429,
                detail=(
                    "Bypass cache hourly limit exceeded. "
                    f"Limit={OCR_BYPASS_MAX_FILES_PER_HOUR} files/hour, "
                    f"recent={recent_bypass_files}, remaining={remaining}."
                ),
            )

    # 2. PROCESS FILES (OCR + caching + batching)
    proc_results, extracted_data, file_results = await process_files(
        file_data,
        session_id,
        cache_mode=cache_mode,
    )
    results.extend(proc_results)
    file_results = file_results_early + file_results

    elapsed = time.time() - start_time
    logger.info(f"Processing {len(files)} files took {elapsed:.1f}s")

    # 3. POST-PROCESSING PIPELINE
    try:
        successful = sum(1 for r in results if r.success)
        failed_count = len(results) - successful

        if not extracted_data:
            update_progress(session_id, done=True, status="error")
            error_messages = [r.error for r in results if r.error]
            error_detail = f"No documents could be processed successfully. {'; '.join(error_messages)}"
            raise HTTPException(status_code=400, detail=error_detail)

        final_data, all_warnings = run_pipeline(extracted_data, session_id)

        update_progress(session_id, done=True, status="complete")

        # Persist per-file telemetry and create manual review queue items for problematic files.
        for fr in file_results:
            db.add(OcrProcessingLog(
                user_id=user.id,
                session_id=session_id,
                filename=fr.filename,
                status=fr.status,
                document_type=fr.document_type or "",
                error_category=fr.error_category or "",
                processing_ms=float(fr.processing_ms or 0.0),
                cached=bool(fr.cached),
                provenance_json=fr.provenance_json or "",
            ))
            if fr.status in {"failed", "partial"}:
                reason = fr.error or "Perlu review manual karena hasil OCR belum stabil"
                db.add(OcrReviewItem(
                    user_id=user.id,
                    session_id=session_id,
                    filename=fr.filename,
                    status="pending",
                    reason=reason,
                    document_type=fr.document_type or "",
                    error_category=fr.error_category or "",
                ))
        db.commit()

        # Record usage (counts towards free tier limit)
        record_usage(db, user.id, count=successful)

        return ProcessingPreviewResponse(
            status="success",
            message=f"Processed {successful} documents, consolidated to {len(final_data)} unique records",
            total_files=len(files),
            successful=successful,
            failed=failed_count,
            data=final_data,
            validation_warnings=all_warnings,
            file_results=file_results,
            cache_stats=ocr_cache.stats,
            session_id=session_id,
            cache_mode=cache_mode,
        )

    except HTTPException:
        raise
    except Exception as post_exc:
        update_progress(session_id, done=True, status="error")
        logger.error(f"Post-processing error: {post_exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Post-processing failed: {str(post_exc)}")
