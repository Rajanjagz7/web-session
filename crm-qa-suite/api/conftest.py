import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import config  # noqa: E402
from crm_client import CrmClient  # noqa: E402


@pytest.fixture(scope="session")
def cfg():
    return config.load()


@pytest.fixture(scope="session")
def client(cfg):
    c = CrmClient(cfg)
    c.login()
    return c


@pytest.fixture
def uid():
    """Short unique suffix so parallel/repeated runs never collide."""
    return uuid.uuid4().hex[:8]


@pytest.fixture
def cleanup(client):
    """Register (resource, id) pairs; they are deleted in dependency order after the test."""
    created: list[tuple[str, str]] = []
    yield created
    order = {"deals": 0, "contacts": 1, "companies": 2, "pipelines": 3, "files": 4, "imports": 5}
    for res, rid in sorted(created, key=lambda x: order.get(x[0], 9)):
        client.delete(f"/{res}/{rid}")


@pytest.fixture
def pipeline(client, cleanup, uid):
    p = client.make_pipeline(f"QA pipe {uid}", stages=("Lead", "Qualified", "Proposal"))
    cleanup.append(("pipelines", p["id"]))
    return p


@pytest.fixture
def deal_factory(client, cleanup):
    def make(pipeline: dict, title: str = "QA deal", stage_idx: int = 0, **extra):
        body = {"title": title, "pipelineId": pipeline["id"], "stageId": pipeline["stages"][stage_idx]["id"], **extra}
        d = client.create("deals", body)
        cleanup.append(("deals", d["id"]))
        return d
    return make


def pytest_configure(config):
    for m in ("positive", "negative", "edge", "boundary", "security", "known_bug"):
        config.addinivalue_line("markers", f"{m}: {m} test case")
