CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS contract_templates (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    package_type VARCHAR(64),
    content TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_contract_templates_org ON contract_templates(org_id);
CREATE INDEX IF NOT EXISTS idx_contract_templates_package_type ON contract_templates(package_type);

CREATE TABLE IF NOT EXISTS contract_instances (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL,
    template_id UUID NOT NULL REFERENCES contract_templates(id) ON DELETE RESTRICT,
    jamaah_id UUID,
    package_id UUID,
    template_name VARCHAR(255) NOT NULL,
    package_type VARCHAR(64),
    recipient_name VARCHAR(255) NOT NULL,
    recipient_phone VARCHAR(64),
    recipient_email VARCHAR(255),
    public_token VARCHAR(128) NOT NULL UNIQUE,
    variables JSONB NOT NULL DEFAULT '{}'::jsonb,
    rendered_content TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'terkirim',
    expires_at TIMESTAMPTZ NOT NULL,
    signed_at TIMESTAMPTZ,
    signed_name VARCHAR(255),
    signature_mode VARCHAR(16),
    signature_value TEXT,
    signed_ip_address VARCHAR(64),
    document_hash VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_contract_instances_org ON contract_instances(org_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_contract_instances_status ON contract_instances(org_id, status);
CREATE INDEX IF NOT EXISTS idx_contract_instances_token ON contract_instances(public_token);
