# Release candidate runbook (fictional local only)

No hosting or production provider is approved. Do not expose either WSGI launcher to the Internet. Production prerequisites: explicit release-mode approval, actual OIDC provider and confidential exchange, HTTPS reverse-proxy trust model, separate durable session store review, rate limits, secret rotation, backup/restore, monitoring, accessibility and data rights sign-off. Do not deploy the offline test adapter.

## Final browser-only release gate (owner-approved target, not implemented)

Follow [P8 acceptance](../P_PHASE_ROADMAP.md) and the [recruiter walkthrough](../product/RECRUITER_WALKTHROUGH_V1.md). After separate hosting and release approval, verify the exact deployed revision from a fresh supported browser using one HTTPS URL, integrated authentication, approved isolated demo access, the full buyer journey, persisted reopen and logout. The presenter must not start services, use a shell, configure Auth0, connect to Neon or import certificates. Provisioning, migrations, TLS, secret custody and service startup are operator/deployment concerns, not demonstration steps. Verify R0 plan limits and fail safely on unavailable services. An optional prepared one-click fictional local fallback must not expose fixture adapters publicly or bypass production identity controls. Do not deploy or provision resources under this documentation change.

## Reproduce from a clean checkout (engineering procedure)
Use Python 3.12, Node 22, `npm ci --prefix frontend/react`, `npm run build --prefix frontend/react`. Run `python -m backend.run_synthetic_api --fixture-only --frontend react --synthetic-map --port 8765`. SQLite private fixture-file mode is optional. No external account or live data required. See [walkthrough](../product/RECRUITER_WALKTHROUGH_V1.md).

The PostgreSQL runtime workflow uses an ephemeral PostgreSQL 17 service, locked frontend dependencies, pinned psycopg/psycopg_pool/Playwright/PyJWT. Explicit fresh disposable database bootstrap only; never upgrade or overwrite an existing buyer database. Credentials generated per CI execution, no credentials or session files in artifacts. Original seed and revised v1/v2/v3 are immutable; activation is admin-only generation-checked. Rollback is another activation event. Local offline TLS transport test uses an ephemeral self-signed cert and fictional issuer; never disable certificate checks for an actual deployment.

## Verification and dependency review
Run existing regression, PostgreSQL compatibility and runtime, React browser and offline OIDC workflows. Locked npm resolution and pinned Python direct dependencies are a reproducibility baseline, not a full security audit; review transitive versions, SBOM, dependency advisories and platform configuration before public hosting. No paid jobs or external accounts. Actual visual evidence is only the synthetic screenshots from the verified CI run. Deployment gates remain open.

## Operational failure
If evidence validation fails, 503; refuse unreviewed builds. If the identity session file is unavailable, fail closed with 503. Session bearer token hashes and CSRF values stored in a private local POSIX SQLite file; identity pending state is in memory, login restart requires starting again. This is an offline test candidate, not an approved distributed production session design. Do not restore session databases into a new deployment; require login after restore. User data retention and provider revocation remain open.

Dedicated release-check CI uses pinned axe-core against actual browser views and npm audit of locked production dependencies, reporting aggregate counts only. Review all findings before declaring accessibility or dependency acceptance. Python transitive advisory review still required.

## Operational preparation follow-up
See [Production Runtime Preparation V1](PRODUCTION_RUNTIME_PREPARATION_V1.md). Existing fixture-only launcher has explicit validated environment configuration; authenticated `/health/live` reports process liveness independent of DB, existing `/health` checks source integrity, active revision and effective database permissions. Never expose fixture Basic or offline OIDC on a public interface. No actual provider or production configuration approved.

## Controlled activation and recovery
See [activation decision register](CONTROLLED_PRODUCT_ACTIVATION_PREPARATION_V1.md). Rehearse two historical revisions with private operator seals and backup/restore without owner/ACL restoration, then fresh restricted reader. No real backup, cloud or production approval.
