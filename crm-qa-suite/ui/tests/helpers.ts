import { APIRequestContext, Page, expect } from '@playwright/test';

export const PROJECT = process.env.CRM_PROJECT_ID ?? '';
export const pipelinesUrl = `/projects/${PROJECT}/pipelines`;

const apiHeaders = () => ({
  accept: 'application/json',
  'crm-org-id': process.env.CRM_ORG_ID ?? 'default',
  'crm-project-id': PROJECT,
  'crm-env-mode': process.env.CRM_ENV_MODE ?? 'live',
});

/** Delete every pipeline whose name starts with the given prefix (test hygiene). */
export async function deletePipelinesByPrefix(request: APIRequestContext, prefix: string) {
  const r = await request.get('/api/crm/v1/pipelines?limit=100&include_archived=true', { headers: apiHeaders() });
  const list = (await r.json()).data as { id: string; name: string }[];
  for (const p of list.filter((x) => x.name.startsWith(prefix))) {
    await request.delete(`/api/crm/v1/pipelines/${p.id}`, { headers: apiHeaders() });
  }
}

export async function countPipelines(request: APIRequestContext, name: string) {
  const r = await request.get('/api/crm/v1/pipelines?limit=100&include_archived=true', { headers: apiHeaders() });
  return ((await r.json()).data as { name: string }[]).filter((p) => p.name === name).length;
}

export async function openNewPipelineDialog(page: Page) {
  await page.goto(pipelinesUrl);
  // An empty project also shows an empty-state "New pipeline" button, so take the header one.
  await page.getByRole('button', { name: 'New pipeline' }).first().click();
  const dialog = page.getByRole('dialog', { name: 'New pipeline' });
  await expect(dialog).toBeVisible();
  return dialog;
}
