# Schemas

This directory holds the published, machine-readable contracts of the BASIS
ecosystem. Four contracts are now published — the action **vocabulary** in
[`vocabulary/vocabulary.yaml`](vocabulary/vocabulary.yaml), the **action
string** format in [`action-string/action-string.yaml`](action-string/action-string.yaml),
the **resource identifier** format in
[`resource-identifier/resource-identifier.yaml`](resource-identifier/resource-identifier.yaml),
and the **decision request** shape in
[`decision-request/decision-request.yaml`](decision-request/decision-request.yaml);
the remaining planned contracts are still **placeholder directories**. The
contracts, their order, and what is deferred are described in
[`../docs/migration-plan.md`](../docs/migration-plan.md); the lifecycle states
referenced below are defined in
[`../docs/contract-governance.md`](../docs/contract-governance.md).

---

## Directory structure

Each contract lives in its own directory, named for the contract:

```text
schemas/
├── vocabulary/             the five canonical action verbs       — PUBLISHED (vocabulary.yaml)
├── action-string/          {verb}:{domain}[:{object}]            — PUBLISHED (action-string.yaml)
├── resource-identifier/    {resource_type}:{local_resource_id}  — PUBLISHED (resource-identifier.yaml)
├── decision-request/       kernel input shape                   — PUBLISHED (decision-request.yaml)
├── decision-response/      kernel output shape                  — placeholder
└── audit-event/            canonical audit structure            — placeholder
```

A placeholder directory holds only a `PLACEHOLDER.md` describing the contract it
will eventually publish. When a contract migrates, its directory gains the actual
schema definition with embedded version and lifecycle metadata, and (later) a
changelog and compatibility fixtures. The vocabulary contract migrated first and
fixes the conventions the rest follow.

## Metadata pattern (the expected shape for every contract)

Every published contract carries a `contract:` block with explicit metadata, so a
consumer can read its identity, version, and lifecycle from the contract alone.
The vocabulary contract establishes the pattern future contracts reuse:

```yaml
contract:
  name: <contract-id>          # matches the directory name
  title: <human-readable title>
  version: <semver>            # e.g. 0.1.0
  lifecycle: experimental      # experimental | candidate | stable
  governed_by: basis-architecture   # where the contract is decided
  published_by: basis-schemas       # where it is published
  source: <path in basis-architecture>
  description: <one-paragraph summary>
  depends_on: [<contract-id>, ...]  # optional; other contracts this one builds on

<contract-body>:               # the contract's own payload, e.g. `vocabulary:`
  ...
```

When a contract builds on another, it declares the dependency with `depends_on`.
The action-string contract, for example, declares `depends_on: [vocabulary]`
because its verb segment draws its allowed values from the vocabulary contract —
the shape is published here, the verbs are published there.

YAML is the chosen format: it is human-diffable, comment-friendly, and trivially
machine-readable. This repository deliberately does **not** adopt a full
schema-generation framework yet; the pattern above is the smallest stable shape
that proves the publish-and-consume model.

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
