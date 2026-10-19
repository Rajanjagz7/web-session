import time

from playwright.sync_api import expect

from config import INSTALLER_COMPANY
from helpers import login, open_add_job_drawer, fill_job_form, submit_job, submit_and_report, control_for_label

RUN_ID = str(int(time.time() * 1000))[-8:]


def uniq(n: int) -> str:
    return f"{RUN_ID}{n}"


def abn(n: int) -> str:
    return uniq(n).rjust(11, "0")[-11:]


def phone(n: int) -> str:
    return "4" + uniq(n).rjust(8, "0")[-8:]


def _base_valid(i: int) -> dict:
    return dict(
        customerName=f"Field Boundary {i}",
        email=f"field.boundary.{uniq(i)}@yopmail.com",
        phone=phone(i),
        abnAcn=abn(i),
        addressSearch="1 George Street Sydney",
        postcode="2000",
        activityType="Heating & Cooling",
        buildingType="Residential Building",
        leadMethod="Phone",
        ownReference=f"REF-{RUN_ID}-BND{i}",
        installationDate="15-10-2026",
        installer=INSTALLER_COMPANY,
        fillEquipment=True,
    )


def test_abn_negative_sign_prefix(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _base_valid(1)
    del fields["abnAcn"]
    fill_job_form(dialog, fields)
    abn_field = dialog.get_by_placeholder("12345678901")
    abn_field.fill("-1234567890")
    held = abn_field.input_value()
    print(f'[ABN negative-sign] typed "-1234567890" -> field holds "{held}"')
    submit_and_report(page, dialog, "ABN negative-sign")


def test_abn_letters_mixed_with_digits(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _base_valid(2)
    del fields["abnAcn"]
    fill_job_form(dialog, fields)
    abn_field = dialog.get_by_placeholder("12345678901")
    abn_field.fill("1234ABCD901")
    held = abn_field.input_value()
    print(f'[ABN letters] typed "1234ABCD901" -> field holds "{held}"')
    submit_and_report(page, dialog, "ABN letters")


def test_abn_all_zeros_valid_but_meaningless(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _base_valid(3)
    fields["abnAcn"] = "00000000000"
    fill_job_form(dialog, fields)
    result = submit_and_report(page, dialog, "ABN all-zeros")
    print(f"[ABN all-zeros] job created: {result['created']}")


def test_postcode_negative_sign_prefix(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _base_valid(4)
    del fields["postcode"]
    fill_job_form(dialog, fields)
    postcode_field = dialog.get_by_placeholder("2000")
    postcode_field.fill("-200")
    held = postcode_field.input_value()
    print(f'[Postcode negative-sign] typed "-200" -> field holds "{held}"')
    submit_and_report(page, dialog, "Postcode negative-sign")


def test_postcode_letters(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _base_valid(5)
    del fields["postcode"]
    fill_job_form(dialog, fields)
    postcode_field = dialog.get_by_placeholder("2000")
    postcode_field.fill("ABCD")
    held = postcode_field.input_value()
    print(f'[Postcode letters] typed "ABCD" -> field holds "{held}"')
    submit_and_report(page, dialog, "Postcode letters")


def test_postcode_all_zeros_valid_but_nonexistent(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _base_valid(6)
    fields["postcode"] = "0000"
    fill_job_form(dialog, fields)
    result = submit_and_report(page, dialog, "Postcode all-zeros")
    print(f"[Postcode all-zeros] job created: {result['created']}")


def test_phone_negative_sign_and_decimal_characters(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _base_valid(7)
    del fields["phone"]
    fill_job_form(dialog, fields)
    phone_field = dialog.get_by_placeholder("412345678")
    phone_field.click()
    page.keyboard.type("-41.234.567")
    held = phone_field.input_value()
    print(f'[Phone negative/decimal] typed "-41.234.567" -> field holds "{held}"')
    submit_and_report(page, dialog, "Phone negative/decimal")


def test_installation_date_non_numeric_characters(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _base_valid(8)
    del fields["installationDate"]
    fill_job_form(dialog, fields)
    date_field = dialog.get_by_placeholder("DD-MM-YYYY")
    date_field.click()
    page.keyboard.type("AB-CD-EFGH")
    held = date_field.input_value()
    print(f'[Date non-numeric] typed "AB-CD-EFGH" -> field holds "{held}"')
    submit_and_report(page, dialog, "Date non-numeric")


def test_installation_date_extreme_boundary_years(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _base_valid(9)
    del fields["installationDate"]
    fill_job_form(dialog, fields)
    date_field = dialog.get_by_placeholder("DD-MM-YYYY")

    date_field.click()
    page.keyboard.type("01-01-0001")
    print(f'[Date year 0001] field holds "{date_field.input_value()}"')

    date_field.fill("")
    date_field.click()
    page.keyboard.type("31-12-9999")
    print(f'[Date year 9999] field holds "{date_field.input_value()}"')

    submit_and_report(page, dialog, "Date extreme years")


def test_installation_date_incomplete(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _base_valid(10)
    del fields["installationDate"]
    fill_job_form(dialog, fields)
    date_field = dialog.get_by_placeholder("DD-MM-YYYY")
    date_field.click()
    page.keyboard.type("15-13")
    print(f'[Date incomplete] typed "15-13" -> field holds "{date_field.input_value()}"')
    submit_and_report(page, dialog, "Date incomplete")


def test_site_address_gibberish_no_suggestions_stays_required(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _base_valid(11)
    del fields["addressSearch"]
    fill_job_form(dialog, fields)

    address_control = control_for_label(dialog, "Site address")
    address_control.click()
    page.keyboard.type("zzzzxxxxqqqq99999nonexistentplace")
    page.wait_for_timeout(1500)
    option_count = page.get_by_role("option").count()
    print(f"[Address gibberish] suggestion count: {option_count}")
    assert option_count == 0

    # Close the dropdown without selecting anything by clicking a neutral
    # area - pressing Escape here closes the whole drawer, not just the open
    # select (a known gotcha in this app, see helpers.py history).
    dialog.get_by_text("Add Job", exact=True).first.click()
    page.wait_for_timeout(300)
    submit_job(dialog)
    page.wait_for_timeout(1500)
    expect(dialog.get_by_text("Site address is required", exact=True)).to_be_visible()


def test_own_reference_negative_number_and_decimal_accepted_as_free_text(page):
    login(page)
    dialog = open_add_job_drawer(page)
    fields = _base_valid(12)
    fields["ownReference"] = "-999.50"
    fill_job_form(dialog, fields)
    ref_field = dialog.get_by_placeholder("REF-001")
    print(f'[Own reference negative/decimal] field holds "{ref_field.input_value()}"')
    submit_and_report(page, dialog, "Own reference negative/decimal")
