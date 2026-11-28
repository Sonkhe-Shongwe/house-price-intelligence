-- PostgreSQL 17 synthetic compatibility baseline, not a production migration.

CREATE TABLE source_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    dataset_id TEXT NOT NULL,
    extracted_at_utc TEXT NOT NULL,
    source_query TEXT NOT NULL,
    source_updated_at_utc TEXT,
    data_sha256 TEXT,
    historical_asof_verified INTEGER NOT NULL DEFAULT 0 CHECK (historical_asof_verified IN (0,1)),
    public_display_approved INTEGER NOT NULL DEFAULT 0 CHECK (public_display_approved IN (0,1))
);


-- A reproducible curated evidence build can combine independent publisher
-- snapshots. Investigations bind to one build, never a misleading single
-- sales/improvement/geography snapshot.
CREATE TABLE curated_builds (
    build_id TEXT PRIMARY KEY,
    built_at_utc TEXT NOT NULL,
    build_hash_sha256 TEXT NOT NULL,
    build_kind TEXT NOT NULL CHECK (build_kind IN ('historical_research','synthetic_fixture'))
);

CREATE TABLE curated_build_sources (
    build_id TEXT NOT NULL REFERENCES curated_builds(build_id),
    snapshot_id TEXT NOT NULL REFERENCES source_snapshots(snapshot_id),
    source_role TEXT NOT NULL CHECK (source_role IN ('sales','assessment','geography','other')),
    PRIMARY KEY (build_id, snapshot_id, source_role)
);

CREATE TABLE parcels (
    pin TEXT PRIMARY KEY CHECK (length(pin) = 14 AND pin !~ '[^0-9]'),
    township_code TEXT NOT NULL
);

CREATE TABLE buildings (
    building_id TEXT PRIMARY KEY,
    pin TEXT NOT NULL REFERENCES parcels(pin),
    identity_verified INTEGER NOT NULL DEFAULT 0 CHECK (identity_verified IN (0,1)),
    UNIQUE (building_id, pin)
);

-- Source row identity is not the same as sale document identity. One transaction
-- can have multiple parcel links; do not allocate one sale price to each parcel.
CREATE TABLE sale_transactions (
    transaction_id TEXT PRIMARY KEY,
    snapshot_id TEXT NOT NULL REFERENCES source_snapshots(snapshot_id),
    source_row_id TEXT NOT NULL,
    document_number TEXT,
    sale_date TEXT NOT NULL,
    price_usd_cents BIGINT NOT NULL CHECK (price_usd_cents > 0),
    UNIQUE (snapshot_id, source_row_id)
);

CREATE TABLE sale_transaction_parcels (
    transaction_id TEXT NOT NULL REFERENCES sale_transactions(transaction_id),
    pin TEXT NOT NULL REFERENCES parcels(pin),
    PRIMARY KEY (transaction_id, pin)
);

-- Historical assessment cards are not automatically mapped to a physical
-- building. Nullable building_id prevents false identity assertions.
CREATE TABLE assessment_records (
    assessment_id TEXT PRIMARY KEY,
    snapshot_id TEXT NOT NULL REFERENCES source_snapshots(snapshot_id),
    pin TEXT NOT NULL REFERENCES parcels(pin),
    tax_year INTEGER NOT NULL CHECK (tax_year BETWEEN 1900 AND 2100),
    card_number TEXT NOT NULL,
    building_id TEXT,
    assessor_class TEXT,
    building_area_sqft DOUBLE PRECISION CHECK (building_area_sqft > 0),
    UNIQUE (snapshot_id, pin, tax_year, card_number),
    FOREIGN KEY (building_id, pin) REFERENCES buildings(building_id, pin)
);

CREATE TABLE parcel_geographies (
    snapshot_id TEXT NOT NULL REFERENCES source_snapshots(snapshot_id),
    pin TEXT NOT NULL REFERENCES parcels(pin),
    tax_year INTEGER NOT NULL,
    neighborhood_code TEXT,
    latitude DOUBLE PRECISION CHECK (latitude BETWEEN -90 AND 90),
    longitude DOUBLE PRECISION CHECK (longitude BETWEEN -180 AND 180),
    derived_or_backfilled INTEGER NOT NULL DEFAULT 1 CHECK (derived_or_backfilled IN (0,1)),
    CHECK ((latitude IS NULL) = (longitude IS NULL)),
    PRIMARY KEY (snapshot_id, pin, tax_year)
);

-- Only explicitly imported sale transactions can be selected as evidence for
-- a specific curated build. This prevents an investigation on one build from
-- referencing a transaction registered solely to another build.
CREATE TABLE curated_build_transactions (
    build_id TEXT NOT NULL REFERENCES curated_builds(build_id),
    transaction_id TEXT NOT NULL REFERENCES sale_transactions(transaction_id),
    PRIMARY KEY (build_id, transaction_id)
);

-- Disposable invented-address index for P3 browser identity tests only.
-- No publisher address feed, geocoding or real parcel-address assertion.
CREATE TABLE synthetic_address_index (
    address_id TEXT PRIMARY KEY,
    pin TEXT NOT NULL UNIQUE REFERENCES parcels(pin),
    display_address TEXT NOT NULL,
    search_key TEXT NOT NULL
);

-- User-entered enquiries are distinct from verified publisher attributes.
CREATE TABLE investigations (
    investigation_id TEXT PRIMARY KEY,
    build_id TEXT NOT NULL REFERENCES curated_builds(build_id),
    subject_pin TEXT REFERENCES parcels(pin),
    analysis_date TEXT NOT NULL,
    user_input_json TEXT NOT NULL,
    match_policy_version TEXT NOT NULL,
    evidence_status TEXT NOT NULL CHECK (evidence_status IN (
        'supported_neighbourhood', 'exploratory_spatial', 'insufficient_data', 'out_of_coverage'
    )),
    created_at_utc TEXT NOT NULL,
    UNIQUE (investigation_id, build_id)
);

CREATE TABLE comparable_evidence (
    investigation_id TEXT NOT NULL,
    build_id TEXT NOT NULL,
    rank INTEGER NOT NULL CHECK (rank > 0),
    transaction_id TEXT NOT NULL,
    selection_tier TEXT NOT NULL CHECK (selection_tier IN ('same_neighborhood','spatial_fallback')),
    explanation TEXT NOT NULL,
    -- Freeze original sale provenance and exact cents in this P3-only schema.
    -- Do not reconstruct them from mutable transaction rows on reopen.
    source_snapshot_id TEXT NOT NULL REFERENCES source_snapshots(snapshot_id),
    sale_price_usd_cents BIGINT NOT NULL CHECK (sale_price_usd_cents > 0),
    PRIMARY KEY (investigation_id, rank),
    UNIQUE (investigation_id, transaction_id),
    FOREIGN KEY (investigation_id, build_id) REFERENCES investigations(investigation_id, build_id) ON DELETE CASCADE,
    FOREIGN KEY (build_id, transaction_id) REFERENCES curated_build_transactions(build_id, transaction_id)
);

CREATE TABLE shortlists (
    shortlist_id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    created_at_utc TEXT NOT NULL
);

CREATE TABLE shortlist_investigations (
    shortlist_id TEXT NOT NULL REFERENCES shortlists(shortlist_id) ON DELETE CASCADE,
    investigation_id TEXT NOT NULL REFERENCES investigations(investigation_id) ON DELETE CASCADE,
    note_text TEXT,
    member_order BIGINT GENERATED ALWAYS AS IDENTITY UNIQUE,
    PRIMARY KEY (shortlist_id, investigation_id)
);

-- P3/P4 synthetic-only candidate: retain the exact evidence response produced
-- for an investigation, rather than trying to recreate it from mutable tables.
-- This is NOT an approved production migration or public-user data store.
CREATE TABLE investigation_results (
    investigation_id TEXT PRIMARY KEY REFERENCES investigations(investigation_id) ON DELETE CASCADE,
    response_json TEXT NOT NULL,
    result_sha256 TEXT NOT NULL CHECK (length(result_sha256) = 64),
    recorded_at_utc TEXT NOT NULL
);
