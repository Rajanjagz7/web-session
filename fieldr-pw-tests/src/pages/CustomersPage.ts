import { type Locator } from '@playwright/test';
import { env } from '../lib/env';
import { BasePage } from './BasePage';

export class CustomersPage extends BasePage {
  async openList(): Promise<void> {
    await this.open(env.routes.customers);
  }
  async openDetails(customerId: string): Promise<void> {
    await this.open(`${env.routes.customers}/${encodeURIComponent(customerId)}`); // TODO(confirm): route shape
  }

  get searchBox(): Locator {
    return this.page.getByRole('searchbox'); // TODO(confirm): may be a textbox named Search
  }
  get rows(): Locator {
    return this.page.getByRole('row');
  }
  row(text: string | RegExp): Locator {
    return this.page.getByRole('row', { name: text });
  }

  /** CUS-01 / CUS-02 / JOB-04 */
  get createJobButton(): Locator {
    return this.page.getByRole('button', { name: 'Create Job' });
  }

  /** CUS-03e : portal access screen */
  get portalAccessSection(): Locator {
    return this.page.getByRole('region', { name: /portal access/i }); // TODO(confirm)
  }

  /** SEC-05 / SEC-06 */
  get companyNameInput(): Locator {
    return this.page.getByLabel(/company name/i);
  }
  get saveButton(): Locator {
    return this.page.getByRole('button', { name: /save/i });
  }
}


/** Invitations tab of the Customer section (INV-*, SEC-01/02, BUG-09*). */
export class InvitesPage extends BasePage {
  async openInvites(): Promise<void> {
    await this.open(env.routes.invites);
  }

  get inviteButton(): Locator {
    return this.page.getByRole('button', { name: /invite/i }); // TODO(confirm)
  }
  get inviteDialog(): Locator {
    return this.dialog(/invite/i);
  }
  get searchBox(): Locator {
    return this.page.getByRole('searchbox'); // TODO(confirm)
  }
  /** INV-05. TODO(confirm): the "waiting" count element; ask dev for a test-id. */
  get waitingCount(): Locator {
    return this.page.getByTestId('invites-waiting-count');
  }
  get rows(): Locator {
    return this.page.getByRole('row');
  }

  // ---- INV-01: customer invite details step
  field(label: string | RegExp): Locator {
    return this.inviteDialog.getByLabel(label);
  }
  get companyName(): Locator {
    return this.field(/company name/i);
  }
  get address(): Locator {
    return this.field(/address/i);
  }
  get notes(): Locator {
    return this.field(/notes/i);
  }
  get dateOfBirth(): Locator {
    return this.field(/date of birth/i);
  }
  get licences(): Locator {
    return this.field(/licen[cs]e/i);
  }
  /** INV-04 */
  get registrationEmailLabel(): Locator {
    return this.inviteDialog.getByLabel('Your registration email'); // TODO: confirm it is a form label
  }
  get oldSignInEmailLabel(): Locator {
    return this.inviteDialog.getByLabel('Your sign-in email'); // TODO: confirm it is a form label
  }
  get submit(): Locator {
    return this.inviteDialog.getByRole('button', { name: /submit|accept|continue|send/i }); // TODO(confirm)
  }

  // ---- row actions (SEC-01 / SEC-02)
  rowAction(row: string | RegExp, action: 'View' | 'Resend' | 'Cancel'): Locator {
    return this.page.getByRole('row', { name: row }).getByRole('button', { name: action });
  }
  get sendInviteButton(): Locator {
    return this.page.getByRole('button', { name: /send invite/i });
  }
  get emailInput(): Locator {
    return this.page.getByLabel(/email/i);
  }
}
