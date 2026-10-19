"""Close reasons are one list per organisation, so tests restore the original list afterwards."""
import pytest

GOOD = [{"code": "price", "label": "Too expensive", "outcome": "lost"},
        {"code": "referral", "label": "Referral", "outcome": "won"}]


@pytest.fixture
def reasons(client):
    original = client.get("/close-reasons").json()["reasons"]
    yield
    client.put("/close-reasons", json={"reasons": original})


@pytest.mark.positive
def test_set_and_apply_reasons(client, reasons, pipeline, deal_factory):
    assert client.put("/close-reasons", json={"reasons": GOOD}).status_code == 200
    d = deal_factory(pipeline)
    lost = client.post(f"/deals/{d['id']}/lost", json={"reason": "price"})
    assert lost.status_code == 200 and lost.json()["closeReason"] == "price"
    client.post(f"/deals/{d['id']}/reopen", json={})
    won = client.post(f"/deals/{d['id']}/won", json={"reason": "referral"})
    assert won.status_code == 200 and won.json()["closeReason"] == "referral"


@pytest.mark.negative
@pytest.mark.parametrize("endpoint,reason", [("lost", "nonexistent"), ("lost", "referral"), ("lost", "PRICE"),
                                              ("won", "price")])
def test_reason_must_match_outcome_and_code(client, reasons, pipeline, deal_factory, endpoint, reason):
    client.put("/close-reasons", json={"reasons": GOOD})
    d = deal_factory(pipeline)
    assert client.post(f"/deals/{d['id']}/{endpoint}", json={"reason": reason}).status_code == 400


@pytest.mark.negative
@pytest.mark.parametrize("bad", [
    [{}],
    [{"code": "a", "label": "A", "outcome": "maybe"}],
    [{"code": "Bad Code!", "label": "A", "outcome": "lost"}],
    [{"code": "a", "label": "x" * 121, "outcome": "lost"}],
    [{"code": "a", "label": "A", "outcome": "lost"}, {"code": "a", "label": "B", "outcome": "lost"}],
])
def test_invalid_reason_lists(client, reasons, bad):
    assert client.put("/close-reasons", json={"reasons": bad}).status_code == 400


@pytest.mark.boundary
@pytest.mark.parametrize("count,expected", [(50, 200), (51, 400)])
def test_reason_count_boundary(client, reasons, count, expected):
    body = [{"code": f"c{i}", "label": f"L{i}", "outcome": "lost"} for i in range(count)]
    assert client.put("/close-reasons", json={"reasons": body}).status_code == expected


@pytest.mark.edge
def test_deal_keeps_reason_after_reason_removed(client, reasons, pipeline, deal_factory):
    client.put("/close-reasons", json={"reasons": GOOD})
    d = deal_factory(pipeline)
    client.post(f"/deals/{d['id']}/lost", json={"reason": "price"})
    client.put("/close-reasons", json={"reasons": [GOOD[1]]})
    assert client.get(f"/deals/{d['id']}").json()["closeReason"] == "price"
