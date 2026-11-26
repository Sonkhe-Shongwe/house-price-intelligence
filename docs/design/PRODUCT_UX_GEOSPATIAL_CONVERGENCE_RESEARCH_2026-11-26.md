# Product, UX and geospatial convergence research

**26 November 2026 | Research recommendation, not design approval or implementation authority.** Development baseline 46a046d: all 11 registered workflows passed. Read with [pinnacle vision](../product/PINNACLE_VISION.md), [product brief](../product/PRODUCT_BRIEF.md), [prior mapping research](PROFESSIONAL_UI_AND_MAPPING_RESEARCH_2026-11-23.md), [workspace contract](../engineering/BUYER_WORKSPACE_UX_V1.md), [synthetic geographic contract](../engineering/SYNTHETIC_GEOGRAPHIC_EVIDENCE_V1.md) and [source register](../research/SOURCE_REGISTER.md).

## Competitive findings

Official product documentation reviewed, not hands-on account-based testing:
- [Zillow comparison](https://www.zillow.com/learn/home-comparison-tool-zillow-app/): save, select, compare aligned home facts. Adopt recognition over manual identifiers.
- [Redfin comparable research](https://support.redfin.com/hc/en-us/articles/360018505351-Owner-Estimate): map-assisted selection of nearby similar sales. HPI retains canonical eligibility rules.
- [Property24](https://www.property24.com/property-values): address-led reports and property history, not authority to acquire new South African records.
- [PriceHubble digital reports](https://support.pricehubble.com/hc/en-gb/articles/35308308064145-How-to-use-the-new-digital-reports): integrated charts, map, comparable evidence and dossier; HPI has no validated valuation.
- [LandInsight comparables](https://pages.land.tech/landinsight-product-comparables): filtered geographic exploration; link map and evidence rail without silently rematching frozen results.
- [Cloud CMA Live](https://cloudagentsuite.com/cloud-cma-live): aligned comparison and map presentation; separate decision views from entry forms.

HPI is an evidence-based buyer decision workspace, not a listings marketplace. Differentiation is a product hypothesis, not validated demand.

## Information architecture proposal

1. Workspace: new investigation CTA, recent investigations, named comparisons, coverage/data mode, returning-user empty state.
2. Investigate: search supported source address index; explicitly select unique parcel or abstain; separate user-reported asking price and area; analysis date; submit once.
3. Dossier: verified/approved property label if available, evidence status/count, asking price, analysis date, comparable rail, ranked table and optional map, matching rationale, source/version, limitations. Parcel is not verified building identity.
4. Saved: owner-scoped recent records, filters, one-click reopen and select for comparison; explicit list bound, no routine UUID entry. Do not invent old property labels; consider optional buyer nickname contract.
5. Compare: two or three properties, aligned statuses, user asking prices, attributes, historical sales and notes; map only where supported; save/reopen, preserve drafts and pending writes across navigation; no automatic winner.
6. Methodology: coverage, inclusion rules, missing data, provenance; material caveats stay visible.
7. Authentication: branded entry/exit, existing Auth0 flow, expired-session/retry states; no new provider.

First flagship: one accepted market/class, historical evidence, owner-safe saved workspace, comparison and authorised browser-only release. Map should support evidence, but actual geographic disclosure is gated. Pinnacle extensions (validated valuation/intervals, live listing feeds, market/amenity layers, ownership costs, reports, monitoring) require separate research and validation.

## Map stack and unresolved decisions

- Keep proven React/TS/Vite and [MapLibre](https://maplibre.org/maplibre-gl-js/docs/) as renderer candidate. Reuse lazy same-origin worker, selection/fallback behaviour from GeoMapPanel/GeoVectorMap and virtual fixtures.
- Separate geometry from basemap. [Cook County historical parcel metadata](https://catalog.data.gov/dataset/assessor-parcel-universe) covers previous tax years; [current parcel universe](https://datacatalog.cookcountyil.gov/Property-Taxation/Assessor-Parcel-Universe-Current-/pabr-t5kh) identifies centroid coordinates and missing geography. Centroid is not rooftop/building identity. Prior bounded audit found 137 coordinate pairs; as-of validity and rights remain unresolved. No property rows fetched here; private projection deliberately withholds geometry.
- First basemap experiment candidate: [Protomaps regional PMTiles](https://docs.protomaps.com/basemaps/downloads), separately versioned OSM-derived context with required attribution. Benchmark archive size, extent/zoom, fonts/sprites, HTTP Range/CORS/CSP, free hosting quotas and update model before adoption. [PMTiles](https://docs.protomaps.com/pmtiles/) uses range requests; open data does not guarantee free delivery. No download, provider account or hosting authorised.
- [MapTiler](https://www.maptiler.com/terms/cloud/) free plan limited to noncommercial/R&D; evaluate only under appropriate terms. Proprietary hosted alternatives not necessary now. [OSM public raster policy](https://operations.osmfoundation.org/policies/tiles/) requires suitable Referer, attribution/cache, no bulk use; restrictive current CSP/referrer policy incompatible with direct use as-is. [Nominatim policy](https://operations.osmfoundation.org/policies/nominatim/) prohibits client autocomplete on public service; prefer existing bounded address index.
- PostGIS is a potential later spatial tool, not required for small first evidence map. [ST_DWithin](https://postgis.net/docs/ST_DWithin.html) supports geographic metres and index-assisted queries. Verify actual need and platform support before any separate migration; do not replace current price-free matcher or recalculate frozen evidence.
- Proposed versioned owner-scoped read-only geometry DTO (not implemented): investigation ID, source build and geometry revision, kind/precision, attribution, availability/reason, subject and ranked comparable GeoJSON, opaque feature keys, distance support flag. Check ownership, rank/count, source seal, extent, precision, rights and identity. Real coordinates withheld until authorised; virtual points never placed on real streets as though genuine. No geometry means honest empty map.
- Desktop trial 60/40 map/evidence split; deliberate fit bounds; one selection linking markers/cards, accessible list, no hover-driven camera jumps. Mobile Evidence/Map toggle; usable without GPU or tiles; no external synthetic CI requests.

## Frontend convergence and design system

BuyerWorkflow.tsx uses original synthetic API and different subject/map fields; PrivateBetaRehearsal.tsx uses verified historical-shape routes and redacted responses. Latest private workspace metadata listing passed existing CI but lacks visual approval. Build one shared presentational shell, typed view model and capability flags with separate validated synthetic/private adapters. Reuse navigation, history, comparison, map renderer and dossier where semantics match. Never fall back to synthetic records to hide private-service failure. Preserve exact cents, frozen evidence, CSRF, ownership and seals; metadata summaries are not reverified evidence. No guessing labels, leaking PINs, raw source JSON or expanding projection without review. Keep rehearsal as technical regression route until parity/cutover approval.

Compare two coherent high-fidelity concepts: Editorial Atelier (warm architectural editorial type) and Intelligence Studio (slate, precision, high-contrast sans). Shared semantic tokens for canvas/surface/ink/action/status/border/focus, 4/8/12/16/24/32/48/64 spacing, readable type, consistent icons, 44px primary controls, semantic tables, responsive cards. Prototype full journeys rather than hero screenshots; no final palette/logo selected. Native controls and scoped CSS first. [Radix](https://www.radix-ui.com/primitives/docs/overview/accessibility) or [shadcn](https://ui.shadcn.com/docs) for complex accessible components if justified; [TanStack Table](https://tanstack.com/table/latest) only if complexity merits it. No automatic dependency adoption. Charts limited to interpretable observed values, with explicit denominators and no inference from sparse samples.

## Next bounded work and acceptance

A. Audit richer components against private API, inventory missing fields/ownership and draft typed adapters/capabilities; no contract expansion without review.
B. Produce two original full-flow high-fidelity fictional concepts: sign-in, empty/returning workspace, search, supported/insufficient dossier, saved list, comparison, mobile. Show actual renders and interactions for owner review.
C. Implement reviewed shared design and adapter slice; disposable CI checks evidence exactness, source integrity, ownership, frozen records, notes, restart, comparison and logout.
D. Independently prototype geographic contract/renderer and regional basemap option only under approved rights/cost; test selection, missing geometry, GPU/worker failure, no data leak. Real display remains blocked.
E. Representative desktop/mobile tasks, keyboard/focus, screen-reader, zoom/reflow, loading/error/no evidence, stale responses and drafts. Target [WCAG 2.2 AA](https://www.w3.org/TR/WCAG22/) and [Web Vitals](https://web.dev/articles/vitals) good thresholds (LCP <=2.5s, INP <=200ms, CLS <=0.1 at 75th percentile); no conformance or performance claim without measurements. Owner visual acceptance before flagship release. Retain eight-step directive and phase gates.

R0: no paid services, live extraction, deployment, real geometry exposure, main merge or access-window replay. Research is source-informed, not proof of usability, cost or legal clearance. Approved 87.1% unchanged.
