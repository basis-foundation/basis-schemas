"""Focused checks on the published trace-rule-evidence contract.

These tests validate ``schemas/trace-rule-evidence/trace-rule-evidence.yaml``
(PR E of `basis-architecture`'s operation-aware schema readiness plan,
ADR-0005): its metadata, its declared dependencies, that its published field
policy accepts well-formed rule-evidence records and rejects malformed ones,
that ``rule_id``/``effect`` stay in parity with ``policy-rule``, that
condition-level evidence stays bounded (no ``field_path``/``operator``/
``expected_value``), and that this contract never defines a raw-secret,
raw-request, or debug/exception field.

This is a contract publication, not a parser: the only behavior exercised
here is applying the contract's own published rules to example rule-evidence
objects.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import basis_schemas

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = REPO_ROOT / "schemas" / "trace-rule-evidence"
EVIDENCE_FILE = EVIDENCE_DIR / "trace-rule-evidence.yaml"
POLICY_RULE_FILE = REPO_ROOT / "schemas" / "policy-rule" / "policy-rule.yaml"
REASON_CODE_FILE = REPO_ROOT / "schemas" / "reason-code" / "reason-code.yaml"

#: Fields that must never appear on this contract — raw secrets, raw
#: request/policy data, or debug/exception artifacts.
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
    "debug",
    "exception",
    "stack_trace",
    "traceback",
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
    return _load_yaml(EVIDENCE_FILE)


def _body() -> dict:
    return _load()["trace_rule_evidence"]


def _is_valid_condition_result(obj: object, body: dict) -> bool:
    if not isinstance(obj, dict):
        return False
    shape = body["condition_result_shape"]
    allowed = set(shape["required"]) | set(shape["optional"])
    if set(obj) - allowed:
        return False
    if any(field not in obj for field in shape["required"]):
        return False
    condition_id = obj.get("condition_id")
    if not isinstance(condition_id, str) or not condition_id.strip():
        return False
    if obj.get("result") not in body["condition_result_values"]:
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


def _is_valid_evidence(obj: object, body: dict) -> bool:
    if not isinstance(obj, dict):
        return False

    allowed = set(body["required"]) | set(body["optional"])
    if not body["additional_properties"] and set(obj) - allowed:
        return False
    if any(field not in obj for field in body["required"]):
        return False

    rule_id = obj.get("rule_id")
    if not isinstance(rule_id, str) or not rule_id.strip():
        return False

    if obj.get("effect") not in body["effect_values"]:
        return False

    if obj.get("rule_result") not in body["rule_result_values"]:
        return False

    if "condition_results" in obj and obj["condition_results"] is not None:
        results = obj["condition_results"]
        if not isinstance(results, list) or not results:
            return False
        seen_ids = []
        any_condition_error = False
        for item in results:
            if not _is_valid_condition_result(item, body):
                return False
            seen_ids.append(item["condition_id"])
            if item.get("result") == "error":
                any_condition_error = True
        if len(seen_ids) != len(set(seen_ids)):
            return False
        # A condition evaluation error forces the containing rule's own
        # rule_result to error (a rule cannot be matched/not_matched while
        # one of its conditions could not be evaluated).
        if any_condition_error and obj.get("rule_result") != "error":
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


def test_trace_rule_evidence_file_exists() -> None:
    assert EVIDENCE_FILE.is_file(), (
        "schemas/trace-rule-evidence/trace-rule-evidence.yaml must exist"
    )


def test_trace_rule_evidence_yaml_parses() -> None:
    assert _load()


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


def test_contract_metadata_matches_expected_values() -> None:
    contract = _load()["contract"]
    assert contract["name"] == "trace-rule-evidence"
    assert contract["title"] == "BASIS Trace Rule Evidence"
    assert contract["version"] == "0.1.0"
    assert contract["governed_by"] == "basis-architecture"
    assert contract["published_by"] == "basis-schemas"


def test_lifecycle_is_experimental() -> None:
    assert _load()["contract"]["lifecycle"] == "experimental"


def test_declares_expected_dependencies() -> None:
    assert _load()["contract"]["depends_on"] == [
        "contract-metadata",
        "policy-rule",
        "policy-condition",
        "reason-code",
    ]


def test_is_tracked_in_operation_aware_response_trace_contracts() -> None:
    assert "trace-rule-evidence" in basis_schemas.OPERATION_AWARE_RESPONSE_TRACE_CONTRACTS
    assert basis_schemas.OPERATION_AWARE_RESPONSE_TRACE_CONTRACTS[0] == "trace-rule-evidence"


# ---------------------------------------------------------------------------
# Field policy
# ---------------------------------------------------------------------------


def test_required_and_optional_fields() -> None:
    body = _body()
    assert body["required"] == ["rule_id", "effect", "rule_result"]
    assert set(body["optional"]) == {"condition_results", "reason_code", "explanation"}


def test_unknown_fields_are_rejected_by_policy() -> None:
    assert _body()["additional_properties"] is False


def test_effect_values_match_policy_rule() -> None:
    assert _body()["effect_values"] == ["allow", "deny"]


def test_rule_result_values_are_the_published_four() -> None:
    assert _body()["rule_result_values"] == ["matched", "not_matched", "skipped", "error"]


def test_condition_result_values_are_the_published_three() -> None:
    assert _body()["condition_result_values"] == ["matched", "not_matched", "error"]


def test_rule_result_vocabulary_avoids_ambiguous_words() -> None:
    # The task guidance explicitly warns against "passed" / "failed" /
    # "success", which could be confused with evaluator success/failure.
    values = set(_body()["rule_result_values"])
    for ambiguous in ("passed", "failed", "success"):
        assert ambiguous not in values


# ---------------------------------------------------------------------------
# Parity with policy-rule and reason-code
# ---------------------------------------------------------------------------


def test_effect_values_match_policy_rule_source_file() -> None:
    policy_rule_body = _load_yaml(POLICY_RULE_FILE)["policy_rule"]
    assert _body()["effect_values"] == policy_rule_body["fields"][1]["enum"]


def test_reason_code_pattern_matches_source_contract() -> None:
    reason_code_body = _load_yaml(REASON_CODE_FILE)["reason_code"]
    assert _body()["reason_code_pattern"] == reason_code_body["pattern"]


# ---------------------------------------------------------------------------
# Condition-error propagation (a condition error forces rule_result: error)
# ---------------------------------------------------------------------------


def test_condition_error_with_matched_rule_result_is_invalid() -> None:
    body = _body()
    invalid = {
        "rule_id": "rule-x",
        "effect": "deny",
        "rule_result": "matched",
        "condition_results": [{"condition_id": "cond-x", "result": "error"}],
    }
    assert not _is_valid_evidence(invalid, body)


def test_condition_error_with_error_rule_result_is_valid() -> None:
    body = _body()
    valid = {
        "rule_id": "rule-x",
        "effect": "deny",
        "rule_result": "error",
        "condition_results": [{"condition_id": "cond-x", "result": "error"}],
    }
    assert _is_valid_evidence(valid, body)


def test_condition_not_matched_does_not_force_rule_error() -> None:
    body = _body()
    valid = {
        "rule_id": "rule-x",
        "effect": "deny",
        "rule_result": "not_matched",
        "condition_results": [{"condition_id": "cond-x", "result": "not_matched"}],
    }
    assert _is_valid_evidence(valid, body)


# ---------------------------------------------------------------------------
# skipped vs. not_applicable are distinct concepts
# ---------------------------------------------------------------------------


def test_skipped_is_a_rule_result_not_a_bundle_applicability_value() -> None:
    # "skipped" is a per-rule trace state published here; "not_applicable" is
    # evaluation-trace's own bundle_applicability concept. The two vocabularies
    # must never be merged into one.
    body = _body()
    assert "skipped" in body["rule_result_values"]
    assert "not_applicable" not in body["rule_result_values"]


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------


def test_no_redaction_classification_field_published() -> None:
    body = _body()
    allowed = set(body["required"]) | set(body["optional"])
    assert "redaction_classification" not in allowed
    condition_shape = body["condition_result_shape"]
    condition_allowed = set(condition_shape["required"]) | set(condition_shape["optional"])
    assert "redaction_classification" not in condition_allowed


# ---------------------------------------------------------------------------
# Hardened primitive-type validation
# ---------------------------------------------------------------------------


def _minimal_valid_evidence() -> dict:
    return {"rule_id": "rule-x", "effect": "allow", "rule_result": "matched"}


@pytest.mark.parametrize("bad_value", [123, True, 1.5, [], {}, None])
def test_rule_id_rejects_non_string_types(bad_value: object) -> None:
    body = _body()
    evidence = _minimal_valid_evidence()
    evidence["rule_id"] = bad_value
    assert not _is_valid_evidence(evidence, body)


@pytest.mark.parametrize("bad_value", [1, True, [], {}, "ALLOW", None])
def test_effect_rejects_invalid_primitive_or_casing(bad_value: object) -> None:
    body = _body()
    evidence = _minimal_valid_evidence()
    evidence["effect"] = bad_value
    assert not _is_valid_evidence(evidence, body)


@pytest.mark.parametrize("bad_value", [1, True, [], {}, "MATCHED", None])
def test_rule_result_rejects_invalid_primitive_or_casing(bad_value: object) -> None:
    body = _body()
    evidence = _minimal_valid_evidence()
    evidence["rule_result"] = bad_value
    assert not _is_valid_evidence(evidence, body)


@pytest.mark.parametrize("bad_value", ["not-a-list", 1, {}, True])
def test_condition_results_rejects_non_array_types(bad_value: object) -> None:
    body = _body()
    evidence = _minimal_valid_evidence()
    evidence["condition_results"] = bad_value
    assert not _is_valid_evidence(evidence, body)


def test_bool_is_not_silently_accepted_as_a_string_identifier() -> None:
    # bool is a subclass of int in Python; confirm it is never mistaken for
    # a valid non-empty string identifier.
    body = _body()
    evidence = _minimal_valid_evidence()
    evidence["rule_id"] = True
    assert not _is_valid_evidence(evidence, body)
    assert isinstance(True, int)  # documents the Python subtlety this guards against


# ---------------------------------------------------------------------------
# Examples
# ---------------------------------------------------------------------------


def test_required_valid_examples_accepted() -> None:
    body = _body()
    for example in body["examples"]["valid"]:
        assert _is_valid_evidence(example, body), f"valid example rejected: {example!r}"


def test_required_invalid_examples_rejected() -> None:
    body = _body()
    for case in body["examples"]["invalid"]:
        assert "reason" in case, f"invalid example missing a reason: {case!r}"
        assert not _is_valid_evidence(case["value"], body), (
            f"invalid example accepted ({case['reason']}): {case['value']!r}"
        )


def test_invalid_examples_cover_required_cases() -> None:
    reasons = " ".join(case["reason"] for case in _body()["examples"]["invalid"]).lower()
    assert "missing required rule id" in reasons
    assert "empty rule id" in reasons
    assert "invalid effect" in reasons
    assert "not_applicable effect" in reasons
    assert "invalid rule_result" in reasons
    assert "malformed condition evidence" in reasons
    assert "duplicate condition ids" in reasons
    assert "malformed reason code" in reasons
    assert "unknown field" in reasons
    assert "raw evidence field" in reasons
    assert "debug/stack-trace field" in reasons
    assert "condition error present but rule_result is matched" in reasons


def test_every_rule_result_value_appears_in_a_valid_example() -> None:
    body = _body()
    seen = {example["rule_result"] for example in body["examples"]["valid"]}
    assert set(body["rule_result_values"]) <= seen


def test_every_effect_value_appears_in_a_valid_example() -> None:
    body = _body()
    seen = {example["effect"] for example in body["examples"]["valid"]}
    assert set(body["effect_values"]) <= seen


# ---------------------------------------------------------------------------
# Boundedness / security
# ---------------------------------------------------------------------------


def test_forbidden_fields_never_appear_in_contract_source() -> None:
    text = EVIDENCE_FILE.read_text(encoding="utf-8")
    for field in FORBIDDEN_FIELDS:
        # Allow the field name to appear inside a comment/description as a
        # documented exclusion (e.g. "It does not define access_token...").
        # It must never appear as a published field id.
        assert f"id: {field}\n" not in text, (
            f"forbidden field {field!r} appears as a published field"
        )


def test_condition_result_shape_excludes_raw_condition_fields() -> None:
    shape = _body()["condition_result_shape"]
    allowed = set(shape["required"]) | set(shape["optional"])
    for raw_field in ("field_path", "operator", "expected_value"):
        assert raw_field not in allowed, (
            f"condition_result_shape must not carry raw condition field {raw_field!r}"
        )


def test_duplicate_condition_ids_within_one_record_are_rejected() -> None:
    body = _body()
    duplicate = {
        "rule_id": "rule-x",
        "effect": "deny",
        "rule_result": "matched",
        "condition_results": [
            {"condition_id": "cond-a", "result": "matched"},
            {"condition_id": "cond-a", "result": "not_matched"},
        ],
    }
    assert not _is_valid_evidence(duplicate, body)
