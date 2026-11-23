# Backend: synthetic-only investigation service

**Current candidate: 23 November 2026.** Python standard library, SQLite, WSGI, HTML/CSS/JS. This is a local fictional-data investigation prototype, **not** a production API, an authorised public property database or an appraisal.

- `investigation_contract.py`: validates buyer-entered enquiry fields and four evidence statuses; buyer asking price is user reported.
- `synthetic_investigation_store.py`: server-bound fictional address selection, curated source joins, exact sale-price strings from integer cents, saved results and tamper-checked reopening.
- `synthetic_http.py` and `run_synthetic_api.py`: loopback-only HTTP boundary with no real-source publication.
- `schema_draft.sql`: **frozen fixture-only v1 baseline** of 16 domain/fixture tables. It is not an approved production DDL. Do not change this v1 script in place after versioning: add a numbered migration.
- `schema_migrations.py` and numbered `migrations/`: immutable v1, v2 query indexes and **v3 synthetic parcel-candidate table**, with SHA-256 history, SQLite user-version checks, foreign keys, explicit DDL rollback and no adoption of unversioned databases. Version control adds one metadata table, `schema_migrations`.
- `synthetic_demo.py`: creates an in-memory v3 fixture by default, with four unambiguous invented addresses and two different parcels sharing the *same invented street address*. Historic v1/v2 fixtures can still upgrade, preserving saved investigations.

From the repository root, run only for local, synthetic-only acceptance:

```bash
python -m backend.run_synthetic_api --fixture-only --port 8765
python tools/dev_check.py --focus app
```

Open http://127.0.0.1:8765/ locally. Nothing is persisted after process shutdown and the service must not be deployed or given real publisher records. Automated tests run in GitHub Actions on the permanent `development` branch. Fixture migrations are an engineering candidate, not the accepted production backup/restore, source-ingestion or user-identity plan.

See the [single current P3 contract and proposed ERD](../docs/engineering/P3_APPLICATION_CONTRACT.md), [current checkpoint](../docs/CHECKPOINT.md), and [engineering guardrails](../docs/engineering/ENGINEERING_CONTRACT.md).
