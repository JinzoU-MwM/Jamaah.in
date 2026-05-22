-- jamaah_crm: Jamaica/CRM Service migrations
-- Migration 001: Initial schema

CREATE TABLE jamaah_profiles (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL,
    title               VARCHAR(20) DEFAULT '',
    nama                VARCHAR(255) NOT NULL DEFAULT '',
    nama_ayah           VARCHAR(255) DEFAULT '',
    jenis_identitas     VARCHAR(50) DEFAULT 'NIK',
    no_identitas        VARCHAR(50),
    nama_paspor         VARCHAR(255) DEFAULT '',
    no_paspor           VARCHAR(50),
    tanggal_paspor      DATE,
    kota_paspor         VARCHAR(100) DEFAULT '',
    tempat_lahir        VARCHAR(100) DEFAULT '',
    tanggal_lahir       DATE,
    gender              VARCHAR(10) DEFAULT '',
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
    provider_visa       VARCHAR(255) DEFAULT '',
    no_visa             VARCHAR(100) DEFAULT '',
    tanggal_visa        DATE,
    tanggal_visa_akhir  DATE,
    asuransi            VARCHAR(255) DEFAULT '',
    no_polis            VARCHAR(100) DEFAULT '',
    tanggal_input_polis DATE,
    tanggal_awal_polis  DATE,
    tanggal_akhir_polis DATE,
    no_bpjs             VARCHAR(100) DEFAULT '',
    email               VARCHAR(255) DEFAULT '',
    contact_emergency_name VARCHAR(255) DEFAULT '',
    contact_emergency_phone VARCHAR(30) DEFAULT '',
    lead_source         VARCHAR(30) DEFAULT 'walk_in',
    referring_agent_id UUID,
    ihram_size          VARCHAR(10) DEFAULT '',
    mukena_size         VARCHAR(10) DEFAULT '',
    baju_size           VARCHAR(10) DEFAULT '',
    search_vector       TSVECTOR,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE jamaah_package_registrations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id           UUID NOT NULL,
    jamaah_id       UUID NOT NULL REFERENCES jamaah_profiles(id) ON DELETE CASCADE,
    package_id       UUID NOT NULL,
    room_type        VARCHAR(20) NOT NULL DEFAULT 'quad',
    price_snapshot   BIGINT NOT NULL,
    discount_amount  BIGINT DEFAULT 0,
    custom_price     BIGINT,
    pipeline_status  VARCHAR(30) NOT NULL DEFAULT 'prospek',
    registered_at   TIMESTAMPTZ DEFAULT NOW(),
    dp_date          TIMESTAMPTZ,
    lunas_date       TIMESTAMPTZ,
    berangkat_date   TIMESTAMPTZ,
    mahram_id        UUID REFERENCES jamaah_profiles(id),
    internal_notes   TEXT DEFAULT '',
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_jamaah_package UNIQUE (jamaah_id, package_id)
);

CREATE TABLE jamaah_notes (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jamaah_id   UUID NOT NULL REFERENCES jamaah_profiles(id) ON DELETE CASCADE,
    org_id      UUID NOT NULL,
    user_id     UUID NOT NULL,
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

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

CREATE TABLE jamaah_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jamaah_id       UUID NOT NULL REFERENCES jamaah_profiles(id) ON DELETE CASCADE,
    package_id      UUID,
    org_id          UUID NOT NULL,
    doc_type        VARCHAR(30) NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'belum_diterima',
    file_url        TEXT,
    file_name       VARCHAR(255),
    file_size       BIGINT,
    notes           TEXT DEFAULT '',
    verified_by     UUID,
    verified_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_jamaah_org ON jamaah_profiles(org_id);
CREATE INDEX idx_jamaah_nama ON jamaah_profiles(org_id, nama);
CREATE INDEX idx_jamaah_search ON jamaah_profiles USING GIN(search_vector);
CREATE UNIQUE INDEX uq_no_identitas ON jamaah_profiles(org_id, no_identitas) WHERE no_identitas IS NOT NULL AND no_identitas != '';
CREATE UNIQUE INDEX uq_no_paspor ON jamaah_profiles(org_id, no_paspor) WHERE no_paspor IS NOT NULL AND no_paspor != '';
CREATE INDEX idx_registration_org ON jamaah_package_registrations(org_id);
CREATE INDEX idx_registration_package ON jamaah_package_registrations(package_id);
CREATE INDEX idx_registration_status ON jamaah_package_registrations(org_id, pipeline_status);
CREATE INDEX idx_registration_jamaah ON jamaah_package_registrations(jamaah_id);
CREATE INDEX idx_notes_jamaah ON jamaah_notes(jamaah_id);
CREATE INDEX idx_followups_due ON follow_ups(org_id, due_date, is_completed);
CREATE INDEX idx_docs_jamaah ON jamaah_documents(jamaah_id);
CREATE INDEX idx_docs_type_status ON jamaah_documents(org_id, doc_type, status);