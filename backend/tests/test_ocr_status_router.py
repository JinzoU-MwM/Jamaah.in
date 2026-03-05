"""
Tests for OCR status endpoint.
"""
import importlib

from fastapi import status

from app.auth import create_access_token

documents_router_module = importlib.import_module("app.routers.documents_router")


def test_ocr_status_requires_auth(client):
    """Endpoint should reject requests without JWT."""
    response = client.get("/ocr/status")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_ocr_status_returns_provider_state(client, test_user, monkeypatch):
    """Endpoint should return OCR config/provider readiness for authenticated users."""
    monkeypatch.setattr(documents_router_module, "OCR_ENGINE", "gemini")
    monkeypatch.setattr(documents_router_module, "OCR_FALLBACK_ENABLED", True)
    monkeypatch.setattr(documents_router_module, "GEMINI_API_KEY", "gem-key")
    monkeypatch.setattr(documents_router_module, "GEMINI_MODEL", "gemini-2.5-flash")
    monkeypatch.setattr(documents_router_module, "EXTRACT_PROMPT_VERSION", "v-test-1")
    monkeypatch.setattr(documents_router_module, "EXTRACT_TEXT_PROMPT_VERSION", "v-text-1")
    monkeypatch.setattr(documents_router_module, "GEMINI_CACHE_TTL_SECONDS", 600)
    monkeypatch.setattr(documents_router_module, "GEMINI_TEXT_CACHE_TTL_SECONDS", 300)
    monkeypatch.setattr(documents_router_module, "OCR_BYPASS_MAX_FILES_PER_HOUR", 42)
    monkeypatch.setattr(
        documents_router_module,
        "get_ai_cache_stats",
        lambda db: {"total": 5, "active": 4, "expired": 1},
    )
    monkeypatch.setattr(documents_router_module.ocr_engine, "TESSERACT_AVAILABLE", True)

    token = create_access_token(data={"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/ocr/status", headers=headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["primary_engine"] == "gemini"
    assert data["fallback_enabled"] is True
    assert data["providers"]["gemini"]["configured"] is True
    assert data["providers"]["gemini"]["prompt_version"] == "v-test-1"
    assert data["providers"]["gemini"]["text_prompt_version"] == "v-text-1"
    assert data["providers"]["gemini"]["cache_ttl_seconds"] == 600
    assert data["providers"]["gemini"]["text_cache_ttl_seconds"] == 300
    assert data["providers"]["gemini"]["bypass_max_files_per_hour"] == 42
    assert data["providers"]["tesseract"]["available"] is True
    assert "zai" not in data["providers"]
    assert "cache" in data
    assert data["ai_cache"] == {"total": 5, "active": 4, "expired": 1}
    assert "requested_by" in data
