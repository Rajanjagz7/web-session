"""Add Quote through the UI: the happy path, and the validation on an incomplete Sections tab.

Uses the customer "Quinn Crashcheck..." and the item "QA Crashcheck Item..." created on 2026-09-21.
"""
import re

from pages.quote_page import QuotePage
from utils.au_data import stamp


def _start(page) -> QuotePage:
    quote = QuotePage(page)
    quote.open_new()
    customer = quote.pick_customer("Crashcheck")
    assert "Crashcheck" in customer
    quote.fill_description(f"Switchboard upgrade and 6 downlights, quote QA {stamp()}")
    quote.next()
    return quote


def test_incomplete_section_shows_inline_errors_and_sends_nothing(logged_in_page):
    page = logged_in_page
    quote = _start(page)
    sent = []
    page.on("request", lambda r: sent.append(r.url) if r.method == "POST" and "/quote/create" in r.url else None)
    quote.save().click()
    page.wait_for_timeout(1500)
    errors = quote.inline_errors()
    assert errors, "expected 'Please enter ...' messages for the empty section/line"
    assert any("section" in e.lower() for e in errors), errors
    assert not sent, f"Save sent a request despite validation errors: {sent}"


def test_create_quote_with_one_line_item(logged_in_page):
    page = logged_in_page
    quote = _start(page)
    quote.fill_section_name("Switchboard and lighting")
    item = quote.pick_item("QA Crashcheck")
    assert "QA Crashcheck" in item
    page.wait_for_timeout(800)
    quote.set_quantity("2")
    values = quote.line_values()
    assert values["unit"], f"picking an item should fill the unit: {values}"
    assert float(values["rate"] or 0) > 0, f"picking an item should fill the rate: {values}"
    with page.expect_response(lambda r: "/quote/create" in r.url and r.request.method == "POST") as resp:
        quote.save().click()
    assert resp.value.status == 200, f"quote/create returned {resp.value.status}"
    # After Save the app opens the new quote itself (number QTE-nnnn, status Draft), not the list.
    page.get_by_text(re.compile(r"QTE-\d+")).first.wait_for(timeout=20_000)
    assert page.get_by_text("Draft", exact=True).first.is_visible()
    assert "$20.00" in page.locator("main").first.inner_text(), "2 x $10.00 should total $20.00"
