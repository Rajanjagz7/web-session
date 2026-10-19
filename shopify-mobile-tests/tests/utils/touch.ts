import type { Page } from '@playwright/test';

/**
 * Playwright's `page.touchscreen` only exposes `tap()` - there's no built-in
 * swipe. A JS-dispatched TouchEvent doesn't drive the browser's native
 * scroll/gesture recognizer either, so it wouldn't actually move the page.
 * Driving Input.dispatchTouchEvent over CDP does, because Chromium treats it
 * as real input. That ties this helper to Chromium - fine here since the
 * project only runs Mobile Chrome.
 */
export async function swipeUp(page: Page, distancePx = 400, steps = 10) {
  const viewport = page.viewportSize();
  if (!viewport) throw new Error('Viewport size not available for swipe gesture');

  const x = viewport.width / 2;
  const startY = viewport.height * 0.8;
  const endY = Math.max(startY - distancePx, viewport.height * 0.1);
  const touchPoint = (y: number) => [{ x, y, radiusX: 1, radiusY: 1, force: 1, id: 0 }];

  const cdp = await page.context().newCDPSession(page);
  try {
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: touchPoint(startY) });
    for (let i = 1; i <= steps; i++) {
      const y = startY + ((endY - startY) * i) / steps;
      await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: touchPoint(y) });
    }
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  } finally {
    await cdp.detach();
  }
}
