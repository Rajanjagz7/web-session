// Logs in to the rajanjagz7 Fieldr tenant (credentials come from fieldr-qa/pw/.env; nothing is printed) and saves the session.
import { chromium } from "@playwright/test";
import dotenv from "dotenv";
import fs from "fs";

const envPath = "C:/Users/Baps/Downloads/rajan backup/fieldr-qa/pw/.env";
const env = dotenv.parse(fs.readFileSync(envPath));
const BASE = env.FLDR_BASE_URL;
const STATE = "C:/Users/Baps/AppData/Local/Temp/claude/c--Users-Baps-Downloads-rajan-backup/4080ed99-fcc1-4297-8820-b9fd19f50d55/scratchpad/fieldr_rajan_state.json";

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await ctx.newPage();
await page.goto(BASE + "/login");
await page.getByRole("heading", { name: "Welcome to Fieldr" }).waitFor();
await page.getByRole("button", { name: "Mobile Number" }).click();
const mobile = env.FLDR_MOBILE;
const box = page.locator("form").getByRole("textbox").first();
await box.click();
await box.press("End"); // keep the pre-filled "+61" prefix, type the digits after it like a person would
await box.pressSequentially(mobile, { delay: 60 });
console.log("field after typing (masked):", (await box.inputValue()).replace(/\d(?=\d{3})/g, "*"));
await page.getByRole("button", { name: "Send OTP" }).click();
await page.getByRole("textbox", { name: /Digit 1/ }).waitFor({ timeout: 25000 });
for (let i = 0; i < 6; i++) await page.getByRole("textbox", { name: new RegExp(`Digit ${i + 1}`) }).fill(env.FLDR_OTP[i]);
await page.getByRole("button", { name: "Verify & Login" }).click();
await page.waitForURL(/\/app/, { timeout: 30000 }).catch(() => {});
await page.waitForTimeout(3000);
console.log("landed:", page.url().replace(BASE, ""));
if (page.url().includes("/app")) {
  await ctx.storageState({ path: STATE });
  const nav = await page.locator("nav a, aside a").evaluateAll((as) => [...new Set(as.map((a) => (a.textContent || "").trim() + " -> " + a.getAttribute("href")))].filter((x) => x.length > 6));
  console.log("nav:", nav.slice(0, 40));
  console.log("title:", await page.title());
} else {
  console.log("login failed; page text:", (await page.locator("body").innerText()).replace(/\n+/g, " | ").slice(0, 300));
}
await browser.close();
