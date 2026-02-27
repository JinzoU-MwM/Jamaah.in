"""
Documents Router — /process-documents/ endpoint and /progress/ SSE.
Handles file upload validation and delegates to DocumentProcessor.
"""
import uuid
import time
import logging
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, UploadFile, HTTPException, Request, Depends
from sqlalchemy.orm import Session
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
)
from app.services.progress import update_progress, create_progress_stream
from app.services.cache import ocr_cache
from app.config import ALLOWED_EXTENSIONS
from app.database import get_db
from app.auth import get_current_user, check_access, record_usage
from app.models.user import User

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["Documents"])


@router.get("/progress/{session_id}")
async def progress_stream(session_id: str):
    """SSE endpoint for real-time progress updates."""
    return await create_progress_stream(session_id)


@router.post("/process-documents/", response_model=ProcessingPreviewResponse)
@limiter.limit("10/minute")
async def process_documents(
    request: Request,
    files: List[UploadFile] = File(..., description="Identity document images"),
    session_id: str = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Process documents and return extracted data as JSON for preview.
    
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
                error=f"Invalid file type: {file_ext}"
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
                error=f"File too large: {size_mb:.1f}MB (max {MAX_FILE_SIZE_MB}MB)"
            ))
            continue

        file_data.append((file.filename, file_ext, content))

    # 2. PROCESS FILES (OCR + caching + batching)
    proc_results, extracted_data, file_results = await process_files(file_data, session_id)
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
            session_id=session_id
        )

    except HTTPException:
        raise
    except Exception as post_exc:
        update_progress(session_id, done=True, status="error")
        logger.error(f"Post-processing error: {post_exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Post-processing failed: {str(post_exc)}")
