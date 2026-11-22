# Engineering contract: correctness before prediction

**Reviewed:** 22 November 2026. Applies to both the research pipeline and the future buyer application. The [P0–P8 roadmap](../P_PHASE_ROADMAP.md) specifies stage acceptance, while this document states safeguards that remain binding throughout.

## Data invariants

1. A sale transaction, parcel, building and historical assessment-year record are separate entities. Never multiply transactions through joins or allocate a multi-parcel sale price to one building.
2. Preserve PIN as a 14-character string with leading zeros. Store publisher dataset ID, transaction document, relevant source version/extraction date and rule revision where allowed.
3. A comparable must represent an eligible **earlier** completed sale with transparent class/geography, recency and floor-area rules. A subject property must never be its own comparable; repeat sales of the same PIN do not count as independent houses.
4. A buyer's manually entered asking price is neither a verified listing price nor a completed sale. Source facts, inferred historical measures and user inputs must never be conflated.
5. Missing, ambiguous, stale, out-of-coverage or thin-data evidence is an explicit product status, not an exception that should be concealed.
6. A prior tax-year record does **not** prove it existed at a historical decision date. Do not claim a leakage-free historical backtest or valid current estimates without documented data availability.
7. Retain sale counts, excluded records and rejection reasons. Pilot thresholds are provisional, not publisher-certified market validity.
8. Separate original raw extracts, curated facts, matching decisions, user enquiries and any optional predictions. Do not expose raw records or names through CI artifacts or public Git.
9. Rank comparable candidates without using the subject's true recorded sale price; use that price only for subsequent retrospective evaluation.
10. A geographic fallback is labelled **exploratory evidence** until independently validated. The 2 km fallback has shown weak historical median-price accuracy on its 17 test cases.

## Research audit gate: status after live Phase 0–2 runs

- [x] Publisher schemas and selected source fields inspected during a real extraction.
- [x] Documented extraction row counts, screening exclusions and join counts; configured row cap not reached in the verified run.
- [x] Empirical comparable coverage measured for the selected historical township/Class 203 slice.
- [x] Offline regression tests cover integral-decimal counts, multi-parcel and bad joins, future sales, duplicate properties, weak support and report-export hygiene.
- [ ] Validate repeat extraction stability and publisher change drift; offset pagination can shift if the source changes mid-run.
- [ ] Independently review representative sale/parcel/building cases and full eligibility semantics for public display.
- [ ] Establish genuine historical as-of data availability or explicit restrictions that prevent misleading evaluation.
- [ ] Approve dataset-specific public display, attribution and redistribution rights, per required field.
- [ ] Evaluate coverage/accuracy against untouched later sales and documented abstention policy.

**Evidence:** [Phase 0](../research/PHASE0_LIVE_AUDIT_RESULTS.md), [Phase 1](../research/PHASE1_CLOUD_AUDIT_RESULTS.md), [Phase 2](../research/PHASE2_CLOUD_AUDIT_RESULTS.md), [cloud operations](../AUTOMATED_DATA_AUDIT.md). These checks do not mean all P1/P2 delivery gates are complete.

## Application engineering gates (P3–P8)

- [ ] Domain ERD distinguishes transaction, parcel, building, historical record, buyer property inquiry, match run, evidence, saved investigation and shortlist.
- [ ] API contract validates enquiry/class/geography/asking price, and returns `supported_neighbourhood`, `exploratory_spatial`, `insufficient_data` or `out_of_coverage` accurately.
- [ ] Persistent records include evidence snapshot/rule version and can be safely reopened; idempotent import and migrations are tested.
- [ ] Unit, API/database and browser end-to-end tests cover future sale, bad join, unsupported property, stale source, insufficient data and inconsistent metadata.
- [ ] Security, resource controls, accessibility and user-data handling match actual application scope; authorisation is required if accounts are introduced.
- [ ] Source field reuse/display is approved before public product deployment; no property-level record leaks in CI.
- [ ] Recruiter demonstration and clean setup are reproducible and show both supported evidence and honest refusal.

## Current known limitations

The raw extractor's **$20k–$5m** analyst sale-price bounds, **±25%** floor area and **365-day** lookback are provisional. The Phase 2 spatial fallback is an experimental **2 km**, not a validated market boundary. Some historical rows can be backfilled or revised, and offset paging during updates may change downloaded populations. A no-cap result in one run is **not** proof of stable repeated pagination. No price-prediction model has been approved.
