"""Sanity check: cached session logs in and the dashboard renders."""


def test_dashboard_loads(logged_in_page):
    page = logged_in_page
    assert "/app/dashboard" in page.url
    page.get_by_role("heading", name="Dashboard").wait_for(timeout=10_000)
