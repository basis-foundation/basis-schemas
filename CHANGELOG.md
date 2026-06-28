# Changelog

All notable changes to `basis-schemas` are recorded here. This repository
publishes shared contracts decided in `basis-architecture`; entries describe what
was published or changed, not implementation behavior.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/);
contract versions and lifecycle states follow
[`docs/contract-governance.md`](docs/contract-governance.md).

## [Unreleased]

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
