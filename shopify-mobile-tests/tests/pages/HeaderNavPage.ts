import { expect, type Locator, type Page } from '@playwright/test';

/**
 * The mobile header's nav is a native <details>/<summary> disclosure
 * (id="Details-menu-drawer-container" -> #menu-drawer), not a JS-driven
 * off-canvas panel. Its open/closed state is exactly the <details open>
 * attribute, so Playwright's normal visibility checks (backed by the
 * browser's own rendering of closed <details> content) are enough - no
 * custom waiting logic needed.
 */
export class HeaderNavPage {
  readonly page: Page;
  readonly burgerButton: Locator;
  readonly drawer: Locator;
  readonly closeButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.burgerButton = page.getByRole('button', { name: 'Menu' });
    this.drawer = page.locator('#menu-drawer');
    this.closeButton = this.drawer.getByRole('button', { name: 'Close' });
  }

  navLink(name: string | RegExp): Locator {
    return this.drawer.getByRole('link', { name });
  }

  async open() {
    await expect(this.burgerButton).toBeVisible();
    await this.burgerButton.tap();
    await expect(this.drawer).toBeVisible();
  }

  async close() {
    await this.closeButton.tap();
    await expect(this.drawer).toBeHidden();
  }
}
