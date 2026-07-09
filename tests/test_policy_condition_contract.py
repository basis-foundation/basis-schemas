"""Focused checks on the published policy-condition contract.

These tests validate ``schemas/policy-condition/policy-condition.yaml`` (PR D
of `basis-architecture`'s operation-aware schema readiness plan, ADR-0005):
its metadata, its declared dependencies, that its published field policy
accepts well-formed conditions and rejects malformed ones, that the operator
vocabulary is structurally open rather than a closed enum, that expected_value
stays data-only (no executable/script fields, no unsupported nested shapes),
and that this contract never defines a raw-secret or executable-policy field.

This is a contract publication, not a parser: the only behavior exercised
here is applying the contract's own published rules (required fields, the
no-unknown-fields policy, the field_path/operator patterns, and the
expected_value scalar/homogeneous-array shape) to example condition objects.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import basis_schemas

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
CONDITION_DIR = REPO_ROOT / "schemas" / "policy-condition"
CONDITION_FILE = CONDITION_DIR / "policy-condition.yaml"
REASON_CODE_FILE = REPO_ROOT / "schemas" / "reason-code" / "reason-code.yaml"

#: Fields that must never appear on this contract — raw secrets, tokens, or
#: executable-policy fields.
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
    "raw_claims",
    "full_claim_set",
    "raw_payload",
    "raw_protocol_payload",
    "device_secret",
    "credential",
    "script",
    "code",
    "executable",
    "command",
    "expression",
)


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict), f"{path} must parse to a mapping"
    return data


def _load() -> dict:
    return _load_yaml(CONDITION_FILE)


def _body() -> dict:
    return _load()["policy_condition"]


def _field(fields: list, field_id: str) -> dict:
    for field in fields:
        if field["id"] == field_id:
            return field
    raise AssertionError(f"field {field_id!r} not declared")


def _is_valid_expected_value(value: object, body: dict) -> bool:
    scalar_types = (str, int, float, bool)
    if value is None:
        return True
    if isinstance(value, bool):
        return True
    if isinstance(value, (str, int, float)):
        return True
    if isinstance(value, list):
        if not value:
            # Homogeneous-array rule is meaningless for an empty list; treat
            # as vacuously homogeneous, but every item must still be a
            # scalar of an allowed type were the list non-empty. An empty
            # array is accepted as a degenerate homogeneous array.
            return True
        # bool is a subclass of int; keep bool and int/float distinguishable.
        normalized_types = set()
        for item in value:
            if not isinstance(item, scalar_types):
                return False
            if isinstance(item, bool):
                normalized_types.add(bool)
            elif isinstance(item, (int, float)):
                normalized_types.add("number")
            elif isinstance(item, str):
                normalized_types.add(str)
        return len(normalized_types) == 1
    return False


def _is_valid_condition(obj: object, body: dict) -> bool:
    if not isinstance(obj, dict):
        return False

    required = body["required"]
    optional = body["optional"]
    allowed = set(required) | set(optional)
    if not body["additional_properties"] and set(obj) - allowed:
        return False
    if any(field not in obj for field in required):
        return False

    condition_id = obj.get("condition_id")
    if not isinstance(condition_id, str) or not condition_id.strip():
        return False

    field_path = obj.get("field_path")
    if not isinstance(field_path, str) or not re.match(body["field_path_pattern"], field_path):
        return False

    operator = obj.get("operator")
    if not isinstance(operator, str) or not re.match(body["operator_pattern"], operator):
        return False

    if "expected_value" not in obj:
        return False
    if not _is_valid_expected_value(obj["expected_value"], body):
        return False

    return True


# ---------------------------------------------------------------------------
# File / parsing
# ---------------------------------------------------------------------------


def test_policy_condition_file_exists() -> None:
    assert CONDITION_FILE.is_file(), "schemas/policy-condition/policy-condition.yaml must exist"


def test_policy_condition_yaml_parses() -> None:
    assert _load()


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


def test_contract_metadata_matches_expected_values() -> None:
    contract = _load()["contract"]
    assert contract["name"] == "policy-condition"
    assert contract["title"] == "BASIS Policy Condition"
    assert contract["version"] == "0.1.0"
    assert contract["governed_by"] == "basis-architecture"
    assert contract["published_by"] == "basis-schemas"
    assert contract["source"] == "docs/architecture/operation-aware-schema-readiness-plan.md"
    assert isinstance(contract.get("description"), str) and contract["description"].strip()


def test_lifecycle_is_experimental() -> None:
    assert _load()["contract"]["lifecycle"] == "experimental"


def test_contract_metadata_dependencies_are_exact() -> None:
    depends_on = _load()["contract"].get("depends_on")
    assert depends_on == ["contract-metadata"]


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------


def test_required_fields_are_exact() -> None:
    assert _body()["required"] == ["condition_id", "field_path", "operator", "expected_value"]


def test_no_optional_fields() -> None:
    assert _body()["optional"] == []


def test_unknown_fields_are_rejected_by_policy() -> None:
    assert _body()["additional_properties"] is False


def test_every_field_has_a_description() -> None:
    for field in _body()["fields"]:
        assert isinstance(field.get("description"), str) and field["description"].strip(), (
            f"field {field['id']!r} missing a description"
        )


def test_no_unrestricted_extension_bag() -> None:
    field_ids = {f["id"] for f in _body()["fields"]}
    for speculative in ("metadata", "extensions", "extra", "arbitrary", "custom_fields", "context"):
        assert speculative not in field_ids


# ---------------------------------------------------------------------------
# Condition ID
# ---------------------------------------------------------------------------


def test_condition_id_required_and_non_empty() -> None:
    field = _field(_body()["fields"], "condition_id")
    assert field["required"] is True
    assert field["non_empty"] is True


def test_missing_condition_id_rejected() -> None:
    body = _body()
    condition = {"field_path": "subject_id", "operator": "equals", "expected_value": "alice"}
    assert not _is_valid_condition(condition, body)


def test_empty_condition_id_rejected() -> None:
    body = _body()
    condition = {
        "condition_id": "",
        "field_path": "subject_id",
        "operator": "equals",
        "expected_value": "alice",
    }
    assert not _is_valid_condition(condition, body)


def test_condition_id_wrong_type_rejected() -> None:
    body = _body()
    condition = {
        "condition_id": 12345,
        "field_path": "subject_id",
        "operator": "equals",
        "expected_value": "alice",
    }
    assert not _is_valid_condition(condition, body)


# ---------------------------------------------------------------------------
# Field path
# ---------------------------------------------------------------------------


def test_missing_field_path_rejected() -> None:
    body = _body()
    condition = {"condition_id": "cond-1", "operator": "equals", "expected_value": "alice"}
    assert not _is_valid_condition(condition, body)


@pytest.mark.parametrize(
    "field_path",
    [
        "subject_id",
        "subject_attrs.clearance",
        "location.site_id",
        "device.device_class",
        "protocol_context.protocol",
        "risk_context.score",
        "evaluation_time",
    ],
)
def test_valid_field_paths_accepted(field_path: str) -> None:
    body = _body()
    condition = {
        "condition_id": "cond-fp",
        "field_path": field_path,
        "operator": "equals",
        "expected_value": "x",
    }
    assert _is_valid_condition(condition, body), f"valid field_path rejected: {field_path!r}"


@pytest.mark.parametrize(
    "field_path",
    [
        "",
        "Subject_Id",
        "subject_roles[0]",
        "subject_attrs.get('clearance')",
        "subject_attrs..clearance",
        ".subject_id",
        "subject_id.",
        "subject-id",
        # Attack-style / expression-syntax inputs: none is a plain dotted path.
        "subject/attrs/clearance",  # slash / path traversal
        "subject_attrs clearance",  # whitespace
        "subject_attrs.${clearance}",  # shell-style interpolation
        "subject_attrs.{{clearance}}",  # template interpolation
        "subject_attrs.clearance == 'x'",  # expression syntax
        "subject_attrs.clearance()",  # call syntax
        "subject_attrs.clearance;drop",  # statement separator
    ],
)
def test_malformed_field_paths_rejected(field_path: str) -> None:
    body = _body()
    condition = {
        "condition_id": "cond-fp",
        "field_path": field_path,
        "operator": "equals",
        "expected_value": "x",
    }
    assert not _is_valid_condition(condition, body), (
        f"malformed field_path accepted: {field_path!r}"
    )


def test_field_path_wrong_type_rejected() -> None:
    body = _body()
    condition = {
        "condition_id": "cond-fp",
        "field_path": 42,
        "operator": "equals",
        "expected_value": "x",
    }
    assert not _is_valid_condition(condition, body)


# ---------------------------------------------------------------------------
# Operator
# ---------------------------------------------------------------------------


def test_missing_operator_rejected() -> None:
    body = _body()
    condition = {"condition_id": "cond-op", "field_path": "subject_id", "expected_value": "alice"}
    assert not _is_valid_condition(condition, body)


def test_illustrative_operators_are_accepted() -> None:
    body = _body()
    for operator in body["illustrative_operators"]:
        condition = {
            "condition_id": "cond-op",
            "field_path": "subject_id",
            "operator": operator,
            "expected_value": "alice",
        }
        assert _is_valid_condition(condition, body), f"illustrative operator rejected: {operator!r}"


@pytest.mark.parametrize(
    "operator",
    ["EQUALS", "equals:strict", "equals-strict", "1_leading_digit", "_leading_underscore", ""],
)
def test_malformed_operators_rejected(operator: str) -> None:
    body = _body()
    condition = {
        "condition_id": "cond-op",
        "field_path": "subject_id",
        "operator": operator,
        "expected_value": "alice",
    }
    assert not _is_valid_condition(condition, body), f"malformed operator accepted: {operator!r}"


def test_structurally_valid_unknown_future_operator_accepted() -> None:
    # The operator vocabulary is deliberately open: a well-formed operator
    # absent from illustrative_operators must not be rejected merely for
    # being unrecognized.
    body = _body()
    condition = {
        "condition_id": "cond-future-op",
        "field_path": "subject_id",
        "operator": "matches_future_pattern",
        "expected_value": "alice",
    }
    assert _is_valid_condition(condition, body)
    assert "matches_future_pattern" not in body["illustrative_operators"]


def test_illustrative_operators_are_labeled_non_final() -> None:
    body = _body()
    assert body["illustrative_operators"] == [
        "equals",
        "not_equals",
        "in",
        "greater_than",
        "less_than",
        "exists",
    ]


def test_operator_wrong_type_rejected() -> None:
    body = _body()
    condition = {
        "condition_id": "cond-op",
        "field_path": "subject_id",
        "operator": 42,
        "expected_value": "alice",
    }
    assert not _is_valid_condition(condition, body)


# ---------------------------------------------------------------------------
# Expected value
# ---------------------------------------------------------------------------


def test_missing_expected_value_rejected() -> None:
    body = _body()
    condition = {"condition_id": "cond-val", "field_path": "subject_id", "operator": "equals"}
    assert not _is_valid_condition(condition, body)


@pytest.mark.parametrize(
    "value", ["alice", 42, 0.5, True, False, None, ["a", "b"], [1, 2, 3], [True, False]]
)
def test_valid_expected_value_types_accepted(value: object) -> None:
    body = _body()
    condition = {
        "condition_id": "cond-val",
        "field_path": "subject_id",
        "operator": "equals",
        "expected_value": value,
    }
    assert _is_valid_condition(condition, body), f"valid expected_value rejected: {value!r}"


def test_null_expected_value_is_a_legitimate_value_not_absence() -> None:
    body = _body()
    condition = {
        "condition_id": "cond-null",
        "field_path": "subject_id",
        "operator": "equals",
        "expected_value": None,
    }
    assert _is_valid_condition(condition, body)
    # Distinguish from the key being entirely absent (invalid, tested above).
    missing = {"condition_id": "cond-null", "field_path": "subject_id", "operator": "equals"}
    assert not _is_valid_condition(missing, body)


@pytest.mark.parametrize(
    "value",
    [
        {"nested": "object-not-allowed"},
        ["west-campus", 42],
        ["west-campus", True],
        [1, "two"],
        # bool is a subclass of int; a number/bool mix must not be collapsed
        # into a single "number" type and silently accepted.
        [1, True],
        [{"a": 1}],
        [[1, 2]],
    ],
)
def test_unsupported_expected_value_shapes_rejected(value: object) -> None:
    body = _body()
    condition = {
        "condition_id": "cond-val",
        "field_path": "subject_id",
        "operator": "in",
        "expected_value": value,
    }
    assert not _is_valid_condition(condition, body), f"unsupported value shape accepted: {value!r}"


def test_expected_value_declares_scalar_and_array_item_types() -> None:
    body = _body()
    assert body["expected_value_scalar_types"] == ["string", "number", "boolean", "null"]
    assert body["expected_value_array_item_types"] == ["string", "number", "boolean"]


# ---------------------------------------------------------------------------
# Executable / secret regression
# ---------------------------------------------------------------------------


def test_no_forbidden_secret_or_executable_fields_defined() -> None:
    field_ids = {f["id"] for f in _body()["fields"]}
    for forbidden in FORBIDDEN_FIELDS:
        assert forbidden not in field_ids, f"forbidden field defined on contract: {forbidden!r}"


def test_script_field_rejected_as_unknown() -> None:
    body = _body()
    condition = {
        "condition_id": "cond-script",
        "field_path": "subject_id",
        "operator": "equals",
        "expected_value": "alice",
        "script": "return True",
    }
    assert not _is_valid_condition(condition, body)


def test_unknown_field_rejected() -> None:
    body = _body()
    condition = {
        "condition_id": "cond-unknown",
        "field_path": "subject_id",
        "operator": "equals",
        "expected_value": "alice",
        "priority": 1,
    }
    assert not _is_valid_condition(condition, body)


# ---------------------------------------------------------------------------
# Reason-code pattern reuse (shared token shape, not a shared concept)
# ---------------------------------------------------------------------------


def test_operator_pattern_matches_reason_code_token_shape() -> None:
    # operator and reason_code are different concepts, but this contract
    # deliberately reuses reason-code's already-published lowercase
    # snake_case token pattern for operator, rather than inventing a second
    # equivalent pattern.
    reason_code_pattern = _load_yaml(REASON_CODE_FILE)["reason_code"]["pattern"]
    assert _body()["operator_pattern"] == reason_code_pattern


# ---------------------------------------------------------------------------
# Examples
# ---------------------------------------------------------------------------


def test_required_valid_examples_accepted() -> None:
    body = _body()
    for example in body["examples"]["valid"]:
        assert _is_valid_condition(example, body), f"valid example rejected: {example!r}"


def test_required_invalid_examples_rejected() -> None:
    body = _body()
    for case in body["examples"]["invalid"]:
        assert "reason" in case, f"invalid example missing a reason: {case!r}"
        assert not _is_valid_condition(case["value"], body), (
            f"invalid condition accepted ({case['reason']}): {case['value']!r}"
        )


def test_invalid_examples_cover_required_cases() -> None:
    reasons = " ".join(case["reason"] for case in _body()["examples"]["invalid"]).lower()
    assert "missing required condition_id" in reasons
    assert "empty condition_id" in reasons
    assert "missing required field_path" in reasons
    assert "malformed field path" in reasons
    assert "missing required operator" in reasons
    assert "malformed operator" in reasons
    assert "missing required expected value" in reasons
    assert "unsupported value shape" in reasons
    assert "unknown field" in reasons
    assert "script" in reasons


# ---------------------------------------------------------------------------
# Package integration
# ---------------------------------------------------------------------------


def test_new_condition_contract_is_tracked_in_metadata() -> None:
    assert "policy-condition" in basis_schemas.OPERATION_AWARE_POLICY_CONTRACTS
    assert "policy-condition" not in basis_schemas.PLANNED_CONTRACTS
    assert "policy-condition" not in basis_schemas.PUBLISHED_CONTRACTS
    assert "policy-condition" not in basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS
    assert "policy-condition" not in basis_schemas.OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS
    assert "policy-condition" not in basis_schemas.OPERATION_AWARE_REQUEST_CONTRACTS


def test_repository_layout_updated() -> None:
    assert CONDITION_DIR.is_dir()
    assert (CONDITION_DIR / "policy-condition.yaml").is_file()
    assert (REPO_ROOT / "docs" / "policy-condition.md").is_file()
