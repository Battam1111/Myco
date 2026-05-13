"""Cluster module — v0.8.8 max-aggressive merge of context, errors, severity, version.

=== context ===
Handler context and result types.

Per ``docs/architecture/L3_IMPLEMENTATION/command_manifest.md``, every
command handler has signature::

    def run(args: dict, *, ctx: MycoContext) -> Result

``MycoContext`` is constructed by the surface layer (Stage B.7) from
the real process environment. Tests use ``MycoContext.for_testing``
to build a minimal context from a loaded substrate.

``Result`` is the handler's return shape. In Stage B.1, ``findings``
is typed as ``tuple[Any, ...]`` — it will be tightened to
``tuple[Finding, ...]`` when Stage B.2 lands the ``Finding`` class.

=== errors ===
Exception hierarchy for Myco.

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

=== severity ===
Severity ladder.

Four-level severity taxonomy, strictly ordered. Per
``docs/architecture/L1_CONTRACT/exit_codes.md``:

    CRITICAL (4)  >  HIGH (3)  >  MEDIUM (2)  >  LOW (1)

Severity is a property of each individual finding. The exit code is
computed from the *worst* finding the exit policy considers actionable
(that computation lives in Stage B.2's immune kernel, not here).

This module owns *only* the enum and the ``downgrade`` primitive used
by skeleton-mode downgrade. It is dependency-free.

=== version ===
Version primitives.

Governing doctrine: ``docs/architecture/L1_CONTRACT/versioning.md``
(contract version grammar + package version sync rules; consumed
by :class:`SH1PackageVersionRef`).

Two grammars are supported — one for package versions (PEP 440 subset)
and one for contract versions (``vMAJOR.MINOR.PATCH[-<tag>]``). Both
are deliberately minimal re-implementations rather than delegating to
``packaging`` — we only need internal ordering and equality, not
parity with PyPI's version grammar. Widening either grammar is a
contract change that gets its own craft.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, TextIO

if TYPE_CHECKING:
    from .substrate_cluster import Substrate
import re
from enum import IntEnum
from typing import ClassVar

# =========================================================================
# === context — formerly context.py
# =========================================================================


@dataclass(frozen=True)
class MycoContext:
    """What a handler sees when it runs.

    Frozen; handlers treat it as read-only. Mutability (e.g. writing
    notes) happens through subsystem services that accept ``ctx`` and
    perform their own side effects.
    """

    substrate: Substrate
    now: datetime
    env: Mapping[str, str]
    stdout: TextIO
    stderr: TextIO

    @classmethod
    def for_testing(
        cls,
        root: Path | None = None,
        *,
        substrate: Substrate | None = None,
        now: datetime | None = None,
        env: Mapping[str, str] | None = None,
        stdout: TextIO | None = None,
        stderr: TextIO | None = None,
    ) -> MycoContext:
        """Construct a ``MycoContext`` for tests.

        Either ``root`` (load the substrate at that path) or
        ``substrate`` (pre-loaded) must be supplied. Everything else
        defaults to sensible real values.
        """
        if substrate is None:
            if root is None:
                raise ValueError("for_testing requires root= or substrate=")
            from .substrate_cluster import Substrate as _Substrate

            substrate = _Substrate.load(root)
        return cls(
            substrate=substrate,
            now=now or datetime.now(timezone.utc),
            env=dict(env) if env is not None else dict(os.environ),
            stdout=stdout or sys.stdout,
            stderr=stderr or sys.stderr,
        )


@dataclass(frozen=True)
class Result:
    """What a handler returns.

    ``exit_code`` is the finding-driven exit (0/1/2); operational
    failures raise ``MycoError`` instead of being stuffed here.
    ``findings`` carries lint findings (typed as ``Any`` in Stage B.1
    and tightened in B.2). ``payload`` is free-form structured output
    that the surface layer may render as JSON.
    """

    exit_code: int = 0
    findings: tuple[Any, ...] = ()
    payload: Mapping[str, Any] = field(default_factory=dict)


# =========================================================================
# === errors — formerly errors.py
# =========================================================================


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


# =========================================================================
# === severity — formerly severity.py
# =========================================================================


class Severity(IntEnum):
    """Four-level severity, ordered LOW < MEDIUM < HIGH < CRITICAL."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @classmethod
    def from_name(cls, name: str) -> Severity:
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
    when ``.myco/state/autoseeded.txt`` is present). A no-op when
    ``sev <= ceiling``.
    """
    return sev if sev <= ceiling else ceiling


# =========================================================================
# === version — formerly version.py
# =========================================================================

_PACKAGE_RE = re.compile(
    "^(?P<major>\\d+)\\.(?P<minor>\\d+)\\.(?P<patch>\\d+)(?:\\.dev(?P<dev>\\d*))?$"
)

_CONTRACT_RE = re.compile(
    "^v?(?P<major>\\d+)\\.(?P<minor>\\d+)\\.(?P<patch>\\d+)(?:-(?P<tag>[A-Za-z0-9._-]+))?$"
)


@dataclass(frozen=True, order=True)
class PackageVersion:
    """PEP 440 subset: ``MAJOR.MINOR.PATCH`` optionally with ``.devN``.

    Ordering: ``0.4.0.dev < 0.4.0 < 0.4.1``. Within the ``.dev`` track,
    ``.dev`` (no number) sorts *before* ``.dev0``, which sorts before
    ``.dev1``, etc.
    """

    major: int
    minor: int
    patch: int
    _release_kind: int
    _dev_num: int
    _GRAMMAR: ClassVar[str] = "MAJOR.MINOR.PATCH[.devN]"

    @classmethod
    def parse(cls, text: str) -> PackageVersion:
        """Parse ``text`` (``MAJOR.MINOR.PATCH[.devN]``) into a ``PackageVersion``.

        Raises ``ValueError`` on shape mismatch. Accepts ``.dev``
        (anonymous dev) as well as ``.dev<int>`` (numbered).
        """
        m = _PACKAGE_RE.match(text)
        if not m:
            raise ValueError(f"not a valid package version ({cls._GRAMMAR}): {text!r}")
        dev = m.group("dev")
        if dev is None:
            kind, num = (1, 0)
        else:
            kind, num = (0, int(dev) if dev else -1)
        return cls(int(m["major"]), int(m["minor"]), int(m["patch"]), kind, num)

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self._release_kind == 1:
            return base
        return f"{base}.dev" if self._dev_num == -1 else f"{base}.dev{self._dev_num}"


@dataclass(frozen=True, order=True)
class ContractVersion:
    """``vMAJOR.MINOR.PATCH[-<tag>]``.

    The leading ``v`` is optional on read and normalized away; ``__str__``
    re-adds it. The pre-release tag is compared lexicographically; this
    happens to work for ``alpha.1 < alpha.2 < beta.1`` and we accept the
    narrow scope (widen via craft if we ever outgrow it).
    """

    major: int
    minor: int
    patch: int
    _has_final: int
    _tag: str
    _GRAMMAR: ClassVar[str] = "vMAJOR.MINOR.PATCH[-<tag>]"

    @classmethod
    def parse(cls, text: str) -> ContractVersion:
        """Parse ``text`` (``vMAJOR.MINOR.PATCH[-<tag>]``) into a ``ContractVersion``.

        Leading ``v`` is optional on read and dropped in storage;
        ``__str__`` re-adds it. Raises ``ValueError`` on shape
        mismatch.
        """
        m = _CONTRACT_RE.match(text)
        if not m:
            raise ValueError(f"not a valid contract version ({cls._GRAMMAR}): {text!r}")
        tag = m["tag"] or ""
        return cls(
            int(m["major"]), int(m["minor"]), int(m["patch"]), 0 if tag else 1, tag
        )

    def __str__(self) -> str:
        base = f"v{self.major}.{self.minor}.{self.patch}"
        return f"{base}-{self._tag}" if self._tag else base
