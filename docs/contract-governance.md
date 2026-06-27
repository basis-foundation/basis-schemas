# Contract Governance

This document defines how contracts published in `basis-schemas` are governed:
the lifecycle states a contract moves through, the compatibility expectations
that apply in each state, and the process for making a breaking change. It
operationalizes, for this repository, the compatibility philosophy decided in
`basis-architecture` (`docs/architecture/compatibility-philosophy.md` and
`docs/architecture/action-vocabulary.md`). Where this document and the
architecture governance differ, the architecture governs.

The governing premise, carried from `basis-architecture`: a shared contract is a
**durable commitment**, not an implementation-convenience choice. The
ecosystem's operational timescales — audit records retained for years, policies
in effect for the lifetime of OT systems — mean the cost of a compatibility
break is paid by operators in the field. Changes to shared vocabulary are
therefore treated as significant events: explicit, versioned, and communicated
with lead time.

---

## Contract states

Every published contract carries one of three lifecycle states. The state is
declared in the contract's own metadata — concretely, the `contract.lifecycle`
field, as in the first published contract
[`../schemas/vocabulary/vocabulary.yaml`](../schemas/vocabulary/vocabulary.yaml)
(`lifecycle: experimental`) — and is the single signal a consumer reads to know
how much it can rely on the shape.

### Experimental

An **experimental** contract is published for early consumption and feedback but
carries **no compatibility guarantee**. Its shape may change in any way, including
incompatibly, between revisions without a major version increment.

- Use: a contract whose shape is still being proven against real consumers.
- Consumer expectation: pin to an exact revision; expect breaking changes; do not
  depend on it from anything with a long maintenance window.
- A contract enters this state when first published and leaves it only when its
  shape has been exercised by real consumers and decided stable in
  `basis-architecture`.

### Candidate

A **candidate** contract is believed stable and is a proposed final shape, but it
is not yet committed to as a durable contract. Changes should be additive;
breaking changes are still permitted but require a recorded rationale and a
deprecation signal to known consumers.

- Use: a contract that has stabilized in implementation and is awaiting
  confirmation as a durable commitment.
- Consumer expectation: safe to adopt with awareness that a breaking change,
  while discouraged, remains possible during a deprecation window.
- A candidate graduates to stable when `basis-architecture` confirms the shape as
  a durable commitment.

### Stable

A **stable** contract is a durable commitment. It may be extended only
additively, and it may be changed incompatibly only through the breaking-change
process below. Stability for shared BASIS contracts is measured in years to
decades, in line with OT audit-retention and device-lifecycle timescales.

- Use: a contract that the ecosystem treats as a fixed point.
- Consumer expectation: rely on it for the operational lifetime of a deployment;
  additive extensions will not break existing use.

```text
experimental ──▶ candidate ──▶ stable
 (no guarantee)  (proposed     (durable
                  final)        commitment)
```

A contract advances only forward through these states, and only on a decision
recorded in `basis-architecture`. A contract is never published directly as
stable on its first revision; stability is earned by being exercised.

## Compatibility expectations

Compatibility is a property of the **contract**, not of any one consumer, because
a change to a shared shape affects every consumer simultaneously. The following
classification applies across all states (the *consequences* of a breaking change
differ by state, but the classification does not):

**Additive (compatible) changes.** Adding an optional field, adding a new
enumerated value that existing consumers can ignore, or adding a new alias that
evaluates identically to an existing one. Identifier components must be
additive-extensible: new fields may be added; existing fields must not be removed
or semantically redefined.

**Breaking (incompatible) changes.** Removing or renaming a field; changing a
field's type or meaning; making an optional field required; removing or renaming
an enumerated value; narrowing or broadening the scope of an action so that
requests that previously matched no longer do, or vice versa; or changing a
default outcome. Any change that requires migrating existing policies or audit
records is breaking.

Two compatibility requirements are specific to this ecosystem and apply to every
stable contract:

- **Audit continuity.** An audit record produced under an earlier schema version
  must remain interpretable for its full retention period. A new schema version
  must be interpretable against records from prior versions, either through
  defined migration logic or through a stability commitment that makes migration
  unnecessary. The action-vocabulary version field exists precisely so historical
  records can be interpreted across vocabulary evolution.
- **Explicit version identity.** Every contract carries a version, and every
  consumer can identify which version it handles. Mismatches must be detectable
  rather than silent. Compatibility between two revisions is **stated, not
  inferred** — this is what compatibility snapshots (planned for a later phase)
  make testable.

## Breaking-change process

A breaking change to a stable contract is a significant, deliberate event. It is
never made silently. The process is:

1. **Decide in architecture first.** The change is reasoned about and decided in
   `basis-architecture`, in an ADR that records the rationale and the migration
   path. A breaking change that cannot be accompanied by a defined migration path
   is not made until the migration path is understood.
2. **Increment the major version.** A breaking change requires a major version
   increment of the contract. The prior version's identity is preserved so
   consumers and historical records remain attributable to it.
3. **Deprecate before removal.** The surface being changed or removed is marked
   deprecated and continues to function during a deprecation period. Deprecation
   is recorded explicitly in the schema changelog or the relevant ADR — not in a
   code comment or a verbal notice. Removal occurs only after the deprecation
   period ends.
4. **Make the period operationally meaningful.** Deprecation periods are measured
   in months or quarters, matching the pace at which constrained OT deployments
   can realistically migrate — not in weeks.
5. **Provide compatibility fixtures.** Where a migration path exists, it is
   accompanied by fixtures that let consumers test their handling of both the old
   and new shapes, so drift surfaces as a failing shared fixture rather than a
   production incident.

Additive changes do not require the major-version process: they take a minor
version increment and need no deprecation, because existing consumers are
unaffected.

## Summary

| State        | Compatibility guarantee | Permitted changes                            | Typical consumer stance        |
| ------------ | ----------------------- | -------------------------------------------- | ------------------------------ |
| experimental | none                    | any, including breaking, without major bump  | pin exact revision; expect churn |
| candidate    | additive expected       | additive freely; breaking with rationale + deprecation | adopt with awareness |
| stable       | durable                 | additive freely; breaking only via full process | rely on for deployment lifetime |

Governance authority rests with `basis-architecture` and the Basis Foundation
process. This repository publishes and enforces the states; it does not decide
contracts.
