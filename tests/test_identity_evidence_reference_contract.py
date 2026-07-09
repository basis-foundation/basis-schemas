"""Focused checks on the published identity-evidence-reference contract.

These tests validate
``schemas/identity-evidence-reference/identity-evidence-reference.yaml``: its
metadata, its declared dependencies, and that the published field policy
(including the nested ``evidence_digest`` shape and the reused
``redaction_classification`` vocabulary) accepts well-formed identity evidence
references and rejects malformed ones — in particular any reference that
tries to carry a raw token, cookie, credential, or full claim set.

This is a contract publication, not a parser: the only behavior exercised
here is applying the contract's own published rules (required fields, the
no-unknown-fields policy, the digest sub-shape, and the redaction
classification enum) to example reference objects.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import basis_schemas

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
REFERENCE_DIR = REPO_ROOT / "schemas" / "identity-evidence-reference"
REFERENCE_FILE = REFERENCE_DIR / "identity-evidence-reference.yaml"

#: Fields that must never appear on this contract — raw secrets, tokens, or
#: complete claim sets. Regression coverage for the architecture's explicit
#: prohibition list.
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
    "raw_claims",
    "full_claim_set",
    "credential",
)


def _load() -> dict:
    with REFERENCE_FILE.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict), "identity-evidence-reference.yaml must parse to a mapping"
    return data


def _body() -> dict:
    return _load()["identity_evidence_reference"]


def _field(fields: list, field_id: str) -> dict:
    for field in fields:
        if field["id"] == field_id:
            return field
    raise AssertionError(f"field {field_id!r} not declared")


def _is_valid_reference(obj: object, body: dict) -> bool:
    """Apply the contract's own published rules to a candidate reference."""
    if not isinstance(obj, dict):
        return False

    allowed = set(body["required"]) | set(body["optional"])
    if not body["additional_properties"] and set(obj) - allowed:
        return False

    if any(field not in obj for field in body["required"]):
        return False

    for field in ("reference_id", "identity_source"):
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


def test_identity_evidence_reference_file_exists() -> None:
    assert REFERENCE_FILE.is_file(), (
        "schemas/identity-evidence-reference/identity-evidence-reference.yaml must exist"
    )


def test_identity_evidence_reference_yaml_parses() -> None:
    assert _load()


def test_contract_metadata_matches_expected_values() -> None:
    contract = _load()["contract"]
    assert contract["name"] == "identity-evidence-reference"
    assert contract["title"] == "BASIS Identity Evidence Reference"
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
        "identity_source",
        "redaction_classification",
    ]
    assert body["optional"] == [
        "normalization_version",
        "mapping_version",
        "request_id",
        "correlation_id",
    ]
    assert body["additional_properties"] is False


def test_evidence_digest_shape() -> None:
    digest_shape = _body()["evidence_digest_shape"]
    assert digest_shape["required"] == ["algorithm", "value"]
    assert digest_shape["additional_properties"] is False


def test_digest_algorithm_pattern_accepts_open_lowercase_labels() -> None:
    pattern = re.compile(_field(_body()["evidence_digest_shape"]["fields"], "algorithm")["pattern"])
    for good in ("sha-256", "sha3-256", "blake3", "md5"):
        assert pattern.match(good), f"valid algorithm label rejected: {good!r}"
    for bad in ("SHA256", "sha_256", "", "-sha256"):
        assert not pattern.match(bad), f"malformed algorithm label accepted: {bad!r}"


def test_digest_value_pattern_accepts_lowercase_hex_only() -> None:
    pattern = re.compile(_field(_body()["evidence_digest_shape"]["fields"], "value")["pattern"])
    assert pattern.match("9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08")
    for bad in ("", "SHA256HEX", "sha256:9f86d081", "0x9f86d081", "9f86 d081"):
        assert not pattern.match(bad), f"malformed digest value accepted: {bad!r}"


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
    # tokens, credentials, or full claim sets.
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
    assert "identity_source" in reasons
    assert "redaction_classification" in reasons or "redaction classification" in reasons
    assert "request_id" in reasons  # malformed request_id
    assert "access token" in reasons or "access_token" in reasons
    assert "claim" in reasons  # raw claim set rejected
    assert "unknown" in reasons or "additional" in reasons


def test_evidence_reference_is_provider_neutral() -> None:
    # No OIDC- or JWT-specific field is required; identity_source is the
    # only required provenance field and is a plain, opaque string.
    identity_source_field = _field(_body()["fields"], "identity_source")
    assert identity_source_field["type"] == "string"
    field_ids = {f["id"] for f in _body()["fields"]}
    assert "issuer" not in field_ids
    assert "iss" not in field_ids
    assert "jwks_uri" not in field_ids


def test_new_evidence_reference_contract_is_tracked_in_metadata() -> None:
    assert (
        "identity-evidence-reference" in basis_schemas.OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS
    )
    assert "identity-evidence-reference" not in basis_schemas.PLANNED_CONTRACTS
    assert "identity-evidence-reference" not in basis_schemas.PUBLISHED_CONTRACTS
    assert (
        "identity-evidence-reference" not in basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS
    )
