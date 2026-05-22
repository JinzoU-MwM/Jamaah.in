Date: 2026-03-04

Completed warning cleanup and CI test stabilization for OCR status gate.

Changes made:
1) Deprecation cleanup (datetime.utcnow)
- backend/app/auth.py:
  - Added utc_now() helper using datetime.now(timezone.utc).replace(tzinfo=None)
  - Replaced utcnow usage in create_access_token, register_user, activate_pro
- backend/app/routers/shared_router.py:
  - Added utc_now() helper and replaced utcnow usage for shared link expiry set/check
- backend/tests/test_shared_router.py:
  - Added utc_now() helper and replaced utcnow in test fixtures
- backend/app/models/user.py:
  - Added utc_now() helper
  - Replaced Column defaults and trial/subscription active checks previously using datetime.utcnow

2) FastAPI startup deprecation cleanup
- backend/main.py:
  - Replaced @app.on_event("startup") with lifespan context manager
  - init_db() now runs in lifespan startup block

3) Pydantic v2 config deprecation cleanup
- backend/app/schemas.py:
  - Replaced inner class Config with model_config = ConfigDict(populate_by_name=True)

4) HTTP 422 constant deprecation cleanup in app/tests
- backend/app/error_handlers.py:
  - HTTP_422_UNPROCESSABLE_ENTITY -> HTTP_422_UNPROCESSABLE_CONTENT
- backend/tests/integration/test_auth_integration.py:
  - assertion constant updated to HTTP_422_UNPROCESSABLE_CONTENT

5) Test stability improvement for CI gate
- backend/tests/test_shared_router.py:
  - Moved require_pro_plan dependency override from module-global scope into setup_method
  - Added teardown pop for require_pro_plan override to avoid cross-file interference

Verification:
- Ran: python -m pytest -q backend/tests/test_shared_router.py backend/tests/test_ocr_status_router.py -W default
- Result: 8 passed, 2 warnings
- Remaining warnings are from FastAPI internals importing deprecated HTTP_422 constant (upstream package), not from project code paths modified above.