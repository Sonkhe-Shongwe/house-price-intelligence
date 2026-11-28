"""Private operator-held historical integrity seal, not a release approval.
Only a bounded, owner-controlled POSIX file is accepted. Never log seal values.
"""
import json
import os
from pathlib import Path
import re
import stat
from backend.curated_ingestion_candidate import ImportRefused

def _unique(pairs):
    result={}
    for k,v in pairs:
        if k in result:
            raise ValueError("Duplicate seal key")
        result[k]=v
    return result

def load_historical_seal(path):
    try:
        if os.name!="posix":raise ValueError
        p=Path(path).absolute()
        parent=p.parent
        # No symlinked path components; final directory and file are private.
        if parent.resolve(strict=True)!=parent:raise ValueError
        flags=os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW
        directory=os.open(parent,flags)
        try:
            st=os.fstat(directory)
            if st.st_uid!=os.getuid() or st.st_mode&0o077:raise ValueError
            fd=os.open(p.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=directory)
            with os.fdopen(fd,"rb") as stream:
                st=os.fstat(stream.fileno())
                if not stat.S_ISREG(st.st_mode) or st.st_uid!=os.getuid() or st.st_nlink!=1 or st.st_mode&0o077 or st.st_size>4096:
                    raise ValueError
                raw=stream.read(4097)
        finally:os.close(directory)
        if len(raw)>4096:raise ValueError
        seal=json.loads(raw.decode("utf-8"),object_pairs_hook=_unique)
        if (not isinstance(seal,dict) or set(seal)!={"build_id","relational_sha256"}
            or not isinstance(seal["build_id"],str) or not re.fullmatch(r"historical-[a-f0-9]{64}",seal["build_id"])
            or not isinstance(seal["relational_sha256"],str) or not re.fullmatch(r"[a-f0-9]{64}",seal["relational_sha256"])):
            raise ValueError
        return seal
    except (OSError,ValueError,TypeError,UnicodeError,RecursionError):
        raise ImportRefused("Private historical seal configuration refused") from None
