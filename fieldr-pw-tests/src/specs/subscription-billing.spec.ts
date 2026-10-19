/**
 * Release notes: New Features > Subscription & Billing and iPhone App; Improvements > Subscription Screens and Purchase History.
 * IDs in this file: IPH-01, IPH-02, IPH-03, SUB-01, SUB-02, SUB-03, SUBS-01, SUBS-02, SUBS-03, SUBS-04
 * Traceability: docs/traceability-matrix.md. Every title starts with its ID and carries area + persona tags.
 */
import { test } from '../fixtures/data.fixture';

test.describe('@billing iPhone App', () => {
  test('[IPH-01] @billing @manual @super-admin MANUAL Companies can sign up and pay through the App Store on iPhone', async () => {
    test.fixme(true, 'reason: MANUAL - App Store / TestFlight device required');
  });

  test('[IPH-02] @billing @manual @super-admin MANUAL App Store billing stays off until it is switched on', async () => {
    test.fixme(true, 'reason: MANUAL - App Store build plus the feature flag state; also verify web flows unchanged with the flag off');
  });

  test('[IPH-03] @billing @manual @super-admin MANUAL A company already paying by card is never charged twice', async () => {
    test.fixme(true, 'reason: MANUAL - real payments on both rails; compare provider ledgers');
  });
});

test.describe('@billing Subscription & Billing', () => {
  test('[SUB-01] @billing @super-admin A cancelled subscription can be resumed before it ends', async () => {
    test.fixme(true, 'reason: needs a billing-sandbox company with a cancelled-but-not-ended subscription');
  });

  test('[SUB-02] @billing @super-admin Payment History shows whether each charge was monthly or yearly', async () => {
    test.fixme(true, 'reason: needs a billing sandbox with both a monthly and a yearly charge');
  });

  test('[SUB-03] @billing @super-admin The first invoice lists each add-on separately', async () => {
    test.fixme(true, 'reason: needs a billing sandbox company with a first invoice that includes add-ons');
  });
});

test.describe('@billing Subscription screens & Purchase History', () => {
  test('[SUBS-01] @billing @super-admin Trial, cancellation and renewal status are clearer on Current Subscription, plan cards and the cancel card', async () => {
    test.fixme(true, 'reason: needs billing-sandbox companies in trial, cancelled and renewing states; expected wording unconfirmed');
  });

  test('[SUBS-02] @billing @super-admin A cancelled trial is shown separately from an active plan', async () => {
    test.fixme(true, 'reason: needs a billing-sandbox company with a cancelled trial');
  });

  test('[SUBS-03] @billing @super-admin Alert messages use the space better', async () => {
    test.fixme(true, 'reason: visual-layout change with no stated expectation; use a screenshot baseline once approved');
  });

  test('[SUBS-04] @billing @super-admin The onboarding fee is handled correctly for resumed subscriptions', async () => {
    test.fixme(true, 'reason: needs a billing sandbox resumed subscription and the expected fee amount');
  });
});
