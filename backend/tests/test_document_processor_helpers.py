import json

from app.services.document_processor import categorize_error_message, _build_failed_file_provenance


def test_categorize_error_message_rate_limit():
    assert categorize_error_message("Gemini API 429 rate limit exceeded") == "rate_limit"


def test_categorize_error_message_timeout():
    assert categorize_error_message("Request timeout while processing") == "timeout"


def test_categorize_error_message_invalid_file_type():
    assert categorize_error_message("Invalid file type: .txt") == "invalid_file_type"


def test_categorize_error_message_fallback_unknown():
    assert categorize_error_message("Unexpected parser branch") == "processing_error"


def test_build_failed_file_provenance_includes_cache_mode():
    payload = json.loads(_build_failed_file_provenance("bypass"))
    assert payload["status"] == "failed"
    assert payload["cache_mode"] == "bypass"
    assert payload["cached"] is False
