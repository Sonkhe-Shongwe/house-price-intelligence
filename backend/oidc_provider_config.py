"""Owner-injected Auth0 configuration candidate, no discovery or live launcher.

Local HTTPS qualification only. Never fetch keys automatically or load
credentials from the public repository. Existing fictional HTTP guard remains.
"""
import re
from jwt.algorithms import RSAAlgorithm
from backend.oidc_exchange import ConfidentialCodeExchange
from backend.persistent_oidc import PersistentBoundary

ISSUER=re.compile(r"https://[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z]{2})?\.auth0\.com/")
CALLBACK="https://127.0.0.1:8766/auth/callback"


def _pinned_keys(jwks):
    if not isinstance(jwks,dict) or set(jwks)!={"keys"} or not isinstance(jwks["keys"],list) or not 1<=len(jwks["keys"])<=8:
        raise ValueError("Provider signing keys refused")
    keys={}
    try:
        for item in jwks["keys"]:
            if (not isinstance(item,dict) or item.get("kty")!="RSA"
                or item.get("use")!="sig" or item.get("alg","RS256")!="RS256"
                or any(k in item for k in ("d","p","q","dp","dq","qi","oth"))
                or not isinstance(item.get("kid"),str) or not 1<=len(item["kid"])<=128
                or item["kid"] in keys
                or any(not isinstance(item.get(k),str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,1024}",item[k]) for k in ("n","e"))):
                raise ValueError
            key=RSAAlgorithm.from_jwk({k:item[k] for k in ("kty","n","e")})
            if not 2048<=key.key_size<=4096 or key.public_numbers().e!=65537:
                raise ValueError
            keys[item["kid"]]=key
    except Exception:
        raise ValueError("Provider signing keys refused") from None
    return keys


def prepare_auth0(*,issuer,client_id,client_secret,redirect_uri,jwks,owner_by_subject,session_file):
    """Build components only; caller must hold explicit trusted configuration.

    ID token maximum lifetime remains 600 seconds in OidcBoundary. Use a
    dedicated private session file; never reuse a fictional store or reassign
    existing owner IDs to different subjects. Provider registration is separate.
    """
    if (not isinstance(issuer,str) or not ISSUER.fullmatch(issuer)
        or redirect_uri!=CALLBACK
        or not isinstance(owner_by_subject,dict) or not 1<=len(owner_by_subject)<=2
        or any(not isinstance(sub,str) or not re.fullmatch(r"auth0\|[A-Za-z0-9_-]{1,128}",sub)
               or not isinstance(owner,str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}",owner)
               or owner.startswith("fixture-") for sub,owner in owner_by_subject.items())
        or len(set(owner_by_subject.values()))!=len(owner_by_subject)):
        raise ValueError("Provider configuration refused")
    keys=_pinned_keys(jwks)
    exchange=ConfidentialCodeExchange(issuer=issuer,token_endpoint=issuer+"oauth/token",
        client_id=client_id,client_secret=client_secret,redirect_uri=redirect_uri)
    boundary=PersistentBoundary(session_file=session_file,issuer=issuer,client_id=client_id,
        authorize_endpoint=issuer+"authorize",redirect_uri=redirect_uri,public_keys=keys,
        owner_map={(issuer,sub):owner for sub,owner in owner_by_subject.items()})
    return boundary,exchange
