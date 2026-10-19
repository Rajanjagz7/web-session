import { test as base, expect, type APIRequestContext, type Browser, type BrowserContext, type Page } from '@playwright/test';
import { NOTE_BY_ID, type Kind, type Note, type Persona } from '../notes';
import { ApiClient } from './api';

export { expect };

export type Uniq = (prefix: string) => string;

export interface Fx {
  readonly page: Page;
  readonly request: APIRequestContext;
  readonly api: ApiClient;
  readonly uniq: Uniq;
  readonly browser: Browser;
  readonly context: BrowserContext;
}

let counter = 0;

export const test = base.extend<{ api: ApiClient; uniq: Uniq }>({
  api: async ({}, use) => {
    const api = await ApiClient.create();
    await use(api);
    await api.dispose();
  },
  // Unique names per run, so tests never collide and leftovers are easy to spot.
  uniq: async ({}, use, testInfo) => {
    const run = `${Date.now().toString(36)}${testInfo.workerIndex}`;
    await use((prefix: string) => `${prefix}-${run}-${++counter}`);
  },
});

function note(id: string, kind: Kind): Note {
  const n = NOTE_BY_ID.get(id);
  if (!n) throw new Error(`Unknown release-note id ${id}: add it to src/notes.ts first`);
  if (n.kind !== kind) throw new Error(`${id} is declared "${n.kind}" in src/notes.ts but registered as "${kind}"`);
  return n;
}

const title = (n: Note, persona: Persona, text: string): string => `[${n.id}] @${n.area} @${persona} ${text}`;

/** A live test. The persona comes from notes.ts unless `as` registers an extra persona run (permission checks). */
export function live(id: string, text: string, body: (fx: Fx) => Promise<void>, as?: Persona): void {
  const n = note(id, 'live');
  const persona = as ?? n.persona;
  test(title(n, persona, text), async ({ page, request, api, uniq, browser, context }) => {
    await body({ page, request, api, uniq, browser, context });
  });
}

/** A test that cannot run yet because a prerequisite is missing. The reason is the one recorded in notes.ts. */
export function fixme(id: string): void {
  const n = note(id, 'fixme');
  test(title(n, n.persona, n.text), async () => {
    test.fixme(true, `reason: ${n.reason ?? 'prerequisite missing'}`);
  });
}

/** MANUAL: App Store / mobile, real payments, or a wall-clock moment. */
export function manual(id: string): void {
  const n = note(id, 'manual');
  test(title(n, n.persona, `MANUAL ${n.text}`), async () => {
    test.fixme(true, `reason: MANUAL - ${n.reason ?? 'needs a manual run'}`);
  });
}

/** Call at the top of a test whose expected value is not in the release notes. */
export function needs(value: string, envName: string): void {
  test.fixme(value === '', `reason: expected value not configured; set ${envName} in .env (one-line fill)`);
}
