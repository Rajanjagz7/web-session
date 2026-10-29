"""Cache-busting stamps from file CONTENT, so a changed asset can never be served stale again.

  python3 stamp_assets.py            rewrite every ?v=... (scripts, styles, icons, manifest; data JSON is revalidated by the headers instead) in public/index.html and public/static/*.js, and the SHELL name in public/sw.js
  python3 stamp_assets.py --check    exit 1 (and say which) when a stamp is out of date

Why: the stamps used to be bumped by hand (journal.js?v=20261028s). Every forgotten bump showed up as "I still see the old UI", and the
service worker version was bumped in a dead copy of sw.js. Now the version of a file is the first 8 hex characters of its sha1, so it changes
exactly when the file changes. Run this after editing anything under public/ (test_static_layout.py fails until you do).
"""
import hashlib
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(BASE, "public")
REF = re.compile(r'(/?(?:static/)?[A-Za-z0-9_.\-]+\.(?:js|css|svg|png|ico|webmanifest))\?v=([0-9A-Za-z]+)')
SHELL = re.compile(r"(const SHELL = ')[^']*(')")


def _resolve(ref):
    name = ref.lstrip("/")
    for cand in (os.path.join(PUBLIC, name), os.path.join(PUBLIC, "static", name)):
        if os.path.isfile(cand):
            return cand
    return None


def _hash(path):
    with open(path, "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()[:8]


def _files():
    out = [os.path.join(PUBLIC, "index.html")]
    sdir = os.path.join(PUBLIC, "static")
    out += sorted(os.path.join(sdir, n) for n in os.listdir(sdir) if n.endswith(".js"))
    return out


def shell_name():
    """The service worker cache name: changes whenever any script / stylesheet of the app shell changes (old caches are then purged on activate)."""
    h = hashlib.sha1()
    sdir = os.path.join(PUBLIC, "static")
    for n in sorted(os.listdir(sdir)):
        if n.endswith((".js", ".css")):
            h.update(n.encode())
            h.update(open(os.path.join(sdir, n), "rb").read())
    return "algo-shell-" + h.hexdigest()[:8]


def stamp(write=True):
    """Returns the list of (file, reference, old, new) that were / would be changed. Several passes: a stamped .js changes its own hash."""
    changes = []
    for _ in range(6):
        changed = False
        for path in _files():
            with open(path, encoding="utf-8") as f:
                text = f.read()

            def fix(m):
                target = _resolve(m.group(1))
                if not target:
                    return m.group(0)
                new = _hash(target)
                if new != m.group(2):
                    changes.append((os.path.relpath(path, BASE), m.group(1), m.group(2), new))
                return m.group(0).replace("v=" + m.group(2), "v=" + new)
            new_text = REF.sub(fix, text)
            if new_text != text:
                changed = True
                if write:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new_text)
        sw = os.path.join(PUBLIC, "sw.js")
        with open(sw, encoding="utf-8") as f:
            text = f.read()
        new_text = SHELL.sub(lambda m: m.group(1) + shell_name() + m.group(2), text)
        if new_text != text:
            changes.append(("public/sw.js", "SHELL", re.search(SHELL, text).group(0), shell_name()))
            changed = True
            if write:
                with open(sw, "w", encoding="utf-8") as f:
                    f.write(new_text)
        if not write or not changed:
            break
    return changes


if __name__ == "__main__":
    check = "--check" in sys.argv
    ch = stamp(write=not check)
    for c in ch:
        print(("STALE " if check else "stamped ") + " ".join(map(str, c)))
    if check and ch:
        print("run: python3 stamp_assets.py")
        sys.exit(1)
    print("all asset stamps are current" if check else f"{len(ch)} stamp(s) updated")
