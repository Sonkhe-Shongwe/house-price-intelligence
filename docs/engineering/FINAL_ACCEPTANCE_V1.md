# Final Product Acceptance and Release Engineering V1

Owner authorised FA1–FA8 on 24 November 2026. Starting planning estimate 79.2%; original real-data MVP and existing P0–P8 weights/gates retained. No main merge, deployment, provider accounts, external contact, real property display or valuation.

## FA1 coverage diagnostic
Count-only queries against sale and building sources for township 17, sale years 2024/2025, assessment years 2023/2024. Count rows, non-null and distinct PINs; class 203 counts when the sales class field exists and for building data. Fixed source metadata before/after. No raw records or identifiers returned; no more holdout attempts or ranking changes. Aggregate source counts cannot establish the exact reasons for parcel-level join exclusions. Preserve the earlier too-few-subjects blocker.
