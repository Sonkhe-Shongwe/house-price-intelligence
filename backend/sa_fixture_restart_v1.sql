-- Dedicated invented-only restart rehearsal extension; not a production migration.
CREATE TABLE sa_restart_migrations (
    version INTEGER PRIMARY KEY CHECK (version = 1),
    script_sha256 TEXT NOT NULL CHECK (length(script_sha256) = 64)
);
CREATE TABLE sa_restart_shortlists (
    owner_key TEXT PRIMARY KEY NOT NULL CHECK (owner_key IN ('fictional-alice','fictional-bob')),
    snapshot_json TEXT NOT NULL,
    snapshot_sha256 TEXT NOT NULL CHECK (length(snapshot_sha256) = 64)
);
