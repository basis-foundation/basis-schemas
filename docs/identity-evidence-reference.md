# Identity Evidence Reference Contract

The **identity evidence reference** contract publishes a safe reference shape
for trusted identity evidence. It is the first of two evidence-reference
contracts from the operation-aware schema readiness plan (`basis-architecture`
ADR-0005, "PR B — Evidence Reference Contracts"); see
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md).

- Contract file: [`../schemas/identity-evidence-reference/identity-evidence-reference.yaml`](../schemas/identity-evidence-reference/identity-evidence-reference.yaml)
- Governed by: `basis-architecture`
- Published by: `basis-schemas`
- Version: `0.1.0`
- Lifecycle: `experimental`
- Depends on: [`contract-metadata`](contract-metadata.md), [`redaction-classification`](redaction-classification.md)

## Purpose

Future operation-aware request, trace, audit, and explanation contracts need
to answer "which trusted identity evidence supported this request?" without
duplicating that evidence's sensitive raw material into every artifact that
cites it. This contract publishes a **reference** shape: a stable identifier,
a structural digest, a provider-neutral source label, optional normalization
and claim-mapping provenance, a redaction classification, and optional
association with a decision request and a broader correlated operation.

The core rule: **reference evidence, do not duplicate secrets or raw
sensitive payloads.** This contract never carries an `access_token`,
`id_token`, `refresh_token`, `jwt`, `bearer_token`, `authorization_header`,
`cookie`, `session_secret`, `client_secret`, `password`, `private_key`,
`raw_claims`, `full_claim_set`, or `credential` field — any such field is
rejected as unknown, because `additional_properties: false` closes the shape
to exactly the fields below.

## What this contract does not define

Consistent with PR B's scope in
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md),
this contract does not define: identity establishment, authentication, claim
validation, token verification, evidence storage, evidence retrieval,
evidence retention, evidence signing, evidence verification, runtime hashing
behavior, authorization evaluation, or enforcement. It also does not
introduce the operation-aware `DecisionRequest`/`DecisionResponse`, any
policy or trace/audit contract, or a final reason-code vocabulary — those
remain scoped to later PRs (C through G).

## Canonical shape

| Field                     | Required | Type              | Meaning |
| ------------------------- | -------- | ------------------ | ------- |
| `reference_id`            | yes      | string (non-empty) | Stable identifier for the evidence artifact. |
| `evidence_digest`         | yes      | object              | Structural digest — see below. |
| `identity_source`         | yes      | string (non-empty) | Opaque, provider-neutral label for the identity source/authority. |
| `redaction_classification`| yes      | enum                | One of the five published redaction-classification values. |
| `normalization_version`   | no       | string or null      | Identity-normalization mapping version, when tracked. |
| `mapping_version`         | no       | string or null      | Claim-mapping version, when applicable. |
| `request_id`              | no       | string or null      | Associated decision request, when already known. Non-empty when present. |
| `correlation_id`          | no       | string or null      | Broader cross-system trace id, passed through verbatim. |

Unknown fields are rejected.

### `evidence_digest` shape

| Field       | Required | Type   | Meaning |
| ----------- | -------- | ------ | ------- |
| `algorithm` | yes      | string | Open, lowercase kebab-case algorithm label (e.g. `sha-256`). Not a closed enum. |
| `value`     | yes      | string | Lowercase hexadecimal digest value, no prefix or whitespace. |

`evidence_digest` is **structural metadata only**. This contract does not
implement, canonicalize, or verify hashing, does not claim tamper evidence or
cryptographic authenticity, and does not define a canonicalization rule.
Evidence producers (`basis-identity`) own deterministic digest generation;
this contract only validates that a published digest reference has the
right shape.

## Reference identifier semantics

`reference_id` is explicit, deterministic, and stable for the referenced
evidence artifact: independent of Python import path, source filename, or
temporary storage path, and safe to place in a future request, trace, or
audit artifact because it is not itself a secret. It follows this
repository's existing `request_id` / `event_id` convention: UUID v4 is
recommended, but no regular expression is enforced, so future evidence
producers are not blocked by a premature identifier grammar.

## Redaction-classification semantics

`redaction_classification` reuses the five values published by
[`redaction-classification`](redaction-classification.md) — it does not
redefine or duplicate that vocabulary. It describes **handling requirements
for the referenced identity evidence artifact**, not permission to expose raw
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
  identity evidence is commonly produced before a specific authorization
  request exists — for example, at login or session-establishment time.
- `correlation_id` associates evidence with a broader end-to-end operation or
  workflow, passed through verbatim, mirroring `audit-event`'s
  `correlation_id` exactly (no non-emptiness constraint).

This contract does not redefine `request_id` or `correlation_id`; it reuses
their existing semantics and does not introduce a new identifier contract.

## Producer and consumer ownership

- **`basis-identity`** produces trusted identity evidence and mints
  `reference_id` / `evidence_digest` values. It remains the sole owner of
  identity establishment, authentication, claim validation, and token
  verification — none of that behavior is defined here.
- **`basis-gateway`** will later assemble these references into
  operation-aware requests and gateway audit events (PR C onward).
- **`basis-core`** consumes references as request context; it does not
  retrieve, authenticate, normalize, or interpret raw identity evidence.
- **`basis-console`** will later display redacted reference metadata and
  explanations; it does not retrieve or expose prohibited evidence.

This contract is identity-provider-neutral by design: `identity_source` is an
opaque label, not an OIDC- or JWT-specific field, so identity providers
beyond OIDC remain representable without a contract change.

## Secret and raw-evidence prohibitions

This contract never carries: `access_token`, `id_token`, `refresh_token`,
`jwt`, `bearer_token`, `authorization_header`, `cookie`, `session_secret`,
`client_secret`, `password`, `private_key`, `raw_claims`, `full_claim_set`,
or `credential`. Any of these appearing on a candidate object is rejected as
an unknown field, because the schema's `additional_properties: false` policy
closes the object to exactly the fields listed above. This is enforced by
regression tests, not merely documented.

## Scope boundaries

This contract does not define identity establishment, authentication, claim
validation, token verification, adapter normalization logic, protocol
parsing, evidence storage, evidence retrieval, evidence retention, evidence
signing, evidence verification, runtime hashing behavior, authorization
evaluation, or enforcement. It does not introduce the operation-aware
`DecisionRequest`, `DecisionResponse`, `PolicyBundle`, `PolicyRule`,
`PolicyCondition`, `EvaluationTrace`, `TraceRuleEvidence`, `AuditEvidence`,
`GatewayAuditEvent`, a final reason-code vocabulary, or a compatibility
test-vector framework. Each of those belongs to a later PR (C through G) per
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md).

## Examples

A minimal valid reference:

```yaml
reference_id: idev-0002-0000-0000-000000000002
evidence_digest:
  algorithm: sha3-256
  value: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b85
identity_source: basis-local
redaction_classification: safe_after_redaction
```

Invalid references include: a missing or empty `reference_id`, a missing or
malformed `evidence_digest` (missing `algorithm`/`value`, an uppercase
algorithm label, or a non-hexadecimal digest value), a missing
`identity_source`, a missing or unsupported `redaction_classification`, an
empty `request_id`, and any raw-token, raw-claims, or otherwise unknown
field.

## Compatibility notes

This contract is purely additive: it does not change any existing contract's
shape, required fields, or serialized values, and it does not make any
existing contract depend on it. A future PR (C onward) may add a field to an
operation-aware request or audit contract that carries an
`identity-evidence-reference`-shaped value; this PR does not add that field
itself.

## Why `experimental`?

The lifecycle describes this **published contract**, which is new in
`basis-schemas` — not a claim that the underlying need for a safe identity
evidence reference is unsettled. See
[`contract-governance.md`](contract-governance.md).
