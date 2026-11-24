# Source-bound React integration boundary: P3 and P6 evidence

**Date:** 24 November 2026  
**Status:** Bounded experimental adapter on an isolated feature branch. No visual approval, production frontend migration, real geographic API, new data rights, public release, PR #4 merge, or phase credit.

## 1. Problem

The tested React/MapLibre design uses explicitly invented labels, sale amounts and diagram coordinates. The actual HPI fixture API exposes frozen, checked historical-sale evidence with a different structure. Substituting one object for another would risk fictitious map positions appearing to be verified locations, floating-point price conversions, or client-side changes to server matching.

The new standalone TypeScript adapter, at design-prototypes/react-map-spike/src/evidenceBridge.ts, defines an untrusted-JSON to read-only-presentation boundary. The current backend, SQLite, live browser, and original React concept screens are untouched.

## 2. Authoritative API interpretation

| Actual endpoint | Server semantics | Proposed presentation rule |
| --- | --- | --- |
| POST /v1/addresses/search | Multiple possible invented address candidates; no automatic parcel selection | Future UI must make the parcel choice explicit, not infer a building |
| GET /v1/addresses/{id} | Synthetic mapping, parcel-only scope, building identity unverified | Preserve identity limitations |
| POST /v1/investigations | Server-owned matching/eligibility, exact source and asking-price roles | Current adapter does NOT submit investigations or recompute eligibility |
| GET /v1/investigations/{uuid} | Verified frozen source, contract version p3-draft-v0.3, valuation null, exact decimal USD strings, warnings, build/snapshot IDs | Validate before rendering; retain original dollars and cents without floating-point conversion |
| GET /v1/shortlists/{uuid} | Up to three linked investigations, each rechecked for immutable evidence; notes stored separately | Check nested saved IDs, membership, note text and policy version |
| PATCH /v1/shortlists/{sid}/entries/{iid} | Actual mutable note persistence | Deliberately not wired yet; future UI must show pending/saved/failure states and never claim account privacy |

Backend response statuses include supported_neighbourhood, exploratory_spatial, insufficient_data and out_of_coverage. Spatial fallback must remain labelled exploratory; it cannot be portrayed as a validated valuation. A subject asking price is user-reported, and a completed sale amount is the exact source string, not a prediction.

## 3. Key safeguards implemented

1. Reject API contract versions other than p3-draft-v0.3, malformed saved UUIDs, non-fixture source kinds, missing build/snapshot provenance, unsupported statuses and non-null valuation.
2. Require two-decimal USD text for both user-reported asking amounts and recorded sales. Format only whole dollars with BigInt and preserve cents. Reject legacy float sale-price fields and invalid decimal strings.
3. Check the number of displayed comparables agrees with selected_count; keep server evidence order and explanations. The comparable presentation key is only an investigation-specific UI key, **never an invented transaction ID**.
4. Respect parcel identity only, without asserting that a parcel is a verified house. Do not accept elevated building identity from an address-linked result.
5. Keep a shortlist note distinct from its frozen child investigation. Reject duplicate members, notes longer than the backend limit and mismatched child IDs.
6. Every adapted investigation explicitly reports that geographic position is unavailable because there is **no verified server map-feature contract**. The separate diagram points and virtual MapLibre coordinates cannot be associated with API results.
7. The bridge performs **no fetch or mutation**. It is a pure conversion step, not a production client, authentication layer or substitute for the Python matcher.

## 4. Test basis and confidence limits

The isolated CI adds a Python exporter that runs the **real backend.synthetic_http WSGI application** using an invented in-memory SQLite fixture. It creates a supported and an insufficient investigation, a two-member shortlist, and reopens frozen evidence through the actual API paths. The test compiler uses the locked TypeScript dependency, and Node then verifies the actual API JSON against the adapter.

Test cases check supported and insufficient statuses, exact cents including very large numbers, source snapshots, unavailable map coordinates, note/child identity integrity, plus adversarial changes to prices, statuses, counts, contract versions, identity and provenance.

**Verified CI:** [isolated React / real P3-P6 bridge run 45300580369](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45300580369) at exact isolated branch commit `ee5410e5d88203b41f8b9486bb8da6ea6498abcc` passed clean npm install, TypeScript, code-split Vite build, actual local WSGI-backed source JSON, exact dollars/cents and **13 negative/tamper assertions**, plus **6/6 real Chromium MapLibre/UI journeys**. The bridge test uses the pinned TypeScript compiler rather than requiring an extra esbuild package. These tests do not yet connect the React browser to a running Python HTTP listener. The WebGL browser tests separately exercise the prototype's original invented points, not API-based property geography.

## 5. Future owner-approved integration sequence

1. Evaluate the current visual concepts and select a deliberate art direction, or reject both, before any final UI migration.
2. Add a future same-origin API request layer with abort/race handling, no caching, and the typed response validation above. On failure, clear old UI state and show a readable error.
3. Wire a source-backed investigation and shortlists into React **with the map disabled**, then prove the existing localhost WSGI host/origin and authentication limitations are preserved.
4. For serving a Vite production build from Python, explicitly review and test a bounded hashed-asset manifest allowlist, strict MIME types and CSP worker-src support. Do not replace the allowlist with an arbitrary filesystem server, wildcard CORS or relaxed content security.
5. Only after a source-owned geometry API, identity precision and map rights are approved, introduce geographic markers, licensed basemap/attribution, fallback and browser/performance testing. Do not infer physical distances from SVG or virtual coordinates.
6. Revalidate actual Python/SQLite persistence, frozen snapshot/cents checks, backend error cases, frontend accessibility, low-power/no-GPU, narrow-screen and browser security before any migration proposal.

## 6. Owner and repository boundaries

The experiment is restricted to the isolated feature branch. The canonical development application, stable main, draft PR #4, old synthetic fixtures and weighted P0-P8 22.8% baseline remain unchanged. The adapter is a useful engineering proof but not an approved production user interface or the long-unresolved geographic evidence contract.
