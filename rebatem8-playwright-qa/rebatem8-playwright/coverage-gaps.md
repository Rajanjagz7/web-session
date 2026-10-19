# Extended test coverage gaps

This supplement contains candidate tests only. Every case is marked **Not executed / requires fixture or requirements** because the discovery exercise established navigation, visible controls, and selected read-only/API smoke behavior, but did not establish the complete business contract.

## Why exhaustive testing is not possible yet

- No product requirements, acceptance criteria, field-level validation rules, state-transition matrices, rounding/accounting rules, retention policies, or report schemas were provided.
- The discovery environment had sparse or empty data in several modules (for example, projects and invoices reported no data), so realistic fixtures are needed for positive, negative, boundary, dependency, and pagination tests.
- Only the discovered authenticated role was available. Additional roles and a permission matrix are required for meaningful RBAC, object-level authorization, and privilege-escalation tests.
- Several pages expose list buttons or headings, but create/update/delete, approval, upload, generation, and publish workflows were not verified. Candidate cases explicitly identify these as unverified rather than assuming they exist.
- Concurrency, retry/idempotency, session expiry, performance, and file-security tests require controlled harnesses, multiple sessions, representative volume, and agreed expected behavior.
- Financial calculator, rebate, and invoice assertions require authoritative examples defining precision, rounding order, currency/time-zone treatment, eligibility, and invoice immutability.
- Audit assertions require a documented event taxonomy, actor/target fields, retention, access controls, and whether exports/downloads are auditable.

The cases deliberately avoid claims that unobserved features exist or that any defect is present. Before execution, convert each candidate into a requirement-linked test, supply disposable fixtures and roles, and record the actual workflow/API contract discovered during implementation.
