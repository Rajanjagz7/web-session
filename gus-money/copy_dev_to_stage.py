"""Copies lenders and products from dev (gusdev) to stage (gusstage). Re-runnable: items already on stage are skipped.
Usage (from gus-money/):  python copy_dev_to_stage.py lenders | products | deactivate | status
The stage session comes from .auth/stage.json (created by a normal web sign-in). No credentials are stored."""
import io, os, sys, time, json
sys.path.insert(0, r"C:\Users\Baps\Downloads\rajan backup\gus-money")
sys.path.insert(0, r"C:\Users\Baps\AppData\Local\Temp\claude\c--Users-Baps-Downloads-rajan-backup\4080ed99-fcc1-4297-8820-b9fd19f50d55\scratchpad")
import requests
from lenderlib import client  # dev client (logged in)
from stage_lib import stage_session, call

phase = sys.argv[1] if len(sys.argv) > 1 else "status"
dev = client()
st = stage_session()
writes = {"n": 0, "remaining": None}

def swrite(method, endpoint, **kw):
    r = call(st, method, endpoint, **kw)
    writes["n"] += 1
    rem = r.headers.get("ratelimit-remaining")
    if rem is not None: writes["remaining"] = int(rem)
    if r.status_code == 429:
        print("STOP: stage write limit reached (429), retry-after", r.headers.get("retry-after"), "s")
        raise SystemExit(2)
    return r

def dev_lenders():
    return {l["name"]: l for l in dev.request("GET", "/lenders", params={"limit": 100}).json()["data"]}

def dev_products():
    ps = dev.request("GET", "/products", params={"limit": 100}).json()["data"]
    return sorted(ps, key=lambda p: p["createdAt"])  # oldest first, so stage's newest-first list matches dev

def stage_lenders():
    return {l["name"]: l for l in call(st, "GET", "/lenders", params={"limit": 100}).json()["data"]}

def stage_products():
    return call(st, "GET", "/products", params={"limit": 100}).json()["data"]

def make_logo(name):
    """A neutral monogram, used only when the dev lender has no logo."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (400, 400), (31, 78, 121)); d = ImageDraw.Draw(im)
    txt = "".join(w[0] for w in name.split()[:3]).upper()
    f = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 150)
    b = d.textbbox((0, 0), txt, font=f)
    d.text(((400 - (b[2] - b[0])) / 2 - b[0], (400 - (b[3] - b[1])) / 2 - b[1]), txt, font=f, fill=(255, 255, 255))
    buf = io.BytesIO(); im.save(buf, "PNG"); return buf.getvalue()

def upload_logo_to_stage(lender):
    src = lender.get("logoPreview") or lender.get("logo")
    data, ctype = None, "image/png"
    if src and src.startswith("http"):
        resp = requests.get(src, timeout=30)
        if resp.status_code == 200 and resp.content:
            data = resp.content; ctype = resp.headers.get("content-type", "image/png").split(";")[0]
    if data is None: data, ctype = make_logo(lender["name"]), "image/png"
    ext = "png" if "png" in ctype else ("jpg" if "jp" in ctype else "png")
    fname = lender["name"].lower().replace(" ", "-").replace(".", "") + "." + ext
    p = swrite("POST", "/uploads/presign", json={"target": "profiles", "files": [{"fileName": fname, "contentType": ctype, "fileType": "image"}]})
    p.raise_for_status()
    u = p.json()["data"]["uploads"][0]
    put = requests.put(u["uploadUrl"], data=data, headers={"Content-Type": ctype}, timeout=60)
    assert put.status_code == 200, f"logo upload for {lender['name']} -> {put.status_code}"
    return u["publicUrl"]

if phase == "status":
    sl, sp = stage_lenders(), stage_products()
    print(f"dev: {len(dev_lenders())} lenders, {len(dev_products())} products | stage: {len(sl)} lenders, {len(sp)} products")

elif phase == "lenders":
    existing = stage_lenders()
    for name, l in dev_lenders().items():
        if name in existing:
            print(f"skip (already on stage): {name}"); continue
        logo = upload_logo_to_stage(l)
        subs = []
        email = l.get("contactEmail")
        if not email:
            email = "anz.support@yopmail.com" if name == "ANZ" else name.lower().replace(" ", ".") + "@yopmail.com"
            subs.append("contactEmail (missing on dev) -> " + email)
        body = {"name": l["name"], "legalName": l["legalName"], "abn": l["abn"], "contactName": l.get("contactName") or "Customer Support", "contactEmail": email,
                "contactPhone": l["contactPhone"], "logo": logo}
        if l.get("website"): body["website"] = l["website"]
        if subs: print("   substitutions for", name, ":", subs)
        r = swrite("POST", "/lenders", json=body)
        if r.status_code == 422 and any(x.get("field") == "website" for x in (r.json().get("details") or [])):
            fixed = "https://" + l["website"].replace("%20", "").split(" ")[0].split("/")[0]
            print("   website rejected on stage; retrying with", fixed)
            body["website"] = fixed
            r = swrite("POST", "/lenders", json=body)
        j = r.json(); d = (j.get("details") or [{}])[0]
        print(f"{name:28s} -> {r.status_code} {'' if r.status_code == 201 else d.get('field', '') + ': ' + str(d.get('message') or j.get('message'))}")
        if r.status_code != 201:
            print("   payload keys:", list(body)); break
    print("writes this run:", writes["n"], "| stage remaining:", writes["remaining"])

elif phase == "products":
    sl = stage_lenders()
    have = {(p["lender"]["name"], p["name"]) for p in stage_products()}
    done = 0
    for p in dev_products():
        key = (p["lender"]["name"], p["name"])
        if key in have: continue
        lid = sl[p["lender"]["name"]]["_id"]
        body = {"lenderId": lid, "name": p["name"], "type": p["type"], "interestRateBps": p["interestRateBps"], "minAmountCents": p["minAmountCents"],
                "maxAmountCents": p["maxAmountCents"], "termMonths": p["termMonths"]}
        for k in ("description", "comparisonRateBps", "eligibilityNotes"):
            if p.get(k) is not None: body[k] = p[k]
        crit = {k: v for k, v in (p.get("criteria") or {}).items() if k != "requiresBankConnection"}
        if crit: body["criteria"] = crit
        if p.get("fees"): body["fees"] = [{"name": f["name"], "amountCents": f["amountCents"], "frequency": f["frequency"]} for f in p["fees"]]
        if writes["remaining"] is not None and writes["remaining"] <= 6:
            print("pausing products: keeping the last few writes for deactivations"); break
        r = swrite("POST", "/products", json=body)
        if r.status_code != 201:
            j = r.json(); d = (j.get("details") or [{}])[0]
            print(f"FAILED {key} -> {r.status_code} {d.get('field', '')}: {d.get('message') or j.get('message')}"); break
        done += 1
    print(f"products created this run: {done} | writes this run: {writes['n']} | stage remaining: {writes['remaining']}")

elif phase == "deactivate":
    dev_inactive = {(p["lender"]["name"], p["name"]) for p in dev_products() if not p["isActive"]}
    n = 0
    for p in stage_products():
        if (p["lender"]["name"], p["name"]) in dev_inactive and p["isActive"]:
            r = swrite("PUT", f"/products/{p['_id']}", json={"isActive": False})
            print(f"deactivate {p['lender']['name']} / {p['name']} -> {r.status_code}"); n += 1
    print(f"deactivated: {n} | stage remaining: {writes['remaining']}")
