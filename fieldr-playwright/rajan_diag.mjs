import { chromium } from "@playwright/test";
import dotenv from "dotenv";
import fs from "fs";
const env = dotenv.parse(fs.readFileSync("C:/Users/Baps/Downloads/rajan backup/fieldr-qa/pw/.env"));
const BASE = env.FLDR_BASE_URL;
const browser = await chromium.launch({ headless: true });
const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
const calls = [];
page.on("response", async (r) => { const q = r.request(); if (q.method() !== "GET" && r.url().includes("fieldr")) calls.push(`${q.method()} ${r.url().replace(BASE, "")} -> ${r.status()} ${(await r.text().catch(() => "")).slice(0, 160)}`); });
await page.goto(BASE + "/login");
await page.getByRole("heading", { name: "Welcome to Fieldr" }).waitFor();
for (const mode of ["mobile", "email"]) {
  await page.goto(BASE + "/login"); await page.getByRole("heading", { name: "Welcome to Fieldr" }).waitFor();
  calls.length = 0;
  if (mode === "mobile") { await page.getByRole("button", { name: "Mobile Number" }).click(); await page.locator("form").getByRole("textbox").first().fill(env.FLDR_MOBILE.replace(/^\+?61/, "").replace(/^0/, "")); }
  else { await page.getByRole("button", { name: "Email Address" }).click(); await page.locator("form").getByRole("textbox").first().fill(env.FLDR_EMAIL); }
  await page.getByRole("button", { name: "Send OTP" }).click();
  await page.waitForTimeout(5000);
  console.log(`--- ${mode}:`, calls, "| otp boxes:", await page.getByRole("textbox", { name: "Digit 1" }).count(), "| text:", (await page.locator("main").innerText()).replace(/\n+/g, " | ").slice(0, 260));
}
await browser.close();
