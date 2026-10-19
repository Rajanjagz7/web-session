import { chromium } from "@playwright/test";
import dotenv from "dotenv";
import fs from "fs";
const env = dotenv.parse(fs.readFileSync("C:/Users/Baps/Downloads/rajan backup/fieldr-qa/pw/.env"));
const BASE = env.FLDR_BASE_URL;
const mode = process.argv[2] || "mobile";
const browser = await chromium.launch({ headless: true });
const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
const calls = [];
page.on("response", async (r) => { const q = r.request(); if (q.method() !== "GET" && r.url().includes("/api/")) calls.push(`${q.method()} ${r.url().replace(BASE, "")} -> ${r.status()} ${(await r.text().catch(() => "")).slice(0, 200)}`); });
await page.goto(BASE + "/login"); await page.getByRole("heading", { name: "Welcome to Fieldr" }).waitFor();
if (mode === "mobile") { await page.getByRole("button", { name: "Mobile Number" }).click(); await page.locator("form").getByRole("textbox").first().fill(env.FLDR_MOBILE); }
else { await page.getByRole("button", { name: "Email Address" }).click(); await page.locator("form").getByRole("textbox").first().fill(env.FLDR_EMAIL); }
const typed = await page.locator("form").getByRole("textbox").first().inputValue();
console.log("identifier typed (masked):", typed.replace(/\d(?=\d{3})/g, "*").replace(/(.{2}).+(@.*)/, "$1***$2"));
await page.getByRole("button", { name: "Send OTP" }).click();
await page.waitForTimeout(5000);
console.log(mode, "calls:", calls);
console.log("otp boxes:", await page.getByRole("textbox", { name: "Digit 1" }).count(), "| text:", (await page.locator("main").innerText()).replace(/\n+/g, " | ").slice(0, 300));
await browser.close();
