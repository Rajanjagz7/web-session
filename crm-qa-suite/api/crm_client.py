"""Reusable API client for the CRM dashboard API (/api/crm/v1)."""
from __future__ import annotations

import requests

from config import Config


class CrmClient:
    def __init__(self, cfg: Config, timeout: int = 30):
        self.cfg = cfg
        self.timeout = timeout
        self.session = requests.Session()
        self.project_id = cfg.project_id

    # -- auth -------------------------------------------------------------
    def login(self) -> None:
        r = self.session.post(
            f"{self.cfg.base_url}/api/auth/login",
            json={"email": self.cfg.email, "password": self.cfg.password},
            # The endpoint is CSRF-protected (same-origin only); a test client presents the app's own origin.
            headers={"origin": self.cfg.base_url, "referer": f"{self.cfg.base_url}/login"},
            timeout=self.timeout,
        )
        if r.status_code != 200:
            raise RuntimeError(f"Login failed with HTTP {r.status_code}")

    def headers(self, project_id: str | None = None, **extra: str) -> dict[str, str]:
        h = {
            "accept": "application/json",
            "crm-org-id": self.cfg.org_id,
            "crm-project-id": project_id or self.project_id,
            "crm-env-mode": self.cfg.env_mode,
        }
        h.update(extra)
        return h

    # -- transport ----------------------------------------------------------
    def request(self, method: str, path: str, json=None, data=None, project_id: str | None = None,
                headers: dict | None = None, authenticated: bool = True, **kw) -> requests.Response:
        h = self.headers(project_id)
        if json is not None or data is not None:
            h["content-type"] = "application/json"
        if headers:
            h.update(headers)
        sess = self.session if authenticated else requests.Session()
        return sess.request(method, f"{self.cfg.api}{path}", json=json, data=data, headers=h,
                            timeout=self.timeout, **kw)

    def get(self, path, **kw):
        return self.request("GET", path, **kw)

    def post(self, path, json=None, **kw):
        return self.request("POST", path, json=json if json is not None else None, **kw)

    def patch(self, path, json=None, **kw):
        return self.request("PATCH", path, json=json, **kw)

    def put(self, path, json=None, **kw):
        return self.request("PUT", path, json=json, **kw)

    def delete(self, path, **kw):
        return self.request("DELETE", path, **kw)

    # -- domain helpers (return parsed JSON, assert success) ------------------
    def create(self, resource: str, body: dict) -> dict:
        r = self.post(f"/{resource}", json=body)
        assert r.status_code == 201, f"create {resource} -> {r.status_code}: {r.text[:300]}"
        return r.json()

    def make_pipeline(self, name: str, stages=("Lead", "Qualified")) -> dict:
        return self.create("pipelines", {"name": name, "stages": [{"name": s} for s in stages]})

    def upload_csv(self, name: str, csv_text: str) -> str:
        """Presigned-URL upload flow; returns the ready File id."""
        raw = csv_text.encode("utf-8")
        f = self.create("files", {"fileName": name, "contentType": "text/csv", "byteSize": len(raw)})
        up = f["upload"]
        put = requests.request(up.get("method", "PUT"), up["url"], data=raw, headers=up.get("headers") or {},
                               timeout=self.timeout)
        assert put.status_code == 200, f"S3 upload -> {put.status_code}"
        done = self.post(f"/files/{f['id']}/complete", json={})
        assert done.status_code == 200, f"complete -> {done.status_code}: {done.text[:200]}"
        return f["id"]
