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

  // Inspect Country combobox current value + options
  const countryBox = page.getByRole('combobox', { name: /country/i });
  const countryValue = await countryBox.innerText().catch(() => null);

  snap = await ui.snapshot();
  const streetRef = ref("Street Address");
  const street2Ref = snap.match(/@(e\d+) textbox "Street Address 2"/)?.[1];
  const cityRef = snap.match(/@(e\d+) textbox "City"/)?.[1];
  const stateRef = snap.match(/@(e\d+) textbox "State"/)?.[1];
  const postRef = snap.match(/@(e\d+) textbox "Post Code"/)?.[1];

  if (streetRef) await ui.click(`@${streetRef}`);
  if (streetRef) await page.keyboard.type("1 Test Street", { delay: 20 });
  if (cityRef) await ui.fill(`@${cityRef}`, "Sydney");
  if (stateRef) await ui.fill(`@${stateRef}`, "NSW");
  if (postRef) await ui.fill(`@${postRef}`, "2000");

  await page.waitForTimeout(500);
  const afterFill = await ui.snapshot();
  const checkboxRef = afterFill.match(/@(e\d+) checkbox "I agree/)?.[1];
  if (checkboxRef) await ui.click(`@${checkboxRef}`);
  await page.waitForTimeout(500);

  const final = await ui.snapshot({ full: true });
  return { countryValue, final };
}
