"""Focused checks on the published reason-code contract.

These tests validate ``schemas/reason-code/reason-code.yaml``: its metadata,
its declared dependency on contract-metadata, and that the published pattern
accepts well-formed reason codes and rejects malformed ones — while remaining
extensible: a structurally valid code that is not one of the illustrative
examples must still be accepted, because this contract is a format, not a
closed enum.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import basis_schemas

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
REASON_CODE_DIR = REPO_ROOT / "schemas" / "reason-code"
REASON_CODE_FILE = REASON_CODE_DIR / "reason-code.yaml"

REQUIRED_VALID = (
    "allow_rule_matched",
    "deny_rule_matched",
    "missing_required_context",
    "unknown_resource_type",
)
REQUIRED_INVALID = (
    "",
    "ALLOW_RULE_MATCHED",
    "1_invalid_start",
    "read:ahu",
    "deny-rule-matched",
    "_leading_underscore",
    "trailing_underscore_",
    "double__underscore",
)


def _load() -> dict:
    with REASON_CODE_FILE.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict), "reason-code.yaml must parse to a mapping"
    return data


def _pattern() -> re.Pattern[str]:
    return re.compile(_load()["reason_code"]["pattern"])


def test_reason_code_file_exists() -> None:
    assert REASON_CODE_FILE.is_file(), "schemas/reason-code/reason-code.yaml must exist"


def test_reason_code_yaml_parses() -> None:
    assert _load()


def test_contract_metadata_matches_expected_values() -> None:
    contract = _load()["contract"]
    assert contract["name"] == "reason-code"
    assert contract["title"] == "BASIS Reason Code"
    assert isinstance(contract.get("version"), str) and contract["version"]
    assert contract["governed_by"] == "basis-architecture"
    assert contract["published_by"] == "basis-schemas"


def test_lifecycle_is_experimental() -> None:
    assert _load()["contract"]["lifecycle"] == "experimental"


def test_contract_metadata_dependency_is_declared() -> None:
    depends_on = _load()["contract"].get("depends_on")
    assert isinstance(depends_on, list), "contract.depends_on must be a list"
    assert "contract-metadata" in depends_on


def test_valid_examples_accepted_by_pattern() -> None:
    pattern = _pattern()
    for code in REQUIRED_VALID:
        assert pattern.match(code), f"valid reason code rejected: {code!r}"


def test_invalid_examples_rejected_by_pattern() -> None:
    pattern = _pattern()
    for code in REQUIRED_INVALID:
        assert not pattern.match(code), f"invalid reason code accepted: {code!r}"


def test_declared_examples_match_pattern() -> None:
    data = _load()["reason_code"]
    pattern = re.compile(data["pattern"])
    for code in data["examples"]["valid"]:
        assert pattern.match(code), f"declared-valid example rejected: {code!r}"
    for code in data["examples"]["invalid"]:
        assert not pattern.match(code), f"declared-invalid example accepted: {code!r}"


def test_pattern_does_not_enumerate_a_closed_vocabulary() -> None:
    # Extensibility requirement: a structurally valid but unrecognized future
    # code must be accepted, not rejected merely for being absent from the
    # illustrative list.
    pattern = _pattern()
    assert pattern.match("future_unrecognized_reason_code")
    illustrative = set(_load()["reason_code"]["illustrative_examples"])
    assert "future_unrecognized_reason_code" not in illustrative


def test_illustrative_examples_are_not_labeled_final() -> None:
    contract = _load()["contract"]
    description = contract["description"].lower()
    assert (
        "not a closed enum" in description
        or "not the final" in description
        or ("final vocabulary" in description)
    )


def test_illustrative_examples_match_adr_0003_categories_lowercased() -> None:
    # ADR-0003's own illustrative examples, lowercased per this contract's
    # serialization choice (see docs/reason-code.md).
    illustrative = _load()["reason_code"]["illustrative_examples"]
    expected = {
        "allow_rule_matched",
        "deny_rule_matched",
        "no_allow_rule_matched",
        "missing_required_context",
        "unknown_resource_type",
        "unsupported_schema_version",
        "policy_bundle_invalid",
        "evaluation_error",
    }
    assert set(illustrative) == expected


def test_new_shared_contract_is_tracked_in_metadata() -> None:
    assert "reason-code" in basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS
    assert "reason-code" not in basis_schemas.PLANNED_CONTRACTS
