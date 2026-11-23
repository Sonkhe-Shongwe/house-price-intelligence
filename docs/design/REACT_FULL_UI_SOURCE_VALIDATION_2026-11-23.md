# React + MapLibre full UI design spike: bounded validation

**Recorded:** 23 November 2026. **Stage:** isolated candidate and owner-review package, not the production HPI frontend, P-stage acceptance, final aesthetic or map data approval.

## What was validated

The owner-conversation v0.4 source ZIP was extracted without changing the HPI backend or `frontend/`. Exact experiment source used React 19.3.1, React DOM 19.3.1, TypeScript 7.0.2, Vite 8.3.8 and MapLibre GL JS 6.19.0. The dependencies were taken from the independently [successful GitHub compatibility run 45270604600](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45270604600), whose Linux package tree and lockfile were downloaded as temporary validation inputs.

**TypeScript `tsc --noEmit`: PASSED. Normal Vite production ESM build: PASSED.** The candidate is code-split: the default illustrated SVG map and evidence UI load without the MapLibre source chunk; the `VectorMap` import is deferred until the user selects the optional WebGL view.

The experiment also built a **second, single-file IIFE bundle solely for an offline browser-test harness** because the local Chromium sandbox rejects all browser navigations, including localhost and file URLs. The harness injects the resulting bundled JavaScript/CSS into an empty Chromium document. This is **not the same runtime transport** as serving the normal ESM production build with Vite.

**Six out of six Chromium tests PASSED in the transformed offline harness:**
1. SVG map pin/evidence-card synchronisation and exact invented sale price strings, including cents.
2. Switching to zero eligible sales clears previously selected sales and never implies valuation.
3. Editorial/Intelligence theme and shortlist notes, including the intentional non-persistence of page-only notes.
4. Mobile evidence/map switching and 375px/320px horizontal overflow checks, with reduced-motion treatment.
5. Optional vector mode never destroys the evidence UI, even when the optional module cannot load.
6. Real screenshots of editorial, intelligence, vector-failure fallback and mobile views.

**Important distinction:** The two tests that enter vector mode **saw the new error-boundary fallback**, not successful WebGL rendering in the full design. Browser failure came from single-file IIFE transformation and the local runtime blocking network/file origins, rather than an observed failure of the normal ESM MapLibre source. The separate small [MapLibre v6 GitHub browser smoke 45270177840](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45270177840) has successfully rendered GPU/WebGL with the local bundled worker. **The complete UI with the normal Vite ESM worker has NOT yet passed hosted Chromium.**

## Actual bugs found and fixed in the full candidate source

- A rejected lazy `VectorMap` module previously propagated an uncaught error through the component tree, potentially dropping the entire app. A React `MapImportBoundary` now confines that failure to the map panel. The ranked evidence remains usable.
- The MapLibre component previously handled synchronous constructor failure but could remain stuck at `Preparing local vector renderer` when a worker fails asynchronously. Added a bounded 6.5-second startup fallback, guarded MapLibre `error`/ `load` events and cleanup. This code passed TypeScript and Vite compilation but its normal ESM/WebGL behaviour needs a full hosted test.
- The first error fallback CSS used both absolute-position and relative map-stage classes on one element, causing a full-page overlay. The error content is now correctly nested inside the positioned map panel, as confirmed by a revised Chromium screenshot.
- The source package now contains a reviewed-looking **dependency lock derived from the successful GitHub-installed dependency tree**, with exact pinned versions and `npm install --package-lock-only --offline` consistency passing locally. A clean `npm ci` of the **full source** in GitHub remains unverified. Do not call it a proven reproducible release just because its lockfile parses.

## Measured normal build weights (uncompressed)

| Component | Bytes | Gzip output reported by Vite |
| --- | ---: | ---: |
| Initial React app JS | 242,749 | ~75.9 KB |
| Optional MapLibre JS | 1,057,902 | ~292.4 KB |
| Separate MapLibre worker | 550,379 | not reported |
| Main app CSS | 16,853 | ~4.3 KB |
| Deferred map CSS | 71,339 | ~10.3 KB |

The initial JS is about **81% smaller** than the old, intentionally non-lazy 1,275,898-byte compatibility smoke. These are transferred bundle artifacts, **not Core Web Vitals or realistic startup-time measurements**. MapLibre remains a large optional dependency, and the normal ESM build reports a chunk-size warning; profile real devices if it is selected.

## Reviewable artifact

The finished **owner-conversation ZIP** is named `HPI_React_Visual_Study_V05_Review_Package.zip`. It contains edited source TSX/TS/CSS, exact-version `package.json` and `package-lock.json`, the normal code-split Vite `dist/`, six browser tests, four real screenshots, a verification JSON and a standalone HTML preview. Its local SHA-256 is `cb18520dae7bc7d12c2082b005847c95c2a5888c4031bb2d7b2527d24090a3ea`. The artifact is **available in the owner conversation**, not yet committed as editable React files to GitHub.

The separate `HPI_React_Visual_Study_V05_Standalone_Offline.html` works without npm for visual inspection. It uses the transformed inline bundle, so selecting the MapLibre tab may deliberately demonstrate the graceful fallback rather than display a real vector map.

## Unresolved and formal decision boundary

- The full React source has **not been checked into `development`** or executed by its own exact-source `npm ci` + actual Vite-server Chromium Actions run.
- MapLibre ESM render success in a small, independent compatibility fixture does **not** prove full UI WebGL integration, keyboard map accessibility, security policy compatibility, source-verified geographic accuracy or tile rights.
- Current SQLite synthetic parcel coordinates still coincide at `42.04, -87.68`; the candidate uses separate *invented virtual drawing positions*, which have no geographic meaning.
- No final colour, logo, navigation, framework, mapping service, geocoder, real data, valuation, auth, public deployment or release has been approved.
- `main`, draft PR #4, real application API/DB/UI and P0–P8 weights/scores are unchanged (P3 10%; weighted MVP 22.8%).
- [GitHub Issue #7](https://github.com/Sonkhe-Shongwe/house-price-intelligence/issues/7) remains OPEN for the full-source hosted CI and owner design/architecture decision.

**Next bounded gate:** Commit the full source as editable files to an isolated feature branch (not `main`), run clean `npm ci` with a full-source 6-journey Chromium workflow against the actual ESM build/worker, record screenshots/console/failure proof, and compare the interface against the already verified original standalone SVG. Seek separate owner review before selecting React/MapLibre or modifying the served application.
