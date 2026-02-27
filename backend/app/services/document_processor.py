"""
Document Processor — Orchestrates OCR, caching, batching, and the data pipeline.

This is the core business logic for processing identity documents (KTP, Passport, Visa).
Pipeline: Upload → Cache Check → OCR → Parse → Sanitize → Fuzzy Merge → Validate
"""
import io
import os
import re
import asyncio
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

from app.schemas import ExtractedDataItem, ProcessingResult, FileResult, ValidationWarning
from app.services import ocr_engine, cleaner
from app.services.gemini_ocr import extract_document_data as gemini_extract_data
from app.services.cache import ocr_cache
from app.services.validators import validate_row
from app.services.progress import update_progress
from app.mappers import doc_data_to_item
from app.config import ALLOWED_EXTENSIONS

logger = logging.getLogger(__name__)

# ---- OCR Engine Config ----
OCR_ENGINE = os.getenv("OCR_PRIMARY_ENGINE", "gemini").lower().strip()
OCR_FALLBACK_ENABLED = os.getenv("OCR_FALLBACK_ENABLED", "true").lower() == "true"

logger.info(f"OCR Engine: primary={OCR_ENGINE}, fallback_enabled={OCR_FALLBACK_ENABLED}")

# ---- Processing Config ----
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_FILES_PER_REQUEST = 50
BATCH_SIZE = 20
GEMINI_CONCURRENCY = 10
MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 1.0

# Thread pool for I/O-bound API/OCR calls
_executor = ThreadPoolExecutor(max_workers=15)

# Semaphore to rate-limit concurrent Gemini API calls (initialized lazily)
_gemini_semaphore: asyncio.Semaphore = None


def _parse_text_to_structured(raw_text: str) -> dict:
    """
    Parse raw OCR text (from Tesseract) into structured document fields using regex.
    This is a best-effort parser for KTP, Passport, and Visa documents.
    """
    text = raw_text.upper()
    data = {
        "document_type": "UNKNOWN",
        "nama": "",
        "no_identitas": "",
        "tempat_lahir": "",
        "tanggal_lahir": "",
        "jenis_kelamin": "",
        "alamat": "",
        "rt_rw": "",
        "kelurahan": "",
        "kecamatan": "",
        "kabupaten": "",
        "provinsi": "",
        "agama": "",
        "status_pernikahan": "",
        "pekerjaan": "",
        "pendidikan": "",
        "kewarganegaraan": "",
        "no_paspor": "",
        "tanggal_paspor": "",
        "kota_paspor": "",
        "no_visa": "",
        "tanggal_visa": "",
        "tanggal_visa_akhir": "",
        "provider_visa": "",
        "nama_ayah": "",
        "no_telepon": "",
        "no_hp": "",
    }

    # Detect document type
    if "NIK" in text or "KARTU TANDA PENDUDUK" in text or "KTP" in text:
        data["document_type"] = "KTP"
    elif "PASSPORT" in text or "PASPOR" in text or "REPUBLIC OF INDONESIA" in text:
        data["document_type"] = "PASPOR"
    elif "VISA" in text:
        data["document_type"] = "VISA"

    lines = raw_text.strip().split("\n")

    def find_value(patterns, text_block=raw_text):
        """Find first matching pattern and return the captured group."""
        for pat in patterns:
            m = re.search(pat, text_block, re.IGNORECASE | re.MULTILINE)
            if m:
                return m.group(1).strip()
        return ""

    # NIK / No Identitas
    data["no_identitas"] = find_value([
        r'NIK\s*[:\-]?\s*(\d{10,16})',
        r'(\d{16})',  # Fallback: any 16-digit number
    ])

    # Nama
    data["nama"] = find_value([
        r'NAM[AE]\s*[:\-]?\s*(.+?)(?:\n|$)',
        r'SURNAME\s*[/\\]?\s*(?:GIVEN\s*NAME[S]?)?\s*[:\-]?\s*(.+?)(?:\n|$)',
    ])

    # Tempat/Tanggal Lahir
    ttl = find_value([
        r'TEMPAT\s*/?\s*T(?:GL|ANGGAL)\s*LAHIR\s*[:\-]?\s*(.+?)(?:\n|$)',
        r'(?:PLACE|DATE)\s*(?:OF)?\s*BIRTH\s*[:\-]?\s*(.+?)(?:\n|$)',
    ])
    if ttl:
        parts = re.split(r'[,/]', ttl, maxsplit=1)
        data["tempat_lahir"] = parts[0].strip()
        if len(parts) > 1:
            data["tanggal_lahir"] = parts[1].strip()

    # Date patterns
    if not data["tanggal_lahir"]:
        data["tanggal_lahir"] = find_value([
            r'(?:TGL|TANGGAL)\s*LAHIR\s*[:\-]?\s*(\d{2}[\-/\.]\d{2}[\-/\.]\d{4})',
            r'DATE\s*OF\s*BIRTH\s*[:\-]?\s*(\d{2}[\-/\.]\d{2}[\-/\.]\d{4})',
        ])

    # Jenis Kelamin
    jk = find_value([
        r'JENIS\s*KELAMIN\s*[:\-]?\s*(.+?)(?:\n|$)',
        r'SEX\s*[:\-]?\s*([MF])',
    ])
    if jk:
        jk_upper = jk.upper().strip()
        if "LAKI" in jk_upper or jk_upper == "M":
            data["jenis_kelamin"] = "LAKI-LAKI"
        elif "PEREM" in jk_upper or jk_upper == "F":
            data["jenis_kelamin"] = "PEREMPUAN"

    # Alamat
    data["alamat"] = find_value([r'ALAMAT\s*[:\-]?\s*(.+?)(?:\n|$)'])
    data["rt_rw"] = find_value([r'RT\s*/?\s*RW\s*[:\-]?\s*(.+?)(?:\n|$)'])
    data["kelurahan"] = find_value([r'KEL(?:URAHAN)?(?:\s*/\s*DESA)?\s*[:\-]?\s*(.+?)(?:\n|$)'])
    data["kecamatan"] = find_value([r'KEC(?:AMATAN)?\s*[:\-]?\s*(.+?)(?:\n|$)'])

    # Agama
    data["agama"] = find_value([r'AGAMA\s*[:\-]?\s*(.+?)(?:\n|$)'])

    # Status Pernikahan
    data["status_pernikahan"] = find_value([r'STATUS\s*(?:PERKAWINAN|PERNIKAHAN)?\s*[:\-]?\s*(.+?)(?:\n|$)'])

    # Pekerjaan
    data["pekerjaan"] = find_value([r'PEKERJAAN\s*[:\-]?\s*(.+?)(?:\n|$)'])

    # Passport number
    data["no_paspor"] = find_value([
        r'(?:NO\.?\s*)?PAS(?:S)?POR(?:T)?\s*[:\-]?\s*([A-Z0-9]{6,9})',
        r'PASSPORT\s*(?:NO\.?)?\s*[:\-]?\s*([A-Z0-9]{6,9})',
    ])

    # Visa number
    data["no_visa"] = find_value([
        r'VISA\s*(?:NO\.?)?\s*[:\-]?\s*([A-Z0-9]{6,12})',
    ])

    # Clean up — remove empty whitespace-only values
    for key in data:
        if isinstance(data[key], str):
            data[key] = data[key].strip()

    return data


def _process_with_gemini(img_bytes: bytes, filename: str) -> dict:
    """Process using Gemini AI (direct image → structured JSON)."""
    return gemini_extract_data(img_bytes, filename)


def _process_with_tesseract(img_bytes: bytes, filename: str) -> dict:
    """Process using Tesseract OCR + regex parsing."""
    if not ocr_engine.TESSERACT_AVAILABLE:
        raise RuntimeError("Tesseract is not installed. Install pytesseract and Tesseract-OCR.")
    raw_text = ocr_engine.extract_text_from_image(img_bytes, filename)
    if not raw_text or len(raw_text.strip()) < 10:
        raise RuntimeError(f"Tesseract extracted no usable text from {filename}")
    return _parse_text_to_structured(raw_text)


def _process_with_hybrid(img_bytes: bytes, filename: str) -> dict:
    """Process using Tesseract for text extraction + Gemini for structured parsing.
    Uses fewer Gemini API tokens since it sends text instead of images.
    """
    if not ocr_engine.TESSERACT_AVAILABLE:
        raise RuntimeError("Tesseract is not installed for hybrid mode.")
    raw_text = ocr_engine.extract_text_from_image(img_bytes, filename)
    if not raw_text or len(raw_text.strip()) < 10:
        raise RuntimeError(f"Tesseract extracted no usable text from {filename}")
    # Send text to Gemini for structured parsing (cheaper than sending images)
    return gemini_extract_data(raw_text, filename)


def _process_single_image(img_bytes: bytes, filename: str) -> dict:
    """Process a single image through OCR with engine selection and retry/fallback."""
    # Select primary engine
    engines = {
        "gemini": _process_with_gemini,
        "tesseract": _process_with_tesseract,
        "hybrid": _process_with_hybrid,
    }
    primary_fn = engines.get(OCR_ENGINE, _process_with_gemini)
    last_error = None

    # Try primary engine with retries
    for attempt in range(1, MAX_RETRIES + 2):
        try:
            result = primary_fn(img_bytes, filename)
            if attempt > 1:
                logger.info(f"Retry succeeded for {filename} on attempt {attempt}")
            logger.info(
                f"OCR [{OCR_ENGINE}] result for {filename}: type={result.get('document_type', '?')}, "
                f"nama='{result.get('nama', '')}'"
            )
            return result
        except Exception as e:
            last_error = e
            if attempt <= MAX_RETRIES:
                delay = RETRY_DELAY_SECONDS * attempt
                logger.warning(f"OCR [{OCR_ENGINE}] attempt {attempt} failed for {filename}: {e}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"All {attempt} OCR [{OCR_ENGINE}] attempts failed for {filename}: {e}")

    # Fallback to Gemini if primary wasn't Gemini and fallback is enabled
    if OCR_FALLBACK_ENABLED and OCR_ENGINE != "gemini":
        logger.info(f"Falling back to Gemini for {filename} after {OCR_ENGINE} failed")
        try:
            result = _process_with_gemini(img_bytes, filename)
            logger.info(f"OCR [gemini-fallback] result for {filename}: type={result.get('document_type', '?')}")
            return result
        except Exception as e:
            logger.error(f"Gemini fallback also failed for {filename}: {e}")
            last_error = e

    # Return empty result with error info instead of crashing
    return {
        'document_type': 'UNKNOWN',
        'nama': None,
        'no_identitas': None,
        '_error': str(last_error),
        '_partial': True,
    }


def _has_useful_data(doc_data: dict) -> bool:
    """Check if OCR result contains meaningful data worth keeping."""
    return bool(
        doc_data.get('nama')
        or doc_data.get('no_identitas')
        or doc_data.get('no_paspor')
        or doc_data.get('no_visa')
    )


async def process_files(
    file_data: List[Tuple[str, str, bytes]],
    session_id: str,
) -> Tuple[List[ProcessingResult], List[ExtractedDataItem], List[FileResult]]:
    """
    Process a batch of files through OCR with caching and progress tracking.

    Args:
        file_data: List of (filename, file_ext, content_bytes)
        session_id: Session ID for progress tracking

    Returns:
        Tuple of (results, extracted_data, file_results)
    """
    loop = asyncio.get_event_loop()

    # Lazy-init the Gemini semaphore (needs a running event loop)
    global _gemini_semaphore
    if _gemini_semaphore is None:
        _gemini_semaphore = asyncio.Semaphore(GEMINI_CONCURRENCY)

    async def _rate_limited_ocr(img_bytes: bytes, filename: str) -> dict:
        """Run OCR with semaphore to limit concurrent Gemini API calls."""
        async with _gemini_semaphore:
            return await loop.run_in_executor(
                _executor, _process_single_image, img_bytes, filename
            )

    async def _process_one(filename: str, file_ext: str, content: bytes):
        """Process a single file (PDF or image) with cache check."""
        file_hash = ocr_cache.compute_hash(content)
        cached_result = ocr_cache.get(file_hash)
        was_cached = cached_result is not None

        try:
            if file_ext == '.pdf':
                if cached_result:
                    items = cached_result
                else:
                    pdf_images = ocr_engine.convert_pdf_to_images(content)
                    logger.info(f"PDF '{filename}': converted to {len(pdf_images)} page(s)")
                    items = []
                    page_tasks = []
                    for page_num, pil_image in enumerate(pdf_images, start=1):
                        page_name = f"{filename}_page{page_num}"
                        img_buffer = io.BytesIO()
                        pil_image.save(img_buffer, format='PNG')
                        img_bytes = img_buffer.getvalue()
                        logger.info(f"  Page {page_num}: {len(img_bytes)} bytes PNG, size={pil_image.size}")
                        page_tasks.append(_rate_limited_ocr(img_bytes, page_name))

                    page_results = await asyncio.gather(*page_tasks)
                    for idx, doc_data in enumerate(page_results):
                        doc_type = doc_data.get('document_type', '?')
                        has_data = _has_useful_data(doc_data)
                        logger.info(
                            f"  Page {idx+1} OCR result: type={doc_type}, "
                            f"nama='{doc_data.get('nama', '')}', "
                            f"no_visa='{doc_data.get('no_visa', '')}', "
                            f"has_data={has_data}"
                        )
                        if has_data:
                            items.append(doc_data_to_item(doc_data))

                    logger.info(f"PDF '{filename}': {len(items)} valid items extracted")
                    # Only cache non-empty results so failed files can be retried
                    if items:
                        ocr_cache.put(file_hash, items)

                return filename, True, "PDF", items, was_cached
            else:
                # Image processing
                if cached_result:
                    items = cached_result
                else:
                    doc_data = await _rate_limited_ocr(content, filename)

                    if doc_data.get('_partial'):
                        return filename, False, doc_data.get('_error', 'OCR failed'), [], False

                    items = [doc_data_to_item(doc_data)]
                    ocr_cache.put(file_hash, items)

                doc_type = items[0].jenis_identitas if items else "UNKNOWN"
                return filename, True, doc_type, items, was_cached

        except Exception as e:
            logger.error(f"Error processing {filename}: {e}", exc_info=True)
            return filename, False, str(e), [], False

    # --- Batch Processing ---
    update_progress(session_id, total=len(file_data), status="processing")

    all_batches = [
        file_data[i:i + BATCH_SIZE]
        for i in range(0, len(file_data), BATCH_SIZE)
    ]
    logger.info(f"Processing {len(file_data)} files in {len(all_batches)} batch(es) of up to {BATCH_SIZE}")

    tasks = []
    for batch in all_batches:
        batch_tasks = [_process_one(fn, ext, content) for fn, ext, content in batch]
        tasks.extend(batch_tasks)

    results: List[ProcessingResult] = []
    extracted_data: List[ExtractedDataItem] = []
    file_results: List[FileResult] = []

    completed = 0
    for coro in asyncio.as_completed(tasks):
        filename, success, doc_type_or_error, items, was_cached = await coro
        completed += 1

        if success:
            extracted_data.extend(items)
            results.append(ProcessingResult(
                filename=filename, success=True,
                document_type=doc_type_or_error, data=None
            ))
            file_results.append(FileResult(
                filename=filename, status="success",
                document_type=doc_type_or_error, cached=was_cached
            ))
        else:
            results.append(ProcessingResult(
                filename=filename, success=False,
                error=doc_type_or_error
            ))
            file_results.append(FileResult(
                filename=filename, status="failed",
                error=doc_type_or_error
            ))

        update_progress(
            session_id,
            current=completed,
            current_file=filename,
            status="processing" if completed < len(file_data) else "post-processing",
            completed_files=[fr.filename for fr in file_results if fr.status == "success"],
            failed_files=[fr.filename for fr in file_results if fr.status == "failed"],
        )

    return results, extracted_data, file_results


def run_pipeline(
    extracted_data: List[ExtractedDataItem],
    session_id: str,
) -> Tuple[List[ExtractedDataItem], List[List[ValidationWarning]]]:
    """
    Post-processing pipeline: Sanitize → Fuzzy Merge → Validate.

    Args:
        extracted_data: Raw extracted items from OCR
        session_id: Session ID for progress tracking

    Returns:
        Tuple of (final_data, validation_warnings)
    """
    # STEP 1: SANITIZATION
    update_progress(session_id, status="sanitizing")
    sanitized_data = []
    for item in extracted_data:
        cleaned_item = cleaner.clean_entry(item)
        if cleaned_item:
            sanitized_data.append(cleaned_item)

    # STEP 2: FUZZY MERGE
    update_progress(session_id, status="merging")
    final_data = cleaner.fuzzy_merge_data(sanitized_data)

    # STEP 3: VALIDATION
    update_progress(session_id, status="validating")
    all_warnings = []
    for item in final_data:
        row_dict = item.model_dump() if hasattr(item, 'model_dump') else item.dict()
        warnings = validate_row(row_dict)
        all_warnings.append([ValidationWarning(**w) for w in warnings])

    logger.info(
        f"Pipeline: {len(extracted_data)} raw → {len(sanitized_data)} sanitized → "
        f"{len(final_data)} merged, {sum(len(w) for w in all_warnings)} warnings"
    )

    return final_data, all_warnings
