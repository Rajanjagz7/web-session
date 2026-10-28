"""Gann time-price angle bounce (user, 28 Oct). A slanted support line is drawn from the last confirmed swing low (1x1 = the diagonal that crosses
the chart corner to corner); when the latest closed bar dips to that line and closes back above it, that is the buy-the-bounce entry (a call).
The mirror - a falling line from the last swing high, price rejected from below - is a put. Buy-only: nothing is ever sold or written.
Same maths as the chart indicator in index.html (gannCalc)."""
from __future__ import annotations

TOUCH = 0.0007          # a bar "touches" the line when its low/high gets within 0.07% of it
MIN_RR = 1.2
WINDOW = 80             # closed 15-minute bars (about 3 sessions) the 1x1 angle is scaled to


def line_value(bars, side, swing=5, ratio=1.0):
    """Return (line_by_index, anchor_idx) for the 1x1 (or `ratio`) support ('BUY') / resistance ('SELL') line over `bars`."""
    n = len(bars)
    if n < 12:
        return None, -1
    low = side == "BUY"
    ai = -1
    for i in range(n - 1 - swing, swing - 1, -1):
        v = bars[i]["l"] if low else bars[i]["h"]
        if all((bars[j]["l"] >= v) if low else (bars[j]["h"] <= v) for j in range(i - swing, i + swing + 1)):
            ai = i
            break
    if ai < 0:
        ai = min(range(n), key=lambda i: bars[i]["l"]) if low else max(range(n), key=lambda i: bars[i]["h"])
    ap = bars[ai]["l"] if low else bars[ai]["h"]
    unit = (max(b["h"] for b in bars) - min(b["l"] for b in bars)) / max(1, n) * ratio
    return [ap + (1 if low else -1) * unit * (i - ai) if i >= ai else None for i in range(n)], ai


def bounce(bars):
    """Look at the LAST bar of `bars` (closed bars only). Returns {side, line, stop, target, why} or None."""
    bars = [b for b in (bars or []) if b.get("h") and b.get("l") and b.get("c")][-WINDOW:]
    if len(bars) < 20:
        return None
    last = bars[-1]
    for side in ("BUY", "SELL"):
        ln, ai = line_value(bars, side)
        if not ln or ln[-1] is None or ln[-1] <= 0 or ai >= len(bars) - 3:
            continue
        v = ln[-1]
        if side == "BUY":
            ok = last["l"] <= v * (1 + TOUCH) and last["c"] > v and last["c"] > last["o"] and bars[-2]["c"] > (ln[-2] or v)
        else:
            ok = last["h"] >= v * (1 - TOUCH) and last["c"] < v and last["c"] < last["o"] and bars[-2]["c"] < (ln[-2] or v)
        if not ok:
            continue
        px = last["c"]
        if side == "BUY":
            stop = round(min(last["l"], v) - px * 0.0015, 2)
            target = max(b["h"] for b in bars[-30:])
            risk, reward = px - stop, target - px
        else:
            stop = round(max(last["h"], v) + px * 0.0015, 2)
            target = min(b["l"] for b in bars[-30:])
            risk, reward = stop - px, px - target
        if risk <= 0 or reward / risk < MIN_RR:
            continue
        return {"side": side, "line": round(v, 2), "stop": stop, "target": round(target, 2), "px": px, "rr": reward / risk,
                "why": f"Gann {'support' if side == 'BUY' else 'resistance'} 1x1 bounce at {v:,.2f} · stop {stop:,.2f} · target {target:,.2f} · R:R 1:{reward / risk:.1f}"}
    return None
