export default async function run(page, ui) {
  await page.waitForTimeout(1500);
  let snap = await ui.snapshot();
  await ui.click(`@${snap.match(/@(e\d+) button "Next"/)[1]}`);
  await page.waitForTimeout(800);

  snap = await ui.snapshot();
  const ref = (label) => snap.match(new RegExp(`@(e\\d+) textbox "${label}"`))?.[1];
  await ui.fill(`@${ref("First name")}`, "Test");
  await ui.fill(`@${ref("Last name")}`, "User");
  await ui.fill(`@${ref("Email address")}`, `qa.test.${Date.now()}@example.com`);
  await ui.fill(`@${ref("Phone number")}`, "412345678");
  await ui.fill(`@${ref("Password")}`, "TestPass123!");
  await ui.fill(`@${ref("Confirm Password")}`, "TestPass123!");
  await page.waitForTimeout(300);
  snap = await ui.snapshot();
  await ui.click(`@${snap.match(/@(e\d+) button "Next"/)[1]}`);
  await page.waitForTimeout(800);

  // Click the Country combobox to open its dropdown
  snap = await ui.snapshot();
  const countryRef = snap.match(/@(e\d+) combobox "Country"/)?.[1];
  await ui.click(`@${countryRef}`);
  await page.waitForTimeout(600);
  const opened = await ui.snapshot({ full: true });
  return { opened };
}
