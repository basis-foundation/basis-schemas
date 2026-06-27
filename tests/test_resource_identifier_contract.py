"""Focused checks on the published resource-identifier contract.

These tests validate ``schemas/resource-identifier/resource-identifier.yaml``:
its metadata and that the published validation pattern accepts well-formed
canonical resource identifiers and rejects malformed ones. The format is decided
in ``basis-architecture`` and enforced by ``basis-core``; these tests confirm the
publication reproduces that shape faithfully.

This is a contract publication, not a parser: the only behavior exercised here is
applying the contract's own published regex to example strings.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import basis_schemas

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
RESOURCE_DIR = REPO_ROOT / "schemas" / "resource-identifier"
RESOURCE_FILE = RESOURCE_DIR / "resource-identifier.yaml"

# Examples mandated by the phase requirements. The contract's own examples are
# additionally cross-checked in test_declared_examples_match_pattern.
REQUIRED_VALID = ("ahu:rooftop-1", "setpoint:zone-3", "controller:boiler-1")
REQUIRED_INVALID = ("rooftop-1", "ahu:", ":rooftop-1", "ahu::rooftop-1", "ahu:rooftop-1:extra")


def _load() -> dict:
    with RESOURCE_FILE.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict), "resource-identifier.yaml must parse to a mapping"
    return data


def _pattern() -> re.Pattern[str]:
    return re.compile(_load()["resource_identifier"]["pattern"])


def test_resource_identifier_file_exists() -> None:
    assert RESOURCE_FILE.is_file(), (
        "schemas/resource-identifier/resource-identifier.yaml must exist"
    )


def test_resource_identifier_yaml_parses() -> None:
    assert _load()


def test_contract_metadata_matches_expected_values() -> None:
    contract = _load()["contract"]
    assert contract["name"] == "resource-identifier"
    assert contract["title"] == "BASIS Resource Identifier"
    assert contract["version"] == "0.1.0"
    assert contract["governed_by"] == "basis-architecture"
    assert contract["published_by"] == "basis-schemas"


def test_lifecycle_is_experimental() -> None:
    assert _load()["contract"]["lifecycle"] == "experimental"


def test_valid_examples_accepted_by_pattern() -> None:
    pattern = _pattern()
    for resource_id in REQUIRED_VALID:
        assert pattern.match(resource_id), f"valid resource identifier rejected: {resource_id!r}"


def test_invalid_examples_rejected_by_pattern() -> None:
    pattern = _pattern()
    for resource_id in REQUIRED_INVALID:
        assert not pattern.match(resource_id), (
            f"invalid resource identifier accepted: {resource_id!r}"
        )


def test_declared_examples_match_pattern() -> None:
    # The examples published inside the contract must be self-consistent with the
    # contract's own pattern.
    data = _load()["resource_identifier"]
    pattern = re.compile(data["pattern"])
    for resource_id in data["examples"]["valid"]:
        assert pattern.match(resource_id), f"declared-valid example rejected: {resource_id!r}"
    for resource_id in data["examples"]["invalid"]:
        assert not pattern.match(resource_id), f"declared-invalid example accepted: {resource_id!r}"


def test_structure_is_exactly_two_segments() -> None:
    data = _load()["resource_identifier"]
    assert data["segments_exact"] == 2
    # A two-segment identifier is accepted; a three-segment one is not.
    pattern = re.compile(data["pattern"])
    assert pattern.match("ahu:rooftop-1")
    assert not pattern.match("ahu:rooftop-1:extra")


def test_placeholder_removed_from_resource_identifier_dir() -> None:
    assert not (RESOURCE_DIR / "PLACEHOLDER.md").exists(), (
        "schemas/resource-identifier/PLACEHOLDER.md should be removed now that the "
        "contract is published"
    )


def test_remaining_future_contracts_still_have_placeholders() -> None:
    # resource-identifier is published; every still-deferred contract must remain
    # a placeholder holding only PLACEHOLDER.md.
    assert "resource-identifier" in basis_schemas.PUBLISHED_CONTRACTS
    deferred = [
        c for c in basis_schemas.PLANNED_CONTRACTS if c not in basis_schemas.PUBLISHED_CONTRACTS
    ]
    for contract in deferred:
        directory = REPO_ROOT / "schemas" / contract
        entries = sorted(p.name for p in directory.iterdir() if p.is_file())
        assert entries == ["PLACEHOLDER.md"], (
            f"{contract} should remain a placeholder, found: {entries}"
        )
