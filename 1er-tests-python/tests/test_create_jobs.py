import re
import time

import pytest
from playwright.sync_api import expect

from config import INSTALLER_COMPANY
from helpers import (
    login,
    open_add_job_drawer,
    fill_job_form,
    submit_job,
    expect_field_error,
    expect_job_created,
    submit_and_report,
)

# Unique per test run so re-runs don't collide on ABN/phone/email.
RUN_ID = str(int(time.time() * 1000))[-8:]


def uniq(n: int) -> str:
    return f"{RUN_ID}{n}"


def abn(n: int) -> str:
    return uniq(n).rjust(11, "0")[-11:]


def phone(n: int) -> str:
    return "4" + uniq(n).rjust(8, "0")[-8:]


# ---------------------------------------------------------------------------
# Valid job creation - Australian data
# ---------------------------------------------------------------------------

VALID_CASES = [
    dict(
        label="Heating & Cooling / Residential / Phone lead / Sydney CBD",
        customerName="Olivia Bennett",
        addressSearch="1 George Street Sydney",
        postcode="2000",
        activityType="Heating & Cooling",
        buildingType="Residential Building",
        leadMethod="Phone",
        installationDate="28-08-2026",
    ),
    dict(
        label="Hot Water Heat Pump / Residential / Website lead / Artarmon",
        customerName="Jack Sullivan",
        addressSearch="50 Elizabeth Street Artarmon",
        postcode="2064",
        activityType="Hot Water Heat Pump",
        buildingType="Residential Building",
        newSystem="Heat pump",
        leadMethod="Website",
        installationDate="29-08-2026",
    ),
    dict(
        label="Heating & Cooling / Small Business / Referral lead / North Sydney",
        customerName="Mia Robertson",
        addressSearch="123 Walker Street North Sydney",
        postcode="2060",
        activityType="Heating & Cooling",
        buildingType="Small Business Site",
        leadMethod="Referral",
        installationDate="01-09-2026",
    ),
    dict(
        label="Hot Water Heat Pump / Small Business / Email lead / St Leonards",
        customerName="Noah Fitzgerald",
        addressSearch="66 Pacific Highway St Leonards",
        postcode="2065",
        activityType="Hot Water Heat Pump",
        buildingType="Small Business Site",
        # 'New system' is only shown for Hot Water Heat Pump + Residential
        # Building - Small Business Site skips it.
        leadMethod="Email",
        installationDate="02-09-2026",
    ),
    dict(
        label="Heating & Cooling / Residential / Phone lead / Dulwich Hill",
        customerName="Ava Thompson",
        addressSearch="789 New Canterbury Road Dulwich Hill",
        postcode="2203",
        activityType="Heating & Cooling",
        buildingType="Residential Building",
        leadMethod="Phone",
        installationDate="03-09-2026",
    ),
    dict(
        label="Hot Water Heat Pump / Residential / Referral lead / Punchbowl",
        customerName="Lucas Whitfield",
        addressSearch="898 Punchbowl Road Punchbowl",
        postcode="2196",
        activityType="Hot Water Heat Pump",
        buildingType="Residential Building",
        newSystem="Heat pump",
        leadMethod="Referral",
        installationDate="04-09-2026",
    ),
]


@pytest.mark.parametrize(
    "i,data",
    list(enumerate(VALID_CASES)),
    ids=[c["label"] for c in VALID_CASES],
)
def test_valid_job_creation(page, i, data):
    login(page)
    dialog = open_add_job_drawer(page)

    fields = dict(
        customerName=data["customerName"],
        email=f"{data['customerName'].lower().replace(' ', '.')}.{uniq(i)}@yopmail.com",
        phone=phone(i),
        abnAcn=abn(i),
        addressSearch=data["addressSearch"],
        postcode=data["postcode"],
        activityType=data["activityType"],
        buildingType=data["buildingType"],
        leadMethod=data["leadMethod"],
        ownReference=f"REF-{RUN_ID}-{i}",
        installationDate=data["installationDate"],
        installer=INSTALLER_COMPANY,
        fillEquipment=True,
    )
    if "newSystem" in data:
        fields["newSystem"] = data["newSystem"]

    fill_job_form(dialog, fields)
    submit_job(dialog)
    expect_job_created(page, dialog, data["customerName"])


# ---------------------------------------------------------------------------
# Invalid field formats
# ---------------------------------------------------------------------------


def _format_base(i: int) -> dict:
    return dict(
        customerName=f"Format Test {i}",
        email=f"format.test.{uniq(i)}@yopmail.com",
        phone=phone(100 + i),
        abnAcn=abn(100 + i),
        addressSearch="1 George Street Sydney",
        postcode="2000",
        activityType="Heating & Cooling",
        buildingType="Residential Building",
        leadMethod="Phone",
        ownReference=f"REF-{RUN_ID}-INV{i}",
        installationDate="10-09-2026",
        installer=INSTALLER_COMPANY,
        fillEquipment=True,
    )


def test_invalid_job_1_malformed_email_rejected(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _format_base(1)
    fields["email"] = "not-an-email"
    fill_job_form(dialog, fields)
    submit_job(dialog)
    expect_field_error(dialog, "Enter a valid email")
    expect(dialog.get_by_placeholder("Enter customer name")).to_be_visible()


def test_invalid_job_2_abn_too_short_rejected(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _format_base(2)
    fields["abnAcn"] = "12345"
    fill_job_form(dialog, fields)
    submit_job(dialog)
    expect_field_error(dialog, "ABN/ACN must be exactly 11 digits")
    expect(dialog.get_by_placeholder("Enter customer name")).to_be_visible()


def test_invalid_job_3_abn_over_11_digits_silently_truncated(page):
    """
    Actual app behaviour (found by running this case): the ABN/ACN input has
    a maxlength of 11, so typing 13 digits just truncates to the first 11
    rather than showing "must be exactly 11 digits" - the job submits
    successfully. This documents that real behaviour instead of assuming a
    rejection that doesn't happen.
    """
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _format_base(3)
    fields["abnAcn"] = "1234567890123"
    fill_job_form(dialog, fields)

    abn_field = dialog.get_by_placeholder("12345678901")
    expect(abn_field).to_have_value("12345678901")  # truncated to first 11 digits

    submit_job(dialog)
    expect_job_created(page, dialog, "Format Test 3")


def test_invalid_job_4_email_and_phone_blank(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _format_base(4)
    del fields["email"]
    del fields["phone"]
    fill_job_form(dialog, fields)
    submit_job(dialog)
    expect_field_error(dialog, "Email is required")
    expect_field_error(dialog, "Phone is required")
    # Fields that were filled must not also show as required.
    expect(dialog.get_by_text("Customer name is required", exact=True)).not_to_be_visible()
    expect(dialog.get_by_placeholder("Enter customer name")).to_be_visible()


# ---------------------------------------------------------------------------
# Negative / edge cases
# ---------------------------------------------------------------------------


def test_negative_job_1_fully_empty_form_shows_every_required_field_error(page):
    login(page)
    dialog = open_add_job_drawer(page)
    submit_job(dialog)

    for message in [
        "Customer name is required",
        "Email is required",
        "Phone is required",
        "ABN/ACN is required",
        "Site address is required",
        "Postcode is required",
        "Activity type is required",
        "Building type is required",
        "Method of lead generation is required",
        "Own reference is required",
        "Installation date is required",
        "Installer (company) is required",
    ]:
        expect_field_error(dialog, message)
    expect(dialog.get_by_placeholder("Enter customer name")).to_be_visible()


def test_negative_job_2_installer_blank_everything_else_valid(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fill_job_form(
        dialog,
        dict(
            customerName="Missing Installer",
            email=f"missing.installer.{uniq(5)}@yopmail.com",
            phone=phone(105),
            abnAcn=abn(105),
            addressSearch="1 George Street Sydney",
            postcode="2000",
            activityType="Heating & Cooling",
            buildingType="Residential Building",
            leadMethod="Phone",
            ownReference=f"REF-{RUN_ID}-NEG2",
            installationDate="11-09-2026",
            # installer intentionally omitted
        ),
    )
    submit_job(dialog)
    expect_field_error(dialog, "Installer (company) is required")
    expect(dialog.get_by_text("Customer name is required", exact=True)).not_to_be_visible()
    expect(dialog.get_by_placeholder("Enter customer name")).to_be_visible()


def test_negative_job_3_site_address_blank_everything_else_valid(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fill_job_form(
        dialog,
        dict(
            customerName="Missing Address",
            email=f"missing.address.{uniq(6)}@yopmail.com",
            phone=phone(106),
            abnAcn=abn(106),
            postcode="2000",
            activityType="Heating & Cooling",
            buildingType="Residential Building",
            leadMethod="Phone",
            ownReference=f"REF-{RUN_ID}-NEG3",
            installationDate="12-09-2026",
            installer=INSTALLER_COMPANY,
            # addressSearch intentionally omitted
        ),
    )
    submit_job(dialog)
    expect_field_error(dialog, "Site address is required")
    expect(dialog.get_by_placeholder("Enter customer name")).to_be_visible()


def test_negative_job_4_extremely_long_name_and_reference_do_not_crash(page):
    login(page)
    dialog = open_add_job_drawer(page)
    long_name = ("Very Long Customer Name " * 15).strip()  # ~375 chars
    long_ref = f"REF-{RUN_ID}-" + "X" * 200

    fill_job_form(
        dialog,
        dict(
            customerName=long_name,
            email=f"long.input.{uniq(7)}@yopmail.com",
            phone=phone(107),
            abnAcn=abn(107),
            addressSearch="1 George Street Sydney",
            postcode="2000",
            activityType="Heating & Cooling",
            buildingType="Residential Building",
            leadMethod="Phone",
            ownReference=long_ref,
            installationDate="13-09-2026",
            installer=INSTALLER_COMPANY,
            fillEquipment=True,
        ),
    )
    submit_job(dialog)
    page.wait_for_timeout(2000)

    # The app must still be alive and on the Jobs page either way (accepted
    # the long input or showed a validation message) - it must not crash.
    expect(page).to_have_url(re.compile(r"/jobs"))


def test_negative_job_5_html_script_injection_name_handled_safely(page):
    login(page)
    dialog = open_add_job_drawer(page)

    alert_fired = {"value": False}

    def on_dialog(js_dialog):
        alert_fired["value"] = True
        js_dialog.dismiss()

    page.on("dialog", on_dialog)

    fill_job_form(
        dialog,
        dict(
            customerName="<script>alert('xss')</script> O'Brien-Smith",
            email=f"xss.test.{uniq(8)}@yopmail.com",
            phone=phone(108),
            abnAcn=abn(108),
            addressSearch="1 George Street Sydney",
            postcode="2000",
            activityType="Heating & Cooling",
            buildingType="Residential Building",
            leadMethod="Phone",
            ownReference=f"REF-{RUN_ID}-NEG5",
            installationDate="14-09-2026",
            installer=INSTALLER_COMPANY,
            fillEquipment=True,
        ),
    )
    submit_job(dialog)
    page.wait_for_timeout(2000)

    # The script tag must never actually execute as JS.
    assert alert_fired["value"] is False
    expect(page).to_have_url(re.compile(r"/jobs"))


# ---------------------------------------------------------------------------
# Negative / edge cases: special characters & symbol boundary values
# ---------------------------------------------------------------------------

# Deliberately punctuation/symbol-heavy, includes the exact characters
# requested: !@#!$)(@$&%$*9
SPECIAL_CHARS = "!@#!$)(@$&%$*9^&*()_+-=[]{}|;:'<>,.?/~"


def test_negative_job_6_special_characters_in_name_and_reference(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fill_job_form(
        dialog,
        dict(
            customerName=SPECIAL_CHARS,
            email=f"special.chars.{uniq(9)}@yopmail.com",
            phone=phone(109),
            abnAcn=abn(109),
            addressSearch="1 George Street Sydney",
            postcode="2000",
            activityType="Heating & Cooling",
            buildingType="Residential Building",
            leadMethod="Phone",
            ownReference=SPECIAL_CHARS,
            installationDate="15-09-2026",
            installer=INSTALLER_COMPANY,
            fillEquipment=True,
        ),
    )

    name_value = dialog.get_by_placeholder("Enter customer name").input_value()
    ref_value = dialog.get_by_placeholder("REF-001").input_value()
    print(f'[Negative 6] Customer name field holds: "{name_value}"')
    print(f'[Negative 6] Own reference field holds: "{ref_value}"')

    submit_job(dialog)
    page.wait_for_timeout(2500)

    try:
        still_open = dialog.get_by_placeholder("Enter customer name").is_visible()
    except Exception:
        still_open = False
    if still_open:
        print("[Negative 6] Result: submission BLOCKED. Dialog validation text:\n" + dialog.inner_text())
    else:
        print("[Negative 6] Result: job CREATED with special-character customer name/own reference (no validation blocked it).")
    # Must not crash the app either way.
    expect(page).to_have_url(re.compile(r"/jobs"))


def test_negative_job_7_special_characters_in_numeric_only_fields(page):
    login(page)
    dialog = open_add_job_drawer(page)

    dialog.get_by_placeholder("Enter customer name").fill("Special Char Numeric Test")
    dialog.get_by_placeholder("customer@email.com").fill(f"special.numeric.{uniq(10)}@yopmail.com")

    phone_field = dialog.get_by_placeholder("412345678")
    phone_field.click()
    page.keyboard.type(SPECIAL_CHARS)
    print(f'[Negative 7] Phone field holds after typing special characters: "{phone_field.input_value()}"')

    abn_field = dialog.get_by_placeholder("12345678901")
    abn_field.fill(SPECIAL_CHARS)
    print(f'[Negative 7] ABN/ACN field holds after special characters: "{abn_field.input_value()}"')

    postcode_field = dialog.get_by_placeholder("2000")
    postcode_field.fill(SPECIAL_CHARS)
    print(f'[Negative 7] Postcode field holds after special characters: "{postcode_field.input_value()}"')

    submit_job(dialog)
    page.wait_for_timeout(2000)
    try:
        still_open = dialog.get_by_placeholder("Enter customer name").is_visible()
    except Exception:
        still_open = False
    if still_open:
        print("[Negative 7] Result: submission BLOCKED. Dialog validation text:\n" + dialog.inner_text())
    else:
        print("[Negative 7] Result: job CREATED - numeric fields accepted special characters unexpectedly.")
    expect(page).to_have_url(re.compile(r"/jobs"))


def test_negative_job_8_special_characters_in_email_local_part_rejected(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fill_job_form(
        dialog,
        dict(
            customerName="Special Email Test",
            email=f"{SPECIAL_CHARS}@yopmail.com",
            phone=phone(111),
            abnAcn=abn(111),
            addressSearch="1 George Street Sydney",
            postcode="2000",
            activityType="Heating & Cooling",
            buildingType="Residential Building",
            leadMethod="Phone",
            ownReference=f"REF-{RUN_ID}-NEG8",
            installationDate="16-09-2026",
            installer=INSTALLER_COMPANY,
            fillEquipment=True,
        ),
    )
    submit_job(dialog)
    expect_field_error(dialog, "Enter a valid email")
    expect(dialog.get_by_placeholder("Enter customer name")).to_be_visible()


# ---------------------------------------------------------------------------
# Additional edge cases & boundary values
# ---------------------------------------------------------------------------


def _edge_base(i: int) -> dict:
    return dict(
        customerName=f"Edge Case {i}",
        email=f"edge.case.{uniq(i)}@yopmail.com",
        phone=phone(200 + i),
        abnAcn=abn(200 + i),
        addressSearch="1 George Street Sydney",
        postcode="2000",
        activityType="Heating & Cooling",
        buildingType="Residential Building",
        leadMethod="Phone",
        ownReference=f"REF-{RUN_ID}-EDGE{i}",
        installationDate="20-09-2026",
        installer=INSTALLER_COMPANY,
        fillEquipment=True,
    )


def test_edge_case_1_postcode_too_short(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _edge_base(1)
    fields["postcode"] = "20"
    fill_job_form(dialog, fields)
    postcode_value = dialog.get_by_placeholder("2000").input_value()
    print(f'[Edge 1] Postcode field holds: "{postcode_value}"')
    submit_and_report(page, dialog, "Edge 1")


def test_edge_case_2_postcode_from_different_state_than_address(page):
    login(page)
    dialog = open_add_job_drawer(page)
    # Address is "1 George Street, Sydney NSW 2000" but postcode is filled
    # with a Melbourne (VIC) postcode - checks for cross-field state/postcode
    # consistency validation.
    fields = _edge_base(2)
    fields["addressSearch"] = "1 George Street Sydney"
    fields["postcode"] = "3000"
    fill_job_form(dialog, fields)
    submit_and_report(page, dialog, "Edge 2")


def test_edge_case_3_whitespace_only_name_and_reference(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _edge_base(3)
    fields["customerName"] = "   "
    fields["ownReference"] = "   "
    fill_job_form(dialog, fields)
    name_value = dialog.get_by_placeholder("Enter customer name").input_value()
    print(f'[Edge 3] Customer name field holds: "{name_value}" (length {len(name_value)})')
    submit_and_report(page, dialog, "Edge 3")


def test_edge_case_4_sql_injection_style_name_handled_safely(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _edge_base(4)
    fields["customerName"] = "Robert'); DROP TABLE Jobs;--"
    fill_job_form(dialog, fields)
    result = submit_and_report(page, dialog, "Edge 4")
    if result["created"]:
        # If it was created, the app must still be fully functional afterwards
        # (i.e. the string was stored as literal text, not executed as SQL).
        page.goto("/jobs")
        expect(page.get_by_role("button", name=re.compile("add job", re.I))).to_be_visible()
    expect(page).to_have_url(re.compile(r"/jobs"))


def test_edge_case_5_unicode_and_emoji_in_name(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _edge_base(5)
    fields["customerName"] = "陈伟 🏠 Müller Nguyễn"
    fill_job_form(dialog, fields)
    name_value = dialog.get_by_placeholder("Enter customer name").input_value()
    print(f'[Edge 5] Customer name field holds: "{name_value}"')
    submit_and_report(page, dialog, "Edge 5")


def test_edge_case_6_duplicate_abn_phone_email_from_valid_job_1(page):
    """
    Valid Job 1 (index 0 above) was created with abn(0)/phone(0) and email
    `olivia.bennett.<uniq(0)>@yopmail.com`. Reusing them here checks whether
    the app flags/blocks duplicate customer identifiers or just creates a
    second job freely.
    """
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _edge_base(6)
    fields["customerName"] = "Duplicate Of Olivia"
    fields["email"] = f"olivia.bennett.{uniq(0)}@yopmail.com"
    fields["phone"] = phone(0)
    fields["abnAcn"] = abn(0)
    fill_job_form(dialog, fields)
    submit_and_report(page, dialog, "Edge 6")


def test_edge_case_7_installation_date_in_the_past(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _edge_base(7)
    fields["installationDate"] = "01-01-2020"
    fill_job_form(dialog, fields)
    date_value = dialog.get_by_placeholder("DD-MM-YYYY").input_value()
    print(f'[Edge 7] Installation date field holds: "{date_value}"')
    submit_and_report(page, dialog, "Edge 7")


def test_edge_case_8_calendar_invalid_date(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _edge_base(8)
    fields["installationDate"] = "31-02-2026"  # February has no 31st
    fill_job_form(dialog, fields)
    date_value = dialog.get_by_placeholder("DD-MM-YYYY").input_value()
    print(f'[Edge 8] Installation date field holds: "{date_value}"')
    submit_and_report(page, dialog, "Edge 8")


def test_edge_case_9_phone_too_short(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _edge_base(9)
    fields["phone"] = "41234"
    fill_job_form(dialog, fields)
    phone_value = dialog.get_by_placeholder("412345678").input_value()
    print(f'[Edge 9] Phone field holds: "{phone_value}"')
    submit_and_report(page, dialog, "Edge 9")


def test_edge_case_10_phone_too_long(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _edge_base(10)
    fields["phone"] = "412345678999"
    fill_job_form(dialog, fields)
    phone_value = dialog.get_by_placeholder("412345678").input_value()
    print(f'[Edge 10] Phone field holds: "{phone_value}"')
    submit_and_report(page, dialog, "Edge 10")


# ---------------------------------------------------------------------------
# Multi-product jobs - "+ Add another product"
# ---------------------------------------------------------------------------


def _multi_base(i: int) -> dict:
    return dict(
        customerName=f"Multi Product {i}",
        email=f"multi.product.{uniq(300 + i)}@yopmail.com",
        phone=phone(300 + i),
        abnAcn=abn(300 + i),
        addressSearch="1 George Street Sydney",
        postcode="2000",
        activityType="Heating & Cooling",
        buildingType="Residential Building",
        leadMethod="Phone",
        ownReference=f"REF-{RUN_ID}-MULTI{i}",
        installationDate="25-09-2026",
        installer=INSTALLER_COMPANY,
    )


PRODUCT_COUNTS = [2, 3, 2, 4, 3]


@pytest.mark.parametrize(
    "i,count",
    list(enumerate(PRODUCT_COUNTS, start=1)),
    ids=[f"{count}-products" for count in PRODUCT_COUNTS],
)
def test_multi_product_job(page, i, count):
    login(page)
    dialog = open_add_job_drawer(page)

    fields = _multi_base(i)
    fields["productCount"] = count
    fill_job_form(dialog, fields)

    # Every "PRODUCT N" block and its own Remove button should be present
    # before submitting.
    for p in range(1, count + 1):
        expect(dialog.get_by_text(f"Product {p}", exact=True)).to_be_visible()
    expect(dialog.get_by_role("button", name=re.compile("remove", re.I))).to_have_count(count)

    submit_job(dialog)
    expect_job_created(page, dialog, f"Multi Product {i}")
