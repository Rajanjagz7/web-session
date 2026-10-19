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

  // Click into the Address combobox and type
  snap = await ui.snapshot();
  const addressRef = snap.match(/@(e\d+) combobox "Address"/)?.[1];
  await ui.click(`@${addressRef}`);
  await page.keyboard.type("1 George Street Sydney", { delay: 30 });
  await page.waitForTimeout(2000);

  const withSuggestions = await ui.snapshot({ full: true });
  return { withSuggestions };
}
