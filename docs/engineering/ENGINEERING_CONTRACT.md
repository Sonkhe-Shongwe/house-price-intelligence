# Engineering contract: correctness before prediction

## Data invariants

1. A sale transaction, land parcel, building and historical assessment-year record are distinct. Do not multiply transactions through joins or allocate a multi-parcel sale price to a single building.
2. Preserve PIN as a 14-character string, including leading zeros. Record official transaction identifiers, source dataset ID, extraction snapshot and source date where permitted.
3. A comparable must refer to a completed **earlier** sale, in the same supported property class and location (or an explicitly documented expansion), with enough physical similarity to be meaningful.
4. A property entered by the user is not an independently verified listing; asking price is not recorded sale price.
5. Unknown/missing and out-of-coverage evidence must remain explicit. An insufficient-data response is valid product behaviour, not an application crash.
6. Historical models and comparisons must not use future transactions or property characteristics unavailable as of the evaluation date. The current Phase 0 prior-year proxy is **not** a proven point-in-time snapshot.
7. Report sample sizes, discarded records and rejection reasons. Do not silently remove expensive homes solely to make estimates look better.
8. Separate cleaned data, user-entered values, derived analytical results and optional model predictions in the application data model.

## Audit-specific quality gates

- [ ] Source metadata and whitelisted fields inspected on the actual run
- [ ] No extraction row cap or unstable pagination overlooked
- [ ] Sale and building grain verified with representative sample records
- [ ] Official class codes independently confirmed
- [ ] Eligible transactions and comparable coverage measured
- [ ] Data rights and personal-information minimisation reviewed
- [ ] Independent tests check bad joins, multi-parcel exclusions, future comparables and weak-data outcomes

## Software quality gates, after phase 0

- Persist the user inquiry, comparable evidence and source/rule versions.
- Keep selection/eligibility logic independently testable, separate from UI.
- Implement safe authorization and server-side validation if accounts exist.
- Include repeatable fixtures for demos but distinguish them from real market evidence.
- Keep setup docs, tests and a browser-to-database integration test.
- Show failures honestly: stale snapshot, unsupported segment, no eligible comps, ambiguous building matching.

## Known Phase 0 gaps to fix after first real run

The current script uses an exploratory $20k-$5m price screen, same-class, ±25% floor area and 365-day lookback. These are **not** authoritative county rules and must be justified or revised from the measured sample. It uses prior assessment tax year, which may contain later revisions. Offset pagination could shift under concurrent source updates; reproduce a stable extract and document its timestamp. A row cap may truncate either dataset. Do not interpret an incomplete or unexpectedly small output as final coverage evidence.
