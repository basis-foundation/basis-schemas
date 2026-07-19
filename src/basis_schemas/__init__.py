"""Repository metadata for ``basis-schemas``.

This package carries repository metadata: the package name, version, the ordered
list of contracts planned for migration, and which of them have been published.
All six contracts of the first planned wave — the action **vocabulary**, the
**action string**, the **resource identifier**, the **decision request**, the
**decision response**, and the **audit event** — are now published under
``schemas/``. That is every *currently planned* contract; it is not a claim that
the contract set is closed forever — future contracts may still be added through
``basis-architecture`` governance. The metadata gives the test suite and type
checker something real to run.

A second, separate wave has since begun: the shared metadata and vocabulary
contracts from ``basis-architecture``'s operation-aware schema readiness plan
(ADR-0005) — ``contract-metadata``, ``redaction-classification``, and
``reason-code``. These are tracked in ``OPERATION_AWARE_SHARED_METADATA_CONTRACTS``
below, deliberately kept separate from ``PLANNED_CONTRACTS`` /
``PUBLISHED_CONTRACTS``, which continue to track only the original six-contract
first wave. See ``docs/operation-aware-schema-readiness.md``.

PR B of that same second wave has since published the evidence-reference
contracts — ``identity-evidence-reference`` and ``adapter-evidence-reference``
— tracked separately again, in
``OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS`` below, for the same reason:
they are additive publications, not an extension of the first-wave six-contract
count.

PR C of that same second wave has since published the operation-aware
decision request — ``operation-aware-decision-request`` — tracked separately
again, in ``OPERATION_AWARE_REQUEST_CONTRACTS`` below, for the same reason:
it is an additive publication alongside the unchanged first-wave
``decision-request``, not a replacement for it.

PR D of that same second wave has since published the policy bundle and rule
contracts — ``policy-condition``, ``policy-rule``, and ``policy-bundle``, in
dependency order — tracked separately again, in
``OPERATION_AWARE_POLICY_CONTRACTS`` below, for the same reason: they are
additive publications, not an extension of the first-wave six-contract count,
of PR A's shared metadata contracts, of PR B's evidence-reference contracts,
or of PR C's request contract.

PR E of that same second wave has since published the response and trace
contracts — ``trace-rule-evidence``, ``evaluation-trace``, and
``operation-aware-decision-response``, in dependency order — tracked
separately again, in ``OPERATION_AWARE_RESPONSE_TRACE_CONTRACTS`` below,
for the same reason: they are additive publications, not an extension of
the first-wave six-contract count, of PR A's shared metadata contracts, of
PR B's evidence-reference contracts, of PR C's request contract, or of
PR D's policy contracts.

PR F of that same second wave has since published the audit contracts —
``audit-evidence`` and ``gateway-audit-event``, in dependency order —
tracked separately again, in ``OPERATION_AWARE_AUDIT_CONTRACTS`` below,
for the same reason: they are additive publications, not an extension of
the first-wave six-contract count (the existing first-wave ``audit-event``
is unchanged), of PR A's shared metadata contracts, of PR B's evidence-
reference contracts, of PR C's request contract, of PR D's policy
contracts, or of PR E's response/trace contracts.

PR G, the seventh and final PR of that same second wave, has since
published canonical, cross-contract compatibility examples and test
vectors under ``examples/operation-aware/compatibility/``, connecting PR A
through PR F into five complete operation-aware authorization scenarios.
It publishes no new schema contract and adds no new tracking tuple here —
every contract it exercises was already published by an earlier PR. With
PR G published, the operation-aware second wave described above is
complete. See ``docs/operation-aware-compatibility-vectors.md``.

This package does **not** define, validate, or implement any contract. Contracts
are decided in ``basis-architecture`` and published, once migrated, under the
``schemas/`` directory. This package also does **not** carry the contract
files themselves onto a consumer's disk: the built wheel packages only this
``src/basis_schemas`` metadata module, not ``schemas/``, ``docs/``, or
``examples/``. See "How to consume contracts" in ``README.md``.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "__version__",
    "PROJECT_NAME",
    "PLANNED_CONTRACTS",
    "PUBLISHED_CONTRACTS",
    "CONTRACT_STATES",
    "OPERATION_AWARE_SHARED_METADATA_CONTRACTS",
    "OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS",
    "OPERATION_AWARE_REQUEST_CONTRACTS",
    "OPERATION_AWARE_POLICY_CONTRACTS",
    "OPERATION_AWARE_RESPONSE_TRACE_CONTRACTS",
    "OPERATION_AWARE_AUDIT_CONTRACTS",
    "is_phase1_foundation",
]

__version__: Final[str] = "0.2.1"

PROJECT_NAME: Final[str] = "basis-schemas"

#: The six contracts planned for the first migration wave, in dependency-and-
#: stability order. See ``docs/migration-plan.md``. All six are now published
#: (see ``PUBLISHED_CONTRACTS``). Future contracts may still be added later
#: through ``basis-architecture`` governance.
PLANNED_CONTRACTS: Final[tuple[str, ...]] = (
    "vocabulary",
    "action-string",
    "resource-identifier",
    "decision-request",
    "decision-response",
    "audit-event",
)

#: Contracts that have actually been published under ``schemas/`` (a real
#: machine-readable definition, not a placeholder). Vocabulary was first,
#: action-string second, resource-identifier third, decision-request fourth,
#: decision-response fifth, audit-event sixth. With audit-event published, every
#: contract in ``PLANNED_CONTRACTS`` is now published — no placeholders remain.
PUBLISHED_CONTRACTS: Final[tuple[str, ...]] = (
    "vocabulary",
    "action-string",
    "resource-identifier",
    "decision-request",
    "decision-response",
    "audit-event",
)

#: The lifecycle states a published contract may carry, lowest to highest
#: commitment. See ``docs/contract-governance.md``.
CONTRACT_STATES: Final[tuple[str, ...]] = (
    "experimental",
    "candidate",
    "stable",
)

#: Shared metadata/vocabulary contracts published by PR A of the
#: operation-aware schema readiness plan (``basis-architecture`` ADR-0005,
#: "PR A — Shared Metadata and Vocabulary"). These are foundational building
#: blocks for later operation-aware contracts (PR B onward); they are a
#: second, separate wave and do not extend ``PLANNED_CONTRACTS`` /
#: ``PUBLISHED_CONTRACTS`` above, which track only the original six-contract
#: migration wave from ``docs/migration-plan.md``. See
#: ``docs/operation-aware-schema-readiness.md``.
OPERATION_AWARE_SHARED_METADATA_CONTRACTS: Final[tuple[str, ...]] = (
    "contract-metadata",
    "redaction-classification",
    "reason-code",
)

#: Evidence-reference contracts published by PR B of the operation-aware
#: schema readiness plan (``basis-architecture`` ADR-0005, "PR B — Evidence
#: Reference Contracts"). These let future operation-aware request, trace,
#: audit, and explanation contracts reference trusted identity evidence and
#: normalized adapter evidence without embedding raw tokens, claims,
#: credentials, or protocol payloads. Like
#: ``OPERATION_AWARE_SHARED_METADATA_CONTRACTS`` above, this is a separate,
#: additive tracking tuple: it does not extend ``PLANNED_CONTRACTS`` /
#: ``PUBLISHED_CONTRACTS``, which continue to track only the original
#: six-contract first wave. See ``docs/operation-aware-schema-readiness.md``.
OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS: Final[tuple[str, ...]] = (
    "identity-evidence-reference",
    "adapter-evidence-reference",
)

#: The operation-aware decision request contract published by PR C of the
#: operation-aware schema readiness plan (``basis-architecture`` ADR-0005,
#: "PR C — Operation-Aware DecisionRequest"). This is the richer, additive
#: vNext request shape a future ``basis-core`` v0.2.0 evaluates; it does not
#: replace or modify the existing first-wave ``decision-request`` in
#: ``PLANNED_CONTRACTS`` / ``PUBLISHED_CONTRACTS``. Like
#: ``OPERATION_AWARE_SHARED_METADATA_CONTRACTS`` and
#: ``OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS`` above, this is a
#: separate, additive tracking tuple. See
#: ``docs/operation-aware-schema-readiness.md``.
OPERATION_AWARE_REQUEST_CONTRACTS: Final[tuple[str, ...]] = ("operation-aware-decision-request",)

#: The policy bundle and rule contracts published by PR D of the
#: operation-aware schema readiness plan (``basis-architecture`` ADR-0005,
#: "PR D — Policy Bundle and Rule Contracts"), in dependency-and-publication
#: order: the deterministic, data-only condition shape; the rule shape that
#: composes conditions with match criteria and an allow/deny effect; and the
#: bundle shape that groups rules under a versioned, scoped, owned identity.
#: Like ``OPERATION_AWARE_SHARED_METADATA_CONTRACTS``,
#: ``OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS``, and
#: ``OPERATION_AWARE_REQUEST_CONTRACTS`` above, this is a separate, additive
#: tracking tuple: it does not extend ``PLANNED_CONTRACTS`` /
#: ``PUBLISHED_CONTRACTS``, which continue to track only the original
#: six-contract first wave. See ``docs/operation-aware-schema-readiness.md``.
OPERATION_AWARE_POLICY_CONTRACTS: Final[tuple[str, ...]] = (
    "policy-condition",
    "policy-rule",
    "policy-bundle",
)

#: The response and trace contracts published by PR E of the operation-aware
#: schema readiness plan (``basis-architecture`` ADR-0005, "PR E —
#: DecisionResponse and EvaluationTrace"), in dependency-and-publication
#: order: the bounded per-rule trace-evidence shape; the deterministic,
#: bounded evaluation-trace shape that collects it; and the additive vNext
#: response shape that echoes the operation-aware request and optionally
#: references or embeds the trace. Like
#: ``OPERATION_AWARE_SHARED_METADATA_CONTRACTS``,
#: ``OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS``,
#: ``OPERATION_AWARE_REQUEST_CONTRACTS``, and
#: ``OPERATION_AWARE_POLICY_CONTRACTS`` above, this is a separate, additive
#: tracking tuple: it does not extend ``PLANNED_CONTRACTS`` /
#: ``PUBLISHED_CONTRACTS``, which continue to track only the original
#: six-contract first wave. The existing first-wave ``decision-response`` is
#: unchanged and is not part of this tuple. See
#: ``docs/operation-aware-schema-readiness.md``.
OPERATION_AWARE_RESPONSE_TRACE_CONTRACTS: Final[tuple[str, ...]] = (
    "trace-rule-evidence",
    "evaluation-trace",
    "operation-aware-decision-response",
)

#: The audit contracts published by PR F of the operation-aware schema
#: readiness plan (``basis-architecture`` ADR-0005, "PR F — Audit Evidence
#: and GatewayAuditEvent"), in dependency-and-publication order: the
#: bounded, durable kernel-side audit-evidence shape produced by
#: ``basis-core`` as part of its response; and the gateway-emitted
#: enforcement-boundary event shape that references that evidence by
#: ``audit_evidence_id`` rather than embedding it. Like
#: ``OPERATION_AWARE_SHARED_METADATA_CONTRACTS``,
#: ``OPERATION_AWARE_EVIDENCE_REFERENCE_CONTRACTS``,
#: ``OPERATION_AWARE_REQUEST_CONTRACTS``,
#: ``OPERATION_AWARE_POLICY_CONTRACTS``, and
#: ``OPERATION_AWARE_RESPONSE_TRACE_CONTRACTS`` above, this is a separate,
#: additive tracking tuple: it does not extend ``PLANNED_CONTRACTS`` /
#: ``PUBLISHED_CONTRACTS``, which continue to track only the original
#: six-contract first wave. The existing first-wave ``audit-event`` is
#: unchanged and is not part of this tuple. See
#: ``docs/operation-aware-schema-readiness.md``.
OPERATION_AWARE_AUDIT_CONTRACTS: Final[tuple[str, ...]] = (
    "audit-evidence",
    "gateway-audit-event",
)


def is_phase1_foundation() -> bool:
    """Return ``True`` while the repository is a Phase 1 foundation skeleton.

    Phase 1 published documentation, tooling, and placeholder directories only,
    with no migrated contract. That phase is over: the vocabulary contract is
    now published, so this returns ``False``. It is derived from
    ``PUBLISHED_CONTRACTS`` so it stays correct as more contracts migrate.
    """
    return not PUBLISHED_CONTRACTS
