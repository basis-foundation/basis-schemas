# Release notes

This document is the external-facing summary of what `basis-schemas`
publishes at each release. It complements
[`CHANGELOG.md`](../CHANGELOG.md), which records the exhaustive,
PR-by-PR history; this document distills that history into what a
downstream consumer (`basis-core`, `basis-gateway`, `basis-adapters`,
`basis-console`) actually needs to know before depending on a release.

## v0.2.2 — Evidence-Provenance Fixture Correction

**This is a patch release.** It corrects canonical operation-aware
compatibility-vector fixture semantics to agree with a newly merged
`basis-architecture` clarification; it publishes no new contract, changes
no contract shape, field, version, or enum, and does not change any
authorization outcome. The `20` published contracts and `5` canonical
compatibility scenarios are unchanged in number and unchanged in shape.

**A note on versioning.** The package version in `pyproject.toml` and
`basis_schemas.__version__` is now `0.2.2`, bumped from `0.2.1` to
distribute this correction. No individual contract version changed.

**What changed.** `basis-core`'s roadmap PR 37 ("Wire the five canonical
scenarios end-to-end") was the first point in either repository's history
where the merged operation-aware evaluation pipeline was compared, field by
field, against these vectors. That comparison surfaced three repeatable
disagreements, resolved by `basis-architecture`'s operation-aware
evidence-provenance semantics clarification
(`docs/architecture/operation-aware-evidence-provenance-semantics.md`):

- **Top-level `explanation` is optional and non-authoritative.** Every
  scenario's expected response, trace, audit evidence, and gateway audit
  event now carry `explanation: null` at the top level, replacing
  synthesized aggregate sentences no governed evaluation stage actually
  produces. `reason_code` remains the authoritative machine-readable
  explanation.
- **Matched rule evidence preserves its authored `reason_code`/
  `explanation` verbatim** — including a matched-but-non-decisive `ALLOW`
  rule under deny precedence, which is genuine matched evidence even though
  a matched `DENY` rule determines the final outcome. A wording
  inconsistency between `deny-precedence`'s authored policy-bundle text
  ("operations," plural) and its expected trace ("operation," singular) is
  corrected to match the authored bundle text exactly. Non-matched and
  skipped rules continue to omit authored match rationale.
- **Bundle identity is retained for `NOT_APPLICABLE` and for a typed
  semantic policy-validation failure.** The `not-applicable` and
  `invalid-policy-bundle` scenarios' `bundle_id`/`bundle_version` — previously
  `null` or absent — now carry the identity of the specific bundle that was
  checked (and found out of scope) or rejected (for its duplicate rule
  IDs). Bundle identity is provenance for which bundle was involved; it is
  never a claim that the bundle applied, matched, or granted anything.

The `invalid-policy-bundle` scenario's `v0.2.1` correction — classifying its
duplicate-`rule_id` defect as `failure_reason: policy_validation_failure`,
not `invalid_policy_bundle` — is unchanged and reverified by this release.

**No contract schema, field, enum, or contract version changed** as part of
this release, and **no authorization outcome changed**: every scenario's
`outcome` / `evaluation_status` / `failure_reason` is identical to
`v0.2.1`. This is a compatibility-fixture correction aligned to newly
clarified architecture, not a new evaluator feature, a new schema family, a
new reason-code vocabulary, or a breaking change.

**Consumer direction.** Consumers using the canonical operation-aware
compatibility vectors should update from the `v0.2.1` source snapshot to
`v0.2.2`. As with prior releases, consume this repository's contracts and
fixtures from a pinned source release, repository tag, or vendored
snapshot — not by scraping `main`.

## v0.2.1 — Compatibility Vector Classification Fix

**This is a patch release.** It corrects the failure-category
classification of one operation-aware compatibility scenario; it
publishes no new contract, changes no contract shape, field, version, or
enum, and does not alter compatibility semantics generally. The `20`
published contracts and `5` canonical compatibility scenarios from
`v0.2.0` are unchanged in number and unchanged in shape.

**A note on versioning.** The package version in `pyproject.toml` and
`basis_schemas.__version__` is now `0.2.1`, bumped from `0.2.0` to
distribute this correction. No individual contract version changed —
every contract still carries the same contract version it carried under
`v0.2.0`.

The `invalid-policy-bundle` compatibility scenario keeps its name and its
underlying defect (a policy bundle with duplicate `rule_id` values
across its `rules` array). What changes is its **expected failure
category**:

- before (`v0.2.0`): `failure_reason: invalid_policy_bundle`
- after (`v0.2.1`): `failure_reason: policy_validation_failure`

Duplicate `rule_id` values are a **semantic bundle-validation defect**,
not a structural one: the bundle and every rule within it are
individually well-formed — every field, at every level, conforms to its
own schema — but the bundle as a whole violates a cross-rule uniqueness
invariant that no single rule object's schema can express. Per
ADR-0002 Section 14, that is "shaped correctly but fails internal
consistency validation" (`policy_validation_failure`), not "does not
conform to the required shape" (`invalid_policy_bundle`).
`invalid_policy_bundle` remains the correct classification for a bundle
that is structurally malformed; this fix narrows nothing about that
category, it only corrects which category this one scenario's defect
belongs to.

All four result artifacts for the `invalid-policy-bundle` scenario now
agree on the corrected category:

- the expected evaluation trace
- the expected operation-aware decision response
- the expected kernel audit evidence
- the expected gateway audit event

Within those artifacts, the kernel `outcome` remains `null` — evaluation
failed before an ALLOW/DENY outcome could be produced — and gateway
enforcement remains `deny`, because the gateway fails closed on any
evaluation failure regardless of failure category.

No contract schema, field, enum, or contract version changed as part of
this release. `policy_validation_failure` and `invalid_policy_bundle`
were both already published, valid members of the `failure_reason` enum
before this fix; this release only corrects which of the two values one
scenario's fixtures expect.

**Consumer direction.** Consumers using the canonical operation-aware
compatibility vectors should update from the `v0.2.0` source snapshot to
`v0.2.1`. As with `v0.2.0`, consume this repository's contracts and
fixtures from a pinned source release, repository tag, or vendored
snapshot — not by scraping `main`, which may move ahead of any tagged
release.

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
