"""
Tests for OCR review queue and dashboard endpoints.
"""
import importlib
from datetime import timedelta

from fastapi import status

from app.auth import create_access_token
from app.models.ocr_review import OcrProcessingLog
from app.models.user import PlanType, SubscriptionStatus, utc_now
from app.schemas import ProcessingResult, ExtractedDataItem, FileResult

documents_router_module = importlib.import_module("app.routers.documents_router")


def _auth_headers(user_id: int) -> dict:
    token = create_access_token(data={"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


def _activate_pro_subscription(db_session, user):
    sub = user.subscription
    sub.plan = PlanType.PRO
    sub.status = SubscriptionStatus.ACTIVE
    sub.subscribed_at = utc_now()
    sub.expires_at = utc_now() + timedelta(days=30)
    db_session.commit()


def test_ocr_review_queue_requires_auth(client):
    response = client.get("/ocr/review-queue")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_ocr_review_queue_and_dashboard_flow(client, test_user, monkeypatch):
    async def mock_process_files(_file_data, _session_id, cache_mode="default"):
        assert cache_mode in {"default", "refresh", "bypass"}
        return (
            [ProcessingResult(filename="ktp.jpg", success=True)],
            [ExtractedDataItem(nama="AHMAD", no_identitas="1234567890123456")],
            [
                FileResult(
                    filename="ktp.jpg",
                    status="failed",
                    error="OCR timeout",
                    error_category="timeout",
                    processing_ms=1200.0,
                    cached=False,
                ),
                FileResult(
                    filename="paspor.jpg",
                    status="success",
                    processing_ms=500.0,
                    cached=True,
                    document_type="PASPOR",
                ),
            ],
        )

    def mock_run_pipeline(extracted_data, _session_id):
        return extracted_data, []

    monkeypatch.setattr(documents_router_module, "process_files", mock_process_files)
    monkeypatch.setattr(documents_router_module, "run_pipeline", mock_run_pipeline)

    files = {"files": ("ktp.jpg", b"fake-jpg-bytes", "image/jpeg")}
    headers = _auth_headers(test_user.id)
    process_resp = client.post("/process-documents/", headers=headers, files=files)
    assert process_resp.status_code == status.HTTP_200_OK

    queue_resp = client.get("/ocr/review-queue", headers=headers)
    assert queue_resp.status_code == status.HTTP_200_OK
    queue_data = queue_resp.json()
    assert queue_data["count"] >= 1
    first_item = queue_data["items"][0]
    assert first_item["status"] == "pending"
    assert first_item["filename"] == "ktp.jpg"

    decision_resp = client.patch(
        f"/ocr/review-queue/{first_item['id']}",
        headers=headers,
        json={"action": "approve", "notes": "sudah dicek"},
    )
    assert decision_resp.status_code == status.HTTP_200_OK
    assert decision_resp.json()["status"] == "approved"

    dashboard_resp = client.get("/ocr/dashboard?days=30", headers=headers)
    assert dashboard_resp.status_code == status.HTTP_200_OK
    dashboard = dashboard_resp.json()
    assert dashboard["total_files"] >= 2
    assert dashboard["failed_count"] >= 1
    assert dashboard["pending_review_count"] == 0


def test_process_documents_cache_mode_forwarded(client, test_user, monkeypatch):
    seen = {"mode": None}

    async def mock_process_files(_file_data, _session_id, cache_mode="default"):
        seen["mode"] = cache_mode
        return (
            [ProcessingResult(filename="ktp.jpg", success=True)],
            [ExtractedDataItem(nama="AHMAD", no_identitas="1234567890123456")],
            [FileResult(filename="ktp.jpg", status="success", cached=False, processing_ms=123.0)],
        )

    def mock_run_pipeline(extracted_data, _session_id):
        return extracted_data, []

    monkeypatch.setattr(documents_router_module, "process_files", mock_process_files)
    monkeypatch.setattr(documents_router_module, "run_pipeline", mock_run_pipeline)

    headers = _auth_headers(test_user.id)
    files = {"files": ("ktp.jpg", b"fake-jpg-bytes", "image/jpeg")}
    response = client.post("/process-documents/?cache_mode=refresh", headers=headers, files=files)
    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["cache_mode"] == "refresh"
    assert seen["mode"] == "refresh"


def test_process_documents_invalid_cache_mode_rejected(client, test_user):
    headers = _auth_headers(test_user.id)
    files = {"files": ("ktp.jpg", b"fake-jpg-bytes", "image/jpeg")}
    response = client.post("/process-documents/?cache_mode=invalid", headers=headers, files=files)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_process_documents_bypass_requires_pro_plan(client, test_user):
    headers = _auth_headers(test_user.id)
    files = {"files": ("ktp.jpg", b"fake-jpg-bytes", "image/jpeg")}
    response = client.post("/process-documents/?cache_mode=bypass", headers=headers, files=files)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "requires active Pro subscription" in response.json()["detail"]


def test_process_documents_bypass_allowed_for_pro(client, db_session, test_user, monkeypatch):
    _activate_pro_subscription(db_session, test_user)
    seen = {"mode": None}

    async def mock_process_files(_file_data, _session_id, cache_mode="default"):
        seen["mode"] = cache_mode
        return (
            [ProcessingResult(filename="ktp.jpg", success=True)],
            [ExtractedDataItem(nama="AHMAD", no_identitas="1234567890123456")],
            [FileResult(filename="ktp.jpg", status="success", cached=False, processing_ms=120.0)],
        )

    def mock_run_pipeline(extracted_data, _session_id):
        return extracted_data, []

    monkeypatch.setattr(documents_router_module, "process_files", mock_process_files)
    monkeypatch.setattr(documents_router_module, "run_pipeline", mock_run_pipeline)
    monkeypatch.setattr(documents_router_module, "OCR_BYPASS_MAX_FILES_PER_HOUR", 100)

    headers = _auth_headers(test_user.id)
    files = {"files": ("ktp.jpg", b"fake-jpg-bytes", "image/jpeg")}
    response = client.post("/process-documents/?cache_mode=bypass", headers=headers, files=files)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["cache_mode"] == "bypass"
    assert seen["mode"] == "bypass"


def test_process_documents_bypass_hourly_limit_enforced(client, db_session, test_user, monkeypatch):
    _activate_pro_subscription(db_session, test_user)
    monkeypatch.setattr(documents_router_module, "OCR_BYPASS_MAX_FILES_PER_HOUR", 2)

    def should_not_run(*args, **kwargs):
        raise AssertionError("process_files should not run when bypass limit is exceeded")

    monkeypatch.setattr(documents_router_module, "process_files", should_not_run)

    db_session.add(
        OcrProcessingLog(
            user_id=test_user.id,
            session_id="sess-a",
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
            session_id="sess-b",
            filename="b.jpg",
            status="success",
            processing_ms=120.0,
            cached=False,
            provenance_json='{"cache_mode": "bypass"}',
        )
    )
    db_session.commit()

    headers = _auth_headers(test_user.id)
    files = {"files": ("ktp.jpg", b"fake-jpg-bytes", "image/jpeg")}
    response = client.post("/process-documents/?cache_mode=bypass", headers=headers, files=files)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "Bypass cache hourly limit exceeded" in response.json()["detail"]
