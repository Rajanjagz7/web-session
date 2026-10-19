"""Robustness / hostile-input tests found during the 2026-10-01 break-it session."""
import base64
import concurrent.futures as cf

import pytest


# ---------- pagination integrity and cursor tampering (all pass today) ------------------------------
@pytest.fixture
def twenty_five_contacts(client):
    with cf.ThreadPoolExecutor(5) as ex:
        ids = list(ex.map(lambda i: client.create("contacts", {"firstName": f"Pg{i:02d}"})["id"], range(25)))
    yield ids
    for i in ids:
        client.delete(f"/contacts/{i}")


def walk(client, size):
    seen, cur = [], None
    while True:
        r = client.get(f"/contacts?limit={size}" + (f"&starting_after={cur}" if cur else ""))
        assert r.status_code == 200
        body = r.json()
        seen += [x["id"] for x in body["data"]]
        if not body["has_more"]:
            return seen
        cur = body["next_cursor"]


@pytest.mark.edge
@pytest.mark.parametrize("size", [1, 7, 25, 100])
def test_pagination_is_complete_and_duplicate_free(client, twenty_five_contacts, size):
    seen = walk(client, size)
    assert len(seen) == len(set(seen))
    assert set(twenty_five_contacts) <= set(seen)


@pytest.mark.security
@pytest.mark.negative
@pytest.mark.parametrize("make", [
    lambda cur: cur[:-6],                                   # truncated
    lambda cur: "!!!!",                                     # not base64
    lambda cur: "A" * 5000,                                 # oversized
    lambda cur: "%00",                                      # null byte
    lambda cur: "' OR 1=1",                                 # injection-shaped
    lambda cur: base64.urlsafe_b64encode(bytes([b ^ 1 if i == 55 else b for i, b in enumerate(
        base64.urlsafe_b64decode(cur + "=" * (-len(cur) % 4)))])).decode().rstrip("="),  # one flipped byte
])
def test_tampered_cursors_are_rejected(client, twenty_five_contacts, make):
    cur = client.get("/contacts?limit=2").json()["next_cursor"]
    r = client.get(f"/contacts?limit=2&starting_after={make(cur)}")
    assert r.status_code == 400


@pytest.mark.security
def test_cursor_is_bound_to_resource_and_project(client, twenty_five_contacts, cfg):
    cur = client.get("/contacts?limit=2").json()["next_cursor"]
    assert client.get(f"/companies?limit=2&starting_after={cur}").status_code == 400
    other = next((p["id"] for ws in client.get("/workspaces", params={"limit": 100}).json()["data"]
                  for p in client.get(f"/workspaces/{ws['id']}/projects", params={"limit": 100}).json()["data"]
                  if p["id"] != cfg.project_id), None)
    if other:
        assert client.get(f"/contacts?limit=2&starting_after={cur}", project_id=other).status_code == 400


# ---------- body parsing (all pass today) ------------------------------------------------------------
@pytest.mark.negative
@pytest.mark.parametrize("body", ["[1,2,3]", '"x"', "123", "null", "{}", '{"a":' * 2000 + "1" + "}" * 2000,
                                  '{"name":"x","stages":[{"name":"a"}]}garbage', '{"name":"x","stages":[{"name":NaN}]}'])
def test_malformed_bodies_get_400(client, body):
    r = client.request("POST", "/pipelines", data=body, headers={"content-type": "application/json"})
    assert r.status_code == 400


@pytest.mark.boundary
@pytest.mark.known_bug
@pytest.mark.xfail(strict=False, reason="BUG (intermittent, ~1 in 5): an oversized body sometimes gets an empty 502 from the proxy instead of 413")
def test_oversized_body_is_413(client):
    # The body limit sits between 1 MB (parsed, then rejected as an unknown key) and 2 MB (413).
    r = client.request("POST", "/pipelines", data='{"pad":"' + "A" * 10_000_000 + '"}',
                       headers={"content-type": "application/json"})
    assert r.status_code == 413


@pytest.mark.negative
@pytest.mark.parametrize("ident", ["%00", "-1", "1e5", "null", "undefined", "[object Object]", "g" * 24, "%F0%9F%98%80"])
def test_hostile_ids_never_500(client, ident):
    assert client.get(f"/pipelines/{ident}").status_code in (400, 404)


# ---------- known bugs found in the break-it session (strict xfail) ------------------------------------
@pytest.mark.known_bug
@pytest.mark.xfail(reason="BUG: a null byte in the search query returns HTTP 500")
@pytest.mark.parametrize("resource", ["contacts", "companies", "deals", "files"])
def test_null_byte_in_search_is_a_400_not_500(client, resource):
    assert client.get(f"/{resource}?q=a%00b").status_code < 500


@pytest.mark.known_bug
@pytest.mark.xfail(reason="BUG: HTTP TRACE returns an unstructured 500")
def test_trace_method_is_not_a_500(client):
    assert client.request("TRACE", "/pipelines").status_code < 500


@pytest.mark.known_bug
@pytest.mark.xfail(reason="HARDENING: text/plain bodies are parsed as JSON (CORS 'simple request' content type)")
def test_non_json_content_type_is_rejected(client, cleanup):
    r = client.request("POST", "/pipelines", data='{"name":"ct","stages":[{"name":"a"}]}',
                       headers={"content-type": "text/plain"})
    if r.status_code == 201:
        cleanup.append(("pipelines", r.json()["id"]))
    assert r.status_code in (400, 415)


@pytest.mark.known_bug
@pytest.mark.xfail(reason="DESIGN: control characters / null bytes / newlines are accepted in names")
@pytest.mark.parametrize("name", ["a\x00b", "a\nb", "\x01\x02", "a\r\nX-Evil: 1"])
def test_control_characters_rejected_in_names(client, cleanup, name):
    r = client.post("/pipelines", json={"name": name, "stages": [{"name": "s"}]})
    if r.status_code == 201:
        cleanup.append(("pipelines", r.json()["id"]))
    assert r.status_code == 400


@pytest.mark.known_bug
@pytest.mark.xfail(reason="BUG: invalid UTF-8 bytes are accepted and silently replaced with U+FFFD")
def test_invalid_utf8_is_rejected(client, cleanup):
    r = client.request("POST", "/pipelines", data=b'{"name":"\xff\xfe","stages":[{"name":"a"}]}',
                       headers={"content-type": "application/json"})
    if r.status_code == 201:
        cleanup.append(("pipelines", r.json()["id"]))
    assert r.status_code == 400


@pytest.mark.known_bug
@pytest.mark.xfail(reason="DESIGN: name limit counts UTF-16 units, so 100 emoji (200 units) are refused as '>120 characters'")
def test_length_limit_counts_characters_not_utf16_units(client, cleanup):
    r = client.post("/pipelines", json={"name": "😀" * 100, "stages": [{"name": "s"}]})
    if r.status_code == 201:
        cleanup.append(("pipelines", r.json()["id"]))
    assert r.status_code == 201
