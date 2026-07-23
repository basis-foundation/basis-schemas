"""Compatibility vector tests for PR G of the operation-aware schema
readiness plan (``basis-architecture`` ADR-0005, "PR G — Compatibility
Examples and Test Vectors").

These tests validate the canonical, cross-contract compatibility fixtures
published under ``examples/operation-aware/compatibility/``. They are
deliberately scoped to three things:

1. **Artifact validation** — every fixture in every scenario directory
   validates against its governing contract's own published field policy
   (PR A through PR F, consumed exactly as published, never modified here).
2. **Cross-artifact compatibility** — the invariants that only become
   visible once a scenario's six artifacts are considered together (shared
   identifiers, policy provenance, evaluation-state agreement).
3. **Scenario expectations and drift detection** — each canonical scenario
   encodes the evaluation-outcome category ADR-0002 says it should, and the
   harness actually notices when a fixture is mutated to violate that.

This file does **not** implement policy evaluation, condition evaluation, or
rule matching. It validates that a *static, hand-authored* fixture set
matches the shape and cross-object invariants the published contracts and
architecture already define — it never computes an authorization outcome
from a request and a policy bundle. Whether a real ``basis-core`` v0.2.0
evaluator reaches the recorded outcome for a given scenario is a future
``basis-core`` conformance question, not something asserted here.

This suite reuses the same generic shape-validator pattern this
repository's own per-contract test suites already establish (see, for
example, ``test_operation_aware_decision_request_contract.py``'s
``_validate_object``) rather than a second, divergent implementation. It
does not duplicate PR A through PR F's own dedicated contract test suites,
which remain authoritative for each contract's own shape.
"""

from __future__ import annotations

import copy
import re
from collections.abc import Callable
from functools import cache
from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = REPO_ROOT / "schemas"
COMPAT_DIR = REPO_ROOT / "examples" / "operation-aware" / "compatibility"

# ---------------------------------------------------------------------------
# Scenario / artifact layout
# ---------------------------------------------------------------------------

REQUEST_FILENAME = "operation-aware-decision-request.yaml"
TRACE_FILENAME = "expected-evaluation-trace.yaml"
RESPONSE_FILENAME = "expected-operation-aware-decision-response.yaml"
AUDIT_FILENAME = "expected-audit-evidence.yaml"
GATEWAY_FILENAME = "expected-gateway-audit-event.yaml"

#: Each scenario's own policy-bundle filename. Four scenarios use a valid
#: ``policy-bundle.yaml``; the fifth intentionally uses a differently named,
#: intentionally invalid fixture (see the file's own header comment) so it
#: is never mistaken for a valid one by a casual reader or a naive glob.
SCENARIOS: dict[str, dict[str, Any]] = {
    "allow-basic": {"policy_filename": "policy-bundle.yaml", "policy_valid": True},
    "deny-precedence": {"policy_filename": "policy-bundle.yaml", "policy_valid": True},
    "default-deny": {"policy_filename": "policy-bundle.yaml", "policy_valid": True},
    "not-applicable": {"policy_filename": "policy-bundle.yaml", "policy_valid": True},
    "invalid-policy-bundle": {
        "policy_filename": "invalid-policy-bundle.yaml",
        "policy_valid": False,
    },
}


def _artifact_filenames(scenario: str) -> list[str]:
    return [
        REQUEST_FILENAME,
        SCENARIOS[scenario]["policy_filename"],
        TRACE_FILENAME,
        RESPONSE_FILENAME,
        AUDIT_FILENAME,
        GATEWAY_FILENAME,
    ]


# ---------------------------------------------------------------------------
# YAML loading (duplicate-key-detecting, offline, no network/env access)
# ---------------------------------------------------------------------------


class _NoDuplicateKeysLoader(yaml.SafeLoader):
    """A ``SafeLoader`` that raises on duplicate mapping keys.

    PyYAML's default loader silently lets a later duplicate key overwrite an
    earlier one. That is exactly the kind of drift a compatibility fixture
    must never hide, so every fixture in this directory is loaded through
    this loader instead of a bare ``yaml.safe_load``.
    """


def _no_duplicate_keys_constructor(loader: yaml.SafeLoader, node: yaml.MappingNode) -> dict:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        if key in mapping:
            raise ValueError(f"duplicate mapping key detected: {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=True)
    return mapping


_NoDuplicateKeysLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicate_keys_constructor
)


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        data = yaml.load(handle, Loader=_NoDuplicateKeysLoader)
    assert isinstance(data, dict), f"{path} must parse to a mapping"
    return data


@cache
def _load_yaml_cached(path_str: str) -> dict:
    return _load_yaml(Path(path_str))


def _load_scenario_artifact(scenario: str, filename: str) -> dict:
    return copy.deepcopy(_load_yaml_cached(str(COMPAT_DIR / scenario / filename)))


def _load_scenario(scenario: str) -> dict[str, dict]:
    cfg = SCENARIOS[scenario]
    return {
        "request": _load_scenario_artifact(scenario, REQUEST_FILENAME),
        "policy": _load_scenario_artifact(scenario, cfg["policy_filename"]),
        "trace": _load_scenario_artifact(scenario, TRACE_FILENAME),
        "response": _load_scenario_artifact(scenario, RESPONSE_FILENAME),
        "audit": _load_scenario_artifact(scenario, AUDIT_FILENAME),
        "gateway": _load_scenario_artifact(scenario, GATEWAY_FILENAME),
    }


def _all_fixture_yaml_files() -> list[Path]:
    return sorted(COMPAT_DIR.rglob("*.yaml"))


# ---------------------------------------------------------------------------
# Generic contract-shape validation (reuses the pattern already established
# in test_operation_aware_decision_request_contract.py's _validate_object,
# generalized across every PR A-F contract this PR's fixtures exercise).
# ---------------------------------------------------------------------------

CONTRACT_FILES: dict[str, Path] = {
    "operation-aware-decision-request": SCHEMAS_DIR
    / "operation-aware-decision-request"
    / "operation-aware-decision-request.yaml",
    "operation-aware-decision-response": SCHEMAS_DIR
    / "operation-aware-decision-response"
    / "operation-aware-decision-response.yaml",
    "policy-bundle": SCHEMAS_DIR / "policy-bundle" / "policy-bundle.yaml",
    "policy-rule": SCHEMAS_DIR / "policy-rule" / "policy-rule.yaml",
    "policy-condition": SCHEMAS_DIR / "policy-condition" / "policy-condition.yaml",
    "evaluation-trace": SCHEMAS_DIR / "evaluation-trace" / "evaluation-trace.yaml",
    "trace-rule-evidence": SCHEMAS_DIR / "trace-rule-evidence" / "trace-rule-evidence.yaml",
    "audit-evidence": SCHEMAS_DIR / "audit-evidence" / "audit-evidence.yaml",
    "gateway-audit-event": SCHEMAS_DIR / "gateway-audit-event" / "gateway-audit-event.yaml",
    "identity-evidence-reference": SCHEMAS_DIR
    / "identity-evidence-reference"
    / "identity-evidence-reference.yaml",
    "adapter-evidence-reference": SCHEMAS_DIR
    / "adapter-evidence-reference"
    / "adapter-evidence-reference.yaml",
}

CONTRACT_BODY_KEY: dict[str, str] = {
    "operation-aware-decision-request": "operation_aware_decision_request",
    "operation-aware-decision-response": "operation_aware_decision_response",
    "policy-bundle": "policy_bundle",
    "policy-rule": "policy_rule",
    "policy-condition": "policy_condition",
    "evaluation-trace": "evaluation_trace",
    "trace-rule-evidence": "trace_rule_evidence",
    "audit-evidence": "audit_evidence",
    "gateway-audit-event": "gateway_audit_event",
    "identity-evidence-reference": "identity_evidence_reference",
    "adapter-evidence-reference": "adapter_evidence_reference",
}


@cache
def _contract_body(name: str) -> dict:
    data = _load_yaml(CONTRACT_FILES[name])
    return data[CONTRACT_BODY_KEY[name]]


_PRIMITIVE_TYPE_CHECKS: dict[str, Callable[[Any], bool]] = {
    "string": lambda v: isinstance(v, str),
    "array": lambda v: isinstance(v, list),
    "object": lambda v: isinstance(v, dict),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
}


def _declared_types(field: dict) -> list[str]:
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


#: Maps (contract_name, field_id) to how that field's nested value must be
#: further validated, beyond the generic primitive-type/pattern/enum checks
#: every field already gets. Three kinds:
#:   ("shape", key)          -- validate against contract_body[key] (a
#:                              nested *_shape sub-schema in the SAME file)
#:   ("contract", name)      -- validate as a full instance of another
#:                              published contract (an evidence reference,
#:                              or an embedded trace)
#:   ("array_contract", name) -- value is an array whose items are each a
#:                              full instance of another published contract
#:   ("array_shape", key)    -- value is an array whose items each match a
#:                              nested *_shape sub-schema in the SAME file
NESTED_SHAPE_FIELDS: dict[tuple[str, str], tuple[str, str]] = {
    ("operation-aware-decision-request", "location"): ("shape", "location_shape"),
    ("operation-aware-decision-request", "device"): ("shape", "device_shape"),
    ("operation-aware-decision-request", "protocol_context"): (
        "shape",
        "protocol_context_shape",
    ),
    ("operation-aware-decision-request", "safety_context"): ("shape", "safety_context_shape"),
    ("operation-aware-decision-request", "environment_context"): (
        "shape",
        "environment_context_shape",
    ),
    ("operation-aware-decision-request", "risk_context"): ("shape", "risk_context_shape"),
    ("operation-aware-decision-request", "identity_evidence_reference"): (
        "contract",
        "identity-evidence-reference",
    ),
    ("operation-aware-decision-request", "adapter_evidence_reference"): (
        "contract",
        "adapter-evidence-reference",
    ),
    ("operation-aware-decision-response", "evaluation_trace"): ("contract", "evaluation-trace"),
    ("policy-bundle", "scope"): ("shape", "scope_shape"),
    ("policy-bundle", "rules"): ("array_contract", "policy-rule"),
    ("policy-rule", "match"): ("shape", "match_shape"),
    ("policy-rule", "conditions"): ("array_contract", "policy-condition"),
    ("evaluation-trace", "rule_evidence"): ("array_contract", "trace-rule-evidence"),
    ("trace-rule-evidence", "condition_results"): ("array_shape", "condition_result_shape"),
    ("audit-evidence", "identity_evidence_reference"): (
        "contract",
        "identity-evidence-reference",
    ),
    ("audit-evidence", "adapter_evidence_reference"): ("contract", "adapter-evidence-reference"),
    ("identity-evidence-reference", "evidence_digest"): ("shape", "evidence_digest_shape"),
    ("adapter-evidence-reference", "evidence_digest"): ("shape", "evidence_digest_shape"),
}

#: Populated at the bottom of this module, after every dedicated
#: validate_* function is defined. Referenced only at call time (never at
#: import/definition time), so the forward reference is safe.
_VALIDATOR_DISPATCH: dict[str, Callable[[Any], bool]] = {}


def _dispatch_validate(contract_name: str, value: object) -> bool:
    validator = _VALIDATOR_DISPATCH.get(contract_name)
    if validator is not None:
        return validator(value)
    return _validate_body(value, _contract_body(contract_name), contract_name)


def _validate_nested(contract_name: str, key: str, value: object) -> bool:
    if value is None:
        return True
    spec = NESTED_SHAPE_FIELDS.get((contract_name, key))
    if spec is None:
        return True
    kind, target = spec
    if kind == "shape":
        if not isinstance(value, dict):
            return False
        return _validate_body(value, _contract_body(contract_name)[target], contract_name)
    if kind == "array_shape":
        if not isinstance(value, list):
            return False
        shape = _contract_body(contract_name)[target]
        return all(
            isinstance(item, dict) and _validate_body(item, shape, contract_name) for item in value
        )
    if kind == "contract":
        return _dispatch_validate(target, value)
    if kind == "array_contract":
        if not isinstance(value, list):
            return False
        return all(_dispatch_validate(target, item) for item in value)
    return True


def _validate_field_value(contract_name: str, key: str, value: object, field: dict) -> bool:
    field_type = field.get("type")
    nullable = isinstance(field_type, list) and "null" in field_type
    if value is None:
        return nullable

    declared_types = _declared_types(field)
    if not _matches_declared_type(value, declared_types):
        return False

    if field.get("non_empty") and isinstance(value, str) and not value.strip():
        return False

    if "pattern" in field:
        # A field's `pattern` applies to a scalar string value directly, or
        # to each item of an array value (e.g. policy-rule's match_shape /
        # policy-bundle's scope_shape selector arrays) -- never to the array
        # itself.
        if isinstance(value, list):
            if not all(
                isinstance(item, str) and re.match(field["pattern"], item) for item in value
            ):
                return False
        elif not isinstance(value, str) or not re.match(field["pattern"], value):
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

    return _validate_nested(contract_name, key, value)


def _validate_body(obj: object, body: dict, contract_name: str) -> bool:
    """Validate ``obj`` against a shape body's own required/optional/fields
    policy — generic across a contract's top-level body and every nested
    ``*_shape`` sub-schema it declares.
    """
    if not isinstance(obj, dict):
        return False

    required = body.get("required", [])
    optional = body.get("optional", [])
    additional_properties = body.get("additional_properties", True)
    fields = body.get("fields", [])

    allowed = set(required) | set(optional)
    if not additional_properties and set(obj) - allowed:
        return False
    if any(field not in obj for field in required):
        return False

    fields_by_id = {f["id"]: f for f in fields}
    for key, value in obj.items():
        field = fields_by_id.get(key)
        if field is None:
            continue
        if not _validate_field_value(contract_name, key, value, field):
            return False
    return True


def _evaluation_invariant_ok(
    evaluation_status: object, outcome: object, failure_reason: object
) -> bool:
    """The outcome/evaluation_status/failure_reason invariant ADR-0002
    Section 14 requires, reused identically across
    operation-aware-decision-response, evaluation-trace, audit-evidence, and
    gateway-audit-event: a failed evaluation never serializes a non-null
    outcome, and failure_reason is non-null if and only if evaluation_status
    is "failed".
    """
    if evaluation_status == "failed":
        return outcome is None and failure_reason is not None
    if evaluation_status == "completed":
        return outcome in ("allow", "deny", "not_applicable") and failure_reason is None
    return False


# --- Per-contract validators -------------------------------------------


def validate_operation_aware_decision_request(value: object) -> bool:
    body = _contract_body("operation-aware-decision-request")
    if not _validate_body(value, body, "operation-aware-decision-request"):
        return False
    assert isinstance(value, dict)
    action = value.get("action")
    if not isinstance(action, str) or not re.match(body["action_pattern"], action):
        return False
    resource = value.get("resource")
    if resource is not None and not (
        isinstance(resource, str) and re.match(body["resource_pattern"], resource)
    ):
        return False
    evaluation_time = value.get("evaluation_time")
    if evaluation_time is not None and not (
        isinstance(evaluation_time, str)
        and re.match(body["evaluation_time_pattern"], evaluation_time)
    ):
        return False
    return True


def validate_identity_evidence_reference(value: object) -> bool:
    return _validate_body(
        value, _contract_body("identity-evidence-reference"), "identity-evidence-reference"
    )


def validate_adapter_evidence_reference(value: object) -> bool:
    return _validate_body(
        value, _contract_body("adapter-evidence-reference"), "adapter-evidence-reference"
    )


def validate_policy_condition(value: object) -> bool:
    return _validate_body(value, _contract_body("policy-condition"), "policy-condition")


def validate_policy_rule(value: object) -> bool:
    if not _validate_body(value, _contract_body("policy-rule"), "policy-rule"):
        return False
    assert isinstance(value, dict)
    match = value.get("match")
    conditions = value.get("conditions")
    has_match = isinstance(match, dict) and bool(match)
    has_conditions = isinstance(conditions, list) and bool(conditions)
    if not (has_match or has_conditions):
        return False
    if has_conditions:
        assert isinstance(conditions, list)
        condition_ids = [c["condition_id"] for c in conditions]
        if len(condition_ids) != len(set(condition_ids)):
            return False
    return True


def validate_policy_bundle(value: object) -> bool:
    if not _validate_body(value, _contract_body("policy-bundle"), "policy-bundle"):
        return False
    assert isinstance(value, dict)
    rules = value.get("rules")
    if not isinstance(rules, list) or not rules:
        return False
    for rule in rules:
        if not validate_policy_rule(rule):
            return False
    rule_ids = [r["rule_id"] for r in rules]
    if len(rule_ids) != len(set(rule_ids)):
        return False
    return True


def validate_trace_rule_evidence(value: object) -> bool:
    if not _validate_body(value, _contract_body("trace-rule-evidence"), "trace-rule-evidence"):
        return False
    assert isinstance(value, dict)
    condition_results = value.get("condition_results") or []
    if condition_results:
        condition_ids = [c["condition_id"] for c in condition_results]
        if len(condition_ids) != len(set(condition_ids)):
            return False
        if (
            any(c.get("result") == "error" for c in condition_results)
            and value.get("rule_result") != "error"
        ):
            return False
    return True


def validate_evaluation_trace(value: object) -> bool:
    if not _validate_body(value, _contract_body("evaluation-trace"), "evaluation-trace"):
        return False
    assert isinstance(value, dict)
    evaluation_status = value.get("evaluation_status")
    outcome = value.get("outcome")
    failure_reason = value.get("failure_reason")
    if not _evaluation_invariant_ok(evaluation_status, outcome, failure_reason):
        return False

    bundle_applicability = value.get("bundle_applicability")
    rule_evidence = value.get("rule_evidence") or []

    if evaluation_status == "completed":
        if bundle_applicability == "not_applicable" and outcome != "not_applicable":
            return False
        if outcome == "not_applicable" and bundle_applicability != "not_applicable":
            return False
        if outcome in ("allow", "deny") and bundle_applicability != "applicable":
            return False
        if bundle_applicability == "applicable" and outcome not in ("allow", "deny"):
            return False

    if bundle_applicability == "not_applicable" and rule_evidence:
        return False

    rule_ids = [entry["rule_id"] for entry in rule_evidence]
    if len(rule_ids) != len(set(rule_ids)):
        return False

    if (
        any(entry.get("rule_result") == "error" for entry in rule_evidence)
        and evaluation_status != "failed"
    ):
        return False

    return True


def validate_operation_aware_decision_response(value: object) -> bool:
    if not _validate_body(
        value,
        _contract_body("operation-aware-decision-response"),
        "operation-aware-decision-response",
    ):
        return False
    assert isinstance(value, dict)
    return _evaluation_invariant_ok(
        value.get("evaluation_status"), value.get("outcome"), value.get("failure_reason")
    )


def validate_audit_evidence(value: object) -> bool:
    if not _validate_body(value, _contract_body("audit-evidence"), "audit-evidence"):
        return False
    assert isinstance(value, dict)
    if not _evaluation_invariant_ok(
        value.get("evaluation_status"), value.get("outcome"), value.get("failure_reason")
    ):
        return False
    matched_rule_ids = value.get("matched_rule_ids") or []
    if len(matched_rule_ids) != len(set(matched_rule_ids)):
        return False
    return True


def validate_gateway_audit_event(value: object) -> bool:
    if not _validate_body(value, _contract_body("gateway-audit-event"), "gateway-audit-event"):
        return False
    assert isinstance(value, dict)
    if not _evaluation_invariant_ok(
        value.get("evaluation_status"), value.get("outcome"), value.get("failure_reason")
    ):
        return False
    if value.get("enforcement_action") not in ("allow", "deny"):
        return False
    gateway_failure_reason = value.get("gateway_failure_reason")
    if gateway_failure_reason is not None and value.get("enforcement_action") != "deny":
        return False
    return True


_VALIDATOR_DISPATCH.update(
    {
        "operation-aware-decision-request": validate_operation_aware_decision_request,
        "operation-aware-decision-response": validate_operation_aware_decision_response,
        "policy-bundle": validate_policy_bundle,
        "policy-rule": validate_policy_rule,
        "policy-condition": validate_policy_condition,
        "evaluation-trace": validate_evaluation_trace,
        "trace-rule-evidence": validate_trace_rule_evidence,
        "audit-evidence": validate_audit_evidence,
        "gateway-audit-event": validate_gateway_audit_event,
        "identity-evidence-reference": validate_identity_evidence_reference,
        "adapter-evidence-reference": validate_adapter_evidence_reference,
    }
)


# ---------------------------------------------------------------------------
# Cross-artifact invariants (pure functions over a loaded scenario dict, so
# they can be reused both for the canonical scenarios and for the negative
# mutation tests below).
# ---------------------------------------------------------------------------


def _request_ids_align(scenario: dict[str, dict]) -> bool:
    ids = {
        scenario["request"]["request_id"],
        scenario["trace"]["request_id"],
        scenario["response"]["request_id"],
        scenario["audit"]["request_id"],
        scenario["gateway"]["request_id"],
    }
    return len(ids) == 1


def _correlation_ids_align(scenario: dict[str, dict]) -> bool:
    request_corr = scenario["request"].get("correlation_id")
    if request_corr is None:
        return True
    for name in ("trace", "response", "audit", "gateway"):
        other = scenario[name].get("correlation_id")
        if other is not None and other != request_corr:
            return False
    return True


def _bundle_provenance_aligns(scenario: dict[str, dict]) -> bool:
    # Permissive: PR F documents that bundle_id/bundle_version are echoed
    # only where each artifact happens to carry them; this checks agreement
    # only where present, never a stronger both-or-none rule.
    seen: dict[str, set[str]] = {}
    for name in ("trace", "response", "audit", "gateway"):
        for field in ("bundle_id", "bundle_version"):
            value = scenario[name].get(field)
            if value is not None:
                seen.setdefault(field, set()).add(value)
    return all(len(values) <= 1 for values in seen.values())


def _response_trace_agree(scenario: dict[str, dict]) -> bool:
    response, trace = scenario["response"], scenario["trace"]
    if response["request_id"] != trace["request_id"]:
        return False
    response_corr = response.get("correlation_id")
    trace_corr = trace.get("correlation_id")
    if response_corr is not None and trace_corr is not None and response_corr != trace_corr:
        return False
    if response["evaluation_status"] != trace["evaluation_status"]:
        return False
    if response["outcome"] != trace["outcome"]:
        return False
    if response.get("failure_reason") != trace.get("failure_reason"):
        return False
    response_trace_id = response.get("trace_id")
    if response_trace_id is not None and response_trace_id != trace["trace_id"]:
        return False
    response_reason = response.get("reason_code")
    trace_reason = trace.get("reason_code")
    if response_reason is not None and trace_reason is not None and response_reason != trace_reason:
        return False
    return True


def _audit_agrees_with_kernel(scenario: dict[str, dict]) -> bool:
    response, audit = scenario["response"], scenario["audit"]
    for field in ("request_id", "evaluation_status", "outcome", "failure_reason"):
        if response.get(field) != audit.get(field):
            return False
    response_trace_id = response.get("trace_id")
    audit_trace_id = audit.get("trace_id")
    if (
        response_trace_id is not None
        and audit_trace_id is not None
        and response_trace_id != audit_trace_id
    ):
        return False
    return True


def _gateway_agrees_with_audit(scenario: dict[str, dict]) -> bool:
    audit, gateway = scenario["audit"], scenario["gateway"]
    if gateway["audit_evidence_id"] != audit["evidence_id"]:
        return False
    if gateway["request_id"] != audit["request_id"]:
        return False
    for field in ("evaluation_status", "outcome", "failure_reason"):
        if gateway.get(field) != audit.get(field):
            return False
    gateway_trace_id = gateway.get("trace_id")
    audit_trace_id = audit.get("trace_id")
    if (
        gateway_trace_id is not None
        and audit_trace_id is not None
        and gateway_trace_id != audit_trace_id
    ):
        return False
    return True


def _trace_rules_exist_in_policy(scenario: dict[str, dict]) -> bool:
    trace, policy = scenario["trace"], scenario["policy"]
    rules_by_id = {rule["rule_id"]: rule for rule in policy.get("rules", [])}
    for entry in trace.get("rule_evidence", []):
        rule = rules_by_id.get(entry["rule_id"])
        if rule is None:
            return False
        if rule["effect"] != entry["effect"]:
            return False
    return True


# ---------------------------------------------------------------------------
# Evidence-provenance invariants (basis-architecture's operation-aware
# evidence-provenance semantics clarification: "Top-Level Explanation
# Provenance," "Rule-Evidence Projection," and "Bundle Identity Provenance").
# Pure functions over a loaded scenario dict, following the same pattern as
# the cross-artifact invariants above, so they can be reused both for the
# canonical scenarios and for the negative mutation tests below.
# ---------------------------------------------------------------------------


def _authored_rules_by_id(policy: dict) -> dict[str, dict]:
    return {rule["rule_id"]: rule for rule in policy.get("rules", [])}


def _top_level_explanations_are_null(scenario: dict[str, dict]) -> bool:
    return all(
        scenario[name].get("explanation") is None
        for name in ("response", "trace", "audit", "gateway")
    )


def _matched_rule_evidence_matches_authored(scenario: dict[str, dict]) -> bool:
    rules_by_id = _authored_rules_by_id(scenario["policy"])
    for entry in scenario["trace"].get("rule_evidence", []):
        if entry.get("rule_result") != "matched":
            continue
        rule = rules_by_id.get(entry["rule_id"])
        if rule is None:
            return False
        if entry.get("reason_code") != rule.get("reason_code"):
            return False
        if entry.get("explanation") != rule.get("explanation"):
            return False
    return True


def _not_matched_or_skipped_omit_rationale(scenario: dict[str, dict]) -> bool:
    for entry in scenario["trace"].get("rule_evidence", []):
        if entry.get("rule_result") not in ("not_matched", "skipped"):
            continue
        if entry.get("reason_code") is not None or entry.get("explanation") is not None:
            return False
    return True


def _bundle_identity_matches_policy(scenario: dict[str, dict]) -> bool:
    expected_id = scenario["policy"].get("bundle_id")
    expected_version = scenario["policy"].get("bundle_version")
    for name in ("response", "trace", "audit", "gateway"):
        if scenario[name].get("bundle_id") != expected_id:
            return False
        if scenario[name].get("bundle_version") != expected_version:
            return False
    return True


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def test_compatibility_directory_exists() -> None:
    assert COMPAT_DIR.is_dir()


def test_compatibility_readme_exists() -> None:
    assert (COMPAT_DIR / "README.md").is_file()


def test_conceptual_documentation_exists() -> None:
    assert (REPO_ROOT / "docs" / "operation-aware-compatibility-vectors.md").is_file()


def test_scenario_directories_exist() -> None:
    for scenario in SCENARIOS:
        assert (COMPAT_DIR / scenario).is_dir(), f"missing scenario directory: {scenario}"


def test_no_unexpected_scenario_directories() -> None:
    actual = {p.name for p in COMPAT_DIR.iterdir() if p.is_dir()}
    assert actual == set(SCENARIOS), f"unexpected scenario directories: {actual - set(SCENARIOS)}"


@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_required_artifacts_present(scenario: str) -> None:
    scenario_dir = COMPAT_DIR / scenario
    for filename in _artifact_filenames(scenario):
        assert (scenario_dir / filename).is_file(), f"{scenario}: missing {filename}"


@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_no_unexpected_artifact_files(scenario: str) -> None:
    scenario_dir = COMPAT_DIR / scenario
    expected = set(_artifact_filenames(scenario))
    actual = {p.name for p in scenario_dir.iterdir() if p.is_file()}
    assert actual == expected, f"{scenario}: unexpected files {actual - expected}"


def test_scenario_identifiers_are_unique() -> None:
    assert len(SCENARIOS) == len(set(SCENARIOS))


# ---------------------------------------------------------------------------
# YAML hygiene
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path", _all_fixture_yaml_files(), ids=lambda p: str(p.relative_to(COMPAT_DIR))
)
def test_every_fixture_parses_as_yaml_with_no_duplicate_keys(path: Path) -> None:
    data = _load_yaml(path)
    assert isinstance(data, dict)


_PLACEHOLDER_MARKERS = ("TODO", "FIXME", "TBD", "XXX", "lorem ipsum")


@pytest.mark.parametrize(
    "path", _all_fixture_yaml_files(), ids=lambda p: str(p.relative_to(COMPAT_DIR))
)
def test_no_placeholder_text_in_fixtures(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for marker in _PLACEHOLDER_MARKERS:
        assert marker.lower() not in text.lower(), f"{path}: placeholder marker {marker!r} present"


@pytest.mark.parametrize(
    "path", _all_fixture_yaml_files(), ids=lambda p: str(p.relative_to(COMPAT_DIR))
)
def test_no_templating_or_runtime_generation_markers(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for marker in ("{{", "}}", "${", "<%", "%>"):
        assert marker not in text, f"{path}: templating marker {marker!r} present"


# ---------------------------------------------------------------------------
# Contract validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_request_validates_against_contract(scenario: str) -> None:
    data = _load_scenario_artifact(scenario, REQUEST_FILENAME)
    assert validate_operation_aware_decision_request(data), f"{scenario}: invalid request fixture"


@pytest.mark.parametrize("scenario", [s for s, cfg in SCENARIOS.items() if cfg["policy_valid"]])
def test_valid_policy_bundle_validates_against_contract(scenario: str) -> None:
    data = _load_scenario_artifact(scenario, SCENARIOS[scenario]["policy_filename"])
    assert validate_policy_bundle(data), (
        f"{scenario}: expected-valid policy bundle failed validation"
    )


def test_invalid_policy_bundle_parses_but_fails_validation() -> None:
    scenario = "invalid-policy-bundle"
    path = COMPAT_DIR / scenario / SCENARIOS[scenario]["policy_filename"]
    # Must parse as ordinary YAML -- the failure is a policy-shape failure,
    # never a YAML syntax failure.
    data = _load_yaml(path)
    assert isinstance(data, dict)
    assert not validate_policy_bundle(data), "invalid-policy-bundle.yaml unexpectedly validated"
    rule_ids = [rule["rule_id"] for rule in data["rules"]]
    assert len(rule_ids) != len(set(rule_ids)), (
        "invalid-policy-bundle.yaml no longer contains the intended duplicate rule_id"
    )


@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_expected_trace_validates_against_contract(scenario: str) -> None:
    data = _load_scenario_artifact(scenario, TRACE_FILENAME)
    assert validate_evaluation_trace(data), f"{scenario}: invalid expected-evaluation-trace fixture"


@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_expected_response_validates_against_contract(scenario: str) -> None:
    data = _load_scenario_artifact(scenario, RESPONSE_FILENAME)
    assert validate_operation_aware_decision_response(data), (
        f"{scenario}: invalid expected-operation-aware-decision-response fixture"
    )


@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_expected_audit_evidence_validates_against_contract(scenario: str) -> None:
    data = _load_scenario_artifact(scenario, AUDIT_FILENAME)
    assert validate_audit_evidence(data), f"{scenario}: invalid expected-audit-evidence fixture"


@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_expected_gateway_event_validates_against_contract(scenario: str) -> None:
    data = _load_scenario_artifact(scenario, GATEWAY_FILENAME)
    assert validate_gateway_audit_event(data), (
        f"{scenario}: invalid expected-gateway-audit-event fixture"
    )


# ---------------------------------------------------------------------------
# Cross-artifact consistency
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_request_ids_align_across_scenario(scenario: str) -> None:
    assert _request_ids_align(_load_scenario(scenario))


@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_correlation_ids_align_where_present(scenario: str) -> None:
    assert _correlation_ids_align(_load_scenario(scenario))


@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_bundle_provenance_aligns_where_present(scenario: str) -> None:
    assert _bundle_provenance_aligns(_load_scenario(scenario))


@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_response_and_trace_agree(scenario: str) -> None:
    assert _response_trace_agree(_load_scenario(scenario))


@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_audit_evidence_agrees_with_kernel_result(scenario: str) -> None:
    assert _audit_agrees_with_kernel(_load_scenario(scenario))


@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_gateway_event_agrees_with_audit_evidence(scenario: str) -> None:
    assert _gateway_agrees_with_audit(_load_scenario(scenario))


@pytest.mark.parametrize("scenario", [s for s, cfg in SCENARIOS.items() if cfg["policy_valid"]])
def test_trace_rule_identifiers_exist_in_policy_with_matching_effect(scenario: str) -> None:
    assert _trace_rules_exist_in_policy(_load_scenario(scenario))


# ---------------------------------------------------------------------------
# Scenario semantics
# ---------------------------------------------------------------------------


def test_allow_basic_semantics() -> None:
    s = _load_scenario("allow-basic")
    assert s["response"]["evaluation_status"] == "completed"
    assert s["response"]["outcome"] == "allow"
    assert s["trace"]["bundle_applicability"] == "applicable"
    matched = [r for r in s["trace"]["rule_evidence"] if r["rule_result"] == "matched"]
    assert any(r["effect"] == "allow" for r in matched)
    assert not any(r["effect"] == "deny" for r in matched)
    assert s["gateway"]["outcome"] == "allow"
    assert s["gateway"]["enforcement_action"] == "allow"


def test_deny_precedence_semantics() -> None:
    s = _load_scenario("deny-precedence")
    matched = [r for r in s["trace"]["rule_evidence"] if r["rule_result"] == "matched"]
    assert any(r["effect"] == "allow" for r in matched), "no matching ALLOW rule recorded"
    assert any(r["effect"] == "deny" for r in matched), "no matching DENY rule recorded"
    assert s["response"]["outcome"] == "deny"
    assert s["gateway"]["outcome"] == "deny"
    assert s["gateway"]["enforcement_action"] == "deny"


def test_default_deny_semantics() -> None:
    s = _load_scenario("default-deny")
    assert s["trace"]["bundle_applicability"] == "applicable"
    assert not any(rule["effect"] == "deny" for rule in s["policy"]["rules"])
    assert not any(entry["rule_result"] == "matched" for entry in s["trace"]["rule_evidence"]), (
        "no rule should have matched in the default-deny scenario"
    )
    assert s["response"]["outcome"] == "deny"
    assert s["gateway"]["outcome"] == "deny"


def test_default_deny_is_distinguishable_from_deny_precedence() -> None:
    default_deny = _load_scenario("default-deny")
    deny_precedence = _load_scenario("deny-precedence")
    # Explicit deny: at least one DENY rule matched.
    assert any(
        entry["rule_result"] == "matched" and entry["effect"] == "deny"
        for entry in deny_precedence["trace"]["rule_evidence"]
    )
    # Default deny: no DENY rule exists in the bundle at all.
    assert not any(rule["effect"] == "deny" for rule in default_deny["policy"]["rules"])
    # Both nonetheless serialize the same outcome value -- no invented
    # default_deny / implicit_deny outcome exists anywhere.
    assert default_deny["response"]["outcome"] == "deny"
    assert deny_precedence["response"]["outcome"] == "deny"


def test_not_applicable_semantics() -> None:
    s = _load_scenario("not-applicable")
    assert s["response"]["evaluation_status"] == "completed"
    assert s["response"]["outcome"] == "not_applicable"
    assert s["trace"]["bundle_applicability"] == "not_applicable"
    assert s["trace"]["rule_evidence"] == []
    assert s["audit"]["outcome"] == "not_applicable"
    # THE critical fail-closed distinction: kernel outcome preserved as
    # not_applicable, never rewritten as deny, while the gateway separately
    # fails closed.
    assert s["gateway"]["outcome"] == "not_applicable"
    assert s["gateway"]["enforcement_action"] == "deny"


def test_invalid_policy_bundle_semantics() -> None:
    # Named scenario directory: "invalid-policy-bundle" (the supplied policy
    # bundle is invalid). Kernel failure category: `policy_validation_failure`
    # -- the bundle is shaped correctly (every rule and every top-level field
    # individually valid) but violates the cross-rule, bundle-level rule_id
    # uniqueness invariant, which is internal-consistency validation, not a
    # structural shape defect (ADR-0002 Section 14). See
    # test_mutation_invalid_policy_bundle_becomes_valid_once_duplicate_is_fixed
    # below, which proves the duplicate rule_id is the fixture's only defect.
    s = _load_scenario("invalid-policy-bundle")
    assert s["response"]["evaluation_status"] == "failed"
    assert s["response"]["outcome"] is None
    assert s["response"]["failure_reason"] == "policy_validation_failure"
    assert s["trace"]["evaluation_status"] == "failed"
    assert s["trace"]["outcome"] is None
    assert s["trace"]["failure_reason"] == "policy_validation_failure"
    assert s["trace"]["bundle_applicability"] is None
    assert s["trace"]["rule_evidence"] == []
    assert s["audit"]["outcome"] is None
    assert s["audit"]["failure_reason"] == "policy_validation_failure"
    assert s["audit"].get("matched_rule_ids") in (None, [])
    # Kernel failed/null state preserved verbatim; gateway fails closed
    # separately, never as a kernel deny.
    assert s["gateway"]["evaluation_status"] == "failed"
    assert s["gateway"]["outcome"] is None
    assert s["gateway"]["failure_reason"] == "policy_validation_failure"
    assert s["gateway"]["enforcement_action"] == "deny"


def test_invalid_policy_bundle_cross_artifact_agreement() -> None:
    """The four result artifacts (trace, response, audit, gateway) must all
    agree on evaluation_status/outcome/failure_reason/request_id -- this is
    the specific cross-artifact agreement this correction must not break by
    updating one artifact's failure_reason without the other three.
    """
    s = _load_scenario("invalid-policy-bundle")
    for field in ("request_id",):
        values = {s[name][field] for name in ("trace", "response", "audit", "gateway")}
        assert len(values) == 1, f"{field} disagrees across result artifacts: {values}"
    for field in ("evaluation_status", "outcome", "failure_reason"):
        values = {s[name].get(field) for name in ("trace", "response", "audit", "gateway")}
        assert len(values) == 1, f"{field} disagrees across result artifacts: {values}"
    assert s["response"]["failure_reason"] == "policy_validation_failure"


def test_invalid_policy_bundle_no_reason_code_invented() -> None:
    """No approved reason-code equivalent for policy_validation_failure is
    published in this repository's governed vocabulary (docs/reason-code.md,
    ADR-0003 Section 12); this scenario must not invent one.
    """
    s = _load_scenario("invalid-policy-bundle")
    assert s["trace"].get("reason_code") is None
    assert s["response"].get("reason_code") is None
    assert s["audit"].get("reason_code") is None
    assert s["gateway"].get("reason_code") is None


# ---------------------------------------------------------------------------
# Evidence-provenance semantics (basis-architecture's operation-aware
# evidence-provenance semantics clarification). See
# docs/operation-aware-compatibility-vectors.md, "Evidence-provenance
# semantics," for the conceptual summary these tests enforce.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_top_level_explanation_is_null_across_all_result_artifacts(scenario: str) -> None:
    """No canonical fixture requires basis-core to synthesize aggregate,
    human-readable top-level explanation prose. explanation is optional and
    non-authoritative; reason_code remains the authoritative machine-
    readable explanation. Null is the correct, complete, expected value when
    no governed stage supplies a top-level explanation -- not a placeholder
    for a missing feature.
    """
    assert _top_level_explanations_are_null(_load_scenario(scenario))


@pytest.mark.parametrize("scenario", [s for s, cfg in SCENARIOS.items() if cfg["policy_valid"]])
def test_matched_rule_evidence_preserves_authored_reason_and_explanation(scenario: str) -> None:
    """A matched rule's trace-rule-evidence reason_code/explanation are that
    rule's own authored fields, preserved verbatim -- never synthesized
    replacement prose. Applies equally to a matched-but-non-decisive ALLOW
    rule under deny precedence: deny precedence governs the final outcome,
    not whether the ALLOW rule genuinely matched.
    """
    assert _matched_rule_evidence_matches_authored(_load_scenario(scenario))


@pytest.mark.parametrize("scenario", [s for s, cfg in SCENARIOS.items() if cfg["policy_valid"]])
def test_not_matched_and_skipped_rules_omit_authored_rationale(scenario: str) -> None:
    """A rule that did not match, or was never reached, emitted no reason
    code and authored no explanation for this evaluation -- its evidence
    entry must not present its authored success/deny rationale as though it
    had.
    """
    assert _not_matched_or_skipped_omit_rationale(_load_scenario(scenario))


def test_deny_precedence_matched_allow_rule_is_evidenced_with_authored_text() -> None:
    """The specific case the clarification calls out by name: a matched-but-
    non-decisive ALLOW rule in the deny-precedence scenario remains genuine
    matched evidence, carrying its own non-null authored reason_code and
    explanation, not omitted merely because a DENY rule also matched.
    """
    s = _load_scenario("deny-precedence")
    rules_by_id = _authored_rules_by_id(s["policy"])
    allow_matches = [
        e
        for e in s["trace"]["rule_evidence"]
        if e["effect"] == "allow" and e["rule_result"] == "matched"
    ]
    assert allow_matches, "deny-precedence scenario must record a matched ALLOW rule"
    for entry in allow_matches:
        rule = rules_by_id[entry["rule_id"]]
        assert entry.get("reason_code") == rule.get("reason_code")
        assert entry.get("explanation") == rule.get("explanation")
        assert entry.get("explanation") is not None


def test_no_rule_result_error_in_current_canonical_scenarios() -> None:
    """The governed error-evidence shape (an errored rule using governed
    error evidence, never its authored success/deny rationale) is not
    exercised by any of the five current canonical scenarios -- deliberately
    deferred (see README.md, "Deferred scenarios": condition-evaluation-
    error). This test documents that fact; it is expected to be updated
    alongside a real governed error-evidence fixture if a future PR adds a
    sixth scenario.
    """
    for scenario in SCENARIOS:
        s = _load_scenario(scenario)
        assert not any(
            entry.get("rule_result") == "error" for entry in s["trace"]["rule_evidence"]
        ), f"{scenario}: unexpectedly has rule_result: error; update this test with the new fixture"


def test_not_applicable_retains_bundle_identity() -> None:
    """A NOT_APPLICABLE outcome preserves the checked bundle's identity as
    provenance for which bundle was checked -- not a claim that the bundle
    applied, matched, or granted anything.
    """
    s = _load_scenario("not-applicable")
    assert s["policy"].get("bundle_id") is not None
    assert _bundle_identity_matches_policy(s)


def test_invalid_policy_bundle_retains_bundle_identity() -> None:
    """A typed semantic policy-validation failure preserves the rejected
    bundle's identity: the bundle constructed successfully as a well-formed,
    identified typed object before being rejected by the cross-rule
    rule_id-uniqueness invariant, so its identity remains known and
    reportable.
    """
    s = _load_scenario("invalid-policy-bundle")
    assert s["policy"].get("bundle_id") is not None
    assert _bundle_identity_matches_policy(s)


# ---------------------------------------------------------------------------
# Security / synthetic-data policy
# ---------------------------------------------------------------------------

FORBIDDEN_FIELD_NAMES = frozenset(
    {
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
        "debug",
        "debug_data",
        "exception",
        "stack_trace",
        "traceback",
        "signature",
        "signature_algorithm",
        "hash_chain",
        "previous_hash",
        "merkle_root",
    }
)

FORBIDDEN_RAW_TEXT_MARKERS = (
    "BEGIN PRIVATE KEY",
    "eyJhbGciOiJ",  # a real-looking JWT header prefix
    "Bearer ",
)


def _collect_keys(value: object, keys: set[str]) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            keys.add(key)
            _collect_keys(nested, keys)
    elif isinstance(value, list):
        for item in value:
            _collect_keys(item, keys)


@pytest.mark.parametrize(
    "path", _all_fixture_yaml_files(), ids=lambda p: str(p.relative_to(COMPAT_DIR))
)
def test_no_forbidden_field_names_in_any_fixture(path: Path) -> None:
    data = _load_yaml(path)
    keys: set[str] = set()
    _collect_keys(data, keys)
    overlap = keys & FORBIDDEN_FIELD_NAMES
    assert not overlap, f"{path}: forbidden field name(s) present: {overlap}"


@pytest.mark.parametrize(
    "path", _all_fixture_yaml_files(), ids=lambda p: str(p.relative_to(COMPAT_DIR))
)
def test_no_forbidden_raw_text_markers_in_any_fixture(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for marker in FORBIDDEN_RAW_TEXT_MARKERS:
        assert marker not in text, f"{path}: forbidden marker {marker!r} present"


def test_digest_values_are_synthetic_lowercase_hexadecimal() -> None:
    for scenario in SCENARIOS:
        request = _load_scenario_artifact(scenario, REQUEST_FILENAME)
        for field in ("identity_evidence_reference", "adapter_evidence_reference"):
            reference = request.get(field)
            if reference is None:
                continue
            digest = reference["evidence_digest"]
            assert re.match(r"^[a-f0-9]+$", digest["value"]), (
                f"{scenario}: {field}.evidence_digest.value is not lowercase hex"
            )


def test_identifiers_use_the_documented_compat_prefixes() -> None:
    for scenario in SCENARIOS:
        request = _load_scenario_artifact(scenario, REQUEST_FILENAME)
        trace = _load_scenario_artifact(scenario, TRACE_FILENAME)
        audit = _load_scenario_artifact(scenario, AUDIT_FILENAME)
        gateway = _load_scenario_artifact(scenario, GATEWAY_FILENAME)
        assert request["request_id"].startswith("req-compat-")
        assert trace["trace_id"].startswith("trace-compat-")
        assert audit["evidence_id"].startswith("audit-compat-")
        assert gateway["event_id"].startswith("gateway-event-compat-")


# ---------------------------------------------------------------------------
# Negative mutation tests: prove the harness detects drift, not merely that
# the authored fixtures happen to be internally consistent.
# ---------------------------------------------------------------------------


def test_mutation_response_request_id_mismatch_is_detected() -> None:
    scenario = _load_scenario("allow-basic")
    scenario["response"]["request_id"] = "req-compat-DIFFERENT-001"
    assert not _request_ids_align(scenario)


def test_mutation_response_outcome_differs_from_trace_is_detected() -> None:
    scenario = _load_scenario("allow-basic")
    scenario["response"]["outcome"] = "deny"
    assert not _response_trace_agree(scenario)


def test_mutation_audit_outcome_differs_from_response_is_detected() -> None:
    scenario = _load_scenario("allow-basic")
    scenario["audit"]["outcome"] = "deny"
    assert not _audit_agrees_with_kernel(scenario)


def test_mutation_gateway_outcome_differs_from_audit_is_detected() -> None:
    scenario = _load_scenario("allow-basic")
    scenario["gateway"]["outcome"] = "deny"
    assert not _gateway_agrees_with_audit(scenario)


def test_mutation_gateway_references_wrong_evidence_record_is_detected() -> None:
    scenario = _load_scenario("allow-basic")
    scenario["gateway"]["audit_evidence_id"] = "audit-compat-WRONG-RECORD"
    assert not _gateway_agrees_with_audit(scenario)


def test_mutation_trace_rule_effect_differs_from_policy_rule_is_detected() -> None:
    scenario = _load_scenario("allow-basic")
    scenario["trace"]["rule_evidence"][0]["effect"] = "deny"
    assert not _trace_rules_exist_in_policy(scenario)


def test_mutation_trace_refers_to_nonexistent_rule_id_is_detected() -> None:
    scenario = _load_scenario("allow-basic")
    scenario["trace"]["rule_evidence"][0]["rule_id"] = "rule-does-not-exist-in-bundle"
    assert not _trace_rules_exist_in_policy(scenario)


def test_mutation_not_applicable_trace_with_rule_evidence_is_rejected() -> None:
    scenario = _load_scenario("not-applicable")
    scenario["trace"]["rule_evidence"] = [
        {"rule_id": "allow-operator-hvac-write", "effect": "allow", "rule_result": "skipped"}
    ]
    assert not validate_evaluation_trace(scenario["trace"])


def test_mutation_failed_response_carrying_allow_is_rejected() -> None:
    scenario = _load_scenario("invalid-policy-bundle")
    scenario["response"]["outcome"] = "allow"
    assert not validate_operation_aware_decision_response(scenario["response"])


def test_mutation_invalid_policy_bundle_becomes_valid_once_duplicate_is_fixed() -> None:
    scenario = _load_scenario("invalid-policy-bundle")
    fixed = scenario["policy"]
    fixed["rules"][1]["rule_id"] = "deny-duplicate-rule-renamed"
    assert validate_policy_bundle(fixed), (
        "renaming the duplicate rule_id should make the bundle valid"
    )


def test_mutation_valid_policy_bundle_becomes_invalid_with_injected_duplicate() -> None:
    scenario = _load_scenario("allow-basic")
    bundle = scenario["policy"]
    bundle["rules"].append(copy.deepcopy(bundle["rules"][0]))
    assert not validate_policy_bundle(bundle), (
        "duplicate rule_id should invalidate an otherwise-valid bundle"
    )


def test_mutation_synthesized_top_level_explanation_is_detected() -> None:
    scenario = _load_scenario("allow-basic")
    scenario["response"]["explanation"] = "A synthesized aggregate sentence."
    assert not _top_level_explanations_are_null(scenario)


def test_mutation_matched_rule_explanation_diverging_from_authored_text_is_detected() -> None:
    scenario = _load_scenario("allow-basic")
    scenario["trace"]["rule_evidence"][0]["explanation"] = "A different, synthesized sentence."
    assert not _matched_rule_evidence_matches_authored(scenario)


def test_mutation_matched_rule_reason_code_diverging_from_authored_value_is_detected() -> None:
    scenario = _load_scenario("allow-basic")
    scenario["trace"]["rule_evidence"][0]["reason_code"] = "deny_rule_matched"
    assert not _matched_rule_evidence_matches_authored(scenario)


def test_mutation_not_matched_rule_gaining_authored_rationale_is_detected() -> None:
    scenario = _load_scenario("default-deny")
    entry = scenario["trace"]["rule_evidence"][0]
    assert entry["rule_result"] == "not_matched"
    entry["reason_code"] = "allow_rule_matched"
    entry["explanation"] = "Operators may read AHU telemetry."
    assert not _not_matched_or_skipped_omit_rationale(scenario)


def test_mutation_not_applicable_bundle_identity_nulled_out_is_detected() -> None:
    scenario = _load_scenario("not-applicable")
    scenario["response"]["bundle_id"] = None
    scenario["response"]["bundle_version"] = None
    assert not _bundle_identity_matches_policy(scenario)


def test_mutation_invalid_policy_bundle_identity_nulled_out_is_detected() -> None:
    scenario = _load_scenario("invalid-policy-bundle")
    scenario["trace"]["bundle_id"] = None
    scenario["trace"]["bundle_version"] = None
    assert not _bundle_identity_matches_policy(scenario)


# ---------------------------------------------------------------------------
# Hermeticity: this suite must never depend on comparing against a moving
# branch pointer (the CI hazard a prior PR in this repository's history
# already fixed once). This asserts that no tests/*.py file shells out to
# the version control tool with a two-branch comparison subcommand against
# an upstream-tracking or trunk reference.
#
# The token pieces below are deliberately split so that *this detector's
# own source* never itself reconstructs, on one line, the exact phrase it
# is searching for in every other file -- keeping a manual repository-wide
# text search for that phrase clean everywhere, including here.
# ---------------------------------------------------------------------------


_TOK_A = "git"
_TOK_B = "diff"
_TOK_C = "show"
_TOK_D = "main"
_TOK_E = "origin" + "/" + _TOK_D

_BRANCH_DEPENDENT_GIT_PATTERNS = (
    re.compile(_TOK_A + r"\s+" + _TOK_B + r"\s+" + _TOK_D),
    re.compile(_TOK_A + r"\s+" + _TOK_C + r"\s+" + _TOK_D),
    re.compile(_TOK_A + r"\s+" + _TOK_B + r"\s+" + _TOK_E),
    re.compile(_TOK_A + r"\s+" + _TOK_C + r"\s+" + _TOK_E),
)


def test_tests_directory_has_no_branch_dependent_git_usage() -> None:
    offenders: list[str] = []
    for path in (REPO_ROOT / "tests").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for pattern in _BRANCH_DEPENDENT_GIT_PATTERNS:
            if pattern.search(text):
                offenders.append(f"{path.name}: {pattern.pattern}")
    assert not offenders, offenders
