import pytest


def contact(client, cleanup, **body):
    r = client.post("/contacts", json={"firstName": "QA", **body})
    if r.status_code == 201:
        cleanup.append(("contacts", r.json()["id"]))
    return r


@pytest.mark.positive
def test_create_and_update_contact(client, cleanup, uid):
    r = contact(client, cleanup, lastName="Sharma", email=f"QA.{uid}@Example.COM", phone="+61412345678")
    assert r.status_code == 201
    c = r.json()
    assert c["email"] == f"qa.{uid}@example.com"  # lower-cased
    assert c["status"] == "lead"
    r = client.patch(f"/contacts/{c['id']}", json={"lastName": "Updated"})
    assert r.status_code == 200 and r.json()["lastName"] == "Updated"


@pytest.mark.positive
def test_archive_contact_keeps_previous_status(client, cleanup):
    c = contact(client, cleanup, status="customer").json()
    r = client.post(f"/contacts/{c['id']}/archive")
    assert r.status_code == 200
    assert r.json()["status"] == "archived" and r.json()["statusBeforeArchive"] == "customer"


@pytest.mark.positive
def test_contact_linked_to_company(client, cleanup, uid):
    co = client.create("companies", {"name": f"QA Co {uid}"})
    cleanup.append(("companies", co["id"]))
    c = contact(client, cleanup, companyId=co["id"]).json()
    assert c["companyName"] == co["name"]
    assert client.delete(f"/companies/{co['id']}").status_code == 409  # still referenced


@pytest.mark.negative
@pytest.mark.parametrize("body", [
    {"email": "notanemail"}, {"email": "a@b"}, {"email": "a b@example.com"}, {"email": "<script>@e.com"},
    {"email": None}, {"firstName": ""}, {"status": "zzz"}, {"companyId": "000000000000000000000000"},
    {"customProperties": {"undefined_prop": 1}}, {"customProperties": "x"}, {"id": "x"},
])
def test_contact_rejects_invalid(client, cleanup, body):
    assert contact(client, cleanup, **body).status_code in (400, 404)


@pytest.mark.boundary
@pytest.mark.parametrize("length,expected", [(1, 201), (200, 201), (201, 400)])
def test_contact_first_name_boundary(client, cleanup, length, expected):
    assert contact(client, cleanup, firstName="f" * length).status_code == expected


@pytest.mark.edge
def test_unicode_and_markup_in_names_round_trip(client, cleanup):
    for name in ("José 李", "<b>x</b>", "O'Brien-Smith"):
        c = contact(client, cleanup, firstName=name).json()
        assert client.get(f"/contacts/{c['id']}").json()["firstName"] == name


@pytest.mark.security
@pytest.mark.parametrize("q", ["' OR 1=1 --", ".*", "%", "\\"])
def test_search_strings_are_inert(client, q):
    r = client.get("/contacts", params={"q": q})
    assert r.status_code == 200 and r.json()["data"] == []


@pytest.mark.negative
def test_company_validation(client):
    assert client.post("/companies", json={"name": ""}).status_code == 400
    assert client.post("/companies", json={"name": "x", "status": "zzz"}).status_code == 400


# ---- known validation gaps (strict xfail: these start failing the gate the day they are fixed,
# ---- prompting removal of the marker) -----------------------------------------------------------
@pytest.mark.known_bug
@pytest.mark.xfail(reason="BUG: contact phone is not validated")
@pytest.mark.parametrize("phone", ["abc", "1"])
def test_phone_should_be_validated(client, cleanup, phone):
    assert contact(client, cleanup, phone=phone).status_code == 400


@pytest.mark.known_bug
@pytest.mark.xfail(reason="BUG: whitespace-only first name accepted")
def test_whitespace_first_name_rejected(client, cleanup):
    assert contact(client, cleanup, firstName="   ").status_code == 400


@pytest.mark.known_bug
@pytest.mark.xfail(reason="BUG: ownerActorId is not verified")
def test_unknown_owner_rejected(client, cleanup):
    assert contact(client, cleanup, ownerActorId="nope").status_code in (400, 404)


@pytest.mark.known_bug
@pytest.mark.xfail(reason="BUG: company domain not validated / normalised")
def test_company_domain_validated(client, cleanup):
    r = client.post("/companies", json={"name": "QA dom", "domain": "not a domain"})
    if r.status_code == 201:
        cleanup.append(("companies", r.json()["id"]))
    assert r.status_code == 400


@pytest.mark.known_bug
@pytest.mark.xfail(reason="BUG: inconsistent length limits (company name unlimited, email > 254)")
def test_company_name_length_capped(client, cleanup):
    r = client.post("/companies", json={"name": "N" * 300})
    if r.status_code == 201:
        cleanup.append(("companies", r.json()["id"]))
    assert r.status_code == 400
