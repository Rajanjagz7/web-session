import { request as pwRequest, type APIRequestContext, type APIResponse } from '@playwright/test';
import { env, fill } from '../config/env';
import { KEY } from '../config/payloads';

export interface SeededCustomer {
  readonly id: string;
  readonly company: string | undefined;
  readonly contact: string;
  readonly email: string;
}
export interface SeedLine {
  readonly name: string;
  readonly quantity: number;
  readonly sellPrice: number;
  /** undefined = a line with no cost price (QUO-03). */
  readonly costPrice?: number;
}

type Json = Record<string, unknown>;

/** Pulls an id out of a create response. TODO(confirm): the real response envelope; adjust here only. */
export function idOf(body: unknown, what: string): string {
  const b = body as { id?: unknown; _id?: unknown; data?: { id?: unknown; _id?: unknown } } | null;
  const id = b?.id ?? b?._id ?? b?.data?.id ?? b?.data?._id;
  if (typeof id !== 'string' || id === '') throw new Error(`Could not read an id from the ${what} response: ${JSON.stringify(body)?.slice(0, 200)}`);
  return id;
}

/**
 * Seeds entities through the API with a service token (never through long UI flows).
 * Everything created is deleted in dispose(). Delete paths are TODO(confirm); a failed delete is reported, not hidden.
 */
export class ApiClient {
  private readonly cleanups: Array<{ label: string; run: () => Promise<APIResponse> }> = [];

  private constructor(private readonly ctx: APIRequestContext) {}

  static async create(): Promise<ApiClient> {
    const ctx = await pwRequest.newContext({
      baseURL: env.apiUrl,
      // TODO(confirm): the auth scheme for the service token (Bearer assumed).
      extraHTTPHeaders: env.serviceToken ? { Authorization: `Bearer ${env.serviceToken}` } : {},
    });
    return new ApiClient(ctx);
  }

  private requireToken(): void {
    if (!env.serviceToken) throw new Error('SERVICE_TOKEN is not set in .env: API seeding is unavailable (see README).');
  }

  async post(path: string, data: Json): Promise<APIResponse> {
    this.requireToken();
    return this.ctx.post(path, { data });
  }

  async get(path: string): Promise<APIResponse> {
    this.requireToken();
    return this.ctx.get(path);
  }

  async put(path: string, data: Json): Promise<APIResponse> {
    this.requireToken();
    return this.ctx.put(path, { data });
  }

  async delete(path: string): Promise<APIResponse> {
    this.requireToken();
    return this.ctx.delete(path);
  }

  async createCustomer(opts: { company?: string; contact: string; email: string; mobile?: string; active?: boolean }): Promise<SeededCustomer> {
    const k = KEY.customer;
    const data: Json = { [k.contactName]: opts.contact, [k.email]: opts.email, [k.isActive]: opts.active ?? true };
    if (opts.company !== undefined) data[k.company] = opts.company;
    if (opts.mobile !== undefined) data[k.mobile] = opts.mobile;
    const res = await this.post(env.api.customers, data);
    if (!res.ok()) throw new Error(`Seeding a customer failed with ${res.status()}: ${(await res.text()).slice(0, 200)}`);
    const id = idOf(await res.json(), 'customer');
    this.cleanups.push({ label: `customer ${id}`, run: () => this.ctx.delete(fill(env.api.customer, id)) });
    return { id, company: opts.company, contact: opts.contact, email: opts.email };
  }

  async createQuote(customerId: string, title: string, lines: readonly SeedLine[]): Promise<string> {
    const q = KEY.quote;
    const data: Json = {
      [q.customerId]: customerId,
      [q.title]: title,
      [q.lines]: lines.map((l) => ({
        [q.lineName]: l.name,
        [q.lineQty]: l.quantity,
        [q.lineSell]: l.sellPrice,
        ...(l.costPrice === undefined ? {} : { [q.lineCost]: l.costPrice }),
      })),
    };
    const res = await this.post(env.api.quotes, data);
    if (!res.ok()) throw new Error(`Seeding a quote failed with ${res.status()}: ${(await res.text()).slice(0, 200)}`);
    return idOf(await res.json(), 'quote');
  }

  async createJob(customerId: string, name: string, extra: Json = {}): Promise<string> {
    const j = KEY.job;
    const res = await this.post(env.api.jobs, { [j.customerId]: customerId, [j.name]: name, ...extra });
    if (!res.ok()) throw new Error(`Seeding a job failed with ${res.status()}: ${(await res.text()).slice(0, 200)}`);
    const id = idOf(await res.json(), 'job');
    this.cleanups.push({ label: `job ${id}`, run: () => this.ctx.delete(fill(env.api.job, id)) });
    return id;
  }

  async createRole(name: string): Promise<string> {
    const res = await this.post(env.api.roles, { [KEY.role.name]: name });
    if (!res.ok()) throw new Error(`Seeding a role failed with ${res.status()}: ${(await res.text()).slice(0, 200)}`);
    return idOf(await res.json(), 'role');
  }

  async createInvite(kind: 'staff' | 'customer', email: string): Promise<{ id: string; link: string | undefined }> {
    const res = await this.post(env.api.invites, { [KEY.invite.kind]: kind, [KEY.invite.email]: email });
    if (!res.ok()) throw new Error(`Seeding an invite failed with ${res.status()}: ${(await res.text()).slice(0, 200)}`);
    const body = (await res.json()) as Json & { data?: Json };
    const id = idOf(body, 'invite');
    const link = (body[KEY.invite.link] ?? body.data?.[KEY.invite.link]) as string | undefined;
    this.cleanups.push({ label: `invite ${id}`, run: () => this.ctx.delete(fill(env.api.invite, id)) });
    return { id, link };
  }

  async createUser(opts: { firstName: string; lastName: string; email: string; mobile?: string }): Promise<string> {
    const k = KEY.user;
    const data: Json = { [k.firstName]: opts.firstName, [k.lastName]: opts.lastName, [k.email]: opts.email };
    if (opts.mobile !== undefined) data[k.mobile] = opts.mobile;
    const res = await this.post(env.api.users, data);
    if (!res.ok()) throw new Error(`Seeding a user failed with ${res.status()}: ${(await res.text()).slice(0, 200)}`);
    const id = idOf(await res.json(), 'user');
    this.cleanups.push({ label: `user ${id}`, run: () => this.ctx.delete(fill(env.api.user, id)) });
    return id;
  }

  async deleteCustomer(id: string): Promise<APIResponse> {
    return this.ctx.delete(fill(env.api.customer, id));
  }

  async dispose(): Promise<void> {
    const failures: string[] = [];
    for (const c of this.cleanups.reverse()) {
      try {
        const r = await c.run();
        if (!r.ok() && r.status() !== 404) failures.push(`${c.label}: ${r.status()}`);
      } catch (e) {
        failures.push(`${c.label}: ${String(e)}`);
      }
    }
    await this.ctx.dispose();
    if (failures.length) console.warn(`[cleanup] could not delete: ${failures.join('; ')}`);
  }
}
