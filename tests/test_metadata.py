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


def test_repository_is_still_phase1_foundation() -> None:
    # Phase 1 ships placeholders only. This guard flips when the first contract
    # is migrated and the metadata is updated accordingly.
    assert basis_schemas.is_phase1_foundation() is True
