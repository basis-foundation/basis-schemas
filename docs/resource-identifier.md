# Resource Identifier Contract

The **resource identifier** contract is the third machine-readable contract
published in `basis-schemas`. It publishes the canonical typed resource-identifier
format decided in `basis-architecture`
(`docs/architecture/resource-identifier-reconciliation.md`) and enforced today by
`basis-core`. It is a publication, not a parser: it defines the shape, it does not
implement validation behavior.

- Contract file: [`../schemas/resource-identifier/resource-identifier.yaml`](../schemas/resource-identifier/resource-identifier.yaml)
- Governed by: `basis-architecture`
- Published by: `basis-schemas`
- Version: `0.1.0`
- Lifecycle: `experimental`

## Structure

```text
{resource_type}:{local_resource_id}
```

A canonical resource identifier is exactly two colon-separated segments:

| Segment             | Required | Meaning |
| ------------------- | -------- | ------- |
| `resource_type`     | yes      | The classification of the resource (e.g. `ahu`, `setpoint`, `controller`). The prefix; the kernel derives the resource type from it. |
| `local_resource_id` | yes      | The specific resource within that type (e.g. `rooftop-1`, `zone-3`, `boiler-1`). |

The `resource_type` matches `^[a-z][a-z0-9_-]*$`; the `local_resource_id` matches
`^[a-z0-9][a-z0-9_-]*$`. Neither segment may contain a colon, so additional
segments are structurally impossible. The full string matches:

```text
^[a-z][a-z0-9_-]*:[a-z0-9][a-z0-9_-]*$
```

## Examples

Valid: `ahu:rooftop-1`, `setpoint:zone-3`, `controller:boiler-1`.

Invalid: `rooftop-1` (no type prefix), `ahu:` (empty local resource id),
`:rooftop-1` (empty resource type), `ahu::rooftop-1` (empty middle segment),
`ahu:rooftop-1:extra` (a third segment — the local resource id may not be
subdivided).

## Composition: who produces and consumes the identifier

This contract publishes the **shape** of a canonical resource identifier; the
boundary ownership of producing one is decided in `basis-architecture` and
summarized here:

- **Adapters emit two separate fields** — a `resource_type` (e.g. `ahu`) and a
  local, untyped `resource_id` (e.g. `rooftop-1`). A local resource id on its own
  is a normalization input, not a canonical identifier.
- **The gateway owns composition** — it combines the `resource_type` and the
  local resource id into `"{resource_type}:{local_resource_id}"` at the same
  boundary where it composes the canonical action, so the action's `{domain}` and
  the resource's `{type}` prefix come from one input and stay consistent.
- **The kernel consumes the canonical identifier** — it evaluates and audits the
  composed `resource_id` and derives the resource type from the prefix; it has no
  separate `resource_type` field.

Aligning the `resource_type` with the action string's `{domain}` segment for the
same operation is intentional: both are filled from one `resource_type` field at
composition time. Whether "action domain" and "resource type" are ultimately one
concept or two is an open architecture question recorded in the reconciliation
report; this contract publishes only the identifier shape and does not resolve it.

## Relationship to `basis-core`

`basis-core` enforces a resource-identifier format at runtime in its validator.
Its regex (`^[a-z][a-z0-9_-]*(:[a-z0-9][a-z0-9_:/-]*)$`) accepts a permissive
superset: the qualifier after the first colon may itself contain further colons
and slashes (for example `sensor:co2:lobby`). This contract publishes the
architecture's canonical `{resource_type}:{local_resource_id}` structure — exactly
two non-empty segments — which is the shape the gateway composes from the
adapter's two fields. Where they differ, `basis-architecture` governs, and this
published shape is the canonical one consumers should target.

## Why `experimental`?

The lifecycle describes this **published contract**, which is new in
`basis-schemas` — not the maturity of the format itself, which is settled and in
production use. It advances to `candidate` once real consumers exercise it and to
`stable` only when `basis-architecture` confirms the shape as a durable
commitment. See [`contract-governance.md`](contract-governance.md).
