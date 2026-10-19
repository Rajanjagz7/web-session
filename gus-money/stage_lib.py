"""Stage API client that reuses a browser-created session (.auth/stage.json). Credentials are never stored here."""
import json, requests

STAGE = "https://gusstage.softwareco.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36"

def stage_session():
    state = json.load(open(".auth/stage.json", encoding="utf-8"))
    s = requests.Session()
    for c in state["cookies"]:
        s.cookies.set(c["name"], c["value"], domain=c["domain"], path=c["path"])
    s.headers.update({"user-agent": UA, "referer": STAGE + "/dashboard", "origin": STAGE, "x-device-id": "0f6e3c1a-5b7d-4e2a-9a41-3c8d2b6f7e10", "x-client-timezone": "Asia/Calcutta"})
    return s

def call(s, method, endpoint, **kw):
    headers = {"x-target-endpoint": endpoint, **kw.pop("headers", {})}
    return s.request(method, STAGE + "/api/proxy", headers=headers, timeout=30, **kw)
