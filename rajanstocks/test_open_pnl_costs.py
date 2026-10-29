"""Open server trades carry costPctEff so the Journal can show open P&L after the estimated exit cost (state itself is not changed)."""
import nse_calendar
import stock_trader


def test_stock_status_open_trades_carry_cost_pct(monkeypatch):
    st = {"trades": [{"status": "OPEN", "sym": "TCS", "entry": 100, "qty": 1, "unrealised": 5, "hz": "intraday"},
                     {"status": "CLOSED", "sym": "INFY", "net": 3, "hz": "intraday", "cost": 0.2}],
          "log": [], "lastRun": "2099-01-01T00:00:00+05:30"}
    monkeypatch.setattr(stock_trader, "_load", lambda cached=False, verify=False: st)
    monkeypatch.setattr(stock_trader, "_cash", lambda s: (0, 0, 0))
    monkeypatch.setattr(nse_calendar, "session_open", lambda now: False)
    out = stock_trader.status()
    assert out["open"][0]["costPctEff"] == stock_trader.CFG["costPct"]
    assert "costPctEff" not in st["trades"][0]            # a copy: saved state is untouched
