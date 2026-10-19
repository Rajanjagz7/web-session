import { type Locator } from '@playwright/test';
import { env } from '../config/env';
import { BasePage } from './BasePage';

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
    return this.inviteDialog.getByText('Your registration email');
  }
  get oldSignInEmailLabel(): Locator {
    return this.inviteDialog.getByText('Your sign-in email');
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
