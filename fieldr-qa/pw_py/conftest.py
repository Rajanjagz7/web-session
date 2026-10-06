"""Shared pytest fixtures. `page` here is already logged in and on the dashboard,
using a cached session (see utils/auth.py) so each test run doesn't request a fresh OTP."""
import os

import pytest

from utils.auth import ensure_logged_in, get_or_create_storage_state
from utils.config import AUTH_STATE_PATH, ROOT

SHOTS = ROOT / "screenshots"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Save a screenshot to screenshots/ whenever a test using a page fails."""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        page = item.funcargs.get("page")
        if page is not None:
            SHOTS.mkdir(exist_ok=True)
            try:
                page.screenshot(path=str(SHOTS / f"{item.name.replace('/', '_')}.png"), full_page=True)
            except Exception:
                pass


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    return {**browser_type_launch_args, "headless": os.environ.get("FLDR_HEADLESS", "0") == "1"}


@pytest.fixture
def logged_in_page(page):
    """A page already on /app/dashboard. Reuses the cached session; if the server rejects it
    (expired), deletes the cache and logs in fresh once."""
    try:
        ensure_logged_in(page)
    except RuntimeError:
        # Only an actual bounce to the login page means the session is dead. A blank splash
        # (finding C1) is a site flake and must NOT throw away a valid cached login.
        if "/login" in page.url and AUTH_STATE_PATH.exists():
            AUTH_STATE_PATH.unlink()
            raise RuntimeError("Cached session expired (redirected to /login); deleted it. "
                               "Re-run once to log in fresh (one OTP request).")
        raise
    return page


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Every context (including the default `page` fixture's) starts with the cached login."""
    args = {**browser_context_args, "viewport": {"width": 1440, "height": 1000}}
    if AUTH_STATE_PATH.exists():
        args["storage_state"] = str(AUTH_STATE_PATH)
    return args
