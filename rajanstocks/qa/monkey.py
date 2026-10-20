"""Monkey test: on every screen click a seeded-random set of visible buttons / chips / rows and watch for JavaScript errors,
failing API calls, blank screens and horizontal overflow.

    python qa/monkey.py [base_url] [clicks_per_screen]     # needs the server running (default http://127.0.0.1:8000)

Dangerous actions (reset, clear, delete, exit all, ...) are skipped. Exit code 1 when anything is found.
"""
import random
import re
import sys

from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")
CLICKS = int(sys.argv[2]) if len(sys.argv) > 2 else 30
SCREENS = ["picks", "options", "markets", "ipo", "journal", "indicators", "vedic", "daily", "portfolio", "orders", "alerts"]
SKIP = re.compile(r"reset|clear|delete|remove|exit all|wipe|sign out|logout|allow notif|subscribe|disable|turn off|cancel all|square", re.I)
VIEWPORTS = {"web": dict(viewport={"width": 1366, "height": 800}),
             "mobile": dict(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)}
NO_PUSH = "new MutationObserver(() => { const e = document.getElementById('pushAsk'); if (e) e.remove(); }).observe(document, {childList: true, subtree: true});"

CLICKABLE = """() => {
  const root = document.querySelector('.view.on'); if (!root) return [];
  document.querySelectorAll('[data-mk]').forEach(e => e.removeAttribute('data-mk'));     // indexes from earlier scans would collide
  const out = [];
  root.querySelectorAll('button, [role=button], [data-act], [data-view], [data-sym], .chip, .pick-row, tr[data-jv], summary, a[href^="#"]').forEach((e, i) => {
    const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    if (r.width < 8 || r.height < 8 || cs.visibility === 'hidden' || cs.pointerEvents === 'none' || e.disabled) return;
    if (r.bottom < 0 || r.top > innerHeight * 4) return;
    e.setAttribute('data-mk', String(i)); out.push({i, t: (e.innerText || e.getAttribute('aria-label') || e.title || e.id || e.tagName).trim().slice(0, 40)});
  });
  return out;
}"""


def run(kind, seed):
    rnd = random.Random(seed)
    problems = []
    with sync_playwright() as p:
        try:
            b = p.chromium.launch(channel="chrome")
        except Exception:
            b = p.chromium.launch()
        ctx = b.new_context(**VIEWPORTS[kind])
        ctx.add_init_script(NO_PUSH)
        page = ctx.new_page()
        js, http = [], []
        page.on("pageerror", lambda e: js.append(str(e)[:220]))
        page.on("console", lambda m: js.append("console: " + m.text[:220]) if m.type == "error" and "Failed to load resource" not in m.text and "ERR_NETWORK" not in m.text else None)
        page.on("response", lambda r: http.append(f"{r.status} {r.url.replace(BASE, '')[:100]}") if r.status >= 400 and "/api/" in r.url else None)
        page.goto(BASE + "/#picks")
        page.wait_for_function("!document.getElementById('boot')", timeout=120000)
        for scr in SCREENS:
            page.evaluate(f"go('{scr}')")
            page.wait_for_timeout(2500)
            clicked = []
            for n in range(CLICKS):
                try:
                    items = page.evaluate(CLICKABLE)
                except Exception as e:                                  # the page was reloaded / navigated by the last click
                    problems.append((kind, scr, f"page context lost after clicking '{clicked[-1] if clicked else '-'}': {str(e)[:90]}"))
                    page.goto(BASE + "/#" + scr)
                    page.wait_for_function("!document.getElementById('boot')", timeout=120000)
                    page.wait_for_timeout(1500)
                    continue
                items = [x for x in items if not SKIP.search(x["t"])]
                if not items:                                           # a screen can be briefly empty while it re-renders: look again
                    page.wait_for_timeout(2000)
                    items = [x for x in page.evaluate(CLICKABLE) if not SKIP.search(x["t"])]
                if not items:
                    problems.append((kind, scr, f"nothing clickable on the screen after clicking '{clicked[-1] if clicked else '-'}'"))
                    break
                it = rnd.choice(items)
                before_js, before_http = len(js), len(http)
                try:
                    page.locator(f'[data-mk="{it["i"]}"]').first.click(timeout=2500, no_wait_after=True)
                except Exception:
                    continue
                clicked.append(it["t"])
                page.wait_for_timeout(350)
                if len(js) > before_js:
                    problems.append((kind, scr, f"after clicking '{it['t']}': " + " | ".join(js[before_js:before_js + 2])))
                if len(http) > before_http:
                    problems.append((kind, scr, f"after clicking '{it['t']}': HTTP " + " | ".join(http[before_http:before_http + 2])))
                # leave modals / popovers so the next click lands on the screen
                page.keyboard.press("Escape")
                if page.evaluate("document.querySelector('.view.on') === null"):
                    problems.append((kind, scr, f"blank screen after clicking '{it['t']}'"))
                    page.evaluate(f"go('{scr}')")
                    page.wait_for_timeout(800)
                if page.evaluate("document.querySelector('.view.on') && document.querySelector('.view.on').id") != "v-" + (scr if scr != "alerts" or True else scr):
                    page.evaluate(f"go('{scr}')")                       # a click navigated away: that is allowed, come back
                    page.wait_for_timeout(1200)
            ov = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
            if ov > 0:
                problems.append((kind, scr, f"page is {ov}px wider than the screen after interaction"))
            print(f"  [{kind}] {scr:10s} {len(clicked):3d} clicks")
        ctx.close()
        b.close()
    return problems


if __name__ == "__main__":
    all_p = []
    for kind in ("web", "mobile"):
        all_p += run(kind, seed=7)
    seen = set()
    if all_p:
        print(f"\n{len(all_p)} PROBLEMS")
        for k, s, w in all_p:
            if (k, s, w) not in seen:
                seen.add((k, s, w))
                print(f" - [{k}] {s}: {w}")
        sys.exit(1)
    print("\nNO PROBLEMS FOUND")
