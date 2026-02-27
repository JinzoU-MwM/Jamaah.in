# Pricing Model Design - Jamaah.in

**Date:** 2026-02-27
**Status:** Implemented

---

## Plan Structure

| Plan | Price | Features | Limit |
|------|-------|----------|-------|
| **Free** | Rp 0 | Basic OCR, Edit results | **5 scans lifetime** |
| **Pro Trial** | Rp 0 | Full Pro features | **7 days, once per phone** |
| **Pro Monthly** | Rp 99.000 | Full features | 30 days |
| **Pro Annual** | Rp 990.000 | Full features + priority | 365 days (save 17%) |

---

## Anti-Abuse: Phone Verification

### Registration Flow
1. User enters email + password
2. Account created with FREE quota: 5 scans
3. User can optionally verify phone for Pro Trial

### Pro Trial Activation
1. User clicks "Coba Pro 7 Hari"
2. System checks: `phone_used_for_trial?`
   - YES → "Anda sudah pernah pakai trial"
   - NO → Send WhatsApp OTP
3. User verifies OTP → 7-day Pro Trial activated
4. Phone marked as `trial_used`

### WhatsApp OTP Provider
- **Provider:** Fonnte (Indonesian)
- **Cost:** ~Rp 200-300/message
- **API:** https://api.fonnte.com/send

---

## Database Schema

```python
# User model additions
phone_number: str (unique, indexed)
phone_verified: bool = False
phone_otp_code: str (nullable)
phone_otp_expires: datetime (nullable)
trial_used_at: datetime (nullable)  # When Pro Trial was activated
```

---

## API Endpoints

### Phone Verification
- `POST /auth/send-phone-otp` - Send OTP to WhatsApp
- `POST /auth/verify-phone` - Verify phone with OTP

### Subscription
- `GET /subscription/pricing` - Get pricing info
- `GET /subscription/trial-status` - Check if user can activate trial
- `POST /subscription/activate-trial` - Activate 7-day Pro Trial
- `POST /subscription/upgrade` - Upgrade to Pro (monthly/annual)

---

## Files Created/Modified

### Backend
- `backend/app/models/user.py` - Added phone fields
- `backend/app/services/whatsapp_service.py` - WhatsApp OTP service (NEW)
- `backend/app/routers/auth_router.py` - Phone verification endpoints
- `backend/app/routers/subscription_router.py` - Trial activation endpoints
- `backend/alembic/versions/add_phone_verification.py` - Migration (NEW)
- `backend/app/auth.py` - Updated FREE_USAGE_LIMIT to 5

### Frontend
- `frontend-svelte/src/lib/pages/LandingPage.svelte` - Updated pricing cards
- `frontend-svelte/src/lib/pages/ProfilePage.svelte` - Updated pricing display

### Config
- `.env.example` - Added FONNTE_TOKEN

---

## Next Steps

1. Run database migration:
   ```bash
   cd backend && alembic upgrade head
   ```

2. Add FONNTE_TOKEN to `.env`:
   ```
   FONNTE_TOKEN=your-fonnte-api-token
   ```

3. Get Fonnte token at: https://dash.fonnte.com
