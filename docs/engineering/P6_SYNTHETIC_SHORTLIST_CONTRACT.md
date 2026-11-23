# P6 synthetic shortlist and side-by-side evidence candidate

**Documented:** 23 November 2026. **Status:** Short-lived feature candidate only, subject to review and GitHub Actions at its exact HEAD. No owner P3/P6 exit acceptance, production deployment, release, public source-rights permission or phase-score change.

## Buyer problem and smallest supported journey

An individual comparing two or three fictional properties needs to preserve separate investigations, write editable decision notes, inspect sale-evidence differences simultaneously and reopen the same evidence after restarting a local demo server. One subject has three earlier fictional sale records, while another has insufficient data. Both must be visible together without a fabricated estimate.

This proposal builds on the approved integration of [PR #5](https://github.com/Sonkhe-Shongwe/house-price-intelligence/pull/5) into `development`: opt-in on-disk SQLite with preserved response hashes, transaction cents, address identity, schema, source-role and fixture identity validation. It does **not** change the pure Phase 2 matching policy or historical research.

## Fixture-only contract

- Reuse the pre-existing `shortlists` and `shortlist_investigations` tables. There is no schema migration for P6; shortlist membership and notes may change, while the `investigations`, `investigation_results`, `comparable_evidence` and source tables remain unchanged.
- A shortlist has a server-created lowercase UUID, a bounded human label (1-80 characters), a UTC creation timestamp and **0-3** members. Once two or three are saved, the browser displays aligned evidence columns.
- Each saved member refers to an existing verified frozen investigation UUID, not a browser-provided source record. The same investigation or another investigation for the same 14-digit PIN cannot be added twice. Unsupported/unknown PIN enquiries may be included and are labelled as insufficient rather than guessed.
- Each member's `note_text` is an editable plain-text string of at most **800 characters**, with disallowed control characters refused. The UI inserts user text using DOM `textContent` or textarea `value`, never HTML interpretation.
- Every shortlist GET, add, note edit and removal checks the investigation's source snapshot/role, exact sale cents, frozen response hash and parcel mapping via the existing `store.reopen()` guard. A changed or unrecognised stored match-policy version fails closed rather than being silently represented as a current rule.
- The browser comparison covers buyer-entered asking price, synthetic parcel identity, buyer area, supported/insufficient status, selected earlier-sales count, neighbourhood/spatial matching tier, analysis date, source snapshots, stored matching policy version, caveats and the explicit absence of a valuation.
- The local server has no accounts, authorisation, encryption, retention policy or network deployment clearance. Local shortlists are accessible to anyone with local access to this unauthenticated demonstration server; **never enter real user or property data**. Opt-in `--fixture-db` is required for persistence across restarts; the in-memory default remains disposable.

## HTTP paths, local synthetic records only

| Method | Path | Result |
| --- | --- | --- |
| `POST` | `/v1/shortlists` | Create using `{"label":"My fictional shortlist"}`; HTTP 201 + Location |
| `GET` | `/v1/shortlists` | List local shortlist metadata, max 30 recent rows |
| `GET` | `/v1/shortlists/{shortlist_id}` | Fetch verified frozen investigations and editable notes |
| `POST` | `/v1/shortlists/{shortlist_id}/entries` | Add `{"investigation_id":"uuid","note_text":""}`; HTTP 201 |
| `PATCH` | `/v1/shortlists/{shortlist_id}/entries/{investigation_id}` | Edit only `{"note_text":"..."}`; HTTP 200 |
| `DELETE` | `/v1/shortlists/{shortlist_id}/entries/{investigation_id}` | Remove membership, preserve investigation; HTTP 200 |

All paths use strictly checked UUID shapes, bounded JSON request bodies, same-origin/loopback restrictions and parameterised SQL. Invalid fields return 422, unknown shortlist or investigation IDs 404, duplicate membership/property and more than three entries 409, and evidence corruption 503 with a non-leaking error. The server never accepts a caller-provided curated build, sale facts, source fields, geographic coordinates or numeric valuation.

## Validation and negative-case acceptance

1. Create two distinct enquiries through the real browser, one with three eligible fictional sales and one that abstains with zero sales. Add both to one shortlist and render separate aligned evidence columns, including warnings and absent valuation.
2. Edit a note and prove the original investigation JSON/hash, sale transaction price cents, source role and comparable links do not change.
3. Reject a repeated UUID, an additional investigation of the same PIN, an attempt to add a fourth property, overlong notes, unexpected fields and unsafe request origins.
4. Remove a shortlist member without deleting its original investigation. Unknown or tampered saved evidence must fail closed.
5. Explicitly enable a local fixture database, stop/restart the actual HTTP server, navigate directly to the shortlist URL in a new Chromium tab and recover two properties, notes, fixed-two-decimal prices, match policy and unsupported-property warnings.
6. Run backend, HTTP, Playwright Chromium, JavaScript syntax and documentation checks at the exact proposed PR head; record failures transparently and do not merge without later owner approval.

## Exact run mode and release boundary

Use `python -m backend.run_synthetic_api --fixture-only --port 8765 --fixture-db ./local-fictional-demo.sqlite` for an expressly opt-in local persistence test. A fresh path seeds an invented-only dataset; an existing verified database reopens it without erasure. Without `--fixture-db`, the existing process-local demonstration stays in-memory. All database files are Git-ignored. Localhost WSGI is not an acceptable production security boundary.

**Phase accounting remains:** P3 **10%**, overall weighted MVP **22.8%**, and P4/P5/P6 phase exit gates **open**. Passing synthetic tests proves a feature candidate; it does not settle account access, source licensing, true historic as-of data, final buyer UX/accessibility or release readiness.
