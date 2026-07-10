# Release notes

This document is the external-facing summary of what `basis-schemas`
publishes at each release. It complements
[`CHANGELOG.md`](../CHANGELOG.md), which records the exhaustive,
PR-by-PR history; this document distills that history into what a
downstream consumer (`basis-core`, `basis-gateway`, `basis-adapters`,
`basis-console`) actually needs to know before depending on a release.

## v0.2.0 — Operation-Aware Second Wave

**A note on versioning.** The package version in `pyproject.toml` and
`basis_schemas.__version__` is now `0.2.0`, bumped from the `0.1.0` first
public release to publish this cycle's fourteen new contracts. Every
individual contract still carries its own contract version, `0.1.0`,
independent of the package version — publishing a contract for the first
time starts it at `0.1.0` regardless of the package version it ships
under. This release is complete: all seven planned PRs (A through G) of
the operation-aware schema readiness plan have been published.

### Highlights

This release completes `basis-architecture`'s operation-aware schema
readiness plan (ADR-0005), publishing all seven planned PRs (A through G)
and bringing the repository from 6 to 20 total published contracts:

- **Fourteen operation-aware contracts**, published across six PRs in
  dependency order: shared metadata and vocabulary (`contract-metadata`,
  `redaction-classification`, `reason-code`); evidence references
  (`identity-evidence-reference`, `adapter-evidence-reference`); the
  operation-aware decision request (`operation-aware-decision-request`);
  a structured policy data model (`policy-condition`, `policy-rule`,
  `policy-bundle`); an evaluation trace model (`trace-rule-evidence`,
  `evaluation-trace`, `operation-aware-decision-response`); and separate
  kernel and gateway audit artifacts (`audit-evidence`,
  `gateway-audit-event`).
- **Five canonical compatibility scenarios** —
  `allow-basic`, `deny-precedence`, `default-deny`, `not-applicable`, and
  `invalid-policy-bundle` — published under
  [`examples/operation-aware/compatibility/`](../examples/operation-aware/compatibility/README.md),
  each connecting a request, a policy bundle, and the expected trace,
  response, kernel audit evidence, and gateway audit event into one
  coherent, cross-validated fixture set.
- **Additive compatibility with the six first-wave contracts**
  (`vocabulary`, `action-string`, `resource-identifier`,
  `decision-request`, `decision-response`, `audit-event`), which remain
  published, documented, tested, and byte-for-byte unchanged since the
  first public release.
- **A structured policy data model**, not a policy language: conditions,
  rules, and bundles as data, with no operator language, execution
  engine, or scripting surface chosen.
- **An evaluation trace model**, separate from audit evidence, that
  records per-rule match/no-match/error/skip outcomes without exposing a
  rule's own match criteria or condition internals.
- **Separate kernel and gateway audit artifacts** (`audit-evidence` vs.
  `gateway-audit-event`) that are never collapsed into one contract:
  the gateway references kernel evidence by ID rather than embedding or
  reproducing it, and fail-closed gateway enforcement is recorded as its
  own fact, independent of (and never rewriting) the kernel's own
  outcome.
- **Evidence-reference contracts** (`identity-evidence-reference`,
  `adapter-evidence-reference`) that let later contracts point at
  identity and adapter evidence by a structural digest and a redaction
  classification, without embedding raw tokens, claims, or protocol
  payloads.
- **Redaction classifications**, a closed five-value vocabulary
  (`safe_to_expose`, `safe_after_redaction`, `reference_only`,
  `never_store`, `never_display`) evidence is sorted into before it may
  appear in a trace, audit, or explanation artifact.
- **An open reason-code structure** — a lowercase snake_case format, not
  a closed enum — so the final reason-code vocabulary stays with the
  contracts that carry a `reason_code` field in practice, rather than
  being invented here ahead of need.

### Important boundaries

Consistent with what `basis-schemas` is and is not (see
[`README.md`](../README.md) and
[`docs/architecture.md`](architecture.md)), this release:

- does **not** implement a policy engine, a condition operator language,
  or any evaluation behavior — the policy contracts are data shapes a
  future evaluator validates against, not an evaluator;
- does **not** execute policy conditions — `policy-condition` publishes a
  deterministic predicate *shape*, never executable code;
- does **not** perform runtime authentication, token verification, or
  claim validation — the evidence-reference contracts carry structural
  digests and classifications, never raw tokens, claims, or credentials;
- does **not** enforce authorization decisions — enforcement, including
  gateway fail-closed behavior, is `basis-gateway`'s responsibility; this
  repository only publishes the shape of the record that behavior
  produces;
- does **not** verify evidence trust, authenticity, signatures, or
  non-repudiation — evidence digests are validated structurally only, and
  no contract claims otherwise;
- does **not** replace, deprecate, or silently redirect the six first-wave
  contracts — the operation-aware contracts are additive vNext surfaces
  that a future `basis-core` v0.2.0 may adopt, published alongside the
  unchanged first-wave contracts a current `basis-core` v0.1.x already
  consumes.

### Consumer direction

This release is intended to give `basis-core`'s next implementation phase
(v0.2.0) a stable, reviewable operation-aware target to build against,
ahead of adoption. `basis-gateway`, `basis-adapters`, and `basis-console`
are expected to integrate with the operation-aware contracts — in
particular the trace, audit-evidence, and gateway-audit-event shapes —
once `basis-core` produces them. As of this release, **no implementation
repository consumes the operation-aware contracts yet**; this document
does not claim otherwise. Consumers that need the contract files
themselves (including the compatibility vectors) should read them from a
pinned source release, repository tag, submodule, or vendored copy —
`pip install basis-schemas` installs only the small `basis_schemas`
metadata package, not the schema, example, or documentation files
themselves. See "How to consume contracts" in
[`README.md`](../README.md) and section 17 of
[`examples/operation-aware/compatibility/README.md`](../examples/operation-aware/compatibility/README.md#17-packaging-and-downstream-consumption)
for the full packaging rationale.
