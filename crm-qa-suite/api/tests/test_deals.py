import concurrent.futures as cf

import pytest

MAX_SAFE_INT = 9007199254740991


def money(amount, currency="AUD"):
    return {"amount": amount, "currency": currency}


@pytest.mark.positive
def test_create_move_win_reopen(client, pipeline, deal_factory):
    d = deal_factory(pipeline, "Flow", amount=money(50000))
    assert d["status"] == "open" and d["amount"] == money(50000)
    r = client.post(f"/deals/{d['id']}/move", json={"stageId": pipeline["stages"][2]["id"]})
    assert r.status_code == 200 and r.json()["stageId"] == pipeline["stages"][2]["id"]
    won = client.post(f"/deals/{d['id']}/won", json={})
    assert won.status_code == 200 and won.json()["status"] == "won" and won.json()["closedAt"]
    reopened = client.post(f"/deals/{d['id']}/reopen", json={})
    assert reopened.status_code == 200 and reopened.json()["status"] == "open"


@pytest.mark.negative
def test_state_machine_conflicts(client, pipeline, deal_factory):
    d = deal_factory(pipeline)
    assert client.post(f"/deals/{d['id']}/reopen", json={}).status_code == 409  # not closed
    assert client.post(f"/deals/{d['id']}/lost", json={}).status_code == 200
    assert client.post(f"/deals/{d['id']}/won", json={}).status_code == 409  # already closed
    r = client.post(f"/deals/{d['id']}/move", json={"stageId": pipeline["stages"][1]["id"]})
    assert r.status_code == 409  # closed deals cannot move


@pytest.mark.negative
def test_move_to_stage_of_another_pipeline_rejected(client, pipeline, deal_factory, cleanup, uid):
    other = client.make_pipeline(f"QA other {uid}")
    cleanup.append(("pipelines", other["id"]))
    d = deal_factory(pipeline)
    r = client.post(f"/deals/{d['id']}/move", json={"stageId": other["stages"][0]["id"]})
    assert r.status_code == 400


@pytest.mark.negative
@pytest.mark.parametrize("body", [
    {"title": "x", "pipelineId": "000000000000000000000000"},
    {"title": "x", "stageId": "nope"},
    {"title": ""},
    {"title": "t" * 201},
])
def test_create_deal_validation(client, pipeline, body):
    payload = {"pipelineId": pipeline["id"], "stageId": pipeline["stages"][0]["id"], **body}
    assert client.post("/deals", json=payload).status_code in (400, 404)


@pytest.mark.negative
def test_bad_contact_reference(client, pipeline):
    r = client.post("/deals", json={"title": "x", "pipelineId": pipeline["id"],
                                    "stageId": pipeline["stages"][0]["id"],
                                    "contactId": "000000000000000000000000"})
    assert r.status_code == 404


@pytest.mark.boundary
@pytest.mark.parametrize("amount,expected", [
    (0, 201), (1, 201), (MAX_SAFE_INT, 201), (MAX_SAFE_INT + 1, 400), (-1, 400), (10.5, 400), ("5", 400),
])
def test_amount_boundaries(client, pipeline, cleanup, amount, expected):
    r = client.post("/deals", json={"title": "amt", "pipelineId": pipeline["id"],
                                    "stageId": pipeline["stages"][0]["id"], "amount": money(amount)})
    assert r.status_code == expected, r.text[:200]
    if r.status_code == 201:
        cleanup.append(("deals", r.json()["id"]))


@pytest.mark.boundary
@pytest.mark.parametrize("currency,expected", [("AUD", 201), ("aud", 400), ("XYZ", 400), ("AU", 400), ("A" * 1000, 400)])
def test_currency_boundaries(client, pipeline, cleanup, currency, expected):
    r = client.post("/deals", json={"title": "cur", "pipelineId": pipeline["id"],
                                    "stageId": pipeline["stages"][0]["id"], "amount": money(5, currency)})
    assert r.status_code == expected
    if r.status_code == 201:
        cleanup.append(("deals", r.json()["id"]))


@pytest.mark.edge
def test_parallel_won_is_atomic(client, pipeline, deal_factory):
    d = deal_factory(pipeline)
    with cf.ThreadPoolExecutor(3) as ex:
        codes = sorted(ex.map(lambda _: client.post(f"/deals/{d['id']}/won", json={}).status_code, range(3)))
    assert codes == [200, 409, 409]


@pytest.mark.edge
def test_parallel_patches_all_succeed(client, pipeline, deal_factory):
    d = deal_factory(pipeline)
    with cf.ThreadPoolExecutor(5) as ex:
        codes = list(ex.map(lambda i: client.patch(f"/deals/{d['id']}", json={"title": f"race {i}"}).status_code, range(5)))
    assert codes == [200] * 5


@pytest.mark.edge
def test_move_to_same_stage_is_noop(client, pipeline, deal_factory):
    d = deal_factory(pipeline)
    r = client.post(f"/deals/{d['id']}/move", json={"stageId": d["stageId"]})
    assert r.status_code == 200


@pytest.mark.edge
def test_reports_match_seeded_deals(client, pipeline, deal_factory):
    deal_factory(pipeline, "a", stage_idx=0, amount=money(100))
    deal_factory(pipeline, "b", stage_idx=0, amount=money(250))
    deal_factory(pipeline, "c", stage_idx=1, amount=money(1000))
    r = client.get(f"/reports/deals.by_stage?pipeline_id={pipeline['id']}")
    assert r.status_code == 200
    rows = {row["label"]: row for row in r.json()["data"]}
    assert rows["Lead"]["count"] == 2 and rows["Lead"]["amount"] == 350
    assert rows["Qualified"]["count"] == 1 and rows["Qualified"]["amount"] == 1000
