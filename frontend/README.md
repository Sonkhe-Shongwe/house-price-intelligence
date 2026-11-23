# Frontend: fictional property-investigation browser

**Current synthetic-only candidate (23 November 2026):** Plain HTML, CSS and JavaScript served through a local Python WSGI API and disposable SQLite fixtures on `development`. This is not approved real-world address search, a commercial listing UI, a public deployment or final visual branding.

## Implemented browser journey

1. Enter an **invented** street-address query, such as `Fictional Way` or `105 Fictional Court`. The browser sends `POST /v1/addresses/search` and displays candidate IDs/labels without silently selecting a parcel.
2. Two parcels can share `105 Fictional Court`. Each option has an explicit fictional parcel hint. A click calls `GET /v1/addresses/{address_id}`, returning one server-owned parcel key with `identity_scope=parcel_only` and `building_identity_verified=false`. The selection is not a verified physical building. The internal synthetic 14-digit PIN remains available as an alternative technical entry.
3. Enter building area, optional **user-reported** asking price, optional label and analysis date. `POST /v1/investigations` binds the selected address ID to its server-side parcel; inconsistent or unknown choices return validation errors. Changing the PIN/search clears stale selection.
4. See the four supported/unsupported evidence states, source provenance, explanatory comparable cards, exact fixed-two-decimal `sale_price_usd` strings, and honest exploratory/insufficient warnings. **No current appraisal, prediction or price estimate is generated.**
5. Reopen one saved synthetic investigation using its UUID. Saved evidence is verified against original transactions, snapshot/source roles and original integer cents. **The in-memory data disappear on shutdown**.

## Run and verify

From the repository root:

```bash
python -m backend.run_synthetic_api --fixture-only --port 8765
python tools/dev_check.py
```

Open http://127.0.0.1:8765/ locally. At the [verified development checkpoint](../docs/CHECKPOINT.md), GitHub Actions passed **7 actual Chromium browser journeys**, plus Python, JavaScript and documentation checks. Future runs must be checked on their own exact commit.

## Not yet implemented or approved

Real licensed address-to-parcel/building resolution, durable shortlist or multi-property side-by-side comparison, notes, accounts/permissions, full accessibility and responsive owner acceptance, geocoding/map service, approved publisher-field display, current property prices, live listings, public deployment and final UI visual identity.

For the provisional source/API/schema meaning see the [P3 contract and proposed ERD](../docs/engineering/P3_APPLICATION_CONTRACT.md). For deliverables and stage gates see the [80-package roadmap](../docs/P_PHASE_ROADMAP.md).
