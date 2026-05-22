-- jamaah_aiocr: AI/OCR Service migrations
-- Migration 001: Initial schema

CREATE TABLE scan_jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL,
    user_id         UUID NOT NULL,
    package_id      UUID,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    total_files     INT NOT NULL DEFAULT 0,
    processed_files INT NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE scan_results (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_job_id     UUID NOT NULL REFERENCES scan_jobs(id) ON DELETE CASCADE,
    org_id          UUID NOT NULL,
    file_name       VARCHAR(255) NOT NULL,
    file_url        TEXT NOT NULL,
    file_size       BIGINT,
    file_hash       VARCHAR(64) NOT NULL,
    doc_type        VARCHAR(20),
    extracted_data  JSONB NOT NULL DEFAULT '{}',
    normalized_data JSONB DEFAULT '{}',
    validation_errors JSONB DEFAULT '[]',
    cache_hit       BOOLEAN DEFAULT FALSE,
    model_used      VARCHAR(50) DEFAULT 'gemini-2.0-flash',
    prompt_version  VARCHAR(20) DEFAULT 'v1',
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    error_message   TEXT,
    processing_time_ms INT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

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

CREATE INDEX idx_scan_jobs_org ON scan_jobs(org_id);
CREATE INDEX idx_scan_jobs_status ON scan_jobs(org_id, status);
CREATE INDEX idx_scan_results_job ON scan_results(scan_job_id);
CREATE INDEX idx_scan_results_hash ON scan_results(file_hash);
CREATE INDEX idx_ai_cache_hash ON ai_cache(input_hash);
CREATE INDEX idx_ai_cache_expires ON ai_cache(expires_at);
CREATE INDEX idx_export_templates_org ON export_templates(org_id);