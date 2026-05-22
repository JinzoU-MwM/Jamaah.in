# Update 2026-03-04 — Frontend API Modularization + CI/CD Hardening

## Frontend service architecture refactor
- Refactored `frontend-svelte/src/lib/services/api.js` into a thin facade.
- Added shared core helper `frontend-svelte/src/lib/services/apiCore.js` for:
  - `API_URL`
  - `authHeaders`
  - `parseError`
- Split API implementation into domain modules under `frontend-svelte/src/lib/services/apiDomains/`:
  - `authSubscriptionApi.js`
  - `groupOpsApi.js`
  - `contentApi.js`
  - `paymentApi.js`
  - `documentExcelApi.js`
  - `supportTicketApi.js`
  - `registrationApi.js`
- `ApiService` now composes domain modules via `Object.assign(...)` and keeps backward compatibility for existing callers.

## Frontend quality/test setup
- Added Vitest and coverage dependency in frontend package:
  - `vitest`
  - `@vitest/coverage-v8`
- Updated scripts in `frontend-svelte/package.json`:
  - `test`: `vitest run`
  - `test:watch`: `vitest`
  - `test:all`: `npm run check && npm run test`
- Added Vitest config in `frontend-svelte/vite.config.js` (`test` section with node environment and coverage config).
- Added API domain tests:
  - `frontend-svelte/src/lib/services/apiDomains/apiDomains.test.js`
  - Includes success path, cache behavior, cache invalidation, and error mapping assertions.
- Current status from local runs:
  - `npm run test` passes (9 tests)
  - `npm run check` passes (0 errors, 0 warnings)
  - `npm run build` passes

## Super-admin/frontend cleanup done in same session
- Fixed Svelte syntax/type/a11y issues to get `svelte-check` clean.
- Updated components/pages including:
  - `SuperAdminDashboard.svelte`
  - `TicketList.svelte`
  - `TicketDetail.svelte`
  - `UserManagement.svelte`
  - `RegistrationLinkModal.svelte`
  - `OnboardingModal.svelte`
  - `Charts.svelte`

## Security-related adjustment
- Removed JWT query-string usage from document URL helper in frontend (`ApiService.getDocumentUrl` now returns clean path without `?token=...`).
- Removed unused token-query helper in backend `document_router.py`.

## Backend tests adjusted
- Updated `backend/tests/test_shared_router.py` mocks to align with current router behavior (`joinedload`/room relationship expectations).
- Local targeted backend test passes: `python -m pytest -q backend/tests/test_shared_router.py`.

## CI/CD hardening
- Reworked `.github/workflows/deploy.yml`:
  - Added `verify` job before deploy:
    - backend dependency install + smoke pytest
    - frontend `npm ci`, `npm run check`, `npm run test`, `npm run build`
  - `deploy` job now depends on `verify`.
  - VPS deploy script hardened with `set -euo pipefail`.
  - Uses `git pull --ff-only`.
  - Runs backend migration: `alembic upgrade head`.
  - Uses frontend `npm ci` + build.
  - Adds post-restart health check: `curl -fsS http://127.0.0.1:8000/health`.

## Notes for future sessions
- The working tree may still contain additional modified files beyond this refactor session; review `git status` before commit.
- Deploy workflow assumes:
  - `alembic` available in backend venv
  - SSH user can restart service via sudo non-interactively
  - backend health endpoint reachable at `127.0.0.1:8000/health`
