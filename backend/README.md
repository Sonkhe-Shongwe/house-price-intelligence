# Backend: P3 contract pending

**Status (22 November 2026):** No application backend framework, SQL schema, migration or HTTP API has been implemented. The live Phase 0–2 data audits have **succeeded**, so the original constraint "wait for the Phase 0 audit" is no longer the active blocker.

**Next:** Define and accept the P3 domain model and contract: sale, parcel, building, assessment record, buyer-entered inquiry, matching run, selected comparable evidence, source/rule version, saved investigation and shortlist. Then select the API framework and relational database based on those requirements, and implement the first P4 database-to-investigation endpoint.

Existing research Python modules under `audit/` are **not** a production API. Protect historical provenance and do not expose source-level sales before field reuse rights are approved.

See [P0–P8 roadmap](../docs/P_PHASE_ROADMAP.md), [current checkpoint](../docs/CHECKPOINT.md) and [engineering contract](../docs/engineering/ENGINEERING_CONTRACT.md).
