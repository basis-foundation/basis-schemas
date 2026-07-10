"""Focused checks on the published audit-evidence contract.

These tests validate ``schemas/audit-evidence/audit-evidence.yaml`` (PR F of
`basis-architecture`'s operation-aware schema readiness plan, ADR-0005): its
metadata, its declared dependencies, that its published field policy accepts
well-formed evidence records and rejects malformed ones, that
``evaluation_status`` / ``outcome`` / ``failure_reason`` observe the required
invariant (a failed evaluation never carries a non-null outcome, kept in
parity with PR E), that ``bundle_version`` / ``reason_code`` patterns stay in
parity with their source contracts, that nested
``identity_evidence_reference`` / ``adapter_evidence_reference`` values stay
in parity with PR B, and that this contract never defines a raw-secret,
raw-request, gateway-enforcement, or cryptographic-signing field.

This is a contract publication, not a parser: the only behavior exercised
here is applying the contract's own published rules to example evidence
objects.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import basis_schemas

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = REPO_ROOT / "schemas" / "audit-evidence"
EVIDENCE_FILE = EVIDENCE_DIR / "audit-evidence.yaml"
RESPONSE_FILE = (
    REPO_ROOT
    / "schemas"
    / "operation-aware-decision-response"
    / "operation-aware-decision-response.yaml"
)
TRACE_FILE = REPO_ROOT / "schemas" / "evaluation-trace" / "evaluation-trace.yaml"
POLICY_BUNDLE_FILE = REPO_ROOT / "schemas" / "policy-bundle" / "policy-bundle.yaml"
REASON_CODE_FILE = REPO_ROOT / "schemas" / "reason-code" / "reason-code.yaml"
IDENTITY_EVIDENCE_REF_FILE = (
    REPO_ROOT / "schemas" / "identity-evidence-reference" / "identity-evidence-reference.yaml"
)
ADAPTER_EVIDENCE_REF_FILE = (
    REPO_ROOT / "schemas" / "adapter-evidence-reference" / "adapter-evidence-reference.yaml"
)
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
    "enforcement_action",
    "enforcement_result",
    "enforcement_status",
    "http_status",
    "response_status",
    "gateway_enforcement",
    "event_id",
    "event_type",
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
    return _load_yaml(EVIDENCE_FILE)


def _body() -> dict:
    return _load()["audit_evidence"]


def _identity_ref_body() -> dict:
    return _load_yaml(IDENTITY_EVIDENCE_REF_FILE)["identity_evidence_reference"]


def _adapter_ref_body() -> dict:
    return _load_yaml(ADAPTER_EVIDENCE_REF_FILE)["adapter_evidence_reference"]


def _is_valid_digest(obj: object) -> bool:
    if not isinstance(obj, dict):
        return False
    if set(obj) - {"algorithm", "value"}:
        return False
    if "algorithm" not in obj or "value" not in obj:
        return False
    if not isinstance(obj["algorithm"], str) or not re.match(
        r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$", obj["algorithm"]
    ):
        return False
    if not isinstance(obj["value"], str) or not re.match(r"^[a-f0-9]+$", obj["value"]):
        return False
    return True


def _is_valid_identity_reference(obj: object) -> bool:
    body = _identity_ref_body()
    if not isinstance(obj, dict):
        return False
    allowed = set(body["required"]) | set(body["optional"])
    if set(obj) - allowed:
        return False
    if any(field not in obj for field in body["required"]):
        return False
    if not isinstance(obj.get("reference_id"), str) or not obj["reference_id"].strip():
        return False
    if not _is_valid_digest(obj.get("evidence_digest")):
        return False
    if not isinstance(obj.get("identity_source"), str) or not obj["identity_source"].strip():
        return False
    if obj.get("redaction_classification") not in body["redaction_classification_values"]:
        return False
    return True


def _is_valid_adapter_reference(obj: object) -> bool:
    body = _adapter_ref_body()
    if not isinstance(obj, dict):
        return False
    allowed = set(body["required"]) | set(body["optional"])
    if set(obj) - allowed:
        return False
    if any(field not in obj for field in body["required"]):
        return False
    if not isinstance(obj.get("reference_id"), str) or not obj["reference_id"].strip():
        return False
    if not _is_valid_digest(obj.get("evidence_digest")):
        return False
    if not isinstance(obj.get("adapter_source"), str) or not obj["adapter_source"].strip():
        return False
    if obj.get("redaction_classification") not in body["redaction_classification_values"]:
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

    for field in ("evidence_id", "request_id"):
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

    if "correlation_id" in obj and obj["correlation_id"] is not None:
        if not isinstance(obj["correlation_id"], str):
            return False

    if "trace_id" in obj and obj["trace_id"] is not None:
        if not isinstance(obj["trace_id"], str) or not obj["trace_id"].strip():
            return False

    if "bundle_id" in obj and obj["bundle_id"] is not None:
        if not isinstance(obj["bundle_id"], str) or not obj["bundle_id"].strip():
            return False

    if "bundle_version" in obj and obj["bundle_version"] is not None:
        if not isinstance(obj["bundle_version"], str) or not re.match(
            body["bundle_version_pattern"], obj["bundle_version"]
        ):
            return False

    matched_rule_ids = obj.get("matched_rule_ids")
    if matched_rule_ids is not None:
        if not isinstance(matched_rule_ids, list):
            return False
        if not all(isinstance(item, str) and item.strip() for item in matched_rule_ids):
            return False
        if len(matched_rule_ids) != len(set(matched_rule_ids)):
            return False

    identity_ref = obj.get("identity_evidence_reference")
    if identity_ref is not None and not _is_valid_identity_reference(identity_ref):
        return False

    adapter_ref = obj.get("adapter_evidence_reference")
    if adapter_ref is not None and not _is_valid_adapter_reference(adapter_ref):
        return False

    if "reason_code" in obj and obj["reason_code"] is not None:
        if not isinstance(obj["reason_code"], str) or not re.match(
            body["reason_code_pattern"], obj["reason_code"]
        ):
            return False

    if "explanation" in obj and obj["explanation"] is not None:
        if not isinstance(obj["explanation"], str) or not obj["explanation"].strip():
            return False

    recorded_at = obj.get("recorded_at")
    if not isinstance(recorded_at, str) or not re.match(body["recorded_at_pattern"], recorded_at):
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


def test_audit_evidence_file_exists() -> None:
    assert EVIDENCE_FILE.is_file(), "schemas/audit-evidence/audit-evidence.yaml must exist"


def test_audit_evidence_yaml_parses() -> None:
    assert _load()


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


def test_contract_metadata_matches_expected_values() -> None:
    contract = _load()["contract"]
    assert contract["name"] == "audit-evidence"
    assert contract["title"] == "BASIS Audit Evidence"
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
        "identity-evidence-reference",
        "adapter-evidence-reference",
        "reason-code",
    ]


# ---------------------------------------------------------------------------
# Field policy
# ---------------------------------------------------------------------------


def test_required_and_optional_fields() -> None:
    body = _body()
    assert body["required"] == [
        "evidence_id",
        "request_id",
        "evaluation_status",
        "outcome",
        "failure_reason",
        "recorded_at",
    ]
    assert set(body["optional"]) == {
        "correlation_id",
        "trace_id",
        "bundle_id",
        "bundle_version",
        "matched_rule_ids",
        "identity_evidence_reference",
        "adapter_evidence_reference",
        "reason_code",
        "explanation",
        "schema_version",
    }


def test_unknown_fields_are_rejected_by_policy() -> None:
    assert _body()["additional_properties"] is False


# ---------------------------------------------------------------------------
# Parity with PR E (outcome / evaluation_status / failure_reason)
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


def test_evaluation_status_values_match_evaluation_trace() -> None:
    trace_body = _load_yaml(TRACE_FILE)["evaluation_trace"]
    assert _body()["evaluation_status_values"] == trace_body["evaluation_status_values"]


def test_failure_reason_values_match_evaluation_trace() -> None:
    trace_body = _load_yaml(TRACE_FILE)["evaluation_trace"]
    assert _body()["failure_reason_values"] == trace_body["failure_reason_values"]


def test_bundle_version_pattern_matches_policy_bundle_source() -> None:
    bundle_body = _load_yaml(POLICY_BUNDLE_FILE)["policy_bundle"]
    assert _body()["bundle_version_pattern"] == bundle_body["fields"][1]["pattern"]


def test_reason_code_pattern_matches_source_contract() -> None:
    reason_code_body = _load_yaml(REASON_CODE_FILE)["reason_code"]
    assert _body()["reason_code_pattern"] == reason_code_body["pattern"]


# ---------------------------------------------------------------------------
# Required invariant: outcome null iff evaluation_status is failed
# ---------------------------------------------------------------------------


def _minimal_valid_evidence(**overrides: object) -> dict:
    base = {
        "evidence_id": "audev-x",
        "request_id": "oadr-x",
        "evaluation_status": "completed",
        "outcome": "allow",
        "failure_reason": None,
        "recorded_at": "2026-05-22T14:30:00Z",
    }
    base.update(overrides)
    return base


def test_failed_evaluation_can_never_be_allow() -> None:
    body = _body()
    invalid = _minimal_valid_evidence(
        evaluation_status="failed", outcome="allow", failure_reason="internal_evaluation_error"
    )
    assert not _is_valid_evidence(invalid, body)


def test_failed_evaluation_requires_null_outcome() -> None:
    body = _body()
    valid = _minimal_valid_evidence(
        evaluation_status="failed", outcome=None, failure_reason="internal_evaluation_error"
    )
    assert _is_valid_evidence(valid, body)


def test_completed_evaluation_requires_null_failure_reason() -> None:
    body = _body()
    invalid = _minimal_valid_evidence(failure_reason="internal_evaluation_error")
    assert not _is_valid_evidence(invalid, body)


def test_completed_evaluation_requires_non_null_outcome() -> None:
    body = _body()
    invalid = _minimal_valid_evidence(outcome=None)
    assert not _is_valid_evidence(invalid, body)


def test_failed_without_failure_reason_is_invalid() -> None:
    body = _body()
    invalid = _minimal_valid_evidence(evaluation_status="failed", outcome=None, failure_reason=None)
    assert not _is_valid_evidence(invalid, body)


def test_not_applicable_is_a_distinct_valid_outcome_from_deny() -> None:
    # NOT_APPLICABLE must remain preserved as its own outcome, never rewritten
    # as a policy deny (ADR-0002 Section 5).
    body = _body()
    not_applicable = _minimal_valid_evidence(outcome="not_applicable")
    deny = _minimal_valid_evidence(outcome="deny")
    assert _is_valid_evidence(not_applicable, body)
    assert _is_valid_evidence(deny, body)
    assert not_applicable["outcome"] != deny["outcome"]


# ---------------------------------------------------------------------------
# matched_rule_ids
# ---------------------------------------------------------------------------


def test_duplicate_matched_rule_ids_are_rejected() -> None:
    body = _body()
    invalid = _minimal_valid_evidence(matched_rule_ids=["rule-a", "rule-a"])
    assert not _is_valid_evidence(invalid, body)


def test_unique_matched_rule_ids_are_valid() -> None:
    body = _body()
    valid = _minimal_valid_evidence(matched_rule_ids=["rule-a", "rule-b"])
    assert _is_valid_evidence(valid, body)


def test_empty_matched_rule_ids_is_valid() -> None:
    body = _body()
    valid = _minimal_valid_evidence(matched_rule_ids=[])
    assert _is_valid_evidence(valid, body)


@pytest.mark.parametrize("bad_value", [1, True, 1.5, {}, "rule-a"])
def test_matched_rule_ids_rejects_non_array_types(bad_value: object) -> None:
    body = _body()
    invalid = _minimal_valid_evidence(matched_rule_ids=bad_value)
    assert not _is_valid_evidence(invalid, body)


@pytest.mark.parametrize("bad_item", [1, True, 1.5, [], {}, None])
def test_matched_rule_ids_rejects_non_string_members(bad_item: object) -> None:
    # bool is a subclass of int in Python; True/False must not be silently
    # accepted as array members where a string rule_id is expected.
    body = _body()
    invalid = _minimal_valid_evidence(matched_rule_ids=["rule-a", bad_item])
    assert not _is_valid_evidence(invalid, body)


# ---------------------------------------------------------------------------
# Policy provenance: bundle_id / bundle_version are independently optional
# ---------------------------------------------------------------------------


def test_bundle_id_present_without_bundle_version_is_not_rejected_by_this_contract() -> None:
    # Review finding: this contract's published constraints do not couple
    # bundle_id presence to bundle_version presence — each is independently
    # optional/nullable (see audit-evidence.md, Section 18). This
    # characterization test documents the ACTUAL, currently-permissive
    # behavior; it intentionally does not assert rejection, because no
    # constraint in the published contract rejects this shape today. A
    # stricter "both present or both absent" invariant would be a shape/
    # validation-behavior change, out of scope for a documentation review.
    body = _body()
    partial = _minimal_valid_evidence(bundle_id="baseline-read-only-telemetry")
    assert _is_valid_evidence(partial, body)


def test_bundle_version_present_without_bundle_id_is_not_rejected_by_this_contract() -> None:
    body = _body()
    partial = _minimal_valid_evidence(bundle_version="1.0.0")
    assert _is_valid_evidence(partial, body)


# ---------------------------------------------------------------------------
# Nested evidence references
# ---------------------------------------------------------------------------


def test_valid_identity_evidence_reference_is_accepted() -> None:
    body = _body()
    valid = _minimal_valid_evidence(
        identity_evidence_reference={
            "reference_id": "idev-0001-0000-0000-000000000001",
            "evidence_digest": {
                "algorithm": "sha-256",
                "value": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            },
            "identity_source": "oidc:https://idp.example.com",
            "redaction_classification": "reference_only",
        }
    )
    assert _is_valid_evidence(valid, body)


def test_invalid_redaction_classification_in_identity_reference_is_rejected() -> None:
    body = _body()
    invalid = _minimal_valid_evidence(
        identity_evidence_reference={
            "reference_id": "idev-0001-0000-0000-000000000001",
            "evidence_digest": {
                "algorithm": "sha-256",
                "value": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            },
            "identity_source": "oidc:https://idp.example.com",
            "redaction_classification": "public",
        }
    )
    assert not _is_valid_evidence(invalid, body)


def test_valid_adapter_evidence_reference_is_accepted() -> None:
    body = _body()
    valid = _minimal_valid_evidence(
        adapter_evidence_reference={
            "reference_id": "adev-0001-0000-0000-000000000001",
            "evidence_digest": {
                "algorithm": "sha-256",
                "value": "1f825aa2f0020ef7cf91dfa30da4668d791c5d4824fc8e41354b89ec05795ab",
            },
            "adapter_source": "basis-adapters:bacnet",
            "redaction_classification": "reference_only",
        }
    )
    assert _is_valid_evidence(valid, body)


def test_malformed_digest_in_adapter_reference_is_rejected() -> None:
    body = _body()
    invalid = _minimal_valid_evidence(
        adapter_evidence_reference={
            "reference_id": "adev-0001-0000-0000-000000000001",
            "evidence_digest": {"algorithm": "sha-256", "value": "sha256:notbarehex"},
            "adapter_source": "basis-adapters:bacnet",
            "redaction_classification": "reference_only",
        }
    )
    assert not _is_valid_evidence(invalid, body)


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
    assert "missing required evidence id" in reasons
    assert "empty evidence id" in reasons
    assert "missing required request id" in reasons
    assert "malformed timestamp" in reasons
    assert "invariant violation" in reasons
    assert "invalid outcome" in reasons
    assert "malformed policy provenance" in reasons
    assert "duplicate rule ids" in reasons
    assert "raw access token" in reasons
    assert "raw claims" in reasons
    assert "raw protocol payload" in reasons
    assert "request snapshot" in reasons
    assert "full policy" in reasons
    assert "stack trace" in reasons
    assert "unknown field" in reasons


def test_every_outcome_value_appears_in_a_valid_example() -> None:
    body = _body()
    seen = {ex["outcome"] for ex in body["examples"]["valid"] if ex["outcome"] is not None}
    assert set(body["outcome_values"]) <= seen


def test_both_evaluation_statuses_appear_in_valid_examples() -> None:
    body = _body()
    seen = {ex["evaluation_status"] for ex in body["examples"]["valid"]}
    assert seen == {"completed", "failed"}


# ---------------------------------------------------------------------------
# Boundedness / security
# ---------------------------------------------------------------------------


def test_forbidden_fields_never_appear_as_published_fields() -> None:
    text = EVIDENCE_FILE.read_text(encoding="utf-8")
    for field in FORBIDDEN_FIELDS:
        assert f"id: {field}\n" not in text, (
            f"forbidden field {field!r} appears as a published field"
        )


def test_no_redaction_classification_field_published_at_top_level() -> None:
    body = _body()
    allowed = set(body["required"]) | set(body["optional"])
    assert "redaction_classification" not in allowed


def test_no_cryptographic_signing_fields_published() -> None:
    text = EVIDENCE_FILE.read_text(encoding="utf-8")
    for field in ("signature", "signature_algorithm", "hash_chain", "previous_hash", "merkle_root"):
        assert f"id: {field}\n" not in text


# ---------------------------------------------------------------------------
# First-wave audit-event unchanged
# ---------------------------------------------------------------------------


def test_first_wave_audit_event_contract_remains_unchanged() -> None:
    # Hermetic structural regression test: reproduces the first-wave
    # contract's own published surface directly from the YAML, rather than
    # diffing against a `main` git ref. This guards against an accidental
    # edit without depending on git history.
    assert FIRST_WAVE_AUDIT_EVENT_FILE.is_file()
    assert FIRST_WAVE_AUDIT_EVENT_DOC.is_file()

    first_wave = _load_yaml(FIRST_WAVE_AUDIT_EVENT_FILE)
    contract = first_wave["contract"]
    body = first_wave["audit_event"]

    assert contract["name"] == "audit-event"
    assert contract["version"] == "0.1.0"
    assert contract["lifecycle"] == "experimental"
    assert contract["governed_by"] == "basis-architecture"
    assert contract["published_by"] == "basis-schemas"
    assert contract["depends_on"] == ["decision-request", "decision-response"]

    assert body["required"] == ["event_id", "event_type", "action", "timestamp"]
    assert body["additional_properties"] is False


# ---------------------------------------------------------------------------
# Hardened primitive-type validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("field", ["evidence_id", "request_id"])
@pytest.mark.parametrize("bad_value", [123, True, 1.5, [], {}, None])
def test_identifier_fields_reject_non_string_types(field: str, bad_value: object) -> None:
    body = _body()
    evidence = _minimal_valid_evidence(**{field: bad_value})
    assert not _is_valid_evidence(evidence, body)


@pytest.mark.parametrize("bad_value", [1, True, [], {}, "ALLOW"])
def test_outcome_rejects_invalid_primitive_or_casing(bad_value: object) -> None:
    body = _body()
    evidence = _minimal_valid_evidence(outcome=bad_value)
    assert not _is_valid_evidence(evidence, body)


@pytest.mark.parametrize("bad_value", [1, True, [], {}, "COMPLETED"])
def test_evaluation_status_rejects_invalid_primitive_or_casing(bad_value: object) -> None:
    body = _body()
    evidence = _minimal_valid_evidence(evaluation_status=bad_value)
    assert not _is_valid_evidence(evidence, body)


@pytest.mark.parametrize("bad_value", [123, True, [], {}, "1.0"])
def test_bundle_version_rejects_non_semver_or_non_string_types(bad_value: object) -> None:
    body = _body()
    evidence = _minimal_valid_evidence(bundle_id="some-bundle", bundle_version=bad_value)
    assert not _is_valid_evidence(evidence, body)


@pytest.mark.parametrize("bad_value", [123, True, [], {}, "ALLOW_RULE_MATCHED"])
def test_reason_code_rejects_invalid_primitive_or_casing(bad_value: object) -> None:
    body = _body()
    evidence = _minimal_valid_evidence(reason_code=bad_value)
    assert not _is_valid_evidence(evidence, body)


def test_bool_is_not_silently_accepted_as_a_string_identifier() -> None:
    # bool is a subclass of int in Python; confirm it is never mistaken for
    # a valid non-empty string identifier.
    body = _body()
    evidence = _minimal_valid_evidence(evidence_id=True)
    assert not _is_valid_evidence(evidence, body)
    assert isinstance(True, int)  # documents the Python subtlety this guards against


@pytest.mark.parametrize("bad_value", [123, True, 1.5, [], {}])
def test_correlation_id_rejects_non_string_non_null_types(bad_value: object) -> None:
    body = _body()
    evidence = _minimal_valid_evidence(correlation_id=bad_value)
    assert not _is_valid_evidence(evidence, body)


@pytest.mark.parametrize("bad_value", [123, True, 1.5, [], {}, ""])
def test_trace_id_rejects_non_string_or_empty_values(bad_value: object) -> None:
    body = _body()
    evidence = _minimal_valid_evidence(trace_id=bad_value)
    assert not _is_valid_evidence(evidence, body)


@pytest.mark.parametrize("bad_value", [123, True, 1.5, [], {}, ""])
def test_bundle_id_rejects_non_string_or_empty_values(bad_value: object) -> None:
    body = _body()
    evidence = _minimal_valid_evidence(bundle_id=bad_value)
    assert not _is_valid_evidence(evidence, body)


@pytest.mark.parametrize("bad_value", [123, True, 1.5, [], {}, "unsupported_schema_version_typo"])
def test_failure_reason_rejects_invalid_primitive_or_unknown_value(bad_value: object) -> None:
    body = _body()
    evidence = _minimal_valid_evidence(
        evaluation_status="failed", outcome=None, failure_reason=bad_value
    )
    assert not _is_valid_evidence(evidence, body)


@pytest.mark.parametrize("bad_value", [123, True, 1.5, [], {}, ""])
def test_explanation_rejects_non_string_or_empty_values(bad_value: object) -> None:
    body = _body()
    evidence = _minimal_valid_evidence(explanation=bad_value)
    assert not _is_valid_evidence(evidence, body)


@pytest.mark.parametrize(
    "bad_value", [123, True, 1.5, [], {}, "2026-05-22", "2026-05-22 14:30:00Z"]
)
def test_recorded_at_rejects_non_string_or_malformed_timestamp(bad_value: object) -> None:
    body = _body()
    evidence = _minimal_valid_evidence(recorded_at=bad_value)
    assert not _is_valid_evidence(evidence, body)


@pytest.mark.parametrize("bad_value", [123, True, 1.5, [], {}, "0.1"])
def test_schema_version_rejects_non_string_or_non_semver(bad_value: object) -> None:
    body = _body()
    evidence = _minimal_valid_evidence(schema_version=bad_value)
    assert not _is_valid_evidence(evidence, body)


@pytest.mark.parametrize("bad_value", [123, True, 1.5, "idev-0001", []])
def test_identity_evidence_reference_rejects_non_object_types(bad_value: object) -> None:
    body = _body()
    evidence = _minimal_valid_evidence(identity_evidence_reference=bad_value)
    assert not _is_valid_evidence(evidence, body)


@pytest.mark.parametrize("bad_value", [123, True, 1.5, "adev-0001", []])
def test_adapter_evidence_reference_rejects_non_object_types(bad_value: object) -> None:
    body = _body()
    evidence = _minimal_valid_evidence(adapter_evidence_reference=bad_value)
    assert not _is_valid_evidence(evidence, body)


# ---------------------------------------------------------------------------
# Repository tracking
# ---------------------------------------------------------------------------


def test_audit_evidence_is_not_in_first_wave_tuples() -> None:
    assert "audit-evidence" not in basis_schemas.PLANNED_CONTRACTS
    assert "audit-evidence" not in basis_schemas.PUBLISHED_CONTRACTS
