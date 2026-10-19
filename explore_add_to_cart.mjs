export default async function run(page, ui) {
  await page.waitForTimeout(2500);
  const before = await ui.snapshot();
  const match = before.match(/@(e\d+) button "Add to cart"(?!\s*\[disabled\])/);
  if (!match) return { error: "no enabled Add to cart button found", before };

  await ui.click(`@${match[1]}`);
  await page.waitForTimeout(2000);

  const url = page.url();
  const after = await ui.snapshot();
  return { clickedRef: match[1], url, after };
}
