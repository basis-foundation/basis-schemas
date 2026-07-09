"""Focused checks on the published evaluation-trace contract.

These tests validate ``schemas/evaluation-trace/evaluation-trace.yaml`` (PR E
of `basis-architecture`'s operation-aware schema readiness plan, ADR-0005):
its metadata, its declared dependencies, that its published field policy
accepts well-formed traces and rejects malformed ones, that ``outcome`` /
``evaluation_status`` / ``failure_reason`` observe the required invariant (a
failed evaluation never carries a non-null outcome), that
``bundle_id``/``bundle_version`` stay in parity with ``policy-bundle``, that
nested ``rule_evidence`` entries stay in parity with ``trace-rule-evidence``,
and that this contract never defines a raw-secret, raw-request, or
gateway-enforcement field.

This is a contract publication, not a parser: the only behavior exercised
here is applying the contract's own published rules to example trace
objects.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import basis_schemas

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
TRACE_DIR = REPO_ROOT / "schemas" / "evaluation-trace"
TRACE_FILE = TRACE_DIR / "evaluation-trace.yaml"
EVIDENCE_FILE = REPO_ROOT / "schemas" / "trace-rule-evidence" / "trace-rule-evidence.yaml"
POLICY_BUNDLE_FILE = REPO_ROOT / "schemas" / "policy-bundle" / "policy-bundle.yaml"
REASON_CODE_FILE = REPO_ROOT / "schemas" / "reason-code" / "reason-code.yaml"

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
    "gateway_enforcement",
    "enforcement_result",
    "http_status",
    "response_status",
    "class_name",
    "module_name",
    "source_file",
    "line_number",
    "implementation_detail",
    "internal_error_detail",
)


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict), f"{path} must parse to a mapping"
    return data


def _load() -> dict:
    return _load_yaml(TRACE_FILE)


def _body() -> dict:
    return _load()["evaluation_trace"]


def _evidence_body() -> dict:
    return _load_yaml(EVIDENCE_FILE)["trace_rule_evidence"]


def _is_valid_rule_evidence(obj: object) -> bool:
    body = _evidence_body()
    if not isinstance(obj, dict):
        return False
    allowed = set(body["required"]) | set(body["optional"])
    if not body["additional_properties"] and set(obj) - allowed:
        return False
    if any(field not in obj for field in body["required"]):
        return False
    if not isinstance(obj.get("rule_id"), str) or not obj["rule_id"].strip():
        return False
    if obj.get("effect") not in body["effect_values"]:
        return False
    if obj.get("rule_result") not in body["rule_result_values"]:
        return False
    return True


def _is_valid_trace(obj: object, body: dict) -> bool:
    if not isinstance(obj, dict):
        return False

    allowed = set(body["required"]) | set(body["optional"])
    if not body["additional_properties"] and set(obj) - allowed:
        return False
    if any(field not in obj for field in body["required"]):
        return False

    for field in ("trace_id", "request_id"):
        value = obj.get(field)
        if not isinstance(value, str) or not value.strip():
            return False

    evaluation_status = obj.get("evaluation_status")
    if evaluation_status not in body["evaluation_status_values"]:
        return False

    outcome = obj.get("outcome")
    if evaluation_status == "completed":
        if outcome not in body["outcome_values"]:
            return False
    else:  # failed
        if outcome is not None:
            return False

    failure_reason = obj.get("failure_reason")
    if evaluation_status == "completed":
        if failure_reason is not None:
            return False
    else:  # failed
        if failure_reason not in body["failure_reason_values"]:
            return False

    bundle_applicability = obj.get("bundle_applicability")
    if (
        bundle_applicability not in body["bundle_applicability_values"]
        and bundle_applicability is not None
    ):
        return False

    # Outcome and bundle_applicability must agree when evaluation_status is
    # completed: not_applicable <-> not_applicable; allow/deny <-> applicable.
    if evaluation_status == "completed":
        if outcome == "not_applicable" and bundle_applicability != "not_applicable":
            return False
        if outcome in ("allow", "deny") and bundle_applicability != "applicable":
            return False

    if "bundle_id" in obj and obj["bundle_id"] is not None:
        if not isinstance(obj["bundle_id"], str) or not obj["bundle_id"].strip():
            return False

    if "bundle_version" in obj and obj["bundle_version"] is not None:
        if not isinstance(obj["bundle_version"], str) or not re.match(
            body["bundle_version_pattern"], obj["bundle_version"]
        ):
            return False

    rule_evidence = obj.get("rule_evidence")
    if not isinstance(rule_evidence, list):
        return False
    # A not_applicable bundle never has candidate rules to report.
    if bundle_applicability == "not_applicable" and rule_evidence:
        return False
    seen_rule_ids = []
    any_rule_error = False
    for entry in rule_evidence:
        if not _is_valid_rule_evidence(entry):
            return False
        seen_rule_ids.append(entry["rule_id"])
        if entry.get("rule_result") == "error":
            any_rule_error = True
    if len(seen_rule_ids) != len(set(seen_rule_ids)):
        return False
    # A rule-evaluation error can never coexist with a completed decision.
    if any_rule_error and evaluation_status != "failed":
        return False

    if "reason_code" in obj and obj["reason_code"] is not None:
        if not isinstance(obj["reason_code"], str) or not re.match(
            body["reason_code_pattern"], obj["reason_code"]
        ):
            return False

    if "explanation" in obj and obj["explanation"] is not None:
        if not isinstance(obj["explanation"], str) or not obj["explanation"].strip():
            return False

    return True


# ---------------------------------------------------------------------------
# File / parsing
# ---------------------------------------------------------------------------


def test_evaluation_trace_file_exists() -> None:
    assert TRACE_FILE.is_file(), "schemas/evaluation-trace/evaluation-trace.yaml must exist"


def test_evaluation_trace_yaml_parses() -> None:
    assert _load()


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


def test_contract_metadata_matches_expected_values() -> None:
    contract = _load()["contract"]
    assert contract["name"] == "evaluation-trace"
    assert contract["title"] == "BASIS Evaluation Trace"
    assert contract["version"] == "0.1.0"
    assert contract["governed_by"] == "basis-architecture"
    assert contract["published_by"] == "basis-schemas"


def test_lifecycle_is_experimental() -> None:
    assert _load()["contract"]["lifecycle"] == "experimental"


def test_declares_expected_dependencies() -> None:
    assert _load()["contract"]["depends_on"] == [
        "contract-metadata",
        "operation-aware-decision-request",
        "policy-bundle",
        "trace-rule-evidence",
        "reason-code",
    ]


def test_is_tracked_in_operation_aware_response_trace_contracts() -> None:
    assert basis_schemas.OPERATION_AWARE_RESPONSE_TRACE_CONTRACTS[1] == "evaluation-trace"


# ---------------------------------------------------------------------------
# Field policy
# ---------------------------------------------------------------------------


def test_required_and_optional_fields() -> None:
    body = _body()
    assert body["required"] == [
        "trace_id",
        "request_id",
        "evaluation_status",
        "outcome",
        "bundle_applicability",
        "rule_evidence",
    ]
    assert set(body["optional"]) == {
        "correlation_id",
        "bundle_id",
        "bundle_version",
        "failure_reason",
        "reason_code",
        "explanation",
    }


def test_unknown_fields_are_rejected_by_policy() -> None:
    assert _body()["additional_properties"] is False


def test_outcome_values_match_decision_response_vocabulary() -> None:
    assert _body()["outcome_values"] == ["allow", "deny", "not_applicable"]


def test_evaluation_status_values() -> None:
    assert _body()["evaluation_status_values"] == ["completed", "failed"]


def test_bundle_applicability_values() -> None:
    assert _body()["bundle_applicability_values"] == ["applicable", "not_applicable"]


def test_failure_reason_values_are_the_new_six_value_vocabulary() -> None:
    assert _body()["failure_reason_values"] == [
        "invalid_request",
        "unsupported_schema_version",
        "invalid_policy_bundle",
        "policy_validation_failure",
        "condition_evaluation_error",
        "internal_evaluation_error",
    ]


def test_failure_reason_values_are_distinct_from_first_wave_decision_response() -> None:
    first_wave_values = {"malformed_request", "policy_error", "audit_error", "internal_error"}
    assert not (set(_body()["failure_reason_values"]) & first_wave_values)


# ---------------------------------------------------------------------------
# Parity with policy-bundle, trace-rule-evidence, and reason-code
# ---------------------------------------------------------------------------


def test_bundle_version_pattern_matches_policy_bundle_source() -> None:
    bundle_body = _load_yaml(POLICY_BUNDLE_FILE)["policy_bundle"]
    assert _body()["bundle_version_pattern"] == bundle_body["fields"][1]["pattern"]


def test_reason_code_pattern_matches_source_contract() -> None:
    reason_code_body = _load_yaml(REASON_CODE_FILE)["reason_code"]
    assert _body()["reason_code_pattern"] == reason_code_body["pattern"]


# ---------------------------------------------------------------------------
# Required invariant: outcome null iff evaluation_status is failed
# ---------------------------------------------------------------------------


def test_failed_evaluation_can_never_be_allow() -> None:
    body = _body()
    invalid = {
        "trace_id": "trace-x",
        "request_id": "req-x",
        "evaluation_status": "failed",
        "outcome": "allow",
        "bundle_applicability": None,
        "failure_reason": "internal_evaluation_error",
        "rule_evidence": [],
    }
    assert not _is_valid_trace(invalid, body)


def test_failed_evaluation_requires_null_outcome() -> None:
    body = _body()
    valid = {
        "trace_id": "trace-x",
        "request_id": "req-x",
        "evaluation_status": "failed",
        "outcome": None,
        "bundle_applicability": None,
        "failure_reason": "internal_evaluation_error",
        "rule_evidence": [],
    }
    assert _is_valid_trace(valid, body)


def test_completed_evaluation_requires_null_failure_reason() -> None:
    body = _body()
    invalid = {
        "trace_id": "trace-x",
        "request_id": "req-x",
        "evaluation_status": "completed",
        "outcome": "allow",
        "bundle_applicability": "applicable",
        "failure_reason": "internal_evaluation_error",
        "rule_evidence": [],
    }
    assert not _is_valid_trace(invalid, body)


def test_completed_evaluation_requires_non_null_outcome() -> None:
    body = _body()
    invalid = {
        "trace_id": "trace-x",
        "request_id": "req-x",
        "evaluation_status": "completed",
        "outcome": None,
        "bundle_applicability": "applicable",
        "rule_evidence": [],
    }
    assert not _is_valid_trace(invalid, body)


# ---------------------------------------------------------------------------
# Rule-evaluation error propagation (evaluation_status must be failed)
# ---------------------------------------------------------------------------


def _trace_with_rule_result(rule_result: str, evaluation_status: str = "completed") -> dict:
    return {
        "trace_id": "trace-x",
        "request_id": "req-x",
        "evaluation_status": evaluation_status,
        "outcome": "deny" if evaluation_status == "completed" else None,
        "bundle_applicability": "applicable",
        "failure_reason": "condition_evaluation_error" if evaluation_status == "failed" else None,
        "rule_evidence": [{"rule_id": "rule-x", "effect": "deny", "rule_result": rule_result}],
    }


def test_rule_result_error_with_completed_status_is_invalid() -> None:
    body = _body()
    assert not _is_valid_trace(_trace_with_rule_result("error", "completed"), body)


def test_rule_result_error_with_failed_status_is_valid() -> None:
    body = _body()
    assert _is_valid_trace(_trace_with_rule_result("error", "failed"), body)


def test_rule_result_matched_with_completed_status_is_valid() -> None:
    body = _body()
    assert _is_valid_trace(_trace_with_rule_result("matched", "completed"), body)


def test_rule_result_skipped_does_not_force_failure() -> None:
    body = _body()
    assert _is_valid_trace(_trace_with_rule_result("skipped", "completed"), body)


# ---------------------------------------------------------------------------
# Outcome / bundle_applicability agreement (completed evaluations only)
# ---------------------------------------------------------------------------


def test_completed_not_applicable_requires_bundle_not_applicable() -> None:
    body = _body()
    invalid = {
        "trace_id": "trace-x",
        "request_id": "req-x",
        "evaluation_status": "completed",
        "outcome": "not_applicable",
        "bundle_applicability": "applicable",
        "rule_evidence": [],
    }
    assert not _is_valid_trace(invalid, body)


def test_completed_allow_requires_bundle_applicable() -> None:
    body = _body()
    invalid = {
        "trace_id": "trace-x",
        "request_id": "req-x",
        "evaluation_status": "completed",
        "outcome": "allow",
        "bundle_applicability": "not_applicable",
        "rule_evidence": [],
    }
    assert not _is_valid_trace(invalid, body)


def test_completed_deny_requires_bundle_applicable() -> None:
    body = _body()
    invalid = {
        "trace_id": "trace-x",
        "request_id": "req-x",
        "evaluation_status": "completed",
        "outcome": "deny",
        "bundle_applicability": "not_applicable",
        "rule_evidence": [],
    }
    assert not _is_valid_trace(invalid, body)


def test_not_applicable_bundle_requires_empty_rule_evidence() -> None:
    body = _body()
    invalid = {
        "trace_id": "trace-x",
        "request_id": "req-x",
        "evaluation_status": "completed",
        "outcome": "not_applicable",
        "bundle_applicability": "not_applicable",
        "rule_evidence": [{"rule_id": "rule-x", "effect": "allow", "rule_result": "skipped"}],
    }
    assert not _is_valid_trace(invalid, body)


def test_failed_evaluation_is_exempt_from_outcome_bundle_applicability_agreement() -> None:
    # Failure may occur before applicability is determined (null) or after
    # an already-applicable bundle was identified; neither is constrained
    # the way completed evaluations are.
    body = _body()
    for bundle_applicability in ("applicable", "not_applicable", None):
        trace = {
            "trace_id": "trace-x",
            "request_id": "req-x",
            "evaluation_status": "failed",
            "outcome": None,
            "bundle_applicability": bundle_applicability,
            "failure_reason": "internal_evaluation_error",
            "rule_evidence": [],
        }
        assert _is_valid_trace(trace, body), f"unexpectedly rejected: {bundle_applicability!r}"


# ---------------------------------------------------------------------------
# Examples
# ---------------------------------------------------------------------------


def test_required_valid_examples_accepted() -> None:
    body = _body()
    for example in body["examples"]["valid"]:
        assert _is_valid_trace(example, body), f"valid example rejected: {example!r}"


def test_required_invalid_examples_rejected() -> None:
    body = _body()
    for case in body["examples"]["invalid"]:
        assert "reason" in case, f"invalid example missing a reason: {case!r}"
        assert not _is_valid_trace(case["value"], body), (
            f"invalid example accepted ({case['reason']}): {case['value']!r}"
        )


def test_invalid_examples_cover_required_cases() -> None:
    reasons = " ".join(case["reason"] for case in _body()["examples"]["invalid"]).lower()
    assert "missing required trace id" in reasons
    assert "missing required request id" in reasons
    assert "invalid outcome" in reasons
    assert "malformed evaluation_status" in reasons
    assert "failed evaluation represented as allow" in reasons
    assert "non-null failure_reason" in reasons
    assert "invalid bundle_version" in reasons
    assert "malformed rule evidence" in reasons
    assert "duplicate rule ids" in reasons
    assert "unknown field" in reasons
    assert "raw request snapshot" in reasons
    assert "stack trace" in reasons


def test_every_outcome_value_appears_in_a_valid_example() -> None:
    body = _body()
    seen = {ex["outcome"] for ex in body["examples"]["valid"] if ex["outcome"] is not None}
    assert set(body["outcome_values"]) <= seen


def test_both_evaluation_statuses_appear_in_valid_examples() -> None:
    body = _body()
    seen = {ex["evaluation_status"] for ex in body["examples"]["valid"]}
    assert seen == {"completed", "failed"}


def test_empty_rule_evidence_is_valid_for_not_applicable() -> None:
    body = _body()
    not_applicable_examples = [
        ex for ex in body["examples"]["valid"] if ex["outcome"] == "not_applicable"
    ]
    assert not_applicable_examples
    assert all(ex["rule_evidence"] == [] for ex in not_applicable_examples)


def test_bundle_applicability_may_remain_applicable_under_failure() -> None:
    # Demonstrates the documented model: a failure occurring inside an
    # already-applicable bundle need not null out bundle_applicability.
    body = _body()
    failed_examples = [
        ex for ex in body["examples"]["valid"] if ex["evaluation_status"] == "failed"
    ]
    assert any(ex["bundle_applicability"] == "applicable" for ex in failed_examples)
    assert any(ex["bundle_applicability"] is None for ex in failed_examples)


# ---------------------------------------------------------------------------
# Boundedness / security
# ---------------------------------------------------------------------------


def test_forbidden_fields_never_appear_as_published_fields() -> None:
    text = TRACE_FILE.read_text(encoding="utf-8")
    for field in FORBIDDEN_FIELDS:
        assert f"id: {field}\n" not in text, (
            f"forbidden field {field!r} appears as a published field"
        )


def test_trace_ordering_documents_no_authorization_precedence() -> None:
    ordering = _body()["trace_ordering"]
    assert ordering["authorization_precedence"] == "not_defined_by_this_contract"


def test_no_redaction_classification_field_published() -> None:
    # Every value this contract carries is already a safe identifier, a
    # closed vocabulary member, or a reason code — see
    # docs/evaluation-trace.md, "Redaction".
    body = _body()
    allowed = set(body["required"]) | set(body["optional"])
    assert "redaction_classification" not in allowed


# ---------------------------------------------------------------------------
# Hardened primitive-type validation
# ---------------------------------------------------------------------------


def _minimal_valid_trace() -> dict:
    return {
        "trace_id": "trace-x",
        "request_id": "req-x",
        "evaluation_status": "completed",
        "outcome": "allow",
        "bundle_applicability": "applicable",
        "rule_evidence": [],
    }


@pytest.mark.parametrize("field", ["trace_id", "request_id"])
@pytest.mark.parametrize("bad_value", [123, True, 1.5, [], {}, None])
def test_identifier_fields_reject_non_string_types(field: str, bad_value: object) -> None:
    body = _body()
    trace = _minimal_valid_trace()
    trace[field] = bad_value
    assert not _is_valid_trace(trace, body)


@pytest.mark.parametrize("bad_value", [1, True, [], {}, "ALLOW"])
def test_outcome_rejects_invalid_primitive_or_casing(bad_value: object) -> None:
    body = _body()
    trace = _minimal_valid_trace()
    trace["outcome"] = bad_value
    assert not _is_valid_trace(trace, body)


@pytest.mark.parametrize("bad_value", [1, True, [], {}, "COMPLETED"])
def test_evaluation_status_rejects_invalid_primitive_or_casing(bad_value: object) -> None:
    body = _body()
    trace = _minimal_valid_trace()
    trace["evaluation_status"] = bad_value
    assert not _is_valid_trace(trace, body)


@pytest.mark.parametrize("bad_value", ["not-a-list", 1, {}, None])
def test_rule_evidence_rejects_non_array_types(bad_value: object) -> None:
    body = _body()
    trace = _minimal_valid_trace()
    trace["rule_evidence"] = bad_value
    assert not _is_valid_trace(trace, body)


@pytest.mark.parametrize("bad_value", [123, True, 1.5, [], {}])
def test_bundle_id_rejects_non_string_types(bad_value: object) -> None:
    body = _body()
    trace = _minimal_valid_trace()
    trace["bundle_id"] = bad_value
    assert not _is_valid_trace(trace, body)


@pytest.mark.parametrize("bad_value", [123, True, [], {}, "1.0"])
def test_bundle_version_rejects_non_semver_or_non_string_types(bad_value: object) -> None:
    body = _body()
    trace = _minimal_valid_trace()
    trace["bundle_id"] = "some-bundle"
    trace["bundle_version"] = bad_value
    assert not _is_valid_trace(trace, body)


def test_bool_is_not_silently_accepted_as_a_string_identifier() -> None:
    # bool is a subclass of int in Python; confirm it is never mistaken for
    # a valid non-empty string identifier.
    body = _body()
    trace = _minimal_valid_trace()
    trace["trace_id"] = True
    assert not _is_valid_trace(trace, body)
    assert isinstance(True, int)  # documents the Python subtlety this guards against
