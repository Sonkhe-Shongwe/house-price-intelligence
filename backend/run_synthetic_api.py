"""Run a LOCAL-only, disposable synthetic investigation HTTP demo.

Invocation (explicit opt-in):
  python -m backend.run_synthetic_api --fixture-only --port 8765

No real data, user accounts, password, map/address search or production hardening.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sqlite3
from wsgiref.simple_server import make_server

from backend.durable_fixture import open_file_demo
from backend.synthetic_demo import in_memory_demo
from backend.synthetic_http import create_app
from backend.react_assets import load_react_assets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-only", action="store_true", help="Required; never serve real source data")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--fixture-db", type=Path, metavar="PATH",
                        help="Explicit opt-in: persist invented fixture evidence at this local SQLite file")
    parser.add_argument("--frontend", choices=("legacy", "react"), default="legacy",
                        help="Explicitly choose the integrated React candidate; legacy remains available")
    parser.add_argument("--synthetic-map", action="store_true", help="Opt in to virtual display geography; no real locations")
    parser.add_argument("--context-transport-fixture", action="store_true",
                        help="Serve generated non-map bytes for local HTTP range qualification only")
    args = parser.parse_args()
    if args.context_transport_fixture and args.frontend != "react":
        parser.error("--context-transport-fixture requires --frontend react")
    if args.synthetic_map and args.frontend != "react":
        parser.error("--synthetic-map requires --frontend react")
    if not args.fixture_only:
        parser.error("This demonstrator requires the explicit --fixture-only opt-in")
    if not 1024 <= args.port <= 65535:
        parser.error("Port must be between 1024 and 65535")
    try:
        assets = load_react_assets() if args.frontend == 'react' else None
        conn, store = (in_memory_demo() if args.fixture_db is None
                       else open_file_demo(args.fixture_db, private_file=args.frontend == 'react'))
    except (RuntimeError, ValueError, sqlite3.Error, OSError) as exc:
        parser.error(f"Refusing fixture database: {exc}")
    try:
        # Deliberately no option to bind to 0.0.0.0 or a remote interface.
        with make_server("127.0.0.1", args.port, create_app(store, react_assets=assets, synthetic_map=args.synthetic_map,
                        context_transport_fixture=args.context_transport_fixture)) as server:
            print(f"Fixture-only API at http://127.0.0.1:{args.port}/health")
            print("WARNING: invented records, no auth, no CORS, NOT FOR DEPLOYMENT")
            if args.fixture_db is not None:
                print("Durable invented-fixture mode; enquiry labels persist on disk.")
                print("Do not enter personal information; no authentication or encryption.")
            server.serve_forever()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
