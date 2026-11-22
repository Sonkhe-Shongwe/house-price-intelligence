# GitHub repository setup and cloud-first workflow

**Repository:** https://github.com/Sonkhe-Shongwe/house-price-intelligence  
**Branch:** `main`  
**Reviewed:** 22 November 2026.

The repository exists and was populated successfully. **Do not create another repository or repeat the initial upload instructions.** Routine historical data audits now run entirely in GitHub Actions; Windows/PowerShell execution is optional debugging, not the required research workflow.

## Recommended workflow: no manual audit ZIP uploads

1. Code changes are committed to `main` (or a reviewed branch).
2. [Property audit unit tests](../.github/workflows/audit-tests.yml) run on pushes and pull requests.
3. A change to audit code or the [data-audit workflow](../.github/workflows/data-audit.yml) triggers a fresh cloud extraction/analysis on `main`; it also supports manual **Run workflow**. There is no daily or weekly schedule.
4. The workflow saves aggregate-only reports for **14 days**. Verified metrics and methodological caveats are preserved in [dated research summaries](research/PHASE2_CLOUD_AUDIT_RESULTS.md) and the [checkpoint](CHECKPOINT.md).
5. Before claiming a run succeeded, inspect its conclusion, logs and artifact. The verified three-phase live run is [45046687782](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45046687782), with 42 offline tests and completed Phase 0–2 extraction/evaluation.

See [automated audit instructions](AUTOMATED_DATA_AUDIT.md) for operational details, including error handling and privacy restrictions.

## Optional Windows working copy

From the parent folder where you want to work:

```powershell
git clone https://github.com/Sonkhe-Shongwe/house-price-intelligence.git
cd house-price-intelligence
git status
```

If you already cloned the repo, **do not clone it again**. Instead open your existing `house-price-intelligence` directory and run:

```powershell
git pull --ff-only origin main
```

For optional local regression tests (Python 3.10+):

```powershell
cd audit/phase0
python -m unittest discover -s tests -v
```

Manual API extraction is documented in [Phase 0 README](../audit/phase0/README.md), but the supported cloud pipeline avoids repeatedly downloading raw datasets on your PC.

## Historical ZIP warning

The earlier `HousePriceIntelligence_Repository.zip` was created before GitHub publication, with an **independent local Git history**. Do not force-push its `main` over the hosted repository. The published repo is authoritative.

## Data security and release boundary

The repository has been reported **public**. Do not commit property-level raw extracts, generated local output, buyer/seller names, user financial details, API keys, environment secrets or research datasets. The `.gitignore` protects known output folders but is not a substitute for reviewing commits. Dataset-specific public-display, attribution, storage and redistribution terms remain **unapproved**. Do not turn research data into a live public property feed on the strength of a successful GitHub Actions run.
