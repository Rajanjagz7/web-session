"""Tenant isolation and authentication. Needs a second project in the same workspace for the isolation cases."""
import pytest


@pytest.fixture
def other_project_id(client, cfg):
    me = client.get("/workspaces", params={"limit": 100}).json()["data"]
    for ws in me:
        projects = client.get(f"/workspaces/{ws['id']}/projects", params={"limit": 100}).json()["data"]
        for p in projects:
            if p["id"] != cfg.project_id:
                return p["id"]
    pytest.skip("account has no second project to test isolation against")


@pytest.mark.security
@pytest.mark.negative
def test_other_project_cannot_read_or_change_records(client, pipeline, deal_factory, other_project_id):
    d = deal_factory(pipeline)
    for method, path, body in [("GET", f"/pipelines/{pipeline['id']}", None),
                               ("GET", f"/deals/{d['id']}", None),
                               ("PATCH", f"/deals/{d['id']}", {"title": "cross"}),
                               ("DELETE", f"/pipelines/{pipeline['id']}", None)]:
        r = client.request(method, path, json=body, project_id=other_project_id)
        assert r.status_code == 404, f"{method} {path} leaked: {r.status_code}"


@pytest.mark.security
def test_cannot_create_deal_with_other_projects_pipeline(client, pipeline, other_project_id):
    r = client.post("/deals", json={"title": "x", "pipelineId": pipeline["id"],
                                    "stageId": pipeline["stages"][0]["id"]}, project_id=other_project_id)
    assert r.status_code == 400


@pytest.mark.security
def test_requires_session(client):
    r = client.get("/pipelines", authenticated=False)
    assert r.status_code == 401


@pytest.mark.security
@pytest.mark.parametrize("pid", ["zzz", "000000000000000000000000"])
def test_unknown_project_is_forbidden(client, pid):
    assert client.get("/pipelines", project_id=pid).status_code == 403


@pytest.mark.negative
def test_missing_project_header(client):
    r = client.request("GET", "/pipelines")
    r2 = client.session.get(f"{client.cfg.api}/pipelines", headers={"accept": "application/json"})
    assert r.status_code == 200 and r2.status_code == 400


@pytest.mark.negative
def test_bad_env_mode_rejected(client):
    assert client.get("/pipelines", headers={"crm-env-mode": "zzz"}).status_code == 400
