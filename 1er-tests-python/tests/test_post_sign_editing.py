import re
import time

from playwright.sync_api import expect

from helpers import login, open_job_detail, open_job_detail_tab, control_for_label

# A signed, "Site Assessment Complete" job with at least one product - reused
# across this file's tests since they're read/no-persist-expected checks,
# not destructive edits (the whole point is that Save doesn't persist, so
# re-running these repeatedly is safe).
SIGNED_JOB = "M8N000114"


def _count_requests_on_save(page, save_action) -> list:
    """
    All the BUG-02 tests below currently assert the ACTUAL (buggy) behaviour
    - zero requests fired - so the suite catches a regression either way: if
    this starts failing because a request DOES fire, that's BUG-02 being
    fixed and these assertions should be flipped to check the request
    succeeds and the edited value persists after reload.
    """
    fired: list = []

    def handler(req):
        if req.method in ("POST", "PATCH", "PUT"):
            fired.append(f"{req.method} {req.url}")

    page.on("request", handler)
    save_action()
    page.wait_for_timeout(2500)
    page.remove_listener("request", handler)
    return fired


class TestBug02SaveFiresNoRequest:
    def test_job_information_tab_editing_own_reference_and_save_fires_no_request(self, page):
        login(page)
        open_job_detail(page, SIGNED_JOB)

        ref_field = page.locator('input[name="ownReference"]').first
        ref_field.fill("REGRESSION-CHECK-" + str(int(time.time() * 1000)))

        fired = _count_requests_on_save(
            page, lambda: page.get_by_role("button", name=re.compile(r"^save$", re.I)).first.click()
        )
        assert fired == []

    def test_post_install_details_tab_editing_ces_number_and_save_fires_no_request(self, page):
        login(page)
        open_job_detail(page, SIGNED_JOB)
        open_job_detail_tab(page, "Post Install Details")

        page.get_by_placeholder("Enter Certificate of Electrical Safety Number").fill(
            "REGRESSION-CES-" + str(int(time.time() * 1000))
        )

        fired = _count_requests_on_save(
            page, lambda: page.get_by_role("button", name=re.compile(r"^save$", re.I)).first.click()
        )
        assert fired == []

    def test_products_tab_editing_existing_product_via_pencil_icon_and_save_fires_no_request(self, page):
        login(page)
        open_job_detail(page, SIGNED_JOB)
        open_job_detail_tab(page, "Products")

        edit_icon = page.get_by_text("Product 1", exact=True).first.locator("xpath=following-sibling::*[1]")
        edit_icon.click()
        page.wait_for_timeout(800)

        brand_control = page.locator(".select__control").nth(0)
        brand_control.click()
        page.wait_for_timeout(400)
        options = page.get_by_role("option").all_text_contents()
        page.get_by_role("option", name=options[0], exact=True).click()

        fired = _count_requests_on_save(
            page,
            lambda: page.get_by_role("button", name=re.compile(r"^save$", re.I)).first.click(force=True),
        )
        assert fired == []


def test_bug07_two_products_can_share_an_identical_serial_number(page):
    """KNOWN BUG (BUG-07): no duplicate-serial-number detection."""
    login(page)
    open_job_detail(page, SIGNED_JOB)
    open_job_detail_tab(page, "Products")

    shared_serial = "SN-DUP-REGRESSION-" + str(int(time.time() * 1000))

    def add_product():
        page.get_by_role("button", name=re.compile("add another product", re.I)).click(force=True)
        page.wait_for_timeout(700)
        panel = page.get_by_text(re.compile(r"Add Product \d+"), exact=False).last.locator(
            'xpath=ancestor::*[.//button[normalize-space(text())="Add"]][1]'
        )

        eq = control_for_label(panel, "Original Equipment")
        eq.click(force=True)
        page.wait_for_timeout(350)
        page.get_by_role("option", name="No existing system (new installation)", exact=True).click()
        page.wait_for_timeout(400)

        install = control_for_label(panel, "Replacement or new installation")
        install.click(force=True)
        page.wait_for_timeout(350)
        install_opts = page.get_by_role("option").all_text_contents()
        page.get_by_role("option", name=install_opts[0], exact=True).click()
        page.wait_for_timeout(400)

        brand = control_for_label(panel, "New Unit - Brand")
        brand.click(force=True)
        page.wait_for_timeout(350)
        page.get_by_role("option", name="ACTRON AIR", exact=True).click()
        page.wait_for_timeout(400)

        model = control_for_label(panel, "New Unit - Model Number")
        model.click(force=True)
        page.wait_for_timeout(350)
        model_opts = page.get_by_role("option").all_text_contents()
        page.get_by_role("option", name=model_opts[0], exact=True).click()
        page.wait_for_timeout(400)

        page.get_by_placeholder(re.compile("serial", re.I)).last.fill(shared_serial)
        page.get_by_role("button", name=re.compile(r"^add$", re.I)).last.click(force=True)
        page.wait_for_timeout(1500)

    add_product()
    add_product()

    # Both products should now display the identical serial with no warning.
    open_job_detail(page, SIGNED_JOB)
    open_job_detail_tab(page, "Products")
    serial_fields = page.locator(f'input[value="{shared_serial}"]')
    expect(serial_fields).to_have_count(2)
