# Frontend: fictional property-investigation browser

**Verified synthetic-only browser baseline (23 November 2026):** The existing HTML/CSS/JavaScript is served by a local Python WSGI API backed by fictional SQLite records. Owner-approved [PR #6](https://github.com/Sonkhe-Shongwe/house-price-intelligence/pull/6) integrated shortlist and comparison into `development`. The unchanged application merge passed [172 Python and 9 hosted Chromium tests](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45254283750). The current tech stack is **not** a visual-design constraint; no framework, map or final visual brand is approved.

## Implemented browser journey

1. Enter an **invented** street-address query, such as `Fictional Way` or `105 Fictional Court`. The browser sends `POST /v1/addresses/search` and displays candidate IDs/labels without silently selecting a parcel.
2. Two parcels can share `105 Fictional Court`. Each option has an explicit fictional parcel hint. A click calls `GET /v1/addresses/{address_id}`, returning one server-owned parcel key with `identity_scope=parcel_only` and `building_identity_verified=false`. The selection is not a verified physical building. The internal synthetic 14-digit PIN remains available as an alternative technical entry.
3. Enter building area, optional **user-reported** asking price, optional label and analysis date. `POST /v1/investigations` binds the selected address ID to its server-side parcel; inconsistent or unknown choices return validation errors. Changing the PIN/search clears stale selection.
4. See the four supported/unsupported evidence states, source provenance, explanatory comparable cards, exact fixed-two-decimal `sale_price_usd` strings, and honest exploratory/insufficient warnings. **No current appraisal, prediction or price estimate is generated.**
5. Reopen one saved synthetic investigation using its UUID. Saved evidence is verified against original transactions, source snapshots/roles and original integer cents.
6. Create or reopen a named fictional shortlist, add **up to three distinct properties** (including insufficient-evidence properties), edit local notes, and compare asking price, evidence status, matching tier, selected sales, source snapshots and limitations side by side. Removing a property from a shortlist does not delete its frozen investigation.
7. Reopen shortlist, evidence and notes across a real process restart **only when `--fixture-db` was explicitly enabled**. Default in-memory runs disappear on shutdown. Notes are local demo content, not account-private.

## Run and verify

From the repository root:

```bash
python -m backend.run_synthetic_api --fixture-only --port 8765
python tools/dev_check.py
# Optional: run server with restart-safe fictional SQLite instead:
# python -m backend.run_synthetic_api --fixture-only --port 8765 --fixture-db ./local-fictional-demo.sqlite
```

Open http://127.0.0.1:8765/ locally. The original P6 application merge passed **9 actual Chromium browser journeys** and 172 Python tests. See the [current checkpoint](../docs/CHECKPOINT.md) for newer exact-SHA verification; documentation changes do not add functionality.

## Not yet implemented or approved

**Not implemented or approved:** licensed real address-to-parcel/building resolution; production-grade multi-user durable persistence, accounts/permissions or privacy; final accessibility/responsive owner acceptance; a verified geographic map contract or map renderer/tile service; approved publisher-field display; current prices/valuations; live listings; public deployment; and final UI visual identity. The map is still proposed, and the six fictional parcel rows currently share one dummy coordinate. See the [mapping research and grey-area review](../docs/design/PROFESSIONAL_UI_AND_MAPPING_RESEARCH_2026-11-23.md) and the [P6 synthetic shortlist contract](../docs/engineering/P6_SYNTHETIC_SHORTLIST_CONTRACT.md).

For the provisional source/API/schema meaning see the [P3 contract and proposed ERD](../docs/engineering/P3_APPLICATION_CONTRACT.md). For deliverables and stage gates see the [80-package roadmap](../docs/P_PHASE_ROADMAP.md).
