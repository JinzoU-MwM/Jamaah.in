Date: 2026-03-04

Implemented MVP for two roadmap items:
1) Manual Review Queue
2) OCR Quality Dashboard

Backend model additions:
- Added backend/app/models/ocr_review.py with:
  - OcrProcessingLog: per-file OCR telemetry
  - OcrReviewItem: manual review queue item (pending/approved/rejected)
- Updated backend/app/models/__init__.py exports for both models.

Documents router enhancements (backend/app/routers/documents_router.py):
- New endpoints:
  - GET /ocr/review-queue
    - Filters by status (default pending), pagination via limit/offset
    - Returns current user queue items
  - PATCH /ocr/review-queue/{item_id}
    - Action: approve|reject
    - Stores notes, reviewed_at, reviewed_by
  - GET /ocr/dashboard?days=7
    - Returns totals, success_rate, cache_hit_rate, avg_processing_ms, pending_review_count, error category breakdown
- Existing /process-documents/ flow now persists telemetry and queue items:
  - Stores OcrProcessingLog for each file_result
  - Creates OcrReviewItem when file_result.status is failed/partial

Tests:
- Added backend/tests/test_ocr_review_router.py
  - Auth requirement test for review queue
  - End-to-end flow test: mocked process -> queue creation -> decision update -> dashboard metrics
- Existing OCR status/shared tests still pass.
- Full backend suite now passes: 102 passed.

CI gate update:
- .github/workflows/deploy.yml backend smoke test now includes:
  - backend/tests/test_shared_router.py
  - backend/tests/test_ocr_status_router.py
  - backend/tests/test_ocr_review_router.py
