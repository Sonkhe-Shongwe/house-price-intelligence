# Backend: synthetic-only property investigation slice

**Status (22 November 2026):** An owner-authorised P3 integration provides a **fixture-only**, stdlib Python and SQLite investigation flow. It is **not** a production backend, real-source ingestion, approved public API, authenticated service or price model.

- `investigation_contract.py`: validated subject input and four evidence statuses, with a no-valuation policy.
- `schema_draft.sql`: 15-table relational *draft* separating parcels, historical records, sale transactions, source builds and saved investigations. It is not an accepted production migration.
- `synthetic_investigation_store.py`: PIN resolution, historical-match orchestration and transactional save/reopen in a curated synthetic build.
- `synthetic_http.py` / `run_synthetic_api.py`: restricted localhost HTTP endpoints and fixed frontend assets.
- `synthetic_demo.py`: invented in-memory dataset; no publisher records or personal data.

Run an explicitly opted-in disposable demo from the repository root:

```bash
python -m backend.run_synthetic_api --fixture-only --port 8765
```

Then open `http://127.0.0.1:8765/`. The process binds only to loopback, has no public auth, and must **never** be deployed or given real records. Saved fixture investigations vanish on shutdown.

For fast checks run `python tools/dev_check.py --focus app`, or `python tools/dev_check.py` for all research and application suites. Browser graphical acceptance is still outstanding. P3 domain/input/technology decisions remain subject to review.

See the [current P3 contract](../docs/engineering/P3_APPLICATION_CONTRACT.md), [engineering guardrails](../docs/engineering/ENGINEERING_CONTRACT.md), [lean directive](../docs/engineering/LEAN_ENGINEERING_DIRECTIVE.md) and [checkpoint](../docs/CHECKPOINT.md).
