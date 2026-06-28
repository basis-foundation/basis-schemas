# Decision Response Contract

The **decision response** contract is the fifth machine-readable contract
published in `basis-schemas`. It publishes the canonical kernel-output shape
decided in `basis-architecture`
(`docs/architecture/ecosystem-contract-inventory.md`, §3.9) and implemented today
by `basis-core`'s `DecisionResponse` (`src/basis_core/decisions/models.py` and
`schemas/decision-response.schema.json`). It is a publication, not a parser: it
defines the shape, it does not implement evaluation behavior.

- Contract file: [`../schemas/decision-response/decision-response.yaml`](../schemas/decision-response/decision-response.yaml)
- Governed by: `basis-architecture`
- Published by: `basis-schemas`
- Version: `0.1.0`
- Lifecycle: `experimental`
- Depends on: [`decision-request`](decision-request.md)

## Purpose

A decision response is the result the policy engine returns after evaluating a
decision request: the outcome, a human-readable reason, the policy or component
that decided, the policy version in effect, an optional failure reason for
enforcement-boundary denials, and a timestamp. It is the single structure that
crosses the authorization boundary back out of the kernel. This contract
publishes that shape so the kernel (which produces it) and the gateway (which
returns it to the caller) agree on one definition.

The response echoes the `request_id` of the request it answers, so a request and
its response correlate one-to-one and both appear, by that id, in the audit
record.

## Canonical shape

The response is a single object. Five fields are required; the rest are optional
with defaults. Unknown fields are rejected (`basis-core` sets
`additionalProperties: false`).

| Field            | Required | Type                | Meaning |
| ---------------- | -------- | ------------------- | ------- |
| `request_id`     | yes      | string (non-empty)  | Echoes the corresponding request's `request_id` for correlation. |
| `outcome`        | yes      | enum                | The decision: `allow`, `deny`, or `not_applicable`. |
| `reason`         | yes      | string (non-empty)  | Human-readable explanation of the outcome. |
| `evaluated_by`   | yes      | string (non-empty)  | Name of the policy or component that produced the decision. |
| `policy_version` | no       | string or null      | Version of the policy set in effect, or null if none was configured. |
| `failure_reason` | no       | enum or null        | Set for enforcement-boundary denials; null for normal policy decisions. |
| `timestamp`      | yes      | string (date-time)  | ISO 8601, timezone-aware. |

The field is named **`outcome`** (not `decision`), and **`reason` and
`evaluated_by` are required for every response** — including `allow` — matching
`basis-core`'s `DecisionResponse` exactly.

## Decision semantics

`outcome` takes one of three explicit values, never a bare string:

- **`allow`** — the action is permitted; the enforcement point proceeds.
- **`deny`** — the action is not permitted; the enforcement point rejects.
- **`not_applicable`** — no policy covered the request; the enforcement point
  applies its configured default, typically treating it as a deny.

The distinction between `deny` and `not_applicable` is diagnostic: `deny` means a
policy evaluated the request and refused it; `not_applicable` means the request
fell outside the scope of any registered policy. Both are audited.

`failure_reason` distinguishes a normal policy decision from a **safe-deny**
caused by an enforcement-boundary failure. It is null for decisions produced by
the policy engine; when set, it is one of `malformed_request` (the request failed
validation before evaluation), `policy_error` (an exception during rule
evaluation; the engine failed closed), `audit_error` (reserved; the audit write
failed but the decision is unaffected), or `internal_error` (an unexpected
exception inside the enforcement point). A safe-deny carries `outcome: deny` with
a non-null `failure_reason`.

## Examples

Allow, produced by normal policy evaluation:

```yaml
request_id: a1b2c3d4-0001-0000-0000-000000000001
outcome: allow
reason: Subject holds a role permitted for 'write:hvac:setpoint'.
evaluated_by: RolePolicyRule
policy_version: "0.1.0"
failure_reason: null
timestamp: "2026-05-22T14:30:01Z"
```

Deny by policy:

```yaml
request_id: a1b2c3d4-0002-0000-0000-000000000002
outcome: deny
reason: subject missing required role
evaluated_by: RolePolicyRule
timestamp: "2026-05-22T14:30:05Z"
```

Safe-deny from an enforcement-boundary failure:

```yaml
request_id: a1b2c3d4-0004-0000-0000-000000000004
outcome: deny
reason: Policy evaluation failed due to an internal rule error. Access denied.
evaluated_by: PolicyEngine
policy_version: "0.1.0"
failure_reason: policy_error
timestamp: "2026-05-22T14:30:07Z"
```

Invalid responses include: a missing or empty `request_id`, a missing `outcome`,
an `outcome` that is not one of the three enum values (e.g. `maybe`), a missing
`reason` or `evaluated_by`, a missing `timestamp`, a `failure_reason` outside the
enum, a `policy_version` that is neither a string nor null, and any unknown field.

## Relationship to the decision request

This contract is the output paired with the [decision request](decision-request.md)
input, which is why it declares `depends_on: [decision-request]`. The link is the
`request_id`: the response echoes the request's id verbatim, so the two correlate
one-to-one. The response carries no action or resource identifier of its own — it
reports the decision about a request, not the request — so it does not depend on
the action-string or resource-identifier contracts.

## Relationship to the audit event

The [audit event](audit-event.md) records what happened around an evaluation and
references both the request and the response by their shared `request_id`, along
with `evaluated_by` and `policy_version`. The response shape was published before
the audit event, giving it a settled output to reference. Note that the audit
event records the decision under its own past-tense outcome vocabulary
(`allowed` / `denied` / `error`), distinct from this contract's `allow` / `deny` /
`not_applicable`; this contract publishes the response only.

## Ownership boundary: who evaluates, returns, and consumes

This contract publishes the **shape** of the kernel output; the boundary
ownership is decided in `basis-architecture` and summarized here:

- **The gateway submits** a decision request to the kernel.
- **The kernel (`basis-core`) evaluates** the request and **returns** the decision
  response. The decision semantics — how rules are matched and how the outcome is
  reached — live in `basis-core`; this contract publishes only the resulting
  shape, never how it is produced.
- **The gateway consumes** the response and returns it to the calling enforcement
  point.
- **`basis-schemas` publishes** the contract so all of the above agree on one
  definition.

## Relationship to `basis-core`

`basis-core` enforces this shape at runtime in `DecisionResponse` and in its
`decision-response.schema.json`: the same required fields, the same `outcome` and
`failure_reason` enums, the non-empty constraints on `request_id`, `reason`, and
`evaluated_by`, and the timezone-aware `timestamp`. This contract reproduces that
shape faithfully; where any difference were to arise, `basis-architecture`
governs and this published shape is the canonical one consumers should target.

## Why `experimental`?

The lifecycle describes this **published contract**, which is new in
`basis-schemas` — not the maturity of the response shape itself, which is settled
and in production use in `basis-core`. It advances to `candidate` once real
consumers exercise it and to `stable` only when `basis-architecture` confirms the
shape as a durable commitment. See
[`contract-governance.md`](contract-governance.md).
