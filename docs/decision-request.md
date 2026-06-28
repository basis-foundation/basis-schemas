# Decision Request Contract

The **decision request** contract is the fourth machine-readable contract
published in `basis-schemas`. It publishes the canonical kernel-input shape
decided in `basis-architecture`
(`docs/architecture/ecosystem-contract-inventory.md`, §3.8) and implemented today
by `basis-core`'s `DecisionRequest` (`src/basis_core/decisions/models.py` and
`schemas/decision-request.schema.json`). It is a publication, not a parser: it
defines the shape, it does not implement validation behavior.

- Contract file: [`../schemas/decision-request/decision-request.yaml`](../schemas/decision-request/decision-request.yaml)
- Governed by: `basis-architecture`
- Published by: `basis-schemas`
- Version: `0.1.0`
- Lifecycle: `experimental`
- Depends on: [`action-string`](action-string.md), [`resource-identifier`](resource-identifier.md)

## Purpose

A decision request is the normalized object the policy engine evaluates: who is
asking (the subject), what they want to do (a composite action), what they want
to do it to (an optional canonical resource identifier), and the surrounding
context. It is the single structure that crosses the authorization boundary into
the kernel. This contract publishes that shape so the gateway (which constructs
it) and the kernel (which consumes it) agree on one definition rather than
re-deriving it.

The request reaches the kernel only **after** the gateway has composed the
canonical action and resource identifier from the adapter's normalized fields. So
this contract expects an already-composed request: a composite `action` such as
`read:ahu` and a canonical `resource_id` such as `ahu:rooftop-1`. It never
carries adapter-local fields such as a bare `resource_type` or an untyped local
resource id.

## Canonical shape

The request is a single object. Four fields are required; the rest are optional
with defaults. Unknown fields are rejected (`basis-core` sets
`additionalProperties: false`).

| Field           | Required | Type                 | Meaning |
| --------------- | -------- | -------------------- | ------- |
| `request_id`    | yes      | string (non-empty)   | Correlation id linking the request to its response and audit record. UUID v4 recommended. |
| `subject_id`    | yes      | string (non-empty)   | Stable identifier of the requesting subject (e.g. JWT `sub`). |
| `subject_roles` | no       | array of string      | Role names held by the subject; normalized to a sorted, deduplicated set. Default `[]`. |
| `subject_attrs` | no       | object (string→string) | Additional subject attributes for ABAC conditions. Default `{}`. |
| `action`        | yes      | string (non-empty)   | Composite action in `{verb}:{domain}[:{object}]` form. See [action-string](action-string.md). |
| `resource_id`   | no       | string or null       | Canonical `{resource_type}:{local_resource_id}` identifier, or null when the request is not resource-specific. See [resource-identifier](resource-identifier.md). |
| `context`       | no       | object (string→string) | Key/value context for policy conditions. Default `{}`. |
| `timestamp`     | yes      | string (date-time)   | ISO 8601, timezone-aware. |

### The subject is flat, not nested

The kernel input carries the subject as **flat fields** — `subject_id`,
`subject_roles`, `subject_attrs` — not as a nested `subject` object. This matches
`basis-core`'s `DecisionRequest` exactly. `basis-core` also has a richer
`Subject` domain type (with `name`, `type`, and so on), but that is an internal
domain model, not part of the request contract; the gateway fills the flat fields
from the authenticated identity at composition time.

## Examples

A resource-specific request with roles and context:

```yaml
request_id: a1b2c3d4-0001-0000-0000-000000000001
subject_id: alice@example.com
subject_roles:
  - operator
action: read:ahu
resource_id: ahu:rooftop-1
context:
  site: west-campus
timestamp: "2026-05-22T14:30:00Z"
```

A resource-independent request omits `resource_id`:

```yaml
request_id: a1b2c3d4-0003-0000-0000-000000000003
subject_id: svc-scheduler
action: browse:ahu
timestamp: "2026-05-22T14:32:00Z"
```

Invalid requests include: a missing or empty `subject_id` (malformed subject), a
missing `action`, an `action` that is not a well-formed action string (e.g.
`read` with no domain), a `resource_id` that is not a canonical resource
identifier (e.g. `rooftop-1` with no type prefix), a missing `request_id` or
`timestamp`, and any unknown field (e.g. a stray `resource_type`).

## Relationship to the other contracts

This contract **composes** two already-published format contracts and depends on
the verb set behind one of them:

- **[vocabulary](vocabulary.md)** — the controlled set of verbs (`read`, `write`,
  `execute`, `browse`, `subscribe`). Reached transitively: the `action` field's
  verb segment is governed by vocabulary through the action-string contract.
- **[action-string](action-string.md)** — the `{verb}:{domain}[:{object}]` shape
  of the `action` field. The decision request does not restate the action grammar;
  it declares `depends_on: [action-string]` and reproduces the canonical pattern
  for convenience.
- **[resource-identifier](resource-identifier.md)** — the
  `{resource_type}:{local_resource_id}` shape of the `resource_id` field, declared
  the same way.

The decision request is the first contract that brings these formats together
into the structure the kernel actually evaluates, which is why it follows once
both formats are published.

## Ownership boundary: who normalizes, composes, and consumes

This contract publishes the **shape** of the kernel input; the boundary ownership
is decided in `basis-architecture` and summarized here:

- **Adapters normalize** protocol operations into a bare verb and separate
  resource fields (a `resource_type` and a local, untyped resource id). They do
  not compose canonical identifiers and do not construct a decision request.
- **The gateway composes** the canonical `action` and `resource_id` from those
  fields and fills the subject from the authenticated identity, producing the
  decision request. Composition behavior lives in the gateway; this contract only
  publishes the resulting shape.
- **The kernel (`basis-core`) consumes** the composed request, evaluates it, and
  derives the resource type from the `resource_id` prefix. It never sees protocol
  frames, a bare verb, or adapter-local resource fields.
- **`basis-schemas` publishes** the contract so all of the above agree on one
  definition.

## Relationship to `basis-core`

`basis-core` enforces this shape at runtime in `DecisionRequest` and in its
`decision-request.schema.json`. Its runtime validators accept a permissive
superset of the canonical formats: the `action` pattern allows two-or-more
segments and the `resource_id` pattern allows additional colon/slash qualifiers
(for example `sensor:co2:lobby`). This contract publishes the architecture's
canonical formats — the action string's two-or-three-segment shape and the
resource identifier's exactly-two-segment shape — which are what the gateway
composes. Where they differ, `basis-architecture` governs, and these published
shapes are the canonical ones consumers should target.

## Why `experimental`?

The lifecycle describes this **published contract**, which is new in
`basis-schemas` — not the maturity of the request shape itself, which is settled
and in production use in `basis-core`. It advances to `candidate` once real
consumers exercise it and to `stable` only when `basis-architecture` confirms the
shape as a durable commitment. See
[`contract-governance.md`](contract-governance.md).
