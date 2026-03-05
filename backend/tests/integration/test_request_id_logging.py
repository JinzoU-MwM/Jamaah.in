"""
Integration tests for request ID propagation and request logging middleware.
"""
from fastapi import status

from app import logging_config


def test_request_id_is_generated_when_missing(client):
    response = client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    request_id = response.headers.get("X-Request-ID")
    assert request_id is not None
    assert len(request_id) >= 16


def test_request_id_uses_incoming_header(client):
    custom_request_id = "req-test-123"
    response = client.get("/health", headers={"X-Request-ID": custom_request_id})

    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("X-Request-ID") == custom_request_id


def test_request_logging_has_expected_fields(client, monkeypatch):
    logs = []

    class FakeLogger:
        def info(self, event, **kwargs):
            logs.append(("info", event, kwargs))

        def exception(self, event, **kwargs):
            logs.append(("exception", event, kwargs))

    fake_logger = FakeLogger()
    monkeypatch.setattr(logging_config.structlog, "get_logger", lambda *args, **kwargs: fake_logger)

    response = client.get("/health", headers={"X-Request-ID": "req-log-001"})

    assert response.status_code == status.HTTP_200_OK

    info_logs = [item for item in logs if item[0] == "info" and item[1] == "http_request"]
    assert info_logs, "expected at least one http_request info log"

    fields = info_logs[-1][2]
    assert fields["request_id"] == "req-log-001"
    assert fields["method"] == "GET"
    assert fields["path"] == "/health"
    assert fields["status_code"] == status.HTTP_200_OK
    assert isinstance(fields["duration_ms"], float)
