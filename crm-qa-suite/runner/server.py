#!/usr/bin/env python3
"""Local runner UI for non-technical users. Standard library only.

  python runner/server.py        ->  http://127.0.0.1:8765

Security model: binds to 127.0.0.1 only; commands are built from a fixed whitelist (no shell, no user-supplied
argv); the password can be written but never read back; only non-secret settings are returned by /api/config.
"""
import json
import os
import re
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"
ENV_FILE = ROOT / ".env"
HOST, PORT = "127.0.0.1", 8765
PUBLIC_KEYS = ["CRM_BASE_URL", "CRM_PROJECT_ID", "CRM_ORG_ID", "CRM_ENV_MODE", "CRM_EMAIL"]
SECRET_KEYS = ["CRM_PASSWORD"]
MARKERS = {"all", "positive", "negative", "edge", "boundary", "security", "known_bug"}
SUITES = {"api", "ui", "all"}
NPX = "npx.cmd" if os.name == "nt" else "npx"

state = {"running": False, "log": [], "started": None, "finished": None, "exit": None, "what": ""}
lock = threading.Lock()


def read_env() -> dict:
    out = {}
    if ENV_FILE.is_file():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("=")
                out[k.strip()] = v.strip()
    return out


def write_env(updates: dict) -> None:
    cur = read_env()
    cur.update({k: v for k, v in updates.items() if v is not None})
    ENV_FILE.write_text("".join(f"{k}={v}\n" for k, v in cur.items()), encoding="utf-8")


def commands(suite: str, marker: str):
    cmds = []
    if suite in ("api", "all"):
        c = [sys.executable, "-m", "pytest", "-q"]
        if marker != "all":
            c += ["-m", marker]
        cmds.append((c, ROOT / "api"))
    if suite in ("ui", "all"):
        c = [NPX, "playwright", "test"]
        if marker != "all":
            c += ["--grep", f"\\[{marker}\\]"]
        cmds.append((c, ROOT / "ui"))
    cmds.append(([sys.executable, str(ROOT / "scripts" / "check_gates.py")], ROOT))
    return cmds


def run_job(suite: str, marker: str):
    env = {**os.environ, **read_env()}
    try:
        code = 0
        for cmd, cwd in commands(suite, marker):
            with lock:
                state["log"].append(f"$ {' '.join(Path(c).name if i == 0 else c for i, c in enumerate(cmd))}")
            p = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, encoding="utf-8", errors="replace")
            for line in p.stdout:
                with lock:
                    state["log"].append(line.rstrip())
                    del state["log"][:-2000]
            code = p.wait() or code
        with lock:
            state["exit"] = code
    except Exception as e:  # report, never crash the server
        with lock:
            state["log"].append(f"runner error: {e}")
            state["exit"] = 1
    finally:
        with lock:
            state["running"] = False
            state["finished"] = time.time()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.send_header("cache-control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path: Path, ctype: str):
        if not path.is_file():
            return self._json({"error": "not found"}, 404)
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("content-type", ctype)
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _same_origin(self) -> bool:
        origin = self.headers.get("origin")
        return origin in (None, f"http://{HOST}:{PORT}", f"http://localhost:{PORT}")

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            return self._file(Path(__file__).parent / "index.html", "text/html; charset=utf-8")
        if path == "/api/status":
            with lock:
                return self._json({**state, "log": state["log"][-400:]})
        if path == "/api/config":
            env = read_env()
            cfg = {k: env.get(k, "") for k in PUBLIC_KEYS}
            cfg["passwordSet"] = bool(env.get("CRM_PASSWORD"))
            return self._json(cfg)
        if path == "/api/reports":
            files = [p.name for p in REPORTS.glob("*") if p.suffix in (".html", ".xml") and p.is_file()]
            return self._json({"files": sorted(files), "uiReport": (REPORTS / "ui-html" / "index.html").is_file()})
        m = re.fullmatch(r"/reports/([\w.\-]+\.(html|xml))", path)
        if m:
            return self._file(REPORTS / m.group(1), "text/html; charset=utf-8" if m.group(2) == "html" else "application/xml")
        if path.startswith("/reports/ui-html/"):
            rel = path[len("/reports/ui-html/"):] or "index.html"
            target = (REPORTS / "ui-html" / rel).resolve()
            if (REPORTS / "ui-html").resolve() not in target.parents and target != (REPORTS / "ui-html" / "index.html").resolve():
                return self._json({"error": "forbidden"}, 403)
            ctype = {"html": "text/html", "js": "text/javascript", "css": "text/css", "png": "image/png",
                     "zip": "application/zip", "webm": "video/webm"}.get(target.suffix.lstrip("."), "application/octet-stream")
            return self._file(target, ctype)
        self._json({"error": "not found"}, 404)

    def do_POST(self):
        if not self._same_origin():
            return self._json({"error": "cross-origin request refused"}, 403)
        n = int(self.headers.get("content-length") or 0)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return self._json({"error": "invalid json"}, 400)
        if self.path == "/api/run":
            suite, marker = body.get("suite"), body.get("marker", "all")
            if suite not in SUITES or marker not in MARKERS:
                return self._json({"error": "unknown suite or marker"}, 400)
            with lock:
                if state["running"]:
                    return self._json({"error": "a run is already in progress"}, 409)
                state.update(running=True, log=[], started=time.time(), finished=None, exit=None, what=f"{suite}/{marker}")
            threading.Thread(target=run_job, args=(suite, marker), daemon=True).start()
            return self._json({"started": True})
        if self.path == "/api/config":
            updates = {k: str(body[k]).strip() for k in PUBLIC_KEYS if k in body}
            if body.get("CRM_PASSWORD"):
                updates["CRM_PASSWORD"] = str(body["CRM_PASSWORD"])
            if any(("\n" in v or "\r" in v) for v in updates.values()):
                return self._json({"error": "newlines not allowed"}, 400)
            write_env(updates)
            return self._json({"saved": True})
        self._json({"error": "not found"}, 404)


if __name__ == "__main__":
    print(f"CRM QA runner on http://{HOST}:{PORT}  (Ctrl+C to stop)")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
