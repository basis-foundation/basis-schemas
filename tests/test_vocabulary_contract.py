"""Focused checks on the published vocabulary contract.

These tests validate the *first real contract* published in this repository:
``schemas/vocabulary/vocabulary.yaml``. They assert the contract metadata, the
published verb set, and that the migration left the rest of the repository in its
placeholder state. The verbs themselves are decided in ``basis-architecture``;
these tests confirm the publication faithfully reproduces that decision.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import basis_schemas

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
VOCAB_DIR = REPO_ROOT / "schemas" / "vocabulary"
VOCAB_FILE = VOCAB_DIR / "vocabulary.yaml"

#: The canonical verbs, in order, as decided in basis-architecture
#: (docs/architecture/action-vocabulary.md). This list is the test oracle: the
#: published contract must match it exactly.
CANONICAL_VERBS = ("read", "write", "execute", "browse", "subscribe")


def _load() -> dict:
    with VOCAB_FILE.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict), "vocabulary.yaml must parse to a mapping"
    return data


def test_vocabulary_file_exists() -> None:
    assert VOCAB_FILE.is_file(), "schemas/vocabulary/vocabulary.yaml must exist"


def test_vocabulary_yaml_parses() -> None:
    # _load() raises if the YAML is malformed or not a mapping.
    assert _load()


def test_contract_metadata_block_exists() -> None:
    data = _load()
    assert "contract" in data, "missing top-level 'contract' metadata block"
    assert isinstance(data["contract"], dict)


def test_contract_name_is_vocabulary() -> None:
    assert _load()["contract"]["name"] == "vocabulary"


def test_contract_version_exists() -> None:
    version = _load()["contract"].get("version")
    assert isinstance(version, str) and version, "contract.version must be a non-empty string"


def test_contract_lifecycle_is_experimental() -> None:
    assert _load()["contract"]["lifecycle"] == "experimental"


def test_contract_governed_by_architecture() -> None:
    assert _load()["contract"]["governed_by"] == "basis-architecture"


def test_contract_published_by_schemas() -> None:
    assert _load()["contract"]["published_by"] == "basis-schemas"


def test_vocabulary_verbs_block_exists() -> None:
    data = _load()
    assert "vocabulary" in data and isinstance(data["vocabulary"], dict)
    assert "verbs" in data["vocabulary"], "missing vocabulary.verbs"
    assert isinstance(data["vocabulary"]["verbs"], list)


def test_exactly_five_verbs_published() -> None:
    verbs = _load()["vocabulary"]["verbs"]
    assert len(verbs) == 5, f"expected exactly five verbs, found {len(verbs)}"


def test_verb_ids_are_exactly_canonical() -> None:
    ids = [verb["id"] for verb in _load()["vocabulary"]["verbs"]]
    assert tuple(ids) == CANONICAL_VERBS, f"verb ids must be {CANONICAL_VERBS}, found {tuple(ids)}"


def test_no_duplicate_verb_ids() -> None:
    ids = [verb["id"] for verb in _load()["vocabulary"]["verbs"]]
    assert len(ids) == len(set(ids)), f"duplicate verb ids present: {ids}"


def test_every_verb_has_a_non_empty_description() -> None:
    for verb in _load()["vocabulary"]["verbs"]:
        description = verb.get("description")
        assert isinstance(description, str) and description.strip(), (
            f"verb {verb.get('id')!r} must have a non-empty description"
        )


def test_placeholder_removed_from_vocabulary_dir() -> None:
    assert not (VOCAB_DIR / "PLACEHOLDER.md").exists(), (
        "schemas/vocabulary/PLACEHOLDER.md should be removed now that the contract is published"
    )


def test_vocabulary_is_a_published_contract() -> None:
    # Vocabulary was the first contract published. (The full published/placeholder
    # invariant across all directories is asserted in test_repository_layout.py.)
    assert "vocabulary" in basis_schemas.PUBLISHED_CONTRACTS
