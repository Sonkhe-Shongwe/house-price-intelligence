# Final Product Acceptance and Release Engineering V1

Owner authorised FA1–FA8 on 24 November 2026. Starting planning estimate 79.2%; original real-data MVP and existing P0–P8 weights/gates retained. No main merge, deployment, provider accounts, external contact, real property display or valuation.

## FA1 coverage diagnostic
Count-only queries against sale and building sources for township 17, sale years 2024/2025, assessment years 2023/2024. Count rows, non-null and distinct PINs; class 203 counts when the sales class field exists and for building data. Fixed source metadata before/after. No raw records or identifiers returned; no more holdout attempts or ranking changes. Aggregate source counts cannot establish the exact reasons for parcel-level join exclusions. Preserve the earlier too-few-subjects blocker.

## FA2/FA3
Add v3 reviewed fictional revision: three varied prices, dates and areas, invented Cedar/Oak/Birch/Grove labels, ambiguous address preserved; unchanged v1/v2 and original seed. Separate virtual display provenance, no real geography. Friendly evidence status and compact mobile navigation. Fresh PostgreSQL bootstrap only; no existing DB migration. Browser verifies richer evidence and map plus frozen prior build.

## FA4/FA5
Offline HTTPS-only WSGI transport for locally signed fictional issuer with injected exchange, server-owned identity mapped to existing PostgreSQL request transaction and RLS. No live provider or launcher. Private POSIX SQLite session persistence with hashed bearer tokens, bounded sessions, atomic expiry and logout, exact-origin/CSRF checks. Reconstruct app from session DB and verify isolation and logout over actual local TLS; no real TLS deployment, persistent pending state or live provider. Existing Basic and SQLite paths retained. Browser CSRF integration remains a separate task if not verified.

## FA6/FA7/FA8
Run existing browser/accessibility regression, new richer fixture and offline TLS scenarios; final owner visual/accessibility sign-off and complete production acceptance remain open. [Release runbook](RELEASE_RUNBOOK_V1.md) is local-only. Record evidence before progress update. No deployment.
