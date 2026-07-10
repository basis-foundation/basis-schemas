# Audit Evidence Contract

The **audit evidence** contract publishes the bounded, durable,
audit-oriented evidence representation of one operation-aware authorization
evaluation. It is the first contract of PR F of `basis-architecture`'s
operation-aware schema readiness plan (ADR-0005, "PR F — Audit Evidence and
GatewayAuditEvent"); see
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md).

- Contract file: [`../schemas/audit-evidence/audit-evidence.yaml`](../schemas/audit-evidence/audit-evidence.yaml)
- Governed by: `basis-architecture`
- Published by: `basis-schemas`
- Version: `0.1.0`
- Lifecycle: `experimental`
- Depends on: [`contract-metadata`](contract-metadata.md), [`operation-aware-decision-response`](operation-aware-decision-response.md), [`evaluation-trace`](evaluation-trace.md), [`policy-bundle`](policy-bundle.md), [`identity-evidence-reference`](identity-evidence-reference.md), [`adapter-evidence-reference`](adapter-evidence-reference.md), [`reason-code`](reason-code.md)

## 1. Purpose

ADR-0003 (`docs/architecture/operation-aware-trace-audit-evidence.md`,
Section 2) defines: "Audit evidence — a durable evidence package derived
from a governed evaluation and its related artifacts, broader than trace
(includes trace as one input) but not a duplicate of it." This contract
publishes that evidence package's *shape*: a stable evidence identifier, the
evaluated request's identity and optional correlation/trace association,
the authoritative kernel evaluation state, the evaluated policy bundle's
bounded identity/version, a bounded list of matched rule identifiers,
optional identity/adapter evidence references, an optional reason code /
safe explanation, and a required recording timestamp.

## 2. Contract file

[`../schemas/audit-evidence/audit-evidence.yaml`](../schemas/audit-evidence/audit-evidence.yaml)

## 3. Governance

Governed by `basis-architecture`. This contract does not decide audit
semantics or evidence-assembly ownership; it publishes the shape ADR-0003
already named.

## 4. Version

`0.1.0`

## 5. Lifecycle

`experimental`

## 6. Dependencies

```yaml
depends_on:
  - contract-metadata
  - operation-aware-decision-response
  - evaluation-trace
  - policy-bundle
  - identity-evidence-reference
  - adapter-evidence-reference
  - reason-code
```

`operation-aware-decision-response`: `evaluation_status` / `outcome` /
`failure_reason` are reused unchanged (parity-tested); `request_id` /
`correlation_id` / `bundle_id` / `bundle_version` echo that contract's
identifiers. `evaluation-trace`: `trace_id` references that contract's
`trace_id`; `matched_rule_ids` is derived from, but does not copy,
`rule_evidence` entries with `rule_result: matched`. `policy-bundle`:
`bundle_id` / `bundle_version` echo that contract's identity/version fields
unchanged. `identity-evidence-reference` / `adapter-evidence-reference`: the
optional evidence-reference fields carry values shaped exactly by those
published contracts, referenced not redefined. `reason-code`: the optional
`reason_code` field reuses that contract's format unchanged.
`redaction-classification` is deliberately not declared — see
[Section 21](#21-redaction-classifications).

## 7. Lifecycle

See [Section 5](#5-lifecycle) above; the field-level record lifecycle (who
produces it, whether it is persisted) is described in
[Section 26](#26-durability-responsibility) and
[Section 28](#28-relationship-to-gatewayauditevent).

## 8. Relationship to EvaluationTrace

**Audit evidence is not a second trace.** Per ADR-0003 Section 2: "Trace
explains evaluation. Audit records evidence." This record is broader than
[`evaluation-trace`](evaluation-trace.md) (it may reference trace, identity
evidence, and adapter evidence) but it is not itself a duplicate trace: it
does not copy `trace-rule-evidence` objects, condition-level evidence, or a
full `evaluation-trace`. `matched_rule_ids` carries only the stable
`rule_id` values of rules an evaluation trace already reported as
`rule_result: matched` — the full per-rule explanation (effect, condition
results, reason code) remains exclusively on `evaluation-trace`'s own
`rule_evidence`, referenced by this record's optional `trace_id`, never
duplicated here.

## 9. Relationship to OperationAwareDecisionResponse

`evaluation_status`, `outcome`, and `failure_reason` are reused unchanged
from [`operation-aware-decision-response`](operation-aware-decision-response.md)
(and kept in parity with [`evaluation-trace`](evaluation-trace.md)), with
the identical required invariant. This record does not carry the response's
own `evaluation_trace` embedding — only the bounded evaluation-state fields
and, when relevant, a `trace_id` reference.

## 10. Relationship to GatewayAuditEvent

**Audit evidence is not a gateway enforcement event.** Per ADR-0003
Section 14 ("Audit Event Assembly Ownership"): `basis-core` "produces
decision response, reason metadata, evaluation trace, kernel-side audit
evidence," while `basis-gateway` "assembles gateway audit event, combines
kernel evidence with enforcement facts, emits audit." This contract is that
**kernel-side audit evidence**: `basis-core` produces the authoritative
decision response, evaluation trace, and this evidence as associated
artifacts of one evaluation — not persisted by `basis-core` anywhere
durable (see [Section 26](#26-durability-responsibility)). This contract
does not define the runtime transport, envelope, return tuple, or delivery
mechanism connecting those three artifacts, and it is not embedded in
`operation-aware-decision-response`: that contract has no `audit_evidence`
or `audit_evidence_id` field (verified directly against
`operation-aware-decision-response.yaml`). It carries no enforcement
action, no enforcement result, and no gateway-runtime fact of any kind —
those live exclusively on the separate
[`gateway-audit-event`](gateway-audit-event.md) contract (also published by
this PR), which references this record by `evidence_id` (its
`audit_evidence_id` field) rather than redefining or duplicating it.
`gateway-audit-event` is the record `basis-gateway` **assembles** by
combining this kernel-produced evidence with the enforcement facts only the
gateway can know; this contract does not itself perform that combination or
claim gateway assembly ownership.

## 11. Relationship to first-wave AuditEvent

**`schemas/audit-event/audit-event.yaml` is unchanged.** Not renamed,
replaced, widened, or reinterpreted: its version, required fields, optional
fields, event types, outcome values, trace representation, schema version,
examples, and validation behavior are all identical to before this PR
(`git diff main -- schemas/audit-event docs/audit-event.md` is empty). It
remains the published v0.1-era audit contract, produced and consumed today
by `basis-core` alone, using the first-wave `allowed` / `denied` / `error`
outcome vocabulary and a free-form `detail` object. This contract is a
separate, additive, operation-aware audit contract, published alongside it,
not superseding it — the two audit vocabularies (`allow`/`deny`/
`not_applicable` here vs. `allowed`/`denied`/`error` there) are never
compared or unified by any contract in this repository.

## 12. Why separate additive contract

The operation-aware evaluation model (ADR-0002) needs a structurally
different evaluation-state representation (`evaluation_status` /
`failure_reason` kept independent of `outcome`, richer than the first-wave
audit-event's `outcome: error` + free-form `detail` pattern) and a bounded
rule/policy provenance model the first-wave contract has no concept of.
Widening the existing `audit-event` in place would break the compatibility
guarantee ADR-0005 Section 7 makes for v0.1-era audit records; publishing a
new, additive contract instead preserves that guarantee exactly, matching
the posture PR C, PR D, and PR E already established.

## 13. Canonical shape

A record is a single object. `evidence_id`, `request_id`,
`evaluation_status`, `outcome`, `failure_reason`, and `recorded_at` are
always-present required keys (`outcome` and `failure_reason` may hold an
explicit `null`). `correlation_id`, `trace_id`, `bundle_id`,
`bundle_version`, `matched_rule_ids`, `identity_evidence_reference`,
`adapter_evidence_reference`, `reason_code`, `explanation`, and
`schema_version` are independently optional. Unknown fields are rejected.

| Field | Required | Type | Meaning |
| --- | --- | --- | --- |
| `evidence_id` | yes | string (non-empty) | Stable identifier for this evidence record. |
| `request_id` | yes | string (non-empty) | The evaluated request's `request_id`. |
| `correlation_id` | no | string or null | Passthrough of the request's `correlation_id`. |
| `trace_id` | no | string or null | Reference to the explanatory `evaluation-trace`. |
| `evaluation_status` / `outcome` / `failure_reason` | yes | see [Section 16](#16-decisionevaluation-state) | Reused unchanged from PR E. |
| `bundle_id` / `bundle_version` | no | string or null | The evaluated policy bundle's identity/version. |
| `matched_rule_ids` | no | array of string | Bounded, stable rule identifiers — see [Section 19](#19-rule-evidencereference-model). |
| `identity_evidence_reference` / `adapter_evidence_reference` | no | object or null | See [Section 20](#20-identityadapter-evidence-references). |
| `reason_code` / `explanation` | no | string or null | See [Section 22](#22-reason-codes) / [23](#23-explanations). |
| `recorded_at` | yes | string (date-time) | See [Section 24](#24-timestamp-semantics). |
| `schema_version` | no | string | See [Section 25](#25-schema-version-semantics). |

## 14. Evidence identity

`evidence_id` is a stable identifier for this specific evaluation's
evidence, independent of array position, storage location, or file path;
safe to reference from a [`gateway-audit-event`](gateway-audit-event.md)
without being itself a secret. No UUID requirement is imposed, matching the
identifier convention already used by `request_id`, `trace_id`, and
`bundle_id`.

## 15. Request/correlation association

`request_id` identifies the evaluated `operation-aware-decision-response`;
`correlation_id`, when present, is passed through verbatim. Per ADR-0003
Section 6: "Audit should usually avoid duplicating the full raw request when
a stable hash or reference is sufficient... A decision request hash, paired
with a request ID and correlation ID, is generally enough." This contract
does not copy the full request — only these identifiers, plus the bounded
evaluation state.

## 16. Decision/evaluation state

`evaluation_status` (`completed` / `failed`), `outcome` (`allow` / `deny` /
`not_applicable` / `null`), and `failure_reason` (the six-value evaluator-
failure vocabulary, or `null`) are reused unchanged from
[`operation-aware-decision-response`](operation-aware-decision-response.md)
and [`evaluation-trace`](evaluation-trace.md), kept in parity by this
repository's test suite. **Required invariant:** `outcome` is null if and
only if `evaluation_status` is `failed`; `failure_reason` is non-null if
and only if `evaluation_status` is `failed`. A `not_applicable` outcome is
never rewritten as `deny`, and a `failed` evaluation is never rewritten as
`allow`.

## 17. Failure representation

See [Section 16](#16-decisionevaluation-state); `failure_reason` is the
identical six-value kernel evaluator-failure vocabulary published by
`operation-aware-decision-response` and `evaluation-trace`, distinct from
the open `reason_code` field ([Section 22](#22-reason-codes)) and from the
existing first-wave `audit-event`'s outcome-based `error`/`detail`
representation, which this contract does not modify or extend.

## 18. Policy provenance

`bundle_id` / `bundle_version` echo [`policy-bundle`](policy-bundle.md)'s
identity/version fields unchanged: the bundle actually evaluated. Both are
optional and nullable — null or absent when no bundle applied (`outcome:
not_applicable`) or when evaluation failed before a bundle was identified.
No full policy bundle, rule set, or scope is embedded — only this bounded
identity/version reference. **This contract does not enforce that the two
fields co-occur:** each is independently optional/nullable, matching the
same independent-field treatment `operation-aware-decision-response`
already gives its own `bundle_id` / `bundle_version` pair. A producer is
expected to keep them logically paired (a real evaluated bundle has both
an identity and a version), but that pairing is a producer responsibility,
not a constraint this schema validates or rejects a record for omitting.

## 19. Rule evidence/reference model

`matched_rule_ids` is a bounded array of stable `rule_id` values (reused
unchanged from [`policy-rule`](policy-rule.md)) whose `evaluation-trace`
`rule_evidence` entry carried `rule_result: matched` — the rules that
contributed to the decision. It never carries a rule's effect, condition
results, reason code, or explanation: the full per-rule explanation remains
exclusively on `evaluation-trace`'s own `rule_evidence`, referenced by this
record's optional `trace_id`. Items must be non-empty and unique within the
array. Empty when no bundle applied, when evaluation failed before rule
matching began, or when no candidate rule matched. **Array order is not
authorization precedence:** this contract does not define, and a
producer's chosen ordering does not imply, any priority or rule-combining
precedence among the listed IDs, mirroring
[`evaluation-trace`](evaluation-trace.md)'s own
`trace_ordering.authorization_precedence: not_defined_by_this_contract`
deferral for `rule_evidence`.

## 20. Identity/adapter evidence references

`identity_evidence_reference` and `adapter_evidence_reference`, when
present, are validated against
[`identity-evidence-reference`](identity-evidence-reference.md) and
[`adapter-evidence-reference`](adapter-evidence-reference.md) exactly as
published — never redefined, never carrying raw evidence, tokens, claims,
or protocol payloads. This mirrors `operation-aware-decision-request`'s own
reuse of the same two contracts.

## 21. Redaction classifications

No top-level `redaction_classification` field is published. Every value
this contract carries directly is already a safe identifier, a closed
vocabulary member, a reason code, or a nested evidence reference that
already carries its own `redaction_classification` (reused from PR B
unchanged) — the same reasoning `evaluation-trace.md` and
`operation-aware-decision-response.md` already document for themselves. See
ADR-0003 Section 10 ("Redaction and Secret Handling") for the unconditional
rule this contract follows: "No audit, trace, or explanation artifact may
contain secrets."

## 22. Reason codes

`reason_code` is optional and, when present, must match
[`reason-code`](reason-code.md)'s published pattern exactly, summarizing
this evidence's evaluation result. Typically echoes the response's own
`reason_code`; this contract does not require equality, since audit
evidence may be assembled with a more specific or differently-scoped code
than the response carried. Per ADR-0003 Section 12, the reason-code
vocabulary itself remains an open, governed compatibility surface, not
finalized by this contract.

## 23. Explanations

`explanation` is an optional, non-empty string summarizing the evidence's
overall result. Descriptive rendering only — not authoritative over the
structured `evaluation_status` / `outcome` / `failure_reason` fields
(ADR-0003 Section 11). No template, variable-interpolation, expression-
evaluation, or script-execution mechanism is defined. Must not contain
secrets.

## 24. Timestamp semantics

`recorded_at` is a required, timezone-aware ISO 8601 timestamp of when this
evidence record was produced/recorded — distinct from
`operation-aware-decision-request`'s `evaluation_time` (request-supplied
context the evaluator reasons about), from any request-side timestamp, and
from a future `gateway-audit-event`'s own emission `timestamp` (a later,
gateway-side event). This contract carries a supplied or producer-assigned
value only: no runtime clock implementation is implemented here.

## 25. Schema-version semantics

`schema_version` is optional, defaulting to `"0.1.0"`, and describes the
audit-evidence INSTANCE format version a record was produced against —
distinct from this contract file's own `contract.version` (the CONTRACT
SHAPE version) and from the `basis-schemas` package version, matching the
three-way distinction `policy-bundle.yaml` already draws. Mirrors
first-wave `audit-event`'s own `schema_version` precedent: fields are
added, never removed or renamed, as this version advances.

## 26. Authority and consistency rules

`operation-aware-decision-response` is the authoritative kernel
authorization result; `evaluation-trace` is the explanatory kernel
artifact; this contract is the durable bounded evidence representation
derived from both. Where values are repeated (`evaluation_status` /
`outcome` / `failure_reason` / `bundle_id` / `bundle_version`), this
repository's test suite enforces parity against the canonical source
contracts.

## 27. Boundedness

This contract does not carry a full request snapshot, a full policy
bundle, raw identity evidence, raw adapter evidence, raw protocol payloads,
credentials, tokens, key material, a per-rule trace object, condition-level
evidence, gateway enforcement facts, storage configuration, or a
cryptographic signature — see [Section 30](#30-security) for the enforced
field list.

## 28. Durability responsibility

**"Durable" describes the evidence record's intended role once a producer
persists it — it is not a claim this YAML shape makes true by itself.**
Per ADR-0003 Section 14, `basis-core` produces this evidence as an
associated artifact of its evaluation (alongside, not embedded within, the
decision response — see [Section 10](#10-relationship-to-gatewayauditevent))
but does not persist it anywhere durable; `basis-console` reads
and visualizes evidence that already exists, and does not become the system
of record for it. This contract does not implement audit storage,
retention, indexing, or export. Which component actually persists audit
evidence durably, and how, is an open question this document does not
settle (ADR-0003 Section 17).

## 29. No cryptographic claims

This contract does not claim YAML shape alone provides immutability, tamper
resistance, tamper evidence, non-repudiation, cryptographic authenticity, or
chain of custody. No `signature`, `signature_algorithm`, `hash_chain`,
`previous_hash`, or `merkle_root` field is published — see
[Section 30](#30-security).

## 30. Security

This contract defines no `access_token`, `id_token`, `refresh_token`,
`jwt`, `bearer_token`, `authorization_header`, `cookie`, `session_secret`,
`client_secret`, `password`, `private_key`, `api_key`, `credential`,
`raw_claims`, `full_claim_set`, `raw_payload`, `raw_protocol_payload`,
`packet`, `frame`, `device_secret`, `full_request`, `request_snapshot`,
`full_policy`, `policy_document`, `policy_source`, `debug`, `debug_data`,
`exception`, `exception_object`, `stack`, `stack_trace`, `traceback`,
`internal_error_detail`, `implementation_detail`, `rule_evidence`,
`condition_results`, `enforcement_action`, `enforcement_result`,
`enforcement_status`, `http_status`, `response_status`,
`gateway_enforcement`, `event_id`, `event_type`, `signature`,
`signature_algorithm`, `hash_chain`, `previous_hash`, `merkle_root`,
`storage_uri`, `bucket_name`, `object_key`, or `retention_policy` field,
anywhere. Any such field is rejected as unknown — enforced by regression
tests.

## 31. Examples

A completed ALLOW evidence record:

```yaml
evidence_id: audev-0001-0000-0000-000000000001
request_id: oadr-0002-0000-0000-000000000002
evaluation_status: completed
outcome: allow
failure_reason: null
bundle_id: baseline-read-only-telemetry
bundle_version: "1.0.0"
matched_rule_ids:
  - rule-operator-read-ahu-telemetry
reason_code: allow_rule_matched
recorded_at: "2026-05-22T14:30:01Z"
```

A failed-evaluation evidence record:

```yaml
evidence_id: audev-0004-0000-0000-000000000004
request_id: oadr-1099-0000-0000-000000000099
evaluation_status: failed
outcome: null
failure_reason: unsupported_schema_version
explanation: The request declared a schema version this kernel does not support.
recorded_at: "2026-05-22T14:30:03Z"
```

The full contract file carries six valid examples (allow, deny with a
referenced trace, not-applicable, a failed evaluation, full policy
provenance with an explicit `schema_version`, and safe identity/adapter
evidence references) and eighteen invalid examples covering a missing or
empty `evidence_id`, a missing `request_id`, a malformed timestamp, every
`evaluation_status`/`outcome`/`failure_reason` invariant violation, an
invalid outcome value, a malformed `bundle_version`, an empty `trace_id`,
duplicate rule IDs, an unsupported nested redaction classification, a raw
access-token field, a raw-claims field, a raw-protocol-payload field, a
request-snapshot field, a full-policy field, a stack-trace field, and an
unknown field.

## 32. Compatibility

Purely additive. No existing contract (`decision-request`,
`decision-response`, `audit-event`, `action-string`, `resource-identifier`,
`contract-metadata`, `redaction-classification`, `reason-code`,
`identity-evidence-reference`, `adapter-evidence-reference`,
`operation-aware-decision-request`, `policy-condition`, `policy-rule`,
`policy-bundle`, `trace-rule-evidence`, `evaluation-trace`,
`operation-aware-decision-response`) changed shape, required fields,
optional fields, examples, or validation behavior, and none was made to
depend on this new contract. This contract is not mandatory anywhere; no
implementation repository consumes it yet.

## 33. Scope boundaries

Per ADR-0003 Section 17 ("Open Questions Deferred"), this contract does not
finalize: the final audit event schema, the reason-code vocabulary, the
audit storage/retention model, a tamper-evident audit design, SIEM/export
integrations, compliance mapping, privacy/data-minimization policy, safety-
system audit requirements, gateway fail-open/fail-closed behavior on audit
failure, the adapter evidence schema, or the identity evidence schema. This
contract does not implement evaluation, enforcement, persistence,
retention, signing, or tamper-evidence. It does not publish PR G's
compatibility-test-vector, compatibility-example, or cross-repository-test-
vector contracts.

## 34. Why `experimental`?

The lifecycle describes this **published contract**, which is new and
unconsumed by any implementation repository — not a claim that the
underlying conceptual category (ADR-0003's audit evidence) is unsettled.
The field names, the `matched_rule_ids` reference model, and the evidence-
reference reuse pattern are `basis-schemas` publication decisions, made
because ADR-0003 names the requirements without choosing exact field names.
It advances to `candidate` once a real consumer (expected: `basis-core`
v0.2.0 producing evidence, `basis-gateway` combining it into
`gateway-audit-event`) exercises it, and to `stable` only when
`basis-architecture` confirms the shape as a durable commitment. See
[`contract-governance.md`](contract-governance.md).
