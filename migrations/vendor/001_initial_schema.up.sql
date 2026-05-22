-- jamaah_vendor: Vendor & Biaya Operasional Service migrations
-- Migration 001: Initial schema

CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE vendors (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL,
    name                VARCHAR(255) NOT NULL,
    type                VARCHAR(50) NOT NULL DEFAULT 'lainnya',
    npwp                VARCHAR(50),
    address             TEXT,
    pic_name            VARCHAR(255),
    pic_phone           VARCHAR(50),
    pic_email           VARCHAR(255),
    bank_name           VARCHAR(255),
    bank_account_number VARCHAR(50),
    bank_account_name   VARCHAR(255),
    notes               TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_vendors_org ON vendors(org_id);
CREATE INDEX idx_vendors_type ON vendors(org_id, type);
CREATE INDEX idx_vendors_name ON vendors USING gin(name gin_trgm_ops);

CREATE TABLE vendor_bills (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL,
    vendor_id       UUID NOT NULL REFERENCES vendors(id) ON DELETE RESTRICT,
    package_id      UUID NOT NULL,
    description     VARCHAR(500) NOT NULL,
    amount          BIGINT NOT NULL,
    currency        VARCHAR(3) DEFAULT 'IDR',
    exchange_rate   DECIMAL(12,4) DEFAULT 1.0,
    amount_idr      BIGINT GENERATED ALWAYS AS ((amount * exchange_rate)::BIGINT) STORED,
    paid_amount     BIGINT NOT NULL DEFAULT 0,
    due_date        DATE,
    status          VARCHAR(20) NOT NULL DEFAULT 'belum_bayar'
                    CHECK (status IN ('belum_bayar','sebagian','lunas')),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_vendor_bills_org ON vendor_bills(org_id);
CREATE INDEX idx_vendor_bills_vendor ON vendor_bills(vendor_id);
CREATE INDEX idx_vendor_bills_package ON vendor_bills(package_id);
CREATE INDEX idx_vendor_bills_status ON vendor_bills(org_id, status);
CREATE INDEX idx_vendor_bills_due ON vendor_bills(org_id, due_date);

CREATE TABLE vendor_payments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL,
    vendor_bill_id      UUID NOT NULL REFERENCES vendor_bills(id) ON DELETE RESTRICT,
    vendor_id           UUID NOT NULL REFERENCES vendors(id) ON DELETE RESTRICT,
    payment_date        DATE NOT NULL,
    amount              BIGINT NOT NULL,
    currency            VARCHAR(3) DEFAULT 'IDR',
    exchange_rate       DECIMAL(12,4) DEFAULT 1.0,
    amount_idr          BIGINT GENERATED ALWAYS AS ((amount * exchange_rate)::BIGINT) STORED,
    source_account      VARCHAR(255),
    transfer_proof_url  VARCHAR(500),
    notes               TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_vendor_payments_bill ON vendor_payments(vendor_bill_id);
CREATE INDEX idx_vendor_payments_vendor ON vendor_payments(vendor_id);
CREATE INDEX idx_vendor_payments_org ON vendor_payments(org_id);
CREATE INDEX idx_vendor_payments_date ON vendor_payments(org_id, payment_date);