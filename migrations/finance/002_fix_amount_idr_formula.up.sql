-- Fix amount_idr formula: use proper decimal arithmetic before casting to bigint
-- Old: amount * exchange_rate::BIGINT (truncates exchange_rate decimals before multiply)
-- New: (amount * exchange_rate)::BIGINT (computes full decimal, then rounds)

ALTER TABLE trip_expenses DROP COLUMN amount_idr;
ALTER TABLE trip_expenses ADD COLUMN amount_idr BIGINT GENERATED ALWAYS AS ((amount * exchange_rate)::BIGINT) STORED;