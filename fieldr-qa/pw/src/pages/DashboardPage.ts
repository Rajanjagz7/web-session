import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

export class DashboardPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  heading = () => this.page.getByRole('heading', { name: 'Dashboard', level: 1 });
  navLink = (name: string) => this.page.getByRole('link', { name, exact: true });
  userMenuBtn = () => this.page.getByRole('button', { name: /@/ });
  // NEEDS UI INSPECTION: the logout menu item label was not observed. Regex is a best guess.
  logoutMenuItem = () => this.page.getByRole('menuitem', { name: /log\s?out|sign\s?out/i });

  async open(): Promise<void> {
    await this.navigate('/app/dashboard');
  }

  async openDeepLink(path: string): Promise<void> {
    await this.navigate(path);
  }

  async clickUserMenu(): Promise<void> {
    await this.userMenuBtn().click();
  }

  async clickLogout(): Promise<void> {
    await this.logoutMenuItem().click();
  }
}
