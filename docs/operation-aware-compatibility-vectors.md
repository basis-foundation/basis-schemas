# Operation-Aware Compatibility Vectors

This document is the conceptual overview of PR G — Compatibility Examples
and Test Vectors, the final planned PR in `basis-architecture`'s
operation-aware schema readiness plan (ADR-0005,
[`docs/architecture/operation-aware-schema-readiness-plan.md`](https://github.com/basis-foundation/basis-architecture/blob/main/docs/architecture/operation-aware-schema-readiness-plan.md)).
The practical directory guide — layout, filenames, and how to read a
scenario — lives in
[`../examples/operation-aware/compatibility/README.md`](../examples/operation-aware/compatibility/README.md).
This document does not duplicate that guide; it explains why PR G exists
and how it fits the rest of the operation-aware second wave.

## 1. Purpose

PR A through PR F each published one governed contract or contract group in
isolation: shared metadata, evidence references, the operation-aware
request, the policy bundle/rule model, the response/trace model, and the
audit model. Each of those PRs is individually well-tested — every contract
carries its own `examples: {valid, invalid}` block and a dedicated test
suite. None of them, individually or together, demonstrated how the
contracts *compose* into a complete operation-aware authorization scenario:
a request evaluated against a bundle, producing a response and trace, from
which audit evidence and a gateway event are derived. PR G closes that gap
by publishing canonical, cross-contract compatibility vectors — not a new
contract.

## 2. Relationship to ADR-0005

ADR-0005's recommended publication order names PR G last, once PR A
through PR F are all published, because compatibility vectors necessarily
depend on every contract they exercise. This document and its companion
examples directory implement exactly the PR G scope ADR-0005 names:
`docs/architecture/operation-aware-schema-readiness-plan.md`, "PR G —
Compatibility Examples and Test Vectors," lists the illustrative scenario
set (allow matched, deny matched, deny-overrides-allow, no-allow-matched,
no-applicable-bundle, missing context, unknown resource type, unsupported
schema version, invalid policy bundle, trace redaction, gateway enforcement
evidence). Per that section's own framing ("illustrative"), and consistent
with this repository's practice throughout the second wave of publishing
the smallest defensible surface at each step, PR G publishes the subset of
that list current architecture and contracts pin down deterministically —
five canonical scenarios — and documents the rest as deferred (see
[Section 14 of the companion README](../examples/operation-aware/compatibility/README.md#14-deferred-scenarios)).

## 3. Relationship to PR A through PR F

PR G does not modify any contract PR A through PR F published. It consumes
them exactly as published: PR A's `reason-code` format and
`redaction-classification` vocabulary, PR B's evidence-reference contracts,
PR C's `operation-aware-decision-request`, PR D's `policy-bundle` /
`policy-rule` / `policy-condition`, PR E's `evaluation-trace` /
`trace-rule-evidence` / `operation-aware-decision-response`, and PR F's
`audit-evidence` / `gateway-audit-event`. Every fixture in
`examples/operation-aware/compatibility/` is validated against these
contracts' own published field policy, not a parallel or looser
reimplementation of it.

## 4. Normative authority hierarchy

```text
basis-architecture:
  normative authorization and audit semantics (ADR-0001 through ADR-0004)

basis-schemas contracts (PR A-F):
  normative machine-readable shapes

PR G compatibility vectors:
  canonical examples of the current architecture and contracts

future implementation repositories (basis-core, basis-gateway,
basis-console, basis-adapters, basis-identity):
  consume the contracts and vectors
```

PR G sits below the contracts, not beside or above them. It never becomes
an alternate policy engine, and it never introduces a semantic distinction
the architecture documents or the published contracts do not already make.

## 5. Scenario coverage

Five canonical scenarios, each covering a distinct evaluation state named
by ADR-0002 (evaluation semantics) and ADR-0003 (trace/audit evidence):

- **`allow-basic`** — an applicable bundle, a matching ALLOW rule, no
  matching DENY rule: `outcome: allow`.
- **`deny-precedence`** — an applicable bundle where both an ALLOW rule and
  a DENY rule match the same request: `outcome: deny` (ADR-0002 Section 6,
  deny precedence is unconditional).
- **`default-deny`** — an applicable bundle where no ALLOW rule matches and
  no DENY rule exists: `outcome: deny` (ADR-0002 Section 4).
- **`not-applicable`** — no published bundle's scope covers the request at
  all: `outcome: not_applicable`, distinct from `deny` (ADR-0002 Section 5),
  with the gateway separately recording fail-closed `enforcement_action:
  deny` without rewriting the kernel's `not_applicable` result.
- **`invalid-policy-bundle`** — a policy bundle that is shaped correctly but
  violates a cross-rule, bundle-level invariant PR D's own `policy-bundle`
  contract defines (duplicate `rule_id` values across the bundle's `rules`
  array — a uniqueness concern no single rule object's own schema can
  express or enforce): `evaluation_status: failed`, `outcome: null`,
  `failure_reason: policy_validation_failure` (ADR-0002 Section 14, "shaped
  correctly but fails internal consistency validation"), with the gateway
  again recording fail-closed `enforcement_action: deny` without ever
  serializing a kernel `deny`. `invalid_policy_bundle` ("does not conform to
  the required shape") remains a valid, non-deprecated failure category for
  a structurally malformed bundle; it is simply not this scenario's defect.

This is deliberately the smallest scenario set that distinguishes every
evaluation-outcome category ADR-0002 names: a substantive `ALLOW`, a
substantive `DENY` reached two different ways (precedence vs. default), a
scope-coverage gap (`NOT_APPLICABLE`), and an evaluation failure. No
scenario is included merely to exercise an enum value with no distinct
evaluation-state justification — see the companion README's "Deferred
scenarios" section for what was deliberately left out and why.

## 6. Contract-validity testing

Every valid artifact in every scenario is validated, field by field,
against its governing contract's own published `required` / `optional` /
`fields` / pattern / enum policy — reusing the same generic shape-validator
pattern this repository's own per-contract test suites already establish
(see, for example, `tests/test_operation_aware_decision_request_contract.py`'s
`_validate_object` helper), rather than a second, divergent
reimplementation. The intentionally invalid `invalid-policy-bundle.yaml`
fixture is checked to parse as YAML and to fail validation for exactly its
documented reason, not for an incidental one (a missing file, a YAML syntax
error, or an unrelated field).

## 7. Cross-object invariant testing

Beyond single-contract validation, `tests/test_operation_aware_compatibility_vectors.py`
checks the invariants that only become visible once multiple contract
instances are considered together: `request_id`/`correlation_id` alignment
across all six artifacts in a scenario; `bundle_id`/`bundle_version`
alignment across the bundle, trace, response, audit evidence, and gateway
event; trace `rule_id` values existing in, and agreeing in `effect` with,
the paired policy bundle's rules; and the audit evidence and gateway event
preserving the kernel's `evaluation_status`/`outcome`/`failure_reason`
unchanged from the response and trace. Negative mutation tests (small,
in-memory changes to a loaded fixture) confirm the harness actually detects
drift in each of these invariants, rather than only confirming the
fixtures as authored.

## 8. Evaluation-semantic expectations

Each scenario's expected artifacts encode exactly one of ADR-0002's
evaluation-outcome categories, and the test suite asserts that encoding
directly (for example: "the `not-applicable` scenario's trace carries
`bundle_applicability: not_applicable` and empty `rule_evidence`"). This is
an assertion about the *fixture set*, not a re-implementation of
evaluation: the test suite never parses `policy-bundle.yaml`'s `match`
criteria against the paired request and computes anything from them.

## 9. Why schemas do not execute policy

`basis-schemas` publishes shapes; it has never executed policy, and PR G
does not change that. These vectors are static, hand-authored expected
outputs. Whether a real `basis-core` v0.2.0 evaluator actually reaches the
result recorded in `expected-operation-aware-decision-response.yaml` for a
given scenario's request and bundle is a future `basis-core` conformance
question, not something this PR proves.

## 10. Downstream conformance use

A future `basis-core` implementation is expected to be able to run each
scenario's `operation-aware-decision-request.yaml` against its
`policy-bundle.yaml` (or `invalid-policy-bundle.yaml`) and reach the
recorded `expected-operation-aware-decision-response.yaml` /
`expected-evaluation-trace.yaml`. A future `basis-gateway` implementation is
expected to be able to assemble each scenario's
`expected-gateway-audit-event.yaml` from the kernel response/trace and
`expected-audit-evidence.yaml`. Neither is implemented or verified by this
PR; these vectors define the target.

## 11. Determinism

Every identifier, digest, and timestamp across every fixture is fixed and
synthetic — no current-time generation, no random UUIDs, no
filesystem-order dependence, and no network access. Fixtures deliberately
distinguish timestamp fields that the architecture keeps separate (a
request's `evaluation_time`, an audit record's `recorded_at`, and a gateway
event's `timestamp`) rather than reusing one value across all three.

## 12. Compatibility and versioning

These vectors are pinned to the `0.1.0`, `experimental` versions of every
contract they exercise. A future breaking change to any of those contracts
(governed by `docs/contract-governance.md`) is expected to revisit these
vectors as part of that change, the same discipline already applied to
every other compatibility surface in this repository.

## 13. Security

Every value in every fixture is synthetic: no real user, employee,
customer, site, device, or infrastructure identifier, and no real
credential, token, claim, or protocol capture. See the companion README's
"Security and synthetic-data policy" section and the test suite's
prohibited-field/prohibited-value scan.

## 14. Deferred scenarios

Condition-evaluation-error, gateway-local failure, and several of
ADR-0005's other illustrative PR G candidates (missing context, unknown
resource type, unsupported schema version) are deliberately not included
as canonical scenarios in this PR. Each is named, with its specific
reasoning, in the companion README's
["Deferred scenarios"](../examples/operation-aware/compatibility/README.md#14-deferred-scenarios)
section. None of this deferral changes any published contract; it is a
scope decision about which canonical examples to publish now.

## 15. Second-wave completion

With PR G published, every PR named in ADR-0005's recommended publication
order (PR A through PR G) is published. This closes the operation-aware
`basis-schemas` second wave. It does not mean any implementation repository
(`basis-core`, `basis-gateway`, `basis-console`, `basis-adapters`,
`basis-identity`) has implemented the operation-aware model these contracts
and vectors describe — see `docs/migration-plan.md` and
`docs/operation-aware-schema-readiness.md` for the explicit statement that
the next phase of work is `basis-core` deterministic evaluation behavior,
not a claim that it already exists.
