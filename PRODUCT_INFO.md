# Jamaah.in — Product Information Document

> **Comprehensive product brief for brainstorming & planning sessions.**
> Last updated � 04 March 2026 (OCR reliability, KK enrichment, and observability update).

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
| **Supported Documents** | KTP/KK (Indonesian ID & Family Card), Passport, Visa |
| **AI Engine** | Google Gemini 2.5 Flash (Vision API) |
| **Fallback Engine** | Tesseract OCR + OpenCV (local, for when Gemini is unavailable) |
| **Input Formats** | JPEG, PNG, WebP, PDF (multi-page) |
| **Batch Processing** | Up to 50 files per upload |
| **Max File Size** | 10MB per file |
| **Extracted Fields** | 32 fields matching Siskopatuh Excel columns |

#### OCR Pipeline
```
Upload → Validate Files → Cache Check → Gemini Vision OCR
→ Structured JSON Extraction → Data Cleaning & Sanitization
→ Fuzzy Merge (KTP/KK+Passport+Visa for same person)
→ Field Validation → Preview Table
```

#### Key Technical Details
- **Direct Image-to-JSON**: Sends raw image bytes to Gemini with a structured extraction prompt — no intermediate text step
- **Concurrent Processing**: Uses `ThreadPoolExecutor(max_workers=15)` with `asyncio.Semaphore` for rate-limiting Gemini API calls
- **Auto-Retry**: Categorized retry policy for timeout/network/429/5xx errors (up to 3 retries, longer cool-down for 429)
- **OCR Result Caching**: MD5 hash-based cache to avoid re-processing identical images
- **PDF Support**: `pdf2image` converts multi-page PDFs into individual images
- **Image Preprocessing**: OpenCV-based card detection, auto-rotation (bruteforce 4 orientations), adaptive thresholding
- **Per-file Telemetry**: Logs include `session_id`, `doc_type`, `cache_hit`, `elapsed_ms`, status, and batch summary metrics
- **Per-file Error Categories**: Failed files are classified (`invalid_file_type`, `file_too_large`, `timeout`, `rate_limit`, `network_error`, etc.)

### 3.2 Data Cleaning & Intelligent Merging

| Feature | Details |
|---------|---------|
| **Name Cleaning** | Blacklist filter (removes "PROVINSI", "KABUPATEN" etc. misreads), sanitization, minimum length check |
| **Date Standardization** | Handles Indonesian months ("MEI", "AGUSTUS"), DD-MM-YYYY ↔ YYYY-MM-DD, OCR typo correction (l→1, O→0) |
| **Fuzzy Merge** | Automatically merges KTP/KK + Passport + Visa records for the same person using `SequenceMatcher` (≥80% name similarity) |
| **Identity Priority** | If passport number exists, `jenis_identitas` and `no_identitas` are prioritized from passport |
| **KK Family Enrichment** | For matched KK members: address is standardized from KK, father name is filled via per-member mapping (`kk_member_fathers`) |
| **Auto Title Assignment** | Title is auto-derived as `TUAN/NONA/NYONYA` using birth date, gender, and marital status |
| **Field Validation** | NIK (16 digits), passport number (letter + 6-7 digits), visa number, date formats, citizenship (WNI/WNA) |
| **Validation Warnings** | Non-blocking warnings shown in preview � includes low-confidence OCR field warnings |
| **Field Provenance & Confidence** | Internal metadata tracks `field->source` and `field->confidence` for explainable merge/review |

### 3.3 Document-Specific Parsers
Specialized regex-based parsers for each document type:

- **KTP Parser** (`ktp_parser.py`, 9.4KB): Extracts NIK, nama, tempat/tanggal lahir, alamat, RT/RW, kelurahan, kecamatan, kabupaten, provinsi, agama, status pernikahan, pekerjaan, pendidikan, kewarganegaraan
- **Passport Parser** (`passport_parser.py`, 18.7KB): Extracts nama, no paspor, tempat/tanggal lahir, tanggal terbit, kota terbit, nama ayah
- **Visa Parser** (`visa_parser.py`, 2.1KB): Extracts no visa, tanggal visa, tanggal akhir visa, provider visa

### 3.4 Interactive Data Preview & Editing

- **Table UI**: Editable table with all 32 Siskopatuh columns
- **Inline Editing**: Click any cell to edit directly
- **Validation Indicators**: Warning badges on fields with validation issues
- **Row Management**: Add, delete, and reorder rows
- **Real-time Progress**: Server-Sent Events (SSE) for live upload/processing progress
- **Per-file Status Detail**: Includes processing duration, cache status, provenance summary, and categorized errors
- **Bulk Edit** (P2): Multi-select checkboxes (shift-click range), bulk edit toolbar (column picker → value → apply), find & replace with match highlighting, delete selected. Keyboard: Ctrl+A, Ctrl+F, Esc

### 3.5 Excel Export

| Feature | Details |
|---------|---------|
| **Format** | `.xlsm` (Excel with macros, Siskopatuh-compatible) |
| **Template Support** | Can load existing `.xlsm` template and append data |
| **Column Mapping** | Exact 15-column Siskopatuh format (No Identitas, Nama, Tempat Lahir, Tanggal Lahir, Alamat, Provinsi, Kabupaten, Kecamatan, Kelurahan, No Paspor, Tanggal Paspor, Kota Paspor, No Visa, Jenis Identitas, Kewarganegaraan) |
| **Date Conversion** | Auto-converts DD-MM-YYYY → YYYY-MM-DD for Excel |

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

### 3.12 Dashboard Analytics (P1)

| Feature | Details |
|---------|---------|
| **Stat Cards** | Total groups, total jamaah, equipment fulfillment rate, passport expiry alerts |
| **Sparkline** | SVG trend of group creation over recent months |
| **Gender Breakdown** | Visual bar chart of male/female ratio |
| **Recent Groups** | Quick-access list of recently updated groups |
| **Backend** | `analytics_router.py` with 8 aggregate metrics |

### 3.13 Itinerary Manager (P1)

| Feature | Details |
|---------|---------|
| **CRUD** | Create, update, delete schedule items per group |
| **Timeline View** | Day-by-day grouped timeline with color-coded categories |
| **Categories** | Flight ✈️, Hotel 🏨, Transport 🚌, Activity 📍 |
| **Pro Feature** | "Jadwal" sidebar nav, only visible for Pro users |
| **Backend** | `Itinerary` model + `itinerary_router.py` |

### 3.14 Document Templates (P3)

| Feature | Details |
|---------|---------|
| **Rooming List** | Printable HTML grouped by room — member names, passport, gender |
| **Group Manifest** | Full member list with passport, DOB, phone, baju size |
| **Print** | Opens in new tab with "🖨️ Cetak" button, clean print-optimized CSS |
| **Backend** | `document_router.py` — returns HTMLResponse |

### 3.15 Smart Notifications (P3)

| Feature | Details |
|---------|---------|
| **Notification Bell** | Bell icon in sidebar with red badge count |
| **Passport Expiry** | Alerts at 90/30/0 days before passport expiration |
| **Subscription Expiry** | Warning when Pro expires within 7 days |
| **Incomplete Data** | Flags groups with members missing critical fields |
| **Empty Groups** | Alerts for groups with 0 members |
| **Auto-refresh** | Refreshes every 5 minutes |
| **Backend** | `notification_router.py` — generates alerts on-the-fly |

### 3.16 PWA / Offline Mode (P2)

| Feature | Details |
|---------|---------|
| **Manifest** | `manifest.json` with standalone display, emerald theme |
| **Service Worker** | Cache-first for static assets, network-first with fallback for API |
| **Install Prompt** | Add to Home Screen on mobile |
| **Offline Caching** | MutawwifManifest caches to localStorage |

### 3.17 Optimistic Locking (P3)

| Feature | Details |
|---------|---------|
| **Version Column** | `version` field on Group model, increments on save |
| **Conflict Detection** | Backend returns 409 on version mismatch |
| **Use Case** | Prevents silent overwrites when multiple team members edit same group |

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

#### Trial Awareness
| Feature | Details |
|---------|---------|
| **Sidebar Trial Card** | Purple gradient card ("🎁 FREE Trial 7 Hari!") shown to users who haven't activated trial |
| **Visibility** | Only shown when `trialAvailable=true` (user hasn't used trial yet) |
| **CTA** | "Aktifkan Sekarang" button opens UpgradeModal with trial flow |
| **Post-Trial** | Card replaced with regular Pro CTA (Rp80rb/bulan) after trial activated |

#### Payment Gateway: Pakasir
| Feature | Details |
|---------|---------|
| **Gateway** | [Pakasir](https://pakasir.com) — Indonesian payment gateway |
| **Payment Methods** | QRIS, Virtual Account, PayPal |
| **Flow** | Create order → Redirect to Pakasir → Webhook callback → Verify & activate Pro |
| **Redirect URL** | Returns to dashboard after payment with `#dashboard` hash |
| **Webhook Endpoint** | `POST /payment/webhook` — receives payment status from Pakasir |
| **Status Polling** | Frontend polls `GET /payment/status/{order_id}` every 5 seconds while payment is pending |
| **Verification** | Double verification: webhook + API check via `GET https://api.pakasir.com/transaction/{api_key}/{order_id}` |

### 3.9 Admin Panel

| Feature | Details |
|---------|---------|
| **User Management** | List, search, paginate; activate/deactivate; grant/revoke admin |
| **Plan Management** | Manually set user plan (free/pro) |
| **System Stats** | Total users, active users, admin users, pro users, free users, total scans |
| **User Deletion** | Permanently delete user and all associated data |

### 3.10 Profile Page

| Feature | Details |
|---------|---------|
| **Access** | Via clicking user info in Sidebar (dedicated "Profil" nav removed) |
| **User Info** | Name, email, join date, avatar color picker |
| **Subscription Info** | Current plan, trial/subscription dates, usage stats |
| **Edit Profile** | Change name, save notification preferences |
| **Change Password** | Current + new password flow |
| **Activity Log** | Recent scan activity with timestamps |
| **Dark Mode Toggle** | Theme switching |
| **Delete Account** | Password confirmation required |
| **Upgrade to Pro** | Inline payment modal with Pakasir integration |
| **Layout** | Two-column grid on desktop, single column on mobile |

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

#### Data Processing Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **DataFrames** | pandas | 2.2.3 |
| **Excel I/O** | openpyxl | 3.1.5 |
| **Date Parsing** | python-dateutil | 2.9.0 |
| **Fuzzy Matching** | difflib.SequenceMatcher | (stdlib) |

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

#### Frontend Pages

| Page | File | Description |
|------|------|-------------|
| **Landing Page** | `LandingPage.svelte` (24KB) | Marketing page with features, pricing, CTA |
| **Login/Register** | `Login.svelte` (22KB) | Auth forms with OTP verification, forgot password |
| **Dashboard** | `Dashboard.svelte` (16KB) | Main work area (gradient header, card layout): file upload, OCR results table, group selector |
| **Profile** | `ProfilePage.svelte` (67KB) | User profile, subscription, settings, payment |
| **Inventory** | `InventoryPage.svelte` | Inventory/logistics management (Pro) |
| **Auto-Rooming** | `RoomingPage.svelte` | Hotel room allocation with drag-and-drop (Pro) |

#### Frontend Components

| Component | File | Description |
|-----------|------|-------------|
| **FileUpload** | `FileUpload.svelte` (10KB) | Drag-and-drop file upload with progress |
| **TableResult** | `TableResult.svelte` (16KB) | Editable data table with 32 columns |
| **GroupSelector** | `GroupSelector.svelte` (10KB) | Group picker with create/select/save |
| **MutawwifManifest** | `MutawwifManifest.svelte` (16KB) | Public mobile-first PIN-protected manifest view |
| **Sidebar** | `Sidebar.svelte` (8KB) | Collapsible navigation, clickable user info, Trial Card for free users |
| **SubscriptionBanner** | `SubscriptionBanner.svelte` (7KB) | Trial/pro status banner |
| **BrandLogo** | `BrandLogo.svelte` (1KB) | SVG brand logo component |

#### API Service Layer
`api.js` — centralized API client with:
- JWT token management (auto-attach Authorization header)
- All backend endpoints wrapped as async methods
- Error handling and response parsing
- **In-memory response cache** with TTL (subscription status: 60s, group lists: 30s, group detail: 30s)
- Cache auto-invalidation on mutations (create/delete group, add/remove members)

---

## 5. Data Model

### 5.1 Database Schema (PostgreSQL)

```mermaid
erDiagram
    users ||--o| subscriptions : has
    users ||--o{ usage_logs : has
    users ||--o{ groups : owns
    users ||--o{ payments : makes
    groups ||--o{ group_members : contains

    users {
        int id PK
        string email UK
        string name
        string password_hash
        bool is_active
        bool is_admin
        datetime created_at
        string avatar_color
        bool notify_usage_limit
        bool notify_expiry
        bool email_verified
        string otp_code
        datetime otp_expires
        string reset_code
        datetime reset_expires
    }

    subscriptions {
        int id PK
        int user_id FK
        string plan
        string status
        datetime trial_start
        datetime trial_end
        datetime subscribed_at
        datetime expires_at
        string payment_ref
    }

    usage_logs {
        int id PK
        int user_id FK
        string action
        int count
        datetime created_at
    }

    payments {
        int id PK
        int user_id FK
        string order_id UK
        int amount
        string status
        string pakasir_ref
        datetime created_at
        datetime paid_at
    }

    groups {
        int id PK
        int user_id FK
        int org_id FK
        string name
        text description
        string shared_token UK
        string shared_pin
        datetime shared_expires_at
        int version
        datetime created_at
        datetime updated_at
    }

    groups ||--o{ rooms : has
    rooms ||--o{ group_members : contains

    rooms {
        int id PK
        int group_id FK
        string room_number
        string room_type
        string gender_type
        int capacity
        bool is_auto_assigned
        datetime created_at
    }

    group_members {
        int id PK
        int group_id FK
        string title
        string nama
        string nama_ayah
        string no_identitas
        string no_paspor
        string no_visa
        string_32_more_columns "..."
    }
```

### 5.2 The 32-Column Data Structure (Siskopatuh)

Every `GroupMember` row and `ExtractedDataItem` contains these 32 fields:

| # | Field | Description |
|---|-------|-------------|
| 1 | `title` | Mr/Mrs/Ms |
| 2 | `nama` | Full name (from KTP/KK/Passport) |
| 3 | `nama_ayah` | Father's name |
| 4 | `jenis_identitas` | ID type: KTP (incl. KK) or PASPOR |
| 5 | `no_identitas` | NIK (16 digits) |
| 6 | `nama_paspor` | Name as on passport |
| 7 | `no_paspor` | Passport number |
| 8 | `tanggal_paspor` | Passport issue date |
| 9 | `kota_paspor` | Passport issue city |
| 10 | `tempat_lahir` | Place of birth |
| 11 | `tanggal_lahir` | Date of birth |
| 12 | `alamat` | Full address |
| 13 | `provinsi` | Province |
| 14 | `kabupaten` | City/Regency |
| 15 | `kecamatan` | Sub-district |
| 16 | `kelurahan` | Village |
| 17 | `no_telepon` | Phone number |
| 18 | `no_hp` | Mobile number |
| 19 | `kewarganegaraan` | Nationality (WNI/WNA) |
| 20 | `status_pernikahan` | Marital status |
| 21 | `pendidikan` | Education level |
| 22 | `pekerjaan` | Occupation |
| 23 | `provider_visa` | Visa provider/embassy |
| 24 | `no_visa` | Visa number |
| 25 | `tanggal_visa` | Visa start date |
| 26 | `tanggal_visa_akhir` | Visa expiry date |
| 27 | `asuransi` | Insurance provider |
| 28 | `no_polis` | Insurance policy number |
| 29 | `tanggal_input_polis` | Policy input date |
| 30 | `tanggal_awal_polis` | Policy start date |
| 31 | `tanggal_akhir_polis` | Policy end date |
| 32 | `no_bpjs` | BPJS (social insurance) number |

---

## 6. API Surface

### 6.1 Authentication (`/auth/*`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | — | Register new user, sends OTP |
| POST | `/auth/login` | — | Login, returns JWT |
| POST | `/auth/verify-otp` | — | Verify email with OTP code |
| POST | `/auth/resend-otp` | — | Resend OTP to email |
| POST | `/auth/forgot-password` | — | Send password reset code |
| POST | `/auth/reset-password` | — | Reset password with code |
| GET | `/auth/me` | JWT | Get current user profile |
| PUT | `/auth/me` | JWT | Update profile (name, avatar, notifications) |
| PUT | `/auth/change-password` | JWT | Change password |
| DELETE | `/auth/me` | JWT | Delete own account |
| GET | `/auth/subscription` | JWT | Get subscription status |
| GET | `/auth/activity` | JWT | Get recent activity log |

### 6.2 Documents (`/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/process-documents/` | JWT | Upload & OCR batch of files (rate: 10/min) |
| GET | `/progress/{session_id}` | — | SSE stream for processing progress |

### 6.3 Excel Export (`/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/generate-excel/` | JWT | Generate `.xlsm` file from extracted data |

### 6.4 Groups (`/groups/*`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/groups/` | JWT | List user's groups |
| POST | `/groups/` | JWT | Create new group |
| GET | `/groups/{id}` | JWT | Get group with members |
| PUT | `/groups/{id}` | JWT | Update group name/description |
| DELETE | `/groups/{id}` | JWT | Delete group (cascade members) |
| POST | `/groups/{id}/members` | JWT | Add members to group |
| PUT | `/groups/{id}/members/{mid}` | JWT | Update a member |
| DELETE | `/groups/{id}/members/{mid}` | JWT | Delete a member |

### 6.5 Payment (`/payment/*`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/payment/create-order` | JWT | Create payment order, returns Pakasir URL |
| POST | `/payment/webhook` | — | Pakasir webhook callback |
| GET | `/payment/status/{order_id}` | JWT | Check payment status (with auto-verify) |

### 6.6 Subscription (`/subscription/*`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/subscription/status` | JWT | Get current subscription details |

### 6.7 Admin (`/admin/*`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/admin/users` | Admin | List users (search, paginate) |
| GET | `/admin/stats` | Admin | System-wide statistics |
| PATCH | `/admin/users/{id}/admin` | Admin | Grant/revoke admin |
| PATCH | `/admin/users/{id}/active` | Admin | Activate/deactivate user |
| PATCH | `/admin/users/{id}/plan` | Admin | Set user plan (free/pro) |
| DELETE | `/admin/users/{id}` | Admin | Delete user permanently |

### 6.8 Shared Manifest (`/shared/*`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/groups/{id}/share` | JWT (Pro) | Generate or update a group's share link |
| DELETE | `/groups/{id}/share` | JWT (Pro) | Revoke a group's share link |
| POST | `/shared/manifest/{token}` | PIN | Access public manifest data |

### 6.9 Rooming (`/rooming/*`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/rooming/group/{group_id}` | JWT (Pro) | List all rooms for a group with members |
| POST | `/rooming/group/{group_id}` | JWT (Pro) | Create a new room manually |
| GET | `/rooming/{room_id}` | JWT (Pro) | Get room details with members |
| DELETE | `/rooming/{room_id}` | JWT (Pro) | Delete a room (unassigns members) |
| POST | `/rooming/assign` | JWT (Pro) | Assign a member to a room |
| POST | `/rooming/unassign/{member_id}` | JWT (Pro) | Unassign member (auto-deletes empty room) |
| POST | `/rooming/auto/{group_id}` | JWT (Pro) | Run auto-rooming algorithm |
| DELETE | `/rooming/auto/{group_id}` | JWT (Pro) | Clear all auto-assigned rooms |
| GET | `/rooming/summary/{group_id}` | JWT (Pro) | Get rooming summary stats |

### 6.10 Inventory (`/inventory/*`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/inventory/forecast/{group_id}` | JWT (Pro) | Get inventory forecast for a group |
| GET | `/inventory/fulfillment/{group_id}` | JWT (Pro) | Get fulfillment status |
| POST | `/inventory/received` | JWT (Pro) | Mark members as received equipment |

### 6.11 Team (`/team/*`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/team/create` | JWT | Create organization |
| POST | `/team/invite` | JWT | Invite member by email |
| POST | `/team/join/{token}` | JWT | Join org via invite token |
| GET | `/team/` | JWT | List org members |
| DELETE | `/team/members/{id}` | JWT | Remove team member |

### 6.12 Analytics (`/analytics/*`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/analytics/summary` | JWT | Dashboard analytics (groups, jamaah, equipment, passport alerts) |

### 6.13 Itinerary (`/itineraries/*`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/itineraries/{group_id}` | JWT (Pro) | List schedule items |
| POST | `/itineraries/{group_id}` | JWT (Pro) | Create schedule item |
| PUT | `/itineraries/{group_id}/{id}` | JWT (Pro) | Update item |
| DELETE | `/itineraries/{group_id}/{id}` | JWT (Pro) | Delete item |

### 6.14 Documents (`/documents/*`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/documents/{group_id}/rooming-list` | JWT | Printable HTML rooming list |
| GET | `/documents/{group_id}/group-manifest` | JWT | Printable HTML group manifest |

### 6.15 Notifications (`/notifications`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/notifications` | JWT | Auto-generated alerts (passport, subscription, data) |

---

## 7. Architecture Diagram

```mermaid
graph TB
    subgraph Frontend["Frontend (Svelte 5 + Vite)"]
        LP[Landing Page]
        LG[Login/Register]
        DB[Dashboard]
        PP[Profile Page]
        MM[MutawwifManifest Page]
        FU[FileUpload Component]
        TR[TableResult Component]
        GS[GroupSelector Component]
        API[api.js Service Layer]
    end

    subgraph Backend["Backend (FastAPI + Python)"]
        AR[Auth Router]
        DR[Documents Router]
        ER[Excel Router]
        GR[Groups Router]
        PR[Payment Router]
        SR[Subscription Router]
        ADR[Admin Router]
        SHR[Shared Router]

        subgraph Services["Services Layer"]
            GOCR[Gemini OCR]
            OCR[Tesseract OCR Engine]
            DP[Document Processor]
            CL[Data Cleaner]
            VD[Validators]
            EX[Excel Service]
            EM[Email Service]
            PS[Payment Service]
            CA[OCR Cache]
            PG[Progress SSE]
            RS[Rooming Service]
        end

        subgraph Parsers["Document Parsers"]
            KP[KTP Parser]
            PAP[Passport Parser]
            VP[Visa Parser]
        end
    end

    subgraph External["External Services"]
        GA[Google Gemini API]
        BV[Brevo Email API]
        PK[Pakasir Payment]
        SB[Supabase PostgreSQL]
    end

    Frontend -->|HTTP/JWT| Backend
    DB --> FU --> API
    DB --> TR --> API
    DB --> GS --> API
    API --> AR & DR & ER & GR & PR & SR

    DR --> DP --> GOCR --> GA
    DP --> OCR
    DP --> CL --> VD
    DP --> CA
    DP --> PG
    GOCR --> KP & PAP & VP
    ER --> EX
    AR --> EM --> BV
    PR --> PS --> PK
    Backend --> SB
```

---

## 8. Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@host:port/database

# Authentication
JWT_SECRET=your-secret-key

# AI/OCR
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash

# Email (Brevo)
SMTP_EMAIL=noreply@jamaah.in
SMTP_PASSWORD=brevo-smtp-key
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_LOGIN=login-email
BREVO_API_KEY=brevo-api-key

# Payment (Pakasir)
SLUG=jamaah-in
PAKASIR_API_KEY=your-pakasir-key
FRONTEND_URL=http://localhost:5173

# App Config
FREE_SCAN_LIMIT=50
TRIAL_DAYS=7
PRO_DURATION_DAYS=30
PRO_PRICE=40000
```

---

## 9. User Flows

### 9.1 New User Registration
```
Landing Page → Click "Daftar" → Enter name/email/password
→ Backend creates user + 7-day trial subscription
→ OTP sent via Brevo (background thread)
→ User enters 6-digit OTP → Email verified → Redirect to Dashboard
```

### 9.2 Document Scanning Flow
```
Dashboard → Drag/drop or click to upload files (max 50)
→ Frontend sends to POST /process-documents/ with JWT
→ Backend validates, generates session_id
→ Frontend connects SSE /progress/{session_id}
→ Backend processes files concurrently (Gemini OCR)
→ Data cleaned → fuzzy merged → validated
→ Results returned as JSON → shown in editable TableResult
→ User reviews/edits → clicks "Download Excel" or "Save to Group"
```

### 9.3 Payment / Upgrade Flow
```
Profile Page → Click "Upgrade ke Pro"
→ Modal shows price (Rp 40.000/month) + features
→ Click "Bayar Sekarang"
→ Frontend calls POST /payment/create-order
→ Backend creates Payment record + builds Pakasir URL
→ New tab opens to Pakasir checkout
→ Frontend polls GET /payment/status/{order_id} every 5s
→ User pays via QRIS/VA/PayPal on Pakasir
→ Pakasir sends webhook to POST /payment/webhook
→ Backend verifies via Pakasir API → activates Pro
→ Frontend detects status=paid → updates UI
→ Pakasir redirects user back to Dashboard
```

### 9.4 Auto-Rooming Flow
```
Dashboard → Open "Auto-Rooming" tab → Select a group
→ Click "Auto-Generate" → Backend algorithm assigns members to rooms
  (families together, males/females separated, respects capacity)
→ Room cards appear in grid with drag-and-drop
→ User can drag members between rooms (optimistic UI, instant move)
→ Click "+" to add manual rooms → Fill room number + gender type
→ Click trash icon to delete rooms → Empty rooms auto-deleted
→ All changes sync to backend in background with rollback on error
```

### 9.5 Mutawwif Manifest Flow
```
Admin: Dashboard → Group → Click "Share" → Set 4-digit PIN → Copy link
Mutawwif: Open shared link on phone → Enter PIN → View mobile manifest
→ See pilgrim names, passport, room, baju size
→ Mark attendance via checklist (persists in LocalStorage)
→ Tap WhatsApp icon to message individual pilgrims
```

---

## 10. Current Pricing Model

| Plan | Price | Limits | Duration |
|------|-------|--------|----------|
| **Free Trial** | Rp 0 | 50 scans, 2 groups | 7 days |
| **Pro** | Rp 40,000/mo | Unlimited scans, unlimited groups | 30 days |

---

## 11. File Structure

```
Automaton Input Jamaah SaaS/
├── backend/
│   ├── main.py                          # FastAPI app entry point
│   ├── requirements.txt                 # Python dependencies
│   ├── app/
│   │   ├── auth.py                      # Auth logic (register, login, JWT)
│   │   ├── config.py                    # App configuration constants
│   │   ├── database.py                  # SQLAlchemy engine + session
│   │   ├── mappers.py                   # OCR result → ExtractedDataItem mapping
│   │   ├── schemas.py                   # Pydantic request/response models
│   │   ├── models/
│   │   │   ├── user.py                  # User, Subscription, UsageLog, Payment
│   │   │   ├── group.py                 # Group, GroupMember (32 columns + version)
│   │   │   ├── team.py                  # Organization, TeamMember, TeamInvite
│   │   │   ├── itinerary.py             # Itinerary schedule items
│   │   │   └── operational.py           # Room, RoomType, GenderType, InventoryMaster
│   │   ├── routers/
│   │   │   ├── auth_router.py           # /auth/* endpoints
│   │   │   ├── documents_router.py      # /process-documents/ + SSE
│   │   │   ├── excel_router.py          # /generate-excel/
│   │   │   ├── groups_router.py         # /groups/* CRUD (SQL COUNT subquery)
│   │   │   ├── payment_router.py        # /payment/* Pakasir integration
│   │   │   ├── subscription_router.py   # /subscription/* status
│   │   │   ├── admin_router.py          # /admin/* user management
│   │   │   ├── rooming_router.py        # /rooming/* room allocation (Pro)
│   │   │   ├── inventory_router.py      # /inventory/* logistics (Pro)
│   │   │   ├── shared_router.py         # /shared/* public manifest
│   │   │   ├── team_router.py           # /team/* multi-user teams
│   │   │   ├── analytics_router.py      # /analytics/* dashboard metrics
│   │   │   ├── itinerary_router.py      # /itineraries/* schedule CRUD (Pro)
│   │   │   ├── document_router.py       # /documents/* printable HTML templates
│   │   │   └── notification_router.py   # /notifications smart alerts
│   │   └── services/
│   │       ├── gemini_ocr.py            # Gemini Vision API integration
│   │       ├── ocr_engine.py            # Tesseract + OpenCV pipeline
│   │       ├── document_processor.py    # Batch processing orchestrator
│   │       ├── cleaner.py               # Data cleaning + fuzzy merge
│   │       ├── validators.py            # Field validation rules
│   │       ├── parser.py                # Parser dispatcher
│   │       ├── parsers/
│   │       │   ├── ktp_parser.py        # KTP-specific regex parsing
│   │       │   ├── passport_parser.py   # Passport-specific regex parsing
│   │       │   └── visa_parser.py       # Visa-specific regex parsing
│   │       ├── excel.py                 # Excel template + export
│   │       ├── email_service.py         # Brevo API + SMTP email
│   │       ├── payment_service.py       # Pakasir API integration
│   │       ├── cache.py                 # MD5-based OCR result cache
│   │       ├── progress.py             # SSE progress tracking
│   │       ├── rooming_service.py       # Auto-rooming algorithm + room CRUD
│   │       └── inventory_service.py     # Equipment forecast + fulfillment
│   ├── templates/                       # Excel template files
│   └── uploads/                         # Temporary file storage
├── frontend-svelte/
│   ├── package.json                     # Node dependencies
│   ├── vite.config.js                   # Vite + Svelte config + proxy
│   └── src/
│       ├── App.svelte                   # Root component + routing
│       └── lib/
│           ├── pages/
│           │   ├── LandingPage.svelte   # Marketing/landing page
│           │   ├── Login.svelte         # Auth (login + register + OTP)
│           │   ├── Dashboard.svelte     # Analytics dashboard
│           │   ├── ScannerPage.svelte   # OCR scanner (was in Dashboard)
│           │   ├── ItineraryPage.svelte # Schedule manager (Pro)
│           │   ├── ProfilePage.svelte   # User profile + settings
│           │   ├── RoomingPage.svelte   # Auto-rooming drag-and-drop (Pro)
│           │   ├── InventoryPage.svelte # Inventory/logistics (Pro)
│           │   └── MutawwifManifest.svelte # Public mobile manifest
│           ├── components/
│           │   ├── FileUpload.svelte    # Drag-drop file upload
│           │   ├── TableResult.svelte   # Editable 32-col data table
│           │   ├── GroupSelector.svelte  # Group picker/creator
│           │   ├── NotificationBell.svelte # Bell icon + dropdown alerts
│           │   ├── SubscriptionBanner.svelte
│           │   └── BrandLogo.svelte
│           └── services/
│               └── api.js               # API client + in-memory cache
├── scripts/
│   └── seed_admin.py                    # Admin user seeder
├── tests/
│   └── test_api.py                      # API integration tests
├── .env                                 # Environment variables
└── backend/alembic/                     # Alembic migrations (version-controlled schema)
```

---

## 12. Key Design Decisions

1. **Gemini Vision over Tesseract**: Gemini provides dramatically better accuracy for Indonesian documents (especially handwritten addresses, batik-background KTPs). Tesseract is kept as fallback.

2. **Direct Image-to-JSON**: Instead of OCR → text → parse, the system sends raw images to Gemini with a structured prompt and gets JSON back. This eliminates regex parsing errors.

3. **Fuzzy Merge**: Travel agents upload KTP/KK + Passport + Visa for the same person as separate files. The system auto-merges them into one row using name similarity matching.

4. **32-Column Standard**: The data schema exactly mirrors Siskopatuh's Excel format — no transformation needed at export time.

5. **SPA with State-based Routing**: No framework router — simple `currentPage` state variable. Lightweight for the multi-page scope.

6. **Non-blocking Emails**: Email sending runs in background threads to prevent registration/OTP endpoints from timing out.

7. **Webhook + Polling**: Payment verification uses both Pakasir webhook (push) and status polling (pull) for reliability.

8. **Database Performance**: Eager loading (`joinedload`) for User→Subscription on every auth request, SQL `COUNT()` subqueries instead of `len(members)`, `joinedload(Room.members)` for rooming queries. Connection pool tuned for remote Supabase (pool_size=10, max_overflow=20, pool_recycle=1800). GZIP compression middleware for large JSON responses.

9. **Optimistic UI**: Drag-and-drop and room deletion update the frontend instantly with rollback on API failure — eliminates perceived latency to Supabase.

10. **Frontend Response Cache**: Lightweight in-memory cache with TTL prevents redundant API calls on page navigation (subscription: 60s, groups: 30s). Auto-invalidated on mutations.

11. **PWA-First Design**: Service worker with cache-first for static and network-first with fallback for API. MutawwifManifest works fully offline via localStorage.

12. **Alembic Migrations**: Version-controlled database schema changes. `env.py` auto-imports all models for autogenerate support.

13. **Optimistic Locking**: `version` column on Group prevents concurrent edit conflicts in multi-user teams.

14. **Smart Notifications**: On-the-fly alert generation (no stored notifications table) — scans live data for passport expiry, subscription expiry, incomplete data.

---

*Document generated from codebase analysis — Jamaah.in v5.0 (P3), February 2026*

