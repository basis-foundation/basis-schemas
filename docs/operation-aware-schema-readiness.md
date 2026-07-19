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
PR C — Operation-Aware DecisionRequest                   [published]
PR D — Policy Bundle and Rule Contracts                  [published]
PR E — DecisionResponse and EvaluationTrace               [published]
PR F — Audit Evidence and GatewayAuditEvent               [published]
PR G — Compatibility Examples and Test Vectors            [published]
```

With PR G published, every PR in this order is published. This completes
the operation-aware `basis-schemas` second wave (see
[Section "PR G — Compatibility Examples and Test Vectors — published"](#pr-g--compatibility-examples-and-test-vectors--published)
below).

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

### How PR C consumes these references

PR C (the operation-aware `DecisionRequest`, published — see below) adds two
optional fields, `identity_evidence_reference` and
`adapter_evidence_reference`, shaped exactly as published by these two PR B
contracts, so a request can cite the identity and adapter evidence that
produced its context without embedding that evidence directly. PR C
references these shapes rather than redefining or duplicating them. No
implementation repository consumes `identity-evidence-reference`,
`adapter-evidence-reference`, or `operation-aware-decision-request` yet; PR B
and PR C publish shapes only, ahead of any implementation adoption.

## PR C — Operation-Aware DecisionRequest — published

PR C publishes the richer, additive vNext request contract that a future
`basis-core` v0.2.0 evaluates:

- **[Operation-aware decision request](operation-aware-decision-request.md)**
  — `schemas/operation-aware-decision-request/operation-aware-decision-request.yaml`.
  Required: `request_id`, `subject_id`, `action`. Optional: `correlation_id`,
  `subject_roles`, `subject_attrs`, `identity_source`, `authority_mode`,
  `identity_evidence_reference`, `resource`, `resource_type`, `location`,
  `device`, `protocol_context`, `operation_intent`,
  `adapter_evidence_reference`, `safety_context`, `environment_context`,
  `risk_context`, `evaluation_time`, `expected_policy_version`.

Published at contract version `0.1.0`, lifecycle `experimental`. Declares
`depends_on: [contract-metadata, action-string, resource-identifier,
identity-evidence-reference, adapter-evidence-reference]`. Does not declare
`reason-code` or `redaction-classification`: the request carries no
`reason_code` field and no top-level `redaction_classification` field of its
own (the nested evidence references already carry theirs).

### Relationship to the first-wave `decision-request`

`schemas/decision-request/decision-request.yaml` is **unchanged**: not
renamed, replaced, widened, or reinterpreted, and its version, required
fields, optional fields, examples, and validation behavior are all
identical to before this PR. It remains the published v0.1-era request
contract. `operation-aware-decision-request` is a separate, additive vNext
contract surface, published alongside it, not superseding it.

### Categories represented

Every ADR-0001 Section 3 request-side category is represented: subject
identity and attributes; identity source / authority mode; the identity
evidence reference; action; resource and resource type; site/building/zone/
area location; device identity and class; protocol and protocol operation;
the adapter evidence reference; operation intent; safety, environment, and
risk context; correlation ID; request ID; and expected policy version.

### Evidence-reference usage

`identity_evidence_reference` and `adapter_evidence_reference` are optional
fields shaped exactly as published by PR B's two contracts — referenced, not
duplicated or redefined. Their own `request_id` / `correlation_id`, when
present, are provenance metadata; the parent request's own identifiers
remain authoritative for the evaluation, with no automatic reconciliation
between the two implemented by this static contract.

### Compatibility posture

Purely additive. No existing contract (`decision-request`,
`decision-response`, `audit-event`, `action-string`, `resource-identifier`,
`contract-metadata`, `redaction-classification`, `reason-code`,
`identity-evidence-reference`, `adapter-evidence-reference`) changed shape,
required fields, optional fields, examples, or validation behavior, and none
was made to depend on this new contract. This contract is not mandatory
anywhere; no implementation repository consumes it yet.

### What PR C intentionally excludes

Consistent with ADR-0005's scope for PR C, this PR does not introduce:

- `PolicyBundle`, `PolicyRule`, or `PolicyCondition`
- An operation-aware `DecisionResponse` or `EvaluationTrace` /
  `TraceRuleEvidence`
- `AuditEvidence` or `GatewayAuditEvent`
- A final, closed reason-code vocabulary
- Compatibility/test-vector fixtures (deferred to PR G)
- Policy syntax, condition operators, evaluation behavior, or enforcement
  behavior
- Runtime request assembly or evidence retrieval (owned by `basis-gateway`,
  `basis-identity`, `basis-adapters`)
- Identity token, JWT, OIDC, or session schemas
- Protocol payload schemas or protocol-specific operation objects
- Topology discovery, audit storage, or policy loading

### How PR D and PR E build on this

PR D (policy bundle and rule contracts, now published — see below) defines
match criteria that reference this request's categories — resource type,
location, device class, protocol/operation evidence, operation intent,
safety/environment/risk context — without choosing a policy language or a
final condition operator set. PR E (the operation-aware `DecisionResponse`
and `EvaluationTrace`) is expected to echo this request's `request_id` the
same way the first-wave `decision-response` echoes `decision-request`'s, and
to reference the identity/adapter evidence this request optionally carries,
and PR D's bundle/rule identifiers, when explaining a trace. PR E does not
exist yet; this section records expected dependency direction only, per
ADR-0005 Section 6.

## PR D — Policy Bundle and Rule Contracts — published

PR D publishes the machine-readable policy model a future `basis-core`
v0.2.0 will validate and evaluate against the operation-aware request
published by PR C:

- **[Policy condition](policy-condition.md)** —
  `schemas/policy-condition/policy-condition.yaml`. A deterministic,
  data-only predicate: `condition_id`, a validated dotted `field_path`
  referencing an `operation-aware-decision-request` category, an open
  (not closed-enum) lowercase snake_case `operator`, and a
  smallest-safe-representation `expected_value` (string, number, boolean,
  null, or a homogeneous array of those scalars). Declares
  `depends_on: [contract-metadata]`.
- **[Policy rule](policy-rule.md)** —
  `schemas/policy-rule/policy-rule.yaml`. A deterministic unit of
  evaluation: a stable `rule_id`, a closed `effect` (`allow` / `deny`
  only — `not_applicable` is excluded, as it is a bundle-applicability
  outcome, not a rule effect), explicit structured `match` criteria
  mirroring PR C's request categories, an optional `conditions` array of
  policy-condition-shaped values, an optional `reason_code` (reusing
  `reason-code` unchanged), and an optional static `explanation`. At least
  one of `match` or `conditions` is required — this contract does not
  permit an unconditional rule. Declares
  `depends_on: [contract-metadata, policy-condition,
  operation-aware-decision-request, reason-code, action-string,
  resource-identifier]`.
- **[Policy bundle](policy-bundle.md)** —
  `schemas/policy-bundle/policy-bundle.yaml`. The unit of policy identity,
  versioning, scope, ownership, and rule grouping: `bundle_id`,
  `bundle_version` (this bundle's content version) and `schema_version`
  (the contract-shape version an instance targets, kept distinct from
  both `bundle_version` and the `basis-schemas` package version),
  `policy_owner` (provenance only, never an authorization subject), an
  optional `scope` (absent means globally applicable), and a non-empty
  `rules` array of policy-rule-shaped values, plus optional
  descriptive/provenance/deprecation metadata. No self-attested
  `validation_status` field is published — validity is derived by a
  future validator, never self-declared. Declares
  `depends_on: [contract-metadata, policy-rule]`.

All three are published at contract version `0.1.0`, lifecycle
`experimental`, in dependency order (`policy-condition` before
`policy-rule` before `policy-bundle`), tracked in
`basis_schemas.OPERATION_AWARE_POLICY_CONTRACTS`.

### Policy scope

`policy-bundle`'s `scope` determines whether a bundle applies to a request
at all — distinct from `policy-rule`'s `match`, which determines which
`allow`/`deny` rules inside an already-applicable bundle are candidates.
Scope covers the categories ADR-0004 Section 3 names as justified: action
vocabulary, resource type, site/building/zone/area, device class,
environment/deployment, identity authority mode, and protocol. Absent scope
means globally applicable; a present scope restricts applicability to
requests matching every populated selector; an entirely empty scope object
is invalid (use omission instead). Whether a present-but-non-matching scope
resolves to `NOT_APPLICABLE` is evaluation semantics (ADR-0002 Section 5),
documented but not implemented by these contracts.

### Rule effects

Closed to exactly `allow` and `deny` (ADR-0004 Section 5). `NOT_APPLICABLE`
is deliberately excluded as a rule effect — it is a bundle-applicability
outcome (ADR-0002 Section 5), never something an individual rule produces.
No `warn`, `advisory`, `audit_only`, `log_only`, or `permit_with_override`
effect is introduced.

### Request match criteria

`policy-rule`'s `match` selectors mirror every category ADR-0004 Section 6
names as drawn from the `DecisionRequest`: subject identity/roles, identity
source/authority mode, action, resource/resource type, site/building/zone/
area, device identity/class, protocol/protocol operation, operation intent,
and safety/environment/risk classification. Within one populated selector,
values are alternatives (any-of); across populated selector categories, all
must match (AND); an absent selector imposes no restriction; an empty
selector list is invalid. This selector-combination contract is a
`basis-schemas` publication choice (documented, not implemented), made
because ADR-0004 names the categories without settling their combination
semantics beyond bundle-level deny precedence.

### Condition extensibility

`policy-condition`'s `operator` vocabulary is deliberately open, per
ADR-0004 Section 7's explicit deferral of the operator/condition language.
The schema validates structural well-formedness only (lowercase snake_case);
future basis-core policy validation determines which operators, and which
`field_path` values, are actually supported. A structurally valid value is
never a claim of runtime support.

### Reason-code reuse

`policy-rule`'s optional `reason_code` reuses the `reason-code` contract's
published pattern exactly. No new closed policy reason-code vocabulary is
introduced by PR D; `illustrative_reason_codes` in `policy-rule.yaml` lists
synthetic, non-final examples only, echoing (not replacing) ADR-0004
Section 13's own illustrative codes.

### Validation boundaries

PR D's contracts and companion tests distinguish, per ADR-0004 Section 11:
**schema-level validation** (required fields, types, enums, patterns,
unknown fields, nested shapes — enforced by each contract's own published
field policy); **bundle validation** (duplicate `rule_id` values across a
bundle, duplicate `condition_id` values within one rule, unsupported field
paths/operators, incompatible schema versions — enforced by this
repository's test suite, not by static YAML/JSON-Schema notation alone);
and **evaluation semantics** (condition matching, deny precedence, default
deny, final outcome — explicitly **not** implemented by any PR D contract).
Invalid policy bundles must never produce `ALLOW` — a requirement PR D
documents for a future `basis-core` validator/evaluator to satisfy, not
something these static contracts implement themselves.

### Compatibility posture

Purely additive. PR D does not modify `decision-request`, `decision-
response`, `audit-event`, `action-string`, `resource-identifier`,
`contract-metadata`, `redaction-classification`, `reason-code`,
`identity-evidence-reference`, `adapter-evidence-reference`, or
`operation-aware-decision-request` — their shapes, required fields,
optional fields, examples, and validation behavior are all unchanged, and
none is made to depend on PR D's new contracts. None of PR D's three
contracts is mandatory anywhere; no implementation repository consumes
them yet.

### Security boundaries

None of PR D's contracts define an `access_token`, `id_token`,
`refresh_token`, `jwt`, `bearer_token`, `authorization_header`, `cookie`,
`session_secret`, `client_secret`, `password`, `private_key`, `api_key`,
`raw_claims`, `raw_payload`, `raw_protocol_payload`, or `device_secret`
field, and none defines a `script`, `code`, `executable`, `command`,
`shell`, `python`, `javascript`, `rego`, `cedar`, `cel`, `wasm`, `sql`,
`template`, or `expression` field — enforced by regression tests, not
merely documented.

### What PR D deliberately excludes

Consistent with ADR-0005's own scope for PR D and ADR-0004 Section 18, this
PR does not introduce or implement: a policy language (Rego, Cedar, CEL,
Python, JavaScript, SQL, WASM, or a custom DSL); executable policy
expressions or embedded code; a final, closed condition-operator registry;
a final, closed reason-code vocabulary; rule ordering/priority semantics
(deferred — see [`policy-rule.md`](policy-rule.md), "Rule ordering
decision"); policy loading, storage, distribution, or synchronization;
policy signing or signature verification; tamper-evident packaging; a
policy approval workflow; a policy authoring or simulation UI; policy
deployment behavior; multi-bundle hierarchy or policy federation;
tenant/site policy delegation; runtime policy evaluation; condition
execution; gateway enforcement; or audit persistence. An operation-aware
`DecisionResponse`, `EvaluationTrace`, `TraceRuleEvidence`, `AuditEvidence`,
`GatewayAuditEvent`, and a compatibility-test-vector framework remain
deferred to PR E through PR G below.

### How PR E will reference bundle/rule identifiers

PR E (the operation-aware `DecisionResponse` and `EvaluationTrace`) is
expected to reference PR D's `bundle_id`, `bundle_version`, and `rule_id`
values in a future response's policy-identification fields and in
evaluation trace rule evidence, the same way PR C's `request_id` is
expected to be echoed by PR E's response. Neither PR E, PR F, nor PR G
exists yet; this section records expected dependency direction only, per
ADR-0005 Section 6. PR D does not imply that basis-core consumes these
policy contracts yet — no implementation repository does.

## PR E — DecisionResponse and EvaluationTrace — published

PR E publishes the machine-readable response and trace contracts a future
`basis-core` v0.2.0 will produce after deterministic operation-aware policy
evaluation, against the request and policy contracts published by PR C and
PR D:

- **[Trace rule evidence](trace-rule-evidence.md)** —
  `schemas/trace-rule-evidence/trace-rule-evidence.yaml`. The bounded,
  deterministic explanation record for one policy rule considered during
  evaluation: `rule_id` and `effect` reused unchanged from `policy-rule`, a
  closed `rule_result` (`matched` / `not_matched` / `skipped` / `error`,
  reproducing ADR-0003 Section 5 and Section 4's rule-evidence categories),
  optional bounded `condition_results` (each a `condition_id` reused from
  `policy-condition` plus a closed three-value `result`), and an optional
  `reason_code` / `explanation`. Never copies a rule's match criteria or
  conditions, and never carries a condition's `field_path` / `operator` /
  `expected_value` or the raw value compared. Declares
  `depends_on: [contract-metadata, policy-rule, policy-condition,
  reason-code]`.
- **[Evaluation trace](evaluation-trace.md)** —
  `schemas/evaluation-trace/evaluation-trace.yaml`. The deterministic,
  bounded explanation of one kernel evaluation: `trace_id` and `request_id`
  identity, optional `correlation_id` passthrough, an applicable policy
  bundle's `bundle_id` / `bundle_version` when one applied, a closed,
  nullable `bundle_applicability` (`applicable` / `not_applicable` / `null`,
  distinct from the final outcome per ADR-0002 Section 5), a closed,
  nullable `outcome` kept structurally independent of a closed
  `evaluation_status` (`completed` / `failed`) and a closed, six-value
  `failure_reason`, a (possibly empty) `rule_evidence` array of
  `trace-rule-evidence`-shaped values, and an optional `reason_code` /
  `explanation`. **Required invariant: `outcome` is null if and only if
  `evaluation_status` is `failed`.** Declares
  `depends_on: [contract-metadata, operation-aware-decision-request,
  policy-bundle, trace-rule-evidence, reason-code]`.
- **[Operation-aware decision response](operation-aware-decision-response.md)**
  — `schemas/operation-aware-decision-response/operation-aware-decision-response.yaml`.
  The additive vNext response contract: `request_id` echoed from PR C's
  request, the same `outcome` / `evaluation_status` / `failure_reason`
  model as `evaluation-trace` (kept in parity), optional `bundle_id` /
  `bundle_version` from PR D, an optional `trace_id` reference and/or
  embedded `evaluation_trace`, and an optional `reason_code` /
  `explanation`. **The existing first-wave `schemas/decision-response/
  decision-response.yaml` is unchanged** — not renamed, replaced, widened,
  or reinterpreted; this is a separate, additive vNext contract surface.
  Declares `depends_on: [contract-metadata,
  operation-aware-decision-request, policy-bundle, evaluation-trace,
  reason-code]`.

All three are published at contract version `0.1.0`, lifecycle
`experimental`, in dependency order (`trace-rule-evidence` before
`evaluation-trace` before `operation-aware-decision-response`), tracked in
`basis_schemas.OPERATION_AWARE_RESPONSE_TRACE_CONTRACTS`.

### Authorization outcomes

`outcome` is closed to exactly `allow` / `deny` / `not_applicable` — the
same vocabulary as the existing `decision-response` and `policy-rule`
`effect` values — kept in parity across `evaluation-trace` and
`operation-aware-decision-response` by this repository's test suite. No
`error`, `failure`, or `invalid` value was added to this enum.

### Evaluation failure separation

Per ADR-0002 Section 14, a policy decision and an evaluation failure are
never collapsed into one ambiguous field. `evaluation_status`
(`completed` / `failed`) and `failure_reason` (a closed, six-value
evaluator-failure vocabulary: `invalid_request`,
`unsupported_schema_version`, `invalid_policy_bundle`,
`policy_validation_failure`, `condition_evaluation_error`,
`internal_evaluation_error`) are independent fields on both
`evaluation-trace` and `operation-aware-decision-response`, with a required
invariant enforced by both contracts' constraints and tested directly: a
failed evaluation can never serialize a non-null `outcome`. This
`failure_reason` vocabulary is new and distinct from the existing
first-wave `decision-response`'s own four-value `failure_reason`
(`malformed_request` / `policy_error` / `audit_error` / `internal_error`),
which PR E does not modify, reinterpret, or extend.

### Policy bundle/rule identity reuse

`evaluation-trace` and `operation-aware-decision-response` both echo PR D's
`policy-bundle.bundle_id` / `bundle_version` unchanged, and
`trace-rule-evidence` echoes PR D's `policy-rule.rule_id` / `effect` and
PR D's `policy-condition.condition_id` unchanged. No identifier or
vocabulary is redefined; every reuse is parity-tested against the
canonical PR D files.

### Reason-code reuse

`reason_code` (on all three PR E contracts, at both rule and condition
level on `trace-rule-evidence`) reuses the `reason-code` contract's
published pattern exactly. No new closed reason-code vocabulary is
introduced by PR E.

### Trace boundedness

None of PR E's three contracts carry a full request snapshot, a full
policy bundle, raw identity evidence, raw adapter evidence, raw protocol
payloads, a condition's `field_path` / `operator` / `expected_value`, or
the raw value a condition compared against. `trace-rule-evidence`'s
`rule_result` and `condition_results.result` are the only mechanism for
representing missing/unknown context; no separate top-level
missing-context field was introduced, since ADR-0003 Section 4 names that
category without settling a field-level vocabulary for it.

### Redaction/security boundary

None of PR E's three contracts define an `access_token`, `id_token`,
`refresh_token`, `jwt`, `bearer_token`, `authorization_header`, `cookie`,
`session_secret`, `client_secret`, `password`, `private_key`, `api_key`,
`credential`, `raw_claims`, `raw_payload`, `raw_protocol_payload`,
`full_request`, `request_snapshot`, `full_policy`, `policy_document`,
`debug`, `exception`, `stack_trace`, `traceback`, `gateway_enforcement`,
`enforcement_result`, `http_status`, or `response_status` field — enforced
by regression tests. No `redaction_classification` field is published on
any of the three: every value each contract carries is already a safe
identifier, a closed vocabulary member, or a reason code.

### Trace vs. audit distinction

Per ADR-0003 Section 2, `evaluation-trace` is the kernel-produced
explanation of one evaluation — it is not an immutable audit record, a
gateway enforcement record, a policy-loading record, a session record, an
identity-verification record, a protocol transaction log, a persistence
format, or a compliance attestation. `AuditEvidence` and
`GatewayAuditEvent` remain deferred to PR F, which will reference
`evaluation-trace`'s `trace_id` and
`operation-aware-decision-response`'s `request_id` rather than redefining
either.

### Compatibility posture

Purely additive. PR E does not modify `decision-request`,
`decision-response`, `audit-event`, `action-string`, `resource-identifier`,
`contract-metadata`, `redaction-classification`, `reason-code`,
`identity-evidence-reference`, `adapter-evidence-reference`,
`operation-aware-decision-request`, `policy-condition`, `policy-rule`, or
`policy-bundle` — their shapes, required fields, optional fields, examples,
and validation behavior are all unchanged, and none is made to depend on
PR E's new contracts. None of PR E's three contracts is mandatory
anywhere; no implementation repository consumes them yet.

### What PR E deliberately excludes

Consistent with ADR-0005's own scope for PR E, this PR does not introduce
or implement: `AuditEvidence` or `GatewayAuditEvent` (deferred to PR F); a
compatibility-test-vector framework (deferred to PR G); a final, closed
reason-code vocabulary; gateway fail-open/fail-closed runtime behavior; a
final trace-ordering/priority model beyond "deterministic for identical
input, not authorization precedence"; policy loading, evaluation, or
enforcement behavior; identity token, JWT, OIDC, or session schemas; or
protocol payload schemas.

### How PR F consumes response/trace identifiers without redefining them

PR F (audit evidence and `GatewayAuditEvent`, now published — see below)
references `evaluation-trace.trace_id`,
`operation-aware-decision-response.request_id`, and PR D's `bundle_id` /
`bundle_version`, the same way PR E's contracts already reference PR C's
`request_id` and PR D's `bundle_id` / `bundle_version` / `rule_id`. PR E
does not imply that `basis-core` consumes these response/trace contracts
yet — no implementation repository does.

## PR F — Audit Evidence and GatewayAuditEvent — published

PR F publishes the bounded, durable audit-evidence shape and the
gateway-emitted enforcement-boundary event shape named by ADR-0003
(`docs/architecture/operation-aware-trace-audit-evidence.md`), against the
response and trace contracts published by PR E:

- **[Audit evidence](audit-evidence.md)** —
  `schemas/audit-evidence/audit-evidence.yaml`. The bounded, durable,
  audit-oriented evidence representation of one evaluation: `evidence_id`
  and `request_id` identity, optional `correlation_id` / `trace_id`
  association, the same `evaluation_status` / `outcome` / `failure_reason`
  model as PR E (kept in parity), optional `bundle_id` / `bundle_version`
  from PR D, a bounded `matched_rule_ids` array (stable rule identifiers,
  never a full per-rule trace), optional `identity_evidence_reference` /
  `adapter_evidence_reference` reused unchanged from PR B, an optional
  `reason_code` / `explanation`, and a required `recorded_at` timestamp
  distinct from any request-supplied `evaluation_time`. This is the
  kernel-side audit evidence ADR-0003 Section 14 names `basis-core` as
  producing (as part of its response, not persisted durably by
  `basis-core`) — not something `basis-gateway` assembles. Declares
  `depends_on: [contract-metadata, operation-aware-decision-response,
  evaluation-trace, policy-bundle, identity-evidence-reference,
  adapter-evidence-reference, reason-code]`.
- **[Gateway audit event](gateway-audit-event.md)** —
  `schemas/gateway-audit-event/gateway-audit-event.yaml`. The bounded,
  gateway-emitted record of what happened at the enforcement boundary:
  `event_id` and a closed `event_type` (`gateway_authorization`, the
  smallest safe representation for this PR), a required emission
  `timestamp`, `request_id` / optional `correlation_id`, the same kernel
  `evaluation_status` / `outcome` / `failure_reason` model reused
  unchanged, a required `audit_evidence_id` reference to the associated
  `audit-evidence` record (referenced, never embedded), an optional
  `gateway_id`, a closed `enforcement_action` (`allow` / `deny`) kept
  structurally independent of the kernel `outcome`, and an optional,
  small, closed `gateway_failure_reason` distinct from the kernel
  `failure_reason`. This is the record ADR-0003 Section 14 names
  `basis-gateway` as assembling by "combining kernel evidence with
  enforcement facts." Declares `depends_on: [contract-metadata,
  operation-aware-decision-response, evaluation-trace, policy-bundle,
  audit-evidence, reason-code]`.

Both are published at contract version `0.1.0`, lifecycle `experimental`,
in dependency order (`audit-evidence` before `gateway-audit-event`),
tracked in `basis_schemas.OPERATION_AWARE_AUDIT_CONTRACTS`.

### Trace vs. audit vs. gateway event

Per ADR-0003 Section 2, the three artifacts are distinct and never
collapsed: `evaluation-trace` (PR E) is the kernel-produced *explanation*
of one evaluation; `audit-evidence` (PR F) is the durable, bounded
*evidence* representation derived from the response, the trace, and PR B's
evidence references — broader than trace, but not a second copy of it;
`gateway-audit-event` (PR F) is the *enforcement-boundary* record
`basis-gateway` emits after combining `audit-evidence` with its own
enforcement facts. `audit-evidence` references `evaluation-trace.trace_id`
rather than embedding rule-level or condition-level evidence;
`gateway-audit-event` references `audit-evidence.evidence_id` rather than
embedding the evidence record.

### Kernel result vs. gateway enforcement

`gateway-audit-event.enforcement_action` is structurally independent of the
kernel `outcome` it echoes: this PR does not require `enforcement_action`
to mechanically equal `outcome`. In particular, `enforcement_action: deny`
is valid and expected alongside kernel `outcome: not_applicable` and
alongside kernel `evaluation_status: failed` (fail-closed gateway behavior
on a kernel result that was not itself a policy deny) — neither
combination rewrites the kernel value: `not_applicable` is never
serialized as `deny`, and a failed evaluation never carries a non-null
outcome. `basis-core` decides; `basis-gateway` enforces and records
enforcement facts (ADR-0003 Section 9).

### Decision/evaluation-state reuse

`evaluation_status`, `outcome`, and `failure_reason` are reused unchanged
on both PR F contracts from PR E's `operation-aware-decision-response` and
`evaluation-trace`, kept in parity by this repository's test suite, with
the identical required invariant already established by PR E: a failed
evaluation never carries a non-null outcome, and `failure_reason` is
non-null if and only if `evaluation_status` is `failed`.

### Fail-closed representation

Per ADR-0003 Section 15 and Section 17, this repository does not model a
deployment-wide fail-open/fail-closed *policy* — that remains explicitly
deferred to later work. `gateway-audit-event.enforcement_action` and the
optional `gateway_failure_reason` (a small, closed, gateway-LOCAL failure
category — `gateway_timeout`, `upstream_unavailable`,
`audit_assembly_failure`, `internal_gateway_error` — distinct in both name
and meaning from the reused kernel `failure_reason`) represent only the
bounded fact of what happened for one event, never a standing deployment
policy. When `gateway_failure_reason` is non-null, `enforcement_action` is
required to be `deny`.

### Policy provenance

Both PR F contracts optionally echo PR D's `policy-bundle.bundle_id` /
`bundle_version` unchanged, the same reuse pattern PR E already
established, kept in parity by this repository's test suite. Neither
contract embeds a full policy bundle, rule set, or scope.

### Evidence references

`audit-evidence` reuses PR B's `identity-evidence-reference` and
`adapter-evidence-reference` unchanged for its own optional evidence
fields. `gateway-audit-event` carries neither field directly — those
remain exclusively on the `audit-evidence` record it references by
`audit_evidence_id`.

### Redaction handling

Neither PR F contract publishes a top-level `redaction_classification`
field: every value each carries directly is already a safe identifier, a
closed vocabulary member, a reason code, or a reference to a record that
already carries its own redaction handling (PR B's evidence-reference
contracts). Per ADR-0003 Section 10's unconditional rule, no audit or
gateway-event artifact may contain a secret — enforced by regression
tests in both new contract's test suites.

### Boundedness

Neither PR F contract carries a full request snapshot, a full policy
bundle, raw identity evidence, raw adapter evidence, raw protocol
payloads, a per-rule trace object, condition-level evidence, or any
subject/action/resource field of its own — both reference the evaluated
request only by `request_id` (and, on `audit-evidence`, `trace_id`), per
ADR-0003 Section 6's "avoid duplicating the full raw request when a stable
reference is sufficient." `gateway-audit-event` additionally carries no
route, endpoint, HTTP status, or response-status field.

### Security

Neither PR F contract defines an `access_token`, `id_token`,
`refresh_token`, `jwt`, `bearer_token`, `authorization_header`, `cookie`,
`session_secret`, `client_secret`, `password`, `private_key`, `api_key`,
`credential`, `raw_claims`, `raw_payload`, `raw_protocol_payload`,
`full_request`, `request_snapshot`, `full_policy`, `policy_document`,
`debug`, `exception`, `stack_trace`, `traceback`, `signature`,
`signature_algorithm`, `hash_chain`, `previous_hash`, or `merkle_root`
field — enforced by regression tests. Neither contract claims YAML shape
alone provides immutability, tamper resistance, non-repudiation,
cryptographic authenticity, or chain of custody; durability is documented
as a producer/storage responsibility ADR-0003 Section 17 leaves open.

### Compatibility posture

Purely additive. PR F does not modify `decision-request`,
`decision-response`, `audit-event`, `action-string`, `resource-identifier`,
`contract-metadata`, `redaction-classification`, `reason-code`,
`identity-evidence-reference`, `adapter-evidence-reference`,
`operation-aware-decision-request`, `policy-condition`, `policy-rule`,
`policy-bundle`, `trace-rule-evidence`, `evaluation-trace`, or
`operation-aware-decision-response` — their shapes, required fields,
optional fields, examples, and validation behavior are all unchanged, and
none is made to depend on PR F's new contracts. Neither of PR F's two
contracts is mandatory anywhere; no implementation repository consumes
them yet.

### First-wave `audit-event` unchanged

`schemas/audit-event/audit-event.yaml` — the first-wave, sixth contract —
is completely unchanged by PR F: no rename, no widening, no version,
field, example, or validation change. `audit-evidence` and
`gateway-audit-event` are separate, additive operation-aware contracts,
published alongside it, using their own outcome/event-type vocabularies
that are never compared or unified with the first-wave contract's own
`allowed`/`denied`/`error` outcome or `authorization_decision` event type.

### What PR F deliberately excludes

Consistent with ADR-0005's own scope for PR F and ADR-0003 Section 17's
"Open Questions Deferred," this PR does not introduce or implement: audit
storage APIs, database schemas, retention engines, log shipping,
SIEM/S3/Kafka/syslog/CloudWatch/OpenTelemetry integrations, cryptographic
signing, signature verification, hash chains, Merkle trees, tamper-proof
or non-repudiation claims, audit approval/review/export workflows, audit
search APIs, audit UI, gateway runtime code, gateway middleware, HTTP
response behavior, policy evaluation, identity verification, protocol
parsing, a final reason-code vocabulary, a deployment-wide fail-open/
fail-closed policy, or a compatibility-test-vector framework (deferred to
PR G). A final trace schema, a final audit event schema, an audit
storage/retention model, a tamper-evident audit design, compliance
mapping, privacy/data-minimization policy, safety-system audit
requirements, adapter evidence schema changes, and identity evidence
schema changes all remain explicitly deferred, per ADR-0003 Section 17.

### How PR G will use canonical examples

PR G (compatibility examples and test vectors) is expected to build
canonical cross-repository fixtures from the examples PR A through PR F
already publish — including `audit-evidence` and `gateway-audit-event`'s
own `examples: {valid, invalid}` blocks — rather than PR F introducing a
compatibility-vector primitive itself. Neither PR G nor any implementation
repository consumes PR F yet; this section records expected direction
only, per ADR-0005 Section 6.

## PR G — Compatibility Examples and Test Vectors — published

PR G publishes canonical, cross-contract compatibility examples and test
vectors that connect PR A through PR F's individually-published contracts
into complete operation-aware authorization scenarios — the final planned
PR in this second wave:

- **[Compatibility vectors overview](operation-aware-compatibility-vectors.md)**
  — the conceptual overview: purpose, authority hierarchy, relationship to
  ADR-0005 and PR A through PR F, and what is and is not claimed.
- **[`examples/operation-aware/compatibility/README.md`](../examples/operation-aware/compatibility/README.md)**
  — the practical directory guide: layout, artifact naming, the scenario
  matrix, and the full per-scenario semantic write-up.

### Canonical scenarios published

Five canonical scenarios, each directory holding six artifacts (an
`operation-aware-decision-request`, a `policy-bundle` — or, for the fifth
scenario, an intentionally invalid one — an `evaluation-trace`, an
`operation-aware-decision-response`, an `audit-evidence`, and a
`gateway-audit-event`):

```text
allow-basic            outcome: allow
deny-precedence        outcome: deny (matching ALLOW and DENY rules; deny wins)
default-deny           outcome: deny (applicable bundle, no matching ALLOW rule, no DENY rule)
not-applicable         outcome: not_applicable (no bundle's scope covers the request)
invalid-policy-bundle  evaluation_status: failed, outcome: null, failure_reason: policy_validation_failure
```

This is deliberately the smallest scenario set that distinguishes every
evaluation-outcome category ADR-0002 names — a substantive `ALLOW`, a
substantive `DENY` reached two different ways, a scope-coverage gap, and an
evaluation failure — not an exhaustive enumeration of every named
illustrative scenario in ADR-0005's own PR G description. See the deferred
scenarios below.

### Directory structure

```text
examples/operation-aware/compatibility/
  README.md
  allow-basic/          operation-aware-decision-request.yaml, policy-bundle.yaml,
                        expected-evaluation-trace.yaml,
                        expected-operation-aware-decision-response.yaml,
                        expected-audit-evidence.yaml,
                        expected-gateway-audit-event.yaml
  deny-precedence/       (same six files)
  default-deny/          (same six files)
  not-applicable/        (same six files)
  invalid-policy-bundle/ operation-aware-decision-request.yaml,
                        invalid-policy-bundle.yaml (intentionally invalid),
                        expected-evaluation-trace.yaml,
                        expected-operation-aware-decision-response.yaml,
                        expected-audit-evidence.yaml,
                        expected-gateway-audit-event.yaml
```

This directory structure is the vector index. It is deliberately not a
governed schema: it is not tracked in `basis_schemas.PUBLISHED_CONTRACTS` or
any `OPERATION_AWARE_*_CONTRACTS` tuple, and no new public contract (a
"compatibility-test-vector," "scenario-manifest," or similar) was added to
`contract-metadata` or any other published contract. It is a deterministic,
documented filesystem convention that both humans and
`tests/test_operation_aware_compatibility_vectors.py` read directly.

### Contract coverage

Every scenario's six artifacts are validated against PR A through PR F's
own published field policy, consumed exactly as published: no existing
contract (`decision-request`, `decision-response`, `audit-event`,
`contract-metadata`, `redaction-classification`, `reason-code`,
`identity-evidence-reference`, `adapter-evidence-reference`,
`operation-aware-decision-request`, `policy-condition`, `policy-rule`,
`policy-bundle`, `trace-rule-evidence`, `evaluation-trace`,
`operation-aware-decision-response`, `audit-evidence`,
`gateway-audit-event`, `action-string`, `resource-identifier`) was
modified, and no contract version, required/optional field, enum, pattern,
constraint, or example changed.

### Invalid-policy scenario: category choice

`invalid-policy-bundle`'s fixture uses a duplicate `rule_id` across two
rules in the same bundle — the same invalidity `policy-bundle.yaml`'s own
published `examples.invalid` block already tests. That contract's own field
policy documents this specific check as BUNDLE-level validation: "a
cross-rule uniqueness concern a single rule object's own schema cannot
express or enforce" (`schemas/policy-bundle/policy-bundle.yaml`). Every rule
in the fixture, and the bundle's own top-level fields, are individually
well formed; the defect only exists across the `rules` array as a whole.
The corresponding kernel failure category is therefore
`policy_validation_failure` ("shaped correctly but fails internal
consistency validation," per ADR-0002 Section 14), not `invalid_policy_bundle`
("does not conform to the required shape") — the earlier revision of this
scenario classified it the other way around, which this correction fixes.
`invalid_policy_bundle` remains a valid, non-deprecated failure category; it
applies to a bundle malformed at the shape level (a missing required field,
a malformed rule/condition shape, an invalid enum value, an invalid
identifier pattern), which is a different defect than this scenario's
fixture demonstrates. `evaluation_status: failed` and `outcome: null` together — never
`deny` — and the gateway event separately records fail-closed
`enforcement_action: deny` without ever serializing a kernel deny.

### Cross-object invariants

`tests/test_operation_aware_compatibility_vectors.py` checks, for every
scenario: `request_id`/`correlation_id` alignment across all six artifacts;
`bundle_id`/`bundle_version` alignment where each artifact happens to carry
them (PR F's own permissive, present-only agreement — no stronger
both-or-none rule is invented here); `evaluation_status`/`outcome`/
`failure_reason`/`reason_code` agreement between the response and trace;
the audit evidence and gateway event preserving the kernel result
unchanged; the gateway event's `audit_evidence_id` referencing the
scenario's own audit-evidence record; and trace `rule_id` values existing
in, and agreeing in `effect` with, the paired policy bundle's rules (never
inferring rule priority from array order). Negative mutation tests (small,
in-memory changes to a loaded fixture) confirm the harness actually
detects drift in each of these invariants.

### Downstream consumption

These vectors are the future conformance target for `basis-core`
(evaluating each scenario's request against its bundle should reach the
recorded response/trace), `basis-gateway` (assembling each scenario's
audit evidence and kernel result into the recorded gateway event,
including fail-closed behavior on `not-applicable` and
`invalid-policy-bundle`), and `basis-console` (sample data for operator-
and training-mode explanation rendering). None of this is implemented or
verified by this PR, and no cross-repository conformance is claimed to be
green today.

### Deterministic and offline

Every identifier, digest, and timestamp is fixed and synthetic: no current-
time generation, no random UUIDs, no filesystem-order dependence, no
network access, and no dependency on `basis-core`, `basis-gateway`,
Docker, AWS, an identity provider, protocol devices, or any other external
service. `tests/test_operation_aware_compatibility_vectors.py` contains no
branch-dependent Git usage (the same CI hazard PR E's own history already
fixed once).

### No runtime policy execution

Neither the fixtures nor their tests parse a policy bundle's `match`/
`conditions` against a request and compute an outcome. These are static,
hand-authored expected artifacts checked for shape and cross-object
consistency — not an evaluator, and not a second policy engine.

### Compatibility authority

```text
basis-architecture:        normative authorization and audit semantics
basis-schemas contracts:   normative machine-readable shapes
PR G compatibility vectors: canonical examples of the current architecture and contracts
future implementation repositories: consume the contracts and vectors
```

PR G does not define new authorization semantics and introduces no
undocumented behavior beyond what ADR-0001 through ADR-0004 and PR A
through PR F already establish.

### Security / synthetic data

Every fixture value is synthetic: no real user, employee, customer, site,
device, or infrastructure identifier, and no real credential, token,
claim, or protocol capture. `tests/test_operation_aware_compatibility_vectors.py`
scans every fixture's parsed keys and raw text for a prohibited-field and
prohibited-marker list as a regression guard.

### Deferred scenarios

Condition-evaluation-error and gateway-local failure are deliberately not
included as canonical scenarios, despite each having a precedent in PR E's
or PR F's own `examples:` blocks — neither has a deterministic,
architecture-approved input-to-outcome mapping distinct from the five
scenarios already published (see
[`examples/operation-aware/compatibility/README.md`, "Deferred scenarios"](../examples/operation-aware/compatibility/README.md#14-deferred-scenarios)
for the full reasoning on each). ADR-0005's own PR G description also names
missing context, unknown resource type, and unsupported schema version as
illustrative candidates; each is deferred for the same reason — it would
either duplicate an evaluation state already covered or require inventing
a deterministic input this repository's published contracts do not yet
pin down precisely enough to fixture confidently.

### Operation-aware second-wave completion

With PR G published, every PR ADR-0005 named (PR A through PR G) is now
published. This closes the operation-aware `basis-schemas` second wave. It
does not mean any implementation repository (`basis-core`, `basis-gateway`,
`basis-console`, `basis-adapters`, `basis-identity`) has implemented the
operation-aware model these contracts and vectors describe, and it does
not mean cross-repository conformance is already green — the next
implementation phase is `basis-core` deterministic evaluation behavior,
consistent with [`docs/migration-plan.md`](migration-plan.md).

## Relationship to the first wave

The first-wave contracts (vocabulary, action-string, resource-identifier,
decision-request, decision-response, audit-event — tracked in
[`migration-plan.md`](migration-plan.md) and in
`basis_schemas.PLANNED_CONTRACTS` / `basis_schemas.PUBLISHED_CONTRACTS`) are
unaffected by this second wave. The operation-aware contracts are an additive
expansion — v0.1-era request/response behavior remains stable throughout, per
ADR-0005 Section 7. Within the operation-aware second wave, each ordered PR
(A through G, per [Section 5](#recommended-publication-order-per-adr-0005-section-5))
gets its own tracking tuple rather than sharing one: PR A's shared contracts
are tracked in `basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS`, PR
B's evidence-reference contracts in
`basis_schemas.OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS`, PR C's
request contract in `basis_schemas.OPERATION_AWARE_REQUEST_CONTRACTS`, PR
D's policy bundle/rule contracts in
`basis_schemas.OPERATION_AWARE_POLICY_CONTRACTS`, PR E's response/trace
contracts in `basis_schemas.OPERATION_AWARE_RESPONSE_TRACE_CONTRACTS`, and
PR F's audit contracts in `basis_schemas.OPERATION_AWARE_AUDIT_CONTRACTS`.
This is one first wave plus one second wave organized into per-PR tracking
groups — not seven separate waves — so none of these tracking groups'
completeness claims ever conflate.

PR G is the one exception to "each ordered PR gets its own tracking
tuple": it publishes no new contract, so it has no
`OPERATION_AWARE_COMPATIBILITY_CONTRACTS` (or similarly named) tuple, and
`src/basis_schemas/__init__.py` is unchanged by PR G. Its published
artifacts are tracked only by the deterministic directory structure under
`examples/operation-aware/compatibility/`, documented in that directory's
own `README.md` — a discovery mechanism, not a governed schema or a
contract-tracking constant.
