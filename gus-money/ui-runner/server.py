"""Tiny local UI for non-technical users: run tests, open reports, edit the target URL.

    python ui-runner/server.py   ->   http://localhost:8765

Credentials are NOT editable here; they stay in .env.
"""
import html
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / ".env"
SUITES = {
    "ui": ["npx", "playwright", "test", "--project=chromium", "--headed", "--retries=0"],
    "ui-smoke": ["npx", "playwright", "test", "--project=chromium", "--grep", "@smoke"],
    "api": [sys.executable, "-m", "pytest"],
}
last_output = "No run yet."


def read_url() -> str:
    for line in ENV.read_text().splitlines() if ENV.exists() else []:
        if line.startswith("ADMIN_BASE_URL="):
            return line.split("=", 1)[1]
    return ""


def write_url(url: str) -> None:
    lines = [l for l in (ENV.read_text().splitlines() if ENV.exists() else []) if not l.startswith("ADMIN_BASE_URL=")]
    ENV.write_text("\n".join([f"ADMIN_BASE_URL={url}"] + lines) + "\n")


def page() -> str:
    buttons = "".join(f'<button name="run" value="{k}">Run {k}</button> ' for k in SUITES)
    return f"""<!doctype html><meta charset=utf-8><title>Gus Money QA</title>
<body style="font-family:sans-serif;max-width:900px;margin:2rem auto">
<h1>Gus Money QA runner</h1>
<form method=post action=/config>Base URL: <input name=url size=40 value="{html.escape(read_url())}"> <button>Save</button></form>
<form method=post action=/run>{buttons}</form>
<p><a href="/report">Open Playwright HTML report</a> (run <code>npx playwright show-report</code>)</p>
<h2>Last output</h2><pre style="background:#111;color:#eee;padding:1rem;overflow:auto">{html.escape(last_output)}</pre>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: str, code: int = 200):
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode())

    def do_GET(self):
        self._send(page())

    def do_POST(self):
        global last_output
        length = int(self.headers.get("Content-Length", 0))
        form = parse_qs(self.rfile.read(length).decode())
        path = urlparse(self.path).path
        if path == "/config" and form.get("url", [""])[0].startswith(("http://", "https://")):
            write_url(form["url"][0].strip())
        elif path == "/run" and form.get("run", [""])[0] in SUITES:
            proc = subprocess.run(SUITES[form["run"][0]], cwd=ROOT, capture_output=True, text=True, shell=sys.platform == "win32")
            last_output = (proc.stdout + proc.stderr)[-8000:]
        self._send(page())


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
