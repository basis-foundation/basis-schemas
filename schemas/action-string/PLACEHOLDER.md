# action-string (placeholder — not yet migrated)

**Contract:** The composite action-name format.

**Planned shape (informative, not yet published):** {verb}:{domain}[:{object}] — e.g. read:hvac:setpoint, write:hvac:setpoint, execute:hvac:override.

**Migration order:** #2 of the six planned first contracts. See
[`../../docs/migration-plan.md`](../../docs/migration-plan.md).

**Initial state on publication:** `experimental`. See
[`../../docs/contract-governance.md`](../../docs/contract-governance.md) for the
lifecycle and compatibility rules.

---

This directory is a placeholder. No schema has been migrated into it yet. When
this contract migrates, this directory will publish the format that wraps the verbs. Owned today by basis-core's format regex and mirrored by the console; this directory will hold the single definition. Depends on the vocabulary contract.

This repository **publishes** decided contracts; it does not invent or redefine
them. The shape above is decided in `basis-architecture` and is reproduced here
only to describe what this directory will eventually hold.
