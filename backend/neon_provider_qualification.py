"""Bounded operator-only HTTPS qualification of the invented Neon buyer path.

No owner DSN, role activation, owner registration, automatic restart, real data
or deployment. Existing Auth0 configuration and independently held seal reused.
"""
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
from time import time,monotonic
import getpass
import hashlib
import re
import ssl
import sys
from wsgiref.simple_server import make_server
from backend.oidc_local_qualification import (private_directory,configuration,_file,
    QuietTLSHandler,QuietServer)
from backend.oidc_provider_config import prepare_auth0
from backend.oidc_identity_http import ORIGIN,neon_buyer_identity_application
from backend.neon_provider_buyer import MODE,open_neon_provider_buyer,NeonProviderBuyer
from backend.neon_preflight import HOST
from backend.react_assets import load_react_assets

MAX_WINDOW=3600


def deadline(value,*,clock=time,steady=monotonic):
    if not isinstance(value,str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z",value):
        raise ValueError("Explicit UTC deadline required")
    end=datetime.strptime(value,"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
    remaining=end-clock()
    if not 0<remaining<=MAX_WINDOW:
        raise ValueError("Window must be current and at most one hour")
    stop=steady()+remaining
    return lambda: min(end-clock(),stop-steady())


def _outside_checkout(path):
    repo=Path(__file__).resolve().parents[1]
    path=Path(path).absolute()
    if path.resolve().is_relative_to(repo):
        raise ValueError("Private files must be outside the repository")
    return path


def provider_configuration(root,end):
    config=configuration(root)
    if len(config["owner_by_subject"])!=1:
        raise ValueError("Single approved owner required")
    # Do not reuse identity-only sessions or another acceptance window's sessions.
    old=config["session_file"]
    scope=hashlib.sha256((old.name+"|"+end).encode("ascii")).hexdigest()
    config["session_file"]=root/("buyer-window-"+scope+".sqlite")
    return config


def bounded_application(app,remaining):
    def guarded(env,start):
        if remaining()<=0:
            body=b'{"error":"qualification_window_closed"}'
            start("503 Service Unavailable",[("Content-Type","application/json"),
                ("Content-Length",str(len(body))),("Cache-Control","no-store"),
                ("X-Content-Type-Options","nosniff")])
            return [body]
        return app(env,start)
    return guarded


class QualificationHandler(QuietTLSHandler):
    def setup(self):
        self.request.settimeout(10)
        super().setup()


@contextmanager
def open_server(root,seal_path,end,client_secret,environ,*,remaining):
    root=private_directory(_outside_checkout(root))
    seal_path=_outside_checkout(seal_path)
    if remaining()<=0 or environ.get("HPI_NEON_MODE")!=MODE:
        raise ValueError("Approved window required")
    config=provider_configuration(root,end)
    tls=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.minimum_version=ssl.TLSVersion.TLSv1_2
    tls.load_cert_chain(_file(root,"localhost.crt"),_file(root,"localhost.key"))
    boundary,exchange=prepare_auth0(**config,client_secret=client_secret)
    NeonProviderBuyer._identity_owners(boundary)
    assets=load_react_assets()
    if remaining()<=0:
        raise ValueError("Window closed")
    with open_neon_provider_buyer(environ,seal_path,boundary) as service:
        if remaining()<=0:
            raise ValueError("Window closed")
        app=neon_buyer_identity_application(boundary,exchange,service,assets)
        with make_server("127.0.0.1",8766,bounded_application(app,remaining),
                server_class=QuietServer,handler_class=QualificationHandler) as server:
            server.socket=tls.wrap_socket(server.socket,server_side=True,do_handshake_on_connect=False)
            server.timeout=0.5
            yield server


def main():
    if len(sys.argv)!=5 or sys.argv[1]!="--qualify-neon-buyer" or not sys.stdin.isatty():
        print("Explicit interactive buyer qualification required",file=sys.stderr)
        return 1
    try:
        root=private_directory(_outside_checkout(sys.argv[2]))
        seal=_outside_checkout(sys.argv[3])
        end=sys.argv[4]
        remaining=deadline(end)
        provider_configuration(root,end)
        from backend.historical_seal_config import load_historical_seal
        from backend.neon_synthetic_seed import fixture_plan
        if load_historical_seal(seal)["build_id"]!=fixture_plan()[0]:
            raise ValueError("Only invented source permitted")
        host=getpass.getpass("Approved direct development hostname (not echoed): ")
        if not HOST.fullmatch(host) or "-pooler" in host:
            raise ValueError("Direct development hostname required")
        secret=getpass.getpass("Auth0 client secret (not echoed): ")
        settings={"HPI_NEON_MODE":MODE,"HPI_NEON_DEVELOPMENT_HOST":host,
            "HPI_NEON_READER_DSN":getpass.getpass("Restricted reader DSN (not echoed): "),
            "HPI_NEON_BUYER_DSN":getpass.getpass("Restricted buyer DSN (not echoed): ")}
        with open_server(root,seal,end,secret,settings,remaining=remaining) as server:
            del secret,settings
            print("Invented buyer qualification: "+ORIGIN,flush=True)
            print("Sign in, complete the buyer journey, sign out and stop with Ctrl+C.",flush=True)
            while remaining()>0:
                server.handle_request()
        print("Qualification window closed; restricted connections closed.",flush=True)
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception:
        print("Buyer qualification configuration or startup refused",file=sys.stderr)
        return 1


if __name__=="__main__":
    raise SystemExit(main())
