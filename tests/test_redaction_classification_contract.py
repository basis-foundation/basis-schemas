"""Focused checks on the published redaction-classification contract.

These tests validate ``schemas/redaction-classification/redaction-classification.yaml``:
its metadata, its declared dependency on contract-metadata, and that it
publishes exactly the five classifications decided in basis-architecture
(``docs/architecture/operation-aware-trace-audit-evidence.md``, ADR-0003,
Section 10), each with a non-empty description, serialized in lowercase
snake_case.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import basis_schemas

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
REDACTION_DIR = REPO_ROOT / "schemas" / "redaction-classification"
REDACTION_FILE = REDACTION_DIR / "redaction-classification.yaml"

#: The five classifications decided in ADR-0003, Section 10. This list is the
#: test oracle: the published contract must match it exactly.
CANONICAL_CLASSIFICATIONS = (
    "safe_to_expose",
    "safe_after_redaction",
    "reference_only",
    "never_store",
    "never_display",
)


def _load() -> dict:
    with REDACTION_FILE.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict), "redaction-classification.yaml must parse to a mapping"
    return data


def test_redaction_classification_file_exists() -> None:
    assert REDACTION_FILE.is_file(), (
        "schemas/redaction-classification/redaction-classification.yaml must exist"
    )


def test_redaction_classification_yaml_parses() -> None:
    assert _load()


def test_contract_metadata_matches_expected_values() -> None:
    contract = _load()["contract"]
    assert contract["name"] == "redaction-classification"
    assert contract["title"] == "BASIS Redaction Classification"
    assert isinstance(contract.get("version"), str) and contract["version"]
    assert contract["governed_by"] == "basis-architecture"
    assert contract["published_by"] == "basis-schemas"


def test_lifecycle_is_experimental() -> None:
    assert _load()["contract"]["lifecycle"] == "experimental"


def test_contract_metadata_dependency_is_declared() -> None:
    depends_on = _load()["contract"].get("depends_on")
    assert isinstance(depends_on, list), "contract.depends_on must be a list"
    assert "contract-metadata" in depends_on


def test_values_block_exists() -> None:
    data = _load()
    assert "redaction_classification" in data
    assert isinstance(data["redaction_classification"], dict)
    assert "values" in data["redaction_classification"]
    assert isinstance(data["redaction_classification"]["values"], list)


def test_exactly_five_classifications_published() -> None:
    values = _load()["redaction_classification"]["values"]
    assert len(values) == 5, f"expected exactly five classifications, found {len(values)}"


def test_classification_ids_are_exactly_canonical() -> None:
    ids = [value["id"] for value in _load()["redaction_classification"]["values"]]
    assert tuple(ids) == CANONICAL_CLASSIFICATIONS, (
        f"classification ids must be {CANONICAL_CLASSIFICATIONS}, found {tuple(ids)}"
    )


def test_no_duplicate_classification_ids() -> None:
    ids = [value["id"] for value in _load()["redaction_classification"]["values"]]
    assert len(ids) == len(set(ids)), f"duplicate classification ids present: {ids}"


def test_every_classification_has_a_non_empty_description() -> None:
    for value in _load()["redaction_classification"]["values"]:
        description = value.get("description")
        assert isinstance(description, str) and description.strip(), (
            f"classification {value.get('id')!r} must have a non-empty description"
        )


def test_ids_are_lowercase_snake_case() -> None:
    for value in _load()["redaction_classification"]["values"]:
        classification_id = value["id"]
        assert classification_id == classification_id.lower(), (
            f"classification id must be lowercase: {classification_id!r}"
        )
        assert " " not in classification_id and "-" not in classification_id, (
            f"classification id must use underscores, not spaces or hyphens: {classification_id!r}"
        )


def test_never_store_and_never_display_are_distinct() -> None:
    values = {
        value["id"]: value["description"] for value in _load()["redaction_classification"]["values"]
    }
    assert values["never_store"] != values["never_display"]
    never_store = values["never_store"].lower()
    never_display = values["never_display"].lower()
    # never_store is about persistence; never_display is about rendering.
    assert "persist" in never_store or "store" in never_store
    assert "render" in never_display or "display" in never_display


def test_declared_examples_match_canonical_ids() -> None:
    body = _load()["redaction_classification"]
    valid_ids = {value["id"] for value in body["values"]}
    for example in body["examples"]["valid"]:
        assert example in valid_ids, (
            f"declared-valid example not a published classification: {example!r}"
        )
    for case in body["examples"]["invalid"]:
        assert case["value"] not in valid_ids, (
            f"declared-invalid example is actually a published classification: {case['value']!r}"
        )


def test_new_shared_contract_is_tracked_in_metadata() -> None:
    assert "redaction-classification" in basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS
    # This second wave is separate from, and does not extend, the first-wave
    # six-contract migration tracked in PLANNED_CONTRACTS / PUBLISHED_CONTRACTS.
    assert "redaction-classification" not in basis_schemas.PLANNED_CONTRACTS
