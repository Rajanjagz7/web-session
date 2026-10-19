"""Read-only follow-up on job_edge_cases.py results. Writes UTF-8 to job_edge_followup.txt."""
import re
import sys

sys.path.insert(0, "1er-tests-python")
from playwright.sync_api import sync_playwright  # noqa: E402
import helpers as h  # noqa: E402

out = open("job_edge_followup.txt", "w", encoding="utf-8")


def log(*a):
    print(*a, file=out, flush=True)


def search(page, term, errors):
    page.goto("/jobs")
    before = len(errors)
    page.get_by_placeholder(re.compile("search jobs", re.I)).fill(term)
    page.wait_for_timeout(2300)
    rows = page.locator("table tbody tr")
    texts = [rows.nth(k).inner_text().replace("\n", " ").replace("\t", " ")[:200] for k in range(min(rows.count(), 3))]
    return rows.count(), texts, errors[before:]


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(base_url="https://nswstage.rebatem8.com.au")
    page.set_default_timeout(30_000)
    errors = []
    page.on("response", lambda r: errors.append(f"{r.status} {r.url.split('/api/v1')[-1][:90]}")
            if "/api/v1/" in r.url and r.status >= 400 else None)
    h.login(page)

    log("== Stored values for jobs created by the edge cases ==")
    for term in ["M8N000109", "M8N000110", "M8N000105", "M8N000106", "M8N000107"]:
        n, texts, errs = search(page, term, errors)
        log(term, "->", texts[:1], errs)

    log("\n== Search: special characters / pattern handling ==")
    for term in ["a", "%", "'", ".", ".*", "(", "[", "*", "\\", "zzzqqq", "O'Brien", "Siobh"]:
        n, texts, errs = search(page, term, errors)
        log(f"{term!r:10} rows={n} errors={errs} first={texts[0][:90] if texts else ''}")

    browser.close()
out.close()
print("done")
