"""One copy of the app shell, content-hash cache stamps, data files that are revalidated (29 Oct 2026 review, bugs 6 + 7)."""
import json
import os
import re

import stamp_assets

BASE = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(BASE, "public")


def read(*p):
    with open(os.path.join(BASE, *p), encoding="utf-8") as f:
        return f.read()


def test_there_is_one_copy_of_the_shell():
    assert os.path.isfile(os.path.join(PUBLIC, "index.html")) and os.path.isfile(os.path.join(PUBLIC, "sw.js"))
    assert not os.path.exists(os.path.join(PUBLIC, "static", "index.html"))      # a dead twin used to be served at /static/index.html
    assert not os.path.exists(os.path.join(PUBLIC, "static", "sw.js"))           # version bumps went into this copy while /sw.js came from public/sw.js


def test_the_service_worker_that_is_registered_is_the_one_that_exists():
    assert re.search(r"serviceWorker\.register\('/sw\.js\?v=[0-9a-f]{8}'", read("public", "index.html"))


def test_every_asset_stamp_matches_the_file_content():
    stale = stamp_assets.stamp(write=False)
    assert not stale, f"run `python3 stamp_assets.py` - stale stamps: {stale}"


def test_every_local_script_is_versioned():
    html = read("public", "index.html")
    for src in re.findall(r'<script[^>]+src="(/[^"]+)"', html):
        assert "?v=" in src, f"{src} has no cache-busting stamp"


def test_cash_seed_is_not_fetched_with_a_frozen_version():
    html = read("public", "index.html")
    assert "picks_cash_seed.json?v=" not in html                                  # the file is regenerated daily: a fixed ?v= served week-old picks
    assert html.count("picks_cash_seed.json") == 1 and "loadCashSeed()" in html   # one shared, revalidated fetch (no 1 MB re-download per render)
    assert "cache:'no-cache'" in html


def test_json_data_is_revalidated_by_the_cdn():
    rules = json.loads(read("vercel.json"))["headers"]
    sources = [r["source"] for r in rules]
    generic, js = sources.index("/static/(.*)"), sources.index("/static/(.*)\\.json")
    assert js > generic                                                           # the later rule wins for .json
    value = next(h["value"] for h in rules[js]["headers"] if h["key"] == "Cache-Control")
    assert "must-revalidate" in value and "s-maxage=300" in value
