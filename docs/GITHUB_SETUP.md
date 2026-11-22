# Publish this local Git repository to GitHub

**The project already has an initialized `main` branch and initial local commit.** The GitHub repository has not been created automatically because the available connected GitHub tools cannot create a new repository.

## Create the remote

1. Go to https://github.com/new while signed in to your GitHub account.
2. Set **Owner:** `Sonkhe-Shongwe`.
3. Set **Repository name:** `house-price-intelligence`.
4. Choose **Private** while we validate source use and public data display. It can be made public later after review.
5. Leave **Add a README**, **Add .gitignore** and **Choose a license** **unchecked**, because this local repo already has an initial Git commit.
6. Create the repository.

## Push from Windows PowerShell

Extract `HousePriceIntelligence_Repository.zip` and open a terminal at the `HousePriceIntelligence` folder (the folder containing `.git` and `README.md`). Git for Windows must be installed.

```powershell
git status
git remote add origin https://github.com/Sonkhe-Shongwe/house-price-intelligence.git
git push -u origin main
```

If a remote named `origin` already exists, check it with `git remote -v`; do not blindly overwrite it. Use Git Credential Manager's browser login if prompted, not a password pasted into a terminal.

## Verify

Open the newly created GitHub repo and confirm `README.md`, `audit/phase0/audit.py`, `audit/phase0/tests/test_audit.py`, `docs/` and `.github/workflows/audit-tests.yml` exist on `main`. GitHub Actions should run the offline tests after a push; if the repository blocks Actions, the local test command is sufficient initially.

Do not upload `audit/phase0/output/`, raw sales files, `.env` or real user financial information.

## Connected-app alternative

After the empty repo is created, this assistant's connected GitHub tools can edit its files. However, they currently cannot create the repository itself, and the direct local Git push above preserves the existing initial commit and full project structure without re-entering every file.
