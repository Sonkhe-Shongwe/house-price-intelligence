# Decisions and open questions

**Updated:** 22 November 2026.

## Confirmed

- House Price Intelligence is the active second software engineering project direction (alongside the separate ShiftForge concept).
- Follow a **product-first** workflow: define pinnacle, independently test data and decide bounded release, then select technologies.
- The prospective buyer's central job is investigating evidence for asking prices and comparing a small shortlist.
- Cook County is the first **feasibility candidate**, not a permanent geographic decision.
- Phase 0 is a source-and-join audit using Python standard library, not a backend stack selection.
- Do not commit real raw data, fetched datasets or personal buyer/seller data to Git.
- Preserve the original SA Tech Graduate Playbook; this repository is an independent project workspace.

## Still open

- Official market boundary and exact detached single-family codes.
- Acceptability of 2022–2024 historical sample and source refresh lag.
- Demonstrated cardinality and coverage of sales-to-building joins.
- Final buyer workflow and whether any maps are warranted.
- Source-specific public-display and redistribution rights.
- Whether prediction can outperform the comparable baseline on a genuine chronological holdout.
- Backend language/framework, relational database, frontend framework, hosting and ML library.
- **Current repository visibility:** Public, as configured at creation. Evaluate switching to private during early research; never publish raw records, sensitive personal data or datasets without reviewing their terms.

## Do not silently decide

Do not convert every home into one parcel, assume all residential class codes are detached houses, call a prior-year row point-in-time valid, claim live prices, claim valuation accuracy, or invent an ingestion result.
