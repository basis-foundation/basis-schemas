"""Focused checks on the published gateway-audit-event contract.

These tests validate ``schemas/gateway-audit-event/gateway-audit-event.yaml``
(PR F of `basis-architecture`'s operation-aware schema readiness plan,
ADR-0005): its metadata, its declared dependencies, that its published field
policy accepts well-formed events and rejects malformed ones, that
``evaluation_status`` / ``outcome`` / ``failure_reason`` observe the required
invariant reused unchanged from PR E, that ``enforcement_action`` is
independently representable from the kernel ``outcome`` (fail-closed
behavior on NOT_APPLICABLE and on evaluator failure), that
``gateway_failure_reason`` is distinct from the kernel ``failure_reason`` and
forces a fail-closed ``enforcement_action``, that this contract references
(never embeds) an ``audit-evidence`` record, and that it never defines a
raw-secret, raw-request, or cryptographic-signing field.

This is a contract publication, not a parser: the only behavior exercised
here is applying the contract's own published rules to example event
objects.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import basis_schemas

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
EVENT_DIR = REPO_ROOT / "schemas" / "gateway-audit-event"
EVENT_FILE = EVENT_DIR / "gateway-audit-event.yaml"
EVIDENCE_FILE = REPO_ROOT / "schemas" / "audit-evidence" / "audit-evidence.yaml"
RESPONSE_FILE = (
    REPO_ROOT
    / "schemas"
    / "operation-aware-decision-response"
    / "operation-aware-decision-response.yaml"
)
TRACE_FILE = REPO_ROOT / "schemas" / "evaluation-trace" / "evaluation-trace.yaml"
POLICY_BUNDLE_FILE = REPO_ROOT / "schemas" / "policy-bundle" / "policy-bundle.yaml"
REASON_CODE_FILE = REPO_ROOT / "schemas" / "reason-code" / "reason-code.yaml"
FIRST_WAVE_AUDIT_EVENT_FILE = REPO_ROOT / "schemas" / "audit-event" / "audit-event.yaml"
FIRST_WAVE_AUDIT_EVENT_DOC = REPO_ROOT / "docs" / "audit-event.md"

FORBIDDEN_FIELDS = (
    "access_token",
    "id_token",
    "refresh_token",
    "jwt",
    "bearer_token",
    "authorization_header",
    "cookie",
    "session_secret",
    "client_secret",
    "password",
    "private_key",
    "api_key",
    "credential",
    "raw_claims",
    "full_claim_set",
    "raw_payload",
    "raw_protocol_payload",
    "packet",
    "frame",
    "device_secret",
    "full_request",
    "request_snapshot",
    "full_policy",
    "policy_document",
    "policy_source",
    "debug",
    "debug_data",
    "exception",
    "exception_object",
    "stack",
    "stack_trace",
    "traceback",
    "internal_error_detail",
    "implementation_detail",
    "rule_evidence",
    "condition_results",
    "subject_id",
    "action",
    "resource",
    "resource_type",
    "http_status",
    "response_status",
    "route",
    "endpoint",
    "audit_evidence",
    "enforcement_status",
    "enforcement_result",
    "signature",
    "signature_algorithm",
    "hash_chain",
    "previous_hash",
    "merkle_root",
    "storage_uri",
    "bucket_name",
    "object_key",
    "retention_policy",
)


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict), f"{path} must parse to a mapping"
    return data


def _load() -> dict:
    return _load_yaml(EVENT_FILE)


def _body() -> dict:
    return _load()["gateway_audit_event"]


def _is_valid_event(obj: object, body: dict) -> bool:
    if not isinstance(obj, dict):
        return False

    allowed = set(body["required"]) | set(body["optional"])
    if not body["additional_properties"] and set(obj) - allowed:
        return False
    if any(field not in obj for field in body["required"]):
        return False

    for field in ("event_id", "request_id", "audit_evidence_id"):
        value = obj.get(field)
        if not isinstance(value, str) or not value.strip():
            return False

    if obj.get("event_type") not in body["event_type_values"]:
        return False

    timestamp = obj.get("timestamp")
    if not isinstance(timestamp, str) or not re.match(body["timestamp_pattern"], timestamp):
        return False

    evaluation_status = obj.get("evaluation_status")
    if evaluation_status not in body["evaluation_status_values"]:
        return False

    outcome = obj.get("outcome")
    if evaluation_status == "completed":
        if outcome not in body["outcome_values"]:
            return False
    else:
        if outcome is not None:
            return False

    failure_reason = obj.get("failure_reason")
    if evaluation_status == "completed":
        if failure_reason is not None:
            return False
    else:
        if failure_reason not in body["failure_reason_values"]:
            return False

    enforcement_action = obj.get("enforcement_action")
    if enforcement_action not in body["enforcement_action_values"]:
        return False

    gateway_failure_reason = obj.get("gateway_failure_reason")
    if gateway_failure_reason is not None:
        if gateway_failure_reason not in body["gateway_failure_reason_values"]:
            return False
        if enforcement_action != "deny":
            return False

    if "correlation_id" in obj and obj["correlation_id"] is not None:
        if not isinstance(obj["correlation_id"], str):
            return False

    if "bundle_id" in obj and obj["bundle_id"] is not None:
        if not isinstance(obj["bundle_id"], str) or not obj["bundle_id"].strip():
            return False

    if "bundle_version" in obj and obj["bundle_version"] is not None:
        if not isinstance(obj["bundle_version"], str) or not re.match(
            body["bundle_version_pattern"], obj["bundle_version"]
        ):
            return False

    if "trace_id" in obj and obj["trace_id"] is not None:
        if not isinstance(obj["trace_id"], str) or not obj["trace_id"].strip():
            return False

    if "gateway_id" in obj and obj["gateway_id"] is not None:
        if not isinstance(obj["gateway_id"], str) or not obj["gateway_id"].strip():
            return False

    if "reason_code" in obj and obj["reason_code"] is not None:
        if not isinstance(obj["reason_code"], str) or not re.match(
            body["reason_code_pattern"], obj["reason_code"]
        ):
            return False

    if "explanation" in obj and obj["explanation"] is not None:
        if not isinstance(obj["explanation"], str) or not obj["explanation"].strip():
            return False

    if "schema_version" in obj and obj["schema_version"] is not None:
        if not isinstance(obj["schema_version"], str) or not re.match(
            body["schema_version_pattern"], obj["schema_version"]
        ):
            return False

    return True


# ---------------------------------------------------------------------------
# File / parsing
# ---------------------------------------------------------------------------


def test_gateway_audit_event_file_exists() -> None:
    assert EVENT_FILE.is_file(), "schemas/gateway-audit-event/gateway-audit-event.yaml must exist"


def test_gateway_audit_event_yaml_parses() -> None:
    assert _load()


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


def test_contract_metadata_matches_expected_values() -> None:
    contract = _load()["contract"]
    assert contract["name"] == "gateway-audit-event"
    assert contract["title"] == "BASIS Gateway Audit Event"
    assert contract["version"] == "0.1.0"
    assert contract["governed_by"] == "basis-architecture"
    assert contract["published_by"] == "basis-schemas"


def test_lifecycle_is_experimental() -> None:
    assert _load()["contract"]["lifecycle"] == "experimental"


def test_declares_expected_dependencies() -> None:
    assert _load()["contract"]["depends_on"] == [
        "contract-metadata",
        "operation-aware-decision-response",
        "evaluation-trace",
        "policy-bundle",
        "audit-evidence",
        "reason-code",
    ]


# ---------------------------------------------------------------------------
# Field policy
# ---------------------------------------------------------------------------


def test_required_and_optional_fields() -> None:
    body = _body()
    assert body["required"] == [
        "event_id",
        "event_type",
        "timestamp",
        "request_id",
        "evaluation_status",
        "outcome",
        "failure_reason",
        "audit_evidence_id",
        "enforcement_action",
    ]
    assert set(body["optional"]) == {
        "correlation_id",
        "bundle_id",
        "bundle_version",
        "trace_id",
        "gateway_id",
        "gateway_failure_reason",
        "reason_code",
        "explanation",
        "schema_version",
    }


def test_unknown_fields_are_rejected_by_policy() -> None:
    assert _body()["additional_properties"] is False


def test_event_type_is_a_single_closed_value() -> None:
    assert _body()["event_type_values"] == ["gateway_authorization"]


def test_enforcement_action_values() -> None:
    assert _body()["enforcement_action_values"] == ["allow", "deny"]


def test_gateway_failure_reason_values_are_small_and_bounded() -> None:
    values = _body()["gateway_failure_reason_values"]
    assert values == [
        "gateway_timeout",
        "upstream_unavailable",
        "audit_assembly_failure",
        "internal_gateway_error",
    ]
    assert len(values) <= 6, "gateway_failure_reason must stay a small, bounded vocabulary"


# ---------------------------------------------------------------------------
# Cross-contract parity (outcome / evaluation_status / failure_reason /
# bundle_version / reason_code) — reused exactly from PR E and audit-evidence
# ---------------------------------------------------------------------------


def test_outcome_values_match_operation_aware_decision_response() -> None:
    response_body = _load_yaml(RESPONSE_FILE)["operation_aware_decision_response"]
    assert _body()["outcome_values"] == response_body["outcome_values"]


def test_evaluation_status_values_match_operation_aware_decision_response() -> None:
    response_body = _load_yaml(RESPONSE_FILE)["operation_aware_decision_response"]
    assert _body()["evaluation_status_values"] == response_body["evaluation_status_values"]


def test_failure_reason_values_match_operation_aware_decision_response() -> None:
    response_body = _load_yaml(RESPONSE_FILE)["operation_aware_decision_response"]
    assert _body()["failure_reason_values"] == response_body["failure_reason_values"]


def test_outcome_values_match_evaluation_trace() -> None:
    trace_body = _load_yaml(TRACE_FILE)["evaluation_trace"]
    assert _body()["outcome_values"] == trace_body["outcome_values"]


def test_outcome_values_match_audit_evidence() -> None:
    evidence_body = _load_yaml(EVIDENCE_FILE)["audit_evidence"]
    assert _body()["outcome_values"] == evidence_body["outcome_values"]


def test_evaluation_status_values_match_audit_evidence() -> None:
    evidence_body = _load_yaml(EVIDENCE_FILE)["audit_evidence"]
    assert _body()["evaluation_status_values"] == evidence_body["evaluation_status_values"]


def test_failure_reason_values_match_audit_evidence() -> None:
    evidence_body = _load_yaml(EVIDENCE_FILE)["audit_evidence"]
    assert _body()["failure_reason_values"] == evidence_body["failure_reason_values"]


def test_bundle_version_pattern_matches_policy_bundle_source() -> None:
    bundle_body = _load_yaml(POLICY_BUNDLE_FILE)["policy_bundle"]
    assert _body()["bundle_version_pattern"] == bundle_body["fields"][1]["pattern"]


def test_bundle_version_pattern_matches_audit_evidence() -> None:
    evidence_body = _load_yaml(EVIDENCE_FILE)["audit_evidence"]
    assert _body()["bundle_version_pattern"] == evidence_body["bundle_version_pattern"]


def test_reason_code_pattern_matches_source_contract() -> None:
    reason_code_body = _load_yaml(REASON_CODE_FILE)["reason_code"]
    assert _body()["reason_code_pattern"] == reason_code_body["pattern"]


def test_reason_code_pattern_matches_audit_evidence() -> None:
    evidence_body = _load_yaml(EVIDENCE_FILE)["audit_evidence"]
    assert _body()["reason_code_pattern"] == evidence_body["reason_code_pattern"]


# ---------------------------------------------------------------------------
# Required invariant: outcome null iff evaluation_status is failed
# ---------------------------------------------------------------------------


def _minimal_valid_event(**overrides: object) -> dict:
    base = {
        "event_id": "gwae-x",
        "event_type": "gateway_authorization",
        "timestamp": "2026-05-22T14:30:00Z",
        "request_id": "oadr-x",
        "evaluation_status": "completed",
        "outcome": "allow",
        "failure_reason": None,
        "audit_evidence_id": "audev-x",
        "enforcement_action": "allow",
    }
    base.update(overrides)
    return base


def test_failed_evaluation_can_never_be_allow() -> None:
    body = _body()
    invalid = _minimal_valid_event(
        evaluation_status="failed",
        outcome="allow",
        failure_reason="internal_evaluation_error",
        enforcement_action="deny",
    )
    assert not _is_valid_event(invalid, body)


def test_completed_evaluation_requires_non_null_outcome() -> None:
    body = _body()
    invalid = _minimal_valid_event(outcome=None)
    assert not _is_valid_event(invalid, body)


def test_completed_evaluation_requires_null_failure_reason() -> None:
    body = _body()
    invalid = _minimal_valid_event(failure_reason="internal_evaluation_error")
    assert not _is_valid_event(invalid, body)


def test_failed_without_failure_reason_is_invalid() -> None:
    body = _body()
    invalid = _minimal_valid_event(
        evaluation_status="failed", outcome=None, failure_reason=None, enforcement_action="deny"
    )
    assert not _is_valid_event(invalid, body)


# ---------------------------------------------------------------------------
# State-matrix: enforcement_action independent of kernel outcome
# ---------------------------------------------------------------------------


def test_completed_allow_paired_with_enforcement_allow_is_valid() -> None:
    body = _body()
    valid = _minimal_valid_event(
        evaluation_status="completed", outcome="allow", enforcement_action="allow"
    )
    assert _is_valid_event(valid, body)


def test_completed_deny_paired_with_enforcement_deny_is_valid() -> None:
    body = _body()
    valid = _minimal_valid_event(
        evaluation_status="completed", outcome="deny", enforcement_action="deny"
    )
    assert _is_valid_event(valid, body)


def test_completed_allow_paired_with_enforcement_deny_is_valid_and_not_forced_equal() -> None:
    # This contract does not force enforcement_action to mechanically equal
    # kernel outcome — a gateway may still deny on top of a kernel allow
    # (e.g. a gateway-local failure; see the gateway_failure_reason tests).
    body = _body()
    valid = _minimal_valid_event(
        evaluation_status="completed",
        outcome="allow",
        enforcement_action="deny",
        gateway_failure_reason="audit_assembly_failure",
    )
    assert _is_valid_event(valid, body)


def test_completed_not_applicable_paired_with_enforcement_deny_is_valid() -> None:
    # Fail-closed gateway behavior on a kernel result that is NOT itself a
    # policy deny: not_applicable must never be conflated with deny.
    body = _body()
    valid = _minimal_valid_event(
        evaluation_status="completed", outcome="not_applicable", enforcement_action="deny"
    )
    assert _is_valid_event(valid, body)
    assert valid["outcome"] == "not_applicable"
    assert valid["outcome"] != "deny"


def test_failed_evaluation_paired_with_enforcement_deny_is_valid() -> None:
    # Fail-closed gateway behavior on a kernel evaluation failure: outcome
    # stays null, never rewritten as deny.
    body = _body()
    valid = _minimal_valid_event(
        evaluation_status="failed",
        outcome=None,
        failure_reason="internal_evaluation_error",
        enforcement_action="deny",
    )
    assert _is_valid_event(valid, body)
    assert valid["outcome"] is None


def test_not_applicable_is_never_reinterpreted_as_deny_anywhere_in_the_contract() -> None:
    # No rule in this contract's constraints text rewrites not_applicable as
    # a kernel-level deny.
    text = EVENT_FILE.read_text(encoding="utf-8")
    assert "not_applicable" in text
    # Sanity: not_applicable and deny remain two distinct enum members.
    body = _body()
    assert "not_applicable" in body["outcome_values"]
    assert "deny" in body["outcome_values"]
    assert body["outcome_values"].count("not_applicable") == 1
    assert body["outcome_values"].count("deny") == 1


# ---------------------------------------------------------------------------
# gateway_failure_reason: distinct from kernel failure_reason, forces deny
# ---------------------------------------------------------------------------


def test_gateway_failure_reason_with_enforcement_allow_is_invalid() -> None:
    body = _body()
    invalid = _minimal_valid_event(
        enforcement_action="allow", gateway_failure_reason="gateway_timeout"
    )
    assert not _is_valid_event(invalid, body)


def test_gateway_failure_reason_with_enforcement_deny_is_valid() -> None:
    body = _body()
    valid = _minimal_valid_event(
        enforcement_action="deny", gateway_failure_reason="gateway_timeout"
    )
    assert _is_valid_event(valid, body)


def test_gateway_failure_reason_is_independent_field_from_kernel_failure_reason() -> None:
    # A gateway-local failure can coexist with a *completed* kernel
    # evaluation_status — the two failure concepts are structurally
    # independent, never overloaded onto one field.
    body = _body()
    valid = _minimal_valid_event(
        evaluation_status="completed",
        outcome="allow",
        failure_reason=None,
        enforcement_action="deny",
        gateway_failure_reason="internal_gateway_error",
    )
    assert _is_valid_event(valid, body)
    assert body["gateway_failure_reason_values"] != body["failure_reason_values"]


@pytest.mark.parametrize("bad_value", ["timeout", "TIMEOUT", "network_error", 1, True, []])
def test_gateway_failure_reason_rejects_values_outside_closed_vocabulary(bad_value: object) -> None:
    body = _body()
    invalid = _minimal_valid_event(enforcement_action="deny", gateway_failure_reason=bad_value)
    assert not _is_valid_event(invalid, body)


# ---------------------------------------------------------------------------
# audit_evidence_id: required reference, no embedding
# ---------------------------------------------------------------------------


def test_missing_audit_evidence_id_is_invalid() -> None:
    body = _body()
    event = _minimal_valid_event()
    del event["audit_evidence_id"]
    assert not _is_valid_event(event, body)


def test_empty_audit_evidence_id_is_invalid() -> None:
    body = _body()
    invalid = _minimal_valid_event(audit_evidence_id="")
    assert not _is_valid_event(invalid, body)


def test_no_embedded_audit_evidence_object_field_is_published() -> None:
    body = _body()
    allowed = set(body["required"]) | set(body["optional"])
    assert "audit_evidence" not in allowed
    assert "audit_evidence_id" in allowed


# ---------------------------------------------------------------------------
# Examples
# ---------------------------------------------------------------------------


def test_required_valid_examples_accepted() -> None:
    body = _body()
    for example in body["examples"]["valid"]:
        assert _is_valid_event(example, body), f"valid example rejected: {example!r}"


def test_required_invalid_examples_rejected() -> None:
    body = _body()
    for case in body["examples"]["invalid"]:
        assert "reason" in case, f"invalid example missing a reason: {case!r}"
        assert not _is_valid_event(case["value"], body), (
            f"invalid example accepted ({case['reason']}): {case['value']!r}"
        )


def test_invalid_examples_cover_required_cases() -> None:
    reasons = " ".join(case["reason"] for case in _body()["examples"]["invalid"]).lower()
    assert "missing required event id" in reasons
    assert "empty event id" in reasons
    assert "invalid event type" in reasons
    assert "malformed timestamp" in reasons
    assert "missing required request id" in reasons
    assert "malformed kernel evaluation state" in reasons
    assert "kernel failed represented with non-null allow outcome" in reasons
    assert "invariant violation" in reasons
    assert "missing required audit evidence reference" in reasons
    assert "empty audit evidence reference" in reasons
    assert "invalid enforcement action" in reasons
    assert "missing required enforcement action" in reasons
    assert "gateway-local failure reason set while enforcement action is allow" in reasons
    assert "malformed reason code" in reasons
    assert "malformed policy provenance" in reasons
    assert "raw request field" in reasons
    assert "raw evidence field" in reasons
    assert "gateway secret field" in reasons
    assert "unknown field" in reasons


def test_every_outcome_value_appears_in_a_valid_example() -> None:
    body = _body()
    seen = {ex["outcome"] for ex in body["examples"]["valid"] if ex["outcome"] is not None}
    assert set(body["outcome_values"]) <= seen


def test_both_evaluation_statuses_appear_in_valid_examples() -> None:
    body = _body()
    seen = {ex["evaluation_status"] for ex in body["examples"]["valid"]}
    assert seen == {"completed", "failed"}


def test_both_enforcement_actions_appear_in_valid_examples() -> None:
    body = _body()
    seen = {ex["enforcement_action"] for ex in body["examples"]["valid"]}
    assert seen == {"allow", "deny"}


def test_gateway_local_failure_only_example_exists() -> None:
    body = _body()
    gateway_local_failures = [
        ex for ex in body["examples"]["valid"] if ex.get("gateway_failure_reason") is not None
    ]
    assert gateway_local_failures
    # Demonstrates enforcement_action independence: kernel succeeded (allow)
    # but the gateway itself failed and enforced deny.
    assert any(
        ex["evaluation_status"] == "completed"
        and ex["outcome"] == "allow"
        and ex["enforcement_action"] == "deny"
        for ex in gateway_local_failures
    )


def test_every_valid_example_references_audit_evidence() -> None:
    body = _body()
    for example in body["examples"]["valid"]:
        assert example.get("audit_evidence_id"), f"example missing audit_evidence_id: {example!r}"


# ---------------------------------------------------------------------------
# Policy provenance: bundle_id / bundle_version are independently optional
# ---------------------------------------------------------------------------


def test_bundle_id_present_without_bundle_version_is_not_rejected_by_this_contract() -> None:
    # Review finding: mirrors the same characterization test in
    # test_audit_evidence_contract.py. This contract's published
    # constraints do not couple bundle_id presence to bundle_version
    # presence (see gateway-audit-event.md, Section 23) — each is
    # independently optional/nullable. This test documents the ACTUAL,
    # currently-permissive behavior; a stricter pairing invariant would be
    # a validation-behavior change, out of scope for a documentation
    # review.
    body = _body()
    partial = _minimal_valid_event(bundle_id="baseline-read-only-telemetry")
    assert _is_valid_event(partial, body)


def test_bundle_version_present_without_bundle_id_is_not_rejected_by_this_contract() -> None:
    body = _body()
    partial = _minimal_valid_event(bundle_version="1.0.0")
    assert _is_valid_event(partial, body)


# ---------------------------------------------------------------------------
# Boundedness / security
# ---------------------------------------------------------------------------


def test_forbidden_fields_never_appear_as_published_fields() -> None:
    text = EVENT_FILE.read_text(encoding="utf-8")
    for field in FORBIDDEN_FIELDS:
        assert f"id: {field}\n" not in text, (
            f"forbidden field {field!r} appears as a published field"
        )


def test_no_redaction_classification_field_published() -> None:
    body = _body()
    allowed = set(body["required"]) | set(body["optional"])
    assert "redaction_classification" not in allowed


def test_no_cryptographic_signing_fields_published() -> None:
    text = EVENT_FILE.read_text(encoding="utf-8")
    for field in ("signature", "signature_algorithm", "hash_chain", "previous_hash", "merkle_root"):
        assert f"id: {field}\n" not in text


@pytest.mark.parametrize("field", ["enforcement_status", "enforcement_result"])
def test_no_enforcement_result_field_published(field: str) -> None:
    # Point 13 review finding: this contract records only the gateway's
    # selected enforcement_action, never a separate execution-result field.
    body = _body()
    allowed = set(body["required"]) | set(body["optional"])
    assert field not in allowed
    invalid = _minimal_valid_event(**{field: "success"})
    assert not _is_valid_event(invalid, body)


def test_no_second_gateway_correlation_id_field_published() -> None:
    body = _body()
    allowed = set(body["required"]) | set(body["optional"])
    assert "gateway_correlation_id" not in allowed
    assert "correlation_id" in allowed


# ---------------------------------------------------------------------------
# First-wave audit-event unchanged
# ---------------------------------------------------------------------------


def test_first_wave_audit_event_contract_remains_unchanged() -> None:
    assert FIRST_WAVE_AUDIT_EVENT_FILE.is_file()
    assert FIRST_WAVE_AUDIT_EVENT_DOC.is_file()

    first_wave = _load_yaml(FIRST_WAVE_AUDIT_EVENT_FILE)
    contract = first_wave["contract"]
    body = first_wave["audit_event"]

    assert contract["name"] == "audit-event"
    assert contract["version"] == "0.1.0"
    assert contract["lifecycle"] == "experimental"
    assert contract["depends_on"] == ["decision-request", "decision-response"]
    assert body["required"] == ["event_id", "event_type", "action", "timestamp"]
    assert body["additional_properties"] is False


def test_event_type_is_distinct_from_first_wave_audit_event_types() -> None:
    first_wave_body = _load_yaml(FIRST_WAVE_AUDIT_EVENT_FILE)["audit_event"]
    first_wave_event_types = set(first_wave_body["event_type_values"])
    assert not (set(_body()["event_type_values"]) & first_wave_event_types)


# ---------------------------------------------------------------------------
# Hardened primitive-type validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("field", ["event_id", "request_id", "audit_evidence_id"])
@pytest.mark.parametrize("bad_value", [123, True, 1.5, [], {}, None])
def test_identifier_fields_reject_non_string_types(field: str, bad_value: object) -> None:
    body = _body()
    event = _minimal_valid_event(**{field: bad_value})
    assert not _is_valid_event(event, body)


@pytest.mark.parametrize("bad_value", [1, True, [], {}, "ALLOW"])
def test_outcome_rejects_invalid_primitive_or_casing(bad_value: object) -> None:
    body = _body()
    event = _minimal_valid_event(outcome=bad_value)
    assert not _is_valid_event(event, body)


@pytest.mark.parametrize("bad_value", [1, True, [], {}, "ALLOW"])
def test_enforcement_action_rejects_invalid_primitive_or_casing(bad_value: object) -> None:
    body = _body()
    event = _minimal_valid_event(enforcement_action=bad_value)
    assert not _is_valid_event(event, body)


@pytest.mark.parametrize("bad_value", [1, True, [], {}, "GATEWAY_AUTHORIZATION"])
def test_event_type_rejects_invalid_primitive_or_casing(bad_value: object) -> None:
    body = _body()
    event = _minimal_valid_event(event_type=bad_value)
    assert not _is_valid_event(event, body)


def test_bool_is_not_silently_accepted_as_a_string_identifier() -> None:
    # bool is a subclass of int in Python; confirm it is never mistaken for
    # a valid non-empty string identifier.
    body = _body()
    event = _minimal_valid_event(event_id=True)
    assert not _is_valid_event(event, body)
    assert isinstance(True, int)  # documents the Python subtlety this guards against


@pytest.mark.parametrize(
    "bad_value", [123, True, 1.5, [], {}, "2026-05-22", "2026-05-22 14:30:00Z"]
)
def test_timestamp_rejects_non_string_or_malformed_value(bad_value: object) -> None:
    body = _body()
    event = _minimal_valid_event(timestamp=bad_value)
    assert not _is_valid_event(event, body)


@pytest.mark.parametrize("bad_value", [123, True, 1.5, [], {}, "unsupported_schema_version_typo"])
def test_failure_reason_rejects_invalid_primitive_or_unknown_value(bad_value: object) -> None:
    body = _body()
    event = _minimal_valid_event(evaluation_status="failed", outcome=None, failure_reason=bad_value)
    assert not _is_valid_event(event, body)


@pytest.mark.parametrize("bad_value", [123, True, 1.5, [], {}])
def test_correlation_id_rejects_non_string_non_null_types(bad_value: object) -> None:
    body = _body()
    event = _minimal_valid_event(correlation_id=bad_value)
    assert not _is_valid_event(event, body)


@pytest.mark.parametrize("bad_value", [123, True, 1.5, [], {}, ""])
def test_bundle_id_rejects_non_string_or_empty_values(bad_value: object) -> None:
    body = _body()
    event = _minimal_valid_event(bundle_id=bad_value)
    assert not _is_valid_event(event, body)


@pytest.mark.parametrize("bad_value", [123, True, 1.5, [], {}, "0.1"])
def test_bundle_version_rejects_non_string_or_non_semver(bad_value: object) -> None:
    body = _body()
    event = _minimal_valid_event(bundle_id="some-bundle", bundle_version=bad_value)
    assert not _is_valid_event(event, body)


@pytest.mark.parametrize("bad_value", [123, True, 1.5, [], {}, ""])
def test_trace_id_rejects_non_string_or_empty_values(bad_value: object) -> None:
    body = _body()
    event = _minimal_valid_event(trace_id=bad_value)
    assert not _is_valid_event(event, body)


@pytest.mark.parametrize("bad_value", [123, True, 1.5, [], {}, ""])
def test_gateway_id_rejects_non_string_or_empty_values(bad_value: object) -> None:
    body = _body()
    event = _minimal_valid_event(gateway_id=bad_value)
    assert not _is_valid_event(event, body)


@pytest.mark.parametrize("bad_value", [123, True, 1.5, [], {}, "ALLOW_RULE_MATCHED"])
def test_reason_code_rejects_invalid_primitive_or_casing(bad_value: object) -> None:
    body = _body()
    event = _minimal_valid_event(reason_code=bad_value)
    assert not _is_valid_event(event, body)


@pytest.mark.parametrize("bad_value", [123, True, 1.5, [], {}, ""])
def test_explanation_rejects_non_string_or_empty_values(bad_value: object) -> None:
    body = _body()
    event = _minimal_valid_event(explanation=bad_value)
    assert not _is_valid_event(event, body)


@pytest.mark.parametrize("bad_value", [123, True, 1.5, [], {}, "0.1"])
def test_schema_version_rejects_non_string_or_non_semver(bad_value: object) -> None:
    body = _body()
    event = _minimal_valid_event(schema_version=bad_value)
    assert not _is_valid_event(event, body)


# ---------------------------------------------------------------------------
# Repository tracking
# ---------------------------------------------------------------------------


def test_gateway_audit_event_is_not_in_first_wave_tuples() -> None:
    assert "gateway-audit-event" not in basis_schemas.PLANNED_CONTRACTS
    assert "gateway-audit-event" not in basis_schemas.PUBLISHED_CONTRACTS
