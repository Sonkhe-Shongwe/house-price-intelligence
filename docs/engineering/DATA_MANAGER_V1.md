# HPI Data Manager v0.1

Owner-approved scoped P0 dependency: replace repeated one-off scripts with one offline, standard-library workspace utility. No new acquisition authority, source login, network operation, cloud storage, GUI, automatic deletion or renewal. Existing P0 gates and approved historical scores unchanged.

## Windows use

Download the exact version of tools/hpi_data_manager.py from development (or use the existing checked-out source). Place it in the private HPI-Data-Workspace, outside Git. In ordinary PowerShell in that folder, run:

```powershell
python hpi_data_manager.py --self-test
python hpi_data_manager.py
```

The default root is the current folder. The manager creates missing folders and a starter catalogue, preserves existing files, recognises the already approved RPPI ZIP in root or 02_Raw_Data, validates the exact SHA-256, bounded archive and CSV, produces tidy monthly CSV, quality report and provenance/retention manifest. It asks for actual first intake date and confirmation of applicable terms on initial import; do not invent a date or accept incompatible terms. It retains the original and creates a canonical raw copy if needed; never deletes previous raw/processed packages or moves the HPI-DATA-001 marker. Known local paths are reported; inspect other copies, chat, backups and sync separately. The deadline is conservative date-only first intake +30 days at the beginning of that day; shorter applicable terms must be observed by owner. No automatic disposal or renewal. Refuses expired/future date, changed manifest, mismatched existing outputs, unexpected archive and Git/symlink/reparse locations. No raw/processed source records in Git/CI. Local file permissions, backup and sync exposure remain owner responsibilities; do not use for sensitive property records until protected-storage acceptance.

Commands: --init-only creates folders only; --status reports registered dataset and known copies; --root selects a private workspace; --self-test uses invented data. RPPI XLSX not compared; source weights and geography names preserved. Only RPPI v1 exact approved file adapter is implemented; no generic downloader or other data families. Use the local manager once per qualified source/version when future adapters are added. No repeated extraction of HPI-DATA-001.

Acceptance: synthetic self-test in audit CI, actual local Windows import and comparison to known profile (19 series, 157 months, 2983 values) and repeat without overwrite. Do not assert actual Windows execution until observed. Prior development 70f6b34 seven of seven CI passed. Next owner local run, then cadastral and transaction source qualification; no scope migration or P1.

## Windows first-import evidence (26 November 2026)

Owner supplied terminal screenshots: offline self-test PASS, actual import complete, registered HPI-DATA-002, 19 series, 157 months, 2,983 observations, zero missing index values, duplicate series or nonpositive index values; 19 initial MoM and 228 initial YoY blanks intentional. Actual first download date entered by owner: 2026-11-26; owner confirmed applicable terms permit private import/retention. Manager reports deadline 2026-12-26, not due at run time; shorter applicable terms prevail. This is owner attestation, not independent review of exact portal agreement. XLSX comparison remains unperformed.

Reported source CSV SHA-256 f6d2d797c82510193acbd31ea8c91ebe0127455f51ea9d82b8e21562dbcd1e29. Known local paths: original ZIP in workspace root and canonical 02_Raw_Data copy, earlier HPI_DATA_002_processed ZIP and extracted folder, canonical 03_Processed_Data/HPI-DATA-002/rppi_monthly.csv. No deletion, no renewal, no new network acquisition. Local permissions, sync, backups, other copies and exact file contents not independently inspected. Preserve old HPI-DATA-001 attempt marker. No source records committed.

Exact implementation 0b88449 passed all seven CI workflows (45857260284, 45857270895, 45857270881, 45857270913, 45857270857, 45857270843, 45857270832). First Windows import and matching aggregate profile demonstrated; actual repeat without overwrite still pending (synthetic idempotence already passed). One final local run of the same manager, without arguments, should reuse the registered intake date/terms and return the same result without new file copies or network requests; stop on conflict, do not delete or overwrite to force a pass. Then D02 cadastral and D01 completed-sale qualification. No P0 exit, score, scope or provider change.

## Windows repeat and pull-first preference (26 November 2026)

Owner supplied second execution screenshot: no new intake/terms prompt, import complete, same 19 series, 157 months, 2,983 observations, zero missing index/duplicate/nonpositive values, identical source CSV SHA-256, five reported local paths unchanged, deadline 26 Dec 2026 unchanged. Actual repeat accepted as observed output parity, consistent with implemented no-overwrite checks and synthetic idempotence; filesystem timestamps and bytes were not separately inspected. No additional acquisition or deletion. Manager v0.1 bounded local acceptance evidence complete, not approval of a production data platform.

Owner prefers GitHub/GitHub Actions/pull workflow over individual downloads and local manual commands. Reaffirm existing cloud-first policy. Use authoritative application repository development branch for code and offline synthetic verification; standard hosted runners in public repositories free subject to current applicable billing/storage limits. Repository confirmed public via API. [GitHub security guidance](https://docs.github.com/en/actions/reference/security/secure-use) advises against self-hosted runners for public repositories; do not attach owner laptop to this public repository or execute untrusted PR code with private data. Raw/processed private data, private logs, credentials and restricted artifacts never in public Git/Actions. Cloud acquisition only after source-specific terms, approved execution environment, scope and retention establish permission; public access alone insufficient. Existing connected GitHub tools support commits, read-only CI inspection and failure reruns; no general dispatch action observed. Local processing can be reduced to a checked-out development branch fast-forward pull and explicit offline manager invocation targeting the separate private workspace; a reviewed one-command wrapper is a possible next improvement, not yet implemented. No unattended pull-and-execute, new runner, scheduled tasks, private repo, provider mutation or new acquisition authorised by this question. No requirement to repeat the successful local test. Proceed with D02 cadastral and D01 transaction source qualification independently; use integrated adapters only when justified by actual approved data. No scope, score or P0 exit decision.

At review of 1bbf2be six of seven CI workflows passed, React in progress; exact implementation 0b88449 previously 7/7.

## v0.2 district adapter (26 November 2026)

Use the existing trusted development checkout, not an individual downloaded script. From that checkout on development, fast-forward pull and run the one manager against the separate private workspace:

```powershell
git pull --ff-only origin development
python tools/hpi_data_manager.py --root "$HOME\Downloads\HPI-Data-Workspace" --dataset HPI-DATA-003
```

Place the already supplied geoBoundaries-ZAF-ADM2_simplified.geojson in that workspace root or 02_Raw_Data first; no new download. The district adapter needs Shapely (already observed installed during HPI-DATA-001 on Windows, same Python environment required). It prompts for actual first intake date, applicable terms confirmation, and earlier exclusive deadline if applicable. --retain-until accepts an earlier date; existing manifest cannot be overwritten or extended. A second run reuses registered details. --status --dataset HPI-DATA-003 gives local registry status. Default remains RPPI; v0.1 RPPI manifest remains byte-compatible. --self-test runs both adapters with invented fixtures. CI installs test-only Shapely 2.1.2. No auto network, deletion, public data upload, or execution from untrusted PR. Only exact approved bytes accepted. District index is CSV (source name/ID, type, coordinate count, bounds, source year; official municipal code intentionally blank); source geometry stays in canonical raw file. No spatial join, topology or positional accuracy qualification. Source licence and supplied snapshot evidence limits in [acquisition record](../research/SOUTH_AFRICAN_DATA_ACQUISITION_2026-11-26.md#26-november-2026--hpi-data-003-approved-manager-integration). Actual Windows import/repeat not yet observed. Do not create another checkout or retain data after deadline.

## Permanent Windows checkout and sibling workspace (26 November 2026)

Owner established Downloads/HPI-Project with separate house-price-intelligence development checkout and HPI-Data-Workspace sibling. Clone succeeded; first district import stopped before processing because lexical parent traversal in the workspace guard incorrectly identified a sibling as inside Git. Absolute path workaround supplied. Corrected guard checks original path for symlink/reparse points, normalises parent traversal, rechecks the normalised path, and rejects actual Git ancestors. Synthetic regression covers sibling relative path from checkout and true nested Git refusal; no manifest version or output change. Run from existing checkout:

```powershell
python tools/hpi_data_manager.py --root "$HOME\Downloads\HPI-Project\HPI-Data-Workspace" --dataset HPI-DATA-003
```

No fresh clone, data move, security bypass or source download. Exact d5db086 implementation passed 7/7 CI before this fix; corrected revision CI and local import pending. Keep prior checkout untouched and private data outside Git.

## District Windows import evidence (26 November 2026)

Owner terminal screenshots confirm permanent sibling workspace, successful development clone, absolute-path workaround and HPI-DATA-003 import complete. Owner entered first intake 26 November 2026, confirmed applicable terms and accepted 30-day cap; reported exclusive deadline 26 December 2026 (shorter terms prevail). This is owner attestation, not independently verified exact source agreement. Reported quality: 52 features, 52 valid geometries, 35,142 coordinate pairs, 49 polygons, 3 multipolygons, 52 missing shapeISO fields, zero duplicate IDs, names, exact geometries or empty geometries. Official municipal code crosswalk, inter-feature topology and boundary accuracy explicitly false/unverified. Registered true, not expired at execution. Three known local paths: source GeoJSON at workspace root, canonical copy in 02_Raw_Data, district_index.csv in 03_Processed_Data/HPI-DATA-003. No deletion, new acquisition, renewal or public upload. Local file timestamps/bytes, complete copy inventory, backups and sync not independently checked.

Exact d5db086 adapter previously passed 7/7 CI; relative-path correction aa44f94 now verified 7/7 (45870033068, 45870040813, 45870040775, 45870040819, 45870040917, 45870040816, 45870040764). Actual import succeeded via absolute path; local relative-path fix and second import not independently exercised, synthetic regression and idempotence tests passed. No additional owner testing necessary at this point. Keep existing Downloads/HPI-Project sibling structure; code via existing Git checkout, private data outside Git. Future manager refinement: non-interactive registration from explicitly approved acquisition metadata, never invent dates or blanket assent. Batch routine changes into next justified pull; no separate setup exercise. Next independent direct-access-first D01 completed-sale/D02 cadastral qualification, and valuable directly obtainable building data when justified. No new email, intake, deployment, provider change, expenditure or phase/score decision.

## v0.3 building partition adapter (26 November 2026)

Use the existing development checkout and separate private sibling workspace. Download only the approved exact gzip file linked in [acquisition record](../research/SOUTH_AFRICAN_DATA_ACQUISITION_2026-11-26.md#26-november-2026--hpi-data-004-approved-adapter-and-download-attempt) directly to HPI-Data-Workspace/02_Raw_Data, preserving its original filename. No extraction, no duplicate raw copy, no chat upload required. First import is noninteractive: supply actual acquisition date, reviewed terms and exclusive retention deadline. For a download actually made 26 Nov 2026 with no shorter terms:

```powershell
git pull --ff-only origin development
python tools/hpi_data_manager.py --root "..\HPI-Data-Workspace" --dataset HPI-DATA-004 --intake-date 2026-11-26 --terms-reviewed --retain-until 2026-12-26
```

If actual intake differs, use actual date and maximum +30 days or shorter deadline. Existing registered manifest is reused on subsequent calls without date/terms/deadline flags. No network, auto-renewal or deletion. Uses existing Shapely/pyproj Python dependencies; CI pinned synthetic tests. Outputs source-row-indexed private CSV with footprint m2, geometric centroid, available height/confidence, quality report and manifest. Source hash is pinned after first successful inspection, not independently publisher-authenticated. Report invalid geometries/duplicates, missing/invalid optional attributes and tile-centroid checks; not a census or property identity. Processing limits and interpretation in acquisition record. No actual local result yet.
