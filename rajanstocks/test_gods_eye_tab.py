"""Rules of the God's Eye tab on fixed inputs (no network)."""
import gods_eye_tab as g


def _row(fl, fs, cl, cs, pl, ps):
    return {"futIdxL": fl, "futIdxS": fs, "futStkL": 1, "futStkS": 1, "ceIdxL": cl, "peIdxL": pl, "ceIdxS": cs, "peIdxS": ps,
            "ceStkL": 0, "peStkL": 0, "ceStkS": 0, "peStkS": 0, "totL": 0, "totS": 0}


def _hist(days):
    oi = []
    for i, (fii, client) in enumerate(days):
        oi.append({"date": f"2026-10-{i + 1:02d}", "rows": {"FII": _row(*fii), "Client": _row(*client), "DII": _row(*fii), "Pro": _row(*fii)}})
    return {"oi": oi, "cash": [{"date": "2026-10-20", "fii": {"buy": 10, "sell": 5, "net": 5}, "dii": {"buy": 1, "sell": 2, "net": -1}}]}


def test_fii_long_pct_label_and_change():
    h = _hist([((60, 40, 10, 5, 10, 5), (50, 50, 100, 0, 100, 0)), ((70, 30, 10, 5, 10, 5), (50, 50, 110, 0, 90, 0))])
    p = g.positioning(h)
    assert p["fii"]["longPct"] == 70.0 and p["fii"]["label"] == "Net Long"
    assert p["fii"]["netChg"] == 40 - 20
    assert p["retail"]["ceBuildup"] == 10.0 and p["retail"]["peBuildup"] == -10.0 and p["retail"]["skew"] == "Bullish"


def test_fii_judged_against_its_own_normal():
    base = [((10, 90, 0, 100, 0, 100), (50, 50, 1, 0, 1, 0))] * 20      # FIIs usually 10 % long
    h = _hist(base + [((20, 80, 0, 100, 0, 100), (50, 50, 1, 0, 1, 0))])
    p = g.positioning(h)
    assert p["fii"]["label"] == "Net Short"                              # absolute label
    assert p["fii"]["longPctAvg20"] == 10.0 and p["fii"]["longPctZ"] > 0  # but longer than usual
    o = g.outlook(p, None, None, None)
    assert o["parts"][0]["pts"] > 0


def test_outlook_label_thresholds_and_missing_inputs():
    assert g.outlook(None, None, None, None) is None
    o = g.outlook(None, None, {"pcr": 1.5, "expiry": "2026-10-27"}, 8.0)
    assert o["score"] == 1 + 2 and o["label"] == "Bullish"
    o = g.outlook(None, None, {"pcr": 0.6, "expiry": "2026-10-27"}, -8.0)
    assert o["label"] == "Bearish"


def test_cash_totals_need_enough_sessions():
    c = g.cash_flows(_hist([((1, 1, 1, 1, 1, 1), (1, 1, 1, 1, 1, 1))]))
    assert c["combined"] == 4 and c["fii5"] is None and c["sessions"] == 1


def test_global_risk_unavailable_without_vix():
    assert g._global_risk([]) is None
    r = g._global_risk([{"name": "US VIX", "price": 30, "chgPct": 20}])
    assert r["label"] == "BEARISH"
