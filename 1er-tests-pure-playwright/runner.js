// Minimal test harness for pure Playwright (no @playwright/test). Collects
// tests via describe()/test(), then run.js executes them sequentially,
// each in its own fresh browser context.

const tests = [];
let suiteStack = [];

function describe(name, fn) {
  suiteStack.push(name);
  fn();
  suiteStack.pop();
}

function test(name, fn) {
  const fullName = [...suiteStack, name].join(' > ');
  tests.push({ name: fullName, fn });
}

class AssertionError extends Error {}

function expect(actual) {
  return {
    toBe(expected) {
      if (actual !== expected) {
        throw new AssertionError(`Expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
      }
    },
    toEqual(expected) {
      if (JSON.stringify(actual) !== JSON.stringify(expected)) {
        throw new AssertionError(`Expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
      }
    },
    toContain(expected) {
      if (!actual.includes(expected)) {
        throw new AssertionError(`Expected "${actual}" to contain "${expected}"`);
      }
    },
    toMatchObject(expected) {
      for (const key of Object.keys(expected)) {
        if (JSON.stringify(actual[key]) !== JSON.stringify(expected[key])) {
          throw new AssertionError(`Expected key "${key}" to be ${JSON.stringify(expected[key])}, got ${JSON.stringify(actual?.[key])}`);
        }
      }
    },
    toHaveLength(n) {
      if (actual.length !== n) {
        throw new AssertionError(`Expected length ${n}, got ${actual.length}`);
      }
    },
    toBeTruthy() {
      if (!actual) throw new AssertionError(`Expected a truthy value, got ${JSON.stringify(actual)}`);
    },
  };
}

async function expectVisible(locator, timeout = 10000) {
  await locator.waitFor({ state: 'visible', timeout });
}

async function expectNotVisible(locator, timeout = 5000) {
  const visible = await locator.isVisible().catch(() => false);
  if (visible) throw new AssertionError('Expected element NOT to be visible, but it was.');
}

async function expectHaveCount(locator, count, timeout = 8000) {
  const start = Date.now();
  let actual;
  do {
    actual = await locator.count();
    if (actual === count) return;
    await new Promise((r) => setTimeout(r, 200));
  } while (Date.now() - start < timeout);
  throw new AssertionError(`Expected count ${count}, got ${actual}`);
}

async function expectHaveValue(locator, value) {
  const actual = await locator.inputValue();
  if (actual !== value) throw new AssertionError(`Expected value "${value}", got "${actual}"`);
}

function expectUrlMatches(page, pattern) {
  const url = page.url();
  if (!pattern.test(url)) throw new AssertionError(`Expected URL to match ${pattern}, got ${url}`);
}

module.exports = {
  describe,
  test,
  tests,
  expect,
  expectVisible,
  expectNotVisible,
  expectHaveCount,
  expectHaveValue,
  expectUrlMatches,
};
