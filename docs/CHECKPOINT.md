# House Price Intelligence: current development checkpoint

**Last updated: 22 November 2026**

Project 2 has an independent repository and a verified real-data audit. The South African graduate-programme research repo is separate and has not been changed for these software development steps.

## Completed

- Phase 0 official Cook County data extraction on user's Windows PC: 3,539 sales and 39,401 residential-characteristic records for the chosen area and period.
- Phase 0 original audit uncovered an integral-decimal parsing defect, now fixed with tests.
- Phase 0 v2: 2,583 screened sales, 1,285 accepted prior-year joins, of which 273 were Class 203.
- Original 20-subject sample: 19 supported by 3+ township-wide comparisons across several classes; **not Class 203-only**.
- See [the evidence and limitations](research/PHASE0_LIVE_AUDIT_RESULTS.md).

## In progress

- Phase 1 targeted geographical and physical-property enrichment for those Class 203 PIN/year keys; script and offline unit tests prepared.
- Historical matching: compare baseline township-wide and exact assessor-neighborhood results on the same 2024 subject sales.
- Live Phase 1 API extraction and evaluation **have not yet been run**. No final technology stack chosen; no app or valuation model is implemented.

## Next user command

From repository root after `git pull origin main`:

```powershell
cd audit\phase1
python -m unittest discover -s tests -v
python expand.py --phase0 ..\phase0\output --out output
```

Then share only `audit/phase1/output/phase1_summary.json` and `phase1_report.md`. Avoid uploading full raw property datasets and never commit output directories.
