#!/usr/bin/env python3
"""Builds the shareable bug report (HTML page, CSV, Markdown) from one data set, so they never disagree.
Output: crm-qa-suite/report/  (bug-report.html, bugs.csv, bugs.md). Contains NO credentials."""
import csv
import html
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "report"
OUT.mkdir(exist_ok=True)

META = {
    "env": "https://crm.staging.notbhavik.dev (staging)",
    "project": "Vercel 3 (6abe377f6194a264a524b653)",
    "date": "1 Oct 2026",
    "scope": "Pipelines, Deals, Contacts, Companies, Close reasons, Files, Imports, Exports, Reports, auth and tenant isolation; "
             "UI in Chromium, Firefox, WebKit and mobile (375 px).",
    "method": "Manual exploration plus over 200 automated checks (pytest for the API, Playwright for the UI), "
              "then fuzzing of bodies, IDs, queries, cursors and encodings. Test data was created and removed by the tests.",
}

# severity: Medium | Low.   layer: Backend | Frontend | Hardening
BUGS = [
 dict(id="BUG-01", sev="Medium", layer="Backend", area="Search (contacts, companies, deals, files)",
      title="A null byte in the search query returns HTTP 500",
      repro="GET /api/crm/v1/contacts?q=a%00b   (same on /companies, /deals, /files)",
      expected="400 validation error, or the search ignores the character.",
      actual="500 internal_error. Other special characters (% \\ ( [ * $ quotes, newlines) are handled fine. The UI search box would show a generic failure.",
      fix="Strip or reject U+0000 in query-string params before they reach the database layer."),
 dict(id="BUG-02", sev="Medium", layer="Frontend", area="Session handling",
      title="Expired session on submit shows a raw API message and leaves the dialog open",
      repro="Sign in, open Pipelines > New pipeline, fill the form, clear cookies (or let the session expire), press Create pipeline.",
      expected="Redirect to /login?next=... or a clear 'Your session expired, sign in again' message that keeps the draft.",
      actual="Dialog stays open and shows 'A secret API key or Dashboard session is required' (developer wording). No sign-in prompt. Reloading goes to the login page and the draft is lost. A normal page load redirects correctly.",
      fix="Handle 401 from the API client centrally: redirect to login with next=, and show a user-facing message."),
 dict(id="BUG-03", sev="Low", layer="Backend", area="Contacts",
      title="Contact phone number is not validated",
      repro='POST /contacts {"firstName":"T","phone":"abc"}  (also "1" and a 40-digit string)',
      expected="400 for values that are not phone numbers (or normalise to E.164).",
      actual="201, stored as entered.",
      fix="Validate and normalise phone numbers."),
 dict(id="BUG-04", sev="Low", layer="Backend", area="Companies",
      title="Company phone and domain are not validated or normalised",
      repro='POST /companies {"name":"x","phone":"xyz","domain":"not a domain"}   also domain "https://example.com/path" and "EXAMPLE.com"',
      expected="400 for invalid values; domain stored as a lower-case hostname.",
      actual="201. 'not a domain' and a full URL are stored verbatim; 'EXAMPLE.com' keeps its case (contact emails are lower-cased).",
      fix="Validate hostname, strip scheme and path, lower-case; validate phone as above."),
 dict(id="BUG-05", sev="Low", layer="Backend", area="Contacts",
      title="Whitespace-only first name is accepted",
      repro='POST /contacts {"firstName":"   "}',
      expected="400, as for an empty name (pipeline names are trimmed and rejected).",
      actual="201 with a blank-looking contact.",
      fix="Trim, then require at least 1 character."),
 dict(id="BUG-06", sev="Low", layer="Backend", area="Contacts",
      title="ownerActorId is not checked against real users",
      repro='POST /contacts {"firstName":"T","ownerActorId":"nope"}',
      expected="400/404 when the user does not exist in the workspace.",
      actual="201. 'nope' then appears as an owner in the contacts.by_owner report.",
      fix="Verify the actor exists and is a member of the workspace."),
 dict(id="BUG-07", sev="Low", layer="Backend", area="Contacts, Companies",
      title="Inconsistent field length limits",
      repro="POST /companies with a 300-character name; POST /contacts with a 300-character email.",
      expected="Limits consistent with the rest of the API (pipeline name 120, contact name 200) and email at most 254.",
      actual="Company name has no practical limit (300 accepted); a 300-character email is accepted (RFC limit is 254).",
      fix="Set explicit maximums on every string field."),
 dict(id="BUG-08", sev="Low", layer="Backend", area="All string fields",
      title="Control characters are accepted and stored in names",
      repro='POST /pipelines {"name":"a\\u0000b","stages":[{"name":"s"}]}   also "\\n", "\\r\\nX-Evil: 1", "\\u0001"',
      expected="400 for control characters in single-line fields.",
      actual="201, stored verbatim. The UI renders them safely, but logs, CSV exports and other tools can be confused.",
      fix="Reject or strip control characters (U+0000-U+001F, U+007F) in single-line fields."),
 dict(id="BUG-09", sev="Low", layer="Backend", area="Request parsing",
      title="Invalid UTF-8 is accepted and silently replaced",
      repro='POST /pipelines with raw body bytes {"name":"\\xff\\xfe",...} and content-type application/json',
      expected="400 'body is not valid UTF-8'.",
      actual="201; the name is stored as two U+FFFD replacement characters. A lone surrogate becomes three.",
      fix="Decode strictly (fatal on invalid sequences)."),
 dict(id="BUG-10", sev="Low", layer="Backend", area="Validation",
      title="The 120-character name limit counts UTF-16 units, not characters",
      repro='POST /pipelines {"name":"<100 x U+1F600>",...}',
      expected="Accepted: 100 characters is under the 120 limit.",
      actual="400 'Too big: expected string to have <=120 characters' (the string is 200 UTF-16 units).",
      fix="Count code points (or grapheme clusters), not string length."),
 dict(id="BUG-11", sev="Low", layer="Backend", area="Proxy / API",
      title="Oversized request bodies sometimes get an empty 502 instead of 413",
      repro="POST a 10 MB JSON body to /pipelines several times. Observed once in about 5 attempts. The limit sits between 1 MB and 2 MB.",
      expected="Always 413 with the JSON error body.",
      actual="Usually 413; intermittently an empty 502 from the proxy (the app closes the connection while the client is still uploading). The service stays healthy.",
      fix="Reject on Content-Length before reading the body, or drain the request before closing."),
 dict(id="BUG-12", sev="Low", layer="Backend", area="HTTP",
      title="TRACE returns a bare 500",
      repro="TRACE /api/crm/v1/pipelines",
      expected="405 or 404 in the standard JSON error format (TRACE should be disabled).",
      actual="500 'Internal Server Error' as plain text.",
      fix="Disable TRACE at the proxy or add a route that returns 405."),
 dict(id="BUG-13", sev="Low", layer="Hardening", area="Request handling",
      title="text/plain bodies are parsed as JSON; mutating calls without an Origin header are accepted",
      repro='POST /pipelines with content-type: text/plain and a JSON body -> 201. Also a session-cookie POST with no Origin header -> 201.',
      expected="415 for non-JSON content types; ideally an Origin/Sec-Fetch-Site check on cookie-authenticated writes.",
      actual="Accepted. Not exploitable today because the required crm-* headers force a CORS preflight, but it removes a layer of CSRF protection. (The login endpoint is protected and rejects cross-site requests.)",
      fix="Require application/json on write endpoints; check Origin/Sec-Fetch-Site for cookie sessions."),
 dict(id="BUG-14", sev="Low", layer="Backend", area="Pipelines",
      title="Stage order has gaps after a stage is deleted",
      repro="Create a pipeline with stages A, B, C; delete B; read the pipeline.",
      expected="order values 0, 1.",
      actual="Remaining stages keep order 0, 2 until the next reorder call. Harmless unless a client assumes consecutive values.",
      fix="Renumber on delete."),
 dict(id="BUG-15", sev="Low", layer="Backend", area="Headers",
      title="An unknown Crm-Org-Id header value is accepted silently",
      repro="Any GET with the header crm-org-id: nope",
      expected="400/403 for an organization that does not exist.",
      actual="200, treated as the default organization.",
      fix="Validate the header against the user's organizations."),
 dict(id="BUG-16", sev="Low", layer="Frontend", area="All pages (accessibility)",
      title="Every page has the same browser title, 'CRM Dashboard'",
      repro="Open Pipelines, Contacts, Deals, Reports; read the tab title or document.title.",
      expected="A distinct title per page, e.g. 'Pipelines - Vercel 3 - CRM' (WCAG 2.4.2 Page Titled).",
      actual="'CRM Dashboard' everywhere (not-found pages are the only ones that differ). Tabs, history and screen readers cannot tell pages apart.",
      fix="Set a per-route title."),
 dict(id="BUG-17", sev="Low", layer="Frontend", area="Reports, Automation, Outbox, Products, My work (accessibility)",
      title="Heading levels skip from h1 to h3",
      repro="Open the pages listed and inspect the headings, or run any heading-outline checker.",
      expected="Levels step down one at a time (h1, h2, h3).",
      actual="h1 is followed directly by h3 (WCAG 1.3.1).",
      fix="Use h2 for section headings, or restyle with CSS instead of changing the level."),
 dict(id="BUG-18", sev="Low", layer="Frontend", area="Files page (accessibility)",
      title="One form field has no label",
      repro="Open the Files page and inspect inputs for a label, aria-label or aria-labelledby.",
      expected="Every control has an accessible name.",
      actual="One input has none, so a screen reader announces it as an unnamed edit field.",
      fix="Add a visible label or aria-label."),
 dict(id="BUG-19", sev="Low", layer="Frontend", area="New pipeline dialog",
      title="Escape closes the dialog and discards typed input without warning",
      repro="Open New pipeline, type a name and stages, press Escape.",
      expected="Either keep the draft or ask before discarding.",
      actual="Closes immediately; the draft is lost. (Focus correctly returns to the trigger button.)",
      fix="Confirm when the form is dirty."),
 dict(id="BUG-20", sev="Low", layer="Frontend", area="Pipelines table at 375 px",
      title="Table cells are truncated on mobile",
      repro="Open Pipelines at 375 px width.",
      expected="Names and dates readable, or the row opens to show the full value.",
      actual="Names show as 'Enterpri...' and the Updated column as 'Oct 1, 2...'. There is no horizontal page scroll.",
      fix="Allow wrapping or stack the row on narrow screens."),
]

DESIGN = [
 ("D-1", "Duplicates are allowed everywhere", "Pipelines (even differing only by case), contacts (same email in any case), companies and close-reason labels can be duplicated. Three parallel creates of the same pipeline name made three pipelines. Stage names within a pipeline and close-reason codes ARE unique. Decide which should be unique, for example contact email."),
 ("D-2", "Stages can be added to an archived pipeline", "The page says an archived pipeline 'takes no new deals', but its stages can still be changed."),
 ("D-3", "Import cannot update existing records", "onDuplicate supports only 'create' (default) and 'reject'. A re-import always creates duplicates unless reject is used; there is no update or skip mode."),
 ("D-4", "Archiving with dependants is allowed", "A pipeline with open deals, and a company with contacts and deals, can be archived. Deleting them is correctly blocked with 409."),
 ("D-5", "Moving a deal to its current stage returns 200", "A no-op is accepted and succeeds rather than reporting 'already in this stage'."),
 ("D-6", "Removing an in-use close reason is allowed", "Deals keep the old code, which is reasonable, but the UI does not warn how many deals use it."),
]

PASSED = [
 "Delete guards: a stage with open deals, a pipeline with any deals, a company with references and the last active stage are all blocked with 409.",
 "Deal state machine: won, lost and reopen enforce valid transitions; closed deals cannot move or close twice; three parallel 'won' calls give one 200 and two 409s.",
 "Close reasons: outcome-specific, exact-code match, code format, 50-reason cap, duplicate code rejected.",
 "Money: integer minor units, no negatives, safe-integer maximum, uppercase ISO currency.",
 "Tenant isolation: another project's records return 404 for read, edit and delete; no session returns 401; bad project header returns 403; no data leaks through cursors or reports.",
 "Pagination: signed cursors bound to resource and project; every tampered cursor returns 400; no duplicates or gaps at limits 1, 7, 25, 100.",
 "Injection: XSS payloads in names and URL parameters never execute and are never reflected into the DOM; SQL, NoSQL and regex strings in search are inert; no open redirect through login ?next=.",
 "Uploads: presigned S3 flow works; type allowlist and 25 MB cap enforced; filenames are labels only (ID-based storage keys).",
 "Imports and exports: 1,500-row import OK; BOM, CRLF, quoted commas and newlines, unicode OK; per-row errors are accurate; 'reject' mode blocks duplicates; exported CSV neutralises formula cells and re-imports losslessly.",
 "Resilience: offline submit keeps the draft and a retry makes exactly one record; acting on a record deleted in another tab shows a clear error; double-click on Create makes one pipeline; no layout overflow from hostile names at desktop or 375 px.",
 "Dialog accessibility and keyboard: modal, labelled, focus trapped and restored; create works with keyboard only; behaviour matches in Chromium and Firefox (WebKit differs only in Safari's own focus rule).",
]

NOT_TESTED = [
 "Member and other non-owner roles (only one account existed): permissions in Settings, member management, API keys.",
 "Automation, Properties, Audit, Catalog products and Outbox beyond layout and accessibility checks.",
 "Real screen readers (NVDA, VoiceOver, TalkBack) and Safari on macOS or iOS hardware.",
 "Export file expiry after 7 days; load and performance testing (deliberately out of scope).",
]


def md_bug(b):
    return (f"### {b['id']} [{b['sev']}] {b['title']}\n"
            f"- **Layer:** {b['layer']}  |  **Area:** {b['area']}\n"
            f"- **Steps / request:** {b['repro']}\n"
            f"- **Expected:** {b['expected']}\n"
            f"- **Actual:** {b['actual']}\n"
            f"- **Suggested fix:** {b['fix']}\n")


def write_md():
    L = ["# CRM staging bug report", "",
         f"Environment: {META['env']}  |  Project: {META['project']}  |  Date: {META['date']}", "",
         f"Scope: {META['scope']}", "", f"Method: {META['method']}", "",
         f"**{len(BUGS)} bugs** ({sum(b['sev']=='Medium' for b in BUGS)} medium, {sum(b['sev']=='Low' for b in BUGS)} low): "
         f"{sum(b['layer']=='Backend' for b in BUGS)} backend, {sum(b['layer']=='Frontend' for b in BUGS)} frontend, "
         f"{sum(b['layer']=='Hardening' for b in BUGS)} hardening. No critical or high severity and no data-exposure issue was found.", "",
         "## Bugs", ""]
    L += [md_bug(b) for b in BUGS]
    L += ["## Design questions (decide whether intended)", ""] + [f"- **{i} {t}.** {d}" for i, t, d in DESIGN]
    L += ["", "## Verified working", ""] + [f"- {p}" for p in PASSED]
    L += ["", "## Not tested", ""] + [f"- {p}" for p in NOT_TESTED]
    (OUT / "bugs.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def write_csv():
    with open(OUT / "bugs.csv", "w", newline="", encoding="utf-8-sig") as f:  # BOM so Excel opens UTF-8 correctly
        w = csv.writer(f)
        w.writerow(["ID", "Severity", "Layer", "Area", "Title", "Steps / request", "Expected", "Actual", "Suggested fix"])
        for b in BUGS:
            w.writerow([b["id"], b["sev"], b["layer"], b["area"], b["title"], b["repro"], b["expected"], b["actual"], b["fix"]])
        for i, t, d in DESIGN:
            w.writerow([i, "Question", "Design", "", t, "", "", d, ""])


def e(s):
    return html.escape(s, quote=True)


CSS = """
<style>
:root{
  /* Layout: a single readable column; summary first, then filterable bug cards, then reference lists. */
  --bg:#f6f7f9; --card:#ffffff; --fg:#1c2330; --muted:#5b6678; --line:#dde1e8; --soft:#eef1f5;
  --accent:#2457d6; --accent-fg:#ffffff;
  --med-bg:#fdeed9; --med-fg:#8a4b00; --low-bg:#e8edf4; --low-fg:#3d4a5f;
  --be:#2457d6; --fe:#0b7a66; --hd:#8a3ea8;
  --font:'IBM Plex Sans',system-ui,-apple-system,'Segoe UI',sans-serif; --mono:'IBM Plex Mono',ui-monospace,Consolas,monospace;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#12151b; --card:#1b2029; --fg:#e6e9ef; --muted:#9aa5b6; --line:#2c3340; --soft:#232a35;
  --accent:#7ba0ff; --accent-fg:#0d1320; --med-bg:#3a2a12; --med-fg:#ffc577; --low-bg:#263040; --low-fg:#b8c3d6;
  --be:#7ba0ff; --fe:#4fd1b4; --hd:#d09bec; color-scheme:dark}}
:root[data-theme="dark"]{
  --bg:#12151b; --card:#1b2029; --fg:#e6e9ef; --muted:#9aa5b6; --line:#2c3340; --soft:#232a35;
  --accent:#7ba0ff; --accent-fg:#0d1320; --med-bg:#3a2a12; --med-fg:#ffc577; --low-bg:#263040; --low-fg:#b8c3d6;
  --be:#7ba0ff; --fe:#4fd1b4; --hd:#d09bec; color-scheme:dark}
body{background:var(--bg);color:var(--fg);font-family:var(--font);font-size:15px;line-height:1.55;margin:0}
.wrap{max-width:860px;margin:0 auto;padding:28px 16px 64px;box-sizing:border-box}
h1{font-size:28px;line-height:1.2;margin:0 0 6px;text-wrap:balance}
h2{font-size:19px;margin:36px 0 12px;text-wrap:balance}
.lede{color:var(--muted);margin:0 0 20px;max-width:65ch}
dl.meta{display:grid;grid-template-columns:max-content 1fr;gap:6px 16px;margin:0 0 22px;font-size:14px}
dl.meta dt{color:var(--muted)} dl.meta dd{margin:0;min-width:0;overflow-wrap:anywhere}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:0 0 8px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px}
.stat b{display:block;font-size:26px;line-height:1.1;font-variant-numeric:tabular-nums}
.stat span{color:var(--muted);font-size:13px}
.verdict{background:var(--soft);border-radius:8px;padding:12px 14px;margin:10px 0 0;font-size:14px}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 14px}
.chip{font:inherit;font-size:13px;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:999px;padding:5px 12px;cursor:pointer}
.chip[aria-pressed="true"]{background:var(--accent);color:var(--accent-fg);border-color:var(--accent)}
.chip:focus-visible,.copy:focus-visible,a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.spacer{flex:1}
.bug{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px;margin:0 0 12px;display:grid;gap:10px;min-width:0}
.bug.med{border-left:4px solid var(--med-fg)}
.bug h3{font-size:16.5px;margin:0;line-height:1.35;text-wrap:balance}
.head{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.id{font-family:var(--mono);font-size:12.5px;color:var(--muted)}
.tag{font-size:12px;border-radius:4px;padding:2px 8px;font-weight:600;letter-spacing:.02em}
.tag.Medium{background:var(--med-bg);color:var(--med-fg)} .tag.Low{background:var(--low-bg);color:var(--low-fg)}
.layer{font-size:12px;font-weight:600;letter-spacing:.04em;text-transform:uppercase}
.layer.Backend{color:var(--be)} .layer.Frontend{color:var(--fe)} .layer.Hardening{color:var(--hd)}
.area{color:var(--muted);font-size:13px}
.kv{display:grid;grid-template-columns:96px 1fr;gap:4px 12px;margin:0;font-size:14px}
.kv dt{color:var(--muted)} .kv dd{margin:0;min-width:0;overflow-wrap:anywhere}
code,.repro{font-family:var(--mono);font-size:12.8px;background:var(--soft);border-radius:4px;padding:1px 5px}
.repro{display:block;padding:8px 10px;white-space:pre-wrap;overflow-wrap:anywhere}
.copy{font:inherit;font-size:12.5px;border:1px solid var(--line);background:transparent;color:var(--accent);border-radius:6px;padding:3px 10px;cursor:pointer;margin-left:auto}
ul.plain{margin:0;padding-left:20px;display:grid;gap:8px} ul.plain li{padding-left:2px}
.design{display:grid;gap:10px;margin:0;padding:0;list-style:none}
.design li{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px}
.design b{display:block;margin-bottom:2px}
footer{color:var(--muted);font-size:13px;margin-top:36px}
@media (max-width:520px){.kv{grid-template-columns:1fr}.kv dt{margin-top:6px}}
</style>
"""

JS = """
<script>
(function(){
  var chips=document.querySelectorAll('.chip[data-f]'), bugs=document.querySelectorAll('.bug'), count=document.getElementById('shown');
  function apply(f){
    var n=0;
    bugs.forEach(function(b){var ok=f==='all'||b.dataset.layer===f||b.dataset.sev===f; b.hidden=!ok; if(ok)n++;});
    chips.forEach(function(c){c.setAttribute('aria-pressed',String(c.dataset.f===f));});
    count.textContent=n+' of '+bugs.length+' shown';
  }
  chips.forEach(function(c){c.addEventListener('click',function(){apply(c.dataset.f);});});
  function copyText(t,btn){
    var done=function(){var o=btn.textContent;btn.textContent='Copied';setTimeout(function(){btn.textContent=o;},1400);};
    var fallback=function(){var ta=document.createElement('textarea');ta.value=t;ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);ta.select();try{document.execCommand('copy');done();}catch(e){btn.textContent='Select and copy manually';}document.body.removeChild(ta);};
    if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(done,fallback);}else{fallback();}
  }
  document.querySelectorAll('.copy[data-md]').forEach(function(b){b.addEventListener('click',function(){copyText(document.getElementById(b.dataset.md).textContent,b);});});
  apply('all');
})();
</script>
"""


def html_bug(b):
    med = " med" if b["sev"] == "Medium" else ""
    md_id = "md-" + b["id"]
    return f"""
<article class="bug{med}" data-layer="{e(b['layer'])}" data-sev="{e(b['sev'])}" id="{e(b['id'])}">
  <div class="head"><span class="id">{e(b['id'])}</span><span class="tag {e(b['sev'])}">{e(b['sev'])}</span>
    <span class="layer {e(b['layer'])}">{e(b['layer'])}</span>
    <button class="copy" type="button" data-md="{md_id}" aria-label="Copy {e(b['id'])} as Markdown">Copy</button></div>
  <h3>{e(b['title'])}</h3>
  <div class="area">{e(b['area'])}</div>
  <dl class="kv">
    <dt>Steps</dt><dd><span class="repro">{e(b['repro'])}</span></dd>
    <dt>Expected</dt><dd>{e(b['expected'])}</dd>
    <dt>Actual</dt><dd>{e(b['actual'])}</dd>
    <dt>Suggested fix</dt><dd>{e(b['fix'])}</dd>
  </dl>
  <script type="text/plain" id="{md_id}">{e(md_bug(b))}</script>
</article>"""


def write_html():
    med = sum(b["sev"] == "Medium" for b in BUGS)
    low = sum(b["sev"] == "Low" for b in BUGS)
    be, fe, hd = (sum(b["layer"] == x for b in BUGS) for x in ("Backend", "Frontend", "Hardening"))
    body = f"""<title>CRM Staging Bug Report</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
{CSS}
<div class="wrap">
  <h1>CRM staging bug report</h1>
  <p class="lede">{len(BUGS)} defects found across the API and the web app, with the steps to reproduce each one. Nothing critical or high-severity, and no case of one customer's data reaching another.</p>
  <dl class="meta">
    <dt>Environment</dt><dd>{e(META['env'])}</dd>
    <dt>Project</dt><dd>{e(META['project'])}</dd>
    <dt>Tested</dt><dd>{e(META['date'])}</dd>
    <dt>Scope</dt><dd>{e(META['scope'])}</dd>
    <dt>Method</dt><dd>{e(META['method'])}</dd>
  </dl>
  <div class="stats">
    <div class="stat"><b>{med}</b><span>Medium</span></div><div class="stat"><b>{low}</b><span>Low</span></div>
    <div class="stat"><b>{be}</b><span>Backend</span></div><div class="stat"><b>{fe}</b><span>Frontend</span></div>
    <div class="stat"><b>{hd}</b><span>Hardening</span></div><div class="stat"><b>{len(DESIGN)}</b><span>Design questions</span></div>
  </div>
  <p class="verdict">Fix first: <a href="#BUG-01">BUG-01</a> (search returns 500) and <a href="#BUG-02">BUG-02</a> (expired session shows a developer error). The Low items are mostly missing validation and accessibility gaps.</p>

  <h2>Bugs</h2>
  <div class="bar" role="group" aria-label="Filter bugs">
    <button class="chip" type="button" data-f="all" aria-pressed="true">All</button>
    <button class="chip" type="button" data-f="Backend" aria-pressed="false">Backend</button>
    <button class="chip" type="button" data-f="Frontend" aria-pressed="false">Frontend</button>
    <button class="chip" type="button" data-f="Hardening" aria-pressed="false">Hardening</button>
    <button class="chip" type="button" data-f="Medium" aria-pressed="false">Medium only</button>
    <span class="spacer"></span><span class="area" id="shown" aria-live="polite"></span>
    <button class="copy" type="button" data-md="md-all" style="margin-left:0">Copy all as Markdown</button>
  </div>
  <script type="text/plain" id="md-all">{e(chr(10).join(md_bug(b) for b in BUGS))}</script>
  {''.join(html_bug(b) for b in BUGS)}

  <h2>Design questions</h2>
  <p class="lede">Not defects as such. Each needs a product decision on whether the current behaviour is intended.</p>
  <ul class="design">{''.join(f'<li><b>{e(i)} {e(t)}</b>{e(d)}</li>' for i, t, d in DESIGN)}</ul>

  <h2>Checked and working</h2>
  <ul class="plain">{''.join(f'<li>{e(p)}</li>' for p in PASSED)}</ul>

  <h2>Not tested</h2>
  <ul class="plain">{''.join(f'<li>{e(p)}</li>' for p in NOT_TESTED)}</ul>

  <footer>Most items above have an automated regression test in the crm-qa-suite folder; the rest (such as the truncated mobile table) were checked by hand. Known bugs are written as expected failures, so once one is fixed its test fails until the marker is removed. This report contains no credentials.</footer>
</div>
{JS}
"""
    (OUT / "bug-report.html").write_text(body, encoding="utf-8")


if __name__ == "__main__":
    write_md(); write_csv(); write_html()
    print(f"wrote {len(BUGS)} bugs + {len(DESIGN)} design questions to {OUT}")
