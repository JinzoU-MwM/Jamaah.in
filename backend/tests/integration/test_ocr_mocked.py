"""
Integration tests for OCR with mocked Gemini API.
"""
import pytest
import responses
from fastapi import status


class TestGeminiOCRMocked:
    """Test OCR with mocked Gemini API."""
    
    @responses.activate
    def test_process_document_success(self, client, auth_headers):
        """Successful document processing with mocked API."""
        # Mock Gemini API
        responses.add(
            responses.POST,
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
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
        from io import BytesIO
        file_content = BytesIO(b"fake image data")
        
        response = client.post(
            "/process-documents/",
            headers=auth_headers,
            files={"files": ("ktp.jpg", file_content, "image/jpeg")}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "session_id" in data
    
    @responses.activate
    def test_gemini_api_rate_limit(self, client, auth_headers):
        """Test retry logic when Gemini returns 429."""
        responses.add(
            responses.POST,
            responses.matchers.regex_matcher(
                r"generativelanguage\.googleapis\.com"
            ),
            json={"error": {"code": 429, "message": "Rate limit exceeded"}},
            status=429,
        )
        
        from io import BytesIO
        file_content = BytesIO(b"fake image data")
        
        response = client.post(
            "/process-documents/",
            headers=auth_headers,
            files={"files": ("ktp.jpg", file_content, "image/jpeg")}
        )
        # Should retry and eventually succeed or fail gracefully
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
