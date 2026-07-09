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
PR B — Evidence Reference Contracts                      [not started]
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

## PRs B through G — not started

The remaining PRs (evidence references; the operation-aware decision request;
policy bundle/rule contracts; response and trace; audit evidence and gateway
audit event; compatibility examples and test vectors) are not yet started.
Each becomes ready for its own PR once the contracts it depends on, per
ADR-0005 Section 6, are published. This document will be updated as each PR
lands, the same way [`migration-plan.md`](migration-plan.md) was updated across
the first wave.

## Relationship to the first wave

The first-wave contracts (vocabulary, action-string, resource-identifier,
decision-request, decision-response, audit-event — tracked in
[`migration-plan.md`](migration-plan.md) and in
`basis_schemas.PLANNED_CONTRACTS` / `basis_schemas.PUBLISHED_CONTRACTS`) are
unaffected by this second wave. The operation-aware contracts are an additive
expansion — v0.1-era request/response behavior remains stable throughout, per
ADR-0005 Section 7. The new shared contracts in PR A are tracked separately in
`basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS`, so the two waves'
completeness claims never conflate.
