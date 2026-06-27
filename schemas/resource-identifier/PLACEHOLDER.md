# resource-identifier (placeholder — not yet migrated)

**Contract:** The canonical typed resource identifier.

**Planned shape (informative, not yet published):** {type}:{qualifier} — e.g. ahu:rooftop-1, sensor:co2:lobby.

**Migration order:** #3 of the six planned first contracts. See
[`../../docs/migration-plan.md`](../../docs/migration-plan.md).

**Initial state on publication:** `experimental`. See
[`../../docs/contract-governance.md`](../../docs/contract-governance.md) for the
lifecycle and compatibility rules.

---

This directory is a placeholder. No schema has been migrated into it yet. When
this contract migrates, this directory will publish the parallel format contract to the action string, stable in basis-core today. It defines the identifier structure only; the resource taxonomy itself remains an open architecture question and is not published here.

This repository **publishes** decided contracts; it does not invent or redefine
them. The shape above is decided in `basis-architecture` and is reproduced here
only to describe what this directory will eventually hold.
