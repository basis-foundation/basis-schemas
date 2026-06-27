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

> **Status: first contract published.** The action **vocabulary** — the five
> canonical verbs — is now published under
> [`schemas/vocabulary/vocabulary.yaml`](schemas/vocabulary/vocabulary.yaml) as
> the first machine-readable contract in this repository. The remaining planned
> contracts are still placeholder directories. See
> [`docs/migration-plan.md`](docs/migration-plan.md).

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

`basis-schemas` exists to **formalize contracts that already exist** across the
ecosystem — not to create new ones. Every contract published here is one that
the implementation repositories already depend on in practice and that
`basis-architecture` has already decided. The ownership model is:

```text
Architecture proposes.
Schemas publish.
Implementations consume.
```

A contract is reasoned about and decided in `basis-architecture` (in an
architecture document or an ADR) before it becomes a schema. Once decided, its
definition, version, and compatibility fixtures live here. Implementations
import the published contract rather than re-declaring it. This repository never
introduces vocabulary or semantics of its own; if a shape has not been decided
in `basis-architecture`, it does not belong here yet.

## First contracts

The following contracts migrate in dependency-and-stability order (lowest-risk
first). The vocabulary contract is **published**; the rest are planned and remain
placeholders.

1. **Vocabulary** — _published_ (`experimental`). The five canonical action
   verbs (`read`, `write`, `execute`, `browse`, `subscribe`), published as the
   machine-readable companion to the governance rules in `basis-architecture`.
   See [`schemas/vocabulary/vocabulary.yaml`](schemas/vocabulary/vocabulary.yaml)
   and [`docs/vocabulary.md`](docs/vocabulary.md).
2. **Action string** — _next planned_. The composite action-name format
   `{verb}:{domain}[:{object}]` (for example `read:hvac:setpoint`).
3. **Resource identifier** — the canonical typed identifier `{type}:{qualifier}`
   (for example `ahu:rooftop-1`).
4. **Decision request** — the kernel input: subject, composite action, optional
   canonical resource identifier, and context.
5. **Decision response** — the kernel output: outcome, reason, evaluating
   policy, policy version, optional failure reason, and timestamp.
6. **Audit event** — the canonical audit structure, including its schema version
   and the action-vocabulary version field that lets consumers interpret
   historical records across vocabulary evolution.

More complex contracts (the normalized request shape, the reserved
`basis_gateway.*` namespace rule, and compatibility snapshots) are deferred to a
later phase. See [`docs/migration-plan.md`](docs/migration-plan.md).

---

## Repository layout

```text
basis-schemas/
├── README.md                      this file
├── docs/
│   ├── architecture.md            role in the ecosystem and dependency boundaries
│   ├── contract-governance.md     contract states, compatibility, breaking changes
│   └── migration-plan.md          migration order and what is deferred
├── schemas/
│   ├── README.md                  directory structure and schema lifecycle
│   ├── vocabulary/                published — vocabulary.yaml (experimental)
│   ├── action-string/             placeholder — not yet migrated
│   ├── resource-identifier/       placeholder — not yet migrated
│   ├── decision-request/          placeholder — not yet migrated
│   ├── decision-response/         placeholder — not yet migrated
│   └── audit-event/               placeholder — not yet migrated
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
- [`docs/migration-plan.md`](docs/migration-plan.md) — the order in which
  contracts migrate and which are deferred.
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

## Governance and license

Contracts published here are decided in `basis-architecture` and governed under
the Basis Foundation process and the compatibility philosophy referenced in
[`docs/contract-governance.md`](docs/contract-governance.md). Licensed under the
Apache License 2.0; see [`LICENSE`](LICENSE).
