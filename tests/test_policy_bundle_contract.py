"""Focused checks on the published policy-bundle contract.

These tests validate ``schemas/policy-bundle/policy-bundle.yaml`` (PR D of
`basis-architecture`'s operation-aware schema readiness plan, ADR-0005): its
metadata, its declared dependencies, that its published field policy accepts
well-formed bundles and rejects malformed ones, that bundle_version and
schema_version are distinct validated fields, that scope is optional with
documented global-scope semantics, that rules must be non-empty with
bundle-level duplicate-rule-id rejection, that no self-asserted
validation_status field exists, and that this contract never defines a
raw-secret or executable-policy field.

This is a contract publication, not a parser: the only behavior exercised
here is applying the contract's own published rules to example bundle
objects, including nested policy-rule-shaped values.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import basis_schemas

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
BUNDLE_DIR = REPO_ROOT / "schemas" / "policy-bundle"
BUNDLE_FILE = BUNDLE_DIR / "policy-bundle.yaml"
RULE_FILE = REPO_ROOT / "schemas" / "policy-rule" / "policy-rule.yaml"
CONDITION_FILE = REPO_ROOT / "schemas" / "policy-condition" / "policy-condition.yaml"

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
    "validation_status",
)


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict), f"{path} must parse to a mapping"
    return data


def _load() -> dict:
    return _load_yaml(BUNDLE_FILE)


def _body() -> dict:
    return _load()["policy_bundle"]


def _rule_body() -> dict:
    return _load_yaml(RULE_FILE)["policy_rule"]


def _condition_body() -> dict:
    return _load_yaml(CONDITION_FILE)["policy_condition"]


def _field(fields: list, field_id: str) -> dict:
    for field in fields:
        if field["id"] == field_id:
            return field
    raise AssertionError(f"field {field_id!r} not declared")


SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
DATE_TIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")


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


def _is_valid_match(obj: object, rule_body: dict) -> bool:
    shape = rule_body["match_shape"]
    if not isinstance(obj, dict):
        return False
    if set(obj) - set(shape["optional"]):
        return False
    if not obj:
        return False
    fields_by_id = {f["id"]: f for f in shape["fields"]}
    for key, value in obj.items():
        field = fields_by_id[key]
        if not isinstance(value, list) or not value:
            return False
        if not all(isinstance(item, str) for item in value):
            return False
        if "pattern" in field and not all(re.match(field["pattern"], item) for item in value):
            return False
        if key == "operation_intents" and not all(
            item in rule_body["operation_intent_values"] for item in value
        ):
            return False
    return True


def _is_valid_rule(obj: object, rule_body: dict, condition_body: dict) -> bool:
    if not isinstance(obj, dict):
        return False
    allowed = set(rule_body["required"]) | set(rule_body["optional"])
    if set(obj) - allowed:
        return False
    if any(field not in obj for field in rule_body["required"]):
        return False
    rule_id = obj.get("rule_id")
    if not isinstance(rule_id, str) or not rule_id.strip():
        return False
    if obj.get("effect") not in ("allow", "deny"):
        return False
    has_match = "match" in obj and obj["match"] is not None
    has_conditions = "conditions" in obj and obj["conditions"] is not None
    if not has_match and not has_conditions:
        return False
    if has_match and not _is_valid_match(obj["match"], rule_body):
        return False
    if has_conditions:
        conditions = obj["conditions"]
        if not isinstance(conditions, list) or not conditions:
            return False
        seen = set()
        for condition in conditions:
            if not _is_valid_condition(condition, condition_body):
                return False
            cid = condition.get("condition_id") if isinstance(condition, dict) else None
            if cid in seen:
                return False
            seen.add(cid)
    if "reason_code" in obj and obj["reason_code"] is not None:
        if not isinstance(obj["reason_code"], str) or not re.match(
            rule_body["reason_code_pattern"], obj["reason_code"]
        ):
            return False
    if "explanation" in obj and obj["explanation"] is not None:
        if not isinstance(obj["explanation"], str) or not obj["explanation"].strip():
            return False
    return True


def _is_valid_scope(obj: object, body: dict) -> bool:
    shape = body["scope_shape"]
    if not isinstance(obj, dict):
        return False
    if set(obj) - set(shape["optional"]):
        return False
    if not obj:
        return False
    fields_by_id = {f["id"]: f for f in shape["fields"]}
    for key, value in obj.items():
        field = fields_by_id[key]
        if not isinstance(value, list) or not value:
            return False
        if not all(isinstance(item, str) for item in value):
            return False
        if "pattern" in field and not all(re.match(field["pattern"], item) for item in value):
            return False
    return True


def _is_valid_bundle(obj: object, body: dict, rule_body: dict, condition_body: dict) -> bool:
    if not isinstance(obj, dict):
        return False

    allowed = set(body["required"]) | set(body["optional"])
    if not body["additional_properties"] and set(obj) - allowed:
        return False
    if any(field not in obj for field in body["required"]):
        return False

    bundle_id = obj.get("bundle_id")
    if not isinstance(bundle_id, str) or not bundle_id.strip():
        return False

    bundle_version = obj.get("bundle_version")
    if not isinstance(bundle_version, str) or not SEMVER_PATTERN.match(bundle_version):
        return False

    schema_version = obj.get("schema_version")
    if not isinstance(schema_version, str) or not SEMVER_PATTERN.match(schema_version):
        return False

    policy_owner = obj.get("policy_owner")
    if not isinstance(policy_owner, str) or not policy_owner.strip():
        return False

    if "scope" in obj and obj["scope"] is not None:
        if not _is_valid_scope(obj["scope"], body):
            return False

    rules = obj.get("rules")
    if not isinstance(rules, list) or not rules:
        return False
    seen_rule_ids = set()
    for rule in rules:
        if not _is_valid_rule(rule, rule_body, condition_body):
            return False
        rid = rule.get("rule_id") if isinstance(rule, dict) else None
        if rid in seen_rule_ids:
            return False
        seen_rule_ids.add(rid)

    for key in ("description", "source_ref", "approval_ref", "compatibility_target", "replaced_by"):
        if key in obj and obj[key] is not None:
            if not isinstance(obj[key], str) or not obj[key].strip():
                return False

    for key in ("created_at", "updated_at"):
        if key in obj and obj[key] is not None:
            if not isinstance(obj[key], str) or not DATE_TIME_PATTERN.match(obj[key]):
                return False

    if "deprecated" in obj and obj["deprecated"] is not None:
        if not isinstance(obj["deprecated"], bool):
            return False

    return True


# ---------------------------------------------------------------------------
# File / parsing
# ---------------------------------------------------------------------------


def test_policy_bundle_file_exists() -> None:
    assert BUNDLE_FILE.is_file(), "schemas/policy-bundle/policy-bundle.yaml must exist"


def test_policy_bundle_yaml_parses() -> None:
    assert _load()


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


def test_contract_metadata_matches_expected_values() -> None:
    contract = _load()["contract"]
    assert contract["name"] == "policy-bundle"
    assert contract["title"] == "BASIS Policy Bundle"
    assert contract["version"] == "0.1.0"
    assert contract["governed_by"] == "basis-architecture"
    assert contract["published_by"] == "basis-schemas"
    assert contract["source"] == "docs/architecture/operation-aware-schema-readiness-plan.md"
    assert isinstance(contract.get("description"), str) and contract["description"].strip()


def test_lifecycle_is_experimental() -> None:
    assert _load()["contract"]["lifecycle"] == "experimental"


def test_contract_metadata_dependencies_are_exact() -> None:
    depends_on = _load()["contract"].get("depends_on")
    assert depends_on == ["contract-metadata", "policy-rule"]


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------


def test_required_fields_are_exact() -> None:
    assert _body()["required"] == [
        "bundle_id",
        "bundle_version",
        "schema_version",
        "policy_owner",
        "rules",
    ]


def test_optional_fields_are_exact() -> None:
    assert _body()["optional"] == [
        "scope",
        "description",
        "source_ref",
        "approval_ref",
        "created_at",
        "updated_at",
        "compatibility_target",
        "deprecated",
        "replaced_by",
    ]


def test_unknown_fields_are_rejected_by_policy() -> None:
    assert _body()["additional_properties"] is False


def test_scope_shape_rejects_unknown_fields() -> None:
    assert _body()["scope_shape"]["additional_properties"] is False


def test_no_validation_status_field_published() -> None:
    field_ids = {f["id"] for f in _body()["fields"]}
    assert "validation_status" not in field_ids
    assert "validation_status" not in _body()["required"]
    assert "validation_status" not in _body()["optional"]


def test_every_field_has_a_description() -> None:
    body = _body()
    for field in body["fields"]:
        assert isinstance(field.get("description"), str) and field["description"].strip()
    for field in body["scope_shape"]["fields"]:
        assert isinstance(field.get("description"), str) and field["description"].strip()


def test_no_unrestricted_extension_bag() -> None:
    field_ids = {f["id"] for f in _body()["fields"]}
    scope_field_ids = {f["id"] for f in _body()["scope_shape"]["fields"]}
    for speculative in ("metadata", "extensions", "extra", "arbitrary", "custom_fields", "context"):
        assert speculative not in field_ids
        assert speculative not in scope_field_ids


# ---------------------------------------------------------------------------
# Bundle ID
# ---------------------------------------------------------------------------


def _minimal_rules() -> list:
    return [{"rule_id": "rule-min", "effect": "allow", "match": {"actions": ["read:ahu"]}}]


def test_missing_bundle_id_rejected() -> None:
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    bundle = {
        "bundle_version": "1.0.0",
        "schema_version": "0.1.0",
        "policy_owner": "team",
        "rules": _minimal_rules(),
    }
    assert not _is_valid_bundle(bundle, body, rbody, cbody)


def test_empty_bundle_id_rejected() -> None:
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    bundle = {
        "bundle_id": "",
        "bundle_version": "1.0.0",
        "schema_version": "0.1.0",
        "policy_owner": "team",
        "rules": _minimal_rules(),
    }
    assert not _is_valid_bundle(bundle, body, rbody, cbody)


# ---------------------------------------------------------------------------
# Bundle version / schema version
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("version", ["1.0.0", "0.1.0", "10.20.30"])
def test_valid_bundle_version_accepted(version: str) -> None:
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    bundle = {
        "bundle_id": "bundle-1",
        "bundle_version": version,
        "schema_version": "0.1.0",
        "policy_owner": "team",
        "rules": _minimal_rules(),
    }
    assert _is_valid_bundle(bundle, body, rbody, cbody)


@pytest.mark.parametrize("version", ["v1", "1.0", "1", "", "1.0.0-beta"])
def test_invalid_bundle_version_rejected(version: str) -> None:
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    bundle = {
        "bundle_id": "bundle-1",
        "bundle_version": version,
        "schema_version": "0.1.0",
        "policy_owner": "team",
        "rules": _minimal_rules(),
    }
    assert not _is_valid_bundle(bundle, body, rbody, cbody)


@pytest.mark.parametrize("version", ["current", "0.1", ""])
def test_invalid_schema_version_rejected(version: str) -> None:
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    bundle = {
        "bundle_id": "bundle-1",
        "bundle_version": "1.0.0",
        "schema_version": version,
        "policy_owner": "team",
        "rules": _minimal_rules(),
    }
    assert not _is_valid_bundle(bundle, body, rbody, cbody)


def test_bundle_version_and_schema_version_are_distinct_fields() -> None:
    assert "bundle_version" in _body()["required"]
    assert "schema_version" in _body()["required"]
    bundle_version_field = _field(_body()["fields"], "bundle_version")
    schema_version_field = _field(_body()["fields"], "schema_version")
    assert bundle_version_field is not schema_version_field
    assert "distinct" in bundle_version_field["description"].lower() or (
        "distinct" in schema_version_field["description"].lower()
    )


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------


def test_missing_owner_rejected() -> None:
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    bundle = {
        "bundle_id": "bundle-1",
        "bundle_version": "1.0.0",
        "schema_version": "0.1.0",
        "rules": _minimal_rules(),
    }
    assert not _is_valid_bundle(bundle, body, rbody, cbody)


def test_policy_owner_is_provenance_not_authz_subject() -> None:
    field = _field(_body()["fields"], "policy_owner")
    description = field["description"].lower()
    assert "not" in description and "authorization subject" in description


# ---------------------------------------------------------------------------
# Scope: optional, global-scope semantics
# ---------------------------------------------------------------------------


def test_scope_is_optional() -> None:
    assert "scope" in _body()["optional"]
    assert "scope" not in _body()["required"]


def test_absent_scope_is_globally_applicable_and_valid() -> None:
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    bundle = {
        "bundle_id": "bundle-global",
        "bundle_version": "1.0.0",
        "schema_version": "0.1.0",
        "policy_owner": "team",
        "rules": _minimal_rules(),
    }
    assert _is_valid_bundle(bundle, body, rbody, cbody)
    assert _body()["scope_semantics"]["absent_scope"] == "globally_applicable"


def test_present_scope_restricts_applicability_documented() -> None:
    semantics = _body()["scope_semantics"]
    assert semantics["present_scope"] == "applicable_if_all_populated_selectors_match"
    assert semantics["non_matching_scope_outcome"] == "not_applicable"


def test_empty_scope_object_rejected() -> None:
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    bundle = {
        "bundle_id": "bundle-1",
        "bundle_version": "1.0.0",
        "schema_version": "0.1.0",
        "policy_owner": "team",
        "scope": {},
        "rules": _minimal_rules(),
    }
    assert not _is_valid_bundle(bundle, body, rbody, cbody)
    assert _body()["scope_semantics"]["empty_scope_object"] == "invalid"


def test_valid_scope_accepted() -> None:
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    bundle = {
        "bundle_id": "bundle-scoped",
        "bundle_version": "1.0.0",
        "schema_version": "0.1.0",
        "policy_owner": "team",
        "scope": {"site_ids": ["west-campus"], "resource_types": ["hvac"]},
        "rules": _minimal_rules(),
    }
    assert _is_valid_bundle(bundle, body, rbody, cbody)


def test_malformed_scope_unknown_selector_rejected() -> None:
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    bundle = {
        "bundle_id": "bundle-scoped",
        "bundle_version": "1.0.0",
        "schema_version": "0.1.0",
        "policy_owner": "team",
        "scope": {"country": "not-a-published-selector"},
        "rules": _minimal_rules(),
    }
    assert not _is_valid_bundle(bundle, body, rbody, cbody)


def test_malformed_scope_pattern_rejected() -> None:
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    bundle = {
        "bundle_id": "bundle-scoped",
        "bundle_version": "1.0.0",
        "schema_version": "0.1.0",
        "policy_owner": "team",
        "scope": {"protocols": ["BACnet"]},
        "rules": _minimal_rules(),
    }
    assert not _is_valid_bundle(bundle, body, rbody, cbody)


def test_scope_distinct_from_rule_match() -> None:
    # Scope determines bundle applicability; match (published by
    # policy-rule) determines which rules inside an applicable bundle are
    # candidates. The two shapes are declared independently.
    scope_selectors = set(_body()["scope_shape"]["optional"])
    match_selectors = set(_rule_body()["match_shape"]["optional"])
    assert scope_selectors <= match_selectors | {
        "actions",
        "resource_types",
        "site_ids",
        "building_ids",
        "zone_ids",
        "area_ids",
        "device_classes",
        "environment_modes",
        "authority_modes",
        "protocols",
    }
    assert scope_selectors != match_selectors


# ---------------------------------------------------------------------------
# Rules: required, non-empty, duplicate-ID rejection
# ---------------------------------------------------------------------------


def test_missing_rules_rejected() -> None:
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    bundle = {
        "bundle_id": "bundle-1",
        "bundle_version": "1.0.0",
        "schema_version": "0.1.0",
        "policy_owner": "team",
    }
    assert not _is_valid_bundle(bundle, body, rbody, cbody)


def test_empty_rules_rejected() -> None:
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    bundle = {
        "bundle_id": "bundle-1",
        "bundle_version": "1.0.0",
        "schema_version": "0.1.0",
        "policy_owner": "team",
        "rules": [],
    }
    assert not _is_valid_bundle(bundle, body, rbody, cbody)


def test_valid_nested_rules_accepted() -> None:
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    bundle = {
        "bundle_id": "bundle-1",
        "bundle_version": "1.0.0",
        "schema_version": "0.1.0",
        "policy_owner": "team",
        "rules": [
            {"rule_id": "rule-allow", "effect": "allow", "match": {"actions": ["read:ahu"]}},
            {
                "rule_id": "rule-deny",
                "effect": "deny",
                "match": {"safety_modes": ["interlock-engaged"]},
            },
        ],
    }
    assert _is_valid_bundle(bundle, body, rbody, cbody)


def test_malformed_nested_rule_rejected() -> None:
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    bundle = {
        "bundle_id": "bundle-1",
        "bundle_version": "1.0.0",
        "schema_version": "0.1.0",
        "policy_owner": "team",
        "rules": [
            {"rule_id": "rule-bad-effect", "effect": "permit", "match": {"actions": ["read:ahu"]}}
        ],
    }
    assert not _is_valid_bundle(bundle, body, rbody, cbody)


def test_duplicate_rule_ids_rejected() -> None:
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    bundle = {
        "bundle_id": "bundle-1",
        "bundle_version": "1.0.0",
        "schema_version": "0.1.0",
        "policy_owner": "team",
        "rules": [
            {"rule_id": "rule-dup", "effect": "allow", "match": {"actions": ["read:ahu"]}},
            {"rule_id": "rule-dup", "effect": "deny", "match": {"actions": ["write:ahu"]}},
        ],
    }
    assert not _is_valid_bundle(bundle, body, rbody, cbody)


def test_condition_id_uniqueness_is_scoped_within_rule_not_across_bundle() -> None:
    # condition_id uniqueness is a RULE-level concern only. Two distinct rules
    # in the same bundle may each use the same condition_id string; the bundle
    # imposes no global condition-id uniqueness requirement. This proves the
    # scoping is within-rule, not accidentally bundle-wide.
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    shared_condition = {
        "condition_id": "cond-shared",
        "field_path": "risk_context.score",
        "operator": "greater_than",
        "expected_value": 0.8,
    }
    bundle = {
        "bundle_id": "bundle-shared-condition-ids",
        "bundle_version": "1.0.0",
        "schema_version": "0.1.0",
        "policy_owner": "team",
        "rules": [
            {"rule_id": "rule-a", "effect": "deny", "conditions": [dict(shared_condition)]},
            {"rule_id": "rule-b", "effect": "deny", "conditions": [dict(shared_condition)]},
        ],
    }
    assert _is_valid_bundle(bundle, body, rbody, cbody)


def test_scope_shape_selector_patterns_match_reproduced_constants() -> None:
    # Field-level parity guard for scope selectors, mirroring the rule-level
    # guard: a scope field's pattern cannot silently diverge from the
    # top-level reproduced (and parity-tested) constant.
    body = _body()
    fields_by_id = {f["id"]: f for f in body["scope_shape"]["fields"]}
    assert fields_by_id["actions"]["pattern"] == body["action_pattern"]
    assert fields_by_id["resource_types"]["pattern"] == body["resource_type_pattern"]
    for selector in ("device_classes", "environment_modes", "authority_modes", "protocols"):
        assert fields_by_id[selector]["pattern"] == body["open_identifier_pattern"], selector


def test_rule_shape_parity_with_standalone_policy_rule() -> None:
    rbody, cbody = _rule_body(), _condition_body()
    for example in rbody["examples"]["valid"]:
        assert _is_valid_rule(example, rbody, cbody)
        body = _body()
        bundle = {
            "bundle_id": "bundle-parity",
            "bundle_version": "1.0.0",
            "schema_version": "0.1.0",
            "policy_owner": "team",
            "rules": [example],
        }
        assert _is_valid_bundle(bundle, body, rbody, cbody)


# ---------------------------------------------------------------------------
# Metadata / provenance
# ---------------------------------------------------------------------------


def test_optional_metadata_fields_accept_valid_values() -> None:
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    bundle = {
        "bundle_id": "bundle-1",
        "bundle_version": "1.0.0",
        "schema_version": "0.1.0",
        "policy_owner": "team",
        "description": "A description.",
        "source_ref": "authoring/bundle-1",
        "approval_ref": "change-123",
        "created_at": "2026-05-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "compatibility_target": "basis-core>=0.2.0",
        "rules": _minimal_rules(),
    }
    assert _is_valid_bundle(bundle, body, rbody, cbody)


def test_empty_description_rejected() -> None:
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    bundle = {
        "bundle_id": "bundle-1",
        "bundle_version": "1.0.0",
        "schema_version": "0.1.0",
        "policy_owner": "team",
        "description": "",
        "rules": _minimal_rules(),
    }
    assert not _is_valid_bundle(bundle, body, rbody, cbody)


def test_malformed_created_at_rejected() -> None:
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    bundle = {
        "bundle_id": "bundle-1",
        "bundle_version": "1.0.0",
        "schema_version": "0.1.0",
        "policy_owner": "team",
        "created_at": "2026-05-01",
        "rules": _minimal_rules(),
    }
    assert not _is_valid_bundle(bundle, body, rbody, cbody)


# ---------------------------------------------------------------------------
# Deprecation
# ---------------------------------------------------------------------------


def test_deprecated_and_replaced_by_accepted() -> None:
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    bundle = {
        "bundle_id": "bundle-legacy",
        "bundle_version": "1.0.0",
        "schema_version": "0.1.0",
        "policy_owner": "team",
        "deprecated": True,
        "replaced_by": "bundle-new",
        "rules": _minimal_rules(),
    }
    assert _is_valid_bundle(bundle, body, rbody, cbody)


def test_deprecated_wrong_type_rejected() -> None:
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    bundle = {
        "bundle_id": "bundle-legacy",
        "bundle_version": "1.0.0",
        "schema_version": "0.1.0",
        "policy_owner": "team",
        "deprecated": "yes",
        "rules": _minimal_rules(),
    }
    assert not _is_valid_bundle(bundle, body, rbody, cbody)


def test_deprecated_defaults_to_false() -> None:
    field = _field(_body()["fields"], "deprecated")
    assert field["default"] is False


# ---------------------------------------------------------------------------
# Secret / executable regression
# ---------------------------------------------------------------------------


def test_no_forbidden_secret_or_executable_fields_defined_anywhere() -> None:
    body = _body()
    field_ids = {f["id"] for f in body["fields"]}
    field_ids |= {f["id"] for f in body["scope_shape"]["fields"]}
    for forbidden in FORBIDDEN_FIELDS:
        assert forbidden not in field_ids, f"forbidden field defined on contract: {forbidden!r}"


def test_credential_field_rejected_as_unknown() -> None:
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    bundle = {
        "bundle_id": "bundle-1",
        "bundle_version": "1.0.0",
        "schema_version": "0.1.0",
        "policy_owner": "team",
        "private_key": "-----BEGIN PRIVATE KEY-----",
        "rules": _minimal_rules(),
    }
    assert not _is_valid_bundle(bundle, body, rbody, cbody)


# ---------------------------------------------------------------------------
# Examples
# ---------------------------------------------------------------------------


def test_required_valid_examples_accepted() -> None:
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    for example in body["examples"]["valid"]:
        assert _is_valid_bundle(example, body, rbody, cbody), f"valid example rejected: {example!r}"


def test_required_invalid_examples_rejected() -> None:
    body, rbody, cbody = _body(), _rule_body(), _condition_body()
    for case in body["examples"]["invalid"]:
        assert "reason" in case, f"invalid example missing a reason: {case!r}"
        assert not _is_valid_bundle(case["value"], body, rbody, cbody), (
            f"invalid bundle accepted ({case['reason']}): {case['value']!r}"
        )


def test_invalid_examples_cover_required_cases() -> None:
    reasons = " ".join(case["reason"] for case in _body()["examples"]["invalid"]).lower()
    assert "missing bundle id" in reasons
    assert "empty bundle id" in reasons
    assert "invalid bundle version" in reasons
    assert "invalid schema version" in reasons
    assert "missing owner" in reasons
    assert "missing rules" in reasons
    assert "empty rules" in reasons
    assert "duplicate rule id" in reasons
    assert "malformed scope" in reasons
    assert "malformed nested rule" in reasons
    assert "unknown field" in reasons
    assert "credential" in reasons or "private" in reasons


def test_deprecated_example_present() -> None:
    valid_examples = _body()["examples"]["valid"]
    assert any(example.get("deprecated") is True for example in valid_examples)


# ---------------------------------------------------------------------------
# Package integration
# ---------------------------------------------------------------------------


def test_new_bundle_contract_is_tracked_in_metadata() -> None:
    assert "policy-bundle" in basis_schemas.OPERATION_AWARE_POLICY_CONTRACTS
    assert "policy-bundle" not in basis_schemas.PLANNED_CONTRACTS
    assert "policy-bundle" not in basis_schemas.PUBLISHED_CONTRACTS


def test_repository_layout_updated() -> None:
    assert BUNDLE_DIR.is_dir()
    assert (BUNDLE_DIR / "policy-bundle.yaml").is_file()
    assert (REPO_ROOT / "docs" / "policy-bundle.md").is_file()


def test_operation_aware_policy_contracts_publication_order() -> None:
    assert basis_schemas.OPERATION_AWARE_POLICY_CONTRACTS == (
        "policy-condition",
        "policy-rule",
        "policy-bundle",
    )
