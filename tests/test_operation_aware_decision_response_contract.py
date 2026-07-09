"""Focused checks on the published operation-aware-decision-response contract.

These tests validate
``schemas/operation-aware-decision-response/operation-aware-decision-response.yaml``
(PR E of `basis-architecture`'s operation-aware schema readiness plan,
ADR-0005): its metadata, its declared dependencies, that its published field
policy accepts well-formed responses and rejects malformed ones, that
``outcome`` / ``evaluation_status`` / ``failure_reason`` observe the required
invariant (a failed evaluation never carries a non-null outcome), that an
embedded ``evaluation_trace`` stays consistent with the response's own
top-level fields, that the existing first-wave ``decision-response`` is
completely untouched by this PR, and that this contract never defines a raw-
secret, raw-request, or gateway-enforcement field.

This is a contract publication, not a parser: the only behavior exercised
here is applying the contract's own published rules to example response
objects.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import basis_schemas

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
RESPONSE_DIR = REPO_ROOT / "schemas" / "operation-aware-decision-response"
RESPONSE_FILE = RESPONSE_DIR / "operation-aware-decision-response.yaml"
FIRST_WAVE_RESPONSE_FILE = REPO_ROOT / "schemas" / "decision-response" / "decision-response.yaml"
FIRST_WAVE_RESPONSE_DOC = REPO_ROOT / "docs" / "decision-response.md"
TRACE_FILE = REPO_ROOT / "schemas" / "evaluation-trace" / "evaluation-trace.yaml"
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
    "full_request",
    "request_snapshot",
    "full_policy",
    "policy_document",
    "enforcement_result",
    "http_status",
    "response_status",
    "gateway_enforcement",
    "event_id",
    "event_type",
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
    return _load_yaml(RESPONSE_FILE)


def _body() -> dict:
    return _load()["operation_aware_decision_response"]


def _trace_body() -> dict:
    return _load_yaml(TRACE_FILE)["evaluation_trace"]


def _is_valid_trace_object(obj: object) -> bool:
    body = _trace_body()
    if not isinstance(obj, dict):
        return False
    allowed = set(body["required"]) | set(body["optional"])
    if set(obj) - allowed:
        return False
    if any(field not in obj for field in body["required"]):
        return False
    return True


def _is_valid_response(obj: object, body: dict) -> bool:
    if not isinstance(obj, dict):
        return False

    allowed = set(body["required"]) | set(body["optional"])
    if not body["additional_properties"] and set(obj) - allowed:
        return False
    if any(field not in obj for field in body["required"]):
        return False

    request_id = obj.get("request_id")
    if not isinstance(request_id, str) or not request_id.strip():
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

    reason_code = obj.get("reason_code")
    if reason_code is not None:
        if not isinstance(reason_code, str) or not re.match(
            body["reason_code_pattern"], reason_code
        ):
            return False

    evaluation_trace = obj.get("evaluation_trace")
    if evaluation_trace is not None:
        if not _is_valid_trace_object(evaluation_trace):
            return False
        # Cross-field consistency: response is authoritative; embedded trace
        # must agree, per docs/operation-aware-decision-response.md,
        # "Response/trace authority". Only fields duplicated between the two
        # contracts carry an equality requirement.
        if evaluation_trace.get("request_id") != request_id:
            return False
        if evaluation_trace.get("evaluation_status") != evaluation_status:
            return False
        if evaluation_trace.get("outcome") != outcome:
            return False
        if evaluation_trace.get("failure_reason") != failure_reason:
            return False
        correlation_id = obj.get("correlation_id")
        trace_correlation_id = evaluation_trace.get("correlation_id")
        if (
            correlation_id is not None
            and trace_correlation_id is not None
            and correlation_id != trace_correlation_id
        ):
            return False
        trace_reason_code = evaluation_trace.get("reason_code")
        if reason_code is not None and trace_reason_code is not None:
            if reason_code != trace_reason_code:
                return False
        trace_id = obj.get("trace_id")
        if trace_id is not None and evaluation_trace.get("trace_id") != trace_id:
            return False

    if "explanation" in obj and obj["explanation"] is not None:
        if not isinstance(obj["explanation"], str) or not obj["explanation"].strip():
            return False

    return True


# ---------------------------------------------------------------------------
# File / parsing
# ---------------------------------------------------------------------------


def test_response_file_exists() -> None:
    assert RESPONSE_FILE.is_file(), (
        "schemas/operation-aware-decision-response/"
        "operation-aware-decision-response.yaml must exist"
    )


def test_response_yaml_parses() -> None:
    assert _load()


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


def test_contract_metadata_matches_expected_values() -> None:
    contract = _load()["contract"]
    assert contract["name"] == "operation-aware-decision-response"
    assert contract["title"] == "BASIS Operation-Aware Decision Response"
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
        "evaluation-trace",
        "reason-code",
    ]


def test_is_tracked_in_operation_aware_response_trace_contracts() -> None:
    assert (
        basis_schemas.OPERATION_AWARE_RESPONSE_TRACE_CONTRACTS[2]
        == "operation-aware-decision-response"
    )


# ---------------------------------------------------------------------------
# Relationship to PR C request and first-wave decision-response
# ---------------------------------------------------------------------------


def test_declares_dependency_on_operation_aware_decision_request() -> None:
    assert "operation-aware-decision-request" in _load()["contract"]["depends_on"]


def test_first_wave_decision_response_contract_remains_unchanged() -> None:
    # Hermetic structural regression test: reproduces the first-wave
    # contract's own published surface directly from the YAML, rather than
    # diffing against a `main` git ref (which is not guaranteed to exist in
    # every checkout, e.g. a CI runner's shallow/branch-only clone). This
    # guards against an accidental edit without depending on git history;
    # tests/test_decision_response_contract.py remains the primary,
    # authoritative first-wave contract test — these are the specific
    # structural facts this PR must not have disturbed.
    assert FIRST_WAVE_RESPONSE_FILE.is_file()
    assert FIRST_WAVE_RESPONSE_DOC.is_file()

    first_wave = _load_yaml(FIRST_WAVE_RESPONSE_FILE)
    contract = first_wave["contract"]
    body = first_wave["decision_response"]

    assert contract["name"] == "decision-response"
    assert contract["title"] == "BASIS Decision Response"
    assert contract["version"] == "0.1.0"
    assert contract["lifecycle"] == "experimental"
    assert contract["governed_by"] == "basis-architecture"
    assert contract["published_by"] == "basis-schemas"
    assert contract["depends_on"] == ["decision-request"]

    assert body["required"] == ["request_id", "outcome", "reason", "evaluated_by", "timestamp"]
    assert body["optional"] == ["policy_version", "failure_reason"]
    assert body["additional_properties"] is False
    assert body["outcome_values"] == ["allow", "deny", "not_applicable"]
    assert body["failure_reason_values"] == [
        "malformed_request",
        "policy_error",
        "audit_error",
        "internal_error",
    ]

    assert len(body["examples"]["valid"]) == 4
    assert len(body["examples"]["invalid"]) == 10


def test_first_wave_response_still_has_its_own_outcome_and_failure_reason() -> None:
    # Sanity check that the first-wave contract's own vocabulary (a
    # different, four-value failure_reason set) still exists unmodified
    # alongside this PR's new, six-value evaluator-failure vocabulary.
    first_wave_body = _load_yaml(FIRST_WAVE_RESPONSE_FILE)["decision_response"]
    assert first_wave_body["failure_reason_values"] == [
        "malformed_request",
        "policy_error",
        "audit_error",
        "internal_error",
    ]
    assert first_wave_body["outcome_values"] == ["allow", "deny", "not_applicable"]


# ---------------------------------------------------------------------------
# Field policy
# ---------------------------------------------------------------------------


def test_required_and_optional_fields() -> None:
    body = _body()
    assert body["required"] == ["request_id", "evaluation_status", "outcome", "failure_reason"]
    assert set(body["optional"]) == {
        "correlation_id",
        "bundle_id",
        "bundle_version",
        "trace_id",
        "evaluation_trace",
        "reason_code",
        "explanation",
    }


def test_unknown_fields_are_rejected_by_policy() -> None:
    assert _body()["additional_properties"] is False


def test_outcome_values_match_evaluation_trace() -> None:
    assert _body()["outcome_values"] == _trace_body()["outcome_values"]


def test_evaluation_status_values_match_evaluation_trace() -> None:
    assert _body()["evaluation_status_values"] == _trace_body()["evaluation_status_values"]


def test_failure_reason_values_match_evaluation_trace() -> None:
    assert _body()["failure_reason_values"] == _trace_body()["failure_reason_values"]


# ---------------------------------------------------------------------------
# Outcome/failure invariants
# ---------------------------------------------------------------------------


def test_completed_allow_is_valid() -> None:
    body = _body()
    assert _is_valid_response(
        {
            "request_id": "r1",
            "evaluation_status": "completed",
            "outcome": "allow",
            "failure_reason": None,
        },
        body,
    )


def test_completed_deny_is_valid() -> None:
    body = _body()
    assert _is_valid_response(
        {
            "request_id": "r1",
            "evaluation_status": "completed",
            "outcome": "deny",
            "failure_reason": None,
        },
        body,
    )


def test_completed_not_applicable_is_valid() -> None:
    body = _body()
    assert _is_valid_response(
        {
            "request_id": "r1",
            "evaluation_status": "completed",
            "outcome": "not_applicable",
            "failure_reason": None,
        },
        body,
    )


def test_failed_allow_is_invalid() -> None:
    body = _body()
    assert not _is_valid_response(
        {
            "request_id": "r1",
            "evaluation_status": "failed",
            "outcome": "allow",
            "failure_reason": "internal_evaluation_error",
        },
        body,
    )


def test_failed_deny_is_invalid() -> None:
    body = _body()
    assert not _is_valid_response(
        {
            "request_id": "r1",
            "evaluation_status": "failed",
            "outcome": "deny",
            "failure_reason": "internal_evaluation_error",
        },
        body,
    )


def test_failed_not_applicable_is_invalid() -> None:
    body = _body()
    assert not _is_valid_response(
        {
            "request_id": "r1",
            "evaluation_status": "failed",
            "outcome": "not_applicable",
            "failure_reason": "internal_evaluation_error",
        },
        body,
    )


def test_failed_no_outcome_is_valid_and_required() -> None:
    body = _body()
    assert _is_valid_response(
        {
            "request_id": "r1",
            "evaluation_status": "failed",
            "outcome": None,
            "failure_reason": "internal_evaluation_error",
        },
        body,
    )


def test_failed_without_failure_reason_is_invalid() -> None:
    body = _body()
    assert not _is_valid_response(
        {
            "request_id": "r1",
            "evaluation_status": "failed",
            "outcome": None,
            "failure_reason": None,
        },
        body,
    )


def test_completed_with_failure_reason_is_invalid() -> None:
    body = _body()
    assert not _is_valid_response(
        {
            "request_id": "r1",
            "evaluation_status": "completed",
            "outcome": "allow",
            "failure_reason": "internal_evaluation_error",
        },
        body,
    )


# ---------------------------------------------------------------------------
# Trace relationship / response-trace consistency
# ---------------------------------------------------------------------------


def test_embedded_trace_must_agree_on_request_id() -> None:
    body = _body()
    mismatched = {
        "request_id": "r1",
        "evaluation_status": "completed",
        "outcome": "allow",
        "failure_reason": None,
        "evaluation_trace": {
            "trace_id": "trace-1",
            "request_id": "DIFFERENT",
            "evaluation_status": "completed",
            "outcome": "allow",
            "bundle_applicability": "applicable",
            "rule_evidence": [],
        },
    }
    assert not _is_valid_response(mismatched, body)


def test_embedded_trace_must_agree_on_outcome() -> None:
    body = _body()
    mismatched = {
        "request_id": "r1",
        "evaluation_status": "completed",
        "outcome": "allow",
        "failure_reason": None,
        "evaluation_trace": {
            "trace_id": "trace-1",
            "request_id": "r1",
            "evaluation_status": "completed",
            "outcome": "deny",
            "bundle_applicability": "applicable",
            "rule_evidence": [],
        },
    }
    assert not _is_valid_response(mismatched, body)


def test_trace_id_must_agree_with_embedded_trace_trace_id() -> None:
    body = _body()
    mismatched = {
        "request_id": "r1",
        "evaluation_status": "completed",
        "outcome": "allow",
        "failure_reason": None,
        "trace_id": "trace-1",
        "evaluation_trace": {
            "trace_id": "trace-2",
            "request_id": "r1",
            "evaluation_status": "completed",
            "outcome": "allow",
            "bundle_applicability": "applicable",
            "rule_evidence": [],
        },
    }
    assert not _is_valid_response(mismatched, body)


def test_consistent_embedded_trace_is_valid() -> None:
    body = _body()
    consistent = {
        "request_id": "r1",
        "evaluation_status": "completed",
        "outcome": "allow",
        "failure_reason": None,
        "trace_id": "trace-1",
        "evaluation_trace": {
            "trace_id": "trace-1",
            "request_id": "r1",
            "evaluation_status": "completed",
            "outcome": "allow",
            "bundle_applicability": "applicable",
            "rule_evidence": [],
        },
    }
    assert _is_valid_response(consistent, body)


def test_embedded_trace_must_agree_on_failure_reason() -> None:
    body = _body()
    mismatched = {
        "request_id": "r1",
        "evaluation_status": "failed",
        "outcome": None,
        "failure_reason": "internal_evaluation_error",
        "evaluation_trace": {
            "trace_id": "trace-1",
            "request_id": "r1",
            "evaluation_status": "failed",
            "outcome": None,
            "bundle_applicability": None,
            "failure_reason": "unsupported_schema_version",
            "rule_evidence": [],
        },
    }
    assert not _is_valid_response(mismatched, body)


def test_embedded_trace_correlation_id_mismatch_is_invalid() -> None:
    body = _body()
    mismatched = {
        "request_id": "r1",
        "correlation_id": "corr-1",
        "evaluation_status": "completed",
        "outcome": "allow",
        "failure_reason": None,
        "evaluation_trace": {
            "trace_id": "trace-1",
            "request_id": "r1",
            "correlation_id": "corr-DIFFERENT",
            "evaluation_status": "completed",
            "outcome": "allow",
            "bundle_applicability": "applicable",
            "rule_evidence": [],
        },
    }
    assert not _is_valid_response(mismatched, body)


def test_embedded_trace_correlation_id_one_sided_is_not_enforced() -> None:
    # Only enforced when both response and embedded trace carry a
    # correlation_id; a one-sided value is not a mismatch.
    body = _body()
    one_sided = {
        "request_id": "r1",
        "correlation_id": "corr-1",
        "evaluation_status": "completed",
        "outcome": "allow",
        "failure_reason": None,
        "evaluation_trace": {
            "trace_id": "trace-1",
            "request_id": "r1",
            "evaluation_status": "completed",
            "outcome": "allow",
            "bundle_applicability": "applicable",
            "rule_evidence": [],
        },
    }
    assert _is_valid_response(one_sided, body)


def test_embedded_trace_reason_code_mismatch_is_invalid() -> None:
    body = _body()
    mismatched = {
        "request_id": "r1",
        "evaluation_status": "completed",
        "outcome": "allow",
        "failure_reason": None,
        "reason_code": "allow_rule_matched",
        "evaluation_trace": {
            "trace_id": "trace-1",
            "request_id": "r1",
            "evaluation_status": "completed",
            "outcome": "allow",
            "bundle_applicability": "applicable",
            "rule_evidence": [],
            "reason_code": "no_applicable_bundle",
        },
    }
    assert not _is_valid_response(mismatched, body)


def test_embedded_trace_reason_code_one_sided_is_not_enforced() -> None:
    # Only enforced when both response and embedded trace carry a
    # non-null reason_code.
    body = _body()
    one_sided = {
        "request_id": "r1",
        "evaluation_status": "completed",
        "outcome": "allow",
        "failure_reason": None,
        "reason_code": "allow_rule_matched",
        "evaluation_trace": {
            "trace_id": "trace-1",
            "request_id": "r1",
            "evaluation_status": "completed",
            "outcome": "allow",
            "bundle_applicability": "applicable",
            "rule_evidence": [],
        },
    }
    assert _is_valid_response(one_sided, body)


# ---------------------------------------------------------------------------
# Examples
# ---------------------------------------------------------------------------


def test_required_valid_examples_accepted() -> None:
    body = _body()
    for example in body["examples"]["valid"]:
        assert _is_valid_response(example, body), f"valid example rejected: {example!r}"


def test_required_invalid_examples_rejected() -> None:
    body = _body()
    for case in body["examples"]["invalid"]:
        assert "reason" in case, f"invalid example missing a reason: {case!r}"
        assert not _is_valid_response(case["value"], body), (
            f"invalid example accepted ({case['reason']}): {case['value']!r}"
        )


def test_invalid_examples_cover_required_cases() -> None:
    reasons = " ".join(case["reason"] for case in _body()["examples"]["invalid"]).lower()
    assert "missing required request id" in reasons
    assert "invalid outcome" in reasons
    assert "malformed evaluation_status" in reasons
    assert "failed evaluation represented as allow" in reasons
    assert "malformed reason code" in reasons
    assert "malformed bundle provenance" in reasons
    assert "malformed embedded trace" in reasons
    assert "response/trace request-id mismatch" in reasons
    assert "unknown field" in reasons
    assert "raw evidence field" in reasons
    assert "gateway enforcement field" in reasons
    assert "response/trace correlation_id mismatch" in reasons
    assert "response/trace failure_reason mismatch" in reasons
    assert "response/trace reason_code mismatch" in reasons


def test_every_outcome_value_appears_in_a_valid_example() -> None:
    body = _body()
    seen = {ex["outcome"] for ex in body["examples"]["valid"] if ex["outcome"] is not None}
    assert set(body["outcome_values"]) <= seen


def test_both_evaluation_statuses_appear_in_valid_examples() -> None:
    body = _body()
    seen = {ex["evaluation_status"] for ex in body["examples"]["valid"]}
    assert seen == {"completed", "failed"}


def test_minimal_valid_example_has_only_required_keys() -> None:
    body = _body()
    minimal = [ex for ex in body["examples"]["valid"] if set(ex) == set(body["required"])]
    assert minimal, "expected at least one example using only the four required keys"


# ---------------------------------------------------------------------------
# Boundedness / security
# ---------------------------------------------------------------------------


def test_forbidden_fields_never_appear_as_published_fields() -> None:
    text = RESPONSE_FILE.read_text(encoding="utf-8")
    for field in FORBIDDEN_FIELDS:
        assert f"id: {field}\n" not in text, (
            f"forbidden field {field!r} appears as a published field"
        )


def test_no_redaction_classification_field_published() -> None:
    body = _body()
    allowed = set(body["required"]) | set(body["optional"])
    assert "redaction_classification" not in allowed


# ---------------------------------------------------------------------------
# Hardened primitive-type validation
# ---------------------------------------------------------------------------


def _minimal_valid_response() -> dict:
    return {
        "request_id": "req-x",
        "evaluation_status": "completed",
        "outcome": "allow",
        "failure_reason": None,
    }


@pytest.mark.parametrize("bad_value", [123, True, 1.5, [], {}, None])
def test_request_id_rejects_non_string_types(bad_value: object) -> None:
    body = _body()
    response = _minimal_valid_response()
    response["request_id"] = bad_value
    assert not _is_valid_response(response, body)


@pytest.mark.parametrize("bad_value", [1, True, [], {}, "ALLOW"])
def test_outcome_rejects_invalid_primitive_or_casing(bad_value: object) -> None:
    body = _body()
    response = _minimal_valid_response()
    response["outcome"] = bad_value
    assert not _is_valid_response(response, body)


@pytest.mark.parametrize("bad_value", [1, True, [], {}, "COMPLETED"])
def test_evaluation_status_rejects_invalid_primitive_or_casing(bad_value: object) -> None:
    body = _body()
    response = _minimal_valid_response()
    response["evaluation_status"] = bad_value
    assert not _is_valid_response(response, body)


@pytest.mark.parametrize("bad_value", [1, True, [], {}, "INTERNAL_EVALUATION_ERROR"])
def test_failure_reason_rejects_invalid_primitive_or_casing(bad_value: object) -> None:
    body = _body()
    response = _minimal_valid_response()
    response["evaluation_status"] = "failed"
    response["outcome"] = None
    response["failure_reason"] = bad_value
    assert not _is_valid_response(response, body)


@pytest.mark.parametrize("bad_value", [123, True, 1.5, [], {}])
def test_bundle_id_rejects_non_string_types(bad_value: object) -> None:
    body = _body()
    response = _minimal_valid_response()
    response["bundle_id"] = bad_value
    assert not _is_valid_response(response, body)


@pytest.mark.parametrize("bad_value", [123, True, [], {}, "1.0"])
def test_bundle_version_rejects_non_semver_or_non_string_types(bad_value: object) -> None:
    body = _body()
    response = _minimal_valid_response()
    response["bundle_id"] = "some-bundle"
    response["bundle_version"] = bad_value
    assert not _is_valid_response(response, body)


@pytest.mark.parametrize("bad_value", [123, True, 1.5, [], {}])
def test_trace_id_rejects_non_string_types(bad_value: object) -> None:
    body = _body()
    response = _minimal_valid_response()
    response["trace_id"] = bad_value
    assert not _is_valid_response(response, body)


@pytest.mark.parametrize("bad_value", [123, True, [], {}, "ALLOW_RULE_MATCHED"])
def test_reason_code_rejects_invalid_primitive_or_casing(bad_value: object) -> None:
    body = _body()
    response = _minimal_valid_response()
    response["reason_code"] = bad_value
    assert not _is_valid_response(response, body)


@pytest.mark.parametrize("bad_value", ["not-an-object", 123, True, []])
def test_evaluation_trace_rejects_non_object_types(bad_value: object) -> None:
    body = _body()
    response = _minimal_valid_response()
    response["evaluation_trace"] = bad_value
    assert not _is_valid_response(response, body)


def test_bool_is_not_silently_accepted_as_a_string_identifier() -> None:
    # bool is a subclass of int in Python; confirm it is never mistaken for
    # a valid non-empty string identifier.
    body = _body()
    response = _minimal_valid_response()
    response["request_id"] = True
    assert not _is_valid_response(response, body)
    assert isinstance(True, int)  # documents the Python subtlety this guards against
