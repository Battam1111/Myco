"""Severity ladder.

Four-level severity taxonomy, strictly ordered. Per
``docs/architecture/L1_CONTRACT/exit_codes.md``:

    CRITICAL (4)  >  HIGH (3)  >  MEDIUM (2)  >  LOW (1)

Severity is a property of each individual finding. The exit code is
computed from the *worst* finding the exit policy considers actionable
(that computation lives in Stage B.2's immune kernel, not here).

This module owns *only* the enum and the ``downgrade`` primitive used
by skeleton-mode downgrade. It is dependency-free.
"""

from __future__ import annotations

from enum import IntEnum

__all__ = ["Severity", "downgrade"]


class Severity(IntEnum):
    """Four-level severity, ordered LOW < MEDIUM < HIGH < CRITICAL."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @classmethod
    def from_name(cls, name: str) -> "Severity":
        """Parse a case-insensitive name; raises ``ValueError`` on miss."""
        try:
            return cls[name.upper()]
        except KeyError as exc:
            raise ValueError(f"unknown severity: {name!r}") from exc

    def label(self) -> str:
        """Stable lowercase label for logging / canon-field storage."""
        return self.name.lower()


def downgrade(sev: Severity, *, ceiling: Severity) -> Severity:
    """Cap ``sev`` at ``ceiling``.

    Used by the skeleton-mode downgrade (``L0``/``L1`` CRITICAL → HIGH
    when ``.myco_state/autoseeded.txt`` is present). A no-op when
    ``sev <= ceiling``.
    """
    return sev if sev <= ceiling else ceiling
