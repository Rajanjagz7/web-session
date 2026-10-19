import pytest

from api import config
from api.api_client import APIClient


@pytest.fixture(scope="session")
def anon_client() -> APIClient:
    return APIClient()


@pytest.fixture(scope="session")
def admin_client() -> APIClient:
    if not config.ADMIN_EMAIL or not config.ADMIN_PASSWORD:
        pytest.skip("ADMIN_EMAIL / ADMIN_PASSWORD not set (see .env.example)")
    client = APIClient()
    resp = client.login(config.ADMIN_EMAIL, config.ADMIN_PASSWORD)
    assert resp.status_code == 200, f"login failed: {resp.status_code}"
    return client
