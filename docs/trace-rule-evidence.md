# Trace Rule Evidence Contract

The **trace rule evidence** contract publishes the bounded, deterministic
explanation record for one policy rule considered during one operation-aware
evaluation. It is the first contract of PR E of `basis-architecture`'s
operation-aware schema readiness plan (ADR-0005, "PR E — DecisionResponse and
EvaluationTrace"); see
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md).

- Contract file: [`../schemas/trace-rule-evidence/trace-rule-evidence.yaml`](../schemas/trace-rule-evidence/trace-rule-evidence.yaml)
- Governed by: `basis-architecture`
- Published by: `basis-schemas`
- Version: `0.1.0`
- Lifecycle: `experimental`
- Depends on: [`contract-metadata`](contract-metadata.md), [`policy-rule`](policy-rule.md), [`policy-condition`](policy-condition.md), [`reason-code`](reason-code.md)

## 1. Purpose

ADR-0003 (`docs/architecture/operation-aware-trace-audit-evidence.md`,
Section 5, "Rule Evaluation Evidence") names rule identifier, rule
applicability, condition results, match/no-match/error, effect, reason code,
and redacted explanation as the conceptual per-rule evidence categories a
future evaluation trace needs. This contract publishes that evidence's
*shape*: a reused rule identifier and effect, a closed `rule_result`, bounded
condition-level evidence, and an optional reason code / explanation. It does
not copy the rule's match criteria or conditions, does not embed executable
policy, and does not embed the full request.

## 2. Contract file

[`../schemas/trace-rule-evidence/trace-rule-evidence.yaml`](../schemas/trace-rule-evidence/trace-rule-evidence.yaml)

## 3. Governance

Governed by `basis-architecture`. This contract does not decide rule
matching or condition evaluation; it publishes the evidence shape a future
`basis-core` v0.2.0 evaluator produces once it has already evaluated.

## 4. Version

`0.1.0`

## 5. Lifecycle

`experimental`

## 6. Dependencies

```yaml
depends_on:
  - contract-metadata
  - policy-rule
  - policy-condition
  - reason-code
```

`policy-rule`: `rule_id` and `effect` reuse that contract's identifier
concept and closed allow/deny vocabulary unchanged (parity-tested).
`policy-condition`: `condition_results` entries reuse that contract's
`condition_id` concept. `reason-code`: the optional `reason_code` field (at
both rule and condition level) reuses that contract's format unchanged.
`redaction-classification` is deliberately not declared: no field on this
contract carries displayable evidence detail that needs a per-field
classification — every value here is already a safe identifier, a closed
vocabulary member, or a reason code.

## 7. Canonical shape

A rule-evidence record is a single object. `rule_id`, `effect`, and
`rule_result` are always required. `condition_results`, `reason_code`, and
`explanation` are independently optional. Unknown fields are rejected
(`additional_properties: false`).

| Field | Required | Type | Meaning |
| --- | --- | --- | --- |
| `rule_id` | yes | string (non-empty) | The `policy-rule.rule_id` this evidence explains. |
| `effect` | yes | string (`allow` \| `deny`) | Reused unchanged from `policy-rule`. |
| `rule_result` | yes | string (`matched` \| `not_matched` \| `skipped` \| `error`) | Whether this rule matched — see [Section 9](#9-rule-result-vocabulary). |
| `condition_results` | no | array or null | Bounded condition-level evidence — see [Section 10](#10-condition-level-evidence). |
| `reason_code` | no | string or null | Reused, unchanged `reason-code`-shaped value. |
| `explanation` | no | string or null (non-empty) | Static, non-executable human-readable text. |

## 8. Relationship to PolicyRule

`rule_id` and `effect` are reused from [`policy-rule`](policy-rule.md)
unchanged — this contract does not redefine either. It does **not** copy
`policy-rule`'s `match` criteria or `conditions` array: a rule-evidence
record explains what happened when a rule was considered, not what the rule
itself is authored to do. A consumer that needs the rule's authored shape
dereferences the policy bundle by `rule_id`; this contract does not
duplicate that content into every trace.

## 9. Rule-result vocabulary

`rule_result` is closed to four lowercase values, reproducing ADR-0003
Section 5 ("Match / no-match / error") and Section 4's "skipped rule IDs"
category unchanged:

- `matched` — the rule's match/conditions were satisfied and its effect
  contributed to combining.
- `not_matched` — the rule was a candidate but did not match.
- `skipped` — the rule was not evaluated at all (for example, evaluation
  short-circuited before reaching it).
- `error` — the rule could not be evaluated (for example, a condition raised
  an evaluation error per ADR-0002 Section 9).

Deliberately **not** named `passed` / `failed` / `success`: those words
could be confused with evaluator success or failure, a distinct,
response-level concept published by
[`operation-aware-decision-response`](operation-aware-decision-response.md)'s
`evaluation_status`. This is a first-published vocabulary — ADR-0003 does
not publish it as a schema itself — but every value traces directly to
architecture text, not to invention in this repository.

## 10. Condition-level evidence

`condition_results` is an optional, non-empty-when-present array of bounded
records, each reusing [`policy-condition`](policy-condition.md)'s
`condition_id` concept:

| Field | Required | Type | Meaning |
| --- | --- | --- | --- |
| `condition_id` | yes | string (non-empty) | The `policy-condition.condition_id` this evidence explains. |
| `result` | yes | string (`matched` \| `not_matched` \| `error`) | Reproduces ADR-0002 Section 9's three condition outcomes exactly. |
| `reason_code` | no | string or null | Reused `reason-code`-shaped value. |
| `explanation` | no | string or null (non-empty) | Static, non-executable human-readable text. |

No fourth `skipped` value is published for conditions: ADR-0002 Section 9
names exactly three condition outcomes ("Match / No match / Evaluation
error"), unlike `rule_result`'s four values above. `condition_id` values
must be unique within one rule-evidence record's `condition_results` array
(rule-evidence-level validation). A `condition_results` entry with
`result: error` additionally forces this record's own `rule_result` to
`error` — see [Section 21](#21-cross-field-invariants).
**Never carried**: the condition's `field_path`, `operator`,
`expected_value`, or the raw request value it was compared against
(ADR-0003 Section 5: "Rule evidence should support operator explanations
without exposing raw sensitive context").

## 11. Reason codes

`reason_code` (at both rule level and condition level) is optional and, when
present, must match the [`reason-code`](reason-code.md) contract's
published pattern exactly. No new pattern, no new closed vocabulary, and no
new official codes are introduced by this contract.

## 12. Safe explanations

`explanation` (at both levels) is an optional, non-empty string. Descriptive
rendering only — not authoritative (ADR-0003 Section 11: explanation must
not invent facts and must be derived from trace/evidence). No template
field, no variable-interpolation syntax, no expression-evaluation mechanism,
and no HTML/script-execution mechanism are defined. Must not contain
secrets or credential material.

## 13. Redaction behavior

No `redaction_classification` field is published on this contract. Every
value this contract carries is already bounded to a safe identifier
(`rule_id`, `condition_id`), a closed vocabulary member (`effect`,
`rule_result`, condition `result`), or a reason code — none require a
per-field redaction decision the way a raw claim value or session reference
would. If a future PR justifies carrying evidence that does need
classification, `redaction_classification` can be added additively, reusing
[`redaction-classification`](redaction-classification.md) unchanged.

## 14. Determinism

The same rule evaluated against the same request and policy bundle version
must produce the same rule-evidence record every time (ADR-0003 Section 5).
This contract does not implement that determinism — it is a future
`basis-core` v0.2.0 evaluator responsibility — but publishes a shape with no
field (such as a wall-clock timestamp) that would make deterministic
reproduction structurally impossible.

## 15. What is intentionally omitted

This contract does not publish: the rule's match criteria or conditions
(see [Section 8](#8-relationship-to-policyrule)); a `field_path` /
`operator` / `expected_value` on condition-level evidence (see
[Section 10](#10-condition-level-evidence)); a `redaction_classification`
field (see [Section 13](#13-redaction-behavior)); a bundle identifier (the
containing [`evaluation-trace`](evaluation-trace.md) carries `bundle_id` /
`bundle_version` once, at the trace level, not once per rule); or a
top-level missing/unknown-context observation field — ADR-0003 Section 4
names "missing context observations" and "unknown value observations" as
trace categories, but does not settle a field-level vocabulary for them, so
this contract represents that information only through the bounded
`condition_results.result: error` category plus an optional `reason_code`,
rather than inventing a new, unfinalized vocabulary here.

## 16. Security

This contract defines no `access_token`, `id_token`, `refresh_token`,
`jwt`, `bearer_token`, `authorization_header`, `cookie`, `session_secret`,
`client_secret`, `password`, `private_key`, `api_key`, `credential`,
`raw_claims`, `full_claim_set`, `raw_payload`, `raw_protocol_payload`,
`full_request`, `request_snapshot`, `full_policy`, `policy_document`,
`debug`, `exception`, `stack_trace`, or `traceback` field, anywhere. Any
such field is rejected as unknown — enforced by regression tests.

## 17. Examples

A matching allow rule:

```yaml
rule_id: rule-operator-read-ahu-telemetry
effect: allow
rule_result: matched
reason_code: allow_rule_matched
explanation: Operator role matched an allow rule for read:ahu.
```

A rule with bounded condition-level evidence:

```yaml
rule_id: rule-deny-elevated-risk
effect: deny
rule_result: matched
condition_results:
  - condition_id: cond-risk-score-high
    result: matched
    reason_code: risk_score_above_threshold
reason_code: deny_rule_matched
```

The full contract file carries six valid examples (matching allow, matching
deny, non-matching, bounded condition evidence, skipped, and a condition
evaluation error) and twelve invalid examples covering missing/empty
`rule_id`, an invalid effect, a rejected `not_applicable` effect, an
invalid `rule_result`, malformed condition evidence, duplicate condition
IDs, a malformed reason code, an unknown field, a raw-evidence field, a
debug/stack-trace field, and a condition-error/rule_result inconsistency
(a `condition_results` entry with `result: error` on a record whose
`rule_result` is `matched` — see [Section 21](#21-cross-field-invariants)).

## 18. Compatibility

Purely additive. This contract does not modify any existing published
contract, and no existing contract is made to depend on it. It is not
mandatory anywhere; no implementation repository consumes it yet.

## 19. Scope boundaries

This contract does not implement rule matching, condition evaluation, or
any other evaluation semantics. It does not publish
[`EvaluationTrace`](evaluation-trace.md) or
[`OperationAwareDecisionResponse`](operation-aware-decision-response.md)
(this contract's own consumers), and it does not publish `AuditEvidence` or
`GatewayAuditEvent` — each belongs to a later PR (F) per
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md).

## 20. Why `experimental`?

The lifecycle describes this **published contract**, which is new and
unconsumed by any implementation repository — not a claim that the
underlying conceptual category (ADR-0003 Section 5's rule evidence) is
unsettled. The `rule_result` vocabulary is a `basis-schemas` first
publication of a category ADR-0003 names but does not itself schematize.
It advances to `candidate` once a real consumer (expected: `basis-core`
v0.2.0's evaluator) exercises it, and to `stable` only when
`basis-architecture` confirms the shape as a durable commitment. See
[`contract-governance.md`](contract-governance.md).

## 21. Cross-field invariants

This contract enforces one cross-field invariant beyond the per-field rules
above: if any entry in `condition_results` has `result: error`, this
record's own `rule_result` MUST also be `error`. A condition that could not
be evaluated makes the containing rule's applicability itself unknown, not
merely `not_matched` — ADR-0002 Section 9 requires an evaluation error to
propagate, not be silently downgraded to a negative or positive outcome.
This is enforced both by the YAML contract's `constraints` block and by
dedicated regression tests
(`test_condition_error_with_matched_rule_result_is_invalid`,
`test_condition_error_with_error_rule_result_is_valid`).

`skipped` is a per-rule state only. It is never assigned to
`condition_results.result` (whose vocabulary is three-valued: `matched` /
`not_matched` / `error`), and it does not correspond to a
bundle-applicability outcome — that vocabulary belongs to
[`evaluation-trace`](evaluation-trace.md).
