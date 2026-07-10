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

> **Status: all six planned contracts published.** The action **vocabulary** —
> the five canonical verbs — is published under
> [`schemas/vocabulary/vocabulary.yaml`](schemas/vocabulary/vocabulary.yaml),
> the **action string** format `{verb}:{domain}[:{object}]` under
> [`schemas/action-string/action-string.yaml`](schemas/action-string/action-string.yaml),
> the **resource identifier** format `{resource_type}:{local_resource_id}`
> under
> [`schemas/resource-identifier/resource-identifier.yaml`](schemas/resource-identifier/resource-identifier.yaml),
> the **decision request** — the kernel input shape — under
> [`schemas/decision-request/decision-request.yaml`](schemas/decision-request/decision-request.yaml),
> the **decision response** — the kernel output shape — under
> [`schemas/decision-response/decision-response.yaml`](schemas/decision-response/decision-response.yaml),
> and the **audit event** — the canonical audit record shape — under
> [`schemas/audit-event/audit-event.yaml`](schemas/audit-event/audit-event.yaml).
> This completes the first planned migration wave; it is not a claim that the
> contract set is closed forever — future contracts may still be added through
> `basis-architecture` governance. See [`docs/migration-plan.md`](docs/migration-plan.md).
> A second wave has since begun: **contract metadata**, **redaction
> classification**, and **reason code** — the shared foundation contracts from
> `basis-architecture`'s operation-aware schema readiness plan (ADR-0005) — are
> now published, along with that wave's **identity evidence reference** and
> **adapter evidence reference** contracts (PR B), the **operation-aware
> decision request** (PR C) — an additive vNext request contract — and the
> **policy condition**, **policy rule**, and **policy bundle** contracts
> (PR D) — a structured policy *data model*, not a policy language — are now
> published, along with that wave's **trace rule evidence**, **evaluation
> trace**, and **operation-aware decision response** contracts (PR E), the
> machine-readable response and trace shapes a future `basis-core` v0.2.0
> will produce after deterministic operation-aware policy evaluation, and
> now that wave's **audit evidence** and **gateway audit event** contracts
> (PR F) — the bounded, durable kernel-side evidence shape and the
> gateway-emitted enforcement-boundary event shape a future `basis-core`
> v0.2.0 and `basis-gateway` will produce and combine; the first-wave
> **decision request**, **decision response**, and **audit event** above
> remain published and unchanged. See
> [`docs/operation-aware-schema-readiness.md`](docs/operation-aware-schema-readiness.md).

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

## First contracts

The following contracts migrate in dependency-and-stability order (lowest-risk
first). All six are now **published** — this completes the first planned wave.
Future contracts may still be added later through `basis-architecture` governance.

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

## Second wave: operation-aware shared metadata

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
│   └── policy-bundle.md                      PR D companion doc
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
│   └── policy-bundle/             published — policy-bundle.yaml (experimental)
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
- [`schemas/README.md`](schemas/README.md) — schema directory structure and
  lifecycle.

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
