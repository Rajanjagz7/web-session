"""Cross-instance cache + lock on Upstash Redis.

Vercel runs several server instances and each used to keep its own in-memory cache, so every cold instance re-downloaded
the same daily candles from Upstox (218 calls for the Picks screen alone). Data that does not change during the day now
lives here once and every instance reads it. Without Redis credentials everything degrades to "miss" (callers just fetch).
Values are JSON, zlib-compressed and base64-encoded (Upstash caps a request at ~1 MB).
"""
import base64
import json
import os
import time
import urllib.request
import zlib


def _creds():
    url = os.environ.get("UPSTASH_REDIS_REST_URL") or os.environ.get("KV_REST_API_URL")
    tok = os.environ.get("UPSTASH_REDIS_REST_TOKEN") or os.environ.get("KV_REST_API_TOKEN")
    return (url, tok) if url and tok else None


def enabled():
    return _creds() is not None


def _pipe(cmds, timeout=4.0):
    url, tok = _creds()
    req = urllib.request.Request(url.rstrip("/") + "/pipeline", data=json.dumps(cmds).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _enc(v):
    return base64.b64encode(zlib.compress(json.dumps(v, separators=(",", ":")).encode(), 6)).decode()


def _dec(s):
    return json.loads(zlib.decompress(base64.b64decode(s)).decode())


def get_many(keys):
    """{key: value} for the keys that exist. One Redis command however many keys."""
    keys = list(keys)
    if not keys or not enabled():
        return {}
    try:
        res = _pipe([["MGET", *["sc:" + k for k in keys]]])[0].get("result") or []
        return {k: _dec(v) for k, v in zip(keys, res) if v}
    except Exception:
        return {}


def get(key):
    return get_many([key]).get(key)


def set_many(items, ttl):
    """items: {key: value}. Failures are ignored: the cache is an optimisation."""
    if not items or not enabled():
        return
    try:
        _pipe([["SET", "sc:" + k, _enc(v), "EX", int(ttl)] for k, v in items.items()])
    except Exception:
        pass


def set(key, value, ttl):
    set_many({key: value}, ttl)


def lock(name, ttl_s):
    """True if THIS caller now owns the lock (SET NX EX). Without Redis the lock is always granted."""
    if not enabled():
        return True
    try:
        return _pipe([["SET", "sl:" + name, str(time.time()), "NX", "EX", int(ttl_s)]])[0].get("result") == "OK"
    except Exception:
        return True            # Redis hiccup: do not block trading logic


def unlock(name):
    if enabled():
        try:
            _pipe([["DEL", "sl:" + name]])
        except Exception:
            pass


def fetch(key, ttl, fn):
    """Return the shared value for key, else compute it with fn() and share it. A falsy result is never stored."""
    v = get(key)
    if v is not None:
        return v
    v = fn()
    if v:
        set(key, v, ttl)
    return v
