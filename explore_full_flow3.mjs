export default async function run(page, ui) {
  const netLog = [];
  page.on('response', (res) => {
    if (res.url().includes('/api/') && (res.request().method() === 'POST' || res.url().includes('sign'))) {
      netLog.push(`${res.status()} ${res.request().method()} ${res.url()}`);
    }
  });

  await page.waitForTimeout(1500);

  let snap = await ui.snapshot();
  await ui.click(`@${snap.match(/@(e\d+) button "Next"/)[1]}`);
  await page.waitForTimeout(800);

  snap = await ui.snapshot();
  const ref = (label) => snap.match(new RegExp(`@(e\\d+) textbox "${label}"`))?.[1];
  const email = `qa.test.${Date.now()}@example.com`;
  await ui.fill(`@${ref("First name")}`, "Test");
  await ui.fill(`@${ref("Last name")}`, "User");
  await ui.fill(`@${ref("Email address")}`, email);
  await ui.fill(`@${ref("Phone number")}`, "412345678");
  await ui.fill(`@${ref("Password")}`, "TestPass123!");
  await ui.fill(`@${ref("Confirm Password")}`, "TestPass123!");
  await page.waitForTimeout(300);
  snap = await ui.snapshot();
  await ui.click(`@${snap.match(/@(e\d+) button "Next"/)[1]}`);
  await page.waitForTimeout(800);

  snap = await ui.snapshot();
  const countryRef = snap.match(/@(e\d+) combobox "Country"/)?.[1];
  await ui.click(`@${countryRef}`);
  await page.waitForTimeout(500);
  await page.getByRole('option', { name: /^AU Australia/ }).click();
  await page.waitForTimeout(400);

  snap = await ui.snapshot();
  const streetRef = ref("Street Address");
  const cityRef = snap.match(/@(e\d+) textbox "City"/)?.[1];
  const stateRef = snap.match(/@(e\d+) textbox "State"/)?.[1];
  const postRef = snap.match(/@(e\d+) textbox "Post Code"/)?.[1];
  await ui.fill(`@${streetRef}`, "1 Test Street");
  await ui.fill(`@${cityRef}`, "Sydney");
  await ui.fill(`@${stateRef}`, "NSW");
  await ui.fill(`@${postRef}`, "2000");
  await page.waitForTimeout(300);

  snap = await ui.snapshot();
  const checkboxRef = snap.match(/@(e\d+) checkbox\b/)?.[1];
  await ui.click(`@${checkboxRef}`);
  await page.waitForTimeout(400);

  const beforeSubmit = await ui.snapshot({ full: true });

  snap = await ui.snapshot();
  const createRef = snap.match(/@(e\d+) button "Create Account"/)?.[1];
  await ui.click(`@${createRef}`);
  await page.waitForTimeout(4000);

  const afterSubmitUrl = page.url();
  const afterSubmitFull = await ui.snapshot({ full: true });

  return { email, beforeSubmit, afterSubmitUrl, afterSubmitFull, netLog };
}
