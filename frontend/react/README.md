# React application integration V1 (review candidate)

Fictional only. Uses the canonical Python WSGI launcher, v0.3 API, matching service and SQLite fixture store. No prototype server or secondary database schema. The legacy UI is still the default until visual acceptance and migration approval.

From the repository root:

    npm ci --prefix frontend/react
    npm run build --prefix frontend/react
    python -m backend.run_synthetic_api --fixture-only --frontend react --port 8765

Open http://127.0.0.1:8765/. For a controlled local restart append --fixture-db ./fictional-demo.sqlite. Do not enter real data. The React file mode checks POSIX private ownership/mode and rejects hard links; Windows ACL validation remains open. No public serving, authentication, real geography, map renderer adoption or valuations. The isolated WebGL proof remains historical on its original branch.

Use --frontend legacy (or omit the option) for the existing UI. Neither frontend owns evidence or matching.


### Optional fictional map

Use the same build and launcher with `--synthetic-map`: `python -m backend.run_synthetic_api --fixture-only --frontend react --synthetic-map --port 8765`. Save/reopen an investigation and choose **Explore fictional map**. Positions come from a versioned virtual display source, not real coordinates, and do not affect matching. No external tiles, geocoder, distance or valuation. Existing `--fixture-db` files remain valid; omit the flag to disable the map. See [contract](../../docs/engineering/SYNTHETIC_GEOGRAPHIC_EVIDENCE_V1.md).


Open `/` for the workspace landing page or `/buyer-workflow` for direct investigation. Use Saved properties to search the latest 30 verified investigations and Compare to reopen existing shortlists. See [workspace contract](../../docs/engineering/BUYER_WORKSPACE_UX_V1.md).
