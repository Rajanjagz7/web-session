// Read-only snapshots of release-note surfaces on the rajanjagz7 tenant.
import { chromium } from "@playwright/test";

const BASE = "https://rajanjagz7.dev.fieldr.app";
const STATE = "C:/Users/Baps/AppData/Local/Temp/claude/c--Users-Baps-Downloads-rajan-backup/4080ed99-fcc1-4297-8820-b9fd19f50d55/scratchpad/fieldr_rajan_state.json";
const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ storageState: STATE, viewport: { width: 1440, height: 900 } });
const page = await ctx.newPage();
const errors = [];
page.on("console", (m) => { if (m.type() === "error" && !/429/.test(m.text())) errors.push(m.text().slice(0, 120)); });
page.on("response", (r) => { if (r.url().includes("/api/") && r.status() >= 400 && r.status() !== 429) errors.push(`${r.status()} ${r.request().method()} ${r.url().replace(BASE, "").slice(0, 90)}`); });

const go = async (path) => { await page.goto(BASE + path, { waitUntil: "domcontentloaded" }); await page.locator("a[href^='/app/']").first().waitFor({ timeout: 25000 }).catch(() => {}); await page.waitForTimeout(2500); };
const buttons = async () => [...new Set((await page.getByRole("button").allInnerTexts()).map((t) => t.replace(/\s+/g, " ").trim()).filter(Boolean))].slice(0, 40);
const headers = async () => (await page.getByRole("columnheader").allInnerTexts()).map((t) => t.replace(/\s+/g, " ").trim());

console.log("=== QUOTES list");
await go("/app/quote/list");
console.log("columns:", await headers());
console.log("first rows:", (await page.getByRole("row").allInnerTexts()).slice(1, 4).map((t) => t.replace(/\s+/g, " ").slice(0, 150)));
console.log("buttons:", await buttons());

console.log("\n=== CUSTOMER list");
await go("/app/customer/list");
console.log("columns:", await headers());
console.log("first rows:", (await page.getByRole("row").allInnerTexts()).slice(1, 6).map((t) => t.replace(/\s+/g, " ").slice(0, 150)));

console.log("\n=== SCHEDULE header");
await go("/app/schedule");
console.log("buttons:", await buttons());

console.log("\n=== CREATE menu");
await go("/app/dashboard");
const create = page.getByRole("button", { name: /create|new|\+/i }).first();
console.log("create button text:", (await create.innerText().catch(() => "none")).replace(/\s+/g, " "));
await create.click().catch(() => {});
await page.waitForTimeout(800);
console.log("menu items:", (await page.getByRole("menuitem").allInnerTexts()).map((t) => t.replace(/\s+/g, " ").trim()));

console.log("\n=== ROLES (settings)");
await go("/app/global-settings/workspace");
const settingsLinks = await page.locator("a[href*='global-settings']").evaluateAll((as) => [...new Set(as.map((a) => (a.textContent || "").trim() + " -> " + a.getAttribute("href")))]);
console.log("settings links:", settingsLinks);
console.log("\nproblems seen:", [...new Set(errors)].slice(0, 12));
await browser.close();
