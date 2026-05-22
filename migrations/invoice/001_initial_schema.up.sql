-- jamaah_invoice: Invoice Service migrations
-- Migration 001: Initial schema

CREATE TABLE invoices (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL,
    invoice_number      VARCHAR(30) UNIQUE NOT NULL,
    jamaah_id           UUID NOT NULL,
    package_id          UUID NOT NULL,
    registration_id     UUID NOT NULL,
    room_type           VARCHAR(20) NOT NULL DEFAULT 'quad',
    price_snapshot      BIGINT NOT NULL,
    discount_amount     BIGINT DEFAULT 0,
    surcharge_amount    BIGINT DEFAULT 0,
    total_amount        BIGINT NOT NULL,
    amount_paid         BIGINT NOT NULL DEFAULT 0,
    amount_remaining    BIGINT NOT NULL DEFAULT 0,
    payment_scheme      VARCHAR(20) NOT NULL DEFAULT 'dp_lunas',
    status              VARCHAR(20) NOT NULL DEFAULT 'belum_bayar',
    issued_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    due_date            TIMESTAMPTZ,
    cancelled_at        TIMESTAMPTZ,
    cancelled_reason    TEXT,
    notes               TEXT DEFAULT '',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE payment_schedules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id      UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    installment_num INT NOT NULL,
    amount          BIGINT NOT NULL,
    due_date        TIMESTAMPTZ,
    description     VARCHAR(255),
    is_paid         BOOLEAN DEFAULT FALSE,
    paid_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE payments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL,
    invoice_id      UUID NOT NULL REFERENCES invoices(id),
    amount          BIGINT NOT NULL,
    payment_method  VARCHAR(30) NOT NULL DEFAULT 'transfer_bank',
    bank_name       VARCHAR(50),
    account_number  VARCHAR(50),
    reference_number VARCHAR(100),
    proof_url       TEXT,
    notes           TEXT DEFAULT '',
    received_by     UUID NOT NULL,
    paid_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_invoices_org ON invoices(org_id);
CREATE INDEX idx_invoices_jamaah ON invoices(jamaah_id);
CREATE INDEX idx_invoices_package ON invoices(package_id);
CREATE INDEX idx_invoices_status ON invoices(org_id, status);
CREATE INDEX idx_invoices_number ON invoices(invoice_number);
CREATE INDEX idx_invoices_due ON invoices(org_id, due_date) WHERE status IN ('belum_bayar', 'sebagian');
CREATE INDEX idx_schedules_invoice ON payment_schedules(invoice_id);
CREATE INDEX idx_schedules_due ON payment_schedules(due_date) WHERE is_paid = FALSE;
CREATE INDEX idx_payments_invoice ON payments(invoice_id);
CREATE INDEX idx_payments_org_date ON payments(org_id, paid_at);