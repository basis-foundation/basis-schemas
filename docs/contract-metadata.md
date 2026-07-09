# Contract Metadata Contract

The **contract metadata** contract formalizes the `contract:` block every
published contract in this repository already carries. It is a shared
foundation contract from the operation-aware schema readiness plan
(`basis-architecture` ADR-0005,
`docs/architecture/operation-aware-schema-readiness-plan.md`, "PR A — Shared
Metadata and Vocabulary"), not part of the original six-contract migration wave
described in [`migration-plan.md`](migration-plan.md). See
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md)
for how this contract fits into that larger, still-in-progress plan.

- Contract file: [`../schemas/contract-metadata/contract-metadata.yaml`](../schemas/contract-metadata/contract-metadata.yaml)
- Governed by: `basis-architecture`
- Published by: `basis-schemas`
- Version: `0.1.0`
- Lifecycle: `experimental`
- Depends on: none

## Purpose

Every contract published here already carries a `contract:` block —
documented informally in [`../schemas/README.md`](../schemas/README.md)
("Metadata pattern") and reused, unchanged, by all six first-wave contracts.
This contract publishes that shape as a citable, reusable definition, so
future contracts (and tooling that reads them) have a stable reference for
what a valid `contract:` block contains, instead of relying on six examples
and a paragraph of prose.

This is a publication of an existing, proven pattern — not a new design. No
existing contract needs to change; the `contract:` block every contract
already has continues to work exactly as before.

## Why one composed contract, not two

The operation-aware schema readiness plan names "schema version metadata" and
"contract identifiers" as two of the shared building blocks PR A should
publish. This contract addresses both together, as a single composed shape,
rather than as two separate contracts, because that is exactly how the
existing `contract:` block already composes them: a contract's identifier
(`name`) and its version (`version`) have never appeared in this repository
except together, alongside lifecycle, governance, and provenance fields.
Splitting a composition that has been proven six times into pieces no
consumer has ever needed separately would add indirection without reducing
duplication — the opposite of what a shared primitive is for.

## Canonical shape

| Field           | Required | Type              | Meaning |
| --------------- | -------- | ------------------ | ------- |
| `name`          | yes      | string (pattern)   | The contract identifier; lowercase kebab-case, matches the directory name. |
| `title`         | yes      | string (non-empty) | Human-readable title. |
| `version`       | yes      | string (pattern)   | The contract's own version (`MAJOR.MINOR.PATCH`) — not the package version. |
| `lifecycle`     | yes      | enum               | `experimental`, `candidate`, or `stable`. |
| `governed_by`   | yes      | string (non-empty) | Where the shape is decided (currently always `basis-architecture`). |
| `published_by`  | yes      | string (non-empty) | Where the definition is published (currently always `basis-schemas`). |
| `source`        | yes      | string (non-empty) | Path to the governing document in `basis-architecture`. |
| `description`   | yes      | string (non-empty) | One-paragraph summary. |
| `depends_on`    | no       | array of strings   | Other contract identifiers this one builds on. |

Unknown fields are rejected.

## Contract identifier semantics

The `name` field is the contract's stable, machine-readable identity:
explicit, deterministic, non-empty, and independent of Python import path,
source filename, generated schema filename, or package installation location.
By convention it matches the contract's directory name under `schemas/`. It
carries no mutable information such as a timestamp or filesystem path, and it
is suitable for use in schema metadata, compatibility records, audit evidence,
trace metadata, and test vectors — anywhere a contract needs to be referenced
without depending on how it happens to be packaged.

## Contract/schema version semantics

The `version` field is the version of this specific machine-readable contract
surface — **not** the `basis-schemas` package release version. The two are
easy to conflate because every first-wave contract currently happens to
publish `"0.1.0"`, the same value as the package version at the time. That is
coincidence, not a rule: a contract's version advances when its own shape
changes, on its own schedule, independent of when the package is released.
This contract defines version metadata only — it does not implement version
negotiation or compatibility resolution; see
[`contract-governance.md`](contract-governance.md) for what a version change
requires.

## Examples

A real, already-published `contract:` block (vocabulary's), reproduced
verbatim to show this schema faithfully describes existing usage:

```yaml
name: vocabulary
title: BASIS Action Vocabulary
version: "0.1.0"
lifecycle: experimental
governed_by: basis-architecture
published_by: basis-schemas
source: docs/architecture/action-vocabulary.md
description: >-
  Canonical action verbs shared across BASIS components.
```

Invalid metadata includes: a missing or empty `name`, a `name` that is not
lowercase kebab-case, a missing or malformed `version` (not
`MAJOR.MINOR.PATCH`), a `lifecycle` outside the three published values, a
malformed `depends_on` entry, and any unknown field.

## Adoption

Existing contracts are not required to change anything in this PR — they
already conform to this shape, which is how it was derived. Future
operation-aware contracts (decision request, policy bundle, evaluation trace,
audit evidence, and the rest of the readiness plan) are expected to reuse this
same `contract:` shape rather than inventing a new one.

## Why `experimental`?

The lifecycle describes this **published contract** — formalizing the pattern
as its own citable definition is new — not the underlying `contract:` block
shape, which has been stable and reused without change since the vocabulary
contract first established it. See [`contract-governance.md`](contract-governance.md).
