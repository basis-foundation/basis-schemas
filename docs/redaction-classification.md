# Redaction Classification Contract

The **redaction classification** contract publishes the five-value vocabulary
evidence is sorted into before it may appear in a trace, audit, or explanation
artifact. It is a shared foundation contract from the operation-aware schema
readiness plan (`basis-architecture` ADR-0005, "PR A — Shared Metadata and
Vocabulary"); see
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md).

- Contract file: [`../schemas/redaction-classification/redaction-classification.yaml`](../schemas/redaction-classification/redaction-classification.yaml)
- Governed by: `basis-architecture`
- Published by: `basis-schemas`
- Version: `0.1.0`
- Lifecycle: `experimental`
- Depends on: [`contract-metadata`](contract-metadata.md)

## Purpose

Operation-aware trace and audit evidence (ADR-0003,
`docs/architecture/operation-aware-trace-audit-evidence.md`, Section 10) must
never contain secrets, and every other piece of evidence must be classified so
producers and consumers agree on how it may be persisted or displayed. This
contract publishes that classification vocabulary as a machine-readable value
set, so future request, response, trace, audit, and evidence-reference
contracts can carry a `redaction_classification` field instead of leaving the
decision to each publisher's discretion.

This contract carries **vocabulary only**. It does not implement a redaction
function, does not decide which classification applies to any specific field
in a future contract, and does not perform masking, hashing, or minimization.

## The five classifications

| Value                 | Meaning |
| --------------------- | ------- |
| `safe_to_expose`       | May appear in authorized operator, audit, trace, or explanation views without additional redaction. Not a claim that the value is public. |
| `safe_after_redaction` | May be retained or displayed only after deterministic redaction or minimization removes sensitive content. |
| `reference_only`       | The raw value must not be duplicated into evidence artifacts; use a stable identifier, hash, or reference instead. |
| `never_store`          | Must not be persisted in any evidence artifact, even redacted, because no redaction makes it safe or useful. |
| `never_display`        | Must never be rendered in an operator-, console-, or audit-review-facing view, though it may exist in a durable record for a narrow purpose such as cryptographic verification. |

Values are serialized in lowercase snake_case, matching this repository's
existing enum convention (the vocabulary contract's verbs; decision-response's
`outcome` and `failure_reason`; audit-event's `outcome`).

## `never_store` vs. `never_display`

These two are easy to conflate and are deliberately kept distinct:

- **`never_store`** is about persistence. The value must not enter a trace,
  audit, explanation, or compatibility-example artifact at all — not even in
  redacted form.
- **`never_display`** is about rendering. The value may legitimately be
  persisted for a narrow purpose (for example, a value needed later for
  cryptographic verification), but it must never be shown in an operator,
  console, training-mode, or audit-review view.

A value can be `never_display` without being `never_store`. The reverse
combination is not meaningful: a value that must never be stored has nothing
left to display.

## Closed vocabulary

Unlike [`reason-code`](reason-code.md), this vocabulary is closed: exactly
five classifications are defined, and a value outside this set is invalid.
Adding a sixth classification is a security-relevant architecture decision,
made in `basis-architecture`, not a change made silently in `basis-schemas`.

## Examples

Valid: `safe_to_expose`, `safe_after_redaction`, `reference_only`,
`never_store`, `never_display`.

Invalid: `SAFE_TO_EXPOSE` (wrong case), `safe-to-expose` (wrong separator),
`public` (not one of the five published classifications), and an empty value.

## Scope boundary

This contract does not define how a producer decides which classification
applies to a specific field of a future contract (that belongs to the
contract that defines the field), and it does not define or implement the
redaction mechanism itself (that belongs to whichever component produces or
renders the evidence). It defines the classification vocabulary those
decisions are expressed in.

## Why `experimental`?

The lifecycle describes this **published contract**, which is new in
`basis-schemas` — not the classification vocabulary itself, which ADR-0003
already settled. See [`contract-governance.md`](contract-governance.md).
