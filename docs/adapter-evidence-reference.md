# Adapter Evidence Reference Contract

The **adapter evidence reference** contract publishes a safe reference shape
for normalized adapter evidence. It is the second of two evidence-reference
contracts from the operation-aware schema readiness plan (`basis-architecture`
ADR-0005, "PR B — Evidence Reference Contracts"); see
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md).

- Contract file: [`../schemas/adapter-evidence-reference/adapter-evidence-reference.yaml`](../schemas/adapter-evidence-reference/adapter-evidence-reference.yaml)
- Governed by: `basis-architecture`
- Published by: `basis-schemas`
- Version: `0.1.0`
- Lifecycle: `experimental`
- Depends on: [`contract-metadata`](contract-metadata.md), [`redaction-classification`](redaction-classification.md)

## Purpose

Future operation-aware request, trace, audit, and explanation contracts need
to answer "which adapter normalization evidence produced this operation
context?" without embedding raw protocol payloads or making `basis-core`
protocol-aware. This contract publishes a **reference** shape: a stable
identifier, a structural digest, an adapter source label, an optional
protocol label, optional normalization and protocol-mapping provenance, a
redaction classification, and optional association with a decision request
and a broader correlated operation.

The core rule: **reference evidence, do not duplicate secrets or raw
sensitive payloads.** This contract never carries a `raw_payload`,
`raw_protocol_payload`, `packet`, `frame`, `credential`, `password`,
`api_key`, `private_key`, or `unredacted_device_secret` field — any such
field is rejected as unknown, because `additional_properties: false` closes
the shape to exactly the fields below.

## What this contract does not define

Consistent with PR B's scope in
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md),
this contract does not define: adapter normalization logic, protocol
parsing, protocol-specific behavior, evidence storage, evidence retrieval,
evidence retention, evidence signing, evidence verification, runtime hashing
behavior, authorization result, or enforcement result. It also does not
introduce the operation-aware `DecisionRequest`/`DecisionResponse`, any
policy or trace/audit contract, or a final reason-code vocabulary — those
remain scoped to later PRs (C through G).

## Canonical shape

| Field                     | Required | Type              | Meaning |
| ------------------------- | -------- | ------------------ | ------- |
| `reference_id`            | yes      | string (non-empty) | Stable identifier for the evidence artifact. |
| `evidence_digest`         | yes      | object              | Structural digest — see below. |
| `adapter_source`          | yes      | string (non-empty) | Opaque label for the adapter/normalization component. |
| `redaction_classification`| yes      | enum                | One of the five published redaction-classification values. |
| `normalization_version`   | no       | string or null      | Adapter normalization-logic version, when tracked. |
| `mapping_version`         | no       | string or null      | Protocol-to-canonical mapping version, when applicable. |
| `protocol`                | no       | string or null      | Open, lowercase protocol label carried as provenance only. |
| `request_id`              | no       | string or null      | Associated decision request, when already known. Non-empty when present. |
| `correlation_id`          | no       | string or null      | Broader cross-system trace id, passed through verbatim. |

Unknown fields are rejected.

### `evidence_digest` shape

| Field       | Required | Type   | Meaning |
| ----------- | -------- | ------ | ------- |
| `algorithm` | yes      | string | Open, lowercase kebab-case algorithm label (e.g. `sha-256`). Not a closed enum. |
| `value`     | yes      | string | Lowercase hexadecimal digest value, no prefix or whitespace. |

Identical in shape and semantics to
[`identity-evidence-reference`](identity-evidence-reference.md)'s
`evidence_digest`. It is **structural metadata only**: this contract does not
implement, canonicalize, or verify hashing, does not claim tamper evidence or
cryptographic authenticity, and does not define a canonicalization rule.
Evidence producers (`basis-adapters`) own deterministic digest generation.

## Reference identifier semantics

`reference_id` follows the same convention as
[`identity-evidence-reference`](identity-evidence-reference.md#reference-identifier-semantics)
and this repository's existing `request_id` / `event_id` fields: explicit,
deterministic, stable, non-empty, and independent of Python import path,
source filename, or temporary storage path. UUID v4 is recommended; no
regular expression is enforced, so future adapter producers are not blocked
by a premature identifier grammar.

## Protocol neutrality

`protocol` is optional, and when present it is an open, lowercase label (for
example `modbus`, `bacnet`, `opcua`, `mqtt`, `dnp3`, `iec61850`, `knx`,
`niagara`, `rest`) validated only against a permissive structural pattern —
never a closed enum. `basis-adapters` has added new protocols additively
across its history (nine published so far, with more on its roadmap); a
closed protocol enum here would need to change every time a new adapter
ships, which is exactly the coupling this contract avoids. `protocol` is
provenance metadata, never a protocol-specific operation-payload field, and
its presence does not make `basis-core` protocol-aware — a consumer may
treat it as an opaque label.

`adapter_source` is likewise an opaque label naming the producing adapter or
normalization component; this contract does not require any protocol-specific
top-level field, so it remains usable across every currently published
adapter and future ones.

## Redaction-classification semantics

`redaction_classification` reuses the five values published by
[`redaction-classification`](redaction-classification.md) — it does not
redefine or duplicate that vocabulary. It describes **handling requirements
for the referenced adapter evidence artifact**, not permission to expose raw
evidence through the reference object itself. A `safe_to_expose`
classification on a reference does not make the underlying evidence public;
normal authorization and access controls still apply to whatever view
carries the reference.

## Request and correlation association

- `reference_id` identifies the evidence artifact itself.
- `request_id` associates the evidence with one specific decision request,
  matching the semantics of `request_id` in
  [`decision-request`](decision-request.md) and
  [`audit-event`](audit-event.md). It is optional and nullable because
  adapter evidence is commonly produced during normalization, ahead of the
  specific authorization request the gateway later assembles.
- `correlation_id` associates evidence with a broader end-to-end operation or
  workflow, passed through verbatim, mirroring `audit-event`'s
  `correlation_id` exactly (no non-emptiness constraint).

This contract does not redefine `request_id` or `correlation_id`; it reuses
their existing semantics and does not introduce a new identifier contract.

## Producer and consumer ownership

- **`basis-adapters`** produces normalized adapter evidence and mints
  `reference_id` / `evidence_digest` values. It remains the sole owner of
  protocol translation and normalization logic — none of that behavior is
  defined here.
- **`basis-gateway`** will later assemble these references into
  operation-aware requests and gateway audit events (PR C onward).
- **`basis-core`** consumes references as request context; it does not
  retrieve, parse, or interpret raw protocol payloads, and this contract
  does not make it protocol-aware.
- **`basis-console`** will later display redacted reference metadata and
  explanations; it does not retrieve or expose prohibited evidence.
- Adapters do not authorize or enforce: this reference carries no
  authorization result or enforcement result field.

## Secret and raw-evidence prohibitions

This contract never carries: `raw_payload`, `raw_protocol_payload`,
`packet`, `frame`, `credential`, `password`, `api_key`, `private_key`, or
`unredacted_device_secret`. Any of these appearing on a candidate object is
rejected as an unknown field, because the schema's
`additional_properties: false` policy closes the object to exactly the
fields listed above. This is enforced by regression tests, not merely
documented.

## Scope boundaries

This contract does not define adapter normalization logic, protocol
parsing, protocol-specific behavior, evidence storage, evidence retrieval,
evidence retention, evidence signing, evidence verification, runtime hashing
behavior, authorization result, or enforcement result. It does not introduce
the operation-aware `DecisionRequest`, `DecisionResponse`, `PolicyBundle`,
`PolicyRule`, `PolicyCondition`, `EvaluationTrace`, `TraceRuleEvidence`,
`AuditEvidence`, `GatewayAuditEvent`, a final reason-code vocabulary, or a
compatibility test-vector framework. Each of those belongs to a later PR (C
through G) per
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md).

## Examples

A minimal valid reference:

```yaml
reference_id: adev-0002-0000-0000-000000000002
evidence_digest:
  algorithm: sha3-256
  value: b1b6ffcf5155299a1e622c8f5b9f56f1fef0d0b0e3c1f2c6f4f6e5b0e2c1e11a
adapter_source: basis-adapters:bacnet
protocol: bacnet
redaction_classification: safe_after_redaction
```

Invalid references include: a missing or empty `reference_id`, a missing or
malformed `evidence_digest` (missing `algorithm`/`value`, an uppercase
algorithm label, or a non-hexadecimal digest value), a missing
`adapter_source`, a malformed `protocol` label (uppercase), a missing or
unsupported `redaction_classification`, an empty `request_id`, and any raw
protocol payload, device secret, or otherwise unknown field.

## Compatibility notes

This contract is purely additive: it does not change any existing contract's
shape, required fields, or serialized values, and it does not make any
existing contract depend on it. A future PR (C onward) may add a field to an
operation-aware request or audit contract that carries an
`adapter-evidence-reference`-shaped value; this PR does not add that field
itself.

## Why `experimental`?

The lifecycle describes this **published contract**, which is new in
`basis-schemas` — not a claim that the underlying need for a safe adapter
evidence reference is unsettled. See
[`contract-governance.md`](contract-governance.md).
