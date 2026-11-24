# HPI source-connected React screen: bounded read-only integration gate

**Recorded:** 24 November 2026  
**Owner decision status:** Experimental, isolated and NOT a frontend-stack adoption, final visual approval, real property map, data-rights approval, public deployment, PR #4 merge or phase acceptance.

## 1. What was added

The isolated React study at design-prototypes/react-map-spike now has a separate **/source-review** screen. Unlike the earlier attractive invented-map demonstration, the new route fetches **actual saved fictional evidence** from the existing Python WSGI API via a **same-origin, loopback-only** preview server. It uses the already-tested read-only P3/P6 TypeScript adapter in src/evidenceBridge.ts, never recomputes source evidence or invents sale prices.

The original SVG/MapLibre fictional-art-direction study at **/** remains separate, with deliberately invented sale locations and examples. No real coordinates from the backend are attached to either view.

### What a reviewer can inspect

- Two persisted-in-memory demonstration investigations: one source-backed supported case (three earlier fictional sales, exact original cents), and one insufficient-data case (zero eligible sales).
- Rank-ordered comparable sale cards showing **real Python fixture-response** sale text and exact matcher explanation, with a keyboard-focusable selected-sale state.
- A conspicuous **Location unavailable** section, with no map markers, simulated distances or inferred building location. The adapted API has no verified map feature contract.
- An actual frozen two-property shortlist obtained from the Python shortlist GET endpoint. Its notes are displayed **read-only**, rather than pretending a typed textarea is saved.
- A build/snapshot provenance section, original warnings, source status, analysis date and explicit absence of a generated valuation.
- Responsive narrow-screen and reduced-motion rendering.

### Source and runtime files

| File | Purpose |
| --- | --- |
| src/SourceReview.tsx | Lazy-loaded React read-only evidence and shortlist view; GET-only client state with AbortController and fail-closed source adaptation |
| src/sourceReview.css | New restrained, responsive CSS without remote fonts or inline-style exceptions |
| src/main.tsx | Route split: /source-review loads the source-connected component; / remains the original fictional-map laboratory |
| src/evidenceBridge.ts | Existing source-bound v0.3 JSON adapter: exact money, source snapshots, status and no-geography guard |
| tests/source_preview_server.py | Deliberately isolated trusted loopback WSGI wrapper, fixed built-asset allowlist and seed-only read-only case index |
| tests/test_source_review.py | Real Chrome against compiled React ESM -> local Python WSGI -> SQLite, plus CSP, mutation denial, tamper rejection and mobile tests |
| .github/workflows/react-map-full-source-ci.yml | Clean npm ci, TypeScript, Vite, existing six design tests and independent seven source-connected Chrome tests |

## 2. How to run the isolated proof

From the repository root on the **isolated feature branch**:

    cd design-prototypes/react-map-spike
    npm ci
    npm run build
    cd ../..
    python design-prototypes/react-map-spike/tests/source_preview_server.py --port 8797

Open http://127.0.0.1:8797/source-review in your browser. The server exposes only a **fictional, disposable, in-memory fixture**. Every launch creates a fresh saved set of UUIDs for two investigations and their shortlist, so no external property data or private user notes should be entered.

**Note:** The preview is not HPI's approved runtime or Python static-asset migration. The existing backend and frontend files are not modified.

## 3. Security contract preserved in the preview

- Bind to **127.0.0.1 only**; reject non-loopback remote addresses, unexpected Host, forwarded/proxy headers, unrelated Origin and cross-site/same-site Fetch Metadata.
- Expose only GET on /source-review, /, the precompiled exact hashed JS/CSS assets, /_study/cases, /health, and existing GET /v1/investigations/{uuid} and /v1/shortlists/{uuid} paths. All mutating verbs are blocked. Arbitrary paths, source maps and dotfiles are never served.
- Read bytes from an explicit allowlist constructed once from **the trusted dist build** at startup, with filename and MIME restrictions and no URL-path-to-filesystem resolution.
- Keep **no-store, nosniff, frame denial, no-referrer, same-origin resource policy and default-deny CSP**. Only the isolated wrapper explicitly adds worker-src 'self' to the existing self-only allowlist; it does not add unsafe-inline, wildcard external hosts or CORS.
- Validate the actual API response against the p3-draft-v0.3 synthetic-data adapter before rendering. An unexpected valuation or altered contract produces an error and clears stale sale cards.
- Abort stale requests on selection changes; do not issue POST/PATCH/DELETE from the React source-review client.

This **does not** solve account isolation, production access control, concurrency, backups or a public deployment. It is one machine's fictional-data browser proof.

## 4. Geography remains separately blocked

Existing source rows still position six invented parcels at the same dummy coordinates. The actual WSGI investigation response exposes **no source-verified geographic feature collection**. The map panel is intentionally unavailable for any source-connected investigation. The old demo's fabricated SVG pins and virtual MapLibre coordinates must never be joined to real API comparable IDs.

A future geographic product needs a source-owned map endpoint with reviewed geometry/precision, sale transaction identity, build/snapshot provenance, licensing and permitted basemap display, plus an accessible list when geometry is missing.

## 5. Test and acceptance interpretation

The new source-connected suite contains **seven** Chrome journeys: actual source evidence and exact sale explanation; stale sale cleanup on insufficient evidence; two-property frozen shortlist with read-only notes; 320px/375px and reduced-motion; strict CSP and host/proxy/mutation/path checks; fail-closed tampered-valuation response; and desktop/mobile visual screenshots.

These run alongside **six** existing original design/MapLibre Chrome journeys, Python fixture tests and the previous TypeScript WSGI contract checks.

**CI status:** Refer to the latest exact-SHA isolated workflow at .github/workflows/react-map-full-source-ci.yml before saying this milestone is green. Results are not an owner decision to change HPI's public frontend or acceptance percentages. Owner review of aesthetics, stack, real market rights and final accessibility remains pending.

## 6. Next gated step

After owner visual review, compare the source-connected React view with the current integrated HTML/JS browser for actual buyer tasks. Make a separate explicit decision about the frontend transition. If approved, plan an integration into the existing Python service with a reviewed manifest-based production asset server, evidence preservation, recovery and rollback, and independent map-source validation. Do not infer consent to merge, deploy or raise the official 22.8% score.
