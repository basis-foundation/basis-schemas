# basis-schemas

`basis-schemas` is the neutral home for the shared contracts of the BASIS
ecosystem. It publishes the machine-readable definitions that
`basis-core`, `basis-gateway`, `basis-adapters`, and `basis-console` must all
agree on, so each contract is defined once and consumed everywhere rather than
re-derived independently in each repository.

BASIS is an open-source core services distribution for identity-aware
authorization in operational technology (OT) environments, governed by the
Basis Foundation. This repository is the single source of truth for the data
shapes those components exchange.

> **Status: v0.2.0 released.** `basis-schemas` publishes **20 contracts**:
> the six first-wave contracts released at v0.1.0 (vocabulary, action
> string, resource identifier, decision request, decision response, audit
> event), plus fourteen operation-aware contracts published across
> `basis-architecture`'s operation-aware schema readiness plan (ADR-0005).
> That second wave — shared metadata, evidence references, the
> operation-aware decision request, a structured policy data model, the
> response and trace contracts, and the kernel/gateway audit contracts —
> is now complete, along with **five canonical compatibility scenarios**
> connecting these contracts under
> [`examples/operation-aware/compatibility/`](examples/operation-aware/compatibility/README.md).
> This is a snapshot of what has shipped, not a claim that the contract set
> is closed — future contracts may still be published through
> `basis-architecture` governance. See
> [`docs/release-notes.md`](docs/release-notes.md) and
> [`CHANGELOG.md`](CHANGELOG.md) for release detail.

---

## What basis-schemas is

`basis-schemas` is a contract repository. It carries the published, versioned,
machine-readable definitions of the shapes multiple BASIS components depend on,
together with the compatibility rules and fixtures that keep those components in
agreement. It sits **below** the implementation repositories in the strict,
downward-only dependency graph of the distribution: components depend on the
schemas, and the schemas depend on nothing else in the distribution.

## What basis-schemas is not

`basis-schemas` holds contracts, not behavior. It is **not**:

- a place to invent new architecture, vocabulary, or semantics;
- a home for policy logic, authorization evaluation, or decision semantics
  (those belong to `basis-core`);
- a home for authentication, token verification, or composition behavior
  (those belong to `basis-gateway`);
- a home for protocol translation or normalization logic (that belongs to
  `basis-adapters`);
- a home for operator workflows or UI (those belong to `basis-console`);
- a home for deployment topology or trust relationships (those belong to
  `basis-deploy`);
- the place where contracts are *decided*. The reasoning that decides what a
  contract should be lives in `basis-architecture`.

## Publish, not invent

`basis-schemas` exists to **publish contracts `basis-architecture` has
decided** — not to create new ones. That covers two related but distinct
cases, both already represented in this repository:

- **Migrating a shape implementation repositories already depend on in
  practice** — the six first-wave contracts (vocabulary through audit-event)
  formalized shapes `basis-core` and its peers were already using.
- **Publishing a shape `basis-architecture` has approved ahead of
  implementation adoption** — the operation-aware second-wave contracts
  (PR A onward, including this repository's `operation-aware-decision-request`)
  are published architecture-first, before any implementation repository
  consumes them, so that `basis-gateway`, `basis-core` v0.2.0, and the rest
  have a stable, reviewable target to build against.

In both cases the ownership model is the same:

```text
Architecture decides.
Schemas publish.
Implementations consume — immediately or incrementally.
```

A contract is reasoned about and decided in `basis-architecture` (in an
architecture document or an ADR) before it becomes a schema. Once decided, its
definition, version, and compatibility fixtures live here. Implementations
import the published contract rather than re-declaring it — whether they adopt
it the same day or incrementally, at their own pace. What does not change
between the two cases: this repository never introduces vocabulary or
semantics of its own; if a shape has not been decided in `basis-architecture`,
it does not belong here yet, regardless of whether an implementation
repository is ready to consume it.

## Current published contract inventory

As of v0.2.0, 20 contracts are published under `schemas/`, all at
`experimental` lifecycle. See [`docs/contract-governance.md`](docs/contract-governance.md)
for what `experimental` means and how contracts advance.

| Group | Contracts | Count |
| --- | --- | --- |
| First wave (v0.1.0) | vocabulary, action-string, resource-identifier, decision-request, decision-response, audit-event | 6 |
| Second wave — shared metadata | contract-metadata, redaction-classification, reason-code | 3 |
| Second wave — evidence references | identity-evidence-reference, adapter-evidence-reference | 2 |
| Second wave — operation-aware request | operation-aware-decision-request | 1 |
| Second wave — policy data model | policy-condition, policy-rule, policy-bundle | 3 |
| Second wave — response and trace | trace-rule-evidence, evaluation-trace, operation-aware-decision-response | 3 |
| Second wave — audit | audit-evidence, gateway-audit-event | 2 |
| **Total** | | **20** |

The first-wave contracts remain published, documented, tested, and
byte-for-byte unchanged since the v0.1.0 release; the second wave is
additive and does not modify them. Five canonical compatibility scenarios
(`allow-basic`, `deny-precedence`, `default-deny`, `not-applicable`,
`invalid-policy-bundle`) connecting request, policy, trace, response, and
audit contracts are published under
[`examples/operation-aware/compatibility/`](examples/operation-aware/compatibility/README.md).

Per-contract detail — dependencies, fields, and rationale — is documented in
[`schemas/README.md`](schemas/README.md) and the per-contract docs linked from
the [Documentation](#documentation) section below. The rest of this section
walks through the order contracts were migrated and published; skip ahead to
[Repository layout](#repository-layout) if you just need the current state.

## Migration history

### First contracts

The following contracts migrated in dependency-and-stability order
(lowest-risk first). All six were published at v0.1.0, completing the first
planned wave. Future contracts may still be added later through
`basis-architecture` governance.

1. **Vocabulary** — _published_ (`experimental`). The five canonical action
   verbs (`read`, `write`, `execute`, `browse`, `subscribe`), published as the
   machine-readable companion to the governance rules in `basis-architecture`.
   See [`schemas/vocabulary/vocabulary.yaml`](schemas/vocabulary/vocabulary.yaml)
   and [`docs/vocabulary.md`](docs/vocabulary.md).
2. **Action string** — _published_ (`experimental`). The composite action-name
   format `{verb}:{domain}[:{object}]` (for example `read:hvac:setpoint`),
   depending on the vocabulary contract for its verb. See
   [`schemas/action-string/action-string.yaml`](schemas/action-string/action-string.yaml)
   and [`docs/action-string.md`](docs/action-string.md).
3. **Resource identifier** — _published_ (`experimental`). The canonical typed
   identifier `{resource_type}:{local_resource_id}` (for example `ahu:rooftop-1`).
   Adapters emit the resource type and local resource id separately; the gateway
   composes them; the kernel consumes the composed identifier. See
   [`schemas/resource-identifier/resource-identifier.yaml`](schemas/resource-identifier/resource-identifier.yaml)
   and [`docs/resource-identifier.md`](docs/resource-identifier.md).
4. **Decision request** — _published_ (`experimental`). The kernel input:
   subject (flat `subject_id` / `subject_roles` / `subject_attrs`), composite
   action, optional canonical resource identifier, and context. Composes the
   action-string and resource-identifier contracts. See
   [`schemas/decision-request/decision-request.yaml`](schemas/decision-request/decision-request.yaml)
   and [`docs/decision-request.md`](docs/decision-request.md).
5. **Decision response** — _published_ (`experimental`). The kernel output:
   `outcome` (allow / deny / not_applicable), reason, evaluating policy
   (`evaluated_by`), policy version, optional failure reason, and timestamp.
   Echoes the request's `request_id`, so it declares `depends_on:
   [decision-request]`. See
   [`schemas/decision-response/decision-response.yaml`](schemas/decision-response/decision-response.yaml)
   and [`docs/decision-response.md`](docs/decision-response.md).
6. **Audit event** — _published_ (`experimental`). The canonical audit record:
   `event_id`, `event_type`, `action`, and `timestamp` required, plus correlation
   ids, subject context, resource, decision evidence (`outcome` as
   `allowed` / `denied` / `error`), an optional per-rule `trace`, free-form
   `detail`, and its own audit `schema_version` (`1.1`) that lets consumers tell
   which fields a record carries. Records the evidence of an evaluation, so it
   declares `depends_on: [decision-request, decision-response]`. See
   [`schemas/audit-event/audit-event.yaml`](schemas/audit-event/audit-event.yaml)
   and [`docs/audit-event.md`](docs/audit-event.md).

More complex contracts (the normalized request shape, the reserved
`basis_gateway.*` namespace rule, and compatibility snapshots) are deferred to a
later phase. See [`docs/migration-plan.md`](docs/migration-plan.md).

### Second wave: operation-aware shared metadata

`basis-architecture`'s operation-aware schema readiness plan (ADR-0005) defines
a further, ordered sequence of contracts beyond the six above, needed for the
richer operation-aware `DecisionRequest`/`DecisionResponse`, policy bundle, and
trace/audit evidence work. Its first PR — **shared metadata and vocabulary** —
is now published:

- **Contract metadata** — _published_ (`experimental`). Formalizes the
  `contract:` block every contract above already carries (identifier, version,
  lifecycle, governance) as its own reusable contract. See
  [`schemas/contract-metadata/contract-metadata.yaml`](schemas/contract-metadata/contract-metadata.yaml)
  and [`docs/contract-metadata.md`](docs/contract-metadata.md).
- **Redaction classification** — _published_ (`experimental`). The five-value
  vocabulary (`safe_to_expose`, `safe_after_redaction`, `reference_only`,
  `never_store`, `never_display`) evidence is sorted into before it may appear
  in a trace, audit, or explanation artifact. See
  [`schemas/redaction-classification/redaction-classification.yaml`](schemas/redaction-classification/redaction-classification.yaml)
  and [`docs/redaction-classification.md`](docs/redaction-classification.md).
- **Reason code** — _published_ (`experimental`). The lowercase snake_case
  string format a reason code must satisfy — deliberately not a closed enum, so
  the final vocabulary stays deferred to the contracts that carry it. See
  [`schemas/reason-code/reason-code.yaml`](schemas/reason-code/reason-code.yaml)
  and [`docs/reason-code.md`](docs/reason-code.md).

These three are additive and separate from the six-contract first wave above;
they do not extend or alter it. See
[`docs/operation-aware-schema-readiness.md`](docs/operation-aware-schema-readiness.md)
for the full second-wave plan and status.

Its second PR — **evidence reference contracts** — is also now published:

- **Identity evidence reference** — _published_ (`experimental`). A safe
  reference to trusted identity evidence — a stable `reference_id`, a
  structural `evidence_digest`, a provider-neutral `identity_source`, optional
  normalization/claim-mapping version provenance, and a
  `redaction_classification` — without embedding raw tokens, cookies,
  credentials, or full claim sets. See
  [`schemas/identity-evidence-reference/identity-evidence-reference.yaml`](schemas/identity-evidence-reference/identity-evidence-reference.yaml)
  and [`docs/identity-evidence-reference.md`](docs/identity-evidence-reference.md).
- **Adapter evidence reference** — _published_ (`experimental`). A safe
  reference to normalized adapter evidence — a stable `reference_id`, a
  structural `evidence_digest`, an opaque `adapter_source`, an optional open
  `protocol` label, optional normalization/mapping version provenance, and a
  `redaction_classification` — without embedding raw protocol payloads or
  device credentials. See
  [`schemas/adapter-evidence-reference/adapter-evidence-reference.yaml`](schemas/adapter-evidence-reference/adapter-evidence-reference.yaml)
  and [`docs/adapter-evidence-reference.md`](docs/adapter-evidence-reference.md).

Both declare `depends_on: [contract-metadata, redaction-classification]` and
are additive and separate from the six-contract first wave and from PR A's
shared metadata contracts; they do not extend or alter either.

Its third PR — the **operation-aware decision request** — is also now
published:

- **Operation-aware decision request** — _published_ (`experimental`). The
  richer, additive vNext request contract a future `basis-core` v0.2.0
  evaluates: `request_id`, `subject_id`, and `action` required; eighteen
  further fields optional, including `subject_roles` / `subject_attrs`,
  `identity_source` / `authority_mode` and an optional
  `identity_evidence_reference`, `resource` / `resource_type`, `location`,
  `device`, `protocol_context`, `operation_intent`, an optional
  `adapter_evidence_reference`, `safety_context` / `environment_context` /
  `risk_context`, `evaluation_time`, and `expected_policy_version`. See
  [`schemas/operation-aware-decision-request/operation-aware-decision-request.yaml`](schemas/operation-aware-decision-request/operation-aware-decision-request.yaml)
  and
  [`docs/operation-aware-decision-request.md`](docs/operation-aware-decision-request.md).
  The existing first-wave `decision-request` is **unchanged**: this is a
  separate, additive contract, not a v2 of it.

Declares `depends_on: [contract-metadata, action-string, resource-identifier,
identity-evidence-reference, adapter-evidence-reference]` and is additive and
separate from the six-contract first wave, PR A's shared metadata contracts,
and PR B's evidence-reference contracts; it does not extend or alter any of
them.

Its fourth PR — **policy bundle and rule contracts** — is also now
published:

- **Policy condition** — _published_ (`experimental`). A deterministic,
  data-only predicate: `condition_id`, a validated dotted `field_path`
  referencing an operation-aware request category, an open (not
  closed-enum) lowercase snake_case `operator`, and a
  smallest-safe-representation `expected_value`. See
  [`schemas/policy-condition/policy-condition.yaml`](schemas/policy-condition/policy-condition.yaml)
  and [`docs/policy-condition.md`](docs/policy-condition.md).
- **Policy rule** — _published_ (`experimental`). A deterministic unit of
  evaluation: a stable `rule_id`, an effect closed to `allow`/`deny`
  (never `not_applicable`, which is a bundle-applicability outcome, not a
  rule effect), explicit match criteria mirroring PR C's request
  categories, optional policy-condition-shaped `conditions`, an optional
  `reason_code` (reusing `reason-code` unchanged), and an optional static
  `explanation`. At least one of `match` or `conditions` is required — no
  unconditional rules. See
  [`schemas/policy-rule/policy-rule.yaml`](schemas/policy-rule/policy-rule.yaml)
  and [`docs/policy-rule.md`](docs/policy-rule.md).
- **Policy bundle** — _published_ (`experimental`). The unit of policy
  identity, versioning, scope, ownership, and rule grouping: `bundle_id`,
  a `bundle_version` distinct from `schema_version`, `policy_owner`
  (provenance only, never an authorization subject), an optional `scope`
  (absent means globally applicable), and a non-empty `rules` array. No
  self-attested `validation_status` field. See
  [`schemas/policy-bundle/policy-bundle.yaml`](schemas/policy-bundle/policy-bundle.yaml)
  and [`docs/policy-bundle.md`](docs/policy-bundle.md).

These three publish a structured policy **data model**, not a policy
language: no Rego, Cedar, CEL, Python, JavaScript, SQL, WASM, or custom DSL
is chosen, and no executable policy expression, embedded code, or `script`
field is published. Declare `depends_on: [contract-metadata]`,
`depends_on: [contract-metadata, policy-condition,
operation-aware-decision-request, reason-code, action-string,
resource-identifier]`, and `depends_on: [contract-metadata, policy-rule]`
respectively, and are additive and separate from the six-contract first
wave and PR A/B/C's contracts; they do not extend or alter any of them.

Its fifth PR — **response and trace contracts** — is also now published:

- **Trace rule evidence** — _published_ (`experimental`). The bounded,
  deterministic explanation record for one policy rule considered during
  evaluation: `rule_id` / `effect` reused unchanged from `policy-rule`, a
  closed `rule_result` (`matched` / `not_matched` / `skipped` / `error`),
  optional bounded `condition_results`, and an optional `reason_code` /
  static `explanation`. Never copies a rule's match criteria, conditions,
  or the raw value compared. See
  [`schemas/trace-rule-evidence/trace-rule-evidence.yaml`](schemas/trace-rule-evidence/trace-rule-evidence.yaml)
  and [`docs/trace-rule-evidence.md`](docs/trace-rule-evidence.md).
- **Evaluation trace** — _published_ (`experimental`). The deterministic,
  bounded explanation of one kernel evaluation: `trace_id` / `request_id`
  identity, a closed, nullable `outcome` matching `decision-response`'s
  outcome vocabulary exactly, a closed `evaluation_status`
  (`completed` / `failed`) and a closed `failure_reason`, and a
  `rule_evidence` array of `trace-rule-evidence`-shaped values. **Required
  invariant, enforced and tested: `outcome` is null if and only if
  `evaluation_status` is `failed`.** See
  [`schemas/evaluation-trace/evaluation-trace.yaml`](schemas/evaluation-trace/evaluation-trace.yaml)
  and [`docs/evaluation-trace.md`](docs/evaluation-trace.md).
- **Operation-aware decision response** — _published_ (`experimental`).
  The additive vNext response contract: `request_id` echoed from PR C's
  request, the identical `outcome` / `evaluation_status` / `failure_reason`
  model as `evaluation-trace`, optional `bundle_id` / `bundle_version`, and
  an optional `trace_id` reference and/or embedded `evaluation_trace`. **The
  existing `schemas/decision-response/decision-response.yaml` is
  unchanged**: this is a separate, additive vNext surface, not a v2. See
  [`schemas/operation-aware-decision-response/operation-aware-decision-response.yaml`](schemas/operation-aware-decision-response/operation-aware-decision-response.yaml)
  and
  [`docs/operation-aware-decision-response.md`](docs/operation-aware-decision-response.md).

These three are additive and separate from the six-contract first wave and
PR A/B/C/D's contracts; they do not extend or alter any of them. Evaluation
trace is explicitly not audit evidence — `AuditEvidence` and
`GatewayAuditEvent` were deferred to PR F.

Its sixth PR — **audit contracts** — is also now published:

- **Audit evidence** — _published_ (`experimental`). The bounded, durable,
  kernel-side evidence representation of one operation-aware authorization
  evaluation: `evidence_id` / `request_id` identity, the identical
  `evaluation_status` / `outcome` / `failure_reason` model reused unchanged
  from `operation-aware-decision-response`, optional `bundle_id` /
  `bundle_version`, a bounded `matched_rule_ids` array, optional
  `identity_evidence_reference` / `adapter_evidence_reference`, and a
  required `recorded_at` timestamp. This is the kernel-side evidence a
  future `basis-core` v0.2.0 produces as an associated evaluation artifact
  alongside the decision response and evaluation trace — not embedded in
  `operation-aware-decision-response`, and not persisted by `basis-core`
  anywhere durable. See
  [`schemas/audit-evidence/audit-evidence.yaml`](schemas/audit-evidence/audit-evidence.yaml)
  and [`docs/audit-evidence.md`](docs/audit-evidence.md).
- **Gateway audit event** — _published_ (`experimental`). The bounded,
  gateway-emitted record of what happened at the enforcement boundary: a
  closed `event_type` (`gateway_authorization`), `request_id`, the
  identical kernel `evaluation_status` / `outcome` / `failure_reason` model
  reused unchanged, a required `audit_evidence_id` reference to the
  associated `audit-evidence` record (referenced, never embedded), and a
  closed `enforcement_action` (`allow` / `deny`) kept structurally
  independent of the kernel `outcome` — fail-closed gateway behavior never
  rewrites the kernel value. `basis-gateway` assembles this record by
  combining kernel evidence with its own enforcement facts; it does not
  produce `AuditEvidence`, and the kernel does not produce
  `GatewayAuditEvent`. See
  [`schemas/gateway-audit-event/gateway-audit-event.yaml`](schemas/gateway-audit-event/gateway-audit-event.yaml)
  and [`docs/gateway-audit-event.md`](docs/gateway-audit-event.md).

Both are additive and separate from the six-contract first wave and PR
A/B/C/D/E's contracts. **The first-wave `schemas/audit-event/audit-event.yaml`
is completely unchanged** — no rename, widening, or vocabulary unification
with either new contract.

Its seventh and final PR — **compatibility examples and test vectors** —
adds no new contract. It publishes canonical, cross-contract compatibility
fixtures under
[`examples/operation-aware/compatibility/`](examples/operation-aware/compatibility/README.md)
connecting PR A through PR F into five complete operation-aware
authorization scenarios — `allow-basic`, `deny-precedence`, `default-deny`,
`not-applicable`, and `invalid-policy-bundle` — validated by
[`tests/test_operation_aware_compatibility_vectors.py`](tests/test_operation_aware_compatibility_vectors.py).
**With PR G published, the operation-aware second wave is complete.** See
[`docs/operation-aware-compatibility-vectors.md`](docs/operation-aware-compatibility-vectors.md).

---

## Repository layout

```text
basis-schemas/
├── README.md                      this file
├── docs/
│   ├── architecture.md            role in the ecosystem and dependency boundaries
│   ├── contract-governance.md     contract states, compatibility, breaking changes
│   ├── migration-plan.md          first-wave migration order and what is deferred
│   ├── operation-aware-schema-readiness.md   second-wave (ADR-0005) plan and status
│   ├── identity-evidence-reference.md        PR B companion doc
│   ├── adapter-evidence-reference.md         PR B companion doc
│   ├── operation-aware-decision-request.md   PR C companion doc
│   ├── policy-condition.md                   PR D companion doc
│   ├── policy-rule.md                        PR D companion doc
│   ├── policy-bundle.md                      PR D companion doc
│   ├── trace-rule-evidence.md                PR E companion doc
│   ├── evaluation-trace.md                   PR E companion doc
│   ├── operation-aware-decision-response.md  PR E companion doc
│   ├── audit-evidence.md                     PR F companion doc
│   ├── gateway-audit-event.md                PR F companion doc
│   └── operation-aware-compatibility-vectors.md  PR G companion doc
├── examples/
│   └── operation-aware/compatibility/  PR G — five canonical compatibility scenarios
├── schemas/
│   ├── README.md                  directory structure and schema lifecycle
│   ├── vocabulary/                published — vocabulary.yaml (experimental)
│   ├── action-string/             published — action-string.yaml (experimental)
│   ├── resource-identifier/       published — resource-identifier.yaml (experimental)
│   ├── decision-request/          published — decision-request.yaml (experimental)
│   ├── decision-response/         published — decision-response.yaml (experimental)
│   ├── audit-event/                published — audit-event.yaml (experimental)
│   ├── contract-metadata/         published — contract-metadata.yaml (experimental)
│   ├── redaction-classification/  published — redaction-classification.yaml (experimental)
│   ├── reason-code/               published — reason-code.yaml (experimental)
│   ├── identity-evidence-reference/  published — identity-evidence-reference.yaml (experimental)
│   ├── adapter-evidence-reference/   published — adapter-evidence-reference.yaml (experimental)
│   ├── operation-aware-decision-request/  published — operation-aware-decision-request.yaml (experimental)
│   ├── policy-condition/          published — policy-condition.yaml (experimental)
│   ├── policy-rule/               published — policy-rule.yaml (experimental)
│   ├── policy-bundle/             published — policy-bundle.yaml (experimental)
│   ├── trace-rule-evidence/       published — trace-rule-evidence.yaml (experimental)
│   ├── evaluation-trace/          published — evaluation-trace.yaml (experimental)
│   ├── operation-aware-decision-response/  published — operation-aware-decision-response.yaml (experimental)
│   ├── audit-evidence/            published — audit-evidence.yaml (experimental)
│   └── gateway-audit-event/       published — gateway-audit-event.yaml (experimental)
├── src/
│   └── basis_schemas/             minimal package: repository metadata
├── tests/                         lightweight metadata and docs checks
└── pyproject.toml                 tooling: pytest, ruff, mypy
```

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — this repository's role in the
  ecosystem and its dependency boundaries.
- [`docs/contract-governance.md`](docs/contract-governance.md) — stable,
  candidate, and experimental contract states; compatibility expectations; and
  the breaking-change process.
- [`docs/migration-plan.md`](docs/migration-plan.md) — the first-wave migration
  order and what is deferred.
- [`docs/operation-aware-schema-readiness.md`](docs/operation-aware-schema-readiness.md)
  — the second-wave (ADR-0005) plan and status.
- [`docs/identity-evidence-reference.md`](docs/identity-evidence-reference.md)
  — the identity evidence reference contract (PR B).
- [`docs/adapter-evidence-reference.md`](docs/adapter-evidence-reference.md)
  — the adapter evidence reference contract (PR B).
- [`docs/operation-aware-decision-request.md`](docs/operation-aware-decision-request.md)
  — the operation-aware decision request contract (PR C).
- [`docs/policy-condition.md`](docs/policy-condition.md) — the policy
  condition contract (PR D).
- [`docs/policy-rule.md`](docs/policy-rule.md) — the policy rule contract
  (PR D).
- [`docs/policy-bundle.md`](docs/policy-bundle.md) — the policy bundle
  contract (PR D).
- [`docs/trace-rule-evidence.md`](docs/trace-rule-evidence.md) — the trace
  rule evidence contract (PR E).
- [`docs/evaluation-trace.md`](docs/evaluation-trace.md) — the evaluation
  trace contract (PR E).
- [`docs/operation-aware-decision-response.md`](docs/operation-aware-decision-response.md)
  — the operation-aware decision response contract (PR E).
- [`docs/audit-evidence.md`](docs/audit-evidence.md) — the kernel-side audit
  evidence contract (PR F).
- [`docs/gateway-audit-event.md`](docs/gateway-audit-event.md) — the
  gateway-emitted enforcement-boundary event contract (PR F).
- [`docs/operation-aware-compatibility-vectors.md`](docs/operation-aware-compatibility-vectors.md)
  — the five canonical compatibility scenarios (PR G).
- [`docs/release-notes.md`](docs/release-notes.md) — the external-facing
  summary of what each release publishes, distilled from `CHANGELOG.md`.
- [`schemas/README.md`](schemas/README.md) — schema directory structure and
  lifecycle.
- [`examples/operation-aware/compatibility/README.md`](examples/operation-aware/compatibility/README.md)
  — the compatibility-vector fixtures themselves, including this
  repository's packaging boundary (see "How to consume contracts" below).

## How to consume contracts

Contracts here are published as YAML files under `schemas/`, not as a
runtime API. `pip install basis-schemas` gives a small metadata package
(`basis_schemas.PUBLISHED_CONTRACTS` and the `OPERATION_AWARE_*` tracking
tuples) — it does **not** put `schemas/`, `docs/`, or `examples/` on disk,
because `pyproject.toml` packages only `src/basis_schemas` in the built
wheel. Consumers that need the contract files themselves — including the
`examples/operation-aware/compatibility/` vectors — read them from a
pinned source release, repository tag, submodule, or vendored copy of this
repository rather than from the installed package. See
[`examples/operation-aware/compatibility/README.md`](examples/operation-aware/compatibility/README.md#17-packaging-and-downstream-consumption),
section 17, for the full packaging rationale.

## Development

This repository uses a lightweight Python toolchain. See
[`docs/architecture.md`](docs/architecture.md) for the rationale.

```bash
python -m pytest        # run tests
ruff check .            # lint
ruff format --check .   # formatting check
mypy src                # type-check the metadata package
```

Every pull request and every push to `main` runs these same quality gates
automatically via GitHub Actions
([`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

## Governance and license

Contracts published here are decided in `basis-architecture` and governed under
the Basis Foundation process and the compatibility philosophy referenced in
[`docs/contract-governance.md`](docs/contract-governance.md). Licensed under the
Apache License 2.0; see [`LICENSE`](LICENSE).
