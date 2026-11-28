"""Private local persistent session store for the offline TLS candidate.
No deployment, external issuer, or production-grade distributed session claim.
"""
import os
import sqlite3
import stat
from pathlib import Path
from contextlib import contextmanager
from hmac import compare_digest
from backend.oidc_boundary import OidcBoundary,AuthDenied,COOKIE,random_token,digest,valid_token

class PersistentBoundary(OidcBoundary):
    def __init__(self,*,session_file,**kwargs):
        super().__init__(**kwargs)
        path=Path(session_file).absolute()
        if os.name!="posix":raise ValueError("Private session file requires POSIX candidate")
        parent=path.parent
        if parent.resolve()!=parent or not parent.is_dir() or parent.stat().st_uid!=os.getuid() or parent.stat().st_mode&0o077:
            raise ValueError("Private session directory required")
        try:
            fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
            os.close(fd)
        except FileExistsError:pass
        self.path=path
        with self._transaction() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS sessions (
               token_hash TEXT PRIMARY KEY CHECK(length(token_hash)=64),
               owner TEXT NOT NULL, csrf TEXT NOT NULL, expires REAL NOT NULL, idle_until REAL NOT NULL)""")
    @contextmanager
    def _transaction(self):
        st=self.path.lstat()
        if not stat.S_ISREG(st.st_mode) or st.st_uid!=os.getuid() or st.st_nlink!=1 or st.st_mode&0o077:
            raise AuthDenied("Private session file refused")
        conn=sqlite3.connect(self.path.as_uri()+"?mode=rw",uri=True,timeout=3)
        try:
            with conn:
                conn.execute("BEGIN IMMEDIATE")
                yield conn
        finally:conn.close()
    def _remove_expired(self,conn):
        now=self.clock()
        conn.execute("DELETE FROM sessions WHERE expires<=? OR idle_until<=?",(now,now))
    def _issue_session(self,owner):
        if owner not in self.owners.values():raise AuthDenied("Identity rejected")
        with self._transaction() as conn:
            self._remove_expired(conn)
            if conn.execute("SELECT count(*) FROM sessions").fetchone()[0]>=128:raise AuthDenied("Session unavailable")
            token,csrf=random_token(),random_token()
            now=self.clock()
            conn.execute("INSERT INTO sessions VALUES(?,?,?,?,?)",(digest(token),owner,csrf,now+3600,now+900))
        return {"cookie":f"{COOKIE}={token}; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=3600","csrf":csrf}
    def _session(self,conn,cookie,method,origin,csrf):
        token=self._cookie_token(cookie)
        self._remove_expired(conn)
        row=conn.execute("SELECT owner,csrf,expires FROM sessions WHERE token_hash=?",(digest(token),)).fetchone()
        if row is None or row[0] not in self.owners.values():raise AuthDenied("Session rejected")
        if method not in ("GET","HEAD") and (origin!=self.origin or not valid_token(csrf) or not compare_digest(row[1],csrf)):
            raise AuthDenied("Session rejected")
        conn.execute("UPDATE sessions SET idle_until=? WHERE token_hash=?",(min(row[2],self.clock()+900),digest(token)))
        return token,row
    def authorize(self,*,cookie,method,origin=None,csrf=None):
        with self._transaction() as conn:
            _,row=self._session(conn,cookie,method,origin,csrf)
            return row[0]
    def csrf_for_session(self,cookie):
        with self._transaction() as conn:
            _,row=self._session(conn,cookie,"GET",None,None)
            return row[1]
    def logout(self,*,cookie,origin,csrf):
        with self._transaction() as conn:
            token,_=self._session(conn,cookie,"POST",origin,csrf)
            conn.execute("DELETE FROM sessions WHERE token_hash=?",(digest(token),))
        return f"{COOKIE}=; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=0"
