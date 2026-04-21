"""Exception hierarchy for Myco.

Per ``docs/architecture/L1_CONTRACT/exit_codes.md``, exit codes ``0``,
``1``, and ``2`` are reserved for finding-driven results (computed by
the exit-policy layer in Stage B.2). Codes ``≥3`` are operational
failures and are *raised* as exceptions.

Every exception in this hierarchy carries an ``exit_code`` class
attribute (always ``≥3``). The surface layer (B.7) maps uncaught
exceptions to ``sys.exit(exc.exit_code)``.

v0.5.8 (Lens 5 P1-08): the ``≥3`` codes are now **differentiated**
so CI scripts and downstream consumers can distinguish classes of
operational failure without string-matching stderr:

- ``3`` — generic operational failure / usage error
- ``4`` — substrate not found (start dir has no ``_canon.yaml``)
- ``5`` — canon schema validation failure

Still within the contract (all ≥3); no contract bump required.
Legacy callers that only check ``exit != 0`` continue to work;
callers that special-case ``== 3`` for substrate/canon failures
now get a more precise signal.
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
    required canon field, malformed ``--exit-on`` spec. Stays at
    ``3`` — contract-protocol failures are indistinguishable at the
    kernel level from generic operational failures (both say "the
    author's expectation diverged from the substrate's state").
    """

    exit_code: int = 3


class CanonSchemaError(ContractError):
    """``_canon.yaml`` failed to parse or validate against the L1 schema.

    v0.5.8: promoted from ``3`` to ``5``. Canon drift is
    distinguishable from generic contract failure and CI scripts
    want to handle it specifically (e.g. auto-regenerate canon on a
    fresh branch but hard-fail on other contract errors).
    """

    exit_code: int = 5


class SubstrateNotFound(MycoError):
    """Walk-up from the given start directory found no valid substrate.

    v0.5.8: promoted from ``3`` to ``4``. Indistinguishable from
    generic operational failure at the raise site; distinguishable
    at the exit-code site is the whole point of this change.
    """

    exit_code: int = 4


class UsageError(MycoError):
    """Bad CLI invocation (unknown verb, missing required arg, bad flag).

    Stays at ``3``. Argparse's own errors already exit ``2`` (which
    technically collides with the finding CRITICAL slot, but is
    baked into argparse and outside our reach). Our ``UsageError``
    raises — distinct from argparse's parse-time exit — and stays
    at the generic ``3`` ladder.
    """

    exit_code: int = 3
