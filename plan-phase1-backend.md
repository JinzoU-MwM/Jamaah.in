# Plan Phase 1 — Backend Refactor Go Microservices

> **Versi**: 1.0  
> **Tanggal**: 2026-05-21  
> **Scope**: Phase 1 backend only — Paket, CRM, Invoice, Dashboard Owner, AI Scanner  
> **Timeline target**: 12 minggu (~3 bulan)

---

## 1. Arsitektur Overview

```
                    ┌─────────────┐
                    │   Internet   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Cloudflare  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  API Gateway│ :8080 (Fiber)
                    │  (Go + JWT) │
                    └──────┬──────┘
                           │ REST routing + auth
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐  ┌─────▼─────┐  ┌──────▼──────┐
   │ Auth Service │  │  Package  │  │  Jamaica    │
   │   :50051    │  │  Service  │  │  Service    │
   │  (gRPC)     │  │  :50052   │  │  :50053     │
   └──────┬──────┘  └─────┬─────┘  └──────┬──────┘
          │               │                │
   ┌──────▼──────┐  ┌─────▼─────┐  ┌──────▼──────┐
   │ Invoice Svc │  │  Finance  │  │  AI/OCR Svc │
   │   :50054    │  │  Service  │  │  :50056     │
   │  (gRPC)     │  │  :50055  │  │  (gRPC)     │
   └──────┬──────┘  └─────┬─────┘  └──────┬──────┘
          │               │                │
          └───────────────┼────────────────┘
                          │
                   ┌──────▼──────┐
                   │     NATS     │  (async events)
                   │  JetStream   │
                   └──────┬──────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
   ┌──────▼──────┐ ┌─────▼─────┐ ┌───────▼───────┐
   │  PostgreSQL │ │   Redis   │ │    MinIO      │
   │  (multi-db) │ │   :6379   │ │   :9000       │
   └─────────────┘ └───────────┘ └───────────────┘
```

### Keputusan Arsitektur

| Keputusan | Pilihan | Alasan |
|-----------|---------|--------|
| Bahasa | Go | Performa, concurrency, single binary, gRPC first-class |
| HTTP framework (Gateway) | Fiber v2 | Fast, Express-like API, mature untuk Go |
| gRPC framework | google.golang.org/grpc | Standard, typed, efficient |
| Database | PostgreSQL 16 | Database-per-service (1 instance, multiple DBs) |
| ORM/Query | sqlc + pgx | Type-safe SQL, performant, Go idiomatic |
| Migrasi DB | golang-migrate | Industry standard |
| Cache | Redis 7 | JWT blacklist, response cache, rate limiting |
| Event bus | NATS JetStream | Lightweight, durable, replay |
| File storage | MinIO | S3-compatible, self-hosted |
| Auth | JWT (RS256) + refresh token | Stateless, scalable |
| Container | Docker Compose (dev & prod) | Simpler than k3s untuk single-server; migrate ke k3s saat perlu multi-node |
| CI/CD | GitHub Actions + GHCR | Gratis, terintegrasi |
| Monitoring | Prometheus + Grafana | Self-hosted, standard |
| Logging | Zap (structured) | Fast, structured JSON logging |

### Kenapa Docker Compose, Bukan k3s?

Untuk Phase 1 di single server, Docker Compose lebih pragmatic:
- Setup lebih simple (1 file YAML)
- Restart lebih cepat saat development
- Resource overhead lebih rendah
- Learning curve lebih rendah
- k3s bisa diadopsi di Phase 3+ kalau perlu multi-node atau rolling deploy zero-downtime

---

## 2. Struktur Project (Monorepo)

```
jamaah-in/
├── cmd/
│   ├── api-gateway/
│   │   └── main.go
│   ├── auth-service/
│   │   └── main.go
│   ├── package-service/
│   │   └── main.go
│   ├── jamaah-service/
│   │   └── main.go
│   ├── invoice-service/
│   │   └── main.go
│   ├── finance-service/
│   │   └── main.go
│   ├── ai-ocr-service/
│   │   └── main.go
│   └── migration/
│       └── main.go
│
├── internal/
│   ├── gateway/          # API Gateway handlers + middleware
│   ├── auth/             # Auth service business logic
│   ├── package/          # Package service business logic
│   ├── jamaah/           # CRM/Jamaah service business logic
│   ├── invoice/          # Invoice service business logic
│   ├── finance/          # Finance service business logic
│   ├── aiocr/            # AI Scanner service business logic
│   └── shared/           # Shared libraries
│       ├── database/     # DB connection helpers
│       ├── redis/        # Redis client helpers
│       ├── nats/         # NATS publisher/subscriber
│       ├── auth/         # JWT validation middleware
│       ├── response/     # Standard HTTP response types
│       ├── pagination/   # Pagination helpers
│       └── validator/    # Custom validators
│
├── proto/                # gRPC Protocol Buffer definitions
│   ├── auth/
│   │   └── auth.proto
│   ├── package/
│   │   └── package.proto
│   ├── jamaah/
│   │   └── jamaah.proto
│   ├── invoice/
│   │   └── invoice.proto
│   ├── finance/
│   │   └── finance.proto
│   └── aiocr/
│       └── aiocr.proto
│
├── migrations/           # SQL migration files per service
│   ├── auth/
│   ├── package/
│   ├── jamaah/
│   ├── invoice/
│   └── finance/
│
├── deployments/
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   ├── Dockerfile.gateway
│   ├── Dockerfile.auth
│   ├── Dockerfile.package
│   ├── Dockerfile.jamaah
│   ├── Dockerfile.invoice
│   ├── Dockerfile.finance
│   ├── Dockerfile.aiocr
│   ├── nginx/
│   │   └── nginx.conf
│   └── traefik/
│       └── traefik.yml
│
├── scripts/
│   ├── migrate.sh
│   ├── seed-dev.sh
│   └── generate-proto.sh
│
├── docs/
│   └── api/
│       ├── openapi.yaml          # REST API spec (Gateway)
│       └── events.md             # NATS event catalog
│
├── frontend-svelte/       # DIPERTAHANKAN dari v1, update API calls
│
├── go.mod
├── go.sum
├── Makefile
├── buf.yaml               # Buf config for protobuf
├── buf.gen.yaml
└── .env.example
```

### Go Module Strategy

**Monorepo dengan Go workspace** (`go.work`):

```
go 1.23

use (
    ./cmd/api-gateway
    ./cmd/auth-service
    ./cmd/package-service
    ./cmd/jamaah-service
    ./cmd/invoice-service
    ./cmd/finance-service
    ./cmd/ai-ocr-service
)
```

Setiap service dan `internal/shared` adalah Go module sendiri, tapi di-develop dalam satu repo untuk kemudahan koordinasi proto changes dan shared libraries.

---

## 3. Service Definitions

### 3.1 API Gateway (`cmd/api-gateway`)

**Port**: 8080 (HTTP)  
**Tanggung Jawab**: Single entry point, routing, auth middleware, rate limiting, request aggregation

```
REST API (browser/mobile) → API Gateway → gRPC → Service
```

Gateway menerjemahkan REST JSON dari frontend menjadi gRPC calls ke service yang sesuai. Tidak ada business logic di gateway.

**Middleware**:
- JWT validation (RS256, public key)
- Rate limiting (Redis-backed)
- Request logging (Zap)
- CORS
- Request ID propagation

**Route Prefix**:
| Prefix | Target Service |
|--------|---------------|
| `/api/v1/auth/*` | Auth Service |
| `/api/v1/packages/*` | Package Service |
| `/api/v1/jamaah/*` | Jamaica Service |
| `/api/v1/invoices/*` | Invoice Service |
| `/api/v1/finance/*` | Finance Service |
| `/api/v1/scan/*` | AI/OCR Service |

---

### 3.2 Auth Service (`cmd/auth-service`)

**Port**: 50051 (gRPC)  
**Database**: `jamaah_auth`

**Fungsi**:
- Registrasi & login user (email + password)
- JWT issuance (access token 15min, refresh token 7d)
- RBAC: Owner, Admin, Finance, CS/Marketing, Viewer
- Organization management (multi-tenant)
- Team invite flow
- Audit log (semua write operation)

**gRPC Methods**:
```protobuf
service AuthService {
  rpc Register(RegisterRequest) returns (RegisterResponse);
  rpc Login(LoginRequest) returns (LoginResponse);
  rpc RefreshToken(RefreshTokenRequest) returns (RefreshTokenResponse);
  rpc GetUser(GetUserRequest) returns (User);
  rpc UpdateUser(UpdateUserRequest) returns (User);
  rpc ListUsers(ListUsersRequest) returns (ListUsersResponse);
  
  // Organization
  rpc CreateOrganization(CreateOrganizationRequest) returns (Organization);
  rpc GetOrganization(GetOrganizationRequest) returns (Organization);
  rpc UpdateOrganization(UpdateOrganizationRequest) returns (Organization);
  rpc AddTeamMember(AddTeamMemberRequest) returns (TeamMember);
  rpc RemoveTeamMember(RemoveTeamMemberRequest) returns (Empty);
  rpc UpdateMemberRole(UpdateMemberRoleRequest) returns (TeamMember);
  rpc ListTeamMembers(ListTeamMembersRequest) returns (ListTeamMembersResponse);
  rpc InviteMember(InviteMemberRequest) returns (InviteMemberResponse);
  rpc AcceptInvite(AcceptInviteRequest) returns (TeamMember);
  
  // Validation
  rpc ValidateToken(ValidateTokenRequest) returns (ValidateTokenResponse);
  rpc HasPermission(HasPermissionRequest) returns (HasPermissionResponse);
}
```

**Database Schema** (`jamaah_auth`):

```sql
-- organizations
CREATE TABLE organizations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    slug        VARCHAR(100) UNIQUE NOT NULL,
    logo_url    TEXT,
    address     TEXT,
    phone       VARCHAR(30),
    email       VARCHAR(255),
    bank_name   VARCHAR(100),
    bank_account VARCHAR(50),
    bank_holder  VARCHAR(255),
    created_by  UUID NOT NULL REFERENCES users(id),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- users
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    name            VARCHAR(255) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    phone           VARCHAR(30) UNIQUE,
    phone_verified  BOOLEAN DEFAULT FALSE,
    role            VARCHAR(20) NOT NULL DEFAULT 'admin', -- owner, admin, finance, cs, viewer
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- team_members (link user to organization with role)
CREATE TABLE team_members (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id      UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role        VARCHAR(20) NOT NULL DEFAULT 'viewer', -- owner, admin, finance, cs, viewer
    status      VARCHAR(20) NOT NULL DEFAULT 'active', -- active, pending, removed
    invited_by  UUID REFERENCES users(id),
    joined_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(org_id, user_id)
);

-- refresh_tokens
CREATE TABLE refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) NOT NULL,
    device_info VARCHAR(255),
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- team_invites
CREATE TABLE team_invites (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id      UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email       VARCHAR(255) NOT NULL,
    role        VARCHAR(20) NOT NULL DEFAULT 'viewer',
    token       VARCHAR(64) UNIQUE NOT NULL,
    invited_by  UUID NOT NULL REFERENCES users(id),
    expires_at  TIMESTAMPTZ NOT NULL,
    status      VARCHAR(20) DEFAULT 'pending',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- audit_logs
CREATE TABLE audit_logs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id      UUID REFERENCES organizations(id),
    user_id     UUID REFERENCES users(id),
    action      VARCHAR(50) NOT NULL,
    entity      VARCHAR(50) NOT NULL,
    entity_id   UUID,
    old_value   JSONB,
    new_value   JSONB,
    ip_address  VARCHAR(45),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_org ON audit_logs(org_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity, entity_id);
```

---

### 3.3 Package Service (`cmd/package-service`)

**Port**: 50052 (gRPC)  
**Database**: `jamaah_package`

**Fungsi**:
- CRUD paket umroh/haji
- Struktur harga bertingkat (quad, triple, double, single)
- Komponen biaya (cost breakdown) per paket
- Status paket (Draft, Open, Full, Closed, Done)
- Kuota tracking (terisi, tersisa)
- Publish/share link paket

**gRPC Methods**:
```protobuf
service PackageService {
  // Package CRUD
  rpc CreatePackage(CreatePackageRequest) returns (Package);
  rpc GetPackage(GetPackageRequest) returns (Package);
  rpc UpdatePackage(UpdatePackageRequest) returns (Package);
  rpc DeletePackage(DeletePackageRequest) returns (Empty);
  rpc ListPackages(ListPackagesRequest) returns (ListPackagesResponse);
  
  // Pricing tiers
  rpc CreatePricingTier(CreatePricingTierRequest) returns (PricingTier);
  rpc UpdatePricingTier(UpdatePricingTierRequest) returns (PricingTier);
  rpc DeletePricingTier(DeletePricingTierRequest) returns (Empty);
  
  // Cost components
  rpc CreateCostComponent(CreateCostComponentRequest) returns (CostComponent);
  rpc UpdateCostComponent(UpdateCostComponentRequest) returns (CostComponent);
  rpc DeleteCostComponent(DeleteCostComponentRequest) returns (Empty);
  
  // Quota tracking
  rpc GetPackageQuota(GetPackageQuotaRequest) returns (PackageQuota);
  rpc UpdatePackageStatus(UpdatePackageStatusRequest) returns (Package);
  
  // Public endpoint
  rpc GetPackageBySlug(GetPackageBySlugRequest) returns (PublicPackage);
}
```

**Database Schema** (`jamaah_package`):

```sql
-- packages
CREATE TABLE packages (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL,
    name                VARCHAR(255) NOT NULL,
    slug                VARCHAR(100) UNIQUE NOT NULL,
    description         TEXT,
    package_type        VARCHAR(30) NOT NULL, -- umroh_reguler, umroh_plus, haji_khusus, haji_onh_plus
    departure_date      DATE NOT NULL,
    return_date         DATE NOT NULL,
    duration_days       INT GENERATED ALWAYS AS (return_date - departure_date + 1) STORED,
    
    -- Quota
    total_seats         INT NOT NULL,
    reserved_seats      INT NOT NULL DEFAULT 0,  -- updated by jamaah-service via event
    
    -- Flight
    airline             VARCHAR(100),
    flight_number_go    VARCHAR(30),
    flight_number_return VARCHAR(30),
    
    -- Hotels
    hotel_makkah_name   VARCHAR(255),
    hotel_makkah_stars  INT CHECK (hotel_makkah_stars BETWEEN 1 AND 5),
    hotel_makkah_nights INT,
    hotel_makkah_distance VARCHAR(30),  -- e.g., "200m dari Masjidil Haram"
    
    hotel_madinah_name   VARCHAR(255),
    hotel_madinah_stars  INT CHECK (hotel_madinah_stars BETWEEN 1 AND 5),
    hotel_madinah_nights INT,
    hotel_madinah_distance VARCHAR(30),
    
    -- Itinerary (rich text)
    itinerary           TEXT,
    
    -- Visibility
    is_published        BOOLEAN DEFAULT FALSE,
    status              VARCHAR(20) NOT NULL DEFAULT 'draft', -- draft, open, full, closed, done
    
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT chk_departure_before_return CHECK (departure_date <= return_date)
);

CREATE INDEX idx_packages_org ON packages(org_id);
CREATE INDEX idx_packages_status ON packages(org_id, status);
CREATE INDEX idx_packages_departure ON packages(org_id, departure_date);

-- pricing_tiers (per paket, per tipe kamar)
CREATE TABLE pricing_tiers (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_id  UUID NOT NULL REFERENCES packages(id) ON DELETE CASCADE,
    room_type   VARCHAR(20) NOT NULL, -- quad, triple, double, single
    price       BIGINT NOT NULL,      -- dalam IDR, no decimal
    label       VARCHAR(100),          -- e.g., "Harga Early Bird"
    is_early_bird BOOLEAN DEFAULT FALSE,
    early_bird_expires_at TIMESTAMPTZ,
    sort_order  INT DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT chk_price_positive CHECK (price > 0)
);

CREATE INDEX idx_pricing_package ON pricing_tiers(package_id);

-- cost_components (biaya internal per paket, untuk HPP)
CREATE TABLE cost_components (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_id      UUID NOT NULL REFERENCES packages(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,  -- e.g., "Tiket Pesawat", "Hotel Makkah"
    category        VARCHAR(50) NOT NULL,  -- flight, hotel_makkah, hotel_madinah, visa, transport, guide, equipment, other
    amount_per_person BIGINT NOT NULL DEFAULT 0,  -- dalam IDR
    quantity        INT NOT NULL DEFAULT 1,  -- multiplier (e.g., 5 malam)
    total_amount    BIGINT GENERATED ALWAYS AS (amount_per_person * quantity) STORED,
    sort_order      INT DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_cost_components_package ON cost_components(package_id);

-- package_documents (brosur PDF/gambar)
CREATE TABLE package_documents (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_id  UUID NOT NULL REFERENCES packages(id) ON DELETE CASCADE,
    file_name   VARCHAR(255) NOT NULL,
    file_url    TEXT NOT NULL,
    file_type   VARCHAR(30) NOT NULL, -- pdf, image
    file_size   BIGINT,
    sort_order  INT DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_package_docs ON package_documents(package_id);

-- view: package profit projection
CREATE VIEW v_package_profit AS
SELECT 
    p.id AS package_id,
    p.name AS package_name,
    p.total_seats,
    COALESCE(SUM(cc.total_amount), 0) AS hpp_per_person,
    COALESCE(SUM(cc.total_amount), 0) * p.total_seats AS total_hpp,
    COALESCE((SELECT price FROM pricing_tiers WHERE package_id = p.id AND room_type = 'quad' ORDER BY sort_order LIMIT 1), 0) AS lowest_price,
    COALESCE((SELECT price FROM pricing_tiers WHERE package_id = p.id AND room_type = 'quad' ORDER BY sort_order LIMIT 1), 0) - COALESCE(SUM(cc.total_amount), 0) AS projected_margin_per_person
FROM packages p
LEFT JOIN cost_components cc ON cc.package_id = p.id
GROUP BY p.id;
```

---

### 3.4 Jamaica/CRM Service (`cmd/jamaah-service`)

**Port**: 50053 (gRPC)  
**Database**: `jamaah_crm`

**Fungsi**:
- Profil jamaah lengkap (identitas + kontak + dokumen)
- Pipeline status (Prospek → Selesai)
- Follow-up & catatan internal
- Document checklist (KTP, KK, paspor, visa, dll.)
- AI Scanner integration (upload → extract → populate profil)
- Siskopatuh export (32 kolom)
- Jamaah duplicate detection (by NIK or paspor number)

**gRPC Methods**:
```protobuf
service JamaicaService {
  // Profile CRUD
  rpc CreateJamaah(CreateJamaahRequest) returns (Jamaah);
  rpc GetJamaah(GetJamaahRequest) returns (Jamaah);
  rpc UpdateJamaah(UpdateJamaahRequest) returns (Jamaah);
  rpc DeleteJamaah(DeleteJamaahRequest) returns (Empty);
  rpc ListJamaah(ListJamaahRequest) returns (ListJamaahResponse);
  rpc SearchJamaah(SearchJamaahRequest) returns (ListJamaahResponse);
  
  // Pipeline
  rpc UpdatePipelineStatus(UpdatePipelineStatusRequest) returns (Jamaah);
  rpc BatchUpdateStatus(BatchUpdateStatusRequest) returns (BatchUpdateStatusResponse);
  
  // Package registration
  rpc RegisterToPackage(RegisterToPackageRequest) returns (JamaahPackageRegistration);
  rpc RemoveFromPackage(RemoveFromPackageRequest) returns (Empty);
  rpc ListJamaahByPackage(ListJamaahByPackageRequest) returns (ListJamaahResponse);
  
  // Follow-ups & Notes
  rpc AddNote(AddNoteRequest) returns (JamaahNote);
  rpc ListNotes(ListNotesRequest) returns (ListNotesResponse);
  rpc AddFollowUp(AddFollowUpRequest) returns (FollowUp);
  rpc ListFollowUps(ListFollowUpsRequest) returns (ListFollowUpsResponse);
  
  // Documents
  rpc UploadDocument(UploadDocumentRequest) returns (JamaahDocument);
  rpc UpdateDocumentStatus(UpdateDocumentStatusRequest) returns (JamaahDocument);
  rpc ListDocuments(ListDocumentsRequest) returns (ListDocumentsResponse);
  
  // AI Scanner integration
  rpc ScanAndPopulate(ScanAndPopulateRequest) returns (ScanAndPopulateResponse);
  rpc ExportSiskopatuh(ExportSiskopatuhRequest) returns (ExportSiskopatuhResponse);
  
  // Alerts
  rpc GetDashboardAlerts(GetDashboardAlertsRequest) returns (DashboardAlerts);
}
```

**Database Schema** (`jamaah_crm`):

```sql
-- jamaah_profiles (master profile, persists across trips)
CREATE TABLE jamaah_profiles (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL,
    
    -- Identitas (32 kolom Siskopatuh + extended)
    title               VARCHAR(20) DEFAULT '',
    nama                VARCHAR(255) NOT NULL,
    nama_ayah           VARCHAR(255) DEFAULT '',
    jenis_identitas     VARCHAR(50) DEFAULT 'NIK',
    no_identitas        VARCHAR(50),           -- NIK KTP
    nama_paspor         VARCHAR(255) DEFAULT '',
    no_paspor           VARCHAR(50),
    tanggal_paspor      DATE,
    kota_paspor         VARCHAR(100) DEFAULT '',
    tempat_lahir        VARCHAR(100) DEFAULT '',
    tanggal_lahir       DATE,
    gender              VARCHAR(10) DEFAULT '', -- derived from title
    alamat              TEXT DEFAULT '',
    provinsi            VARCHAR(100) DEFAULT '',
    kabupaten           VARCHAR(100) DEFAULT '',
    kecamatan           VARCHAR(100) DEFAULT '',
    kelurahan           VARCHAR(100) DEFAULT '',
    no_telepon          VARCHAR(30) DEFAULT '',
    no_hp               VARCHAR(30) DEFAULT '',
    kewarganegaraan     VARCHAR(50) DEFAULT 'WNI',
    status_pernikahan   VARCHAR(50) DEFAULT '',
    pendidikan          VARCHAR(100) DEFAULT '',
    pekerjaan           VARCHAR(100) DEFAULT '',
    golongan_darah      VARCHAR(10) DEFAULT '',
    
    -- Visa fields
    provider_visa       VARCHAR(255) DEFAULT '',
    no_visa             VARCHAR(100) DEFAULT '',
    tanggal_visa        DATE,
    tanggal_visa_akhir  DATE,
    
    -- Asuransi
    asuransi            VARCHAR(255) DEFAULT '',
    no_polis            VARCHAR(100) DEFAULT '',
    tanggal_input_polis DATE,
    tanggal_awal_polis  DATE,
    tanggal_akhir_polis DATE,
    no_bpjs             VARCHAR(100) DEFAULT '',
    
    -- Kontak tambahan
    email               VARCHAR(255) DEFAULT '',
    contact_emergency_name VARCHAR(255) DEFAULT '',
    contact_emergency_phone VARCHAR(30) DEFAULT '',
    
    -- Source
    lead_source         VARCHAR(30) DEFAULT 'walk_in', -- walk_in, referral, online, agent
    referring_agent_id  UUID,           -- FK ke commission-service (Phase 4)
    
    -- Ukuran perlengkapan
    ihram_size          VARCHAR(10) DEFAULT '',  -- S/M/L/XL/XXL
    mukena_size         VARCHAR(10) DEFAULT '',
    baju_size           VARCHAR(10) DEFAULT '',
    
    -- Duplicate detection
    search_vector       TSVECTOR,  -- untuk full-text search
    
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT uq_no_identitas UNIQUE (org_id, no_identitas) WHERE no_identitas IS NOT NULL AND no_identitas != '',
    CONSTRAINT uq_no_paspor UNIQUE (org_id, no_paspor) WHERE no_paspor IS NOT NULL AND no_paspor != ''
);

CREATE INDEX idx_jamaah_org ON jamaah_profiles(org_id);
CREATE INDEX idx_jamaah_nama ON jamaah_profiles(org_id, nama);
CREATE INDEX idx_jamaah_search ON jamaah_profiles USING GIN(search_vector);

-- jamaah_package_registrations (jamaah dalam paket tertentu)
CREATE TABLE jamaah_package_registrations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL,
    jamaah_id       UUID NOT NULL REFERENCES jamaah_profiles(id) ON DELETE CASCADE,
    package_id      UUID NOT NULL,  -- merujuk ke package-service
    
    -- Harga snapshot (dari pricing_tiers saat pendaftaran)
    room_type       VARCHAR(20) NOT NULL, -- quad, triple, double, single
    price_snapshot  BIGINT NOT NULL,       -- harga paket saat daftar (frozen)
    discount_amount BIGINT DEFAULT 0,
    custom_price    BIGINT,                -- override harga individual (jika ada)
    
    -- Pipeline status
    pipeline_status VARCHAR(30) NOT NULL DEFAULT 'prospek', 
    -- prospek, survey, booking, dp, cicilan, lunas, berangkat, selesai, batal
    
    -- Important dates
    registered_at   TIMESTAMPTZ DEFAULT NOW(),
    dp_date         TIMESTAMPTZ,
    lunas_date      TIMESTAMPTZ,
    berangkat_date  TIMESTAMPTZ,
    
    -- Mahram
    mahram_id       UUID REFERENCES jamaah_profiles(id),  -- relasi ke jamaah lain
    
    -- Notes
    internal_notes  TEXT DEFAULT '',
    
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT uq_jamaah_package UNIQUE (jamaah_id, package_id)
);

CREATE INDEX idx_registration_org ON jamaah_package_registrations(org_id);
CREATE INDEX idx_registration_package ON jamaah_package_registrations(package_id);
CREATE INDEX idx_registration_status ON jamaah_package_registrations(org_id, pipeline_status);
CREATE INDEX idx_registration_jamaah ON jamaah_package_registrations(jamaah_id);

-- jamaah_notes (catatan internal per jamaah)
CREATE TABLE jamaah_notes (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jamaah_id   UUID NOT NULL REFERENCES jamaah_profiles(id) ON DELETE CASCADE,
    org_id      UUID NOT NULL,
    user_id     UUID NOT NULL,  -- siapa yang buat catatan
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notes_jamaah ON jamaah_notes(jamaah_id);

-- follow_ups (pengingat)
CREATE TABLE follow_ups (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jamaah_id       UUID NOT NULL REFERENCES jamaah_profiles(id) ON DELETE CASCADE,
    package_id      UUID,
    org_id          UUID NOT NULL,
    user_id         UUID NOT NULL,
    description     TEXT NOT NULL,
    due_date        TIMESTAMPTZ NOT NULL,
    is_completed    BOOLEAN DEFAULT FALSE,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_followups_due ON follow_ups(org_id, due_date, is_completed);

-- jamaah_documents (checklist dokumen)
CREATE TABLE jamaah_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jamaah_id       UUID NOT NULL REFERENCES jamaah_profiles(id) ON DELETE CASCADE,
    package_id      UUID,
    org_id          UUID NOT NULL,
    
    doc_type        VARCHAR(30) NOT NULL, -- ktp, kk, paspor, pas_foto, icv, visa, formulir, akta_nikah, akta_lahir, surat_mahram, surat_rekomendasi, other
    status          VARCHAR(20) NOT NULL DEFAULT 'belum_diterima', -- belum_diterima, diterima, diproses, selesai
    
    file_url        TEXT,        -- MinIO URL
    file_name       VARCHAR(255),
    file_size       BIGINT,
    
    notes           TEXT DEFAULT '',
    verified_by     UUID,       -- user yang verify
    verified_at     TIMESTAMPTZ,
    
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_docs_jamaah ON jamaah_documents(jamaah_id);
CREATE INDEX idx_docs_type_status ON jamaah_documents(org_id, doc_type, status);
```

---

### 3.5 Invoice Service (`cmd/invoice-service`)

**Port**: 50054 (gRPC)  
**Database**: `jamaah_invoice`

**Fungsi**:
- Invoice lifecycle (create, update, cancel)
- Skema pembayaran (DP+pelunasan, cicilan bebas, lunas langsung)
- Rekam pembayaran (penerimaan dari jamaah)
- Pembatalan & refund (Phase 3, schema disiapkan)
- Kwitansi & invoice PDF generation
- Dashboard piutang

**gRPC Methods**:
```protobuf
service InvoiceService {
  // Invoice CRUD
  rpc CreateInvoice(CreateInvoiceRequest) returns (Invoice);
  rpc GetInvoice(GetInvoiceRequest) returns (Invoice);
  rpc UpdateInvoice(UpdateInvoiceRequest) returns (Invoice);
  rpc CancelInvoice(CancelInvoiceRequest) returns (Invoice);
  rpc ListInvoices(ListInvoicesRequest) returns (ListInvoicesResponse);
  
  // Payment schedules (cicilan)
  rpc CreatePaymentSchedule(CreatePaymentScheduleRequest) returns (PaymentSchedule);
  rpc UpdatePaymentSchedule(UpdatePaymentScheduleRequest) returns (PaymentSchedule);
  
  // Payments (penerimaan uang)
  rpc RecordPayment(RecordPaymentRequest) returns (Payment);
  rpc UpdatePayment(UpdatePaymentRequest) returns (Payment);
  rpc DeletePayment(DeletePaymentRequest) returns (Empty);
  rpc ListPayments(ListPaymentsRequest) returns (ListPaymentsResponse);
  
  // Kwitansi / Invoice PDF
  rpc GenerateInvoicePDF(GenerateInvoicePDFRequest) returns (PDFResponse);
  rpc GenerateKwitansiPDF(GenerateKwitansiPDFRequest) returns (PDFResponse);
  rpc GeneratePaymentCardPDF(GeneratePaymentCardPDFRequest) returns (PDFResponse);
  
  // Dashboard
  rpc GetPiutangSummary(GetPiutangSummaryRequest) returns (PiutangSummary);
  rpc GetPiutangAging(GetPiutangAgingRequest) returns (PiutangAgingResponse);
  rpc GetOverdueList(GetOverdueListRequest) returns (ListInvoicesResponse);
}
```

**Database Schema** (`jamaah_invoice`):

```sql
-- invoices
CREATE TABLE invoices (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL,
    invoice_number      VARCHAR(30) UNIQUE NOT NULL,  -- INV/2025/MMDD/XXXX
    jamaah_id           UUID NOT NULL,
    package_id          UUID NOT NULL,
    registration_id     UUID NOT NULL,  -- merujuk ke jamaah_package_registrations
    
    -- Pricing
    room_type           VARCHAR(20) NOT NULL,
    price_snapshot      BIGINT NOT NULL,   -- harga paket saat invoice dibuat
    discount_amount     BIGINT DEFAULT 0,
    surcharge_amount    BIGINT DEFAULT 0,  -- biaya tambahan (perlengkapan, upgrade, dll)
    total_amount        BIGINT NOT NULL,   -- price - discount + surcharge
    amount_paid         BIGINT NOT NULL DEFAULT 0,
    amount_remaining    BIGINT NOT NULL DEFAULT 0,  -- total_amount - amount_paid
    
    -- Payment scheme
    payment_scheme      VARCHAR(20) NOT NULL, -- dp_lunas, cicilan_bebas, lunas_langsung
    
    -- Status
    status              VARCHAR(20) NOT NULL DEFAULT 'belum_bayar', -- belum_bayar, sebagian, lunas, dibatalkan
    
    -- Dates
    issued_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    due_date            TIMESTAMPTZ,          -- jatuh tempo pelunasan
    cancelled_at        TIMESTAMPTZ,
    cancelled_reason    TEXT,
    
    notes               TEXT DEFAULT '',
    
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_invoices_org ON invoices(org_id);
CREATE INDEX idx_invoices_jamaah ON invoices(jamaah_id);
CREATE INDEX idx_invoices_package ON invoices(package_id);
CREATE INDEX idx_invoices_status ON invoices(org_id, status);
CREATE INDEX idx_invoices_number ON invoices(invoice_number);

-- payment_schedules (cicilan schedule)
CREATE TABLE payment_schedules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id      UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    installment_num INT NOT NULL,      -- 1, 2, 3, ...
    amount          BIGINT NOT NULL,
    due_date        TIMESTAMPTZ,
    description     VARCHAR(255),      -- e.g., "DP 30%", "Cicilan 1", "Pelunasan"
    is_paid         BOOLEAN DEFAULT FALSE,
    paid_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_schedules_invoice ON payment_schedules(invoice_id);

-- payments (penerimaan pembayaran dari jamaah)
CREATE TABLE payments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL,
    invoice_id      UUID NOT NULL REFERENCES invoices(id),
    
    amount          BIGINT NOT NULL,
    payment_method  VARCHAR(30) NOT NULL, -- transfer_bank, qris, tunai, cek, giro
    bank_name       VARCHAR(50),          -- jika transfer
    account_number  VARCHAR(50),          -- rekening tujuan
    reference_number VARCHAR(100),        -- nomor referensi/bukti transfer
    proof_url       TEXT,                 -- URL bukti bayar di MinIO
    
    notes           TEXT DEFAULT '',
    received_by     UUID NOT NULL,        -- user yang input
    
    paid_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_payments_invoice ON payments(invoice_id);
CREATE INDEX idx_payments_org_date ON payments(org_id, paid_at);
```

**NATS Events yang dipublish**:
- `payment.completed` → Finance Service (update P&L), Commission Service (Phase 4), Notification Service

---

### 3.6 Finance Service (`cmd/finance-service`)

**Port**: 50055 (gRPC)  
**Database**: `jamaah_finance`

**Fungsi**:
- P&L per trip (pendapatan - pengeluaran = profit)
- Dashboard owner (ringkasan keuangan)
- Laporan piutang aging
- Laporan arus kas proyeksi
- Export laporan ke Excel

**gRPC Methods**:
```protobuf
service FinanceService {
  // P&L
  rpc GetTripPL(GetTripPLRequest) returns (TripPL);
  rpc ListTripPLs(ListTripPLsRequest) returns (ListTripPLsResponse);
  
  // Dashboard
  rpc GetOwnerDashboard(GetOwnerDashboardRequest) returns (OwnerDashboard);
  
  // Reports
  rpc GetPiutangAgingReport(GetPiutangAgingReportRequest) returns (PiutangAgingReport);
  rpc GetCashFlowProjection(GetCashFlowProjectionRequest) returns (CashFlowProjection);
  rpc GetDailyCashReport(GetDailyCashReportRequest) returns (DailyCashReport);
  
  // Vendor expenses (basic, for P&L)
  rpc CreateTripExpense(CreateTripExpenseRequest) returns (TripExpense);
  rpc UpdateTripExpense(UpdateTripExpenseRequest) returns (TripExpense);
  rpc DeleteTripExpense(DeleteTripExpenseRequest) returns (Empty);
  rpc ListTripExpenses(ListTripExpensesRequest) returns (ListTripExpensesResponse);
  
  // Export
  rpc ExportReportToExcel(ExportReportRequest) returns (ExcelResponse);
}
```

**Database Schema** (`jamaah_finance`):

```sql
-- trip_expenses (pengeluaran per trip untuk P&L)
CREATE TABLE trip_expenses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL,
    package_id      UUID NOT NULL,
    
    category        VARCHAR(50) NOT NULL, -- flight, hotel_makkah, hotel_madinah, visa, transport, guide, equipment, catering, other
    description     VARCHAR(255) NOT NULL,
    vendor_name     VARCHAR(255),          -- opsional, merujuk ke vendor (Phase 2)
    amount          BIGINT NOT NULL,
    currency        VARCHAR(3) DEFAULT 'IDR',
    exchange_rate   DECIMAL(12,4) DEFAULT 1.0,
    amount_idr      BIGINT GENERATED ALWAYS AS (amount * exchange_rate::BIGINT) STORED,
    
    expense_date    DATE NOT NULL,
    due_date        DATE,
    status          VARCHAR(20) DEFAULT 'belum_bayar', -- belum_bayar, sebagian, lunas
    
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_expenses_package ON trip_expenses(package_id);
CREATE INDEX idx_expenses_org_date ON trip_expenses(org_id, expense_date);
```

---

### 3.7 AI/OCR Service (`cmd/ai-ocr-service`)

**Port**: 50056 (gRPC)  
**Database**: `jamaah_aiocr`

**Fungsi**:
- Upload & OCR dokumen (KTP, KK, Paspor, Visa)
- Gemini Vision integration
- AI Cache (gambar yang sudah diproses tidak perlu bayar ulang)
- Siskopatuh normalization (dipindahkan dari v1)
- Batch processing (hingga 50 file per request)
- Export 32 kolom Siskopatuh ke Excel

**gRPC Methods**:
```protobuf
service AIOCRService {
  // Scan
  rpc ScanDocuments(ScanDocumentsRequest) returns (ScanDocumentsResponse);
  rpc GetScanResult(GetScanResultRequest) returns (ScanResult);
  rpc ListScanResults(ListScanResultsRequest) returns (ListScanResultsResponse);
  
  // Siskopatuh normalization + export
  rpc NormalizeToSiskopatuh(NormalizeToSiskopatuhRequest) returns (NormalizedData);
  rpc ExportSiskopatuhExcel(ExportSiskopatuhExcelRequest) returns (ExcelResponse);
  
  // Cache management
  rpc GetCacheStats(GetCacheStatsRequest) returns (CacheStats);
  rpc ClearCache(ClearCacheRequest) returns (Empty);
}
```

**Database Schema** (`jamaah_aiocr`):

```sql
-- scan_jobs (batch scan request)
CREATE TABLE scan_jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL,
    user_id         UUID NOT NULL,
    package_id      UUID,           -- opsional, kalau langsung assign ke paket
    status          VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
    total_files     INT NOT NULL DEFAULT 0,
    processed_files INT NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scan_jobs_org ON scan_jobs(org_id);
CREATE INDEX idx_scan_jobs_status ON scan_jobs(org_id, status);

-- scan_results (hasil OCR per file)
CREATE TABLE scan_results (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_job_id     UUID NOT NULL REFERENCES scan_jobs(id) ON DELETE CASCADE,
    org_id          UUID NOT NULL,
    
    -- Input
    file_name       VARCHAR(255) NOT NULL,
    file_url        TEXT NOT NULL,         -- MinIO URL
    file_size       BIGINT,
    file_hash       VARCHAR(64) NOT NULL,  -- SHA-256 untuk cache key
    
    -- Document type detection
    doc_type        VARCHAR(20), -- ktp, kk, paspor, visa, unknown
    
    -- Extracted data (32 kolom Siskopatuh format)
    extracted_data  JSONB NOT NULL DEFAULT '{}',
    
    -- Normalized data (setelah _map_value)
    normalized_data JSONB DEFAULT '{}',
    
    -- Validation
    validation_errors JSONB DEFAULT '[]',
    
    -- AI Cache
    cache_hit       BOOLEAN DEFAULT FALSE,
    model_used      VARCHAR(50) DEFAULT 'gemini-2.0-flash',
    prompt_version  VARCHAR(20) DEFAULT 'v1',
    
    -- Status
    status          VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
    error_message   TEXT,
    
    processing_time_ms INT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scan_results_job ON scan_results(scan_job_id);
CREATE INDEX idx_scan_results_hash ON scan_results(file_hash);

-- ai_cache (persistent cache untuk hasil OCR)
CREATE TABLE ai_cache (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    input_hash      VARCHAR(64) UNIQUE NOT NULL,
    model           VARCHAR(50) NOT NULL,
    prompt_version  VARCHAR(20) NOT NULL,
    task_type       VARCHAR(50) NOT NULL,
    result_json     JSONB NOT NULL,
    hits            INT DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_ai_cache_hash ON ai_cache(input_hash);
CREATE INDEX idx_ai_cache_expires ON ai_cache(expires_at);

-- export_templates (reuse dari v1)
CREATE TABLE export_templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL,
    user_id         UUID NOT NULL,
    name            VARCHAR(100) NOT NULL,
    file_url        TEXT NOT NULL,
    column_mapping  JSONB NOT NULL,
    header_row      INT DEFAULT 1,
    data_start_row  INT DEFAULT 2,
    is_default      BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_export_templates_org ON export_templates(org_id);
```

---

## 4. NATS Event Catalog

Setiap service mempublish dan subscribe ke event tertentu. Ini mencegah tight coupling antar service.

| Event | Publisher | Subscriber | Payload |
|-------|-----------|------------|---------|
| `jamaah.registered` | Jamaica Service | Invoice Service, Notification Service | `{jamaah_id, package_id, registration_id}` |
| `jamaah.status_changed` | Jamaica Service | Invoice Service, Notification Service | `{jamaah_id, old_status, new_status, package_id}` |
| `payment.completed` | Invoice Service | Finance Service, Notification Service | `{invoice_id, jamaah_id, amount, payment_method}` |
| `payment.overdue` | Invoice Service | Notification Service | `{invoice_id, jamaah_id, days_overdue}` |
| `package.seats_updated` | Package Service | Notification Service | `{package_id, reserved_seats, total_seats}` |
| `expense.recorded` | Finance Service | Notification Service | `{package_id, category, amount}` |
| `document.uploaded` | Jamaica Service | AI/OCR Service | `{jamaah_id, doc_type, file_url}` |
| `scan.completed` | AI/OCR Service | Jamaica Service | `{scan_result_id, jamaah_id, normalized_data}` |
| `contract.signed` | (Phase 3) Contract Service | Notification Service | `{contract_id, jamaah_id}` |

---

## 5. Frontend API Contract (REST via Gateway)

Frontend Svelte tetap berkomunikasi via REST JSON ke API Gateway. Gateway menerjemahkan ke gRPC.

### 5.1 Auth

```
POST   /api/v1/auth/register          → Auth.Register
POST   /api/v1/auth/login             → Auth.Login
POST   /api/v1/auth/refresh           → Auth.RefreshToken
POST   /api/v1/auth/logout            → Auth.RevokeToken
GET    /api/v1/auth/me                → Auth.GetUser
PUT    /api/v1/auth/me                → Auth.UpdateUser

POST   /api/v1/orgs                   → Auth.CreateOrganization
GET    /api/v1/orgs/:id               → Auth.GetOrganization
PUT    /api/v1/orgs/:id               → Auth.UpdateOrganization
GET    /api/v1/orgs/:id/members       → Auth.ListTeamMembers
POST   /api/v1/orgs/:id/members       → Auth.AddTeamMember
DELETE /api/v1/orgs/:id/members/:uid  → Auth.RemoveTeamMember
PUT    /api/v1/orgs/:id/members/:uid  → Auth.UpdateMemberRole
POST   /api/v1/orgs/:id/invite        → Auth.InviteMember
POST   /api/v1/invite/accept          → Auth.AcceptInvite
```

### 5.2 Packages

```
POST   /api/v1/packages                        → Package.CreatePackage
GET    /api/v1/packages                        → Package.ListPackages
GET    /api/v1/packages/:id                    → Package.GetPackage
PUT    /api/v1/packages/:id                    → Package.UpdatePackage
DELETE /api/v1/packages/:id                    → Package.DeletePackage
PATCH  /api/v1/packages/:id/status             → Package.UpdatePackageStatus

POST   /api/v1/packages/:id/tiers              → Package.CreatePricingTier
PUT    /api/v1/packages/:id/tiers/:tid         → Package.UpdatePricingTier
DELETE /api/v1/packages/:id/tiers/:tid         → Package.DeletePricingTier

POST   /api/v1/packages/:id/costs              → Package.CreateCostComponent
PUT    /api/v1/packages/:id/costs/:cid         → Package.UpdateCostComponent
DELETE /api/v1/packages/:id/costs/:cid         → Package.DeleteCostComponent

GET    /api/v1/packages/:id/quota              → Package.GetPackageQuota
GET    /api/v1/packages/:slug                   → Package.GetPackageBySlug  (public)
```

### 5.3 Jamaica

```
POST   /api/v1/jamaah                          → Jamaica.CreateJamaah
GET    /api/v1/jamaah                           → Jamaica.ListJamaah
GET    /api/v1/jamaah/:id                       → Jamaica.GetJamaah
PUT    /api/v1/jamaah/:id                       → Jamaica.UpdateJamaah
DELETE /api/v1/jamaah/:id                       → Jamaica.DeleteJamaah
GET    /api/v1/jamaah/search                    → Jamaica.SearchJamaah

PATCH  /api/v1/jamaah/:id/status                → Jamaica.UpdatePipelineStatus
POST   /api/v1/jamaah/:id/register/:pkgId       → Jamaica.RegisterToPackage
DELETE /api/v1/jamaah/:id/register/:pkgId        → Jamaica.RemoveFromPackage
GET    /api/v1/packages/:pkgId/jamaah            → Jamaica.ListJamaahByPackage

POST   /api/v1/jamaah/:id/notes                 → Jamaica.AddNote
GET    /api/v1/jamaah/:id/notes                  → Jamaica.ListNotes
POST   /api/v1/jamaah/:id/follow-ups            → Jamaica.AddFollowUp
GET    /api/v1/jamaah/:id/follow-ups             → Jamaica.ListFollowUps

POST   /api/v1/jamaah/:id/documents             → Jamaica.UploadDocument
PATCH  /api/v1/jamaah/:id/documents/:did         → Jamaica.UpdateDocumentStatus
GET    /api/v1/jamaah/:id/documents              → Jamaica.ListDocuments

POST   /api/v1/scan                             → AIOCR.ScanDocuments
GET    /api/v1/scan/:id                          → AIOCR.GetScanResult

POST   /api/v1/export/siskopatuh                 → AIOCR.ExportSiskopatuhExcel
```

### 5.4 Invoice

```
POST   /api/v1/invoices                          → Invoice.CreateInvoice
GET    /api/v1/invoices                           → Invoice.ListInvoices
GET    /api/v1/invoices/:id                       → Invoice.GetInvoice
PUT    /api/v1/invoices/:id                       → Invoice.UpdateInvoice
POST   /api/v1/invoices/:id/cancel                → Invoice.CancelInvoice

POST   /api/v1/invoices/:id/schedules             → Invoice.CreatePaymentSchedule
PUT    /api/v1/invoices/:id/schedules/:sid         → Invoice.UpdatePaymentSchedule

POST   /api/v1/invoices/:id/payments              → Invoice.RecordPayment
PUT    /api/v1/invoices/:id/payments/:pid          → Invoice.UpdatePayment
DELETE /api/v1/invoices/:id/payments/:pid          → Invoice.DeletePayment
GET    /api/v1/invoices/:id/payments               → Invoice.ListPayments

GET    /api/v1/invoices/:id/pdf                   → Invoice.GenerateInvoicePDF
GET    /api/v1/invoices/:id/kwitansi/:pid         → Invoice.GenerateKwitansiPDF
GET    /api/v1/invoices/:id/card                  → Invoice.GeneratePaymentCardPDF

GET    /api/v1/piutang/summary                    → Invoice.GetPiutangSummary
GET    /api/v1/piutang/aging                      → Invoice.GetPiutangAging
GET    /api/v1/piutang/overdue                    → Invoice.GetOverdueList
```

### 5.5 Finance

```
GET    /api/v1/finance/dashboard                  → Finance.GetOwnerDashboard
GET    /api/v1/finance/trip-pl                     → Finance.ListTripPLs
GET    /api/v1/finance/trip-pl/:pkgId              → Finance.GetTripPL

POST   /api/v1/finance/expenses                   → Finance.CreateTripExpense
PUT    /api/v1/finance/expenses/:id                → Finance.UpdateTripExpense
DELETE /api/v1/finance/expenses/:id                → Finance.DeleteTripExpense
GET    /api/v1/finance/expenses?package_id=        → Finance.ListTripExpenses

GET    /api/v1/finance/aging                       → Finance.GetPiutangAgingReport
GET    /api/v1/finance/cash-flow                   → Finance.GetCashFlowProjection
GET    /api/v1/finance/daily-cash                  → Finance.GetDailyCashReport

GET    /api/v1/finance/export/excel                 → Finance.ExportReportToExcel
```

---

## 6. Tech Stack Detail

### Shared Libraries (`internal/shared/`)

| Package | Fungsi |
|---------|--------|
| `shared/database` | PostgreSQL connection pool, migration helpers |
| `shared/redis` | Redis client, helpers (rate limit, cache, JWT blacklist) |
| `shared/nats` | NATS JetStream client, publish/subscribe helpers |
| `shared/auth` | JWT validation middleware (RS256), role check, org context |
| `shared/response` | Standard HTTP response types (success, error, paginated) |
| `shared/pagination` | Cursor-based pagination helpers |
| `shared/validator` | Custom struct validators (NIK, phone, etc.) |
| `shared/minio` | MinIO client helpers (upload, download, presigned URL) |
| `shared/logger` | Zap logger configuration |
| `shared/config` | Viper config loader (env, yaml, flags) |
| `shared/interceptors` | gRPC interceptors (auth, logging, recovery) |

### Setiap Service: Struktur Internal

```
cmd/auth-service/
├── main.go                    # Entry point, wire dependencies
├── Dockerfile
├── go.mod
├── go.sum
└── internal/
    ├── config/                 # Viper config
    ├── repository/             # Database queries (sqlc generated)
    ├── service/                # Business logic
    ├── handler/                # gRPC handlers
    ├── middleware/             # Service-specific middleware
    └── model/                  # Domain models (Go structs)
```

### Key Libraries per Service

| Concern | Library |
|---------|---------|
| HTTP routing (Gateway) | github.com/gofiber/fiber/v2 |
| gRPC | google.golang.org/grpc |
| Protocol Buffers | google.golang.org/protobuf |
| PostgreSQL driver | github.com/jackc/pgx/v5 |
| SQL queries | github.com/sqlc-dev/sqlc |
| Migrations | github.com/golang-migrate/migrate/v4 |
| JWT | github.com/golang-jwt/jwt/v5 |
| Validation | github.com/go-playground/validator/v10 |
| Logging | go.uber.org/zap |
| Config | github.com/spf13/viper |
| UUID | github.com/google/uuid |
| Natural sort | github.com/fvbommel/sortorder |
| Excel (export) | github.com/xuri/excelize/v2 |
| PDF generation | github.com/go-pdf/fpdf |
| MinIO SDK | github.com/minio/minio-go/v7 |
| Redis | github.com/redis/go-redis/v9 |
| NATS | github.com/nats-io/nats.go |

---

## 7. Infrastructure: Docker Compose

### `deployments/docker-compose.yml`

```yaml
version: "3.9"

services:
  # ===== Data Layer =====
  postgres:
    image: postgres:16-alpine
    container_name: jamaah-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: jamaah
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "127.0.0.1:5433:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./scripts/init-dbs.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U jamaah"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: jamaah-redis
    restart: unless-stopped
    ports:
      - "127.0.0.1:6379:6379"
    volumes:
      - redisdata:/data

  nats:
    image: nats:2-alpine
    container_name: jamaah-nats
    restart: unless-stopped
    ports:
      - "127.0.0.1:4222:4222"
    command: ["--jetstream", "--store_dir", "/data"]
    volumes:
      - natsdata:/data

  minio:
    image: minio/minio
    container_name: jamaah-minio
    restart: unless-stopped
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    ports:
      - "127.0.0.1:9000:9000"
      - "127.0.0.1:9001:9001"
    volumes:
      - miniodata:/data
    command: server /data --console-address ":9001"

  # ===== Application Services =====
  api-gateway:
    build:
      context: ../
      dockerfile: deployments/Dockerfile.gateway
    container_name: jamaah-gateway
    restart: unless-stopped
    ports:
      - "8000:8080"
    environment:
      - AUTH_SERVICE_ADDR=auth-service:50051
      - PACKAGE_SERVICE_ADDR=package-service:50052
      - JAMAAH_SERVICE_ADDR=jamaah-service:50053
      - INVOICE_SERVICE_ADDR=invoice-service:50054
      - FINANCE_SERVICE_ADDR=finance-service:50055
      - AIOCR_SERVICE_ADDR=ai-ocr-service:50056
      - JWT_PUBLIC_KEY=${JWT_PUBLIC_KEY}
      - REDIS_ADDR=redis:6379
    depends_on:
      - auth-service
      - package-service
      - jamaah-service
      - invoice-service
      - finance-service
      - ai-ocr-service

  auth-service:
    build:
      context: ../
      dockerfile: deployments/Dockerfile.auth
    container_name: jamaah-auth
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgres://jamaah:${POSTGRES_PASSWORD}@postgres:5432/jamaah_auth?sslmode=disable
      - NATS_ADDR=nats:4222
      - JWT_PRIVATE_KEY=${JWT_PRIVATE_KEY}
      - JWT_PUBLIC_KEY=${JWT_PUBLIC_KEY}
    depends_on:
      postgres:
        condition: service_healthy

  package-service:
    build:
      context: ../
      dockerfile: deployments/Dockerfile.package
    container_name: jamaah-package
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgres://jamaah:${POSTGRES_PASSWORD}@postgres:5432/jamaah_package?sslmode=disable
      - NATS_ADDR=nats:4222
    depends_on:
      postgres:
        condition: service_healthy

  jamaah-service:
    build:
      context: ../
      dockerfile: deployments/Dockerfile.jamaah
    container_name: jamaah-crm
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgres://jamaah:${POSTGRES_PASSWORD}@postgres:5432/jamaah_crm?sslmode=disable
      - NATS_ADDR=nats:4222
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=${MINIO_ROOT_USER}
      - MINIO_SECRET_KEY=${MINIO_ROOT_PASSWORD}
    depends_on:
      postgres:
        condition: service_healthy

  invoice-service:
    build:
      context: ../
      dockerfile: deployments/Dockerfile.invoice
    container_name: jamaah-invoice
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgres://jamaah:${POSTGRES_PASSWORD}@postgres:5432/jamaah_invoice?sslmode=disable
      - NATS_ADDR=nats:4222
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=${MINIO_ROOT_USER}
      - MINIO_SECRET_KEY=${MINIO_ROOT_PASSWORD}
    depends_on:
      postgres:
        condition: service_healthy

  finance-service:
    build:
      context: ../
      dockerfile: deployments/Dockerfile.finance
    container_name: jamaah-finance
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgres://jamaah:${POSTGRES_PASSWORD}@postgres:5432/jamaah_finance?sslmode=disable
      - NATS_ADDR=nats:4222
    depends_on:
      postgres:
        condition: service_healthy

  ai-ocr-service:
    build:
      context: ../
      dockerfile: deployments/Dockerfile.aiocr
    container_name: jamaah-aiocr
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgres://jamaah:${POSTGRES_PASSWORD}@postgres:5432/jamaah_aiocr?sslmode=disable
      - NATS_ADDR=nats:4222
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=${MINIO_ROOT_USER}
      - MINIO_SECRET_KEY=${MINIO_ROOT_PASSWORD}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    depends_on:
      postgres:
        condition: service_healthy

  # ===== Frontend =====
  frontend:
    build:
      context: ../frontend-svelte
      dockerfile: Dockerfile
    container_name: jamaah-frontend
    restart: unless-stopped
    ports:
      - "8005:80"
    depends_on:
      - api-gateway

volumes:
  pgdata:
  redisdata:
  natsdata:
  miniodata:
```

### Database Init Script (`scripts/init-dbs.sql`)

```sql
-- Create databases for each service
CREATE DATABASE jamaah_auth;
CREATE DATABASE jamaah_package;
CREATE DATABASE jamaah_crm;
CREATE DATABASE jamaah_invoice;
CREATE DATABASE jamaah_finance;
CREATE DATABASE jamaah_aiocr;
```

---

## 8. Implementasi Order & Milestones

### Milestone 1: Foundation (Minggu 1-2)

**Goal**: Project scaffolding, shared libs, Auth Service bisa login

| # | Task | Detail |
|---|------|--------|
| 1.1 | Init monorepo | go.work, Makefile, .env.example, Docker Compose |
| 1.2 | Proto definitions | Auth service protobuf + generate Go code |
| 1.3 | Shared libraries | database, redis, nats, auth, response, pagination, logger, config |
| 1.4 | Docker Compose infra | PostgreSQL (multi-db), Redis, NATS, MinIO |
| 1.5 | Auth Service | Register, Login, JWT, RefreshToken, RBAC, Organization, TeamInvite |
| 1.6 | Auth Service DB | Migrations untuk jamaah_auth |
| 1.7 | API Gateway basic | Fiber server, JWT middleware, proxy to Auth Service |
| 1.8 | Seed script | Script untuk create test org + users |

**Deliverable**: User bisa register, login, dapat JWT. Gateway menerima JWT dan mengvalidasi.

### Milestone 2: Package Service (Minggu 3-4)

**Goal**: CRUD paket umroh lengkap dengan pricing & cost breakdown

| # | Task | Detail |
|---|------|--------|
| 2.1 | Proto definitions | Package service protobuf |
| 2.2 | Package Service | CRUD paket, pricing tiers, cost components |
| 2.3 | Package DB | Migrations untuk jamaah_package |
| 2.4 | Quota tracking | package.seats_updated event via NATS |
| 2.5 | Publish/slug | Public package page endpoint |
| 2.6 | Gateway routes | REST routes untuk /api/v1/packages/* |
| 2.7 | Integration test | CRUD + pricing + cost breakdown test |

**Deliverable**: Admin bisa create paket umroh dengan tier harga dan komponen biaya, lihat proyeksi profit.

### Milestone 3: Jamaica/CRM Service (Minggu 5-7)

**Goal**: Profil jamaah, pipeline, dokumen, AI Scanner integration

| # | Task | Detail |
|---|------|--------|
| 3.1 | Proto definitions | Jamaica service protobuf |
| 3.2 | Jamaica Profile CRUD | Create, read, update, search jamaah |
| 3.3 | Pipeline status | Status transition, event publish |
| 3.4 | Package registration | Register jamaah to package, NATS event to Package Service |
| 3.5 | Notes & Follow-ups | Internal notes, follow-up reminders |
| 3.6 | Document checklist | Upload, status tracking, MinIO integration |
| 3.7 | AI Scanner migration | Port Gemini Vision integration + Siskopatuh normalization from v1 |
| 3.8 | Siskopatuh export | Export 32 kolom ke Excel |
| 3.9 | Dashboard alerts | Passport expiry, overdue follow-ups |
| 3.10 | Gateway routes | REST routes untuk /api/v1/jamaah/*, /api/v1/scan/* |

**Deliverable**: Admin bisa daftarkan jamaah, update pipeline, upload dokumen, scan KTP/paspor, export Siskopatuh.

### Milestone 4: Invoice Service (Minggu 8-10)

**Goal**: Full invoice lifecycle, payment recording, kwitansi PDF

| # | Task | Detail |
|---|------|--------|
| 4.1 | Proto definitions | Invoice service protobuf |
| 4.2 | Invoice CRUD | Create, update, cancel invoice |
| 4.3 | Payment schedule | DP+pelunasan, cicilan bebas, lunas langsung |
| 4.4 | Record payment | Payment recording, amount tracking, status update |
| 4.5 | NATS events | payment.completed event → Finance & Notification |
| 4.6 | PDF generation | Invoice PDF, kwitansi PDF, payment card PDF (fpdf) |
| 4.7 | Piutang dashboard | Summary, aging, overdue list |
| 4.8 | Payment event → jamaah status | Invoice publishes payment.completed → Jamaica updates pipeline status |
| 4.9 | Gateway routes | REST routes untuk /api/v1/invoices/*, /api/v1/piutang/* |

**Deliverable**: Admin bisa buat invoice, catat pembayaran, generate PDF kwitansi, lihat piutang.

### Milestone 5: Finance & Dashboard (Minggu 11-12)

**Goal**: P&L per trip, dashboard owner, laporan

| # | Task | Detail |
|---|------|--------|
| 5.1 | Proto definitions | Finance service protobuf |
| 5.2 | Trip expenses CRUD | Record vendor expenses per trip |
| 5.3 | P&L calculation | Pendapatan - pengeluaran = profit |
| 5.4 | Owner dashboard API | Ringkasan keuangan, overdue, alerts |
| 5.5 | Piutang aging report | 0-30, 31-60, 61-90, >90 hari |
| 5.6 | Cash flow projection | Proyeksi kas masuk dari cicilan |
| 5.7 | Excel export | All reports to .xlsx via excelize |
| 5.8 | Gateway routes | REST routes untuk /api/v1/finance/* |

**Deliverable**: Owner bisa lihat P&L per trip, dashboard keuangan, export laporan.

### Milestone 6: Polish & Deploy (Minggu 12+)

| # | Task | Detail |
|---|------|--------|
| 6.1 | Frontend update | Update Svelte API calls ke REST Gateway baru |
| 6.2 | Integration tests | End-to-end test flow: register → create package → add jamaah → create invoice → record payment → P&L |
| 6.3 | Docker Compose production | Optimized Dockerfiles, health checks, resource limits |
| 6.4 | CI/CD | GitHub Actions: lint, test, build, push to GHCR |
| 6.5 | Deploy to VPS | Restart all services, migrate data |
| 6.6 | Monitoring setup | Prometheus + Grafana basic dashboards |
| 6.7 | Data migration from v1 | Migrate existing users, groups, members to new schema |

---

## 9. Data Migration Plan (v1 → v2)

### Migrasi yang Perlu Dilakukan

| v1 Table | v2 Destination | Catatan |
|----------|---------------|---------|
| `users` | `jamaah_auth.users` | Password hash dipertahankan, role mapping |
| `organizations` | `jamaah_auth.organizations` | Langsung pindah |
| `team_members` | `jamaah_auth.team_members` | Role mapping: owner/admin/viewer |
| `groups` | `jamaah_package.packages` | Mapping: group name → package name, add departure/return dates (need manual input) |
| `group_members` | `jamaah_crm.jamaah_profiles` + `jamaah_crm.jamaah_package_registrations` | 32 kolom Siskopatuh → profile fields |
| `ai_result_cache` | `jamaah_aiocr.ai_cache` | Langsung pindah |
| `inventory_master` | Defer (Phase 3) | Tidak di-migrate di Phase 1 |
| `rooms` | Defer (Phase 2) | Tidak di-migrate di Phase 1 |
| `export_templates` | `jamaah_aiocr.export_templates` | Langsung pindah |
| `payments` (subscription) | Drop | Subscription payment akan di-rebuild |

### Migration Script

Buat Go binary terpisah (`cmd/migration/main.go`) yang:
1. Connect ke v1 DB (PostgreSQL)
2. Read semua data dari v1 tables
3. Transform & insert ke v2 databases (sesuai mapping di atas)
4. Generate UUID baru (v1 pakai integer ID, v2 pakai UUID)
5. Log setiap migrasi ke file untuk audit
6. Flag: `--dry-run` untuk test tanpa write

### Mapping Khusus

**`groups` → `packages`**:
- `name` → `name`
- `description` → `itinerary`
- `created_at` → `created_at`
- Perlu manual input: `departure_date`, `return_date`, `total_seats`, `package_type`, pricing tiers
- Group yang sudah ada di v1 akan dibuat sebagai package dengan status `done` (sudah berangkat)

**`group_members` → `jamaah_profiles` + `jamaah_package_registrations`**:
- 32 kolom Siskopatuh langsung map 1:1
- Setiap member jadi 1 row di `jamaah_profiles`
- Setiap member juga jadi 1 row di `jamaah_package_registrations` (link ke package yang sesuai)
- `pipeline_status` default: `selesai` (untuk data historis)

---

## 10. Frontend Changes Required

Frontend Svelte tetap digunakan, tapi API layer perlu di-update:

### Perubahan Besar

| Area | v1 | v2 |
|------|----|----|
| Auth | Login → dapat JWT | Sama, tapi JWT sekarang RS256 + org context |
| API base | Langsung ke backend 1 port | Semua via `/api/v1/*` di Gateway |
| Scanner flow | Upload → process → preview → download Excel | Upload → process → preview → save to jamaah profile OR download Excel |
| Groups | CRUD groups + members | CRUD packages (new) + jamaah registrations |
| Dashboard | Simple stats | Financial dashboard (P&L, piutang) |

### New Pages Needed

| Page | Fungsi |
|------|--------|
| `/dashboard` | Owner dashboard (keuangan, alerts) |
| `/packages` | Package CRUD |
| `/packages/:id` | Package detail + jamaah list |
| `/jamaah` | Jamaica list (all packages) |
| `/jamaah/:id` | Jamaica profile + pipeline + documents + invoice |
| `/invoices` | Invoice list |
| `/invoices/:id` | Invoice detail + payments + PDF |
| `/finance` | P&L, aging, cash flow |
| `/settings/organization` | Organization settings |
| `/settings/team` | Team management |

### Pages to Deprecate

| v1 Page | v2 Replacement |
|---------|---------------|
| Groups list | Packages list |
| Group detail | Package detail + Jamaica registrations |
| Scanner standalone page | Integrated into Jamaica profile |

---

## 11. Open Items & Decisions Needed

| # | Question | Options | Recommendation |
|---|----------|---------|---------------|
| 1 | **UUID vs int ID?** | UUID (string) vs int (auto-increment) | **UUID** — distributed, no ID collision across services |
| 2 | **IDR amount type?** | int64 (cents) vs float64 vs decimal | **int64** — semua dalam IDR tanpa sen, big int (rupiah penuh) |
| 3 | **gRPC vs REST antar service?** | Full gRPC atau gabung? | **Full gRPC** antar service, REST hanya di Gateway |
| 4 | **Database-per-service?** | 1 PG instance, multiple DB | **Ya** — 1 PG, 6 databases. Simple, tapi boundary jelas |
| 5 | **MinIO or local FS?** | MinIO vs `/uploads` | **MinIO** — S3-compatible, scalable, sudah ada di infra |
| 6 | **PDF library?** | fpdf vs wkhtmltopdf vs Chromium | **fpdf** untuk kwitansi sederhana, pertimbangkan Chromium headless nanti untuk kontrak |
| 7 | **Password hashing?** | bcrypt vs argon2 | **bcrypt** — sudah digunakan di v1, kompatibel untuk migrasi |
| 8 | **Error format?** | Custom vs gRPC status codes | **gRPC status codes** + detailed error info di `details` field |
| 9 | **Frontend state management?** | Svelte stores vs tanstack-query | **Pertahankan** pola Svelte stores yang sudah ada, update API calls |
| 10 | **Deployment strategy?** | Docker Compose vs k3s | **Docker Compose dulu** untuk Phase 1, migrate ke k3s di Phase 3+ |

---

## 12. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Scope creep | Stick to Phase 1 scope; Phase 2-4 services don't exist yet |
| v1 data loss during migration | Migration script with `--dry-run`, backup v1 DB first, parallel run |
| gRPC learning curve | Start with Gateway + Auth to build muscle; proto code generation reduces boilerplate |
| Frontend breaking changes | Keep v1 running on separate port during v2 development; switch over when ready |
| Single developer bottleneck | Prioritize vertical slices: Auth → Package → Jamaica → Invoice → Finance |
| NATS event ordering | Use NATS JetStream with durable consumers (not core NATS); at-least-once delivery |
| Service discovery in Docker Compose | Use Docker DNS (service names); Gateway reads service addrs from env vars |

---

## 13. Success Criteria Phase 1

| Criteria | Target |
|----------|--------|
| User bisa register & login | ✅ |
| Organization + team management berfungsi | ✅ |
| CRUD paket umroh dengan pricing & cost breakdown | ✅ |
| Jamaica profile bisa diisi manual atau via AI Scanner | ✅ |
| Pipeline status berfungsi (Prospek → Selesai) | ✅ |
| Invoice bisa dibuat & payment direkam | ✅ |
| Kwitansi PDF bisa digenerate | ✅ |
| P&L per trip bisa dilihat | ✅ |
| Siskopatuh 32 kolom export masih jalan | ✅ |
| Dashboard owner menampilkan piutang & overdue | ✅ |
| Data v1 bisa di-migrate ke v2 | ✅ |
| Deploy ke VPS via Docker Compose | ✅ |