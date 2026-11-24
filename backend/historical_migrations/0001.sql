CREATE TABLE historical_build_manifests (
    build_id TEXT PRIMARY KEY REFERENCES curated_builds(build_id),
    policy TEXT NOT NULL, source_manifests_json TEXT NOT NULL
);
CREATE TABLE historical_address_states (
    snapshot_id TEXT NOT NULL REFERENCES source_snapshots(snapshot_id),
    pin TEXT NOT NULL REFERENCES parcels(pin),
    tax_year INTEGER NOT NULL,
    address_state TEXT NOT NULL CHECK(address_state IN ('one_nonblank','ambiguous','missing','blank')),
    display_address TEXT,
    CHECK ((address_state='one_nonblank') = (display_address IS NOT NULL)),
    PRIMARY KEY(snapshot_id,pin,tax_year)
);

