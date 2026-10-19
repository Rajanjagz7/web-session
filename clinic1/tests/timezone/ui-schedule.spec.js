// @ts-check
const { test, expect } = require('@playwright/test');
const path = require('path');
test.use({ storageState: path.join(__dirname, '../../playwright/.auth/tz-user.json'), viewport: { width: 1440, height: 900 } });

const O = 'https://sunrise-family-medical.dev.clinic1.ai';
const LOCS = [['Sydney Wellness Clinic', 'Sydney Wellness'], ['Harbour Health Clinic', 'Harbour Health'], ['BRISBANE HEALTH CLINIC', 'BRISBANE']];

async function pickLocation(page, label) {
  await page.locator('text=Location').first().waitFor();
  await page.getByRole('combobox').first().click().catch(() => {});
  await page.getByText(label, { exact: false }).first().click({ timeout: 8000 }).catch(() => {});
}
const to12 = t => { let [h, m] = t.split(':').map(Number); const ap = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12; return `${h}${m ? ':' + String(m).padStart(2, '0') : ''} ${ap}`; };

for (const [name, key] of LOCS) {
  test.describe(name, () => {
    test(`UI: Schedule > Settings month view renders hours and no JS/network errors`, async ({ page }) => {
      const errors = [], failed = [];
      page.on('pageerror', e => errors.push(e.message));
      page.on('console', m => { if (m.type() === 'error') errors.push(m.text().slice(0, 160)); });
      page.on('response', r => { if (/\/api\/v1\//.test(r.url()) && r.status() >= 400 && r.request().method() !== 'OPTIONS') failed.push(`${r.status()} ${r.url().replace(/https:\/\/[^/]+/, '').slice(0, 110)}`); });
      let locApi;
      page.on('response', async r => { if (/clinic\/location\?/.test(r.url()) && !locApi) locApi = await r.json().catch(() => null); });
      await page.goto(O + '/schedule/settings');
      await page.waitForTimeout(4000);
      await pickLocation(page, key);
      await page.waitForTimeout(4000);
      const body = await page.locator('body').innerText();
      await page.screenshot({ path: `test-results/walk/ui-${key.replace(/\W/g, '_')}.png` });
      expect(body).toMatch(/\d{1,2}(:\d\d)? (AM|PM) - \d{1,2}(:\d\d)? (AM|PM)|No schedule|Add Override/);
      const l = locApi?.response?.clinicLocations?.find(x => x.name === name);
      if (l) {
        const mon = l.scheduleDetails.days.find(d => d.dayIndex === 1)?.slots?.[0];
        test.info().annotations.push({ type: 'clinic-hours-Mon', description: mon ? `${to12(mon.startTime)} - ${to12(mon.endTime)}` : 'n/a' });
      }
      expect(errors.filter(e => !/favicon|ResizeObserver|socket|Download the React/i.test(e)), 'console/page errors').toEqual([]);
      expect(failed.filter(f => !/socket|ai-preferences|sticky|notifications/.test(f)), 'failed API calls').toEqual([]);
    });
  });
}

test('UI: page load shows no raw timezone strings / NaN / Invalid Date on schedule screens', async ({ page }) => {
  for (const p of ['/schedule', '/schedule/settings', '/classes', '/room-booking', '/dashboard']) {
    await page.goto(O + p); await page.waitForTimeout(4500);
    const t = await page.locator('body').innerText();
    expect(t, p).not.toMatch(/Invalid Date|NaN|undefined|\[object Object\]/);
  }
});

test('UI: time-of-day labels are well-formed (no 24h/12h mix, no 0 AM / 13 PM)', async ({ page }) => {
  await page.goto(O + '/schedule/settings'); await page.waitForTimeout(5000);
  const t = await page.locator('body').innerText();
  expect(t).not.toMatch(/\b(0|13|14|15|16|17|18|19|20|21|22|23|24) (AM|PM)\b/);
});
