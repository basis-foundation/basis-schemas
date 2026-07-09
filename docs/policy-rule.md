# Policy Rule Contract

The **policy rule** contract publishes the deterministic unit-of-evaluation
shape a future `basis-core` v0.2.0 policy validator and evaluator will use
inside a policy bundle. It is the second contract of PR D of
`basis-architecture`'s operation-aware schema readiness plan (ADR-0005,
"PR D — Policy Bundle and Rule Contracts"); see
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md).

- Contract file: [`../schemas/policy-rule/policy-rule.yaml`](../schemas/policy-rule/policy-rule.yaml)
- Governed by: `basis-architecture`
- Published by: `basis-schemas`
- Version: `0.1.0`
- Lifecycle: `experimental`
- Depends on: [`contract-metadata`](contract-metadata.md), [`policy-condition`](policy-condition.md), [`operation-aware-decision-request`](operation-aware-decision-request.md), [`reason-code`](reason-code.md), [`action-string`](action-string.md), [`resource-identifier`](resource-identifier.md)

## 1. Purpose

ADR-0004 (`docs/architecture/operation-aware-policy-rule-model.md`,
Section 4, "Rule Concept") defines a **rule** as "a deterministic unit of
policy evaluation — the thing that a request is matched against, and the
thing whose identifier appears in trace and audit evidence." This contract
publishes that rule's *shape*: a stable identifier, a closed allow/deny
effect, explicit structured match criteria mirroring
`operation-aware-decision-request`'s categories, optional deterministic
conditions (reusing [`policy-condition`](policy-condition.md)), an optional
reason code (reusing [`reason-code`](reason-code.md)), and an optional
static explanation.

## 2. Contract file

[`../schemas/policy-rule/policy-rule.yaml`](../schemas/policy-rule/policy-rule.yaml)

## 3. Governance

Governed by `basis-architecture`. This contract does not decide rule
matching, condition evaluation, or combining semantics; it publishes the
shape ADR-0004 Sections 4 through 7 and 10 already named.

## 4. Version

`0.1.0`

## 5. Lifecycle

`experimental`

## 6. Dependencies

```yaml
depends_on:
  - contract-metadata
  - policy-condition
  - operation-aware-decision-request
  - reason-code
  - action-string
  - resource-identifier
```

`policy-condition`: a rule's optional `conditions` are policy-condition-shaped
values, referenced not redefined. `operation-aware-decision-request`: match
criteria mirror that contract's categories, and several match selectors
(`authority_modes`, `device_classes`, `protocols`, `safety_modes`,
`safety_classifications`, `environment_modes`, `risk_classifications`,
`operation_intents`) validate directly against patterns and the closed
`operation_intent` vocabulary reproduced from that contract. `reason-code`:
the optional `reason_code` field reuses that contract's format unchanged,
introducing no new closed vocabulary. `action-string` /
`resource-identifier`: `match.actions` and `match.resources` validate
directly against those contracts' own canonical patterns (reproduced and
parity-tested against the ultimate source files, not only against
`operation-aware-decision-request`'s copies of them) — direct field
validation justifies a direct dependency declaration, per this repository's
convention.

## 7. Canonical shape

A rule is a single object. `rule_id` and `effect` are always required.
`match`, `conditions`, `reason_code`, and `explanation` are independently
optional, but **at least one of `match` or `conditions` must be present and
non-empty** (see [Section 12](#12-unconditional-rules-not-permitted)).
Unknown fields are rejected (`additional_properties: false`).

| Field | Required | Type | Meaning |
| --- | --- | --- | --- |
| `rule_id` | yes | string (non-empty) | Stable identifier, unique within its containing bundle. |
| `effect` | yes | string (`allow` \| `deny`) | The outcome this rule produces when it matches. |
| `match` | no (see note) | object or null | Structured match criteria — see [Section 10](#10-match-criteria). |
| `conditions` | no (see note) | array or null | Zero or more policy-condition-shaped values. |
| `reason_code` | no | string or null | Reused, unchanged `reason-code`-shaped value. |
| `explanation` | no | string or null (non-empty) | Static, non-executable human-readable text. |

No priority/ordering field, and no provenance/lifecycle metadata field
(source reference, created/updated timestamp, active/deprecated flag), is
published by this contract — see [Section 15](#15-rule-ordering-decision)
and [Section 16](#16-rule-provenancelifecycle-metadata).

## 8. Rule identifiers

`rule_id` must be a non-empty string, stable, and unique within its
containing bundle (ADR-0004 Section 4: "Rule identifiers must be stable
enough for trace, audit, compatibility tests, and operator explanations.").
No UUID requirement: a short, stable, human-readable token (for example
`rule-operator-read-ahu-telemetry`) is preferred. `rule_id` must never be
derived from a rule's position in its bundle's `rules` array — array
position is not rule identity (see [Section 15](#15-rule-ordering-decision)).

**Uniqueness across a bundle is bundle-level validation, not schema-level
validation.** A single rule object has no sibling rules to compare itself
against; [`policy-bundle`](policy-bundle.md) enforces that `rule_id` values
are unique across a bundle's `rules` array.

## 9. ALLOW/DENY effects

`effect` is closed to exactly two lowercase values: `allow` and `deny`. Any
other value — including `not_applicable` — is rejected. This restates
ADR-0004 Section 5 exactly: "Recommended rule effects, conceptually: ALLOW /
DENY ... Future effects such as advisory, warn, or log-only are out of
scope unless separately governed." This contract does not implement deny
precedence, default deny, or any other combining semantics; it only
publishes the effect vocabulary a future `basis-core` evaluator combines
according to ADR-0002's evaluation semantics.

## 10. Why NOT_APPLICABLE is not a rule effect

`NOT_APPLICABLE` is deliberately **excluded** from the effect enum. Per the
operation-aware evaluation semantics document
(`docs/architecture/operation-aware-evaluation-semantics.md`, Section 5),
`NOT_APPLICABLE` means "the policy bundle, rule set, or enforcement scope is
not applicable to this request" — a **bundle-applicability** outcome, never
something an individual rule inside an already-applicable bundle produces.
Conflating the two would blur exactly the distinction ADR-0002 Section 5
exists to preserve: `NOT_APPLICABLE` is about whether a bundle covers a
request's domain, site, or scope at all (see
[`policy-bundle.md`](policy-bundle.md), "Relationship to NOT_APPLICABLE"),
while a rule's `allow`/`deny` effect is about what happens once a bundle
already applies.

## 11. Match criteria

`match` is an optional object of structured selectors, each an array of
alternative values, mirroring ADR-0004 Section 6 exactly: "This list mirrors
the `DecisionRequest` categories ... deliberately: a rule can only match
what a request can carry." The published selectors:

| Selector | Mirrors (operation-aware-decision-request) | Validation |
| --- | --- | --- |
| `subject_ids` | `subject_id` | non-empty strings |
| `subject_roles` | `subject_roles` | non-empty strings |
| `identity_sources` | `identity_source` | non-empty strings |
| `authority_modes` | `authority_mode` | open identifier pattern |
| `actions` | `action` | action-string pattern |
| `resources` | `resource` | resource-identifier pattern |
| `resource_types` | `resource_type` | resource-identifier resource_type pattern |
| `site_ids` / `building_ids` / `zone_ids` / `area_ids` | `location.*` | non-empty strings |
| `device_ids` | `device.device_id` | non-empty strings |
| `device_classes` | `device.device_class` | open identifier pattern |
| `protocols` | `protocol_context.protocol` | open identifier pattern |
| `protocol_operations` | `protocol_context.operation` | free-form non-empty strings |
| `operation_intents` | `operation_intent` | closed vocabulary (read_only / state_changing / control_affecting) |
| `safety_modes` / `safety_classifications` | `safety_context.*` | open identifier pattern |
| `environment_modes` | `environment_context.mode` | open identifier pattern |
| `risk_classifications` | `risk_context.classification` | open identifier pattern |

No `metadata`/`extensions`/`custom`/`extra`/`arbitrary_context` bag is
published: only selectors grounded in an
`operation-aware-decision-request` category are included.

## 12. Unconditional rules not permitted

ADR-0004 does not explicitly permit or forbid a rule with neither `match`
criteria nor `conditions` — an implicit "matches everything" rule. This
contract adopts the stricter reading: **at least one of `match` or
`conditions` must be present and non-empty on every rule**
(`required_at_least_one: [match, conditions]` in the contract body). This is
a `basis-schemas` publication decision, made because permitting a silent
unconditional rule would be a significant, undocumented policy-authoring
risk in an OT authorization context — a single unconditional `allow` or
`deny` rule would apply to every request within its bundle's scope
regardless of subject, action, or resource, with no visual or structural
signal that it does so. Both an entirely absent `match`/`conditions` pair
and a present-but-empty `match: {}` are rejected; a present-but-empty
`conditions: []` is likewise rejected — see
[`../schemas/policy-rule/policy-rule.yaml`](../schemas/policy-rule/policy-rule.yaml)'s
`constraints` section.

## 13. Relationship to PR C request fields

Every match selector corresponds to a specific
`operation-aware-decision-request` field or nested-shape field (see the
table in [Section 11](#11-match-criteria)), and every reused pattern
(`action_pattern`, `resource_pattern`, `resource_type_pattern`,
`open_identifier_pattern`, `operation_intent_values`) is reproduced from,
and parity-tested against, that contract (and, for `action_pattern` /
`resource_pattern` / `resource_type_pattern`, against the ultimate
`action-string` / `resource-identifier` source files directly). This
contract does not invent a second selector vocabulary alongside PR C's
request categories.

## 14. Selector semantics

ADR-0004 Section 6 names match categories but does not itself settle
intra-selector or inter-selector combination semantics beyond restating
deny precedence at the bundle-combining level (Section 9). This contract
therefore documents (in `match_semantics`), rather than invents, the
following minimal combination contract a future `basis-core` evaluator must
honor:

```yaml
match_semantics:
  within_selector: any_of          # actions: [a, b] matches an action of a OR b
  across_selectors: all_of         # every POPULATED selector category must match (AND)
  absent_selector: no_restriction  # an omitted selector imposes no restriction
  empty_selector_list: invalid     # a present-but-empty selector array is a validation error
```

This is a `basis-schemas` publication choice, not an evaluation
implementation: nothing on this contract executes matching. If a future
architecture document settles different selector-combination semantics,
that document governs and this contract's documentation (and its
`match_semantics` block) is updated accordingly — this is the smallest,
most conventional (any-of within, all-of across) representation consistent
with everything ADR-0004 and the evaluation semantics document currently
state.

Every populated selector must contain at least one value (a present-but-empty
selector array is rejected, per `empty_selector_list: invalid`), and each
value must be the selector's published primitive type (a non-empty string,
validated against the selector's pattern where one is published); no selector
accepts a nested object or arbitrary structure, and unknown selector names are
rejected (`additional_properties: false`). Whether **duplicate values within a
single selector list** are permitted, deduplicated, or rejected is
deliberately **unspecified** by this contract — it validates each item
independently and neither requires uniqueness nor assigns any meaning to a
repeated value. A future policy validator or evaluator may settle that
question; this contract does not imply it either way.

## 15. Conditions

`conditions` is an optional, non-empty-when-present array of
policy-condition-shaped values (see [`policy-condition.md`](policy-condition.md))
— referenced, not redefined; this contract reuses
[`policy-condition`](policy-condition.md)'s exact published field policy
rather than declaring a divergent copy. `condition_id` values must be unique
within one rule's `conditions` array (rule-level validation — a
cross-condition concern a single condition object's own schema cannot
express). This contract does not itself define how `conditions` combine
with `match` or with each other; that is future `basis-core` evaluation
semantics.

## 16. Reason codes

`reason_code` is optional and, when present, must match the
[`reason-code`](reason-code.md) contract's published pattern exactly — no
new pattern, no new closed policy vocabulary, and no new official codes are
introduced by this PR. `illustrative_reason_codes` in the contract body
lists synthetic, non-final examples only (`allow_rule_matched`,
`deny_rule_matched`, `no_allow_rule_matched`), echoing (not replacing)
ADR-0004 Section 13's own illustrative examples. `reason_code` is optional,
consistent with `reason-code`'s own open-vocabulary design and the fact
that ADR-0004 does not require every rule to carry one.

## 17. Explanations

`explanation` is an optional, non-empty string. It is descriptive metadata
only — not authoritative (ADR-0004 Section 14: "the machine-readable
decision and trace are authoritative; explanation text is a rendering, not
a second source of truth"). This contract defines no template field, no
variable-interpolation syntax, no expression-evaluation mechanism, and no
HTML/script-execution mechanism: `explanation` is a single opaque string
field with no companion templating machinery, so there is no structural
mechanism by which it could execute anything. `explanation` must not
contain secrets or credential material — this contract does not validate
that programmatically (there is no secret-detection mechanism published
here), but it is a stated constraint every example in this contract's
`examples` block honors.

## 18. Rule ordering decision

**Deferred, not invented.** ADR-0004 Section 10 and the operation-aware
evaluation semantics document (Section 8) both require that evaluation
never depend on incidental file, map, or runtime iteration order, and state
that "if priority is supported later, priority semantics must be explicit"
— a requirement neither document actually satisfies yet (no priority field,
tie-break direction, or interaction with deny precedence is defined
anywhere in the governing architecture). Publishing a priority field on
this contract now would invent ordering semantics ADR-0004 explicitly left
open, and would risk becoming exactly the kind of "incidental parser or
runtime behavior... encode[d] into a surface that other components and
future compatibility tests then depend on" ADR-0004 warns against.

Instead, `rule_id` is published purely as a **stable identifier** for trace,
audit, compatibility, and deterministic reporting. This contract does not
define evaluation priority and does not make declaration/array order in a
containing bundle's `rules` list authoritative — it **never** is. ADR-0004
Section 10 notes that "stable rule identifiers may be used as a deterministic
tie-breaker" *where no other ordering signal resolves a tie*, but that is an
acceptable future fallback the architecture may choose, not a tie-breaking
mechanism this contract defines or depends on: any ordering or tie-breaking
semantics must be defined by future architecture/core work before
implementation. Stable sorting for display, tests, or trace output is not the
same as authorization evaluation precedence. See
[`policy-bundle.md`](policy-bundle.md), "Duplicate rule-ID validation," for
the corresponding bundle-level statement that array position is not rule
identity.

## 19. Rule provenance/lifecycle metadata

Not published in this PR. ADR-0004 Section 4 names "lifecycle metadata"
(active/deprecated/scheduled) and "source/provenance reference" as
conceptual rule categories, but no real future consumer currently justifies
publishing either at the individual-rule level (as opposed to the
bundle level, where `policy-bundle` does publish `deprecated` /
`replaced_by` / `source_ref` / `approval_ref` — see
[`policy-bundle.md`](policy-bundle.md)). Adding speculative fields here
would be exactly the kind of ungoverned extension this contract's
`additional_properties: false` policy exists to prevent. A future PR may
add rule-level lifecycle/provenance fields additively, once a real
consumer justifies them.

## 20. Examples

A role-based allow rule:

```yaml
rule_id: rule-operator-read-ahu-telemetry
effect: allow
match:
  subject_roles:
    - operator
  actions:
    - read:ahu
reason_code: allow_rule_matched
explanation: Operators may read AHU telemetry.
```

A safety-context deny rule:

```yaml
rule_id: rule-deny-control-during-interlock
effect: deny
match:
  safety_modes:
    - interlock-engaged
  operation_intents:
    - control_affecting
reason_code: deny_rule_matched
explanation: >-
  Control-affecting operations are denied while an interlock is engaged.
```

A rule using a policy condition:

```yaml
rule_id: rule-deny-elevated-risk
effect: deny
conditions:
  - condition_id: cond-risk-score-high
    field_path: risk_context.score
    operator: greater_than
    expected_value: 0.8
reason_code: deny_rule_matched
```

The full contract file carries four valid examples and sixteen invalid
examples covering missing/empty `rule_id`, an invalid effect, a rejected
`not_applicable` effect, a malformed selector, an invalid action, an
invalid resource, an unsupported operation intent, a malformed reason code,
a malformed condition, duplicate condition IDs within one rule, an unknown
field, a rejected `script` field, an unconditional rule, an empty `match`
object, and an empty selector array. All examples use clearly synthetic
values.

## 21. Validation

**Schema-level** (this contract, per-object): required fields present;
`effect` one of `allow`/`deny`; `match`/`conditions` type and shape;
selector array item types and patterns; `reason_code` pattern; `explanation`
non-empty; unknown fields rejected.

**Rule-level** (this contract, cross-field within one rule object): at
least one of `match`/`conditions` present and non-empty; every populated
match selector array non-empty; `condition_id` uniqueness within this
rule's `conditions` array.

**Bundle-level** (deferred to [`policy-bundle`](policy-bundle.md)):
`rule_id` uniqueness across a bundle's `rules` array.

**Evaluation semantics** (not implemented here, deferred to future
`basis-core`): match/no-match/error determination, condition evaluation,
deny precedence, default deny, final outcome.

## 22. Compatibility

Purely additive. This contract does not modify any existing published
contract, and no existing contract is made to depend on it. It is not
mandatory anywhere; no implementation repository consumes it yet.

## 23. Security

This contract defines no `access_token`, `id_token`, `refresh_token`, `jwt`,
`bearer_token`, `authorization_header`, `cookie`, `session_secret`,
`client_secret`, `password`, `private_key`, `api_key`, `raw_claims`,
`full_claim_set`, `raw_payload`, `raw_protocol_payload`, `device_secret`,
`credential`, `script`, `code`, `executable`, `command`, `shell`, `python`,
`javascript`, `rego`, `cedar`, `cel`, `wasm`, `sql`, `template`,
`expression`, or `priority` field, anywhere. Any such field is rejected as
unknown — enforced by regression tests, not merely documented.

## 24. Scope boundaries

This contract does not implement rule matching, condition evaluation, deny
precedence, default deny, or any other evaluation semantics. It does not
choose a policy language. It does not publish `PolicyBundle` (see
[`policy-bundle.md`](policy-bundle.md)), and it does not publish an
operation-aware `DecisionResponse`, `EvaluationTrace`, `TraceRuleEvidence`,
`AuditEvidence`, or `GatewayAuditEvent` — each belongs to a later PR (E
through G) per
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md).

## 25. Why `experimental`?

The lifecycle describes this **published contract**, which is new and
unconsumed by any implementation repository — not a claim that the
underlying conceptual category (ADR-0004's rule concept) is unsettled.
Several field-level choices are `basis-schemas` publication decisions, made
because ADR-0004 deliberately deferred them: the no-unconditional-rules
requirement ([Section 12](#12-unconditional-rules-not-permitted)), the
selector-combination semantics ([Section 14](#14-selector-semantics)), and
the rule-ordering deferral ([Section 18](#18-rule-ordering-decision)). It
advances to `candidate` once a real consumer (expected: `basis-core`
v0.2.0's policy validator and evaluator) exercises it, and to `stable` only
when `basis-architecture` confirms the shape as a durable commitment. See
[`contract-governance.md`](contract-governance.md).
