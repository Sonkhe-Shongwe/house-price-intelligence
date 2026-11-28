"""Validate public package audit results; never include environment paths or secrets."""
import json
from pathlib import Path
import re
import sys


def name(value):
    if not isinstance(value,str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*",value):
        raise ValueError("invalid package name")
    return re.sub(r"[-_.]+","-",value).lower()


def version(value):
    if not isinstance(value,str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.!+_-]*",value):
        raise ValueError("invalid version")
    return value


def inventory(rows):
    result={}
    for row in rows:
        key=name(row["name"])
        if key in result:
            raise ValueError("duplicate package")
        result[key]=version(row["version"])
    return result


def summarize(installed, audit, exit_code):
    expected=inventory(installed)
    # The isolated environment intentionally excludes the auditor and Playwright.
    if not {"psycopg","psycopg-binary","psycopg-pool","pyjwt","cryptography"} <= expected.keys():
        raise ValueError("runtime inventory incomplete")
    if not isinstance(audit,dict) or not isinstance(audit.get("dependencies"),list):
        raise ValueError("audit unavailable")
    observed=inventory(audit["dependencies"])
    if observed!=expected:
        raise ValueError("audit inventory mismatch")
    findings=[]
    for row in audit["dependencies"]:
        if "skip_reason" in row or not isinstance(row.get("vulns"),list):
            raise ValueError("dependency not audited")
        ids=[]
        for item in row["vulns"]:
            ident=item["id"]
            if not isinstance(ident,str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}",ident):
                raise ValueError("invalid advisory ID")
            ids.append(ident)
        if ids:
            findings.append({"name":name(row["name"]),"version":version(row["version"]),
                             "advisory_ids":sorted(set(ids))})
    return {"status":"passed" if exit_code==0 and not findings else "blocked",
            "scope":"resolved Python 3.12 runtime packages and installed bootstrap tools; known advisories only",
            "package_count":len(expected),"inventory":dict(sorted(expected.items())),
            "affected_packages":len(findings),"advisories":sum(len(row["advisory_ids"]) for row in findings),
            "findings":sorted(findings,key=lambda row:row["name"]),"audit_exit_code":exit_code}


def main():
    target=Path(sys.argv[3])
    try:
        result=summarize(json.loads(Path(sys.argv[1]).read_text()),
                         json.loads(Path(sys.argv[2]).read_text()),int(sys.argv[4]))
    except (ValueError,KeyError,TypeError,OSError):
        result={"status":"blocked","reason":"audit_or_inventory_unavailable_or_incomplete"}
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    return 0 if result["status"]=="passed" else 1


if __name__=="__main__":
    raise SystemExit(main())
