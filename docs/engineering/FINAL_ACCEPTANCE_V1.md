# Final Product Acceptance and Release Engineering V1

Owner authorised FA1–FA8 on 24 November 2026. Starting planning estimate 79.2%; original real-data MVP and existing P0–P8 weights/gates retained. No main merge, deployment, provider accounts, external contact, real property display or valuation.

## FA1 coverage diagnostic
Count-only queries against sale and building sources for township 17, sale years 2024/2025, assessment years 2023/2024. Count rows, non-null and distinct PINs; class 203 counts when the sales class field exists and for building data. Fixed source metadata before/after. No raw records or identifiers returned; no more holdout attempts or ranking changes. Aggregate source counts cannot establish the exact reasons for parcel-level join exclusions. Preserve the earlier too-few-subjects blocker.

## FA2/FA3
Add v3 reviewed fictional revision: three varied prices, dates and areas, invented Cedar/Oak/Birch/Grove labels, ambiguous address preserved; unchanged v1/v2 and original seed. Separate virtual display provenance, no real geography. Friendly evidence status and compact mobile navigation. Fresh PostgreSQL bootstrap only; no existing DB migration. Browser verifies richer evidence and map plus frozen prior build.

## FA4/FA5
Offline HTTPS-only WSGI transport for locally signed fictional issuer with injected exchange, server-owned identity mapped to existing PostgreSQL request transaction and RLS. No live provider or launcher. Private POSIX SQLite session persistence with hashed bearer tokens, bounded sessions, atomic expiry and logout, exact-origin/CSRF checks. Reconstruct app from session DB and verify isolation and logout over actual local TLS; no real TLS deployment, persistent pending state or live provider. Existing Basic and SQLite paths retained. Browser CSRF integration now implemented; verify the real TLS browser test.

## FA6/FA7/FA8
Run existing browser/accessibility regression, new richer fixture and offline TLS scenarios; final owner visual/accessibility sign-off and complete production acceptance remain open. [Release runbook](RELEASE_RUNBOOK_V1.md) is local-only. Record evidence before progress update. No deployment.


## Browser session and automated review extension
HTTPS-only browser mutations retrieve a current session-bound CSRF token from the same origin, never store it in browser persistence. TLS CI exercises creating an investigation, saving a shortlist and a note via React and cross-account denial. Legacy HTTP path unchanged. Dedicated axe-core audit of actual desktop workspace/dossier/comparison and mobile comparison emits aggregate rule IDs, impacts and counts, failing on violations; npm production dependency registry audit emits aggregate severity counts. These do not certify production security or accessibility. See CI results before awarding credit.


Initial 48b45dc runtime suite passed the rich V3 browser/map and eight of nine scenarios; offline session denial attempted an unsupported legacy response code 401, fixed with the dedicated no-store identity reply. React test still expected the raw insufficient_data label; change visible expectation to Insufficient evidence and preserve explicit API status assertion. No security guard relaxed. Reverify corrected SHA.

Release-check 45361792484 found zero npm production vulnerabilities but reported serious color-contrast violations on all four scanned views. Darken muted text on light surfaces and retain suitable dark-panel contrast. Add only color-pair diagnostics (no DOM, HTML or record values) for any remaining failures. No accessibility gate waiver.
