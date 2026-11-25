# Backend: synthetic-only investigation service

**Local fixture runtime:** Python, SQLite and WSGI, with legacy and React frontends. The separately tested PostgreSQL runtime and historical reader remain development-only. This is a local fictional-data investigation prototype, **not** a production API, an authorised public property database or an appraisal.

- `investigation_contract.py`: validates buyer-entered enquiry fields and four evidence statuses; buyer asking price is user reported.
- `synthetic_investigation_store.py`: server-bound fictional address selection, curated source joins, exact sale-price strings from integer cents, saved results and tamper-checked reopening.
- `synthetic_http.py` and `run_synthetic_api.py`: loopback-only HTTP boundary with no real-source publication.
- `schema_draft.sql`: **frozen fixture-only v1 baseline** of 16 domain/fixture tables. It is not an approved production DDL. Do not change this v1 script in place after versioning: add a numbered migration.
- `schema_migrations.py` and numbered `migrations/`: immutable v1, v2 query indexes and **v3 synthetic parcel-candidate table**, with SHA-256 history, SQLite user-version checks, foreign keys, explicit DDL rollback and no adoption of unversioned databases. Version control adds one metadata table, `schema_migrations`.
- `synthetic_demo.py`: creates an in-memory v3 fixture by default, with four unambiguous invented addresses and two different parcels sharing the *same invented street address*. Historic v1/v2 fixtures can still upgrade, preserving saved investigations.
- `durable_fixture.py`: explicit on-disk invented-fixture opener with source/schema integrity checks and no adoption of unknown real databases.
- `synthetic_shortlists.py`: capped two-to-three-property shortlist workflow with editable notes that never modify frozen sale evidence. Browser UI compares the properties side by side.

From the repository root, run only for local, synthetic-only acceptance:

```bash
python -m backend.run_synthetic_api --fixture-only --port 8765
python tools/dev_check.py --focus app
```

Open http://127.0.0.1:8765/ locally. By default nothing is persisted after process shutdown; explicit `--fixture-db` mode persists fictional investigations, shortlists and notes across restarts. The service must not be deployed or given real publisher records. Automated tests run in GitHub Actions on the permanent `development` branch. Fixture migrations are an engineering candidate, not the accepted production backup/restore, source-ingestion or user-identity plan.

See the [P3 candidate contract and proposed ERD](../docs/engineering/P3_APPLICATION_CONTRACT.md), [P6 shortlist contract](../docs/engineering/P6_SYNTHETIC_SHORTLIST_CONTRACT.md), [current checkpoint](../docs/CHECKPOINT.md), and [engineering guardrails](../docs/engineering/ENGINEERING_CONTRACT.md).

## PostgreSQL development preparation

The disposable PostgreSQL 17 runtime, split-role historical reader/buyer persistence and authenticated browser rehearsal are CI-verified. Neon development schema and restricted grants are installed; temporary credentials configured, but direct application connectivity and real-data activation are not. The protected connection workflow invokes `python -m backend.neon_service_preflight`; see the checkpoint for the current approval and secret procedure. See [current checkpoint](../docs/CHECKPOINT.md) and [Neon integration](../docs/engineering/NEON_CLOUD_INTEGRATION_V1.md). Do not change the loopback-only fixture guards to connect a real database; use the reviewed cloud integration path.

## Optional durable fictional investigations (development only)

The existing `--fixture-only` command uses disposable in-memory SQLite by default.
To retain invented investigations across controlled restarts, explicitly specify
a **new or previously verified fixture database** in an existing directory:

```bash
python -m backend.run_synthetic_api --fixture-only --port 8765 --fixture-db /path/to/my-fictional.sqlite
```

The file contains seeded fictional evidence plus whatever enquiry labels and
asking-price text the tester chooses to enter. **Do not enter personal data.**
Neither authentication nor encryption is provided. This is a localhost-only
development feature, not a production database, public API or real-data importer.

An existing recognized v3 database reopens without reseeding or rematching old
results. Unknown, corrupted, symlinked or older-version databases are refused
without automatic conversion. Existing values are not silently overwritten.
The durable file, SQLite journal/WAL files and other local data files are
ignored by Git. Use a new path when you want a fresh fictional demonstration.
The existing matcher, transaction cents, snapshot roles and saved-evidence
guards remain unchanged.
