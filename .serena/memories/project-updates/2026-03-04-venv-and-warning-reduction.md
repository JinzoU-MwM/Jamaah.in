Date: 2026-03-04

Created project virtual environment and resolved dependency conflicts for Python 3.13.

Environment setup:
- Created .venv at project root.
- Installed backend requirements in .venv.

Dependency pin updates in backend/requirements.txt to support Python 3.13 wheels:
- fastapi==0.135.1
- pydantic==2.12.5
- psycopg2-binary==2.9.11 (was 2.9.9)
- numpy==2.1.3 (was numpy<2)
- opencv-python==4.10.0.84 (was 4.9.0.80)

Test fixes to keep suite green after auth/access and OCR pipeline evolution:
- tests/conftest.py:
  - auth_headers now uses sub=str(test_user.id) + email claim
  - test_user fixture now creates active trial Subscription by default
- tests/integration/test_auth_integration.py:
  - register success assertion updated to current API response (OTP flow, no immediate access_token)
- tests/integration/test_ocr_mocked.py:
  - switched mocked URL to regex
  - uses valid in-memory PNG payload
  - rate-limit assertion aligned with current endpoint behavior
- tests/test_operational.py:
  - rooming summary mock chain updated to scalar-count-based implementation

Internal deprecation cleanup:
- Replaced datetime.utcnow usage across model defaults in:
  - app/models/export_template.py
  - app/models/group.py
  - app/models/pending_member.py
  - app/models/operational.py
  - app/models/itinerary.py
  - app/models/support_ticket.py
  - app/models/registration.py
  - app/models/team.py
  - (user.py had been updated earlier)
- cleaner.py:
  - prefer model_dump() over dict() to remove Pydantic v2 deprecation warning.

Validation result in .venv:
- backend full suite: 100 passed
- warnings reduced to 11 (remaining warnings are third-party libraries: pytesseract + python-jose)