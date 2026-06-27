# decision-request (placeholder — not yet migrated)

**Contract:** The kernel input shape.

**Planned shape (informative, not yet published):** subject, composite action, optional canonical resource identifier, and context.

**Migration order:** #4 of the six planned first contracts. See
[`../../docs/migration-plan.md`](../../docs/migration-plan.md).

**Initial state on publication:** `experimental`. See
[`../../docs/contract-governance.md`](../../docs/contract-governance.md) for the
lifecycle and compatibility rules.

---

This directory is a placeholder. No schema has been migrated into it yet. When
this contract migrates, this directory will publish the input to policy evaluation. Owned today by basis-core's DecisionRequest. It composes the action-string and resource-identifier contracts, so it follows once both are published. It defines the request shape only, never how the request is evaluated.

This repository **publishes** decided contracts; it does not invent or redefine
them. The shape above is decided in `basis-architecture` and is reproduced here
only to describe what this directory will eventually hold.
