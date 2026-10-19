from config import EMAIL, PASSWORD


def login_api(api_context):
    res = api_context.post("/api/v1/auth/admin/login", data={"email": EMAIL, "password": PASSWORD})
    if not res.ok:
        raise Exception(f"Admin API login failed: {res.status} {res.text()}")
    return res


def to_json(res):
    try:
        return res.json()
    except Exception:
        return None
