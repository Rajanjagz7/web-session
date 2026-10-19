import { test, expect } from '@playwright/test';
import { loginApi, json } from './api-helpers';

/**
 * Creates a small throwaway job via the API so this suite never has to
 * delete/restore a job someone else is using for other testing.
 */
async function createThrowawayJob(request: import('@playwright/test').APIRequestContext) {
  const installersRes = await request.get('/api/v1/installers?limit=50');
  const installers = (await json(installersRes))?.data?.installers ?? (await json(installersRes))?.data?.items ?? [];
  const rajan = installers.find((i: any) => i.companyName === 'Rajan Testing Company');
  if (!rajan) throw new Error('Could not find "Rajan Testing Company" via GET /installers to attach the throwaway job to.');

  const runId = Date.now().toString().slice(-8);
  const res = await request.post('/api/v1/jobs', {
    data: {
      installerId: rajan.id,
      activityType: 'heating_cooling',
      customerType: 'residential',
      customer: {
        name: `Soft Delete QA ${runId}`,
        email: `soft.delete.qa.${runId}@yopmail.com`,
        phoneNumber: `4${runId.slice(-8)}`,
      },
      ownReference: `REF-DEL-${runId}`,
    },
  });
  if (res.status() !== 201) {
    throw new Error(`Throwaway job creation failed: ${res.status()} ${await res.text()}`);
  }
  const body = await json(res);
  return { jobId: body.data.job.id as string, ownReference: `REF-DEL-${runId}` };
}

test.describe('Job soft-delete & restore', () => {
  test('full delete -> excluded from list -> 404 on direct access -> visible in trash -> restore -> reappears', async ({ request }) => {
    await loginApi(request);
    const { jobId, ownReference } = await createThrowawayJob(request);

    // Sanity: it's reachable before deleting.
    const beforeRes = await request.get(`/api/v1/jobs/${jobId}`);
    expect(beforeRes.status()).toBe(200);

    // Delete.
    const deleteRes = await request.delete('/api/v1/jobs', { data: { jobIds: [jobId] } });
    expect(deleteRes.status()).toBe(200);
    const deleteBody = await json(deleteRes);
    expect(deleteBody.data).toMatchObject({ deletedCount: 1, requested: 1, notFound: [] });

    // Excluded from the default (non-deleted) detail route.
    const afterDeleteRes = await request.get(`/api/v1/jobs/${jobId}`);
    expect(afterDeleteRes.status()).toBe(404);

    // Excluded from the default list too - searched by its own unique
    // reference rather than scanning a fixed page, since the total job
    // count keeps growing as the suite runs.
    const listRes = await request.get(`/api/v1/jobs?search=${encodeURIComponent(ownReference)}`);
    const listBody = await json(listRes);
    expect(listBody.data.jobs).toHaveLength(0);

    // Present in the staff trash view with the right flags.
    const trashRes = await request.get('/api/v1/jobs?deleted=true&limit=100');
    const trashBody = await json(trashRes);
    const trashedJob = trashBody.data.jobs.find((j: any) => j.id === jobId);
    expect(trashedJob).toBeTruthy();
    expect(trashedJob.isDeleted).toBe(true);
    expect(trashedJob.deletedAt).toBeTruthy();

    // Restore.
    const restoreRes = await request.post('/api/v1/jobs/restore', { data: { jobIds: [jobId] } });
    expect(restoreRes.status()).toBe(200);
    const restoreBody = await json(restoreRes);
    expect(restoreBody.data).toMatchObject({ restoredCount: 1, requested: 1, notFound: [] });

    // Reachable again, with data intact.
    const afterRestoreRes = await request.get(`/api/v1/jobs/${jobId}`);
    expect(afterRestoreRes.status()).toBe(200);
    const afterRestoreBody = await json(afterRestoreRes);
    expect(afterRestoreBody.data.job.id).toBe(jobId);
  });

  test('delete is idempotent - deleting an already-deleted job reports it correctly, not as an error', async ({ request }) => {
    await loginApi(request);
    const { jobId } = await createThrowawayJob(request);

    const firstDelete = await request.delete('/api/v1/jobs', { data: { jobIds: [jobId] } });
    expect(firstDelete.status()).toBe(200);

    const secondDelete = await request.delete('/api/v1/jobs', { data: { jobIds: [jobId] } });
    expect(secondDelete.status()).toBe(200);
    const body = await json(secondDelete);
    // Already-deleted ids are skipped, not reported as notFound or an error.
    expect(body.data.deletedCount).toBe(0);
    expect(body.data.notFound).toEqual([]);

    // Cleanup: restore so this job doesn't linger deleted.
    await request.post('/api/v1/jobs/restore', { data: { jobIds: [jobId] } });
  });

  test('deleting a nonexistent job id reports it in notFound', async ({ request }) => {
    await loginApi(request);
    const fakeId = '000000000000000000000000';
    const res = await request.delete('/api/v1/jobs', { data: { jobIds: [fakeId] } });
    expect(res.status()).toBe(200);
    const body = await json(res);
    expect(body.data.deletedCount).toBe(0);
    expect(body.data.notFound).toContain(fakeId);
  });
});
