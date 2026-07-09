# Evaluation Trace Contract

The **evaluation trace** contract publishes the deterministic, bounded
explanation of one kernel authorization evaluation. It is the second
contract of PR E of `basis-architecture`'s operation-aware schema readiness
plan (ADR-0005, "PR E — DecisionResponse and EvaluationTrace"); see
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md).

- Contract file: [`../schemas/evaluation-trace/evaluation-trace.yaml`](../schemas/evaluation-trace/evaluation-trace.yaml)
- Governed by: `basis-architecture`
- Published by: `basis-schemas`
- Version: `0.1.0`
- Lifecycle: `experimental`
- Depends on: [`contract-metadata`](contract-metadata.md), [`operation-aware-decision-request`](operation-aware-decision-request.md), [`policy-bundle`](policy-bundle.md), [`trace-rule-evidence`](trace-rule-evidence.md), [`reason-code`](reason-code.md)

## 1. Purpose

ADR-0003 (`docs/architecture/operation-aware-trace-audit-evidence.md`,
Section 2) defines: "Evaluation trace — the kernel-produced explanation of
how policy evaluation reached an outcome." This contract publishes that
explanation's *shape*: trace and request identity, the applicable policy
bundle (when one applied), a closed authorization outcome kept structurally
independent of a closed evaluation status, bounded rule evidence, and an
optional reason code / explanation.

## 2. Contract file

[`../schemas/evaluation-trace/evaluation-trace.yaml`](../schemas/evaluation-trace/evaluation-trace.yaml)

## 3. Governance

Governed by `basis-architecture`. This contract does not decide evaluation
semantics; it publishes the shape ADR-0002 and ADR-0003 already named.

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
  - trace-rule-evidence
  - reason-code
```

`operation-aware-decision-request`: `request_id` / `correlation_id` echo
that contract's identifiers; the full request is never copied.
`policy-bundle`: `bundle_id` / `bundle_version` echo that contract's
identity/version fields unchanged. `trace-rule-evidence`: `rule_evidence` is
a collection of trace-rule-evidence-shaped values, referenced not
redefined. `reason-code`: the optional `reason_code` field reuses that
contract's format unchanged. `redaction-classification` is deliberately not
declared — see [`trace-rule-evidence.md`](trace-rule-evidence.md),
Section 13, for the same reasoning applied here.

## 7. Canonical shape

A trace is a single object. `trace_id`, `request_id`, `evaluation_status`,
`outcome`, `bundle_applicability`, and `rule_evidence` are always-present
required keys (`outcome` may hold an explicit `null`). `correlation_id`,
`bundle_id`, `bundle_version`, `failure_reason`, `reason_code`, and
`explanation` are independently optional. Unknown fields are rejected.

| Field | Required | Type | Meaning |
| --- | --- | --- | --- |
| `trace_id` | yes | string (non-empty) | Stable identifier for this trace. |
| `request_id` | yes | string (non-empty) | The evaluated request's `request_id`. |
| `correlation_id` | no | string or null | Passthrough of the request's `correlation_id`. |
| `evaluation_status` | yes | string (`completed` \| `failed`) | See [Section 13](#13-evaluation-statusfailure). |
| `outcome` | yes (nullable) | string or null | See [Section 12](#12-authorization-outcome). |
| `bundle_applicability` | yes (nullable) | string or null | See [Section 11](#11-bundle-applicability). |
| `bundle_id` / `bundle_version` | no | string or null | The applicable bundle's identity/version — see [Section 10](#10-policy-bundle-association). |
| `failure_reason` | no (nullable) | string or null | See [Section 13](#13-evaluation-statusfailure). |
| `rule_evidence` | yes | array | See [Section 14](#14-rule-evidence). |
| `reason_code` / `explanation` | no | string or null | See [Section 16](#16-reason-codes) / [17](#17-explanations). |

## 8. Trace identity

`trace_id` is a stable identifier unique to this specific evaluation,
independent of array position, safe to reference from an
[`operation-aware-decision-response`](operation-aware-decision-response.md)
(that contract's optional `trace_id` / `evaluation_trace` fields), from
tests, from a future console rendering, and from a future audit event
(PR F) without being itself a secret. No UUID requirement is imposed —
matching the identifier convention already used by `request_id` and
`bundle_id`.

## 9. Request association

`request_id` identifies the `operation-aware-decision-request` this trace
explains; `correlation_id`, when present, is passed through verbatim. The
full request is never copied into a trace — only its identifiers. This
contract does not make the trace authoritative over the request: the
request is the input, the trace is the explanation of what evaluation did
with it.

## 10. Policy bundle association

`bundle_id` and `bundle_version` echo [`policy-bundle`](policy-bundle.md)'s
identity/version fields unchanged, distinct from the request's own
`expected_policy_version` (a request-side expectation) and from
`policy-bundle`'s own `schema_version` (the bundle-shape version). Both are
optional and nullable: null or absent when no bundle applied, or when
applicability could not be determined.

## 11. Bundle applicability

`bundle_applicability` is a closed, nullable field — `applicable` /
`not_applicable` / `null` — distinct from the final authorization outcome
(ADR-0002 Section 5: "`NOT_APPLICABLE`... is not the same as the subject
lacking permission"). `not_applicable` here is the condition that produces
`outcome: not_applicable` when `evaluation_status` is `completed`. `null`
is valid: bundle applicability may be undetermined when evaluation failed
during request/schema validation (evaluation phases 1–2, ADR-0002
Section 3) before bundle applicability is established in phase 3 onward. A
failure that occurs *after* an applicable bundle was already identified
(for example, a condition evaluation error inside that bundle) may still
report `bundle_applicability: applicable` alongside `evaluation_status:
failed` — this contract does not force a fixed correlation between the two
fields **while `evaluation_status` is `failed`**. When `evaluation_status`
is `completed`, however, `outcome` and `bundle_applicability` are required
to agree — see [Section 31](#31-cross-field-invariants).

Bundle scope determines applicability. Rules are evaluated only within an
applicable bundle. `NOT_APPLICABLE` is not a rule effect — see
[`policy-rule.md`](policy-rule.md), "Why NOT_APPLICABLE is not a rule
effect."

## 12. Authorization outcome

`outcome` reuses the existing `decision-response` / `policy-rule` outcome
vocabulary exactly: `allow` / `deny` / `not_applicable`, or `null`. It is a
**required key** on every trace (not merely an optional field), and is
**required to be null when `evaluation_status` is `failed`** — a failed
evaluation never serializes a non-null outcome (ADR-0002 Section 14).

## 13. Evaluation status/failure

`evaluation_status` (`completed` / `failed`) and `failure_reason` (a closed,
six-value evaluator-failure vocabulary, or `null`) are structurally
independent of `outcome`, per ADR-0002 Section 14: "Evaluation errors are
not authorization allows... [the kernel] must not disguise an evaluation
failure as a `DENY` or `NOT_APPLICABLE` decision." The six `failure_reason`
values — `invalid_request`, `unsupported_schema_version`,
`invalid_policy_bundle`, `policy_validation_failure`,
`condition_evaluation_error`, `internal_evaluation_error` — reproduce
ADR-0002 Section 14's representative evaluation-failure categories exactly.
This is kept in parity with
[`operation-aware-decision-response`](operation-aware-decision-response.md)'s
identical field, and is distinct from the existing first-wave
`decision-response`'s own four-value `failure_reason`
(`malformed_request` / `policy_error` / `audit_error` / `internal_error`),
which this contract does not modify or extend.

**Required invariant:** `outcome` is null if and only if
`evaluation_status` is `failed`; `failure_reason` is non-null if and only
if `evaluation_status` is `failed`. A `rule_evidence` entry carrying
`rule_result: error` additionally forces `evaluation_status` to `failed` —
see [Section 31](#31-cross-field-invariants).

## 14. Rule evidence

`rule_evidence` is a required array of
[`trace-rule-evidence`](trace-rule-evidence.md)-shaped values — referenced,
not redefined. It may be **empty**: a `not_applicable` trace (no bundle
applied) or a trace for a failure that occurred before rule evaluation
began legitimately has no rule evidence to report. When
`bundle_applicability` is `not_applicable`, `rule_evidence` MUST be empty —
no rule could have been considered outside an applicable bundle — see
[Section 31](#31-cross-field-invariants).
[`operation-aware-decision-request`](operation-aware-decision-request.md)'s
categories are what rules match against, but this contract does not repeat
that match logic — only the outcome of having applied it. `rule_id` values
within `rule_evidence` must be unique (trace-level validation, mirroring
[`policy-bundle`](policy-bundle.md)'s own bundle-level `rule_id`
uniqueness).

## 15. Condition evidence

Condition-level evidence lives inside each `rule_evidence` entry's own
`condition_results` — see [`trace-rule-evidence.md`](trace-rule-evidence.md),
Section 10. This contract does not duplicate or redefine that shape at the
trace level.

## 16. Reason codes

`reason_code` is optional and, when present, must match
[`reason-code`](reason-code.md)'s published pattern exactly, summarizing
this trace's overall result. Distinct from any individual `rule_evidence`
entry's own `reason_code`.

## 17. Explanations

`explanation` is an optional, non-empty string summarizing the trace's
overall result. Descriptive rendering only — not authoritative (ADR-0003
Section 11). No template, variable-interpolation, expression-evaluation, or
script-execution mechanism is defined. Must not contain secrets.

## 18. Deterministic ordering

`rule_evidence` must be serialized in a stable, deterministic order for
identical input (ADR-0002 Section 8; ADR-0003 Section 13): the same request
evaluated against the same policy bundle version must produce the same
trace, including rule order. This contract documents that requirement
(`trace_ordering` in the contract body) without mandating a specific sort
key — a producer may choose any deterministic ordering (for example, a
stable sort by `rule_id`).

## 19. Ordering vs. authorization precedence

**Deterministic serialization order is not authorization evaluation
precedence.** `policy-rule` intentionally does not publish a
priority/ordering field ([`policy-rule.md`](policy-rule.md), "Rule ordering
decision"), and this contract does not quietly reintroduce one through
trace array order. `rule_evidence` array position is reporting order only;
it never defines which rule "won."

## 20. Trace boundedness

This contract does not carry: a full request snapshot, a full policy
bundle, raw identity evidence, raw adapter evidence, raw protocol payloads,
credentials, tokens, key material, stack traces, or exception objects — see
[Section 28](#28-security) for the enforced field list.

## 21. Evidence references

No `identity_evidence_reference` or `adapter_evidence_reference` field is
published on this contract. ADR-0003 Section 7–8 names these as evidence
categories audit may reference, but this trace already identifies its
request by `request_id`; a future PR F `AuditEvidence` contract is expected
to carry these evidence references directly (associated via `request_id`
and this trace's `trace_id`) rather than this trace duplicating them.

## 22. Redaction

No `redaction_classification` field is published — see
[`trace-rule-evidence.md`](trace-rule-evidence.md), Section 13, for the
same reasoning: every value this contract carries is already a safe
identifier, a closed vocabulary member, or a reason code.

## 23. Missing/unknown context

Per ADR-0002 Section 10, missing or unknown context is represented, at the
rule/condition-evidence level, through
[`trace-rule-evidence`](trace-rule-evidence.md)'s bounded
`condition_results.result: error` category plus an optional `reason_code` —
this contract does not add a separate top-level `missing_context` or
`unknown_value` array, because ADR-0003 Section 4 names these as trace
categories without settling a field-level vocabulary for them (see
[`trace-rule-evidence.md`](trace-rule-evidence.md), Section 15, "What is
intentionally omitted").

## 24. Trace vs. audit

**Trace is not audit.** Per ADR-0003 Section 2: "Trace explains evaluation.
Audit records evidence. Gateway enforcement records what happened at
runtime." This contract is not an immutable audit record, a gateway
enforcement record, a policy-loading record, a session record, an
identity-verification record, a protocol transaction log, a persistence
format, or a compliance attestation. `AuditEvidence` and
`GatewayAuditEvent` are separate, later contracts (PR F) that reference
this trace's `trace_id` rather than being defined by this file.

## 25. Producer/consumer ownership

Produced by a future `basis-core` v0.2.0 kernel as part of evaluation;
embedded in or referenced by
[`operation-aware-decision-response`](operation-aware-decision-response.md);
consumed by `basis-gateway` (assembles audit evidence from this trace in a
future PR F, not implemented here) and `basis-console` (may visualize it,
never authoritatively). `basis-schemas` publishes the shape only.

## 26. Examples

An ALLOW trace:

```yaml
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

A failed-evaluation trace:

```yaml
trace_id: trace-0004-0000-0000-000000000004
request_id: oadr-1099-0000-0000-000000000099
evaluation_status: failed
outcome: null
bundle_applicability: null
failure_reason: unsupported_schema_version
rule_evidence: []
```

The full contract file carries five valid examples (allow, deny-by-
precedence, not-applicable, a failure before bundle applicability was
determined, and a failure inside an already-applicable bundle) and fifteen
invalid examples covering missing `trace_id`/`request_id`, an invalid
outcome, a malformed `evaluation_status`, a failed trace with `outcome:
allow`, a completed trace with a non-null `failure_reason`, an invalid
`bundle_version`, malformed rule evidence, duplicate rule IDs, an unknown
field, a raw request-snapshot field, a stack-trace field, a `rule_result:
error` entry paired with `evaluation_status: completed`, an `outcome:
not_applicable` trace paired with `bundle_applicability: applicable`, an
`outcome: allow` trace paired with `bundle_applicability: not_applicable`,
and a `not_applicable` trace with non-empty `rule_evidence` — see
[Section 31](#31-cross-field-invariants).

## 27. Compatibility

Purely additive. This contract does not modify any existing published
contract, and no existing contract is made to depend on it. It is not
mandatory anywhere; no implementation repository consumes it yet.

## 28. Security

This contract defines no `access_token`, `id_token`, `refresh_token`,
`jwt`, `bearer_token`, `authorization_header`, `cookie`, `session_secret`,
`client_secret`, `password`, `private_key`, `api_key`, `credential`,
`raw_claims`, `full_claim_set`, `raw_payload`, `raw_protocol_payload`,
`packet`, `frame`, `device_secret`, `full_request`, `request_snapshot`,
`full_policy`, `policy_document`, `policy_source`, `debug`, `debug_data`,
`exception`, `exception_object`, `stack`, `stack_trace`, `traceback`,
`gateway_enforcement`, `enforcement_result`, `http_status`, or
`response_status` field, anywhere. Any such field is rejected as unknown —
enforced by regression tests.

## 29. Scope boundaries

This contract does not implement evaluation, persistence, retention, or
storage. It is not itself an audit record. It does not publish
`AuditEvidence` or `GatewayAuditEvent` — each belongs to a later PR (F) per
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md).

## 30. Why `experimental`?

The lifecycle describes this **published contract**, which is new and
unconsumed by any implementation repository — not a claim that the
underlying conceptual category (ADR-0003's evaluation trace) is unsettled.
The `outcome`/`evaluation_status`/`failure_reason` separation and the
`bundle_applicability` representation are `basis-schemas` publication
decisions, made because ADR-0002/ADR-0003 name the requirements without
choosing exact field names. It advances to `candidate` once a real consumer
(expected: `basis-core` v0.2.0's evaluator) exercises it, and to `stable`
only when `basis-architecture` confirms the shape as a durable commitment.
See [`contract-governance.md`](contract-governance.md).

## 31. Cross-field invariants

Beyond the `outcome`/`evaluation_status`/`failure_reason` invariant in
[Section 13](#13-evaluation-statusfailure), this contract enforces three
further cross-field rules:

1. **Rule-error propagation.** If any `rule_evidence` entry carries
   `rule_result: error` (see
   [`trace-rule-evidence.md`](trace-rule-evidence.md), Section 9),
   `evaluation_status` MUST be `failed`. A rule that could not be evaluated
   makes the overall evaluation a failure, not a completed evaluation that
   happens to omit that rule's contribution.
2. **Outcome/bundle-applicability agreement.** When `evaluation_status` is
   `completed`, `outcome` and `bundle_applicability` MUST agree:
   `outcome: not_applicable` if and only if `bundle_applicability:
   not_applicable`, and `outcome: allow` or `outcome: deny` if and only if
   `bundle_applicability: applicable`. This rule is exempt while
   `evaluation_status` is `failed` — see [Section 11](#11-bundle-applicability).
3. **Not-applicable boundedness.** When `bundle_applicability` is
   `not_applicable`, `rule_evidence` MUST be empty.

Each is enforced by the YAML contract's `constraints` block, by dedicated
invalid examples (see [Section 26](#26-examples)), and by dedicated
regression tests (for example,
`test_rule_result_error_with_completed_status_is_invalid`,
`test_completed_not_applicable_requires_bundle_not_applicable`,
`test_not_applicable_bundle_requires_empty_rule_evidence`). `skipped` (a
per-rule `rule_result` value) is never itself a `bundle_applicability`
value — the two vocabularies are distinct and neither invariant above
treats a `skipped` rule as forcing failure or non-applicability.
