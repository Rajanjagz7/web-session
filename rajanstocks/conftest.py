import pytest


@pytest.fixture(autouse=True)
def _clock_independent_rules(monkeypatch):
    """The 29 Oct fresh start and the one-day push test window depend on the real clock; the tests must not."""
    import common
    import push_signals
    monkeypatch.setattr(common, "FRESH_START_FROM", "2999-01-01T00:00:00+05:30")
    monkeypatch.setattr(push_signals, "NO_LIMIT_DAY", "none")
    yield
