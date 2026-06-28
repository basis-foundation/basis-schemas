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
    "is_phase1_foundation",
]

__version__: Final[str] = "0.0.0"

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


def is_phase1_foundation() -> bool:
    """Return ``True`` while the repository is a Phase 1 foundation skeleton.

    Phase 1 published documentation, tooling, and placeholder directories only,
    with no migrated contract. That phase is over: the vocabulary contract is
    now published, so this returns ``False``. It is derived from
    ``PUBLISHED_CONTRACTS`` so it stays correct as more contracts migrate.
    """
    return not PUBLISHED_CONTRACTS
