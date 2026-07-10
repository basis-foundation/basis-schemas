"""Lightweight checks on repository metadata.

These tests validate the package metadata and its agreement with the planned
migration order. They do not validate any contract, because no contract has been
migrated yet.
"""

from __future__ import annotations

import re
from pathlib import Path

import basis_schemas

REPO_ROOT = Path(__file__).resolve().parent.parent

#: The full, flat, release-readiness-review inventory: the six first-wave
#: contracts followed by the fourteen additive operation-aware second-wave
#: contracts, in publication order (PR A through PR F; PR G published no
#: new contract). This is deliberately a single, non-decomposed list — the
#: per-wave tuples above are exercised individually elsewhere, but nothing
#: else in this suite asserts "exactly these twenty names, no more, no
#: fewer, all in one place," which is what a release-readiness review needs
#: to see at a glance.
ALL_PUBLISHED_CONTRACTS: tuple[str, ...] = (
    # First wave (six contracts)
    "vocabulary",
    "action-string",
    "resource-identifier",
    "decision-request",
    "decision-response",
    "audit-event",
    # Second wave, PR A — shared metadata and vocabulary
    "contract-metadata",
    "redaction-classification",
    "reason-code",
    # Second wave, PR B — evidence references
    "identity-evidence-reference",
    "adapter-evidence-reference",
    # Second wave, PR C — operation-aware decision request
    "operation-aware-decision-request",
    # Second wave, PR D — policy bundle and rule contracts
    "policy-condition",
    "policy-rule",
    "policy-bundle",
    # Second wave, PR E — response and trace contracts
    "trace-rule-evidence",
    "evaluation-trace",
    "operation-aware-decision-response",
    # Second wave, PR F — audit contracts
    "audit-evidence",
    "gateway-audit-event",
)


def test_project_name() -> None:
    assert basis_schemas.PROJECT_NAME == "basis-schemas"


def test_all_published_contracts_list_has_twenty_unique_entries() -> None:
    # Sanity check on the literal list above, independent of the filesystem
    # or the package's own tuples: exactly twenty names, no duplicates.
    assert len(ALL_PUBLISHED_CONTRACTS) == 20
    assert len(set(ALL_PUBLISHED_CONTRACTS)) == 20


def test_all_published_contracts_list_matches_package_tuples() -> None:
    # The flat inventory above must equal the union of every published-contract
    # tracking tuple the package exports, with no name missing and no
    # unexpected extra name.
    from_package = (
        set(basis_schemas.PUBLISHED_CONTRACTS)
        | set(basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS)
        | set(basis_schemas.OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS)
        | set(basis_schemas.OPERATION_AWARE_REQUEST_CONTRACTS)
        | set(basis_schemas.OPERATION_AWARE_POLICY_CONTRACTS)
        | set(basis_schemas.OPERATION_AWARE_RESPONSE_TRACE_CONTRACTS)
        | set(basis_schemas.OPERATION_AWARE_AUDIT_CONTRACTS)
    )
    assert set(ALL_PUBLISHED_CONTRACTS) == from_package


def test_all_published_contracts_have_a_schema_directory_and_file() -> None:
    # Every one of the twenty published contracts has a real schema
    # definition on disk, discoverable at the conventional path.
    for contract in ALL_PUBLISHED_CONTRACTS:
        directory = REPO_ROOT / "schemas" / contract
        assert directory.is_dir(), f"missing schema directory: {contract}"
        schema_file = directory / f"{contract}.yaml"
        assert schema_file.is_file(), f"missing schema file: {schema_file}"


def test_schemas_directory_has_no_unexpected_contract_directories() -> None:
    # The inverse of the check above: no schema directory exists that isn't
    # one of the twenty tracked contracts (guards against a contract being
    # published without being added to a tracking tuple).
    schemas_dir = REPO_ROOT / "schemas"
    actual = {p.name for p in schemas_dir.iterdir() if p.is_dir()}
    assert actual == set(ALL_PUBLISHED_CONTRACTS), (
        f"unexpected schema directories: {actual - set(ALL_PUBLISHED_CONTRACTS)}; "
        f"missing schema directories: {set(ALL_PUBLISHED_CONTRACTS) - actual}"
    )


def test_package_version_matches_pyproject_version() -> None:
    # basis_schemas.__version__ and the [project].version declared in
    # pyproject.toml must never drift apart. Parsed with a narrow regex
    # rather than a TOML parser to avoid adding a new dependency for one
    # field; this repository targets Python 3.10, which has no stdlib
    # `tomllib` (added in 3.11).
    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', pyproject_text)
    assert match, "could not find [project].version in pyproject.toml"
    assert basis_schemas.__version__ == match.group(1)


def test_version_is_a_string() -> None:
    assert isinstance(basis_schemas.__version__, str)
    assert basis_schemas.__version__


def test_planned_contracts_match_migration_order() -> None:
    # The six first-wave contracts, in the order recorded in
    # docs/migration-plan.md and the basis-architecture charter.
    assert basis_schemas.PLANNED_CONTRACTS == (
        "vocabulary",
        "action-string",
        "resource-identifier",
        "decision-request",
        "decision-response",
        "audit-event",
    )


def test_contract_states_are_ordered_by_commitment() -> None:
    assert basis_schemas.CONTRACT_STATES == (
        "experimental",
        "candidate",
        "stable",
    )


def test_published_contracts_is_a_subset_in_planned_order() -> None:
    # All six planned contracts — vocabulary, action-string, resource-identifier,
    # decision-request, decision-response, and audit-event — are now published.
    # Published contracts must be a prefix of the planned order (migration
    # proceeds in order, lowest-risk first); with the wave complete, that prefix
    # is the whole planned list.
    assert basis_schemas.PUBLISHED_CONTRACTS == (
        "vocabulary",
        "action-string",
        "resource-identifier",
        "decision-request",
        "decision-response",
        "audit-event",
    )
    published = basis_schemas.PUBLISHED_CONTRACTS
    planned_prefix = basis_schemas.PLANNED_CONTRACTS[: len(published)]
    assert published == planned_prefix


def test_all_planned_contracts_are_published() -> None:
    # Every currently planned contract is published. This is not a claim that the
    # contract set is closed forever — future contracts may be added through
    # basis-architecture governance and would extend PLANNED_CONTRACTS.
    assert set(basis_schemas.PUBLISHED_CONTRACTS) == set(basis_schemas.PLANNED_CONTRACTS)


def test_repository_is_past_phase1_foundation() -> None:
    # The placeholder-only foundation phase is over now that the vocabulary
    # contract is published. This flips back only if all contracts are unpublished.
    assert basis_schemas.is_phase1_foundation() is False


def test_operation_aware_shared_metadata_contracts_match_pr_a() -> None:
    # The three shared contracts published by PR A of the operation-aware
    # schema readiness plan (ADR-0005), in publication order.
    assert basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS == (
        "contract-metadata",
        "redaction-classification",
        "reason-code",
    )


def test_operation_aware_shared_metadata_contracts_do_not_extend_first_wave() -> None:
    # The second wave is additive and separate: it must not appear in, or
    # change the length of, the first-wave six-contract tuples.
    assert len(basis_schemas.PLANNED_CONTRACTS) == 6
    assert len(basis_schemas.PUBLISHED_CONTRACTS) == 6
    for contract in basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS:
        assert contract not in basis_schemas.PLANNED_CONTRACTS
        assert contract not in basis_schemas.PUBLISHED_CONTRACTS


def test_operation_aware_evidence_reference_contracts_match_pr_b() -> None:
    # The two evidence-reference contracts published by PR B of the
    # operation-aware schema readiness plan (ADR-0005), in publication order.
    assert basis_schemas.OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS == (
        "identity-evidence-reference",
        "adapter-evidence-reference",
    )


def test_operation_aware_evidence_reference_contracts_do_not_extend_first_wave() -> None:
    # PR B is additive and separate: it must not appear in, or change the
    # length of, the first-wave six-contract tuples.
    assert len(basis_schemas.PLANNED_CONTRACTS) == 6
    assert len(basis_schemas.PUBLISHED_CONTRACTS) == 6
    for contract in basis_schemas.OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS:
        assert contract not in basis_schemas.PLANNED_CONTRACTS
        assert contract not in basis_schemas.PUBLISHED_CONTRACTS


def test_operation_aware_evidence_reference_contracts_disjoint_from_pr_a() -> None:
    # PR B must never be conflated with PR A's shared metadata contracts: no
    # name should appear in both tracking tuples.
    pr_a = set(basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS)
    pr_b = set(basis_schemas.OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS)
    assert not (pr_a & pr_b), f"contract names appear in both PR A and PR B: {pr_a & pr_b}"


def test_operation_aware_request_contracts_match_pr_c() -> None:
    # The one operation-aware request contract published by PR C of the
    # operation-aware schema readiness plan (ADR-0005).
    assert basis_schemas.OPERATION_AWARE_REQUEST_CONTRACTS == ("operation-aware-decision-request",)


def test_operation_aware_request_contracts_do_not_extend_first_wave() -> None:
    # PR C is additive and separate: it must not appear in, or change the
    # length of, the first-wave six-contract tuples.
    assert len(basis_schemas.PLANNED_CONTRACTS) == 6
    assert len(basis_schemas.PUBLISHED_CONTRACTS) == 6
    for contract in basis_schemas.OPERATION_AWARE_REQUEST_CONTRACTS:
        assert contract not in basis_schemas.PLANNED_CONTRACTS
        assert contract not in basis_schemas.PUBLISHED_CONTRACTS


def test_operation_aware_request_contracts_disjoint_from_pr_a_and_pr_b() -> None:
    # PR C must never be conflated with PR A's shared metadata contracts or
    # PR B's evidence-reference contracts: no name should appear in more than
    # one tracking tuple.
    pr_a = set(basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS)
    pr_b = set(basis_schemas.OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS)
    pr_c = set(basis_schemas.OPERATION_AWARE_REQUEST_CONTRACTS)
    assert not (pr_a & pr_c), f"contract names appear in both PR A and PR C: {pr_a & pr_c}"
    assert not (pr_b & pr_c), f"contract names appear in both PR B and PR C: {pr_b & pr_c}"


def test_operation_aware_policy_contracts_match_pr_d() -> None:
    # The three policy bundle/rule contracts published by PR D of the
    # operation-aware schema readiness plan (ADR-0005), in dependency-and-
    # publication order.
    assert basis_schemas.OPERATION_AWARE_POLICY_CONTRACTS == (
        "policy-condition",
        "policy-rule",
        "policy-bundle",
    )


def test_operation_aware_policy_contracts_do_not_extend_first_wave() -> None:
    # PR D is additive and separate: it must not appear in, or change the
    # length of, the first-wave six-contract tuples.
    assert len(basis_schemas.PLANNED_CONTRACTS) == 6
    assert len(basis_schemas.PUBLISHED_CONTRACTS) == 6
    for contract in basis_schemas.OPERATION_AWARE_POLICY_CONTRACTS:
        assert contract not in basis_schemas.PLANNED_CONTRACTS
        assert contract not in basis_schemas.PUBLISHED_CONTRACTS


def test_operation_aware_policy_contracts_disjoint_from_pr_a_pr_b_and_pr_c() -> None:
    # PR D must never be conflated with PR A's shared metadata contracts,
    # PR B's evidence-reference contracts, or PR C's request contract: no
    # name should appear in more than one tracking tuple.
    pr_a = set(basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS)
    pr_b = set(basis_schemas.OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS)
    pr_c = set(basis_schemas.OPERATION_AWARE_REQUEST_CONTRACTS)
    pr_d = set(basis_schemas.OPERATION_AWARE_POLICY_CONTRACTS)
    assert not (pr_a & pr_d), f"contract names appear in both PR A and PR D: {pr_a & pr_d}"
    assert not (pr_b & pr_d), f"contract names appear in both PR B and PR D: {pr_b & pr_d}"
    assert not (pr_c & pr_d), f"contract names appear in both PR C and PR D: {pr_c & pr_d}"


def test_operation_aware_response_trace_contracts_match_pr_e() -> None:
    # The three response/trace contracts published by PR E of the
    # operation-aware schema readiness plan (ADR-0005), in dependency-and-
    # publication order.
    assert basis_schemas.OPERATION_AWARE_RESPONSE_TRACE_CONTRACTS == (
        "trace-rule-evidence",
        "evaluation-trace",
        "operation-aware-decision-response",
    )


def test_operation_aware_response_trace_contracts_do_not_extend_first_wave() -> None:
    # PR E is additive and separate: it must not appear in, or change the
    # length of, the first-wave six-contract tuples.
    assert len(basis_schemas.PLANNED_CONTRACTS) == 6
    assert len(basis_schemas.PUBLISHED_CONTRACTS) == 6
    for contract in basis_schemas.OPERATION_AWARE_RESPONSE_TRACE_CONTRACTS:
        assert contract not in basis_schemas.PLANNED_CONTRACTS
        assert contract not in basis_schemas.PUBLISHED_CONTRACTS


def test_operation_aware_response_trace_contracts_disjoint_from_pr_a_through_pr_d() -> None:
    # PR E must never be conflated with PR A's shared metadata contracts,
    # PR B's evidence-reference contracts, PR C's request contract, or
    # PR D's policy contracts: no name should appear in more than one
    # tracking tuple.
    pr_a = set(basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS)
    pr_b = set(basis_schemas.OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS)
    pr_c = set(basis_schemas.OPERATION_AWARE_REQUEST_CONTRACTS)
    pr_d = set(basis_schemas.OPERATION_AWARE_POLICY_CONTRACTS)
    pr_e = set(basis_schemas.OPERATION_AWARE_RESPONSE_TRACE_CONTRACTS)
    assert not (pr_a & pr_e), f"contract names appear in both PR A and PR E: {pr_a & pr_e}"
    assert not (pr_b & pr_e), f"contract names appear in both PR B and PR E: {pr_b & pr_e}"
    assert not (pr_c & pr_e), f"contract names appear in both PR C and PR E: {pr_c & pr_e}"
    assert not (pr_d & pr_e), f"contract names appear in both PR D and PR E: {pr_d & pr_e}"


def test_operation_aware_audit_contracts_match_pr_f() -> None:
    # The two audit contracts published by PR F of the operation-aware
    # schema readiness plan (ADR-0005), in dependency-and-publication order.
    assert basis_schemas.OPERATION_AWARE_AUDIT_CONTRACTS == (
        "audit-evidence",
        "gateway-audit-event",
    )


def test_operation_aware_audit_contracts_do_not_extend_first_wave() -> None:
    # PR F is additive and separate: it must not appear in, or change the
    # length of, the first-wave six-contract tuples. The existing first-wave
    # audit-event is unaffected.
    assert len(basis_schemas.PLANNED_CONTRACTS) == 6
    assert len(basis_schemas.PUBLISHED_CONTRACTS) == 6
    for contract in basis_schemas.OPERATION_AWARE_AUDIT_CONTRACTS:
        assert contract not in basis_schemas.PLANNED_CONTRACTS
        assert contract not in basis_schemas.PUBLISHED_CONTRACTS


def test_operation_aware_audit_contracts_disjoint_from_pr_a_through_pr_e() -> None:
    # PR F must never be conflated with PR A's shared metadata contracts,
    # PR B's evidence-reference contracts, PR C's request contract, PR D's
    # policy contracts, or PR E's response/trace contracts: no name should
    # appear in more than one tracking tuple.
    pr_a = set(basis_schemas.OPERATION_AWARE_SHARED_METADATA_CONTRACTS)
    pr_b = set(basis_schemas.OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS)
    pr_c = set(basis_schemas.OPERATION_AWARE_REQUEST_CONTRACTS)
    pr_d = set(basis_schemas.OPERATION_AWARE_POLICY_CONTRACTS)
    pr_e = set(basis_schemas.OPERATION_AWARE_RESPONSE_TRACE_CONTRACTS)
    pr_f = set(basis_schemas.OPERATION_AWARE_AUDIT_CONTRACTS)
    assert not (pr_a & pr_f), f"contract names appear in both PR A and PR F: {pr_a & pr_f}"
    assert not (pr_b & pr_f), f"contract names appear in both PR B and PR F: {pr_b & pr_f}"
    assert not (pr_c & pr_f), f"contract names appear in both PR C and PR F: {pr_c & pr_f}"
    assert not (pr_d & pr_f), f"contract names appear in both PR D and PR F: {pr_d & pr_f}"
    assert not (pr_e & pr_f), f"contract names appear in both PR E and PR F: {pr_e & pr_f}"
