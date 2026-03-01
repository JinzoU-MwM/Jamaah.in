# Jamaah.in — Product Information Document

> **Comprehensive product brief for brainstorming & planning sessions.**
> Last updated — 28 February 2026 (Landing page update & Trial Card).

---

## 1. Product Overview

**Jamaah.in** is an **All-in-One Lightweight ERP** for Indonesian Hajj & Umrah travel agencies ("Biro Perjalanan Haji & Umrah"). What started as an AI-powered OCR tool for Siskopatuh data entry has evolved into a complete operational platform covering document processing, group management, hotel room allocation, inventory/logistics, and tour leader coordination.

### The Problems It Solves
1. **Manual Data Entry** — Travel agencies manually type data from hundreds of identity documents into Excel. Slow, error-prone, repetitive.
2. **Chaotic Room Allocation** — Hotel rooming for 40+ pilgrims done manually on paper/WhatsApp. Gender separation and family grouping rules are easily broken.
3. **Poor Tour Leader Coordination** — Mutawwif (tour leaders) in Saudi Arabia get messy WhatsApp forwards with pilgrim data. No structured checklist.
4. **No Operational Visibility** — Agency owners have no dashboard to track equipment distribution, room assignments, or trip readiness.

### The Solution
- **AI-Powered OCR**: Upload document photos → AI extracts all fields → review/edit → export as Siskopatuh-compatible Excel
- **Smart Rooming**: Auto-assign pilgrims to hotel rooms by gender/family with drag-and-drop adjustments
- **Mobile Manifest**: PIN-protected shareable manifest for tour leaders with offline attendance checklist
- **Inventory Tracking**: Equipment forecast and fulfillment tracking per group

---

## 2. Target Users

| User Type | Description |
|-----------|-------------|
| **Travel Agent Staff** | Data-entry operators who process pilgrim documents daily |
| **Travel Agency Owners** | Business owners who need faster turnaround, fewer errors, and operational visibility |
| **Operations Managers** | Staff handling hotel rooming, equipment logistics, and trip coordination |
| **Tour Leaders (Mutawwif)** | Guides in Saudi Arabia who need a mobile pilgrim manifest with attendance tracking |
| **Freelance Umrah Handlers** | Independent operators managing small groups |

### Market Context
- Indonesia is the world's largest Hajj-sending country (~220,000 pilgrims/year)
- Thousands of licensed travel agencies ("PPIU") must submit data to Siskopatuh
- Most agencies still use manual data entry into Excel templates

---

## 3. Core Features

### 3.1 AI-Powered Document OCR

| Capability | Details |
|-----------|---------|
| **Supported Documents** | KTP (Indonesian ID Card), Passport, Visa |
| **AI Engine** | Google Gemini 2.5 Flash (Vision API) |
| **Fallback Engine** | Tesseract OCR + OpenCV (local, for when Gemini is unavailable) |
| **Input Formats** | JPEG, PNG, WebP, PDF (multi-page) |
| **Batch Processing** | Up to 50 files per upload |
| **Max File Size** | 10MB per file |
| **Extracted Fields** | 32 fields matching Siskopatuh Excel columns |

### 3.2 Data Cleaning & Intelligent Merging

| Feature | Details |
|---------|---------|
| **Name Cleaning** | Blacklist filter (removes "PROVINSI", "KABUPATEN" etc. misreads), sanitization, minimum length check |
| **Date Standardization** | Handles Indonesian months ("MEI", "AGUSTUS"), DD-MM-YYYY ↔ YYYY-MM-DD, OCR typo correction (l→1, O→0) |
| **Fuzzy Merge** | Automatically merges KTP + Passport + Visa records for the same person using `SequenceMatcher` (≥80% name similarity) |
| **Field Validation** | NIK (16 digits), passport number (letter + 6-7 digits), visa number, date formats, citizenship (WNI/WNA) |
| **Validation Warnings** | Non-blocking warnings shown in preview — user can fix before exporting |

### 3.6 Group Management (Jamaah Groups)

Organize pilgrims into named groups/trips (e.g., "UMROH 12 Feb 2026"):

| Feature | Details |
|---------|---------|
| **CRUD Operations** | Create, read, update, delete groups |
| **Member Management** | Add members (from OCR results or manual), edit, delete individual members |
| **Data Model** | 32 columns per member matching Siskopatuh format |
| **Free Tier Limit** | Max 2 groups |
| **Pro Tier** | Unlimited groups |

### 3.6b Auto-Rooming (Pro Feature)

Automatic hotel room allocation for pilgrim groups:

| Feature | Details |
|---------|---------|
| **Auto-Generate** | Algorithm assigns pilgrims to rooms by gender and family relationships |
| **Room Types** | Quad (4), Triple (3), Double (2) — configurable capacity |
| **Gender Separation** | Male-only, Female-only, and Family rooms |
| **Drag-and-Drop** | Optimistic UI — members move between rooms instantly, API syncs in background |
| **Manual Room CRUD** | "+" button to add rooms manually, trash icon to delete rooms |
| **Auto-Delete Empty Rooms** | Backend auto-deletes rooms when last member is removed |
| **Rollback on Error** | If API call fails, UI reverts to previous state |
| **Summary Stats** | Total members, assigned, unassigned, room count (uses SQL aggregates) |
| **PDF Export** | Printable rooming list with room grouping, member names, passport numbers |
| **Reset** | Clear all rooms and assignments with confirmation dialog |

### 3.11 Mutawwif Mobile Manifest

| Feature | Details |
|---------|---------|
| **Public Manifest** | Shareable, PIN-protected mobile view of a group's jamaah for Tour Leaders (Mutawwif) |
| **Privacy First** | Only shows essential operational data (Name, Passport, Room, Baju Size, Equipment). Hides NIK and addresses. |
| **Offline Checklist** | LocalStorage-backed attendance checklist for Mutawwif to mark present pilgrims |
| **WhatsApp Integration** | Direct WhatsApp messaging button for each pilgrim |
| **Offline Mode** (P2) | Caches manifest data to localStorage, fallback when offline, shows "📡 Offline" badge |
| **Pro Feature** | Only admin users with an active Pro subscription can generate and manage share links |

### 3.7 User Authentication & Authorization

| Feature | Details |
|---------|---------|
| **Registration** | Email + password, with 6-digit OTP email verification |
| **Login** | JWT-based (access token, 7-day expiry) |
| **Password Reset** | 6-digit code via email, 15-min expiry |
| **Email Service** | Brevo HTTP API (primary) + SMTP fallback |
| **Non-blocking Emails** | Email sending runs in background threads to prevent timeouts |
| **Password Hashing** | bcrypt |
| **Admin Role** | `is_admin` flag, `require_admin` dependency for admin-only endpoints |

### 3.8 Subscription & Payment System

#### Plans

| Feature | Free (Trial) | Pro |
|---------|-------------|-----|
| **Duration** | 7-day trial | 30 days per payment |
| **Scan Limit** | 5 total scans (after trial) | Unlimited |
| **Groups** | 2 groups | Unlimited |
| **Excel Export** | ✅ | ✅ |
| **Price** | Free | Rp 80,000/month or Rp 800,000/year (~$5/$50 USD) |

#### Payment Gateway: Pakasir
| Feature | Details |
|---------|---------|
| **Gateway** | [Pakasir](https://pakasir.com) — Indonesian payment gateway |
| **Payment Methods** | QRIS, Virtual Account, PayPal |
| **Flow** | Create order → Redirect to Pakasir → Webhook callback → Verify & activate Pro |
| **Redirect URL** | Returns to dashboard after payment with `#dashboard` hash |
| **Webhook Endpoint** | `POST /payment/webhook` — receives payment status from Pakasir |
| **Status Polling** | Frontend polls `GET /payment/status/{order_id}` every 5 seconds while payment is pending |

---

## 4. Tech Stack

### 4.1 Backend

| Layer | Technology | Version |
|-------|-----------|---------|
| **Framework** | FastAPI | 0.115.0 |
| **Server** | Uvicorn (ASGI) | 0.32.0 |
| **Language** | Python 3 | — |
| **ORM** | SQLAlchemy | ≥2.0.0 |
| **Database** | PostgreSQL (Supabase-hosted) | — |
| **DB Driver** | psycopg2-binary | 2.9.9 |
| **Validation** | Pydantic | 2.10.3 |
| **Auth (JWT)** | python-jose[cryptography] | 3.3.0 |
| **Password Hashing** | bcrypt | 4.1.2 |
| **Rate Limiting** | slowapi | — |
| **Migrations** | Alembic | 1.18.4 |
| **File Upload** | python-multipart | 0.0.12 |

#### AI & OCR Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Primary OCR** | Google Gemini 2.5 Flash (Vision API) | — |
| **Fallback OCR** | Tesseract (via pytesseract) | 0.3.10 |
| **Image Processing** | OpenCV (opencv-python) | 4.9.0.80 |
| **Image Handling** | Pillow (PIL) | 11.0.0 |
| **PDF Processing** | pdf2image | 1.17.0 |

#### External Services

| Service | Purpose | Provider |
|---------|---------|----------|
| **OCR AI** | Document text extraction | Google Gemini API |
| **Email** | OTP & password reset | Brevo (Sendinblue) HTTP API + SMTP |
| **Payment** | Subscription payments | Pakasir |
| **Database** | PostgreSQL hosting | Supabase |

### 4.2 Frontend

| Layer | Technology | Version |
|-------|-----------|---------|
| **Framework** | Svelte 5 | 5.43.8 |
| **Build Tool** | Vite | 7.2.4 |
| **CSS** | TailwindCSS + Custom CSS | 3.4.0 |
| **Icons** | Lucide Svelte | 0.563.0 |
| **PostCSS** | autoprefixer + postcss | 8.5.6 |
| **State Management** | Svelte 5 Runes ($state, $props, $derived) | — |

---

## 5. Data Model

### 5.1 Database Schema (PostgreSQL)

- **users** — id, email, name, password_hash, is_active, is_admin, created_at, avatar_color, notify_usage_limit, notify_expiry, email_verified, otp_code, otp_expires, reset_code, reset_expires
- **subscriptions** — id, user_id, plan, status, trial_start, trial_end, subscribed_at, expires_at, payment_ref
- **usage_logs** — id, user_id, action, count, created_at
- **payments** — id, user_id, order_id, amount, status, pakasir_ref, created_at, paid_at
- **groups** — id, user_id, org_id, name, description, shared_token, shared_pin, shared_expires_at, version, created_at, updated_at
- **rooms** — id, group_id, room_number, room_type, gender_type, capacity, is_auto_assigned, created_at
- **group_members** — id, group_id, 32 columns matching Siskopatuh format

### 5.2 The 32-Column Data Structure (Siskopatuh)

1. title, 2. nama, 3. nama_ayah, 4. jenis_identitas, 5. no_identitas, 6. nama_paspor, 7. no_paspor, 8. tanggal_paspor, 9. kota_paspor, 10. tempat_lahir, 11. tanggal_lahir, 12. alamat, 13. provinsi, 14. kabupaten, 15. kecamatan, 16. kelurahan, 17. no_telepon, 18. no_hp, 19. kewarganegaraan, 20. status_pernikahan, 21. pendidikan, 22. pekerjaan, 23. provider_visa, 24. no_visa, 25. tanggal_visa, 26. tanggal_visa_akhir, 27. asuransi, 28. no_polis, 29. tanggal_input_polis, 30. tanggal_awal_polis, 31. tanggal_akhir_polis, 32. no_bpjs

---

## 6. Key Design Decisions

1. **Gemini Vision over Tesseract**: Gemini provides dramatically better accuracy for Indonesian documents
2. **Direct Image-to-JSON**: Sends raw images to Gemini with structured prompt, gets JSON back
3. **Fuzzy Merge**: Auto-merges KTP + Passport + Visa for same person using name similarity
4. **32-Column Standard**: Data schema exactly mirrors Siskopatuh's Excel format
5. **SPA with State-based Routing**: Simple `currentPage` state variable
6. **Non-blocking Emails**: Email sending runs in background threads
7. **Webhook + Polling**: Payment verification uses both webhook and status polling
8. **Database Performance**: Eager loading, SQL COUNT subqueries, connection pool tuning, GZIP compression
9. **Optimistic UI**: Drag-and-drop updates frontend instantly with rollback on API failure
10. **Frontend Response Cache**: In-memory cache with TTL prevents redundant API calls
11. **PWA-First Design**: Service worker with cache-first for static, network-first for API
12. **Alembic Migrations**: Version-controlled database schema changes
13. **Optimistic Locking**: `version` column on Group prevents concurrent edit conflicts
14. **Smart Notifications**: On-the-fly alert generation (no stored notifications table)

---

## 7. Pricing Model

| Plan | Price | Limits | Duration |
|------|-------|--------|----------|
| **Free Trial** | Rp 0 | 50 scans, 2 groups | 7 days |
| **Pro** | Rp 40,000/mo | Unlimited scans, unlimited groups | 30 days |

---

## 8. File Structure

```
backend/
├── main.py                          # FastAPI app entry point
├── app/
│   ├── auth.py, config.py, database.py, mappers.py, schemas.py
│   ├── models/ (user.py, group.py, team.py, itinerary.py, operational.py)
│   ├── routers/ (auth, documents, excel, groups, payment, subscription, admin, rooming, inventory, shared, team, analytics, itinerary, document, notification, export, registration)
│   └── services/ (gemini_ocr, ocr_engine, document_processor, cleaner, validators, parser, parsers/, excel, email_service, payment_service, cache, progress, rooming_service, inventory_service)
frontend-svelte/
├── src/
│   ├── App.svelte                   # Root component + routing
│   └── lib/
│       ├── pages/ (LandingPage, Login, Dashboard, ScannerPage, ItineraryPage, ProfilePage, RoomingPage, InventoryPage, MutawwifManifest, PublicRegistrationPage)
│       ├── components/ (FileUpload, TableResult, GroupSelector, NotificationBell, SubscriptionBanner, BrandLogo, Sidebar, RegistrationLinkModal)
│       └── services/api.js          # API client + in-memory cache
```

---

*Document generated from codebase analysis — Jamaah.in v5.0 (P3), February 2026*
