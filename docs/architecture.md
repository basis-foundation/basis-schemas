# Architecture and Role in the Ecosystem

This document explains what role `basis-schemas` plays in the BASIS ecosystem,
the dependency boundaries it must respect, and the relationship between this
repository and the implementation repositories that consume its contracts. It is
grounded in the charter recorded in `basis-architecture`
(`docs/architecture/basis-schemas.md`), which decides why this repository exists.
That charter governs; this document restates the boundaries this repository
operates within.

---

## Role

`basis-schemas` is the single, neutral home for the shared contracts of the
BASIS distribution. Its role is narrow and deliberate: it **publishes** the
machine-readable definition, version, and compatibility fixtures of each shape
that more than one component must agree on. It does not decide those shapes, and
it does not implement any behavior over them.

The contracts in scope are shared in the precise sense that no single
implementation repository is their natural owner. The decision request and
response, the action vocabulary, the action string and resource identifier
formats, and the audit event are consumed by multiple components. If any of them
lived inside one component, that component would become the de-facto authority
for a contract its peers must also honor — the exact failure mode that motivated
this repository. A neutral repository removes that accidental authority and lets
every component depend on the contract without depending on a peer's
implementation.

## The ownership model

```text
Architecture proposes.
Schemas publish.
Implementations consume.
```

- **`basis-architecture` proposes.** A new or changed shared contract is reasoned
  about and decided there — in an architecture document or an ADR — before it
  becomes a schema. Contracts are not invented in `basis-schemas`; they are
  published here once decided.
- **`basis-schemas` publishes.** Once a contract is decided, its definition,
  version, and compatibility fixtures live here as the single source of truth.
- **Implementations consume.** `basis-core`, `basis-gateway`, `basis-adapters`,
  and `basis-console` import the published contract rather than re-declaring it.
  No component re-declares a contract it does not own.

Two principles follow: each contract is defined once and imported everywhere
("one definition, many consumers"), and no component becomes the authority for a
contract merely because it happened to implement it first.

## Dependency boundaries

The dependency direction is strict and downward-only. `basis-schemas` sits
**below** the implementation repositories in the distribution's dependency
graph. Components depend on the schemas; the schemas depend on nothing else in
the distribution.

```text
        basis-architecture        (proposes; imports nothing at runtime)
                 │  decides
                 ▼
          basis-schemas            (publishes; depends on nothing in the distribution)
                 ▲
   ┌──────┬──────┼──────┬───────────┐
   │      │      │      │           │   consume (import downward)
basis-  basis- basis- basis-     basis-
 core  gateway adapt. console     deploy
```

Concretely, relative to `basis-schemas`:

- **`basis-core`** consumes the decision request/response, action string,
  resource identifier, and audit event, now published here. It originated several
  of these contracts and remains their authoritative implementation; the canonical
  shapes are published here for every component to share. It depends on
  `basis-schemas` only, never sideways on the gateway, adapters, console, or
  deploy.
- **`basis-gateway`** consumes the action string, resource identifier,
  normalized request, decision request/response, and audit event. Its
  composition behavior and its enforcement of the reserved `basis_gateway.*`
  namespace stay in the gateway; only the *rule* and the shapes are candidates
  here. It depends on `basis-schemas` and `basis-core`.
- **`basis-adapters`** consumes the normalized request schema and the action
  vocabulary. It depends on `basis-schemas`.
- **`basis-console`** consumes the normalized request schema, action vocabulary,
  and decision response. Its provisional vocabulary copy is retired in favor of
  the shared definition published here. It depends on `basis-schemas` and
  `basis-gateway`.
- **`basis-deploy`** consumes the compatibility metadata to assemble mutually
  compatible component versions. Its deployment and topology contracts are out
  of scope here.

The invariant across every component: dependencies point **downward toward
`basis-schemas`**, never sideways between implementation repositories.

## What is in scope and what is not

`basis-schemas` holds **contracts** — the shapes multiple components must agree
on. It does **not** hold **behavior**. The following remain owned by their
existing repositories and must not migrate here:

- **Policy logic and authorization evaluation** — how rules are matched and
  decided — belong to `basis-core`. This repository may define the *shape* of a
  decision request; it must not define how the request is evaluated.
- **Authentication** — token verification, subject derivation, identity at the
  trust boundary — belong to `basis-gateway`.
- **Protocol translation** — turning BACnet, Modbus, OPC UA, and the rest into a
  normalized request — belongs to `basis-adapters`. This repository defines the
  normalized *output* shape, not protocol logic.
- **Operator workflows and UI** — belong to `basis-console`.
- **Deployment topology and trust** — belong to `basis-deploy`.
- **Architecture governance** — the reasoning, principles, reconciliations, and
  ADRs that decide *why* a contract takes its shape — belong to
  `basis-architecture`. This repository publishes the *what*; `basis-architecture`
  explains the *why*.

The line is simple: a shape that multiple components must agree on is a candidate
for `basis-schemas`; a decision, behavior, workflow, or deployment arrangement
stays where it is.

## Implementation repositories may consume, but architecture governs

Implementation repositories are free to consume the published schemas — that is
the entire point of the repository. But consuming a schema does not confer any
authority over it. The schemas are **governed by `basis-architecture`**: changes
to a contract's shape or semantics are decided there first, and only then
published here. A change to a shared schema is reviewed as a change with
ecosystem-wide blast radius under the compatibility rules in
[`contract-governance.md`](contract-governance.md). No consumer can unilaterally
change a contract by changing its own copy, because consumers no longer hold
copies — they hold imports of the single published definition.

## The operation-aware expansion

The ownership model above is not limited to the six first-wave contracts. As
`basis-architecture`'s operation-aware schema readiness plan (ADR-0005,
`docs/architecture/operation-aware-schema-readiness-plan.md`) publishes further
contracts here — starting with the shared metadata and vocabulary contracts
(PR A) and now the identity- and adapter-evidence-reference contracts (PR B)
in [`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md)
— the same boundaries apply unchanged: `basis-architecture` decides the
shape, `basis-schemas` publishes it, and implementations consume it. No new
ownership model is introduced for the operation-aware contracts; they are
additive publications under the model already described above. The evidence
reference contracts in particular preserve the boundaries already stated:
`basis-identity` produces identity evidence, `basis-adapters` produces
normalized adapter evidence, `basis-gateway` will assemble references into
operation-aware requests and audit events, `basis-core` consumes references
as request context without retrieving or interpreting raw evidence, and
`basis-console` will display redacted reference metadata only.

## Tooling rationale

This repository uses a lightweight Python toolchain (pytest, ruff, mypy). The
published contracts are static YAML files; the tests parse each contract and
check that its metadata, field policy, and examples are internally consistent and
faithful to the shape `basis-architecture` decided. A minimal `src/basis_schemas`
package carries repository metadata (name, version, and the planned-versus-
published contract lists) so the type checker and test suite have something real
to run against. This deliberately stops short of a full schema-generation
framework: the smallest stable toolchain that keeps the quality gates meaningful
is preferred until a richer validation need actually arises.
