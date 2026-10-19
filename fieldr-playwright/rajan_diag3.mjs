import { chromium } from "@playwright/test";
import dotenv from "dotenv";
import fs from "fs";
const env = dotenv.parse(fs.readFileSync("C:/Users/Baps/Downloads/rajan backup/fieldr-qa/pw/.env"));
const BASE = env.FLDR_BASE_URL;
const mask = (s) => s.replace(/\d(?=\d{3})/g, "*");
const browser = await chromium.launch({ headless: true });
for (const variant of ["fill", "type"]) {
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  const calls = [];
  page.on("response", async (r) => { const q = r.request(); if (q.method() !== "GET" && r.url().includes("/api/")) calls.push(`${q.method()} ${r.url().replace(BASE, "")} -> ${r.status()}`); });
  await page.goto(BASE + "/login"); await page.getByRole("heading", { name: "Welcome to Fieldr" }).waitFor();
  await page.getByRole("button", { name: "Mobile Number" }).click();
  const box = page.locator("form").getByRole("textbox").first();
  console.log(`--- ${variant}: initial field value:`, JSON.stringify(await box.inputValue()));
  if (variant === "fill") await box.fill(env.FLDR_MOBILE);
  else { await box.click(); await box.press("Control+A"); await box.press("Backspace"); await box.pressSequentially(env.FLDR_MOBILE, { delay: 50 }); }
  console.log("value after entering (masked):", mask(await box.inputValue()));
  await page.getByRole("button", { name: "Send OTP" }).click();
  await page.waitForTimeout(4000);
  console.log("api calls:", calls, "| otp boxes:", await page.getByRole("textbox", { name: /Digit/ }).count());
  console.log("page text:", (await page.locator("main").innerText()).replace(/\n+/g, " | ").slice(0, 200));
  await page.context().close();
}
await browser.close();
