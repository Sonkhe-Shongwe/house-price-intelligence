# Visual Foundation V1: working map-linked evidence study

**Created:** 23 November 2026. **Status:** Standalone offline fictional design proof for owner review. NOT the live HPI UI, a real geographic map, an accepted visual direction, framework decision or release.

## Open the study

- [Map & Evidence Studio: single-file, offline prototype](../../design-prototypes/map-evidence-studio.html). Download the HTML and open it in a browser. It needs no server, account, API key or network access.
- [GitHub Actions app/browser workflow](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/workflows/audit-tests.yml) attaches a short-lived hpi-visual-study artifact containing the offline HTML and four genuine Chromium screenshots: Editorial desktop, Intelligence desktop, Editorial mobile and Shortlist desktop. Choose a successful exact-HEAD workflow run.
- [Current checkpoint](../CHECKPOINT.md) is authoritative for working application capability. This prototype never modifies Python/SQLite evidence, sale cents, matching rules or P-stage scores.

## What is interactive

1. **Two switchable, visibly distinct directions:** Editorial Atelier uses warm architecture-inspired surfaces, typographic contrast and a map-first composition. Intelligence Studio uses cool slate/cobalt, strong sans type and places the ranked evidence rail before the map at wide widths.
2. **Linked schematic map and ranked sales:** Subject plus three fictional comparable markers; clicking a marker or card selects both, with explanation beside it. Markers are diagrammatically placed, not a source of distance or similarity conclusions.
3. **Designed insufficient-data state:** Toggle to the second imaginary property (105 Fictional Court, zero eligible sales). The earlier markers and cards disappear; the interface does not generate a current valuation.
4. **Workspace, shortlist and comparison:** Navigate between screens; compare two fictional subject properties side by side; toggle to a fictional location diagram and type temporary local-page notes.
5. **Responsive/accessible starting point:** Mobile has an Evidence | Map toggle, readable cards, named controls, visible keyboard focus and reduced-motion treatment. This is not an independent WCAG 2.2 AA certification.
6. **Regression tested:** Dedicated hosted Chromium tests verify marker/card selection, the two layouts, stale evidence clearing, mobile modes, shortlist controls and no external network requests. Original real browser to Python to SQLite acceptance tests remain separate.

## Important limitations

- The illustrated district, roads, parcel pins, names, dates and prices are **fabricated and not to scale**. No real map tiles, geocoding, provider, public geographic coordinates, account system or deployment are involved.
- The existing SQLite fixture has **six fictional parcels all at the identical test location, latitude 42.04 and longitude -87.68**. The approved application has no verified server-owned map FeatureCollection. This visual demo does NOT change those facts, source provenance or real-world spatial relationships.
- The HTML uses fixed design data, NOT the current P3 API money/evidence contract. Its note editor does NOT write to local SQLite, and never claims account-private storage.
- The proof is self-contained vanilla JS purely for frictionless offline evaluation. **This does not choose the production frontend.** React/TypeScript/Vite, Vue, Svelte, MapLibre and Leaflet remain separately evaluable options.
- Rendering a genuine geographic map requires approved source-coordinates/precision, parcel-versus-building semantics, versioned frozen evidence, basemap rights/cost, attribution, CSP/worker compatibility and keyboard/list fallback. See [UI and mapping research](PROFESSIONAL_UI_AND_MAPPING_RESEARCH_2026-11-23.md).

## Owner review questions

- Which is closer to a truly premium professional product: Editorial's map-first composition or Intelligence Studio's more technical evidence-first balance? Would a hybrid or a third art direction outperform both?
- Is the map at the right size; is the selected sale/card relationship clear; does the absence-of-evidence state feel intentional and trustworthy?
- Which navigation hierarchy, type scale, contrast, density, panel spacing, visual motifs and mobile flow need revision?
- Which *real buyer decision* would justify a future full map with licensed geographic geometry rather than the schematic demonstration?

**Next gate:** Record owner design feedback, then propose a bounded prototype-to-application integration plan. A real map renderer and reliable geographic API need independent approval. No source rights, map provider, styling identity, frontend migration, P-stage acceptance or main integration is approved by this document. P3 10% and weighted MVP 22.8% remain unchanged.
