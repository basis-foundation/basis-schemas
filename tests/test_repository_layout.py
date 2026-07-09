"""Checks that the repository skeleton is present and consistent.

These tests assert that the required documentation exists, that published
contracts have a real schema definition (no leftover placeholder), and that
still-deferred contracts remain placeholders. They are deliberately structural;
they assert the *shape of the repository*, not the *shape of any contract*. The
contract's own shape is checked in ``test_vocabulary_contract.py``.
"""

from __future__ import annotations

from pathlib import Path

import basis_schemas

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_required_docs_exist() -> None:
    required = [
        "README.md",
        "LICENSE",
        "docs/architecture.md",
        "docs/contract-governance.md",
        "docs/migration-plan.md",
        "docs/operation-aware-schema-readiness.md",
        "docs/contract-metadata.md",
        "docs/redaction-classification.md",
        "docs/reason-code.md",
        "docs/identity-evidence-reference.md",
        "docs/adapter-evidence-reference.md",
        "docs/operation-aware-decision-request.md",
        "schemas/README.md",
    ]
    missing = [path for path in required if not (REPO_ROOT / path).is_file()]
    assert not missing, f"missing required files: {missing}"


def test_operation_aware_shared_metadata_contracts_have_directories() -> None:
    # The second-wave shared contracts (PR A of the operation-aware schema
    # readiness plan) each have a real schema definition, mirroring the
    # first-wave invariant above but tracked via a separate metadata tuple.
    for contract in basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS:
        directory = REPO_ROOT / "schemas" / contract
        assert directory.is_dir(), f"missing schema directory: {contract}"
        schema_file = directory / f"{contract}.yaml"
        assert schema_file.is_file(), f"missing schema file: {schema_file}"


def test_operation_aware_shared_metadata_contracts_are_disjoint_from_first_wave() -> None:
    # The second wave must never be conflated with the first-wave six-contract
    # migration: no name should appear in both tuples.
    first_wave = set(basis_schemas.PLANNED_CONTRACTS)
    second_wave = set(basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS)
    assert not (first_wave & second_wave), (
        f"contract names appear in both waves: {first_wave & second_wave}"
    )


def test_operation_aware_evidence_reference_contracts_have_directories() -> None:
    # PR B's evidence-reference contracts each have a real schema definition,
    # mirroring the first-wave and PR A invariants above.
    for contract in basis_schemas.OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS:
        directory = REPO_ROOT / "schemas" / contract
        assert directory.is_dir(), f"missing schema directory: {contract}"
        schema_file = directory / f"{contract}.yaml"
        assert schema_file.is_file(), f"missing schema file: {schema_file}"


def test_operation_aware_evidence_reference_contracts_are_disjoint_from_first_wave() -> None:
    # PR B must never be conflated with the first-wave six-contract migration:
    # no name should appear in both tuples.
    first_wave = set(basis_schemas.PLANNED_CONTRACTS)
    evidence_reference_wave = set(basis_schemas.OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS)
    assert not (first_wave & evidence_reference_wave), (
        f"contract names appear in both waves: {first_wave & evidence_reference_wave}"
    )


def test_operation_aware_request_contracts_have_directories() -> None:
    # PR C's operation-aware request contract has a real schema definition,
    # mirroring the first-wave, PR A, and PR B invariants above.
    for contract in basis_schemas.OPERATION_AWARE_REQUEST_CONTRACTS:
        directory = REPO_ROOT / "schemas" / contract
        assert directory.is_dir(), f"missing schema directory: {contract}"
        schema_file = directory / f"{contract}.yaml"
        assert schema_file.is_file(), f"missing schema file: {schema_file}"


def test_operation_aware_request_contracts_are_disjoint_from_first_wave() -> None:
    # PR C must never be conflated with the first-wave six-contract migration:
    # no name should appear in both tuples.
    first_wave = set(basis_schemas.PLANNED_CONTRACTS)
    request_wave = set(basis_schemas.OPERATION_AWARE_REQUEST_CONTRACTS)
    assert not (first_wave & request_wave), (
        f"contract names appear in both waves: {first_wave & request_wave}"
    )


def test_every_planned_contract_has_a_directory() -> None:
    for contract in basis_schemas.PLANNED_CONTRACTS:
        directory = REPO_ROOT / "schemas" / contract
        assert directory.is_dir(), f"missing schema directory: {contract}"


def test_deferred_contracts_remain_placeholders() -> None:
    # Contracts not yet published must still hold a PLACEHOLDER.md and nothing
    # else. A stray schema file here means a contract was migrated without
    # updating PUBLISHED_CONTRACTS.
    deferred = [
        c for c in basis_schemas.PLANNED_CONTRACTS if c not in basis_schemas.PUBLISHED_CONTRACTS
    ]
    for contract in deferred:
        directory = REPO_ROOT / "schemas" / contract
        assert (directory / "PLACEHOLDER.md").is_file(), f"missing placeholder in: {contract}"
        unexpected = [
            entry.name
            for entry in directory.iterdir()
            if entry.is_file() and entry.name != "PLACEHOLDER.md"
        ]
        assert not unexpected, f"unexpected files in deferred contract {contract}: {unexpected}"


def test_published_contracts_have_no_placeholder() -> None:
    # A published contract directory holds the real definition, not a leftover
    # placeholder.
    for contract in basis_schemas.PUBLISHED_CONTRACTS:
        directory = REPO_ROOT / "schemas" / contract
        assert not (directory / "PLACEHOLDER.md").exists(), (
            f"published contract {contract} still has a PLACEHOLDER.md"
        )
        real_files = [e.name for e in directory.iterdir() if e.is_file()]
        assert real_files, f"published contract {contract} has no schema file"
