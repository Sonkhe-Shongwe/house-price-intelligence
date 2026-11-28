"""Restricted direct Neon candidate for the single-owner provider buyer journey.

No launcher, owner registration, credential provisioning, role activation,
real-data ingestion or public hosting. Use only in a separately approved window.
"""
from contextlib import contextmanager
from backend.auth0_invented_buyer import Auth0InventedBuyer
from backend.neon_synthetic_journey import NeonSyntheticJourney,_connect_service
from backend.neon_service_preflight import service_parameters
from backend.historical_seal_config import load_historical_seal
from backend.neon_synthetic_seed import fixture_plan
from backend.curated_ingestion_candidate import ImportRefused

MODE="development-provider-invented-journey"


class NeonProviderBuyer(NeonSyntheticJourney):
    """Exact invented source and strict cloud transport, separate provider owner."""
    _identity_owners=staticmethod(Auth0InventedBuyer._identity_owners)


@contextmanager
def open_neon_provider_buyer(environ,seal_path,boundary,*,progress=lambda stage:None):
    if environ.get("HPI_NEON_MODE")!=MODE:
        raise ImportRefused("Explicit provider invented journey required")
    # Refuse an invalid owner/issuer before reading secrets or opening connections.
    NeonProviderBuyer._identity_owners(boundary)
    seal=load_historical_seal(seal_path)
    if seal["build_id"]!=fixture_plan()[0]:
        raise ImportRefused("Only the fixed invented build is permitted")
    reader,writer=service_parameters(dict(environ,HPI_NEON_MODE="development-restricted-preflight"))
    for p in (reader,writer):
        p["application_name"]="hpi_provider_invented_journey"
    with _connect_service(reader,"reader",progress) as rd, _connect_service(writer,"buyer",progress) as wr:
        progress("service_identity_permissions_and_seal")
        yield NeonProviderBuyer(rd,wr,seal,boundary,expected_host=environ.get("HPI_NEON_DEVELOPMENT_HOST"))
