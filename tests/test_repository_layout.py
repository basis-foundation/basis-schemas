"""Checks that the repository skeleton is present and still a foundation.

These tests assert that the required documentation exists and that each planned
contract has a placeholder directory containing only a placeholder — i.e. that no
real contract has been migrated. They are deliberately structural; they assert
the *shape of the repository*, not the *shape of any contract*.
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
        "schemas/README.md",
    ]
    missing = [path for path in required if not (REPO_ROOT / path).is_file()]
    assert not missing, f"missing required files: {missing}"


def test_each_planned_contract_has_a_placeholder_directory() -> None:
    for contract in basis_schemas.PLANNED_CONTRACTS:
        directory = REPO_ROOT / "schemas" / contract
        assert directory.is_dir(), f"missing schema directory: {contract}"
        assert (directory / "PLACEHOLDER.md").is_file(), f"missing placeholder in: {contract}"


def test_no_real_contract_has_been_migrated() -> None:
    # Phase 1 invariant: schema directories contain placeholders only. A real
    # contract would arrive as a schema definition file (e.g. .json / .yaml).
    # Finding one means this test — and the phase guard — must be updated.
    contract_files = []
    for contract in basis_schemas.PLANNED_CONTRACTS:
        directory = REPO_ROOT / "schemas" / contract
        for entry in directory.iterdir():
            if entry.is_file() and entry.name != "PLACEHOLDER.md":
                contract_files.append(str(entry.relative_to(REPO_ROOT)))
    assert not contract_files, f"unexpected non-placeholder files during Phase 1: {contract_files}"
