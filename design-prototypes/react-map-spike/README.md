# Spatial Lab: isolated React / TypeScript / MapLibre feasibility proof

**Owner status: research prototype, not an approved framework, map service, app migration, production build, or phase-completion gate.**

This is a deliberate continuation of [`../map-evidence-studio.html`](../map-evidence-studio.html). The current Python/SQLite application is unchanged. Two rendering approaches show **the same invented buyer/comparable records**:

- **SVG baseline:** beautiful, stable, accessible diagram with explicit marker/card selection. No GPU requirement.
- **MapLibre GL JS v6 experiment:** GPU WebGL2 canvas with **inline virtual-coordinate GeoJSON**, stylised park/road layers, click-to-select and a separately bundled worker. **Absolutely no real geographic coordinates, tiles, geocoder, property facts or valuation.**

Both operate with React 19, TypeScript, Vite 8 and custom CSS tokens. All dependency and map choices are subject to later architecture and user review. There is no server API connection or account/private note storage. Text is synthetic study fixture only.

## Run locally

```bash
cd design-prototypes/react-map-spike
npm ci
npm run build
npm run dev
```

Navigate to the displayed `http://127.0.0.1:5173/` URL. The app requires Node 22.12+ (or a currently supported Vite runtime). **After installing development dependencies, all browser content and rendering are local:** no basemap CDN, API key or external fonts. Browser WebGL2 availability determines whether vector rendering works; the evidence list and SVG are available regardless.

Run `npm run typecheck` to check typed TSX and `python -m unittest discover -s design-prototypes/react-map-spike/tests -p 'test_*.py' -v` from the repository root **after `npm run build`**, with Playwright and Chromium available. The isolated feature branch is committed as editable source; [full-source CI run 45298710007](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45298710007) passed a clean `npm ci`, production ESM build, actual MapLibre WebGL-ready and six real browser tests. Do not infer approval to replace the existing Python/SQLite frontend or deploy.

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
