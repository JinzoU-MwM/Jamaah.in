-- jamaah_package: Package Service migrations
-- Migration 001: Initial schema

CREATE TABLE packages (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL,
    name                VARCHAR(255) NOT NULL,
    slug                VARCHAR(100) UNIQUE NOT NULL,
    description         TEXT,
    package_type        VARCHAR(30) NOT NULL DEFAULT 'umroh_reguler',
    departure_date      DATE NOT NULL,
    return_date         DATE NOT NULL,
    duration_days       INT GENERATED ALWAYS AS (return_date - departure_date + 1) STORED,
    total_seats         INT NOT NULL,
    reserved_seats      INT NOT NULL DEFAULT 0,
    airline             VARCHAR(100),
    flight_number_go    VARCHAR(30),
    flight_number_return VARCHAR(30),
    hotel_makkah_name   VARCHAR(255),
    hotel_makkah_stars  INT CHECK (hotel_makkah_stars BETWEEN 1 AND 5),
    hotel_makkah_nights INT,
    hotel_makkah_distance VARCHAR(30),
    hotel_madinah_name   VARCHAR(255),
    hotel_madinah_stars  INT CHECK (hotel_madinah_stars BETWEEN 1 AND 5),
    hotel_madinah_nights INT,
    hotel_madinah_distance VARCHAR(30),
    itinerary           TEXT,
    is_published        BOOLEAN DEFAULT FALSE,
    status              VARCHAR(20) NOT NULL DEFAULT 'draft',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_departure_before_return CHECK (departure_date <= return_date),
    CONSTRAINT chk_total_seats_positive CHECK (total_seats > 0)
);

CREATE TABLE pricing_tiers (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_id              UUID NOT NULL REFERENCES packages(id) ON DELETE CASCADE,
    room_type               VARCHAR(20) NOT NULL,
    price                   BIGINT NOT NULL,
    label                   VARCHAR(100),
    is_early_bird           BOOLEAN DEFAULT FALSE,
    early_bird_expires_at   TIMESTAMPTZ,
    custom_price_override   BIGINT,
    sort_order              INT DEFAULT 0,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_price_positive CHECK (price > 0)
);

CREATE TABLE cost_components (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_id           UUID NOT NULL REFERENCES packages(id) ON DELETE CASCADE,
    name                 VARCHAR(255) NOT NULL,
    category             VARCHAR(50) NOT NULL DEFAULT 'other',
    amount_per_person    BIGINT NOT NULL DEFAULT 0,
    quantity             INT NOT NULL DEFAULT 1,
    total_amount         BIGINT GENERATED ALWAYS AS (amount_per_person * quantity) STORED,
    sort_order           INT DEFAULT 0,
    created_at           TIMESTAMPTZ DEFAULT NOW(),
    updated_at           TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE package_documents (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_id  UUID NOT NULL REFERENCES packages(id) ON DELETE CASCADE,
    file_name   VARCHAR(255) NOT NULL,
    file_url    TEXT NOT NULL,
    file_type   VARCHAR(30) NOT NULL DEFAULT 'pdf',
    file_size   BIGINT,
    sort_order  INT DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_packages_org ON packages(org_id);
CREATE INDEX idx_packages_status ON packages(org_id, status);
CREATE INDEX idx_packages_slug ON packages(slug);
CREATE INDEX idx_packages_departure ON packages(org_id, departure_date);
CREATE INDEX idx_pricing_package ON pricing_tiers(package_id);
CREATE INDEX idx_cost_components_package ON cost_components(package_id);
CREATE INDEX idx_package_docs ON package_documents(package_id);