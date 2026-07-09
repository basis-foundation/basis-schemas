# Reason Code Contract

The **reason code** contract publishes the structural format every BASIS
reason code must satisfy: a single, stable, machine-readable lowercase
snake_case token. It is a shared foundation contract from the operation-aware
schema readiness plan (`basis-architecture` ADR-0005, "PR A — Shared Metadata
and Vocabulary"); see
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md).

- Contract file: [`../schemas/reason-code/reason-code.yaml`](../schemas/reason-code/reason-code.yaml)
- Governed by: `basis-architecture`
- Published by: `basis-schemas`
- Version: `0.1.0`
- Lifecycle: `experimental`
- Depends on: [`contract-metadata`](contract-metadata.md)

## Purpose

Trace, audit, decision, and policy outcomes all need a stable, testable value
to key off of — something more precise than free-text explanation but not yet
tied to any one contract's final vocabulary. ADR-0003
(`docs/architecture/operation-aware-trace-audit-evidence.md`, Section 12) and
the policy/rule model (Section 13) both name reason codes as this kind of
governed, machine-readable surface, and both are explicit that their own
illustrative examples (`ALLOW_RULE_MATCHED`, `DENY_RULE_MATCHED`, and similar)
are "examples only, not a final vocabulary."

This contract publishes exactly that: the **format**, not the vocabulary. A
reason code is a single token matching this contract's pattern; which
specific codes exist is left to the future contracts that carry a
`reason_code` field in practice (decision response, evaluation trace, policy
rule outcomes — see [`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md)).

## Format

| Property   | Value |
| ---------- | ----- |
| Structure  | `{token}` — a single segment, no colons or hyphens |
| Pattern    | `^[a-z][a-z0-9]*(_[a-z0-9]+)*$` |
| Casing     | lowercase snake_case |

A reason code must be non-empty, must start with a lowercase letter, and may
contain only lowercase letters, digits, and single underscores separating
words — no leading, trailing, or doubled underscore, no uppercase, no colon,
and no hyphen.

## Extensibility

This is deliberately **not a closed enum**. A string that matches the pattern
is a structurally valid reason code even if it is not one of the illustrative
examples below. A future contract that wants to constrain its own
`reason_code` field to a specific, closed vocabulary is free to do so — that
constraint belongs to that contract, not to this one. This contract only
guarantees that any reason code, from any future contract, has one
predictable shape that trace, audit, and test tooling can rely on without
knowing the specific vocabulary in advance.

## Casing: a publication choice, not a vocabulary decision

ADR-0003's illustrative examples are written in upper-snake-case
(`ALLOW_RULE_MATCHED`). This contract's examples use lower-snake-case
(`allow_rule_matched`) instead, for consistency with every other enumerated
value already published in this repository — the vocabulary contract's
verbs, decision-response's `outcome` and `failure_reason`, and audit-event's
`outcome` are all lowercase. ADR-0003 explicitly does not finalize a
vocabulary or a serialization; choosing a consistent, repository-wide
serialization casing is a `basis-schemas` publication decision, not a
redefinition of anything ADR-0003 decided.

## Reason codes vs. human-readable explanations

A reason code is machine-readable and stable; it is a separate concept from a
free-text, human-readable explanation string, such as decision-response's
`reason` field. A reason code is never a substitute for an explanation, and an
explanation string is never a substitute for a reason code — future contracts
that need both should carry both, as distinct fields.

## Relationship to existing `failure_reason`

`basis-core`'s decision-response contract already publishes a `failure_reason`
field (see [`decision-response.md`](decision-response.md)): a closed,
four-value enum — `malformed_request`, `policy_error`, `audit_error`,
`internal_error` — that is null for a normal policy decision and set only
when a denial was caused by an enforcement-boundary failure rather than
ordinary policy evaluation. It is a specific field on one published contract,
with values already in production use.

This `reason-code` contract is additive to `failure_reason`, not a
replacement for it:

- `failure_reason` is unchanged. Its four values, their meanings, and
  decision-response's required-field and validation behavior remain exactly
  as currently published; no existing consumer is affected.
- No `failure_reason` value is renamed, removed, or reinterpreted here.
- `reason-code` is broader in scope and narrower in commitment: where
  `failure_reason` is one closed enum scoped to one field of one contract,
  `reason-code` is a general-purpose *format* that future decision, rule,
  trace, audit, and validation-explanation surfaces may use for their own
  machine-readable values — it does not itself define any of those fields.

It happens that all four `failure_reason` values already satisfy this
contract's pattern (they are lowercase snake_case tokens), but that is an
observation about the existing values, not a claim that `failure_reason` has
been redefined to depend on, or be governed by, `reason-code`. Whether a
future operation-aware contract adopts the `reason-code` format for a
`failure_reason`-like field, or for a new field alongside it, is a decision
for that future contract to make — this PR changes nothing about
decision-response today.

## Compatibility

Once a future contract publishes a reason code built on this format, changing
or removing that code is a breaking, compatibility-sensitive change under
[`contract-governance.md`](contract-governance.md) — the same treatment as
any other enumerated value in this repository. This contract's own format
(the pattern itself) is likewise subject to that same governance.

## Examples

Illustrative examples (echoing ADR-0003's categories, re-cased; not
exhaustive or final): `allow_rule_matched`, `deny_rule_matched`,
`no_allow_rule_matched`, `missing_required_context`, `unknown_resource_type`,
`unsupported_schema_version`, `policy_bundle_invalid`, `evaluation_error`.

A structurally valid code outside that list, such as
`future_unrecognized_reason_code`, is also accepted — demonstrating that the
format is open.

Invalid: an empty value, uppercase (`ALLOW_RULE_MATCHED`), a leading digit
(`1_invalid_start`), a colon-containing value (`read:ahu`), hyphens instead of
underscores (`deny-rule-matched`), and a leading, trailing, or doubled
underscore.

## Why `experimental`?

The lifecycle describes this **published contract**, which is new in
`basis-schemas` — not the underlying concept of a reason code, which ADR-0003
and the policy/rule model already established as a governed surface. See
[`contract-governance.md`](contract-governance.md).
