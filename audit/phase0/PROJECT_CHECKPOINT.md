# Historical checkpoint: initial Phase 0 research preparation

> **Archived status, written 22 November 2026:** This is the original pre-extraction planning snapshot, **not the current project checkpoint**. Statements below that the live audit had not run, GitHub was unchanged, and seven tests existed describe this earlier point in the project. They have since been superseded by the successful live Phase 0–2 cloud audits and 42 tests. For current status use [docs/CHECKPOINT.md](../../docs/CHECKPOINT.md) and [current data findings](../../docs/research/PHASE2_CLOUD_AUDIT_RESULTS.md). Preserved to document how the feasibility experiment began.

# Project 2: House Price Intelligence, original execution checkpoint

**Prepared:** 22 November 2026

## Decision

The owner is proceeding with House Price Intelligence as the active project. Its pinnacle vision remains a buyer-facing property decision-intelligence platform. No change to the GitHub repository has been made. The first implementation work item is a reproducible real-data feasibility audit, not a production app or a pre-selected technology stack.

## What has been completed

- Re-read the main GitHub source briefs for House Price Intelligence and data feasibility.
- Re-verified official Cook County data portal descriptions and API field names available from public documentation.
- Created `audit.py` with metadata validation, source extraction, conservative sale-screening, prior-tax-year building joins and prototype comparable-coverage measurement.
- Created offline tests for seven important invariants. They pass.
- Added instructions and documented the distinction between screening proxies and reliable buyer-facing valuation evidence.

## What has NOT been completed

- Successful live extraction and real-data audit (internet access to the API failed in this environment).
- Real join-coverage rates and property-class verification.
- Evidence that the selected data were published before a particular historic sale date.
- Authorisation review of every displayed field for a public app.
- Comparative testing of price prediction and uncertainty ranges.
- Framework choice, application design, database migrations, working frontend, app tests, deployment or any trained ML model.

## Exit criteria for Phase 0

1. Run `audit.py` on a networked computer and inspect saved output and source timestamps.
2. Check source schema, row caps, results and flags; amend extract logic if the published schema differs.
3. Select only verified single-family building class codes with explicit inclusion criteria.
4. Review three traced examples and twenty test subjects; inspect excluded multi-parcel/multi-building cases.
5. Record comparable-coverage rates for at least one suitable market and validate any legally necessary display restrictions.
6. Decide one deliberately limited flagship release and THEN choose the implementation stack.

## Architecture choices, still open

Python or other backend, relational database choice, UI framework, mapping provider, hosting and model library. The audit uses Python standard-library code because it is a disposable measurement instrument, not a binding platform decision.
