export default async function run(page, ui) {
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

  const debugSnap = await ui.snapshot();
  return { debugSnap, email };
}
