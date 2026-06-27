# decision-response (placeholder — not yet migrated)

**Contract:** The kernel output shape.

**Planned shape (informative, not yet published):** outcome, reason, evaluating policy, policy version, optional failure reason, timestamp.

**Migration order:** #5 of the six planned first contracts. See
[`../../docs/migration-plan.md`](../../docs/migration-plan.md).

**Initial state on publication:** `experimental`. See
[`../../docs/contract-governance.md`](../../docs/contract-governance.md) for the
lifecycle and compatibility rules.

---

This directory is a placeholder. No schema has been migrated into it yet. When
this contract migrates, this directory will publish the output of policy evaluation. Owned today by basis-core's DecisionResponse. It defines the response shape only, never the decision semantics, which stay in basis-core.

This repository **publishes** decided contracts; it does not invent or redefine
them. The shape above is decided in `basis-architecture` and is reproduced here
only to describe what this directory will eventually hold.
