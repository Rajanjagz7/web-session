"""The user's own strategies from the Backtest lab, run on daily candles as PAPER-ONLY signals.

Nothing here places an order: signals go through auto_trader.shadow_record(), the same paper log the extra strategies use, so they show
up as paper trades with a win rate and R. The rule maths mirrors public/static/btlab.js (test_custom_strategies.py checks the two agree);
a saved file is only ever data - rule types and every number are whitelisted and clamped, nothing is executed.
"""
import math

MAX_STRATEGIES = 500          # effectively no limit: each one is a few rules; the daily check loads every symbol once and reuses it
SIDES = ("long", "short", "both")

# rule type -> [(param, choices | (min, max), default)]
RULES = {
    "ma_rel": [("type", ("sma", "ema"), "sma"), ("n", (2, 400), 50), ("rel", ("above", "below"), "above")],
    "utbot": [("key", (0.3, 6), 1.0), ("atr", (2, 50), 10), ("dir", ("buy", "sell"), "buy")],
    "adx": [("n", (2, 50), 14), ("op", (">", "<"), ">"), ("v", (5, 60), 20)],
    "alma_slope": [("n", (5, 100), 34), ("dir", ("up", "down"), "up")],
    "ha_mom": [("dir", ("up", "down"), "up")],
    "ma_vs": [("type", ("sma", "ema"), "ema"), ("fast", (1, 200), 8), ("slow", (2, 400), 33), ("rel", ("above", "below"), "above")],
    "ma_cross": [("type", ("sma", "ema"), "ema"), ("fast", (1, 200), 9), ("slow", (2, 400), 21), ("dir", ("up", "down"), "up")],
    "rsi": [("n", (2, 50), 14), ("op", ("<", ">"), "<"), ("v", (1, 99), 30)],
    "breakout": [("n", (1, 250), 20), ("dir", ("high", "low"), "high")],
    "gap": [("dir", ("up", "down"), "down"), ("pct", (0.1, 20), 1)],
    "volume": [("n", (3, 100), 20), ("mult", (0.5, 10), 1.5)],
    "candle": [("dir", ("green", "red"), "green")],
    "ibs": [("op", ("<", ">"), "<"), ("v", (0, 1), 0.1)],
    "macd": [("fast", (2, 100), 12), ("slow", (3, 200), 26), ("sig", (2, 50), 9), ("dir", ("up", "down"), "up")],
    "boll": [("n", (5, 100), 20), ("k", (0.5, 5), 2), ("dir", ("above", "below"), "below")],
    "roc": [("n", (1, 250), 10), ("op", (">", "<"), ">"), ("pct", (0.5, 100), 5)],
    "supertrend": [("n", (2, 50), 10), ("mult", (0.5, 10), 3), ("dir", ("up", "down", "is up", "is down"), "up")],
    "atrp": [("n", (2, 50), 14), ("op", (">", "<"), ">"), ("v", (0.1, 20), 1.5)],
}


def _num(v, lo, hi, d):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return d
    return d if math.isnan(x) or math.isinf(x) else min(hi, max(lo, x))


def clean_rule(c):
    if not isinstance(c, dict) or c.get("t") not in RULES:
        return None
    r = {"t": c["t"]}
    for k, rng, d in RULES[c["t"]]:
        v = c.get(k)
        r[k] = (str(v) if str(v) in rng else d) if isinstance(rng[0], str) else _num(v, rng[0], rng[1], d)
    if r["t"] in ("ma_cross", "macd", "ma_vs") and r["slow"] <= r["fast"]:
        r["slow"] = r["fast"] + 1
    return r


def clean_spec(o):
    """-> a safe spec dict, or None when the strategy has no usable entry rule."""
    if not isinstance(o, dict):
        return None
    side = o.get("side") if o.get("side") in SIDES else "long"
    rl = lambda a: [x for x in (clean_rule(c) for c in (a if isinstance(a, list) else [])[:8]) if x]
    long_, short_ = rl(o.get("long")), rl(o.get("short"))
    if (side != "short" and not long_) or (side != "long" and not short_):
        return None
    st = o.get("stop") if isinstance(o.get("stop"), dict) else {}
    sid = "".join(ch for ch in str(o.get("id") or "") if ch.isalnum() or ch in "-_")[:40]
    if not sid:
        return None
    return {"id": sid, "name": str(o.get("name") or "My strategy").replace("<", "").replace(">", "")[:60], "side": side, "long": long_, "short": short_,
            "stop": {"type": "pct" if st.get("type") == "pct" else "atr", "k": _num(st.get("k"), 0.25, 10, 1.5), "pct": _num(st.get("pct"), 0.25, 30, 2)}}


def clean_all(items):
    out, seen = [], set()
    for o in (items if isinstance(items, list) else [])[:MAX_STRATEGIES]:
        s = clean_spec(o)
        if s and s["id"] not in seen:
            seen.add(s["id"])
            out.append(s)
    return out


# ---------------- indicators (same maths as ctxOf in btlab.js; NaN = not enough data) ----------------
NAN = float("nan")


def _sma(a, k):
    n, o, s = len(a), [NAN] * len(a), 0.0
    for i in range(n):
        s += a[i]
        if i >= k:
            s -= a[i - k]
        if i >= k - 1:
            o[i] = s / k
    return o


def _ema(a, k):
    o, m, e = [NAN] * len(a), 2 / (k + 1), NAN
    for i in range(len(a)):
        e = a[0] if i == 0 else a[i] * m + e * (1 - m)
        if i >= k - 1:
            o[i] = e
    return o


def _ema_raw(a, k):
    o, m, e = [NAN] * len(a), 2 / (k + 1), NAN
    for i, v in enumerate(a):
        if v != v:
            continue
        e = v if e != e else v * m + e * (1 - m)
        o[i] = e
    return o


def _rma(a, k):
    o, s = [NAN] * len(a), 0.0
    for i in range(len(a)):
        if i < k:
            s += a[i]
            if i == k - 1:
                o[i] = s / k
        else:
            o[i] = (o[i - 1] * (k - 1) + a[i]) / k
    return o


def _rma_a(a, k):
    o, s = [NAN] * len(a), 0.0
    for i in range(len(a)):
        if i < k:
            s += a[i]
            if i == k - 1:
                o[i] = s / k
        else:
            o[i] = (o[i - 1] * (k - 1) + a[i]) / k
    return o


class Ctx:
    def __init__(self, bars):
        self.n = len(bars)
        self.o = [float(b["open"]) for b in bars]
        self.h = [float(b["high"]) for b in bars]
        self.l = [float(b["low"]) for b in bars]
        self.c = [float(b["close"]) for b in bars]
        self.v = [float(b.get("volume") or 0) for b in bars]
        self._m = {}

    def get(self, key, fn):
        if key not in self._m:
            self._m[key] = fn()
        return self._m[key]

    def ma(self, typ, k):
        return self.get(f"{typ}{k}", lambda: (_ema if typ == "ema" else _sma)(self.c, k))

    def rsi(self, k):
        def f():
            o, g, l = [NAN] * self.n, 0.0, 0.0
            for i in range(1, self.n):
                ch = self.c[i] - self.c[i - 1]
                u, dn = max(ch, 0), max(-ch, 0)
                if i <= k:
                    g += u / k
                    l += dn / k
                else:
                    g, l = (g * (k - 1) + u) / k, (l * (k - 1) + dn) / k
                if i >= k:
                    o[i] = 100.0 if l == 0 else 100 - 100 / (1 + g / l)
            return o
        return self.get(f"rsi{k}", f)

    def atr(self, k):
        def f():
            tr = [self.h[0] - self.l[0]] + [max(self.h[i] - self.l[i], abs(self.h[i] - self.c[i - 1]), abs(self.l[i] - self.c[i - 1])) for i in range(1, self.n)]
            return _rma(tr, k)
        return self.get(f"atr{k}", f)

    def hh(self, k):
        return self.get(f"hh{k}", lambda: [NAN] * k + [max(self.h[i - k:i]) for i in range(k, self.n)])

    def ll(self, k):
        return self.get(f"ll{k}", lambda: [NAN] * k + [min(self.l[i - k:i]) for i in range(k, self.n)])

    def vavg(self, k):
        def f():
            o, s = [NAN] * self.n, 0.0
            for i in range(self.n):
                s += self.v[i]
                if i >= k:
                    s -= self.v[i - k]
                    o[i] = s / k
            return o
        return self.get(f"v{k}", f)

    def _tr(self):
        return [self.h[0] - self.l[0]] + [max(self.h[i] - self.l[i], abs(self.h[i] - self.c[i - 1]), abs(self.l[i] - self.c[i - 1])) for i in range(1, self.n)]

    def adx(self, k):
        def f():
            n = self.n
            pd, md = [0.0] * n, [0.0] * n
            for i in range(1, n):
                up, dn = self.h[i] - self.h[i - 1], self.l[i - 1] - self.l[i]
                pd[i] = up if (up > dn and up > 0) else 0.0
                md[i] = dn if (dn > up and dn > 0) else 0.0
            ts, ps, ms = _rma_a(self._tr(), k), _rma_a(pd, k), _rma_a(md, k)
            dx, fv = [NAN] * n, -1
            for i in range(n):
                if ts[i] != ts[i]:
                    continue
                p = 100 * ps[i] / ts[i] if ts[i] else 0.0
                m = 100 * ms[i] / ts[i] if ts[i] else 0.0
                d = p + m
                dx[i] = 100 * abs(p - m) / d if d else 0.0
                if fv < 0:
                    fv = i
            out = [NAN] * n
            if fv >= 0:
                for j, v in enumerate(_rma_a(dx[fv:], k)):
                    out[fv + j] = v
            return out
        return self.get(f"adx{k}", f)

    def alma(self, L):
        def f():
            o, m, s = [NAN] * self.n, 0.85 * (L - 1), L / 6
            w = [math.exp(-((j - m) ** 2) / (2 * s * s)) for j in range(L)]
            ws = sum(w)
            for i in range(L - 1, self.n):
                o[i] = sum(w[j] * self.c[i - L + 1 + j] for j in range(L)) / ws
            return o
        return self.get(f"alma{L}", f)

    def ha(self):
        def f():
            hc = [(self.o[i] + self.h[i] + self.l[i] + self.c[i]) / 4 for i in range(self.n)]
            ho = [0.0] * self.n
            for i in range(self.n):
                ho[i] = (self.o[0] + self.c[0]) / 2 if i == 0 else (ho[i - 1] + hc[i - 1]) / 2
            return {"hc": hc, "ho": ho, "e9": _ema_raw(hc, 9), "e21": _ema_raw(hc, 21), "bs": _ema_raw(hc, 20)}
        return self.get("ha", f)

    def utb(self, key, p):
        def f():
            n, at, st, sg = self.n, _rma_a(self._tr(), p), [NAN] * self.n, [0] * self.n
            for i in range(n):
                if at[i] != at[i]:
                    continue
                nl, src = key * at[i], self.c[i]
                ps = st[i - 1] if i > 0 and st[i - 1] == st[i - 1] else 0.0
                pv = self.c[i - 1] if i > 0 else src
                if src > ps and pv > ps:
                    s_ = max(ps, src - nl)
                elif src < ps and pv < ps:
                    s_ = min(ps, src + nl)
                elif src > ps:
                    s_ = src - nl
                else:
                    s_ = src + nl
                st[i] = s_
                if i > 0 and st[i - 1] == st[i - 1]:
                    if src > s_ and self.c[i - 1] <= st[i - 1]:
                        sg[i] = 1
                    elif src < s_ and self.c[i - 1] >= st[i - 1]:
                        sg[i] = -1
            return sg
        return self.get(f"utb{key}_{p}", f)

    def supertrend(self, k, m):
        def f():
            atr, dirs, fu, fl, d = self.atr(k), [0] * self.n, NAN, NAN, 1
            for i in range(1, self.n):
                if atr[i] != atr[i]:
                    continue
                hl2 = (self.h[i] + self.l[i]) / 2
                bu, bl, pfu, pfl = hl2 + m * atr[i], hl2 - m * atr[i], fu, fl
                fu = bu if (pfu != pfu or bu < pfu or self.c[i - 1] > pfu) else pfu
                fl = bl if (pfl != pfl or bl > pfl or self.c[i - 1] < pfl) else pfl
                if pfu == pfu:
                    if d == -1 and self.c[i] > fu:
                        d = 1
                    elif d == 1 and self.c[i] < fl:
                        d = -1
                dirs[i] = d
            return dirs
        return self.get(f"st{k}_{m}", f)


def _ok(*xs):
    return all(x == x for x in xs)


def test(c, X, i):
    """Does rule c hold on bar i (using only data up to i)?"""
    t, C = c["t"], X.c
    if t == "ma_rel":
        m = X.ma(c["type"], int(c["n"]))[i]
        return _ok(m) and (C[i] > m if c["rel"] == "above" else C[i] < m)
    if t == "utbot":
        g = X.utb(c["key"], int(c["atr"]))[i]
        return g == 1 if c["dir"] == "buy" else g == -1
    if t == "adx":
        a = X.adx(int(c["n"]))[i]
        return _ok(a) and (a > c["v"] if c["op"] == ">" else a < c["v"])
    if t == "alma_slope":
        m, a = X.alma(int(c["n"])), X.atr(14)[i]
        if i < 3 or not _ok(m[i], m[i - 3]) or not a > 0:
            return False
        v = (m[i] - m[i - 3]) / a
        return v > 0 if c["dir"] == "up" else v < 0
    if t == "ha_mom":
        h, ad = X.ha(), X.adx(14)[i]
        if i < 1 or not _ok(ad) or ad < 18:
            return False
        if c["dir"] == "up":
            return h["e9"][i] > h["e21"][i] and h["hc"][i] > h["ho"][i] and h["hc"][i] > h["hc"][i - 1] and h["hc"][i] > h["bs"][i] and h["hc"][i - 1] <= h["bs"][i - 1]
        return h["e9"][i] < h["e21"][i] and h["hc"][i] < h["ho"][i] and h["hc"][i] < h["hc"][i - 1] and h["hc"][i] < h["bs"][i] and h["hc"][i - 1] >= h["bs"][i - 1]
    if t == "ma_vs":
        a, b = X.ma(c["type"], int(c["fast"]))[i], X.ma(c["type"], int(c["slow"]))[i]
        return _ok(a, b) and (a > b if c["rel"] == "above" else a < b)
    if t == "ma_cross":
        a, b = X.ma(c["type"], int(c["fast"])), X.ma(c["type"], int(c["slow"]))
        if i < 1 or not _ok(a[i], b[i], a[i - 1], b[i - 1]):
            return False
        return (a[i - 1] <= b[i - 1] and a[i] > b[i]) if c["dir"] == "up" else (a[i - 1] >= b[i - 1] and a[i] < b[i])
    if t == "rsi":
        r = X.rsi(int(c["n"]))[i]
        return _ok(r) and (r < c["v"] if c["op"] == "<" else r > c["v"])
    if t == "breakout":
        if c["dir"] == "high":
            h = X.hh(int(c["n"]))[i]
            return _ok(h) and C[i] > h
        lo = X.ll(int(c["n"]))[i]
        return _ok(lo) and C[i] < lo
    if t == "gap":
        if i < 1:
            return False
        g = (X.o[i] - C[i - 1]) / C[i - 1] * 100
        return g >= c["pct"] if c["dir"] == "up" else g <= -c["pct"]
    if t == "volume":
        a = X.vavg(int(c["n"]))[i]
        return _ok(a) and a > 0 and X.v[i] >= c["mult"] * a
    if t == "candle":
        return C[i] > X.o[i] if c["dir"] == "green" else C[i] < X.o[i]
    if t == "ibs":
        r = X.h[i] - X.l[i]
        if not r > 0:
            return False
        v = (C[i] - X.l[i]) / r
        return v < c["v"] if c["op"] == "<" else v > c["v"]
    if t == "macd":
        f, s, g = int(c["fast"]), int(c["slow"]), int(c["sig"])

        def mk():
            ef, es = _ema_raw(C, f), _ema_raw(C, s)
            m = [a - b for a, b in zip(ef, es)]
            return m, _ema_raw(m, g)
        m, sg = X.get(f"macd{f}_{s}_{g}", mk)
        if i < s + g or i < 1:
            return False
        a, b, a0, b0 = m[i], sg[i], m[i - 1], sg[i - 1]
        return (a0 <= b0 and a > b) if c["dir"] == "up" else (a0 >= b0 and a < b)
    if t == "boll":
        n = int(c["n"])

        def mk():
            o = [NAN] * X.n
            for j in range(n - 1, X.n):
                w = C[j - n + 1:j + 1]
                s, q = sum(w), sum(x * x for x in w)
                mu = s / n
                o[j] = math.sqrt(max(0.0, q / n - mu * mu))
            return o
        sd, mu = X.get(f"sd{n}", mk)[i], X.ma("sma", n)[i]
        if not _ok(sd, mu):
            return False
        return C[i] > mu + c["k"] * sd if c["dir"] == "above" else C[i] < mu - c["k"] * sd
    if t == "roc":
        n = int(c["n"])
        if i < n:
            return False
        v = (C[i] / C[i - n] - 1) * 100
        return v >= c["pct"] if c["op"] == ">" else v <= -c["pct"]
    if t == "supertrend":
        d = X.supertrend(int(c["n"]), c["mult"])
        if i < 2 or not d[i] or not d[i - 1]:
            return False
        if c["dir"] == "is up":
            return d[i] == 1
        if c["dir"] == "is down":
            return d[i] == -1
        return (d[i] == 1 and d[i - 1] == -1) if c["dir"] == "up" else (d[i] == -1 and d[i - 1] == 1)
    if t == "atrp":
        a = X.atr(int(c["n"]))[i]
        if not _ok(a):
            return False
        v = a / C[i] * 100
        return v > c["v"] if c["op"] == ">" else v < c["v"]
    return False


def all_of(rules, X, i):
    return bool(rules) and all(test(c, X, i) for c in rules)


def signal(spec, bars, X=None):
    """The strategy's view on the LAST bar of `bars`: None, or {"side": "BUY"|"SELL", "close": px, "risk": stop distance}."""
    if len(bars) < 60:
        return None
    X = X or Ctx(bars)                      # pass one Ctx per symbol to run many strategies on it without recomputing the indicators
    i = len(bars) - 1
    long_ = spec["side"] != "short" and all_of(spec["long"], X, i)
    short_ = spec["side"] != "long" and all_of(spec["short"], X, i)
    if long_ == short_:
        return None
    a = X.atr(14)[i]
    if not a > 0:
        return None
    px, st = X.c[i], spec["stop"]
    risk = st["k"] * a if st["type"] == "atr" else px * st["pct"] / 100
    return {"side": "BUY" if long_ else "SELL", "close": px, "risk": risk} if risk > 0 else None
