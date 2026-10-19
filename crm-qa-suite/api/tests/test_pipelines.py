import pytest

PIPE_NAME_MAX = 120
MAX_STAGES = 50


# ---------- positive ----------------------------------------------------------
@pytest.mark.positive
def test_create_pipeline_with_stages(client, cleanup, uid):
    p = client.make_pipeline(f"QA create {uid}", stages=("Lead", "Won"))
    cleanup.append(("pipelines", p["id"]))
    assert [s["name"] for s in p["stages"]] == ["Lead", "Won"]
    assert [s["order"] for s in p["stages"]] == [0, 1]
    assert p["archivedAt"] is None


@pytest.mark.positive
def test_rename_archive_unarchive(client, pipeline):
    r = client.patch(f"/pipelines/{pipeline['id']}", json={"name": "QA renamed"})
    assert r.status_code == 200 and r.json()["name"] == "QA renamed"
    assert client.post(f"/pipelines/{pipeline['id']}/archive").status_code == 200
    assert client.post(f"/pipelines/{pipeline['id']}/unarchive").status_code == 200


@pytest.mark.positive
def test_stage_add_rename_reorder_delete(client, pipeline):
    pid = pipeline["id"]
    r = client.post(f"/pipelines/{pid}/stages", json={"name": "Extra"})
    assert r.status_code == 201
    stages = r.json()["stages"]
    extra = next(s for s in stages if s["name"] == "Extra")
    assert client.patch(f"/pipelines/{pid}/stages/{extra['id']}", json={"name": "Extra2"}).status_code == 200
    ids = [s["id"] for s in stages][::-1]
    r = client.post(f"/pipelines/{pid}/stages/reorder", json={"stageIds": ids})
    assert r.status_code == 200
    assert [s["id"] for s in r.json()["stages"]] == ids
    assert [s["order"] for s in r.json()["stages"]] == list(range(len(ids)))
    assert client.delete(f"/pipelines/{pid}/stages/{extra['id']}").status_code == 200


@pytest.mark.positive
def test_unicode_name(client, cleanup):
    p = client.make_pipeline("QA 测试 🚀 ñ", stages=("Étape 1",))
    cleanup.append(("pipelines", p["id"]))
    assert p["name"] == "QA 测试 🚀 ñ"


# ---------- negative ----------------------------------------------------------
@pytest.mark.negative
@pytest.mark.parametrize("body,fragment", [
    ({"name": "", "stages": [{"name": "A"}]}, "/name"),
    ({"name": "x", "stages": []}, "at least one stage"),
    ({"name": 123, "stages": [{"name": "A"}]}, "/name"),
    ({"name": None, "stages": [{"name": "A"}]}, "/name"),
    ({"name": "x", "stages": "abc"}, "/stages"),
    ({"name": "x", "stages": [{"name": ""}]}, "/stages/0/name"),
    ({"name": "x", "stages": [{"name": "A"}], "isAdmin": True}, "Unrecognized"),
])
def test_create_rejects_invalid_body(client, body, fragment):
    r = client.post("/pipelines", json=body)
    assert r.status_code == 400
    assert fragment in r.json()["detail"]


@pytest.mark.negative
def test_malformed_json(client):
    r = client.request("POST", "/pipelines", data="{bad", headers={"content-type": "application/json"})
    assert r.status_code == 400


@pytest.mark.negative
def test_duplicate_stage_names_rejected_case_insensitively(client):
    r = client.post("/pipelines", json={"name": "x", "stages": [{"name": "Lead"}, {"name": "lead"}]})
    assert r.status_code == 400


@pytest.mark.negative
def test_unknown_and_malformed_ids(client):
    assert client.get("/pipelines/000000000000000000000000").status_code == 404
    assert client.get("/pipelines/zzz").status_code == 400


@pytest.mark.negative
def test_cannot_delete_last_active_stage(client, cleanup, uid):
    p = client.make_pipeline(f"QA last {uid}", stages=("Only",))
    cleanup.append(("pipelines", p["id"]))
    assert client.delete(f"/pipelines/{p['id']}/stages/{p['stages'][0]['id']}").status_code == 409


@pytest.mark.negative
def test_reorder_requires_every_stage_exactly_once(client, pipeline):
    ids = [s["id"] for s in pipeline["stages"]]
    for bad in (ids[:-1], ids + [ids[0]], ids[:-1] + ["nope"]):
        assert client.post(f"/pipelines/{pipeline['id']}/stages/reorder", json={"stageIds": bad}).status_code == 400


@pytest.mark.negative
def test_archive_twice_conflicts(client, pipeline):
    assert client.post(f"/pipelines/{pipeline['id']}/archive").status_code == 200
    assert client.post(f"/pipelines/{pipeline['id']}/archive").status_code == 409


@pytest.mark.negative
def test_patch_empty_body_rejected(client, pipeline):
    assert client.patch(f"/pipelines/{pipeline['id']}", json={}).status_code == 400


# ---------- boundary ------------------------------------------------------------
@pytest.mark.boundary
@pytest.mark.parametrize("length,expected", [(1, 201), (PIPE_NAME_MAX, 201), (PIPE_NAME_MAX + 1, 400)])
def test_name_length_boundary(client, cleanup, length, expected):
    r = client.post("/pipelines", json={"name": "n" * length, "stages": [{"name": "A"}]})
    assert r.status_code == expected
    if r.status_code == 201:
        cleanup.append(("pipelines", r.json()["id"]))


@pytest.mark.boundary
@pytest.mark.parametrize("count,expected", [(1, 201), (MAX_STAGES, 201), (MAX_STAGES + 1, 400)])
def test_stage_count_boundary(client, cleanup, count, expected):
    r = client.post("/pipelines", json={"name": f"QA {count} stages",
                                        "stages": [{"name": f"S{i}"} for i in range(count)]})
    assert r.status_code == expected
    if r.status_code == 201:
        cleanup.append(("pipelines", r.json()["id"]))


@pytest.mark.boundary
@pytest.mark.parametrize("limit,expected", [(0, 400), (1, 200), (100, 200), (101, 400), (-1, 400), ("abc", 400)])
def test_list_limit_boundary(client, limit, expected):
    assert client.get(f"/pipelines?limit={limit}").status_code == expected


# ---------- delete guards -------------------------------------------------------
@pytest.mark.negative
def test_delete_guards_with_deals(client, pipeline, deal_factory):
    deal = deal_factory(pipeline, "guarded")
    assert client.delete(f"/pipelines/{pipeline['id']}/stages/{pipeline['stages'][0]['id']}").status_code == 409
    assert client.delete(f"/pipelines/{pipeline['id']}").status_code == 409
    # archive instead of delete is allowed
    assert client.post(f"/pipelines/{pipeline['id']}/archive").status_code == 200
    assert client.get(f"/deals/{deal['id']}").status_code == 200


# ---------- security --------------------------------------------------------------
@pytest.mark.security
def test_xss_name_is_stored_verbatim_not_executed(client, cleanup):
    payload = "<img src=x onerror=alert(1)> QA \"q\" & 'a'"
    p = client.make_pipeline(payload, stages=("A",))
    cleanup.append(("pipelines", p["id"]))
    assert client.get(f"/pipelines/{p['id']}").json()["name"] == payload  # escaped at render time (see UI tests)


# ---------- known bugs / open design questions (strict xfail: flips red when fixed) ----
@pytest.mark.known_bug
@pytest.mark.xfail(reason="DESIGN: duplicate pipeline names are allowed")
def test_duplicate_pipeline_names_rejected(client, cleanup, uid):
    a = client.make_pipeline(f"QA dup {uid}")
    cleanup.append(("pipelines", a["id"]))
    r = client.post("/pipelines", json={"name": f"QA dup {uid}".upper(), "stages": [{"name": "A"}]})
    if r.status_code == 201:
        cleanup.append(("pipelines", r.json()["id"]))
    assert r.status_code in (400, 409)


@pytest.mark.known_bug
@pytest.mark.xfail(reason="DESIGN: stages can be added to an archived pipeline")
def test_cannot_add_stage_to_archived_pipeline(client, pipeline):
    client.post(f"/pipelines/{pipeline['id']}/archive")
    assert client.post(f"/pipelines/{pipeline['id']}/stages", json={"name": "Late"}).status_code in (400, 409)
