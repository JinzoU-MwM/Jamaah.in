"""
Deterministic cache keys for Gemini requests.
"""
from __future__ import annotations

import hashlib


def compute_input_hash(input_data: bytes | str) -> str:
    """Compute stable SHA-256 hash from bytes or text input."""
    if isinstance(input_data, str):
        data = input_data.encode("utf-8")
    else:
        data = input_data
    return hashlib.sha256(data).hexdigest()


def build_gemini_cache_key(
    *,
    input_data: bytes | str,
    prompt_version: str,
    model: str,
    task_type: str,
) -> str:
    """
    Build deterministic key from input hash and request identity dimensions.
    """
    input_hash = compute_input_hash(input_data)
    raw_key = f"{task_type}:{model}:{prompt_version}:{input_hash}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

