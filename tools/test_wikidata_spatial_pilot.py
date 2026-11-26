"""Invented spatial observations only; no public source requests."""
import base64
from email.message import Message
import hashlib
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from tools import wikidata_spatial_pilot as p
from tools import world_bank_pilot as transport


def row(qid="Q123", lat="-26.2", lon="28.0", label="Fictional School"):
    return {"facility": {"type": "uri", "value": "http://www.wikidata.org/entity/"+qid},
            "name": {"type": "literal", "xml:lang": "en", "value": label},
            "lat": {"type": "literal", "datatype": p.XSD+"double", "value": lat},
            "lon": {"type": "typed-literal", "datatype": p.XSD+"decimal", "value": lon}}


def raw(*rows):
    return json.dumps({"head":{"vars":["facility","name","lat","lon"]},
                       "results":{"bindings":list(rows)}}).encode()


class FakeResponse:
    status = 200
    def __init__(self, mime, body=b"{}"):
        self.body = body
        self.headers = Message()
        self.headers["Content-Type"] = mime
        self.headers["Content-Length"] = str(len(body))
    def read(self, n):
        return self.body[:n]


class SpatialTests(unittest.TestCase):
    def root(self, temp):
        root = Path(temp)
        for name in ("01_Source_Catalogue","02_Raw_Data","07_Reports"):
            (root/name).mkdir()
        return root

    def test_fixed_request_and_shared_transport(self):
        u = urlsplit(p.REQUEST)
        self.assertEqual(u.path, "/sparql")
        self.assertEqual(parse_qs(u.query), {"query":[p.QUERY],"format":["json"]})
        self.assertTrue(p.QUERY.endswith("LIMIT 25"))
        self.assertEqual(p.SpatialHTTPS.HOSTNAME, "query-next.wikidata.org")
        self.assertEqual(transport.PinnedHTTPS.HOSTNAME, "api.worldbank.org")
        with patch.object(socket,"getaddrinfo") as dns:
            with self.assertRaises(transport.Refused):
                transport.public_addresses("not-approved.example")
            dns.assert_not_called()
            dns.return_value=[(socket.AF_INET,socket.SOCK_STREAM,6,"",("127.0.0.1",443))]
            with self.assertRaises(transport.Refused):
                transport.public_addresses(p.HOST)
            dns.assert_called_once_with(p.HOST,443,type=socket.SOCK_STREAM,proto=socket.IPPROTO_TCP)
        self.assertEqual(transport.bounded_body(FakeResponse(p.MEDIA[0]),p.MEDIA),b"{}")
        with self.assertRaises(transport.Refused):
            transport.bounded_body(FakeResponse(p.MEDIA[0]))
        with self.assertRaises(transport.Refused):
            transport.bounded_body(FakeResponse("text/html"),p.MEDIA)

    def test_worker_exact_scope(self):
        class Sender:
            def __init__(self): self.messages=[]
            def send_bytes(self,data): self.messages.append(data)
            def close(self): pass
        sender=Sender()
        with patch.object(p,"SpatialHTTPS") as conn, patch.object(p,"remaining",return_value=10):
            conn.return_value.getresponse.return_value=FakeResponse(p.MEDIA[0])
            p.network_worker(1, 123, sender)
            conn.return_value.request.assert_called_once_with("GET",p.REQUEST,headers={
                "Accept":p.MEDIA[0],"Accept-Encoding":"identity","Connection":"close","User-Agent":p.AGENT})
            self.assertEqual(sender.messages,[b"S{}"])
        sender=Sender()
        with patch.object(p,"SpatialHTTPS") as conn:
            p.network_worker(2,123,sender)
            conn.assert_not_called()
            self.assertTrue(sender.messages[0].startswith(b"E"))

    def test_valid_and_axis_order_distances(self):
        rows=p.distances(p.parse(raw(row(),row("Q124",lat="-26.1"),row("Q125",lon="28.1"))))
        by_id={r["qid"]:r for r in rows}
        self.assertEqual(by_id["Q123"]["distance_m"],0)
        # Independent approximate WGS84 local arc ranges (0.1 degree).
        self.assertTrue(11070 < by_id["Q124"]["distance_m"] < 11100)
        self.assertTrue(9980 < by_id["Q125"]["distance_m"] < 10010)
        self.assertEqual(rows[0]["qid"],"Q123")

    def test_invalid_schema_coordinates_duplicates(self):
        extra=row(); extra["email"]={"type":"literal","value":"x"}
        lang=row(); lang["name"]["xml:lang"]="fr"
        datatype=row(); datatype["lat"]["datatype"]=p.XSD+"string"
        for payload in (raw(),raw(row(lat="28.0",lon="-26.2")),raw(row(lat="-26.401")),
                        raw(row(lon="28.301")),raw(row(lat="NaN")),raw(row(),row(lat="-26.1")),
                        raw(row(qid="bad")),raw(row(label="")),raw(extra),raw(lang),raw(datatype),
                        b"{}",b"x"*(p.CAP+1),raw(row()).replace(b'"head":',b'"head": {}, "head":')):
            with self.subTest(payload=payload),self.assertRaises(transport.Refused):
                p.parse(payload)

    def test_exact_record_limit(self):
        self.assertEqual(len(p.parse(raw(*(row("Q"+str(i)) for i in range(1,26))))),25)
        with self.assertRaises(transport.Refused):
            p.parse(raw(*(row("Q"+str(i)) for i in range(1,27))))

    def test_atomic_bundle_and_separate_attempt(self):
        with tempfile.TemporaryDirectory() as temp:
            root=self.root(temp)
            previous=root/"02_Raw_Data"/transport.ATTEMPT
            previous.mkdir()
            payload=raw(row(),row("Q124",lat="-26.1"))
            calls=[]
            def fetch():
                calls.append(1)
                self.assertTrue((root/"02_Raw_Data"/p.ATTEMPT/"dispatch-1.json").is_file())
                return payload
            result=p.execute(root,fetch)
            target=root/"02_Raw_Data"/p.ATTEMPT
            bundle=json.loads((target/"validated.json").read_text())
            self.assertEqual(result["records"],2)
            self.assertEqual(result["sha256"],hashlib.sha256(payload).hexdigest())
            self.assertEqual(base64.b64decode(bundle["body_base64"]),payload)
            self.assertFalse(bundle["registered"])
            self.assertIsNone(bundle["source_vintage"])
            self.assertTrue(previous.is_dir())
            with self.assertRaisesRegex(transport.Refused,"consumed"):
                p.execute(root,fetch)
            self.assertEqual(calls,[1])

    def test_failure_no_publication_or_replay(self):
        with tempfile.TemporaryDirectory() as temp:
            root=self.root(temp)
            calls=[]
            def fetch():
                calls.append(1)
                return raw()
            with self.assertRaises(transport.Refused):
                p.execute(root,fetch)
            self.assertFalse((root/"02_Raw_Data"/p.ATTEMPT/"validated.json").exists())
            with self.assertRaises(transport.Refused):
                p.execute(root,fetch)
            self.assertEqual(calls,[1])


if __name__ == "__main__":
    unittest.main()
