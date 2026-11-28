"""Offline operator configuration and actual loopback TLS transport checks."""
import json
import os
import ssl
import tempfile
import unittest
import urllib.request
from datetime import datetime,timedelta,timezone
from pathlib import Path
from threading import Thread
from ipaddress import ip_address
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm
from backend.oidc_local_qualification import private_directory,configuration,create_server
from backend.oidc_identity_http import ORIGIN


class LocalQualificationTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        self.config=dict(issuer="https://example-fixture.us.auth0.com/",client_id="fixture",
            jwks={"keys":[dict(json.loads(RSAAlgorithm.to_jwk(key.public_key())),
                kid="pinned",use="sig",alg="RS256")]},
            owner_by_subject={"auth0|alice":"owner-a"})
        self.write("identity.json",json.dumps(self.config).encode())
        subject=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,"127.0.0.1")])
        now=datetime.now(timezone.utc)
        cert=(x509.CertificateBuilder().subject_name(subject).issuer_name(subject)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now-timedelta(minutes=1)).not_valid_after(now+timedelta(days=1))
            .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ip_address("127.0.0.1"))]),critical=False)
            .sign(key,hashes.SHA256()))
        self.write("localhost.crt",cert.public_bytes(serialization.Encoding.PEM))
        self.write("localhost.key",key.private_bytes(serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))

    def write(self,name,data):
        p=self.root/name
        p.write_bytes(data)
        p.chmod(0o600)

    def test_configuration_scope_changes_and_unsafe_files_refused(self):
        first=configuration(self.root)["session_file"]
        self.config["owner_by_subject"]={"auth0|bob":"owner-a"}
        self.write("identity.json",json.dumps(self.config).encode())
        self.assertNotEqual(first,configuration(self.root)["session_file"])
        (self.root/"identity.json").chmod(0o644)
        with self.assertRaises(ValueError):configuration(self.root)
        self.root.chmod(0o755)
        try:
            with self.assertRaises(ValueError):private_directory(self.root)
        finally:self.root.chmod(0o700)

    def test_real_tls_listener_no_provider_or_database(self):
        with create_server(self.root,"x"*48) as server:
            self.assertEqual(server.server_address,("127.0.0.1",8766))
            thread=Thread(target=server.serve_forever,daemon=True)
            thread.start()
            try:
                context=ssl.create_default_context(cafile=str(self.root/"localhost.crt"))
                opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),
                    urllib.request.HTTPSHandler(context=context))
                with opener.open(ORIGIN+"/",timeout=5) as response:
                    self.assertEqual(response.status,200)
                    self.assertIn(b"HPI identity qualification",response.read())
            finally:
                server.shutdown()
                thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
