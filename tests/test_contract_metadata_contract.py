"""Focused checks on the published contract-metadata contract.

These tests validate ``schemas/contract-metadata/contract-metadata.yaml``: its
own metadata, its declared field policy, and that the published rules accept
well-formed `contract:` blocks and reject malformed ones. This contract
formalizes a pattern this repository already established and reused six
times, so it is additionally cross-checked here against the real `contract:`
blocks of every currently published contract, proving the new schema
describes existing usage faithfully rather than a new, parallel design.

This is a contract publication, not a parser: the only behavior exercised
here is applying the contract's own published rules (required fields, the
no-unknown-fields policy, the name/version patterns, and the lifecycle enum)
to example metadata blocks.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import basis_schemas

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
METADATA_DIR = REPO_ROOT / "schemas" / "contract-metadata"
METADATA_FILE = METADATA_DIR / "contract-metadata.yaml"


def _load() -> dict:
    with METADATA_FILE.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict), "contract-metadata.yaml must parse to a mapping"
    return data


def _body() -> dict:
    return _load()["contract_metadata"]


def _is_valid_contract_metadata(obj: object, body: dict) -> bool:
    """Apply the contract's own published rules to a candidate metadata block."""
    if not isinstance(obj, dict):
        return False

    allowed = set(body["required"]) | set(body["optional"])
    if not body["additional_properties"] and set(obj) - allowed:
        return False

    if any(field not in obj for field in body["required"]):
        return False

    for field in ("name", "title", "governed_by", "published_by", "source", "description"):
        value = obj.get(field)
        if not isinstance(value, str) or not value.strip():
            return False

    name_pattern = re.compile(_field(body, "name")["pattern"])
    if not name_pattern.match(obj["name"]):
        return False

    version_pattern = re.compile(_field(body, "version")["pattern"])
    version = obj.get("version")
    if not isinstance(version, str) or not version_pattern.match(version):
        return False

    if obj.get("lifecycle") not in _field(body, "lifecycle")["enum"]:
        return False

    if "depends_on" in obj:
        depends_on = obj["depends_on"]
        if not isinstance(depends_on, list):
            return False
        for entry in depends_on:
            if not isinstance(entry, str) or not name_pattern.match(entry):
                return False

    return True


def _field(body: dict, field_id: str) -> dict:
    for field in body["fields"]:
        if field["id"] == field_id:
            return field
    raise AssertionError(f"field {field_id!r} not declared in contract_metadata.fields")


def test_contract_metadata_file_exists() -> None:
    assert METADATA_FILE.is_file(), "schemas/contract-metadata/contract-metadata.yaml must exist"


def test_contract_metadata_yaml_parses() -> None:
    assert _load()


def test_contract_metadata_matches_expected_values() -> None:
    contract = _load()["contract"]
    assert contract["name"] == "contract-metadata"
    assert contract["title"] == "BASIS Contract Metadata"
    assert isinstance(contract.get("version"), str) and contract["version"]
    assert contract["governed_by"] == "basis-architecture"
    assert contract["published_by"] == "basis-schemas"


def test_lifecycle_is_experimental() -> None:
    assert _load()["contract"]["lifecycle"] == "experimental"


def test_contract_metadata_has_no_dependency() -> None:
    # contract-metadata is the most foundational shared contract: nothing else
    # is published yet for it to depend on.
    assert _load()["contract"].get("depends_on") in (None, [])


def test_required_and_optional_fields() -> None:
    body = _body()
    assert body["required"] == [
        "name",
        "title",
        "version",
        "lifecycle",
        "governed_by",
        "published_by",
        "source",
        "description",
    ]
    assert body["optional"] == ["depends_on"]
    assert body["additional_properties"] is False


def test_name_pattern_accepts_all_published_contract_names() -> None:
    pattern = re.compile(_field(_body(), "name")["pattern"])
    all_names = set(basis_schemas.PUBLISHED_CONTRACTS) | set(
        basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS
    )
    for name in all_names:
        assert pattern.match(name), f"published contract name rejected by pattern: {name!r}"


def test_name_pattern_rejects_non_kebab_case() -> None:
    pattern = re.compile(_field(_body(), "name")["pattern"])
    for bad in ("Example_Contract", "Not_A_Valid_Name", "", "UPPER-CASE", "trailing-"):
        assert not pattern.match(bad), f"malformed name accepted by pattern: {bad!r}"


def test_version_pattern_accepts_semver() -> None:
    pattern = re.compile(_field(_body(), "version")["pattern"])
    for good in ("0.1.0", "1.2.3", "10.20.30"):
        assert pattern.match(good), f"valid semver rejected: {good!r}"


def test_version_pattern_rejects_non_semver() -> None:
    pattern = re.compile(_field(_body(), "version")["pattern"])
    for bad in ("v1", "1.0", "", "0.1", "1.2.3-rc1"):
        assert not pattern.match(bad), f"malformed version accepted: {bad!r}"


def test_lifecycle_enum_matches_contract_states() -> None:
    assert _field(_body(), "lifecycle")["enum"] == list(basis_schemas.CONTRACT_STATES)


def test_required_valid_examples_accepted() -> None:
    body = _body()
    for example in body["examples"]["valid"]:
        assert _is_valid_contract_metadata(example, body), f"valid example rejected: {example!r}"


def test_required_invalid_examples_rejected() -> None:
    body = _body()
    for case in body["examples"]["invalid"]:
        assert "reason" in case, f"invalid example missing a reason: {case!r}"
        assert not _is_valid_contract_metadata(case["value"], body), (
            f"invalid metadata accepted ({case['reason']}): {case['value']!r}"
        )


def test_invalid_examples_cover_required_cases() -> None:
    reasons = " ".join(case["reason"] for case in _body()["examples"]["invalid"]).lower()
    assert "missing required name" in reasons
    assert "empty name" in reasons
    assert "malformed name" in reasons
    assert "missing required version" in reasons
    assert "empty version" in reasons
    assert "malformed version" in reasons
    assert "invalid lifecycle" in reasons
    assert "malformed depends_on" in reasons
    assert "unknown" in reasons or "additional" in reasons


def test_existing_published_contract_blocks_are_valid_under_this_schema() -> None:
    """Regression check: every already-published contract's own `contract:`
    block must be accepted by the schema this PR publishes, proving it
    describes existing usage rather than a new, parallel convention."""
    body = _body()
    for name in basis_schemas.PUBLISHED_CONTRACTS:
        contract_file = REPO_ROOT / "schemas" / name / f"{name}.yaml"
        with contract_file.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        block = data["contract"]
        assert _is_valid_contract_metadata(block, body), (
            f"existing published contract block for {name!r} rejected by "
            f"contract-metadata schema: {block!r}"
        )


def test_new_shared_contract_blocks_are_valid_under_this_schema() -> None:
    body = _body()
    for name in basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS:
        contract_file = REPO_ROOT / "schemas" / name / f"{name}.yaml"
        with contract_file.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        block = data["contract"]
        assert _is_valid_contract_metadata(block, body), (
            f"new shared contract block for {name!r} rejected by "
            f"contract-metadata schema: {block!r}"
        )
