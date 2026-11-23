# House Price Intelligence: UX research, visual direction and screen architecture

**Documented:** 23 November 2026  
**Status:** **Research and design exploration, NOT an approved design system or authorisation to implement.**  
**Owner instruction:** Document the explored aesthetic, frontend principles, feature hierarchy, references and open decisions before choosing final product aesthetics. No current frontend styling, layout, source code or phase completion is changed by this record.  
**Authority:** This exploratory design record is subordinate to the [product brief](../product/PRODUCT_BRIEF.md), [pinnacle vision](../product/PINNACLE_VISION.md), [engineering contract](../engineering/ENGINEERING_CONTRACT.md), [P0-P8 roadmap](../P_PHASE_ROADMAP.md) and explicit owner decisions in [DECISIONS.md](../DECISIONS.md).

## 1. Why the design work matters

The visual system must follow the buyer problem. House Price Intelligence (HPI) is intended to be an **evidence-based property-buying decision workspace**. Valuation or machine-learning prediction is only a possible later capability, not the primary value proposition or a committed MVP feature.

Proposed product expression: **Investigate. Compare. Decide.**

- **Investigate:** Understand the property, source coverage, ranked eligible prior sales and the limits of each claim.
- **Compare:** Put two or three shortlisted homes together using identical, meaningful attributes.
- **Decide:** Keep personal notes and reproducible investigations so a buyer can revisit assumptions, not merely view a transient price.
- **Never imply** an asking price is a verified listing, that prior sales guarantee a fair price, or that exploratory spatial evidence is a validated valuation.

The first flagship remains **one supported buyer, market and property class**, manual property enquiry, explainable historical comparables, honest insufficient-data results, and a saved, reopenable two-property shortlist with side-by-side comparison. More markets, accounts, licensed listing imagery, finance scenarios, alerts, interactive maps and validated estimates are **potential pinnacle extensions**, not automatic v1 work.

The current Cook County Evanston / assessor Class 203 work is a **research pilot**, not a permanent market or authorised public data display. The current UI is a **synthetic-only technical prototype**, not an approved brand or final UX.

## 2. Agreed product intent versus design proposals

| Topic | Existing product direction | Design research proposal, not approved |
| --- | --- | --- |
| Target user | Individual buyer examining two or three properties | First-time or occasional buyer, with clear on-demand methodological depth |
| Primary product action | Add enquiry, inspect sales, save and compare | Make the *saved shortlist/workspace* the main organising object, with property dossiers as detail views |
| First input | User-reported price and supported characteristics | Streamlined form; future address/identity entry only when coverage and validation permit |
| Primary analytical object | Ranked previous completed sales and explanations | Scannable comparable list or table; inspect each sale's attributes, date, selection and caveats |
| Decision outcome | Transparent comparisons and abstention | Aligned side-by-side attributes, personal notes, no unverified buy/sell verdict |
| Interface personality | Not approved | Calm, premium, approachable yet precise, with restrained decoration |
| Production stack | Decision pending | Retain lean HTML/CSS/JS during exploration; do not introduce a framework to achieve an aesthetic alone |
| Accessibility/reliability | Binding engineering obligations | Accessibility, error and responsive states are part of the design, not polish added at the end |

**Owner boundary:** A working P3 form was necessary for browser acceptance, but existing teal/navy branding, hero text, cards and decorative details were *not* individually approved. Preserve the working baseline until an agreed UX/UI design can replace its presentation incrementally.

## 3. Source-informed UX principles

The following principles are **research-informed**, while the particular HPI applications are our own design inferences.

| Research theme | Relevant source | What it means in HPI |
| --- | --- | --- |
| Visual hierarchy and attention | [Nielsen Norman Group: Visual Hierarchy](https://www.nngroup.com/articles/visual-hierarchy-ux-definition/) | The buyer should first identify the property, asking-price provenance, evidence status and next action, before secondary metrics |
| Aesthetic minimalism | [NN/g: Aesthetic and Minimalist Design](https://www.nngroup.com/articles/aesthetic-minimalist-design/) | Remove decorative KPIs, duplicate cards and charts that do not support a decision |
| Recognition over recall | [NN/g: Ten Usability Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/) | Preserve selections and notes; make compare attributes simultaneously visible, rather than forcing users to remember separate property pages |
| Progressive disclosure | [NN/g: Progressive Disclosure](https://www.nngroup.com/articles/progressive-disclosure/) | Put essential comparable facts first; let users expand inclusion/exclusion rules and source-lineage details without hiding material warnings |
| Grouped forms | [NN/g: Reducing Cognitive Load in Forms](https://www.nngroup.com/articles/4-principles-reduce-cognitive-load/) | Group location/identity, property attributes and user asking price; validate beside fields and preserve inputs |
| Structured comparison | [Baymard: Comparison Tool Examples](https://baymard.com/ecommerce-design-examples/39-comparison-tool) and [Product Table Examples](https://baymard.com/ecommerce-design-examples/product-table) | Align comparable attributes in rows and properties in columns; also make it easy to select what to compare |
| Property dossier/reference | [PriceHubble: Comparables Section](https://support.pricehubble.com/hc/en-gb/articles/4402384667281-How-to-use-the-Comparables-section) and [Dossier Terminology](https://support.pricehubble.com/hc/en-gb/articles/27080249574289-What-is-a-dossier-and-what-are-other-terms-I-should-know) | Property-specific context, historical transactions and selectable comparable evidence; no copying proprietary model claims or branded visuals |
| Property-oriented consumer reference | [Redfin: Owner Estimate](https://support.redfin.com/hc/en-us/articles/360018505351-Owner-Estimate) | Keep property identity and evidence anchored together; unlike Redfin, HPI currently has no accepted automated estimate or licensed live listings |
| Consistent product chrome | [Linear: A Calmer Interface for a Product in Motion](https://linear.app/now/behind-the-latest-design-refresh), 12 March 2026 | Consistent navigation, header and action placement; calm data density; do not reproduce Linear's design or product |
| Accessibility | [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/), [text contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum), [non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast), [reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow), [target size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum) | Design readable text, visible focus, keyboard navigation, accessible statuses and responsive content; test instead of assuming compliance |
| Performance | [web.dev: Web Vitals](https://web.dev/articles/vitals) | Measure LCP, INP and CLS as the application grows; reserve space for asynchronous content and avoid needless heavy UI dependencies |

Sources were checked on 23 November 2026. These are design heuristics and references, not proof that any particular prototype is more usable. A future real-user/task evaluation remains necessary. No external screenshot, brand asset or proprietary product design was copied into the repository.

## 4. Inspiration distilled, not copied

**PriceHubble:** Structured property dossiers, explicit comparable context, source detail and market-related filters. **Borrow:** coherent, inspectable evidence. **Avoid:** pretending the MVP offers AVM confidence or professional-grade valuations.

**Redfin:** A home-oriented presentation in which the user is never far from property context. **Borrow:** understandable property identity and location context. **Avoid:** suggesting HPI has live listing feeds, verified photos or a current Redfin-equivalent estimate.

**Linear:** Predictable spacing and navigation, quiet surfaces and consistent actions. **Borrow:** product-level consistency and reduced UI friction. **Avoid:** a developer-tool aesthetic that alienates ordinary homebuyers.

**Baymard and NN/g:** Make comparisons readable, disclose details progressively, respect task focus. **Borrow:** interaction patterns that reduce memory load. **Avoid:** treating cards alone as sufficient for multi-attribute decisions.

**Original HPI design intent:** It must be **property-oriented + evidence-oriented + decision-oriented**. Do not design it as a generic BI dashboard filled with gauges or as an imagery-first home-listing marketplace.

## 5. Proposed information architecture

Proposed screen model, subject to owner approval and actual task testing:

```text
My Property Workspace (recommended organising hub)
  |
  +-- Start / add property
  |     +-- Supported market and data coverage explanation
  |     +-- Buyer-entered identity / asking price / supported attributes
  |     +-- Validation, outside-coverage and unresolved-identity states
  |
  +-- Individual property investigation (dossier)
  |     +-- Subject summary and provenance
  |     +-- Evidence support status and understandable caveats
  |     +-- Ranked historical comparable sales
  |     +-- Comparable detail: date, source, attributes, why selected
  |     +-- Exclusions, source build and methodological limitations
  |     +-- Save to shortlist / add notes
  |
  +-- My shortlist
  |     +-- 2 or 3 saved homes, including unsupported ones
  |     +-- Brief evidence state for every home
  |     +-- Return to an identical frozen investigation
  |
  +-- Side-by-side comparison
  |     +-- Asking price (user-entered), property dimensions
  |     +-- Eligible comparable count and evidence tier
  |     +-- Important differences and data gaps
  |     +-- Notes, evidence as-of/build identifiers
  |
  +-- Evidence guide / methodology
        +-- Supported market/class, source versions and dates
        +-- Comparable eligibility and excluded records
        +-- Historic publication-time and fallback caveats
```

This is **information architecture**, not approval for five separate application routes, a permanent sidebar, accounts or a JS framework. A modest single application can support these experiences in fewer pages.

### 5.1 Workspace/home

First view should answer: *What properties am I investigating? What needs attention? What can I do next?*

Recommended visible elements: meaningful heading, simple add-property action, saved shortlist summaries, evidence status, most recent investigation and an unobtrusive coverage notice. A KPI row is **optional** and only justified if it aids task completion. The experimental concept had "Properties under review", "Eligible recorded sales", "Needs more evidence"; these are UI illustrative, not approved product KPIs.

### 5.2 Add property

Order: market coverage -> property identity/location -> physical attributes -> optional asking price and label -> submit. Exact consumer identification (address, PIN, supported map entry, manual details) **still requires research and approval**. The current 14-digit PIN is an internal technical pilot key, not an accepted consumer-facing address workflow.

Use concise labels, units, field hints, examples, cross-field server checks and inline errors. Buyer-reported asking price must not be confused with an official sale. On unsupported input, preserve the entered property and give a useful status.

### 5.3 Investigation detail

Above the fold: property identity/label, asking price marked *user-reported*, analysis date, result evidence status, eligible sale count and one clear next action.

Evidence area: consistently ranked comparable rows/cards with price, date, area, class, size difference, recency, legitimate geography, explanation and limitations, only where source rights permit. Exploratory 2 km fallback is **not a valuation** and should carry a persistent warning.

Details view: provenance, dataset ID, build/snapshot version, rule version, excluded/ambiguous records and known time limitations. Material uncertainty must never be hidden only in a collapsed panel.

### 5.4 Shortlist and comparison

Keep two or three property columns with aligned comparable facts and notes. Mark unknown/not available instead of inventing totals or replacing missing fields with zeros. Give users easy ways to add/remove a property from comparison and return to its frozen investigation. For mobile, consider stacked property summaries with an accessible *compare one attribute at a time* or horizontally scrollable data-table pattern, without truncating critical data.

### 5.5 Evidence and methodology

Explain coverage, recorded sale versus asking price, candidate selection, neighbourhood versus exploratory radius, historical as-of uncertainty, limitations and responsible use. Make this contextual from every investigation. A long documentation page alone is not sufficient.

## 6. First illustrative visual concept: "Precision Slate" property shortlist

**Status: concept only.** The conversation's visual study was not a production frontend implementation. Reconstruct its hierarchy as follows:

```text
+------------------+----------------------------------------------------+
| HPI / Research   | Workspace / My Shortlist    SYNTHETIC CONCEPT    |
|                  |                                                    |
| Overview         | Your shortlist                      + Add property |
| Investigations   | Compare the evidence behind each option           |
| My shortlist *   |                                                    |
| Evidence guide   | [2 properties] [3 selected sales] [1 needs data]  |
|                  |                                                    |
| Research scope   | [Property A]                 [Property B]         |
| Evanston fixture | Supported neighbourhood      Insufficient data   |
| only             | User asking: $500,000       User asking: $540,000 |
|                  | Area 1,600 sq ft            Area 1,850 sq ft     |
|                  |                                                    |
|                  | Side-by-side comparison                             |
|                  |                  Property A    Property B           |
|                  | Asking price     $500,000      $540,000             |
|                  | Building area    1,600         1,850                |
|                  | Eligible sales   3             not available        |
|                  | Evidence tier    neighbourhood insufficient        |
|                  | Valuation        not available not available        |
|                  |                                                    |
|                  | Sources, caveats and limitations                   |
+------------------+----------------------------------------------------+
```

The values above are **invented illustrative test data**. The concept preview was a non-functional interface study. No screenshots, property facts or personal identities have been promoted to real product content. It is **not** approval for sidebar navigation, cards, KPIs, palette or layout.

On desktop, the concept uses a quiet left navigation and a constrained content region. On mobile it reduces navigation density, stacks summary blocks and retains meaningful comparison semantics. Final interaction patterns require testing.

## 7. Three visual directions considered (none approved)

| Direction | Feeling | Candidate palette | Likely fit |
| --- | --- | --- | --- |
| A. Editorial Property | Warm, premium, residential | background `#F7F6F1`; text `#18272B`; accent `#285E56`; muted `#546169` | Consumer-first approachable buying workspace |
| B. Precision Slate | Precise, calm, professional | background `#F5F7FB`; text `#15243A`; accent `#2554A3`; muted `#54627A` | Evidence-rich research and comparison; **researcher's initial preferred study**, not chosen |
| C. Midnight Intelligence | Technical, modern dark | background `#171C24`; text `#F3F6FB`; accent `#91B8FF`; muted `#CAD0DB` | Potential secondary dark theme, not recommended as required v1 |

Estimated WCAG contrast ratios for **text versus named background**: A 14.23:1, B 14.55:1, C 15.79:1. Accent versus named background: A 6.87:1, B 6.81:1, C 8.55:1. Approximate computed colour-pair checks are **not full UI accessibility certification**. Every real text, border, form-control, chart and semantic state combination must be separately tested.

**Design hypothesis:** Begin exploration with Precision Slate's clarity plus some Editorial Property warmth. Do **not** treat that blend as an owner-approved colour system. The existing teal prototype does not bind the final branding.

### Semantic status colour discipline

- **Supported neighbourhood:** descriptive label and appropriately distinct visual support, not a green "good price" verdict.
- **Exploratory spatial:** clear warning that evidence is exploratory and not a validated valuation.
- **Insufficient data / out of coverage:** neutral or caution treatment with readable explanations, never a fabricated price.
- **Validation/system error:** dedicated error treatment; avoid retaining stale previous-property content, links or loading states.
- **Privacy/source permissions:** a separate availability gate, not a decorative status colour.

Never communicate evidence or financial suitability by colour alone.

## 8. Proposed typography, layout and design tokens

**These are starting experiments, not fixed standards or the final brand.**

| Token / pattern | Initial experiment |
| --- | --- |
| Spacing scale | `4, 8, 12, 16, 24, 32, 48, 64px`; group related information more tightly than separate sections |
| Body text | Start with around `16px` and `1.5` line height; avoid tiny grey text for key evidence |
| Page titles | Test `28-36px` desktop; adjust responsively |
| Section titles | Test `20-28px`, with visible structural hierarchy |
| Main actions | Prefer `44-48px` high buttons/inputs where appropriate; WCAG 2.2 AA 2.5.8 is generally **24x24 CSS px**, subject to exceptions, not universally 44x44 |
| Surfaces | Low-contrast containers, restrained 1px separators, corners around `8-12px` where visually appropriate |
| Density | Intentional rather than maximal whitespace; keep closely related property facts in the same group |
| Tables | Aligned currencies, dates and units, responsive overflow/reflow and meaningful headers |
| Desktop layout | Test restrained sidebar where useful and a readable maximum content width; not a permanently approved navigation model |
| Mobile layout | Compact navigation, stacked summaries, usable forms and deliberate treatment of genuine two-dimensional tables |
| Motion | Small purposeful feedback only; support reduced-motion preference |
| Typefaces | System font is an acceptable initial choice; no selected brand font, paid licensing or extra font payload |

**WCAG 2.2 AA references:** typical normal-text contrast `>=4.5:1`, large text `>=3:1`, and essential non-text UI indicators generally `>=3:1`; appropriate target sizes/spacing and reflow are also required. Two-dimensional data tables have particular reflow considerations; do not use that exception as a reason for a fixed-width overall mobile page.

## 9. Frontend professional do / do not

| Do | Avoid |
| --- | --- |
| Native semantic HTML: navigation landmarks, headings, labels, buttons and tables | Clickable generic containers without keyboard semantics |
| Keep a consistent layout and design token vocabulary | Per-page colours and incompatible card/spacing conventions |
| Make price provenance and evidence status visible | "Fair price", "undervalued" badges or model-like numbers without validation |
| Put aligned shortlist facts together | Force a buyer to remember numbers from multiple unrelated cards |
| Show meaningful loading, empty, insufficient, unsupported and error states | Display stale property evidence or share links after a failed/new request |
| Use inline form feedback and preserve entered input | Reset the user's work after unsupported/invalid submissions |
| Provide accessible focus, keyboard control, contrast, zoom and motion handling | Hover-only actions or colour-only risk meaning |
| Use tables for comparisons; use charts only if they truly add insight | Decorative KPIs, gauges, ungrounded maps or unlicensed photos |
| Track LCP, INP, CLS and browser acceptance with representative tasks | Install a UI framework or animation library solely for aesthetic fashion |
| Separate user reports, publisher facts and later predictive output | Conflate asking prices, recorded sale prices and future estimates |
| Protect source rights, historical as-of uncertainty and irreversible evidence snapshots | Hide unresolved rights/time limitations in tiny text |

## 10. Page and interaction acceptance cases to design for

**Workspace:** empty first visit; one and two saved enquiries; insufficient property in shortlist; archived/reopened investigations; no account/session persistence assumptions without a contract.

**Add property:** valid supported input; missing/invalid price; invalid PIN where technical input is used; unknown identity; unsupported class or geography; preserve data while recovering.

**Investigation:** three-plus eligible neighbourhood records; exploratory spatial warnings; fewer than three; no eligible sales; missing coordinates; source/response corruption; analysis date/time limitations.

**State integrity:** on a new valid request, do not display the old result as current; failed new/reopen request clears prior evidence/shareable URL; reject malformed statuses/inconsistent counts/non-synthetic data in fixture-only UI; keyboard and screen-reader messages are perceivable.

**Shortlist/compare:** add two investigations; show a weak-evidence entry; inline notes; exact frozen evidence after reopening; different property characteristics and units; unknown fields clearly missing; longer content and mobile overflow.

**Accessibility and performance:** keyboard-only end-to-end flow, visible focus, screen-reader names and live error announcements; check 320px equivalent reflow/400% zoom where applicable, common mobile/tablet/desktop widths, reduced motion and contrast; record meaningful LCP, INP and CLS when representative production-like builds exist.

A visually attractive concept **does not pass** until actual tasks and error/weak-data states work for users.

## 11. Rollout path within P0-P8 (proposal only)

1. **P0/P3 product alignment:** Confirm first buyer, actual supported market, credible input method, source display permissions and what the interface is legally and factually allowed to claim.
2. **P3 UX contract:** Agree on navigation/information architecture, UI state catalogue and first user journey before adopting a colour system. Keep technical contracts and evidence rules unchanged.
3. **P5 design exploration:** Produce low-fidelity wireframes for workspace, add property, investigation, shortlist comparison and methodology; compare a warm consumer direction with a precise research direction.
4. **P4/P5 integrated implementation:** Once approved, replace visual presentation in small browser-to-API-to-SQLite slices, with complete test coverage and preservation of saved-evidence behaviour.
5. **P6 decision journey:** Complete comparison, notes and revisit experience.
6. **P7/P8 readiness:** Independently assess genuine task success, accessibility, responsive usability, source rights, privacy, recovery and reproducible demo.

**No framework migration or large redesign is authorised by this document.** The current HTML/CSS/JS prototype remains a useful, tested engineering baseline.

## 12. Explicit open design decisions (owner approval pending)

1. **Product personality:** Welcoming consumer homebuying companion, premium analytical research tool, or deliberately balanced hybrid?
2. **Primary landing experience:** My Shortlist / Workspace versus Add Property / Explore; how does a first-time user see an empty state?
3. **Navigation:** Desktop left sidebar, top navigation or a hybrid; practical mobile counterpart.
4. **Visual identity:** Editorial Property, Precision Slate, Midnight, new direction or hybrid; approved colour scale, typeface, logo, tone and iconography.
5. **Property presentation:** Text-first evidence versus licensed imagery-first cards, constrained by verified source rights.
6. **Detail density:** How much methodology should always be visible versus progressively disclosed?
7. **Buyer entry:** Address resolution, supported manual inputs or PIN where technically required; no address-search claim yet.
8. **Maps/location:** Only if real geographic coverage, licensed/correct coordinates and real buyer value justify them.
9. **User persistence:** Local device/session versus accounts; permission/security implications.
10. **Pinnacle expansion:** When if ever to introduce validated prediction, affordability scenarios, market intelligence, reports and alerts.
11. **Design validation:** Which representative buyer tasks, usability comparisons and accessibility benchmarks determine acceptance?

Until these are decided, references, concepts and colour values are **nonbinding exploration**. Any final aesthetic change requires a separate design decision and owner sign-off.

## 13. Status and handoff

**Remote GitHub source before this documentation update:** `3f08060ed282173c0ade8d66cf2d66df45189893`, with last committed 125-test offline CI run successful. The original source at that revision has **not** adopted the consolidated P3 safety patch.

**New owner-supplied local Windows evidence on 23 November:** Screenshots show an isolated patched checkout successfully running **127 Python tests**, **15 Playwright Chromium DOM scenarios** and an actual synthetic **browser -> Python -> SQLite** investigation journey, including reopen and insufficient-data outcomes. The disposable verifier explicitly stated the original repository was not modified. These are local evidence from the user, **not a GitHub CI run on the proposed patch and not production acceptance**. Final P3 domain/input/versioning decisions, actual product design approval, source field rights and eventual release remain open.

**Unchanged estimate:** P3 10%, weighted flagship MVP 22.8%; no progress is added by the design research, illustrative mockup or local-only uncommitted candidate.

**Next design discussion:** Evaluate product personality and shortlist-first IA against a low-fidelity set of real buyer tasks; then agree a visual direction. **Next engineering action is independently governed** by the active P3 contract and verified safety-patch integration process, not by this design study.
