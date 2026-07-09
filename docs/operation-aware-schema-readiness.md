# Operation-Aware Schema Readiness

This document tracks the second wave of contracts entering `basis-schemas`:
the operation-aware contracts named in `basis-architecture`'s schema
readiness plan (ADR-0005,
`docs/architecture/operation-aware-schema-readiness-plan.md`). It is separate
from [`migration-plan.md`](migration-plan.md), which tracks the original
six-contract first wave (vocabulary through audit-event) and remains complete
and unchanged. This document exists so the second wave has its own tracked
order, the same way the first wave did, rather than being folded into a
migration plan that already declares itself complete.

This is a tracking document, not an architecture document. The operation-aware
model, its evaluation semantics, its trace/audit evidence categories, and its
policy bundle/rule model are decided in `basis-architecture` (ADR-0001 through
ADR-0005); this document records which of the contracts that plan names have
been published here, in what order, and what remains deferred.

---

## Recommended publication order (per ADR-0005, Section 5)

```text
PR A — Shared Metadata and Vocabulary                    [published]
PR B — Evidence Reference Contracts                      [published]
PR C — Operation-Aware DecisionRequest                   [not started]
PR D — Policy Bundle and Rule Contracts                  [not started]
PR E — DecisionResponse and EvaluationTrace               [not started]
PR F — Audit Evidence and GatewayAuditEvent               [not started]
PR G — Compatibility Examples and Test Vectors            [not started]
```

Each PR is scoped narrowly for independent review; later PRs depend on earlier
ones. See ADR-0005 Section 6 for the full dependency map.

## PR A — Shared Metadata and Vocabulary — published

PR A publishes the shared building blocks later operation-aware contracts
depend on, without introducing any of those larger contracts themselves:

- **[Contract metadata](contract-metadata.md)** —
  `schemas/contract-metadata/contract-metadata.yaml`. Formalizes the
  `contract:` block pattern (identifier + version + lifecycle + governance)
  already used by all six first-wave contracts, rather than inventing a new
  identifier or version convention.
- **[Redaction classification](redaction-classification.md)** —
  `schemas/redaction-classification/redaction-classification.yaml`. The
  five-value vocabulary (`safe_to_expose`, `safe_after_redaction`,
  `reference_only`, `never_store`, `never_display`) from ADR-0003, Section 10.
- **[Reason code](reason-code.md)** —
  `schemas/reason-code/reason-code.yaml`. The structural format a reason code
  must satisfy (lowercase snake_case token), from ADR-0003, Section 12 and the
  policy/rule model, Section 13. Deliberately not a closed enum: the final
  reason-code vocabulary is deferred to the contracts that carry it in
  practice.

All three are published at contract version `0.1.0`, lifecycle
`experimental`, and are additive: no existing contract's shape, required
fields, or serialized values changed.

### What PR A deliberately does not include

Consistent with ADR-0005's own scope for PR A, this wave does not introduce:

- The operation-aware `DecisionRequest` or `DecisionResponse`
- `PolicyBundle`, `PolicyRule`, or `PolicyCondition`
- `EvaluationTrace` or `TraceRuleEvidence`
- `AuditEvidence` or `GatewayAuditEvent`
- `AdapterEvidenceReference` or `IdentityEvidenceReference`
- A final, closed reason-code vocabulary
- Compatibility/test-vector fixtures (deferred to PR G — see below)

Each of these belongs to a later PR in the order above.

### Compatibility/test-vector metadata: deferred to PR G

ADR-0005 allows a shared compatibility/test-vector primitive in PR A "if
appropriate at this stage." It is not appropriate yet: this repository has no
existing compatibility-vector pattern beyond the ad hoc `examples: {valid,
invalid}` block each contract already carries for its own field-level tests,
and no later contract in this PR would duplicate a shared compatibility
primitive immediately. Building a dedicated compatibility/test-vector
contract now would be speculative. PR G, as described in
`basis-architecture`'s `docs/architecture/operation-aware-schema-readiness-plan.md`
(Section 5), remains the right place for canonical cross-repository examples
and test vectors, once there are enough operation-aware contracts published to
give those fixtures something real to cover.

## PR B — Evidence Reference Contracts — published

PR B publishes the two safe-reference contracts future operation-aware
request, trace, audit, and explanation contracts use to cite trusted identity
evidence and normalized adapter evidence, without duplicating raw tokens,
claims, credentials, or protocol payloads into those artifacts:

- **[Identity evidence reference](identity-evidence-reference.md)** —
  `schemas/identity-evidence-reference/identity-evidence-reference.yaml`. A
  safe reference to trusted identity evidence: `reference_id`,
  `evidence_digest`, an identity-provider-neutral `identity_source`,
  optional `normalization_version` / `mapping_version` provenance,
  `redaction_classification`, and optional `request_id` / `correlation_id`.
  Never carries an `access_token`, `id_token`, `refresh_token`, `jwt`,
  `bearer_token`, `authorization_header`, `cookie`, `session_secret`,
  `client_secret`, `password`, `private_key`, `raw_claims`, `full_claim_set`,
  or `credential` field.
- **[Adapter evidence reference](adapter-evidence-reference.md)** —
  `schemas/adapter-evidence-reference/adapter-evidence-reference.yaml`. A
  safe reference to normalized adapter evidence: `reference_id`,
  `evidence_digest`, an opaque `adapter_source`, an optional open `protocol`
  label, optional `normalization_version` / `mapping_version` provenance,
  `redaction_classification`, and optional `request_id` / `correlation_id`.
  Never carries a `raw_payload`, `raw_protocol_payload`, `packet`, `frame`,
  `credential`, `password`, `api_key`, `private_key`, or
  `unredacted_device_secret` field.

Both are published at contract version `0.1.0`, lifecycle `experimental`,
and declare `depends_on: [contract-metadata, redaction-classification]`.
Neither declares a dependency on `reason-code`, because neither carries a
`reason_code` field. Both are additive: no existing contract's shape,
required fields, or serialized values changed, and no existing contract was
made to depend on either of these two.

### Why two contracts, not one generic evidence-reference shape

Identity evidence and adapter evidence have different producers
(`basis-identity` and `basis-adapters` respectively) and different
provenance concepts (an identity source and normalization/claim-mapping
version, versus an adapter source, a protocol label, and a
normalization/protocol-mapping version). Collapsing them into one untyped
`type: identity | adapter` shape would let a consumer inspect free-form
metadata to recover which producer owns a given reference — losing the
clear, independently citable ownership the architecture calls for. The two
contracts share a structural pattern (`reference_id`, `evidence_digest`,
`redaction_classification`, optional `request_id` / `correlation_id`) but no
shared parent contract was introduced: this repository's static YAML pattern
does not use inheritance or composition machinery, and a third,
purely-for-reuse contract would be a speculative abstraction with no
independent semantic value of its own. If a genuinely reusable primitive
becomes justified by a later PR, it can be introduced additively at that
point.

### What PR B deliberately does not include

Consistent with ADR-0005's own scope for PR B, this wave does not introduce:

- The operation-aware `DecisionRequest` or `DecisionResponse`
- `PolicyBundle`, `PolicyRule`, or `PolicyCondition`
- `EvaluationTrace` or `TraceRuleEvidence`
- `AuditEvidence` or `GatewayAuditEvent`
- A final, closed reason-code vocabulary
- Compatibility/test-vector fixtures (deferred to PR G)
- Identity establishment, authentication, claim validation, or token
  verification (owned by `basis-identity`)
- Adapter normalization logic or protocol parsing (owned by `basis-adapters`)
- Evidence storage, retrieval, retention, signing, or verification
- Runtime hashing, canonicalization, or digest-verification behavior — both
  `evidence_digest` shapes are structural only

Each of these belongs to a later PR in the order above, or remains owned by
an implementation repository as already described in
[`architecture.md`](architecture.md).

### How PR C will consume these references

PR C (the operation-aware `DecisionRequest`) is expected to add optional
fields to the request shape that carry `identity-evidence-reference`- and
`adapter-evidence-reference`-shaped values, so a request can cite the
identity and adapter evidence that produced its context without embedding
that evidence directly. This PR does not add those fields itself, and no
implementation repository consumes `identity-evidence-reference` or
`adapter-evidence-reference` yet; PR B publishes the reference shapes only,
ahead of PR C needing them.

## PRs C through G — not started

The remaining PRs (the operation-aware decision request; policy bundle/rule
contracts; response and trace; audit evidence and gateway audit event;
compatibility examples and test vectors) are not yet started. Each becomes
ready for its own PR once the contracts it depends on, per ADR-0005 Section
6, are published. This document will be updated as each PR lands, the same
way [`migration-plan.md`](migration-plan.md) was updated across the first
wave.

## Relationship to the first wave

The first-wave contracts (vocabulary, action-string, resource-identifier,
decision-request, decision-response, audit-event — tracked in
[`migration-plan.md`](migration-plan.md) and in
`basis_schemas.PLANNED_CONTRACTS` / `basis_schemas.PUBLISHED_CONTRACTS`) are
unaffected by this second wave. The operation-aware contracts are an additive
expansion — v0.1-era request/response behavior remains stable throughout, per
ADR-0005 Section 7. The new shared contracts in PR A are tracked separately in
`basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS`, and PR B's
evidence-reference contracts are tracked separately again in
`basis_schemas.OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS`, so none of the
three waves' completeness claims ever conflate.
