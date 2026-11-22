# Dataset handling

This folder documents the project's data directories. Real downloaded data and curated exports must **not** be committed to Git. The root `.gitignore` excludes `data/raw/`, `data/processed/`, `data/exports/` and `data/tmp/`.

Maintain a separate source/snapshot log containing dataset ID, source URL, extraction time, query/filter, source update timestamp, row caps, license/attribution decisions and SHA-256 hashes when practical. Preserve original source records unmodified in a local raw layer; create auditable transformations into a cleaned layer, then a purpose-built application dataset.

Do not ingest or publish buyer/seller names from the sales API; they are unnecessary for the stated product. The Phase 0 audit requests a fixed whitelist of fields. Confirm display and reuse rights before shipping any property-level facts publicly.

No user financial accounts, real customer profiles, secrets or API tokens belong in this repository.
