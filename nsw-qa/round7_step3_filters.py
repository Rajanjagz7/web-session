"""STEP 3 protocol: filter comparison (A vs B vs none), unknown params, required
params, pagination totalCount vs actual rows. Read-only (GET only)."""
import sys, json
sys.path.insert(0, r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\1er-tests-python")
from config import EMAIL, PASSWORD
from playwright.sync_api import sync_playwright

BASE_URL = "https://nswstage.rebatem8.com.au"

with sync_playwright() as p:
    c = p.request.new_context(base_url=BASE_URL, timeout=20_000)
    c.post("/api/v1/auth/admin/login", data={"email": EMAIL, "password": PASSWORD})

    def g(path):
        return c.get(path).json()

    print("== Installers: status filter comparison ==")
    no_filter = g("/api/v1/installers?skip=0&limit=100")["data"]
    statuses = [s["status"] for s in no_filter["statusList"]]
    print("no filter total:", no_filter["total"])
    for st in statuses:
        d = g(f"/api/v1/installers?skip=0&limit=100&status={st.replace(' ', '+')}")["data"]
        wrong = {i["status"] for i in d["installers"]} - {st}
        print(f"  status={st!r}: total={d['total']} wrong_rows={wrong}")

    print("\n== Installers: assignedPerson filter A vs B vs none ==")
    users = g("/api/v1/installers?skip=0&limit=100")["data"]["installers"]
    people = sorted({i.get("headAdminId") for i in users if i.get("headAdminId")})
    # get real assignedPerson ids by pulling distinct salesAssignedPerson if present in payload
    r1 = g("/api/v1/installers?skip=0&limit=100&assignedPerson=6a60acb8fbc29557832fb70d")["data"]
    r2 = g("/api/v1/installers?skip=0&limit=100&assignedPerson=000000000000000000000000")["data"]
    print(f"  assignedPerson=<real id>: total={r1['total']}")
    print(f"  assignedPerson=<fake id>: total={r2['total']} (should be 0 or different from real)")
    same_as_unfiltered = r1["total"] == no_filter["total"]
    print(f"  filtered total == unfiltered total? {same_as_unfiltered} (True would mean filter is ignored)")

    print("\n== Installers: unknown/garbage param ==")
    r = c.get("/api/v1/installers?skip=0&limit=5&thisParamDoesNotExist=xyz")
    print(f"  unknown param -> {r.status}, total={r.json()['data'].get('total') if r.status==200 else None}")

    print("\n== Installers: unknown status filter value ==")
    r = c.get("/api/v1/installers?skip=0&limit=5&status=NotARealStatus")
    print(f"  status=NotARealStatus -> {r.status} {json.dumps(r.json())[:200]}")

    print("\n== Jobs: required-param behaviour (no params at all) ==")
    r = c.get("/api/v1/jobs")
    print(f"  GET /jobs (no query params) -> {r.status} total={r.json()['data'].get('total') if r.status==200 else r.text()[:150]}")

    print("\n== Pagination: totalCount vs actual rows returned, all endpoints ==")
    for path, key in [("/api/v1/jobs", "jobs"), ("/api/v1/installers", "installers"),
                       ("/api/v1/users?roleType=admin_user", "users"), ("/api/v1/matrix", "items"),
                       ("/api/v1/activity-logs", "logs")]:
        sep = "&" if "?" in path else "?"
        d = g(f"{path}{sep}skip=0&limit=5")["data"]
        declared_total = d["total"]
        # walk all pages and count actual unique rows
        seen = set()
        skip = 0
        while True:
            page_d = g(f"{path}{sep}skip={skip}&limit=50")["data"]
            rows = page_d[key]
            if not rows:
                break
            for row in rows:
                seen.add(row.get("id") or row.get("_id") or json.dumps(row)[:50])
            skip += 50
            if not page_d["isNext"] or skip > declared_total + 100:
                break
        print(f"  {path}: declared total={declared_total}, actual unique rows walked={len(seen)}, match={declared_total == len(seen)}")

    c.dispose()
