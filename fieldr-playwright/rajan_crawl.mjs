// Read-only crawl of the rajanjagz7 tenant: opens each page, records console errors and failing/odd API calls.
import { chromium } from "@playwright/test";
import fs from "fs";

const BASE = "https://rajanjagz7.dev.fieldr.app";
const STATE = "C:/Users/Baps/AppData/Local/Temp/claude/c--Users-Baps-Downloads-rajan-backup/4080ed99-fcc1-4297-8820-b9fd19f50d55/scratchpad/fieldr_rajan_state.json";
const OUT = "C:/Users/Baps/AppData/Local/Temp/claude/c--Users-Baps-Downloads-rajan-backup/4080ed99-fcc1-4297-8820-b9fd19f50d55/scratchpad/crawl.json";

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ storageState: STATE, viewport: { width: 1440, height: 900 } });
const page = await ctx.newPage();

let current = "";
const findings = {};
const add = (k, v) => ((findings[current] ||= { problems: [], apis: new Set() }).problems.push(v));
page.on("response", (r) => {
  const u = r.url();
  if (!u.includes("/api/")) return;
  const rec = (findings[current] ||= { problems: [], apis: new Set() });
  rec.apis.add(`${r.request().method()} ${u.replace(BASE, "").split("?")[0]}`);
  if (r.status() >= 400) rec.problems.push(`${r.status()} ${r.request().method()} ${u.replace(BASE, "").slice(0, 110)}`);
});
page.on("console", (m) => { if (m.type() === "error") add("c", "console: " + m.text().slice(0, 140)); });
page.on("pageerror", (e) => add("e", "pageerror: " + String(e).slice(0, 140)));

await page.goto(BASE + "/app/dashboard");
await page.locator('a[href^="/app/"]').first().waitFor({ timeout: 20000 });
await page.waitForTimeout(1500);
const nav = await page.locator("a[href^='/app/']").evaluateAll((as) => [...new Set(as.map((a) => a.getAttribute("href")))].filter((h) => h && h.startsWith("/app") && !h.includes("/new") && !/\/[0-9a-f]{24}/.test(h)));
console.log("nav links:", nav.length);

const extra = ["/app/global-settings/payment-cards", "/app/this-page-does-not-exist"];
for (const href of [...nav, ...extra]) {
  current = href;
  try {
    await page.goto(BASE + href, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2500);
    const rec = (findings[current] ||= { problems: [], apis: new Set() });
    rec.title = (await page.locator("h1, h2").first().innerText().catch(() => "")).slice(0, 60);
    rec.url = page.url().replace(BASE, "");
  } catch (e) {
    add("n", "navigation: " + String(e).slice(0, 100));
  }
}

const out = Object.fromEntries(Object.entries(findings).map(([k, v]) => [k, { ...v, apis: [...v.apis] }]));
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
for (const [k, v] of Object.entries(out)) {
  const flag = v.problems.length ? "!! " : "   ";
  console.log(`${flag}${k.padEnd(34)} -> ${(v.url || "").padEnd(34)} "${v.title || ""}"${v.problems.length ? "\n      " + v.problems.slice(0, 6).join("\n      ") : ""}`);
}
await browser.close();
