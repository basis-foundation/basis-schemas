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
- **Identity establishment** — identity-provider integration, federation,
  session handling, and BASIS-local identity-token issuance — belongs to
  `basis-identity`. It produces the trusted identity context (and, per PR B,
  the identity evidence reference) that other components consume; it does
  not evaluate authorization.
- **Identity verification at the enforcement boundary and request
  assembly** — verifying accepted caller identity/token context as
  configured, mapping trusted identity into authorization request context,
  invoking `basis-core`, and enforcing decisions — belongs to
  `basis-gateway`. `basis-core` never authenticates: it evaluates the
  structured request it is given (Section 8 of the operation-aware
  authorization model), it does not verify identity itself.
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
(PR A), the identity- and adapter-evidence-reference contracts (PR B), the
operation-aware decision request (PR C), the policy bundle and rule
contracts (PR D), the trace rule evidence, evaluation trace, and
operation-aware decision response contracts (PR E), and now the audit
evidence and gateway audit event contracts (PR F) — see
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md)
— the same boundaries apply unchanged: `basis-architecture` decides the
shape, `basis-schemas` publishes it, and implementations consume it. No new
ownership model is introduced for the operation-aware contracts; they are
additive publications under the model already described above. The evidence
reference contracts in particular preserve the boundaries already stated:
`basis-identity` produces identity evidence, `basis-adapters` produces
normalized adapter evidence, `basis-gateway` will assemble references into
operation-aware requests and audit events, `basis-core` consumes references
as request context without retrieving or interpreting raw evidence, and
`basis-console` will display redacted reference metadata only. PR C's
operation-aware decision request preserves the same evaluation boundary:
`basis-gateway` assembles the request, `basis-core` evaluates it, and
`basis-schemas` publishes only the shape — no implementation repository
consumes PR C yet.

PR D's policy bundle and rule contracts (`policy-condition`, `policy-rule`,
`policy-bundle`) preserve the same boundaries again, restated at the policy
level per ADR-0004 Section 16: `basis-architecture` defines policy model
semantics and governance direction; `basis-schemas` publishes the
machine-readable policy contract shapes only (this repository never
implements policy evaluation); a future `basis-core` v0.2.0 validates and
evaluates policy bundles deterministically; a future `basis-gateway` loads,
selects, and configures policy bundles as runtime input but does not define
policy semantics; `basis-adapters` never author, interpret, or enforce
policy; `basis-identity` never authors or evaluates policy; `basis-console`
may later visualize policy, explanations, and traces but does not evaluate
policy. These contracts publish a structured policy **data model**, not a
policy language: no policy language (Rego, Cedar, CEL, Python, JavaScript,
SQL, WASM, or a custom DSL) is chosen, and no executable policy expression,
embedded code, or `script` field is published. No implementation repository
consumes PR D yet.

PR E's response and trace contracts (`trace-rule-evidence`,
`evaluation-trace`, `operation-aware-decision-response`) preserve the same
boundaries again, restated at the evaluation-explanation level per
ADR-0002 Section 15 and ADR-0003 Section 14: `basis-architecture` defines
decision and trace semantics; `basis-schemas` publishes the response and
trace shapes only; a future `basis-core` v0.2.0 evaluates requests and
produces the decision response and evaluation trace; a future
`basis-gateway` invokes `basis-core`, enforces valid decisions (including
fail-open/fail-closed behavior on evaluation failure, which this repository
does not decide), and later emits its own gateway audit event (PR F);
`basis-console` may later display safe decision explanations and trace
information but is never authoritative; `basis-identity` does not evaluate
authorization policy; `basis-adapters` do not evaluate or enforce
authorization policy. Evaluation trace is explicitly not audit evidence
(ADR-0003 Section 2): `AuditEvidence` and `GatewayAuditEvent` remain
deferred to PR F. No implementation repository consumes PR E yet.

PR F's audit contracts (`audit-evidence`, `gateway-audit-event`) preserve
the same boundaries again, restated at the audit-evidence-assembly level
per ADR-0003 Section 14: `basis-architecture` defines audit semantics,
evidence boundaries, and assembly ownership; `basis-schemas` publishes the
audit contract shapes only; a future `basis-core` v0.2.0 produces
`audit-evidence` as an associated evaluation artifact alongside its
decision response and evaluation trace — not embedded in
`operation-aware-decision-response`, and with no runtime transport,
envelope, return tuple, or delivery mechanism defined by this PR
(kernel-side evidence it does not itself persist durably); a future
`basis-gateway` consumes the kernel
result, enforces it or fails closed, and assembles `gateway-audit-event`
by combining the referenced `audit-evidence` with its own enforcement
facts (`enforcement_action`, `gateway_id`, `gateway_failure_reason`) —
facts the kernel structurally cannot know; `basis-console` may later
display authorized, redacted audit information but is not the audit
authority; `basis-identity` establishes trusted identity context but does
not evaluate authorization policy; `basis-adapters` normalize OT
operations but do not evaluate or enforce authorization policy. This
repository does not implement audit persistence, retention, signing,
tamper-evidence, or gateway enforcement — see
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md),
"PR F," for the full boundary. No implementation repository consumes PR F
yet.

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
