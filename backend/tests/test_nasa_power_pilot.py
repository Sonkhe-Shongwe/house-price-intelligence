"""Synthetic NASA tests only; no network or real records."""
from email.message import Message
import hashlib
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from tools import nasa_power_pilot as p
from tools import world_bank_pilot as transport


def fixture():
    lines = [p.BEGIN, "NASA/POWER Source Native Resolution Daily Data", p.DATES,
             "Location: latitude -26.2 longitude 28.0",
             "Elevation from MERRA-2: Average for 0.5 x 0.625 degree lat/lon region = 1000 meters",
             "The value for missing source data that cannot be computed or is outside of the sources availability range: -999",
             "Parameter(s):",
             p.PARAM+" CERES SYN1deg All Sky Surface Shortwave Downward Irradiance (kW-hr/m^2/day)",
             p.END, ",".join(p.HEADER)]
    return ("\n".join(lines + ["2024,1,%d,%d" % (d,d) for d in range(1,8)])+"\n").encode()


class FakeResponse:
    status=200
    def __init__(self,media,body=b"abc",**extra):
        self.body=body
        self.headers=Message()
        self.headers["Content-Type"]=media
        self.headers["Content-Length"]=str(len(body))
        for key,value in extra.items():
            self.headers[key.replace("_","-")]=value
    def read(self,n):
        return self.body[:n]


class NasaTests(unittest.TestCase):
    def root(self,temp):
        root=Path(temp)
        for name in ("01_Source_Catalogue","02_Raw_Data","07_Reports"):
            (root/name).mkdir()
        return root

    def test_documented_header_variants_and_mean(self):
        raw=fixture()
        for data in (raw,b"\xef\xbb\xbf"+raw.replace(b"\n",b"\r\n"),
                     raw.replace(b"kW-hr/m^2/day",b"kWh/m^2/day"),
                     raw.replace(b"Source Native Resolution Daily Data",b"CERES/MERRA2 Native Resolution Daily Data")):
            r=p.parse(data)
            self.assertEqual(r["mean_kwh_m2_day"],"4.000000")
            self.assertEqual(len(r["records"]),7)
            self.assertFalse(r["reported_location"]["grid_centre_verified"])

    def test_metadata_refusals(self):
        raw=fixture()
        for data,code in ((raw.replace(b"in UTC",b"in LST"),"DATE_UTC"),
                          (raw.replace(b"kW-hr/m^2/day",b"MJ/m^2/day"),"UNIT"),
                          (raw.replace(b"latitude -26.2",b"latitude 1.0"),"LOCATION"),
                          (raw.replace(b"-999\n",b"-1\n"),"MISSING_METADATA"),
                          (raw.replace(b"Parameter(s):",b"unexpected private text"),"METADATA"),
                          (raw.replace(b"-END HEADER-",b"missing"),"PREAMBLE")):
            with self.subTest(code=code),self.assertRaisesRegex(p.CsvRefused,code):
                p.parse(data)

    def test_date_values_and_projection(self):
        raw=fixture()
        for data,code in ((raw.replace(b"2024,1,7,7\n",b""),"ROW_COUNT"),
                          (raw.replace(b"2024,1,7,7",b"2024,1,6,7"),"DUPLICATE"),
                          (raw.replace(b"2024,1,7,7",b"2024,1,8,7"),"DATE"),
                          (raw.replace(b"2024,1,7,7",b"2024,1,7,-999"),"MISSING_VALUE"),
                          (raw.replace(b"2024,1,7,7",b"2024,1,7,NaN"),"VALUE"),
                          (raw.replace(b"2024,1,7,7",b"2024,1,7,99"),"VALUE"),
                          (raw.replace(b"YEAR,MO,DY,",b"YEAR,MO,DY,EXTRA,"),"COLUMNS")):
            with self.subTest(code=code),self.assertRaisesRegex(p.CsvRefused,code):
                p.parse(data)

    def test_scope_and_transport(self):
        self.assertEqual(p.REQUEST,"/api/temporal/daily/point?parameters=ALLSKY_SFC_SW_DWN&community=RE&longitude=28.0&latitude=-26.2&start=20240101&end=20240107&format=CSV&time-standard=UTC")
        with patch.object(socket,"getaddrinfo") as dns:
            dns.return_value=[(socket.AF_INET,socket.SOCK_STREAM,6,"",("127.0.0.1",443))]
            with self.assertRaises(transport.Refused):
                transport.public_addresses(p.HOST)
            dns.assert_called_once_with(p.HOST,443,type=socket.SOCK_STREAM,proto=socket.IPPROTO_TCP)
        for media in p.MEDIA:
            self.assertEqual(transport.bounded_body(FakeResponse(media),p.MEDIA),b"abc")
        for response in (FakeResponse("text/html"),FakeResponse("text/csv",b"x"*(p.CAP+1)),
                         FakeResponse("text/csv",Content_Encoding="gzip")):
            with self.assertRaises(transport.Refused):
                transport.bounded_body(response,p.MEDIA)

    def test_exact_network_worker(self):
        class Sender:
            def __init__(self): self.messages=[]
            def send_bytes(self,data): self.messages.append(data)
            def close(self): pass
        sender=Sender()
        with patch.object(p,"NasaHTTPS") as conn,patch.object(p,"remaining",return_value=10):
            conn.return_value.getresponse.return_value=FakeResponse("text/csv")
            p.network_worker(1,123,sender)
            conn.return_value.request.assert_called_once_with("GET",p.REQUEST,headers={
                "Accept":"text/csv, application/csv","Accept-Encoding":"identity",
                "Connection":"close","User-Agent":"HPI-bounded-research/1.0"})
            self.assertEqual(sender.messages,[b"Sabc"])
        with patch.object(p,"NasaHTTPS") as conn:
            p.network_worker(2,123,sender)
            conn.assert_not_called()
            self.assertEqual(sender.messages[-1],b"ETRANSPORT")

    def test_diagnostics_never_emit_rejected_content(self):
        raw=fixture().replace(b"Parameter(s):",b"PRIVATE_VALUE_123")
        diag=p.safe_diagnostic(raw,"METADATA")
        self.assertEqual(diag["sha256"],hashlib.sha256(raw).hexdigest())
        self.assertEqual(diag["bytes"],len(raw))
        self.assertTrue(diag["flags"]["expected_columns"])
        self.assertNotIn("PRIVATE_VALUE_123",json.dumps(diag))
        self.assertIsNone(p.safe_diagnostic(b"x"*(p.CAP+1),"BODY_LIMIT")["bytes"])
        self.assertFalse(p.safe_diagnostic(b"\xff","UTF8")["flags"]["utf8"])

    def test_atomic_bundle_and_replay(self):
        with tempfile.TemporaryDirectory() as temp:
            root=self.root(temp)
            calls=[]
            def fetch():
                calls.append(1)
                self.assertTrue((root/"02_Raw_Data"/p.ATTEMPT/"dispatch-1.json").is_file())
                return fixture()
            result=p.execute(root,fetch)
            target=root/"02_Raw_Data"/p.ATTEMPT
            bundle=json.loads((target/"validated.json").read_text(encoding="utf-8"))
            self.assertEqual(result["status"],"PASS")
            self.assertEqual(bundle["mean_kwh_m2_day"],"4.000000")
            self.assertFalse(bundle["registered"])
            self.assertEqual(result["sha256"],hashlib.sha256(fixture()).hexdigest())
            with self.assertRaisesRegex(transport.Refused,"consumed"):
                p.execute(root,fetch)
            self.assertEqual(calls,[1])

    def test_failed_attempt_persists_only_diagnostic(self):
        with tempfile.TemporaryDirectory() as temp:
            root=self.root(temp)
            raw=fixture().replace(b"Parameter(s):",b"PRIVATE_VALUE_123")
            result=p.execute(root,lambda:raw)
            target=root/"02_Raw_Data"/p.ATTEMPT
            self.assertEqual(result["reason"],"METADATA")
            self.assertFalse((target/"validated.json").exists())
            self.assertFalse((target/"validated.staging.json").exists())
            self.assertNotIn("PRIVATE_VALUE_123",(target/"refusal.json").read_text())
            with self.assertRaisesRegex(transport.Refused,"consumed"):
                p.execute(root,lambda:self.fail("replay"))

    def test_transport_refusal_has_no_invented_body_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root=self.root(temp)
            def fetch():
                raise transport.Refused("request deadline exceeded")
            result=p.execute(root,fetch)
            self.assertEqual(result["reason"],"TRANSPORT")
            self.assertIsNone(result["sha256"])
            self.assertIsNone(result["bytes"])


if __name__ == "__main__":
    unittest.main()
