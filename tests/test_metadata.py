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
    # The first four contracts — vocabulary, action-string, resource-identifier,
    # and decision-request — are published; the rest remain planned. Published
    # contracts must be a prefix of the planned order (migration proceeds in
    # order, lowest-risk first).
    assert basis_schemas.PUBLISHED_CONTRACTS == (
        "vocabulary",
        "action-string",
        "resource-identifier",
        "decision-request",
    )
    published = basis_schemas.PUBLISHED_CONTRACTS
    planned_prefix = basis_schemas.PLANNED_CONTRACTS[: len(published)]
    assert published == planned_prefix


def test_repository_is_past_phase1_foundation() -> None:
    # The placeholder-only foundation phase is over now that the vocabulary
    # contract is published. This flips back only if all contracts are unpublished.
    assert basis_schemas.is_phase1_foundation() is False
