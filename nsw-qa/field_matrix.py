"""
Field-by-field scenario matrix for the Add Job form (Step 1). For each value, ONLY that
field is filled and the rest left blank, then Send is clicked - the other required
fields always block the submit, so NO job is created. Records:
  - kept:   what the input holds after typing (masking / stripping / truncation)
  - own:    messages that mention this field, beyond the blank-form baseline
  - filled: whether the field's own "... is required" message went away
Client-side behaviour only (server-side checks need a full submit - see earlier rounds).
Output: field_matrix.json + field_matrix.md
"""
import json
import re
import sys

sys.path.insert(0, "1er-tests-python")
from playwright.sync_api import sync_playwright  # noqa: E402
import helpers as h  # noqa: E402

LONG = "Nguyen" * 43  # 258 chars

FIELDS = {
    "Customer Name": ("Enter customer name", "fill", "Customer Name", [
        ("valid", "Olivia Nguyen"), ("1 char", "A"), ("spaces only", "   "), ("digits only", "12345"),
        ("apostrophe/hyphen", "Siobhan O'Brien-Smith"), ("accented", "Nguyễn Văn An"), ("emoji", "Olivia 🙂"),
        ("HTML", "<b>Olivia</b>"), ("100 chars", LONG[:100]), ("258 chars", LONG)]),
    "Customer Email": ("Enter Customer Email", "fill", "Customer Email", [
        ("valid", "olivia.nguyen@yopmail.com"), ("uppercase", "Olivia.NGUYEN@YOPMAIL.COM"),
        ("no @", "olivia.yopmail.com"), ("no local part", "@yopmail.com"), ("no domain", "olivia@"),
        ("no TLD", "olivia@yopmail"), ("double dot", "olivia..nguyen@yopmail.com"), ("space inside", "olivia nguyen@yopmail.com"),
        ("surrounding spaces", "  olivia@yopmail.com  "), ("plus alias", "olivia+jobs@yopmail.com"),
        ("65-char local part", "a" * 65 + "@yopmail.com")]),
    "Customer Phone": ("Enter Customer Phone", "type", "Customer Phone", [
        ("valid mobile 9 digits", "412345678"), ("8 digits", "41234567"), ("10 digits", "4123456789"),
        ("leading 0", "0412345678"), ("+61 prefix", "+61412345678"), ("landline 9 digits", "298765432"),
        ("letters", "abcdefghi"), ("spaces", "412 345 678"), ("dashes", "412-345-678"), ("all zeros", "000000000")]),
    "ABN/ACN": ("12345678901", "fill", "ABN/ACN", [
        ("valid ABN", "33102417032"), ("bad-checksum ABN", "12345678901"), ("9-digit ACN", "004085616"),
        ("10 digits", "3310241703"), ("12 digits", "331024170321"), ("with spaces", "33 102 417 032"),
        ("letters", "ABCDEFGHIJK"), ("all zeros", "00000000000"), ("negative", "-3310241703")]),
    "Postcode": ("2000", "fill", "Postcode", [
        ("valid NSW", "2000"), ("valid NSW regional", "2650"), ("VIC postcode", "3000"), ("QLD postcode", "4000"),
        ("3 digits", "200"), ("5 digits", "20000"), ("letters", "abcd"), ("all zeros", "0000"),
        ("with space", "2 000"), ("negative", "-200")]),
    "Own Reference": ("REF-001", "fill", "Own Reference", [
        ("typical", "REF-2026-0142"), ("spaces only", "   "), ("HTML", "<i>REF</i>"), ("258 chars", LONG)]),
    "Installation Date": ("DD-MM-YYYY", "type", "Installation Date", [
        ("valid future", "15-12-2026"), ("today", "24-09-2026"), ("past", "01-01-2020"), ("31 Dec", "31-12-2026"),
        ("29 Feb non-leap", "29-02-2027"), ("31 Apr", "31-04-2027"), ("day 00", "00-01-2027"), ("month 13", "15-13-2026"),
        ("single digits", "1-1-2027"), ("slashes", "15/12/2026"), ("letters", "ab-cd-efgh"), ("year 1900", "15-12-1900")]),
}


def body_lines(page):
    return {l.strip() for l in page.locator("body").inner_text().splitlines() if l.strip() and len(l.strip()) < 140}


def open_blank(page):
    page.goto("/jobs")
    page.get_by_role("button", name=re.compile("add job", re.I)).click()
    page.get_by_placeholder("Enter customer name").wait_for(state="visible")
    page.wait_for_timeout(600)
    return page.get_by_role("dialog")


results = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(base_url="https://nswstage.rebatem8.com.au")
    page.set_default_timeout(45_000)
    for attempt in range(3):
        try:
            h.login(page)
            break
        except Exception:
            pass

    d = open_blank(page)
    h.submit_job(d)
    page.wait_for_timeout(1500)
    baseline = body_lines(page)

    for field, (placeholder, mode, label, values) in FIELDS.items():
        key = label.lower().split()[-1] if field != "ABN/ACN" else "abn"
        for scenario, value in values:
            rec = dict(field=field, scenario=scenario, typed=value if len(value) < 40 else f"{value[:12]}...({len(value)} chars)")
            try:
                d = open_blank(page)
                inp = d.get_by_placeholder(placeholder).first
                if mode == "type":
                    inp.click()
                    page.keyboard.type(value)
                else:
                    inp.fill(value)
                kept = inp.input_value()
                h.submit_job(d)
                page.wait_for_timeout(1300)
                now = body_lines(page)
                own = sorted(l for l in now - baseline if key in l.lower() or re.search(r"valid|digit|must|format|date", l, re.I))
                rec.update(kept=kept if len(kept) < 40 else f"{kept[:12]}...({len(kept)} chars)",
                           filled=f"{label} is required" not in now, own=own)
            except Exception as e:
                rec.update(error=f"{type(e).__name__}: {str(e)[:120]}")
            results.append(rec)
            print(json.dumps(rec, ensure_ascii=False).encode("ascii", "replace").decode())
    browser.close()

with open("field_matrix.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=1, ensure_ascii=False)
with open("field_matrix.md", "w", encoding="utf-8") as f:
    f.write("| Field | Scenario | Typed | Field holds | Counted as filled | Message shown |\n|---|---|---|---|---|---|\n")
    for r in results:
        f.write(f"| {r['field']} | {r['scenario']} | `{r['typed']}` | `{r.get('kept', '')}` | {r.get('filled', '')} | "
                f"{'; '.join(r.get('own', [])) or r.get('error', '—')} |\n")
print("saved field_matrix.json / field_matrix.md")
