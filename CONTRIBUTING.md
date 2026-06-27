# Contributing to basis-schemas

`basis-schemas` **publishes** contracts; it does not invent them. The most
important rule for contributing follows directly from that: a contract is decided
in `basis-architecture` first, then published here. This repository is not where
shared shapes, vocabulary, or semantics are designed.

## Before you propose a change

- **New or changed contract?** It must be decided in `basis-architecture` (an
  architecture document or an ADR) before a corresponding schema is added or
  changed here. A pull request that introduces a contract shape not yet decided
  in `basis-architecture` will be declined on principle, not on detail.
- **Compatibility-affecting change?** Read
  [`docs/contract-governance.md`](docs/contract-governance.md) first. Breaking
  changes to stable contracts follow the full breaking-change process, including
  an ADR in `basis-architecture`, a major version increment, and a deprecation
  period.
- **Boundary check.** This repository holds shapes, never behavior. Policy logic,
  authentication, protocol translation, operator workflows, and deployment
  topology belong to their owning repositories. See
  [`docs/architecture.md`](docs/architecture.md).

## Phase 1 scope

The repository is currently a foundation skeleton: documentation, tooling, and
placeholder schema directories only. Contributions in this phase should improve
the documentation, tooling, or structure — not migrate contracts. Contract
migration follows the order in [`docs/migration-plan.md`](docs/migration-plan.md)
and begins only once each contract is decided ready in `basis-architecture`.

## Quality gates

All changes must pass the following locally before review:

```bash
python -m pytest
ruff check .
ruff format --check .
mypy src
```

Install the development dependencies with `pip install -e ".[dev]"`.

## License

By contributing, you agree that your contributions are licensed under the
Apache License 2.0, the license of this repository.
