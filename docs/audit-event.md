# Audit Event Contract

The **audit event** contract is the sixth machine-readable contract published in
`basis-schemas`, and the last of the first planned wave. It publishes the
canonical audit-record shape decided in `basis-architecture`
(`docs/architecture/ecosystem-contract-inventory.md`, §3.10) and implemented today
by `basis-core`'s `AuditEvent` (`src/basis_core/audit/events.py` and
`schemas/audit-event.schema.json`). It is a publication, not a parser: it defines
the shape, it does not implement audit behavior.

- Contract file: [`../schemas/audit-event/audit-event.yaml`](../schemas/audit-event/audit-event.yaml)
- Governed by: `basis-architecture`
- Published by: `basis-schemas`
- Version: `0.1.0`
- Lifecycle: `experimental`
- Depends on: [`decision-request`](decision-request.md), [`decision-response`](decision-response.md)

## Purpose

An audit event is the canonical record of a security-relevant occurrence. Most
records describe an authorization decision, but the same shape also carries policy
changes, identity events, emergency overrides, adapter events, and system events,
distinguished by `event_type`. An authorization audit event records the *evidence*
of one evaluation: who asked, what they wanted to do, to what resource, what the
outcome was, which rule decided, the policy version in effect, the rules that
matched, and an optional per-rule decision trace. It correlates to the decision
request and response by `request_id`, so request, response, and audit record line
up one-to-one.

This contract publishes the record shape so the components that produce and read
audit records agree on one definition. It carries its own audit `schema_version`
(currently `1.1`): fields are added — never removed or renamed — as that version
advances, so older records stay interpretable.

## Canonical shape

The record is a single object. Four fields are required; everything else is
optional with the defaults below. Unknown fields are rejected (`basis-core` sets
`additionalProperties: false`).

| Field            | Required | Type            | Meaning |
| ---------------- | -------- | --------------- | ------- |
| `event_id`       | yes      | string (non-empty) | Unique id for this audit record (UUID v4). |
| `event_type`     | yes      | enum            | Category: `authorization_decision`, `policy_change`, `identity_event`, `emergency_override`, `adapter_event`, `system_event`. |
| `action`         | yes      | string (non-empty) | The action recorded; carries an action-string value but is constrained only as non-empty. |
| `timestamp`      | yes      | string (date-time) | When the event occurred; timezone-aware. |
| `schema_version` | no       | string          | Audit schema revision in effect (current `1.1`). |
| `request_id`     | no       | string or null  | The decision request's id; correlates request, response, and record. Non-empty when present. |
| `decision_id`    | no       | string or null  | Identifier for the decision; defaults to `request_id`. Non-empty when present. |
| `correlation_id` | no       | string or null  | Caller-provided cross-system trace id, passed through verbatim. |
| `subject_id`     | no       | string or null  | Stable subject identifier; null for system events. Non-empty when present. |
| `subject_name`   | no       | string or null  | Human-readable subject label. |
| `subject_type`   | no       | enum or null    | `human`, `device`, `service`, `gateway`, `agent`. |
| `subject_roles`  | no       | array of string | Roles held by the subject at event time. |
| `resource_id`    | no       | string or null  | Canonical `{resource_type}:{local_resource_id}` identifier, or null. |
| `resource_type`  | no       | string or null  | Resource type (e.g. `hvac`), or null. |
| `outcome`        | no       | enum or null    | `allowed`, `denied`, or `error`; null for non-decision events. |
| `reason`         | no       | string or null  | Human-readable explanation of the outcome. |
| `evaluated_by`   | no       | string or null  | Rule or component that produced the decision. |
| `policy_version` | no       | string or null  | Policy set version in effect. |
| `matched_rules`  | no       | array of string | Rules that returned allow or deny. |
| `trace`          | no       | object or null  | Optional per-rule decision trace (see below). |
| `detail`         | no       | object          | Free-form event-specific context. |

### Field-name and vocabulary notes (published from basis-core, not the prompt)

Three points where the published shape follows `basis-core` exactly rather than a
generic expectation, documented here so the difference is deliberate and visible:

- **`outcome` uses a past-tense audit vocabulary — `allowed` / `denied` /
  `error` — which is distinct from the decision response's `allow` / `deny` /
  `not_applicable`.** `allowed` and `denied` record a permitted or refused
  decision; `error` records an enforcement-boundary failure. Using the
  decision-response value `allow` here is invalid.
- **There is no `failure_reason` field.** A decision response carries a
  `failure_reason` to mark a safe-deny; the audit record instead represents that
  case as `outcome: error` with the failure context placed in `detail`. A
  `failure_reason` key on an audit event is therefore an *unknown field* and is
  rejected.
- **Event-specific context lives in `detail`**, a free-form key/value object — not
  a fixed `metadata` or `context` schema. Command parameters, error information,
  and adapter metadata all go there.

### The optional decision trace

`trace`, when present, is `basis-core`'s `DecisionTrace`: a `final_outcome` (the
engine's aggregated result), a `short_circuited` flag (true when evaluation
stopped early on a deny), and `evaluated_rules` — an ordered list of
`{rule_name, outcome, reason}`. The trace's outcome vocabulary is the kernel's
`allow` / `deny` / `not_applicable`, because it records the engine's own per-rule
aggregation, not the audit outcome. A record is valid without a trace.

## Examples

Allow:

```yaml
event_id: e1000000-0000-0000-0000-000000000001
event_type: authorization_decision
timestamp: "2026-05-22T14:30:00Z"
schema_version: "1.1"
request_id: a1b2c3d4-0001-0000-0000-000000000001
subject_id: a7b8c9d0-1234-5678-abcd-ef0123456789
subject_type: human
subject_roles: [operator]
action: write:hvac:setpoint
resource_id: hvac:zone-a
resource_type: hvac
outcome: allowed
reason: Subject holds a role permitted for 'write:hvac:setpoint'.
evaluated_by: RolePolicyRule
policy_version: v1.0.0
matched_rules: [RolePolicyRule]
detail: {}
```

Deny:

```yaml
event_id: e1000000-0000-0000-0000-000000000002
event_type: authorization_decision
timestamp: "2026-05-22T14:30:05Z"
request_id: a1b2c3d4-0002-0000-0000-000000000002
subject_id: a7b8c9d0-1234-5678-abcd-ef0123456789
subject_type: human
subject_roles: [viewer]
action: write:hvac:setpoint
resource_id: hvac:zone-a
resource_type: hvac
outcome: denied
reason: Subject role 'viewer' is not permitted to perform 'write:hvac:setpoint'.
evaluated_by: RolePolicyRule
policy_version: v1.0.0
matched_rules: [RolePolicyRule]
```

Error (safe-deny from an enforcement-boundary failure; no `failure_reason`
field — the failure is recorded as `outcome: error` with context in `detail`):

```yaml
event_id: e1000000-0000-0000-0000-000000000003
event_type: authorization_decision
timestamp: "2026-05-22T14:30:07Z"
request_id: a1b2c3d4-0004-0000-0000-000000000004
action: write:hvac:setpoint
resource_id: hvac:zone-a
resource_type: hvac
outcome: error
reason: Policy evaluation failed due to an internal rule error. Access denied.
evaluated_by: PolicyEngine
policy_version: v1.0.0
detail:
  failure: policy_error
```

Invalid records include: a missing or empty `event_id`, a missing `event_type`,
an `event_type` outside the enum, a missing `action` or `timestamp`, an `outcome`
that uses the decision-response vocabulary (e.g. `allow`), a `subject_type`
outside the enum, an empty `request_id`, a `resource_id` that is not a canonical
identifier, a stray `failure_reason` (no such field), and any other unknown field.

## Relationship to the decision request

The audit event records the request side of an evaluation and correlates to it by
`request_id`, which is why it declares `depends_on: [decision-request]`. It
reproduces the request's `subject_id`, `subject_roles`, `action`, and
`resource_id` as recorded evidence. (It additionally carries `subject_name` and
`subject_type`, which the kernel resolves from the subject — these are audit
context, not part of the request contract.)

## Relationship to the decision response

The audit event records the outcome of the evaluation and correlates to the
[decision response](decision-response.md) by the same `request_id`, which is why
it also declares `depends_on: [decision-response]`. It reproduces the response's
`reason`, `evaluated_by`, and `policy_version`. Its `outcome`, however, uses the
audit vocabulary (`allowed` / `denied` / `error`) rather than the response's
(`allow` / `deny` / `not_applicable`), and the response's `failure_reason` maps to
an `error` outcome with detail rather than to a dedicated field.

## Ownership boundary

This contract publishes the **shape** of the audit record; the boundary ownership
is decided in `basis-architecture` and summarized here:

- **The gateway / enforcement boundary initiates** the evaluation flow.
- **The kernel (`basis-core`) evaluates** the request, produces the decision
  response, and **defines and produces the audit record**. The audit semantics —
  what an event means and which fields it carries — live in `basis-core`; this
  contract publishes only the resulting shape.
- **`basis-schemas` publishes** the shared audit shape so producers and consumers
  agree on one definition.

## What this contract does not define

This contract is the audit *record shape*, not an audit pipeline. It deliberately
does **not** define audit storage, indexing, retention, tamper-resistance or
signing, or SIEM / external export — and it introduces no SIEM-specific fields,
trace/OpenTelemetry formats, cryptographic signatures, compliance-framework
mappings, or AI metadata. Those concerns live outside `basis-schemas` (and, where
they exist at all today, inside the owning components); the architecture inventory
records the surrounding audit pipeline as still emerging. If any of them later
stabilizes into a shape multiple components must agree on, it would be decided in
`basis-architecture` and published separately.

## Relationship to `basis-core`

`basis-core` enforces this shape at runtime in `AuditEvent` and in its
`audit-event.schema.json`: the same required fields, the same `event_type`,
`outcome`, and `subject_type` enums, the non-empty constraints on `event_id`,
`action`, and the correlation/subject identifiers, and the timezone-aware
`timestamp`. The audit schema constrains `action` only as non-empty (no action
pattern) and accepts the permissive resource-identifier superset used elsewhere in
`basis-core`; this contract publishes the canonical resource-identifier shape for
`resource_id`, consistent with the other published contracts. Where they differ,
`basis-architecture` governs and the published shape is the canonical one
consumers should target.

## Why `experimental`?

The lifecycle describes this **published contract**, which is new in
`basis-schemas` — not the maturity of the audit-event shape itself, which is
defined and versioned in `basis-core`. It advances to `candidate` once real
consumers exercise it and to `stable` only when `basis-architecture` confirms the
shape as a durable commitment. See
[`contract-governance.md`](contract-governance.md).
