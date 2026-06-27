"""Repository metadata for ``basis-schemas``.

During Phase 1 this package carries only repository metadata: the package name,
version, and the ordered list of contracts planned for migration. No contract has
been published yet. The metadata gives the test suite and type checker something
real to run while the schema directories remain placeholders.

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
    "CONTRACT_STATES",
    "is_phase1_foundation",
]

__version__: Final[str] = "0.0.0"

PROJECT_NAME: Final[str] = "basis-schemas"

#: The six contracts planned for the first migration wave, in dependency-and-
#: stability order. See ``docs/migration-plan.md``. These are *planned*; none has
#: been migrated yet.
PLANNED_CONTRACTS: Final[tuple[str, ...]] = (
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
    """Return ``True`` while the repository is a foundation skeleton.

    Phase 1 publishes documentation, tooling, and placeholder directories only;
    no contract has been migrated. This stays ``True`` until the first contract
    is published under ``schemas/``.
    """
    return True
