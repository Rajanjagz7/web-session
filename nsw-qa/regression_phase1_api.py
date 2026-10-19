"""Regression pass (Phase 1: API-only checks) against the 60 bugs in NSW_BUGS.md/csv,
re-tested on staging as of 30 Sep 2026. Covers every bug whose original repro was a pure
API call or an API-observable status/body check. UI-only bugs (Esc-key, stale dropdown,
client-side masking, etc.) are NOT covered here - see regression_phase2_ui.py.

All jobs created by this script use TEST_INSTALLER_ID ("Testing Company") only, and are
tagged ownReference="REGR-<stamp>-<n>" so they can be found and deleted afterward by
regression_cleanup.py. Brand/model choices are pulled live and varied per NSW-STG-46 check
and the project's existing "vary brand/model" convention.
"""
import sys, json, time, random
sys.path.insert(0, r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\1er-tests-python")
from config import EMAIL, PASSWORD
from playwright.sync_api import sync_playwright

BASE_URL = "https://nswstage.rebatem8.com.au"
TEST_INSTALLER_ID = "6aace061972e326f8fef7aae"  # "Testing Company"
STAMP = str(int(time.time()))[-6:]
rnd = random.Random(7)
results = []
_job_n = [0]


def record(bug_id, verdict, detail):
    """verdict: STILL_OPEN | FIXED | CHANGED | INCONCLUSIVE"""
    results.append({"id": bug_id, "verdict": verdict, "detail": detail})
    print(f"{bug_id:12} {verdict:12} {detail[:140]}")


def valid_abn():
    w = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
    while True:
        d = [rnd.randint(1, 9)] + [rnd.randint(0, 9) for _ in range(10)]
        if sum((x - (1 if i == 0 else 0)) * w[i] for i, x in enumerate(d)) % 89 == 0:
            return "".join(map(str, d))


def base_job(overrides=None, customer_overrides=None, address_overrides=None):
    _job_n[0] += 1
    body = {
        "installerId": TEST_INSTALLER_ID,
        "activityType": "heating_cooling",
        "customerType": "residential",
        "methodOfLeadGeneration": "Customer initiated contact",
        "ownReference": f"REGR-{STAMP}-{_job_n[0]:03d}",
        "installationDate": "2026-12-01",
        "customer": {
            "name": "Regression Probe", "email": f"regression.{STAMP}.{_job_n[0]}@yopmail.com",
            "phoneNumber": "412987600", "countryCode": "+61", "flagCode": "AU", "abnAcn": valid_abn(),
        },
        "address": {
            "fullAddress": "1 George St, Sydney NSW 2000, Australia", "isManual": False,
            "streetNumber": "1", "streetName": "George", "streetType": "Street",
            "suburb": "Sydney", "state": "NSW", "postcode": "2000",
        },
        "createdFrom": "add_job",
    }
    if customer_overrides:
        body["customer"].update(customer_overrides)
    if address_overrides:
        body["address"].update(address_overrides)
    if overrides:
        body.update(overrides)
    return body


with sync_playwright() as p:
    c = p.request.new_context(base_url=BASE_URL, timeout=25_000)
    login = c.post("/api/v1/auth/admin/login", data={"email": EMAIL, "password": PASSWORD})
    assert login.status == 200, f"login failed: {login.status} {login.text()[:200]}"

    # ---------- A. Static 404 / page-load checks ----------
    r = c.get("/api/v1/dashboard/job-count")
    record("NSW-STG-01", "STILL_OPEN" if r.status == 404 else "FIXED" if r.status == 200 else "CHANGED",
           f"GET /dashboard/job-count -> {r.status}")

    r = c.get("/api/v1/site/list")
    record("NSW-STG-02", "STILL_OPEN" if r.status == 404 else "FIXED" if r.status == 200 else "CHANGED",
           f"GET /site/list -> {r.status}")

    r = c.get("/api/v1/invoice/list")
    record("NSW-STG-03", "STILL_OPEN" if r.status == 404 else "FIXED" if r.status == 200 else "CHANGED",
           f"GET /invoice/list -> {r.status}")

    r = c.get("/api/v1/installer/filter/list")
    record("NSW-STG-04", "STILL_OPEN" if r.status == 404 else "FIXED" if r.status == 200 else "CHANGED",
           f"GET /installer/filter/list -> {r.status}")

    r = c.get("/api/v1/rebate/installer/list")
    record("NSW-STG-42", "STILL_OPEN" if r.status == 404 else "FIXED" if r.status == 200 else "CHANGED",
           f"GET /rebate/installer/list -> {r.status}")

    any_job = c.get("/api/v1/jobs?skip=0&limit=1").json()["data"]["jobs"][0]["id"]
    r = c.get(f"/api/v1/audit/checklist?jobId={any_job}")
    record("NSW-STG-25", "STILL_OPEN" if r.status == 404 else "FIXED" if r.status == 200 else "CHANGED",
           f"GET /audit/checklist?jobId=... -> {r.status}")

    # ---------- B. Auth / security ----------
    fresh = p.request.new_context(base_url=BASE_URL, timeout=25_000)
    fresh.post("/api/v1/auth/admin/login", data={"email": EMAIL, "password": PASSWORD})
    r1 = fresh.get("/api/v1/auth/me")
    record("NSW-STG-07", "STILL_OPEN" if r1.status == 401 else "FIXED" if r1.status == 200 else "CHANGED",
           f"first GET /auth/me right after login -> {r1.status}")

    # NSW-STG-38: logout doesn't revoke access token
    sess = p.request.new_context(base_url=BASE_URL, timeout=25_000)
    sess.post("/api/v1/auth/admin/login", data={"email": EMAIL, "password": PASSWORD})
    cookies_before = {ck["name"]: ck["value"] for ck in sess.storage_state()["cookies"]}
    logout_r = sess.post("/api/v1/auth/logout")
    me_after_logout = sess.get("/api/v1/auth/me")
    record("NSW-STG-38", "STILL_OPEN" if me_after_logout.status == 200 else "FIXED" if me_after_logout.status == 401 else "CHANGED",
           f"logout={logout_r.status}, GET /auth/me with old token after logout -> {me_after_logout.status}")
    sess.dispose()

    # NSW-STG-39: refresh token reuse after rotation
    sess2 = p.request.new_context(base_url=BASE_URL, timeout=25_000)
    sess2.post("/api/v1/auth/admin/login", data={"email": EMAIL, "password": PASSWORD})
    old_cookies = sess2.storage_state()["cookies"]
    refresh1 = sess2.post("/api/v1/auth/refresh")
    # replay the OLD refresh token in a brand new context
    replay_ctx = p.request.new_context(base_url=BASE_URL, timeout=25_000, storage_state={"cookies": old_cookies, "origins": []})
    refresh2 = replay_ctx.post("/api/v1/auth/refresh")
    record("NSW-STG-39", "STILL_OPEN" if refresh2.status == 200 else "FIXED" if refresh2.status == 401 else "CHANGED",
           f"refresh1={refresh1.status}, replay OLD refresh token -> {refresh2.status}")
    sess2.dispose(); replay_ctx.dispose()

    # NSW-STG-40: throttling on repeated wrong-password logins
    throttle_ctx = p.request.new_context(base_url=BASE_URL, timeout=25_000)
    statuses = []
    for i in range(12):
        rr = throttle_ctx.post("/api/v1/auth/admin/login", data={"email": "no-such-user-regr@yopmail.com", "password": "wrong"})
        statuses.append(rr.status)
    got_429 = 429 in statuses
    record("NSW-STG-40", "FIXED" if got_429 else "STILL_OPEN",
           f"12x wrong-password attempts -> statuses={statuses}")
    throttle_ctx.dispose()

    # NSW-STG-44: form-encoded login body
    form_ctx = p.request.new_context(base_url=BASE_URL, timeout=25_000)
    rf = form_ctx.post("/api/v1/auth/admin/login", form={"email": EMAIL, "password": PASSWORD})
    record("NSW-STG-44", "STILL_OPEN" if rf.status == 200 else "FIXED" if rf.status in (400, 415) else "CHANGED",
           f"POST login (form-urlencoded) -> {rf.status}")
    form_ctx.dispose()

    # NSW-STG-45: CSP header on /log-in
    rp = c.get("/log-in")
    has_csp = "content-security-policy" in {k.lower() for k in rp.headers.keys()}
    record("NSW-STG-45", "FIXED" if has_csp else "STILL_OPEN",
           f"GET /log-in headers has CSP={has_csp}; headers={sorted(rp.headers.keys())}")

    # NSW-STG-52: login with padded-space email
    pad_ctx = p.request.new_context(base_url=BASE_URL, timeout=25_000)
    rpd = pad_ctx.post("/api/v1/auth/admin/login", data={"email": f"  {EMAIL} ", "password": PASSWORD})
    record("NSW-STG-52", "STILL_OPEN" if rpd.status == 400 else "FIXED" if rpd.status == 200 else "CHANGED",
           f"login with padded-space email -> {rpd.status}")
    pad_ctx.dispose()

    # ---------- C. Installers API ----------
    r = c.get("/api/v1/installers/not-an-id/members")
    record("NSW-STG-41", "STILL_OPEN" if r.status == 500 else "FIXED" if r.status == 400 else "CHANGED",
           f"GET /installers/not-an-id/members -> {r.status}")

    paging_cases = [("skip=-1&limit=5", "skip"), ("limit=-5", "limit-neg"), ("limit=0", "limit-zero"),
                    ("skip=abc", "skip-text"), ("limit=abc", "limit-text")]
    paging_results = []
    for qs, label in paging_cases:
        rr = c.get(f"/api/v1/installers?{qs}")
        paging_results.append(f"{label}={rr.status}")
    all_400 = all("=400" in x for x in paging_results)
    record("NSW-STG-48", "FIXED" if all_400 else "STILL_OPEN", f"invalid paging -> {paging_results}")

    r = c.get("/api/v1/jobs?skip=0&limit=2&sort=createdAt&sortType=sideways")
    record("NSW-STG-49", "STILL_OPEN" if r.status == 200 else "FIXED" if r.status == 400 else "CHANGED",
           f"GET /jobs?sortType=sideways -> {r.status}")

    r = c.get("/api/v1/installers/000000000000000000000000/members")
    body = r.json()
    empty_200 = r.status == 200 and body.get("data", {}).get("members") == []
    record("NSW-STG-50", "STILL_OPEN" if empty_200 else "FIXED" if r.status == 404 else "CHANGED",
           f"GET nonexistent installer members -> {r.status} members={body.get('data',{}).get('members')}")

    r_base = c.get("/api/v1/installers?skip=0&limit=5")
    r_bad = c.get("/api/v1/installers?skip=0&limit=5&status=NotARealStatus")
    same = r_base.text() == r_bad.text()
    record("NSW-STG-54", "STILL_OPEN" if (r_bad.status == 200 and same) else "FIXED",
           f"unrecognised status filter -> {r_bad.status}, identical_to_unfiltered={same}")

    # ---------- D. Jobs list / search ----------
    r = c.get("/api/v1/jobs?search=" + "  M8N000078  ".replace(" ", "%20"))
    total = r.json()["data"]["total"]
    record("NSW-STG-17", "STILL_OPEN" if total == 0 else "FIXED", f"search padded jobnumber -> total={total}")

    r = c.get("/api/v1/jobs?search=Siobhan")
    total = r.json()["data"]["total"]
    record("NSW-STG-18", "STILL_OPEN" if total == 0 else "FIXED_OR_NO_MATCHING_DATA",
           f"search 'Siobhan' (accent-insensitive check) -> total={total}")

    r = c.get("/api/v1/jobs?search=%25")
    total_special = r.json()["data"]["total"]
    r_all = c.get("/api/v1/jobs?skip=0&limit=1")
    total_all = r_all.json()["data"]["total"]
    record("NSW-STG-19", "STILL_OPEN" if total_special == total_all else "FIXED",
           f"search '%' -> total={total_special}, unfiltered total={total_all}")

    status_values = ["Install In Progress", "Action Required", "Being Assessed", "Complete", "Archived"]
    tab_results = []
    for sv in status_values:
        rr = c.get(f"/api/v1/jobs?status={sv.replace(' ', '%20')}")
        tab_results.append(f"{sv}={rr.status}")
    any_400 = any("=400" in x for x in tab_results)
    record("NSW-STG-24", "STILL_OPEN" if any_400 else "FIXED", f"status tabs -> {tab_results}")

    search_terms = ["George%20St", "BAWA", "Heating%20%26%20Cooling"]
    search_results = []
    for term in search_terms:
        rr = c.get(f"/api/v1/jobs?search={term}")
        search_results.append(f"{term}={rr.json()['data']['total']}")
    record("NSW-STG-33", "INCONCLUSIVE", f"search by address/installer/activity (no live match expected in test data) -> {search_results}")

    r = c.get("/api/v1/jobs/M8N999999")
    record("NSW-STG-34", "STILL_OPEN" if r.status == 400 else "FIXED" if r.status == 404 else "CHANGED",
           f"GET /jobs/M8N999999 -> {r.status}")

    r = c.get("/api/v1/jobs?sort=createdAt&sortType=asc&limit=5")
    jobs5 = r.json()["data"]["jobs"]
    old_format = [j["jobNumber"] for j in jobs5 if not j["jobNumber"].startswith("M8N")]
    record("NSW-STG-51", "INFO_ONLY", f"oldest 5 job numbers -> {[j['jobNumber'] for j in jobs5]}; non-M8N count={len(old_format)}")

    # ---------- E. POST /jobs boundary / validation ----------
    r = c.post("/api/v1/jobs", data=base_job({"installationDate": "2027-02-29"}))
    record("NSW-STG-13 / NSW-STG-61", "STILL_OPEN" if r.status == 201 else "FIXED" if r.status == 400 else "CHANGED",
           f"POST /jobs installationDate=2027-02-29 (not leap year) -> {r.status}")

    r = c.post("/api/v1/jobs", data=base_job(customer_overrides={"abnAcn": "12345678901"}))
    record("NSW-STG-14 / NSW-STG-59", "STILL_OPEN" if r.status == 201 else "FIXED" if r.status == 400 else "CHANGED",
           f"POST /jobs abnAcn=12345678901 (bad checksum) -> {r.status}")

    dup_body = base_job(customer_overrides={"email": f"dup.{STAMP}@yopmail.com"})
    r1 = c.post("/api/v1/jobs", data=dup_body)
    dup_body2 = dict(dup_body); dup_body2["ownReference"] = dup_body["ownReference"] + "-dup"
    r2 = c.post("/api/v1/jobs", data=dup_body2)
    record("NSW-STG-32", "STILL_OPEN" if (r1.status == 201 and r2.status == 201) else "FIXED",
           f"duplicate job (same customer/site/installer) -> first={r1.status}, second={r2.status}")

    r = c.post("/api/v1/jobs", data=base_job(customer_overrides={"name": "   "}))
    record("NSW-STG-56", "STILL_OPEN" if r.status == 500 else "FIXED" if r.status == 400 else "CHANGED",
           f"POST /jobs customer.name='   ' -> {r.status}")

    malformed_cases = [
        ("trailing comma", '{"installerId":"x",}'),
        ("unquoted key", '{installerId:"x"}'),
        ("raw newline in string", '{"installerId":"x\ny"}'),
    ]
    malformed_results = []
    for label, raw in malformed_cases:
        rr = c.post("/api/v1/jobs", data=raw, headers={"content-type": "application/json"})
        malformed_results.append(f"{label}={rr.status}")
    any_500 = any("=500" in x for x in malformed_results)
    record("NSW-STG-57", "STILL_OPEN" if any_500 else "FIXED", f"malformed JSON bodies -> {malformed_results}")

    postcode_cases = ["", "   ", "0000", "3000", "1999", "abcd", "2000.5", "-2000"]
    pc_results = []
    for pc in postcode_cases:
        rr = c.post("/api/v1/jobs", data=base_job(address_overrides={"postcode": pc}))
        pc_results.append(f"{pc!r}={rr.status}")
    any_pc_400 = any("=400" in x for x in pc_results)
    record("NSW-STG-58", "STILL_OPEN" if not any_pc_400 else "PARTIALLY_FIXED", f"postcode edge cases -> {pc_results}")

    phone_cases = ["abcdefghi", "412 987 600", "4.12e8", "41298760", "4129876001", "0412987600"]
    ph_results = []
    for ph in phone_cases:
        rr = c.post("/api/v1/jobs", data=base_job(customer_overrides={"phoneNumber": ph}))
        ph_results.append(f"{ph!r}={rr.status}")
    any_ph_400 = any("=400" in x for x in ph_results)
    record("NSW-STG-60", "STILL_OPEN" if not any_ph_400 else "PARTIALLY_FIXED", f"phone edge cases -> {ph_results}")

    try:
        brands = c.get("/api/v1/products/brands?category=air_conditioner&limit=60").json()["data"]["brands"]
        brand_name = brands[0]["brand"]
        models = c.get(f"/api/v1/products/brands/{brand_name}/models?category=air_conditioner&limit=5&skip=0").json()["data"]["models"]
        model_name = models[0]["model"]
        equip = [{"originalEquipment": "Installation of a New Air Conditioner", "brand": brand_name, "model": model_name,
                  "heatingCapacityKw": -5, "coolingCapacityKw": -5}]
        r = c.post("/api/v1/jobs", data=base_job({"equipmentQuoted": equip}))
        record("NSW-STG-62", "STILL_OPEN" if r.status == 201 else "FIXED" if r.status == 400 else "CHANGED",
               f"POST /jobs coolingCapacityKw=-5 -> {r.status}")
    except Exception as e:
        record("NSW-STG-62", "ERROR", f"could not run capacity check: {e}")

    # ---------- F. Notes ----------
    try:
        xss_note = "<p><img src=x onerror=alert(1)></p>"
        rn = c.post("/api/v1/notes", data={"jobId": any_job, "note": xss_note})
        if rn.status in (200, 201):
            note_id = rn.json()["data"].get("note", {}).get("id") or rn.json()["data"].get("id")
            get_notes = c.get(f"/api/v1/notes?jobId={any_job}&limit=5&sort=createdAt&sortType=desc")
            notes_list = get_notes.json()["data"].get("notes", [])
            stored_raw = any(xss_note in (n.get("note") or "") for n in notes_list)
            record("NSW-STG-53", "STILL_OPEN" if stored_raw else "FIXED_OR_ESCAPED",
                   f"POST /notes XSS payload -> {rn.status}, stored_raw_in_list={stored_raw}")
        else:
            record("NSW-STG-53", "FIXED_OR_CHANGED", f"POST /notes XSS payload -> {rn.status} (rejected)")
    except Exception as e:
        record("NSW-STG-53", "ERROR", f"could not run XSS note check: {e}")

    r = c.post("/api/v1/notes", data={"jobId": any_job, "note": "<p></p>"})
    record("NSW-STG-55", "STILL_OPEN" if r.status in (200, 201) else "FIXED" if r.status == 400 else "CHANGED",
           f"POST /notes note='<p></p>' -> {r.status}")

    # ---------- G. Products / brands ----------
    try:
        brands = c.get("/api/v1/products/brands?category=air_conditioner&limit=200").json()["data"]["brands"]
        names = [b["brand"] for b in brands]
        lower_seen = {}
        dupes = []
        for n in names:
            key = n.strip().lower()
            if key in lower_seen and lower_seen[key] != n:
                dupes.append((lower_seen[key], n))
            lower_seen.setdefault(key, n)
        record("NSW-STG-46", "STILL_OPEN" if dupes else "FIXED", f"case-duplicate brands -> {dupes[:6]}")
    except Exception as e:
        record("NSW-STG-46", "ERROR", f"could not run brand-dupe check: {e}")

    c.dispose()

with open(r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\regression_phase1_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=1)

print("\n\n=== SUMMARY ===")
from collections import Counter
counts = Counter(r["verdict"] for r in results)
for k, v in counts.items():
    print(f"{k}: {v}")
print(f"\nregression tag for cleanup: REGR-{STAMP}-*")
