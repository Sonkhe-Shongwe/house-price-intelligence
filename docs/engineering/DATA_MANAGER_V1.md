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
