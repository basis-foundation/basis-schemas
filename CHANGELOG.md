# Changelog

All notable changes to `basis-schemas` are recorded here. This repository
publishes shared contracts decided in `basis-architecture`; entries describe what
was published or changed, not implementation behavior.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/);
contract versions and lifecycle states follow
[`docs/contract-governance.md`](docs/contract-governance.md).

## [Unreleased]

### Added

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

- Removed `schemas/vocabulary/PLACEHOLDER.md`; the directory now holds the real
  contract. All other contract directories remain placeholders.
- `README.md`, `schemas/README.md`, `docs/migration-plan.md`, and
  `docs/contract-governance.md` updated to reflect vocabulary as the first
  published contract and to record the contract-metadata pattern future
  contracts follow. Action string is marked the next planned migration.
- `basis_schemas.is_phase1_foundation()` now returns `False`: the repository has
  moved past the placeholder-only foundation now that the first contract is
  published.
