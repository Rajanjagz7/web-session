"""Round 9 cleanup: for every Round 8 boundary/schema-probe job (identified by
content markers, saved to round9_bad_jobs_list.json), create one replacement
job with proper, realistic data - varied activity type, customer type, real
NSW address, checksum-valid ABN, valid 9-digit mobile, valid date, varied
Brand/Model from the real product catalog, installer fixed to the single
designated "Testing Company" (per instruction) - then permanently delete the
original bad-data jobs via DELETE /api/v1/jobs. Read-back + count check on
every step."""
import sys, json, random, time
from urllib.parse import quote
sys.path.insert(0, r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\1er-tests-python")
from config import EMAIL, PASSWORD
from playwright.sync_api import sync_playwright

BASE_URL = "https://nswstage.rebatem8.com.au"
TEST_INSTALLER_ID = "6aace061972e326f8fef7aae"  # Testing Company, I01-00014
rnd = random.Random(42)

BAD_JOBS = json.load(open(r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\round9_bad_jobs_list.json", encoding="utf-8"))
print(f"{len(BAD_JOBS)} bad-data jobs to replace and delete")

FIRST_NAMES = ["Olivia", "Jack", "Mia", "Noah", "Ava", "Lucas", "Isla", "Ethan", "Grace", "Henry",
               "Zoe", "Leo", "Chloe", "Mason", "Ruby", "Oliver", "Willow", "Archie", "Ella", "Charlie"]
LAST_NAMES = ["Bennett", "Sullivan", "Robertson", "Fitzgerald", "Thompson", "Whitfield", "Nguyen",
              "O'Brien", "Kowalski", "Raman", "Khan", "Reeves", "Dawson", "Harper", "Mitchell"]
ADDRESSES = [
    ("1 George St, Sydney NSW 2000, Australia", "1", "George", "Street", "Sydney", "2000"),
    ("50 Elizabeth St, Artarmon NSW 2064, Australia", "50", "Elizabeth", "Street", "Artarmon", "2064"),
    ("123 Walker St, North Sydney NSW 2060, Australia", "123", "Walker", "Street", "North Sydney", "2060"),
    ("66 Pacific Hwy, St Leonards NSW 2065, Australia", "66", "Pacific", "Highway", "St Leonards", "2065"),
    ("789 New Canterbury Rd, Dulwich Hill NSW 2203, Australia", "789", "New Canterbury", "Road", "Dulwich Hill", "2203"),
    ("898 Punchbowl Rd, Punchbowl NSW 2196, Australia", "898", "Punchbowl", "Road", "Punchbowl", "2196"),
    ("14 Station St, Wentworthville NSW 2145, Australia", "14", "Station", "Street", "Wentworthville", "2145"),
    ("21 Macquarie St, Parramatta NSW 2150, Australia", "21", "Macquarie", "Street", "Parramatta", "2150"),
    ("45 Hunter St, Newcastle West NSW 2300, Australia", "45", "Hunter", "Street", "Newcastle West", "2300"),
    ("100 Crown St, Wollongong NSW 2500, Australia", "100", "Crown", "Street", "Wollongong", "2500"),
    ("5 Hunter St, Hornsby NSW 2077, Australia", "5", "Hunter", "Street", "Hornsby", "2077"),
    ("30 Oxford St, Bondi Junction NSW 2022, Australia", "30", "Oxford", "Street", "Bondi Junction", "2022"),
    ("12 High St, Penrith NSW 2750, Australia", "12", "High", "Street", "Penrith", "2750"),
    ("8 Victoria Rd, Liverpool NSW 2170, Australia", "8", "Victoria", "Road", "Liverpool", "2170"),
    ("77 Beamish St, Campsie NSW 2194, Australia", "77", "Beamish", "Street", "Campsie", "2194"),
]
LEAD_METHODS = ["Customer initiated contact", "Online advertisement", "Social media", "Email campaign", "Referral"]


def valid_abn():
    w = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
    while True:
        d = [rnd.randint(1, 9)] + [rnd.randint(0, 9) for _ in range(10)]
        if sum((x - (1 if i == 0 else 0)) * w[i] for i, x in enumerate(d)) % 89 == 0:
            return "".join(map(str, d))


def mobile():
    return "4" + "".join(str(rnd.randint(0, 9)) for _ in range(8))


with sync_playwright() as p:
    c = p.request.new_context(base_url=BASE_URL, timeout=20_000)
    c.post("/api/v1/auth/admin/login", data={"email": EMAIL, "password": PASSWORD})

    # pull a real Brand+Model pool for each activity type
    def brand_model_pool(category, block=None):
        url = f"/api/v1/products/brands?category={category}&limit=60"
        if block:
            url += f"&block={block}"
        brands = [b["brand"] for b in c.get(url).json()["data"]["brands"]]
        pool = []
        for br in rnd.sample(brands, min(12, len(brands))):
            murl = f"/api/v1/products/brands/{quote(br)}/models?category={category}&limit=20&skip=0"
            if block:
                murl += f"&block={block}"
            models = c.get(murl).json()["data"]["models"]
            for m in models[:5]:
                pool.append((br, m["model"], m.get("heatingCapacityKw", 0), m.get("coolingCapacityKw", 0)))
        return pool

    ac_pool = brand_model_pool("air_conditioner")
    hp_pool = brand_model_pool("water_heater", block="heat_pump")
    print(f"AC catalog pool: {len(ac_pool)} entries, HWHP catalog pool: {len(hp_pool)} entries")

    count_before = c.get("/api/v1/jobs?skip=0&limit=1").json()["data"]["total"]
    stamp = str(int(time.time()))[-6:]

    replacements = []
    for i, bad in enumerate(BAD_JOBS):
        addr = ADDRESSES[i % len(ADDRESSES)]
        activity = "heating_cooling" if i % 2 == 0 else "hot_water_heat_pump"
        customer_type = ["residential", "residential", "business", "small_business"][i % 4]
        first, last = FIRST_NAMES[i % len(FIRST_NAMES)], LAST_NAMES[(i * 3 + 1) % len(LAST_NAMES)]
        full_name = f"{first} {last}"
        email = f"{first.lower()}.{last.lower().replace(chr(39),'')}.{stamp}.{i}@yopmail.com"

        if activity == "heating_cooling":
            brand, model, hkw, ckw = ac_pool[i % len(ac_pool)]
            equip = [{"originalEquipment": "Installation of a New Air Conditioner",
                      "brand": brand, "model": model, "heatingCapacityKw": hkw, "coolingCapacityKw": ckw}]
        else:
            brand, model, hkw, ckw = hp_pool[i % len(hp_pool)]
            equip = [{"originalEquipment": "Brand New Install", "brand": brand, "model": model}]

        body = {
            "installerId": TEST_INSTALLER_ID,
            "activityType": activity,
            "customerType": customer_type,
            "methodOfLeadGeneration": LEAD_METHODS[i % len(LEAD_METHODS)],
            "ownReference": f"CLEAN-{stamp}-{i+1:03d}",
            "installationDate": f"2027-{1 + (i % 12):02d}-{1 + (i % 27):02d}",
            "address": {"fullAddress": addr[0], "isManual": False, "streetNumber": addr[1],
                        "streetName": addr[2], "streetType": addr[3], "suburb": addr[4],
                        "state": "NSW", "postcode": addr[5]},
            "equipmentQuoted": equip,
            "createdFrom": "add_job",
        }
        if customer_type == "residential":
            body["customer"] = {"name": full_name, "email": email, "phoneNumber": mobile(),
                                 "countryCode": "+61", "flagCode": "AU", "abnAcn": valid_abn()}
        else:
            biz = f"{addr[4]} {['Trading','Services','Holdings','Group'][i%4]} Pty Ltd"
            body["customer"] = {"name": biz, "email": email, "phoneNumber": mobile(),
                                 "countryCode": "+61", "flagCode": "AU", "abnAcn": valid_abn(),
                                 "businessType": "", "authFirstName": first, "authLastName": last,
                                 "authSignPosition": ["Owner", "Manager", "Director"][i % 3]}
            if customer_type == "small_business":
                body["averageKwhPerDay"] = "less_than_273"

        r = c.post("/api/v1/jobs", data=body)
        ok = r.status < 300
        rec = {"old_jobNumber": bad["jobNumber"], "old_id": bad["id"], "status": r.status}
        if ok:
            job = r.json()["data"]["job"]
            rec["new_jobNumber"] = job["jobNumber"]
            rec["new_id"] = job["id"]
        else:
            rec["error"] = r.text()[:300]
        replacements.append(rec)
        print(f"[{i+1:3}/{len(BAD_JOBS)}] {bad['jobNumber']} -> {rec.get('new_jobNumber','FAILED')}  ({r.status})")

    failed = [r for r in replacements if r["status"] >= 300]
    print(f"\n{len(replacements)-len(failed)} replacements created OK, {len(failed)} failed")
    if failed:
        print("FAILED cases (not deleting their originals):")
        for f in failed:
            print(" ", f)

    with open(r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\round9_replacements.json", "w", encoding="utf-8") as f:
        json.dump(replacements, f, indent=1)

    count_after_create = c.get("/api/v1/jobs?skip=0&limit=1").json()["data"]["total"]
    print(f"count before={count_before} after creating replacements={count_after_create} delta={count_after_create-count_before} (expect +{len(replacements)-len(failed)})")

    # only delete originals whose replacement succeeded
    to_delete = [r["old_id"] for r in replacements if r["status"] < 300]
    print(f"\ndeleting {len(to_delete)} original bad-data jobs...")
    CHUNK = 25
    deleted_total = 0
    for start in range(0, len(to_delete), CHUNK):
        chunk = to_delete[start:start + CHUNK]
        dr = c.delete("/api/v1/jobs", data={"jobIds": chunk})
        print(f"  delete chunk {start}-{start+len(chunk)}: {dr.status} {dr.text()[:200]}")
        if dr.status < 300:
            deleted_total += dr.json().get("data", {}).get("deletedCount", 0)

    count_final = c.get("/api/v1/jobs?skip=0&limit=1").json()["data"]["total"]
    print(f"\ndeleted_total={deleted_total}, final job count={count_final} "
          f"(expect before={count_before} + replacements={len(replacements)-len(failed)} - deleted={deleted_total})")
    c.dispose()
