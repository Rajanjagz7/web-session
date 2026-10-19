export default async function run(page, ui) {
  await page.waitForTimeout(2500);
  const snap = await ui.snapshot();
  return { snap };
}
