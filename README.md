# 🕌 Jamaah.in — Automasi Input Data Jamaah untuk Siskopatuh

SaaS web application yang mengotomatisasi proses input data jamaah Haji & Umrah dari dokumen identitas (KTP, Paspor, Visa) ke format Excel yang kompatibel dengan **Siskopatuh** (Sistem Kementerian Agama RI).

## ✨ Fitur Utama

- **🤖 AI-Powered OCR** — Google Gemini 2.5 Flash Vision API untuk ekstraksi data dengan akurasi tinggi
- **📄 Multi-Dokumen** — Mendukung KTP, Paspor, dan Visa Indonesia
- **🔀 Smart Merge** — Otomatis menggabungkan data KTP + Paspor + Visa milik orang yang sama (fuzzy matching 80%+)
- **✅ Validasi Data** — Verifikasi NIK (16 digit), nomor paspor, format tanggal, dan lainnya
- **📊 32-Kolom Siskopatuh** — Output langsung sesuai format resmi Siskopatuh
- **📥 Excel Export** — Download file `.xlsm` siap upload ke Siskopatuh
- **👥 Grup Jamaah** — Organisir data per trip/keberangkatan (misal "UMROH 12 Feb 2026")
- **💳 Sistem Langganan** — Free trial 3 hari + Pro plan (Rp 40.000/bulan) via Pakasir
- **🔐 Auth Lengkap** — Register, login (JWT), verifikasi email OTP, reset password
- **👨‍💼 Admin Panel** — Manajemen user, statistik sistem, kontrol langganan

## 🏗️ Tech Stack

### Backend
| Layer | Technology |
|-------|-----------|
| Framework | FastAPI 0.115.0 |
| Server | Uvicorn (ASGI) |
| Database | PostgreSQL (Supabase) |
| ORM | SQLAlchemy ≥2.0 |
| AI OCR | Google Gemini 2.5 Flash |
| Fallback OCR | Tesseract + OpenCV |
| Auth | JWT (python-jose) + bcrypt |
| Email | Brevo API + SMTP fallback |
| Payment | Pakasir |
| Excel | openpyxl + pandas |

### Frontend
| Layer | Technology |
|-------|-----------|
| Framework | Svelte 5 (Runes) |
| Build | Vite 7 |
| Styling | TailwindCSS 3.4 |
| Icons | Lucide Svelte |

## 🚀 Quick Start

### 1. Clone & Environment

```bash
git clone <repo-url>
cd "Automaton Input Jamaah SaaS"
cp .env.example .env
# Edit .env with your API keys
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```
Server runs at `http://localhost:8000` — API docs at `/docs`

### 3. Frontend

```bash
cd frontend-svelte
npm install
npm run dev
```
App runs at `http://localhost:5173`

### 4. Seed Admin User (Optional)

```bash
python scripts/seed_admin.py
```

## ⚙️ Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Auth
JWT_SECRET=your-secret-key

# AI OCR
GEMINI_API_KEY=your-gemini-key
GEMINI_MODEL=gemini-2.5-flash

# Email (Brevo)
SMTP_EMAIL=noreply@jamaah.in
SMTP_PASSWORD=your-smtp-password
BREVO_API_KEY=your-brevo-key

# Payment (Pakasir)
PAKASIR_API_KEY=your-pakasir-key
FRONTEND_URL=http://localhost:5173
```

## 📂 Project Structure

```
├── backend/
│   ├── main.py                      # FastAPI entry point
│   ├── requirements.txt             # Python deps
│   └── app/
│       ├── auth.py                  # Auth logic (JWT, bcrypt)
│       ├── database.py              # SQLAlchemy engine
│       ├── schemas.py               # Pydantic models
│       ├── models/
│       │   ├── user.py              # User, Subscription, Payment
│       │   └── group.py             # Group, GroupMember (32 cols)
│       ├── routers/
│       │   ├── auth_router.py       # /auth/*
│       │   ├── documents_router.py  # /process-documents/ + SSE
│       │   ├── excel_router.py      # /generate-excel/
│       │   ├── groups_router.py     # /groups/* CRUD
│       │   ├── payment_router.py    # /payment/* (Pakasir)
│       │   ├── subscription_router.py
│       │   └── admin_router.py      # /admin/*
│       └── services/
│           ├── gemini_ocr.py        # Gemini Vision API
│           ├── ocr_engine.py        # Tesseract + OpenCV
│           ├── document_processor.py # Batch pipeline
│           ├── cleaner.py           # Data cleaning + fuzzy merge
│           ├── validators.py        # Field validation
│           ├── excel.py             # Excel export
│           ├── email_service.py     # Brevo/SMTP email
│           ├── payment_service.py   # Pakasir API
│           └── parsers/
│               ├── ktp_parser.py
│               ├── passport_parser.py
│               └── visa_parser.py
├── frontend-svelte/
│   └── src/
│       ├── App.svelte               # Root + routing
│       └── lib/
│           ├── pages/
│           │   ├── LandingPage.svelte
│           │   ├── Login.svelte
│           │   ├── Dashboard.svelte
│           │   └── ProfilePage.svelte
│           ├── components/
│           │   ├── FileUpload.svelte
│           │   ├── TableResult.svelte
│           │   ├── GroupSelector.svelte
│           │   └── SubscriptionBanner.svelte
│           └── services/
│               └── api.js            # API client
├── scripts/
│   └── seed_admin.py
└── tests/
```

## 🔌 API Endpoints

| Group | Endpoints | Auth |
|-------|-----------|------|
| **Auth** | `POST /auth/register, login, verify-otp, forgot-password, reset-password` | Public |
| **Auth** | `GET/PUT/DELETE /auth/me`, `GET /auth/subscription, activity` | JWT |
| **Documents** | `POST /process-documents/`, `GET /progress/{session_id}` (SSE) | JWT |
| **Excel** | `POST /generate-excel/` | JWT |
| **Groups** | `GET/POST /groups/`, `GET/PUT/DELETE /groups/{id}`, members CRUD | JWT |
| **Payment** | `POST /payment/create-order, webhook`, `GET /payment/status/{id}` | JWT |
| **Admin** | `GET /admin/users, stats`, `PATCH/DELETE /admin/users/{id}/*` | Admin |

Full interactive docs: `http://localhost:8000/docs`

## 📋 OCR Pipeline

```
Upload Files → Validate (type, size)
→ Cache Check (MD5 hash)
→ Gemini Vision OCR (concurrent, rate-limited)
→ Structured JSON Extraction
→ Data Cleaning (name sanitization, date standardization)
→ Fuzzy Merge (KTP + Passport + Visa → 1 row)
→ Field Validation (NIK, passport no, dates)
→ Preview in editable table
→ Export to Excel or Save to Group
```

## 💰 Pricing

| Plan | Price | Scans | Groups | Duration |
|------|-------|-------|--------|----------|
| Free Trial | Rp 0 | 50 | 2 | 3 hari |
| Pro | Rp 40.000/bln | Unlimited | Unlimited | 30 hari |

## 🧪 Testing

```bash
cd backend
pytest -v --cov=. --cov-report=html
```

See `tests/` directory for test examples.

## 📄 License

Private — All rights reserved.
