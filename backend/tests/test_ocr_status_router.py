"""
Tests for OCR status endpoint.
"""
import importlib
from datetime import timedelta

from fastapi import status

from app.auth import create_access_token
from app.models.ocr_review import OcrProcessingLog
from app.models.user import PlanType, SubscriptionStatus, utc_now

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
    assert data["providers"]["gemini"]["bypass_recent_files_1h"] == 0
    assert data["providers"]["gemini"]["bypass_remaining_files_1h"] == 42
    assert data["providers"]["gemini"]["bypass_allowed_now"] is False
    assert data["providers"]["tesseract"]["available"] is True
    assert "zai" not in data["providers"]
    assert "cache" in data
    assert data["cache_quota"]["bypass"]["limit_files"] == 42
    assert data["cache_quota"]["bypass"]["remaining_files"] == 42
    assert data["subscription"]["plan"] == "free"
    assert data["ai_cache"] == {"total": 5, "active": 4, "expired": 1}
    assert "requested_by" in data


def test_ocr_status_shows_bypass_allowed_for_pro_with_remaining_quota(client, db_session, test_user, monkeypatch):
    sub = test_user.subscription
    sub.plan = PlanType.PRO
    sub.status = SubscriptionStatus.ACTIVE
    sub.subscribed_at = utc_now()
    sub.expires_at = utc_now() + timedelta(days=30)
    db_session.commit()

    monkeypatch.setattr(documents_router_module, "OCR_BYPASS_MAX_FILES_PER_HOUR", 3)
    db_session.add(
        OcrProcessingLog(
            user_id=test_user.id,
            session_id="s-a",
            filename="a.jpg",
            status="success",
            processing_ms=100.0,
            cached=False,
            provenance_json='{"cache_mode": "bypass"}',
        )
    )
    db_session.commit()

    token = create_access_token(data={"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/ocr/status", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["providers"]["gemini"]["bypass_recent_files_1h"] == 1
    assert data["providers"]["gemini"]["bypass_remaining_files_1h"] == 2
    assert data["providers"]["gemini"]["bypass_allowed_now"] is True
    assert data["subscription"]["plan"] == "pro"


def test_ocr_status_shows_bypass_not_allowed_when_quota_exhausted(client, db_session, test_user, monkeypatch):
    sub = test_user.subscription
    sub.plan = PlanType.PRO
    sub.status = SubscriptionStatus.ACTIVE
    sub.subscribed_at = utc_now()
    sub.expires_at = utc_now() + timedelta(days=30)
    db_session.commit()

    monkeypatch.setattr(documents_router_module, "OCR_BYPASS_MAX_FILES_PER_HOUR", 2)
    db_session.add(
        OcrProcessingLog(
            user_id=test_user.id,
            session_id="s-a",
            filename="a.jpg",
            status="success",
            processing_ms=100.0,
            cached=False,
            provenance_json='{"cache_mode": "bypass"}',
        )
    )
    db_session.add(
        OcrProcessingLog(
            user_id=test_user.id,
            session_id="s-b",
            filename="b.jpg",
            status="success",
            processing_ms=100.0,
            cached=False,
            provenance_json='{"cache_mode": "bypass"}',
        )
    )
    db_session.commit()

    token = create_access_token(data={"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/ocr/status", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["providers"]["gemini"]["bypass_recent_files_1h"] == 2
    assert data["providers"]["gemini"]["bypass_remaining_files_1h"] == 0
    assert data["providers"]["gemini"]["bypass_allowed_now"] is False
