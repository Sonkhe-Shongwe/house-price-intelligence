# Automated Cook County Data Audit

**Status:** End-to-end verified on [GitHub Actions run 45045580458](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45045580458), 22 November 2026. Both live phases, 27 offline tests and aggregate artifact upload succeeded.

## What runs

The [Cook County data audit GitHub Actions workflow](../.github/workflows/data-audit.yml) uses an ephemeral GitHub runner to:

1. Run offline regression tests for Phase 0, Phase 1 and the report exporter.
2. Download bounded historical sales and building-characteristics data for township 17, sale years 2022–2024.
3. Reanalyse the historical joins with the corrected Phase 0 v2 policy.
4. Fetch Class 203 historical neighbourhood and selected property attributes and calculate descriptive comparable-selection baselines.
5. Upload **aggregate-only** reports and a run manifest, regardless of whether Phase 0 or Phase 1 succeeded.

No full source extracts or per-PIN case examples are uploaded as artifacts. The workflow runs with read-only repository permissions, no authentication secrets, and a 40-minute timeout. The original records exist only on the temporary runner until it is destroyed.

## Triggering

The workflow automatically starts on `main` pushes changing audit code or its workflow, and it can be started using **Actions → Cook County data audit (Phase 0 and 1) → Run workflow**. There is **no recurring schedule** in the initial version to avoid repeated downloads. Do not trigger a second extraction while one is already running.

## Checking results

Open the workflow run page:

- Inspect the **historical-data-audit** job steps and its generated summary.
- If successful, download the **house-price-audit-summary-N** artifact (retained for 14 days).
- `phase0_summary.json`, `phase0_report.md`, `phase1_summary.json`, `phase1_report.md` and `run_manifest.json` are the expected reports after both phases succeed. A partial artifact is possible if a stage fails.

The first successful run produced [saved Phase 1 findings](research/PHASE1_CLOUD_AUDIT_RESULTS.md) and [an aggregate report artifact](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45045580458/artifacts/14763313317). The artifact expires after 14 days; the project findings document does not.

Do not interpret these historical analyses as current home valuations, arm's-length confirmations or leakage-safe model evaluations. The implementation still requires official property class verification, data timing analysis, source-use review and more representative validation.

## If the source rejects cloud access

Read the failed step logs. Potential causes include rate limiting, HTTP blocks, schema drift, or an extraction row cap. Record the real error before adjusting the pipeline. Do not silently reuse old data or substitute invented reports. A small, authenticated API token or other publisher-approved bulk delivery mechanism may need separate investigation; never commit credentials to the repository.
