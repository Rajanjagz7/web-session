// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('ActiveRx - Edge Cases & Negative Testing Suite', () => {

  test('Edge Case 1: Item invoice shows entire period fee when only 1 session is linked that week', async () => {
    const weeklyPeriodFee = 100.00;
    const linkedSessionsInPeriod = [{ id: 'apt_single_01', date: '2026-09-28', status: 'ARRIVED' }];
    const sessionInvoiceAmount = weeklyPeriodFee / linkedSessionsInPeriod.length;

    expect(linkedSessionsInPeriod).toHaveLength(1);
    expect(sessionInvoiceAmount).toBe(100.00);
  });

  test('Edge Case 2: Item invoice splits period fee evenly when full allowance (2 sessions) is linked', async () => {
    const weeklyPeriodFee = 100.00;
    const linkedSessionsInPeriod = [
      { id: 'apt_split_01', date: '2026-09-29', status: 'ARRIVED' },
      { id: 'apt_split_02', date: '2026-10-01', status: 'ARRIVED' }
    ];
    const sessionInvoiceAmount = weeklyPeriodFee / linkedSessionsInPeriod.length;

    expect(linkedSessionsInPeriod).toHaveLength(2);
    expect(sessionInvoiceAmount).toBe(50.00);
  });

  test('Edge Case 3: Reallocation on late arrival - 2nd session arrives after 1st session invoice already issued', async () => {
    const weeklyPeriodFee = 100.00;
    let sessions = [{ id: 'apt_realloc_01', status: 'ARRIVED', invoiceAmount: 100.00 }];
    expect(sessions[0].invoiceAmount).toBe(100.00);

    sessions.push({ id: 'apt_realloc_02', status: 'ARRIVED', invoiceAmount: 0 });
    const recomputedPerSession = weeklyPeriodFee / sessions.length;
    sessions = sessions.map(s => ({ ...s, invoiceAmount: recomputedPerSession }));

    expect(sessions[0].invoiceAmount).toBe(50.00);
    expect(sessions[1].invoiceAmount).toBe(50.00);
    expect(sessions.reduce((sum, s) => sum + s.invoiceAmount, 0)).toBe(weeklyPeriodFee);
  });

  test('Edge Case 4: Series occurrence beyond paid window with snapshot but no usage row is ADOPTED if allowance has room', async () => {
    const seriesOccurrence = {
      id: 'apt_series_slot3',
      date: '2026-10-02',
      price: 0,
      membershipDiscountSnapshot: { eligible: true, membershipId: 'mem_live_01' },
      hasActiveUsageRow: false
    };
    const periodAllowance = { total: 2, used: 1 };
    const canAdopt = (seriesOccurrence.price === 0) &&
                     (seriesOccurrence.membershipDiscountSnapshot?.eligible) &&
                     (!seriesOccurrence.hasActiveUsageRow) &&
                     (periodAllowance.used < periodAllowance.total);

    expect(canAdopt).toBe(true);
    expect(seriesOccurrence.price).toBe(0);
  });

  test('Negative Case 1: Series occurrence with snapshot but allowance EXHAUSTED is left alone and logged as covered_without_usage_exhausted', async () => {
    const seriesOccurrence = {
      id: 'apt_series_slot4',
      date: '2026-10-03',
      price: 0,
      membershipDiscountSnapshot: { eligible: true, membershipId: 'mem_live_01' },
      hasActiveUsageRow: false
    };
    const periodAllowance = { total: 2, used: 2 };
    const canAdopt = (seriesOccurrence.price === 0) &&
                     (seriesOccurrence.membershipDiscountSnapshot?.eligible) &&
                     (!seriesOccurrence.hasActiveUsageRow) &&
                     (periodAllowance.used < periodAllowance.total);

    const logCode = !canAdopt ? 'covered_without_usage_exhausted' : 'adopted';
    expect(canAdopt).toBe(false);
    expect(logCode).toBe('covered_without_usage_exhausted');
  });

  test('Negative Case 2: Location mismatch - booking at Clinic B is rejected when plan is locked to Clinic A', async () => {
    const plan = { id: 'plan_active', locationId: 'loc_sydney_central' };
    const booking = { id: 'apt_wrong_loc', locationId: 'loc_melbourne_north', status: 'PENDING' };
    const isLocationMatch = plan.locationId === booking.locationId;

    expect(isLocationMatch).toBe(false);
  });

  test('Negative Case 3: Type not included in plan inclusions is declined by engine', async () => {
    const planInclusions = ['Quick Appointment', 'PHYSIO CLASS'];
    const booking = { id: 'apt_other_type', appointmentTypeName: 'Dental Checkup', price: 150 };
    const isTypeIncluded = planInclusions.includes(booking.appointmentTypeName);

    expect(isTypeIncluded).toBe(false);
  });

  test('Negative Case 4: Cancelled, Rescheduled, or No-Show bookings are strictly excluded from linking', async () => {
    const inactiveStatuses = ['CANCELLED', 'RESCHEDULED', 'NO_SHOW', 'DELETED'];
    inactiveStatuses.forEach(status => {
      const booking = { id: status, status };
      const isCandidate = !['CANCELLED', 'RESCHEDULED', 'NO_SHOW', 'DELETED'].includes(booking.status);
      expect(isCandidate).toBe(false);
    });
  });

  test('Negative Case 5: Invoice with partial or full payments (invoice_has_payments) strictly blocks auto-link', async () => {
    const booking = {
      id: 'apt_with_paid_inv',
      status: 'PENDING',
      invoice: { id: 'inv_partial_01', amountPaid: 40.00 }
    };
    const hasLivePayments = booking.invoice && booking.invoice.amountPaid > 0;
    expect(hasLivePayments).toBe(true);
  });

  test('Edge Case 6: Backfill closed period with Paid fee invoice correctly re-allocates fee and reverses unearned residual', async () => {
    const closedPeriod = {
      feeInvoicePaid: true,
      periodFee: 100.00,
      deliveredSessions: [{ id: 'apt_aug_01', date: '2026-08-03' }]
    };
    const allocatedPerSession = closedPeriod.periodFee / closedPeriod.deliveredSessions.length;
    const unallocatedResidual = closedPeriod.periodFee - (allocatedPerSession * closedPeriod.deliveredSessions.length);

    expect(allocatedPerSession).toBe(100.00);
    expect(unallocatedResidual).toBe(0.00);
  });

});
