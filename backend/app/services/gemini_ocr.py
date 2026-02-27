"""
Gemini AI OCR Service — Extracts text and structured data from ID documents
Uses the Google Gemini API for high-accuracy OCR on KTP, Passport, and Visa images.
"""
import os
import io
import json
import base64
import logging
import time
import requests
from PIL import Image

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Structured extraction prompt for Indonesian ID documents
EXTRACT_PROMPT = """Kamu adalah OCR specialist untuk dokumen identitas Indonesia.
Analisis gambar ini dan ekstrak SEMUA informasi yang terlihat.

Tentukan jenis dokumen: KTP, PASPOR, atau VISA.

Kembalikan HANYA JSON (tanpa markdown, tanpa backticks) dengan format berikut:
{
  "document_type": "KTP" atau "PASPOR" atau "VISA",
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
  "no_telepon": "nomor telepon (jika ada)",
  "no_hp": "nomor HP (jika ada)"
}

Isi field yang tidak ditemukan dengan string kosong "".
PENTING: Kembalikan HANYA JSON, tanpa teks lain."""

EXTRACT_TEXT_PROMPT = """Extract ALL text visible in this image. 
Return the raw text exactly as it appears, preserving layout where possible.
This is an Indonesian identity document (KTP, Passport, or Visa)."""


def _get_api_url() -> str:
    """Get the Gemini API URL."""
    return f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"


MAX_API_RETRIES = 3

def _call_gemini(payload: dict) -> dict:
    """Call Gemini API with automatic retry on 429/5xx errors."""
    url = _get_api_url()
    for attempt in range(1, MAX_API_RETRIES + 1):
        resp = requests.post(url, json=payload, timeout=60)
        if resp.status_code == 429 or resp.status_code >= 500:
            delay = 2 ** attempt  # 2s, 4s, 8s backoff
            logger.warning(f"Gemini API {resp.status_code} — retry {attempt}/{MAX_API_RETRIES} in {delay}s")
            time.sleep(delay)
            continue
        resp.raise_for_status()
        return resp.json()
    # Final attempt — let it raise
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


def extract_text_from_image(image_bytes: bytes, filename: str = "") -> str:
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

    logger.info(f"Extracting text from {filename} via Gemini ({GEMINI_MODEL})")
    result = _call_gemini(payload)

    text = result["candidates"][0]["content"]["parts"][0]["text"]
    logger.info(f"Extracted {len(text)} chars from {filename}")
    return text


def extract_document_data(text_or_bytes, filename: str = "") -> dict:
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

    # If we receive bytes, do direct structured extraction from image
    if isinstance(text_or_bytes, bytes):
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
    else:
        # Text-based extraction
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

    logger.info(f"Extracting structured data via Gemini ({GEMINI_MODEL})")
    result = _call_gemini(payload)

    raw_text = result["candidates"][0]["content"]["parts"][0]["text"]

    # Parse JSON response
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code block
        import re
        match = re.search(r'```(?:json)?\s*\n(.*?)\n```', raw_text, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
        else:
            logger.error(f"Failed to parse Gemini response as JSON: {raw_text[:200]}")
            data = {"document_type": "UNKNOWN", "_raw": raw_text}

    return data
