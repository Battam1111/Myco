"""``myco hunger`` — compose substrate hunger report.

Stage B.4 wires two locally-computable signals (contract_drift,
raw_backlog) and leaves ``reflex_signals`` as an empty seam for
Stage B.8's homeostasis dimensions to populate. ``--execute`` patches
the entry-point signals block via ``boot_brief``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from myco.core.context import MycoContext, Result

from .boot_brief import patch_entry_point

__all__ = ["HungerReport", "compose_hunger_report", "run"]


@dataclass(frozen=True)
class HungerReport:
    """A typed view of the hunger state."""

    contract_drift: bool
    raw_backlog: int
    reflex_signals: tuple[str, ...]
    advice: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "contract_drift": self.contract_drift,
            "raw_backlog": self.raw_backlog,
            "reflex_signals": list(self.reflex_signals),
            "advice": list(self.advice),
        }


def compose_hunger_report(ctx: MycoContext) -> HungerReport:
    """Assemble the hunger report from substrate state.

    - ``contract_drift``: True iff canon's ``contract_version`` !=
      ``synced_contract_version`` (when the latter is set).
    - ``raw_backlog``: count of ``notes/raw/*.md`` files.
    - ``reflex_signals``: empty at B.4; populated by B.8 dimensions.
    - ``advice``: human-readable nudges derived from the above.
    """
    canon = ctx.substrate.canon
    synced = canon.synced_contract_version
    contract_drift = bool(synced) and (synced != canon.contract_version)

    raw_dir = ctx.substrate.paths.notes / "raw"
    if raw_dir.is_dir():
        raw_backlog = sum(1 for p in raw_dir.glob("*.md") if p.is_file())
    else:
        raw_backlog = 0

    reflex_signals: tuple[str, ...] = ()  # Stage B.8 fills this in.

    advice_parts: list[str] = []
    if contract_drift:
        advice_parts.append(
            f"contract drifted: canon={canon.contract_version}, "
            f"synced={synced}; run `myco reflect`"
        )
    if raw_backlog > 0:
        advice_parts.append(
            f"raw_backlog={raw_backlog}; consider `myco digest`"
        )
    if not advice_parts:
        advice_parts.append("substrate quiet; no action required")

    return HungerReport(
        contract_drift=contract_drift,
        raw_backlog=raw_backlog,
        reflex_signals=reflex_signals,
        advice=tuple(advice_parts),
    )


def run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """Manifest handler: compose the report and optionally patch entry-point."""
    execute = bool(args.get("execute", False))
    report = compose_hunger_report(ctx)

    entry_point_path: str | None = None
    if execute:
        signals = {
            "contract_drift": report.contract_drift,
            "raw_backlog": report.raw_backlog,
            "advice": "; ".join(report.advice),
        }
        path = patch_entry_point(ctx=ctx, signals=signals)
        entry_point_path = str(path)

    return Result(
        exit_code=0,
        payload={
            "report": report.as_dict(),
            "execute": execute,
            "entry_point_patched": entry_point_path,
        },
    )
