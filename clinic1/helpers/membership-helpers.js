/**
 * Helper utilities for ActiveRx Membership Coverage Linker QA
 */
class MembershipTestHelper {
  constructor(apiClient) {
    this.api = apiClient;
  }

  /**
   * Helper to create an appointment for a patient
   */
  async createAppointment({ patientId, appointmentTypeId, startDateTime, clinicId, price = 99, status = 'PENDING' }) {
    return this.api.post('/appointments', {
      patientId,
      appointmentTypeId,
      startDateTime,
      clinicId,
      price,
      status
    });
  }

  /**
   * Helper to buy or assign a membership plan to a patient
   */
  async activateMembership({ patientId, planId, paymentMethod = 'stripe', freeAssign = false }) {
    return this.api.post('/memberships/activate', {
      patientId,
      planId,
      paymentMethod,
      freeAssign
    });
  }

  /**
   * Helper to update appointment status (Arrived, Started, Completed)
   */
  async updateAppointmentStatus(appointmentId, status) {
    return this.api.patch(`/appointments/${appointmentId}/status`, {
      status // 'ARRIVED', 'STARTED', 'COMPLETED'
    });
  }

  /**
   * Helper to inspect membership usages for a patient / booking
   */
  async getMembershipUsages(patientId, appointmentId = null) {
    return this.api.get(`/memberships/usages`, {
      patientId,
      ...(appointmentId ? { appointmentId } : {})
    });
  }

  /**
   * Helper to retrieve invoices for an appointment
   */
  async getAppointmentInvoices(appointmentId) {
    return this.api.get(`/appointments/${appointmentId}/invoices`);
  }

  /**
   * Advance Stripe Test Clock for subscription renewal simulation
   */
  async advanceStripeClock(testClockId, targetTimestamp) {
    return this.api.post(`/test-utils/stripe-clock/advance`, {
      testClockId,
      targetTimestamp
    });
  }
}

module.exports = { MembershipTestHelper };
