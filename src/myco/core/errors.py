"""Exception hierarchy for Myco.

Per ``docs/architecture/L1_CONTRACT/exit_codes.md``, exit codes ``0``,
``1``, and ``2`` are reserved for finding-driven results (computed by
the exit-policy layer in Stage B.2). Codes ``≥3`` are operational
failures and are *raised* as exceptions.

Every exception in this hierarchy carries an ``exit_code`` class
attribute (always ``≥3``). The surface layer (B.7) maps uncaught
exceptions to ``sys.exit(exc.exit_code)``.
"""

from __future__ import annotations

__all__ = [
    "MycoError",
    "ContractError",
    "CanonSchemaError",
    "SubstrateNotFound",
    "UsageError",
]


class MycoError(Exception):
    """Root of the Myco exception hierarchy.

    Default ``exit_code`` is ``3`` (generic operational failure).
    Subclasses may override but must stay at ``≥3`` so they never
    collide with finding-driven exit codes (0/1/2).
    """

    exit_code: int = 3


class ContractError(MycoError):
    """A hard-contract invariant was violated.

    Examples: unknown ``schema_version`` in ``_canon.yaml``, missing
    required canon field, malformed ``--exit-on`` spec. Always ``3``
    regardless of severity — these are not lint findings.
    """

    exit_code: int = 3


class CanonSchemaError(ContractError):
    """``_canon.yaml`` failed to parse or validate against the L1 schema."""

    exit_code: int = 3


class SubstrateNotFound(MycoError):
    """Walk-up from the given start directory found no valid substrate."""

    exit_code: int = 3


class UsageError(MycoError):
    """Bad CLI invocation (unknown verb, missing required arg, bad flag)."""

    exit_code: int = 3
