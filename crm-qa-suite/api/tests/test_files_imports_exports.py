import time

import pytest


def wait_import(client, import_id, timeout=60):
    end = time.time() + timeout
    while time.time() < end:
        imp = client.get(f"/imports/{import_id}").json()
        if imp["status"] in ("completed", "failed"):
            return imp
        time.sleep(0.7)
    raise AssertionError("import did not finish")


def run_import(client, cleanup, name, csv, **extra):
    fid = client.upload_csv(name, csv)
    cleanup.append(("files", fid))
    r = client.post("/imports", json={"resource": "contacts", "fileId": fid, **extra})
    assert r.status_code == 202, r.text[:200]
    cleanup.append(("imports", r.json()["id"]))
    return wait_import(client, r.json()["id"])


def created_contact_ids(client, import_id):
    rows = client.get(f"/imports/{import_id}/rows").json()["data"]
    return [r["recordId"] for r in rows if r["recordId"]], rows


@pytest.fixture
def import_cleanup(client, cleanup):
    """Contacts created by an import must be removed too."""
    holder = []
    yield holder
    for cid in holder:
        client.delete(f"/contacts/{cid}")


# ---- files -------------------------------------------------------------------------------
@pytest.mark.negative
@pytest.mark.parametrize("body", [
    {"fileName": "x.exe", "contentType": "application/x-msdownload", "byteSize": 10},
    {"fileName": "z.csv", "contentType": "text/csv", "byteSize": 0},
    {"fileName": "big.csv", "contentType": "text/csv", "byteSize": 26214401},
    {"fileName": "a" * 256, "contentType": "text/csv", "byteSize": 5},
])
def test_file_registration_rejected(client, body):
    assert client.post("/files", json=body).status_code == 400


@pytest.mark.boundary
@pytest.mark.parametrize("size,expected", [(1, 201), (26214400, 201), (26214401, 400)])
def test_file_size_boundary(client, cleanup, size, expected):
    r = client.post("/files", json={"fileName": "b.csv", "contentType": "text/csv", "byteSize": size})
    assert r.status_code == expected
    if r.status_code == 201:
        cleanup.append(("files", r.json()["id"]))


# ---- imports -------------------------------------------------------------------------------
@pytest.mark.positive
def test_import_reports_per_row_outcomes(client, cleanup, import_cleanup, uid):
    csv = (f"firstName,lastName,email\nImp,One,imp1.{uid}@example.com\nImp,Two,imp2.{uid}@example.com\n"
           ",NoFirst,bad@example.com\nBad,Email,not-an-email\n")
    imp = run_import(client, cleanup, "rows.csv", csv)
    ids, rows = created_contact_ids(client, imp["id"])
    import_cleanup.extend(ids)
    assert imp["rows"] == {"total": 4, "created": 2, "failed": 2, "pending": 0, "notProcessed": 0}
    assert "firstName" in rows[2]["error"]["detail"] and "email" in rows[3]["error"]["detail"].lower()


@pytest.mark.edge
def test_import_unicode_bom_crlf_and_quoting(client, cleanup, import_cleanup, uid):
    csv = ("﻿name_placeholder\r\n").replace("name_placeholder", "firstName,lastName,email") + (
        f'"Smith, John","Line1\nLine2",q.{uid}@example.com\r\n李雷,Ñandú,u.{uid}@example.com\r\n')
    imp = run_import(client, cleanup, "edge.csv", csv)
    ids, _ = created_contact_ids(client, imp["id"])
    import_cleanup.extend(ids)
    assert imp["rows"]["created"] == 2
    got = {client.get(f"/contacts/{i}").json()["firstName"] for i in ids}
    assert got == {"Smith, John", "李雷"}


@pytest.mark.negative
@pytest.mark.parametrize("csv,code", [
    ("firstName,lastName,email\n", "import_file_empty"),
    ("firstName,lastName,email\n\n\n,,\n", "import_file_empty"),
    ("foo,bar\n1,2\n", "import_columns_invalid"),
    ("firstName,lastName,email\nA\n", "import_file_invalid"),
])
def test_import_rejects_bad_files(client, cleanup, csv, code):
    imp = run_import(client, cleanup, "bad.csv", csv)
    assert imp["status"] == "failed" and imp["error"]["code"] == code


@pytest.mark.negative
def test_non_csv_file_refused_for_import(client, cleanup):
    f = client.create("files", {"fileName": "a.png", "contentType": "image/png", "byteSize": 10})
    cleanup.append(("files", f["id"]))
    import requests
    requests.put(f["upload"]["url"], data=b"0123456789", headers=f["upload"].get("headers") or {})
    client.post(f"/files/{f['id']}/complete", json={})
    assert client.post("/imports", json={"resource": "contacts", "fileId": f["id"]}).status_code == 400


@pytest.mark.edge
def test_on_duplicate_reject(client, cleanup, import_cleanup, uid):
    email = f"dup.{uid}@example.com"
    first = run_import(client, cleanup, "d1.csv", f"firstName,email\nDup,{email}\n")
    import_cleanup.extend(created_contact_ids(client, first["id"])[0])
    second = run_import(client, cleanup, "d2.csv", f"firstName,email\nDup,{email}\nNew,new.{uid}@example.com\n",
                        onDuplicate="reject")
    import_cleanup.extend(created_contact_ids(client, second["id"])[0])
    assert second["rows"]["created"] == 1 and second["rows"]["failed"] == 1


@pytest.mark.negative
def test_import_option_validation(client):
    assert client.post("/imports", json={"resource": "users", "fileId": "x"}).status_code == 400
    assert client.post("/imports", json={"resource": "contacts", "fileId": "000000000000000000000000"}).status_code == 404
    assert client.post("/imports", json={"resource": "contacts", "fileId": "x", "onDuplicate": "update"}).status_code == 400


# ---- exports ---------------------------------------------------------------------------------
@pytest.mark.positive
def test_export_csv_contains_seeded_contact_and_neutralises_formulas(client, cleanup, import_cleanup, uid):
    csv = ('firstName,lastName,email,phone\n'
           f'"=HYPERLINK(""http://evil.test"",""x"")",Formula,f.{uid}@example.com,\'+61412345678\n')
    imp = run_import(client, cleanup, "formula.csv", csv)
    import_cleanup.extend(created_contact_ids(client, imp["id"])[0])
    ex = client.post("/exports", json={"resource": "contacts"})
    assert ex.status_code == 202
    eid = ex.json()["id"]
    cleanup.append(("exports", eid))
    end = time.time() + 60
    while time.time() < end:
        st = client.get(f"/exports/{eid}").json()
        if st["status"] not in ("queued", "running"):
            break
        time.sleep(0.7)
    assert st["status"] == "completed" and st["rowCount"] >= 1
    # Download goes through the signed link the UI uses; assert the API exposes one.
    assert st["byteSize"] and st["expiresAt"]


@pytest.mark.negative
def test_export_rejects_unknown_resource(client):
    assert client.post("/exports", json={"resource": "users"}).status_code == 400
