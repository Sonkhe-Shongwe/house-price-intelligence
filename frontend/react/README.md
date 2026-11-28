# React application integration V1 (integrated fictional workspace)

Fictional only. Uses the canonical Python WSGI launcher, v0.3 API, matching service and SQLite fixture store. No prototype server or secondary database schema. React is integrated on development; the legacy SQLite launcher remains the default unless the React flag is specified. Atlas primary visual direction approved; core frontend qualification verified, final real-buyer/release acceptance remains open.

From the repository root:

    npm ci --prefix frontend/react
    npm run build --prefix frontend/react
    python -m backend.run_synthetic_api --fixture-only --frontend react --port 8765

Open http://127.0.0.1:8765/. For a controlled local restart append --fixture-db ./fictional-demo.sqlite. Do not enter real data. The React file mode checks POSIX private ownership/mode and rejects hard links; Windows ACL validation remains open. This local SQLite path has no public serving, production authentication, real geography or valuations. MapLibre/PMTiles are integrated for fictional display and generated contextual qualification only; actual combined Auth0/Neon invented buyer milestone verified separately, no live real-property or deployed service. The isolated WebGL proof remains historical on its original branch.

Use --frontend legacy (or omit the option) for the existing UI. Neither frontend owns evidence or matching.


### Optional fictional map

Use the same build and launcher with `--synthetic-map`: `python -m backend.run_synthetic_api --fixture-only --frontend react --synthetic-map --port 8765`. Save/reopen an investigation and choose **Explore fictional map**. Positions come from a versioned virtual display source, not real coordinates, and do not affect matching. No external tiles, geocoder, distance or valuation. Existing `--fixture-db` files remain valid; omit the flag to disable the map. See [contract](../../docs/engineering/SYNTHETIC_GEOGRAPHIC_EVIDENCE_V1.md).


Open `/` for the workspace landing page or `/buyer-workflow` for direct investigation. Use Saved properties to search the latest 30 verified investigations and Compare to reopen existing shortlists. See [workspace contract](../../docs/engineering/BUYER_WORKSPACE_UX_V1.md).

### Optional generated contextual qualification

With the same React build, run the local fixture launcher with `--context-transport-fixture` and visit `/context-preview`. Explicitly load the invented contextual map. This separate opt-in view serves a tiny generated PMTiles archive via same-origin conditional ranges, with no property markers or external sources; disabled by default. No real regional archive is acquired or displayed. See [checkpoint](../../docs/CHECKPOINT.md) and the [bounded proposal](../../docs/design/BASEMAP_ACQUISITION_PROPOSAL_2026-11-26.md).

### Authenticated private historical-shape rehearsal

The same React bundle now includes `/private-beta-rehearsal` when explicitly served through the approved private rehearsal runtime (offline HTTPS/OIDC fixtures or the previously authorised actual provider/Neon invented milestone). Actual disposable PostgreSQL browser tests verify fictional address search, save, refresh/reopen and cross-owner refusal. This is not a public or live real-data route; ordinary launcher instructions above remain unchanged. See [private beta contract](../../docs/engineering/PRIVATE_REAL_DATA_BETA_V1.md) and [checkpoint](../../docs/CHECKPOINT.md).
