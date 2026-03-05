"""
Gemini AI OCR Service — Extracts text and structured data from ID documents
Uses the Google Gemini API for high-accuracy OCR on KTP/KK, Passport, and Visa images.
"""
import os
import io
import json
import base64
import logging
import time
import threading
import re
import requests
from PIL import Image
from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal
from app.services.ai_result_cache_repo import get_ai_cache, put_ai_cache
from app.services.gemini_cache_key import build_gemini_cache_key, compute_input_hash
from app.services.metrics import metrics_store

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
EXTRACT_PROMPT_VERSION = os.getenv("GEMINI_EXTRACT_PROMPT_VERSION", "2026-03-05-v1")
EXTRACT_TEXT_PROMPT_VERSION = os.getenv("GEMINI_TEXT_PROMPT_VERSION", "2026-03-05-v1")
GEMINI_CACHE_TTL_SECONDS = int(os.getenv("GEMINI_CACHE_TTL_SECONDS", "604800"))  # 7 days
GEMINI_TEXT_CACHE_TTL_SECONDS = int(os.getenv("GEMINI_TEXT_CACHE_TTL_SECONDS", "259200"))  # 3 days

_singleflight_registry_lock = threading.Lock()
_singleflight_locks: dict[str, threading.Lock] = {}
_CACHE_MODES = {"default", "refresh", "bypass"}

# Structured extraction prompt for Indonesian ID documents
EXTRACT_PROMPT = """Kamu adalah OCR specialist untuk dokumen identitas Indonesia.
Analisis gambar ini dan ekstrak SEMUA informasi yang terlihat.

Tentukan jenis dokumen: KTP, KK, PASPOR, atau VISA.
Jika dokumen adalah KK (Kartu Keluarga), isi:
- "document_type" = "KK"
- "kk_member_names" = daftar nama anggota keluarga dipisahkan titik koma (;)
- "kk_member_fathers" = mapping per anggota format "NAMA_ANGGOTA:NAMA_AYAH" dipisahkan titik koma (;)
- "alamat" = alamat KK

Kembalikan HANYA JSON (tanpa markdown, tanpa backticks) dengan format berikut:
{
  "document_type": "KTP" atau "KK" atau "PASPOR" atau "VISA",
  "nama": "nama lengkap",
  "no_identitas": "NIK atau nomor identitas",
  "tempat_lahir": "kota lahir",
  "tanggal_lahir": "DD-MM-YYYY",
  "jenis_kelamin": "LAKI-LAKI atau PEREMPUAN",
  "alamat": "alamat lengkap",
  "rt_rw": "RT/RW",
  "kelurahan": "kelurahan/desa",
  "kecamatan": "kecamatan",
  "kabupaten": "kabupaten/kota",
  "provinsi": "provinsi",
  "agama": "agama",
  "status_pernikahan": "BELUM KAWIN/KAWIN/CERAI HIDUP/CERAI MATI",
  "pekerjaan": "pekerjaan",
  "pendidikan": "pendidikan terakhir",
  "kewarganegaraan": "WNI atau WNA",
  "no_paspor": "nomor paspor (jika paspor/visa)",
  "tanggal_paspor": "tanggal terbit paspor DD-MM-YYYY",
  "kota_paspor": "kota terbit paspor",
  "no_visa": "nomor visa (jika visa)",
  "tanggal_visa": "tanggal terbit visa DD-MM-YYYY",
  "tanggal_visa_akhir": "tanggal berakhir visa DD-MM-YYYY",
  "provider_visa": "provider/embassy visa",
  "nama_ayah": "nama ayah (jika ada)",
  "kk_member_names": "nama anggota KK dipisahkan ';' (khusus KK)",
  "kk_member_fathers": "mapping anggota ke ayah: NAMA:NAMA_AYAH dipisahkan ';' (khusus KK)",
  "no_telepon": "nomor telepon (jika ada)",
  "no_hp": "nomor HP (jika ada)"
}

Isi field yang tidak ditemukan dengan string kosong "".
PENTING: Kembalikan HANYA JSON, tanpa teks lain."""

EXTRACT_TEXT_PROMPT = """Extract ALL text visible in this image. 
Return the raw text exactly as it appears, preserving layout where possible.
This is an Indonesian identity document (KTP, KK, Passport, or Visa)."""


def _get_singleflight_lock(cache_key: str) -> threading.Lock:
    with _singleflight_registry_lock:
        lock = _singleflight_locks.get(cache_key)
        if lock is None:
            lock = threading.Lock()
            _singleflight_locks[cache_key] = lock
        return lock


def _load_persistent_cache(cache_key: str) -> dict | None:
    db = SessionLocal()
    try:
        return get_ai_cache(db, cache_key=cache_key)
    except SQLAlchemyError as exc:
        logger.warning("Persistent cache read failed: %s", exc)
        return None
    finally:
        db.close()


def _store_persistent_cache(
    *,
    cache_key: str,
    input_data: bytes | str,
    prompt_version: str,
    task_type: str,
    result: dict,
    ttl_seconds: int,
) -> None:
    db = SessionLocal()
    try:
        put_ai_cache(
            db,
            cache_key=cache_key,
            input_hash=compute_input_hash(input_data),
            model=GEMINI_MODEL,
            prompt_version=prompt_version,
            task_type=task_type,
            result=result,
            ttl_seconds=ttl_seconds,
        )
    except SQLAlchemyError as exc:
        logger.warning("Persistent cache write failed: %s", exc)
    finally:
        db.close()


def _normalize_cache_mode(cache_mode: str) -> str:
    normalized = (cache_mode or "default").strip().lower()
    if normalized not in _CACHE_MODES:
        raise ValueError(f"Unsupported cache_mode='{cache_mode}'")
    return normalized


def _resolve_cache_policy(cache_mode: str) -> tuple[bool, bool]:
    normalized = _normalize_cache_mode(cache_mode)
    if normalized == "default":
        return True, True
    if normalized == "refresh":
        return False, True
    return False, False


def _resolve_cached_or_compute(
    *,
    cache_key: str,
    input_data: bytes | str,
    prompt_version: str,
    task_type: str,
    ttl_seconds: int,
    compute_fn,
    allow_cache_read: bool = True,
    allow_cache_write: bool = True,
) -> dict:
    if allow_cache_read:
        cached = _load_persistent_cache(cache_key)
        if cached is not None:
            metrics_store.observe_gemini_cache_result(task_type, True)
            logger.info("Gemini persistent cache HIT task=%s key=%s...", task_type, cache_key[:12])
            return cached

    key_lock = _get_singleflight_lock(cache_key)
    with key_lock:
        if allow_cache_read:
            cached = _load_persistent_cache(cache_key)
            if cached is not None:
                metrics_store.observe_gemini_cache_result(task_type, True)
                logger.info(
                    "Gemini persistent cache HIT(after-wait) task=%s key=%s...",
                    task_type,
                    cache_key[:12],
                )
                return cached

        metrics_store.observe_gemini_cache_result(task_type, False)
        metrics_store.observe_gemini_api_call(task_type)
        logger.info("Gemini persistent cache MISS task=%s key=%s... calling upstream", task_type, cache_key[:12])
        result = compute_fn()
        if allow_cache_write:
            _store_persistent_cache(
                cache_key=cache_key,
                input_data=input_data,
                prompt_version=prompt_version,
                task_type=task_type,
                result=result,
                ttl_seconds=ttl_seconds,
            )
        else:
            logger.info(
                "Gemini persistent cache write skipped task=%s key=%s...",
                task_type,
                cache_key[:12],
            )
        return result


def _get_api_url() -> str:
    """Get the Gemini API URL."""
    return f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"


MAX_API_RETRIES = 3

def _call_gemini(payload: dict) -> dict:
    """Call Gemini API with automatic retry on rate limit/network/server errors."""
    url = _get_api_url()
    for attempt in range(1, MAX_API_RETRIES + 1):
        try:
            resp = requests.post(url, json=payload, timeout=60)
        except requests.Timeout:
            delay = min(10, 2 ** attempt)
            logger.warning(f"Gemini API timeout - retry {attempt}/{MAX_API_RETRIES} in {delay}s")
            time.sleep(delay)
            continue
        except requests.RequestException as e:
            delay = min(10, 2 ** attempt)
            logger.warning(f"Gemini API network error ({type(e).__name__}) - retry {attempt}/{MAX_API_RETRIES} in {delay}s")
            time.sleep(delay)
            continue

        if resp.status_code == 429:
            delay = min(20, 2 ** attempt + 2)  # extra cool-down for rate limits
            logger.warning(f"Gemini API 429 - retry {attempt}/{MAX_API_RETRIES} in {delay}s")
            time.sleep(delay)
            continue
        if resp.status_code >= 500:
            delay = min(10, 2 ** attempt)
            logger.warning(f"Gemini API {resp.status_code} - retry {attempt}/{MAX_API_RETRIES} in {delay}s")
            time.sleep(delay)
            continue

        resp.raise_for_status()
        return resp.json()

    # Final attempt - let it raise
    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()


def _image_to_base64(img_bytes: bytes) -> tuple:
    """Convert image bytes to base64 and detect MIME type."""
    img = Image.open(io.BytesIO(img_bytes))
    fmt = img.format or "JPEG"
    mime_map = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
    mime_type = mime_map.get(fmt.upper(), "image/jpeg")

    # Convert to JPEG if format is unusual
    if fmt.upper() not in mime_map:
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG")
        img_bytes = buf.getvalue()
        mime_type = "image/jpeg"

    return base64.b64encode(img_bytes).decode("utf-8"), mime_type


def extract_text_from_image(image_bytes: bytes, filename: str = "", cache_mode: str = "default") -> str:
    """
    Extract raw text from an image using Gemini Vision API.

    Args:
        image_bytes: Image file content as bytes
        filename: Original filename (for logging)

    Returns:
        Extracted text from the image
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not configured")

    task_type = "extract_text_from_image"
    allow_cache_read, allow_cache_write = _resolve_cache_policy(cache_mode)
    cache_key = build_gemini_cache_key(
        input_data=image_bytes,
        prompt_version=EXTRACT_TEXT_PROMPT_VERSION,
        model=GEMINI_MODEL,
        task_type=task_type,
    )
    
    def _compute_result() -> dict:
        b64_image, mime_type = _image_to_base64(image_bytes)
        payload = {
            "contents": [{
                "parts": [
                    {"text": EXTRACT_TEXT_PROMPT},
                    {"inline_data": {"mime_type": mime_type, "data": b64_image}},
                ]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 4096,
            },
        }
        upstream_result = _call_gemini(payload)
        text_value = upstream_result["candidates"][0]["content"]["parts"][0]["text"]
        return {"text": text_value}

    cached_payload = _resolve_cached_or_compute(
        cache_key=cache_key,
        input_data=image_bytes,
        prompt_version=EXTRACT_TEXT_PROMPT_VERSION,
        task_type=task_type,
        ttl_seconds=GEMINI_TEXT_CACHE_TTL_SECONDS,
        compute_fn=_compute_result,
        allow_cache_read=allow_cache_read,
        allow_cache_write=allow_cache_write,
    )
    text = cached_payload.get("text", "")
    logger.info(f"Extracted {len(text)} chars from {filename} (cache_mode={cache_mode})")
    return text


def _parse_structured_json(raw_text: str) -> dict:
    # Parse JSON response
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code block
        match = re.search(r'```(?:json)?\s*\n(.*?)\n```', raw_text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        logger.error(f"Failed to parse Gemini response as JSON: {raw_text[:200]}")
        return {"document_type": "UNKNOWN", "_raw": raw_text}


def extract_document_data(text_or_bytes, filename: str = "", cache_mode: str = "default") -> dict:
    """
    Extract structured document data from an image or text.

    If given bytes, sends the image directly to Gemini for structured extraction.
    If given a string (pre-extracted text), parses it into structured fields.

    Args:
        text_or_bytes: Either image bytes or pre-extracted text string
        filename: Original filename (for logging)

    Returns:
        Dictionary with extracted document fields
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not configured")

    allow_cache_read, allow_cache_write = _resolve_cache_policy(cache_mode)

    # If we receive bytes, do direct structured extraction from image
    if isinstance(text_or_bytes, bytes):
        task_type = "extract_document_data:image"
        cache_key = build_gemini_cache_key(
            input_data=text_or_bytes,
            prompt_version=EXTRACT_PROMPT_VERSION,
            model=GEMINI_MODEL,
            task_type=task_type,
        )

        def _compute_result() -> dict:
            b64_image, mime_type = _image_to_base64(text_or_bytes)
            payload = {
                "contents": [{
                    "parts": [
                        {"text": EXTRACT_PROMPT},
                        {"inline_data": {"mime_type": mime_type, "data": b64_image}},
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 4096,
                    "responseMimeType": "application/json",
                },
            }
            result = _call_gemini(payload)
            raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
            return _parse_structured_json(raw_text)
    else:
        task_type = "extract_document_data:text"
        cache_key = build_gemini_cache_key(
            input_data=text_or_bytes,
            prompt_version=EXTRACT_PROMPT_VERSION,
            model=GEMINI_MODEL,
            task_type=task_type,
        )
        
        def _compute_result() -> dict:
            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"{EXTRACT_PROMPT}\n\nBerikut teks dari dokumen:\n\n{text_or_bytes}"
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 4096,
                    "responseMimeType": "application/json",
                },
            }
            result = _call_gemini(payload)
            raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
            return _parse_structured_json(raw_text)

    logger.info(
        "Extracting structured data for %s via Gemini (%s) key=%s... cache_mode=%s",
        filename,
        GEMINI_MODEL,
        cache_key[:12],
        cache_mode,
    )
    return _resolve_cached_or_compute(
        cache_key=cache_key,
        input_data=text_or_bytes,
        prompt_version=EXTRACT_PROMPT_VERSION,
        task_type=task_type,
        ttl_seconds=GEMINI_CACHE_TTL_SECONDS,
        compute_fn=_compute_result,
        allow_cache_read=allow_cache_read,
        allow_cache_write=allow_cache_write,
    )

