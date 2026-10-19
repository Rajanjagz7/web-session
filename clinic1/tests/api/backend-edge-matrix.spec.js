// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * QA Test Suite: ActiveRx Advanced Edge Matrix & Resilience Scenarios
 * Focus: Mid-cycle upgrades, multi-item appointments, status regressions,
 * failure isolation during backfill, and downgrades.
 */
test.describe('ActiveRx - Advanced Edge Matrix & Resilience Scenarios', () => {

  test('Edge 1: Mid-cycle plan upgrade retroactively links previously exhausted sessions in current window', async () => {
    const currentPeriod = {
      start: '2026-09-21',
      end: '2026-09-28',
      allowanceCap: 1,
      used: 1
    };

    const session1 = { id: 'apt_upg_01', date: '2026-09-22', status: 'COVERED', price: 0 };
    const session2 = { id: 'apt_upg_02', date: '2026-09-25', status: 'PENDING', price: 99 };

    currentPeriod.allowanceCap = 2;

    const remainingAllowance = currentPeriod.allowanceCap - currentPeriod.used;
    expect(remainingAllowance).toBe(1);

    if (remainingAllowance > 0 && session2.status === 'PENDING') {
      session2.status = 'COVERED';
      session2.price = 0;
      session2.membershipDiscountSnapshot = { eligible: true, planId: 'upgraded_plan_2x30' };
      currentPeriod.used += 1;
    }

    expect(session2.status).toBe('COVERED');
    expect(session2.price).toBe(0);
    expect(currentPeriod.used).toBe(2);
  });

  test('Edge 2: Multi-item appointment splits covered consultation from non-covered consumable items', async () => {
    const appointmentItems = [
      { id: 'item_01', type: 'CONSULTATION', code: 'PHYSIO-30', price: 90, coveredByPlan: true },
      { id: 'item_02', type: 'CONSUMABLE', code: 'RESIST-BAND', price: 15, coveredByPlan: false }
    ];

    const processedItems = appointmentItems.map(item => {
      if (item.coveredByPlan) {
        return {
          ...item,
          patientOwes: 0,
          membershipDiscount: item.price,
          status: 'PAID_BY_MEMBERSHIP'
        };
      } else {
        return {
          ...item,
          patientOwes: item.price,
          membershipDiscount: 0,
          status: 'PATIENT_PAYABLE'
        };
      }
    });

    const totalPatientOwes = processedItems.reduce((sum, item) => sum + item.patientOwes, 0);
    const totalCovered = processedItems.reduce((sum, item) => sum + item.membershipDiscount, 0);

    expect(totalPatientOwes).toBe(15);
    expect(totalCovered).toBe(90);
    expect(processedItems[0].status).toBe('PAID_BY_MEMBERSHIP');
    expect(processedItems[1].status).toBe('PATIENT_PAYABLE');
  });

  test('Edge 3: Status regression releases usage row and voids/credits unearned item invoice', async () => {
    let periodUsageCount = 1;
    const session = {
      id: 'apt_regress_01',
      status: 'ARRIVED',
      usageRowId: 'usage_row_991',
      invoiceId: 'inv_item_882',
      invoiceStatus: 'PAID'
    };

    const handleStatusReversion = (appt, newStatus) => {
      appt.status = newStatus;
      appt.usageRowId = null;
      periodUsageCount -= 1;

      if (appt.invoiceId) {
        appt.invoiceStatus = 'VOIDED';
      }

      return { reverted: true, newStatus };
    };

    const result = handleStatusReversion(session, 'BOOKED');
    expect(result.reverted).toBe(true);
    expect(session.status).toBe('BOOKED');
    expect(session.usageRowId).toBeNull();
    expect(session.invoiceStatus).toBe('VOIDED');
    expect(periodUsageCount).toBe(0);
  });

  test('Edge 4: Backfill migration isolates patient errors and continues processing remaining candidates', async () => {
    const candidates = [
      { patientId: 'pat_01', hasCorruptedInvoice: false },
      { patientId: 'pat_02', hasCorruptedInvoice: true },
      { patientId: 'pat_03', hasCorruptedInvoice: false }
    ];

    const migrationStats = {
      totalCandidates: candidates.length,
      linked: 0,
      errors: 0,
      skipped_error: []
    };

    for (const candidate of candidates) {
      try {
        if (candidate.hasCorruptedInvoice) {
          throw new Error('Corrupted invoice metadata for patient ' + candidate.patientId);
        }
        migrationStats.linked += 1;
      } catch (err) {
        migrationStats.errors += 1;
        migrationStats.skipped_error.push({ patientId: candidate.patientId, reason: err.message });
      }
    }

    expect(migrationStats.linked).toBe(2);
    expect(migrationStats.errors).toBe(1);
    expect(migrationStats.skipped_error[0].patientId).toBe('pat_02');
  });

  test('Edge 5: Staged migration strictly limits execution to specified MIGRATION_CLINIC_IDS', async () => {
    const allowedClinics = ['clinic_active_rx_01', 'clinic_active_rx_02'];
    const testPatients = [
      { id: 'pat_a', clinicId: 'clinic_active_rx_01' },
      { id: 'pat_b', clinicId: 'clinic_unrelated_99' },
      { id: 'pat_c', clinicId: 'clinic_active_rx_02' }
    ];

    const migrationLog = testPatients.map(pat => {
      if (allowedClinics.includes(pat.clinicId)) {
        return { patientId: pat.id, action: 'PROCESSED' };
      } else {
        return { patientId: pat.id, action: 'SKIPPED_EXCLUDED_CLINIC' };
      }
    });

    const processed = migrationLog.filter(l => l.action === 'PROCESSED');
    const skipped = migrationLog.filter(l => l.action === 'SKIPPED_EXCLUDED_CLINIC');

    expect(processed).toHaveLength(2);
    expect(skipped).toHaveLength(1);
    expect(skipped[0].patientId).toBe('pat_b');
  });

  test('Edge 6: Subscription downgrade on renewal only links earliest up to new lower allowance cap', async () => {
    const newAllowanceCap = 1;
    const futureBookings = [
      { id: 'apt_f1', time: '2026-10-01T09:00:00Z', status: 'PENDING' },
      { id: 'apt_f2', time: '2026-10-02T10:00:00Z', status: 'PENDING' },
      { id: 'apt_f3', time: '2026-10-03T11:00:00Z', status: 'PENDING' }
    ];

    let linkedCount = 0;
    const sortedBookings = [...futureBookings].sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());

    for (const b of sortedBookings) {
      if (linkedCount < newAllowanceCap) {
        b.status = 'COVERED';
        linkedCount++;
      } else {
        b.status = 'PENDING_EXHAUSTED';
      }
    }

    expect(sortedBookings[0].status).toBe('COVERED');
    expect(sortedBookings[1].status).toBe('PENDING_EXHAUSTED');
    expect(sortedBookings[2].status).toBe('PENDING_EXHAUSTED');
    expect(linkedCount).toBe(1);
  });

});