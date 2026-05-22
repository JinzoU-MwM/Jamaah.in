-- jamaah_finance: Finance Service migrations
-- Migration 001: Initial schema

CREATE TABLE trip_expenses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL,
    package_id      UUID NOT NULL,
    category        VARCHAR(50) NOT NULL DEFAULT 'other',
    description     VARCHAR(255) NOT NULL,
    vendor_name     VARCHAR(255),
    amount          BIGINT NOT NULL,
    currency        VARCHAR(3) DEFAULT 'IDR',
    exchange_rate   DECIMAL(12,4) DEFAULT 1.0,
    amount_idr      BIGINT GENERATED ALWAYS AS (amount * exchange_rate::BIGINT) STORED,
    expense_date    DATE NOT NULL,
    due_date        DATE,
    status          VARCHAR(20) DEFAULT 'belum_bayar',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_expenses_package ON trip_expenses(package_id);
CREATE INDEX idx_expenses_org_date ON trip_expenses(org_id, expense_date);
CREATE INDEX idx_expenses_status ON trip_expenses(org_id, status);