-- Fixture-only candidate grain, never real addresses or publisher records.
-- One street label may identify multiple parcels; one parcel may have aliases.
CREATE TABLE synthetic_address_candidates (
    candidate_id TEXT PRIMARY KEY,
    display_address TEXT NOT NULL,
    search_key TEXT NOT NULL,
    pin TEXT NOT NULL REFERENCES parcels(pin),
    parcel_hint TEXT NOT NULL,
    UNIQUE (search_key, pin)
);
CREATE INDEX idx_fixture_candidate_search ON synthetic_address_candidates(search_key);
CREATE INDEX idx_fixture_candidate_parcel ON synthetic_address_candidates(pin);

-- Backfill each invented v1/v2 mapping without losing its selection ID.
INSERT INTO synthetic_address_candidates
    (candidate_id, display_address, search_key, pin, parcel_hint)
SELECT address_id, display_address, search_key, pin,
       'Synthetic parcel ' || CAST(pin AS BIGINT)
FROM synthetic_address_index;
