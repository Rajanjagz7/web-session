"""Indicator parity harness: run the CHART's (frontend) Z Trend math and the BACKEND's rzt.py
on identical synthetic bars and compare line values, flips and state.

Run:  python test_rzt_parity.py        (needs node on PATH)
Writes /tmp/parity_bars.json, /tmp/parity_fe.json, /tmp/parity_be.json and prints the verdict.
"""
import json
import re
import subprocess
import sys

import rzt

BARS_N = 260
LN, MULT, FLT, SW = 14, 2.0, 1, 5

# 1. deterministic synthetic bars (seeded LCG so both sides get byte-identical input)
seed = 123456789


def rnd():
    global seed
    seed = (1103515245 * seed + 12345) % (2 ** 31)
    return seed / 2 ** 31


bars, px = [], 100.0
for i in range(BARS_N):
    drift = 0.15 if (i // 30) % 2 == 0 else -0.12
    o = px
    h = o + abs(rnd()) * 1.4 + 0.05
    l = o - abs(rnd()) * 1.4 - 0.05
    c = min(max(o + drift + (rnd() - 0.5) * 1.2, l + 0.01), h - 0.01)
    bars.append({"o": round(o, 4), "h": round(h, 4), "l": round(l, 4), "c": round(c, 4)})
    px = c
json.dump(bars, open("/tmp/parity_bars.json", "w"))

# 2. backend results
be = rzt.compute(bars, LN, MULT, FLT, SW)
json.dump({"lvl": be["lvl"], "sig": be["sig"], "dir": be["dir"], "zones": be["zones"],
           "mb": be["mb"]}, open("/tmp/parity_be.json", "w"))

# 3. frontend results: extract the chart's functions from static/index.html and run them in node
html = open("static/index.html", encoding="utf-8").read()


def grab(pattern):
    m = re.search(pattern, html, re.S)
    if not m:
        raise SystemExit(f"cannot extract: {pattern}")
    if "{" not in m.group(0):                       # single-line const: return just that line
        return html[m.start():html.index("\n", m.start())]
    out, depth, started = [], 0, False
    for ch in html[m.start():]:
        out.append(ch)
        if ch == "{":
            depth += 1
            started = True
        elif ch == "}":
            depth -= 1
            if started and depth == 0:
                break
    return "".join(out)


fe_src = "\n".join([
    grab(r"const NA=n=>new Array\(n\)\.fill\(NaN\);"),
    grab(r"const C=d=>d\.map\(b=>b\.c\),Hh=[^\n]*"),
    grab(r"function emaA\(a,n,al\)\{[^\n]*"),
    grab(r"const ema=\(a,n\)=>emaA\(a,n,2/\(n\+1\)\), rma=\(a,n\)=>emaA\(a,n,1/n\);"),
    grab(r"const zip=\(a,b,f\)=>a\.map\(\(v,i\)=>f\(v,b\[i\]\)\);"),
    grab(r"function rsi\(c,n\)\{const o=NA\(c\.length\);let g=0[^\n]*"),
    grab(r"function adx\(d,n\)\{const len=d\.length[^\n]*"),
    grab(r"function trA\(d\)\{[^\n]*"),
    grab(r"const atr=\(d,n\)=>rma\(trA\(d\),n\);"),
    grab(r"function rztMB\(d\)\{[^\n]*"),
    grab(r"function rztCalc\(d,p\)\{[^\n]*"),
])
harness = fe_src + """
const bars = JSON.parse(require('fs').readFileSync('/tmp/parity_bars.json', 'utf8'));
const d = bars.map(b => ({o: b.o, h: b.h, l: b.l, c: b.c}));
const p = {len: LN, mult: MULT, flt: FLT, sw: SW};
const out = rztCalc(d, p);
require('fs').writeFileSync('/tmp/parity_fe.json', JSON.stringify({lvl: Array.from(out.lvl, v => isFinite(v) ? v : null),
  sig: Array.from(out.sig), trend: Array.from(out.trend), zones: out.z, mb: rztMB(d)}));
"""
harness = harness.replace("LN", str(LN)).replace("MULT", repr(MULT)).replace("FLT", str(FLT)).replace("SW", str(SW))
open("/tmp/parity_fe.js", "w").write(harness)
subprocess.run(["node", "/tmp/parity_fe.js"], check=True, timeout=60)
fe = json.load(open("/tmp/parity_fe.json"))

# 4. compare
lvl_diff = [abs(a - b) for a, b in zip(be["lvl"], fe["lvl"]) if a is not None and b is not None and a == a and b == b]
max_lvl = max(lvl_diff) if lvl_diff else 0.0
be_flips = [(i, s) for i, s in enumerate(be["sig"]) if s]
fe_flips = [(i, s) for i, s in enumerate(fe["sig"]) if s]
be_state = "BUY" if be["dir"][-1] > 0 else "SELL" if be["dir"][-1] < 0 else "WAIT"
fe_state = "BUY" if (fe["trend"][-1] or 0) > 0 else "SELL" if (fe["trend"][-1] or 0) < 0 else "WAIT"
mb_diff = sum(1 for a, b in zip(be["mb"], fe["mb"]) if a != b)
print(f"bars={BARS_N} params: len={LN} mult={MULT} flt={FLT} sw={SW}")
print(f"backend flips: {be_flips}")
print(f"frontend flips: {fe_flips}")
print(f"flips agree: {be_flips == fe_flips}")
print(f"max |trail line| difference: {max_lvl:.6f}")
print(f"state: backend={be_state} frontend={fe_state}")
print(f"momentum bar mismatches: {mb_diff}")
print(f"zones backend: {be['zones']}")
print(f"zones frontend: {fe['zones']}")
ok = be_flips == fe_flips and max_lvl < 0.01 and be_state == fe_state and mb_diff == 0
print("PARITY:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
