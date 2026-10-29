from datetime import datetime
import market_api as m


def at(h, mi):
    return datetime(2026, 10, 29, h, mi, tzinfo=m.IST)


def test_volume_fraction_grows_through_the_day():
    f = [m.day_volume_frac(at(*t)) for t in ((9, 10), (9, 30), (10, 15), (12, 30), (15, 0), (15, 40))]
    assert f == sorted(f) and f[0] == 0.10 and f[-1] == 1.0
    assert 0.2 < m.day_volume_frac(at(10, 15)) < 0.3


def test_a_morning_surge_counts_as_a_surge():
    # 0.6x of a normal DAY done by 10:15 is ~2.3x the normal pace for that time - a rider, but raw volx (0.6) never reaches 2
    assert 0.6 / m.day_volume_frac(at(10, 15)) >= 2.0
