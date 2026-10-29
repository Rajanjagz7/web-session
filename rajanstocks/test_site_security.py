"""Closed holes from the 29 Oct 2026 review: cross-site writes, public default admin key, open kv-migrate, naive timestamps."""
import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("GODS_EYE_ADMIN_KEY", "test-admin-key-not-a-real-secret")

import gods_eye_api  # noqa: E402
import server  # noqa: E402

client = TestClient(server.app)


def test_cross_site_write_is_refused():
    for headers in ({"Origin": "https://evil.example"}, {"Sec-Fetch-Site": "cross-site"}, {"Origin": "null"}, {"Sec-Fetch-Site": "same-site", "Origin": "https://x.vercel.app"}):
        r = client.post("/api/does-not-exist", headers=headers)
        assert r.status_code == 403, headers


def test_writes_from_the_app_itself_and_from_scripts_pass_the_guard():
    # a path that does not exist: 404 means the guard let it through to the router (no real book is touched)
    assert client.post("/api/does-not-exist").status_code == 404                                              # curl / GitHub heartbeat: no Origin
    assert client.post("/api/does-not-exist", headers={"Origin": "http://testserver"}).status_code == 404     # same origin
    assert client.post("/api/does-not-exist", headers={"Sec-Fetch-Site": "same-origin"}).status_code == 404
    assert client.get("/api/does-not-exist", headers={"Origin": "https://evil.example"}).status_code == 404   # reads are not blocked here


def test_public_default_admin_key_no_longer_works(monkeypatch):
    monkeypatch.setattr(gods_eye_api, "ADMIN_API_KEY", "")                                    # server with no key configured
    for key in ("ge-admin-secure-key-2026", "", "anything"):
        r = client.post("/api/v1/admin/killswitch", json={"enabled": True}, headers={"x-admin-key": key})
        assert r.status_code == 401, key
    assert gods_eye_api._KILL_SWITCH is False


def test_admin_key_still_works_when_configured(monkeypatch):
    monkeypatch.setattr(gods_eye_api, "ADMIN_API_KEY", "k-123")
    assert client.post("/api/v1/admin/killswitch", json={"enabled": True}, headers={"x-admin-key": "wrong"}).status_code == 401
    assert client.post("/api/v1/admin/killswitch", json={"enabled": True}, headers={"x-admin-key": "k-123"}).status_code == 200
    gods_eye_api._KILL_SWITCH = False


@pytest.mark.parametrize("method", ["get", "post"])
def test_kv_migrate_needs_the_admin_secret(monkeypatch, method):
    called = []
    import shared_cache
    monkeypatch.setattr(shared_cache, "migrate_state", lambda ow=False: called.append(ow) or {"ok": False})
    monkeypatch.delenv("CRON_SECRET", raising=False)
    monkeypatch.delenv("GODS_EYE_ADMIN_KEY", raising=False)
    assert getattr(client, method)("/api/m/kv-migrate?overwrite=1").status_code == 403                       # nothing configured: disabled
    monkeypatch.setenv("CRON_SECRET", "s3cret")
    assert getattr(client, method)("/api/m/kv-migrate?overwrite=1").status_code == 403                       # no credentials
    assert getattr(client, method)("/api/m/kv-migrate?overwrite=1", headers={"Authorization": "Bearer nope"}).status_code == 403
    assert called == []                                                                                      # the migration never ran
    assert getattr(client, method)("/api/m/kv-migrate", headers={"Authorization": "Bearer s3cret"}).status_code == 200
    assert called == [False]


def test_timestamps_carry_the_ist_offset():
    import strategies_api
    import re
    src = open(os.path.join(os.path.dirname(strategies_api.__file__), "strategies_api.py"), encoding="utf-8").read()
    assert 'datetime.now().isoformat' not in src and src.count("datetime.now(IST).isoformat") >= 3
