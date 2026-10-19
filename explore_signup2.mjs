export default async function run(page, ui) {
  await page.waitForTimeout(1500);

  let snap = await ui.snapshot();
  let next = snap.match(/@(e\d+) button "Next"/);
  await ui.click(`@${next[1]}`);
  await page.waitForTimeout(1000);

  snap = await ui.snapshot();
  const ref = (label) => snap.match(new RegExp(`@(e\\d+) textbox "${label}"`))?.[1];

  await ui.fill(`@${ref("First name")}`, "Test");
  await ui.fill(`@${ref("Last name")}`, "User");
  await ui.fill(`@${ref("Email address")}`, `qa.test.${Date.now()}@example.com`);
  await ui.fill(`@${ref("Phone number")}`, "412345678");
  await ui.fill(`@${ref("Password")}`, "TestPass123!");
  await ui.fill(`@${ref("Confirm Password")}`, "TestPass123!");

  await page.waitForTimeout(500);
  snap = await ui.snapshot();
  next = snap.match(/@(e\d+) button "Next"/);
  await ui.click(`@${next[1]}`);
  await page.waitForTimeout(1000);

  const step3 = await ui.snapshot({ full: true });
  return { step3 };
}
