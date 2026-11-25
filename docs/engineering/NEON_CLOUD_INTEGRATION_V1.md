# Neon Cloud Integration V1

25 November 2026. Owner selected free Neon for persistent private development instead of Windows storage. [Checkpoint](../CHECKPOINT.md) is the live status ledger; this contract describes the architecture, evidence and acceptance procedure. [Full previous contract](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/e33ca781c7d40faa3ea48a5b456e572b06b2b724/docs/engineering/NEON_CLOUD_INTEGRATION_V1.md) preserves the dated implementation and failed-run details.

## Boundaries and target

Use the existing Frankfurt PostgreSQL 17 project, explicit nondefault development branch, database hpi_private, approved owner hpi_private_owner. Initial PG17.12 and 1 GiB branch limit confirmed. No production SQL, paid infrastructure, public deployment, public data release, valuation or main merge. Public network access, no IP allowlist, unprotected branches and six-hour history retention were observed; these are not protected-storage acceptance. Windows security concern remains unresolved; owner declined changes to existing credentials. Use a trusted secret path, never owner credentials in public repository workflows, logs, chat or browser. No real data until storage and permitted-use gate passes.

## Verified schema and service separation

| Milestone | Evidence |
| --- | --- |
| Initial canonical/historical schema | 396867b 11/11 CI; 43-statement guarded transaction; 23 tables, 82 constraints, 36 indexes |
| Restricted historical grants | b7a67c7 7/7 CI; first verification error rolled back; corrected transaction and independent ACL check: 13 approved reads, no writes or buyer access |
| Buyer ownership | ab0c676 10/10 CI, runtime 26 tests; 35-statement guarded transaction, 25 tables, 90 constraints, 40 indexes, five RLS policies, five migration-history rows |
| Split-role persistence | 8c178fe 10/10 CI; sealed frozen evidence, redacted output, owner isolation, exact cents and tamper refusal |
| Authenticated browser | c01de7d 11/11 CI, runtime 45582844740 job 139096927406 (27 tests); actual invented-data HTTPS browser search/save/reopen and cross-owner denial |
| Direct connection qualification code | 9e42749 10/10 CI (29 runtime tests); 0ea5f71 10/10 ordinary CI with sanitized diagnostic corrections |

Canonical SQL/checksums and ownership evidence from the [previous contract](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/e33ca781c7d40faa3ea48a5b456e572b06b2b724/docs/engineering/NEON_CLOUD_INTEGRATION_V1.md) remain authoritative for migration history. No application data seeded. Existing disposable migration, import and runtime entry-point guards retained. Do not silently reuse the fixture consolidated runtime for live service access.

Reader: SELECT on exactly the approved 13 historical tables; no buyer or owner registration access, no write/DDL/temp/sequence permissions. Buyer: SELECT/INSERT on five owner-isolated buyer tables, DELETE/UPDATE(note_text) on shortlist membership, identity sequence USAGE only; no historical source reads or owner registration. Both have no elevated flags or inherited membership. RLS trusts the server's transaction-local owner context; do not expose arbitrary SQL or raw source identifiers. Owner is not a service principal.

## Restricted connection acceptance

[Owner bootstrap preflight](../../backend/neon_preflight.py) is historical empty-target qualification only. Do not run it against installed schema or put an owner secret in Actions. [Restricted service verifier](../../backend/neon_service_preflight.py) uses direct PostgreSQL driver connections to independently pinned development host, two distinct restricted DSNs, verify-full with system roots and required channel binding; rejects pooled or unapproved connection settings, masked/undersized credentials and ambient PG variables. Read-only identity, existing privilege/policy checks, actual zero-row SELECT allow/deny probes and absence of unbound buyer visibility. Returns aggregate status or allowlisted diagnostic category; no DSNs or source records.

Temporary GitHub environment neon-development-preflight is the initial acceptance runner, not application hosting. User configured three secrets: HPI_NEON_DEVELOPMENT_HOST, HPI_NEON_READER_DSN, HPI_NEON_BUYER_DSN. Their values cannot be inspected with the available connector. Required reviewer is owner; self-review allowed, admin bypass permitted by owner, normal approval required; branch-rule restriction deferred for empty-database test. Do not claim environment independently hardened or use this configuration for real data without review. Both temporary logins enabled with expiry 25 November 11:44:42 UTC; no owner password changed. No credential resets unless necessary and authorised.

[Connection workflow](../../.github/workflows/neon-restricted-preflight.yml) v4 at e33ca78 passed all seven ordinary checks. It verifies exact checkout SHA, push before equals parent, single added marker and marker content naming that exact source. The previous manual approved-SHA environment variable is obsolete for v4. First-attempt and development-only trigger remain; pinned actions, protected environment approval and no artifact upload. The marker is not yet added. Use the actual new reviewed source HEAD after documentation reconciliation; no activation in this audit.

### Failed direct attempts retained

| Run | Result |
| --- | --- |
| [v1](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45588341695) | Setup and approved source passed; generic preflight refusal. Connector later verified both actual restricted identities, not driver TLS. |
| [v2](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45589321079) | buyer_configuration before connecting; reader parsed, buyer DSN exact error unknown. |
| [v3](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45593255237) | Stale approved SHA blocked before DSN check. |
| v4 | Ordinary CI passed, no live run yet. |

Before retry: verify exact head, development identity, empty application tables and temporary credential validity. Trigger only the new marker, approve normally. If configuration refusal, correct only indicated secret; if login/TLS/permission refusal diagnose safely and preserve the distinction between connector identity and application-driver acceptance. Do not repeatedly reset credentials or re-run historical markers. Disable temporary logins after the acceptance window and remove temporary secrets when no longer needed. No claim of automated future cleanup.

## Remaining acceptance

Direct restricted driver TLS/auth and denials; persistent invented-data browser/API path with trusted owner identity, frozen evidence and source seal; protected backups/restore; actual runtime configuration and hosting decision; private-use scope, operator list, source rights and protected storage. The conditional single bounded extraction remains unused. See [private beta contract](PRIVATE_REAL_DATA_BETA_V1.md). No real data or production access by this audit. All full phase gates open.
