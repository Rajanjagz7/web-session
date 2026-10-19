"""
Pytest + Playwright test suite for the scenario:

  On the Appointments screen, select a practitioner. If that practitioner
  has no appointment types available, select another practitioner. The
  chosen appointment type's duration must be more than 20 minutes.

Each test function's docstring is the MANUAL test case (Test ID, Title,
Preconditions, Steps, Expected Result) exactly as documented in
TestCases_Practitioner_AppointmentType_Selection.md. The code below each
docstring is the Playwright automation of that same test case, so manual
and automated versions stay paired and in sync.

Run with:
    pytest test_appointment_scenarios_pytest.py -v -s --headed
"""
import re

import pytest
from playwright.sync_api import Page, expect

URL = "https://practice2.dev.ozmed.health/"
EMAIL = "fep5@yopmail.com"
PASSWORD = "Test@1234"
OTP = "489567"
MIN_DURATION_MINUTES = 20

DURATION_RE = re.compile(r"\((\d+)\s*mins?\)", re.IGNORECASE)


def parse_duration(text: str):
    m = DURATION_RE.search(text)
    return int(m.group(1)) if m else None


def login(page: Page):
    page.goto(URL, wait_until="networkidle", timeout=30_000)
    page.wait_for_function(
        "() => { const r = document.getElementById('root'); return r && r.children.length > 0; }",
        timeout=15_000,
    )
    inputs = page.locator("input").all()
    inputs[0].fill(EMAIL)
    inputs[1].fill(PASSWORD)
    page.get_by_role("button", name="Sign In").click()
    page.wait_for_timeout(2500)

    if "verify" in page.url:
        for _ in range(3):
            otp_inputs = page.locator("input").all()
            for i, digit in enumerate(OTP):
                if i < len(otp_inputs):
                    otp_inputs[i].fill(digit)
            page.get_by_role("button", name="Submit").click()
            page.wait_for_timeout(3000)
            if "verify" not in page.url:
                break


def open_book_appointment_modal(page: Page):
    page.get_by_role("link", name="Appointments").click()
    page.wait_for_timeout(3000)
    page.get_by_role("button", name="Book Appointment").click()
    page.wait_for_timeout(1200)
    return page.locator("[class*='MuiDialog-paper']")


def pick_any_date(page: Page, dialog):
    dialog.locator("button[aria-label='Choose date']").click()
    page.wait_for_timeout(500)
    for b in page.locator("button.MuiPickersDay-root").all():
        cls = b.get_attribute("class") or ""
        if "Mui-disabled" not in cls:
            b.click()
            page.wait_for_timeout(800)
            return True
    return False


def select_first_slot(page: Page, dialog) -> bool:
    dialog.locator("text=Practitioner Availability").scroll_into_view_if_needed()
    page.wait_for_timeout(500)
    slot_start = page.locator("span", has_text=re.compile(r"^\d{2}:\d{2}$")).first
    for _ in range(8):
        if slot_start.count() > 0:
            break
        page.wait_for_timeout(1000)
    if slot_start.count() == 0:
        return False
    slot_start.click()
    page.wait_for_timeout(800)
    return True


@pytest.fixture(scope="module")
def authed_page(browser):
    """Logs in once and reuses the session for every test in this module —
    avoids re-triggering OTP (which has shown occasional flakiness) for
    every single test case."""
    context = browser.new_context(no_viewport=True)
    page = context.new_page()
    login(page)
    yield page
    context.close()


@pytest.fixture
def appointment_dialog(authed_page):
    """Opens a fresh Book Appointment modal for each test, closes it after."""
    dialog = open_book_appointment_modal(authed_page)
    yield authed_page, dialog
    try:
        if dialog.count() > 0 and dialog.is_visible():
            cancel = dialog.get_by_role("button", name="Cancel")
            if cancel.count() > 0:
                cancel.click()
            else:
                authed_page.keyboard.press("Escape")
    except Exception:
        pass
    authed_page.wait_for_timeout(500)


# ---------------------------------------------------------------------------

def test_tc_apt_12_date_prerequisite_for_practitioner(appointment_dialog):
    """
    TC_APT_12 — Date is a prerequisite for the Practitioner field
    Preconditions: Add Appointment modal freshly opened (only Date + Concern
        fields visible).
    Steps:
        1. Without picking a date, look for the Practitioner field.
    Expected Result: Practitioner field is not present until a date is
        selected. After selecting any enabled date, the Practitioner field
        appears.
    Priority: Medium
    """
    page, dialog = appointment_dialog

    labels_before = [l.inner_text().strip() for l in dialog.locator("label").all()]
    assert "Practitioner" not in labels_before

    assert pick_any_date(page, dialog), "Could not pick any enabled date"

    labels_after = [l.inner_text().strip() for l in dialog.locator("label").all()]
    assert "Practitioner" in labels_after


def test_tc_apt_01_select_practitioner_with_types(appointment_dialog):
    """
    TC_APT_01 — Select a practitioner that has appointment types
    Preconditions: Logged in; on Appointments screen; date already selected
        in the Add Appointment modal.
    Steps:
        1. Click the Practitioner field.
        2. Select a practitioner from the dropdown (e.g. "Olivia Brown").
    Expected Result: Practitioner is set; an "Appointment Type" field
        appears below it.
    Priority: High
    """
    page, dialog = appointment_dialog
    pick_any_date(page, dialog)

    prac_input = dialog.locator("input[role='combobox']").first
    prac_input.click()
    page.wait_for_timeout(300)
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(3000)
    options = page.get_by_role("option").all()
    assert len(options) > 0, "No practitioners listed"

    # Pick the practitioner known to have appointment types in this env
    target = next((o for o in options if "Olivia Brown" in o.inner_text()), options[0])
    target.click()
    page.wait_for_timeout(1200)

    labels = [l.inner_text().strip() for l in dialog.locator("label").all()]
    assert "Appointment Type" in labels


def test_tc_apt_02_practitioner_with_zero_appointment_types(appointment_dialog):
    """
    TC_APT_02 — Practitioner with zero appointment types prompts selecting
        another
    Preconditions: Date selected in modal.
    Steps:
        1. Select a practitioner known/likely to have no appointment types
           (e.g. "Liam Martin Amelia").
        2. Open the Appointment Type dropdown.
    Expected Result: Appointment Type dropdown shows 0 options (empty
        list). No appointment type can be selected for this practitioner.
    Priority: High
    """
    page, dialog = appointment_dialog
    pick_any_date(page, dialog)

    prac_input = dialog.locator("input[role='combobox']").first
    prac_input.click()
    page.wait_for_timeout(300)
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(3000)
    options = page.get_by_role("option").all()
    zero_type_prac = next((o for o in options if "Liam Martin Amelia" in o.inner_text()), None)
    assert zero_type_prac is not None, "Expected test-data practitioner not found"
    zero_type_prac.click()
    page.wait_for_timeout(1200)

    combo_inputs = dialog.locator("input[role='combobox']").all()
    assert len(combo_inputs) >= 2, "Appointment Type field did not appear"
    combo_inputs[1].click()
    page.wait_for_timeout(300)
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(4000)
    type_options = page.get_by_role("option").all()
    assert len(type_options) == 0


def test_tc_apt_03_switch_to_another_practitioner(appointment_dialog):
    """
    TC_APT_03 — Switching to another practitioner after a zero-type
        practitioner
    Preconditions: TC_APT_02 just executed (zero-type practitioner
        selected).
    Steps:
        1. Clear/reopen the Practitioner field.
        2. Select a different practitioner (e.g. "Olivia Brown").
        3. Open the Appointment Type dropdown.
    Expected Result: Appointment Type dropdown now shows one or more
        options. Previous practitioner's empty state does not block
        re-selection.
    Priority: High
    """
    page, dialog = appointment_dialog
    pick_any_date(page, dialog)

    prac_input = dialog.locator("input[role='combobox']").first
    prac_input.click()
    page.wait_for_timeout(300)
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(3000)
    options = page.get_by_role("option").all()
    zero_type_prac = next((o for o in options if "Liam Martin Amelia" in o.inner_text()), None)
    assert zero_type_prac is not None
    zero_type_prac.click()
    page.wait_for_timeout(1200)

    # Switch to a practitioner that does have appointment types
    prac_input.click()
    page.wait_for_timeout(300)
    prac_input.fill("")
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(2500)
    options2 = page.get_by_role("option").all()
    olivia = next((o for o in options2 if "Olivia Brown" in o.inner_text()), None)
    assert olivia is not None
    olivia.click()
    page.wait_for_timeout(1200)

    combo_inputs = dialog.locator("input[role='combobox']").all()
    assert len(combo_inputs) >= 2
    combo_inputs[1].click()
    page.wait_for_timeout(300)
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(4000)
    type_options = page.get_by_role("option").all()
    assert len(type_options) > 0


def test_tc_apt_04_appointment_type_shows_duration(appointment_dialog):
    """
    TC_APT_04 — Appointment type list displays duration per option
    Preconditions: A practitioner with appointment types is selected.
    Steps:
        1. Open the Appointment Type dropdown.
    Expected Result: Each option's label includes its duration in minutes,
        e.g. "Mental Health Care Plan Note (21 mins)".
    Priority: Medium
    """
    page, dialog = appointment_dialog
    pick_any_date(page, dialog)

    prac_input = dialog.locator("input[role='combobox']").first
    prac_input.click()
    page.wait_for_timeout(300)
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(3000)
    options = page.get_by_role("option").all()
    olivia = next((o for o in options if "Olivia Brown" in o.inner_text()), options[0])
    olivia.click()
    page.wait_for_timeout(1200)

    combo_inputs = dialog.locator("input[role='combobox']").all()
    combo_inputs[1].click()
    page.wait_for_timeout(300)
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(4000)
    type_options = page.get_by_role("option").all()
    assert len(type_options) > 0
    for o in type_options:
        text = o.inner_text().strip()
        assert parse_duration(text) is not None, f"No duration parsed from {text!r}"


def test_tc_apt_05_select_type_duration_over_20_minutes(appointment_dialog):
    """
    TC_APT_05 — Select an appointment type with duration > 20 minutes
        (positive)
    Preconditions: Practitioner with appointment types selected (e.g.
        "Olivia Brown").
    Steps:
        1. Open Appointment Type dropdown.
        2. Select an option whose duration is greater than 20 minutes
           (e.g. "Mental Health Care Plan Note (21 mins)" or
           "General Consultation 2 (50 mins)").
    Expected Result: Appointment type is accepted; a "Practitioner
        Availability" panel appears below with bookable slots sized to
        that duration.
    Priority: High
    """
    page, dialog = appointment_dialog
    pick_any_date(page, dialog)

    prac_input = dialog.locator("input[role='combobox']").first
    prac_input.click()
    page.wait_for_timeout(300)
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(3000)
    options = page.get_by_role("option").all()
    olivia = next((o for o in options if "Olivia Brown" in o.inner_text()), options[0])
    olivia.click()
    page.wait_for_timeout(1200)

    combo_inputs = dialog.locator("input[role='combobox']").all()
    combo_inputs[1].click()
    page.wait_for_timeout(300)
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(4000)
    type_options = page.get_by_role("option").all()

    chosen = None
    for o in type_options:
        text = o.inner_text().strip()
        d = parse_duration(text)
        if d is not None and d > MIN_DURATION_MINUTES:
            chosen = (o, text, d)
            break
    assert chosen is not None, f"No appointment type with duration > {MIN_DURATION_MINUTES} min found"

    chosen[0].click()
    page.wait_for_timeout(1500)
    expect(dialog.locator("text=Practitioner Availability")).to_be_visible()


def test_tc_apt_08_boundary_21_minutes_qualifies(appointment_dialog):
    """
    TC_APT_08 — Boundary: 21 minutes qualifies
    Preconditions: Practitioner "Olivia Brown" selected.
    Steps:
        1. Open Appointment Type dropdown.
        2. Select "Mental Health Care Plan Note (21 mins)".
    Expected Result: Selection succeeds and is treated as valid (21 > 20).
    Priority: Medium (boundary)
    """
    page, dialog = appointment_dialog
    pick_any_date(page, dialog)

    prac_input = dialog.locator("input[role='combobox']").first
    prac_input.click()
    page.wait_for_timeout(300)
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(3000)
    options = page.get_by_role("option").all()
    olivia = next((o for o in options if "Olivia Brown" in o.inner_text()), options[0])
    olivia.click()
    page.wait_for_timeout(1200)

    combo_inputs = dialog.locator("input[role='combobox']").all()
    combo_inputs[1].click()
    page.wait_for_timeout(300)
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(4000)
    type_options = page.get_by_role("option").all()

    target = None
    for o in type_options:
        text = o.inner_text().strip()
        if "Mental Health Care Plan Note" in text:
            target = (o, text)
            break
    assert target is not None, "Expected 21-minute appointment type not found in this environment"
    assert parse_duration(target[1]) == 21

    target[0].click()
    page.wait_for_timeout(1500)
    expect(dialog.locator("text=Practitioner Availability")).to_be_visible()


@pytest.mark.skip(reason=(
    "TC_APT_06 documents a test-data/business rule (exclude types <=20 min) "
    "rather than a UI assertion — the UI itself does not block selecting a "
    "short appointment type. Covered functionally by the selection logic in "
    "test_tc_apt_05/08/13, which only ever choose types > 20 min."
))
def test_tc_apt_06_short_duration_type_excluded_by_selection_rule():
    """
    TC_APT_06 — Reject/avoid appointment type with duration <= 20 minutes
    Preconditions: Practitioner with appointment types selected, including
        at least one <=20 min option (e.g. "Surcharge on Sydney (4 mins)").
    Steps:
        1. Open Appointment Type dropdown.
        2. Attempt to select "Surcharge on Sydney (4 mins)".
    Expected Result (business rule under test): Per the scenario's
        requirement, this type should be excluded from selection by the
        test/automation logic — it does not satisfy "duration > 20
        minutes". (The UI itself does not block this selection; the
        exclusion is a test-data selection rule, not a UI validation.)
    Priority: High
    """


@pytest.mark.skip(reason=(
    "No appointment type with exactly 20 minutes exists in the current "
    "environment's data set. Documented as a manual/exploratory boundary "
    "case to (re)run if such test data is added."
))
def test_tc_apt_07_boundary_exactly_20_minutes_does_not_qualify():
    """
    TC_APT_07 — Boundary: exactly 20 minutes does not qualify
    Preconditions: A practitioner has an appointment type with exactly 20
        minutes duration (synthetic/boundary case — none observed in
        current data set).
    Steps:
        1. Open Appointment Type dropdown.
        2. Locate an option with exactly "(20 mins)".
    Expected Result: This option must NOT be selected, since the
        requirement is strictly "more than 20 minutes" (20 is not > 20).
    Priority: Medium (boundary)
    """


@pytest.mark.skip(reason=(
    "No practitioner in the current environment has appointment types that "
    "are all <=20 minutes — this practitioner would need to be added to "
    "test data to exercise this path automatically."
))
def test_tc_apt_09_practitioner_has_types_but_none_over_20_minutes():
    """
    TC_APT_09 — Practitioner has appointment types, but none exceed 20
        minutes
    Preconditions: A practitioner whose appointment types are all <=20
        minutes (synthetic scenario; construct via filtering or test data
        if such a practitioner exists).
    Steps:
        1. Select that practitioner.
        2. Inspect all Appointment Type options' durations.
    Expected Result: None qualify; test logic should move on and try the
        next practitioner in the list, same as the zero-types case
        (TC_APT_02/03).
    Priority: High
    """


@pytest.mark.skip(reason=(
    "Negative/hypothetical scenario requiring every practitioner in the "
    "environment to be disqualified — not reproducible against current "
    "live test data without seeding a dedicated environment."
))
def test_tc_apt_10_no_practitioner_qualifies_at_all():
    """
    TC_APT_10 — No practitioner in the list has a qualifying appointment
        type
    Preconditions: Hypothetical/negative scenario — all practitioners have
        either zero types or only types <=20 minutes.
    Steps:
        1. Iterate through every practitioner in the dropdown, checking
           Appointment Type durations for each.
    Expected Result: No valid practitioner + appointment-type combination
        found. The flow should stop and report a clear failure rather than
        silently proceeding (e.g. "No practitioner with an appointment
        type over 20 minutes was found").
    Priority: Medium
    """


def test_tc_apt_11_next_blocked_without_appointment_type(appointment_dialog):
    """
    TC_APT_11 — Next button blocked without a valid appointment type
    Preconditions: Practitioner selected, no Appointment Type selected
        yet.
    Steps:
        1. Click "Next" without selecting an Appointment Type.
    Expected Result: Validation error "Appointment Type is required!" is
        shown; modal stays on Step 1 (Appointment info).
    Priority: High
    """
    page, dialog = appointment_dialog
    pick_any_date(page, dialog)

    prac_input = dialog.locator("input[role='combobox']").first
    prac_input.click()
    page.wait_for_timeout(300)
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(3000)
    options = page.get_by_role("option").all()
    zero_type_prac = next((o for o in options if "Liam Martin Amelia" in o.inner_text()), options[0])
    zero_type_prac.click()
    page.wait_for_timeout(1200)

    dialog.get_by_role("button", name="Next").click()
    page.wait_for_timeout(1500)

    assert "Appointment Type is required" in dialog.inner_text()
    assert "Patient info" not in dialog.inner_text()


def test_tc_apt_13_end_to_end_qualifying_booking(appointment_dialog):
    """
    TC_APT_13 — End-to-end: qualifying practitioner + appointment type
        books successfully
    Preconditions: Logged in, on Appointments screen, an existing patient
        available to attach.
    Steps:
        1. Open "Book Appointment".
        2. Pick any open date.
        3. Select a practitioner; if it has no appointment types, select
           the next practitioner in the list, repeating until one with
           appointment types is found.
        4. From that practitioner's Appointment Type list, select the
           first option whose duration is > 20 minutes. If none qualify
           for this practitioner, return to step 3 and try the next
           practitioner.
        5. Select the first available time slot shown under "Practitioner
           Availability".
        6. Fill in a Concern.
        7. Click Next.
        8. Search for and select an existing patient.
        9. Click Submit.
    Expected Result: Appointment is created and appears in the
        Appointments table with the correct practitioner, the selected
        appointment type (duration > 20 min), date, and a "Scheduled"
        status.
    Priority: Critical
    """
    page, dialog = appointment_dialog
    pick_any_date(page, dialog)

    prac_input = dialog.locator("input[role='combobox']").first
    prac_input.click()
    page.wait_for_timeout(300)
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(3000)
    prac_count = len(page.get_by_role("option").all())
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    chosen_prac = chosen_type = None
    for idx in range(prac_count):
        prac_input.click()
        page.wait_for_timeout(300)
        prac_input.fill("")
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(2500)
        opts = page.get_by_role("option").all()
        if idx >= len(opts):
            break
        prac_name = opts[idx].inner_text().strip().splitlines()[0]
        opts[idx].click()
        page.wait_for_timeout(1200)

        combo_inputs = dialog.locator("input[role='combobox']").all()
        if len(combo_inputs) < 2:
            continue
        appt_type_input = combo_inputs[1]
        appt_type_input.click()
        page.wait_for_timeout(300)
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(4000)
        type_opts = page.get_by_role("option").all()
        qualifying = [
            (i, o.inner_text().strip())
            for i, o in enumerate(type_opts)
            if (parse_duration(o.inner_text().strip()) or 0) > MIN_DURATION_MINUTES
        ]
        if not qualifying:
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)
            continue

        # Try every qualifying (>20 min) type for this practitioner before
        # moving on to the next practitioner — a type with no open slot
        # should not disqualify the practitioner outright.
        slot_found = False
        for qualifying_idx, qualifying_text in qualifying:
            type_opts[qualifying_idx].click()
            page.wait_for_timeout(1500)
            if select_first_slot(page, dialog):
                slot_found = True
                break
            appt_type_input.click()
            page.wait_for_timeout(300)
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(3000)
            type_opts = page.get_by_role("option").all()

        if slot_found:
            chosen_prac, chosen_type = prac_name, qualifying_text
            break
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

    assert chosen_prac is not None, "No qualifying practitioner+type+slot combination found"

    concern = page.get_by_role("textbox", name="Concern")
    concern.click()
    concern.fill("Pytest E2E: appointment type duration > 20 minutes.")
    page.wait_for_timeout(300)

    dialog.get_by_role("button", name="Next").click()
    page.wait_for_timeout(1500)
    assert "Appointment Type is required" not in dialog.inner_text()
    assert "Patient info" in dialog.inner_text()

    search_input = dialog.get_by_role("combobox", name="Search Patient")
    search_input.click()
    search_input.fill("Lucas Wilson")
    page.wait_for_timeout(2000)
    results = page.get_by_role("option").all()
    assert len(results) > 0, "No matching patient found"
    results[0].click()
    page.wait_for_timeout(800)

    # NOTE: left unsubmitted intentionally — this suite validates the
    # selection rule end-to-end without mutating booking data on every
    # pytest run. The real submission flow is covered separately by
    # create_appointments.py / create_long_duration_appointments.py.
    submit_btn = dialog.get_by_role("button", name="Submit")
    expect(submit_btn).to_be_enabled()


def test_tc_apt_14_practitioner_reselection_advances_cleanly(appointment_dialog):
    """
    TC_APT_14 — Practitioner re-selection does not duplicate or corrupt
        Appointment Type field
    Preconditions: A zero-type practitioner was selected first, then
        switched to a valid one.
    Steps:
        1. Select zero-type practitioner ("Liam Martin Amelia").
        2. Switch to a valid practitioner ("Olivia Brown").
        3. Select a qualifying appointment type and a slot.
        4. Click Next.
    Expected Result: Step 1 validates successfully and advances to Step 2
        (Patient info) — confirms no leftover/stale state from the
        discarded first practitioner selection blocks progress.
    Priority: Medium
    """
    page, dialog = appointment_dialog
    pick_any_date(page, dialog)

    prac_input = dialog.locator("input[role='combobox']").first
    prac_input.click()
    page.wait_for_timeout(300)
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(3000)
    options = page.get_by_role("option").all()
    zero_type_prac = next((o for o in options if "Liam Martin Amelia" in o.inner_text()), None)
    assert zero_type_prac is not None
    zero_type_prac.click()
    page.wait_for_timeout(1200)

    prac_input.click()
    page.wait_for_timeout(300)
    prac_input.fill("")
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(2500)
    options2 = page.get_by_role("option").all()
    olivia = next((o for o in options2 if "Olivia Brown" in o.inner_text()), None)
    assert olivia is not None
    olivia.click()
    page.wait_for_timeout(1200)

    combo_inputs = dialog.locator("input[role='combobox']").all()
    combo_inputs[1].click()
    page.wait_for_timeout(300)
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(4000)
    type_options = page.get_by_role("option").all()
    chosen = next(
        (o for o in type_options if (parse_duration(o.inner_text()) or 0) > MIN_DURATION_MINUTES),
        None,
    )
    assert chosen is not None
    chosen.click()
    page.wait_for_timeout(1500)
    assert select_first_slot(page, dialog)

    concern = page.get_by_role("textbox", name="Concern")
    concern.click()
    concern.fill("Pytest: re-selection flow.")
    page.wait_for_timeout(300)

    dialog.get_by_role("button", name="Next").click()
    page.wait_for_timeout(1500)
    assert "Patient info" in dialog.inner_text()
