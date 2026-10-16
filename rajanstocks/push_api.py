"""Web Push relay: signs (VAPID) and sends a push message to a browser subscription.

Stateless on purpose — the browser keeps its own subscription and sends it with each request.
Set VAPID_PRIVATE_KEY (base64url, raw 32 bytes) in the environment; VAPID_PUBLIC_KEY is optional
(the default below is the matching public key the page subscribes with).
"""
import json
import os
import time
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/push")

PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY") or "BDaJ0ouMU8W6NF9n6GkKKXx1f088Z2H83uCGYGI8T1imOBJaYHoVxmJRVDTvgrrvzM2e8SnQpeIlUJKPHOKiEjs"
# Only genuine browser push services are allowed, so this cannot be used as an open HTTP relay.
ALLOWED_SUFFIXES = (
    "fcm.googleapis.com",
    ".push.services.mozilla.com",
    ".push.apple.com",
    ".notify.windows.com",
)
_recent = {}


class SendBody(BaseModel):
    subscription: dict
    title: str = "Notification"
    body: str = ""
    url: str = "/"
    tag: Optional[str] = None
    critical: bool = False


def _host_ok(endpoint: str) -> bool:
    u = urlparse(endpoint or "")
    h = u.hostname or ""
    return u.scheme == "https" and any(h == s.lstrip(".") or h.endswith(s) for s in ALLOWED_SUFFIXES)


@router.get("/key")
def key():
    return {"publicKey": PUBLIC_KEY, "configured": bool(os.environ.get("VAPID_PRIVATE_KEY"))}


@router.post("/send")
def send(p: SendBody):
    priv = os.environ.get("VAPID_PRIVATE_KEY")
    if not priv:
        raise HTTPException(503, "Push is not configured on the server (VAPID_PRIVATE_KEY is missing).")
    sub = p.subscription or {}
    ep = sub.get("endpoint", "")
    if not _host_ok(ep):
        raise HTTPException(400, "Unsupported push service.")
    # light per-endpoint throttle: 1 message every 2 seconds
    now = time.time()
    if now - _recent.get(ep, 0) < 2:
        raise HTTPException(429, "Too many push requests; slow down.")
    _recent[ep] = now
    if len(_recent) > 500:
        for k in [k for k, t in _recent.items() if now - t > 60]:
            _recent.pop(k, None)
    try:
        from pywebpush import webpush, WebPushException
    except Exception as e:  # dependency missing on this deploy
        raise HTTPException(503, f"Web Push library unavailable: {e}")
    payload = json.dumps({
        "title": p.title[:120], "body": p.body[:300], "url": p.url[:300], "tag": p.tag, "critical": p.critical,
    })
    try:
        webpush(
            subscription_info=sub,
            data=payload,
            vapid_private_key=priv,
            vapid_claims={"sub": os.environ.get("VAPID_SUBJECT", "https://rajanstocks.vercel.app")},
            ttl=600,
        )
    except WebPushException as e:
        code = getattr(getattr(e, "response", None), "status_code", None)
        if code in (404, 410):
            return {"ok": False, "gone": True}
        raise HTTPException(502, f"Push service rejected the message ({code}).")
    except Exception as e:
        raise HTTPException(500, f"Could not send push: {e}")
    return {"ok": True}
