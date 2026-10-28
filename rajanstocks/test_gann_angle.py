import gann_angle as g


def _bars():
    b = []
    for i in range(21):
        b.append(dict(t=i, o=100 - i * .3 + .1, h=100 - i * .3 + .5, l=100 - i * .3 - .5, c=100 - i * .3))
    for i in range(21, 56):
        px = 94 + (i - 20) * 1.5
        b.append(dict(t=i, o=px - .2, h=px + .5, l=px - .5, c=px + .2))
    for i in range(56, 66):
        px = 146 - (i - 55) * 1.5
        b.append(dict(t=i, o=px + 1, h=px + 1.4, l=px - .3, c=px))
    return b


def _with_bounce(close_off):
    b, v = _bars(), 130.0
    for _ in range(20):
        v = g.line_value(b + [dict(t=99, o=v + .5, h=v + 6, l=v, c=v + 3)], "BUY")[0][-1]
    return b + [dict(t=99, o=v + .5, h=v + 6, l=v, c=v + close_off)], v


def test_support_bounce_is_a_buy():
    t, v = _with_bounce(3)
    r = g.bounce(t)
    assert r and r["side"] == "BUY" and r["stop"] < v and r["target"] > r["px"]


def test_close_under_the_line_is_no_trade():
    t, v = _with_bounce(-1)
    assert g.bounce(t) is None


def test_too_few_bars():
    assert g.bounce(_bars()[:10]) is None
