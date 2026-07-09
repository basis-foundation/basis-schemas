# Policy Bundle Contract

The **policy bundle** contract publishes the unit-of-policy-identity,
versioning, scope, ownership, provenance, validation, compatibility, and
rule-grouping shape a future `basis-core` v0.2.0 policy validator and
evaluator will operate on, and a future `basis-gateway` will load and
select at runtime. It is the third and final contract of PR D of
`basis-architecture`'s operation-aware schema readiness plan (ADR-0005,
"PR D — Policy Bundle and Rule Contracts"); see
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md).

- Contract file: [`../schemas/policy-bundle/policy-bundle.yaml`](../schemas/policy-bundle/policy-bundle.yaml)
- Governed by: `basis-architecture`
- Published by: `basis-schemas`
- Version: `0.1.0`
- Lifecycle: `experimental`
- Depends on: [`contract-metadata`](contract-metadata.md), [`policy-rule`](policy-rule.md)

## 1. Purpose

ADR-0004 (`docs/architecture/operation-aware-policy-rule-model.md`,
Section 2, "Policy Bundle Concept") defines a **policy bundle** as "the unit
of policy distribution, versioning, validation, and compatibility. It is the
thing `basis-core` evaluates a `DecisionRequest` against, the thing
`basis-gateway` loads and selects at runtime, and the thing compatibility
tests are written against as a stable target." This contract publishes that
bundle's *shape*: a stable identifier, an explicit bundle content version
distinct from the bundle-format schema version, a policy owner/authority
reference, an optional structured applicability scope, a non-empty
collection of policy-rule-shaped rules, and optional
descriptive/provenance/deprecation metadata.

## 2. Contract file

[`../schemas/policy-bundle/policy-bundle.yaml`](../schemas/policy-bundle/policy-bundle.yaml)

## 3. Governance

Governed by `basis-architecture`. This contract does not decide bundle
loading, validation, or evaluation behavior; it publishes the shape ADR-0004
Sections 2, 3, and 12 already named.

## 4. Version

`0.1.0`

## 5. Lifecycle

`experimental`

## 6. Dependencies

```yaml
depends_on:
  - contract-metadata
  - policy-rule
```

`policy-rule`: a bundle's `rules` are policy-rule-shaped values, referenced
not redefined. No other contract is declared as a direct dependency: this
contract's `scope` selectors reproduce the same patterns
([`policy-rule`](policy-rule.md)'s own already-parity-tested
`action_pattern` / `resource_type_pattern` / `open_identifier_pattern`
copies) rather than re-declaring a separate direct dependency on
`action-string` or `resource-identifier` at the bundle level — the
canonical source of those patterns is reached transitively, through the
already-declared `policy-rule` dependency, exactly as `policy-rule` itself
reaches `operation-aware-decision-request`'s categories transitively for
some of its own selectors.

## 7. Canonical shape

A bundle is a single object. `bundle_id`, `bundle_version`,
`schema_version`, `policy_owner`, and `rules` are always required — the
smallest usable policy identity plus its rule content. `scope` is optional
(see [Section 12](#12-bundle-scope) and
[Section 13](#13-global-scope-representation)). `description`, `source_ref`,
`approval_ref`, `created_at`, `updated_at`, `compatibility_target`,
`deprecated`, and `replaced_by` are optional metadata/provenance/deprecation
fields. Unknown fields are rejected (`additional_properties: false`).

| Field | Required | Type | Meaning |
| --- | --- | --- | --- |
| `bundle_id` | yes | string (non-empty) | Stable, machine-readable bundle identity. |
| `bundle_version` | yes | string (semver) | This bundle's own authored content version. |
| `schema_version` | yes | string (semver) | The policy-bundle contract shape version this instance targets. |
| `policy_owner` | yes | string (non-empty) | Provenance/governance owner reference. Not an authorization subject. |
| `scope` | no | object or null | Optional applicability scope — absent means globally applicable. |
| `rules` | yes | array (non-empty) | Policy-rule-shaped values this bundle groups. |
| `description` | no | string or null | Human-readable summary. |
| `source_ref` | no | string or null | Informative authoring/source reference. |
| `approval_ref` | no | string or null | Informative approval/review reference. |
| `created_at` / `updated_at` | no | string or null (date-time) | Timezone-aware ISO 8601 provenance timestamps. |
| `compatibility_target` | no | string or null | Informative compatibility-target label. |
| `deprecated` | no | boolean (default `false`) | Explicit deprecation flag. Does not imply removal. |
| `replaced_by` | no | string or null | `bundle_id` of a known specific replacement. |

There is **no `validation_status` field** — see
[Section 17](#17-validation-status-as-derived-state).

## 8. Bundle identity

`bundle_id` must be a non-empty, stable, machine-readable string,
independent of any local filename or repository path, suitable for use in
a future `DecisionResponse`, evaluation trace, audit record, compatibility
test, or console explanation. No UUID requirement: a short, stable,
human-readable token (for example `west-campus-hvac-operations`) is
preferred. `bundle_id` identifies "the same bundle" across successive
content revisions (ADR-0004 Section 2) — it is distinct from
`bundle_version`, which identifies a specific revision of that same
bundle's content.

## 9. Bundle version

`bundle_version` is the version of **this bundle's own authored rule
content**, in semantic-version form (`MAJOR.MINOR.PATCH`, pattern
`^\d+\.\d+\.\d+$`, following this repository's existing `contract-metadata`
version convention). It advances whenever the bundle's rules or scope
change in a way the bundle's own authors consider a new revision. This
contract implements no version negotiation or compatibility resolution — it
only publishes the field.

## 10. Schema version

`schema_version` is the version of the **policy-bundle contract shape**
this bundle instance was authored against — for example, `0.1.0` for a
bundle authored against this PR's shape. It is required so a future
`basis-core` validator can determine, before evaluation begins, whether it
supports this bundle's shape at all (per the operation-aware evaluation
semantics document, Section 12, "schema version compatibility," and
evaluation phase 2, "validate policy bundle shape and version" — see
`docs/architecture/operation-aware-evaluation-semantics.md`, Section 3).
This mirrors `audit-event`'s own precedent of carrying a `schema_version`
field distinct from the contract's own metadata version.

## 11. Package version distinction

`bundle_version`, `schema_version`, and the `basis-schemas` package version
(`__version__` in `src/basis_schemas/__init__.py`) are three independent
concepts that this contract never conflates:

- `bundle_version` — this specific bundle's authored content revision.
- `schema_version` — the policy-bundle contract shape a bundle instance
  targets.
- `basis-schemas` package version — the release version of this
  repository's published package, unrelated to any individual bundle.

## 12. Policy owner

`policy_owner` is a stable, non-empty reference to who authored or is
accountable for this bundle's content (ADR-0004 Section 12,
"Author/source reference"). It is **provenance and governance metadata
only**: `policy_owner` is **not** an authorization subject, grants no
permission by its mere presence, and must not contain credential material.
An opaque label (a team name, a system identifier, or an owning-repository
reference) is sufficient; this contract does not require or assume any
specific identity-system shape for this field.

## 13. Bundle scope

`scope`, when present, is a small, explicit, nested object of applicability
selectors — `actions`, `resource_types`, `site_ids`, `building_ids`,
`zone_ids`, `area_ids`, `device_classes`, `environment_modes`,
`authority_modes`, `protocols` — covering the scope categories ADR-0004
Section 3 names as justified (domain/action-vocabulary scope, resource-type
scope, site/building/zone/area scope, device-class scope,
environment/deployment scope, identity authority-mode scope, and protocol
scope). No separate `domain` selector is published: domain-level scoping is
expressed through `actions`' domain segment or `resource_types`, consistent
with including only selectors actually grounded in a request category. No
`metadata`/`extensions`/`custom`/`arbitrary_context` bag is published.

**Scope determines whether a bundle applies to a request at all — it is
distinct from a rule's own `match` criteria (published by
[`policy-rule`](policy-rule.md)), which determine which `allow`/`deny`
rules inside an already-applicable bundle are candidates for that request.**
See [Section 14](#14-scope-vs-rule-matching).

## 14. Global-scope representation

**Absent `scope` (or an explicit `scope: null`) means this bundle is
globally applicable.** A present `scope` restricts applicability to
requests whose context matches every one of its populated selectors. This
is a `basis-schemas` publication choice, adopted because ADR-0004 Section 3
states the applicability principle ("a bundle outside its declared scope
should not pretend to deny or allow a request; it should be semantically
not applicable") without choosing a concrete field-level representation —
this contract adopts the minimal representation consistent with that
principle:

```yaml
scope_semantics:
  absent_scope: globally_applicable
  present_scope: applicable_if_all_populated_selectors_match
  non_matching_scope_outcome: not_applicable
  empty_scope_object: invalid
```

**Absent `scope` is not invalid; it is a deliberate, documented way to
express "this bundle applies everywhere."** A present-but-entirely-empty
`scope: {}` object, by contrast, **is** rejected — an empty scope object is
ambiguous (does it mean "restrict to nothing" or "no restriction"?), so
this contract requires omission of the `scope` field entirely to express
global applicability, and requires at least one populated selector whenever
`scope` is present at all.

## 15. Scope vs. rule matching

Restated for emphasis, because this is the single most important
distinction this contract's `scope` field embodies: `scope` is a
**bundle-applicability** gate (does this bundle apply to the request at
all?), evaluated conceptually *before* any of the bundle's rules are
considered. A rule's own `match` (published by
[`policy-rule`](policy-rule.md)) is a **rule-candidacy** filter within an
already-applicable bundle (which specific `allow`/`deny` rules inside this
bundle are candidates for this request?). The two shapes are declared
independently and are not the same selector set (`scope_shape` omits
`subject_ids`, `subject_roles`, `identity_sources`, `device_ids`,
`protocol_operations`, `operation_intents`, `safety_modes`, and
`safety_classifications` — all rule-level concerns, not bundle-applicability
concerns).

## 16. Relationship to NOT_APPLICABLE

Whether a present-but-non-matching `scope` actually resolves a request to
`NOT_APPLICABLE` is **evaluation semantics** (ADR-0002 Section 5,
`docs/architecture/operation-aware-evaluation-semantics.md`), not something
this schema implements. This document states the expected semantic
contract (`non_matching_scope_outcome: not_applicable`) so a future
`basis-core` evaluator has a documented target, but no evaluation logic
exists anywhere in this contract — there is no evaluator here to produce a
`NOT_APPLICABLE`, `ALLOW`, or `DENY` outcome.

## 17. Rules

`rules` is required and must be a **non-empty** array of
policy-rule-shaped values (see [`policy-rule.md`](policy-rule.md)) —
referenced, not redefined; this contract reuses `policy-rule`'s exact
published field policy. At least one rule is required: a bundle with zero
rules cannot produce a substantive decision. **Declaration order in this
array is never authoritative** — array position is not rule identity,
consistent with `policy-rule`'s own rule-ordering deferral (see
[`policy-rule.md`](policy-rule.md), "Rule ordering decision").

## 18. Duplicate rule-ID validation

`rule_id` values across a bundle's `rules` array must be unique. This is
**bundle-level validation**: a cross-rule uniqueness concern a single rule
object's own schema cannot express or enforce on its own (a standalone rule
has no sibling rules to compare itself against). This contract's companion
test suite (`tests/test_policy_bundle_contract.py`) enforces this
programmatically; static YAML/JSON-Schema notation cannot cleanly express
an array-uniqueness-by-subfield constraint, so this is documented here and
tested, rather than expressed as a single declarative schema rule — the
same "strongest truthful field policy plus focused contract-validation
tests" approach this repository already uses for `policy-rule`'s
`condition_id` uniqueness (see [`policy-rule.md`](policy-rule.md),
Section 15).

## 19. Metadata/provenance

`description`, `source_ref`, `approval_ref`, `created_at`, `updated_at`,
and `compatibility_target` are the smallest useful set of metadata fields
justified by ADR-0004 Section 12 ("Policy Metadata and Provenance").
ADR-0004 also names "Environment/site scope" (already covered by `scope`,
[Section 13](#13-bundle-scope)) as a metadata category; this contract does
not duplicate that as a separate metadata field. None of these fields
grants any permission or has any evaluation effect — they are informative
provenance only, and none is validated against an external system by this
contract (for example, `approval_ref` is not checked against any actual
approval-tracking system; it is a reference field a deployment's own
process may populate).

## 20. Validation status as derived state

**This contract deliberately does not publish a `validation_status`
field.** A bundle cannot make itself valid by declaring itself valid:
whether a bundle is valid is **derived** by a future `basis-core`
validator/runtime process, evaluated against the bundle's actual content
at validation time — never self-asserted by the bundle's own authored
content. Publishing a self-attested `validation_status` field would let a
bundle author (or a corrupted/stale bundle) claim validity independent of
whatever a real validator would determine, which is exactly the kind of
misleading self-certification a security-relevant configuration artifact
must not be able to produce. `validation_status` is therefore explicitly
listed among this contract's forbidden/unknown fields and is rejected if
present — enforced by regression tests, not merely documented.

## 21. Deprecation metadata

`deprecated` (boolean, default `false`) is an explicit flag; its presence
**does not imply removal** and this contract implements no migration,
redirection, or enforcement behavior based on it. `replaced_by` (optional
string) names the `bundle_id` of a known specific replacement, when one
exists. This contract does **not** enforce that `replaced_by` is populated
only when `deprecated` is `true`, and does **not** validate that the
referenced `bundle_id` actually exists anywhere — producers are expected to
keep the two fields logically consistent, but that alignment is a producer
responsibility, not something this static contract validates. No migration
behavior is implied or implemented by either field.

## 22. Validation

**Schema-level** (this contract, per-object): required fields present;
`bundle_version` / `schema_version` semver pattern; `policy_owner`
non-empty; `scope` shape and selector patterns; `rules` array-of-object
type; metadata field types; `deprecated` boolean type; unknown fields
rejected (including a rejected `validation_status`).

**Bundle-level** (this contract, cross-field within one bundle object):
`rules` non-empty; every populated `scope` selector array non-empty; an
entirely empty `scope: {}` object rejected; `rule_id` uniqueness across the
`rules` array.

**Evaluation semantics** (not implemented here, deferred to future
`basis-core`): scope-applicability determination, `NOT_APPLICABLE`
resolution, rule matching, condition evaluation, deny precedence, default
deny, final outcome. **Invalid policy bundles must never produce ALLOW** —
this restates ADR-0004 Section 11 ("Invalid policy bundles must not produce
ALLOW decisions") and the operation-aware evaluation semantics document
Section 14 (safe error handling: an evaluation failure is a distinct
outcome category from `ALLOW`, `DENY`, and `NOT_APPLICABLE`); this contract
does not implement that safety property — it documents the requirement a
future `basis-core` validator/evaluator must satisfy.

## 23. Compatibility

Purely additive. This contract does not modify any existing published
contract, and no existing contract is made to depend on it. It is not
mandatory anywhere; no implementation repository consumes it yet.

## 24. Security

This contract defines no `access_token`, `id_token`, `refresh_token`, `jwt`,
`bearer_token`, `authorization_header`, `cookie`, `session_secret`,
`client_secret`, `password`, `private_key`, `api_key`, `raw_claims`,
`full_claim_set`, `raw_payload`, `raw_protocol_payload`, `device_secret`,
`credential`, `script`, `code`, `executable`, `command`, `shell`, `python`,
`javascript`, `rego`, `cedar`, `cel`, `wasm`, `sql`, `template`,
`expression`, or `validation_status` field, anywhere. Any such field is
rejected as unknown — enforced by regression tests, not merely documented.

## 25. Examples

A small global bundle (no `scope`, meaning globally applicable):

```yaml
bundle_id: baseline-read-only-telemetry
bundle_version: "1.0.0"
schema_version: "0.1.0"
policy_owner: platform-security-team
rules:
  - rule_id: rule-operator-read-ahu-telemetry
    effect: allow
    match:
      subject_roles:
        - operator
      actions:
        - read:ahu
    reason_code: allow_rule_matched
```

A site-scoped OT operations bundle, containing both an allow and a deny
rule:

```yaml
bundle_id: west-campus-hvac-operations
bundle_version: "2.3.1"
schema_version: "0.1.0"
policy_owner: west-campus-ot-team
description: HVAC operation rules scoped to the west campus site.
scope:
  site_ids:
    - west-campus
  resource_types:
    - hvac
rules:
  - rule_id: rule-west-campus-hvac-allow
    effect: allow
    match:
      subject_roles:
        - operator
      resource_types:
        - hvac
      operation_intents:
        - state_changing
    reason_code: allow_rule_matched
  - rule_id: rule-west-campus-hvac-deny-interlock
    effect: deny
    match:
      safety_modes:
        - interlock-engaged
      operation_intents:
        - control_affecting
    reason_code: deny_rule_matched
```

The full contract file carries four valid examples (including a bundle with
provenance metadata and a deprecated bundle with a `replaced_by` reference)
and thirteen invalid examples covering missing/empty `bundle_id`, an
invalid `bundle_version`, an invalid `schema_version`, a missing
`policy_owner`, missing/empty `rules`, duplicate `rule_id` values, a
malformed `scope` (an unknown selector key), a malformed nested rule, an
unknown field (including a rejected `validation_status`), a rejected
`private_key` field, and an empty `scope: {}` object. All examples use
clearly synthetic values.

## 26. Scope boundaries

This contract does not implement policy loading, storage, distribution,
synchronization, signing, signature verification, tamper-evident packaging,
an approval workflow, an authoring UI, a simulation UI, deployment
behavior, multi-bundle hierarchy, policy federation, tenant/site policy
delegation, or runtime evaluation — every one of these remains explicitly
deferred, per ADR-0004 Section 18. It does not publish an operation-aware
`DecisionResponse`, `EvaluationTrace`, `TraceRuleEvidence`, `AuditEvidence`,
or `GatewayAuditEvent` — each belongs to a later PR (E through G) per
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md).
PR E is expected to reference this contract's `bundle_id`,
`bundle_version`, and `policy-rule`'s `rule_id` values in a future
`DecisionResponse`'s policy-identification fields and in evaluation trace
rule evidence, without this PR choosing that shape.

## 27. Why `experimental`?

The lifecycle describes this **published contract**, which is new and
unconsumed by any implementation repository — not a claim that the
underlying conceptual category (ADR-0004's bundle concept) is unsettled.
Several field-level choices are `basis-schemas` publication decisions, made
because ADR-0004 deliberately deferred them: the global-scope
representation ([Section 14](#14-global-scope-representation)), the
omission of a self-attested `validation_status` field
([Section 20](#20-validation-status-as-derived-state)), and the smallest
useful metadata field set ([Section 19](#19-metadataprovenance)). It
advances to `candidate` once a real consumer (expected: `basis-core`
v0.2.0's policy validator/evaluator and `basis-gateway`'s policy-loading
mechanism) exercises it, and to `stable` only when `basis-architecture`
confirms the shape as a durable commitment. See
[`contract-governance.md`](contract-governance.md).
