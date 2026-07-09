"""Focused checks on the published operation-aware-decision-request contract.

These tests validate
``schemas/operation-aware-decision-request/operation-aware-decision-request.yaml``
(PR C of `basis-architecture`'s operation-aware schema readiness plan,
ADR-0005): its metadata, its declared dependencies, that its published field
policy accepts well-formed operation-aware requests and rejects malformed
ones, that it never defines a raw-secret or raw-evidence field, and that the
existing first-wave ``decision-request`` contract is unaffected by this
publication.

This is a contract publication, not a parser: the only behavior exercised
here is applying the contract's own published rules (required fields, the
no-unknown-fields policy at every nesting level, the reused
action-string/resource-identifier patterns, the reused evidence-reference
contracts' own rules, and the closed operation_intent vocabulary) to example
request objects.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

import basis_schemas

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
REQUEST_DIR = REPO_ROOT / "schemas" / "operation-aware-decision-request"
REQUEST_FILE = REQUEST_DIR / "operation-aware-decision-request.yaml"
DECISION_REQUEST_FILE = REPO_ROOT / "schemas" / "decision-request" / "decision-request.yaml"
ACTION_STRING_FILE = REPO_ROOT / "schemas" / "action-string" / "action-string.yaml"
RESOURCE_IDENTIFIER_FILE = (
    REPO_ROOT / "schemas" / "resource-identifier" / "resource-identifier.yaml"
)
IDENTITY_REFERENCE_FILE = (
    REPO_ROOT / "schemas" / "identity-evidence-reference" / "identity-evidence-reference.yaml"
)
ADAPTER_REFERENCE_FILE = (
    REPO_ROOT / "schemas" / "adapter-evidence-reference" / "adapter-evidence-reference.yaml"
)

#: Fields that must never appear on this contract, anywhere (top-level or
#: nested) — raw secrets, tokens, claim sets, or protocol payloads.
#: Regression coverage for the architecture's explicit prohibition list.
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
    "packet",
    "frame",
    "device_secret",
)


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict), f"{path} must parse to a mapping"
    return data


def _load() -> dict:
    return _load_yaml(REQUEST_FILE)


def _body() -> dict:
    return _load()["operation_aware_decision_request"]


def _field(fields: list, field_id: str) -> dict:
    for field in fields:
        if field["id"] == field_id:
            return field
    raise AssertionError(f"field {field_id!r} not declared")


#: Maps a contract-declared ``type`` token to the Python type(s) a value must
#: be an instance of. ``bool`` is deliberately excluded from ``number``:
#: Python's ``bool`` is a subclass of ``int``, so ``isinstance(True, int)``
#: is ``True`` — without excluding it explicitly, a boolean would silently
#: pass as a valid ``risk_context.score``, which the published contract does
#: not intend (its ``score`` field is numeric evidence, not a flag).
_PRIMITIVE_TYPE_CHECKS: dict[str, Callable[[Any], bool]] = {
    "string": lambda v: isinstance(v, str),
    "array": lambda v: isinstance(v, list),
    "object": lambda v: isinstance(v, dict),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
}


def _declared_types(field: dict) -> list[str]:
    """Return a field's declared, non-null type token(s).

    A field's ``type`` is either a single token (``"string"``) or a list
    that includes ``"null"`` for an optional/nullable field (``["string",
    "null"]``). This strips ``"null"`` — nullability is handled separately,
    by the caller checking ``value is None`` before any type comparison.
    """
    declared = field.get("type")
    if isinstance(declared, list):
        return [t for t in declared if t != "null"]
    return [declared] if declared else []


def _matches_declared_type(value: object, declared_types: list[str]) -> bool:
    if not declared_types:
        return True
    return any(
        _PRIMITIVE_TYPE_CHECKS[t](value) for t in declared_types if t in _PRIMITIVE_TYPE_CHECKS
    )


def _validate_object(
    obj: object,
    required: list,
    optional: list,
    additional_properties: bool,
    fields: list,
    custom_validators: dict[str, Callable[[Any], bool]] | None = None,
) -> bool:
    """Apply a shape's own published rules to a candidate object.

    Generic across the top-level request body and every nested ``*_shape``
    (including the reused identity/adapter evidence-reference contracts'
    own bodies), so nested validation is never a divergent re-implementation
    of a dependency contract's rules.

    Every field is checked against its declared primitive type
    (``_matches_declared_type``) before any of the more specific rules
    (``non_empty``, ``pattern``, ``enum``, array-item, or object value-type
    checks) run — those specific rules assume the base type already matches
    and do not themselves reject a wrong primitive type (for example, a
    ``non_empty`` check on a field holding an integer would otherwise be
    silently skipped instead of failing the object).
    """
    if not isinstance(obj, dict):
        return False

    allowed = set(required) | set(optional)
    if not additional_properties and set(obj) - allowed:
        return False
    if any(field not in obj for field in required):
        return False

    fields_by_id = {f["id"]: f for f in fields}
    custom_validators = custom_validators or {}

    for key, value in obj.items():
        field = fields_by_id.get(key)
        if field is None:
            continue

        field_type = field.get("type")
        nullable = isinstance(field_type, list) and "null" in field_type

        if value is None:
            if not nullable:
                return False
            continue

        if not _matches_declared_type(value, _declared_types(field)):
            return False

        if field.get("non_empty") and isinstance(value, str) and not value.strip():
            return False

        if "pattern" in field:
            if not isinstance(value, str) or not re.match(field["pattern"], value):
                return False

        if "enum" in field:
            enum_values = [v for v in field["enum"] if v is not None]
            if value not in enum_values:
                return False

        if isinstance(value, list) and field.get("item_type") == "string":
            if not all(isinstance(item, str) for item in value):
                return False

        if isinstance(value, dict) and field.get("value_type") == "string":
            if not all(isinstance(k, str) and isinstance(v, str) for k, v in value.items()):
                return False

        if key in custom_validators and not custom_validators[key](value):
            return False

    return True


def _validate_shape(obj: object, shape: dict) -> bool:
    return _validate_object(
        obj,
        shape.get("required", []),
        shape.get("optional", []),
        shape["additional_properties"],
        shape["fields"],
    )


def _validate_evidence_reference(value: object, ref_body: dict) -> bool:
    digest_shape = ref_body["evidence_digest_shape"]
    return _validate_object(
        value,
        ref_body["required"],
        ref_body["optional"],
        ref_body["additional_properties"],
        ref_body["fields"],
        custom_validators={
            "evidence_digest": lambda digest: _validate_object(
                digest,
                digest_shape["required"],
                [],
                digest_shape["additional_properties"],
                digest_shape["fields"],
            )
        },
    )


def _is_valid_request(obj: object, body: dict) -> bool:
    identity_reference_body = _load_yaml(IDENTITY_REFERENCE_FILE)["identity_evidence_reference"]
    adapter_reference_body = _load_yaml(ADAPTER_REFERENCE_FILE)["adapter_evidence_reference"]

    custom_validators: dict[str, Callable[[Any], bool]] = {
        "identity_evidence_reference": lambda v: _validate_evidence_reference(
            v, identity_reference_body
        ),
        "adapter_evidence_reference": lambda v: _validate_evidence_reference(
            v, adapter_reference_body
        ),
        "location": lambda v: _validate_shape(v, body["location_shape"]),
        "device": lambda v: _validate_shape(v, body["device_shape"]),
        "protocol_context": lambda v: _validate_shape(v, body["protocol_context_shape"]),
        "safety_context": lambda v: _validate_shape(v, body["safety_context_shape"]),
        "environment_context": lambda v: _validate_shape(v, body["environment_context_shape"]),
        "risk_context": lambda v: _validate_shape(v, body["risk_context_shape"]),
    }

    if not _validate_object(
        obj,
        body["required"],
        body["optional"],
        body["additional_properties"],
        body["fields"],
        custom_validators=custom_validators,
    ):
        return False

    assert isinstance(obj, dict)

    action = obj.get("action")
    if not isinstance(action, str) or not re.match(body["action_pattern"], action):
        return False

    if "resource" in obj and obj["resource"] is not None:
        resource = obj["resource"]
        if not isinstance(resource, str) or not re.match(body["resource_pattern"], resource):
            return False

    if "evaluation_time" in obj and obj["evaluation_time"] is not None:
        evaluation_time = obj["evaluation_time"]
        if not isinstance(evaluation_time, str) or not re.match(
            body["evaluation_time_pattern"], evaluation_time
        ):
            return False

    return True


# ---------------------------------------------------------------------------
# File / parsing
# ---------------------------------------------------------------------------


def test_operation_aware_decision_request_file_exists() -> None:
    assert REQUEST_FILE.is_file(), (
        "schemas/operation-aware-decision-request/operation-aware-decision-request.yaml must exist"
    )


def test_operation_aware_decision_request_yaml_parses() -> None:
    assert _load()


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


def test_contract_metadata_matches_expected_values() -> None:
    contract = _load()["contract"]
    assert contract["name"] == "operation-aware-decision-request"
    assert contract["title"] == "BASIS Operation-Aware Decision Request"
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
        "action-string",
        "resource-identifier",
        "identity-evidence-reference",
        "adapter-evidence-reference",
    ]


def test_does_not_depend_on_reason_code_or_redaction_classification() -> None:
    # This request carries no reason_code field and no top-level
    # redaction_classification field of its own.
    depends_on = _load()["contract"].get("depends_on", [])
    assert "reason-code" not in depends_on
    assert "redaction-classification" not in depends_on


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------


def test_required_fields_are_minimal() -> None:
    assert _body()["required"] == ["request_id", "subject_id", "action"]


def test_optional_fields_cover_every_operation_aware_category() -> None:
    assert _body()["optional"] == [
        "correlation_id",
        "subject_roles",
        "subject_attrs",
        "identity_source",
        "authority_mode",
        "identity_evidence_reference",
        "resource",
        "resource_type",
        "location",
        "device",
        "protocol_context",
        "operation_intent",
        "adapter_evidence_reference",
        "safety_context",
        "environment_context",
        "risk_context",
        "evaluation_time",
        "expected_policy_version",
    ]


def test_unknown_top_level_fields_are_rejected_by_policy() -> None:
    assert _body()["additional_properties"] is False


def test_every_nested_shape_rejects_unknown_fields() -> None:
    body = _body()
    for shape_name in (
        "location_shape",
        "device_shape",
        "protocol_context_shape",
        "safety_context_shape",
        "environment_context_shape",
        "risk_context_shape",
    ):
        assert body[shape_name]["additional_properties"] is False, (
            f"{shape_name} must reject unknown fields"
        )


def test_every_field_has_a_description() -> None:
    body = _body()
    for field in body["fields"]:
        assert isinstance(field.get("description"), str) and field["description"].strip(), (
            f"field {field['id']!r} missing a description"
        )
    for shape_name in (
        "location_shape",
        "device_shape",
        "protocol_context_shape",
        "safety_context_shape",
        "environment_context_shape",
        "risk_context_shape",
    ):
        for field in body[shape_name]["fields"]:
            assert isinstance(field.get("description"), str) and field["description"].strip(), (
                f"{shape_name} field {field['id']!r} missing a description"
            )


def test_no_unrestricted_extension_bag() -> None:
    # No metadata/extensions/extra/arbitrary/properties/custom_fields bag.
    field_ids = {f["id"] for f in _body()["fields"]}
    for speculative in ("metadata", "extensions", "extra", "arbitrary", "custom_fields"):
        assert speculative not in field_ids


# ---------------------------------------------------------------------------
# Primitive type validation
#
# Every field is checked against its declared type deterministically, not
# only when a non_empty/pattern/enum rule happens to also be declared for
# that field. A base request (valid but for the one field under test) is
# reused so each case isolates exactly one wrong-type value.
# ---------------------------------------------------------------------------


def _base_request() -> dict:
    return {
        "request_id": "oadr-type-0000-0000-000000000000",
        "subject_id": "alice",
        "action": "read:ahu",
    }


def test_request_id_wrong_type_rejected() -> None:
    body = _body()
    request = _base_request()
    request["request_id"] = 12345
    assert not _is_valid_request(request, body)


def test_subject_id_wrong_type_rejected() -> None:
    body = _body()
    request = _base_request()
    request["subject_id"] = 12345
    assert not _is_valid_request(request, body)


@pytest.mark.parametrize("bad_value", [12345, {"nope": "not-a-string"}, ["not", "a", "string"]])
def test_correlation_id_wrong_type_rejected(bad_value: object) -> None:
    body = _body()
    request = _base_request()
    request["correlation_id"] = bad_value
    assert not _is_valid_request(request, body)


def test_identity_source_wrong_type_rejected() -> None:
    body = _body()
    request = _base_request()
    request["identity_source"] = 42
    assert not _is_valid_request(request, body)


def test_authority_mode_wrong_type_rejected() -> None:
    body = _body()
    request = _base_request()
    request["authority_mode"] = 42
    assert not _is_valid_request(request, body)


def test_subject_roles_non_array_rejected() -> None:
    body = _body()
    request = _base_request()
    request["subject_roles"] = "operator"  # a bare string, not an array of strings
    assert not _is_valid_request(request, body)


def test_subject_roles_non_string_items_rejected() -> None:
    body = _body()
    request = _base_request()
    request["subject_roles"] = ["operator", 5]
    assert not _is_valid_request(request, body)


def test_subject_attrs_non_object_rejected() -> None:
    body = _body()
    request = _base_request()
    request["subject_attrs"] = "not-an-object"
    assert not _is_valid_request(request, body)


@pytest.mark.parametrize(
    "bad_attrs", [{"clearance": 2}, {1: "clearance"}, {"clearance": ["level-2"]}]
)
def test_subject_attrs_non_string_keys_or_values_rejected(bad_attrs: dict) -> None:
    body = _body()
    request = _base_request()
    request["subject_attrs"] = bad_attrs
    assert not _is_valid_request(request, body)


def test_protocol_context_operation_wrong_type_rejected() -> None:
    body = _body()
    request = _base_request()
    request["protocol_context"] = {"operation": 12345}
    assert not _is_valid_request(request, body)


@pytest.mark.parametrize("bad_score", ["0.62", {"value": 0.62}, True, False])
def test_risk_context_score_wrong_type_rejected(bad_score: object) -> None:
    # True/False are deliberately included: Python's bool is an int
    # subclass, so a naive isinstance(value, (int, float)) check would
    # silently accept a boolean as a numeric risk score.
    body = _body()
    request = _base_request()
    request["risk_context"] = {"score": bad_score}
    assert not _is_valid_request(request, body)


@pytest.mark.parametrize("good_score", [0, 1, 62, 0.62, -1.5])
def test_risk_context_score_accepts_int_or_float(good_score: object) -> None:
    body = _body()
    request = _base_request()
    request["risk_context"] = {"score": good_score}
    assert _is_valid_request(request, body)


def test_evaluation_time_wrong_type_rejected() -> None:
    body = _body()
    request = _base_request()
    request["evaluation_time"] = 1747924200  # a unix timestamp int, not a string
    assert not _is_valid_request(request, body)


def test_expected_policy_version_wrong_type_rejected() -> None:
    body = _body()
    request = _base_request()
    request["expected_policy_version"] = 2
    assert not _is_valid_request(request, body)


# ---------------------------------------------------------------------------
# Minimal request
# ---------------------------------------------------------------------------


def test_minimal_request_is_accepted() -> None:
    body = _body()
    minimal = {
        "request_id": "oadr-minimal-0000-0000-000000000000",
        "subject_id": "svc-scheduler",
        "action": "browse:ahu",
    }
    assert _is_valid_request(minimal, body)


def test_richer_context_not_required() -> None:
    # No location, device, protocol, safety, environment, risk, or evidence
    # reference is required for a structurally valid request.
    body = _body()
    minimal = {
        "request_id": "oadr-minimal-0000-0000-000000000001",
        "subject_id": "svc-scheduler",
        "action": "browse:ahu",
    }
    assert _is_valid_request(minimal, body)
    for optional_field in body["optional"]:
        assert optional_field not in minimal


# ---------------------------------------------------------------------------
# Subject
# ---------------------------------------------------------------------------


def test_valid_subject_accepted() -> None:
    body = _body()
    request = {
        "request_id": "oadr-subj-0000-0000-000000000000",
        "subject_id": "alice",
        "subject_roles": ["operator", "viewer"],
        "subject_attrs": {"clearance": "level-2"},
        "action": "read:ahu",
    }
    assert _is_valid_request(request, body)


def test_empty_subject_id_rejected() -> None:
    body = _body()
    request = {"request_id": "oadr-subj-0001", "subject_id": "", "action": "read:ahu"}
    assert not _is_valid_request(request, body)


def test_subject_roles_must_be_strings() -> None:
    body = _body()
    request = {
        "request_id": "oadr-subj-0002",
        "subject_id": "alice",
        "subject_roles": ["operator", 5],
        "action": "read:ahu",
    }
    assert not _is_valid_request(request, body)


def test_subject_attrs_must_be_string_to_string() -> None:
    body = _body()
    request = {
        "request_id": "oadr-subj-0003",
        "subject_id": "alice",
        "subject_attrs": {"clearance": 2},
        "action": "read:ahu",
    }
    assert not _is_valid_request(request, body)


def test_no_raw_token_or_claims_fields_on_subject() -> None:
    field_ids = {f["id"] for f in _body()["fields"]}
    for forbidden in FORBIDDEN_FIELDS:
        assert forbidden not in field_ids


# ---------------------------------------------------------------------------
# Action
# ---------------------------------------------------------------------------


def test_valid_action_accepted() -> None:
    body = _body()
    for action in ("read:ahu", "write:hvac:setpoint", "execute:command"):
        request = {"request_id": "oadr-act", "subject_id": "alice", "action": action}
        assert _is_valid_request(request, body), f"valid action rejected: {action!r}"


def test_invalid_action_rejected() -> None:
    body = _body()
    for action in ("read", "read:", ":ahu", "read::setpoint"):
        request = {"request_id": "oadr-act", "subject_id": "alice", "action": action}
        assert not _is_valid_request(request, body), f"invalid action accepted: {action!r}"


def test_action_pattern_matches_published_action_string_contract() -> None:
    canonical = _load_yaml(ACTION_STRING_FILE)["action_string"]["pattern"]
    assert _body()["action_pattern"] == canonical


# ---------------------------------------------------------------------------
# Resource
# ---------------------------------------------------------------------------


def test_valid_resource_accepted() -> None:
    body = _body()
    request = {
        "request_id": "oadr-res",
        "subject_id": "alice",
        "action": "read:ahu",
        "resource": "ahu:rooftop-1",
        "resource_type": "ahu",
    }
    assert _is_valid_request(request, body)


def test_malformed_resource_rejected() -> None:
    body = _body()
    request = {
        "request_id": "oadr-res",
        "subject_id": "alice",
        "action": "read:ahu",
        "resource": "rooftop-1",
    }
    assert not _is_valid_request(request, body)


def test_resource_pattern_matches_published_resource_identifier_contract() -> None:
    canonical = _load_yaml(RESOURCE_IDENTIFIER_FILE)["resource_identifier"]["pattern"]
    assert _body()["resource_pattern"] == canonical


def test_resource_type_pattern_matches_resource_identifier_segment_pattern() -> None:
    canonical = _load_yaml(RESOURCE_IDENTIFIER_FILE)["resource_identifier"]["resource_type_pattern"]
    assert _body()["resource_type_pattern"] == canonical


def test_resource_is_optional_and_resource_type_is_a_distinct_field() -> None:
    body = _body()
    assert "resource" in body["optional"]
    assert "resource_type" in body["optional"]
    resource_field = _field(body["fields"], "resource")
    resource_type_field = _field(body["fields"], "resource_type")
    assert resource_field["governed_by"] == "resource-identifier"
    assert "governed_by" not in resource_type_field


# ---------------------------------------------------------------------------
# Evidence references
# ---------------------------------------------------------------------------


def test_valid_identity_evidence_reference_accepted() -> None:
    body = _body()
    request = {
        "request_id": "oadr-idev",
        "subject_id": "alice",
        "action": "read:ahu",
        "identity_evidence_reference": {
            "reference_id": "idev-test-0000-0000-000000000000",
            "evidence_digest": {
                "algorithm": "sha-256",
                "value": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            },
            "identity_source": "oidc:https://idp.example.com",
            "redaction_classification": "reference_only",
        },
    }
    assert _is_valid_request(request, body)


def test_malformed_identity_evidence_reference_rejected() -> None:
    body = _body()
    request = {
        "request_id": "oadr-idev",
        "subject_id": "alice",
        "action": "read:ahu",
        "identity_evidence_reference": {
            "evidence_digest": {
                "algorithm": "sha-256",
                "value": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            },
            "identity_source": "oidc:https://idp.example.com",
            "redaction_classification": "reference_only",
        },
    }
    assert not _is_valid_request(request, body)


def test_valid_adapter_evidence_reference_accepted() -> None:
    body = _body()
    request = {
        "request_id": "oadr-adev",
        "subject_id": "alice",
        "action": "read:ahu",
        "adapter_evidence_reference": {
            "reference_id": "adev-test-0000-0000-000000000000",
            "evidence_digest": {
                "algorithm": "sha-256",
                "value": "1f825aa2f0020ef7cf91dfa30da4668d791c5d4824fc8e41354b89ec05795ab",
            },
            "adapter_source": "basis-adapters:modbus",
            "redaction_classification": "reference_only",
        },
    }
    assert _is_valid_request(request, body)


def test_malformed_adapter_evidence_reference_rejected() -> None:
    body = _body()
    request = {
        "request_id": "oadr-adev",
        "subject_id": "alice",
        "action": "read:ahu",
        "adapter_evidence_reference": {
            "reference_id": "adev-test-0000-0000-000000000000",
            "evidence_digest": {"algorithm": "SHA256", "value": "1f825aa2"},
            "adapter_source": "basis-adapters:modbus",
            "redaction_classification": "reference_only",
        },
    }
    assert not _is_valid_request(request, body)


def test_evidence_references_are_optional() -> None:
    body = _body()
    assert "identity_evidence_reference" in body["optional"]
    assert "adapter_evidence_reference" in body["optional"]


def test_evidence_reference_fields_reference_pr_b_governance() -> None:
    body = _body()
    identity_field = _field(body["fields"], "identity_evidence_reference")
    adapter_field = _field(body["fields"], "adapter_evidence_reference")
    assert identity_field["governed_by"] == "identity-evidence-reference"
    assert adapter_field["governed_by"] == "adapter-evidence-reference"
    # This contract does not reproduce PR B's evidence_digest_shape or
    # redaction_classification_values locally: no divergent copy exists.
    assert "evidence_digest_shape" not in body
    assert "redaction_classification_values" not in body


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------


def test_partial_location_hierarchy_accepted() -> None:
    body = _body()
    request = {
        "request_id": "oadr-loc",
        "subject_id": "alice",
        "action": "read:ahu",
        "location": {"site_id": "west-campus"},
    }
    assert _is_valid_request(request, body)


def test_full_location_hierarchy_accepted() -> None:
    body = _body()
    request = {
        "request_id": "oadr-loc",
        "subject_id": "alice",
        "action": "read:ahu",
        "location": {
            "site_id": "west-campus",
            "building_id": "bldg-3",
            "zone_id": "zone-a",
            "area_id": "area-1",
        },
    }
    assert _is_valid_request(request, body)


def test_malformed_location_rejected() -> None:
    body = _body()
    request = {
        "request_id": "oadr-loc",
        "subject_id": "alice",
        "action": "read:ahu",
        "location": {"site_id": "west-campus", "country": "not-a-published-field"},
    }
    assert not _is_valid_request(request, body)


# ---------------------------------------------------------------------------
# Device
# ---------------------------------------------------------------------------


def test_valid_device_accepted() -> None:
    body = _body()
    request = {
        "request_id": "oadr-dev",
        "subject_id": "alice",
        "action": "read:ahu",
        "device": {"device_id": "ahu-14", "device_class": "controller"},
    }
    assert _is_valid_request(request, body)


def test_malformed_device_class_rejected() -> None:
    body = _body()
    request = {
        "request_id": "oadr-dev",
        "subject_id": "alice",
        "action": "read:ahu",
        "device": {"device_class": "Controller"},
    }
    assert not _is_valid_request(request, body)


# ---------------------------------------------------------------------------
# Protocol context
# ---------------------------------------------------------------------------


def test_open_protocol_identifier_accepted() -> None:
    body = _body()
    for protocol in ("bacnet", "modbus", "opcua", "some-future-protocol"):
        request = {
            "request_id": "oadr-proto",
            "subject_id": "alice",
            "action": "read:ahu",
            "protocol_context": {"protocol": protocol, "operation": "ReadProperty"},
        }
        assert _is_valid_request(request, body), f"open protocol rejected: {protocol!r}"


def test_malformed_protocol_label_rejected() -> None:
    body = _body()
    request = {
        "request_id": "oadr-proto",
        "subject_id": "alice",
        "action": "read:ahu",
        "protocol_context": {"protocol": "BACnet"},
    }
    assert not _is_valid_request(request, body)


def test_no_protocol_specific_payload_fields_defined() -> None:
    body = _body()
    protocol_field_ids = {f["id"] for f in body["protocol_context_shape"]["fields"]}
    for forbidden in FORBIDDEN_FIELDS:
        assert forbidden not in protocol_field_ids


# ---------------------------------------------------------------------------
# Operation intent
# ---------------------------------------------------------------------------


def test_valid_operation_intent_values_accepted() -> None:
    body = _body()
    for value in body["operation_intent_values"]:
        request = {
            "request_id": "oadr-intent",
            "subject_id": "alice",
            "action": "write:hvac:setpoint",
            "operation_intent": value,
        }
        assert _is_valid_request(request, body), f"valid operation_intent rejected: {value!r}"


def test_invalid_operation_intent_rejected() -> None:
    body = _body()
    request = {
        "request_id": "oadr-intent",
        "subject_id": "alice",
        "action": "write:hvac:setpoint",
        "operation_intent": "destructive",
    }
    assert not _is_valid_request(request, body)


def test_operation_intent_values_are_lowercase_snake_case() -> None:
    for value in _body()["operation_intent_values"]:
        assert re.match(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$", value), value


def test_operation_intent_is_closed_enum() -> None:
    assert _body()["operation_intent_values"] == [
        "read_only",
        "state_changing",
        "control_affecting",
    ]


# ---------------------------------------------------------------------------
# Safety / environment / time / risk context
# ---------------------------------------------------------------------------


def test_absent_evaluation_contexts_accepted() -> None:
    body = _body()
    request = {"request_id": "oadr-ctx", "subject_id": "alice", "action": "read:ahu"}
    assert _is_valid_request(request, body)


def test_valid_safety_context_accepted() -> None:
    body = _body()
    request = {
        "request_id": "oadr-safety",
        "subject_id": "alice",
        "action": "execute:hvac:reset",
        "safety_context": {
            "mode": "interlock-engaged",
            "classification": "elevated",
            "constraint_ids": ["lockout-tagout-active"],
        },
    }
    assert _is_valid_request(request, body)


def test_malformed_safety_context_rejected() -> None:
    body = _body()
    request = {
        "request_id": "oadr-safety",
        "subject_id": "alice",
        "action": "execute:hvac:reset",
        "safety_context": {"mode": "Interlock_Engaged"},
    }
    assert not _is_valid_request(request, body)


def test_valid_environment_context_accepted() -> None:
    body = _body()
    request = {
        "request_id": "oadr-env",
        "subject_id": "alice",
        "action": "read:ahu",
        "environment_context": {"mode": "maintenance_mode", "condition_ids": ["scheduled-window"]},
    }
    assert _is_valid_request(request, body)


def test_malformed_environment_context_rejected() -> None:
    body = _body()
    request = {
        "request_id": "oadr-env",
        "subject_id": "alice",
        "action": "read:ahu",
        "environment_context": {"mode": "Maintenance Mode"},
    }
    assert not _is_valid_request(request, body)


def test_valid_evaluation_time_accepted() -> None:
    body = _body()
    for value in ("2026-05-22T14:30:00Z", "2026-05-22T14:30:05+00:00", "2026-05-22T14:30:05.123Z"):
        request = {
            "request_id": "oadr-time",
            "subject_id": "alice",
            "action": "read:ahu",
            "evaluation_time": value,
        }
        assert _is_valid_request(request, body), f"valid evaluation_time rejected: {value!r}"


def test_invalid_evaluation_time_rejected() -> None:
    body = _body()
    for value in ("2026-05-22T14:30:00", "not-a-timestamp", "2026-05-22"):
        request = {
            "request_id": "oadr-time",
            "subject_id": "alice",
            "action": "read:ahu",
            "evaluation_time": value,
        }
        assert not _is_valid_request(request, body), f"invalid evaluation_time accepted: {value!r}"


def test_valid_risk_context_accepted() -> None:
    body = _body()
    request = {
        "request_id": "oadr-risk",
        "subject_id": "alice",
        "action": "read:ahu",
        "risk_context": {"classification": "elevated", "score": 0.62},
    }
    assert _is_valid_request(request, body)


def test_malformed_risk_classification_rejected() -> None:
    body = _body()
    request = {
        "request_id": "oadr-risk",
        "subject_id": "alice",
        "action": "read:ahu",
        "risk_context": {"classification": "Elevated Risk!"},
    }
    assert not _is_valid_request(request, body)


def test_risk_score_has_no_enforced_bounds() -> None:
    score_field = _field(_body()["risk_context_shape"]["fields"], "score")
    assert "pattern" not in score_field
    assert "enum" not in score_field
    assert "minimum" not in score_field and "maximum" not in score_field


# ---------------------------------------------------------------------------
# Policy expectation
# ---------------------------------------------------------------------------


def test_valid_expected_policy_version_accepted() -> None:
    body = _body()
    request = {
        "request_id": "oadr-policy",
        "subject_id": "alice",
        "action": "read:ahu",
        "expected_policy_version": "0.2.0",
    }
    assert _is_valid_request(request, body)


def test_empty_expected_policy_version_rejected() -> None:
    body = _body()
    request = {
        "request_id": "oadr-policy",
        "subject_id": "alice",
        "action": "read:ahu",
        "expected_policy_version": "",
    }
    assert not _is_valid_request(request, body)


# ---------------------------------------------------------------------------
# Request / correlation identifiers
# ---------------------------------------------------------------------------


def test_request_id_semantics_preserved() -> None:
    request_field = _field(_body()["fields"], "request_id")
    assert request_field["required"] is True
    assert request_field["non_empty"] is True


def test_correlation_id_is_optional_and_passthrough() -> None:
    body = _body()
    assert "correlation_id" in body["optional"]
    correlation_field = _field(body["fields"], "correlation_id")
    assert "pattern" not in correlation_field
    assert "enum" not in correlation_field

    request = {
        "request_id": "oadr-corr",
        "subject_id": "alice",
        "action": "read:ahu",
        "correlation_id": "corr-anything-goes",
    }
    assert _is_valid_request(request, body)


def test_provenance_association_documents_no_automatic_reconciliation() -> None:
    association = _body()["provenance_association"]
    assert association["parent_fields_authoritative"] is True
    assert association["nested_reference_fields"] == "provenance_metadata_only"
    assert association["automatic_reconciliation"] is False


def test_provenance_association_covers_every_overlapping_field_pair() -> None:
    # The parent-vs-nested-provenance rule applies uniformly to every field
    # this request and a nested evidence reference could both carry:
    # request/correlation identifiers, identity_source, and the protocol
    # label. This is a regression guard against the rule silently narrowing
    # back to identifiers only.
    pairs = {
        (pair["parent"], pair["nested"])
        for pair in _body()["provenance_association"]["overlapping_field_pairs"]
    }
    assert ("request_id", "identity_evidence_reference.request_id") in pairs
    assert ("request_id", "adapter_evidence_reference.request_id") in pairs
    assert ("correlation_id", "identity_evidence_reference.correlation_id") in pairs
    assert ("correlation_id", "adapter_evidence_reference.correlation_id") in pairs
    assert ("identity_source", "identity_evidence_reference.identity_source") in pairs
    assert ("protocol_context.protocol", "adapter_evidence_reference.protocol") in pairs


# ---------------------------------------------------------------------------
# Secret / raw-evidence regression
# ---------------------------------------------------------------------------


def test_no_forbidden_secret_or_raw_evidence_fields_defined_anywhere() -> None:
    body = _body()
    all_field_ids: set[str] = {f["id"] for f in body["fields"]}
    for shape_name in (
        "location_shape",
        "device_shape",
        "protocol_context_shape",
        "safety_context_shape",
        "environment_context_shape",
        "risk_context_shape",
    ):
        all_field_ids |= {f["id"] for f in body[shape_name]["fields"]}

    for forbidden in FORBIDDEN_FIELDS:
        assert forbidden not in all_field_ids, f"forbidden field defined on contract: {forbidden!r}"

    allowed = set(body["required"]) | set(body["optional"])
    for forbidden in FORBIDDEN_FIELDS:
        assert forbidden not in allowed


# ---------------------------------------------------------------------------
# Examples
# ---------------------------------------------------------------------------


def test_required_valid_examples_accepted() -> None:
    body = _body()
    for example in body["examples"]["valid"]:
        assert _is_valid_request(example, body), f"valid example rejected: {example!r}"


def test_required_invalid_examples_rejected() -> None:
    body = _body()
    for case in body["examples"]["invalid"]:
        assert "reason" in case, f"invalid example missing a reason: {case!r}"
        assert not _is_valid_request(case["value"], body), (
            f"invalid request accepted ({case['reason']}): {case['value']!r}"
        )


def test_invalid_examples_cover_required_cases() -> None:
    reasons = " ".join(case["reason"] for case in _body()["examples"]["invalid"]).lower()
    assert "missing required request_id" in reasons
    assert "empty request_id" in reasons
    assert "missing required subject_id" in reasons
    assert "empty subject_id" in reasons
    assert "invalid action" in reasons
    assert "malformed resource identifier" in reasons
    assert "unknown top-level field" in reasons
    assert "malformed nested structure" in reasons
    assert "unsupported operation_intent value" in reasons
    assert "invalid evaluation_time" in reasons
    assert "malformed expected_policy_version" in reasons
    assert "malformed identity evidence reference" in reasons
    assert "malformed adapter evidence reference" in reasons
    assert "access token" in reasons or "access_token" in reasons
    assert "claims" in reasons
    assert "raw protocol payload" in reasons


def test_examples_use_synthetic_values_not_the_first_wave_series() -> None:
    # The first-wave decision-request examples use the a1b2c3d4-* request_id
    # series; this contract's examples use a distinct oadr-* series so the
    # two fixture sets are never mistaken for one another.
    for example in _body()["examples"]["valid"]:
        assert example["request_id"].startswith("oadr-")


# ---------------------------------------------------------------------------
# Package integration
# ---------------------------------------------------------------------------


def test_new_request_contract_is_tracked_in_metadata() -> None:
    assert "operation-aware-decision-request" in basis_schemas.OPERATION_AWARE_REQUEST_CONTRACTS
    assert "operation-aware-decision-request" not in basis_schemas.PLANNED_CONTRACTS
    assert "operation-aware-decision-request" not in basis_schemas.PUBLISHED_CONTRACTS
    assert (
        "operation-aware-decision-request"
        not in basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS
    )
    assert (
        "operation-aware-decision-request"
        not in basis_schemas.OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS
    )


def test_repository_layout_updated() -> None:
    assert REQUEST_DIR.is_dir()
    assert (REQUEST_DIR / "operation-aware-decision-request.yaml").is_file()
    assert (REPO_ROOT / "docs" / "operation-aware-decision-request.md").is_file()


# ---------------------------------------------------------------------------
# Backward compatibility: the first-wave decision-request is untouched
# ---------------------------------------------------------------------------


def test_first_wave_decision_request_contract_unchanged() -> None:
    decision_request = _load_yaml(DECISION_REQUEST_FILE)
    contract = decision_request["contract"]
    assert contract["name"] == "decision-request"
    assert contract["version"] == "0.1.0"
    assert contract["lifecycle"] == "experimental"
    assert contract["depends_on"] == ["action-string", "resource-identifier"]

    body = decision_request["decision_request"]
    assert body["required"] == ["request_id", "subject_id", "action", "timestamp"]
    assert body["optional"] == ["subject_roles", "subject_attrs", "resource_id", "context"]
    assert body["additional_properties"] is False
    assert len(body["examples"]["valid"]) == 3
    assert len(body["examples"]["invalid"]) == 8


def test_first_wave_tracking_unchanged() -> None:
    assert basis_schemas.PLANNED_CONTRACTS == (
        "vocabulary",
        "action-string",
        "resource-identifier",
        "decision-request",
        "decision-response",
        "audit-event",
    )
    assert basis_schemas.PUBLISHED_CONTRACTS == basis_schemas.PLANNED_CONTRACTS


def test_pr_a_and_pr_b_tracking_unchanged() -> None:
    assert basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS == (
        "contract-metadata",
        "redaction-classification",
        "reason-code",
    )
    assert basis_schemas.OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS == (
        "identity-evidence-reference",
        "adapter-evidence-reference",
    )
