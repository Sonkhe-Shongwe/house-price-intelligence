# Frontend: synthetic-only property investigation browser

**Status (22 November 2026):** A plain HTML/CSS/JavaScript *demonstration* is included with the P3 fixture-only HTTP service. It is not a deployed consumer product, validated address search or proof of browser graphical acceptance.

The page accepts an invented 14-digit parcel PIN, user-reported asking price and investigation date. It presents synthetic comparable-sale evidence, source-build details, neighbourhood versus exploratory fallback warnings, insufficient/out-of-coverage states, and reopens saved fixture results by investigation ID. No numeric property valuation is generated.

Start with `python -m backend.run_synthetic_api --fixture-only --port 8765` from the repository root, then visit `http://127.0.0.1:8765/`. The HTTP and asset tests have been exercised locally; a genuine graphical browser journey remains unverified because the prior Chromium environment was blocked.

**Not implemented:** trusted address search, map-based lookup, user accounts, shortlist/side-by-side user workflow, publisher-data display rights, current prices or production deployment.

See the [P3 application contract](../docs/engineering/P3_APPLICATION_CONTRACT.md), [product brief](../docs/product/PRODUCT_BRIEF.md) and [current checkpoint](../docs/CHECKPOINT.md).
