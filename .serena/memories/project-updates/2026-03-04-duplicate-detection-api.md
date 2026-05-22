Date: 2026-03-04

Continued implementation after OCR review/dashboard MVP:
Added Duplicate Detection API for group members.

Backend changes:
- Updated backend/app/routers/groups_router.py
  - Added helper `_duplicate_key_candidates(member)`
  - Added endpoint `GET /groups/{group_id}/duplicates`
    - Detects duplicate groups by normalized keys:
      - passport number
      - identity number
      - visa number
      - name + birth date composite
    - Returns duplicate_groups list with key type/value and full member rows (`to_dict_full`).

Tests:
- Added backend/tests/integration/test_group_duplicates.py
  - `test_group_duplicate_detection_by_passport_and_name_birth`
  - `test_group_duplicate_detection_empty`
- Adjusted test seeding strategy to insert members directly into DB (bypass upsert merge behavior) so duplicate detection path is exercised.

CI gate:
- Updated `.github/workflows/deploy.yml` backend smoke test to include:
  - `backend/tests/integration/test_group_duplicates.py`

Verification:
- New duplicate tests pass.
- Updated smoke gate command passes (12 passed).
- Full backend suite passes (104 passed).