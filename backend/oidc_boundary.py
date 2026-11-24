"""Offline OIDC client/session boundary. No live discovery, provider, or HTTP login.
Use only server-injected pinned keys and a confidential code-exchange implementation.
In-memory state/session store is a test candidate, not multi-worker production storage.
"""
from dataclasses import dataclass
from hashlib import sha256
from base64 import urlsafe_b64encode
from hmac import compare_digest
from threading import RLock
from time import time
from urllib.parse import urlencode,urlsplit
import re
import secrets
import jwt

TOKEN=re.compile(r"^[A-Za-z0-9_-]{43}$")
COOKIE="__Host-hpi_session"
class AuthDenied(ValueError):pass
def random_token():return secrets.token_urlsafe(32)
def digest(value):return sha256(value.encode("ascii")).hexdigest()
def valid_token(value):return isinstance(value,str) and TOKEN.fullmatch(value) is not None
def https_url(value):
    u=urlsplit(value)
    if u.scheme!="https" or not u.hostname or u.username or u.password or u.fragment or u.query:
        raise ValueError("Pinned HTTPS endpoint required")
    return value
@dataclass(frozen=True)
class Pending:
    binding:str
    nonce:str
    verifier:str
    expires:float
@dataclass
class Session:
    owner:str
    csrf:str
    expires:float
    idle_until:float

class OidcBoundary:
    def __init__(self,*,issuer,client_id,authorize_endpoint,redirect_uri,public_keys,owner_map,clock=time):
        self.issuer=https_url(issuer)
        self.endpoint=https_url(authorize_endpoint)
        self.redirect=https_url(redirect_uri)
        if urlsplit(self.endpoint).netloc!=urlsplit(self.issuer).netloc:raise ValueError("Issuer endpoint mismatch")
        self.origin="https://"+urlsplit(self.redirect).netloc
        if not isinstance(client_id,str) or not client_id:raise ValueError("Client ID required")
        self.client_id=client_id
        self.keys=dict(public_keys)
        if not self.keys:raise ValueError("Pinned keys required")
        # Mapping is provisioned server-side, never taken from email, token roles or client owner.
        self.owners=dict(owner_map)
        self.clock=clock
        self.pending={}
        self.sessions={}
        self.lock=RLock()
    def _prune(self):
        now=self.clock()
        self.pending={k:v for k,v in self.pending.items() if v.expires>now}
        self.sessions={k:v for k,v in self.sessions.items() if v.expires>now and v.idle_until>now}
    def begin(self,browser_binding):
        if not valid_token(browser_binding):raise AuthDenied("Login binding rejected")
        with self.lock:
            self._prune()
            if len(self.pending)>=128:raise AuthDenied("Login unavailable")
            state,nonce,verifier=random_token(),random_token(),random_token()
            self.pending[digest(state)]=Pending(digest(browser_binding),nonce,verifier,self.clock()+300)
        challenge=urlsafe_b64encode(sha256(verifier.encode("ascii")).digest()).decode("ascii").rstrip("=")
        params={"response_type":"code","scope":"openid","client_id":self.client_id,"redirect_uri":self.redirect,
                "state":state,"nonce":nonce,"code_challenge":challenge,"code_challenge_method":"S256"}
        return self.endpoint+"?"+urlencode(params)
    def _verify(self,token,nonce):
        if not isinstance(token,str) or len(token)>16000:raise AuthDenied("Identity rejected")
        try:
            header=jwt.get_unverified_header(token)
            if header.get("alg")!="RS256" or any(k in header for k in ("jku","x5u","jwk","crit")):
                raise AuthDenied("Identity rejected")
            kid=header.get("kid")
            if not isinstance(kid,str) or kid not in self.keys:raise AuthDenied("Identity rejected")
            claims=jwt.decode(token,self.keys[kid],algorithms=["RS256"],audience=self.client_id,issuer=self.issuer,
                options={"require":["iss","sub","aud","exp","iat","nonce"],"strict_aud":True})
            if (type(claims["iat"]) is not int or type(claims["exp"]) is not int
                or claims["exp"]<=claims["iat"] or claims["exp"]-claims["iat"]>600
                or not isinstance(claims["nonce"],str) or not compare_digest(claims["nonce"],nonce)
                or ("azp" in claims and claims["azp"]!=self.client_id)):
                raise AuthDenied("Identity rejected")
            owner=self.owners.get((claims["iss"],claims["sub"]))
            if owner is None:raise AuthDenied("Identity rejected")
            return owner
        except (jwt.PyJWTError,ValueError,TypeError,KeyError) as exc:
            raise AuthDenied("Identity rejected") from None
    def finish(self,*,state,browser_binding,code,exchange):
        """Exchange is injected by trusted server code; offline tests never call a provider."""
        if not valid_token(state) or not valid_token(browser_binding) or not isinstance(code,str) or not 1<=len(code)<=2048:
            raise AuthDenied("Login callback rejected")
        with self.lock:
            self._prune()
            pending=self.pending.get(digest(state))
            if pending is None or not compare_digest(pending.binding,digest(browser_binding)):
                raise AuthDenied("Login callback rejected")
            del self.pending[digest(state)] # single use even on failed exchange
        try:token=exchange(code=code,verifier=pending.verifier,redirect_uri=self.redirect)
        except Exception:raise AuthDenied("Identity exchange unavailable") from None
        owner=self._verify(token,pending.nonce)
        return self._issue_session(owner)

    def _issue_session(self,owner):
        with self.lock:
            self._prune()
            if len(self.sessions)>=128:raise AuthDenied("Session unavailable")
            token,csrf=random_token(),random_token()
            now=self.clock()
            self.sessions[digest(token)]=Session(owner,csrf,now+3600,now+900)
        return {"cookie":f"{COOKIE}={token}; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=3600","csrf":csrf}
    def _cookie_token(self,cookie):
        if not isinstance(cookie,str) or len(cookie)>4096:raise AuthDenied("Session rejected")
        found=[p.strip().split("=",1)[1] for p in cookie.split(";") if p.strip().startswith(COOKIE+"=")]
        if len(found)!=1 or not valid_token(found[0]):raise AuthDenied("Session rejected")
        return found[0]
    def authorize(self,*,cookie,method,origin=None,csrf=None):
        token=self._cookie_token(cookie)
        with self.lock:
            self._prune()
            session=self.sessions.get(digest(token))
            if session is None:raise AuthDenied("Session rejected")
            if method not in ("GET","HEAD") and (origin!=self.origin or not valid_token(csrf) or not compare_digest(session.csrf,csrf)):
                raise AuthDenied("Session rejected")
            session.idle_until=min(session.expires,self.clock()+900)
            return session.owner
    def logout(self,*,cookie,origin,csrf):
        with self.lock:
            self.authorize(cookie=cookie,method="POST",origin=origin,csrf=csrf)
            self.sessions.pop(digest(self._cookie_token(cookie)),None)
        return f"{COOKIE}=; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=0"
