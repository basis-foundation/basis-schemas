"""Focused checks on the published policy-rule contract.

These tests validate ``schemas/policy-rule/policy-rule.yaml`` (PR D of
`basis-architecture`'s operation-aware schema readiness plan, ADR-0005): its
metadata, its declared dependencies, that its published field policy accepts
well-formed rules and rejects malformed ones, that effect is closed to
exactly allow/deny (never not_applicable), that match criteria and conditions
reuse — rather than diverge from — operation-aware-decision-request,
action-string, resource-identifier, reason-code, and policy-condition, that
no rule is permitted without at least one of match or conditions, and that
this contract never defines a raw-secret, priority, or executable-policy
field.

This is a contract publication, not a parser: the only behavior exercised
here is applying the contract's own published rules to example rule objects.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import basis_schemas

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
RULE_DIR = REPO_ROOT / "schemas" / "policy-rule"
RULE_FILE = RULE_DIR / "policy-rule.yaml"
CONDITION_FILE = REPO_ROOT / "schemas" / "policy-condition" / "policy-condition.yaml"
ACTION_STRING_FILE = REPO_ROOT / "schemas" / "action-string" / "action-string.yaml"
RESOURCE_IDENTIFIER_FILE = (
    REPO_ROOT / "schemas" / "resource-identifier" / "resource-identifier.yaml"
)
OADR_FILE = (
    REPO_ROOT
    / "schemas"
    / "operation-aware-decision-request"
    / "operation-aware-decision-request.yaml"
)
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
    "raw_claims",
    "full_claim_set",
    "raw_payload",
    "raw_protocol_payload",
    "device_secret",
    "credential",
    "script",
    "code",
    "executable",
    "expression",
    "priority",
)


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict), f"{path} must parse to a mapping"
    return data


def _load() -> dict:
    return _load_yaml(RULE_FILE)


def _body() -> dict:
    return _load()["policy_rule"]


def _condition_body() -> dict:
    return _load_yaml(CONDITION_FILE)["policy_condition"]


def _field(fields: list, field_id: str) -> dict:
    for field in fields:
        if field["id"] == field_id:
            return field
    raise AssertionError(f"field {field_id!r} not declared")


def _is_valid_expected_value(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        if not value:
            return True
        normalized_types = set()
        for item in value:
            if isinstance(item, bool):
                normalized_types.add(bool)
            elif isinstance(item, (int, float)):
                normalized_types.add("number")
            elif isinstance(item, str):
                normalized_types.add(str)
            else:
                return False
        return len(normalized_types) == 1
    return False


def _is_valid_condition(obj: object, condition_body: dict) -> bool:
    if not isinstance(obj, dict):
        return False
    required = condition_body["required"]
    optional = condition_body["optional"]
    allowed = set(required) | set(optional)
    if set(obj) - allowed:
        return False
    if any(field not in obj for field in required):
        return False

    condition_id = obj.get("condition_id")
    if not isinstance(condition_id, str) or not condition_id.strip():
        return False
    field_path = obj.get("field_path")
    if not isinstance(field_path, str) or not re.match(
        condition_body["field_path_pattern"], field_path
    ):
        return False
    operator = obj.get("operator")
    if not isinstance(operator, str) or not re.match(condition_body["operator_pattern"], operator):
        return False
    if "expected_value" not in obj or not _is_valid_expected_value(obj["expected_value"]):
        return False
    return True


def _is_valid_match(obj: object, body: dict) -> bool:
    shape = body["match_shape"]
    if not isinstance(obj, dict):
        return False
    if set(obj) - set(shape["optional"]):
        return False
    if not obj:
        # Empty match object: no populated selector.
        return False

    fields_by_id = {f["id"]: f for f in shape["fields"]}
    for key, value in obj.items():
        field = fields_by_id[key]
        if not isinstance(value, list):
            return False
        if not value:
            return False
        if not all(isinstance(item, str) for item in value):
            return False
        if "pattern" in field:
            if not all(re.match(field["pattern"], item) for item in value):
                return False
        if key == "operation_intents":
            if not all(item in body["operation_intent_values"] for item in value):
                return False
    return True


def _is_valid_rule(obj: object, body: dict, condition_body: dict) -> bool:
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

    effect = obj.get("effect")
    if effect not in ("allow", "deny"):
        return False

    has_match = "match" in obj and obj["match"] is not None
    has_conditions = "conditions" in obj and obj["conditions"] is not None
    if not has_match and not has_conditions:
        return False

    if has_match:
        if not _is_valid_match(obj["match"], body):
            return False

    if has_conditions:
        conditions = obj["conditions"]
        if not isinstance(conditions, list) or not conditions:
            return False
        seen_ids = set()
        for condition in conditions:
            if not _is_valid_condition(condition, condition_body):
                return False
            cid = condition.get("condition_id") if isinstance(condition, dict) else None
            if cid in seen_ids:
                return False
            seen_ids.add(cid)

    if "reason_code" in obj and obj["reason_code"] is not None:
        reason_code = obj["reason_code"]
        if not isinstance(reason_code, str) or not re.match(
            body["reason_code_pattern"], reason_code
        ):
            return False

    if "explanation" in obj and obj["explanation"] is not None:
        explanation = obj["explanation"]
        if not isinstance(explanation, str) or not explanation.strip():
            return False

    return True


# ---------------------------------------------------------------------------
# File / parsing
# ---------------------------------------------------------------------------


def test_policy_rule_file_exists() -> None:
    assert RULE_FILE.is_file(), "schemas/policy-rule/policy-rule.yaml must exist"


def test_policy_rule_yaml_parses() -> None:
    assert _load()


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


def test_contract_metadata_matches_expected_values() -> None:
    contract = _load()["contract"]
    assert contract["name"] == "policy-rule"
    assert contract["title"] == "BASIS Policy Rule"
    assert contract["version"] == "0.1.0"
    assert contract["governed_by"] == "basis-architecture"
    assert contract["published_by"] == "basis-schemas"
    assert contract["source"] == "docs/architecture/operation-aware-schema-readiness-plan.md"
    assert isinstance(contract.get("description"), str) and contract["description"].strip()


def test_lifecycle_is_experimental() -> None:
    assert _load()["contract"]["lifecycle"] == "experimental"


def test_contract_metadata_dependencies_are_exact() -> None:
    depends_on = _load()["contract"].get("depends_on")
    assert depends_on == [
        "contract-metadata",
        "policy-condition",
        "operation-aware-decision-request",
        "reason-code",
        "action-string",
        "resource-identifier",
    ]


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------


def test_required_fields_are_exact() -> None:
    assert _body()["required"] == ["rule_id", "effect"]


def test_optional_fields_are_exact() -> None:
    assert _body()["optional"] == ["match", "conditions", "reason_code", "explanation"]


def test_unknown_fields_are_rejected_by_policy() -> None:
    assert _body()["additional_properties"] is False


def test_required_at_least_one_declared() -> None:
    assert _body()["required_at_least_one"] == ["match", "conditions"]


def test_match_shape_rejects_unknown_fields() -> None:
    assert _body()["match_shape"]["additional_properties"] is False


def test_every_field_has_a_description() -> None:
    body = _body()
    for field in body["fields"]:
        assert isinstance(field.get("description"), str) and field["description"].strip()
    for field in body["match_shape"]["fields"]:
        assert isinstance(field.get("description"), str) and field["description"].strip()


def test_no_unrestricted_extension_bag() -> None:
    field_ids = {f["id"] for f in _body()["fields"]}
    match_field_ids = {f["id"] for f in _body()["match_shape"]["fields"]}
    for speculative in ("metadata", "extensions", "extra", "arbitrary", "custom_fields", "context"):
        assert speculative not in field_ids
        assert speculative not in match_field_ids


# ---------------------------------------------------------------------------
# Rule ID
# ---------------------------------------------------------------------------


def test_missing_rule_id_rejected() -> None:
    body, cbody = _body(), _condition_body()
    rule = {"effect": "allow", "match": {"actions": ["read:ahu"]}}
    assert not _is_valid_rule(rule, body, cbody)


def test_empty_rule_id_rejected() -> None:
    body, cbody = _body(), _condition_body()
    rule = {"rule_id": "", "effect": "allow", "match": {"actions": ["read:ahu"]}}
    assert not _is_valid_rule(rule, body, cbody)


# ---------------------------------------------------------------------------
# Effect
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("effect", ["allow", "deny"])
def test_valid_effects_accepted(effect: str) -> None:
    body, cbody = _body(), _condition_body()
    rule = {"rule_id": "rule-effect", "effect": effect, "match": {"actions": ["read:ahu"]}}
    assert _is_valid_rule(rule, body, cbody)


@pytest.mark.parametrize("effect", ["permit", "ALLOW", "grant", ""])
def test_invalid_effects_rejected(effect: str) -> None:
    body, cbody = _body(), _condition_body()
    rule = {"rule_id": "rule-effect", "effect": effect, "match": {"actions": ["read:ahu"]}}
    assert not _is_valid_rule(rule, body, cbody)


def test_not_applicable_effect_rejected() -> None:
    body, cbody = _body(), _condition_body()
    rule = {
        "rule_id": "rule-effect",
        "effect": "not_applicable",
        "match": {"actions": ["read:ahu"]},
    }
    assert not _is_valid_rule(rule, body, cbody)


def test_effect_enum_is_exactly_allow_deny() -> None:
    effect_field = _field(_body()["fields"], "effect")
    assert effect_field["enum"] == ["allow", "deny"]


# ---------------------------------------------------------------------------
# Unconditional rules rejected
# ---------------------------------------------------------------------------


def test_rule_with_neither_match_nor_conditions_rejected() -> None:
    body, cbody = _body(), _condition_body()
    rule = {"rule_id": "rule-unconditional", "effect": "allow"}
    assert not _is_valid_rule(rule, body, cbody)


def test_rule_with_only_match_accepted() -> None:
    body, cbody = _body(), _condition_body()
    rule = {"rule_id": "rule-match-only", "effect": "allow", "match": {"actions": ["read:ahu"]}}
    assert _is_valid_rule(rule, body, cbody)


def test_rule_with_only_conditions_accepted() -> None:
    body, cbody = _body(), _condition_body()
    rule = {
        "rule_id": "rule-conditions-only",
        "effect": "deny",
        "conditions": [
            {
                "condition_id": "cond-1",
                "field_path": "risk_context.score",
                "operator": "greater_than",
                "expected_value": 0.8,
            }
        ],
    }
    assert _is_valid_rule(rule, body, cbody)


def test_empty_match_object_rejected() -> None:
    body, cbody = _body(), _condition_body()
    rule = {"rule_id": "rule-empty-match", "effect": "allow", "match": {}}
    assert not _is_valid_rule(rule, body, cbody)


def test_empty_conditions_array_rejected() -> None:
    body, cbody = _body(), _condition_body()
    rule = {"rule_id": "rule-empty-conditions", "effect": "allow", "conditions": []}
    assert not _is_valid_rule(rule, body, cbody)


def test_empty_match_and_empty_conditions_together_rejected() -> None:
    # Both present but both empty: neither an empty match object nor an empty
    # conditions array may satisfy the "at least one populated" invariant, even
    # in combination — this must not silently become an implicit match-all.
    body, cbody = _body(), _condition_body()
    rule = {
        "rule_id": "rule-both-empty",
        "effect": "allow",
        "match": {},
        "conditions": [],
    }
    assert not _is_valid_rule(rule, body, cbody)


# ---------------------------------------------------------------------------
# Match selectors
# ---------------------------------------------------------------------------


def test_match_shape_selectors_are_exact() -> None:
    assert _body()["match_shape"]["optional"] == [
        "subject_ids",
        "subject_roles",
        "identity_sources",
        "authority_modes",
        "actions",
        "resources",
        "resource_types",
        "site_ids",
        "building_ids",
        "zone_ids",
        "area_ids",
        "device_ids",
        "device_classes",
        "protocols",
        "protocol_operations",
        "operation_intents",
        "safety_modes",
        "safety_classifications",
        "environment_modes",
        "risk_classifications",
    ]


def test_empty_selector_array_rejected() -> None:
    body, cbody = _body(), _condition_body()
    rule = {"rule_id": "rule-empty-selector", "effect": "allow", "match": {"actions": []}}
    assert not _is_valid_rule(rule, body, cbody)


def test_non_array_selector_rejected() -> None:
    body, cbody = _body(), _condition_body()
    rule = {
        "rule_id": "rule-non-array-selector",
        "effect": "allow",
        "match": {"actions": "read:ahu"},
    }
    assert not _is_valid_rule(rule, body, cbody)


def test_malformed_selector_rejected() -> None:
    body, cbody = _body(), _condition_body()
    rule = {
        "rule_id": "rule-malformed-protocol",
        "effect": "allow",
        "match": {"protocols": ["BACnet"]},
    }
    assert not _is_valid_rule(rule, body, cbody)


def test_unknown_selector_key_rejected() -> None:
    body, cbody = _body(), _condition_body()
    rule = {
        "rule_id": "rule-unknown-selector",
        "effect": "allow",
        "match": {"tenant_ids": ["tenant-a"]},
    }
    assert not _is_valid_rule(rule, body, cbody)


def test_selector_with_nested_object_item_rejected() -> None:
    # A selector value must be a list of the selector's published primitive
    # type; an arbitrary nested object as an item is not accepted.
    body, cbody = _body(), _condition_body()
    rule = {
        "rule_id": "rule-nested-selector-item",
        "effect": "allow",
        "match": {"subject_ids": [{"nested": "object"}]},
    }
    assert not _is_valid_rule(rule, body, cbody)


def test_match_shape_selector_patterns_match_reproduced_constants() -> None:
    # Field-level parity guard: each patterned selector inside match_shape must
    # use exactly the pattern this contract reproduces at the top level, so a
    # field pattern cannot silently drift away from the parity-tested constant.
    body = _body()
    fields_by_id = {f["id"]: f for f in body["match_shape"]["fields"]}
    assert fields_by_id["actions"]["pattern"] == body["action_pattern"]
    assert fields_by_id["resources"]["pattern"] == body["resource_pattern"]
    assert fields_by_id["resource_types"]["pattern"] == body["resource_type_pattern"]
    for selector in (
        "authority_modes",
        "device_classes",
        "protocols",
        "safety_modes",
        "safety_classifications",
        "environment_modes",
        "risk_classifications",
    ):
        assert fields_by_id[selector]["pattern"] == body["open_identifier_pattern"], selector


# ---------------------------------------------------------------------------
# Cross-contract parity: action / resource / resource-type / operation-intent
# ---------------------------------------------------------------------------


def test_action_pattern_matches_published_action_string_contract() -> None:
    canonical = _load_yaml(ACTION_STRING_FILE)["action_string"]["pattern"]
    assert _body()["action_pattern"] == canonical


def test_resource_pattern_matches_published_resource_identifier_contract() -> None:
    canonical = _load_yaml(RESOURCE_IDENTIFIER_FILE)["resource_identifier"]["pattern"]
    assert _body()["resource_pattern"] == canonical


def test_resource_type_pattern_matches_resource_identifier_contract() -> None:
    canonical = _load_yaml(RESOURCE_IDENTIFIER_FILE)["resource_identifier"]["resource_type_pattern"]
    assert _body()["resource_type_pattern"] == canonical


def test_open_identifier_pattern_matches_oadr_contract() -> None:
    canonical = _load_yaml(OADR_FILE)["operation_aware_decision_request"]["open_identifier_pattern"]
    assert _body()["open_identifier_pattern"] == canonical


def test_operation_intent_values_match_oadr_contract() -> None:
    canonical = _load_yaml(OADR_FILE)["operation_aware_decision_request"]["operation_intent_values"]
    assert _body()["operation_intent_values"] == canonical


def test_reason_code_pattern_matches_reason_code_contract() -> None:
    canonical = _load_yaml(REASON_CODE_FILE)["reason_code"]["pattern"]
    assert _body()["reason_code_pattern"] == canonical


def test_valid_action_in_match_accepted() -> None:
    body, cbody = _body(), _condition_body()
    for action in ("read:ahu", "write:hvac:setpoint"):
        rule = {"rule_id": "rule-action", "effect": "allow", "match": {"actions": [action]}}
        assert _is_valid_rule(rule, body, cbody), f"valid action rejected: {action!r}"


def test_invalid_action_in_match_rejected() -> None:
    body, cbody = _body(), _condition_body()
    rule = {"rule_id": "rule-invalid-action", "effect": "allow", "match": {"actions": ["read"]}}
    assert not _is_valid_rule(rule, body, cbody)


def test_invalid_resource_in_match_rejected() -> None:
    body, cbody = _body(), _condition_body()
    rule = {
        "rule_id": "rule-invalid-resource",
        "effect": "allow",
        "match": {"resources": ["rooftop-1"]},
    }
    assert not _is_valid_rule(rule, body, cbody)


def test_valid_resource_type_in_match_accepted() -> None:
    body, cbody = _body(), _condition_body()
    rule = {"rule_id": "rule-res-type", "effect": "allow", "match": {"resource_types": ["hvac"]}}
    assert _is_valid_rule(rule, body, cbody)


def test_unsupported_operation_intent_rejected() -> None:
    body, cbody = _body(), _condition_body()
    rule = {
        "rule_id": "rule-bad-intent",
        "effect": "allow",
        "match": {"operation_intents": ["destructive"]},
    }
    assert not _is_valid_rule(rule, body, cbody)


def test_valid_operation_intents_accepted() -> None:
    body, cbody = _body(), _condition_body()
    for value in body["operation_intent_values"]:
        rule = {
            "rule_id": "rule-intent",
            "effect": "allow",
            "match": {"operation_intents": [value]},
        }
        assert _is_valid_rule(rule, body, cbody)


def test_valid_authority_mode_in_match_accepted() -> None:
    body, cbody = _body(), _condition_body()
    rule = {
        "rule_id": "rule-authority",
        "effect": "allow",
        "match": {"authority_modes": ["federated"]},
    }
    assert _is_valid_rule(rule, body, cbody)


def test_malformed_authority_mode_rejected() -> None:
    body, cbody = _body(), _condition_body()
    rule = {
        "rule_id": "rule-authority",
        "effect": "allow",
        "match": {"authority_modes": ["Federated"]},
    }
    assert not _is_valid_rule(rule, body, cbody)


def test_valid_device_class_in_match_accepted() -> None:
    body, cbody = _body(), _condition_body()
    rule = {
        "rule_id": "rule-device-class",
        "effect": "allow",
        "match": {"device_classes": ["controller"]},
    }
    assert _is_valid_rule(rule, body, cbody)


def test_malformed_device_class_rejected() -> None:
    body, cbody = _body(), _condition_body()
    rule = {
        "rule_id": "rule-device-class",
        "effect": "allow",
        "match": {"device_classes": ["Controller"]},
    }
    assert not _is_valid_rule(rule, body, cbody)


def test_valid_protocol_in_match_accepted() -> None:
    body, cbody = _body(), _condition_body()
    rule = {"rule_id": "rule-protocol", "effect": "allow", "match": {"protocols": ["bacnet"]}}
    assert _is_valid_rule(rule, body, cbody)


def test_protocol_operations_are_free_form_non_empty() -> None:
    body, cbody = _body(), _condition_body()
    rule = {
        "rule_id": "rule-protocol-op",
        "effect": "allow",
        "match": {"protocol_operations": ["WriteProperty"]},
    }
    assert _is_valid_rule(rule, body, cbody)


# ---------------------------------------------------------------------------
# Match semantics documentation
# ---------------------------------------------------------------------------


def test_match_semantics_documented() -> None:
    semantics = _body()["match_semantics"]
    assert semantics["within_selector"] == "any_of"
    assert semantics["across_selectors"] == "all_of"
    assert semantics["absent_selector"] == "no_restriction"
    assert semantics["empty_selector_list"] == "invalid"


# ---------------------------------------------------------------------------
# Conditions
# ---------------------------------------------------------------------------


def test_valid_conditions_accepted() -> None:
    body, cbody = _body(), _condition_body()
    rule = {
        "rule_id": "rule-cond",
        "effect": "deny",
        "conditions": [
            {
                "condition_id": "cond-1",
                "field_path": "risk_context.score",
                "operator": "greater_than",
                "expected_value": 0.8,
            }
        ],
    }
    assert _is_valid_rule(rule, body, cbody)


def test_malformed_condition_rejected() -> None:
    body, cbody = _body(), _condition_body()
    rule = {
        "rule_id": "rule-cond",
        "effect": "deny",
        "conditions": [
            {
                "condition_id": "cond-1",
                "field_path": "risk_context.score",
                "expected_value": 0.8,
            }
        ],
    }
    assert not _is_valid_rule(rule, body, cbody)


def test_duplicate_condition_ids_within_rule_rejected() -> None:
    body, cbody = _body(), _condition_body()
    rule = {
        "rule_id": "rule-dup-cond",
        "effect": "deny",
        "conditions": [
            {
                "condition_id": "cond-dup",
                "field_path": "risk_context.score",
                "operator": "greater_than",
                "expected_value": 0.8,
            },
            {
                "condition_id": "cond-dup",
                "field_path": "risk_context.classification",
                "operator": "equals",
                "expected_value": "elevated",
            },
        ],
    }
    assert not _is_valid_rule(rule, body, cbody)


def test_condition_shape_parity_with_standalone_policy_condition() -> None:
    # A condition valid on its own, per policy-condition's own examples, must
    # be equally valid when nested inside a rule's conditions array.
    cbody = _condition_body()
    for example in cbody["examples"]["valid"]:
        assert _is_valid_condition(example, cbody)
        body = _body()
        rule = {"rule_id": "rule-nested-cond", "effect": "deny", "conditions": [example]}
        assert _is_valid_rule(rule, body, cbody)


# ---------------------------------------------------------------------------
# Reason code
# ---------------------------------------------------------------------------


def test_reason_code_is_optional() -> None:
    assert "reason_code" in _body()["optional"]


def test_valid_reason_code_accepted() -> None:
    body, cbody = _body(), _condition_body()
    rule = {
        "rule_id": "rule-reason",
        "effect": "allow",
        "match": {"actions": ["read:ahu"]},
        "reason_code": "allow_rule_matched",
    }
    assert _is_valid_rule(rule, body, cbody)


def test_structurally_valid_future_reason_code_accepted() -> None:
    body, cbody = _body(), _condition_body()
    rule = {
        "rule_id": "rule-reason",
        "effect": "allow",
        "match": {"actions": ["read:ahu"]},
        "reason_code": "future_unrecognized_reason_code",
    }
    assert _is_valid_rule(rule, body, cbody)


def test_malformed_reason_code_rejected() -> None:
    body, cbody = _body(), _condition_body()
    rule = {
        "rule_id": "rule-reason",
        "effect": "allow",
        "match": {"actions": ["read:ahu"]},
        "reason_code": "ALLOW_RULE_MATCHED",
    }
    assert not _is_valid_rule(rule, body, cbody)


def test_no_new_closed_reason_code_vocabulary() -> None:
    reason_code_field = _field(_body()["fields"], "reason_code")
    assert "enum" not in reason_code_field


# ---------------------------------------------------------------------------
# Explanation
# ---------------------------------------------------------------------------


def test_explanation_is_optional_non_empty_string() -> None:
    field = _field(_body()["fields"], "explanation")
    assert field["required"] is False
    assert field["non_empty"] is True


def test_empty_explanation_rejected() -> None:
    body, cbody = _body(), _condition_body()
    rule = {
        "rule_id": "rule-explanation",
        "effect": "allow",
        "match": {"actions": ["read:ahu"]},
        "explanation": "",
    }
    assert not _is_valid_rule(rule, body, cbody)


def test_valid_explanation_accepted() -> None:
    body, cbody = _body(), _condition_body()
    rule = {
        "rule_id": "rule-explanation",
        "effect": "allow",
        "match": {"actions": ["read:ahu"]},
        "explanation": "Operators may read AHU telemetry.",
    }
    assert _is_valid_rule(rule, body, cbody)


# ---------------------------------------------------------------------------
# Rule ordering: deferred, not published
# ---------------------------------------------------------------------------


def test_no_priority_or_ordering_field_published() -> None:
    field_ids = {f["id"] for f in _body()["fields"]}
    for speculative in ("priority", "order", "weight", "rank", "sequence"):
        assert speculative not in field_ids


# ---------------------------------------------------------------------------
# Secret / executable regression
# ---------------------------------------------------------------------------


def test_no_forbidden_secret_or_executable_fields_defined_anywhere() -> None:
    body = _body()
    field_ids = {f["id"] for f in body["fields"]}
    field_ids |= {f["id"] for f in body["match_shape"]["fields"]}
    for forbidden in FORBIDDEN_FIELDS:
        assert forbidden not in field_ids, f"forbidden field defined on contract: {forbidden!r}"


# ---------------------------------------------------------------------------
# Examples
# ---------------------------------------------------------------------------


def test_required_valid_examples_accepted() -> None:
    body, cbody = _body(), _condition_body()
    for example in body["examples"]["valid"]:
        assert _is_valid_rule(example, body, cbody), f"valid example rejected: {example!r}"


def test_required_invalid_examples_rejected() -> None:
    body, cbody = _body(), _condition_body()
    for case in body["examples"]["invalid"]:
        assert "reason" in case, f"invalid example missing a reason: {case!r}"
        assert not _is_valid_rule(case["value"], body, cbody), (
            f"invalid rule accepted ({case['reason']}): {case['value']!r}"
        )


def test_invalid_examples_cover_required_cases() -> None:
    reasons = " ".join(case["reason"] for case in _body()["examples"]["invalid"]).lower()
    assert "missing required rule id" in reasons
    assert "empty rule id" in reasons
    assert "invalid effect" in reasons
    assert "not_applicable effect" in reasons
    assert "malformed selector" in reasons
    assert "invalid action" in reasons
    assert "invalid resource" in reasons
    assert "unsupported operation intent" in reasons
    assert "malformed reason code" in reasons
    assert "malformed condition" in reasons
    assert "unknown field" in reasons
    assert "script" in reasons


# ---------------------------------------------------------------------------
# Package integration
# ---------------------------------------------------------------------------


def test_new_rule_contract_is_tracked_in_metadata() -> None:
    assert "policy-rule" in basis_schemas.OPERATION_AWARE_POLICY_CONTRACTS
    assert "policy-rule" not in basis_schemas.PLANNED_CONTRACTS
    assert "policy-rule" not in basis_schemas.PUBLISHED_CONTRACTS


def test_repository_layout_updated() -> None:
    assert RULE_DIR.is_dir()
    assert (RULE_DIR / "policy-rule.yaml").is_file()
    assert (REPO_ROOT / "docs" / "policy-rule.md").is_file()
