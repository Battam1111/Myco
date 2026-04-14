"""Handler context and result types.

Per ``docs/architecture/L3_IMPLEMENTATION/command_manifest.md``, every
command handler has signature::

    def run(args: dict, *, ctx: MycoContext) -> Result

``MycoContext`` is constructed by the surface layer (Stage B.7) from
the real process environment. Tests use ``MycoContext.for_testing``
to build a minimal context from a loaded substrate.

``Result`` is the handler's return shape. In Stage B.1, ``findings``
is typed as ``tuple[Any, ...]`` — it will be tightened to
``tuple[Finding, ...]`` when Stage B.2 lands the ``Finding`` class.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, TextIO
import sys

from .substrate import Substrate

__all__ = ["MycoContext", "Result"]


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
    ) -> "MycoContext":
        """Construct a ``MycoContext`` for tests.

        Either ``root`` (load the substrate at that path) or
        ``substrate`` (pre-loaded) must be supplied. Everything else
        defaults to sensible real values.
        """
        if substrate is None:
            if root is None:
                raise ValueError("for_testing requires root= or substrate=")
            substrate = Substrate.load(root)
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
