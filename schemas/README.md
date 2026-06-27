# Schemas

This directory holds the published, machine-readable contracts of the BASIS
ecosystem. During Phase 1 it contains **placeholder directories only** — one per
planned first contract. No real contract has been migrated yet. The contracts,
their order, and what is deferred are described in
[`../docs/migration-plan.md`](../docs/migration-plan.md); the lifecycle states
referenced below are defined in
[`../docs/contract-governance.md`](../docs/contract-governance.md).

---

## Directory structure

Each contract lives in its own directory, named for the contract. The placeholder
directories present today are:

```text
schemas/
├── vocabulary/             the five canonical action verbs
├── action-string/          {verb}:{domain}[:{object}]
├── resource-identifier/    {type}:{qualifier}
├── decision-request/       kernel input shape
├── decision-response/      kernel output shape
└── audit-event/            canonical audit structure
```

Each directory currently holds only a `PLACEHOLDER.md` describing the contract it
will eventually publish. When a contract migrates, its directory will gain the
actual schema definition, its version and state metadata, a changelog, and
(later) compatibility fixtures. The exact file layout and the schema-definition
format are chosen when the first contract migrates — Phase 1 does not commit the
repository to a particular framework before any schema exists.

## Schema lifecycle

A contract moves through three published states, never skipping forward and never
moving backward:

```text
experimental ──▶ candidate ──▶ stable
```

- **experimental** — published for early feedback; no compatibility guarantee.
  Every contract enters here on first publication.
- **candidate** — believed stable and proposed as final; additive changes
  expected, breaking changes discouraged and signalled.
- **stable** — a durable commitment, extendable only additively and changeable
  incompatibly only through the breaking-change process.

A contract's state is declared in its own metadata so a consumer can read, from
the contract alone, how much it can rely on the shape. State transitions are
decided in `basis-architecture`, not here; this directory publishes the state, it
does not decide it. See
[`../docs/contract-governance.md`](../docs/contract-governance.md) for the full
definitions, compatibility classification, and breaking-change process.

## What does not go here

This directory holds **contracts**, not behavior. Policy logic, authentication,
protocol translation, operator workflows, and deployment topology stay in their
owning repositories. A schema here defines a *shape* that multiple components
must agree on — never how that shape is evaluated, produced, or enforced. See
[`../docs/architecture.md`](../docs/architecture.md) for the full boundary.
