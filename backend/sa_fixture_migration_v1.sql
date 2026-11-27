-- Optional, disposable fictional ZA persistence extension v1.
-- Separate from the immutable v1-v3 US migration history.
CREATE TABLE sa_fixture_migrations (
    version INTEGER PRIMARY KEY CHECK (version = 1),
    script_sha256 TEXT NOT NULL CHECK (length(script_sha256) = 64)
);
CREATE TABLE sa_fixture_investigations (
    owner_key TEXT NOT NULL CHECK (owner_key IN ('fictional-alice','fictional-bob')),
    investigation_id TEXT NOT NULL CHECK (length(investigation_id) = 36),
    market TEXT NOT NULL CHECK (market = 'ZA'),
    currency TEXT NOT NULL CHECK (currency = 'ZAR'),
    area_unit TEXT NOT NULL CHECK (area_unit = 'm2'),
    namespace TEXT NOT NULL CHECK (namespace = 'za-fictional-erf'),
    property_token TEXT NOT NULL CHECK (length(property_token) = 20),
    build_id TEXT NOT NULL CHECK (build_id = 'za-fictional-build-v1'),
    policy_version TEXT NOT NULL CHECK (policy_version = 'za-fictional-pinelands-v1'),
    analysis_date TEXT NOT NULL CHECK (length(analysis_date) = 10),
    asking_cents BIGINT CHECK (asking_cents IS NULL OR asking_cents BETWEEN 1 AND 100000000000),
    request_json TEXT NOT NULL,
    response_json TEXT NOT NULL,
    frozen_sha256 TEXT NOT NULL CHECK (length(frozen_sha256) = 64),
    PRIMARY KEY (owner_key, investigation_id),
    UNIQUE (investigation_id)
);
CREATE INDEX idx_sa_fixture_owner ON sa_fixture_investigations(owner_key, investigation_id);
