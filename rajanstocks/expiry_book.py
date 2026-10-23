"""Expiry diary - so you can look up what happened in an OLD expiry days or weeks later.

Upstox serves candle history for an option contract for as long as you know its instrument key -
but expired contracts vanish from the live instrument master, so the key must be written down while
the contract still trades. Every live chain fetch is recorded here (strike -> CE/PE instrument key);
when that expiry passes, the Trade screen's "Old expiry" picker can still pull each contract's chart.

  GET /api/m/expiries?symbol=NIFTY                 - recorded expiries for the symbol (past ones included)
  GET /api/m/expired?symbol=NIFTY&expiry=2026-10-27 - the recorded strikes with their instrument keys

Storage is the shared KV store (works across Vercel's instances), one book per symbol+expiry plus a
small per-symbol index. Nothing here is a signal - it is a record-keeping aid for review and learning.
"""
from datetime import datetime

from fastapi import APIRouter, HTTPException

import market_api

router = APIRouter(prefix="/api/m")

TTL_DAYS = 150          # keep a recorded expiry for about 5 months, then let it go


def record_chain_book(ch):
    """Called after every live chain fetch: write every contract key into the diary (idempotent, cheap)."""
    try:
        import shared_cache
        sym, exp = ch.get("symbol"), ch.get("expiry")
        rows = ch.get("rows") or []
        if not sym or not exp or not rows:
            return
        today = datetime.now(market_api.IST).date().isoformat()
        book = shared_cache.get(f"expbook:{sym}:{exp}") or {}
        for r in rows:
            st = book.setdefault(str(r.get("strike")), {})
            for side in ("ce", "pe"):
                leg = r.get(side) or {}
                if leg.get("key"):
                    cur = st.get(side) or {}
                    st[side] = {"key": leg["key"], "firstSeen": cur.get("firstSeen") or today, "lastSeen": today}
        book["_asOf"] = today
        if ch.get("spot"):
            book["_spot"] = ch.get("spot")
        shared_cache.set(f"expbook:{sym}:{exp}", book, TTL_DAYS * 86400)
        idx = shared_cache.get(f"expbook:index:{sym}") or {}
        meta = idx.get(exp) or {}
        idx[exp] = {"strikes": len([k for k in book if not k.startswith("_")]), "asOf": today,
                    "spot": ch.get("spot") or meta.get("spot") or 0, "firstSeen": meta.get("firstSeen") or today}
        shared_cache.set(f"expbook:index:{sym}", idx, TTL_DAYS * 86400)
    except Exception as e:
        print(f"[expbook] record failed: {e}")


@router.get("/expiries")
def expiries(symbol: str = "NIFTY"):
    """Every expiry this server has seen chain data for, oldest last. `live` ones still trade."""
    sym = symbol.upper().strip()
    import shared_cache
    idx = shared_cache.get(f"expbook:index:{sym}") or {}
    today = datetime.now(market_api.IST).date().isoformat()
    out = []
    for exp in sorted(idx):
        m = idx[exp] or {}
        out.append({"expiry": exp, "strikes": m.get("strikes") or 0, "asOf": m.get("asOf"),
                    "spot": m.get("spot") or 0, "passed": bool(exp < today)})
    return {"symbol": sym, "expiries": out, "note": "Recorded while the chains were live. Pick a passed expiry, "
            "then a strike + CE/PE, and the Trade screen loads that contract's daily candles from its recorded key."}


@router.get("/expired")
def expired(symbol: str = "NIFTY", expiry: str = ""):
    """The recorded strikes (with instrument keys) for one past expiry."""
    sym = symbol.upper().strip()
    if not expiry:
        raise HTTPException(400, "expiry=YYYY-MM-DD is required")
    import shared_cache
    book = shared_cache.get(f"expbook:{sym}:{expiry}")
    if not book:
        raise HTTPException(404, f"No diary entry for {sym} {expiry} - it was never recorded while it traded")
    rows = []
    for k in sorted((k for k in book if not k.startswith("_")), key=lambda x: float(x)):
        st = book[k] or {}
        rows.append({"strike": float(k),
                     "ce": {"key": (st.get("ce") or {}).get("key"), "lastSeen": (st.get("ce") or {}).get("lastSeen")} if st.get("ce") else None,
                     "pe": {"key": (st.get("pe") or {}).get("key"), "lastSeen": (st.get("pe") or {}).get("lastSeen")} if st.get("pe") else None})
    return {"symbol": sym, "expiry": expiry, "asOf": book.get("_asOf"), "spotAt": book.get("_spot") or 0, "rows": rows}
