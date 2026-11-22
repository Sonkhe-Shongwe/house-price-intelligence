# Working with the hosted GitHub repository

**Repository:** https://github.com/Sonkhe-Shongwe/house-price-intelligence  
**Branch:** `main`  
**Published:** 22 November 2026.

The repository was created on GitHub and its 21 initial project files were migrated and verified. **Do not create another repository or repeat the initial upload instructions.**

## Set up a working copy on Windows

Install Git for Windows and Python 3.10+ if needed. Open PowerShell in the folder where you keep development projects:

```powershell
git clone https://github.com/Sonkhe-Shongwe/house-price-intelligence.git
cd house-price-intelligence
git status
cd audit/phase0
python -m unittest discover -s tests -v
```

Then, with working internet access to the Cook County Open Data API, run:

```powershell
python audit.py --township 17 --start 2022-01-01 --end 2025-01-01 --out output
```

The live extract is **not yet verified**. Review the results and any errors before using the dataset to make valuation claims. Outputs and raw data remain ignored by Git.

## Important: the earlier ZIP is not the GitHub clone

The `HousePriceIntelligence_Repository.zip` produced before publication contains an independent **local Git history**. The connected GitHub migration created new remote commits. These histories differ. If you extracted that old ZIP earlier, **clone the hosted repository afresh** instead of pushing its `main` branch into GitHub or force-pushing over the hosted history.

## Normal development workflow

```powershell
git pull --ff-only
# make and test changes
git add .
git commit -m "Describe the change"
git push
```

Verify the changes on GitHub after pushing. The `.github/workflows/audit-tests.yml` workflow runs the offline unit tests on pushes and pull requests, subject to GitHub Actions being enabled.

## Data and security

As published, this GitHub repository is **public**. Do not commit raw sales or property records, owner/buyer/seller personal information, generated audit reports, credentials, `.env` files or genuine user financial details. Review dataset-specific reuse and publication terms before adding live records or turning the source into a public demo. You can change the repository visibility in GitHub settings if you want private development.
