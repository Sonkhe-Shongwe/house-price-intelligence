"""Actual pg_dump/pg_restore of the historical schema, invented input only.
No raw dump artifact, original extract re-supply, external storage or network.
"""
import copy
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import tempfile
import unittest
import psycopg
from backend.postgres_ingestion import initialise
from backend.historical_postgres import import_historical
from backend.historical_reader import ROLE,PrivateHistoricalReader,provision_reader,seal_historical
from backend.curated_ingestion_candidate import ImportRefused
from test_historical_import import population

ADMIN=os.environ["HPI_PG_DSN"]
DB="hpi_ingest_fixture"

class HistoricalRecoveryTests(unittest.TestCase):
    def test_sealed_historical_backup_restore_and_fresh_role(self):
        container=os.environ["HPI_PG_CONTAINER"]
        self.assertRegex(container,r"^[a-f0-9]{64}$")
        def docker(*args,**kwargs):
            # Never print raw dump, database exceptions or credentials.
            result=subprocess.run(["docker","exec",*args],stderr=subprocess.DEVNULL,timeout=60,**kwargs)
            self.assertEqual(result.returncode,0,"Disposable recovery command failed")
        def read(password,sealfile,request=None):
            with psycopg.connect(ADMIN,dbname=DB,user=ROLE,password=password,autocommit=True) as conn:
                reader=PrivateHistoricalReader.from_seal_file(conn,sealfile)
                match=reader.search("1 Fictional Court","2025-04-01")
                req=request or {"township_code":"17","class_code":"203","analysis_date":"2025-04-01",
                                "subject":{"address_id":match["address_id"],"building_area_sqft":1600}}
                result=reader.review(req)
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    conn.execute("UPDATE hpi_candidate.sale_transactions SET price_usd_cents=1")
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    conn.execute("SELECT * FROM hpi_candidate.investigations")
                return match,result,req
        with psycopg.connect(ADMIN,autocommit=True) as admin,tempfile.TemporaryDirectory() as private:
            self.assertEqual((admin.info.host,admin.info.dbname,admin.info.user),("127.0.0.1","hpi_fixture","postgres"))
            self.assertIsNone(admin.execute("SELECT 1 FROM pg_database WHERE datname=%s",(DB,)).fetchone())
            self.assertIsNone(admin.execute("SELECT 1 FROM pg_roles WHERE rolname=%s",(ROLE,)).fetchone())
            admin.execute("CREATE DATABASE hpi_ingest_fixture")
            try:
                with psycopg.connect(ADMIN,dbname=DB,autocommit=True) as conn:
                    initialise(conn)
                    args=population()
                    one=import_historical(conn,**args)
                    seal1=seal_historical(conn,**args)
                    revised=copy.deepcopy(args);revised["rows"]["sales"][0]["sale_price"]="525000.02"
                    two=import_historical(conn,**revised)
                    seal2=seal_historical(conn,**revised)
                    self.assertNotEqual(one,two)
                    password=secrets.token_urlsafe(32)
                    provision_reader(conn,password)
                files=[]
                for i,seal in enumerate((seal1,seal2)):
                    path=Path(private)/("seal-"+str(i)+".json")
                    path.write_text(json.dumps(seal));path.chmod(0o600);files.append(path)
                before=[read(password,path) for path in files]
                self.assertEqual(before[0][1]["selected_count"],3)
                self.assertNotEqual(before[0][0]["address_id"],before[1][0]["address_id"])
                del args,revised,seal1,seal2
                with tempfile.TemporaryFile(dir=private) as dump:
                    docker(container,"pg_dump","-U","postgres","-d",DB,"-Fc","--schema=hpi_candidate","--no-owner","--no-acl",stdout=dump)
                    self.assertGreater(dump.tell(),0)
                    # Replace only the disposable database. Credentials/grants
                    # are provisioned from reviewed code, not restored from backup.
                    admin.execute("DROP DATABASE hpi_ingest_fixture")
                    admin.execute("DROP ROLE hpi_historical_reader")
                    admin.execute("CREATE DATABASE hpi_ingest_fixture")
                    dump.seek(0)
                    docker("-i",container,"pg_restore","-U","postgres","-d",DB,"--exit-on-error","--single-transaction","--no-owner","--no-acl",stdin=dump,stdout=subprocess.DEVNULL)
                new_password=secrets.token_urlsafe(32)
                with psycopg.connect(ADMIN,dbname=DB,autocommit=True) as conn:
                    provision_reader(conn,new_password)
                    self.assertEqual(conn.execute("SELECT count(*) FROM hpi_candidate.curated_builds").fetchone()[0],2)
                    self.assertEqual(conn.execute("SELECT count(*) FROM hpi_candidate.source_snapshots").fetchone()[0],8)
                    self.assertEqual(conn.execute("SELECT price_usd_cents FROM hpi_candidate.sale_transactions ORDER BY price_usd_cents").fetchall(),
                                     [(52500001,)]*7+[(52500002,)])
                    self.assertEqual(conn.execute("SELECT count(*) FROM hpi_candidate.investigations").fetchone()[0],0)
                with self.assertRaises(psycopg.OperationalError):
                    psycopg.connect(ADMIN,dbname=DB,user=ROLE,password=password,connect_timeout=3).close()
                for i,path in enumerate(files):
                    self.assertEqual(read(new_password,path,before[i][2]),before[i])
                with self.assertRaises(ImportRefused):
                    read(new_password,files[1],before[0][2])
                with psycopg.connect(ADMIN,dbname=DB,autocommit=True) as conn:
                    conn.execute("UPDATE hpi_candidate.sale_transactions SET price_usd_cents=price_usd_cents+1")
                with self.assertRaisesRegex(ImportRefused,"seal mismatch"):
                    read(new_password,files[0])
            finally:
                admin.execute("DROP DATABASE IF EXISTS hpi_ingest_fixture")
                admin.execute("DROP ROLE IF EXISTS hpi_historical_reader")
