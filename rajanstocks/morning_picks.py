"""The morning shortlist: 10-15 stock trades, strongest and best risk/reward first.  Used by the Picks screen (`top`) and the Auto Trader,
and replayed by morning_backtest.py - one ranking, so what is backtested is what trades.

Priority
  1  strength >= 75 (a confluence score of 3 or 4 of 4: trend vs 20/50-day EMA, today's range, volume) AND good risk/reward.
     A stock that is ALSO Open = Low (BUY) / Open = High (SELL) goes to the very top of this group.
  2  Open = Low  -> BUY,  Open = High -> SELL  (price has not traded beyond its opening price on that side), good risk/reward.
  3  fill-up: the best remaining BUY / SELL ideas (strength >= 50) with good risk/reward - only until the list has MIN_PICKS.
At most MAX_PICKS in all, at most MAX_PER_SECTOR from one sector.

Good risk/reward = the stop is not wide (<= MAX_RISK_PCT of the price) AND there is room to run: the nearest obstacle (the last 20 sessions' high for a BUY / low for a SELL) is at least
MIN_ROOM_R x the risk away (a stock already beyond that high / low is in free air).
"""
STRENGTH_MIN = 75
FILL_STRENGTH_MIN = 50
MIN_PICKS, MAX_PICKS = 10, 15
MAX_PER_SECTOR = 4
MAX_RISK_PCT = 5.0
MIN_ROOM_R = 1.0          # 1.5 left only ~8 trades a day on 100 liquid stocks; 1.0 gives ~10-11 (see docs/MORNING_PICKS_SENSITIVITY.md)
OPEN_TOL = 0.0005          # |open - day low (high)| <= 0.05% of the open counts as "Open = Low (High)"


def open_flags(p):
    """(open_low, open_high) from the pick's day range. Only true once price has moved off the open in that direction."""
    op, hi, lo, ltp = (p.get(k) or 0 for k in ("open", "high", "low", "ltp"))
    if op <= 0 or hi <= 0 or lo <= 0 or ltp <= 0:
        return False, False
    return (abs(op - lo) / op <= OPEN_TOL and ltp > op), (abs(hi - op) / op <= OPEN_TOL and ltp < op)


def swing_risk(p, side):
    """Stop distance of a swing trade on `side`: the pick's own stop (1.5-3 ATR beyond the 5-session swing) when it is on that side of
    the price, else 1.5 ATR (an Open = Low / High idea on a stock whose trend score points the other way or is neutral)."""
    ltp = p.get("ltp") or 0
    d = 1 if side == "BUY" else -1
    r = d * (ltp - p["stop"]) if p.get("stop") else 0.0
    return r if r > 0 else 1.5 * (p.get("atr") or ltp * 0.015)


def intraday_risk(p, side):
    """Stop distance of the intraday plan: just beyond today's extreme, kept within 0.3-0.6 ATR (same rule as the Picks screen's Intraday plan)."""
    ltp = p.get("ltp") or 0
    atr = p.get("atr") or ltp * 0.015
    ext = (ltp - (p.get("low") or ltp)) if side == "BUY" else ((p.get("high") or ltp) - ltp)
    return min(max(ext + 0.1 * atr, 0.3 * atr), 0.6 * atr)


def risk_and_room(p, side):
    """(risk in price, room in R) for a swing trade on `side`; room = distance to the last 20 sessions' extreme in the trade's direction."""
    ltp = p.get("ltp") or 0
    if ltp <= 0:
        return 0.0, 0.0
    d = 1 if side == "BUY" else -1
    risk = swing_risk(p, side)
    wall = p.get("hi20") if d > 0 else p.get("lo20")
    if not wall:
        # rows cached before hi20 / lo20 existed: use the closes of the earlier sessions in the spark (never assume free air -
        # that let every stock through the room check until the cache was rebuilt)
        sp = [x for x in (p.get("spark") or [])[:-1] if x]
        if len(sp) < 5:
            return risk, 0.0
        wall = max(sp) if d > 0 else min(sp)
    dist = d * (wall - ltp)
    return risk, 9.0 if dist <= 0 else dist / risk        # already beyond the 20-session extreme = free air


def good_rr(p, side):
    risk, room = risk_and_room(p, side)
    ltp = p.get("ltp") or 0
    return risk > 0 and risk / ltp * 100 <= MAX_RISK_PCT and room >= MIN_ROOM_R


def classify(p):
    """The shortlist entry for one Picks row (tier 1-3, side, why) or None. Pure: no I/O."""
    sig = p.get("signal")
    strength = p.get("strength") or 0
    ol, oh = open_flags(p)
    side = sig if sig in ("BUY", "SELL") else None
    flag = "BUY" if ol and sig != "SELL" else "SELL" if oh and sig != "BUY" else None
    if side and strength >= STRENGTH_MIN and good_rr(p, side):
        both = flag == side
        return {"tier": 1, "side": side, "both": both,
                "why": f"strength {strength:.0f}%" + (f" + Open = {'Low' if side == 'BUY' else 'High'}" if both else "") + f" · room {min(risk_and_room(p, side)[1], 9):.1f}R"}
    if flag and good_rr(p, flag):
        return {"tier": 2, "side": flag, "both": False, "why": f"Open = {'Low' if flag == 'BUY' else 'High'} · strength {strength:.0f}%"}
    if side and strength >= FILL_STRENGTH_MIN and good_rr(p, side):
        return {"tier": 3, "side": side, "both": False, "why": f"strength {strength:.0f}%"}
    return None


def eagle(p):
    """Eagle Trades: strength >= 75 AND Open = Low (BUY) / Open = High (SELL) agreeing with the Picks signal. No risk/reward gate and no cap on how
    many a day: on 212 F&O stocks the room-to-run gate left ~1 trade a day and did not improve accuracy (docs/EAGLE_TRADES_BACKTEST.md).
    Returns a classify()-shaped dict or None."""
    sig = p.get("signal")
    strength = p.get("strength") or 0
    ol, oh = open_flags(p)
    if strength >= STRENGTH_MIN and ((ol and sig == "BUY") or (oh and sig == "SELL")):
        return {"tier": 1, "side": sig, "both": True, "why": f"strength {strength:.0f}% + Open = {'Low' if sig == 'BUY' else 'High'}"}
    return None


def select(picks, min_n=MIN_PICKS, max_n=MAX_PICKS, stocks_only=True, per_sector=None):
    """Ranked shortlist of Picks rows: [{**pick, tier, side, rank, why}]. Tier 3 only fills up to `min_n`."""
    rows = []
    for p in picks or []:
        if stocks_only and p.get("kind") == "index":
            continue
        c = classify(p)
        if not c:
            continue
        risk, room = risk_and_room(p, c["side"])
        strength = p.get("strength") or 0
        rank = {1: 10.0, 2: 5.0, 3: 1.0}[c["tier"]] + (1.0 if c["both"] else 0.0) + strength / 100 + min(room, 3.0) / 30 + min(p.get("volx") or 0, 3) / 300
        d, ltp = (1 if c["side"] == "BUY" else -1), p["ltp"]
        lv = {"entry": round(ltp, 2), "stop": round(ltp - d * risk, 2), "target": round(ltp + d * 1.5 * risk, 2), "target2": round(ltp + d * 2.5 * risk, 2),
              "risk": round(risk, 2), "rr": 1.5}                          # levels for THE SHORTLIST SIDE (an Open = High idea on a bullish-scored stock is a SELL)
        rows.append({**p, **lv, "tier": c["tier"], "side": c["side"], "both": c["both"], "why": c["why"], "room": round(min(room, 9.0), 2), "rank": round(rank, 4)})
    rows.sort(key=lambda r: -r["rank"])
    out, per_sec = [], {}
    for r in rows:
        if len(out) >= max_n:
            break
        if r["tier"] == 3 and len(out) >= min_n:
            break
        sec = r.get("sec") or ""
        if sec and per_sec.get(sec, 0) >= (MAX_PER_SECTOR if per_sector is None else per_sector):
            continue
        per_sec[sec] = per_sec.get(sec, 0) + 1
        out.append(r)
    return out


def summary(shortlist):
    return {"count": len(shortlist), "tier1": sum(1 for r in shortlist if r["tier"] == 1), "tier2": sum(1 for r in shortlist if r["tier"] == 2),
            "tier3": sum(1 for r in shortlist if r["tier"] == 3)}
