# Changelog

All notable changes to `basis-schemas` are recorded here. This repository
publishes shared contracts decided in `basis-architecture`; entries describe what
was published or changed, not implementation behavior.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/);
contract versions and lifecycle states follow
[`docs/contract-governance.md`](docs/contract-governance.md).

## [Unreleased]

## [0.2.2] - 2026-07-22

### Fixed

- **Corrected canonical operation-aware compatibility vector fixtures to
  agree with `basis-architecture`'s newly merged evidence-provenance
  clarification** (`docs/architecture/operation-aware-evidence-provenance-semantics.md`).
  This clarification resolved three narrow evidence-provenance disagreements
  surfaced when `basis-core`'s merged operation-aware implementation was
  first compared, field by field, against these vectors. This release
  corrects the fixtures, not the architecture: it introduces no new
  authorization semantics, no new schema field, no new reason-code
  vocabulary, and no change to any authorization outcome, `failure_reason`
  classification, or scenario count.
  - **Top-level `explanation` is no longer synthesized aggregate prose.**
    `explanation` on `expected-operation-aware-decision-response.yaml`,
    `expected-evaluation-trace.yaml`, `expected-audit-evidence.yaml`, and
    `expected-gateway-audit-event.yaml` is optional and non-authoritative;
    `reason_code` remains the authoritative machine-readable explanation.
    Every one of the five canonical scenarios now carries
    `explanation: null` at the top level in all four artifacts, replacing
    hand-authored aggregate sentences ("Operator role matched an allow rule
    for read:ahu.", "Deny precedence applied; an interlock-scoped deny rule
    matched.", and similar) that no governed evaluation stage actually
    supplies.
  - **Matched rule evidence now preserves authored `reason_code`/
    `explanation` exactly.** `allow-basic`'s matched rule's `explanation`
    now reads "Operators may read AHU telemetry." (the rule's own authored
    text in `policy-bundle.yaml`), not a synthesized sentence.
    `deny-precedence`'s matched `ALLOW` rule (`allow-operator-write-hvac-setpoint`)
    now carries its authored `explanation`, "Operators may write HVAC
    setpoints." — previously omitted even though the rule genuinely
    matched; deny precedence governs the final outcome, not whether the
    `ALLOW` rule matched. `deny-precedence`'s matched `DENY` rule's
    `explanation` is corrected from "Control-affecting **operation** denied
    while an interlock is engaged." to "Control-affecting **operations**
    are denied while an interlock is engaged." — matching
    `policy-bundle.yaml`'s own authored text exactly, correcting a
    previously undetected wording drift between the authored rule and the
    expected trace.
  - **Non-matched and skipped rules omit authored match rationale.**
    `default-deny`'s one candidate rule was already correctly
    `rule_result: not_matched` with no `reason_code`/`explanation`; this
    release adds regression coverage proving the harness would catch a
    future regression here. No canonical scenario currently exercises
    `rule_result: skipped` or `rule_result: error`; both remain deferred
    (see `examples/operation-aware/compatibility/README.md`, "Deferred
    scenarios").
  - **Bundle identity is now retained for `NOT_APPLICABLE` and for the
    typed semantic policy-validation failure.** `not-applicable`'s
    `bundle_id`/`bundle_version` (previously `null` on the response, and
    absent on the trace, audit evidence, and gateway event) now carry
    `bundle-compat-hvac-scope` / `"1.0.0"` — the identity of the bundle
    whose scope was checked and found not to cover the request — on every
    artifact that carries the fields. `invalid-policy-bundle`'s
    `bundle_id`/`bundle_version` (previously absent everywhere) now carry
    `bundle-compat-invalid-policy` / `"1.0.0"` — the identity of the typed
    bundle that constructed successfully before being rejected for its
    duplicate `rule_id` values. Bundle identity is provenance for which
    bundle was checked or rejected; it is never a claim that the bundle
    applied, matched, or granted anything. The `invalid-policy-bundle`
    scenario's `failure_reason: policy_validation_failure` classification
    (corrected in `v0.2.1`) is unchanged and reverified by this release.
  - Updated all four `expected-*.yaml` artifacts in every one of the five
    scenario directories under
    `examples/operation-aware/compatibility/`; updated
    `examples/operation-aware/compatibility/README.md` and
    `docs/operation-aware-compatibility-vectors.md` with a new
    "Evidence-provenance semantics" section documenting the governed
    null/optional-explanation, rule-evidence-projection, and
    bundle-identity-retention rules; added and strengthened
    `tests/test_operation_aware_compatibility_vectors.py` coverage,
    including new cross-artifact invariants (top-level explanation
    nullness, matched-rule authored-text preservation, not-matched/skipped
    rationale omission, and bundle-identity retention for `not-applicable`
    and `invalid-policy-bundle`) and paired negative-mutation tests proving
    the harness detects drift in each. **No schema contract, field, or
    enum changed**, and **no authorization outcome changed**: every
    scenario's `outcome` / `evaluation_status` / `failure_reason` is
    identical to `v0.2.1`. This is a compatibility-fixture correction
    aligned to newly clarified architecture, not a new evaluator feature,
    schema family, reason-code vocabulary, or breaking change.

## [0.2.1] - 2026-07-18

### Fixed

- **Corrected the `invalid-policy-bundle` operation-aware compatibility
  vector's failure-category classification.** The scenario's duplicate
  `rule_id` defect is now classified as `policy_validation_failure` rather
  than `invalid_policy_bundle`, correcting a misclassification introduced
  when the scenario was first published in `v0.2.0`. The policy bundle in
  this scenario is shaped correctly — every rule and every top-level field
  is individually valid — but violates a cross-rule, bundle-level
  invariant (`rule_id` uniqueness across the `rules` array) that no single
  rule object's own schema can express or enforce: duplicate `rule_id`
  values are a **semantic, cross-object validation failure**, not a
  structural one. Per ADR-0002 Section 14, that is "shaped correctly but
  fails internal consistency validation" (`policy_validation_failure`),
  not "does not conform to the required shape" (`invalid_policy_bundle`).
  `invalid_policy_bundle` remains the correct, valid classification for a
  bundle that fails at the structural shape level — this correction does
  not narrow or deprecate that category, only fixes which category this
  one scenario's defect belongs to. Updated
  `expected-evaluation-trace.yaml`, `expected-operation-aware-decision-response.yaml`,
  `expected-audit-evidence.yaml`, and `expected-gateway-audit-event.yaml`
  (**four expected artifacts**) under
  `examples/operation-aware/compatibility/invalid-policy-bundle/` to agree
  on `failure_reason: policy_validation_failure`; removed the
  `reason_code: policy_bundle_invalid` value from the three artifacts that
  carried it, since no approved reason-code equivalent for
  `policy_validation_failure` is published in this repository's governed
  reason-code vocabulary — that structural reason code was **removed, not
  replaced with an invented one**. Updated
  `examples/operation-aware/compatibility/README.md`,
  `docs/operation-aware-compatibility-vectors.md`, and
  `docs/operation-aware-schema-readiness.md` to describe the corrected
  reasoning, and updated `tests/test_operation_aware_compatibility_vectors.py`
  accordingly. The `invalid-policy-bundle` scenario directory keeps its
  existing name — it describes the broad scenario (the supplied bundle is
  invalid), which is a separate concern from the precise
  `failure_reason` category. **No schema contract, field, or enum
  changed**: `policy_validation_failure` and `invalid_policy_bundle` were
  both already published, six-value-enum members of `evaluation-trace`,
  `operation-aware-decision-response`, `audit-evidence`, and
  `gateway-audit-event`'s `failure_reason` field before this correction.
  This is a compatibility-vector correctness fix, not a new feature or a
  contract change. The release is prepared through a dedicated release PR,
  consistent with this repository's existing release convention (see `b5d6709`, "chore:
  prepare v0.2.0 release").

## [0.2.0] - 2026-07-10

### Added

- **Operation-aware compatibility examples and test vectors published**
  (second-wave, PR G of `basis-architecture`'s operation-aware schema
  readiness plan, ADR-0005 — the final planned PR in this second wave).
  Publishes canonical, cross-contract compatibility fixtures under
  `examples/operation-aware/compatibility/` connecting PR A through PR F's
  individually-published contracts into five complete operation-aware
  authorization scenarios: `allow-basic` (a matching ALLOW rule, no
  matching DENY rule), `deny-precedence` (a matching ALLOW and a matching
  DENY rule in the same applicable bundle; DENY wins unconditionally),
  `default-deny` (an applicable bundle with no matching ALLOW rule and no
  DENY rule at all), `not-applicable` (no policy bundle's scope covers the
  request; the gateway separately records fail-closed enforcement without
  the kernel's `not_applicable` outcome ever being rewritten as `deny`),
  and `invalid-policy-bundle` (an intentionally invalid bundle — duplicate
  `rule_id` values — producing `evaluation_status: failed`,
  `outcome: null`, `failure_reason: invalid_policy_bundle`, never a kernel
  `deny`). Each scenario directory carries six artifacts: an
  `operation-aware-decision-request`, a `policy-bundle` (or, for the fifth
  scenario, an intentionally invalid `invalid-policy-bundle.yaml`), an
  `expected-evaluation-trace`, an `expected-operation-aware-decision-response`,
  an `expected-audit-evidence`, and an `expected-gateway-audit-event`. Adds
  no new public contract, no new entry to `PUBLISHED_CONTRACTS` or any
  `OPERATION_AWARE_*_CONTRACTS` tracking tuple, and modifies no existing
  contract YAML — PR A through PR F are consumed exactly as published.
  `tests/test_operation_aware_compatibility_vectors.py` validates every
  fixture against its governing contract's own field policy and checks the
  cross-artifact invariants (shared identifiers, policy provenance,
  evaluation-state agreement) that only become visible once a scenario's
  six artifacts are considered together, plus negative-mutation tests
  proving the harness detects drift. See
  [`examples/operation-aware/compatibility/README.md`](examples/operation-aware/compatibility/README.md)
  and
  [`docs/operation-aware-compatibility-vectors.md`](docs/operation-aware-compatibility-vectors.md).
  **With PR G published, the operation-aware second wave is complete** —
  see [`docs/operation-aware-schema-readiness.md`](docs/operation-aware-schema-readiness.md).

- **Audit contracts published** (second-wave, PR F of
  `basis-architecture`'s operation-aware schema readiness plan, ADR-0005).
  Publishes the bounded, durable, audit-oriented evidence shape and the
  gateway-emitted enforcement-boundary event shape named by ADR-0003
  (`docs/architecture/operation-aware-trace-audit-evidence.md`). Two
  contracts, in dependency order:
  - `schemas/audit-evidence/audit-evidence.yaml` — the bounded, durable
    evidence representation of one operation-aware authorization
    evaluation: `evidence_id` and `request_id` identity, optional
    `correlation_id` / `trace_id` association, the identical
    `evaluation_status` / `outcome` / `failure_reason` model reused
    unchanged from `operation-aware-decision-response` and
    `evaluation-trace` (parity-tested, same required invariant), optional
    `bundle_id` / `bundle_version` from `policy-bundle`, a bounded
    `matched_rule_ids` array of stable rule identifiers (never a full
    per-rule trace), optional `identity_evidence_reference` /
    `adapter_evidence_reference` reused unchanged from PR B, an optional
    `reason_code` / `explanation`, a required `recorded_at` timestamp
    distinct from any request-supplied `evaluation_time`, and an optional
    instance-level `schema_version`. This is the kernel-side audit
    evidence ADR-0003 Section 14 names `basis-core` as producing as an
    associated evaluation artifact alongside the decision response and
    evaluation trace — not embedded in `operation-aware-decision-response`
    (which has no `audit_evidence`/`audit_evidence_id` field), with no
    runtime transport, envelope, return tuple, or delivery mechanism
    defined by this PR; not persisted by `basis-core` anywhere durable,
    and not assembled by `basis-gateway` (that is `gateway-audit-event`'s
    role — see below). Contract version `0.1.0`, lifecycle `experimental`.
    Declares `depends_on: [contract-metadata,
operation-aware-decision-response, evaluation-trace, policy-bundle,
identity-evidence-reference, adapter-evidence-reference,
reason-code]`.
  - `schemas/gateway-audit-event/gateway-audit-event.yaml` — the bounded,
    gateway-emitted record of what happened at the enforcement boundary
    for one event: `event_id` and a closed `event_type`
    (`gateway_authorization`, the smallest safe representation for this
    PR), a required emission `timestamp` distinct from `audit-evidence`'s
    own `recorded_at`, `request_id` / optional `correlation_id` (no
    `subject_id` / `action` / `resource` / `resource_type` field — per
    ADR-0003 Section 6, this contract avoids duplicating the evaluated
    request), the identical kernel `evaluation_status` / `outcome` /
    `failure_reason` model reused unchanged (parity-tested), optional
    `bundle_id` / `bundle_version` / `trace_id`, a required
    `audit_evidence_id` reference to the associated `audit-evidence`
    record (referenced, never embedded), an optional `gateway_id`, a
    closed `enforcement_action` (`allow` / `deny`) kept structurally
    independent of the kernel `outcome` — `enforcement_action: deny` is
    valid and expected alongside kernel `outcome: not_applicable` and
    alongside `evaluation_status: failed`, representing fail-closed
    gateway behavior without ever rewriting the kernel value — and an
    optional, small, closed `gateway_failure_reason`
    (`gateway_timeout` / `upstream_unavailable` /
    `audit_assembly_failure` / `internal_gateway_error`) distinct in name
    and meaning from the kernel `failure_reason`, required to pair with
    `enforcement_action: deny` when non-null. This is the record
    ADR-0003 Section 14 names `basis-gateway` as assembling by "combining
    kernel evidence with enforcement facts." Contract version `0.1.0`,
    lifecycle `experimental`. Declares
    `depends_on: [contract-metadata, operation-aware-decision-response,
  evaluation-trace, policy-bundle, audit-evidence, reason-code]`.
    `docs/audit-evidence.md` and `docs/gateway-audit-event.md` added.
    Cross-contract parity is enforced by tests: both contracts' reproduced
    `outcome_values` / `evaluation_status_values` / `failure_reason_values`
    are tested for exact agreement with `operation-aware-decision-response`
    and `evaluation-trace`; both contracts' `bundle_version_pattern` and
    `reason_code_pattern` are tested against their canonical source
    contracts. State-matrix cross-object invariants are tested directly:
    kernel `outcome: not_applicable` paired with gateway
    `enforcement_action: deny`; kernel `evaluation_status: failed` paired
    with `enforcement_action: deny`; a gateway-local failure (kernel
    completed/allow, `gateway_failure_reason` set, `enforcement_action:
deny`) demonstrating `enforcement_action` independence from kernel
    outcome; and `gateway_failure_reason` rejected whenever paired with
    `enforcement_action: allow`. Every contract sets
    `additional_properties: false` at every object level and never carries
    an `access_token`, `id_token`, `refresh_token`, `jwt`, `bearer_token`,
    `authorization_header`, `cookie`, `session_secret`, `client_secret`,
    `password`, `private_key`, `api_key`, `credential`, `raw_claims`,
    `full_claim_set`, `raw_payload`, `raw_protocol_payload`, `full_request`,
    `request_snapshot`, `full_policy`, `policy_document`, `debug`,
    `exception`, `stack_trace`, `traceback`, `subject_id`, `action`,
    `resource`, `resource_type`, `http_status`, `response_status`,
    `signature`, `signature_algorithm`, `hash_chain`, `previous_hash`, or
    `merkle_root` field — any such field is rejected as unknown, enforced
    by regression tests. Neither contract publishes a top-level
    `redaction_classification` field, and neither claims YAML shape alone
    provides immutability, tamper resistance, non-repudiation,
    cryptographic authenticity, or chain of custody — durability and
    storage remain explicitly a producer/deployment responsibility, per
    ADR-0003 Section 17's "Open Questions Deferred." Does not implement
    audit storage, retention, indexing, export, signing, tamper-evidence,
    gateway enforcement, gateway middleware, or HTTP response behavior —
    every one of these remains explicitly deferred. **The first-wave
    `schemas/audit-event/audit-event.yaml` is completely unchanged** — no
    rename, no widening, no version/field/example/validation change; its
    `authorization_decision` event type and `allowed`/`denied`/`error`
    outcome vocabulary remain exactly as published, never compared or
    unified with either new contract's own vocabulary. No existing
    contract (`decision-request`, `decision-response`, `audit-event`,
    `action-string`, `resource-identifier`, `contract-metadata`,
    `redaction-classification`, `reason-code`,
    `identity-evidence-reference`, `adapter-evidence-reference`,
    `operation-aware-decision-request`, `policy-condition`, `policy-rule`,
    `policy-bundle`, `trace-rule-evidence`, `evaluation-trace`,
    `operation-aware-decision-response`) changed shape, required fields,
    optional fields, examples, or validation behavior, and none was made to
    depend on these two new contracts. Not mandatory anywhere; no
    implementation repository consumes PR F yet.
- `basis_schemas.OPERATION_AWARE_AUDIT_CONTRACTS` metadata listing PR F's
  two contracts in dependency-and-publication order. Additive: does not
  change `PLANNED_CONTRACTS`, `PUBLISHED_CONTRACTS`,
  `OPERATION_AWARE_SHARED_METADATA_CONTRACTS`,
  `OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS`,
  `OPERATION_AWARE_REQUEST_CONTRACTS`, `OPERATION_AWARE_POLICY_CONTRACTS`,
  or `OPERATION_AWARE_RESPONSE_TRACE_CONTRACTS`.
  `docs/operation-aware-schema-readiness.md` updated: PR F marked
  published, with a section describing the contracts published, their
  dependency order, the trace-vs-audit-vs-gateway-event distinction, the
  kernel-result-vs-gateway-enforcement separation, decision/evaluation-
  state reuse, fail-closed representation, policy provenance, evidence
  references, redaction handling, boundedness, security, compatibility
  posture, first-wave `audit-event` unchanged confirmation, what PR F
  deliberately excludes, and how PR G is expected to use PR A through
  PR F's own published examples. `PR G` remains marked not started.

- **Response and trace contracts published** (second-wave, PR E of
  `basis-architecture`'s operation-aware schema readiness plan, ADR-0005).
  Publishes the machine-readable response and trace shapes a future
  `basis-core` v0.2.0 will produce after deterministic operation-aware
  policy evaluation, per ADR-0002
  (`docs/architecture/operation-aware-evaluation-semantics.md`) and ADR-0003
  (`docs/architecture/operation-aware-trace-audit-evidence.md`). Three
  contracts, in dependency order:
  - `schemas/trace-rule-evidence/trace-rule-evidence.yaml` — the bounded,
    deterministic explanation record for one policy rule considered during
    evaluation: `rule_id` and `effect` reused unchanged from `policy-rule`,
    a closed `rule_result` (`matched` / `not_matched` / `skipped` /
    `error`, reproducing ADR-0003 Section 5's "Match / no-match / error"
    and Section 4's skipped-rule category), optional bounded
    `condition_results` (each a `condition_id` reused from
    `policy-condition` plus a closed three-value `result` reproducing
    ADR-0002 Section 9's three condition outcomes), and an optional
    `reason_code` (reusing `reason-code` unchanged) / static
    `explanation`. Never copies a rule's match criteria or conditions, and
    never carries a condition's `field_path`, `operator`, `expected_value`,
    or the raw value compared. Contract version `0.1.0`, lifecycle
    `experimental`. Declares `depends_on: [contract-metadata, policy-rule,
policy-condition, reason-code]`.
  - `schemas/evaluation-trace/evaluation-trace.yaml` — the deterministic,
    bounded explanation of one kernel evaluation: `trace_id` and
    `request_id` identity, optional `correlation_id` passthrough, an
    applicable policy bundle's `bundle_id` / `bundle_version` (reused
    unchanged from `policy-bundle`) when one applied, a closed, nullable
    `bundle_applicability` (`applicable` / `not_applicable` / `null`,
    distinct from the final outcome per ADR-0002 Section 5's
    `NOT_APPLICABLE` semantics), a closed, nullable `outcome`
    (`allow` / `deny` / `not_applicable` / `null`, matching
    `decision-response`'s outcome vocabulary exactly — no new outcome
    value introduced) kept structurally independent of a closed
    `evaluation_status` (`completed` / `failed`) and a closed, new
    six-value `failure_reason` (`invalid_request` /
    `unsupported_schema_version` / `invalid_policy_bundle` /
    `policy_validation_failure` / `condition_evaluation_error` /
    `internal_evaluation_error`, reproducing ADR-0002 Section 14's
    representative evaluation-failure categories — distinct from, and
    never conflated with, the existing first-wave `decision-response`'s
    own four-value `failure_reason`), a (possibly empty) `rule_evidence`
    array of `trace-rule-evidence`-shaped values with trace-level
    `rule_id` uniqueness, and an optional `reason_code` / `explanation`.
    **Required invariant, enforced and tested: `outcome` is null if and
    only if `evaluation_status` is `failed`** — a failed evaluation never
    serializes an authorization outcome (ADR-0002 Section 14). Contract
    version `0.1.0`, lifecycle `experimental`. Declares
    `depends_on: [contract-metadata, operation-aware-decision-request,
policy-bundle, trace-rule-evidence, reason-code]`.
  - `schemas/operation-aware-decision-response/operation-aware-decision-response.yaml`
    — the additive vNext response contract: `request_id` echoed from PR
    C's `operation-aware-decision-request`, the identical
    `outcome` / `evaluation_status` / `failure_reason` model as
    `evaluation-trace` (kept in parity, same required invariant), optional
    `bundle_id` / `bundle_version` from `policy-bundle`, an optional
    `trace_id` reference and/or embedded `evaluation_trace` — when both
    are present, `evaluation_trace.trace_id` must equal `trace_id`, and
    when `evaluation_trace` is present its `request_id` /
    `evaluation_status` / `outcome` must agree with the response's own
    (documented invariants, tested against the contract's own examples,
    not statically enforceable in YAML) — and an optional `reason_code` /
    `explanation`. **The existing `schemas/decision-response/
  decision-response.yaml` is unchanged**: not renamed, replaced,
    widened, or reinterpreted; this is a separate, additive vNext contract
    surface, not a v2. Contract version `0.1.0`, lifecycle `experimental`.
    Declares `depends_on: [contract-metadata,
  operation-aware-decision-request, policy-bundle, evaluation-trace,
  reason-code]`.
    `docs/trace-rule-evidence.md`, `docs/evaluation-trace.md`, and
    `docs/operation-aware-decision-response.md` added. Cross-contract parity
    is enforced by tests: `trace-rule-evidence`'s reproduced `effect_values`
    are tested against `policy-rule`'s own already-verified copy;
    `evaluation-trace`'s reproduced `bundle_version_pattern` is tested
    against `policy-bundle`'s own pattern; all three contracts' reproduced
    `reason_code_pattern` is tested against the canonical `reason-code`
    contract; and the `outcome_values` / `evaluation_status_values` /
    `failure_reason_values` vocabularies are tested for exact agreement
    between `evaluation-trace` and `operation-aware-decision-response`.
    Every contract sets `additional_properties: false` at every object level
    and never carries an `access_token`, `id_token`, `refresh_token`, `jwt`,
    `bearer_token`, `authorization_header`, `cookie`, `session_secret`,
    `client_secret`, `password`, `private_key`, `api_key`, `credential`,
    `raw_claims`, `full_claim_set`, `raw_payload`, `raw_protocol_payload`,
    `full_request`, `request_snapshot`, `full_policy`, `policy_document`,
    `debug`, `exception`, `stack_trace`, `traceback`, `gateway_enforcement`,
    `enforcement_result`, `http_status`, or `response_status` field — any
    such field is rejected as unknown, enforced by regression tests. Does
    not implement rule matching, condition evaluation, deny precedence,
    default deny, evaluation, persistence, gateway enforcement, or audit —
    every one of these remains explicitly deferred. Evaluation trace is
    explicitly not audit evidence (ADR-0003 Section 2): `AuditEvidence` and
    `GatewayAuditEvent` remain deferred to PR F, which is expected to
    reference `evaluation-trace.trace_id` and
    `operation-aware-decision-response.request_id` rather than redefining
    either. No existing contract (`decision-request`, `decision-response`,
    `audit-event`, `action-string`, `resource-identifier`,
    `contract-metadata`, `redaction-classification`, `reason-code`,
    `identity-evidence-reference`, `adapter-evidence-reference`,
    `operation-aware-decision-request`, `policy-condition`, `policy-rule`,
    `policy-bundle`) changed shape, required fields, optional fields,
    examples, or validation behavior, and none was made to depend on these
    three new contracts. Not mandatory anywhere; no implementation
    repository consumes PR E yet.
- `basis_schemas.OPERATION_AWARE_RESPONSE_TRACE_CONTRACTS` metadata listing
  PR E's three contracts in dependency-and-publication order. Additive:
  does not change `PLANNED_CONTRACTS`, `PUBLISHED_CONTRACTS`,
  `OPERATION_AWARE_SHARED_METADATA_CONTRACTS`,
  `OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS`,
  `OPERATION_AWARE_REQUEST_CONTRACTS`, or
  `OPERATION_AWARE_POLICY_CONTRACTS`.
  `docs/operation-aware-schema-readiness.md` updated: PR E marked
  published, with a section describing the contracts published, their
  dependency order, authorization outcomes, evaluation-failure separation,
  policy bundle/rule identity reuse, reason-code reuse, trace boundedness,
  the redaction/security boundary, the trace-vs-audit distinction,
  compatibility posture, what PR E deliberately excludes, and how PR F is
  expected to consume PR E's identifiers without redefining them.

- **Policy bundle and rule contracts published** (second-wave, PR D of
  `basis-architecture`'s operation-aware schema readiness plan, ADR-0005).
  Publishes the machine-readable policy model a future `basis-core` v0.2.0
  will validate and evaluate against the operation-aware request published
  by PR C, per the policy bundle/rule model in
  `docs/architecture/operation-aware-policy-rule-model.md` (ADR-0004). This
  is a structured policy **data model**, not a policy language: no Rego,
  Cedar, CEL, Python, JavaScript, SQL, WASM, or custom DSL is chosen, and no
  executable policy expression, embedded code, or `script` field is
  published. Three contracts, in dependency order:
  - `schemas/policy-condition/policy-condition.yaml` — a deterministic,
    data-only predicate: `condition_id`, a validated dotted `field_path`
    referencing an operation-aware-decision-request category, an open (not
    closed-enum) lowercase snake_case `operator`, and a
    smallest-safe-representation `expected_value` (string, number, boolean,
    null, or a homogeneous array of those scalars). All four fields
    required; no optional fields. Contract version `0.1.0`, lifecycle
    `experimental`. Declares `depends_on: [contract-metadata]`. The operator
    vocabulary is deliberately open (ADR-0004 Section 7 defers the operator
    language); a structurally valid field path or operator is never a claim
    of `basis-core` runtime support.
  - `schemas/policy-rule/policy-rule.yaml` — a deterministic unit of
    evaluation: a stable `rule_id`, an effect closed to exactly `allow` /
    `deny` (ADR-0004 Section 5) — `not_applicable` is rejected, because it
    is a bundle-applicability outcome (ADR-0002 Section 5), never a rule
    effect — explicit structured `match` criteria mirroring
    operation-aware-decision-request's categories (subject/action/resource/
    location/device/protocol/operation-intent/safety/environment/risk
    selectors, each an any-of array; every populated selector category is
    AND-combined), an optional non-empty `conditions` array of
    policy-condition-shaped values with rule-level duplicate-condition-ID
    rejection, an optional `reason_code` reusing the `reason-code` contract
    unchanged, and an optional static, non-executable `explanation`. At
    least one of `match` or `conditions` is required — this contract does
    not permit an unconditional rule that implicitly matches every request.
    No rule-ordering/priority field is published: ADR-0004 Section 10 and
    the evaluation semantics document's Section 8 require any future
    priority model to be explicit, which neither document yet is, so this
    contract relies on the already-required, already-unique `rule_id` as a
    future deterministic tie-breaker instead of inventing ordering
    semantics. Contract version `0.1.0`, lifecycle `experimental`. Declares
    `depends_on: [contract-metadata, policy-condition,
operation-aware-decision-request, reason-code, action-string,
resource-identifier]`.
  - `schemas/policy-bundle/policy-bundle.yaml` — the unit of policy
    identity, versioning, scope, ownership, provenance, and rule grouping:
    `bundle_id`, `bundle_version` (this bundle's own content version) and
    `schema_version` (the policy-bundle contract shape version an instance
    targets) kept as two distinct required semver fields — neither
    conflated with the other nor with the `basis-schemas` package version
    — `policy_owner` (provenance/governance metadata only, never an
    authorization subject, never a credential), an optional `scope` (small
    explicit nested selectors: action, resource type, site/building/zone/
    area, device class, environment mode, authority mode, protocol; absent
    scope means globally applicable, a present scope restricts
    applicability to requests matching every populated selector, and an
    entirely empty scope object is invalid), and a required non-empty
    `rules` array of policy-rule-shaped values with bundle-level duplicate-
    rule-ID rejection. Optional descriptive/provenance/deprecation
    metadata: `description`, `source_ref`, `approval_ref`, `created_at`,
    `updated_at`, `compatibility_target`, `deprecated`, `replaced_by`. **No
    `validation_status` field is published** — a bundle cannot make itself
    valid by declaring itself valid; validity is derived by a future
    `basis-core` validator/runtime process, never self-asserted. Contract
    version `0.1.0`, lifecycle `experimental`. Declares
    `depends_on: [contract-metadata, policy-rule]`.
    `docs/policy-condition.md`, `docs/policy-rule.md`, and
    `docs/policy-bundle.md` added. Cross-contract parity is enforced by tests:
    `policy-rule`'s reproduced `action_pattern` / `resource_pattern` /
    `resource_type_pattern` / `open_identifier_pattern` /
    `operation_intent_values` / `reason_code_pattern` are tested against the
    canonical `action-string`, `resource-identifier`,
    `operation-aware-decision-request`, and `reason-code` contracts;
    `policy-bundle`'s reproduced scope patterns are tested against
    `policy-rule`'s own already-verified copies; nested condition and rule
    shapes are tested for parity against their standalone contracts. Every
    contract sets `additional_properties: false` at every object level and
    never carries an `access_token`, `id_token`, `refresh_token`, `jwt`,
    `bearer_token`, `authorization_header`, `cookie`, `session_secret`,
    `client_secret`, `password`, `private_key`, `api_key`, `raw_claims`,
    `raw_payload`, `raw_protocol_payload`, `device_secret`, `script`, `code`,
    `executable`, `command`, `shell`, `python`, `javascript`, `rego`,
    `cedar`, `cel`, `wasm`, `sql`, `template`, or `expression` field — any
    such field is rejected as unknown, enforced by regression tests. Does not
    implement policy loading, storage, distribution, synchronization,
    signing, signature verification, tamper-evident packaging, an approval
    workflow, an authoring UI, a simulation UI, deployment behavior,
    multi-bundle hierarchy, policy federation, tenant/site policy delegation,
    runtime evaluation, condition execution, gateway enforcement, or audit
    persistence — every one of these remains explicitly deferred, per
    ADR-0004 Section 18. No existing contract (`decision-request`,
    `decision-response`, `audit-event`, `action-string`,
    `resource-identifier`, `contract-metadata`, `redaction-classification`,
    `reason-code`, `identity-evidence-reference`,
    `adapter-evidence-reference`, `operation-aware-decision-request`)
    changed shape, required fields, optional fields, examples, or validation
    behavior, and none was made to depend on these three new contracts. Not
    mandatory anywhere; no implementation repository consumes PR D yet.
- `basis_schemas.OPERATION_AWARE_POLICY_CONTRACTS` metadata listing PR D's
  three contracts in dependency-and-publication order. Additive: does not
  change `PLANNED_CONTRACTS`, `PUBLISHED_CONTRACTS`,
  `OPERATION_AWARE_SHARED_METADATA_CONTRACTS`,
  `OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS`, or
  `OPERATION_AWARE_REQUEST_CONTRACTS`.
  `docs/operation-aware-schema-readiness.md` updated: PR D marked published,
  with a section describing the contracts published, their dependency
  order, policy scope, rule effects, request match criteria, condition
  extensibility, reason-code reuse, validation boundaries, compatibility
  posture, security boundaries, what PR D intentionally excludes, and how
  PR E is expected to reference PR D's bundle/rule identifiers in a future
  response and evaluation trace.
- **Operation-aware decision request contract published** (second-wave,
  PR C of `basis-architecture`'s operation-aware schema readiness plan,
  ADR-0005).
  `schemas/operation-aware-decision-request/operation-aware-decision-request.yaml`
  publishes the richer, additive vNext request shape a future `basis-core`
  v0.2.0 evaluates, formalizing the conceptual categories named in ADR-0001
  (`docs/architecture/operation-aware-authorization-model.md`, Section 3).
  Contract version `0.1.0`, lifecycle `experimental`. Required:
  `request_id`, `subject_id`, `action`. Optional: `correlation_id`,
  `subject_roles`, `subject_attrs`, `identity_source`, `authority_mode`, an
  `identity_evidence_reference`, `resource`, `resource_type`, `location`
  (`site_id` / `building_id` / `zone_id` / `area_id`), `device` (`device_id`
  / `device_class`), `protocol_context` (`protocol` / `operation`), a closed
  `operation_intent` (`read_only` / `state_changing` / `control_affecting`),
  an `adapter_evidence_reference`, `safety_context` (`mode` /
  `classification` / `constraint_ids`), `environment_context` (`mode` /
  `condition_ids`), `risk_context` (`classification` / `score`),
  `evaluation_time`, and `expected_policy_version`. Declares `depends_on:
[contract-metadata, action-string, resource-identifier,
identity-evidence-reference, adapter-evidence-reference]`. Never carries an
  `access_token`, `id_token`, `refresh_token`, `jwt`, `bearer_token`,
  `authorization_header`, `cookie`, `session_secret`, `client_secret`,
  `password`, `private_key`, `api_key`, `raw_claims`, `full_claim_set`,
  `raw_payload`, `raw_protocol_payload`, `packet`, `frame`, or
  `device_secret` field, anywhere top-level or nested — any such field is
  rejected as unknown. **The existing `schemas/decision-request/decision-request.yaml`
  is unchanged**: not renamed, replaced, widened, or reinterpreted; this is
  a separate, additive vNext contract surface, not a v2. Notable
  compatibility choices, documented in
  `docs/operation-aware-decision-request.md`: only three fields are
  required (unlike `decision-request`'s four — `evaluation_time` is
  optional here, where `decision-request` requires `timestamp`); the
  canonical resource identifier field is named `resource` rather than
  `resource_id` to sit beside the new explicit `resource_type` field;
  `operation_intent` is closed to three values because ADR-0001 names them
  consistently, unlike the deliberately open `reason-code`; and
  `decision-request`'s free-form `context` map is not retained, in favor of
  the new explicit structured fields. Does not define request assembly,
  evaluation, evidence retrieval, or enforcement; no implementation
  repository consumes this contract yet. `docs/operation-aware-decision-request.md`
  added.
- `basis_schemas.OPERATION_AWARE_REQUEST_CONTRACTS` metadata listing PR C's
  one contract. Additive: does not change `PLANNED_CONTRACTS`,
  `PUBLISHED_CONTRACTS`, `OPERATION_AWARE_SHARED_METADATA_CONTRACTS`, or
  `OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS`.
  `docs/operation-aware-schema-readiness.md` updated: PR C marked published,
  with a section describing the contract published, its dependencies, its
  relationship to the first-wave `decision-request`, the categories
  represented, evidence-reference usage, compatibility posture, what PR C
  intentionally excludes, and how PR D and PR E are expected to build on it.
- **Identity evidence reference contract published** (second-wave, PR B of
  `basis-architecture`'s operation-aware schema readiness plan, ADR-0005).
  `schemas/identity-evidence-reference/identity-evidence-reference.yaml`
  publishes a safe reference to trusted identity evidence: `reference_id`,
  `evidence_digest` (`algorithm` + `value`, structural only), a
  provider-neutral `identity_source`, optional `normalization_version` /
  `mapping_version` provenance, `redaction_classification` (reused, not
  duplicated, from `redaction-classification`), and optional `request_id` /
  `correlation_id`. Contract version `0.1.0`, lifecycle `experimental`.
  Declares `depends_on: [contract-metadata, redaction-classification]`. Never
  carries `access_token`, `id_token`, `refresh_token`, `jwt`, `bearer_token`,
  `authorization_header`, `cookie`, `session_secret`, `client_secret`,
  `password`, `private_key`, `raw_claims`, `full_claim_set`, or `credential`
  — any such field is rejected as unknown. Does not define identity
  establishment, authentication, claim validation, token verification,
  evidence storage/retrieval/retention, or evidence signing/verification.
  `docs/identity-evidence-reference.md` added.
- **Adapter evidence reference contract published** (second-wave, PR B).
  `schemas/adapter-evidence-reference/adapter-evidence-reference.yaml`
  publishes a safe reference to normalized adapter evidence: `reference_id`,
  `evidence_digest` (structural only), an opaque `adapter_source`, an
  optional open (not closed-enum) `protocol` label, optional
  `normalization_version` / `mapping_version` provenance,
  `redaction_classification`, and optional `request_id` / `correlation_id`.
  Contract version `0.1.0`, lifecycle `experimental`. Declares `depends_on:
[contract-metadata, redaction-classification]`. Never carries
  `raw_payload`, `raw_protocol_payload`, `packet`, `frame`, `credential`,
  `password`, `api_key`, `private_key`, or `unredacted_device_secret` — any
  such field is rejected as unknown. Does not define adapter normalization
  logic, protocol parsing, evidence storage/retrieval/retention, or evidence
  signing/verification, and does not make `basis-core` protocol-aware.
  `docs/adapter-evidence-reference.md` added.
- `basis_schemas.OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS` metadata
  listing the two PR B contracts, in publication order. Additive: does not
  change `PLANNED_CONTRACTS`, `PUBLISHED_CONTRACTS`, or
  `OPERATION_AWARE_SHARED_METADATA_CONTRACTS`.
- `docs/operation-aware-schema-readiness.md` updated: PR B marked published,
  with a section describing the contracts published, their dependencies,
  what PR B intentionally excludes, and how PR C is expected to consume
  these references (an optional field on a future operation-aware request,
  not added by this PR).
- **Contract metadata contract published** (second-wave, PR A of
  `basis-architecture`'s operation-aware schema readiness plan, ADR-0005).
  `schemas/contract-metadata/contract-metadata.yaml` formalizes the
  `contract:` block pattern already used identically by all six first-wave
  contracts (identifier, title, version, lifecycle, governance, source,
  description, optional `depends_on`) as its own reusable, citable contract.
  Contract version `0.1.0`, lifecycle `experimental`. No existing contract's
  `contract:` block changes; this publishes the pattern they already follow.
  `docs/contract-metadata.md` added.
- **Redaction classification contract published** (second-wave, PR A).
  `schemas/redaction-classification/redaction-classification.yaml` publishes
  the five-value vocabulary decided in `basis-architecture`
  (`docs/architecture/operation-aware-trace-audit-evidence.md`, ADR-0003,
  §10): `safe_to_expose`, `safe_after_redaction`, `reference_only`,
  `never_store`, `never_display`. Contract version `0.1.0`, lifecycle
  `experimental`. Declares `depends_on: [contract-metadata]`. Vocabulary only;
  no redaction behavior implemented. `docs/redaction-classification.md` added.
- **Reason code contract published** (second-wave, PR A).
  `schemas/reason-code/reason-code.yaml` publishes the structural format a
  reason code must satisfy (lowercase snake*case token,
  `^[a-z][a-z0-9]\*(*[a-z0-9]+)\*$`), from ADR-0003 §12 and the policy/rule
model §13. Contract version `0.1.0`, lifecycle `experimental`. Declares
`depends_on: [contract-metadata]`. Deliberately not a closed enum — the
final reason-code vocabulary remains deferred to the contracts that carry a
`reason_code`field in practice.`docs/reason-code.md` added.
- `docs/operation-aware-schema-readiness.md` — tracks the ADR-0005 PR A–G
  publication order and status, separately from the first-wave
  `docs/migration-plan.md`, which is unaffected and remains complete.
- `basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS` metadata listing
  the three second-wave contracts published by PR A. Additive: does not
  change `PLANNED_CONTRACTS` or `PUBLISHED_CONTRACTS`, which continue to track
  only the original six-contract first wave.

PR A's three contracts are shared foundation building blocks only; PR B's two
contracts are evidence-reference building blocks; PR C's one contract
(above) is the operation-aware `DecisionRequest`. Together they do not
introduce the operation-aware `DecisionResponse`, `PolicyBundle`/
`PolicyRule`/`PolicyCondition`, `EvaluationTrace`/`TraceRuleEvidence`,
`AuditEvidence`/`GatewayAuditEvent`, a final reason-code vocabulary, or
compatibility/test-vector fixtures — each is deferred to a later PR (D
through G) per ADR-0005 and `docs/operation-aware-schema-readiness.md`.

## [0.1.0] - 2026-06-28

First public release of `basis-schemas`. It publishes the six contracts of the
first planned wave — the action vocabulary, the action string, the resource
identifier, the decision request, the decision response, and the audit event —
each at contract version `0.1.0`, lifecycle `experimental`. This is the first
public release, not a claim that the contract set is closed: future contracts may
be added through `basis-architecture` governance.

### Added

- **Audit event contract published** (sixth machine-readable contract; completes
  the first planned wave). `schemas/audit-event/audit-event.yaml` publishes the
  canonical audit-record shape decided in `basis-architecture`
  (`docs/architecture/ecosystem-contract-inventory.md`, §3.10) and implemented by
  `basis-core`'s `AuditEvent` (`audit/events.py`, `audit-event.schema.json`).
  Contract version `0.1.0`, lifecycle `experimental`. It declares `depends_on:
[decision-request, decision-response]`: an audit record holds the evidence of an
  evaluation and correlates to both by `request_id`. Required fields are
  `event_id`, `event_type`, `action`, and `timestamp`; all other fields
  (correlation ids, subject context, resource, decision evidence, per-rule
  `trace`, free-form `detail`, and the audit `schema_version` `1.1`) are optional;
  unknown fields are rejected (`additional_properties: false`). Published exactly
  as basis-core defines it, including two points where the shape differs from a
  generic expectation: the `outcome` vocabulary is past-tense (`allowed` /
  `denied` / `error`), distinct from the decision response's `allow` / `deny` /
  `not_applicable`; and there is no `failure_reason` field — an
  enforcement-boundary failure is recorded as `outcome: error` with context in
  `detail`. No storage, retention, signing, indexing, SIEM-export, trace/OTel,
  cryptographic-signature, compliance-mapping, or AI-metadata fields or behavior
  were introduced; this publishes the record shape, not an audit pipeline.
- `docs/audit-event.md` — short companion explaining the published contract.
- **Decision response contract published** (fifth machine-readable contract).
  `schemas/decision-response/decision-response.yaml` publishes the canonical
  kernel-output shape decided in `basis-architecture`
  (`docs/architecture/ecosystem-contract-inventory.md`, §3.9) and implemented by
  `basis-core`'s `DecisionResponse` (`decisions/models.py`,
  `decision-response.schema.json`). Contract version `0.1.0`, lifecycle
  `experimental`. It declares `depends_on: [decision-request]`: the response is
  the kernel output paired with that input and echoes its `request_id`. Required
  fields are `request_id`, `outcome`, `reason`, `evaluated_by`, and `timestamp`;
  `policy_version` and `failure_reason` are optional; unknown fields are rejected
  (`additional_properties: false`). The decision field is named `outcome` (values
  `allow` / `deny` / `not_applicable`), and `reason` and `evaluated_by` are
  required for every response — matching `basis-core` exactly. `failure_reason`
  (`malformed_request` / `policy_error` / `audit_error` / `internal_error`, or
  null) distinguishes a safe-deny from a normal policy decision. No obligations,
  advice, confidence scores, or gateway-specific fields were introduced.
- `docs/decision-response.md` — short companion explaining the published contract.
- **Decision request contract published** (fourth machine-readable contract).
  `schemas/decision-request/decision-request.yaml` publishes the canonical
  kernel-input shape decided in `basis-architecture`
  (`docs/architecture/ecosystem-contract-inventory.md`, §3.8) and implemented by
  `basis-core`'s `DecisionRequest` (`decisions/models.py`,
  `decision-request.schema.json`). Contract version `0.1.0`, lifecycle
  `experimental`. It declares `depends_on: [action-string, resource-identifier]`:
  the request composes the canonical `action` and `resource_id` formats published
  by those contracts. Required fields are `request_id`, `subject_id`, `action`,
  and `timestamp`; `subject_roles`, `subject_attrs`, `resource_id`, and `context`
  are optional; unknown fields are rejected (`additional_properties: false`). The
  subject is carried as flat fields (`subject_id` / `subject_roles` /
  `subject_attrs`), matching `basis-core` exactly rather than as a nested object.
  The contract expects an already-composed request — a composite action such as
  `read:ahu` and a canonical resource identifier such as `ahu:rooftop-1` — never
  adapter-local fields such as a bare `resource_type`.
- `docs/decision-request.md` — short companion explaining the published contract.
- **Resource identifier contract published** (third machine-readable contract).
  `schemas/resource-identifier/resource-identifier.yaml` publishes the canonical
  typed resource-identifier format `{resource_type}:{local_resource_id}` decided
  in `basis-architecture`
  (`docs/architecture/resource-identifier-reconciliation.md`) and enforced by
  `basis-core`. Contract version `0.1.0`, lifecycle `experimental`. The published
  pattern accepts exactly two non-empty colon-separated segments (a resource type
  prefix and a local resource id) and rejects single, empty, or extra segments.
  Adapters emit the resource type and local resource id as separate fields, the
  gateway composes them into the canonical identifier, and the kernel consumes it
  and derives the resource type from the prefix.
- `docs/resource-identifier.md` — short companion explaining the published
  contract.
- **Action string contract published** (second machine-readable contract).
  `schemas/action-string/action-string.yaml` publishes the composite action-name
  format `{verb}:{domain}[:{object}]` decided in `basis-architecture`
  (`docs/architecture/action-vocabulary.md`) and enforced by `basis-core`.
  Contract version `0.1.0`, lifecycle `experimental`. It declares
  `depends_on: [vocabulary]`: the format is published here, the valid verbs are
  published by the vocabulary contract. The published pattern accepts two or
  three colon-separated lowercase segments (verb, domain, optional object) and
  rejects empty or extra segments.
- `docs/action-string.md` — short companion explaining the published contract.
- **Vocabulary contract published** (first machine-readable contract).
  `schemas/vocabulary/vocabulary.yaml` publishes the five canonical action verbs
  — `read`, `write`, `execute`, `browse`, `subscribe` — as decided in
  `basis-architecture` (`docs/architecture/action-vocabulary.md`). Contract
  version `0.1.0`, lifecycle `experimental`. The `experimental` lifecycle
  reflects that this published-contract format and its consumption path are new,
  not that the architectural vocabulary is unsettled.
- `docs/vocabulary.md` — short companion explaining the published contract.
- `CHANGELOG.md` — this file.
- `PyYAML` added as a dev dependency for parsing published YAML contracts in
  tests.
- `basis_schemas.PUBLISHED_CONTRACTS` metadata distinguishing published
  contracts from still-placeholder ones.

### Changed

- **Release-readiness pass for v0.1.0.** Set the package version to `0.1.0` and
  refreshed the package description; removed stale "Phase 1 / foundation
  skeleton / not yet migrated / once they migrate" wording from
  `docs/architecture.md`, `CONTRIBUTING.md`, and `pyproject.toml` now that all
  six contracts are published; aligned the `decision-request` examples with the
  `decision-response` and `audit-event` examples so a shared `request_id` tells
  one coherent story (matching `basis-core`'s fixtures); and made the
  audit-event `schema_version` terminology consistent across the docs. No
  contract shapes changed.
- Removed `schemas/audit-event/PLACEHOLDER.md`; the directory now holds the real
  contract. No placeholder directories remain — every planned contract is
  published.
- `basis_schemas.PUBLISHED_CONTRACTS` now includes `audit-event` as the sixth
  published contract, making it equal to `PLANNED_CONTRACTS`; `README.md`,
  `schemas/README.md`, and `docs/migration-plan.md` updated to reflect the first
  planned wave as complete. Wording is deliberately "all currently planned
  contracts are published," not that the contract set is closed — future
  contracts may still be added through `basis-architecture` governance.
- Removed `schemas/decision-response/PLACEHOLDER.md`; the directory now holds the
  real contract. The remaining contract directory (`audit-event`) remains a
  placeholder.
- `basis_schemas.PUBLISHED_CONTRACTS` now includes `decision-response` as the
  fifth published contract; `README.md`, `schemas/README.md`, and
  `docs/migration-plan.md` updated to reflect it as published rather than next
  planned, with `audit-event` now the next planned migration.
- Removed `schemas/decision-request/PLACEHOLDER.md`; the directory now holds the
  real contract. The remaining two contract directories (`decision-response`,
  `audit-event`) remain placeholders.
- `basis_schemas.PUBLISHED_CONTRACTS` now includes `decision-request` as the
  fourth published contract; `README.md`, `schemas/README.md`, and
  `docs/migration-plan.md` updated to reflect it as published rather than next
  planned, with `decision-response` now the next planned migration.
- Removed `schemas/resource-identifier/PLACEHOLDER.md`; the directory now holds
  the real contract. The remaining three contract directories
  (`decision-request`, `decision-response`, `audit-event`) remain placeholders.
- `basis_schemas.PUBLISHED_CONTRACTS` now includes `resource-identifier` as the
  third published contract; `README.md`, `schemas/README.md`, and
  `docs/migration-plan.md` updated to reflect it as published rather than next
  planned, with `decision-request` now the next planned migration.
- Removed `schemas/vocabulary/PLACEHOLDER.md`; the directory now holds the real
  contract. All other contract directories remain placeholders.
- `README.md`, `schemas/README.md`, `docs/migration-plan.md`, and
  `docs/contract-governance.md` updated to reflect vocabulary as the first
  published contract and to record the contract-metadata pattern future
  contracts follow. Action string is marked the next planned migration.
- `basis_schemas.is_phase1_foundation()` now returns `False`: the repository has
  moved past the placeholder-only foundation now that the first contract is
  published.
