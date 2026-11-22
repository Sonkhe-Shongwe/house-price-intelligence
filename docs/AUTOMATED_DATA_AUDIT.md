# Automated Cook County Data Audit

**Status:** End-to-end three-phase audit verified on [GitHub Actions run 45046687782](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45046687782), 22 November 2026. All three live phases, 42 offline tests and aggregate artifact upload succeeded.

## What runs

The [Cook County data audit GitHub Actions workflow](../.github/workflows/data-audit.yml) uses an ephemeral GitHub runner to:

1. Run offline regression tests for Phase 0, Phase 1, Phase 2 and the report exporter.
2. Download bounded historical sales and building-characteristics data for township 17, sale years 2022–2024.
3. Reanalyse the historical joins with the corrected Phase 0 v2 policy.
4. Fetch Class 203 historical neighbourhood and selected property attributes and calculate descriptive comparable-selection baselines.
5. Evaluate the Phase 2 neighbourhood-first and limited 2 km spatial fallback policy, recording support and paired historical errors.
6. Upload **aggregate-only** reports and a run manifest, including partial summaries when a phase fails.

No full source extracts or per-PIN case examples are uploaded as artifacts. The workflow runs with read-only repository permissions, no authentication secrets, and a 40-minute timeout. The original records exist only on the temporary runner until it is destroyed.

## Triggering

The workflow automatically starts on `main` pushes changing audit code or its workflow, and it can be started using **Actions → Cook County data audit (Phases 0 to 2) → Run workflow**. There is **no recurring schedule** in the initial version to avoid repeated downloads. Do not trigger a second extraction while one is already running.

**Documentation-only changes do not trigger a new live Cook County data download.** The separate [unit-test workflow](../.github/workflows/audit-tests.yml) also runs the [documentation consistency check](../tools/check_docs.py) on pushes and pull requests; this validates internal Markdown references and P0–P8 arithmetic without consuming external API requests.

## Checking results

Open the workflow run page:

- Inspect the **historical-data-audit** job steps and its generated summary.
- If successful, download the **house-price-audit-summary-N** artifact (retained for 14 days).
- `phase0_summary.json`, `phase0_report.md`, `phase1_summary.json`, `phase1_report.md`, `phase2_summary.json`, `phase2_report.md` and `run_manifest.json` are expected after all three phases succeed. A partial artifact is possible if a stage fails.

The latest completed three-phase run produced [saved Phase 2 findings](research/PHASE2_CLOUD_AUDIT_RESULTS.md) and [an aggregate report artifact](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45046687782/artifacts/14764136546). The artifact expires after 14 days; the project findings document does not.

Do not interpret these historical analyses as current home valuations, arm's-length confirmations or leakage-safe model evaluations. The implementation still requires official property class verification, data timing analysis, source-use review and more representative validation.

## If the source rejects cloud access

Read the failed step logs. Potential causes include rate limiting, HTTP blocks, schema drift, or an extraction row cap. Record the real error before adjusting the pipeline. Do not silently reuse old data or substitute invented reports. A small, authenticated API token or other publisher-approved bulk delivery mechanism may need separate investigation; never commit credentials to the repository.
