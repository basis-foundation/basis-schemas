# Schemas

This directory holds the published, machine-readable contracts of the BASIS
ecosystem. All six contracts of the first planned wave are now published — the
action **vocabulary** in
[`vocabulary/vocabulary.yaml`](vocabulary/vocabulary.yaml), the **action
string** format in [`action-string/action-string.yaml`](action-string/action-string.yaml),
the **resource identifier** format in
[`resource-identifier/resource-identifier.yaml`](resource-identifier/resource-identifier.yaml),
the **decision request** shape in
[`decision-request/decision-request.yaml`](decision-request/decision-request.yaml),
the **decision response** shape in
[`decision-response/decision-response.yaml`](decision-response/decision-response.yaml),
and the **audit event** shape in
[`audit-event/audit-event.yaml`](audit-event/audit-event.yaml). No placeholder
directories remain. This completes the first planned wave; it does not close the
contract set — future contracts may be added through `basis-architecture`
governance. The contracts, their order, and what is deferred to a later wave are
described in
[`../docs/migration-plan.md`](../docs/migration-plan.md); the lifecycle states
referenced below are defined in
[`../docs/contract-governance.md`](../docs/contract-governance.md).

A second wave has since added twelve further contracts — `contract-metadata`,
`redaction-classification`, `reason-code` (PR A), `identity-evidence-reference`,
`adapter-evidence-reference` (PR B), `operation-aware-decision-request` (PR C),
`policy-condition`, `policy-rule`, `policy-bundle` (PR D), and now
`trace-rule-evidence`, `evaluation-trace`, `operation-aware-decision-response`
(PR E) — tracked separately in
[`../docs/operation-aware-schema-readiness.md`](../docs/operation-aware-schema-readiness.md).
They are additive; they do not extend or alter the six-contract first wave.

---

## Directory structure

Each contract lives in its own directory, named for the contract:

```text
schemas/
├── vocabulary/                 the five canonical action verbs       — PUBLISHED (vocabulary.yaml)
├── action-string/               {verb}:{domain}[:{object}]            — PUBLISHED (action-string.yaml)
├── resource-identifier/        {resource_type}:{local_resource_id}  — PUBLISHED (resource-identifier.yaml)
├── decision-request/            kernel input shape                   — PUBLISHED (decision-request.yaml)
├── decision-response/           kernel output shape                  — PUBLISHED (decision-response.yaml)
├── audit-event/                 canonical audit record shape         — PUBLISHED (audit-event.yaml)
├── contract-metadata/           the `contract:` block shape itself   — PUBLISHED (contract-metadata.yaml)
├── redaction-classification/    5-value redaction vocabulary         — PUBLISHED (redaction-classification.yaml)
├── reason-code/                 reason-code string format            — PUBLISHED (reason-code.yaml)
├── identity-evidence-reference/ safe reference to identity evidence  — PUBLISHED (identity-evidence-reference.yaml)
├── adapter-evidence-reference/  safe reference to adapter evidence   — PUBLISHED (adapter-evidence-reference.yaml)
├── operation-aware-decision-request/  additive vNext request shape  — PUBLISHED (operation-aware-decision-request.yaml)
├── policy-condition/            deterministic, data-only condition shape — PUBLISHED (policy-condition.yaml)
├── policy-rule/                 allow/deny rule shape                — PUBLISHED (policy-rule.yaml)
├── policy-bundle/                policy identity/version/scope/rules shape — PUBLISHED (policy-bundle.yaml)
├── trace-rule-evidence/         bounded per-rule trace explanation shape — PUBLISHED (trace-rule-evidence.yaml)
├── evaluation-trace/            deterministic, bounded evaluation explanation shape — PUBLISHED (evaluation-trace.yaml)
└── operation-aware-decision-response/  additive vNext response shape — PUBLISHED (operation-aware-decision-response.yaml)
```

The first six directories are the first-wave contracts described above and in
[`../docs/migration-plan.md`](../docs/migration-plan.md). The last twelve —
`contract-metadata`, `redaction-classification`, `reason-code`,
`identity-evidence-reference`, `adapter-evidence-reference`,
`operation-aware-decision-request`, `policy-condition`, `policy-rule`,
`policy-bundle`, `trace-rule-evidence`, `evaluation-trace`, and
`operation-aware-decision-response` — are a second wave: shared foundation,
evidence-reference, request, policy bundle/rule, and response/trace
contracts from `basis-architecture`'s operation-aware schema readiness plan
(ADR-0005), PRs A, B, C, D, and E respectively. They are not part of the
first wave's six-contract count and do not extend it.
`operation-aware-decision-request` and `operation-aware-decision-response`
are additive alongside `decision-request` and `decision-response`, not
replacements for them. `policy-condition`, `policy-rule`, and
`policy-bundle` publish a structured policy DATA model, not a policy
language — no policy evaluation is implemented by any contract in this
repository. `trace-rule-evidence` and `evaluation-trace` publish evaluation
*explanation* shapes, not audit records — audit evidence and gateway audit
events remain deferred to PR F. See
[`../docs/operation-aware-schema-readiness.md`](../docs/operation-aware-schema-readiness.md).

Every directory above now holds a real schema definition; no `PLACEHOLDER.md`
files remain. When a future contract is added, it follows the same pattern: a
directory is created (briefly holding a `PLACEHOLDER.md` describing the contract
it will publish), and on migration it gains the actual schema definition with
embedded version and lifecycle metadata, and (later) a changelog and
compatibility fixtures. The vocabulary contract migrated first and fixes the
conventions the rest follow.

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

This pattern is now formalized as its own reusable contract,
[`contract-metadata`](contract-metadata/contract-metadata.yaml) (see
[`../docs/contract-metadata.md`](../docs/contract-metadata.md)), so it has a
citable definition rather than only this prose description. No existing
contract needs to change: `contract-metadata` publishes the shape every
contract here already follows.

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
