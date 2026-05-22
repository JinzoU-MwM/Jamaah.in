-- Revert: restore old truncated formula
ALTER TABLE trip_expenses DROP COLUMN amount_idr;
ALTER TABLE trip_expenses ADD COLUMN amount_idr BIGINT GENERATED ALWAYS AS (amount * exchange_rate::BIGINT) STORED;