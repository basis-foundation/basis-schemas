"""Focused checks on the published decision-response contract.

These tests validate ``schemas/decision-response/decision-response.yaml``: its
metadata and that the published field policy and enumerated value sets accept
well-formed decision responses and reject malformed ones. The shape is decided in
``basis-architecture`` and implemented by ``basis-core``; these tests confirm the
publication reproduces that shape faithfully.

This is a contract publication, not a parser: the only behavior exercised here is
applying the contract's own published rules (required fields, the no-unknown-
fields policy, the outcome / failure-reason enums, and the non-empty and
nullable-type constraints) to example responses.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import basis_schemas

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
RESPONSE_DIR = REPO_ROOT / "schemas" / "decision-response"
RESPONSE_FILE = RESPONSE_DIR / "decision-response.yaml"


def _load() -> dict:
    with RESPONSE_FILE.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict), "decision-response.yaml must parse to a mapping"
    return data


def _body() -> dict:
    return _load()["decision_response"]


def _is_valid_response(obj: object, body: dict) -> bool:
    """Apply the contract's own published rules to a candidate response object.

    Returns True only if ``obj`` satisfies every published rule: it is a mapping,
    no unknown field appears, all required fields are present, the non-empty
    string fields are non-empty, ``outcome`` is a published outcome value,
    ``failure_reason`` (when present and non-null) is a published failure-reason
    value, and ``policy_version`` (when present) is a string or null.
    """
    if not isinstance(obj, dict):
        return False

    allowed = set(body["required"]) | set(body["optional"])
    if not body["additional_properties"] and set(obj) - allowed:
        return False

    if any(field not in obj for field in body["required"]):
        return False

    for field in ("request_id", "reason", "evaluated_by"):
        value = obj.get(field)
        if not isinstance(value, str) or not value.strip():
            return False

    if obj.get("outcome") not in body["outcome_values"]:
        return False

    if "failure_reason" in obj and obj["failure_reason"] is not None:
        if obj["failure_reason"] not in body["failure_reason_values"]:
            return False

    if "policy_version" in obj and obj["policy_version"] is not None:
        if not isinstance(obj["policy_version"], str):
            return False

    return True


def test_decision_response_file_exists() -> None:
    assert RESPONSE_FILE.is_file(), "schemas/decision-response/decision-response.yaml must exist"


def test_decision_response_yaml_parses() -> None:
    assert _load()


def test_contract_metadata_matches_expected_values() -> None:
    contract = _load()["contract"]
    assert contract["name"] == "decision-response"
    assert contract["title"] == "BASIS Decision Response"
    assert contract["version"] == "0.1.0"
    assert contract["governed_by"] == "basis-architecture"
    assert contract["published_by"] == "basis-schemas"


def test_lifecycle_is_experimental() -> None:
    assert _load()["contract"]["lifecycle"] == "experimental"


def test_declares_dependency_on_decision_request() -> None:
    # The response is the output paired with the decision-request input and echoes
    # its request_id, so it must declare that dependency.
    assert "decision-request" in _load()["contract"]["depends_on"]


def test_required_fields_match_basis_core() -> None:
    # The canonical required set, identical to basis-core's
    # decision-response.schema.json.
    assert _body()["required"] == ["request_id", "outcome", "reason", "evaluated_by", "timestamp"]


def test_outcome_values_match_basis_core() -> None:
    assert _body()["outcome_values"] == ["allow", "deny", "not_applicable"]


def test_failure_reason_values_match_basis_core() -> None:
    assert _body()["failure_reason_values"] == [
        "malformed_request",
        "policy_error",
        "audit_error",
        "internal_error",
    ]


def test_unknown_fields_are_rejected_by_policy() -> None:
    assert _body()["additional_properties"] is False


def test_required_valid_examples_accepted() -> None:
    body = _body()
    for response in body["examples"]["valid"]:
        assert _is_valid_response(response, body), f"valid response rejected: {response!r}"


def test_required_invalid_examples_rejected() -> None:
    body = _body()
    for case in body["examples"]["invalid"]:
        assert "reason" in case, f"invalid example missing a reason: {case!r}"
        assert not _is_valid_response(case["value"], body), (
            f"invalid response accepted ({case['reason']}): {case['value']!r}"
        )


def test_invalid_examples_cover_required_cases() -> None:
    # The phase mandates coverage of these failure modes; assert the published
    # invalid examples exercise each one.
    reasons = " ".join(case["reason"] for case in _body()["examples"]["invalid"]).lower()
    assert "missing required request_id" in reasons  # missing required field
    assert "empty request_id" in reasons  # malformed request_id
    assert "outcome" in reasons and ("invalid" in reasons or "missing" in reasons)
    assert "failure_reason" in reasons  # invalid failure reason
    assert "policy_version" in reasons  # malformed policy_version
    assert "unknown" in reasons or "additional" in reasons  # unknown field


def test_every_valid_outcome_value_appears_in_a_valid_example() -> None:
    body = _body()
    seen = {response["outcome"] for response in body["examples"]["valid"]}
    assert set(body["outcome_values"]) <= seen, (
        "each outcome value should be demonstrated by a valid example"
    )


def test_placeholder_removed_from_decision_response_dir() -> None:
    assert not (RESPONSE_DIR / "PLACEHOLDER.md").exists(), (
        "schemas/decision-response/PLACEHOLDER.md should be removed now that the "
        "contract is published"
    )


def test_remaining_future_contracts_still_have_placeholders() -> None:
    # decision-response is published; audit-event remains the only deferred
    # contract and must hold only PLACEHOLDER.md.
    assert "decision-response" in basis_schemas.PUBLISHED_CONTRACTS
    deferred = [
        c for c in basis_schemas.PLANNED_CONTRACTS if c not in basis_schemas.PUBLISHED_CONTRACTS
    ]
    assert deferred == ["audit-event"]
    for contract in deferred:
        directory = REPO_ROOT / "schemas" / contract
        entries = sorted(p.name for p in directory.iterdir() if p.is_file())
        assert entries == ["PLACEHOLDER.md"], (
            f"{contract} should remain a placeholder, found: {entries}"
        )
