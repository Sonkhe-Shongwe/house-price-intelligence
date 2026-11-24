# Production Data Activation Preparation V1

Owner continued the offline engineering workstream on 24 November 2026. Existing authority covers scoped development commits, synthetic tests, hosted CI and documentation. No additional live extraction, real property publication, provider provisioning, deployment, valuation or main merge. Current approved estimate 85.7%; prior proposed 86.5% remains a proposal pending explicit score review.

## Contract and risk
- Separate checksum-tracked historical extension of canonical PostgreSQL v3; no fixture runtime migration or destructive upgrade. Refuse unversioned historical tables rather than silently adopting.
- Inactive source builds only. Administrator verifies original intake against canonical rows once and issues a relational seal held separately by trusted configuration. The seal is a SHA-256 integrity commitment, not source authentication or a licence. Repeatable-read read-only transactions verify the entire scoped build before matching. No raw extract re-supply for read.
- Dedicated internal reader login with explicit SELECT grants on source tables only; no buyer tables, source writes, schema creation, temporary tables, elevated privileges or inherited role membership. Verify privileges and migration checksums on use. This principal can read source rows directly; it is not a buyer account or public field-level security boundary. Reader is scoped to the disposable historical database, not all production DB infrastructure.
- Private exact address and redacted review reuse canonical matching and disclosure logic; no new public route, no comparable rows returned. Historical dates not publication-time proof.
- Test PostgreSQL migration re-entry, tamper refusal, role denial/drift, cross-build seal rejection, exact matching without raw inputs, and historical row modification. Preserve previous fixture CI and evidence.
- Remaining: actual authenticated bounded extraction/completeness, operator-controlled production credentials, protected configuration, migration review for existing non-disposable installations, real field projection, production monitoring/recovery and owner release approval.
