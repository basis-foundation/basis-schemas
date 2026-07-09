"""Focused checks on the published adapter-evidence-reference contract.

These tests validate
``schemas/adapter-evidence-reference/adapter-evidence-reference.yaml``: its
metadata, its declared dependencies, and that the published field policy
(including the nested ``evidence_digest`` shape, the open ``protocol``
label, and the reused ``redaction_classification`` vocabulary) accepts
well-formed adapter evidence references and rejects malformed ones — in
particular any reference that tries to carry a raw protocol payload or
device credential.

This is a contract publication, not a parser: the only behavior exercised
here is applying the contract's own published rules (required fields, the
no-unknown-fields policy, the digest sub-shape, the protocol pattern, and
the redaction classification enum) to example reference objects.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import basis_schemas

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
REFERENCE_DIR = REPO_ROOT / "schemas" / "adapter-evidence-reference"
REFERENCE_FILE = REFERENCE_DIR / "adapter-evidence-reference.yaml"
IDENTITY_REFERENCE_FILE = (
    REPO_ROOT / "schemas" / "identity-evidence-reference" / "identity-evidence-reference.yaml"
)

#: Fields that must never appear on this contract — raw protocol payloads or
#: device credentials. Regression coverage for the architecture's explicit
#: prohibition list.
FORBIDDEN_FIELDS = (
    "raw_payload",
    "raw_protocol_payload",
    "packet",
    "frame",
    "credential",
    "password",
    "api_key",
    "private_key",
    "unredacted_device_secret",
)

#: Protocols already published by basis-adapters, per its own roadmap. The
#: protocol field must accept all of these without being a closed enum.
KNOWN_PROTOCOLS = (
    "rest",
    "bacnet",
    "modbus",
    "opcua",
    "mqtt",
    "dnp3",
    "iec61850",
    "knx",
    "niagara",
)


def _load() -> dict:
    with REFERENCE_FILE.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict), "adapter-evidence-reference.yaml must parse to a mapping"
    return data


def _body() -> dict:
    return _load()["adapter_evidence_reference"]


def _identity_body() -> dict:
    with IDENTITY_REFERENCE_FILE.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data["identity_evidence_reference"]


def _field(fields: list, field_id: str) -> dict:
    for field in fields:
        if field["id"] == field_id:
            return field
    raise AssertionError(f"field {field_id!r} not declared")


def _field_shape(fields: list, field_id: str) -> dict:
    """A field's definition with the free-text ``description`` stripped, so
    cross-contract parity checks compare validation-relevant keys only (type,
    required, default, non_empty, pattern, enum, governed_by) and are not
    tripped up by descriptions that legitimately differ because one contract
    talks about "identity evidence" and the other about "adapter evidence".
    """
    return {k: v for k, v in _field(fields, field_id).items() if k != "description"}


def _is_valid_reference(obj: object, body: dict) -> bool:
    """Apply the contract's own published rules to a candidate reference."""
    if not isinstance(obj, dict):
        return False

    allowed = set(body["required"]) | set(body["optional"])
    if not body["additional_properties"] and set(obj) - allowed:
        return False

    if any(field not in obj for field in body["required"]):
        return False

    for field in ("reference_id", "adapter_source"):
        value = obj.get(field)
        if not isinstance(value, str) or not value.strip():
            return False

    digest = obj.get("evidence_digest")
    digest_shape = body["evidence_digest_shape"]
    if not isinstance(digest, dict):
        return False
    allowed_digest = set(digest_shape["required"])
    if not digest_shape["additional_properties"] and set(digest) - allowed_digest:
        return False
    if any(field not in digest for field in digest_shape["required"]):
        return False
    algorithm_pattern = re.compile(_field(digest_shape["fields"], "algorithm")["pattern"])
    value_pattern = re.compile(_field(digest_shape["fields"], "value")["pattern"])
    if not isinstance(digest.get("algorithm"), str) or not algorithm_pattern.match(
        digest["algorithm"]
    ):
        return False
    if not isinstance(digest.get("value"), str) or not value_pattern.match(digest["value"]):
        return False

    if obj.get("redaction_classification") not in body["redaction_classification_values"]:
        return False

    if "protocol" in obj and obj["protocol"] is not None:
        protocol_pattern = re.compile(_field(body["fields"], "protocol")["pattern"])
        if not isinstance(obj["protocol"], str) or not protocol_pattern.match(obj["protocol"]):
            return False

    if "request_id" in obj and obj["request_id"] is not None:
        if not isinstance(obj["request_id"], str) or not obj["request_id"].strip():
            return False

    if "correlation_id" in obj and obj["correlation_id"] is not None:
        if not isinstance(obj["correlation_id"], str):
            return False

    for field in ("normalization_version", "mapping_version"):
        if field in obj and obj[field] is not None and not isinstance(obj[field], str):
            return False

    return True


def test_adapter_evidence_reference_file_exists() -> None:
    assert REFERENCE_FILE.is_file(), (
        "schemas/adapter-evidence-reference/adapter-evidence-reference.yaml must exist"
    )


def test_adapter_evidence_reference_yaml_parses() -> None:
    assert _load()


def test_contract_metadata_matches_expected_values() -> None:
    contract = _load()["contract"]
    assert contract["name"] == "adapter-evidence-reference"
    assert contract["title"] == "BASIS Adapter Evidence Reference"
    assert isinstance(contract.get("version"), str) and contract["version"]
    assert contract["governed_by"] == "basis-architecture"
    assert contract["published_by"] == "basis-schemas"


def test_lifecycle_is_experimental() -> None:
    assert _load()["contract"]["lifecycle"] == "experimental"


def test_contract_metadata_dependencies_are_declared() -> None:
    depends_on = _load()["contract"].get("depends_on")
    assert isinstance(depends_on, list), "contract.depends_on must be a list"
    assert "contract-metadata" in depends_on
    assert "redaction-classification" in depends_on


def test_does_not_depend_on_reason_code() -> None:
    # This contract carries no reason_code field, so it must not declare a
    # dependency on reason-code merely for conceptual proximity.
    depends_on = _load()["contract"].get("depends_on", [])
    assert "reason-code" not in depends_on


def test_required_and_optional_fields() -> None:
    body = _body()
    assert body["required"] == [
        "reference_id",
        "evidence_digest",
        "adapter_source",
        "redaction_classification",
    ]
    assert body["optional"] == [
        "normalization_version",
        "mapping_version",
        "protocol",
        "request_id",
        "correlation_id",
    ]
    assert body["additional_properties"] is False


def test_evidence_digest_shape() -> None:
    digest_shape = _body()["evidence_digest_shape"]
    assert digest_shape["required"] == ["algorithm", "value"]
    assert digest_shape["additional_properties"] is False


def test_evidence_digest_shape_matches_identity_reference_contract() -> None:
    # The digest sub-shape is deliberately identical across both
    # evidence-reference contracts.
    identity_digest_shape = _identity_body()["evidence_digest_shape"]
    assert _body()["evidence_digest_shape"]["required"] == identity_digest_shape["required"]
    assert (
        _body()["evidence_digest_shape"]["additional_properties"]
        == identity_digest_shape["additional_properties"]
    )


def test_shared_reference_semantics_match_between_identity_and_adapter_contracts() -> None:
    """Cross-contract parity check for the concepts the two evidence-reference
    contracts intentionally share: ``reference_id``, ``evidence_digest``
    (required fields, algorithm validation, digest value validation),
    ``redaction_classification``, optional ``request_id``, optional
    ``correlation_id``, and the ``additional_properties: false`` policy.

    Deliberately excluded from this comparison: each contract's
    producer-specific fields (``identity_source`` vs. ``adapter_source``,
    ``protocol``) and each contract's own ``normalization_version`` /
    ``mapping_version`` (same field names, but contract-specific provenance
    semantics — not one of the shared concepts this PR aligns). Free-text
    ``description`` values are also excluded: they legitimately differ
    because one contract talks about "identity evidence" and the other about
    "adapter evidence"; only validation-relevant keys are compared.

    This does not require the two contracts to be identical, and it does not
    introduce a generic shared ``evidence-reference`` contract — it only
    proves the two independently published contracts stayed aligned on the
    parts they were designed to share.
    """
    identity_body = _identity_body()
    adapter_body = _body()

    # additional_properties: false on both top-level shapes.
    assert identity_body["additional_properties"] is False
    assert adapter_body["additional_properties"] is False

    # reference_id: identical validation-relevant definition.
    assert _field_shape(identity_body["fields"], "reference_id") == _field_shape(
        adapter_body["fields"], "reference_id"
    )

    # evidence_digest: identical top-level field definition...
    assert _field_shape(identity_body["fields"], "evidence_digest") == _field_shape(
        adapter_body["fields"], "evidence_digest"
    )
    # ...identical required fields and additional_properties policy on the
    # nested shape...
    identity_digest_shape = identity_body["evidence_digest_shape"]
    adapter_digest_shape = adapter_body["evidence_digest_shape"]
    assert identity_digest_shape["required"] == adapter_digest_shape["required"]
    assert (
        identity_digest_shape["additional_properties"]
        == adapter_digest_shape["additional_properties"]
    )
    # ...and identical algorithm / digest-value validation rules.
    for sub_field in ("algorithm", "value"):
        assert _field_shape(identity_digest_shape["fields"], sub_field) == _field_shape(
            adapter_digest_shape["fields"], sub_field
        )

    # redaction_classification: identical field definition (enum, governed_by,
    # required) and identical reproduced value list.
    assert _field_shape(identity_body["fields"], "redaction_classification") == _field_shape(
        adapter_body["fields"], "redaction_classification"
    )
    assert (
        identity_body["redaction_classification_values"]
        == adapter_body["redaction_classification_values"]
    )

    # request_id / correlation_id: identical optional-association semantics.
    assert _field_shape(identity_body["fields"], "request_id") == _field_shape(
        adapter_body["fields"], "request_id"
    )
    assert _field_shape(identity_body["fields"], "correlation_id") == _field_shape(
        adapter_body["fields"], "correlation_id"
    )


def test_digest_algorithm_pattern_accepts_open_lowercase_labels() -> None:
    pattern = re.compile(_field(_body()["evidence_digest_shape"]["fields"], "algorithm")["pattern"])
    for good in ("sha-256", "sha3-256", "blake3", "md5"):
        assert pattern.match(good), f"valid algorithm label rejected: {good!r}"
    for bad in ("SHA256", "sha_256", "", "-sha256"):
        assert not pattern.match(bad), f"malformed algorithm label accepted: {bad!r}"


def test_digest_value_pattern_accepts_lowercase_hex_only() -> None:
    pattern = re.compile(_field(_body()["evidence_digest_shape"]["fields"], "value")["pattern"])
    assert pattern.match("1f825aa2f0020ef7cf91dfa30da4668d791c5d4824fc8e41354b89ec05795ab")
    for bad in ("", "SHA256HEX", "sha256:1f825aa2", "0x1f825aa2", "1f82 5aa2"):
        assert not pattern.match(bad), f"malformed digest value accepted: {bad!r}"


def test_protocol_pattern_is_open_not_a_closed_enum() -> None:
    field = _field(_body()["fields"], "protocol")
    assert "enum" not in field, "protocol must not be a closed enum"
    pattern = re.compile(field["pattern"])
    for protocol in KNOWN_PROTOCOLS:
        assert pattern.match(protocol), f"known protocol rejected: {protocol!r}"
    # A protocol basis-adapters has not published yet must still validate,
    # proving the field is open rather than an enumeration of known values.
    assert pattern.match("future-protocol")
    for bad in ("Modbus", "MODBUS", ""):
        assert not pattern.match(bad), f"malformed protocol label accepted: {bad!r}"


def test_redaction_classification_values_match_published_contract() -> None:
    # Reused, not duplicated: must match the real redaction-classification
    # contract's published ids exactly.
    redaction_file = (
        REPO_ROOT / "schemas" / "redaction-classification" / "redaction-classification.yaml"
    )
    with redaction_file.open(encoding="utf-8") as handle:
        canonical = yaml.safe_load(handle)
    canonical_ids = [v["id"] for v in canonical["redaction_classification"]["values"]]
    assert _body()["redaction_classification_values"] == canonical_ids


def test_no_forbidden_secret_or_raw_evidence_fields_defined() -> None:
    # Regression: the schema itself must never define a field for raw
    # protocol payloads or device credentials.
    field_ids = {f["id"] for f in _body()["fields"]}
    for forbidden in FORBIDDEN_FIELDS:
        assert forbidden not in field_ids, f"forbidden field defined on contract: {forbidden!r}"
    allowed = set(_body()["required"]) | set(_body()["optional"])
    for forbidden in FORBIDDEN_FIELDS:
        assert forbidden not in allowed


def test_required_valid_examples_accepted() -> None:
    body = _body()
    for example in body["examples"]["valid"]:
        assert _is_valid_reference(example, body), f"valid example rejected: {example!r}"


def test_required_invalid_examples_rejected() -> None:
    body = _body()
    for case in body["examples"]["invalid"]:
        assert "reason" in case, f"invalid example missing a reason: {case!r}"
        assert not _is_valid_reference(case["value"], body), (
            f"invalid reference accepted ({case['reason']}): {case['value']!r}"
        )


def test_invalid_examples_cover_required_cases() -> None:
    reasons = " ".join(case["reason"] for case in _body()["examples"]["invalid"]).lower()
    assert "missing required reference_id" in reasons
    assert "empty reference_id" in reasons
    assert "evidence_digest" in reasons  # missing / malformed digest cases
    assert "algorithm" in reasons  # invalid digest algorithm format
    assert "digest value" in reasons  # malformed digest value
    assert "adapter_source" in reasons
    assert "redaction_classification" in reasons or "redaction classification" in reasons
    assert "protocol" in reasons  # malformed protocol label
    assert "request_id" in reasons  # malformed request_id
    assert "raw protocol payload" in reasons or "raw_protocol_payload" in reasons
    assert "device" in reasons or "secret" in reasons  # device credential rejected
    assert "unknown" in reasons or "additional" in reasons


def test_evidence_reference_is_protocol_neutral_at_top_level() -> None:
    # protocol is optional and adapter_source is a plain opaque string; no
    # protocol-specific top-level payload field is defined.
    field_ids = {f["id"] for f in _body()["fields"]}
    assert "protocol" in field_ids
    for protocol_specific in ("register", "point", "object_id", "node_id", "group_address"):
        assert protocol_specific not in field_ids


def test_new_evidence_reference_contract_is_tracked_in_metadata() -> None:
    assert (
        "adapter-evidence-reference" in basis_schemas.OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS
    )
    assert "adapter-evidence-reference" not in basis_schemas.PLANNED_CONTRACTS
    assert "adapter-evidence-reference" not in basis_schemas.PUBLISHED_CONTRACTS
    assert (
        "adapter-evidence-reference" not in basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS
    )
