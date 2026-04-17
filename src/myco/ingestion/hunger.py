"""``myco hunger`` — compose substrate hunger report.

Stage B.4 wires two locally-computable signals (contract_drift,
raw_backlog) and leaves ``reflex_signals`` as an empty seam for
Stage B.8's homeostasis dimensions to populate. ``--execute`` patches
the entry-point signals block via ``boot_brief``.

v0.5.3 adds a ``local_plugins`` block — a terse summary of what
substrate-local plugins are loaded so the agent sees extensibility
state on every boot. Governing craft:
``docs/primordia/v0_5_3_fungal_vocabulary_craft_2026-04-17.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from myco.core.context import MycoContext, Result
from myco.surface.manifest import load_manifest, load_manifest_with_overlay

from .boot_brief import patch_entry_point

__all__ = ["HungerReport", "LocalPluginsSummary", "compose_hunger_report", "run"]


@dataclass(frozen=True)
class LocalPluginsSummary:
    """Terse view of the substrate-local plugin surface.

    v0.5.4 added :attr:`count_by_kind` to match the v0.5.3 CHANGELOG
    promise that the payload breaks the count down per registration
    kind. The flat ``count`` is retained for backward compatibility.
    """

    count: int
    errors: tuple[str, ...]
    overlay_verbs: tuple[str, ...]
    #: Per-kind breakdown. Keys: ``"dimension"``, ``"adapter"``,
    #: ``"schema_upgrader"``, ``"overlay_verb"``. Missing keys default
    #: to 0 when any kind is absent. Added at v0.5.4 to align the
    #: hunger payload with the v0.5.3 release-notes promise.
    count_by_kind: Mapping[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return {
            "count": self.count,
            "count_by_kind": dict(self.count_by_kind),
            "errors": list(self.errors),
            "overlay_verbs": list(self.overlay_verbs),
        }


@dataclass(frozen=True)
class HungerReport:
    """A typed view of the hunger state."""

    contract_drift: bool
    raw_backlog: int
    reflex_signals: tuple[str, ...]
    advice: tuple[str, ...]
    local_plugins: LocalPluginsSummary = field(
        default_factory=lambda: LocalPluginsSummary(
            count=0, errors=(), overlay_verbs=()
        )
    )

    def as_dict(self) -> dict[str, object]:
        return {
            "contract_drift": self.contract_drift,
            "raw_backlog": self.raw_backlog,
            "reflex_signals": list(self.reflex_signals),
            "advice": list(self.advice),
            "local_plugins": self.local_plugins.as_dict(),
        }


def _summarize_local_plugins(ctx: MycoContext) -> LocalPluginsSummary:
    """Compute the count/errors/overlay_verbs triple for the hunger report.

    - ``count``: total plugins surfaced by ``graft --list`` equivalent
      logic — dimensions + adapters + schema_upgraders + overlay_verbs.
      Zero when there is no ``.myco/plugins/`` and no overlay.
    - ``errors``: whatever ``Substrate.local_plugin_errors`` captured
      at load time (empty on clean load).
    - ``overlay_verbs``: names of verbs contributed by the overlay.
    """
    errors = tuple(ctx.substrate.local_plugin_errors)

    # Count registered items per kind; mirror graft._collect_plugins
    # without importing that module to avoid a cycle of hunger → graft
    # → ctx. v0.5.4 changed `count` from a bare int to an int +
    # `count_by_kind` dict so the agent sees what's registered without
    # a second verb call.
    by_kind: dict[str, int] = {
        "dimension": 0, "adapter": 0,
        "schema_upgrader": 0, "overlay_verb": 0,
    }
    try:
        from myco.homeostasis.registry import default_registry as _reg

        by_kind["dimension"] = len(_reg().all())
    except Exception:  # noqa: BLE001
        pass
    try:
        from myco.ingestion.adapters import all_adapters

        by_kind["adapter"] = len(list(all_adapters()))
    except Exception:  # noqa: BLE001
        pass
    try:
        from myco.core.canon import schema_upgraders

        by_kind["schema_upgrader"] = len(schema_upgraders)
    except Exception:  # noqa: BLE001
        pass

    overlay_verbs: tuple[str, ...] = ()
    try:
        merged = load_manifest_with_overlay(ctx.substrate.root)
        base_names = {c.name for c in load_manifest().commands}
        overlay_verbs = tuple(
            c.name for c in merged.commands if c.name not in base_names
        )
        by_kind["overlay_verb"] = len(overlay_verbs)
    except Exception as exc:  # noqa: BLE001
        errors = errors + (f"manifest overlay parse failed: {exc}",)

    count = sum(by_kind.values())
    return LocalPluginsSummary(
        count=count,
        errors=errors,
        overlay_verbs=overlay_verbs,
        count_by_kind=dict(by_kind),
    )


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

    local_plugins = _summarize_local_plugins(ctx)
    if local_plugins.errors:
        advice_parts.append(
            "substrate-local plugin errors present; run `myco graft --validate`"
        )

    return HungerReport(
        contract_drift=contract_drift,
        raw_backlog=raw_backlog,
        reflex_signals=reflex_signals,
        advice=tuple(advice_parts),
        local_plugins=local_plugins,
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
