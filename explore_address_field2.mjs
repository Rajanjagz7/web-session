export default async function run(page, ui) {
  const netLog = [];
  page.on('request', (req) => {
    const u = req.url();
    if (/place|address|geocode|autocomplete/i.test(u)) netLog.push(`REQ ${req.method()} ${u}`);
  });
  page.on('response', (res) => {
    const u = res.url();
    if (/place|address|geocode|autocomplete/i.test(u)) netLog.push(`RES ${res.status()} ${u}`);
  });

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

  // Select country first
  snap = await ui.snapshot();
  const countryRef = snap.match(/@(e\d+) combobox "Country"/)?.[1];
  await ui.click(`@${countryRef}`);
  await page.waitForTimeout(500);
  await page.getByRole('option', { name: /^AU Australia/ }).click();
  await page.waitForTimeout(400);

  snap = await ui.snapshot();
  const addressRef = snap.match(/@(e\d+) combobox "Address"/)?.[1];
  await ui.click(`@${addressRef}`);
  await page.keyboard.type("125 Nancy Ellis", { delay: 40 });
  await page.waitForTimeout(2500);

  const withSuggestions = await ui.snapshot({ full: true });
  return { withSuggestions, netLog };
}
