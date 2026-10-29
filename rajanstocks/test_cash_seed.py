"""The cash seed is a snapshot of a past session: rows are tagged with its date, never duplicated, and never added twice."""
import json
import os

import market_api


def test_seed_rows_are_tagged_with_the_snapshot_date_and_never_duplicated():
    seed = json.load(open(market_api._static_path("picks_cash_seed.json"), encoding="utf-8"))
    sym = next(iter(seed))
    data = {"picks": [{"s": "RELIANCE", "universe": "fno", "kind": "stock", "signal": "BUY"},
                      {"s": sym, "universe": "fno", "kind": "stock", "signal": "SELL"}], "buy": [], "sell": []}
    out = market_api._inject_cash_seed_if_needed(data)
    cash = [r for r in out["picks"] if r.get("universe") == "cash"]
    assert cash and all(r["seed"] is True and len(r["seedDate"]) == 10 for r in cash)
    assert sym not in {r["s"] for r in cash}, "a symbol the scan already has was added again from the seed"
    assert len({r["s"] for r in out["picks"]}) == len(out["picks"])
    assert out["count"] == len(out["picks"]) and out["cashSeedDate"] == cash[0]["seedDate"]
    n = len(out["picks"])
    assert len(market_api._inject_cash_seed_if_needed(out)["picks"]) == n, "second call added the seed again"


def test_a_stock_in_the_fno_list_is_not_also_a_cash_row():
    d = {"picks": [{"s": "SYRMA", "universe": "fno", "ltp": 1669}, {"s": "SYRMA", "universe": "cash", "ltp": 1433}, {"s": "ABC", "universe": "cash", "ltp": 10}],
         "buy": [{"s": "SYRMA", "universe": "cash"}, {"s": "ABC", "universe": "cash"}], "sell": []}
    out = market_api._drop_cash_dupes(d)
    assert [(r["s"], r["universe"]) for r in out["picks"]] == [("SYRMA", "fno"), ("ABC", "cash")] and out["count"] == 2
    assert [r["s"] for r in out["buy"]] == ["ABC"]
