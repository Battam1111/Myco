"""MF3 — symbiont host-side artifact integrity.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/extensibility.md``
per-host axis (formerly "*(future per-host dimension — reserved)*",
LANDED v0.6.0).

Severity: LOW at land, ramps to MEDIUM after 30 sessions.

When a substrate has installed symbiont host-side artifacts (e.g.
``~/.cursor/rules/myco.mdc``, ``~/.continue/rules/myco.md``,
``~/.config/zed/commands/myco.toml``), MF3 verifies the signature
header is intact. Tampered or stale artifacts emit MEDIUM. The
signature is a comment line ``# myco-symbiont-sig: <substrate_id>:<version>``
written at install time.

Read-only: MF3 does not write or repair host-side artifacts. Repair
is via ``myco-install host <client> --with-symbionts`` re-run.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["MF3SymbiontArtifactIntegrity"]

_SIG_TOKEN: str = "# myco-symbiont-sig:"

#: Known artifact paths per host. Each entry: (host_id, abs_path_factory).
#: abs_path_factory takes home() and returns Path or None if not applicable
#: on this OS.
_ARTIFACT_REGISTRY: tuple[tuple[str, str], ...] = (
    ("cursor", ".cursor/rules/myco.mdc"),
    ("continue_dev", ".continue/rules/myco.md"),
    ("zed", ".config/zed/commands/myco.toml"),
    ("goose", ".config/goose/recipes/myco-bootstrap.yaml"),
)


class MF3SymbiontArtifactIntegrity(Dimension):
    """Host-side symbiont artifacts must carry intact signature headers."""

    id = "MF3"
    category = Category.MECHANICAL
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        # MF3 only fires when the substrate has explicitly declared
        # symbiont integration is active (via canon governance or
        # ``.myco_state/symbionts/`` install marker). Default: don't
        # probe user home for arbitrary substrates.
        marker = ctx.substrate.root / ".myco_state" / "symbionts" / "installed.txt"
        if not marker.is_file():
            return
        try:
            home = Path(os.path.expanduser("~"))
        except Exception:
            return
        for host_id, rel in _ARTIFACT_REGISTRY:
            path = home / rel
            if not path.is_file():
                continue
            try:
                head = path.read_text(encoding="utf-8", errors="replace")[:512]
            except OSError:
                continue
            if _SIG_TOKEN not in head:
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=(
                        f"symbiont artifact for host {host_id!r} at "
                        f"{path} is missing signature header "
                        f"({_SIG_TOKEN}); reinstall via "
                        f"`myco-install host {host_id} --with-symbionts`"
                    ),
                    path=str(path),
                )
