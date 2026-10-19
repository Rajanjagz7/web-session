import { Page, expect } from '@playwright/test';
import { ResidentialCustomer, BusinessCustomer } from '../data/australian-data';

function normalizeAuPhone(phone: string): string {
  let digits = phone.replace(/\D/g, '');
  if (digits.startsWith('61')) {
    digits = digits.substring(2);
  }
  if (digits.startsWith('0')) {
    digits = digits.substring(1);
  }
  return digits;
}

export class AddJobModal {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async selectDropdownByLabel(labelText: string, optionText: string, searchInput = '') {
    const item = this.page.locator('.form-item').filter({ hasText: labelText }).first();
    const control = item.locator('.select__control');
    await control.scrollIntoViewIfNeeded();
    await expect(control).not.toHaveClass(/is-disabled/, { timeout: 10000 });
    await control.click();
    await this.page.waitForTimeout(300);

    if (searchInput) {
      const inp = item.locator('input.select__input');
      await inp.fill(searchInput);
      await this.page.waitForTimeout(400);
    }

    const opt = this.page.locator('[class*="-option"]:not(:has-text("Loading"))').filter({ hasText: optionText }).first();
    await opt.waitFor({ state: 'visible', timeout: 8000 });
    await opt.click();
    await this.page.waitForTimeout(300);
  }

  async open() {
    const addBtn = this.page.getByRole('button', { name: 'Add Job' });
    await addBtn.waitFor({ state: 'visible' });
    await addBtn.click();
    await this.page.waitForTimeout(1000);
    const actSelect = this.page.locator('.form-item').filter({ hasText: 'Activity Type' }).first();
    await expect(actSelect).toBeVisible({ timeout: 10000 });
  }

  private async selectEquipmentBrandModel(activityType: string) {
    const isHeatPump = activityType.toLowerCase().includes('heat pump');
    const eqName = isHeatPump ? 'Electric Hot Water Unit' : 'Installation of a New Air Conditioner';
    const brandName = isHeatPump ? 'AGM Energy' : 'ACTRON AIR';
    const modelName = isHeatPump ? 'AGMHP270W' : 'CAY500T - ELY500T';

    // 1. Original Equipment
    const eqItem = this.page.locator('.form-item').filter({ hasText: 'Original Equipment' }).first();
    await eqItem.waitFor({ state: 'visible', timeout: 5000 });
    const eqCtrl = eqItem.locator('.select__control');
    await eqCtrl.scrollIntoViewIfNeeded();
    await expect(eqCtrl).not.toHaveClass(/is-disabled/, { timeout: 10000 });
    await eqCtrl.click();
    await this.page.waitForTimeout(400);

    const preferredEq = this.page.locator('[class*="-option"]:not(:has-text("Loading"))').filter({ hasText: eqName }).first();
    if (await preferredEq.isVisible({ timeout: 2000 }).catch(() => false)) {
      await preferredEq.click();
    } else {
      await this.page.locator('[class*="-option"]:not(:has-text("Loading"))').first().click();
    }
    await this.page.waitForTimeout(500);

    // 2. Brand
    const brandItem = this.page.locator('.form-item').filter({ hasText: 'Brand' }).first();
    const brandCtrl = brandItem.locator('.select__control');
    await brandCtrl.scrollIntoViewIfNeeded();
    await expect(brandCtrl).not.toHaveClass(/is-disabled/, { timeout: 10000 });
    await brandCtrl.click();
    await this.page.waitForTimeout(400);

    const preferredBrand = this.page.locator('[class*="-option"]:not(:has-text("Loading"))').filter({ hasText: brandName }).first();
    if (await preferredBrand.isVisible({ timeout: 2000 }).catch(() => false)) {
      await preferredBrand.click();
    } else {
      await this.page.locator('[class*="-option"]:not(:has-text("Loading"))').first().click();
    }
    await this.page.waitForTimeout(500);

    // 3. Model
    const modelItem = this.page.locator('.form-item').filter({ hasText: 'Model' }).first();
    const modelCtrl = modelItem.locator('.select__control');
    await modelCtrl.scrollIntoViewIfNeeded();
    await expect(modelCtrl).not.toHaveClass(/is-disabled/, { timeout: 10000 });
    await modelCtrl.click();
    await this.page.waitForTimeout(400);

    const preferredModel = this.page.locator('[class*="-option"]:not(:has-text("Loading"))').filter({ hasText: modelName }).first();
    if (await preferredModel.isVisible({ timeout: 2000 }).catch(() => false)) {
      await preferredModel.click();
    } else {
      await this.page.locator('[class*="-option"]:not(:has-text("Loading"))').first().click();
    }
    await this.page.waitForTimeout(400);
  }

  async fillResidentialJob(config: {
    reference?: string;
    activityType: string;
    leadGen: string;
    buildingType: string;
    company: string;
    installerPerson?: string;
    customer: ResidentialCustomer;
    newSystem?: string;
  }) {
    // 1. Reference
    const ref = config.reference || `RJN-RES-${Date.now().toString().slice(-6)}`;
    await this.page.locator('input[name="ownReference"]').fill(ref);

    // 2. Activity Type
    await this.selectDropdownByLabel('Activity Type', config.activityType);

    // 3. Lead Gen
    await this.selectDropdownByLabel('Method of Lead Generation', config.leadGen);

    // 4. Building Type
    await this.selectDropdownByLabel('Building Type', config.buildingType.substring(0, 15));

    // 5. Company
    await this.selectDropdownByLabel('Installer', config.company, 'Rajan');

    // 6. Person
    const personItem = this.page.locator('.form-item').filter({ hasText: 'Attended' }).first();
    if (await personItem.isVisible({ timeout: 2000 }).catch(() => false)) {
      const control = personItem.locator('.select__control');
      await control.scrollIntoViewIfNeeded();
      await control.click();
      await this.page.waitForTimeout(300);
      if (config.installerPerson) {
        const opt = this.page.locator('[class*="-option"]:not(:has-text("Loading"))').filter({ hasText: config.installerPerson }).first();
        if (await opt.isVisible({ timeout: 1500 }).catch(() => false)) {
          await opt.click();
        } else {
          await this.page.locator('[class*="-option"]:not(:has-text("Loading"))').first().click();
        }
      } else {
        await this.page.locator('[class*="-option"]:not(:has-text("Loading"))').first().click();
      }
      await this.page.waitForTimeout(300);
    }

    // 7. Customer fields
    await this.page.locator('input[name="customerName"]').fill(config.customer.fullName);
    const cleanPhone = normalizeAuPhone(config.customer.phone);
    await this.page.locator('input[name="phone"]').fill(cleanPhone);
    const uniqueEmail = config.customer.email.includes('@')
      ? `${config.customer.email.split('@')[0]}.${Date.now()}@yopmail.com`
      : config.customer.email;
    await this.page.locator('input[name="email"]').fill(uniqueEmail);

    // 8. Manual Address Switcher
    const switcher = this.page.locator('.switcher-toggle');
    await switcher.scrollIntoViewIfNeeded();
    await switcher.click();
    await this.page.waitForTimeout(300);
    await this.page.locator('input[name="customerAddress"]').fill(`${config.customer.address.street}, ${config.customer.address.suburb} ${config.customer.address.state}`);
    await this.page.locator('input[name="postcode"]').fill(config.customer.address.postcode);

    // 9. Hot Water Heat Pump - New System (if visible)
    const newSysItem = this.page.locator('.form-item').filter({ hasText: 'New System' }).first();
    if (await newSysItem.isVisible({ timeout: 1000 }).catch(() => false)) {
      if (config.newSystem) {
        await this.selectDropdownByLabel('New System', config.newSystem);
      } else {
        const ctrl = newSysItem.locator('.select__control');
        await ctrl.scrollIntoViewIfNeeded();
        await ctrl.click();
        await this.page.waitForTimeout(300);
        await this.page.locator('[class*="-option"]:not(:has-text("Loading"))').first().click();
      }
      await this.page.waitForTimeout(500);
    }

    // 10. Equipment to Be Quoted: Original Equipment, Brand, Model
    await this.selectEquipmentBrandModel(config.activityType);

    return ref;
  }

  async fillBusinessJob(config: {
    reference?: string;
    activityType: string;
    leadGen: string;
    buildingType: string;
    company: string;
    installerPerson?: string;
    business: BusinessCustomer;
    newSystem?: string;
  }) {
    // 1. Reference
    const ref = config.reference || `RJN-BIZ-${Date.now().toString().slice(-6)}`;
    await this.page.locator('input[name="ownReference"]').fill(ref);

    // 2. Activity Type
    await this.selectDropdownByLabel('Activity Type', config.activityType);

    // 3. Lead Gen
    await this.selectDropdownByLabel('Method of Lead Generation', config.leadGen);

    // 4. Building Type
    await this.selectDropdownByLabel('Building Type', 'Small Business');

    // 5. Company
    await this.selectDropdownByLabel('Installer', config.company, 'Rajan');

    // 6. Person
    const personItem = this.page.locator('.form-item').filter({ hasText: 'Attended' }).first();
    if (await personItem.isVisible({ timeout: 2000 }).catch(() => false)) {
      const ctrl = personItem.locator('.select__control');
      await ctrl.scrollIntoViewIfNeeded();
      await ctrl.click();
      await this.page.waitForTimeout(300);
      if (config.installerPerson) {
        const opt = this.page.locator('[class*="-option"]:not(:has-text("Loading"))').filter({ hasText: config.installerPerson }).first();
        if (await opt.isVisible({ timeout: 1500 }).catch(() => false)) {
          await opt.click();
        } else {
          await this.page.locator('[class*="-option"]:not(:has-text("Loading"))').first().click();
        }
      } else {
        await this.page.locator('[class*="-option"]:not(:has-text("Loading"))').first().click();
      }
      await this.page.waitForTimeout(300);
    }

    // 7. Business fields
    await this.page.locator('input[name="businessName"]').fill(config.business.businessName);
    await this.page.locator('input[name="authFirstName"]').fill(config.business.signatoryFirstName);
    await this.page.locator('input[name="authLastName"]').fill(config.business.signatoryLastName);
    await this.page.locator('input[name="authSignPosition"]').fill(config.business.signatoryPosition);
    const cleanPhone = normalizeAuPhone(config.business.phone);
    await this.page.locator('input[name="authPhoneNumber"]').fill(cleanPhone);
    const uniqueEmail = config.business.email.includes('@')
      ? `${config.business.email.split('@')[0]}.${Date.now()}@yopmail.com`
      : config.business.email;
    await this.page.locator('input[name="authEmail"]').fill(uniqueEmail);
    await this.page.locator('input[name="abnAcn"]').fill(config.business.abn);

    // 8. Manual Address Switcher
    const switcher = this.page.locator('.switcher-toggle');
    await switcher.scrollIntoViewIfNeeded();
    await switcher.click();
    await this.page.waitForTimeout(300);
    await this.page.locator('input[name="customerAddress"]').fill(`${config.business.address.street}, ${config.business.address.suburb} ${config.business.address.state}`);
    await this.page.locator('input[name="postcode"]').fill(config.business.address.postcode);

    // 9. Hot Water Heat Pump - New System if applicable
    const newSysItem = this.page.locator('.form-item').filter({ hasText: 'New System' }).first();
    if (await newSysItem.isVisible({ timeout: 1000 }).catch(() => false)) {
      if (config.newSystem) {
        await this.selectDropdownByLabel('New System', config.newSystem);
      } else {
        const ctrl = newSysItem.locator('.select__control');
        await ctrl.scrollIntoViewIfNeeded();
        await ctrl.click();
        await this.page.waitForTimeout(300);
        await this.page.locator('[class*="-option"]:not(:has-text("Loading"))').first().click();
      }
      await this.page.waitForTimeout(500);
    }

    // 10. Equipment to Be Quoted: Original Equipment, Brand, Model
    await this.selectEquipmentBrandModel(config.activityType);

    return ref;
  }

  async submitAndExpectSuccess(): Promise<string> {
    const [response] = await Promise.all([
      this.page.waitForResponse(
        res => res.url().includes('/api/v1/jobs') && res.request().method() === 'POST',
        { timeout: 25000 }
      ),
      this.page.locator('#submitButton').click()
    ]);

    expect(response.status()).toBe(201);
    const json = await response.json();
    const jobId = json?.data?.job?.jobNumber || json?.data?.jobId || json?.jobId || '';
    await this.page.waitForTimeout(2000);
    return jobId;
  }
}
