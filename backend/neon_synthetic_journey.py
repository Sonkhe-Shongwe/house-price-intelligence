"""Explicit, invented-only Neon journey adapter. No public server or importer.
The existing loopback HTTPS and fictional issuer boundary remains mandatory.
"""
from contextlib import contextmanager
import psycopg
from backend.neon_preflight import DATABASE, HOST
from backend.neon_service_preflight import service_parameters, _identity, _inspect_services, _connection_outcome
from backend.private_beta_rehearsal import PrivateBetaRehearsal
from backend.historical_reader import ROLE as READER, _verified_seal, _verify_reader_privileges
from backend.buyer_ownership import ROLE as BUYER
from backend.historical_postgres import _verify
from backend.historical_seal_config import load_historical_seal
from backend.neon_synthetic_seed import fixture_plan
from backend.curated_ingestion_candidate import ImportRefused

MODE="development-invented-journey"


class NeonSyntheticJourney(PrivateBetaRehearsal):
    """Internal adapter restricted to the exact generated fictional build."""
    def __init__(self,reader,writer,seal,boundary,*,expected_host):
        self.expected_host=expected_host
        self._plan=fixture_plan()
        self._startup_verified=False
        if seal.get("build_id")!=self._plan[0]:
            raise ImportRefused("Only the fixed invented build is permitted")
        super().__init__(reader,writer,seal,boundary)
        _inspect_services(reader,writer,database=DATABASE)
        with self._source():
            pass
        self._startup_verified=True

    def _check_connection(self,conn,role):
        host=self.expected_host
        if (not isinstance(host,str) or not HOST.fullmatch(host) or "-pooler" in host
            or role not in (READER,BUYER) or not conn.autocommit
            or (conn.info.host,conn.info.port,conn.info.dbname,conn.info.user)!=(host,5432,DATABASE,role)
            or not conn.pgconn.ssl_in_use):
            raise ImportRefused("Restricted direct Neon session required")
        p=conn.info.get_parameters()
        if any(p.get(k)!=v for k,v in (("sslmode","verify-full"),("sslrootcert","system"),("channel_binding","require"),("gssencmode","disable"))):
            raise ImportRefused("Strict cloud TLS configuration required")
        _identity(conn,role,DATABASE)

    def _verify_source(self,conn,seal):
        _verify_reader_privileges(conn)
        adapter,build,ids,stamp=_verified_seal(conn,seal)
        expected_build,expected_ids,expected_rows=self._plan
        if (build,ids)!=(expected_build,expected_ids):
            raise ImportRefused("Only the fixed invented build is permitted")
        # Verify exact generated values, not just a matching seal supplied by
        # an operator. No other historical build can be selected by a request.
        # Every request still verifies the complete external relational seal.
        # An unchanged cryptographic fingerprint binds the exact row check
        # performed at construction; avoid repeating one SELECT per seed row.
        if not self._startup_verified:
            _verify(adapter,build,ids,expected_rows)
        return adapter,build,ids,stamp


@contextmanager
def _connect_service(config,kind,progress):
    """Report only a fixed role and classified driver outcome, never a DSN."""
    progress(kind+"_connection")
    try:
        conn=psycopg.connect(**config,autocommit=True)
    except psycopg.Error as exc:
        progress(kind+"_connection_"+_connection_outcome(exc))
        raise
    with conn:
        yield conn


@contextmanager
def open_neon_synthetic_journey(environ,seal_path,boundary,*,progress=lambda stage:None):
    """Restricted connections only; caller provides a private external seal.
    No owner DSN, mode fallback, fixture guard override or persistent hosting.
    """
    if environ.get("HPI_NEON_MODE")!=MODE:
        raise ImportRefused("Explicit invented cloud journey required")
    progress("seal_configuration")
    seal=load_historical_seal(seal_path)
    if seal["build_id"]!=fixture_plan()[0]:
        raise ImportRefused("Only the fixed invented build is permitted")
    settings=dict(environ,HPI_NEON_MODE="development-restricted-preflight")
    progress("service_configuration")
    reader,writer=service_parameters(settings)
    for p in (reader,writer):
        p["application_name"]="hpi_invented_journey"
    with _connect_service(reader,"reader",progress) as rd, _connect_service(writer,"buyer",progress) as wr:
        progress("service_identity_permissions_and_seal")
        yield NeonSyntheticJourney(rd,wr,seal,boundary,expected_host=environ.get("HPI_NEON_DEVELOPMENT_HOST"))
