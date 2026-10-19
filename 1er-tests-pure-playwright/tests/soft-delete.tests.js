const { describe, test, expect } = require('../runner');
const { loginApi, json } = require('../api-helpers');

async function createThrowawayJob(request) {
  const installersRes = await request.get('/api/v1/installers?limit=50');
  const installersBody = (await json(installersRes)) || {};
  const installers = installersBody?.data?.installers ?? installersBody?.data?.items ?? [];
  const rajan = installers.find((i) => i.companyName === 'Rajan Testing Company');
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
  return { jobId: body.data.job.id, ownReference: `REF-DEL-${runId}` };
}

describe('Job soft-delete & restore', () => {
  test('full delete -> excluded from list -> 404 on direct access -> visible in trash -> restore -> reappears', async ({ request }) => {
    await loginApi(request);
    const { jobId, ownReference } = await createThrowawayJob(request);

    const beforeRes = await request.get(`/api/v1/jobs/${jobId}`);
    expect(beforeRes.status()).toBe(200);

    const deleteRes = await request.delete('/api/v1/jobs', { data: { jobIds: [jobId] } });
    expect(deleteRes.status()).toBe(200);
    const deleteBody = await json(deleteRes);
    expect(deleteBody.data).toMatchObject({ deletedCount: 1, requested: 1, notFound: [] });

    const afterDeleteRes = await request.get(`/api/v1/jobs/${jobId}`);
    expect(afterDeleteRes.status()).toBe(404);

    const listRes = await request.get(`/api/v1/jobs?search=${encodeURIComponent(ownReference)}`);
    const listBody = await json(listRes);
    expect(listBody.data.jobs).toHaveLength(0);

    const trashRes = await request.get('/api/v1/jobs?deleted=true&limit=100');
    const trashBody = await json(trashRes);
    const trashedJob = trashBody.data.jobs.find((j) => j.id === jobId);
    expect(trashedJob).toBeTruthy();
    expect(trashedJob.isDeleted).toBe(true);
    expect(trashedJob.deletedAt).toBeTruthy();

    const restoreRes = await request.post('/api/v1/jobs/restore', { data: { jobIds: [jobId] } });
    expect(restoreRes.status()).toBe(200);
    const restoreBody = await json(restoreRes);
    expect(restoreBody.data).toMatchObject({ restoredCount: 1, requested: 1, notFound: [] });

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
    expect(body.data.deletedCount).toBe(0);
    expect(body.data.notFound).toEqual([]);

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
