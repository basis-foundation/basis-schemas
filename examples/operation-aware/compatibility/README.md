# Operation-Aware Compatibility Vectors

This directory holds the canonical compatibility examples and test vectors
published by PR G of `basis-architecture`'s operation-aware schema readiness
plan (ADR-0005,
[`docs/architecture/operation-aware-schema-readiness-plan.md`](../../../docs/operation-aware-schema-readiness.md)),
the final planned PR in the operation-aware `basis-schemas` second wave. See
also [`docs/operation-aware-compatibility-vectors.md`](../../../docs/operation-aware-compatibility-vectors.md)
for the conceptual overview; this file is the practical directory guide.

## 1. Purpose

PR A through PR F published the operation-aware contracts individually:
shared metadata, evidence references, the request, the policy bundle/rule
model, the response/trace model, and the audit model. None of those PRs
showed how the contracts compose into a complete, coherent authorization
scenario. This directory publishes canonical, cross-contract examples that
do — so that future `basis-core`, `basis-gateway`, `basis-console`,
`basis-adapters`, and `basis-identity` implementations have a shared,
machine-validated target for how these contracts are expected to fit
together.

## 2. Authority model

```text
basis-architecture:
  normative authorization and audit semantics

basis-schemas contracts (PR A-F):
  normative machine-readable shapes

PR G compatibility vectors (this directory):
  canonical examples of the current architecture and contracts

future implementation repositories:
  consume the contracts and vectors
```

These vectors do not define new authorization semantics. Every scenario is
derived from `basis-architecture`'s operation-aware authorization model
(ADR-0001), evaluation semantics (ADR-0002), trace/audit evidence model
(ADR-0003), and policy/rule model (ADR-0004), and from the contracts PR A
through PR F already published. Where a plausible scenario could not be
derived confidently from that material, it was deferred rather than
invented — see [Section 14, "Deferred scenarios."](#14-deferred-scenarios)

## 3. Directory structure

```text
examples/operation-aware/compatibility/
  README.md                                   this file

  allow-basic/
    operation-aware-decision-request.yaml
    policy-bundle.yaml
    expected-evaluation-trace.yaml
    expected-operation-aware-decision-response.yaml
    expected-audit-evidence.yaml
    expected-gateway-audit-event.yaml

  deny-precedence/          (same six files)
  default-deny/             (same six files)
  not-applicable/           (same six files)

  invalid-policy-bundle/
    operation-aware-decision-request.yaml
    invalid-policy-bundle.yaml                 (intentionally invalid)
    expected-evaluation-trace.yaml
    expected-operation-aware-decision-response.yaml
    expected-audit-evidence.yaml
    expected-gateway-audit-event.yaml
```

This directory structure is the vector index. It is deliberately **not** a
governed schema, is **not** tracked in any `basis_schemas` contract-tracking
tuple, and is **not** added to `contract-metadata`. It is a deterministic
filesystem convention — one directory per scenario, one file per artifact —
that both humans and `tests/test_operation_aware_compatibility_vectors.py`
read directly. No index manifest file is introduced.

## 4. Artifact naming

Every file name matches the `basis_schemas` contract it is an instance of,
in kebab-case, prefixed with `expected-` for artifacts that describe an
*outcome* of evaluation (the trace, response, audit evidence, and gateway
event) rather than an *input* to it (the request and the policy bundle).
`invalid-policy-bundle/invalid-policy-bundle.yaml` is named for what it is
— an intentionally invalid policy bundle — rather than `policy-bundle.yaml`,
so it is never mistaken for a valid fixture by a casual reader or a
naive glob.

## 5. Scenario matrix

| Scenario                | `evaluation_status` | `outcome`       | `bundle_applicability` | gateway `enforcement_action` |
|--------------------------|----------------------|-----------------|--------------------------|-------------------------------|
| `allow-basic`            | completed            | allow           | applicable               | allow                          |
| `deny-precedence`        | completed            | deny            | applicable               | deny                           |
| `default-deny`           | completed            | deny            | applicable               | deny                           |
| `not-applicable`         | completed            | not_applicable  | not_applicable            | deny (fail-closed)             |
| `invalid-policy-bundle`  | failed               | null            | null                     | deny (fail-closed)             |

Every row above covers a distinct, architecture-grounded evaluation state.
No two scenarios are distinguishable only by cosmetic differences in the
example data.

## 6. Contract mapping

Each scenario directory carries one instance of six contracts:

- `operation-aware-decision-request.yaml` → `operation-aware-decision-request` (PR C)
- `policy-bundle.yaml` / `invalid-policy-bundle.yaml` → `policy-bundle` (PR D), whose `rules` are `policy-rule`-shaped (PR D)
- `expected-evaluation-trace.yaml` → `evaluation-trace` (PR E), whose `rule_evidence` entries are `trace-rule-evidence`-shaped (PR E)
- `expected-operation-aware-decision-response.yaml` → `operation-aware-decision-response` (PR E)
- `expected-audit-evidence.yaml` → `audit-evidence` (PR F)
- `expected-gateway-audit-event.yaml` → `gateway-audit-event` (PR F)

`allow-basic`'s request and audit evidence additionally carry an
`identity_evidence_reference` and `adapter_evidence_reference` (PR B), and
every `reason_code` value used across every scenario is a structurally
valid `reason-code` (PR A) token, reusing `no_applicable_bundle` and other
codes already used in PR A through PR F's own published `examples:` blocks
rather than inventing new ones. The `invalid-policy-bundle` scenario carries
no `reason_code` at all: no approved reason-code equivalent for a
`policy_validation_failure`-category result is published in this
repository's governed reason-code vocabulary (see
[`docs/reason-code.md`](../../../docs/reason-code.md)), and this PR does
not invent one.

## 7. Allow scenario (`allow-basic`)

An applicable (globally-scoped) bundle, one matching ALLOW rule, no
matching DENY rule: `outcome: allow`. Demonstrates the ordinary path
end-to-end, including PR B evidence-reference integration and gateway
enforcement agreeing with the kernel outcome.

## 8. Deny-precedence scenario (`deny-precedence`)

One ALLOW rule and one DENY rule both match the same request in the same
applicable bundle. Per ADR-0002 Section 6, deny precedence is
unconditional: the final outcome is `deny` even though an allow rule also
matched. The trace records both matched rules; array order in
`rule_evidence` is never authorization precedence (see
[Section 9](#9-semantic-expectations)).

## 9. Semantic expectations

- **Default-deny scenario (`default-deny`):** the bundle is applicable, but
  its one rule (scoped to a different subject role) does not match — no
  allow rule matched, and there is no deny rule at all. Per ADR-0002
  Section 4, this is `deny`, not `not_applicable`: default deny presumes an
  applicable bundle that grants nothing; `NOT_APPLICABLE` presumes no
  applicable bundle in the first place.
- **Not-applicable scenario (`not-applicable`):** the one published bundle
  scopes itself to `hvac` resources; the request targets a `chiller`
  resource, which that scope does not cover at all. Per ADR-0002 Section 5,
  `bundle_applicability` and `outcome` are both `not_applicable`, and
  `rule_evidence` is empty — no rule was ever a candidate. The gateway
  event separately records `enforcement_action: deny` (fail-closed
  enforcement on a kernel result that was not itself a policy deny); the
  kernel `outcome: not_applicable` is never rewritten as `deny` anywhere in
  this scenario's artifacts.
- **Invalid-policy scenario (`invalid-policy-bundle`):** `invalid-policy-bundle.yaml`
  intentionally fails `policy-bundle`'s own published field policy (duplicate
  `rule_id` values — the same invalid case that contract's own `examples:`
  block already tests). The bundle is structurally well formed — every rule
  and every top-level field is individually valid — but it violates a
  cross-rule, bundle-level invariant (`rule_id` uniqueness across the
  `rules` array) that no single rule object's own schema can express or
  enforce. Per ADR-0002 Section 14, that makes this a
  `policy_validation_failure` ("shaped correctly but fails internal
  consistency validation"), not an `invalid_policy_bundle` ("does not
  conform to the required shape"), so the response/trace/audit/gateway-event
  artifacts all carry `failure_reason: policy_validation_failure`.
  `invalid_policy_bundle` remains a valid failure category — it applies to a
  bundle that is malformed at the shape level (a missing required field, a
  malformed rule, an invalid enum value, and similar), which is not what this
  scenario's fixture demonstrates. `evaluation_status: failed` and
  `outcome: null` together, never `deny` — an evaluation failure is not a
  policy decision (ADR-0002 Section 14). The gateway event separately
  records `enforcement_action: deny` (fail-closed on a kernel failure).

## 10. Structural validation

`tests/test_operation_aware_compatibility_vectors.py` validates every
`operation-aware-decision-request.yaml`, `policy-bundle.yaml`,
`expected-evaluation-trace.yaml`,
`expected-operation-aware-decision-response.yaml`,
`expected-audit-evidence.yaml`, and `expected-gateway-audit-event.yaml`
against its governing contract's own published field policy (reusing the
same validator pattern this repository's own per-contract test suites
already use — no second, divergent validator implementation). The
intentionally-invalid `invalid-policy-bundle.yaml` is checked to parse as
YAML and to fail policy-bundle's own validation for exactly the documented
reason (duplicate `rule_id`), not merely because a file is missing or
malformed.

## 11. Cross-artifact validation

Beyond per-file contract validation, the test suite checks that the six
artifacts in each scenario directory agree with each other wherever the
architecture requires it: `request_id` (and `correlation_id`, when carried)
line up across every artifact; `bundle_id` / `bundle_version` line up
across the bundle, trace, response, audit evidence, and gateway event
wherever each carries them; the response and trace agree on
`evaluation_status` / `outcome` / `failure_reason` / `reason_code`; the
trace's `rule_evidence` entries reference `rule_id` values that actually
exist in the paired policy bundle, with matching `effect`; the audit
evidence and gateway event preserve the kernel's `evaluation_status` /
`outcome` / `failure_reason` unchanged; and the gateway event's
`audit_evidence_id` references the scenario's own audit-evidence record.
Rule order is never treated as evaluation precedence.

## 12. What `basis-schemas` does not execute

These vectors are static, hand-authored YAML files checked against
published contract shapes. Nothing in this repository parses a policy
bundle's `match`/`conditions` against a request and computes an outcome —
that is `basis-core`'s future v0.2.0 responsibility. This directory and its
tests do not implement, approximate, or stand in for policy evaluation,
rule matching, condition evaluation, gateway enforcement, or audit
persistence.

## 13. How future implementations should consume these vectors

- **`basis-core`:** given each scenario's `operation-aware-decision-request.yaml`
  and `policy-bundle.yaml` (or `invalid-policy-bundle.yaml`) as evaluator
  input, a conformant v0.2.0 kernel is expected to produce a response and
  trace matching `expected-operation-aware-decision-response.yaml` and
  `expected-evaluation-trace.yaml` respectively.
- **`basis-gateway`:** given each scenario's kernel response/trace and the
  associated `expected-audit-evidence.yaml`, a conformant gateway is
  expected to assemble a `gateway-audit-event` matching
  `expected-gateway-audit-event.yaml`, including the fail-closed
  `enforcement_action: deny` behavior on `not-applicable` and
  `invalid-policy-bundle`.
- **`basis-console`:** may use these vectors as sample data for operator-
  mode and training-mode explanation rendering, clearly distinguished from
  live decisions, consistent with ADR-0003 Section 16.

None of the above is implemented by this PR, and no cross-repository
conformance is claimed to be green today. These vectors are the target
future implementations are expected to conform to.

## 14. Deferred scenarios

- **Condition-evaluation-error:** deliberately not included. `PR E`
  publishes `condition_evaluation_error` as a failure category, but this PR
  does not invent a deterministic input-to-error mapping for it (unsupported
  operator behavior, runtime type coercion, and similar are all
  architecture-unsettled per ADR-0002 Section 9's open questions). Deferred
  to future implementation-derived compatibility work.
- **Gateway-local failure:** deliberately not included as a canonical
  scenario, despite `gateway-audit-event.yaml`'s own `examples:` block
  already illustrating one (`audit_assembly_failure`). Adding it here would
  not exercise a new *kernel* evaluation state (it pairs with an ordinary
  allow decision) and the gateway-local failure taxonomy is explicitly
  named as pending a richer classification (ADR-0003 Section 17). Deferred
  to future implementation-derived compatibility work.
- **Missing optional/required context, unknown resource type, unsupported
  schema version:** named in ADR-0005's PR G scope as illustrative
  candidates, but each would either duplicate an evaluation state already
  covered above (missing optional context behaves like `default-deny` or
  `not-applicable` depending on the rule) or require inventing a
  deterministic input this repository's published contracts do not yet
  pin down precisely enough to fixture confidently. Deferred.

## 15. Versioning and compatibility expectations

Every fixture in this directory is expressed against the `0.1.0`,
`experimental` contract versions PR A through PR F published. If any of
those contracts changes shape in a future revision, these vectors are
expected to be revisited alongside that change — the same compatibility
discipline `docs/contract-governance.md` already requires for the
contracts themselves.

## 16. Security and synthetic-data policy

All identifiers, digests, timestamps, and evidence values in this directory
are synthetic and deterministic: no real user, employee, customer, site,
device, or infrastructure identifier; no real credential, token, claim set,
or protocol capture. Digest values are illustrative lowercase hexadecimal
strings, not real cryptographic digests of real evidence. See
`tests/test_operation_aware_compatibility_vectors.py`'s security checks for
the enforced prohibited-field and prohibited-value list.

## 17. Packaging and downstream consumption

This directory is repository-distributed only. `pyproject.toml` packages
only `src/basis_schemas` in the built wheel; `examples/` (like `schemas/`
and `docs/`) is not included in the installed Python package. A consumer
that only `pip install`s `basis-schemas` does not receive these vectors on
disk.

Downstream repositories consume the canonical vectors from a pinned
`basis-schemas` source release, repository tag, submodule, vendored test
fixture, or future approved distribution mechanism. This PR does not
mandate one transport mechanism, does not require consumers to scrape the
moving `main` branch, and does not add these vectors to the wheel merely to
make consumption more convenient — doing so would be a packaging change
outside this PR's scope and is left to future release-engineering decisions
if repository policy ever requires it.
