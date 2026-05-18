"""
OpenCode Zen OCR Service — Extracts text and structured data from ID documents
Uses GPT models via OpenCode Zen API for OCR on KTP/KK, Passport, and Visa images.
"""
import os
import io
import json
import base64
import logging
import time
import re
import requests
from PIL import Image

from app.services.gemini_ocr import (
    GEMINI_CACHE_TTL_SECONDS,
    GEMINI_TEXT_CACHE_TTL_SECONDS,
    EXTRACT_PROMPT,
    EXTRACT_TEXT_PROMPT,
    _resolve_cache_policy,
    _resolve_cached_or_compute,
    _parse_structured_json,
    build_gemini_cache_key,
)

logger = logging.getLogger(__name__)

OPENCODE_API_KEY = os.getenv("OPENCODE_API_KEY", "")
OPENCODE_MODEL = os.getenv("OPENCODE_MODEL", "gpt-5-nano")
OPENCODE_API_URL = "https://opencode.ai/zen/v1/chat/completions"

MAX_API_RETRIES = 3


def _call_opencode(payload: dict) -> dict:
    """Call OpenCode Zen API with automatic retry on rate limit/network/server errors."""
    headers = {
        "Authorization": f"Bearer {OPENCODE_API_KEY}",
        "Content-Type": "application/json",
    }
    for attempt in range(1, MAX_API_RETRIES + 1):
        try:
            resp = requests.post(OPENCODE_API_URL, json=payload, headers=headers, timeout=60)
        except requests.Timeout:
            delay = min(10, 2 ** attempt)
            logger.warning(f"OpenCode API timeout - retry {attempt}/{MAX_API_RETRIES} in {delay}s")
            time.sleep(delay)
            continue
        except requests.RequestException as e:
            delay = min(10, 2 ** attempt)
            logger.warning(f"OpenCode API network error ({type(e).__name__}) - retry {attempt}/{MAX_API_RETRIES} in {delay}s")
            time.sleep(delay)
            continue

        if resp.status_code == 429:
            delay = min(20, 2 ** attempt + 2)
            logger.warning(f"OpenCode API 429 - retry {attempt}/{MAX_API_RETRIES} in {delay}s")
            time.sleep(delay)
            continue
        if resp.status_code >= 500:
            delay = min(10, 2 ** attempt)
            logger.warning(f"OpenCode API {resp.status_code} - retry {attempt}/{MAX_API_RETRIES} in {delay}s")
            time.sleep(delay)
            continue

        resp.raise_for_status()
        return resp.json()

    resp = requests.post(OPENCODE_API_URL, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()


def _image_to_base64(img_bytes: bytes) -> tuple:
    """Convert image bytes to base64 and detect MIME type."""
    img = Image.open(io.BytesIO(img_bytes))
    fmt = img.format or "JPEG"
    mime_map = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
    mime_type = mime_map.get(fmt.upper(), "image/jpeg")

    if fmt.upper() not in mime_map:
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG")
        img_bytes = buf.getvalue()
        mime_type = "image/jpeg"

    return base64.b64encode(img_bytes).decode("utf-8"), mime_type


def _extract_result_text(result: dict) -> str:
    """Extract text from OpenCode Zen API response."""
    return result["choices"][0]["message"]["content"]


def extract_text_from_image(image_bytes: bytes, filename: str = "", cache_mode: str = "default") -> str:
    """
    Extract raw text from an image using OpenCode Zen Vision.
    """
    if not OPENCODE_API_KEY:
        raise RuntimeError("OPENCODE_API_KEY not configured")

    task_type = "opencode_extract_text"
    allow_cache_read, allow_cache_write = _resolve_cache_policy(cache_mode)
    cache_key = build_gemini_cache_key(
        input_data=image_bytes,
        prompt_version="opencode-text-v1",
        model=OPENCODE_MODEL,
        task_type=task_type,
    )

    def _compute_result() -> dict:
        b64_image, mime_type = _image_to_base64(image_bytes)
        payload = {
            "model": OPENCODE_MODEL,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": EXTRACT_TEXT_PROMPT},
                    {"type": "image_url", "image_url": {
                        "url": f"data:{mime_type};base64,{b64_image}"
                    }},
                ]
            }],
            "temperature": 0.1,
            "max_tokens": 4096,
        }
        upstream_result = _call_opencode(payload)
        text_value = _extract_result_text(upstream_result)
        return {"text": text_value}

    cached_payload = _resolve_cached_or_compute(
        cache_key=cache_key,
        input_data=image_bytes,
        prompt_version="opencode-text-v1",
        task_type=task_type,
        ttl_seconds=GEMINI_TEXT_CACHE_TTL_SECONDS,
        compute_fn=_compute_result,
        cache_mode=cache_mode,
        allow_cache_read=allow_cache_read,
        allow_cache_write=allow_cache_write,
    )
    text = cached_payload.get("text", "")
    logger.info(f"OpenCode extracted {len(text)} chars from {filename}")
    return text


def extract_document_data(text_or_bytes, filename: str = "", cache_mode: str = "default") -> dict:
    """
    Extract structured document data from an image or text using OpenCode Zen.
    """
    if not OPENCODE_API_KEY:
        raise RuntimeError("OPENCODE_API_KEY not configured")

    allow_cache_read, allow_cache_write = _resolve_cache_policy(cache_mode)

    if isinstance(text_or_bytes, bytes):
        task_type = "opencode_extract_document:image"
        cache_key = build_gemini_cache_key(
            input_data=text_or_bytes,
            prompt_version="opencode-structured-v1",
            model=OPENCODE_MODEL,
            task_type=task_type,
        )

        def _compute_result() -> dict:
            b64_image, mime_type = _image_to_base64(text_or_bytes)
            payload = {
                "model": OPENCODE_MODEL,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": EXTRACT_PROMPT},
                        {"type": "image_url", "image_url": {
                            "url": f"data:{mime_type};base64,{b64_image}"
                        }},
                    ]
                }],
                "temperature": 0.1,
                "max_tokens": 4096,
            }
            result = _call_opencode(payload)
            raw_text = _extract_result_text(result)
            return _parse_structured_json(raw_text)
    else:
        task_type = "opencode_extract_document:text"
        cache_key = build_gemini_cache_key(
            input_data=text_or_bytes,
            prompt_version="opencode-structured-v1",
            model=OPENCODE_MODEL,
            task_type=task_type,
        )

        def _compute_result() -> dict:
            payload = {
                "model": OPENCODE_MODEL,
                "messages": [{
                    "role": "user",
                    "content": [{
                        "type": "text",
                        "text": f"{EXTRACT_PROMPT}\n\nBerikut teks dari dokumen:\n\n{text_or_bytes}"
                    }]
                }],
                "temperature": 0.1,
                "max_tokens": 4096,
            }
            result = _call_opencode(payload)
            raw_text = _extract_result_text(result)
            return _parse_structured_json(raw_text)

    logger.info(
        "Extracting structured data for %s via OpenCode (%s) key=%s... cache_mode=%s",
        filename,
        OPENCODE_MODEL,
        cache_key[:12],
        cache_mode,
    )
    return _resolve_cached_or_compute(
        cache_key=cache_key,
        input_data=text_or_bytes,
        prompt_version="opencode-structured-v1",
        task_type=task_type,
        ttl_seconds=GEMINI_CACHE_TTL_SECONDS,
        compute_fn=_compute_result,
        cache_mode=cache_mode,
        allow_cache_read=allow_cache_read,
        allow_cache_write=allow_cache_write,
    )
