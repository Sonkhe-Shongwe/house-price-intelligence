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

Temporary GitHub environment neon-development-preflight is the initial acceptance runner, not application hosting. User configured three secrets: HPI_NEON_DEVELOPMENT_HOST, HPI_NEON_READER_DSN, HPI_NEON_BUYER_DSN. Their values cannot be inspected with the available connector. Required reviewer is owner; self-review allowed, admin bypass permitted by owner, normal approval required; branch-rule restriction deferred for empty-database test. Do not claim environment independently hardened or use this configuration for real data without review. Both temporary logins were enabled with expiry 25 November 11:44:42 UTC, then disabled after successful qualification; no owner password changed. No credential resets unless necessary and authorised.

[Connection workflow](../../.github/workflows/neon-restricted-preflight.yml): v7 verified TLS and buyer permissions, then the owner corrected the reader secret. v8 passed both restricted connections using the Ubuntu CA bundle and unchanged strict TLS/channel-binding settings. No application change. **Direct restricted connection acceptance passed:** [v8 activation 32f85ff](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/32f85ff4e5c7aa1c324ec9e9b917117352c44a5f), [protected run 45603859165](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45603859165), job 139169484606, first attempt, exact source and one-time marker passed. 25 November 11:23 UTC: password-free certificate and hostname verified; aggregate status restricted_services_verified, direct_tls=true, postgres_major=17, reader_tables=13, buyer_tables=5, read_only=true, real_data_activated=false. Seven ordinary workflows passed on both preparation 6b7f456 and activation 32f85ff. This closes the direct-driver subgate, not persistent application or phase acceptance.

**Temporary login cleanup completed:** explicit development branch and hpi_private only, guarded owner transaction after zero active service sessions; ALTER ROLE NOLOGIN for the two restricted service roles. Independent 11:24:51 UTC read-only verification: both NOLOGIN, all elevated/inherited flags false, zero active service sessions, five RLS policies, all 22 application tables empty. Passwords and grants not changed; original expiry retained. Existing GitHub environment secrets were not inspected or removed; do not reuse expired credentials or assume the environment is hardened. Future login/secret provisioning requires a separately authorised bounded integration window.

### Failed direct attempts retained

| Run | Result |
| --- | --- |
| [v1](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45588341695) | Setup and approved source passed; generic preflight refusal. Connector later verified both actual restricted identities, not driver TLS. |
| [v2](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45589321079) | buyer_configuration before connecting; reader parsed, buyer DSN exact error unknown. |
| [v3](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45593255237) | Stale approved SHA blocked before DSN check. |
| [v4](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45598049479) | Exact source guard passed; buyer_configuration before either direct connection. Seven ordinary workflows passed. |
| [v5](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45599814345) | Both configurations passed; reader_connection failed, buyer not attempted; seven ordinary workflows passed. Available endpoint logs returned no events. |
| [v6](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45600971047) | Both roles certificate; seven ordinary workflows passed. No authentication or permission acceptance. |
| [v7](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45602679938) | Password-free TLS passed; buyer verified; reader authentication failed. Seven ordinary workflows passed. |

Connection acceptance is complete; no replay of old markers. Temporary logins have been disabled. GitHub environment secrets remain stored and should be removed when no longer needed; any later integration credentials require separate bounded handling. Do not weaken TLS or permissions. No unattended execution or cleanup claim.

## Remaining acceptance

Persistent invented-data browser/API path with trusted owner identity, frozen evidence and source seal; protected backups/restore; actual runtime configuration and hosting decision; private-use scope, operator list, source rights and protected storage. The conditional single bounded extraction remains unused. See [private beta contract](PRIVATE_REAL_DATA_BETA_V1.md). No real data or production access by this audit. All full phase gates open.

## Invented persistent application preparation

Comparison and chronological abstention passed ten workflows on 1b0dc86 (runtime 45611278686, 37 tests). Fixed source-shaped four-parcel fixture is now shared by ordinary CI and the [invented seed generator](../../backend/neon_synthetic_seed.py). The operator-only SQL plan refuses wrong database/owner, unexpected tables or migration hashes, nonempty application tables, enabled service roles or active service sessions. It is intended for one atomic transaction on the explicitly verified development target; no reset or arbitrary inputs. The [restricted synthetic journey adapter](../../backend/neon_synthetic_journey.py) requires direct strict TLS, pinned host, exact fixed generated build and independently loaded seal; it checks exact source rows and uses the existing loopback HTTPS/fictional issuer and owner-isolated service. Existing loopback-only entry points retain their guards. Ordinary CI exercises disposable seed and refusal cases, then the existing browser journey. No live data, actual cloud seed, deployment or login change during preparation; exact-head CI pending. A protected integrated test and bounded credential window remain necessary.

Protected journey preparation: 230507f passed 10/10 workflows, 40 runtime tests. [One-shot browser harness](../../backend/neon_invented_acceptance.py) and [protected workflow](../../.github/workflows/neon-invented-journey.yml) prepare an independent seal on local disposable PostgreSQL, then use only the two restricted cloud credentials with loopback HTTPS and fictional identity. Same browser harness is executed against disposable CI; ordinary runtime workflow exports fixed invented-only seed SQL for operator review (no live records or credentials). Marker exact-parent/first-attempt guard, environment approval, no artifacts from protected job. Actual seed and activation remain pending ordinary CI and separate credential-window authorisation. Any partial invented buyer writes remain for review, not destructive automatic cleanup.
