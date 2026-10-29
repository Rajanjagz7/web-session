"""Open = Low on the Trade screen: entry is the day's LOW, stop low-10, and the signal ends once price ran / the 1.5x target traded (user's NIFTY 22850 CE example)."""
import json, pathlib, re, subprocess

SRC = (pathlib.Path(__file__).parent / "public/index.html").read_text(encoding="utf-8")


def run(leg, exp=False):
    pre = "const PD_TOL=0.5;" + re.search(r"const pdSl=.*\n", SRC).group(0)
    fn = re.search(r"function pdEval\(.*?\n  return\{levels:lv,sigs,top\}\}", SRC, re.S).group(0)
    js = f"const ZONES={{}},OPT={{sym:'NIFTY'}},fmtP=x=>x;{pre}\n{fn}\nconsole.log(JSON.stringify(pdEval({json.dumps(leg)},{str(exp).lower()})));"
    return json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)


def test_signal_is_over_once_price_ran_past_the_first_target():
    out = run(dict(ltp=141.25, open=95.0, high=183.75, low=85.8, prev=112.9))
    assert [s["st"] for s in out["sigs"]] == ["ran"] and out["top"]["st"] == "ran"          # was "hit" (BUY) at 141


def test_buy_zone_is_near_the_low_with_stop_ten_below_it():
    out = run(dict(ltp=96.0, open=95.0, high=100.0, low=85.8, prev=112.9))
    s = out["top"]
    assert s["st"] == "hit" and s["entry"] == 85.8 and s["sl"] == 75.8                      # open 95, low 86 -> stop 76


def test_fell_through_the_stop_is_not_a_buy():
    out = run(dict(ltp=70.0, open=95.0, high=100.0, low=85.8, prev=112.9))
    assert out["top"] is None or out["top"]["st"] != "hit"
