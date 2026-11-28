# React / TypeScript / Vite + MapLibre GL JS v6: verified compatibility spike

**Date:** 23 November 2026. **Classification:** Experimental technology evidence, not application integration, a final visual-system choice, a real geographic map, a permitted third-party tile provider or P-stage acceptance.

## What was actually run

A new, narrowly triggered [isolated GitHub Actions workflow](../../.github/workflows/react-map-bundler-compat.yml) generates a disposable React/TypeScript/Vite app, installs published npm packages, builds the site, and uses genuine Chromium to switch from a simple SVG diagram to an inline-GeoJSON MapLibre WebGL renderer. The application uses only invented geometry and makes **no external map/tile/geocoder/font calls** in the browser.

**Verified green exact-commit run:** [CI 45270177840](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45270177840) at development commit [4647022](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/4647022d8c10bd59861f72170d9ed00882e27d4e). Its TypeScript check, Vite build, React interaction, actual WebGL/map-ready state, screenshot and no-remote-request assertions all passed. The generated, **not yet committed** experimental lockfile, distribution, and Chromium screenshot are in the [run artifact](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45270177840/artifacts/14865206063).

**Installed directly tested versions:** React and React DOM 19.3.1; MapLibre GL JS 6.19.0; Vite 8.3.8; TypeScript 7.0.2; Node 22 in GitHub Actions. The smoke is deliberately small, and **does not validate the previously prepared full high-fidelity React design source** or its six prospective Playwright acceptance tests. That source is a separate downloadable draft candidate under owner review; do not call it integrated or browser-green.

## Compatibility lessons from three successive CI typecheck attempts

1. **ESM exports:** MapLibre v6 no longer provides a default export. `import maplibregl from 'maplibre-gl'` failed TS1192. Use `import * as maplibregl from 'maplibre-gl'` or named exports.
2. **Worker bundling:** Follow the official Vite integration `import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'` and `maplibregl.setWorkerUrl(workerUrl)`. The original unvalidated candidate used plain `?url`; that was corrected locally.
3. **WebGL support:** In the v6 build, `maplibregl.supported()` fails TS2339. Construct the map and catch MapLibre's `GPUInitializationError` (or a related startup exception), presenting a usable list/SVG fallback.
4. **GeoJSON typing:** The temporary smoke's `GeoJSON.FeatureCollection` namespace failed TS2503 without an explicitly available namespace. Use a carefully typed local literal or explicitly import an installed GeoJSON type package. This was a problem in the **smoke fixture**, not established as a defect in the full source.
5. **Real browser test:** Chromium reached `ready` while rendering a fictional circle from local inline GeoJSON, with no remote browser requests or uncaught client errors. A working WebGL proof is **not** evidence of correct parcel coordinates, source reuse permission or safe production CSP.

Official library reference: https://maplibre.org/maplibre-gl-js/docs/ and https://maplibre.org/maplibre-gl-js/docs/guides/v5-to-v6-migration-guide/ .

## Measured build weights from the disposable smoke

| Built file | Uncompressed |
| --- | ---: |
| JavaScript entry, React and MapLibre combined (not lazy) | 1,275,898 bytes (~1.28 MB) |
| Dedicated same-origin MapLibre worker | 550,379 bytes (~550 KB) |
| CSS including MapLibre styles | 71,339 bytes (~71 KB) |
| Entry HTML | 370 bytes |

The entry JS was reported by Vite as approximately **360 KB gzip**, CSS approximately **10.25 KB gzip**. All counts are from this **minimal bundled trial**, not a benchmark of the full design or user page. Vite reported a large-chunk warning. This strongly supports **lazy-loading the vector renderer only when the user switches to a map**; keep text evidence and lightweight fallback accessible before/without WebGL. Measure the *full* candidate bundle after its own verified build, and separately profile real devices, LCP, INP, CLS and browser memory.

## Boundaries and further proof needed

- The source artifact drafted in the previous session is **not yet committed as editable files or tested end to end**. Its MapLibre worker, ESM imports and obsolete support check were identified/corrected in the **local draft source**, but the original React app must pass its own `npm ci`, `npm run build` and all six Playwright tests before integration or technology selection.
- The generated smoke lockfile lives in a time-limited workflow artifact. A future official prototype commit needs a reviewed lockfile and `npm ci` for reproducibility, dependency licence review and vulnerability policy.
- The smoke runs through a local Vite preview, not the existing Python WSGI static asset allowlist or strict CSP. Production map worker, inline style, generated CSS/JS and any actual tile host require a **separate safe serving and CSP review**.
- All virtual coordinates, price labels and example properties are invented. Real map display depends on source-owned, permissioned geographic evidence and accuracy, not a successful renderer.
- No `frontend/`, `backend/`, SQL schema, source rights, test acceptance, `main`, PR #4, deployment or P-stage score was changed. Formal P3 remains 10% and overall MVP 22.8%.
- The existing [high-fidelity SVG visual study](../../design-prototypes/map-evidence-studio.html) is the working reviewed baseline. [Issue #7](https://github.com/Sonkhe-Shongwe/house-price-intelligence/issues/7) tracks the outstanding complete React app validation and owner decision.

**Decision status:** MapLibre v6 with React/Vite is **technically feasible** as shown by the isolated working browser proof. The product has **not selected** React, MapLibre, provider, map display rights, design direction or a migration.
