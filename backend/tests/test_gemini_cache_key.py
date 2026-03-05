"""
Unit tests for deterministic Gemini cache key generation.
"""
from app.services.gemini_cache_key import build_gemini_cache_key, compute_input_hash


def test_compute_input_hash_is_stable_for_same_bytes():
    input_data = b"same-document-binary"
    assert compute_input_hash(input_data) == compute_input_hash(input_data)


def test_build_gemini_cache_key_same_inputs_same_key():
    key_1 = build_gemini_cache_key(
        input_data=b"file-bytes",
        prompt_version="v1",
        model="gemini-2.5-flash",
        task_type="extract_document_data:image",
    )
    key_2 = build_gemini_cache_key(
        input_data=b"file-bytes",
        prompt_version="v1",
        model="gemini-2.5-flash",
        task_type="extract_document_data:image",
    )
    assert key_1 == key_2


def test_build_gemini_cache_key_changes_when_prompt_changes():
    base_kwargs = {
        "input_data": b"file-bytes",
        "model": "gemini-2.5-flash",
        "task_type": "extract_document_data:image",
    }
    key_1 = build_gemini_cache_key(prompt_version="v1", **base_kwargs)
    key_2 = build_gemini_cache_key(prompt_version="v2", **base_kwargs)
    assert key_1 != key_2


def test_build_gemini_cache_key_changes_when_model_changes():
    base_kwargs = {
        "input_data": b"file-bytes",
        "prompt_version": "v1",
        "task_type": "extract_document_data:image",
    }
    key_1 = build_gemini_cache_key(model="gemini-2.5-flash", **base_kwargs)
    key_2 = build_gemini_cache_key(model="gemini-2.5-pro", **base_kwargs)
    assert key_1 != key_2


def test_build_gemini_cache_key_changes_when_task_changes():
    base_kwargs = {
        "input_data": "same text payload",
        "prompt_version": "v1",
        "model": "gemini-2.5-flash",
    }
    key_1 = build_gemini_cache_key(task_type="extract_document_data:text", **base_kwargs)
    key_2 = build_gemini_cache_key(task_type="extract_text_from_image", **base_kwargs)
    assert key_1 != key_2
