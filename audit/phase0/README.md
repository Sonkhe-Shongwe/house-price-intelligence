# House Price Intelligence: Phase 0 data feasibility audit

**Prepared 22 November 2026.** This is an executable feasibility instrument, **not** the completed audit or a valuation model. No Cook County data could be downloaded from the execution environment in which this instrument was prepared. It has been tested only against synthetic unit-test fixtures.

## Purpose

Test whether recorded Cook County parcel sales can be screened and joined to one plausible residential building record from the prior assessment year, then measure a simple comparable-sales coverage experiment. The project should not move to production claims before inspecting the real results.

Official source entries:

- Sales: https://datacatalog.cookcountyil.gov/d/wvhk-k5uv
- Building characteristics: https://datacatalog.cookcountyil.gov/d/x54s-btds
- County open-data policy: https://datacatalog.cookcountyil.gov/stories/s/About-Open-Data/pvqg-z4sc/

## Running on Windows / PowerShell

Requires Python 3.10+ with network access to the Cook County Open Data portal. Uses only Python's standard library.

```powershell
cd HousePriceIntelligence_Phase0_Audit
python -m unittest discover -s tests -v
python audit.py --township 17 --start 2022-01-01 --end 2025-01-01 --out output
```

The program queries the API's published schema **before** requesting selected columns. It refuses to proceed if a required field name is absent. It selects no buyer or seller names, and downloads no personal financial account data.

The run saves `output/field_inventory.json`, `output/sales_selected_fields.jsonl`, `output/buildings_selected_fields.jsonl`, `output/audit_summary.json`, and `output/audit_report.md`. Treat the raw extracts as local working data; do not commit them to a public repository.

**If API access, quotas or schema changes prevent downloading:** save the error message and field inventory. Do not fabricate a report or silently swap data sources. With paging, a data update while downloading could shift records, so verify repeated extracts and record your snapshot date. The script raises a cap warning if its per-dataset `--max-rows` value is reached; the capped results are not complete.

## Deliberately limited experiment

1. Township code 17 as an initial candidate only. The actual geography and detached-house segment still need validation.
2. Sales dated 2022 through 2024 and historical building records from the preceding tax year.
3. Reject records with unknown/missing sale flags, certain non-market indicators, multi-parcel transactions, missing documents, implausible pilot prices, or duplicate sale identities.
4. Join by 14-digit PIN and prior tax year. Exclude zero/multiple matching building rows and invalid building size.
5. For up to 20 test subjects sold in 2024, count earlier sales within 365 days, same property class, within 25% of building size, excluding the same parcel and sale document.
6. Generate reason counts and a small number of traceable comparable examples.

These filters **are provisional analyst-defined screens**. The pilot does not establish true arm's-length sale status or prove publication-time correctness. The code deliberately does **not** call all class-2 residential buildings detached single-family houses. First consult the official class-code dictionary and choose exact class types. A prior tax-year row might itself have been revised after the relevant sale.

## Stop/go criteria before starting the real app

- Confirm complete extracts and valid API schema.
- Document sales and building row counts, exclusion reasons, joins, and repeated-sale handling.
- Verify the correct single-family class codes for the chosen geography.
- Check at least 20 representative historical subjects, and record how many have at least three credible prior comparisons.
- Check point-in-time restrictions, lag and chosen fields' intended public-display rights.
- Only then decide the flagship's buyer workflow and whether an ML branch is justified. Do not infer model accuracy from the comparable count.

## Honest limitations

The pilot uses a fixed prior-tax-year join. It cannot prove that a building characteristic was available on the actual sale date. It cannot measure late-arriving sales as of a past historical evaluation date without preserved release snapshots. It also does not train, test or publish any predictive model. Nothing in this package authorizes claims of current property valuation accuracy.
