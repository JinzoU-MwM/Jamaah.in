# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Commands

### Go Backend v2 (PRIMARY — use this)
```powershell
# Build all services
$env:PATH += ";C:\Program Files\Go\bin"
Set-Location "D:\Codding\Project\Automaton Input Jamaah SaaS"
go build -o bin/api-gateway.exe   ./cmd/api-gateway
go build -o bin/auth-service.exe  ./cmd/auth-service
go build -o bin/package-service.exe ./cmd/package-service
go build -o bin/jamaah-service.exe  ./cmd/jamaah-service
go build -o bin/invoice-service.exe ./cmd/invoice-service
go build -o bin/finance-service.exe ./cmd/finance-service
go build -o bin/ai-ocr-service.exe ./cmd/ai-ocr-service
go build -o bin/vendor-service.exe  ./cmd/vendor-service

# Run a single service (example: auth)
$env:POSTGRES_PORT = "5433"; $env:POSTGRES_USER = "jamaah"; $env:POSTGRES_PASSWORD = "Jamaah123!"
$env:REDIS_ADDR = "localhost:6379"; $env:NATS_ADDR = "nats://localhost:4222"
go run ./cmd/auth-service

# Run migrations
go run cmd/migration/main.go -service all -direction up
# On Windows with spaces in path, run via psql instead:
docker cp migrations/auth/001_initial_schema.up.sql jamaah-postgres:/tmp/auth.sql
docker exec jamaah-postgres psql -U jamaah -d jamaah_auth -f /tmp/auth.sql

# Test
go test -v ./internal/...
go test -v ./internal/auth/...
```

### Frontend (Svelte 5 SPA)
```bash
cd frontend-svelte
npm run dev        # dev server (port 5173), proxies /api → localhost:8080 (Go gateway)
npm run build      # production build
npm run check      # svelte-check (type/lint)
npm run test       # vitest run
```

### Python Backend v1 (LEGACY — do NOT add features here)
```bash
cd backend
python main.py     # v1 dev server port 8000 — legacy only
```

### Local Infrastructure (Docker)
```powershell
docker ps   # check: jamaah-postgres (5433), jamaah-redis (6379), jamaah-nats (4222), jamaah-minio (9000)
# All containers should be running healthy before starting Go services
```

---

## Architecture

### Overview
**v2 (active)**: Go microservices + Svelte 5 SPA. No SvelteKit. Auth via Bearer JWT token (RSA keys in `certs/`).
**v1 (legacy)**: Python FastAPI in `backend/` — being replaced, do not add new features.

### Go Services (`cmd/` + `internal/`)
Each service is a standalone Fiber HTTP server. No gRPC between services yet — API Gateway does HTTP reverse proxy.

| Service | Port | DB | Binary |
|---------|------|----|--------|
| api-gateway | 8080 | — | `bin/api-gateway.exe` |
| auth-service | 50051 | `jamaah_auth` | `bin/auth-service.exe` |
| package-service | 50052 | `jamaah_package` | `bin/package-service.exe` |
| jamaah-service | 50053 | `jamaah_crm` | `bin/jamaah-service.exe` |
| invoice-service | 50054 | `jamaah_invoice` | `bin/invoice-service.exe` |
| finance-service | 50055 | `jamaah_finance` | `bin/finance-service.exe` |
| ai-ocr-service | 50056 | `jamaah_aiocr` | `bin/ai-ocr-service.exe` |
| vendor-service | 50057 | `jamaah_vendor` | `bin/vendor-service.exe` |

- **Config**: `internal/shared/config/config.go` — reads env vars with sane defaults (postgres port 5433, redis localhost:6379, etc.)
- **DB**: pgx/v5 pool via `internal/shared/database/`
- **Auth**: RSA JWT (`certs/private.pem` + `certs/public.pem`). Middleware checks `Authorization: Bearer <token>`.
- **Gateway CORS**: reads `ALLOWED_ORIGINS` env var — must NOT use wildcard `*` when `AllowCredentials: true`.
- **Migrations**: SQL files in `migrations/<service>/`. Run via `cmd/migration/main.go` or directly with psql.

### API Gateway Routes
```
GET  /health               → gateway itself
/api/v1/auth/*             → auth-service :50051
/api/v1/packages/*         → package-service :50052
/api/v1/jamaah/*           → jamaah-service :50053
/api/v1/invoices/*         → invoice-service :50054
/api/v1/finance/*          → finance-service :50055
/api/v1/vendors/*          → vendor-service :50057
/api/v1/scan/*              → ai-ocr-service :50056
```

### Frontend (`frontend-svelte/`)
- **SPA routing**: `src/App.svelte` owns `currentPage` state. Pages lazy-loaded via dynamic `import()`.
- **API calls**: `src/lib/services/api.js` → `ApiService`. Base in `apiCore.js` (adds `credentials: 'include'`, prefix `/api`).
- **Cache**: In-memory TTL cache in `api.js`. Call `cacheInvalidate(prefix)` after mutations.
- **Components**: `src/lib/components/` — shared UI. `src/lib/pages/` — full-page views.
- **Design system**: Blue primary (`#2563eb`/`#1d4ed8`), gold accent (`#f59e0b`), emerald `.in` (`#10b981`), slate neutrals. Font: Plus Jakarta Sans.

### Local Docker Infrastructure
All containers run from `docker-compose.yml` at repo root:
- `jamaah-postgres` — PostgreSQL 16, port 5433, user=`jamaah`, pass=`Jamaah123!`
- `jamaah-redis` — Redis 7, port 6379
- `jamaah-nats` — NATS JetStream, port 4222 (HTTP monitoring: 8222)
- `jamaah-minio` — MinIO S3, ports 9000 (API) + 9001 (Console)
- `jamaah-frontend-local` — nginx serving Svelte build, port 8005

### Databases (per-service)
- `jamaah_auth` — users, organizations, team_members, refresh_tokens, team_invites, audit_logs
- `jamaah_package` — packages, pricing_tiers, cost_components, package_documents
- `jamaah_crm` — jamaah_profiles, jamaah_package_registrations, jamaah_notes, follow_ups, jamaah_documents
- `jamaah_invoice` — invoices, payment_schedules, payments
- `jamaah_finance` — trip_expenses
- `jamaah_aiocr` — scan_jobs, scan_results, ai_cache, export_templates
- `jamaah_vendor` — vendors, vendor_bills, vendor_payments

---

## Project Context (v2 Pivot)

Jamaah.in is pivoting from a Siskopatuh input tool (v1) to a full travel-admin business system (v2). The Python `backend/` is v1 legacy. The Go microservices in `cmd/` + `internal/` are v2.

12 planned modules: Paket & Harga, CRM & Pipeline, Invoice & Pembayaran, Laporan Keuangan, Vendor & Biaya Ops, Komisi Agen, Dokumen & Paspor, AI Scanner (enhanced), E-Kontrak Digital, Pembatalan & Refund, Persediaan, Penggajian. See `prd-refactor.md` for full spec.
