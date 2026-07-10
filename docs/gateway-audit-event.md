# Gateway Audit Event Contract

The **gateway audit event** contract publishes the bounded, gateway-emitted
record of what happened at the authorization enforcement boundary after
`basis-gateway` received one kernel evaluation result. It is the second
contract of PR F of `basis-architecture`'s operation-aware schema readiness
plan (ADR-0005, "PR F — Audit Evidence and GatewayAuditEvent"); see
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md).

- Contract file: [`../schemas/gateway-audit-event/gateway-audit-event.yaml`](../schemas/gateway-audit-event/gateway-audit-event.yaml)
- Governed by: `basis-architecture`
- Published by: `basis-schemas`
- Version: `0.1.0`
- Lifecycle: `experimental`
- Depends on: [`contract-metadata`](contract-metadata.md), [`operation-aware-decision-response`](operation-aware-decision-response.md), [`evaluation-trace`](evaluation-trace.md), [`policy-bundle`](policy-bundle.md), [`audit-evidence`](audit-evidence.md), [`reason-code`](reason-code.md)

## 1. Purpose

ADR-0003 (`docs/architecture/operation-aware-trace-audit-evidence.md`,
Section 2) defines: "Gateway audit event — the runtime record basis-gateway
emits after enforcement... it combines kernel-produced evidence with
enforcement facts." This contract publishes that record's *shape*: a stable
event identifier and closed event type, an emission timestamp, the
evaluated request's identity, the authoritative kernel evaluation state, a
required reference to the associated [`audit-evidence`](audit-evidence.md)
record, and the gateway's own bounded enforcement facts — what it actually
did, and, when relevant, why it could not complete enforcement itself.

## 2. Contract file

[`../schemas/gateway-audit-event/gateway-audit-event.yaml`](../schemas/gateway-audit-event/gateway-audit-event.yaml)

## 3. Governance

Governed by `basis-architecture`. This contract does not decide gateway
enforcement behavior, fail-open/fail-closed deployment policy, or audit
assembly ownership; it publishes the event shape ADR-0003 Section 9 and
Section 14 already named.

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
  - audit-evidence
  - reason-code
```

`operation-aware-decision-response` / `evaluation-trace`:
`evaluation_status` / `outcome` / `failure_reason` are reused unchanged
(parity-tested); `request_id` / `correlation_id` / `bundle_id` /
`bundle_version` / `trace_id` echo those contracts' identifiers.
`policy-bundle`: `bundle_id` / `bundle_version` echo that contract's
identity/version fields unchanged. `audit-evidence`: `audit_evidence_id`
references that contract's own `evidence_id`, not redefined here.
`reason-code`: the optional `reason_code` field reuses that contract's
format unchanged. `identity-evidence-reference` and
`adapter-evidence-reference` are deliberately not declared — this contract
carries no identity or adapter evidence reference of its own; those remain
exclusively on the referenced `audit-evidence` record.

## 7. Lifecycle

See [Section 5](#5-lifecycle) above.

## 8. Relationship to kernel response

`request_id`, `evaluation_status`, `outcome`, and `failure_reason` echo the
authoritative [`operation-aware-decision-response`](operation-aware-decision-response.md)
this event followed, reused unchanged and kept structurally independent of
this contract's own `enforcement_action` — see
[Section 17](#17-gateway-enforcement-action). The kernel response remains
the sole authority for the authorization outcome; this contract never
rewrites it.

## 9. Relationship to evaluation trace

`trace_id` is an optional reference to the
[`evaluation-trace`](evaluation-trace.md) that explains the kernel
evaluation behind this event, echoed from the associated `audit-evidence`
record when the producer chooses to carry it. Reference only — no
`rule_evidence` or `condition_results` is ever embedded on this contract.

## 10. Relationship to AuditEvidence

**This contract references, but does not embed, `audit-evidence`.**
`audit_evidence_id` is a required, stable reference to the `evidence_id` of
the [`audit-evidence`](audit-evidence.md) record this event's enforcement
facts were combined with (ADR-0003 Section 14: `basis-gateway` "combines
kernel evidence with enforcement facts"). Per ADR-0003 Section 6's "avoid
duplicating... when a stable reference is sufficient" reasoning, applied
here by analogy, a bounded reference is preferred over a second, potentially
inconsistent copy of a record this contract does not own. No embedded
`audit_evidence` object field is published by this contract — see
[Section 22](#22-auditevidence-embeddingreference-model).

## 11. Relationship to first-wave AuditEvent

**`schemas/audit-event/audit-event.yaml` is unchanged** — not renamed,
replaced, widened, or reinterpreted; its `authorization_decision` event
type, its `allowed`/`denied`/`error` outcome vocabulary, and its free-form
`detail` object remain exactly as published before this PR. This contract's
own `event_type` vocabulary (currently the single value
`gateway_authorization`) is deliberately disjoint from the first-wave
contract's `event_type` values — the two are never compared or unified by
any contract in this repository.

## 12. Why separate additive contract

`basis-gateway`'s enforcement-boundary record needs a structurally
different evaluation-state representation (the reused PR E
`evaluation_status`/`outcome`/`failure_reason` triple, richer than the
first-wave `audit-event`'s `outcome: error` + free-form `detail` pattern)
and an explicit reference to a bounded kernel-side evidence record
(`audit-evidence`) the first-wave contract has no concept of. Publishing a
new, additive contract preserves the compatibility guarantee ADR-0005
Section 7 makes for v0.1-era audit records, matching the posture PR C
through PR F already established.

## 13. Canonical shape

An event is a single object. `event_id`, `event_type`, `timestamp`,
`request_id`, `evaluation_status`, `outcome`, `failure_reason`,
`audit_evidence_id`, and `enforcement_action` are always-present required
keys (`outcome` and `failure_reason` may hold an explicit `null`).
`correlation_id`, `bundle_id`, `bundle_version`, `trace_id`, `gateway_id`,
`gateway_failure_reason`, `reason_code`, `explanation`, and
`schema_version` are independently optional. Unknown fields are rejected.

| Field | Required | Type | Meaning |
| --- | --- | --- | --- |
| `event_id` | yes | string (non-empty) | Stable identifier for this event. |
| `event_type` | yes | string (`gateway_authorization`) | See [Section 15](#15-event-type). |
| `timestamp` | yes | string (date-time) | See [Section 16](#16-event-timestamp). |
| `request_id` / `correlation_id` | yes / no | string (non-empty) / string or null | See [Section 18](#18-requestcorrelation-association). |
| `evaluation_status` / `outcome` / `failure_reason` | yes | see [Section 19](#19-kernel-evaluation-state) | Reused unchanged from PR E. |
| `bundle_id` / `bundle_version` / `trace_id` | no | string or null | Policy provenance / trace association. |
| `audit_evidence_id` | yes | string (non-empty) | Reference to the associated `audit-evidence` record. |
| `gateway_id` | no | string or null | See [Section 17.1](#171-gateway-identity). |
| `enforcement_action` | yes | string (`allow` \| `deny`) | See [Section 17](#17-gateway-enforcement-action). |
| `gateway_failure_reason` | no | string or null | See [Section 20](#20-kernel-failure-vs-gateway-local-failure). |
| `reason_code` / `explanation` | no | string or null | See [Section 26](#26-reason-codesexplanations). |
| `schema_version` | no | string | Instance format version — see `audit-evidence.md`, Section 25, for the same pattern. |

## 14. Event identity

`event_id` is a stable identifier for this specific enforcement-boundary
occurrence, independent of array position, storage location, or file path.
No UUID requirement is imposed, matching this repository's existing
identifier convention.

## 15. Event type

`event_type` is closed to a single value in this PR: `gateway_authorization`
— the enforcement-boundary event that follows one kernel authorization
evaluation. This is the smallest safe representation pending a richer
taxonomy, per ADR-0003 Section 17's explicit deferral of "final audit event
schema." No HTTP-status-shaped, vendor-specific, or protocol-specific event
type is published.

## 16. Event timestamp

`timestamp` is a required, timezone-aware ISO 8601 timestamp of when
`basis-gateway` emitted this event (ADR-0003 Section 9's "audit emission
timestamp") — distinct from `audit-evidence`'s own `recorded_at` (when the
kernel-side evidence was recorded) and from any request-side timestamp.

## 17. Gateway enforcement action

`enforcement_action` (`allow` / `deny`) records what `basis-gateway`
actually did at the enforcement boundary for this event (ADR-0003
Section 9: "`basis-core` decides. `basis-gateway` enforces and records
enforcement facts."). It is the smallest-safe placeholder vocabulary
pending a richer taxonomy, per ADR-0003 Section 17's explicit deferral of
"final audit event schema" — deliberately not `forward` / `block` /
`permit`, or any HTTP-status-shaped or vendor/protocol-specific value. This
contract does not require `enforcement_action` to mechanically equal the
kernel `outcome` — that mapping is a gateway/deployment behavior this
document does not standardize. In particular, `enforcement_action: deny`
must be representable, and is valid, alongside `outcome: not_applicable`
and alongside `evaluation_status: failed` (fail-closed gateway behavior on
a kernel result that was not itself a policy deny) — see
[Section 21](#21-fail-closed-representation) and the state-matrix tests
in `../tests/test_gateway_audit_event_contract.py`.

**This contract records the gateway's selected action only, not an
execution result.** No `enforcement_status` or `enforcement_result` field
is published (`additional_properties: false` rejects either as unknown —
see [Section 29](#29-security)). `enforcement_action` is never a guarantee
that the selected action was successfully carried out end-to-end (for
example, that a downstream device actually received and complied with a
deny); it records only that `basis-gateway` selected that action for this
event. Enforcement-result / execution-success semantics are not defined by
this PR and remain deferred to future architecture work (ADR-0003
Section 17).

### 17.1. Gateway identity

`gateway_id` is an optional, non-empty reference to the gateway instance
that emitted this event (ADR-0003 Section 9's "gateway instance
reference"). Not a credential, not a subject, not a policy-loader identity
— purely an instance label. No route, endpoint, network address, or
HTTP-layer detail is carried here or anywhere else on this contract.

## 18. Request/correlation association

`request_id` and optional `correlation_id` are reused unchanged from PR
C/E. Per ADR-0003 Section 6, this contract does not copy the full request:
no `subject_id`, `action`, `resource`, or `resource_type` field is
published. A consumer that needs those values recovers them via
`request_id` from the evaluated request, or via `audit_evidence_id` from
the associated `audit-evidence` record. No separate, gateway-scoped
correlation concept is published — Section 9 names "gateway correlation
ID" as an evidence category, but this contract reuses the existing
`correlation_id` rather than introducing a second one, to avoid a field
published merely because it might be useful someday.

## 19. Kernel evaluation state

`evaluation_status`, `outcome`, and `failure_reason` are reused unchanged
from [`operation-aware-decision-response`](operation-aware-decision-response.md),
[`evaluation-trace`](evaluation-trace.md), and
[`audit-evidence`](audit-evidence.md), kept in parity by this repository's
test suite, with the identical required invariant: `outcome` is null if and
only if `evaluation_status` is `failed`; `failure_reason` is non-null if
and only if `evaluation_status` is `failed`.

## 20. Authorization outcome

This field is never rewritten by this contract: `not_applicable` is not
`deny`, and a `failed` evaluation is never `allow`. See
[Section 17](#17-gateway-enforcement-action) for the gateway's own,
independently-representable action.

## 21. Fail-closed representation

This contract does not model a deployment-wide fail-open/fail-closed
**policy** — ADR-0003 Section 15 explicitly requires later work to define
that. It represents only the bounded **fact** of what the gateway did for
this one event, via `enforcement_action` (and, when the gateway itself
failed, `gateway_failure_reason` — see
[Section 22](#22-kernel-failure-vs-gateway-local-failure)).
`enforcement_action: deny` alongside `outcome: not_applicable`, and
alongside `evaluation_status: failed`, are both valid, representable, and
distinct from a kernel-level deny.

## 22. Kernel failure vs. gateway-local failure

`gateway_failure_reason` is a closed, bounded, optional category for a
gateway-LOCAL failure — the gateway itself failing to complete enforcement
or audit assembly for this event, for a gateway-side reason (ADR-0003
Section 9's "timeout/error behavior"): `gateway_timeout`,
`upstream_unavailable`, `audit_assembly_failure`, or
`internal_gateway_error`. It is distinct in both name and meaning from this
contract's own kernel `failure_reason` field: a kernel evaluation failure
means the kernel could not produce a decision; a gateway-local failure
means the gateway itself could not complete its own work, independent of
whether the kernel succeeded. **Required invariant:** when
`gateway_failure_reason` is non-null, `enforcement_action` MUST be `deny` —
a gateway-local failure must fail closed for this event. When null (the
ordinary case), `enforcement_action` may be either `allow` or `deny`.

## 23. Policy provenance

`bundle_id` / `bundle_version` echo [`policy-bundle`](policy-bundle.md)'s
identity/version fields unchanged, for the same "policy provenance"
reasons [`audit-evidence.md`](audit-evidence.md), Section 18, documents for
itself, including that same section's caveat: this contract does not
enforce that the two fields co-occur — each is independently
optional/nullable. No full policy bundle, rule set, or scope is embedded.

## 24. Subject/action/resource context

No `subject_id`, `action`, `resource`, or `resource_type` field is
published on this contract — see [Section 18](#18-requestcorrelation-association).

## 25. AuditEvidence embedding/reference model

See [Section 10](#10-relationship-to-auditevidence). `audit_evidence_id` is
required; no embedded `audit_evidence` object field is published in this
PR. If a future PR finds embedding justified, it must add matching
cross-object invariant tests that an embedded object's `evidence_id` equals
`audit_evidence_id`, the way
[`operation-aware-decision-response.yaml`](operation-aware-decision-response.md)
already does for its own embedded `evaluation_trace`.

## 26. Reason codes/explanations

`reason_code` is optional and, when present, must match
[`reason-code`](reason-code.md)'s published pattern exactly, and explains
the gateway's own action or failure — it is not required to equal the
associated `audit-evidence` record's own `reason_code`, since the two
explain different layers, mirroring the exact distinction
`audit-evidence.md` already documents for its own `reason_code` field.
`explanation` is an optional, non-empty string, descriptive rendering only
— not authoritative over the structured fields (ADR-0003 Section 11). No
template, variable-interpolation, expression-evaluation, or
script-execution mechanism is defined. Must not contain secrets.

## 27. Authority and consistency

[`operation-aware-decision-response`](operation-aware-decision-response.md)
remains the sole authority for the authorization outcome. This contract is
the authoritative record of **gateway enforcement-boundary behavior** for
one event: `enforcement_action`, `gateway_id`, and `gateway_failure_reason`
are facts only `basis-gateway` can know and record, and no other contract
in this repository redefines them.

## 28. Redaction

No top-level `redaction_classification` field is published. Every value
this contract carries directly is already a safe identifier, a closed
vocabulary member, a reason code, or a reference to a record that already
carries its own redaction handling — the same reasoning `audit-evidence.md`
already documents for itself. See ADR-0003 Section 10's unconditional rule:
"No audit, trace, or explanation artifact may contain secrets."

## 29. Security

This contract defines no `access_token`, `id_token`, `refresh_token`,
`jwt`, `bearer_token`, `authorization_header`, `cookie`, `session_secret`,
`client_secret`, `password`, `private_key`, `api_key`, `credential`,
`raw_claims`, `full_claim_set`, `raw_payload`, `raw_protocol_payload`,
`packet`, `frame`, `device_secret`, `full_request`, `request_snapshot`,
`full_policy`, `policy_document`, `policy_source`, `debug`, `debug_data`,
`exception`, `exception_object`, `stack`, `stack_trace`, `traceback`,
`internal_error_detail`, `implementation_detail`, `rule_evidence`,
`condition_results`, `subject_id`, `action`, `resource`, `resource_type`,
`http_status`, `response_status`, `route`, `endpoint`, `audit_evidence`,
`signature`, `signature_algorithm`, `hash_chain`, `previous_hash`,
`merkle_root`, `storage_uri`, `bucket_name`, `object_key`, or
`retention_policy` field, anywhere. Any such field is rejected as unknown —
enforced by regression tests. This contract does not claim YAML shape alone
provides immutability, tamper resistance, non-repudiation, cryptographic
authenticity, or chain of custody — see
[`audit-evidence.md`](audit-evidence.md), Section 29, for the same
reasoning applied here.

## 30. Examples

Kernel ALLOW, gateway enforces allow:

```yaml
event_id: gwae-0001-0000-0000-000000000001
event_type: gateway_authorization
timestamp: "2026-05-22T14:30:02Z"
request_id: oadr-0002-0000-0000-000000000002
evaluation_status: completed
outcome: allow
failure_reason: null
audit_evidence_id: audev-0001-0000-0000-000000000001
gateway_id: gateway-west-campus-01
enforcement_action: allow
reason_code: allow_rule_matched
```

Kernel evaluation failure, gateway fails closed:

```yaml
event_id: gwae-0004-0000-0000-000000000004
event_type: gateway_authorization
timestamp: "2026-05-22T14:30:04Z"
request_id: oadr-1099-0000-0000-000000000099
evaluation_status: failed
outcome: null
failure_reason: unsupported_schema_version
audit_evidence_id: audev-0004-0000-0000-000000000004
enforcement_action: deny
explanation: Kernel evaluation failed; gateway fail-closed policy denied the request.
```

The full contract file carries six valid examples (kernel allow + gateway
allow; kernel deny + gateway deny; kernel not-applicable + gateway
fail-closed deny; kernel evaluation failure + gateway fail-closed deny; a
gateway-local failure on top of a kernel allow, demonstrating
`enforcement_action` independence; and a minimal example with only required
keys) and twenty-one invalid examples covering a missing/empty `event_id`,
an invalid `event_type`, a malformed `timestamp`, a missing `request_id`, a
malformed `evaluation_status`, every `evaluation_status`/`outcome`/
`failure_reason` invariant violation, a missing/empty `audit_evidence_id`,
an invalid or missing `enforcement_action`, a `gateway_failure_reason` set
alongside `enforcement_action: allow`, a malformed `reason_code`, a
malformed `bundle_version`, a raw request field, a raw evidence field, a
gateway secret field, and an unknown field.

## 31. Compatibility

Purely additive. No existing contract (`decision-request`,
`decision-response`, `audit-event`, `action-string`, `resource-identifier`,
`contract-metadata`, `redaction-classification`, `reason-code`,
`identity-evidence-reference`, `adapter-evidence-reference`,
`operation-aware-decision-request`, `policy-condition`, `policy-rule`,
`policy-bundle`, `trace-rule-evidence`, `evaluation-trace`,
`operation-aware-decision-response`, `audit-evidence`) changed shape,
required fields, optional fields, examples, or validation behavior, and
none was made to depend on this new contract. This contract is not
mandatory anywhere; no implementation repository consumes it yet.

## 32. Scope boundaries

Per ADR-0003 Section 17 ("Open Questions Deferred"), this contract does not
finalize: the final audit event schema, the reason-code vocabulary, the
audit storage/retention model, a tamper-evident audit design, SIEM/export
integrations, compliance mapping, privacy/data-minimization policy, safety-
system audit requirements, or gateway fail-open/fail-closed behavior on
audit failure. This contract does not implement gateway enforcement,
gateway middleware, HTTP response behavior, audit persistence, retention,
signing, or tamper-evidence. It does not publish PR G's compatibility-
test-vector, compatibility-example, or cross-repository-test-vector
contracts.

## 33. Why `experimental`?

The lifecycle describes this **published contract**, which is new and
unconsumed by any implementation repository — not a claim that the
underlying conceptual category (ADR-0003's gateway audit event) is
unsettled. The `enforcement_action` and `gateway_failure_reason`
vocabularies are `basis-schemas` publication decisions, made because
ADR-0003 Section 9 names the requirements without choosing exact field
names or a final vocabulary — Section 17 explicitly defers the "final
audit event schema." It advances to `candidate` once a real consumer
(expected: `basis-gateway`'s enforcement path) exercises it, and to
`stable` only when `basis-architecture` confirms the shape as a durable
commitment. See [`contract-governance.md`](contract-governance.md).
