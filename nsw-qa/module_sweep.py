"""
Round 5 - deep sweep of every admin module reachable from the sidebar (UI, report-only).
Per page: API 4xx/5xx and console errors on load, row count, search behaviour
(no-match text, '%' wildcard, surrounding spaces), next-page click, and the Add/Create
form's blank-submit validation. Add forms are never filled, so nothing is saved.
Output: module_sweep.txt (JSON lines, UTF-8) + sweep-<page>.png screenshots.
"""
import json
import re
import sys

sys.path.insert(0, "1er-tests-python")
from playwright.sync_api import sync_playwright  # noqa: E402
import helpers as h  # noqa: E402

out = open("module_sweep.txt", "w", encoding="utf-8")
SKIP = re.compile(r"log ?out|sign ?out", re.I)


def log(obj):
    print(json.dumps(obj, ensure_ascii=False), file=out, flush=True)


def lines(page):
    return {l.strip() for l in page.locator("body").inner_text().splitlines() if l.strip() and len(l.strip()) < 140}


def row_ids(page):
    rows = page.locator("table tbody tr")
    return [re.sub(r"\s+", " ", rows.nth(k).inner_text())[:60] for k in range(rows.count())]


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(base_url="https://nswstage.rebatem8.com.au")
    page.set_default_timeout(20_000)
    errs, console = [], []
    page.on("response", lambda r: errs.append(f"{r.status} {r.request.method} {r.url.split('/api/v1')[-1][:100]}")
            if "/api/v1/" in r.url and r.status >= 400 else None)
    page.on("console", lambda m: console.append(m.text[:160]) if m.type == "error" else None)
    for _ in range(3):
        try:
            h.login(page)
            break
        except Exception:
            pass

    links = page.locator("aside a[href], nav a[href]").evaluate_all(
        "els => els.map(e => ({text: e.innerText.trim(), href: e.getAttribute('href')}))")
    seen, pages = set(), []
    for l in links:
        if l["href"] and l["href"].startswith("/") and l["href"] not in seen and not SKIP.search(l["text"] or ""):
            seen.add(l["href"])
            pages.append(l)
    log(dict(id="SIDEBAR", pages=pages))

    for pg in pages:
        name, href = pg["text"] or pg["href"], pg["href"]
        rec = dict(id="PAGE", name=name, href=href)
        try:
            e0, c0 = len(errs), len(console)
            page.goto(href)
            page.wait_for_timeout(4500)
            rec.update(landed=page.url, load_api_errors=errs[e0:], load_console_errors=console[c0:][:5],
                       heading=next(iter(page.locator("h1, h2").all_inner_texts()), ""),
                       rows=page.locator("table tbody tr").count(),
                       empty_state=bool(re.search(r"no data|no records|not found", page.locator("body").inner_text(), re.I)))
            base_rows = row_ids(page)
            page.screenshot(path=f"sweep-{re.sub(r'[^a-z0-9]+', '-', href.lower()).strip('-') or 'root'}.png", full_page=True)

            # search behaviour
            search = page.locator("input[placeholder*='earch' i]").first
            if search.count() and search.is_visible():
                srch = {}
                for term, label in [("zzqxw", "no-match"), ("%", "percent"), ("'", "quote")]:
                    e1 = len(errs)
                    search.fill(term)
                    page.wait_for_timeout(3000)
                    r = row_ids(page)
                    srch[label] = dict(rows=len(r), same_as_unfiltered=bool(base_rows) and r == base_rows,
                                       api_errors=errs[e1:])
                if base_rows:
                    token = re.split(r"\s+", base_rows[0].strip())[0]
                    for term, label in [(token, "first-cell"), (f"  {token}  ", "first-cell padded"), (token.lower(), "first-cell lower")]:
                        search.fill(term)
                        page.wait_for_timeout(3000)
                        srch[label] = dict(term=term, rows=len(row_ids(page)))
                search.fill("")
                page.wait_for_timeout(2000)
                rec["search"] = srch

            # pagination
            nxt = page.get_by_role("button", name=re.compile(r"^(next|›|»|>)$", re.I))
            two = page.get_by_role("button", name="2", exact=True)
            tgt = nxt if nxt.count() else two
            if tgt.count() and tgt.first.is_enabled():
                e1 = len(errs)
                tgt.first.click()
                page.wait_for_timeout(3000)
                p2 = row_ids(page)
                rec["page2"] = dict(rows=len(p2), identical_to_page1=p2 == base_rows and bool(p2), api_errors=errs[e1:])

            # Add / Create form blank submit
            page.goto(href)
            page.wait_for_timeout(3000)
            add = page.get_by_role("button", name=re.compile(r"^\s*\+?\s*(add|create|new)\b", re.I))
            if add.count() and add.first.is_visible():
                rec["add_button"] = add.first.inner_text().strip()
                before = lines(page)
                add.first.click()
                page.wait_for_timeout(2000)
                form_text = sorted(lines(page) - before)[:40]
                submit = page.get_by_role("button", name=re.compile(r"^(save|submit|create|add|send|confirm|update)\b", re.I))
                cand = [b for b in submit.all() if b.is_visible() and b.inner_text().strip() != rec["add_button"]]
                if cand:
                    e1 = len(errs)
                    cand[-1].click()
                    page.wait_for_timeout(2500)
                    rec["add_form"] = dict(fields_shown=form_text, submit_button=cand[-1].inner_text().strip(),
                                           blank_submit_messages=sorted(l for l in lines(page) - before
                                                                        if re.search(r"required|valid|must|error|please", l, re.I))[:25],
                                           api_calls_on_blank_submit=errs[e1:])
                else:
                    rec["add_form"] = dict(fields_shown=form_text, submit_button=None)
                page.screenshot(path=f"sweep-add-{re.sub(r'[^a-z0-9]+', '-', href.lower()).strip('-')}.png", full_page=True)
        except Exception as ex:
            rec["script_error"] = f"{type(ex).__name__}: {str(ex)[:200]}"
        log(rec)

    browser.close()
out.close()
print("done")
