"""Explicit operator-only loopback identity qualification. No database access.

Run on a trusted POSIX host, outside the repository, with a private directory
and a locally trusted certificate. Never print the callback URL or secrets.
"""
import getpass
import hashlib
import json
import os
from pathlib import Path
import ssl
import stat
import sys
from wsgiref.simple_server import make_server,WSGIRequestHandler,WSGIServer
from backend.oidc_identity_http import identity_only_application,ORIGIN
from backend.oidc_provider_config import prepare_auth0,CALLBACK


class QuietTLSHandler(WSGIRequestHandler):
    def get_environ(self):
        env=super().get_environ()
        env["wsgi.url_scheme"]="https"
        env["HTTPS"]="on"
        return env

    def log_message(self,*args):
        pass


class QuietServer(WSGIServer):
    def handle_error(self,request,client_address):
        pass


def _unique(pairs):
    result={}
    for k,v in pairs:
        if k in result:raise ValueError("Duplicate configuration key")
        result[k]=v
    return result


def private_directory(path):
    root=Path(path).absolute()
    if (os.name!="posix" or root.resolve(strict=True)!=root or not root.is_dir()
        or root.stat().st_uid!=os.getuid() or root.stat().st_mode&0o077):
        raise ValueError("Private operator directory required")
    return root


def _file(root,name):
    path=root/name
    st=path.lstat()
    if (not stat.S_ISREG(st.st_mode) or st.st_uid!=os.getuid()
        or st.st_nlink!=1 or st.st_mode&0o077 or st.st_size>65536):
        raise ValueError("Private operator file required")
    return path


def configuration(root):
    config=json.loads(_file(root,"identity.json").read_text(encoding="utf-8"),object_pairs_hook=_unique)
    if not isinstance(config,dict) or set(config)!={"issuer","client_id","jwks","owner_by_subject"}:
        raise ValueError("Identity configuration refused")
    # Different issuer/client/owner mappings get different session stores.
    # A configuration change must not silently reassign a prior session.
    scope=json.dumps([config["issuer"],config["client_id"],config["owner_by_subject"]],
        sort_keys=True,separators=(",",":")).encode()
    session=root/("sessions-"+hashlib.sha256(scope).hexdigest()+".sqlite")
    return dict(config,redirect_uri=CALLBACK,session_file=session)


def create_server(root,client_secret):
    root=private_directory(root)
    config=configuration(root)
    cert,key=_file(root,"localhost.crt"),_file(root,"localhost.key")
    context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version=ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(cert,key)
    boundary,exchange=prepare_auth0(**config,client_secret=client_secret)
    server=make_server("127.0.0.1",8766,identity_only_application(boundary,exchange,
            diagnostic=lambda category: print("Identity callback rejected: "+category,flush=True)),
        server_class=QuietServer,handler_class=QuietTLSHandler)
    try:
        server.socket=context.wrap_socket(server.socket,server_side=True)
    except Exception:
        server.server_close()
        raise
    return server


def main():
    if len(sys.argv)!=3 or sys.argv[1]!="--qualify-auth0" or not sys.stdin.isatty():
        print("Explicit interactive identity qualification required",file=sys.stderr)
        return 1
    try:
        root=private_directory(sys.argv[2])
        configuration(root)
        secret=getpass.getpass("Auth0 client secret (not echoed): ")
        with create_server(root,secret) as server:
            del secret
            print("Identity-only qualification at "+ORIGIN,flush=True)
            print("Use a trusted local certificate. Stop with Ctrl+C.",flush=True)
            server.serve_forever()
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception:
        print("Identity qualification configuration or startup refused",file=sys.stderr)
        return 1


if __name__=="__main__":
    raise SystemExit(main())
