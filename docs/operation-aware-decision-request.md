# Operation-Aware Decision Request Contract

The **operation-aware decision request** contract publishes the richer,
additive vNext request shape from `basis-architecture`'s operation-aware
schema readiness plan (ADR-0005, "PR C — Operation-Aware DecisionRequest").
It is the third PR of the second wave, building on PR A's shared metadata and
PR B's evidence-reference contracts; see
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md).

## 1. Purpose

An operation-aware `DecisionRequest` lets `basis-gateway` assemble a single
structured object carrying the operational context a future, richer
`basis-core` v0.2.0 kernel evaluates: verified subject identity and
attributes, the composite action, the resource and its explicit type,
location and device context, protocol evidence, operation intent, safety /
environment / risk context, and an expected policy version — in addition to
optional references to the trusted identity evidence and normalized adapter
evidence that produced that context. It formalizes the conceptual fields
named in `basis-architecture` ADR-0001
(`docs/architecture/operation-aware-authorization-model.md`, Section 3)
without narrowing, renaming, or reinterpreting them, and without inventing
new authorization semantics of its own.

## 2. Contract file

[`../schemas/operation-aware-decision-request/operation-aware-decision-request.yaml`](../schemas/operation-aware-decision-request/operation-aware-decision-request.yaml)

## 3. Governance

Governed by `basis-architecture`. This contract does not decide
authorization semantics; it publishes the shape ADR-0001 through ADR-0005
already named.

## 4. Version

`0.1.0`

## 5. Lifecycle

`experimental`

## 6. Dependencies

```yaml
depends_on:
  - contract-metadata
  - action-string
  - resource-identifier
  - identity-evidence-reference
  - adapter-evidence-reference
```

`reason-code` and `redaction-classification` are deliberately **not**
declared: this request carries no `reason_code` field (that is a
response/trace concept, deferred to PR E) and no top-level
`redaction_classification` field of its own — the nested evidence references
already carry theirs.

## 7. Relationship to the existing `decision-request`

**`schemas/decision-request/decision-request.yaml` is unchanged by this PR.**
It is not renamed, replaced, widened, reinterpreted, or altered in version,
required fields, optional fields, examples, or validation behavior. It
remains the published v0.1-era request contract — the kernel input `basis-core`
v0.1.0 evaluates today: `request_id`, `subject_id`, `action`, and `timestamp`
required; `subject_roles`, `subject_attrs`, `resource_id`, and `context`
optional.

## 8. Why this is a separate additive contract

The operation-aware request is a **new, vNext contract surface**, not a v2 of
`decision-request`. `basis-core` v0.1.0 continues to evaluate the existing
`decision-request` shape unmodified; `basis-core` v0.2.0 (not yet built) is
expected to add support for this richer shape additively, consistent with
ADR-0005's compatibility rules (`basis-architecture`
`docs/architecture/operation-aware-schema-readiness-plan.md`, Section 7):
"v0.1-era request/response behavior must remain stable." Publishing a second contract,
rather than editing the first, is what makes that compatibility guarantee
possible to keep.

## 9. Canonical shape

The request is a single object. Three fields are required; eighteen are
optional. Unknown fields are rejected
(`additional_properties: false`).

| Field | Required | Type | Meaning |
| --- | --- | --- | --- |
| `request_id` | yes | string (non-empty) | Identifies this specific evaluation request. |
| `correlation_id` | no | string or null | Broader cross-system trace id, passed through verbatim. |
| `subject_id` | yes | string (non-empty) | Verified requesting subject. |
| `subject_roles` | no | array of string | Role names held by the subject. Default `[]`. |
| `subject_attrs` | no | object (string→string) | ABAC attributes. Default `{}`. |
| `identity_source` | no | string or null | Opaque identity source/authority label. |
| `authority_mode` | no | string or null | Opaque identity authority mode label (open, lowercase). |
| `identity_evidence_reference` | no | object or null | [`identity-evidence-reference`](identity-evidence-reference.md)-shaped value. |
| `action` | yes | string (non-empty) | Composite action. See [action-string](action-string.md). |
| `resource` | no | string or null | Canonical resource identifier. See [resource-identifier](resource-identifier.md). |
| `resource_type` | no | string or null | Explicit normalized resource-type classification. |
| `location` | no | object or null | `site_id` / `building_id` / `zone_id` / `area_id`, each optional. |
| `device` | no | object or null | `device_id` / `device_class`, each optional. |
| `protocol_context` | no | object or null | `protocol` / `operation`, each optional. |
| `operation_intent` | no | string or null | `read_only` / `state_changing` / `control_affecting`. |
| `adapter_evidence_reference` | no | object or null | [`adapter-evidence-reference`](adapter-evidence-reference.md)-shaped value. |
| `safety_context` | no | object or null | `mode` / `classification` / `constraint_ids`, each optional. |
| `environment_context` | no | object or null | `mode` / `condition_ids`, each optional. |
| `risk_context` | no | object or null | `classification` / `score`, each optional. |
| `evaluation_time` | no | string (date-time) or null | Timezone-aware ISO 8601 timestamp supplied by the producer. |
| `expected_policy_version` | no | string or null | Non-empty; the policy version the request expects to be evaluated against. |

## 10. Required fields

`request_id`, `subject_id`, and `action` — the smallest usable authorization
identity. See Section 28 for why `evaluation_time`, required as `timestamp`
in `decision-request`, is optional here instead.

## 11. Optional operation-aware fields

Every other field in the table above. Structurally valid requests may omit
all of them; a request need not carry a site, building, zone, device,
protocol, safety context, risk context, identity evidence, or adapter
evidence to be a well-formed operation-aware request. Evaluation
semantics — not this schema — determine how policy treats missing optional
context; this contract does not encode default allow/deny behavior.

## 12. Subject semantics

`subject_id`, `subject_roles`, and `subject_attrs` carry the same meaning as
the identically-named fields in `decision-request`: the subject is
represented as flat fields, not a nested object, matching the existing
contract's convention rather than introducing a new one. Roles remain
authorization input, not proof of authentication; attributes remain
structured ABAC context. No raw token, session secret, cookie, or complete
unredacted claim set is carried anywhere on this contract — see Section 29.

## 13. Identity source and authority semantics

`identity_source` and `authority_mode` are independent, optional, opaque
labels a producer may attach even when no `identity_evidence_reference` is
present. `identity_source` mirrors the field of the same name and meaning
published by [`identity-evidence-reference`](identity-evidence-reference.md)
(an unconstrained non-empty string); `authority_mode` is a new field on this
contract, an open lowercase label (for example `federated`, `synchronized`,
or `standalone-air-gapped`, per `basis-identity`'s identity authority modes)
rather than a closed enum, because `basis-architecture` has not published a
governed authority-mode vocabulary as its own schema contract. Neither field
requires or assumes any OIDC- or JWT-specific shape, and neither makes
`basis-core` identity-provider-aware. When both `identity_source` and an
`identity_evidence_reference` are present, the parent `identity_source`
field is authoritative and the reference's own `identity_source` is
provenance metadata — see the general rule in Section 26.

## 14. Identity evidence reference

`identity_evidence_reference`, when present, must be shaped exactly as
published by [`identity-evidence-reference`](identity-evidence-reference.md)
— this contract does not redefine or duplicate that shape, only references
it. It is optional: identity evidence is commonly produced independently of
any one authorization request (for example at login time). See Section 26
for how its own `request_id` / `correlation_id` relate to this request's.

## 15. Action semantics

`action` reuses the [action-string](action-string.md) contract's
`{verb}:{domain}[:{object}]` format unchanged. This contract does not invent
a second action grammar, and does not carry a protocol-native operation
value in this field — that distinct concept is `protocol_context.operation`
(Section 19).

## 16. Resource and resource-type semantics

`resource` carries the same canonical `{resource_type}:{local_resource_id}`
meaning as `decision-request`'s `resource_id` field, reusing
[resource-identifier](resource-identifier.md) unchanged; it is renamed from
`resource_id` to `resource` on this contract only, to sit naturally beside
the new, explicit `resource_type` field. This does not modify
`decision-request.resource_id` in any way. `resource_type` is an explicit
normalized classification for policy matching, distinct from the type prefix
embedded in `resource` — useful when policy needs to match on type even for
a resource-independent request, or when a producer knows the type ahead of
composing a full canonical identifier. This contract implements **no
runtime cross-field derivation or consistency check** between `resource_type`
and the prefix of `resource`; producers are expected to keep them aligned,
but that alignment is not validated here.

## 17. Location context

`location` is an optional object with four independently optional fields —
`site_id`, `building_id`, `zone_id`, `area_id` — each a non-empty string when
present. No hierarchy level is required, no parent/child relationship is
enforced, and this contract implements no topology lookup, no topology
graph, and no geospatial behavior.

## 18. Device context

`device` is an optional object with two independently optional fields —
`device_id` and `device_class` (an open lowercase label, e.g. `controller`,
`sensor`, `actuator`, `gateway`). `device` is protocol-neutral and carries no
device credentials, no raw device configuration, and no live device lookup.
`device` is distinct from `resource`: `resource` is the authorization
target, `device` is the physical or logical device involved in exposing or
acting on that resource. They are not assumed to always be identical.

## 19. Protocol context

`protocol_context` is an optional object with two independently optional
fields: `protocol` (an open lowercase label, reusing
adapter-evidence-reference's `protocol` pattern) and `operation` (a
free-form, non-empty protocol-native operation name, e.g. a BACnet service
name). Both are evidence/provenance fields. This contract carries no
protocol-specific payload field and no protocol library dependency;
`basis-core` may match policy against this normalized string context, but
does not parse BACnet, Modbus, OPC UA, MQTT, DNP3, IEC 61850, KNX, Niagara,
REST, or any future protocol. When both `protocol_context.protocol` and an
`adapter_evidence_reference` are present, the parent `protocol_context.protocol`
field is authoritative and the reference's own `protocol` is provenance
metadata — see the general rule in Section 26.

## 20. Adapter evidence reference

`adapter_evidence_reference`, when present, must be shaped exactly as
published by [`adapter-evidence-reference`](adapter-evidence-reference.md) —
referenced, not redefined or duplicated. It is optional: adapter evidence is
commonly produced during normalization, ahead of the specific request the
gateway later assembles. See Section 26.

## 21. Operation intent

`operation_intent` is closed to exactly three values —
`read_only`, `state_changing`, `control_affecting` — serialized in this
repository's lowercase snake_case convention. Unlike `reason-code`, which
ADR-0003 explicitly calls "examples only, not a final vocabulary,"
`operation_intent`'s three categories are named consistently and without
qualification across ADR-0001 and the operation-aware authorization and
policy/rule-model architecture documents, which is why this contract closes
the vocabulary rather than leaving it open. `operation_intent` complements,
rather than replaces, `action`: it is not an enforcement command, an
obligation, or executable behavior — purely a descriptive classification
available for policy matching.

## 22. Safety context

`safety_context` is an optional object with three independently optional
fields: `mode` (open lowercase label), `classification` (open lowercase
label), and `constraint_ids` (array of strings, default `[]`; each item's
type is validated, but this contract does not itself enforce item
non-emptiness — no repository convention for item-level validation exists
yet to build on). This contract does not design a safety system, does not
claim safety certification, does not make BASIS a safety controller, and
carries no control commands or executable policy. No closed vocabulary is
defined for `mode` or `classification` because `basis-architecture` has not
published one.

## 23. Environment context

`environment_context` is an optional object with two independently optional
fields: `mode` (open lowercase label; illustrative examples include
`maintenance_mode` and `degraded_connectivity`, not a closed list) and
`condition_ids` (array of strings, default `[]`; same item-validation
posture as `constraint_ids` above — type-checked, not non-emptiness-checked).
Distinct from `safety_context`. This contract implements no runtime
discovery behavior and defines no environment-state ontology.

## 24. Time context

`evaluation_time` is an optional, timezone-aware ISO 8601 timestamp supplied
by the producer for evaluation to reason about (for example, a future
time-window policy condition). It carries supplied time context only: this
contract implements no runtime clock lookup, no time-window evaluation
behavior, and no timezone-database behavior.

## 25. Risk context

`risk_context` is an optional object with two independently optional fields:
`classification` (open lowercase label) and `score` (a number with no
enforced bounds, scale, or calculation method). This contract defines no
final risk taxonomy, no risk engine, and no risk-calculation behavior, and
makes no accuracy claim about any value carried here.

## 26. Request and correlation identifiers

`request_id` identifies this specific evaluation request; `correlation_id`
associates it with a broader end-to-end operation, workflow, or request
chain, passed through verbatim with no format constraint.

### General rule: parent fields vs. nested reference provenance

This request and a nested evidence reference can carry overlapping
information under different field names. The rule is the same in every
such case, and is published machine-readably as
`provenance_association` on the contract body:

- **The parent request's field is authoritative for the evaluation.**
- **A nested evidence reference's same-concept field is provenance
  metadata** — produced earlier and independently by `basis-identity` or
  `basis-adapters` (for example at login time, or during adapter
  normalization, ahead of this specific request existing).
- **Producers should keep overlapping values aligned** when both are
  present.
- **This contract implements no automatic reconciliation or cross-field
  consistency validation** between a parent field and a nested reference's
  same-concept field — that remains a future implementation concern, not
  something the static contract expresses.

This rule applies to every overlapping pair the contract currently defines:

| Parent field | Nested reference field |
| --- | --- |
| `request_id` | `identity_evidence_reference.request_id` |
| `request_id` | `adapter_evidence_reference.request_id` |
| `correlation_id` | `identity_evidence_reference.correlation_id` |
| `correlation_id` | `adapter_evidence_reference.correlation_id` |
| `identity_source` | `identity_evidence_reference.identity_source` (see Section 13) |
| `protocol_context.protocol` | `adapter_evidence_reference.protocol` (see Section 19) |

None of this makes `basis-core` retrieve or interpret raw evidence: the
kernel still only evaluates the structured request it receives (Section 31),
and the reconciliation described above — if a future implementation chooses
to perform it at all — is gateway or producer behavior, never something this
contract or the kernel does at evaluation time.

## 27. Expected policy version

`expected_policy_version` is an optional, non-empty string stating the
policy bundle version the request expects to be evaluated against — an
expectation, distinct from whatever policy version a future
`DecisionResponse` records as actually evaluated. This contract implements
no policy loading, negotiation, selection, or compatibility-resolution
behavior, and enforces no version format (e.g. semver), because the policy
bundle's own versioning scheme is deferred to PR D.

## 28. Missing optional context

A request may be structurally valid while any or all optional context is
absent. This is a deliberate design choice: evaluation semantics — not this
schema — determine how policy treats missing optional context (per
ADR-0002's deferred "missing context behavior" question, `basis-architecture`
`docs/adr/0002-operation-aware-evaluation-semantics.md`). This contract does
not encode default allow/deny behavior.

**Compatibility note on required fields.** `decision-request` requires four
fields: `request_id`, `subject_id`, `action`, `timestamp`. This contract
requires only three — `request_id`, `subject_id`, `action` — and makes the
analogous time field, `evaluation_time`, optional. This is a deliberate
difference for this new vNext surface, not an oversight: not every
operation-aware request needs time-window evaluation, and treating time as
one of several optional evaluation-context categories (alongside safety,
environment, and risk) keeps the required core minimal, consistent with
ADR-0005's instruction (`basis-architecture`
`docs/architecture/operation-aware-schema-readiness-plan.md`) to keep richer
context additive rather than mandatory.

## 29. Secret/raw-evidence prohibitions

This contract never carries — anywhere, top-level or nested — an
`access_token`, `id_token`, `refresh_token`, `jwt`, `bearer_token`,
`authorization_header`, `cookie`, `session_secret`, `client_secret`,
`password`, `private_key`, `api_key`, `raw_claims`, `full_claim_set`,
`raw_payload`, `raw_protocol_payload`, `packet`, `frame`, or `device_secret`
field. Any such field is rejected as unknown, because
`additional_properties: false` closes every object in this contract
(top-level and every nested `*_shape`) to exactly the fields published
above. Evidence references are used instead of embedding raw material. This
is enforced by regression tests, not merely documented.

## 30. Producer ownership

- **`basis-identity`** establishes trusted identity context and mints
  `identity-evidence-reference` values, consumed here as an optional field.
- **`basis-adapters`** normalizes protocol operations and mints
  `adapter-evidence-reference` values, consumed here as an optional field.
- **`basis-gateway`** assembles this request from identity context,
  normalized adapter evidence, and any additional runtime-supplied context;
  validates runtime inputs; invokes `basis-core`; later enforces the
  decision. This contract does not implement assembly.
- **`basis-schemas`** publishes this request shape only.

## 31. Kernel consumer expectations

**`basis-core`** evaluates the structured request deterministically. It does
not authenticate, does not parse protocols, does not retrieve evidence, and
does not enforce. The kernel evaluates only the structured request it
receives — this contract must not, and does not, cause `basis-core` to fetch
context from identity providers, tokens, sessions, protocol networks, device
networks, topology services, risk engines, safety systems, or external
policy services. No implementation repository consumes this contract yet;
this PR does not claim otherwise.

## 32. Examples

A minimal request (only the three required fields):

```yaml
request_id: oadr-0001-0000-0000-000000000001
subject_id: svc-scheduler
action: browse:ahu
```

An OT operation-rich request (resource, resource type, location, device,
protocol context, adapter evidence reference, and operation intent):

```yaml
request_id: oadr-0003-0000-0000-000000000003
subject_id: a7b8c9d0-1234-5678-abcd-ef0123456789
subject_roles:
  - operator
action: write:hvac:setpoint
resource: hvac:zone-a
resource_type: hvac
location:
  site_id: west-campus
  building_id: bldg-3
  zone_id: zone-a
device:
  device_id: ahu-14
  device_class: controller
protocol_context:
  protocol: bacnet
  operation: WriteProperty
adapter_evidence_reference:
  reference_id: adev-0003-0000-0000-000000000003
  evidence_digest:
    algorithm: sha-256
    value: 1f825aa2f0020ef7cf91dfa30da4668d791c5d4824fc8e41354b89ec05795ab
  adapter_source: basis-adapters:bacnet
  protocol: bacnet
  redaction_classification: reference_only
operation_intent: state_changing
```

The full contract file carries two further valid examples (a subject-rich
request with an identity evidence reference, and a full contextual request
with safety/environment/risk/time/policy-version context) and seventeen
invalid examples covering: missing/empty `request_id` and `subject_id`, an
invalid `action`, a malformed `resource`, an unknown top-level field, a
malformed nested structure, an unsupported `operation_intent` value, an
invalid `evaluation_time`, an empty `expected_policy_version`, malformed
identity and adapter evidence references, raw token/claims/protocol-payload
fields, and a malformed `authority_mode`. All examples use clearly synthetic
values.

## 33. Legacy `context` field: not retained

`decision-request` carries an optional, unstructured `context` field
(`object`, string→string) for policy conditions. This contract does **not**
retain it. The explicit structured fields this contract adds —
`subject_attrs` for ABAC attributes, `location`, `device`,
`protocol_context`, `safety_context`, `environment_context`, and
`risk_context` for everything else ADR-0001 names — already cover
substantially more of what a generic `context` map would otherwise carry
informally. Retaining an open string-keyed bag alongside all of these
explicit, governed fields would create a second, ungoverned channel for the
same context, contrary to this contract's `additional_properties: false`
policy and to the instruction that "future additive fields should be
governed and versioned." If a genuinely new context category emerges that
none of the explicit fields above cover, the right response is an additive
field on a future contract revision, decided in `basis-architecture` — not
a free-form escape hatch here.

## 34. Compatibility

Purely additive. This PR does not modify `decision-request`,
`decision-response`, `audit-event`, `action-string`, `resource-identifier`,
`contract-metadata`, `redaction-classification`, `reason-code`,
`identity-evidence-reference`, or `adapter-evidence-reference` — their
shapes, required fields, optional fields, examples, and validation behavior
are all unchanged. No existing contract is made to depend on this one. This
contract is not mandatory anywhere: no implementation repository is required
to adopt it, and none does yet.

## 35. Scope boundaries

This PR publishes `OperationAwareDecisionRequest` only. It does not publish
`PolicyBundle`, `PolicyRule`, `PolicyCondition`, an operation-aware
`DecisionResponse`, `EvaluationTrace`, `TraceRuleEvidence`, `AuditEvidence`,
`GatewayAuditEvent`, a final reason-code vocabulary, or a compatibility
test-vector framework — each belongs to a later PR (D through G) per
[`operation-aware-schema-readiness.md`](operation-aware-schema-readiness.md).
It does not implement policy syntax, condition operators, evaluation
behavior, enforcement behavior, runtime request assembly, evidence
retrieval, identity token schemas, JWT schemas, OIDC schemas, session
schemas, protocol payload schemas, protocol-specific operation objects,
topology discovery, audit storage, or policy loading.

## 36. Why `experimental`?

The lifecycle describes this **published contract**, which is new and
unconsumed by any implementation repository — not a claim that the
underlying conceptual categories (named in ADR-0001) are unsettled. Several
field-level choices are new design decisions made in `basis-schemas` itself,
not open architecture questions: the closed `operation_intent` vocabulary
(Section 21), the optional `evaluation_time` (Section 28), the `resource`
rename from `decision-request`'s `resource_id` (Section 16), and the
decision not to carry a `decision-request`-style catch-all `context` field
(Section 33) are all `experimental` in the sense that early feedback may
still refine them, even though the categories they formalize are stable
architecture. It advances to `candidate` once a real consumer (expected:
`basis-gateway` assembling requests, `basis-core` v0.2.0 evaluating them)
exercises it, and to `stable` only when `basis-architecture` confirms the
shape as a durable commitment. See
[`contract-governance.md`](contract-governance.md).
