import { chromium } from "@playwright/test";
import dotenv from "dotenv";
import fs from "fs";
const env = dotenv.parse(fs.readFileSync("C:/Users/Baps/Downloads/rajan backup/fieldr-qa/pw/.env"));
const BASE = env.FLDR_BASE_URL;
const browser = await chromium.launch({ headless: true });
const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
const calls = [];
page.on("response", async (r) => { const q = r.request(); if (q.method() !== "GET" && r.url().includes("/api/")) calls.push(`${q.method()} ${r.url().replace(BASE, "")} -> ${r.status()} ${(await r.text().catch(() => "")).slice(0, 140)}`); });
await page.goto(BASE + "/login"); await page.getByRole("heading", { name: "Welcome to Fieldr" }).waitFor();
await page.getByRole("button", { name: "Mobile Number" }).click();
await page.locator("form").getByRole("textbox").first().fill(env.FLDR_MOBILE);
await page.getByRole("button", { name: "Send OTP" }).click();
await page.waitForTimeout(4000);
const boxes = page.getByRole("textbox", { name: /Digit/ });
console.log("otp boxes found:", await boxes.count());
if (await boxes.count() >= 6) {
  for (let i = 0; i < 6; i++) await boxes.nth(i).fill(env.FLDR_OTP[i]);
  await page.getByRole("button", { name: "Verify & Login" }).click();
  await page.waitForTimeout(4000);
}
console.log("url:", page.url().replace(BASE, ""));
console.log("calls:", calls);
console.log("page says:", (await page.locator("main").innerText().catch(() => "")).replace(/\n+/g, " | ").slice(0, 260));
await browser.close();
