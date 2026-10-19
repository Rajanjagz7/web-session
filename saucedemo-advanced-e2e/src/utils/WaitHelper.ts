import { Page } from '@playwright/test';

export class WaitHelper {
  constructor(private page: Page) {}

  async waitForCondition(
    condition: () => Promise<boolean>,
    timeout: number = 30_000,
    interval: number = 500,
  ): Promise<void> {
    const start = Date.now();
    while (Date.now() - start < timeout) {
      if (await condition()) return;
      await this.page.waitForTimeout(interval);
    }
    throw new Error(`Condition not met within ${timeout}ms`);
  }

  async retry<T>(fn: () => Promise<T>, retries: number = 3, delay: number = 1000): Promise<T> {
    let lastError: Error | undefined;
    for (let i = 0; i < retries; i++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error as Error;
        if (i < retries - 1) await this.page.waitForTimeout(delay);
      }
    }
    throw lastError!;
  }
}
