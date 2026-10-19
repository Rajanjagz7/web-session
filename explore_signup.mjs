export default async function run(page, ui) {
  await page.waitForTimeout(1500);

  // Step 1: Account Type -> Individual is already checked, click Next
  let snap = await ui.snapshot();
  let next = snap.match(/@(e\d+) button "Next"/);
  await ui.click(`@${next[1]}`);
  await page.waitForTimeout(1000);

  const step2 = await ui.snapshot({ full: true });

  return { step2 };
}
