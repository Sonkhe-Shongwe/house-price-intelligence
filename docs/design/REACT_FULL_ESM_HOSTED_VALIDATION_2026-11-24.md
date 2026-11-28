# Full React / MapLibre ESM visual-study gate: hosted browser evidence

**Verified:** 24 November 2026. **Classification:** Isolated technology and design-prototype verification, **not** a final UI approval, production frontend integration, real-map accuracy decision, external mapping provider selection or portfolio P-stage acceptance.

## Exact-source verification

Source: [feature/react-maplibre-full-spike-validation-20261123](https://github.com/Sonkhe-Shongwe/house-price-intelligence/tree/feature/react-maplibre-full-spike-validation-20261123/design-prototypes/react-map-spike).

**Green exact-head commit:** [3affb4d49ce52821d2813bb57767b71bd8833f8b](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/3affb4d49ce52821d2813bb57767b71bd8833f8b).

**Passing [GitHub Actions run 45298710007](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45298710007):**

- Clean `npm ci --no-fund --no-audit` from a **committed package-lock.json**, React 19.3.1, TypeScript 7.0.2, Vite 8.3.8, MapLibre 6.19.0.
- `npm run typecheck` and `npm run build` succeeded; production ESM Vite output contained a separate **lazy MapLibre chunk** and **bundled same-origin worker**.
- **Six of six real Google Chrome 157 / Playwright Chromium scenarios passed** against the normal Vite production preview server, not a transformed IIFE.
- A strict `HPI_REQUIRE_WEBGL=1` assertion proved that the **complete React interface reached its MapLibre WebGL-ready state**, not merely the error fallback. It rendered inline fictional geometry with **no external browser requests**.
- Other browser scenarios checked linked SVG pins/ranked sale cards, exact fictional cents in UI text, a subject with zero eligible records, shortlist note state and reload reset, 320px/375px mobile panel switching/no horizontal page overflow, reduced-motion styling and screenshots of both styles, mobile and WebGL.

[Workflow source](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/feature/react-maplibre-full-spike-validation-20261123/.github/workflows/react-map-full-source-ci.yml). Screenshots and compiled `dist/` are archived in the run's short-lived `hpi-react-map-full-source-45298710007` artifact.

## Measured uncompressed build output

| Asset | Bytes | Reported Vite gzip |
| --- | ---: | ---: |
| Initial React interface JavaScript | 242,749 | approximately 75.90 KB |
| On-demand MapLibre JavaScript | 1,057,902 | approximately 292.43 KB |
| Separate MapLibre worker | 550,379 | not reported |
| Initial stylesheet | 16,853 | approximately 4.29 KB |
| On-demand MapLibre stylesheet | 71,339 | approximately 10.25 KB |

This is asset size from a synthetic laboratory app. It is **not** measured LCP/INP/CLS, real field network performance, or evidence that MapLibre should be preferred over SVG. The optional map chunk is still comparatively large.

## Defects discovered by genuine hosted ESM validation

1. Initial standalone toolchain checks found three MapLibre 6 API incompatibilities: no default export, obsolete `supported()` check, and correct Vite worker import `?worker&url`. The standalone code was corrected before this source-controlled milestone.
2. The full React v0.5 prototype passed an offline Chromium harness but failed its first actual hosted mobile test due to **page-wide overflow caused by unwrapped narrow status and evidence labels** at small widths.
3. A CSS-only correction on the isolated branch wrapped mobile status values and narrow evidence columns while preserving the original assertion that `scrollWidth` must not exceed the viewport. The exact-head retest passed all six scenarios.
4. The runner's `playwright install --with-deps` setup was unusually slow. The tested workflow uses the runner's installed Chrome 157 when available and a pinned Playwright installation. That is an execution-time improvement; it does not weaken the WebGL-ready or no-third-party-request assertions.

Passing tests do not constitute a complete accessible-map audit, adversarial security review or evidence-source authorisation. The React error-boundary fallback had prior local-browser evidence, but this successful hosted run specifically exercised the **normal WebGL-ready path**, not a forced mid-flight worker failure.

## Still open

- **Owner aesthetic choice:** Editorial and Intelligence directions and map/list layout must be reviewed, potentially revised or discarded. No visual identity is approved.
- **Production CSP/static serving:** HPI's actual Python WSGI server serves only allowlisted assets and restricts worker/resource origins. This spike was served through Vite preview, **not** through that server.
- **Trusted geographic contract:** The six original fictional parcel records share identical legacy test coordinates. The prototype's fictional virtual map positions are **not property geography**, surveyed centroids or building locations. Real map data and source-linked read-only FeatureCollection remain unimplemented.
- **Mapping rights/cost/attribution:** No basemap tile supplier, geocoder, satellite imagery, publisher sale/coordinate permissions or commercial licence has been approved.
- **Production performance/accessibility:** MapLibre still needs low-end device profiling, reduced-motion/keyboard/screen-reader review beyond covered tests, WebGL unavailable / worker-failure fallback against the served production build, and CSP testing.
- **Deployment/ownership:** This code is on an isolated feature branch, **not** the ongoing development app, stable main or a public release. PR #4 remains draft. P3 **10%** and total weighted **22.8%** remain unchanged until owner phase accounting.
- **Original HPI regression suite:** Existing Python/browser gates remain distinct; their latest feature-branch check should be verified separately before any future merge.

## Decision and suggested next milestone

**Technical compatibility gate: PASSED** for the complete source's local-origin ESM/MapLibre renderer and six UI journeys. **Product adoption gate: OPEN.**

Next, conduct an owner visual review of the actual green-run screenshots and map-to-evidence interactions. If a visual direction is approved, create a separately scoped integration proposal for HPI's existing Python WSGI static serving/CSP, frozen comparable source IDs, geometry contract, auth/privacy and final UX tests. No automatic framework selection, merge, deploy or scope expansion follows from this proof.

[Issue #7](https://github.com/Sonkhe-Shongwe/house-price-intelligence/issues/7) tracks the remaining owner decision and integration gates; [current checkpoint](../CHECKPOINT.md) remains the operational handoff.
