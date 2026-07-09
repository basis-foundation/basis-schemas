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

This package does **not** define, validate, or implement any contract. Contracts
are decided in ``basis-architecture`` and published, once migrated, under the
``schemas/`` directory.
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
    "is_phase1_foundation",
]

__version__: Final[str] = "0.1.0"

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


def is_phase1_foundation() -> bool:
    """Return ``True`` while the repository is a Phase 1 foundation skeleton.

    Phase 1 published documentation, tooling, and placeholder directories only,
    with no migrated contract. That phase is over: the vocabulary contract is
    now published, so this returns ``False``. It is derived from
    ``PUBLISHED_CONTRACTS`` so it stays correct as more contracts migrate.
    """
    return not PUBLISHED_CONTRACTS
