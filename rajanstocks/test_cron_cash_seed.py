import pytest
from fastapi import HTTPException

import market_api


def test_cash_seed_cron_needs_the_secret_and_reports_the_build(monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "s3")
    with pytest.raises(HTTPException) as e:
        market_api.cron_cash_seed(authorization="Bearer wrong", x_admin_key="", key="")
    assert e.value.status_code == 401
    monkeypatch.setattr(market_api, "ensure_universe", lambda: None)
    monkeypatch.setattr(market_api, "picks", lambda refresh=False, response=None: {"picks": [{"universe": "cash"}, {"universe": "fno"}, {"universe": "fno"}], "complete": True})
    r = market_api.cron_cash_seed(authorization="Bearer s3", x_admin_key="", key="")
    assert r["ok"] and r["rows"] == 3 and r["cashRows"] == 1 and r["fnoRows"] == 2


def test_key_in_the_address_works_for_a_manual_run(monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "s3")
    monkeypatch.setattr(market_api, "ensure_universe", lambda: None)
    monkeypatch.setattr(market_api, "picks", lambda refresh=False, response=None: {"picks": [], "complete": False})
    assert market_api.cron_cash_seed(authorization="", x_admin_key="", key="s3")["ok"]
    with pytest.raises(HTTPException):
        market_api.cron_cash_seed(authorization="", x_admin_key="", key="nope")
