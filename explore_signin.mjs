export default async function run(page, ui) {
  await page.waitForTimeout(2500);
  const before = await ui.snapshot();
  const addBtn = before.match(/@(e\d+) button "Add to cart"(?!\s*\[disabled\])/);
  await ui.click(`@${addBtn[1]}`);
  await page.waitForTimeout(1500);

  const toastSnap = await ui.snapshot();
  const toastText = await page.locator('[role="status"], [class*="toast"], [data-sonner-toast]').allInnerTexts().catch(() => []);

  const signInBtn = toastSnap.match(/@(e\d+) button "Sign In"/);
  if (signInBtn) {
    await ui.click(`@${signInBtn[1]}`);
    await page.waitForTimeout(1500);
  }

  const modalSnap = await ui.snapshot({ full: true });
  return { toastText, url: page.url(), modalSnap };
}
