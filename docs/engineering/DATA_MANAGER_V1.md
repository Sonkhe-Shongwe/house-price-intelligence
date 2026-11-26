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
