# House Price Intelligence: Professional UX/UI and interactive mapping research

**Date:** 23 November 2026
**Classification:** Research and proposed technical decisions, NOT owner approval to implement a framework migration, connect paid/external mapping services, change source rights, merge to main, deploy or award phase progress.

**Repository basis:** product brief, P0-P8 roadmap, existing UX study and Visual Foundation V1 proposal, P3/P6 contracts and decision register, backend/schema_draft.sql, backend/synthetic_demo.py, backend/synthetic_investigation_store.py, backend/investigation_contract.py, backend/synthetic_http.py, frontend/index.html, frontend/styles.css, frontend/app.js, and CI configuration.

## 1. Research outcome

The visual target is a **premium, original, map-centred property intelligence workspace**, not a listing marketplace or a generic KPI dashboard. Make the buyer's journey feel expertly designed: Investigate -> understand geographic evidence -> compare two or three homes -> decide with readable limitations.

The recommendation is to:
- Design at least **two genuinely different high-fidelity desktop/mobile concepts** before selecting colour, navigation and typography. Original editorial architecture and precise intelligence-studio aesthetics are promising candidates, not chosen brands.
- Treat frontend technology as open. Compare **React + TypeScript + Vite + design tokens**, possibly Tailwind CSS v4, selected shadcn/Base UI primitives and Motion, against a simpler vanilla TS/Vite or Vue/Svelte implementation. No framework creates visual excellence automatically.
- Test **MapLibre GL JS** as the first custom vector-map renderer and **Leaflet** as a simpler alternative. Keep the map **renderer**, **basemap/tile provider**, **geocoder**, **approved property-coordinate source** and **distance/evidence rules** distinct.
- Do **not** render today's synthetic parcels on a geographic map as separate homes: the current six fake parcels have exactly the same fixture coordinates, and there is no frozen map feature response contract.
- First prototype linked map/list interactions with an honestly labelled **schematic fictional district** (not-to-scale). Only proceed to a geographic prototype after a controlled new fixture and a source-verified map response model.
- Preserve the Python/SQLite evidence source of truth, exact recorded sale cents, source role, snapshot, parcel-only identity and abstention rules. The map displays findings; it does not recompute or override matching.

## 2. What makes professional products feel professional

**Information architecture:** one conspicuous buyer action at a time. A user always sees their chosen property, its user-reported asking price, whether evidence supports any comparison, and where to go next. No decorative "market intelligence" widgets without meaningful source data.

**Typography and design language:** one deliberate type hierarchy, legible secondary text (around 14–16px) and body (around 16px), consistent spacing scale (4, 8, 12, 16, 24, 32, 48, 64), polished empty and error states, constrained content width and harmonious surface treatments. Visual design need not be restrained to monochrome minimalist software; premium editorial, carefully styled map labels and sophisticated imagery-free graphics are all options.

**Motion:** use subtle purpose-driven transitions to show focus, selection and change. Proposed 120–220ms for common micro-interactions is a hypothesis, not a measured rule. Avoid permanent animation, pointless 3D, scroll-jacking, invasive parallax and animated dashboards. Follow reduced-motion preferences.

**State integrity:** don't leave the old property's sale pins or prices visible after a new lookup fails. Don't present a loading map as "no evidence". Distinguish investigation unavailable, map tiles unavailable, missing coordinates, insufficient sale evidence and out of scope.

**Product originality:** the buyer should interact with evidence, not a collection of listings. Keep first-market limitations, fictional-data status and lack of validated valuation evident and prominent.

Industry patterns examined (behavioural reference only, not approval to copy):
- LandInsight / LandTech: map joined with relevant comparable-sales sidebar: https://land.tech/products/landinsight
- Cloud CMA Live: selected comparable markers, toggled and ranked evidence: https://cloudagentsuite.com/cloud-cma-live
- Primer: controlled map layers and compact property detail research: https://www.primer.city/
- NN/g on complex apps and progressive disclosure: https://www.nngroup.com/articles/complex-application-design/ and https://www.nngroup.com/articles/progressive-disclosure/

## 3. Proposed buyer app hierarchy

**Workspace:** continue a fictional shortlist, create a new investigation, see latest saved investigations and evidence statuses; clear first-time empty state. Do NOT eagerly load a map on this landing view.

**Investigate / Evidence dossier:** subject card and input provenance, explicit identity accuracy, evidence status, eligible earlier-sale records, selected map + synchronised evidence list, matching explanation, limitations, source snapshots and analysis date. This is where the interactive map belongs most prominently.

**Shortlist / Compare:** two or three properties with editable notes, aligned evidence facts and separate map toggle to examine subjects' geographic relationships when locations are valid. A map is supplementary to the comparison table, not a substitute for the figures.

**Methodology:** compact, readable explanation of supported geography and class, source build, why each record qualifies, how distance is measured, privacy and outstanding historical-as-of caveats. Crucial warning copy belongs on the main view too, not only behind a disclosure.

Four views can be implemented via one application shell; four backend page routes or an additional server runtime are not automatically necessary.

## 4. Investigation map behaviour: research proposal

**Desktop:** prototype a responsive approximately 55–65% interactive map and 35–45% evidence rail, with the subject's heading and status above. Test other proportions with real task scenarios, not a fixed 60/40 contract. Explicit "fit all evidence" control, attribution, map legend, zoom controls and accessible table/list.

**Pins and legend:** the subject marker is distinctive. Eligible comparables are labelled 1, 2, 3 to match ranked cards. A selected sale highlights its marker and card. Exploratory fallback is styled as exploratory, **not a validated value**. Missing geometry yields a clear "location not verified" card outside the map. An excluded property must not appear as if it were eligible.

**Linked interaction:** the app holds one selectedComparableId. Clicking map feature, card or keyboard-accessible list item updates this ID; keep hover, keyboard focus and persistent selection distinct. Use MapLibre feature IDs/feature-state for visual treatment when using layers, or 1–4 simple labelled markers. Only move camera deliberately, not on every hover, note keystroke or re-render. Keep popups small and mirror their critical facts in accessible DOM.

**Mobile:** a usable Evidence | Map switch and a readable panel. No full-page horizontal overflow or tiny fixed sidebars; avoid map gesture capture that blocks page scrolling. The evidence list remains fully usable with GPU disabled or tiles offline.

**Limitations:** do not show false travel time, safety ranking, school quality, price prediction, verified rooftop location or other unsupported "nearby intelligence". A stated neighbourhood code is not a proof of coordinate precision. Empty states are intentionally designed.

## 5. Real map rendering and supplier comparison

| Candidate | Benefits for HPI | Trade-off / risk | Proposed status |
| --- | --- | --- | --- |
| MapLibre GL JS | Fully customisable vector map, WebGL rendering, stable GeoJSON feature layers, camera fit, custom selectable map style | MapLibre v6 requires WebGL2; worker, Vite bundle, CSP, tile/style/fonts, mobile rendering and fallback need tests | First interactive geographic map spike |
| Leaflet | Easy map/marker/GeoJSON implementation, lower conceptual complexity, SVG/Canvas/raster support | Less flexible full vector-basemap styling; fine for 4 markers, but less bespoke map personality by default | Simpler fallback |
| Mapbox GL JS | Polished proprietary ecosystem, hosted styles and services | Map-load billing, commercial licensing and coupling | Optional if compelling measured value |
| Google Maps JS | Familiar commercial basemaps, maps and Places integrations | Commercial SKUs, storage/reuse restrictions, not a source of qualified historic sales | Not default |
| OpenLayers | Strong GIS and projection ecosystem | Complexity not warranted solely by 1 subject and 3 comparable markers | Later only if GIS requires |
| deck.gl / Cesium / three.js | Large-scale geospatial data or immersive 3D | Unjustified complexity/performance for first property-evidence map | Avoid now |

**The renderer is not the tile provider.** MapLibre does not license property coordinates, road tiles or geocoding. Selecting it does not permit exposing source property data.

| Basemap model | Advantage | Blocking question |
| --- | --- | --- |
| MapTiler Cloud vector tiles + styles | Attractive customizable styles, easy MapLibre integration | Free tier limited to non-commercial/R&D; terms require attribution and constrain server proxy/caching. Paid plan and actual tile request quotas need review |
| Protomaps PMTiles, self-hosted | Control, privacy, bounded region, CDN/static-storage delivery, no paid third-party renderer API | Licensed basemap and attribution, CORS/HTTP Range, file distribution, tile updates, storage and egress responsibilities |
| Mapbox/Google-hosted tiles | Hosted, comprehensive | Vendor and pricing/usage restrictions |
| OpenStreetMap Foundation public tiles | Reference service / compliant limited use | Donation-funded, no SLA, prefetch/bulk disallowed, valid Referer/cache/identification and attribution mandated; not assumed production CDN |
| Same-origin illustrated schematic | Reliable offline UX proof, no real-location claims or third-party dependencies | Not a real street basemap and must be labelled as schematic |

**Critical HPI security interaction:** current synthetic_http.py has Referrer-Policy: no-referrer, connect-src 'self', img-src 'self', and no explicit worker-src. That conflicts with direct OSM public tile policy requiring a valid browser Referer, and with hosted vector tiles and MapLibre workers as-is. Do not remove security headers wholesale. A self-hosted map worker and tightly reviewed map resource origins are safer design options.

**Provider cost model:** Compare (a) map initialisations per month, (b) tile/font/style requests for zoom and panning, (c) geocoder searches, (d) storage/egress for PMTiles, (e) attribution and licence, (f) caching terms, (g) public vs non-commercial use and (h) overage controls. Mapbox often charges based on map loads, MapTiler with independent third-party SDKs can count tile API requests. Never treat these as the same "free" unit. Quote current provider terms when actually selecting service.

Official sources: https://maplibre.org/maplibre-gl-js/docs/ ; https://maplibre.org/maplibre-gl-js/docs/guides/v5-to-v6-migration-guide/ ; https://leafletjs.com/ ; https://docs.protomaps.com/pmtiles/maplibre ; https://docs.protomaps.com/guide/security-privacy ; https://www.maptiler.com/cloud/pricing/ ; https://www.maptiler.com/terms/cloud/ ; https://www.mapbox.com/pricing ; https://developers.google.com/maps/billing-and-pricing/pricing ; https://operations.osmfoundation.org/policies/tiles/

## 6. Exact geo-data blockers in the present repository

The six invented parcel rows in backend/synthetic_demo.py all insert parcel_geographies at **latitude 42.04, longitude -87.68**. Subject and candidate location values are consulted during matching, but the current investigation response does not expose an explicit, trusted map FeatureCollection. The selected address is parcel-only and building_identity_verified=false. Stored evidence must reopen with identical sale cents, snapshot/build association, selected comparable identity and source role.

**Do not**:
- Display six shifted or randomly jittered pins on a realistic map and call them evidence coordinates.
- Geocode fictional street names with a real provider and imply a found property.
- Treat parcels, buildings and sales transaction locations as interchangeable.
- Rewrite or reseed frozen v1–v3 fixture databases to make a screenshot look better.
- Send a user-provided arbitrary browser lat/lon value into the trusted matcher or into a frozen evidence view.
- Display a valid-lat/lon but wrong-area coordinate without checking claimed source/coverage.
- Silently treat absent geometry as [0, 0] or a zero-distance comparable.

**Safest staged map approach:**
- **G0:** Map interaction designed and tested using an obviously fictional, *not-to-scale schematic district*. These are display positions for a visual proof, not verified real geography. No real basemap or third-party tile services required.
- **G1:** If a true geographic demo is approved, create a separate versioned **distinct synthetic parcel geography fixture** with accurate internal consistency and documented source kind/geometry type. Keep historic investigation records and checksums intact, and test migration/reopen. Do not mutate original v1 schema/fixture history.
- **G2:** Define a **new read-only, versioned map evidence endpoint** (example path GET /v1/investigations/{uuid}/map). It must reverify frozen evidence and selected comparable IDs, geometry snapshot, build role, coordinate precision, parcel scope and permissions before emitting the map. No data in the browser can widen eligible comparables.
- **G3:** Real-market case later requires first-market data and coordinate-source rights, building-vs-parcel accuracy, publication times, source licensing and eventual owner acceptance.

**Illustrative map DTO (NOT implemented):**

    {
      "contract_version": "map-proposal-v0",
      "source_kind": "synthetic_fixture",
      "investigation_id": "<existing-saved-uuid>",
      "map_available": false,
      "geometry_kind": "parcel_centroid_not_rooftop",
      "coordinate_accuracy": "demo_unverified",
      "source_snapshot_id": null,
      "features": [],
      "limitations": ["No verified geographically distinct map points for current fixture"]
    }

Later, use validated RFC 7946 GeoJSON coordinates ordered **[longitude, latitude]** (not latitude/longitude). Validate finite values, allowed bounds, stable feature IDs, source version, positional precision, coordinate role, evidence eligibility and missing geometry. Straight-line distance between parcel centroids is not travel time or a verified rooftop measurement. The map must reflect the matcher, not alter its rules. See https://www.rfc-editor.org/info/rfc7946/ and https://postgis.net/docs/ST_DWithin.html for future spatial-data semantics.

## 7. Professional frontend technology to combine or avoid

**Test first:** React + TypeScript + Vite; a curated design-token system (CSS custom properties or Tailwind v4); selected shadcn/ui components using **Base UI** or Radix, with one consistent interaction foundation; optional Motion for real UI transitions; MapLibre on a separately loaded map view.

**Equally valid competitors:** Vue + TypeScript + Vite, Svelte + TypeScript, or modular vanilla TS + Vite. A modern component architecture is helpful if four linked views and complex request states demand it. **No framework selection is approved yet.**

**Important 2026 update:** shadcn/ui began using **Base UI by default for new projects in July 2026**, while Radix remains supported. Do not mix multiple headless libraries haphazardly or assume a default shadcn template is an original visual identity.

Avoid introducing Next.js or a full React server framework solely for this client-side authenticated-never, localhost test app. Avoid heavy 3D, large icon packs, three animation systems or fake property imagery. One good design system, clear state management, accessible primitives and a tested bundling pipeline will do more than novelty.

**Serving challenge:** the current Python WSGI app serves only three hard-coded static frontend assets. Vite will build hashed JS/CSS/SVG/font files; those will need a narrowly scoped build-manifest asset allowlist, accurate MIME types and path traversal resistance. Same-origin API should remain authoritative. Worker hosting/CSP needs explicit testing before adding MapLibre; local offline CI must not rely on external CDN tiles, styles, fonts or a real geocoder.

**React/map integration:** create map instance once in a dedicated lifecycle; remove it on unmount, including StrictMode test scenarios; keep selectedComparableId outside the map object; update layer/feature state without unnecessary redraws; clear markers on failed/reopened investigations; bound camera with fitBounds and sidebar padding; map resize on actual panel width changes.

References: https://vite.dev/guide/ ; https://react.dev/learn/build-a-react-app-from-scratch ; https://tailwindcss.com/docs/theme ; https://ui.shadcn.com/docs/changelog/2026-07-base-ui-default ; https://motion.dev/docs/react-use-reduced-motion ; https://maplibre.org/maplibre-gl-js/docs/

## 8. UI completeness: state matrix

The application needs a tested presentation for each of these: first run with zero saved enquiries; supported 3-sales evidence; insufficient data/zero sale; exploratory spatial warning; out-of-coverage; two fictional candidates with same street label; invalid asking price; new enquiry loading; failure clearing stale old evidence; loss of map tiles while evidence API works; no GPU; missing geo; invalid/tampered source; shortlist of one, two or three; fourth/duplicate attempted; notes edited, save failed and restored; persisted database restart; deleted shortlist member; and multiple screen widths/zoom.

Keep buyer-reported asking price visually separate from historic completed sale; never show calculated current value. Do not present outdated or missing coordinates as precise. Use DOM-safe text rendering, explicit save status and an honest note that local demo notes are not secure account records.

**Accessibility:** meaningful semantic headings, tables with row/column headers, form labels, focus-visible, status announcements, keyboard and touch selection parity, and map-to-list equivalence. WCAG 2.2 AA targets: typical normal text contrast at least 4.5:1, relevant non-text indicators at least 3:1, target-size minimum generally 24x24 CSS pixels subject to exceptions; design primary controls comfortably larger where possible. Test 320, 375, 768, 1024 and 1440px widths, 400% zoom, reduced motion, low-bandwidth and WebGL loss.

**Performance:** benchmark LCP <=2.5s, INP <=200ms, CLS <=0.1 at 75th percentile (published Web Vitals "good" thresholds, **not current HPI results**). Defer map bundles/tiles until map view, reserve map panel space, measure rendering and device GPU, avoid thousands of DOM markers and frequent GeoJSON updates. For 1 subject and 3 comparables, clustering or GPU-heavy overlays are not required. Inspect memory after repeated entering/exiting map view.

Sources: https://www.w3.org/TR/WCAG22/ ; https://web.dev/articles/vitals ; https://maplibre.org/maplibre-gl-js/docs/guides/large-data/

## 9. Rights, costs, privacy and security grey areas

- **Source rights:** public record search accessibility is not publication licence for transaction or parcel fields. Basemap permission does not authorise sale data. Track approved geography, field, retention, attribution and historical validity.
- **Provider data movement:** map tile servers may receive browser IP/network and map-request metadata. Don't send buyer notes, IDs or searches in provider URL query parameters. Evaluate third-party privacy and data-processing implications.
- **OpenStreetMap tile usage:** public tile.openstreetmap.org requires visible OSM attribution, appropriate caching, identifying client requests, valid browser Referer and no bulk/prefetch. Current HPI Referrer-Policy conflicts. Provider-agnostic future map does not mean abusing community tiles.
- **Nominatim public geocoding:** absolute 1 request per second maximum for the whole application, and client-side autocomplete is prohibited. Existing fictional candidate index is **not** a real geocoder. Review a licensed commercial geocoder or self-hosted permitted alternative if actual address search later becomes essential.
- **MapTiler:** free plan is non-commercial/R&D, requires attribution; proxying and server-side caching may be restricted. A public recruiting demo's usage classification needs explicit review. See current provider contract.
- **Google/Mapbox:** proprietary price units, data retention and storage rules; do not scrape tile caches, reverse-engineer addresses or republish licensed content.
- **OSM ODbL:** OSM data itself is open under ODbL with attribution/other conditions, but OSM Foundation tile servers are separately governed. Check derivative database/output obligations if combining data.
- **Frontend supply chain:** lock versions, licence check, dependency audit and no unpinned runtime CDN scripts. Maintain offline Actions tests; do not weaken existing CSP broadly for display.
- **Local notes/privacy:** current WSGI local server lacks accounts, auth and encryption; not suitable for real buyer information. Persistent fixture-only labels/notes must remain fictional.
- **Future report exports:** map style/tile screenshot terms and attribution, WebGL canvas and print rendering limitations must be reviewed before screenshot/PDF exports.
- **Actual release:** hosted security, access boundaries, tile costs, geocoder rates, rights, cross-device behaviour and operational limits are separate P7/P8 gates.

Sources: https://operations.osmfoundation.org/policies/tiles/ ; https://operations.osmfoundation.org/policies/nominatim/ ; https://www.maptiler.com/terms/cloud/ ; https://docs.protomaps.com/guide/security-privacy ; https://osmfoundation.org/wiki/Licence/Attribution_Guidelines ; https://developers.google.com/maps/documentation/geolocation/policies

## 10. Ranked unresolved decisions and acceptance test plan

| Urgency | Grey area | Evidence needed to close |
| --- | --- | --- |
| BLOCKER | All fixture map coords identical, no trusted map response | Decide schematic mock vs versioned geo fixture, ensure each map point is backed by trustworthy evidence or explicitly schematic |
| BLOCKER | Map renderer vs basemap supplier conflated | Compare MapLibre/Leaflet in a working POC; separately choose lawful tiles and license/cost |
| BLOCKER | Current CSP/strict static allowlist incompatible with new map/build assets | Design explicit safe manifest/worker/asset loading, preserve CSP, pass browser tests offline |
| BLOCKER | No production property coordinate rights/precision | Remain invented-only; later decide real parcel centroid/building roles, approved source, source version and geometry bounds |
| HIGH | Professional aesthetic and product identity still unapproved | Compare original editorial and intelligence design at desktop/mobile, supported/insufficient states, with owner |
| HIGH | Framework migration risk and benefit unknown | Time-box React/TS/Vite vs simpler option with same real buyer journey and regression checks |
| HIGH | Map accessibility/performance | Map/list keyboard parity, reduced motion, no GPU and offline fallback, tested widths and performance profile |
| HIGH | Source publication-time validity and rights | Resolve P0/P2/P3 data gate separately, no false historic mapping or public property claims |
| HIGH | Unknown privacy/data movement and billable requests | Cost worksheet, tile/geocoder terms, request auditing and usage caps before external service |
| MEDIUM | Desktop layout split / mobile map-switch | Compare alternatives using actual two-property tasks and capture owner preference |
| MEDIUM | Accurate distances vs geographic impression | Clear centroid/approximate definitions and no implicit travel-time promise |
| DEFER | 3D terrain, satellite, street view, amenities, crime, market forecasts | Add only with reliable licensed inputs, user need and independent acceptance |

**Reviewable sequence:**
1. Select two authentic, fully considered, high-fidelity visual directions and map/list layouts, including mobile.
2. Build an **offline, schematic fictional map/list interaction proof** with no real-coordinate claim. Compare a modern component approach and a lightweight one where meaningful.
3. Only after review, approve a map renderer/tiles strategy and draft the versioned frozen map response contract. Any fixture schema change requires a safe migration, source-integrity tests and explicit permission.
4. Implement chosen frontend in bounded connected stages on permanent development; maintain existing Python, API, SQLite and real Chromium acceptance, with P6 behaviour untouched.
5. Perform owner review for identity, aesthetic and interactions, keyboard/zoom/mobile/no-GPU, source claims and performance. Do not adjust P3/P4/P5/P6 exit or 22.8% without a formal owner-approved phase audit.

## 11. Source index and boundaries

Official documentation reviewed on 23 Nov 2026:
- Rendering: https://maplibre.org/maplibre-gl-js/docs/ , https://maplibre.org/maplibre-gl-js/docs/guides/v5-to-v6-migration-guide/ , https://leafletjs.com/
- Tile supply and licensing: https://docs.protomaps.com/ , https://docs.protomaps.com/pmtiles/maplibre , https://www.maptiler.com/cloud/pricing/ , https://www.maptiler.com/terms/cloud/ , https://www.mapbox.com/pricing , https://developers.google.com/maps/billing-and-pricing/pricing
- Public geo rules: https://operations.osmfoundation.org/policies/tiles/ , https://operations.osmfoundation.org/policies/nominatim/ , https://osmfoundation.org/wiki/Licence/Attribution_Guidelines
- GeoJSON: https://www.rfc-editor.org/info/rfc7946/
- Frontend: https://react.dev/learn/build-a-react-app-from-scratch , https://vite.dev/guide/ , https://tailwindcss.com/docs/theme , https://ui.shadcn.com/docs/changelog/2026-07-base-ui-default , https://motion.dev/docs/react-use-reduced-motion
- Quality: https://www.w3.org/TR/WCAG22/ , https://web.dev/articles/vitals
- Real product examples (reference patterns, **not** approved source data or reproductions): https://land.tech/products/landinsight , https://cloudagentsuite.com/cloud-cma-live , https://www.primer.city/

**No visual direction, frontend framework, map provider or map implementation is hereby approved.** This is research designed to close grey areas before further implementation. Main is unchanged, PR #4 remains a separate draft integration gate, and the P0–P8 estimate remains 22.8%.
