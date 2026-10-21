"""Primary/backup Upstash failover: switch, survive restarts, switch back and merge without losing or mixing data."""
import json

import pytest

import shared_cache as sc

P, B = ("https://p.upstash.io", "tp"), ("https://b.upstash.io", "tb")


class Fake:
    def __init__(self):
        self.db = {P: {}, B: {}}
        self.refuse = {P: False, B: False}

    def pipe(self, creds, cmds, timeout=8.0):
        if self.refuse[creds]:
            return [{"error": "ERR max requests limit exceeded. Limit: 500000"} for _ in cmds]
        d, out = self.db[creds], []
        for c in cmds:
            op = c[0]
            if op == "PING":
                out.append({"result": "PONG"})
            elif op == "GET":
                out.append({"result": d.get(c[1])})
            elif op == "SET":
                d[c[1]] = c[2]
                out.append({"result": "OK"})
            elif op == "DEL":
                out.append({"result": int(d.pop(c[1], None) is not None)})
            else:
                out.append({"result": None})
        return out


@pytest.fixture
def f(monkeypatch):
    fk = Fake()
    monkeypatch.setattr(sc, "_creds", lambda: P)
    monkeypatch.setattr(sc, "_backup_creds", lambda: B)
    monkeypatch.setattr(sc, "_pipe_to", fk.pipe)
    restart()
    return fk


def restart():                     # a new serverless instance: nothing remembered in memory
    sc._FO.update(on=False, until=0, since=None, why="")
    sc._FO_CHECKED["done"] = False


K = "rajanone:auto:v1"


def test_switch_restart_and_merge_back(f):
    f.db[P][K] = json.dumps({"cfg": {"riskPct": 1.5, "cfgAt": 100}, "trades": [{"id": "A-1", "sym": "NIFTY", "date": "2026-10-20", "entry": 100}], "log": []})
    f.refuse[P] = True
    # primary refuses -> backup, and the switch is remembered in the backup
    assert sc.kv([["GET", K]])[0]["result"] is None
    assert sc.FO_FLAG in f.db[B]
    # the backup period saves default settings and a trade that happens to reuse id A-1
    sc.kv([["SET", K, json.dumps({"cfg": {"riskPct": 0.5}, "trades": [{"id": "A-1", "sym": "BANKNIFTY", "date": "2026-10-22", "entry": 50}], "log": []})]])
    restart()                                          # every instance recycled before the primary came back
    f.refuse[P] = False
    sc.kv([["GET", "x"]])                              # first call of a fresh instance finishes the merge
    m = json.loads(f.db[P][K])
    assert m["cfg"]["riskPct"] == 1.5                  # the user's settings were not replaced by backup defaults
    assert {t["id"] for t in m["trades"]} == {"A-1", "A-1-b"}   # both trades kept
    assert sc.FO_FLAG not in f.db[B]
    assert not sc._FO["on"]


def test_no_write_when_primary_unreadable(f):
    f.db[P][K] = json.dumps({"trades": [{"id": "A-1"}]})
    f.db[B][K] = json.dumps({"trades": [{"id": "A-2"}]})
    f.refuse[P] = True
    assert sc._resync(B, P) is False
    assert json.loads(f.db[P][K])["trades"] == [{"id": "A-1"}]


def test_newer_settings_from_backup_win():
    m = sc._merge_state(K, {"cfg": {"riskPct": 1, "cfgAt": 100}}, {"cfg": {"riskPct": 2, "cfgAt": 200}})
    assert m["cfg"]["riskPct"] == 2


def test_reset_on_backup_is_respected():
    old = {"trades": [{"id": "A-1", "openedAt": "2026-10-20T10:00:00+05:30"}]}
    new = {"resetAt": "2026-10-25T09:00:00+05:30", "trades": [{"id": "A-9", "openedAt": "2026-10-26T10:00:00+05:30"}]}
    m = sc._merge_state(K, old, new)
    assert [t["id"] for t in m["trades"]] == ["A-9"]


def test_push_subscriptions_united():
    m = sc._merge_state("rajanone:push:v1", {"subs": {"a": 1}}, {"subs": {"b": 2}})
    assert set(m["subs"]) == {"a", "b"}
