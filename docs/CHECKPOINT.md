# House Price Intelligence: current checkpoint

**Reviewed:** 25 November 2026. **Approved weighted MVP estimate: 87.1%** (24 November). Active P4 (95%) and P7 (83%); P5 (89%) integrated browser work, P8 (35%) downstream. All full phase gates open. This is the sole live operational handoff, not production or valuation approval.

## Repository and verification

- Latest verified functional source: [7d4e831](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/7d4e831aed74c7e2eccadcf3cb8874bb5e438eb6); 11/11 ordinary workflows passed, including [identity push 45683747551](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45683747551) and [identity PR 45683763307](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45683763307). Identity push job 139450753845: 26/26 tests in 1.473s, including native logout, CSRF/origin refusal, old-cookie denial and unchanged CSP. Earlier documentation audit 4f666004 passed 7/7. Reverify current head separately.
- Stable `main`: [103c854](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/103c854eae36a0a0fa81bb007b71ebadc52179d6). Retain [integration PR #4](https://github.com/Sonkhe-Shongwe/house-price-intelligence/pull/4); verify state before integration. No main merge or deployment authorised.
- Owner-observed WSL2 Ubuntu, Python 3.14.4, PyJWT 2.15.1, cryptography 50.0.2. Prior Windows checkout switched safely to development, preserving three untracked ZIPs. Owner-observed local suite: 25/25 in 1.868s before the native logout change. The subsequent browser showed the new logout control; local 26-test output was not supplied. Current local HEAD/working tree not directly inspectable.

## Current verified implementation on development

| Subgate | Evidence and limitation |
| --- | --- |
| Buyer workspace | React/TypeScript five-view fictional journey, exact-cent frozen evidence, saved history, two-to-three-property shortlist, notes/comparison and fictional MapLibre. SQLite fixture retained. |
| Disposable PostgreSQL | Sealed matching, split roles, RLS, redaction, CSRF, restart, revisions, source integrity and cross-owner denial. Not a real-property API. |
| Direct Neon TLS | [v8 run 45603859165](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45603859165) accepted both restricted roles, verify-full, channel binding and actual denial probes. No replay. |
| Persistent invented buyer journey | [v3 run 45627319372](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45627319372), activation 09c04b6, 8/8 workflows. Search/save twice, supported and insufficient evidence, comparison, fresh sessions/reopen and cross-owner denial. One-time window consumed. |
| Disposable recovery | [45628678686](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45628678686) 43 tests: saved buyer records, external seal, ACLs, five RLS policies restored. [45630291466](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45630291466) 43 tests including AES-256 encrypted disposable restore and wrong-key/truncation refusal. No retained backup or key. |
| Managed recovery | Non-root snapshot refused by provider. No snapshot/restore branch created. Isolated point-in-time restore requires explicit approval and supported procedure; no current clone substitution or production action. |
| External identity | Owner-observed actual Auth0 login, authenticated landing, session persistence after launcher restart and native sign-out returning to unauthenticated landing. CI verifies old-cookie denial; no actual provider-wide SSO logout or buyer/database integration claim. |

**Neon read-only observation, 25 November 18:42:26 UTC:** explicit nondefault development database: two investigations, two results, three evidence rows, one shortlist, two memberships; both restricted roles NOLOGIN, zero restricted sessions. Prior verified seed: four invented sales, five RLS policies; 25 tables, 90 constraints, 40 indexes, one sequence, five migration history records. Preserve records, passwords and grants. Reader SELECT on 13 approved tables only; buyer access limited to five owner-isolated tables, membership DELETE/note UPDATE and sequence USAGE. No real source activation. See [Neon contract](engineering/NEON_CLOUD_INTEGRATION_V1.md).

## Actual Auth0 identity qualification: local milestone verified

Owner created a dedicated development Regular Web Application and verified one test user's email. Required setup: RS256, client_secret_post, Authorization Code with S256 PKCE, no public signup, exact HTTPS callback. Screenshots confirm app type, signing/authentication method, callback configuration and 600-second ID token lifetime; reverify other settings if necessary. Browser reached Auth0 and local callback after leaf certificate import into Windows LocalMachine TrustedPeople.

- 4293a6e local HTTPS launcher: 20/20 local and 11/11 CI. 8cb0be4 corrected form referrer policy; 21/21 local passed.
- 2dfa465 diagnostic-label regression failed; 8bdcc13 corrected it, 23/23 local and 11/11 CI passed. Owner confirmed callback fields code, state, iss; former parser allowed two.
- 6539ac6 exact callback issuer validation: 24/24 local and 11/11 CI. Actual exchange succeeded, time validation rejected; replay rejected state.
- Windows and WSL UTC clocks agree within one second; actual provider duration and offset unknown. 1dbcb6a distinguishes expired, future, invalid temporal claims and excessive duration. Strict 600-second cap retained. Later owner evidence below supersedes the earlier failure.

**Owner evidence, 25 November:** 25/25 local identity tests passed in 1.868s. Two fresh callbacks returned `token_not_yet_valid`; Ubuntu clock readings bracketed an external HTTP Date approximately five seconds ahead. After Windows time resynchronisation and WSL shutdown/restart, local/external readings aligned within one second. Fresh browser authentication displayed Identity verified, and the same landing persisted after launcher restart (owner screenshots). No clock leeway or token policy change. The console logout attempt was blocked by existing CSP before a request; not a logout failure. Native same-origin CSRF-protected form correction 7d4e831 passed all 11 workflows. Owner screenshots show actual Auth0 consent, authenticated landing with Sign out, then unauthenticated landing with Sign in after the requested logout procedure. Browser outcome observed; server-side old-cookie denial verified in CI, not independently probed with an actual token. No provider-wide logout claimed.

**Operator cleanup:** stop the qualification launcher with Ctrl+C. Remove only the exact temporary local leaf certificate imports from Windows CurrentUser/LocalMachine TrustedPeople after verifying the certificate fingerprint. Cleanup not yet owner-confirmed. No further provider login or setup needed for this isolated milestone. No Neon connection in launcher.

## Recovery, storage and access gates

Disposable encrypted recovery is verified, not independent off-provider backup or managed recovery. Observed Free-plan constraints: unprotected branches, public endpoint access, empty IP allowlist, six-hour history capped at 1 GiB, no scheduled snapshots. Prior bounded snapshot attempt refused; no root/production workaround, reset, finalization or deletion. Off-provider encrypted storage, key custody, trusted operator device, access inventory and permitted use remain open. Existing protected environment requires normal owner approval for separately authorised service windows; no bypass or repeat of consumed v8/v3 markers.

## Research and data-use boundary

Historical research pilot: Cook County township 17 / Evanston, Class 203. The [fixed chronological holdout](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45368763925) covered 59 eligible 2025 subjects; current matcher improved paired township MAE by 16.8% ($152,615.81 vs $183,415.81), 1 km did not improve it. MdAPE 22.53%; no model or changed policy approved. Prior [private live rehearsal](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45375702613) verified 142 eligible sales, 137 parcel-year keys, 59/59 restricted-reader/address-token and matcher parity (41 supported neighbourhood, 18 exploratory fallback); temporary database removed. No real dataset currently present; fixed invented seed and saved invented buyer records only. Original research, caveats and run evidence are retained in [rehearsal contract](engineering/PRIVATE_REAL_REHEARSAL_V1.md) and [previous full checkpoint](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/8e85c848c66f5c540e3730f8e93d87011d39ffcd/docs/CHECKPOINT.md).

Prior one-time collection is consumed. On 24 November the owner authorised **one additional bounded extraction only after protected storage and permitted-use scope are verified**; it remains unused. No paid infrastructure, public deployment/disclosure, valuation or main merge. Actual operator/access list, historical as-of availability, physical building identity, private-use scope and public redistribution rights remain unresolved. Four source licence IDs unspecified; that is not an unrestricted licence.

## Next acceptance task

1. Establish protected storage, independent encrypted backup/recovery and operator/access list. Evaluate isolated point-in-time recovery only with explicit approval and supported non-destructive operation. Preserve R0.
2. Verify permitted-use scope before unused conditional bounded extraction.
3. Integrate actual identity with the controlled buyer runtime and qualify its end-to-end ownership boundary under separately authorised service windows. Production, public display, valuation, paid resources and main integration retain separate gates.

Routine scoped work follows [AGENTS](../AGENTS.md), [master prompt](MASTER_CONTINUATION_PROMPT.md) and [lean directive](engineering/LEAN_ENGINEERING_DIRECTIVE.md). No unattended execution claims.

## Evidence versus acceptance

Approved 87.1% unchanged; proposed 87.7% unapproved. [Detailed roadmap](P_PHASE_ROADMAP.md), [summary](ROADMAP.md), [decisions](DECISIONS.md). All full gates open. Documentation audit or CI is not production acceptance.

## Historical continuity and audit record

[Complete pre-cleanup checkpoint](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/1dbcb6aba082af909ee3fe79d5b0a1cfec8cc867/docs/CHECKPOINT.md) preserves all dated runs, failures, role windows and corrections. [Pre-cleanup index](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/1dbcb6aba082af909ee3fe79d5b0a1cfec8cc867/docs/DOCUMENTATION_INDEX.md) preserves prior navigation. Original documents remain in Git history; dated research and reviews untouched. This audit consolidates the ledger and reconciles stale connectivity, identity and recovery statements without code, credential, schema, workflow or score changes.
