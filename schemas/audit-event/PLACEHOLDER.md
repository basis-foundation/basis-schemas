# audit-event (placeholder — not yet migrated)

**Contract:** The canonical audit event structure.

**Planned shape (informative, not yet published):** schema version, action-vocabulary version, action, resource, evaluating policy and version, outcome, timestamp.

**Migration order:** #6 of the six planned first contracts. See
[`../../docs/migration-plan.md`](../../docs/migration-plan.md).

**Initial state on publication:** `experimental`. See
[`../../docs/contract-governance.md`](../../docs/contract-governance.md) for the
lifecycle and compatibility rules.

---

This directory is a placeholder. No schema has been migrated into it yet. When
this contract migrates, this directory will publish the broadest contract of the first set, referencing action, resource, and policy version. Owned today by basis-core's AuditEvent, with the gateway as a producer. The event shape is a contract; audit persistence and the audit pipeline are not, and stay out of this repository.

This repository **publishes** decided contracts; it does not invent or redefine
them. The shape above is decided in `basis-architecture` and is reproduced here
only to describe what this directory will eventually hold.
