# Policy Condition Contract

The **policy condition** contract publishes the deterministic, data-only
predicate shape a future `basis-core` v0.2.0 policy validator and evaluator
will use as part of a policy rule. It is the first contract of PR D of
`basis-architecture`'s operation-aware schema readiness plan (ADR-0005,
"PR D — Policy Bundle and Rule Contracts"); see
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md).

- Contract file: [`../schemas/policy-condition/policy-condition.yaml`](../schemas/policy-condition/policy-condition.yaml)
- Governed by: `basis-architecture`
- Published by: `basis-schemas`
- Version: `0.1.0`
- Lifecycle: `experimental`
- Depends on: [`contract-metadata`](contract-metadata.md)

## 1. Purpose

A policy rule's `match` criteria (published by
[`policy-rule`](policy-rule.md)) can express common, structured operation-aware
selectors — role, action, resource type, site, and the rest — but not every
policy need reduces to a structured selector list. ADR-0004
(`docs/architecture/operation-aware-policy-rule-model.md`, Section 7,
"Conditions") names a **condition** as the mechanism a rule uses for
deterministic tests beyond what its match criteria alone can express. This
contract publishes that condition's *shape*: a stable identifier, a validated
dotted reference into the operation-aware request context, an open operator
identifier, and a data-only expected value.

## 2. Contract file

[`../schemas/policy-condition/policy-condition.yaml`](../schemas/policy-condition/policy-condition.yaml)

## 3. Governance

Governed by `basis-architecture`. This contract does not decide condition
evaluation semantics; it publishes the shape ADR-0004 Section 7 already named
(explicit, deterministic, no external data fetching, no side effects,
distinguishes match/no-match/error, no silent type coercion, no
missing-context-as-truthy).

## 4. Version

`0.1.0`

## 5. Lifecycle

`experimental`

## 6. Dependencies

```yaml
depends_on:
  - contract-metadata
```

`policy-condition` does **not** declare a dependency on
`operation-aware-decision-request`. Although a condition's `field_path`
conceptually references categories that contract publishes, this contract
does not formally validate a field path against
`operation-aware-decision-request`'s field list — it validates only that a
field path is a structurally well-formed dotted identifier (see
[Section 9](#9-request-field-paths)). A dependency is declared only when a
field's own validation directly uses another contract's published rule; this
one does not.

## 7. Canonical shape

A condition is a single object. All four fields are required. Unknown fields
are rejected (`additional_properties: false`).

| Field | Required | Type | Meaning |
| --- | --- | --- | --- |
| `condition_id` | yes | string (non-empty) | Identifies this condition, stable within its containing rule. |
| `field_path` | yes | string (validated dotted path) | Which part of the operation-aware request this condition evaluates. |
| `operator` | yes | string (validated, open identifier) | The comparison this condition expresses. Not a closed enum. |
| `expected_value` | yes | string / number / boolean / null / homogeneous array of those scalars | The data-only value compared against. |

All four fields are required because a condition missing any one of them is
not a usable predicate: without `condition_id` it cannot be referenced
stably from trace, audit, or its containing rule's own duplicate-ID check;
without `field_path`, `operator`, or `expected_value` it is not a complete
test. There are no optional fields on this contract — no
priority/lifecycle/provenance metadata is published at the condition level,
consistent with keeping this the smallest useful shape.

## 8. Condition identifiers

`condition_id` must be a non-empty string, stable within its containing rule.
No UUID requirement: a short, stable, human-readable token (for example
`cond-risk-score-high`) is preferred, because — like `policy-rule`'s
`rule_id` (ADR-0004 Section 4) — a condition identifier that changes across
bundle revisions without an explicit rename breaks trace, audit, and
compatibility-test consumers that referenced it. `condition_id` must not
carry a timestamp or other mutable information.

**Uniqueness is rule-level validation, not schema-level validation.** A
standalone condition object has no sibling conditions to compare itself
against, so this contract cannot enforce that `condition_id` is unique on its
own. [`policy-rule`](policy-rule.md) enforces that condition IDs are unique
within a single rule's `conditions` array; see that document's validation
section.

## 9. Request field paths

`field_path` is a validated **dotted identifier path** — lowercase segments
separated by single dots, matching
`^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$` — identifying which part of the
operation-aware request (published by
[`operation-aware-decision-request`](operation-aware-decision-request.md))
this condition evaluates. Illustrative examples: `subject_id`,
`subject_attrs.clearance`, `location.site_id`, `device.device_class`,
`protocol_context.protocol`, `risk_context.score`, `evaluation_time`.

**This contract does not finalize a closed request-field vocabulary.** It
validates only that a field path is *structurally* well-formed — no method
calls, no array-indexing syntax (`subject_roles[0]`), no function calls
(`subject_attrs.get('clearance')`), and no executable expression of any
kind. A structurally valid field path is **not** a claim that `basis-core`
currently supports evaluating it: an unsupported (but well-formed) field
path is rejected during future policy validation, not silently evaluated,
and not rejected by this schema. See
[Section 12](#12-structural-validation-vs-runtime-support).

## 10. Operator identifiers

`operator` is a validated, extensible, machine-readable identifier —
lowercase snake_case, matching `^[a-z][a-z0-9]*(_[a-z0-9]+)*$` (the same
token shape the [`reason-code`](reason-code.md) contract already publishes,
reused here for convenience — operator and reason code remain distinct
concepts). `illustrative_operators` in the contract body lists non-final
examples only: `equals`, `not_equals`, `in`, `greater_than`, `less_than`,
`exists`.

## 11. Why the operator vocabulary remains open

ADR-0004 Section 7 states explicitly: "This document does not define a full
operator language ... That is deferred to the eventual policy format
design." Publishing a closed operator enum now would prematurely finalize a
decision ADR-0004 deliberately left open. This contract therefore accepts
**any** structurally valid future operator and rejects only malformed
identifiers (uppercase, a leading digit, a colon, a hyphen, or a
leading/trailing/doubled underscore). Which operators a given `field_path`
and `expected_value` combination actually supports is determined by future
`basis-core` policy validation, not by this contract.

## 12. Structural validation vs. runtime support

This is the central design distinction of this contract, restated for
emphasis: a structurally valid `field_path` or `operator` is a claim about
*shape*, not about *support*. `basis-core`'s future policy validator is
free to reject a well-formed-but-unsupported field path or operator during
policy validation (a bundle-validation concern, per
[`policy-bundle.md`](policy-bundle.md)); this schema never makes that
determination, and never silently evaluates an unsupported value as though
it were supported — there is no evaluation implemented here at all.

## 13. Expected-value representation

`expected_value` is the smallest safe, data-only representation this
contract can express: a string, a number, a boolean, an explicit `null`, or
a homogeneous array of string/number/boolean scalars (see
`expected_value_scalar_types` / `expected_value_array_item_types` in the
contract body). Nested objects, nested arrays, heterogeneous arrays,
functions, code, templates, arbitrary executable expressions, and external
data-source or network references are **not** supported.

`expected_value` is **required** — the key must always be present — but its
value may legitimately be the null literal itself (for example, an explicit
equals-null comparison, or a value an illustrative `exists`-style operator
does not otherwise need). This differs from this repository's usual
required+nullable pairing, where a nullable type marks "absent" (see, for
example, `operation-aware-decision-request`'s many `type: [string, "null"],
required: false` fields): here `null` is itself a meaningful data value, not
an absence marker. A condition entirely missing the `expected_value` key is
invalid; a condition whose `expected_value` is explicitly `null` is valid.

**Homogeneous-array limitation.** Static YAML/JSON-Schema notation cannot
cleanly express "an array whose items are all the same one of string,
number, or boolean" as a single declarative rule. This contract documents
the constraint in prose (`expected_value_array_item_types`) and its
companion test suite (`tests/test_policy_condition_contract.py`) enforces it
programmatically — this is the smallest truthful representation available
given this repository's existing tooling, not a claim that the YAML shape
alone enforces homogeneity.

## 14. Determinism requirements

ADR-0004 Section 7 requires that a condition be explicit, deterministic, and
side-effect-free, and that its evaluation distinguish match / no-match /
error without treating missing context as truthy or silently coercing
incompatible types. This contract satisfies those requirements **by
construction**, not by implementing them: because `expected_value` is
restricted to inert, data-only scalars and homogeneous arrays, and because
there is no operator-execution mechanism defined anywhere on this contract,
there is no non-deterministic or side-effecting behavior *possible* within
this shape. The determinism requirement is therefore a property of the data
model, not a runtime guarantee this contract implements.

## 15. No external data fetching

A condition never carries a URL, a query, a lookup reference, or any other
mechanism that could cause a future evaluator to fetch additional context at
evaluation time. `field_path` references only context the operation-aware
request itself may carry; there is no field on this contract through which a
condition could name an external data source.

## 16. No executable expressions

This contract defines no `script`, `code`, `executable`, `command`,
`shell`, `python`, `javascript`, `rego`, `cedar`, `cel`, `wasm`, `sql`,
`template`, or `expression` field, at any nesting level (there is only one
level: this contract has no nested sub-shapes). Any such field is rejected
as unknown. See the top-level CRITICAL DESIGN BOUNDARY comment in
[`../schemas/policy-condition/policy-condition.yaml`](../schemas/policy-condition/policy-condition.yaml)
for the full non-goal list: this is a structured policy DATA model, never a
policy language.

## 17. Examples

A subject-attribute equality condition:

```yaml
condition_id: cond-clearance-equals-level-2
field_path: subject_attrs.clearance
operator: equals
expected_value: level-2
```

A numeric risk-score condition:

```yaml
condition_id: cond-risk-score-above-threshold
field_path: risk_context.score
operator: greater_than
expected_value: 0.5
```

A structurally valid, illustrative, explicitly non-final future operator:

```yaml
condition_id: cond-device-class-future-operator
field_path: device.device_class
operator: matches_future_pattern
expected_value: controller
```

The full contract file carries five valid examples and thirteen invalid
examples covering missing/empty `condition_id`, missing/malformed
`field_path`, missing/malformed `operator`, missing `expected_value`,
unsupported value shapes (a nested object, a heterogeneous array), an
unknown field, and a rejected `script` field. All examples use clearly
synthetic values.

## 18. Compatibility

Purely additive. This contract does not modify any existing published
contract, and no existing contract is made to depend on it. It is not
mandatory anywhere; no implementation repository consumes it yet.

## 19. Scope boundaries

This contract does not implement, and does not define: condition
evaluation, match/no-match/error determination, operator support
determination, field-path support determination, external context
retrieval, a policy language, or an evaluation engine. It does not choose
Rego, Cedar, CEL, Python, JavaScript, SQL, WASM, a custom DSL, or a
templated expression language. It does not publish `PolicyRule` or
`PolicyBundle` (see [`policy-rule.md`](policy-rule.md) and
[`policy-bundle.md`](policy-bundle.md)), and it does not publish an
operation-aware `DecisionResponse`, `EvaluationTrace`,
`TraceRuleEvidence`, `AuditEvidence`, or `GatewayAuditEvent` — each belongs
to a later PR (E through G) per
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md).

## 20. Why `experimental`?

The lifecycle describes this **published contract**, which is new and
unconsumed by any implementation repository — not a claim that the
underlying conceptual category (ADR-0004 Section 7's condition concept) is
unsettled. The operator-vocabulary openness and the field-path structural
(not semantic) validation are `basis-schemas` publication decisions, made
because ADR-0004 deliberately deferred both; early feedback from a real
future consumer (expected: `basis-core` v0.2.0's policy validator) may
still refine field-level details, even though the underlying architecture
category is stable. It advances to `candidate` once such a consumer
exercises it, and to `stable` only when `basis-architecture` confirms the
shape as a durable commitment. See
[`contract-governance.md`](contract-governance.md).
