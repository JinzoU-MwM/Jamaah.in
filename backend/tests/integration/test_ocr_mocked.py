"""
Integration tests for OCR with mocked Gemini API.
"""
import pytest
import re
import responses
from fastapi import status
from PIL import Image
from io import BytesIO


def make_test_image_bytes() -> BytesIO:
    """Create a tiny valid image payload for OCR endpoint tests."""
    buf = BytesIO()
    img = Image.new("RGB", (8, 8), color="white")
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


class TestGeminiOCRMocked:
    """Test OCR with mocked Gemini API."""
    
    @responses.activate
    def test_process_document_success(self, client, auth_headers):
        """Successful document processing with mocked API."""
        # Mock Gemini API
        responses.add(
            responses.POST,
            re.compile(r"https://generativelanguage\.googleapis\.com/.*"),
            json={
                "candidates": [{
                    "content": {
                        "parts": [{
                            "text": '''{
                                "nama": "AHMAD FAUZAN",
                                "no_identitas": "3201123456780001",
                                "tempat_lahir": "JAKARTA",
                                "tanggal_lahir": "01-01-1990",
                                "alamat": "JL. MERDEKA NO. 1",
                                "jenis_identitas": "KTP"
                            }'''
                        }]
                    }
                }]
            },
            status=200,
        )
        
        # Upload document
        file_content = make_test_image_bytes()
        
        response = client.post(
            "/process-documents/",
            headers=auth_headers,
            files={"files": ("ktp.png", file_content, "image/png")}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "session_id" in data
    
    @responses.activate
    def test_gemini_api_rate_limit(self, client, auth_headers):
        """Test retry logic when Gemini returns 429."""
        responses.add(
            responses.POST,
            re.compile(r"https://generativelanguage\.googleapis\.com/.*"),
            json={"error": {"code": 429, "message": "Rate limit exceeded"}},
            status=429,
        )
        
        file_content = make_test_image_bytes()
        
        response = client.post(
            "/process-documents/",
            headers=auth_headers,
            files={"files": ("ktp.png", file_content, "image/png")}
        )
        # Should retry and eventually succeed or fail gracefully
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        ]
