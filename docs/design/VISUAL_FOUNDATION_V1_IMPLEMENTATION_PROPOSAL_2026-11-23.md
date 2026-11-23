# Visual Foundation V1: professional baseline implementation proposal

**Prepared:** 23 November 2026  
**Status:** **PROPOSAL FOR OWNER REVIEW. NOT A SELECTED DESIGN SYSTEM, UI IMPLEMENTATION, NEW PHASE GATE OR RELEASE APPROVAL.**  
**Source baseline:** Owner-authorised [PR #5](https://github.com/Sonkhe-Shongwe/house-price-intelligence/pull/5) and [PR #6](https://github.com/Sonkhe-Shongwe/house-price-intelligence/pull/6) merged into the continuing `development` branch at `44e278f5ff68475616d889d2c7fafd0b5b3c6304`; stable `main` is unchanged. See the current [checkpoint](../CHECKPOINT.md) for exact verified CI.

This proposal translates the existing [UX research and product direction](UX_RESEARCH_AND_PRODUCT_DIRECTION_2026-11-23.md), [product brief](../product/PRODUCT_BRIEF.md), [engineering directive](../engineering/LEAN_ENGINEERING_DIRECTIVE.md), [P3 application contract](../engineering/P3_APPLICATION_CONTRACT.md) and [P6 synthetic shortlist contract](../engineering/P6_SYNTHETIC_SHORTLIST_CONTRACT.md) into a **reviewable professional visual baseline**. No CSS, HTML or JS implementation is authorised by this document. No real-property data or imagery is authorised.

## 1. What a baseline means

The goal is **a complete, aesthetically coherent, functionally honest baseline for meaningful owner review**, not the final choice of colours, logo, typography, navigation or visual personality. The current app already supports invented-address selection, explainable investigation, frozen evidence and a multi-property shortlist. The next work must improve its **presentation and navigability**, rather than add an unrelated ML, map, authentication or listing feature.

The first buyer opens the app and can: (1) understand that it is a fictional-data pilot with no valuation, (2) find or add a property, (3) inspect eligible completed-sale examples and their limitations, (4) collect two or three homes, (5) compare matching evidence and write notes, and (6) reopen that workspace with a deliberately enabled local SQLite file. All six tasks must be clear to a non-technical person before visual styling is accepted.

**Proposed content principle:** "Investigate. Compare. Decide." Show the property, then the quality of evidence, then possible buyer actions. Avoid a statistics dashboard, real-listing appearance or claims that a low asking price is automatically a good buy.

## 2. Proposed experience: one application with four meaningful views

A multi-page framework is **not** justified. Keep the existing HTML/CSS/vanilla JS and same-origin WSGI contract, but reorganise presentation into four recognisable views (via semantic sections and small client-side navigation if accepted), preserving existing API calls.

| View | Primary buyer question | Above-the-fold content | Next action |
| --- | --- | --- | --- |
| **Workspace** (suggested landing) | Which homes am I considering? | One clear headline, "Add property", saved shortlist summaries, recent synthetic investigation status and conspicuous fixture scope | Continue saved shortlist or investigate |
| **Add / Investigate** | What property is this and what evidence exists? | Verified fixture-only coverage, invented address candidate selection/ambiguity, buyer asking price and supported attributes | Investigate |
| **Evidence dossier** | Why should I trust or doubt this comparison? | Property label and parcel-only identity, buyer asking price, evidence status, eligible sales, analysis date and clearly visible material caveat | Inspect ranked sale evidence or add to shortlist |
| **Shortlist / Compare** | What differs among my options? | Two or three property identities, editable buyer notes, evidence status, aligned comparisons and source disclosure | Review a subject, edit notes, remove or reopen |

**Not approved:** mandatory left sidebar, four independent backend URLs, new authentication, map tiles, imagery, address provider or production real market. A modest navigation shell is enough for V1. Add a dedicated methodology/help reveal within the views rather than a fifth fully separate page until user testing justifies it.

## 3. Proposed visual direction to prototype, not select

Research identified **Editorial Property**, **Precision Slate**, and **Midnight Intelligence**. Prototype **Precision Slate's legibility and data hierarchy with subtle Editorial Property warmth** as one *test candidate*. This is a starting experiment, not a claim that the user has chosen the final palette.

| Role | Candidate token | Purpose |
| --- | --- | --- |
| App canvas | `#F5F7FB` | Quiet neutral/slate base |
| Primary text | `#15243A` | Strong headline and evidence contrast |
| Primary action | `#2554A3` | Focused call to action, not an evidence-confidence score |
| Warm secondary surface | `#F7F6F1` | Selectively distinguish buyer notes; no decorative wall of cards |
| Secondary copy | `#54627A` | Readable descriptions and limitations |
| Surface | `#FFFFFF` | Forms, evidence cards and comparison |
| Borders/dividers | `#DFE4ED` (trial) | Consistent section boundaries |
| Support, caution, error | **Undecided** semantic tokens | Determine by testable meaning and contrast, never colour alone |

The first five values are drawn from the researched *candidate* palettes, not newly approved brand tokens; the border is an implementation hypothesis. Recheck **each real component's** contrast and focus treatment rather than relying on rough palette-level ratios.

- **Typography:** system sans-serif initially; normal body around 16px / 1.5; 28–36px responsive page title; 20–28px section title; readable 13–16px auxiliary labels (not today's 10–11px critical evidence).
- **Spacing:** apply the research scale `4 / 8 / 12 / 16 / 24 / 32 / 48 / 64px`. Use 8–12px radii and restrained 1px boundaries. Avoid inconsistent local visual rules.
- **Controls:** 44–48px tall primary inputs/buttons where practical, clear disabled/busy/success/error states, keyboard-visible focus, no hover-only controls.
- **Density:** prioritize comparables and side-by-side evidence; no non-actionable KPIs, stock photography, icon clutter or decorative charts.
- **Motion:** subtle feedback only; obey `prefers-reduced-motion`. Do not add animation packages.

## 4. Specific component inventory

These components make a professional baseline without forcing a framework or massive redesign:

1. **App shell:** wordmark/identity text, application view navigation, prominent "Synthetic demonstration" banner, responsive content width and one primary action at a time.
2. **Property identity header:** buyer label, invented parcel identity, explicit "building not verified" information, user-reported asking price and permitted attributes.
3. **Evidence-status system:** descriptive text labels for `supported_neighbourhood`, `exploratory_spatial`, `insufficient_data`, and `out_of_coverage`; warnings must remain visible and self-explanatory.
4. **Address candidate picker:** show truly distinct candidate IDs when street labels are identical; require explicit choice and clear the old selection on edit.
5. **Enquiry form:** grouped address/identity, buyer area, optional asking price, analysis date; inline validation; preserve inputs after an error.
6. **Comparable-sale row/card:** fake recorded sale price displayed as exact 2-decimal text, recorded sale date, eligibility rationale, material differences and provenance. No "predicted value" component.
7. **Saved property card:** compact label, buyer asking price, evidence quality and visible action to inspect evidence, edit notes or remove from a shortlist.
8. **Side-by-side comparison:** genuine HTML table with property column headers and row headers, aligned values and explicit "not available" rather than fabricated zeros; keyboard usable at narrow widths.
9. **Note editor:** plainly labelled, bounded length, separate explicit save action, visible saved/error state and no accidental claim of private cloud storage.
10. **Loading / empty / error / unsupported states:** accessible feedback that does not leave a different property's stale evidence displayed as current.
11. **Provenance panel:** source snapshots, build, match policy, limitations, data freshness and invented-only scope; material uncertainty stays visible outside any collapsed details.

**Single source of domain truth:** components render the verified response from the existing `backend.synthetic_investigation_store`, `backend.synthetic_shortlists` and HTTP contracts. Do not modify comparable prices, rank, evidence status or source links inside UI state.

## 5. Concrete layout and responsive proposal

**Desktop, 1280px or wider:** quiet navigation area or compact top rail, 1120–1280px maximum readable content, clear breadcrumb/view name, generous but not excessive property identity and evidence hierarchy. Workspace uses shortlist summary/list then one obvious add-property action. The evidence dossier uses a readable facts sidebar only if content warrants it. The comparison's primary structure is a table, not a collage of disconnected KPI cards.

**Tablet, 768–1279px:** compact top navigation, one- or two-column forms, collapsible secondary metadata, cards with consistent headings and a table that scrolls only in its own comparison region.

**Mobile, 320–767px:** one-column form and dossier, no page-wide horizontal scroll; accessible visible comparison scroll affordance with persistent row labels if practical. Provide readable text at zoom/400% and an understandable row-by-row comparison alternative if needed. Never truncate warnings, price provenance or the "not valued" limitation.

**Fixture scope:** the current "Evanston / Cook County / Class 203" area is a labelled synthetic research pilot, **not an approved live market**. A PIN is an internal synthetic test identifier, not an accepted consumer address experience.

## 6. Implement in five bounded reviewable passes, after owner approval

| Pass | Exact change | Completion check |
| --- | --- | --- |
| **V1.1 Audit and design tokens** | Inventory current `frontend/index.html`, `frontend/styles.css` and `frontend/app.js`; consolidate colours, spacing, type, focus and semantic states behind a small CSS token vocabulary. Prepare static desktop/mobile proposals and an owner review checkpoint. | Current API/browser scenarios still pass; visual tokens demonstrably consistent; no real-data or contract changes |
| **V1.2 Shell and workspace** | Add semantic navigation and clear workspace-first entry/reopen actions using current shortlist endpoints. Keep empty state excellent and avoid premature sidebar lock-in. | A first-time tester can create an investigation and a returning tester can reopen a shortlist without developer explanation |
| **V1.3 Investigation and evidence detail** | Align property identity, input provenance, warnings and ranked comparables; improve validation, loading and abstention states. Do not change matcher logic. | Real browser tests cover supported, ambiguous, insufficient, conflicting and stale/failed request cases |
| **V1.4 Shortlist and comparison refinement** | Unify property cards, note editor and data table; align units/price and evidence warnings, including mobile table behaviour. | Two saved homes, one unsupported, survive restart; side-by-side values and notes stay identical; keyboard navigation succeeds |
| **V1.5 Quality review and visual acceptance** | Test at representative widths, keyboard-only, focus, 320px/400% zoom, reduced motion, contrast and major screen-reader labels; inspect console/errors and gather owner aesthetic feedback through screenshots or interactive local app. | CI green at exact commit, no regression in original scenario count, recorded remaining limitations and **separate owner design decisions** |

Each pass is a **proposal**, not a commitment to build or merge. Prefer a small batch of genuine cross-layer fixes and a single reviewed visual-baseline integration checkpoint, rather than redesigning every screen without feedback.

## 7. Non-negotiable review checks

**Functional:** supported 3-sale investigation, ambiguous fictional address selection, no-match/unsupported property, saved notes and two-property comparison, correct source/asking distinction, restart reload using explicit `--fixture-db`, exact frozen comparable cents, no valuation.

**Accessibility:** semantic navigation and headings, accessible form labels, error/status announcements, clearly visible keyboard focus, no keyboard trap, zoom/mobile reflow, meaningful table headers, sufficient actual contrast and reduced motion.

**Trust:** not a live listings site, map, bank appraisal, verified building address, live property model, or provider-backed current sale feed. Missing evidence is never a zero-valued property or an implicit buying recommendation.

**Engineering:** current standard-library Python + vanilla frontend stack; no new runtime dependencies, no external networks, no public service binding, no real data, no account system and no API/DB-contract changes solely to obtain a visual effect. Commit/review and inspect exact Python/JS/Chromium/doc CI results after approved UI edits.

**Owner experience:** evaluate against a first-time buyer and a returning buyer. Ask whether each can find the primary action and discern evidence quality without instructions. Collect feedback by screen, not vague "make it premium" changes.

## 8. Owner decisions to make after viewing the first baseline

1. Product personality: **calm professional analyst** vs **warm consumer homebuyer** vs balanced.
2. The first screen: saved **Workspace/Shortlist** vs a guided **Add Property** start.
3. Layout/navigation: compact top bar vs contextual side navigation; mobile analogue.
4. Visual identity: choose or reject the proposed slate/warm prototype; approve actual typeface, icon style and accent later.
5. Information density: what must be immediately visible on property dossiers vs disclosed on demand.
6. Whether a later map or image is even relevant after source accuracy and licensing are proven. Neither belongs to V1 by default.

**The owner reviews design, but this document does not approve a final aesthetic.** P3 remains 10% and overall weighted MVP 22.8%; P4/P5/P6 stage exit gates remain open. A visual baseline is meaningful progress only when implemented, tested, independently reviewed and then accepted within the existing P0–P8 gates.
