# Real-Data Integration V1 (authorised 24 November 2026)

Owner authorises scoped GitHub commits, PostgreSQL importer, API/React integration, synthetic tests, hosted CI and documentation. No additional live extraction, public deployment, valuation or main merge. Owner accepts 85.7% planning reassessment (P1 95%, P2 75%, all other stages unchanged). Public API availability and publisher open-data policy support continued noncommercial development; they are not proof of unrestricted redistribution. No external contact prerequisite. Public real-property display remains a separate gate.

## Engineering lifecycle

1. Requirements: controlled historical evidence for township 17/class 203, 2024–2025 sales and 2023–2024 prior assessments. Preserve exact cents, earlier-only matcher, explicit ambiguity and unknown publication time. No valuation.
2. Contract: offline source-shaped records plus authentic complete-extraction metadata, strict schemas and bounded keys; deterministic plan and per-source fingerprints. Derived transaction identity is not a publisher row ID. Preserve exact historical parcel-year, not physical building identity.
3. Risk: fail closed on source drift, private fields, duplicate conflicting money, ambiguous assessments, extra enrichment keys, incomplete/tampered imported rows. Refuse arbitrary HTTP-supplied records. No live extraction; tests are generated fictional inputs.
4. Implementation: inactive historical research build through existing canonical PostgreSQL schema in disposable loopback ingestion DB, separate build manifest/address-state tables, immutable build-scoped snapshots, atomic lock and transaction. Reuse existing relational query and redacted investigation contract privately; no fixture service relaxation.
5. Verification: intake unit tests and hosted PostgreSQL tests (exact cents, idempotency, revision isolation, redacted matching, fixture access refusal, tamper refusal). Existing full regression and browser suites retained.
6. Integrated acceptance: private redacted read only; historical search, saved evidence and row-level public API still not activated. Browser stays fictional. Actual production migration, least-privilege historical read role, source provenance/completeness adapter and approved display projection are subsequent gates.
7. Review: inspect exact-head CI before claiming integration; no extra extraction. Keep historic research and fixture snapshots unchanged.
8. Handoff: update checkpoint, roadmap and decision register; no additional percentage claim before verified result.
