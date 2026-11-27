# HPI Data Manager | Current operations and historical evidence

**Current operating instructions (26 November 2026):** Six owner-observed registrations (HPI-DATA-002/003/004/005/006/008); 007 parked. Use the permanent development checkout and sibling private workspace. Open retention migration completed; no mandatory internal expiry or deadline prompt, actual source conditions and law prevail. Actual acquisition date and terms confirmation remain necessary on first import; existing manifests reused. The chronological sections below record original behaviour at the time, including superseded deadlines and pending tests. They are not current instructions. See [checkpoint](../CHECKPOINT.md) and [repository audit](../reviews/DATA_FIRST_REPOSITORY_AUDIT_2026-11-26.md).

Optional read-only integrity check, from the existing checkout after the next routine pull and passing CI:

```powershell
python tools/hpi_data_manager.py --root "..\HPI-Data-Workspace" --audit-workspace
```

Checks all supported dataset IDs (including unregistered/parked 007) against fixed file locations, retention, exact raw and processed hashes and quality reports, without generating or changing any file. Reports missing/unregistered or inconsistent datasets and returns nonzero if any fails. Does not re-run geospatial or RPPI transformation, verify legal rights or enumerate external copies. The starter CSV is historical scaffolding; manifests and live audit are authoritative. No new download, re-import or mandatory user action.

## Original v0.1 design and evidence (historical)

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

## Building Windows import evidence (26 November 2026)

Owner supplied terminal screenshots reporting successful HPI-DATA-004 import after fast-forward pull, using the existing sibling private workspace via relative path. Command explicitly supplied actual intake 26 Nov 2026, terms-reviewed flag and exclusive deadline 26 Dec 2026. Owner attestation, not independent review of exact download transaction or terms. Registered true, not expired at execution. Records 289,867; usable 289,864; invalid geometry 3; exact WKB duplicate geometry 0; expanded bytes 104,403,718; coordinate pairs 1,628,736; missing height and confidence each 289,867; invalid optional values each 0; 673 usable centroids outside nominal tile rectangle; source property names confidence and height. Median footprint 64.6415 m², minimum 8.1373 m², maximum 112,415.7286 m², summed individual footprint 31,716,992.7284 m². Compressed byte count and SHA-256 not shown in screenshots; manager enforces 50 MiB and stores hash locally, not independently verified. Expanded byte, record and coordinate caps satisfied; no measured processing duration or peak memory. Source records are imagery-derived detections, not verified houses, floor area, sales, ground truth or union coverage. Do not extrapolate national building count or claim accuracy from geometry pass rate. Missing height/confidence cannot be imputed as measurements; outside-tile records and extreme footprint need investigation before density/joins, do not silently discard or assign them.

Four reported paths: canonical original gzip in 02_Raw_Data, derived building_index.csv under 03_Processed_Data/HPI-DATA-004, quality JSON under 07_Reports and manifest under 01_Source_Catalogue. No deletion or renewal. Broader copy inventory, backups, permissions, actual file bytes and repeat execution not independently inspected; synthetic repeat tests passed. No additional download, repeat run or raw file upload requested. Exact d0ba960 passed all seven workflows (45874166853, 45874177678, 45874177726, 45874177552, 45874177773, 45874177698, 45874179332). Prior path correction now exercised locally via relative sibling argument. HPI-DATA-004 bounded acquisition/import milestone delivered. HPI-DATA-002/003/004 share exclusive maximum deadline 26 Dec 2026 or shorter terms, no automatic disposal or renewal. Before deadline obtain timely disposal decision and inventory copies.

Next: qualify official municipal geographic identifiers and lawful direct D02 cadastral / D01 completed-sale sources; prioritise a real complementary key/value dataset over additional footprint partitions. Consider a bounded private spatial integration experiment using existing 003/004 after defining and approving exact scope, ambiguity checks, CRS, boundary vintage and retention; no automatic joins or nationwide scale. No more local setup or email dependence. R0, no P0 exit, product scope or score change.

## Open data retention policy (26 November 2026)

Owner explicitly removed the internal blanket deadline for openly licensed repertoire data, superseding the earlier 30-day approvals for HPI-DATA-002/003/004 only as to the project-imposed cap. No fixed expiry by default for these qualified open sources, subject to actual licence, portal terms, purpose and law; any applicable source-specific deadline remains binding. DataFirst exact portal agreement and exact newer geoBoundaries upstream metadata are not independently verified; existing owner attestation and licence evidence retained, not a fresh grant of rights. No relaxation of restricted property/transaction/ownership privacy and protection controls, no new acquisition or public redistribution. Existing private storage and no automatic deletion remain.

Data Manager supports null deadline for open adapters and optional source-specific deadline, preserves first intake, licence, checksums, quality and existing output compatibility. Explicit --remove-internal-deadlines migrates only the three known 26 Nov 2026 registrations with documented 26 Dec project cap and matching identity/terms fields; different deadlines are preserved, expired legacy cap requires review, no raw or processed file changes. Prior cap retained as historical metadata. Each manifest replacement is atomic; rerunning is safe, no re-import. New open imports may omit --retain-until; actual date and applicable terms confirmation still needed, no automatic assent. Older manifests remain unchanged until explicit migration. Restricted data policy in PRIVATE_REAL_DATA_BETA_V1.md unchanged.

From permanent development checkout, after verified CI:

```powershell
git pull --ff-only origin development
if ($LASTEXITCODE -eq 0) {
    python tools/hpi_data_manager.py --root "..\HPI-Data-Workspace" --remove-internal-deadlines
}
```

No new downloads or reprocessing. Prior 73bb4b8 7/7 CI. New CI and local metadata migration pending. Continue complementary D01/D02 and geographic codes after correction; no phase/score change.

## Open retention Windows migration evidence (26 November 2026)

Owner terminal screenshot confirms successful migration of HPI-DATA-002, 003 and 004: each reports internal deadline removed, deadline null, retention_due_or_expired false, retention_policy open-source-terms-v1. No further owner command needed. Actual raw/processed bytes, file timestamps and complete copy inventory not independently inspected; migration implementation changes registry metadata only. 7/7 workflows successful at inspection of 642e16d. Applicable source terms and law remain binding; exact DataFirst portal agreement and newer geoBoundaries upstream metadata not independently verified. Restricted property/transaction privacy controls unchanged; no fresh data, redistribution, renewal or deletion authority inferred. Prior 26 December project cap is historical, not a current internal deadline for these three datasets.

Current repertoire: D03 partial (289,864 usable imagery-derived footprints, one Mbombela-containing tile; height/confidence all missing, 673 outside nominal tile centroids); D07 partial (52 district boundaries representing 2020, official codes and cross-feature topology unverified); D09 partial (19 RPPI series, 2,983 observations, Jan 2010–Jan 2023). OSM 49-way test closed, no retained records. Other 12 inventory families have no retained qualified dataset; individual completed sales and cadastral identity are decisive gaps for comparable-sales product. No nationwide property coverage, stable property join, current price prediction or actual integrated SA buyer evidence demonstrated. Next qualify official geographic identifiers/crosswalk, cadastral and transaction direct routes; pursue complementary context sources where materially useful, not additional footprint tiles or email dependence. Derived metrics and estimates must remain distinct from observations. Existing product-first 87.1% weighted estimate and P0 94% retained as historical planning estimates, not data readiness. P0-G exit remains blocked. R0; no new acquisition, spatial integration, deployment, provider or scope changes.

## v0.4 official district and metro code adapter (26 November 2026)

Owner explicitly approved HPI-DATA-005 bounded acquisition, private processing and registration. Save only the [official PDF](https://isibaloweb.statssa.gov.za/metadata/CENSUS/2022/06.%20Census%202022%20Code%20lists.pdf) as `06. Census 2022 Code lists.pdf` inside the existing private workspace `02_Raw_Data` (at most 5 MiB; no other download). Do not put it in Git. The manager remains offline. From the existing development checkout after exact-head CI verification:

```powershell
git pull --ff-only origin development
if ($LASTEXITCODE -eq 0) {
    python -m pip install "pypdf==7.2.0"
    if ($LASTEXITCODE -eq 0) {
        python tools/hpi_data_manager.py --root "..\HPI-Data-Workspace" --dataset HPI-DATA-005
    }
}
```

Enter actual download date; inspect page 2 terms and confirm private noncommercial processing, attribution and independent processing. Compare all 52 previewed code/name pairs against the actual PDF page 4 before confirming yes. Stop on discrepancies, changed terms, unexpected PDF or parser failure; no partial registration or forced correction. 44 districts, eight metros, exact 52 unique codes and names; no local-level table, no join. PDF bounded, 10 pages, source identity and terms checked, hash pinned on first successful registration (not a publisher checksum). Outputs private reference CSV, JSON report and manifest; source-specific retention and no automatic deletion; sale of original or derived data/application requires prior permission. Repeat reuses existing reviewed manifest, refuses changed source/retention/output. Read-only workspace audit recognises fourth registration. Synthetic CI uses an invented PDF, not Stats SA rows. Actual PDF acquisition, visual review and Windows registration are pending; do not claim completed until observed. Existing three adapters/retention migration unchanged. No acquisition of another source, data integration or release.

## HPI-DATA-005 Windows registration evidence (26 November 2026)

Owner supplied terminal screenshots of actual PDF import from permanent development checkout and sibling private workspace. First attempt stopped on blank intake date, before registration; subsequent command supplied 2026-11-26 and --terms-reviewed. Owner confirmed all 52 name/code pairs visually match page 4. Import complete, registered true: 52 entries, 44 districts, eight metros, zero duplicate codes and names, ten pages, source page 4, visual_page_reviewed_by_owner true, crosswalk_verified false. Deadline null, retention_due_or_expired false, policy stats-sa-noncommercial-v1. Four reported private paths: 02_Raw_Data/06. Census 2022 Code lists.pdf, 03_Processed_Data/HPI-DATA-005/district_codes.csv, 07_Reports/HPI-DATA-005_quality.json, 01_Source_Catalogue/HPI-DATA-005.json. Owner attestation and observed terminal output, not independent file-byte, hash, rights or page-image verification. Exact file size/hash and complete copy inventory not shown. No repeat required; synthetic repeat passed. No material join or additional intake approved; source terms and noncommercial limitation remain binding.

Exact implementation [23aedf1](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/23aedf153a581cc2757cb55665ee9ca4cf328dfe) passed all seven triggered Actions workflows (45884040787, 45884049211, 45884049056, 45884049097, 45884049070, 45884049061, 45884049229); invented PDF and 219 backend fixture tests passed. Four retained datasets across D03/D07/D09, still partial. No P0 gate/score change.
 
## Private geographic candidate reconciliation (26 November 2026)

Owner explicitly authorised one bounded read-only offline experiment on existing HPI-DATA-003 and HPI-DATA-005, R0, no spatial joins or modification of source datasets. After verified CI, from permanent development checkout:

```powershell
git pull --ff-only origin development
if ($LASTEXITCODE -eq 0) {
    python tools/hpi_data_manager.py --root "..\HPI-Data-Workspace" --geo-crosswalk
}
```

No new dependencies or downloads; no initialise, writes, registry changes or geometry operations. Checks registered raw and derived checksums, report consistency, source identity, retention, terms attestation, count, schema, unique original IDs/names, source years and district/metro reference counts. Conservative casefold/whitespace normalisation, one-to-one exact names only; collision groups and unmatched names on both sides explicitly reported. HPI-DATA-003 contains ADM2 tier but no independent district/metro classification, so cannot verify subtype equivalence; official reference supplies candidate type only. Local terminal JSON contains candidate rows and provenance; share summary counts only, keep detailed output private. No accepted mapping or claim of temporal/boundary equivalence, no aliases without separate approval. Invented-data CI includes successful matching, ambiguity, unmatched and invalid tables, checksum failure and unchanged file comparison. Actual local result pending; stop on failure, do not edit sources to force matches.

## Geographic candidate experiment local evidence (26 November 2026)

Owner terminal screenshots confirm successful local read-only execution of --geo-crosswalk and summary-only repeat. 52 geometry rows, 52 code rows, 40 exact one-to-one name candidates (76.9% coverage), 40 district candidates, zero metro candidates, zero ambiguous groups or rows on either side, 12 unmatched geometry rows and 12 unmatched official-code rows. Four district and all eight metro references unmatched. Crosswalk, boundary equivalence and independent subtype classification all false. The successful report entails the implemented local manifest/hash/quality/retention validations passed; underlying bytes and hashes not independently observed. No writes or geometry operations reported. Full unmatched lists not supplied; no alias pairs inferred. Naming conventions are a hypothesis, not established explanation. No repeat necessary for summary. Exact implementation [2608c01](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/2608c01ad11ee599cf1769bd9f1826fc5a967fa7) passed 7/7 triggered workflows (45885043170, 45885051174, 45885051166, 45885051182, 45885051190, 45885051213, 45885051236). Bounded experiment delivered, not accepted crosswalk or P0 exit. Next inspect only unmatched labels locally; research official name history before separately approved alias comparison.

## Approved documentary alias comparison (26 November 2026)

Owner approved only the twelve proposed name variants for 003/005. After focused CI passes, from permanent development checkout run:

```powershell
git pull --ff-only origin development
if ($LASTEXITCODE -eq 0) {
    python tools/hpi_data_manager.py --root "..\HPI-Data-Workspace" --geo-alias | ConvertFrom-Json | Select-Object -ExpandProperty summary
}
```

The existing --geo-crosswalk remains unchanged. New standalone --geo-alias reuses full manifest/hash/quality/terms validation and requires the observed exact baseline (40 candidates, 12 unmatched each, zero ambiguities). It checks the explicit public-source name/code/type allowlist against actual unmatched local labels; no automatic suffix removal or fuzzy matching. Missing or changed labels abstain, including the cropped Buffalo City label; changed baseline, duplicate or already-used identities and conflicting command modes fail closed. Report separates original exact candidates and documentary aliases, remaining unmatched and abstentions. No downloads, dependencies, writes, retained crosswalk, geometry operations or accepted identity. Both vintages and source terms remain binding. Actual run pending; share summary only. Synthetic tests use invented labels; no private records in CI.

## Documentary alias local evidence (26 November 2026)

Owner supplied terminal screenshot of successful fast-forward pull and --geo-alias summary. Both sources 52 rows; exact baseline 40, twelve documentary alias candidates (four historical district renames and eight metro variants), total 52, 44 district and eight metro candidates, zero unmatched rows on either side, zero abstentions and zero ambiguous groups. This confirms the previously cropped Buffalo City label satisfied the exact allowlist. Candidate coverage 100%, not identity accuracy. Crosswalk_verified, boundary_equivalence_verified and independent_district_metro_classification_verified all false. Successful execution entails local manifest/hash/provenance/retention checks passed; private bytes and hashes not independently inspected. No persisted mapping, new intake, geometry operations or source changes reported; no repeat required. [Implementation ef4c385](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/ef4c3854eeb9e3850af26ad98e0b133cf8bc2681), audit push 45886325301 passed; 6/7 triggered workflows successful at inspection. Recheck exact-head CI. Bounded experiment delivered, not approval of downstream use. No P0 or score change.

## HPI-DATA-006 fixed RPPI publication adapter (26 November 2026)

Owner explicitly approved one [official P0160 June 2026 PDF](https://www.statssa.gov.za/publications/P0160/P0160June2026.pdf), at most 5 MiB, R0, private processing and registration, no merge with 002. Save as P0160June2026.pdf in existing sibling HPI-Data-Workspace/02_Raw_Data, outside Git. After focused CI passes, from permanent development checkout:

```powershell
git pull --ff-only origin development
if ($LASTEXITCODE -eq 0) {
    python tools/hpi_data_manager.py --root "..\HPI-Data-Workspace" --dataset HPI-DATA-006
}
```

Existing pypdf 7.2.0 reused; no additional dependencies. Actual intake date required; review printed page 11 terms (PDF page 12). Validate cover, release date, page 6 Table 4, base and revision note. Preview two metro rows transformed to six dated observations, two published weights and four reported changes; compare all values visually before confirming yes. Rounding-interval compatibility tests use half a displayed decimal unit on both indices and reported growth, not exact rounded point equality. Source values retained; weights repeated only as metadata, not summed. Output metro_index.csv, quality report and private manifest with source/output hashes and provenance; distinct private noncommercial retention policy, no overwrite, no renewal, no 002 merge. Audit/status recognise 006. Synthetic PDF with invented numeric values used in CI; actual layout, source bytes, rights and visual review not independently verified. Stop on parsing discrepancy, do not force or guess values. No other download, API call, property evidence, valuation, continuous monthly series or release. Local import pending.

## HPI-DATA-006 actual cover parser correction (26 November 2026)

Owner terminal showed initial import stopping before registration at the publication identity gate. Read-only diagnostic confirms 12 PDF pages and actual cover extraction contains official publisher domain, STATISTICAL RELEASE, P0160, Residential Property Price Index, June 2026 and embargo date 5 November 2026. The publisher's full name was absent from extracted cover text; original synthetic fixture incorrectly required it. Correct the gate to require the observed domain, ordered release/title/month and embargo-labelled date, with exact 12-page count. Negative tests for wrong domain, identifier, month and embargo date (including date elsewhere); existing numeric, rights, visual and integrity gates unchanged. No re-download, new acquisition or source modification. Actual table/rights extraction not yet observed. Reuse same local PDF and rerun documented command after focused checks; stop on any further discrepancy.

## HPI-DATA-006 local registration evidence (26 November 2026)

Owner terminal screenshots confirm fast-forward to 15e4251, successful actual PDF parsing and preview of both Table 4 metro rows, followed by registration true and visual_page_reviewed_by_owner true. Six index observations, two published weights and four rounding checks passed; base 2020-12=100, observations 2025-06/2026-05/2026-06, publication 2026-11-05, printed page 5/PDF page 6, twelve-page document. continuous_time_series, merged_with_002 and individual_sales all false. Null deadline, retention_due_or_expired false, stats-sa-p0160-private-v1; source terms and law prevail. Reported private paths: 02_Raw_Data/P0160June2026.pdf, 03_Processed_Data/HPI-DATA-006/metro_index.csv, 07_Reports/HPI-DATA-006_quality.json and 01_Source_Catalogue/HPI-DATA-006.json. Owner-observed registration, not independent access to bytes, hashes or full workspace audit. No repeat required. Original importer 2d7ab41 and corrected [15e4251](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/15e42517ca5401c1bbc92676a1cd97c281baf25e) each passed 7/7 workflows; correction audit push 45888934686. Preserve 002 separately; no Treasury intake, archive acquisition or integration authority inferred.

## HPI-DATA-007 bounded Treasury intake (26 November 2026)

Owner approved two fixed facts requests (CPT/JHB, financial year ending 2024) and one model request; 256 KiB response-body cap each, 768 KiB combined, strict R0, private registration only. Existing manager remains offline by default; standalone opt-in network action uses standard-library verified HTTPS, fixed host/paths, no redirects, credentials, report following, retry or pagination. A private exclusive attempt marker consumes the one-time request window even on failure; never delete/reset it to bypass review. No source or existing registry modification. Read [terms](https://municipalmoney.gov.za/terms) before running. After focused CI passes, from permanent checkout:

```powershell
git pull --ff-only origin development
if ($LASTEXITCODE -eq 0) {
    python tools/hpi_data_manager.py --root "..\HPI-Data-Workspace" --dataset HPI-DATA-007 --acquire-treasury
}
```

Confirm terms only if accepted. Do not rerun on error; send only STOP reason or aggregate summary, no private response rows. Validates documented model dimensions/fields and update period first, then complete single-page 0/1 outcome per metro, exact year/code/name, conservative opinion labels, no unexpected fields or obvious personal information. Screening is not a comprehensive privacy guarantee. Unexpected schema/labels/redirect/size stop; no raw payload saved on validation failure. Separate local raw ZIP of exact three JSON bodies (ZIP overhead not transfer), per-response hashes, processed JSON, quality report and manifest. No public display. Model last_updated is a reference/update period, not actual publication date; missing explicit date leaves publication qualification false and private feasibility evidence only, not release/attributed product use. No third-party services or extra package. Synthetic test transport only in CI. Actual API model/response and local registration unverified. Status is offline, no retry. Body cap does not include HTTP/TLS overhead.

## HPI-DATA-007 failed first attempt and metadata format correction (26 November 2026)

Owner terminal shows successful pull to d1288a2, terms confirmation, then STOP: Required source update metadata missing. Code path establishes the first model request returned parseable JSON with matching dimension/attribute checks before the update-date gate; neither facts request was reached. Exact returned update value and byte count not retained or observed. The attempt guard is consumed and must not be deleted or reset. No registration, raw response bundle or change to existing datasets observed. [Publisher source](https://github.com/OpenUpSA/municipal-data/blob/837732c20e8289bca6d30d826bba2ba86804dc54/municipal_finance/views.py) emits minute-resolution timestamps for recorded updates; [publisher regression test](https://github.com/OpenUpSA/municipal-data/blob/837732c20e8289bca6d30d826bba2ba86804dc54/municipal_finance/tests/test_cube_updates.py) confirms YYYY-MM-DDTHH:MM format. Existing parser only accepted month/day dates. Corrected parser accepts these three precise formats, validates calendar/time and future date, rejects absent/malformed/stale values, preserves original precision and separates publication date. Timestamp mismatch is likely, not confirmed actual response. No further API calls in this session. Synthetic regression tests only. Original attempt remains blocked; fresh explicit authority and separately tracked attempt required for any new requests.

## Approved HPI-DATA-007 recovery (26 November 2026)

Owner explicitly approved one separate recovery, at most three additional requests and 768 KiB response bodies, R0, same CPT/JHB 2023/24 scope and terms. Keep original attempt marker unchanged; new exclusive recovery marker and per-request dispatch records, plus metadata-only diagnostics for validation failures (no unvalidated response body retained). Corrected update format parser remains strict; unknown format stops before facts. No replay of either attempt. After synthetic CI passes, from the permanent checkout:

```powershell
git pull --ff-only origin development
if ($LASTEXITCODE -eq 0) {
    python tools/hpi_data_manager.py --root "..\HPI-Data-Workspace" --dataset HPI-DATA-007 --recover-treasury
}
```

Confirm terms only if accepted. No marker removal, new dependencies, report fetching, join or other intake. On STOP, share only the diagnostic and error, never rerun. Maximum four requests cumulatively given observed first model request; actual previous response byte count unknown. Actual recovery not observed. No public display; source update is not publication date.

## HPI-DATA-007 recovery empirical result (26 November 2026)

Owner terminal screenshot confirms fast-forward to 5cac51f, terms acceptance, then recovery diagnostic request CPT, response body 595 bytes, ValueError, STOP: Treasury fact outside exact approved municipality/year scope. Code path establishes model validation succeeded, CPT response passed JSON and outer facts schema/cardinality checks, then failed the row-level combined field/code/year/type/name guard. Exact failing predicate and row are unknown; no unvalidated response retained by design. Prior timestamp correction allowed progression, but the exact first response timestamp remains unknown. Johannesburg was not dispatched. Total observed/inferred dispatches across both attempts: three (initial model, recovery model and CPT); one recovery request unused, not reusable under consumed one-time authority. Original and recovery attempt markers remain; no registration or source mutation reported. Preserve both markers and local dispatch/diagnostic evidence, no further retries or deletion. Exact [5cac51f](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/5cac51fa5290bccf099e96afb9c4ceef8ab2ea32) CI 6/7 successful, 1 pending, 0 other conclusions at inspection; focused recovery tests and documentation passed. No actual private bytes independently inspected. Both live attempts consumed; park this adapter pending independent documentary evidence or explicitly authorised new direction.

## Approved HPI-DATA-008 revised Census household services adapter (26 November 2026)

Owner approves one [revised municipal fact sheet PDF](https://census.statssa.gov.za/assets/documents/2022/Census_2022_Municipal_factsheet-Web.pdf), max 5 MiB, private R0 only. Save original filename Census_2022_Municipal_factsheet-Web.pdf in private sibling 02_Raw_Data (not Git). Existing pypdf 7.2.0 reused. After focused CI succeeds:

```powershell
git pull --ff-only origin development
if ($LASTEXITCODE -eq 0) {
    python tools/hpi_data_manager.py --root "..\HPI-Data-Workspace" --dataset HPI-DATA-008
}
```

Use actual download date and review PDF page 4 terms. Adapter enforces 5 MiB local file cap, 41 pages, report/ISBN, erratum, rights markers, 2021 frame, printed page marker, column order/units/paired years, exact metro row and eight decimal-comma percentages each, range and uniqueness. Visual comparison of all 16 cells and their headers mandatory on PDF pages 30 and 35; no raw source values in Git/CI. Specific errors report gate, metro and column/count only; no guessed layout or other source rows printed. Separate CSV/report/manifest and checksums; independent source terms/noncommercial retention; no merge or property-level inference. 2023 bibliographic year and 2025 revision announcement distinct from unknown exact revision publication date. Synthetic fixtures only; actual local pypdf extraction, size/hash and registration unverified. Local file cap is not a network transfer limiter for manual browser download. Stop on discrepancy, do not redownload or edit original. 007 unchanged and no replay. Status and audit include 008; audit reports parked/unregistered IDs as incomplete, not corruption.

## HPI-DATA-008 local registration evidence (26 November 2026)

Owner terminal screenshots show actual source preview and successful registration true, visual_page_reviewed_by_owner true, 16 observations, 16 unique and 16 percentage-range checks, 41 PDF pages with source pages 30/35, 2021 municipal frame and revision notice present. Original publication year 2023; exact revision publication date null. Household microdata, material join and property service reliability verified flags all false. Null retention deadline under stats-sa-census-private-v1, source terms and law prevail. Known local paths: 02_Raw_Data/Census_2022_Municipal_factsheet-Web.pdf, 03_Processed_Data/HPI-DATA-008/household_services.csv, 07_Reports/HPI-DATA-008_quality.json and 01_Source_Catalogue/HPI-DATA-008.json. Owner-observed registration; actual bytes, hashes and full workspace audit not independently inspected. No repeat required. [Importer 2533443](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/2533443909b4244babc5dd8a3ddf5523cd6c08ec) passed all 7/7 workflows, including [focused audit job](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45892381299/job/140157913250), [React](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45892388838) and [runtime](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45892388903). Existing five registrations preserved by scoped import; no material join or application change.

## Approved independent contextual proof (26 November 2026)

Owner approves private offline 006/008 analysis, independent source reports and scenarios; no workspace writes, new intake, material joins, application modifications or expenditure. Standalone --context-proof validates only those two registrations, policy/terms/visual attestations, retention and stored file checksums, then re-extracts original PDFs in memory and requires exact CSV and quality-report parity. Source provenance and dates checked; offline proof cannot verify later external rights changes or publisher authenticity beyond existing attestations. No crosswalk, cross-family arithmetic, addresses or user records. Five fixed hypothetical cases per source: different metros, same metro, three candidates, partially supported, unknown and unsupported. Shared area referenced once, missing data abstains, no composite score or property claim. Terminal JSON only; no persisted output, dependencies or network. After focused CI passes:

```powershell
git pull --ff-only origin development
if ($LASTEXITCODE -eq 0) {
    $proofJson = python tools/hpi_data_manager.py --root "..\HPI-Data-Workspace" --context-proof
    if ($LASTEXITCODE -eq 0) {
        $proof = $proofJson | ConvertFrom-Json
        $proof.summary | ConvertTo-Json -Depth 5
    } else {
        $proofJson
    }
}
```

For private inspection only, display `$proof.market_evidence | ConvertTo-Json -Depth 12` and `$proof.household_service_evidence | ConvertTo-Json -Depth 12`. Share only summary or STOP error, not private reports, source files or hashes. Synthetic tests reuse invented PDFs and check workspace snapshot parity on success and failure, including coordinated processed/checksum drift. Actual local run pending; no buyer validation or public-display authority.

### Contextual proof synthetic verification and checkpoint correction

Initial [5089943](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/5089943c4c57120840ef6ff38a7121a76ef9789e) [focused CI job](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45894293337/job/140164247472) passed all Data Manager tests (including contextual proof) and 219 backend fixture tests; documentation check failed because checkpoint compression removed literal development/main guidance markers. Restored both markers without weakening the checker or modifying the proof. New revision CI pending at correction. Actual local run still pending.

### Actual local contextual proof result (26 November 2026)

Owner terminal evidence shows successful --context-proof on private workspace after pull, two source integrity checks passed (006: six observations; 008: sixteen), five scenarios per source and ten evaluations. Same-area shared context and unsupported/unknown abstention true. Material join, persisted outputs, application integration, property valuation and buyer utility validated false; network requests zero. Separate report excerpts show null references and explicit property-level evidence unavailable for unknown/unsupported areas, and source-specific next verification questions. The implemented checks re-extract the original PDFs and compare registered outputs and reports; this is owner-observed runtime evidence, not independent inspection of private bytes or hashes, and not a full workspace audit. No raw/derived rows or screenshots committed. [Corrected revision 8d47cc2](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/8d47cc27233034e1bc70276d9726f5c3860cdf85) passed 7/7 workflows, including [audit and documentation](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45894391628), [React](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45894397645) and [PostgreSQL runtime](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45894397639). No repeat required. The proof demonstrates reproducible source-specific context and abstention, not measured buyer utility or future rights clearance.

## HPI-DATA-009 approved DBE Q3 2023 adapter (27 November 2026)

See [approved scope and local command](ACQUISITION_INTELLIGENCE_SIDE_DIRECTIVE.md#27-november-2026--d11-approved-hpi-data-009-local-import). Exact supplied archive in 02_Raw_Data; no additional download. Manager supports --dataset HPI-DATA-009, --status, --audit-workspace and fixture self-test. Historical institutional projection only, no Q2/Stata extraction, no property joins or release. Local execution and registration pending.

### HPI-DATA-009 actual local import result (27 November 2026)

[Owner-observed registration evidence](ACQUISITION_INTELLIGENCE_SIDE_DIRECTIVE.md#27-november-2026--d11-hpi-data-009-actual-local-registration): 25,505 institutions, 19,412 plausible mapped candidates, 6,093 unmapped, one optional Suburb withheld, zero duplicate/invalid EMIS, null retention deadline. Private bytes and full workspace audit not independently verified; no property join or current-location claim. Seven maintained registrations now owner-observed.

## D02-P1 approved cadastral research pilot (27 November 2026)

Owner approved exact D02-P1. Integrated explicit module command `python -m tools.hpi_data_manager --root "..\\HPI-Data-Workspace" --d02-pilot` from permanent checkout, only after exact implementation CI succeeds. Reuse existing Shapely, public-IP pinned TLS, killable worker deadline, fixed query, body/row/pair caps and exclusive attempt ledger under 07_Reports/D02-P1-cape-town-parcels-once. Stores only fixed metadata, aggregate quality, response hash or safe reason; raw response remains in memory, no registration/joins/app. One attempt, even on refusal; never delete marker or retry. No real source request in CI. See [approved scope](../DECISIONS.md#d02-p1-one-request-pilot-authority-27-november-2026). Actual Windows result pending; share aggregate terminal output only. Prior proposal revision d633c51 passed seven exact-head runs, including [audit push](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45939644803) and [React](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45939650882). No P0 progress credit; R0.

## D02-P1 actual STOP and offline correction (27 November 2026)

Owner screenshot of private Windows pilot reports 90,232 response bytes, SHA-256 a21816f1c95f90ec32a7351ac35fcf42c5fd4961d81cc22e71aaf8bf3322192f, started 2026-11-27T04:30:29.640838+00:00, STOP/SCHEMA, raw_retained=false, registered=false, max one dispatched request. Transport succeeded under body cap; record count, valid GeoJSON, identifiers and geometry unverified. Raw not retained by design, so exact mismatch cannot be reconstructed. One-time D02-P1 authority consumed; preserve ledger. All seven workflows passed at [cd44d63](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/cd44d63396d204120fed4530e985d283466d62d7), including [audit](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45939988189) and [focused job](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45939988189/job/140311846801). Local Git hash not independently verified.

Offline correction based on [Esri REST JS query implementation](https://github.com/Esri/arcgis-rest-js/blob/main/packages/arcgis-rest-feature-service/src/query.ts): GeoJSON may carry exceededTransferLimit under top-level properties; original allowlist omitted this valid variant. Accept only known boolean, reject conflicting flags and other metadata; split generic SCHEMA into fixed safe JSON/API_ERROR/COLLECTION/COLLECTION_METADATA/FEATURE_SCHEMA diagnostics. Invented tests added. This is a plausible cause, not confirmed from discarded body. No raw retention, new query, attempt reset, or new acquisition authority. Proposed D02-P2: separate fresh approval for one identical fixed request, all original field/byte/feature/pair/time/Windows limits and aggregate-only rules, new attempt marker only after explicit approval and implementation CI. If refusal persists, park rather than indefinite retries. D01 blocked; P0 94%, overall 87.1%, R0.

## D02-P2 authorised corrected execution (27 November 2026)

Owner explicitly approves one corrected request; same endpoint, envelope, field allowlist, caps, 60-second deadline and aggregate-only output. Command after exact implementation CI: `python -m tools.hpi_data_manager --root "..\HPI-Data-Workspace" --d02-p2`. The consumed --d02-pilot CLI is disabled; P2 verifies the original owner-observed P1 STOP ledger against exact scope, timestamp and response hash, without modifying it. Separate exclusive 07_Reports/D02-P2-cape-town-parcels-once ledger; no raw data retained. Offline fixtures exercise missing/tampered prior, replay, original ledger preservation and incompatible CLI modes in addition to corrected ArcGIS schema and previous limits. No live request in CI. Actual source format remains unverified; if another refusal, park rather than retry. [Approval](../DECISIONS.md#d02-p2-corrected-one-request-authority-27-november-2026). P0 94%, weighted 87.1%, R0.

## D02-P2 actual STOP and pilot closure (27 November 2026)

Owner screenshot: D02-P2 started 2026-11-27T04:36:16.569926+00:00, STOP/FIELDS, 90,232 bytes, SHA-256 a21816f1c95f90ec32a7351ac35fcf42c5fd4961d81cc22e71aaf8bf3322192f identical to P1, raw_retained=false, registered=false, maximum one dispatched request. Transport and collection validation passed; reached at least one feature's property validation. No aggregate feature count or geometry/identity qualification established. Identical digest strongly supports same response; documented collection correction resolved the earlier stopping point but actual metadata variant unknown. Possible field causes: extra property keys, feature ID type/equality, OBJECTID type/range, string type/length/control characters/email screening. Exact cause cannot be reconstructed; raw was not retained. No claim of source defect or confirmed personal-data absence. At [a11948b](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/a11948bc40060bacb71de37621a651de35117204) seven exact-head workflows passed, including [audit](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45940700268) and [focused job](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45940700268/job/140314087751). Windows hash and ledger contents not independently read.

Both approvals consumed; park this API pilot, preserve both ledgers and disable the P2 CLI as well as P1. No additional request or speculative parser change. Future distinct authorised acquisition design should separate response safety gates from quality findings; emit fixed field-specific reason codes/type counts without values or identifiers, profile valid subsets only with explicit accounting, and avoid treating every harmless representation difference as fatal. A normal documented portal export or separately qualified cadastral source may be more productive; not authorised here. D01 and D02 remain unresolved, no registration, app use, joins, costs or phase credit. P0 94%, weighted 87.1%, R0. Next: genuinely different D01/D02 route with material evidence, or owner scope decision; no third identical attempt.
