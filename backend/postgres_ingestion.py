"""PostgreSQL versioned fixture importer, separate disposable ingestion database.
Reuses the exact canonical import algorithm. Never called by buyer HTTP requests.
"""
from backend.curated_ingestion_candidate import CANDIDATE_DDL, _import_rows, _verify_build, ImportRefused
from backend.postgres_fixture import FixtureConnection, migrate
from backend.synthetic_investigation_store import SyntheticInvestigationStore

def _check(conn):
    if (conn.info.host,conn.info.dbname,conn.info.user)!=("127.0.0.1","hpi_ingest_fixture","postgres") or not conn.autocommit:
        raise ImportRefused("Only disposable loopback ingestion fixture database allowed")

def initialise(conn):
    _check(conn)
    _initialise_schema(conn)


def _initialise_schema(conn):
    """Shared migration implementation; caller must enforce target boundary."""
    with conn.transaction():
        if conn.execute("SELECT to_regnamespace('hpi_candidate')").fetchone()[0] is not None:
            raise ImportRefused("Refusing existing schema")
        migrate(conn)
        conn.execute("SET LOCAL search_path TO hpi_candidate, pg_catalog")
        conn.execute(CANDIDATE_DDL,prepare=False)

def import_revision(conn,revision):
    _check(conn)
    adapter=FixtureConnection(conn)
    with conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(194323)")
        if conn.execute("SELECT to_regclass('candidate_manifests')").fetchone()[0] is None:
            raise ImportRefused("Unknown ingestion candidate")
        return _import_rows(adapter,revision)

class ImportedFixtureStore(SyntheticInvestigationStore):
    def __init__(self,conn,revision):
        _check(conn)
        self.connection=FixtureConnection(conn)
        self.build_id=_verify_build(self.connection,revision)
        self._build()
