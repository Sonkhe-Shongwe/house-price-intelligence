# GitHub repository setup and two-branch workflow

**Current operating method:** 25 November 2026 (two-branch adoption 23 November). The [repository](https://github.com/Sonkhe-Shongwe/house-price-intelligence) exists. Do not create a second repository or re-upload historical ZIPs. The [cloud-first workflow](engineering/CLOUD_FIRST_WORKFLOW.md) is authoritative for approvals and milestone merges.

## Branch responsibilities

Standing authority delegates ordinary scoped source changes and verification; use connected GitHub tools and Neon administrative access before asking for manual Windows operations. Direct application credentials and protected storage remain separate from the administrative integration.

- **`development`:** Permanent working branch. Approved source, tests and documentation updates go here and trigger the offline GitHub Actions application/Chromium suite.
- **`main`:** Stable owner-reviewed integration branch. Changes arrive from `development` through a milestone pull request, after explicit approval and passing checks. Do not commit routine changes directly to `main`.
- **[Draft integration PR #4](https://github.com/Sonkhe-Shongwe/house-price-intelligence/pull/4):** The active review surface, not authority to merge automatically. Preserve ancestry with a normal merge when an approved milestone is ready. New feature branches are exceptional, not the default.
- **Live research audit:** Separate [data-audit workflow](../.github/workflows/data-audit.yml), running only on its restricted triggers or an explicitly authorised manual dispatch. Routine documentation/feature changes must not cause external downloads.

## New optional Windows checkout

Only if a checkout does not already exist:

```powershell
git clone https://github.com/Sonkhe-Shongwe/house-price-intelligence.git
cd house-price-intelligence
git fetch origin
git switch development
git status
```

A fresh clone may initially select `main` because it is the remote default. Switch deliberately to `development` for ongoing development.

## Existing Windows checkout (preserve uncommitted work)

First inspect rather than reset:

```powershell
cd "C:\path\to\house-price-intelligence"
git status
git branch -vv
git fetch origin
```

If there are **uncommitted or untracked files**, review and preserve them before changing branches or pulling; do not blindly overwrite the known older experimental checkout. With a clean working tree and the desired local branch selected:

```powershell
git switch development
git pull --ff-only origin development
```

If `git switch development` fails because of local changes, stop and inspect. Do not force-switch, hard-reset, force-push or delete research ZIPs. Local Windows use is optional for platform-specific testing and owner UX review; the cloud repository is the authoritative committed source.

## Verification and safe data handling

From the repository root:

```powershell
python tools/dev_check.py
python -m backend.run_synthetic_api --fixture-only --port 8765
```

The second command launches a **loopback-only fictional-data app** at http://127.0.0.1:8765/. It is not an approved public application. For current CI checks, follow the [checkpoint](CHECKPOINT.md) rather than repeating a historic test count. The offline [application workflow](../.github/workflows/audit-tests.yml) tests `development` pushes and PRs targeting `main`; never infer browser/production acceptance solely from a green lint job.

For a deliberate new research audit, see [Automated data audit](AUTOMATED_DATA_AUDIT.md). Historical three-phase cloud run: [45046687782](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45046687782), with aggregate-only reports and 14-day artifact retention. Do not put raw source extracts, identifying property records, user data, licence-restricted fields or API credentials into public Git or CI artifacts.

**Historical migration caution:** The old ZIP used independent Git history. Never force-push it over the published repository; see [migration manifest](MIGRATION_MANIFEST.md).
