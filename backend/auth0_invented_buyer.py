"""Auth0-shaped owner-only integration with the exact invented disposable build.

No cloud connector, real intake, owner provisioning or deployment entry point.
The original offline fixture and Neon adapters retain their existing guards.
"""
import re
from backend.private_beta_rehearsal import PrivateBetaRehearsal
from backend.persistent_oidc import PersistentBoundary
from backend.oidc_provider_config import CALLBACK,ISSUER
from backend.oidc_identity_http import ORIGIN
from backend.curated_ingestion_candidate import ImportRefused
from backend.historical_reader import _verified
from backend.historical_postgres import _verify
from backend.neon_synthetic_seed import fixture_plan


class Auth0InventedBuyer(PrivateBetaRehearsal):
    """Reuse the buyer service with a separate, pinned single-owner identity."""
    @staticmethod
    def _identity_owners(boundary):
        if (not isinstance(boundary,PersistentBoundary) or not ISSUER.fullmatch(boundary.issuer)
            or boundary.redirect!=CALLBACK or boundary.origin!=ORIGIN
            or len(boundary.owners)!=1):
            raise ImportRefused("Owner-only provider identity required")
        (identity,owner),=boundary.owners.items()
        if (not isinstance(identity,tuple) or len(identity)!=2 or identity[0]!=boundary.issuer
            or not isinstance(identity[1],str) or not re.fullmatch(r"auth0\|[A-Za-z0-9_-]{1,128}",identity[1])
            or not isinstance(owner,str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}",owner)
            or owner.startswith("fixture-")):
            raise ImportRefused("Separate provider owner required")
        return frozenset((owner,))

    def __init__(self,reader,writer,seal,boundary):
        self._plan=fixture_plan()
        if not isinstance(seal,dict) or seal.get("build_id")!=self._plan[0]:
            raise ImportRefused("Only the fixed invented build is permitted")
        super().__init__(reader,writer,seal,boundary)
        with self._source():
            pass

    def _verify_source(self,conn,seal):
        adapter,build,ids,stamp=_verified(conn,seal)
        expected_build,expected_ids,rows=self._plan
        if (build,ids)!=(expected_build,expected_ids):
            raise ImportRefused("Only the fixed invented build is permitted")
        _verify(adapter,build,ids,rows)
        return adapter,build,ids,stamp
