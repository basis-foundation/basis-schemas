# Operation-Aware Decision Response Contract

The **operation-aware decision response** contract publishes the additive,
richer kernel-output shape a future `basis-core` v0.2.0 will return for one
[`operation-aware-decision-request`](operation-aware-decision-request.md).
It is the third contract of PR E of `basis-architecture`'s operation-aware
schema readiness plan (ADR-0005, "PR E — DecisionResponse and
EvaluationTrace"); see
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md).

- Contract file: [`../schemas/operation-aware-decision-response/operation-aware-decision-response.yaml`](../schemas/operation-aware-decision-response/operation-aware-decision-response.yaml)
- Governed by: `basis-architecture`
- Published by: `basis-schemas`
- Version: `0.1.0`
- Lifecycle: `experimental`
- Depends on: [`contract-metadata`](contract-metadata.md), [`operation-aware-decision-request`](operation-aware-decision-request.md), [`policy-bundle`](policy-bundle.md), [`evaluation-trace`](evaluation-trace.md), [`reason-code`](reason-code.md)

## 1. Purpose

ADR-0001 Section 4 names the conceptual response categories: decision
outcome, failure reason, matched rules, policy identifiers, evaluation
trace, and human-readable explanation. This contract publishes the
authoritative kernel result for one operation-aware decision request: which
request was evaluated, whether evaluation completed, the authorization
outcome when one exists, the evaluated policy bundle, a machine-readable
reason, a safe explanation, and the evaluation trace or a reference to it.

## 2. Contract file

[`../schemas/operation-aware-decision-response/operation-aware-decision-response.yaml`](../schemas/operation-aware-decision-response/operation-aware-decision-response.yaml)

## 3. Governance

Governed by `basis-architecture`. This contract does not decide evaluation
or enforcement behavior; it publishes the response shape ADR-0001,
ADR-0002, and ADR-0003 already named.

## 4. Version

`0.1.0`

## 5. Lifecycle

`experimental`

## 6. Dependencies

```yaml
depends_on:
  - contract-metadata
  - operation-aware-decision-request
  - policy-bundle
  - evaluation-trace
  - reason-code
```

`operation-aware-decision-request`: `request_id` is echoed unchanged.
`policy-bundle`: `bundle_id` / `bundle_version` echo that contract's
identity/version fields unchanged. `evaluation-trace`: the optional
embedded `evaluation_trace` field is evaluation-trace-shaped, referenced
not redefined, and its `outcome` / `evaluation_status` / `failure_reason`
vocabulary is reused unchanged here (parity-tested). `reason-code`: the
optional `reason_code` field reuses that contract's format unchanged.

## 7. Relationship to existing decision-response

**`schemas/decision-response/decision-response.yaml` is unchanged.** Not
renamed, replaced, widened, or reinterpreted: its version, required fields,
optional fields, failure semantics, examples, and validation behavior are
all identical to before this PR (`git diff main --
schemas/decision-response docs/decision-response.md` is empty). It remains
the published v0.1-era response contract, alongside this new,
separate, additive vNext surface.

## 8. Why separate additive contract

The first-wave `decision-response` carries a simpler, already-stable
`outcome` / `reason` / `evaluated_by` / `policy_version` / `failure_reason`
shape in production use by `basis-core` v0.1.0. The operation-aware model
needs a structurally different failure representation (an independent
`evaluation_status` / closed `failure_reason` pair, richer than the
four-value first-wave `failure_reason`) and a trace relationship the
first-wave contract has no concept of. Widening the existing contract in
place would break the compatibility guarantee ADR-0005 Section 7 makes for
v0.1-era responses; publishing a new, additive vNext contract instead
preserves that guarantee exactly, matching the same posture PR C already
established for the request side.

## 9. Canonical shape

A response is a single object. `request_id`, `evaluation_status`,
`outcome`, and `failure_reason` are always-present required keys (`outcome`
and `failure_reason` may hold an explicit `null`). `correlation_id`,
`bundle_id`, `bundle_version`, `trace_id`, `evaluation_trace`,
`reason_code`, and `explanation` are independently optional. Unknown fields
are rejected.

| Field | Required | Type | Meaning |
| --- | --- | --- | --- |
| `request_id` | yes | string (non-empty) | Echoes the request's `request_id`. |
| `correlation_id` | no | string or null | Passthrough of the request's `correlation_id`. |
| `evaluation_status` | yes | string (`completed` \| `failed`) | See [Section 13](#13-evaluation-status). |
| `outcome` | yes (nullable) | string or null | See [Section 11](#11-authorization-outcomes). |
| `failure_reason` | yes (nullable) | string or null | See [Section 14](#14-evaluation-failure). |
| `bundle_id` / `bundle_version` | no | string or null | The evaluated bundle's identity/version — [Section 15](#15-policy-identityversion). |
| `trace_id` / `evaluation_trace` | no | string / object or null | See [Section 20](#20-trace-relationship). |
| `reason_code` / `explanation` | no | string or null | See [Section 18](#18-reason-codes) / [19](#19-safe-explanation). |

## 10. Request identity

`request_id` echoes the `operation-aware-decision-request`'s `request_id`
unchanged, non-empty, required. `correlation_id`, when carried, is passed
through verbatim with no reconciliation behavior implemented.

## 11. Authorization outcomes

`outcome` reuses the existing outcome vocabulary exactly — `allow` / `deny`
/ `not_applicable` — matching `decision-response` and `evaluation-trace`.
No new outcome value is introduced. It is a required key present on every
response, and holds an explicit `null` exactly when `evaluation_status` is
`failed` (see [Section 16](#16-outcomefailure-invariants)).

## 12. Evaluation status

See [Section 13](#13-evaluation-status) below (kept together with
[Section 14](#14-evaluation-failure) since the two are one governed pair).

## 13. Evaluation status

`evaluation_status` is closed to `completed` / `failed`, per ADR-0002
Section 14's distinction between a substantive policy decision and an
evaluation failure.

## 14. Evaluation failure

`failure_reason` is a closed, six-value evaluator-failure vocabulary —
`invalid_request`, `unsupported_schema_version`, `invalid_policy_bundle`,
`policy_validation_failure`, `condition_evaluation_error`,
`internal_evaluation_error` — reproducing ADR-0002 Section 14's
representative evaluation-failure categories exactly, kept in parity with
[`evaluation-trace`](evaluation-trace.md)'s identical field. It is distinct
from, and never conflated with, the open `reason_code` field, and distinct
from the existing first-wave `decision-response`'s own four-value
`failure_reason` (`malformed_request` / `policy_error` / `audit_error` /
`internal_error`) — a v0.1-era enforcement-boundary safe-deny concept this
contract does not modify, reinterpret, or extend. The two vocabularies
happen to share a field name (`failure_reason`) but live on two different,
independently versioned contracts with two different closed value sets;
they are never compared or unified by any contract in this repository.

## 15. Policy identity/version

`bundle_id` / `bundle_version` echo [`policy-bundle`](policy-bundle.md)'s
identity/version fields unchanged: the bundle actually evaluated. Both are
optional and nullable — null or absent when no bundle applied (`outcome:
not_applicable`) or when evaluation failed before a bundle was identified.

## 16. Outcome/failure invariants

**Required invariants**, enforced by this contract's `constraints` and
tested directly:

- `outcome` is one of `allow` / `deny` / `not_applicable` **if and only if**
  `evaluation_status` is `completed`.
- `outcome` is `null` **if and only if** `evaluation_status` is `failed`.
- `failure_reason` is `null` **if and only if** `evaluation_status` is
  `completed`.
- `failure_reason` is one of the six published values **if and only if**
  `evaluation_status` is `failed`.

Consequently: `completed + allow` valid; `completed + deny` valid;
`completed + not_applicable` valid; `failed + allow` **invalid**; `failed +
deny` **invalid**; `failed + not_applicable` **invalid**; `failed + no
outcome` (i.e. `outcome: null`) **valid, and required**. A failed
evaluation can never serialize an authorization outcome of any kind — the
exact invariant ADR-0002 Section 14 requires ("Evaluation errors are not
authorization allows... must not disguise an evaluation failure as a
`DENY` or `NOT_APPLICABLE` decision").

## 17. Expected vs. evaluated policy version

`operation-aware-decision-request.expected_policy_version` is a
request-side expectation stated by the producer; this contract's
`bundle_version` is the policy bundle version actually evaluated. This
contract implements no negotiation, selection, or compatibility-resolution
behavior between the two — it only publishes what was actually evaluated.
No separate `evaluator identity` field (analogous to first-wave
`decision-response`'s `evaluated_by`) is published: `bundle_id` +
`bundle_version` + the trace's rule evidence already identify what
produced the decision, and adding a duplicate identity field would overlap
that meaning without a justified independent use.

## 18. Reason codes

`reason_code` is optional and, when present, must match
[`reason-code`](reason-code.md)'s published pattern exactly. Typically
populated for a completed decision to explain the outcome; this contract
does not require it to be null under failure, and does not require its
presence in either state.

## 19. Safe explanation

`explanation` is an optional, non-empty string. Descriptive rendering
only — not authoritative; `outcome` / `evaluation_status` / `failure_reason`
are authoritative (ADR-0003 Section 11). No template, variable-
interpolation, expression-evaluation, or script-execution mechanism is
defined. Must not contain secrets.

## 20. Trace relationship

The response may carry an optional `trace_id` (a reference), an optional
embedded `evaluation_trace` (the full
[`evaluation-trace`](evaluation-trace.md)-shaped object), both, or neither.
This is the architecture-permitted direction the PR E task description
names as preferred: "response carries an optional embedded
evaluation_trace; `trace_id`, if separately present, must identify that
same trace."

## 21. Response/trace authority

The response is the **authoritative kernel result**; an embedded or
referenced trace is the **explanatory record** that must agree with it.
When `evaluation_trace` is present:

- Its `request_id`, `evaluation_status`, `outcome`, and `failure_reason`
  MUST equal this response's own — these four are always present on both
  contracts (per their respective required-key rules), so this equality is
  unconditional.
- Its `bundle_id` / `bundle_version`, when both carry them, must agree.
- Its `correlation_id`, when both this response and the embedded trace
  carry one, must agree — a one-sided `correlation_id` (present on only
  one of the two) is not a mismatch.
- Its `reason_code`, when both this response and the embedded trace carry
  a non-null value, must agree — a one-sided `reason_code` is not a
  mismatch, since each contract's `reason_code` is independently optional.
- When both `trace_id` and `evaluation_trace` are present,
  `evaluation_trace.trace_id` must equal `trace_id`.

## 22. Cross-field consistency

The equalities in [Section 21](#21-responsetrace-authority) are
**documented invariants this static YAML contract cannot itself
enforce** — JSON-Schema-style static notation has no cross-object
value-equality primitive. This repository's test suite validates them
directly against the contract's own published examples (see
[`../tests/test_operation_aware_decision_response_contract.py`](../tests/test_operation_aware_decision_response_contract.py)),
and a future `basis-core` runtime is expected to enforce them at
evaluation time.

## 23. Missing/unknown context

Represented at the trace/rule-evidence level — see
[`evaluation-trace.md`](evaluation-trace.md), Section 23. This contract
adds no separate missing-context field of its own.

## 24. Gateway enforcement boundary

This contract does not decide fail-open/fail-closed behavior when
`evaluation_status` is `failed` — that is a `basis-gateway`/deployment
decision (ADR-0002 Section 14: "Gateways should fail closed when the
kernel cannot produce a valid allow decision... this is a `basis-gateway`
enforcement responsibility"). No `enforcement_result`, `http_status`,
`response_status`, `route`, or similar gateway-runtime field is published.

## 25. Security/redaction

This contract defines no `access_token`, `id_token`, `refresh_token`,
`jwt`, `bearer_token`, `authorization_header`, `cookie`, `session_secret`,
`client_secret`, `password`, `private_key`, `api_key`, `credential`,
`raw_claims`, `full_claim_set`, `raw_payload`, `raw_protocol_payload`,
`full_request`, `request_snapshot`, `full_policy`, `policy_document`,
`enforcement_result`, `http_status`, `response_status`,
`gateway_enforcement`, `event_id`, or `event_type` field, anywhere. Any
such field is rejected as unknown — enforced by regression tests. No
`redaction_classification` field is published on the response itself — see
[`evaluation-trace.md`](evaluation-trace.md), Section 22, for the same
reasoning; any embedded `evaluation_trace`'s own bounded fields carry no
raw value needing classification.

## 26. Examples

A completed allow, with an embedded, consistent trace:

```yaml
request_id: oadr-0002-0000-0000-000000000002
evaluation_status: completed
outcome: allow
failure_reason: null
bundle_id: baseline-read-only-telemetry
bundle_version: "1.0.0"
trace_id: trace-0001-0000-0000-000000000001
evaluation_trace:
  trace_id: trace-0001-0000-0000-000000000001
  request_id: oadr-0002-0000-0000-000000000002
  evaluation_status: completed
  outcome: allow
  bundle_applicability: applicable
  bundle_id: baseline-read-only-telemetry
  bundle_version: "1.0.0"
  rule_evidence:
    - rule_id: rule-operator-read-ahu-telemetry
      effect: allow
      rule_result: matched
      reason_code: allow_rule_matched
reason_code: allow_rule_matched
```

A failed evaluation:

```yaml
request_id: oadr-1099-0000-0000-000000000099
evaluation_status: failed
outcome: null
failure_reason: unsupported_schema_version
```

The full contract file carries five valid examples (completed allow with
embedded trace, completed deny referenced by `trace_id` only, completed
not-applicable, a failed evaluation, and a minimal response with only the
four required keys) and fifteen invalid examples covering a missing
`request_id`, an invalid outcome, a malformed `evaluation_status`, a failed
response with `outcome: allow`, a failed response with `failure_reason:
null`, a completed response with a non-null `failure_reason`, a malformed
reason code, a malformed `bundle_version`, a malformed embedded trace, a
response/trace `request_id` mismatch, an unknown field, a raw-evidence
field, a gateway-enforcement field, a response/trace `correlation_id`
mismatch, a response/trace `failure_reason` mismatch, and a response/trace
`reason_code` mismatch (both non-null but disagreeing) — see
[Section 21](#21-responsetrace-authority).

## 27. Compatibility

Purely additive. No existing contract (`decision-request`,
`decision-response`, `audit-event`, `action-string`, `resource-identifier`,
`contract-metadata`, `redaction-classification`, `reason-code`,
`identity-evidence-reference`, `adapter-evidence-reference`,
`operation-aware-decision-request`, `policy-condition`, `policy-rule`,
`policy-bundle`, `trace-rule-evidence`, `evaluation-trace`) changed shape,
required fields, optional fields, examples, or validation behavior, and
none was made to depend on this new contract. This contract is not
mandatory anywhere; no implementation repository consumes it yet.

## 28. Scope boundaries

This contract does not implement evaluation, enforcement, or audit
persistence. It does not publish `AuditEvidence` or `GatewayAuditEvent` —
each belongs to a later PR (F) per
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md).

## 29. Why `experimental`?

The lifecycle describes this **published contract**, which is new and
unconsumed by any implementation repository — not a claim that the
underlying conceptual category is unsettled. The `outcome` /
`evaluation_status` / `failure_reason` separation, the trace-relationship
model, and the field names chosen throughout are `basis-schemas`
publication decisions, made because ADR-0001/ADR-0002/ADR-0003 name the
requirements ("preserve the distinction between policy decision and
evaluation failure," "make evaluation results explainable") without
choosing exact field names or a final response shape. It advances to
`candidate` once a real consumer (expected: `basis-core` v0.2.0's
evaluator, and `basis-gateway`'s enforcement path) exercises it, and to
`stable` only when `basis-architecture` confirms the shape as a durable
commitment. See [`contract-governance.md`](contract-governance.md).
