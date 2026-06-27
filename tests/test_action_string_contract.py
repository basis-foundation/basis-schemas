"""Focused checks on the published action-string contract.

These tests validate ``schemas/action-string/action-string.yaml``: its metadata,
its declared dependency on the vocabulary contract, and that the published
validation pattern accepts well-formed action strings and rejects malformed ones.
The format is decided in ``basis-architecture`` and enforced by ``basis-core``;
these tests confirm the publication reproduces that shape faithfully.

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
ACTION_DIR = REPO_ROOT / "schemas" / "action-string"
ACTION_FILE = ACTION_DIR / "action-string.yaml"

# Examples mandated by the phase requirements. The contract's own examples are
# additionally cross-checked in test_declared_examples_match_pattern.
REQUIRED_VALID = ("read:ahu", "write:setpoint", "execute:command", "read:hvac:setpoint")
REQUIRED_INVALID = ("read", "read:", ":ahu", "read::setpoint", "read:ahu:setpoint:extra")


def _load() -> dict:
    with ACTION_FILE.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict), "action-string.yaml must parse to a mapping"
    return data


def _pattern() -> re.Pattern[str]:
    return re.compile(_load()["action_string"]["pattern"])


def test_action_string_file_exists() -> None:
    assert ACTION_FILE.is_file(), "schemas/action-string/action-string.yaml must exist"


def test_action_string_yaml_parses() -> None:
    assert _load()


def test_contract_metadata_matches_expected_values() -> None:
    contract = _load()["contract"]
    assert contract["name"] == "action-string"
    assert contract["title"] == "BASIS Action String"
    assert isinstance(contract.get("version"), str) and contract["version"]
    assert contract["governed_by"] == "basis-architecture"
    assert contract["published_by"] == "basis-schemas"


def test_lifecycle_is_experimental() -> None:
    assert _load()["contract"]["lifecycle"] == "experimental"


def test_vocabulary_dependency_is_declared() -> None:
    depends_on = _load()["contract"].get("depends_on")
    assert isinstance(depends_on, list), "contract.depends_on must be a list"
    assert "vocabulary" in depends_on, "action-string must declare a dependency on vocabulary"


def test_valid_examples_accepted_by_pattern() -> None:
    pattern = _pattern()
    for action in REQUIRED_VALID:
        assert pattern.match(action), f"valid action string rejected: {action!r}"


def test_invalid_examples_rejected_by_pattern() -> None:
    pattern = _pattern()
    for action in REQUIRED_INVALID:
        assert not pattern.match(action), f"invalid action string accepted: {action!r}"


def test_declared_examples_match_pattern() -> None:
    # The examples published inside the contract must be self-consistent with the
    # contract's own pattern.
    data = _load()["action_string"]
    pattern = re.compile(data["pattern"])
    for action in data["examples"]["valid"]:
        assert pattern.match(action), f"declared-valid example rejected: {action!r}"
    for action in data["examples"]["invalid"]:
        assert not pattern.match(action), f"declared-invalid example accepted: {action!r}"


def test_structure_is_two_or_three_segments() -> None:
    data = _load()["action_string"]
    assert data["min_segments"] == 2
    assert data["max_segments"] == 3
    # A three-segment string is accepted; a four-segment string is not.
    pattern = re.compile(data["pattern"])
    assert pattern.match("read:hvac:setpoint")
    assert not pattern.match("read:hvac:setpoint:extra")


def test_placeholder_removed_from_action_string_dir() -> None:
    assert not (ACTION_DIR / "PLACEHOLDER.md").exists(), (
        "schemas/action-string/PLACEHOLDER.md should be removed now that the contract is published"
    )


def test_remaining_future_contracts_still_have_placeholders() -> None:
    # action-string is published; every still-deferred contract must remain a
    # placeholder holding only PLACEHOLDER.md.
    assert "action-string" in basis_schemas.PUBLISHED_CONTRACTS
    deferred = [
        c for c in basis_schemas.PLANNED_CONTRACTS if c not in basis_schemas.PUBLISHED_CONTRACTS
    ]
    for contract in deferred:
        directory = REPO_ROOT / "schemas" / contract
        entries = sorted(p.name for p in directory.iterdir() if p.is_file())
        assert entries == ["PLACEHOLDER.md"], (
            f"{contract} should remain a placeholder, found: {entries}"
        )
