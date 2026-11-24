# Spatial Lab: isolated React / TypeScript / MapLibre feasibility proof

**Owner status: research prototype, not an approved framework, map service, app migration, production build, or phase-completion gate.**

This is a deliberate continuation of [`../map-evidence-studio.html`](../map-evidence-studio.html). The current Python/SQLite application is unchanged. Two rendering approaches show **the same invented buyer/comparable records**:

- **SVG baseline:** beautiful, stable, accessible diagram with explicit marker/card selection. No GPU requirement.
- **MapLibre GL JS v6 experiment:** GPU WebGL2 canvas with **inline virtual-coordinate GeoJSON**, stylised park/road layers, click-to-select and a separately bundled worker. **Absolutely no real geographic coordinates, tiles, geocoder, property facts or valuation.**

Both operate with React 19, TypeScript, Vite 8 and custom CSS tokens. All dependency and map choices remain subject to owner review. **The original SVG/MapLibre concept at `/` remains standalone and invented.** A separate **`/source-review` route** reads the actual local Python/SQLite fixture API through an isolated read-only same-origin preview, without reusing invented map coordinates. No accounts, private notes, real property datasets or production permissions are supplied.

## Run locally

```bash
cd design-prototypes/react-map-spike
npm ci
npm run build
npm run dev
```

Navigate to the displayed `http://127.0.0.1:5173/` URL. The app requires Node 22.12+ (or a currently supported Vite runtime). **After installing development dependencies, all browser content and rendering are local:** no basemap CDN, API key or external fonts. Browser WebGL2 availability determines whether vector rendering works; the evidence list and SVG are available regardless.

Run `npm run typecheck` to check typed TSX and `python -m unittest discover -s design-prototypes/react-map-spike/tests -p 'test_*.py' -v` from the repository root **after `npm run build`**, with Playwright and Chromium available. The isolated feature branch is committed as editable source; [full-source CI run 45298710007](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45298710007) passed a clean `npm ci`, production ESM build, actual MapLibre WebGL-ready and six real browser tests. Do not infer approval to replace the existing Python/SQLite frontend or deploy.

## Source-backed P3/P6 adapter validation (24 November)

The separate **evidenceBridge.ts** module is a read-only candidate for presenting the *actual* Python fixture API, not the example data in data.ts. It validates p3-draft-v0.3 exact-decimal sale prices, synthetic build and snapshot provenance, evidence status, and up to three verified shortlist entries. Crucially, adapted API investigations always report **no verified map geometry**; the invented SVG/MapLibre positions in this prototype are never reused for source-backed records.

Run the isolated cross-layer check as part of [.github/workflows/react-map-full-source-ci.yml](../../.github/workflows/react-map-full-source-ci.yml), or reproduce after npm ci from the repository root by exporting fixture-only WSGI JSON with tests/export_real_api_contract.py, compiling evidenceBridge.ts with the pinned TypeScript compiler, and executing tests/test_evidence_bridge.mjs. This test is deliberately separate from the six browser UI tests.

**Verified** by [GitHub Actions 45300580369](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45300580369): the actual WSGI API JSON and 13 integrity/tamper guards passed, alongside six real Chrome journeys and the clean Vite build. See the [source/geometry integration contract](../../docs/design/READ_ONLY_REACT_EVIDENCE_ADAPTER_2026-11-24.md). **That adapter-only test does not itself establish browser-to-Python connectivity.** The separate source-connected preview below does; real geometry, live application changes, framework acceptance and release remain unapproved.

## Explicit parcel selection and saved investigation workflow (24 November)

The separate **/buyer-workflow** route is an opt-in fixture-only React -> Python WSGI -> SQLite integration proof. It searches invented addresses, distinguishes two synthetic parcels sharing one address, requires selection and server-side PIN verification, accepts buyer-reported area/asking price/date, saves through the original POST investigation route, and immediately reopens the frozen evidence with a GET. Exact sale strings, warnings and provenance remain Python-owned. The map stays **unavailable** because there is no verified geographic feature contract.

Run from the repository root:

```bash
npm ci --prefix design-prototypes/react-map-spike
npm run build --prefix design-prototypes/react-map-spike
python design-prototypes/react-map-spike/tests/source_preview_server.py --port 8797 --enable-buyer-workflow
```

Then open **http://127.0.0.1:8797/buyer-workflow**. Test searches: **101 Fictional Way** (one parcel) and **105 Fictional Court** (two distinct parcel options). The flag explicitly permits only address search and investigation creation. Remove it to restore the original GET-only preview; no shortlist mutations are allowed in either mode.

An additional [eight-scenario browser test](tests/test_buyer_workflow.py) covers creation, exact cents, frozen reopening, ambiguous parcel identity, stale search clearing, denial of other writes, mobile and screenshots. It runs in the isolated [React CI workflow](../../.github/workflows/react-map-full-source-ci.yml). The result is **not** proof of production readiness or public security. See the [buyer-workflow integration gate](../../docs/design/REACT_BUYER_WORKFLOW_CREATE_REOPEN_GATE_2026-11-24.md).
## Working read-only React -> local Python/SQLite preview (24 November)

The new source-connected investigation screen is separate from the invented-map style lab. It performs **real same-origin GET requests** to HPI's existing WSGI `GET /v1/investigations/{uuid}` and `GET /v1/shortlists/{uuid}`, using fresh fictional records seeded by the isolated Python runner. It displays exact cents, source snapshots and matching explanations, with a deliberate **Location unavailable** panel and no fictitious property pins.

Run from the **repository root**:

```bash
npm ci --prefix design-prototypes/react-map-spike
npm run build --prefix design-prototypes/react-map-spike
python design-prototypes/react-map-spike/tests/source_preview_server.py --port 8797
```

Open http://127.0.0.1:8797/source-review in your browser. This local WSGI preview is **read-only**. It serves a finite built HTML/hashed asset allowlist and guarded GET paths, rejects writes, proxy headers and cross-site origins, and inherits the backend's exact source contracts. No other HPI application route is modified.

[Detailed integration/security handoff](../../docs/design/SOURCE_CONNECTED_REACT_PREVIEW_GATE_2026-11-24.md) and [isolated feature branch](https://github.com/Sonkhe-Shongwe/house-price-intelligence/tree/feature/react-maplibre-full-spike-validation-20261123).

**Verified browser end-to-end:** [GitHub Actions 45306167930](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45306167930) passed the original six WebGL/UI tests and seven new source-connected Chrome tests. This is a local fictional-data proof, not the public HPI app, approved geographic coordinates, final visual direction or phase acceptance.
## Map accuracy and privacy boundary

`src/data.ts` uses **diagram x/y percentages**. The MapLibre adapter converts these percentages to entirely virtual positions near the origin to exercise GeoJSON and WebGL. Those numbers are **not** verified longitude/latitude for any subject, sale, neighbourhood or parcel. They must never be passed to the HPI matcher, used to calculate real distance, or published as geographic evidence.

MapLibre's `setWorkerUrl` is set to a **Vite-bundled same-origin worker asset (`?worker&url`, per MapLibre v6 guidance)**. `style` contains local GeoJSON only, no network sources. This investigates one potential solution to the existing Python WSGI CSP/worker issue; it **does not** prove compatibility with the current strict WSGI static allowlist or production CSP. Both require a separately reviewed integration contract.

The supported fictional subject has three invented earlier-sale records. Another fictional subject has **zero**. Switching clears the previous subject's selected sales. Neither screen derives an estimated price; comparable sale text remains supplied data, not recomputed UI. The shortlist notes are temporarily in memory and disappear on reload.

## Decision criteria, not automatic acceptance

| Question | Evidence this spike produces | Still required |
| --- | --- | --- |
| Can typed component UI keep map and list selection in sync? | Real Chromium keyboard/click test and focusable evidence controls | Screen-reader audit, stakeholder task validation |
| Does a more advanced map automatically improve buyer usefulness? | Same fictitious records in SVG and WebGL2 | Owner preference and meaningful real geographical use case |
| Can MapLibre avoid tile-provider requests? | Inline style/source, no remote browser requests in CI | Licensed real basemap, proper attribution, real geographic API |
| Is MapLibre accessible without WebGL? | Graceful fallback and always-present evidence list | Full keyboard canvas controls if required, low-end mobile check |
| Is a React/Vite build maintainable? | Separate components, typed fixture, pinned declared direct dependencies, proposed build and browser tests | Safe manifest-based WSGI integration, rollback, production dependency/security and performance audit |
| Is it fast enough? | Build artifact and planned browser timing/screenshot evidence | Device-side profiling, measured bundle and Core Web Vitals against release-like assets |

See [mapping research](../../docs/design/PROFESSIONAL_UI_AND_MAPPING_RESEARCH_2026-11-23.md), [Visual Foundation proposal](../../docs/design/VISUAL_FOUNDATION_V1_IMPLEMENTATION_PROPOSAL_2026-11-23.md) and the [live checkpoint](../../docs/CHECKPOINT.md). **P3 10%, overall 22.8% unchanged**; PR #4 and `main` untouched.

## Isolated hosted validation

The workflow at `.github/workflows/react-map-full-source-ci.yml` runs a clean `npm ci`, a TypeScript/Vite build, and real Chromium checks against the built ESM application with its own worker. It does not replace the working HPI app.
