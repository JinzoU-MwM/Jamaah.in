Date: 2026-03-04

Implemented Audit Log MVP and integrated with existing workflows.

New model/service:
- Added backend/app/models/audit_log.py
  - AuditLog table with user_id, action, resource_type, resource_id, details_json, created_at
- Added backend/app/services/audit.py
  - helper: record_audit_event(db, user_id, action, resource_type, resource_id, details)
- Exported AuditLog in backend/app/models/__init__.py

Router integrations:
1) auth_router
- Added GET /auth/audit
  - Returns current user audit logs (limit/offset)

2) groups_router
- Added audit logging for:
  - add_members -> action: group_members_upsert
  - update_member -> action: group_member_update
  - delete_member -> action: group_member_delete

3) documents_router
- Added audit logging for OCR review decision:
  - action: ocr_review_decision on PATCH /ocr/review-queue/{item_id}

Tests:
- Added backend/tests/integration/test_audit_log.py
  - Verifies audit entries for member upsert/update/delete flow
- Existing test suites still pass.

CI smoke gate update:
- .github/workflows/deploy.yml backend smoke test now includes:
  - backend/tests/integration/test_audit_log.py

Verification:
- Updated smoke command: 13 passed
- Full backend suite: 105 passed
