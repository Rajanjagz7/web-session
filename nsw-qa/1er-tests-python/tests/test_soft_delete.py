from config import INSTALLER_COMPANY
import time

from api_helpers import login_api, to_json


def create_throwaway_job(api_context):
    """Creates a small throwaway job via the API so this suite never has to delete/restore a job someone else is using."""
    installers_res = api_context.get("/api/v1/installers?limit=50")
    installers_body = to_json(installers_res) or {}
    installers = (
        installers_body.get("data", {}).get("installers")
        or installers_body.get("data", {}).get("items")
        or []
    )
    rajan = next((i for i in installers if i.get("companyName") == INSTALLER_COMPANY), None)
    if not rajan:
        raise Exception(f'Could not find "{INSTALLER_COMPANY}" via GET /installers to attach the throwaway job to.')

    run_id = str(int(time.time() * 1000))[-8:]
    res = api_context.post(
        "/api/v1/jobs",
        data={
            "installerId": rajan["id"],
            "activityType": "heating_cooling",
            "customerType": "residential",
            "customer": {
                "name": f"Soft Delete QA {run_id}",
                "email": f"soft.delete.qa.{run_id}@yopmail.com",
                "phoneNumber": f"4{run_id[-8:]}",
            },
            "ownReference": f"REF-DEL-{run_id}",
        },
    )
    if res.status != 201:
        raise Exception(f"Throwaway job creation failed: {res.status} {res.text()}")
    body = to_json(res)
    return body["data"]["job"]["id"], f"REF-DEL-{run_id}"


def test_full_delete_trash_restore_cycle(api_context):
    login_api(api_context)
    job_id, own_reference = create_throwaway_job(api_context)

    # Sanity: it's reachable before deleting.
    before_res = api_context.get(f"/api/v1/jobs/{job_id}")
    assert before_res.status == 200

    # Delete.
    delete_res = api_context.delete("/api/v1/jobs", data={"jobIds": [job_id]})
    assert delete_res.status == 200
    delete_body = to_json(delete_res)
    assert delete_body["data"]["deletedCount"] == 1
    assert delete_body["data"]["requested"] == 1
    assert delete_body["data"]["notFound"] == []

    # Excluded from the default (non-deleted) detail route.
    after_delete_res = api_context.get(f"/api/v1/jobs/{job_id}")
    assert after_delete_res.status == 404

    # Excluded from the default list too - searched by its own unique
    # reference rather than scanning a fixed page, since the total job count
    # keeps growing as the suite runs.
    list_res = api_context.get(f"/api/v1/jobs?search={own_reference}")
    list_body = to_json(list_res)
    assert len(list_body["data"]["jobs"]) == 0

    # Present in the staff trash view with the right flags.
    trash_res = api_context.get("/api/v1/jobs?deleted=true&limit=100")
    trash_body = to_json(trash_res)
    trashed_job = next((j for j in trash_body["data"]["jobs"] if j["id"] == job_id), None)
    assert trashed_job is not None
    assert trashed_job["isDeleted"] is True
    assert trashed_job["deletedAt"]

    # Restore.
    restore_res = api_context.post("/api/v1/jobs/restore", data={"jobIds": [job_id]})
    assert restore_res.status == 200
    restore_body = to_json(restore_res)
    assert restore_body["data"]["restoredCount"] == 1
    assert restore_body["data"]["requested"] == 1
    assert restore_body["data"]["notFound"] == []

    # Reachable again, with data intact.
    after_restore_res = api_context.get(f"/api/v1/jobs/{job_id}")
    assert after_restore_res.status == 200
    after_restore_body = to_json(after_restore_res)
    assert after_restore_body["data"]["job"]["id"] == job_id


def test_delete_is_idempotent(api_context):
    login_api(api_context)
    job_id, _ = create_throwaway_job(api_context)

    first_delete = api_context.delete("/api/v1/jobs", data={"jobIds": [job_id]})
    assert first_delete.status == 200

    second_delete = api_context.delete("/api/v1/jobs", data={"jobIds": [job_id]})
    assert second_delete.status == 200
    body = to_json(second_delete)
    # Already-deleted ids are skipped, not reported as notFound or an error.
    assert body["data"]["deletedCount"] == 0
    assert body["data"]["notFound"] == []

    # Cleanup: restore so this job doesn't linger deleted.
    api_context.post("/api/v1/jobs/restore", data={"jobIds": [job_id]})


def test_deleting_nonexistent_job_id_reports_it_in_not_found(api_context):
    login_api(api_context)
    fake_id = "000000000000000000000000"
    res = api_context.delete("/api/v1/jobs", data={"jobIds": [fake_id]})
    assert res.status == 200
    body = to_json(res)
    assert body["data"]["deletedCount"] == 0
    assert fake_id in body["data"]["notFound"]
