/** Per-run AU test data helpers. The epoch is the only varying input. */
export class DataGenerator {
  /** RFC 2606 reserved domain: mail can never reach a real person. */
  static unregisteredEmail(): string {
    return `qa+${Date.now()}@example.com`;
  }
}
