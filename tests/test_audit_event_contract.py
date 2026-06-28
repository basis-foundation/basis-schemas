"""Focused checks on the published audit-event contract.

These tests validate ``schemas/audit-event/audit-event.yaml``: its metadata and
that the published field policy and enumerated value sets accept well-formed audit
records and reject malformed ones. The shape is decided in ``basis-architecture``
and implemented by ``basis-core``; these tests confirm the publication reproduces
that shape faithfully.

This is a contract publication, not a parser: the only behavior exercised here is
applying the contract's own published rules (required fields, the no-unknown-
fields policy, the event-type / outcome / subject-type enums, the non-empty
constraints, and the canonical resource-identifier regex) to example records.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import basis_schemas

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIT_DIR = REPO_ROOT / "schemas" / "audit-event"
AUDIT_FILE = AUDIT_DIR / "audit-event.yaml"


def _load() -> dict:
    with AUDIT_FILE.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict), "audit-event.yaml must parse to a mapping"
    return data


def _body() -> dict:
    return _load()["audit_event"]


def _is_valid_event(obj: object, body: dict) -> bool:
    """Apply the contract's own published rules to a candidate audit record.

    Returns True only if ``obj`` satisfies every published top-level rule: it is a
    mapping, no unknown field appears, all required fields are present, ``event_id``
    and ``action`` are non-empty, ``event_type`` is a published value, the
    correlation/subject identifiers (when present and non-null) are non-empty,
    ``subject_type`` / ``outcome`` (when present and non-null) are published
    values, and ``resource_id`` (when present and non-null) matches the canonical
    resource pattern.
    """
    if not isinstance(obj, dict):
        return False

    allowed = set(body["required"]) | set(body["optional"])
    if not body["additional_properties"] and set(obj) - allowed:
        return False

    if any(field not in obj for field in body["required"]):
        return False

    for field in ("event_id", "action"):
        value = obj.get(field)
        if not isinstance(value, str) or not value.strip():
            return False

    if obj.get("event_type") not in body["event_type_values"]:
        return False

    for field in ("request_id", "decision_id", "subject_id"):
        if field in obj and obj[field] is not None:
            if not isinstance(obj[field], str) or not obj[field].strip():
                return False

    if obj.get("subject_type") is not None and "subject_type" in obj:
        if obj["subject_type"] not in body["subject_type_values"]:
            return False

    if obj.get("outcome") is not None and "outcome" in obj:
        if obj["outcome"] not in body["outcome_values"]:
            return False

    if obj.get("resource_id") is not None and "resource_id" in obj:
        if not isinstance(obj["resource_id"], str) or not re.match(
            body["resource_id_pattern"], obj["resource_id"]
        ):
            return False

    return True


def test_audit_event_file_exists() -> None:
    assert AUDIT_FILE.is_file(), "schemas/audit-event/audit-event.yaml must exist"


def test_audit_event_yaml_parses() -> None:
    assert _load()


def test_contract_metadata_matches_expected_values() -> None:
    contract = _load()["contract"]
    assert contract["name"] == "audit-event"
    assert contract["title"] == "BASIS Audit Event"
    assert contract["version"] == "0.1.0"
    assert contract["governed_by"] == "basis-architecture"
    assert contract["published_by"] == "basis-schemas"


def test_lifecycle_is_experimental() -> None:
    assert _load()["contract"]["lifecycle"] == "experimental"


def test_declares_dependencies_on_decision_contracts() -> None:
    # The audit event records the request and the response and correlates by
    # request_id, so it must declare both decision contracts as dependencies.
    depends_on = _load()["contract"]["depends_on"]
    assert "decision-request" in depends_on
    assert "decision-response" in depends_on


def test_required_fields_match_basis_core() -> None:
    # The canonical required set, identical to basis-core's
    # audit-event.schema.json.
    assert _body()["required"] == ["event_id", "event_type", "action", "timestamp"]


def test_event_type_values_match_basis_core() -> None:
    assert _body()["event_type_values"] == [
        "authorization_decision",
        "policy_change",
        "identity_event",
        "emergency_override",
        "adapter_event",
        "system_event",
    ]


def test_outcome_values_are_audit_vocabulary() -> None:
    # The audit outcome vocabulary is past-tense and distinct from the
    # decision-response outcome vocabulary.
    assert _body()["outcome_values"] == ["allowed", "denied", "error"]


def test_subject_type_values_match_basis_core() -> None:
    assert _body()["subject_type_values"] == ["human", "device", "service", "gateway", "agent"]


def test_unknown_fields_are_rejected_by_policy() -> None:
    assert _body()["additional_properties"] is False


def test_no_failure_reason_field() -> None:
    # The audit event has no failure_reason field (unlike the decision response);
    # an enforcement-boundary failure is recorded as outcome 'error'.
    field_ids = {f["id"] for f in _body()["fields"]}
    assert "failure_reason" not in field_ids
    assert "failure_reason" not in set(_body()["required"]) | set(_body()["optional"])


def test_required_valid_examples_accepted() -> None:
    body = _body()
    for event in body["examples"]["valid"]:
        assert _is_valid_event(event, body), f"valid audit event rejected: {event!r}"


def test_required_invalid_examples_rejected() -> None:
    body = _body()
    for case in body["examples"]["invalid"]:
        assert "reason" in case, f"invalid example missing a reason: {case!r}"
        assert not _is_valid_event(case["value"], body), (
            f"invalid audit event accepted ({case['reason']}): {case['value']!r}"
        )


def test_invalid_examples_cover_required_cases() -> None:
    # The phase mandates coverage of these failure modes; assert the published
    # invalid examples exercise each one.
    reasons = " ".join(case["reason"] for case in _body()["examples"]["invalid"]).lower()
    assert "missing required event_id" in reasons
    assert "empty event_id" in reasons  # malformed event_id
    assert "event_type" in reasons  # missing and invalid event_type
    assert "outcome" in reasons  # invalid outcome
    assert "subject_type" in reasons  # invalid subject_type
    assert "request_id" in reasons  # malformed request_id
    assert "failure_reason" in reasons  # rejected as unknown field
    assert "unknown" in reasons or "additional" in reasons


def test_outcome_distinct_from_decision_response_vocabulary() -> None:
    # 'allow' is the decision-response value; it must be invalid as an audit
    # outcome. This pins the deliberate vocabulary difference.
    body = _body()
    assert "allow" not in body["outcome_values"]
    bad = {
        "event_id": "e1000000-0000-0000-0000-0000000000ff",
        "event_type": "authorization_decision",
        "action": "write:hvac:setpoint",
        "timestamp": "2026-05-22T14:30:00Z",
        "outcome": "allow",
    }
    assert not _is_valid_event(bad, body)


def test_placeholder_removed_from_audit_event_dir() -> None:
    assert not (AUDIT_DIR / "PLACEHOLDER.md").exists(), (
        "schemas/audit-event/PLACEHOLDER.md should be removed now that the contract is published"
    )


def test_all_planned_contracts_are_now_published() -> None:
    # audit-event is the last planned contract; with it published, no planned
    # contract remains a placeholder.
    assert "audit-event" in basis_schemas.PUBLISHED_CONTRACTS
    deferred = [
        c for c in basis_schemas.PLANNED_CONTRACTS if c not in basis_schemas.PUBLISHED_CONTRACTS
    ]
    assert deferred == [], f"expected all planned contracts published, still deferred: {deferred}"
    # And no schema directory still holds a PLACEHOLDER.md.
    for contract in basis_schemas.PLANNED_CONTRACTS:
        assert not (REPO_ROOT / "schemas" / contract / "PLACEHOLDER.md").exists(), (
            f"{contract} still has a PLACEHOLDER.md"
        )
