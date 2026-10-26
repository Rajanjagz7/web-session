"""God's Eye tab - one screen that answers "what is the money doing, and what does it say for tomorrow and for expiry".

Sources (all public / already used by the app, nothing fabricated - a missing input is shown as unavailable):
  * FII / DII cash-market flows      NSE  /api/fiidiiTradeReact          (provisional, published ~18:00 IST on trading days)
  * Participant-wise F&O open int.   NSE  archives  fao_participant_oi_DDMMYYYY.csv  (Client / DII / FII / Pro, ~19:30 IST)
  * Option chain (OI, PCR, walls)    Upstox chain via market_api.chain()
  * Signal cards                     observer_api (same -10..+10 score as Picks) + DJI + a GLOBALRISK composite

Daily update: .github/workflows/fii-dii.yml runs `python gods_eye_tab.py --update` at 18:45 and 20:15 IST (Mon-Fri) and
commits public/static/fii_dii.json, which redeploys the site. The API also refreshes itself lazily after 18:00 IST if the
file is behind (stored in the shared cache), so a missed workflow run does not leave the screen a day old.

Every derived label has its rule written next to it (RULES) and is returned with the data so the screen can explain it.
Informational only - not investment advice.
"""
import csv
import io
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import date, datetime, timedelta, timezone

import requests
from fastapi import APIRouter

import shared_cache

router = APIRouter(prefix="/api/ge")
IST = timezone(timedelta(hours=5, minutes=30))
HERE = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(HERE, "public", "static", "fii_dii.json") if os.path.isdir(os.path.join(HERE, "public", "static")) \
    else os.path.join(HERE, "static", "fii_dii.json")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "*/*"}
PART_URL = "https://archives.nseindia.com/content/nsccl/fao_participant_oi_{d}.csv"
KEEP_CASH, KEEP_OI = 90, 60
HIST_KEY = "ge:hist"

RULES = {
    "fiiFutures": "FII index-futures Long % = long / (long + short) contracts. Net Long when >= 55 %, Net Short when <= 45 %, else Neutral.",
    "fiiOptions": "FII index-options bias = (call long - call short) - (put long - put short) contracts. Positive = positioned for a rise.",
    "retail": "Retail (Client) CE / PE buildup = day change in index call / put LONG contracts, as % of the previous day. "
              "Skew is Bullish when CE buildup beats PE buildup by more than 5 points, Bearish the other way, else Neutral.",
    "cash": "Cash-market net = buy - sell value (Rs crore, NSE provisional). Combined = FII + DII.",
    "pcr": "PCR = total put OI / total call OI of the nearest NIFTY expiry. >= 1.2 put writers support the market, <= 0.8 call writers cap it.",
    "walls": "Call wall = strike with the highest call OI (resistance); put wall = highest put OI (support); max pain = strike where option buyers lose the most.",
    "expected": "Expected move to expiry = ATM call + ATM put premium (the market's own straddle price).",
    "outlook": "Next-day score (-10..+10) = FII futures long % vs their own 20-session normal (+-3) + FII futures change (+-1) + FII options tilt vs their 20-session normal (+-2) "
               "+ cash flows (+-2) + PCR (+-1) + NIFTY trend score (+-2). "
               "Bullish >= +2.5, Bearish <= -2.5, else Neutral.",
    "globalRisk": "GLOBALRISK (-10 risk-off .. +10 risk-on) from US VIX level and change, S&P / Nasdaq futures, gold, crude and USD/INR moves.",
    "throughput": "Signal throughput = share of the tracked instruments whose signal was computed from fresh data in this refresh.",
}


# ---------------------------------------------------------------- NSE data
def _now():
    return datetime.now(IST)


def _num(v):
    try:
        return float(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def fetch_cash():
    """Latest FII/FPI and DII cash-market activity (Rs crore) from NSE, or None."""
    import nse_service
    rows = nse_service.nse_service._get_json("https://www.nseindia.com/api/fiidiiTradeReact")
    out = {}
    for r in rows or []:
        cat = (r.get("category") or "").upper()
        k = "fii" if "FII" in cat or "FPI" in cat else "dii" if "DII" in cat else None
        if not k:
            continue
        out[k] = {"buy": _num(r.get("buyValue")), "sell": _num(r.get("sellValue")), "net": _num(r.get("netValue"))}
        try:
            out["date"] = datetime.strptime(r.get("date"), "%d-%b-%Y").date().isoformat()
        except Exception:
            pass
    return out if out.get("fii") and out.get("dii") and out.get("date") else None


MC_URL = "https://www.moneycontrol.com/markets/fii-dii-data/"


def fetch_cash_history():
    """Last ~30 sessions of FII / DII cash-market NET (Rs crore) from moneycontrol's FII/DII page - NSE only publishes the latest day,
    so this fills the 5 / 20-day history. Net only (no gross buy / sell); NSE's own rows are never overwritten by these."""
    import re
    r = requests.get(MC_URL, headers={**UA, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"}, timeout=20)
    r.raise_for_status()
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
    rows = (((json.loads(m.group(1)) if m else {}).get("props") or {}).get("pageProps") or {}).get("FiiDiiData", {}).get("fiiDiiData") or []
    out = []
    for x in rows:
        f, d = _num(x.get("fiiCM")), _num(x.get("diiCM"))
        if x.get("date") and f is not None and d is not None:
            out.append({"date": x["date"], "fii": {"buy": None, "sell": None, "net": f}, "dii": {"buy": None, "sell": None, "net": d}, "src": "moneycontrol"})
    return out


PART_COLS = ["futIdxL", "futIdxS", "futStkL", "futStkS", "ceIdxL", "peIdxL", "ceIdxS", "peIdxS",
             "ceStkL", "peStkL", "ceStkS", "peStkS", "totL", "totS"]


def fetch_participant_oi(d):
    """Participant-wise open interest (contracts) for one session: {Client|DII|FII|Pro|TOTAL: {...}} or None if not published."""
    r = requests.get(PART_URL.format(d=d.strftime("%d%m%Y")), headers=UA, timeout=20)
    if r.status_code != 200 or b"Client" not in r.content[:2000]:
        return None
    rows = {}
    for row in csv.reader(io.StringIO(r.text)):
        if len(row) < 15:
            continue
        who = row[0].strip().strip('"')
        if who not in ("Client", "DII", "FII", "Pro", "TOTAL"):
            continue
        vals = [_num(x) for x in row[1:15]]
        if None in vals:
            continue
        rows[who] = dict(zip(PART_COLS, vals))
    return rows if "FII" in rows and "Client" in rows else None


def _trading_days_back(n, start=None):
    import nse_calendar
    d, out = (start or _now().date()), []
    while len(out) < n:
        if nse_calendar.is_trading_day(d):
            out.append(d)
        d -= timedelta(days=1)
    return out


def _load_file():
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"cash": [], "oi": [], "updatedAt": None}


def history():
    """Newest of: the committed file (daily workflow) and the shared-cache copy (lazy runtime refresh)."""
    a, b = _load_file(), shared_cache.get(HIST_KEY) or {}
    key = lambda h: ((h.get("cash") or [{}])[-1].get("date") or "", (h.get("oi") or [{}])[-1].get("date") or "")
    return b if b and key(b) > key(a) else a


def update(write_file=False, budget=None):
    """Fetch what is missing (latest cash day + recent participant-OI days) and merge into the history."""
    t_end = time.time() + budget if budget else None
    h = history()
    cash, oi = list(h.get("cash") or []), list(h.get("oi") or [])
    have_cash, have_oi = {c["date"] for c in cash}, {o["date"] for o in oi}
    notes = []
    try:
        c = fetch_cash()
        if c and c["date"] not in have_cash:
            cash.append(c)
            notes.append("cash " + c["date"])
    except Exception as e:
        notes.append(f"cash failed: {str(e)[:80]}")
    have_cash = {c["date"] for c in cash}
    if len([d for d in _trading_days_back(20) if d.isoformat() not in have_cash]) > 1 and not (t_end and time.time() > t_end):
        try:                                     # history gaps (first run, missed days): backfill net flows, keep NSE rows as they are
            added = [c for c in fetch_cash_history() if c["date"] not in have_cash]
            cash.extend(added)
            if added:
                notes.append(f"cash history +{len(added)}")
        except Exception as e:
            notes.append(f"cash history failed: {str(e)[:80]}")
    for d in sorted(_trading_days_back(8 if oi else 25)):
        if d.isoformat() in have_oi:
            continue
        if t_end and time.time() > t_end:
            break
        try:
            rows = fetch_participant_oi(d)
        except Exception as e:
            notes.append(f"oi {d} failed: {str(e)[:60]}")
            continue
        if rows:
            oi.append({"date": d.isoformat(), "rows": rows})
            notes.append("oi " + d.isoformat())
    cash = sorted({c["date"]: c for c in cash}.values(), key=lambda c: c["date"])[-KEEP_CASH:]
    oi = sorted({o["date"]: o for o in oi}.values(), key=lambda o: o["date"])[-KEEP_OI:]
    new = {"cash": cash, "oi": oi, "updatedAt": _now().isoformat(timespec="seconds"), "notes": notes}
    shared_cache.set(HIST_KEY, new, 10 * 86400)
    if write_file:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(new, f, separators=(",", ":"))
    return new


def _maybe_refresh(h):
    """After 18:00 IST on a trading day, if today's numbers are not in yet, try once every 20 minutes (any instance)."""
    import nse_calendar
    now = _now()
    today = now.date().isoformat()
    if not nse_calendar.is_trading_day(now.date()) or now.hour < 18:
        return h
    latest_cash = (h.get("cash") or [{}])[-1].get("date")
    latest_oi = (h.get("oi") or [{}])[-1].get("date")
    if latest_cash == today and (latest_oi == today or now.hour < 19):
        return h
    if not shared_cache.lock("ge-refresh", 1200):
        return h
    try:
        return update(budget=8)
    except Exception:
        return h


# ---------------------------------------------------------------- analytics
def _pct(a, b):
    return round(a / (a + b) * 100, 1) if a is not None and b is not None and (a + b) > 0 else None


def _chg_pct(now, prev):
    return round((now - prev) / prev * 100, 1) if now is not None and prev else None


def positioning(h):
    oi = h.get("oi") or []
    if not oi:
        return None
    cur, prev = oi[-1], (oi[-2] if len(oi) > 1 else None)
    R, P = cur["rows"], (prev["rows"] if prev else {})
    out = {"date": cur["date"], "prevDate": prev["date"] if prev else None, "participants": []}
    for who in ("FII", "DII", "Pro", "Client"):
        r, p = R.get(who), P.get(who)
        if not r:
            continue
        net = r["futIdxL"] - r["futIdxS"]
        pnet = (p["futIdxL"] - p["futIdxS"]) if p else None
        out["participants"].append({
            "who": "Retail (Client)" if who == "Client" else who, "key": who,
            "futLongPct": _pct(r["futIdxL"], r["futIdxS"]), "futNet": net, "futNetChg": (net - pnet) if pnet is not None else None,
            "callNet": r["ceIdxL"] - r["ceIdxS"], "putNet": r["peIdxL"] - r["peIdxS"],
            "stkFutLongPct": _pct(r["futStkL"], r["futStkS"]),
        })
    f, fp = R["FII"], P.get("FII")
    lp = _pct(f["futIdxL"], f["futIdxS"])
    out["fii"] = {
        "longPct": lp, "shortPct": round(100 - lp, 1) if lp is not None else None,
        "label": "Net Long" if lp is not None and lp >= 55 else "Net Short" if lp is not None and lp <= 45 else "Neutral",
        "net": f["futIdxL"] - f["futIdxS"],
        "netChg": (f["futIdxL"] - f["futIdxS"]) - (fp["futIdxL"] - fp["futIdxS"]) if fp else None,
        "longPctPrev": _pct(fp["futIdxL"], fp["futIdxS"]) if fp else None,
        "optBias": (f["ceIdxL"] - f["ceIdxS"]) - (f["peIdxL"] - f["peIdxS"]),
        "optBiasPrev": ((fp["ceIdxL"] - fp["ceIdxS"]) - (fp["peIdxL"] - fp["peIdxS"])) if fp else None,
    }
    c, cp = R["Client"], P.get("Client")
    ce_b = _chg_pct(c["ceIdxL"], cp["ceIdxL"]) if cp else None
    pe_b = _chg_pct(c["peIdxL"], cp["peIdxL"]) if cp else None
    skew = None
    if ce_b is not None and pe_b is not None:
        skew = "Bullish" if ce_b - pe_b > 5 else "Bearish" if pe_b - ce_b > 5 else "Neutral"
    out["retail"] = {"ceBuildup": ce_b, "peBuildup": pe_b, "skew": skew,
                     "ceLong": c["ceIdxL"], "peLong": c["peIdxL"], "futLongPct": _pct(c["futIdxL"], c["futIdxS"])}
    out["series"] = [{"date": o["date"], "fiiLongPct": _pct(o["rows"]["FII"]["futIdxL"], o["rows"]["FII"]["futIdxS"]),
                      "clientLongPct": _pct(o["rows"]["Client"]["futIdxL"], o["rows"]["Client"]["futIdxS"]),
                      "fiiOptBias": (o["rows"]["FII"]["ceIdxL"] - o["rows"]["FII"]["ceIdxS"]) - (o["rows"]["FII"]["peIdxL"] - o["rows"]["FII"]["peIdxS"])}
                     for o in oi[-21:] if "FII" in o["rows"] and "Client" in o["rows"]]
    base = out["series"][:-1][-20:]            # the 20 sessions BEFORE today: FIIs are structurally short index futures (hedges),
    if len(base) >= 5:                          # so today's reading is judged against their own recent normal, not against 50 %
        import statistics as st
        lp_ = [x["fiiLongPct"] for x in base if x["fiiLongPct"] is not None]
        ob_ = [x["fiiOptBias"] for x in base]
        out["fii"]["longPctAvg20"] = round(st.mean(lp_), 1)
        out["fii"]["longPctZ"] = round((lp - st.mean(lp_)) / max(1.0, st.pstdev(lp_)), 2) if lp is not None else None
        out["fii"]["optBiasAvg20"] = round(st.mean(ob_))
        out["fii"]["optBiasZ"] = round((out["fii"]["optBias"] - st.mean(ob_)) / max(20000.0, st.pstdev(ob_)), 2)
    return out


def cash_flows(h):
    cash = h.get("cash") or []
    if not cash:
        return None
    last = cash[-1]
    tail = lambda n, k: round(sum((c.get(k) or {}).get("net") or 0 for c in cash[-n:]), 2) if len(cash) >= n else None   # not enough sessions stored yet
    streak, sign = 0, None
    for c in reversed(cash):
        s = (c["fii"]["net"] or 0) > 0
        if sign is None:
            sign = s
        if s != sign:
            break
        streak += 1
    return {"date": last["date"], "fii": last["fii"], "dii": last["dii"],
            "combined": round((last["fii"]["net"] or 0) + (last["dii"]["net"] or 0), 2),
            "fii5": tail(5, "fii"), "dii5": tail(5, "dii"), "fii20": tail(20, "fii"), "dii20": tail(20, "dii"),
            "fiiStreak": {"days": streak, "side": "buying" if sign else "selling"}, "sessions": len(cash),
            "backfilled": sum(1 for c in cash[-20:] if c.get("src")),
            "days": [{"date": c["date"], "fii": c["fii"]["net"], "dii": c["dii"]["net"]} for c in cash[-20:]]}


def options_view(sym="NIFTY", expiry=""):
    """Nearest-expiry OI picture: totals, PCR, OI change, walls, max pain, ATM straddle -> expected range."""
    import market_api
    c = market_api.chain(sym, expiry)
    rows = c.get("rows") or []
    if not rows:
        return None
    ce = [(r["strike"], r.get("ce") or {}) for r in rows]
    pe = [(r["strike"], r.get("pe") or {}) for r in rows]
    call_oi = sum(x.get("oi") or 0 for _, x in ce)
    put_oi = sum(x.get("oi") or 0 for _, x in pe)
    call_chg = sum(x.get("oiChg") or 0 for _, x in ce)
    put_chg = sum(x.get("oiChg") or 0 for _, x in pe)
    spot, atm = c.get("spot"), c.get("atm")
    cw = max(ce, key=lambda t: t[1].get("oi") or 0)[0] if call_oi else None
    pw = max(pe, key=lambda t: t[1].get("oi") or 0)[0] if put_oi else None
    strikes = [r["strike"] for r in rows]

    def pain(k):
        return sum((k - s) * (x.get("oi") or 0) for s, x in ce if k > s) + sum((s - k) * (x.get("oi") or 0) for s, x in pe if k < s)
    max_pain = min(strikes, key=pain) if call_oi and put_oi else None
    arow = min(rows, key=lambda r: abs(r["strike"] - (atm or spot or 0)))
    straddle = ((arow.get("ce") or {}).get("ltp") or 0) + ((arow.get("pe") or {}).get("ltp") or 0)
    pcr = round(put_oi / call_oi, 2) if call_oi else None
    if call_chg > 0 and put_chg > 0:
        build = "Both sides adding (range)"
    elif put_chg > call_chg and put_chg > 0:
        build = "Put writing (supportive)"
    elif call_chg > put_chg and call_chg > 0:
        build = "Call writing (capping)"
    elif call_chg < 0 and put_chg < 0:
        build = "Unwinding"
    else:
        build = "Neutral"
    exp = c.get("expiry")
    days_left = None
    try:
        import nse_calendar
        d0, d1, n = _now().date(), date.fromisoformat(exp), 0
        d = d0
        while d < d1:
            d += timedelta(days=1)
            if nse_calendar.is_trading_day(d):
                n += 1
        days_left = n
    except Exception:
        pass
    return {"symbol": sym, "expiry": exp, "expiries": (c.get("expiries") or [])[:4], "daysLeft": days_left, "spot": spot, "atm": atm,
            "callOI": call_oi, "putOI": put_oi, "callPct": _pct(call_oi, put_oi), "putPct": _pct(put_oi, call_oi),
            "callOIChg": call_chg, "putOIChg": put_chg, "pcr": pcr, "buildup": build,
            "callWall": cw, "putWall": pw, "maxPain": max_pain, "straddle": round(straddle, 2),
            "range": [round(spot - straddle, 2), round(spot + straddle, 2)] if spot and straddle else None, "lot": c.get("lot")}


def outlook(pos, cash, opt, nifty_score):
    """Next-day read-out. Each part is shown with its contribution, so the user sees WHY."""
    parts = []

    def add(name, pts, why):
        parts.append({"name": name, "pts": round(pts, 2), "why": why})
    if pos and pos.get("fii", {}).get("longPct") is not None:
        f = pos["fii"]
        if f.get("longPctZ") is not None:
            add("FII index futures", max(-3, min(3, f["longPctZ"] * 1.5)),
                f"FIIs are {f['longPct']}% long in index futures vs a 20-session average of {f['longPctAvg20']}% ({'more' if f['longPctZ'] > 0 else 'less'} long than usual)")
        else:
            add("FII index futures", max(-3, min(3, (f["longPct"] - 50) / 5)), f"FIIs are {f['longPct']}% long in index futures ({f['label']})")
        if f.get("netChg") is not None:
            tot = abs(f["net"]) + abs(f["netChg"]) or 1
            add("FII futures change", 1 if f["netChg"] > 0 else -1 if f["netChg"] < 0 else 0,
                f"{'added' if f['netChg'] > 0 else 'cut'} {abs(f['netChg']):,.0f} net long contracts vs the previous session" if f["netChg"] else "no change")
        b = f["optBias"]
        if f.get("optBiasZ") is not None:
            add("FII index options", max(-2, min(2, f["optBiasZ"])),
                f"call net minus put net = {b:+,.0f} contracts vs a 20-session average of {f['optBiasAvg20']:+,.0f} ({'more bullish' if f['optBiasZ'] > 0 else 'more bearish'} than usual)")
        else:
            add("FII index options", max(-2, min(2, b / 100000)), f"call net minus put net = {b:+,.0f} contracts ({'bullish' if b > 0 else 'bearish' if b < 0 else 'flat'} tilt)")
    if cash:
        comb = cash["combined"]
        add("Cash flows", max(-2, min(2, comb / 2000)), f"FII {cash['fii']['net']:+,.0f} cr, DII {cash['dii']['net']:+,.0f} cr on {cash['date']} (combined {comb:+,.0f} cr)")
    if opt and opt.get("pcr") is not None:
        p = opt["pcr"]
        add("Put-call ratio", 1 if p >= 1.2 else -1 if p <= 0.8 else (p - 1) * 2.5, f"NIFTY PCR {p} for the {opt['expiry']} expiry")
    if nifty_score is not None:
        add("NIFTY trend score", max(-2, min(2, nifty_score / 4)), f"God's Eye NIFTY score {nifty_score:+.1f}")
    if not parts:
        return None
    score = round(max(-10, min(10, sum(p["pts"] for p in parts))), 1)
    agree = sum(1 for p in parts if (p["pts"] > 0) == (score > 0) and abs(p["pts"]) > 0.2)
    label = "Bullish" if score >= 2.5 else "Bearish" if score <= -2.5 else "Neutral"
    return {"score": score, "label": label, "parts": parts, "agree": agree, "of": len(parts),
            "confidence": "High" if agree >= max(3, len(parts) - 1) and label != "Neutral" else "Medium" if label != "Neutral" else "Low"}


def expiry_view(opt, out):
    if not opt:
        return None
    lv = []
    if opt.get("range"):
        lv.append(f"Market prices a move of about ±{opt['straddle']:,.0f} by expiry: {opt['range'][0]:,.0f} - {opt['range'][1]:,.0f}")
    if opt.get("putWall") and opt.get("callWall"):
        lv.append(f"Support (put wall) {opt['putWall']:,.0f} · resistance (call wall) {opt['callWall']:,.0f}")
    if opt.get("maxPain") and opt.get("spot"):
        gap = opt["maxPain"] - opt["spot"]
        lv.append(f"Max pain {opt['maxPain']:,.0f} is {abs(gap):,.0f} pts {'above' if gap > 0 else 'below'} spot - expiry-day pull is usually toward it")
    if out:
        lv.append(f"Positioning read-out is {out['label'].lower()} ({out['score']:+.1f})")
    return {"expiry": opt["expiry"], "daysLeft": opt["daysLeft"], "lines": lv}


# ---------------------------------------------------------------- cards
EXTRA_CARDS = [("DJI", "DJI", "DJ:DJI", "")]


def _global_risk(gl):
    by = {i["name"]: i for i in gl or []}
    vix = by.get("US VIX")
    if not vix:
        return None
    pts, why = 0.0, []
    lvl = vix["price"]
    pts += max(-4, min(3, (18 - lvl) / 2.5))
    why.append(f"US VIX {lvl:.2f}")
    pts += max(-2, min(2, -vix["chgPct"] / 5))
    for n, w in (("S&P 500 Fut", 2.5), ("Nasdaq 100 Fut", 2.0)):
        if n in by:
            pts += max(-2, min(2, by[n]["chgPct"] * w / 2))
    if "Gold (COMEX)" in by:
        pts -= max(-1, min(1, by["Gold (COMEX)"]["chgPct"] / 1.5))
    if "Crude (NYMEX)" in by:
        pts -= max(-1, min(1, abs(by["Crude (NYMEX)"]["chgPct"]) / 3)) if abs(by["Crude (NYMEX)"]["chgPct"]) > 2 else 0
    if "USD / INR" in by:
        pts -= max(-1, min(1, by["USD / INR"]["chgPct"] / 0.5))
    score = round(max(-10, min(10, pts)), 1)
    return {"key": "GLOBALRISK", "name": "GLOBALRISK", "score": score, "price": lvl, "chgPct": vix["chgPct"], "ccy": "",
            "label": "BULLISH" if score >= 2.5 else "BEARISH" if score <= -2.5 else "NEUTRAL", "valueLabel": "US VIX",
            "detail": {"reasons": [f"US VIX at {lvl:.2f} ({vix['chgPct']:+.2f}%)"] +
                       [f"{n} {by[n]['chgPct']:+.2f}%" for n in ("S&P 500 Fut", "Nasdaq 100 Fut", "Gold (COMEX)", "Crude (NYMEX)", "USD / INR") if n in by]}}


def cards():
    import market_api
    import observer_api
    t0 = time.time()
    base = observer_api.observer()
    items = [dict(i) for i in base["items"]]
    pool = ThreadPoolExecutor(max_workers=2)
    futs = [pool.submit(observer_api._fetch, it) for it in EXTRA_CARDS]
    done, _ = wait(futs, timeout=10)
    pool.shutdown(wait=False)
    for it, f in zip(EXTRA_CARDS, futs):
        res = f.result() if f in done else None
        if not res or "error" in res:
            old = shared_cache.get(f"obs-stale|{it[0]}")
            res = dict(old, stale=True) if old else {"key": it[0], "name": it[1], "pending": True}
        items.append(res)
    try:
        gl = market_api.global_markets()["items"]
    except Exception:
        gl = []
    gr = _global_risk(gl)
    items.append(gr or {"key": "GLOBALRISK", "name": "GLOBALRISK", "error": "global feed unavailable"})
    ok = sum(1 for i in items if i.get("score") is not None and not i.get("stale") and not i.get("error") and not i.get("pending"))
    ms = int((time.time() - t0) * 1000)
    thr = {"pct": round(ok / len(items) * 100), "ok": ok, "total": len(items), "ms": ms,
           "load": "Steady" if ms < 4000 else "Busy" if ms < 10000 else "Heavy"}
    return items, thr, base.get("marketOpen"), gl


def feeds(h):
    import market_api
    out = []
    try:
        b = market_api.budget() if hasattr(market_api, "budget") else None
        calls = (b or {}).get("calls") or {}
        out.append({"name": "Upstox (prices, chains)", "state": "OK", "detail": f"{calls.get('perMin', 0)} calls/min"})
    except Exception as e:
        out.append({"name": "Upstox (prices, chains)", "state": "Degraded", "detail": str(e)[:60]})
    try:
        kv = market_api.kv_health()
        fo = kv.get("failover") or {}
        out.append({"name": "Shared store (Upstash)", "state": "OK" if kv.get("ok") and fo.get("active") != "backup" else "Backup" if kv.get("ok") else "Down",
                    "detail": "running on the backup database" if fo.get("active") == "backup" else "primary"})
    except Exception:
        out.append({"name": "Shared store (Upstash)", "state": "Unknown", "detail": ""})
    cd = (h.get("cash") or [{}])[-1].get("date")
    od = (h.get("oi") or [{}])[-1].get("date")
    last_td = _trading_days_back(1, _now().date() if _now().hour >= 19 else _now().date() - timedelta(days=1))[0].isoformat()
    out.append({"name": "NSE FII/DII + participant OI", "state": "OK" if od and od >= last_td else "Behind",
                "detail": f"cash {cd or '—'} · OI {od or '—'}"})
    return out


_lock = threading.Lock()
_mem = {"t": 0, "data": None}


def build():
    h = _maybe_refresh(history())
    pos, cash = positioning(h), cash_flows(h)
    pool = ThreadPoolExecutor(max_workers=2)
    f_cards = pool.submit(cards)
    f_opt = pool.submit(options_view, "NIFTY", "")
    done, _ = wait([f_cards, f_opt], timeout=20)
    pool.shutdown(wait=False)
    items, thr, mkt_open, gl = f_cards.result() if f_cards in done else ([], None, None, [])
    try:
        opt = f_opt.result() if f_opt in done else None
    except Exception:
        opt = None
    nifty = next((i.get("score") for i in items if i.get("key") == "NIFTY" and i.get("score") is not None), None)
    out = outlook(pos, cash, opt, nifty)
    return {
        "asOf": _now().isoformat(timespec="seconds"), "marketOpen": mkt_open,
        "cards": items, "throughput": thr, "positioning": pos, "cash": cash, "options": opt,
        "outlook": out, "expiry": expiry_view(opt, out), "feeds": feeds(h), "rules": RULES,
        "dataUpdatedAt": h.get("updatedAt"),
        "schedule": "FII/DII and participant OI refresh daily at 18:45 and 20:15 IST (Mon-Fri), plus on demand after 18:00 IST.",
    }


@router.get("/dashboard")
def dashboard(refresh: bool = False):
    with _lock:
        ttl = 60 if (_mem["data"] or {}).get("marketOpen") else 300
        if refresh or not _mem["data"] or time.time() - _mem["t"] > ttl:
            got = None if refresh else shared_cache.get("ge:dash")
            if got and time.time() - got.get("_t", 0) < ttl:
                _mem.update(t=got["_t"], data=got)
            else:
                d = build()
                d["_t"] = time.time()
                shared_cache.set("ge:dash", d, ttl)
                _mem.update(t=time.time(), data=d)
        return _mem["data"]


@router.get("/fii-dii")
def fii_dii():
    h = history()
    return {"cash": cash_flows(h), "positioning": positioning(h), "updatedAt": h.get("updatedAt"), "rules": RULES}


@router.get("/options")
def options(symbol: str = "NIFTY", expiry: str = ""):
    return options_view(symbol.upper().strip(), expiry)


# ---------------------------------------------------------------- sectors & stocks (Nifty 500, by NSE industry)
RULES["opportunity"] = ("Opportunity score (0-100, price-based - no fundamentals or relationship data are used): 1-month return rank in the "
                        "Nifty 500 (25), 1-month return vs its own sector (15), trend - above its 20-session average and up over 5 sessions (15), "
                        "place in the 52-week range (15), volume vs its 20-session average (10), Picks strength (20; re-weighted when the "
                        "stock is not in Picks). Missing parts are left out and the rest re-weighted, never counted as zero.")
RULES["breadth"] = "Breadth = share of the sector's stocks trading above their own 20-session average close."
_sec = {"t": 0, "data": None}


def _pctile(vals):
    """value -> percentile rank 0..1 within the list."""
    import bisect
    xs = sorted(v for v in vals if v is not None)
    n = len(xs)
    if n < 2:
        return lambda v: 0.5
    return lambda v: None if v is None else bisect.bisect_left(xs, v) / (n - 1)


def _median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    m = len(xs) // 2
    return round(xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2, 2)


def _opportunity(r, r20, sec_med20):
    parts = []
    if r["ret20"] is not None:
        parts.append(("1-month return rank", 25, r20(r["ret20"])))
        m = sec_med20.get(r["sec"])
        if m is not None:
            parts.append(("vs sector (1 month)", 15, max(0.0, min(1.0, 0.5 + (r["ret20"] - m) / 20))))
    if r["aboveAvg"] is not None and r["ret5"] is not None:
        parts.append(("trend", 15, (0.6 if r["aboveAvg"] else 0) + (0.4 if r["ret5"] > 0 else 0)))
    if r["rangePos"] is not None:
        rp = r["rangePos"] / 100
        parts.append(("52-week range", 15, rp if rp <= 0.95 else 0.8))      # at the very top = extended: a little less
    if r["volx"] is not None:
        parts.append(("volume", 10, max(0.0, min(1.0, (r["volx"] - 0.5) / 1.5))))
    if r["strength"] is not None:
        parts.append(("Picks strength", 20, r["strength"] / 100))
    w = sum(p[1] for p in parts)
    if w < 40:                                  # too little to score honestly
        return None, []
    return round(sum(p[1] * p[2] for p in parts) / w * 100), [{"name": n_, "weight": round(wt / w * 100), "value": round(v * 100)} for n_, wt, v in parts]


def sectors_build():
    import equity_bhav
    import stocks_api
    uni = stocks_api._constituents("nifty500")
    q = stocks_api._quote_rows([u["s"] for u in uni])
    try:
        days = equity_bhav.load_days()
    except Exception:
        days = {}
    dates = sorted(days)[-25:]
    picks = {}
    try:                                         # only what is already cached - never start a Picks build from here
        import market_api
        cached = shared_cache.get("picks|" + date.today().isoformat()) or market_api._PK.get("data") or {}
        for p in cached.get("picks") or []:
            picks[p["s"]] = p
    except Exception:
        pass
    today = _now().date().isoformat()
    rows = []
    for u in uni:
        s, qq = u["s"], q.get(u["s"])
        if not qq or not qq.get("last"):
            continue
        last, prev = qq["last"], qq["prev"]
        closes = [days[d][s]["close"] for d in dates if s in days[d] and days[d][s].get("close")]
        vols = [days[d][s]["volume"] for d in dates if s in days[d] and days[d][s].get("volume")]
        if len(closes) < 6 and (picks.get(s) or {}).get("spark"):
            closes = list(picks[s]["spark"])
        if closes and today not in dates and abs(closes[-1] - last) / last > 0.0005:
            closes = closes + [last]                    # today's live price as the newest close
        ret5 = round((last / closes[-6] - 1) * 100, 2) if len(closes) >= 6 and closes[-6] else None
        ret20 = round((last / closes[-21] - 1) * 100, 2) if len(closes) >= 21 and closes[-21] else None
        avg20 = sum(closes[-21:-1]) / len(closes[-21:-1]) if len(closes) >= 11 else None
        vavg = sum(vols[-20:]) / len(vols[-20:]) if len(vols) >= 10 else None
        yh, yl = qq.get("yh") or None, qq.get("yl") or None
        pk = picks.get(s) or {}
        rows.append({"s": s, "n": u["n"], "sec": u["industry"] or "Other", "last": last, "chg": round((last / prev - 1) * 100, 2) if prev else None,
                     "ret5": ret5, "ret20": ret20, "aboveAvg": (last > avg20) if avg20 else None,
                     "volx": round(qq["vol"] / vavg, 2) if vavg and qq.get("vol") else None,
                     "yh": yh, "yl": yl, "fromHigh": round((last / yh - 1) * 100, 1) if yh else None,
                     "rangePos": round((last - yl) / (yh - yl) * 100) if yh and yl and yh > yl else None,
                     "signal": pk.get("signal"), "strength": pk.get("strength"), "rsi": pk.get("rsi"),
                     "fno": bool(pk) and pk.get("universe") != "cash"})
    r20 = _pctile([r["ret20"] for r in rows])
    by_sec = {}
    for r in rows:
        by_sec.setdefault(r["sec"], []).append(r)
    sec_med20 = {k: _median([x["ret20"] for x in v]) for k, v in by_sec.items()}
    for r in rows:
        r["opp"], r["oppParts"] = _opportunity(r, r20, sec_med20)
    sectors = []
    for k, v in by_sec.items():
        known = [x for x in v if x["chg"] is not None]
        ab = [x for x in v if x["aboveAvg"] is not None]
        top = sorted([x for x in v if x["opp"] is not None], key=lambda x: -x["opp"])
        sectors.append({"sec": k, "count": len(v), "share": round(len(v) / len(rows) * 100, 1),
                        "adv": sum(1 for x in known if x["chg"] > 0), "dec": sum(1 for x in known if x["chg"] < 0),
                        "chg": _median([x["chg"] for x in v]), "ret20": sec_med20.get(k),
                        "breadth": round(sum(1 for x in ab if x["aboveAvg"]) / len(ab) * 100) if ab else None,
                        "opp": _median([x["opp"] for x in v]), "top": [x["s"] for x in top[:5]],
                        "best": max(known, key=lambda x: x["chg"])["s"] if known else None,
                        "worst": min(known, key=lambda x: x["chg"])["s"] if known else None,
                        "bull": sum(1 for x in v if x["signal"] == "BUY"), "bear": sum(1 for x in v if x["signal"] == "SELL")})
    sectors.sort(key=lambda x: -x["count"])
    scored = [r for r in rows if r["opp"] is not None]
    best_sec = max([x for x in sectors if x["ret20"] is not None and x["count"] >= 5], key=lambda x: x["ret20"], default=None)
    lead = max(scored, key=lambda r: r["opp"])["s"] if scored else None
    brk = [r for r in rows if r["fromHigh"] is not None and r["fromHigh"] >= -2 and (r["volx"] or 0) >= 1.5 and r["s"] != lead]
    dip = [r for r in rows if r["ret20"] is not None and r["ret20"] <= -10 and r["aboveAvg"] is False and (r["rangePos"] or 0) >= 25]
    stand = []
    if scored:
        t = max(scored, key=lambda r: r["opp"])
        stand.append({"key": "opp", "title": "Highest Opportunity Score", "s": t["s"], "n": t["n"], "sec": t["sec"], "value": f"{t['opp']}/100",
                      "why": "best mix of 1-month strength, trend, 52-week position and volume in the Nifty 500"})
    if best_sec:
        stand.append({"key": "sector", "title": "Strongest sector (1 month)", "sec": best_sec["sec"], "value": f"{best_sec['ret20']:+.1f}%",
                      "why": f"median stock {best_sec['ret20']:+.1f}% in a month · {best_sec['breadth']}% above their 20-session average"})
    if brk:
        t = max(brk, key=lambda r: r["volx"] or 0)
        stand.append({"key": "breakout", "title": "Breakout with volume", "s": t["s"], "n": t["n"], "sec": t["sec"], "value": f"{t['volx']}x vol",
                      "why": f"within {abs(t['fromHigh'])}% of its 52-week high on {t['volx']}x its usual volume"})
    if dip:
        t = min(dip, key=lambda r: r["ret20"])
        stand.append({"key": "pullback", "title": "Deepest pullback (mid-range)", "s": t["s"], "n": t["n"], "sec": t["sec"], "value": f"{t['ret20']:+.1f}%",
                      "why": "fell the most in a month but still well above its 52-week low - a watch, not a signal"})
    known = [r for r in rows if r["chg"] is not None]
    ab = [r for r in rows if r["aboveAvg"] is not None]
    return {"asOf": _now().isoformat(timespec="seconds"), "universe": "Nifty 500", "count": len(rows),
            "adv": sum(1 for r in known if r["chg"] > 0), "dec": sum(1 for r in known if r["chg"] < 0),
            "breadth": round(sum(1 for r in ab if r["aboveAvg"]) / len(ab) * 100) if ab else None,
            "historyDays": len(dates), "sectors": sectors, "stocks": rows, "standouts": stand,
            "rules": {"opportunity": RULES["opportunity"], "breadth": RULES["breadth"]},
            "note": "Sector = NSE industry classification of the Nifty 500. Opportunity scores use prices only (no P/E, ROCE or supplier data)."}


@router.get("/sectors")
def sectors(refresh: bool = False):
    import market_api
    ttl = 120 if market_api.market_open() else 900
    with _lock:
        if not refresh and _sec["data"] and time.time() - _sec["t"] < ttl:
            return _sec["data"]
    got = None if refresh else shared_cache.get("ge:sec")
    if got and time.time() - got.get("_t", 0) < ttl:
        d = got
    else:
        d = sectors_build()
        d["_t"] = time.time()
        shared_cache.set("ge:sec", d, ttl)
    with _lock:
        _sec.update(t=time.time(), data=d)
    return d


if __name__ == "__main__":
    if "--update" in sys.argv:
        r = update(write_file=True)
        print("updated", r["updatedAt"], r.get("notes"), "cash days", len(r["cash"]), "oi days", len(r["oi"]))
