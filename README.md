# House Price Intelligence

**Status: Phase 0 data feasibility; product and technology choices remain provisional.**

House Price Intelligence is a prospective homebuyer's evidence-based decision workspace. The user can eventually enter an asking price, investigate verified completed sales, understand which properties are comparable, save a shortlist and make an informed comparison. A statistical price estimate will be included **only if** source-quality and time-based model evaluation justify it.

This is a **software engineering project**, not merely a house-price notebook. The central challenge is to convert complex historical transaction and building records into a trustworthy, reproducible buyer workflow.

## Current state (22 November 2026)

- Active project selected; no complete application implemented.
- Existing Phase 0 Python standard-library audit migrated into [`audit/phase0`](audit/phase0/). Seven fabricated-data unit tests exist and have been verified locally.
- Live Cook County extraction, measured joins and comparable coverage **have not been completed**. Do not represent placeholder examples as real valuations.
- Frontend, server framework, production database and machine-learning methods are intentionally **not selected yet**. Product requirements and measured data constraints determine those decisions.

## Quick start for the existing audit (Python 3.10+)

From a terminal in the repository root:

```powershell
cd audit/phase0
python -m unittest discover -s tests -v
python audit.py --township 17 --start 2022-01-01 --end 2025-01-01 --out output
```

The second command requires network access to the Cook County Open Data APIs and must be checked for schema mismatches, row caps and changes in field semantics. See [`audit/phase0/README.md`](audit/phase0/README.md).

**Do not commit extracted sales, datasets, personal information, generated outputs or credentials.** See [data handling](data/README.md).

## Documents

| File | Purpose |
| --- | --- |
| [`docs/product/PRODUCT_BRIEF.md`](docs/product/PRODUCT_BRIEF.md) | Buyer problem, original release concept, product rules |
| [`docs/product/PINNACLE_VISION.md`](docs/product/PINNACLE_VISION.md) | Ultimate vision vs bounded flagship |
| [`docs/research/DATA_FEASIBILITY.md`](docs/research/DATA_FEASIBILITY.md) | Dataset risks, source leads, research gates |
| [`docs/research/SOURCE_REGISTER.md`](docs/research/SOURCE_REGISTER.md) | Primary URLs and provenance |
| [`docs/engineering/ENGINEERING_CONTRACT.md`](docs/engineering/ENGINEERING_CONTRACT.md) | Engineering invariants and quality gates |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Phase 0 through first release |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Settled vs open choices |
| [`docs/CHECKPOINT.md`](docs/CHECKPOINT.md) | Current handoff and next action |
| [`docs/MIGRATION_MANIFEST.md`](docs/MIGRATION_MANIFEST.md) | Origins and excluded materials |

## Product boundaries

**Pinnacle (vision only):** Property dossiers, comparable-sales intelligence, validated estimates and uncertainty, neighbourhood context, shortlist comparisons, financial scenarios, saved decision reports and optional monitoring.

**Candidate flagship:** One market, one validated property class, entering a home and asking price, trustworthy sales comparables with explanations and dates, shortlist comparison, persistence and insufficient-data handling. ML only after a chronological holdout evaluation.

**First implementation slice:** Download and audit real sales/characteristic data, establish one-to-one historical property records, compute traceable prior-sale comparables, then expose the result in a saved user workflow.

## Relationship to graduate preparation

The separate [SA Tech Graduate Playbook](https://github.com/Sonkhe-Shongwe/sa-tech-grad-playbook.) remains the canonical graduate recruitment research repository. This repository contains the standalone application and only project-relevant context. Source documents in the playbook are preserved, not moved or deleted.

## Contribution and development style

Use small reviewed commits, document rejected assumptions and keep regression tests for data join errors, multi-parcel sales, missing attributes and future sales. Never claim to have tested live source records until an actual extract has been run and its report saved.

## Automated data audit

Phase 0 and Phase 1 can run in GitHub Actions without installing the audit locally. See [Automated Data Audit](docs/AUTOMATED_DATA_AUDIT.md) for triggers, report artifacts, failure handling and privacy limits. The end-to-end cloud extraction and report upload were verified in [the first successful run](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45045580458). See the [saved Phase 1 findings](docs/research/PHASE1_CLOUD_AUDIT_RESULTS.md).
