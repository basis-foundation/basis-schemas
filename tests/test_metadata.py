"""Lightweight checks on repository metadata.

These tests validate the package metadata and its agreement with the planned
migration order. They do not validate any contract, because no contract has been
migrated yet.
"""

from __future__ import annotations

import basis_schemas


def test_project_name() -> None:
    assert basis_schemas.PROJECT_NAME == "basis-schemas"


def test_version_is_a_string() -> None:
    assert isinstance(basis_schemas.__version__, str)
    assert basis_schemas.__version__


def test_planned_contracts_match_migration_order() -> None:
    # The six first-wave contracts, in the order recorded in
    # docs/migration-plan.md and the basis-architecture charter.
    assert basis_schemas.PLANNED_CONTRACTS == (
        "vocabulary",
        "action-string",
        "resource-identifier",
        "decision-request",
        "decision-response",
        "audit-event",
    )


def test_contract_states_are_ordered_by_commitment() -> None:
    assert basis_schemas.CONTRACT_STATES == (
        "experimental",
        "candidate",
        "stable",
    )


def test_published_contracts_is_a_subset_in_planned_order() -> None:
    # All six planned contracts — vocabulary, action-string, resource-identifier,
    # decision-request, decision-response, and audit-event — are now published.
    # Published contracts must be a prefix of the planned order (migration
    # proceeds in order, lowest-risk first); with the wave complete, that prefix
    # is the whole planned list.
    assert basis_schemas.PUBLISHED_CONTRACTS == (
        "vocabulary",
        "action-string",
        "resource-identifier",
        "decision-request",
        "decision-response",
        "audit-event",
    )
    published = basis_schemas.PUBLISHED_CONTRACTS
    planned_prefix = basis_schemas.PLANNED_CONTRACTS[: len(published)]
    assert published == planned_prefix


def test_all_planned_contracts_are_published() -> None:
    # Every currently planned contract is published. This is not a claim that the
    # contract set is closed forever — future contracts may be added through
    # basis-architecture governance and would extend PLANNED_CONTRACTS.
    assert set(basis_schemas.PUBLISHED_CONTRACTS) == set(basis_schemas.PLANNED_CONTRACTS)


def test_repository_is_past_phase1_foundation() -> None:
    # The placeholder-only foundation phase is over now that the vocabulary
    # contract is published. This flips back only if all contracts are unpublished.
    assert basis_schemas.is_phase1_foundation() is False


def test_operation_aware_shared_metadata_contracts_match_pr_a() -> None:
    # The three shared contracts published by PR A of the operation-aware
    # schema readiness plan (ADR-0005), in publication order.
    assert basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS == (
        "contract-metadata",
        "redaction-classification",
        "reason-code",
    )


def test_operation_aware_shared_metadata_contracts_do_not_extend_first_wave() -> None:
    # The second wave is additive and separate: it must not appear in, or
    # change the length of, the first-wave six-contract tuples.
    assert len(basis_schemas.PLANNED_CONTRACTS) == 6
    assert len(basis_schemas.PUBLISHED_CONTRACTS) == 6
    for contract in basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS:
        assert contract not in basis_schemas.PLANNED_CONTRACTS
        assert contract not in basis_schemas.PUBLISHED_CONTRACTS
