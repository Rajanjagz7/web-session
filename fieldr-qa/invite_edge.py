"""Boundary / negative / security edge-case sweep: Invite, User Groups, User create.
Target: rajanjagz7.dev.fieldr.app dev tenant, authorized by the tenant owner (this conversation).
Read-mostly: creates a bounded number of clearly-labelled QA_EDGE_* records; no real payment or SMS-triggering data.
"""
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fieldr_seed as f  # noqa: E402

api = f.Fieldr()
results = []


def probe(label, method, path, **kw):
    code, body = api.call(method, path, **kw)
    row = {"label": label, "method": method, "path": path, "code": code, "message": body.get("message"), "data_preview": json.dumps(body.get("data"), default=str)[:200]}
    results.append(row)
    print(f"{label:46} {code:>4} {str(body.get('message'))[:90]}")
    return code, body


REAL_ROLE = api.list("role", 10)
ROLE_USER = next(r["_id"] for r in REAL_ROLE if r["roleName"] == "User")
ROLE_ADMIN = next((r["_id"] for r in REAL_ROLE if r["roleName"] == "companyAdmin"), None)
print("roles:", [(r["roleName"], r["_id"]) for r in REAL_ROLE])

print("\n== INVITE: boundary + negative ==")
probe("empty body", "POST", "/invite/create", json={})
probe("email empty string", "POST", "/invite/create", json={"email": ""})
probe("email whitespace only", "POST", "/invite/create", json={"email": "   "})
probe("email no @", "POST", "/invite/create", json={"email": "not-an-email"})
probe("email missing tld", "POST", "/invite/create", json={"email": "a@b"})
probe("email double dot", "POST", "/invite/create", json={"email": "a..b@yopmail.com"})
probe("email leading space", "POST", "/invite/create", json={"email": " qa.edge1@yopmail.com"})
probe("email 254+ char local part", "POST", "/invite/create", json={"email": ("a" * 250) + "@yopmail.com"})
probe("email unicode homoglyph", "POST", "/invite/create", json={"email": "qa.аdge@yopmail.com"})  # Cyrillic a
probe("email null byte", "POST", "/invite/create", json={"email": "qa.edge\x00@yopmail.com"})
probe("email XSS payload", "POST", "/invite/create", json={"email": "<script>alert(1)</script>@yopmail.com"})
probe("email NoSQL operator", "POST", "/invite/create", json={"email": {"$ne": None}})
probe("email as array", "POST", "/invite/create", json={"email": ["a@yopmail.com", "b@yopmail.com"]})
probe("email as number", "POST", "/invite/create", json={"email": 12345})
probe("roleId missing (default role?)", "POST", "/invite/create", json={"email": "qa.edge.norole@yopmail.com"})
probe("roleId bogus string", "POST", "/invite/create", json={"email": "qa.edge.badrole@yopmail.com", "roleId": "not-an-objectid"})
probe("roleId privilege escalation -> companyAdmin", "POST", "/invite/create", json={"email": "qa.edge.escalate@yopmail.com", "roleId": ROLE_ADMIN})
c1, b1 = probe("valid invite #1", "POST", "/invite/create", json={"email": "qa.edge.dup@yopmail.com", "roleId": ROLE_USER})
probe("duplicate invite (same email)", "POST", "/invite/create", json={"email": "qa.edge.dup@yopmail.com", "roleId": ROLE_USER})
probe("invite to existing user's email", "POST", "/invite/create", json={"email": "qa.user342075@yopmail.com", "roleId": ROLE_USER})
_, admin_body = api.call("GET", "/user/get/6aae2a64d77d9ef26bdcf123")
probe("invite to workspace owner's own email", "POST", "/invite/create", json={"email": admin_body.get("data", {}).get("email", "rajanjagz7@yopmail.com"), "roleId": ROLE_USER})

if c1 == 200:
    inv_id = b1["data"]["_id"]
    probe("resend valid invite", "POST", f"/invite/{inv_id}/resend", json={})
    probe("resend nonexistent invite id (fake ObjectId)", "POST", "/invite/000000000000000000000000/resend", json={})
    probe("resend malformed id", "POST", "/invite/not-an-id/resend", json={})
    probe("verify own invite id (should need no auth normally)", "GET", f"/invite/verify/{inv_id}")
    probe("verify with SQLi-style id", "GET", "/invite/verify/' OR '1'='1")
    probe("get invite by id", "GET", f"/invite/{inv_id}")
    probe("get invite: sequential id guess (IDOR probe)", "GET", "/invite/000000000000000000000001")
    probe("accept with garbage token", "POST", "/invite/accept", json={"token": "garbage-token-1234"})
    probe("accept with empty token", "POST", "/invite/accept", json={"token": ""})

print("\n== USER GROUP: boundary + negative ==")
probe("empty body", "POST", "/user/group/create", json={})
probe("name empty string", "POST", "/user/group/create", json={"name": ""})
probe("name whitespace only", "POST", "/user/group/create", json={"name": "   "})
probe("name 1 char", "POST", "/user/group/create", json={"name": "A"})
probe("name 255 chars", "POST", "/user/group/create", json={"name": "N" * 255})
probe("name 256 chars", "POST", "/user/group/create", json={"name": "N" * 256})
probe("name 2000 chars", "POST", "/user/group/create", json={"name": "N" * 2000})
probe("name XSS payload", "POST", "/user/group/create", json={"name": "<img src=x onerror=alert(1)>QA_EDGE"})
probe("name with only emoji", "POST", "/user/group/create", json={"name": "\U0001f600\U0001f600\U0001f600"})
gc, gb = probe("valid group (for dup test)", "POST", "/user/group/create", json={"name": "QA_EDGE Duplicate Test Crew"})
probe("duplicate group name", "POST", "/user/group/create", json={"name": "QA_EDGE Duplicate Test Crew"})
probe("group with nonexistent user id", "POST", "/user/group/create", json={"name": "QA_EDGE Bad Members", "users": ["000000000000000000000000"]})
probe("group with malformed user id", "POST", "/user/group/create", json={"name": "QA_EDGE Bad Members 2", "users": ["not-an-id"]})
real_uid = api.list("user", 5)[0]["_id"]
probe("group with duplicate member twice", "POST", "/user/group/create", json={"name": "QA_EDGE Dup Member", "users": [real_uid, real_uid]})
if gc == 200:
    gid = gb["data"]["_id"]
    probe("update group: add same member twice via update", "PUT", f"/user/group/update/{gid}", json={"users": [real_uid, real_uid]})
    probe("update nonexistent group", "PUT", "/user/group/update/000000000000000000000000", json={"name": "x"})
    probe("delete nonexistent group", "DELETE", "/user/group/delete/000000000000000000000000")
    probe("get group by malformed id", "GET", "/user/group/list/not-an-id")

print("\n== USER CREATE: boundary + negative (via API, no UI seat-limit redirect) ==")
probe("empty body", "POST", "/user/create", json={})
probe("firstName 2 chars (below 3 min seen in Customer)", "POST", "/user/create", json={"firstName": "Al", "lastName": "Edge", "email": "qa.edge.short@yopmail.com", "phone": "412345001", "countryCode": "+61", "industry": "Agriculture", "type": "user"})
probe("firstName 200 chars", "POST", "/user/create", json={"firstName": "N" * 200, "lastName": "Edge", "email": "qa.edge.long@yopmail.com", "phone": "412345002", "countryCode": "+61", "industry": "Agriculture", "type": "user"})
probe("phone letters", "POST", "/user/create", json={"firstName": "Qa", "lastName": "Edge", "email": "qa.edge.phone1@yopmail.com", "phone": "ABCDEFGHI", "countryCode": "+61", "industry": "Agriculture", "type": "user"})
probe("phone with + and spaces", "POST", "/user/create", json={"firstName": "Qa", "lastName": "Edge", "email": "qa.edge.phone2@yopmail.com", "phone": "+61 4 12 34 56 78", "countryCode": "+61", "industry": "Agriculture", "type": "user"})
probe("type = companyAdmin (privilege escalation)", "POST", "/user/create", json={"firstName": "Qa", "lastName": "Edge", "email": "qa.edge.priv@yopmail.com", "phone": "412345004", "countryCode": "+61", "industry": "Agriculture", "type": "companyAdmin"})
probe("email SQLi-ish payload", "POST", "/user/create", json={"firstName": "Qa", "lastName": "Edge", "email": "'; DROP TABLE users; --@yopmail.com", "phone": "412345005", "countryCode": "+61", "industry": "Agriculture", "type": "user"})

print("\n== AUTH / SESSION probes ==")
no_auth = f.requests.Session()
r = no_auth.get(f"{f.BASE}/api/v1/user/list", params={"skip": 0, "limit": 5})
print(f"{'user/list with NO cookie':46} {r.status_code:>4} {r.text[:120]}")
tampered = f.requests.Session(); tampered.headers.update(f.HEADERS); tampered.cookies.set("connect.sid", os.environ.get("FLDR_COOKIE", "") + "tampered")
r = tampered.get(f"{f.BASE}/api/v1/user/list", params={"skip": 0, "limit": 5})
print(f"{'user/list with TAMPERED cookie':46} {r.status_code:>4} {r.text[:120]}")

counts = Counter(r["code"] for r in results)
print("\nSUMMARY status codes:", dict(counts))
json.dump(results, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "invite_edge-log.json"), "w"), indent=1)
