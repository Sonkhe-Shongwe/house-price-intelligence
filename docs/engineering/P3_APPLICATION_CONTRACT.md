# P3 application contract and integration review

**Reviewed:** 22 November 2026; **CI evidence addendum:** 23 November 2026. **Status:** Synthetic-only application contract included in the authorised repository integration. Integration and passing tests do **not** constitute final P3 acceptance, external deployment, or connection to publisher records. **Prior verified baseline:** `main` at `cd98592f4b20bd02362ec0802db989ac7e94ee32`.

This is the **single current P3 application contract for the integrated candidate**. Earlier v0.1–v0.5 notes remain historical local review material and should not become competing current implementation instructions. The [engineering contract](ENGINEERING_CONTRACT.md) and [lean engineering directive](LEAN_ENGINEERING_DIRECTIVE.md) govern correctness and delivery.

## Buyer journey implemented with synthetic fixtures

1. The local page accepts a 14-digit invented parcel PIN, building area, optional user-reported asking price and label, and analysis date. Pilot township `17` and assessor class `203` are fixed for this demo. PIN is an internal lookup key, **not** approved consumer address search.
2. The local HTTP boundary validates the request and passes it to a SQLite fixture store. Only the server chooses the curated build, its source snapshots, location, assessments and recorded transactions.
3. The store resolves the subject using exactly one prior-tax-year assessment from the selected build; missing or ambiguous records abstain. Candidates are restricted to eligible transactions from the same build. Multi-parcel sales are excluded as individual-house comparables.
4. The unchanged Phase 2 matcher applies earlier-only sale dates, unique comparable PINs, class and township restrictions, floor-area tolerance, neighbourhood preference and bounded exploratory geographic fallback. Prices do not influence eligibility/ranking.
5. The store saves an investigation, selected evidence and a hash of the frozen response in one SQLite transaction. The result can be reopened by UUID; tampered or inconsistent saved evidence fails closed.
6. The page displays fabricated comparables, selection explanations, evidence status, provenance and warnings. No numerical valuation is returned. Saved records disappear when the local in-memory server stops.

**Run locally, with explicit fixture opt-in:**

```bash
python -m backend.run_synthetic_api --fixture-only --port 8765
```

The server listens only on `127.0.0.1`. It is not authorised for public deployment, importing real records, user accounts or client data. Python standard library and SQLite are sufficient for this isolated slice.

## HTTP and status contract

| Method and path | Meaning |
| --- | --- |
| `GET /` | HTML application |
| `GET /assets/styles.css`, `GET /assets/app.js` | Exact allowlisted browser assets |
| `GET /health` | `{ "status": "ok", "mode": "synthetic_fixture_only" }` |
| `POST /v1/investigations` | Validate, investigate, save and return an invented-fixture result; HTTP `201` plus `Location` |
| `GET /v1/investigations/{uuid}` | Reopen saved immutable result; HTTP `200`, or `404` when absent |

The `POST` request is JSON with allowed top-level fields `township_code`, `class_code`, `analysis_date` and `subject`. Allowed subject fields are `pin`, `building_area_sqft`, `asking_price_usd` and `label`. Caller-provided coordinates, neighbourhood codes, source metadata, candidate lists, synthetic flags and IDs are prohibited. An illustrative valid request:

```json
{
  "township_code": "17", "class_code": "203", "analysis_date": "2024-07-01",
  "subject": {
    "pin": "00000000000001", "building_area_sqft": 1600,
    "asking_price_usd": "500000.00", "label": "Synthetic buyer example"
  }
}
```

The service uses one of four **API-facing statuses**:

| Status | Meaning and pricing restriction |
| --- | --- |
| `supported_neighbourhood` | At least the policy minimum eligible sales in the same assessor neighbourhood; sale evidence is descriptive, not a validated valuation |
| `exploratory_spatial` | Bounded nearby sales only; carries the fallback accuracy warning, no valuation |
| `insufficient_data` | Missing PIN, absent/ambiguous assessment, weak sale coverage or missing trusted location; abstain |
| `out_of_coverage` | Unsupported market/class or resolved property outside scope; abstain |

The internal matcher retains `same_neighborhood` and `spatial_fallback` tier names; these are **not** the external status spellings. `valuation` is always `null`. The asking price is `user_reported`. A result records analysis date, immutable investigation ID, a curated `data_build` (build ID, UTC creation, source snapshot IDs, synthetic source type) and the provisional rule/contract version. Historical as-of availability and public source-display approval are both explicitly false in this candidate.

Validation errors use HTTP `422` with a field/code, malformed JSON uses `400`, missing/oversize bodies use `411`/`413`, invalid media type uses `415`, unavailable evidence uses `503` without raw SQL or source details, and unknown/mismatched routes use `404`/`405`. An unsupported-but-well-formed investigation is **a saved response**, not a validation exception. The local server rejects cross-origin/remote traffic and serves no general filesystem paths; these controls do **not** turn it into a production security boundary.

## SQL and source integrity

The 15-table proposed SQLite schema separates source snapshots, curated builds, parcels, buildings, sale transactions, transaction-parcel links, assessment-year records, geography, investigation responses/evidence and shortlists. It preserves: 14-digit PIN identity, one transaction across multiple parcels, unambiguous prior-year characteristics, correct snapshot roles, source-build membership, composite evidence foreign keys, transaction rollback, and saved evidence integrity checks. Shortlist tables exist in the proposed schema, **but shortlist creation and comparison are not implemented user features**.

The synthetic fixture store refuses non-synthetic builds. A string `synthetic-` marker is an extra safeguard against accidental dataset mixing, not cryptographic evidence that any arbitrary imported dataset is invented. There is no real-data ingestion, trusted public address resolver, authentication model, production migration strategy, independently validated price prediction, or permission to display property-level Cook County records.

## Verification and remaining acceptance

**Verified in the isolated integration workspace before publication:** 12 Phase 0 tests, 12 Phase 1 tests, 14 Phase 2 tests, 4 aggregate-export tests and 83 P3 application tests: **125 Python tests passing locally** on Python 3.13. JavaScript syntax and local HTTP GET/POST/persist/reopen paths passed. The local test report alone was not GitHub CI evidence. Independent inspection now confirms [run 45059455620](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45059455620) passed 125 committed tests plus documentation checks on Python 3.12 at [`e8b8f70`](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/e8b8f70de2bb10fd61b9cec9cc1d12aabdc6cfef). It does not include the separately prepared uncommitted reopen-guard patch. Chromium graphical browser execution was blocked by administrator policy and remains unverified.

**Later 23 November 2026 evidence:** The earlier browser-blocked statement is dated historical context. Owner-supplied Windows screenshots now confirm **127 Python tests, 15 Chromium DOM scenarios and full synthetic browser-to-Python-to-SQLite success/insufficient/reopen/error journey** in an **isolated patched checkout**. The original repo was preserved. The patch's extra two backend tests and browser checks are **not in GitHub main/CI**, which still represents 125 committed tests. See [current checkpoint](../CHECKPOINT.md) and [continuity audit](../reviews/CONTINUITY_AND_DIRECTIVE_AUDIT_2026-11-23.md).

**Next acceptance gates:** Owner review of the integrated PIN-first experience and external status contract; full verification of any later reopen-guard patch; actual visual browser acceptance in a permitted environment; then real source rights, as-of availability and release/security review before any publisher data or public service.

The weighted project baseline **22.8%** and P3 **10%** are unchanged pending formal acceptance. Avoid inferring completion from the number of tests or this document.
