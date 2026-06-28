"""Focused checks on the published decision-request contract.

These tests validate ``schemas/decision-request/decision-request.yaml``: its
metadata and that the published field policy and the canonical patterns it
reproduces accept well-formed decision requests and reject malformed ones. The
shape is decided in ``basis-architecture`` and implemented by ``basis-core``;
these tests confirm the publication reproduces that shape faithfully.

This is a contract publication, not a parser: the only behavior exercised here is
applying the contract's own published rules (required fields, the no-unknown-
fields policy, and the canonical action / resource-identifier regexes) to example
requests.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import basis_schemas

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
REQUEST_DIR = REPO_ROOT / "schemas" / "decision-request"
REQUEST_FILE = REQUEST_DIR / "decision-request.yaml"


def _load() -> dict:
    with REQUEST_FILE.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict), "decision-request.yaml must parse to a mapping"
    return data


def _body() -> dict:
    return _load()["decision_request"]


def _is_valid_request(obj: object, body: dict) -> bool:
    """Apply the contract's own published rules to a candidate request object.

    Returns True only if ``obj`` satisfies every published rule: it is a mapping,
    all required fields are present, ``request_id`` / ``subject_id`` are non-empty,
    ``action`` matches the canonical action pattern, ``resource_id`` (when present
    and non-null) matches the canonical resource pattern, and no unknown field
    appears (the contract sets additional_properties: false).
    """
    if not isinstance(obj, dict):
        return False

    allowed = set(body["required"]) | set(body["optional"])
    if not body["additional_properties"] and set(obj) - allowed:
        return False

    if any(field not in obj for field in body["required"]):
        return False

    for field in ("request_id", "subject_id"):
        value = obj.get(field)
        if not isinstance(value, str) or not value.strip():
            return False

    action = obj.get("action")
    if not isinstance(action, str) or not re.match(body["action_pattern"], action):
        return False

    if "resource_id" in obj and obj["resource_id"] is not None:
        resource_id = obj["resource_id"]
        pattern = body["resource_id_pattern"]
        if not isinstance(resource_id, str) or not re.match(pattern, resource_id):
            return False

    return True


def test_decision_request_file_exists() -> None:
    assert REQUEST_FILE.is_file(), "schemas/decision-request/decision-request.yaml must exist"


def test_decision_request_yaml_parses() -> None:
    assert _load()


def test_contract_metadata_matches_expected_values() -> None:
    contract = _load()["contract"]
    assert contract["name"] == "decision-request"
    assert contract["title"] == "BASIS Decision Request"
    assert contract["version"] == "0.1.0"
    assert contract["governed_by"] == "basis-architecture"
    assert contract["published_by"] == "basis-schemas"


def test_lifecycle_is_experimental() -> None:
    assert _load()["contract"]["lifecycle"] == "experimental"


def test_declares_dependency_on_format_contracts() -> None:
    # The request composes the action-string and resource-identifier formats, so
    # it must declare both as dependencies.
    depends_on = _load()["contract"]["depends_on"]
    assert "action-string" in depends_on
    assert "resource-identifier" in depends_on


def test_required_fields_match_basis_core() -> None:
    # The canonical required set, identical to basis-core's
    # decision-request.schema.json.
    assert _body()["required"] == ["request_id", "subject_id", "action", "timestamp"]


def test_unknown_fields_are_rejected_by_policy() -> None:
    assert _body()["additional_properties"] is False


def test_required_valid_examples_accepted() -> None:
    body = _body()
    for request in body["examples"]["valid"]:
        assert _is_valid_request(request, body), f"valid request rejected: {request!r}"


def test_required_invalid_examples_rejected() -> None:
    body = _body()
    for case in body["examples"]["invalid"]:
        # Each invalid example is a {reason, value} mapping documenting why it is
        # invalid; the value must fail validation.
        assert "reason" in case, f"invalid example missing a reason: {case!r}"
        assert not _is_valid_request(case["value"], body), (
            f"invalid request accepted ({case['reason']}): {case['value']!r}"
        )


def test_invalid_examples_cover_required_cases() -> None:
    # The phase mandates coverage of these failure modes; assert the published
    # invalid examples exercise each one.
    reasons = " ".join(case["reason"] for case in _body()["examples"]["invalid"]).lower()
    assert "subject" in reasons  # malformed / missing subject
    assert "action" in reasons  # missing and invalid action string
    assert "resource identifier" in reasons  # invalid resource identifier
    assert "request_id" in reasons  # missing required field
    assert "timestamp" in reasons  # missing required field
    assert "unknown" in reasons or "additional" in reasons  # unknown field


def test_action_pattern_matches_published_action_string_contract() -> None:
    # The reproduced canonical action pattern must be exactly the one published by
    # the action-string contract; the request must not invent its own.
    action_string = REPO_ROOT / "schemas" / "action-string" / "action-string.yaml"
    with action_string.open(encoding="utf-8") as handle:
        canonical = yaml.safe_load(handle)["action_string"]["pattern"]
    assert _body()["action_pattern"] == canonical


def test_resource_id_pattern_matches_published_resource_identifier_contract() -> None:
    resource_identifier = REPO_ROOT / "schemas" / "resource-identifier" / "resource-identifier.yaml"
    with resource_identifier.open(encoding="utf-8") as handle:
        canonical = yaml.safe_load(handle)["resource_identifier"]["pattern"]
    assert _body()["resource_id_pattern"] == canonical


def test_canonical_action_and_resource_examples() -> None:
    # The phase's canonical examples must validate.
    body = _body()
    assert re.match(body["action_pattern"], "read:ahu")
    assert re.match(body["resource_id_pattern"], "ahu:rooftop-1")


def test_placeholder_removed_from_decision_request_dir() -> None:
    assert not (REQUEST_DIR / "PLACEHOLDER.md").exists(), (
        "schemas/decision-request/PLACEHOLDER.md should be removed now that the "
        "contract is published"
    )


def test_remaining_future_contracts_still_have_placeholders() -> None:
    # decision-request is published; every still-deferred contract must remain a
    # placeholder holding only PLACEHOLDER.md.
    assert "decision-request" in basis_schemas.PUBLISHED_CONTRACTS
    deferred = [
        c for c in basis_schemas.PLANNED_CONTRACTS if c not in basis_schemas.PUBLISHED_CONTRACTS
    ]
    for contract in deferred:
        directory = REPO_ROOT / "schemas" / contract
        entries = sorted(p.name for p in directory.iterdir() if p.is_file())
        assert entries == ["PLACEHOLDER.md"], (
            f"{contract} should remain a placeholder, found: {entries}"
        )
