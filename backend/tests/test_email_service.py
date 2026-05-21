"""
Unit tests for email_service — covers Resend API, SMTP fallback, and email builders.
No real HTTP calls are made; urllib.request.urlopen is mocked throughout.
"""
import sys
import json
import smtplib
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import app.services.email_service as svc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_urlopen_response(body: dict, status: int = 200):
    """Return a mock that looks like urllib.request.urlopen's return value."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(body).encode()
    mock_resp.status = status
    return mock_resp


# ---------------------------------------------------------------------------
# generate_otp
# ---------------------------------------------------------------------------

def test_generate_otp_is_six_digits():
    otp = svc.generate_otp()
    assert otp.isdigit()
    assert len(otp) == 6


def test_generate_otp_is_different_each_call():
    otps = {svc.generate_otp() for _ in range(20)}
    assert len(otps) > 1  # extremely unlikely to be identical 20 times


# ---------------------------------------------------------------------------
# _send_via_resend_api
# ---------------------------------------------------------------------------

class TestSendViaResendApi:
    def test_returns_false_when_no_api_key(self):
        with patch.object(svc, "RESEND_API_KEY", ""):
            result = svc._send_via_resend_api("to@example.com", "Subject", "<p>html</p>")
        assert result is False

    def test_sends_correct_payload(self):
        mock_resp = _make_urlopen_response({"id": "abc-123"})
        with (
            patch.object(svc, "RESEND_API_KEY", "re_test_key"),
            patch.object(svc, "SMTP_EMAIL", "noreply@jamaah.in"),
            patch("urllib.request.urlopen", return_value=mock_resp) as mock_open,
        ):
            result = svc._send_via_resend_api("user@example.com", "Test Subject", "<b>hi</b>")

        assert result is True
        # Inspect the Request object passed to urlopen
        request_obj = mock_open.call_args[0][0]
        assert request_obj.get_full_url() == "https://api.resend.com/emails"
        assert request_obj.get_method() == "POST"
        assert request_obj.get_header("Authorization") == "Bearer re_test_key"
        assert request_obj.get_header("Content-type") == "application/json"

        payload = json.loads(request_obj.data)
        assert payload["to"] == ["user@example.com"]
        assert payload["subject"] == "Test Subject"
        assert payload["html"] == "<b>hi</b>"
        assert "Jamaah.in" in payload["from"]
        assert "noreply@jamaah.in" in payload["from"]

    def test_returns_false_on_http_error(self):
        import urllib.error
        http_err = urllib.error.HTTPError(
            url="https://api.resend.com/emails",
            code=422,
            msg="Unprocessable Entity",
            hdrs=None,
            fp=BytesIO(b'{"name":"validation_error"}'),
        )
        with (
            patch.object(svc, "RESEND_API_KEY", "re_test_key"),
            patch("urllib.request.urlopen", side_effect=http_err),
        ):
            result = svc._send_via_resend_api("bad@example.com", "Subject", "<p>html</p>")
        assert result is False

    def test_returns_false_on_network_error(self):
        with (
            patch.object(svc, "RESEND_API_KEY", "re_test_key"),
            patch("urllib.request.urlopen", side_effect=OSError("connection refused")),
        ):
            result = svc._send_via_resend_api("user@example.com", "Subject", "<p>html</p>")
        assert result is False

    def test_uses_fallback_from_when_smtp_email_empty(self):
        mock_resp = _make_urlopen_response({"id": "xyz"})
        with (
            patch.object(svc, "RESEND_API_KEY", "re_test_key"),
            patch.object(svc, "SMTP_EMAIL", ""),
            patch("urllib.request.urlopen", return_value=mock_resp) as mock_open,
        ):
            svc._send_via_resend_api("user@example.com", "Subject", "<p>html</p>")

        payload = json.loads(mock_open.call_args[0][0].data)
        assert "noreply@jamaah.in" in payload["from"]


# ---------------------------------------------------------------------------
# _send_via_smtp (fallback)
# ---------------------------------------------------------------------------

class TestSendViaSmtp:
    def test_returns_false_when_not_configured(self):
        with (
            patch.object(svc, "SMTP_EMAIL", ""),
            patch.object(svc, "SMTP_PASSWORD", ""),
        ):
            result = svc._send_via_smtp("to@example.com", "Subject", "<p>html</p>")
        assert result is False

    def test_sends_via_smtp_successfully(self):
        mock_server = MagicMock()
        with (
            patch.object(svc, "SMTP_EMAIL", "noreply@jamaah.in"),
            patch.object(svc, "SMTP_PASSWORD", "secret"),
            patch.object(svc, "SMTP_HOST", "smtp.hostinger.com"),
            patch.object(svc, "SMTP_PORT", 587),
            patch("smtplib.SMTP") as mock_smtp_cls,
        ):
            mock_smtp_cls.return_value.__enter__ = lambda s: mock_server
            mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
            result = svc._send_via_smtp("user@example.com", "Subject", "<p>html</p>")

        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()

    def test_returns_false_on_smtp_exception(self):
        with (
            patch.object(svc, "SMTP_EMAIL", "noreply@jamaah.in"),
            patch.object(svc, "SMTP_PASSWORD", "secret"),
            patch("smtplib.SMTP", side_effect=smtplib.SMTPException("conn failed")),
        ):
            result = svc._send_via_smtp("user@example.com", "Subject", "<p>html</p>")
        assert result is False


# ---------------------------------------------------------------------------
# _send_email — routing logic
# ---------------------------------------------------------------------------

class TestSendEmail:
    def test_uses_resend_when_api_key_set(self):
        with (
            patch.object(svc, "RESEND_API_KEY", "re_test_key"),
            patch.object(svc, "_send_via_resend_api", return_value=True) as mock_resend,
            patch.object(svc, "_send_via_smtp", return_value=True) as mock_smtp,
        ):
            result = svc._send_email("to@example.com", "Subject", "<p>html</p>")

        assert result is True
        mock_resend.assert_called_once_with("to@example.com", "Subject", "<p>html</p>")
        mock_smtp.assert_not_called()

    def test_falls_back_to_smtp_when_no_api_key(self):
        with (
            patch.object(svc, "RESEND_API_KEY", ""),
            patch.object(svc, "_send_via_resend_api", return_value=True) as mock_resend,
            patch.object(svc, "_send_via_smtp", return_value=True) as mock_smtp,
        ):
            result = svc._send_email("to@example.com", "Subject", "<p>html</p>")

        assert result is True
        mock_resend.assert_not_called()
        mock_smtp.assert_called_once_with("to@example.com", "Subject", "<p>html</p>")


# ---------------------------------------------------------------------------
# send_otp_email
# ---------------------------------------------------------------------------

class TestSendOtpEmail:
    def test_sends_to_correct_address(self):
        with patch.object(svc, "_send_email", return_value=True) as mock_send:
            svc.send_otp_email("user@example.com", "123456")
        mock_send.assert_called_once()
        assert mock_send.call_args[0][0] == "user@example.com"

    def test_subject_contains_otp_code(self):
        with patch.object(svc, "_send_email", return_value=True) as mock_send:
            svc.send_otp_email("user@example.com", "654321")
        subject = mock_send.call_args[0][1]
        assert "654321" in subject

    def test_html_body_contains_otp_code(self):
        with patch.object(svc, "_send_email", return_value=True) as mock_send:
            svc.send_otp_email("user@example.com", "987654")
        html = mock_send.call_args[0][2]
        assert "987654" in html

    def test_returns_send_email_result(self):
        with patch.object(svc, "_send_email", return_value=False):
            assert svc.send_otp_email("user@example.com", "123456") is False
        with patch.object(svc, "_send_email", return_value=True):
            assert svc.send_otp_email("user@example.com", "123456") is True


# ---------------------------------------------------------------------------
# send_reset_email
# ---------------------------------------------------------------------------

class TestSendResetEmail:
    def test_sends_to_correct_address(self):
        with patch.object(svc, "_send_email", return_value=True) as mock_send:
            svc.send_reset_email("user@example.com", "111222")
        assert mock_send.call_args[0][0] == "user@example.com"

    def test_subject_contains_reset_code(self):
        with patch.object(svc, "_send_email", return_value=True) as mock_send:
            svc.send_reset_email("user@example.com", "333444")
        subject = mock_send.call_args[0][1]
        assert "333444" in subject

    def test_html_body_contains_reset_code(self):
        with patch.object(svc, "_send_email", return_value=True) as mock_send:
            svc.send_reset_email("user@example.com", "555666")
        html = mock_send.call_args[0][2]
        assert "555666" in html
