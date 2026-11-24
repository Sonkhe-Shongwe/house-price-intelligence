# Controlled SQLite restart of fictional HPI evidence

**24 November 2026. Experimental proof only.** No approved public storage, backend schema migration, real data, valuation, production integration, user accounts or phase acceptance.

## The reliability gap

The original in_memory_demo created new fictional starter investigations and a new shortlist every time Python started. A saved investigation could reopen only while the same Python process ran. A browser confirmation was not proof of recovery after restart.

## Isolated, explicitly gated mechanism

The additional fixture_persistence.py within design-prototypes/react-map-spike/tests makes an exclusive, owner-controlled private SQLite file only when an operator specifies an absolute .sqlite3 path. First creation backs up the original in-memory synthetic dataset into a private temporary database, seeds two starter cases and a shortlist, stores their UUIDs in a preview_bootstrap record and publishes the complete file only after integrity checks. An existing file is opened in read/write mode and **never reseeded or migrated**.

The preview CLI option **--fixture-db ABSOLUTE_PATH.sqlite3** requires **both** --enable-buyer-workflow and --enable-shortlist-workflow. Omitting --fixture-db retains the old disposable in-memory behaviour, and the previous two privilege levels remain unchanged.

Every file reopen demands an absolute private non-symlink regular file owned by the local operator; an HPIF SQLite application marker, matching schema version, passing SQLite integrity and foreign-key checks, the expected fictional build and snapshots, valid starter case UUIDs/statuses and the original two-member shortlist. Unknown or imported databases are refused instead of silently initialized.

## Manual run on the isolated feature branch

From the repository root:

    npm ci --prefix design-prototypes/react-map-spike
    npm run build --prefix design-prototypes/react-map-spike
    mkdir -p local-fictional-proof
    chmod 700 local-fictional-proof
    python design-prototypes/react-map-spike/tests/source_preview_server.py --port 8797 --enable-buyer-workflow --enable-shortlist-workflow --fixture-db "$(pwd)/local-fictional-proof/demo.sqlite3"

Open http://127.0.0.1:8797/buyer-workflow. Create two investigations using fictional addresses, save both to a shortlist and save a note on each. Copy investigation and shortlist IDs. Stop the server, restart with the exact same arguments and file, and reopen those IDs. This folder must never contain real personal or property data.

## Hosted acceptance checks

The new test_persistent_restart.py starts an actual localhost Python WSGI process and uses real Chromium to create two investigations, a two-property shortlist and notes. It captures the original HTTP JSON, saved result response_json and SHA-256 fields, selected sale cents/transactions, source snapshots and stored membership/notes; gracefully interrupts the Python process, restarts with the same SQLite path, reopens both records in the browser and compares all original database rows and API documents. It also verifies starter IDs are not regenerated, default in-memory mode DOES regenerate IDs, and foreign databases, symlinks, weak permissions and missing opt-in flags are refused. A fifth case intentionally alters a fictional source transaction's cents **after shutdown** and confirms the next server startup refuses that database without rewriting frozen evidence.

**Verify the exact-SHA GitHub Actions result before claiming the restart test passed.** This is not proof of disk-crash/power-loss resilience, concurrent users, encryption, backups, authentication or safe public access.

## Boundaries and follow-up

The canonical backend and frontend directories remain unchanged. Existing dummy coordinates do not provide verified geography, and no property estimate is generated. The experiment lives only on feature/react-maplibre-full-spike-validation-20261123; development, main, draft PR #4 and the official 22.8% progress baseline remain unchanged.

Any production persistence design still needs its own durability, migration, isolation, permissions, rollback and privacy review, plus explicit owner approval of the React interface and data rights.