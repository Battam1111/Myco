"""``myco brief`` — the one explicit human-facing verb.

v0.5.5 MAJOR-G. Governing craft:
``docs/primordia/v0_5_5_close_audit_loose_threads_craft_2026-04-17.md``.

L0 principle 1 says humans do not browse Myco: humans speak natural
language, Agents invoke verbs. ``brief`` is the one carved exception
for the "show me what happened" moment — a markdown rollup of the
substrate's current state that a human can skim in 60 seconds. It
does NOT replace any agent-side verb; it summarizes the outputs of
agent-side verbs for a single human reading moment.

Sections (stable order):

1. Identity (substrate_id, contract_version, tags)
2. Hunger (current substrate backlog + reflex signals)
3. Immune (last 10 findings by severity)
4. Notes inventory (raw / integrated / distilled counts)
5. Primordia (most recent 5 craft docs with dates)
6. Local plugins (substrate-local extension inventory)
7. Suggested next (1-3 concrete actions)

Shape is fixed so repeated invocations are comparable; content is
derived from live substrate state (no cache).

No flags besides the global `--project-dir` and `--json`. Markdown is
the only human format; `--json` emits the same structure as a nested
dict for agents that want to pass it through.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from myco.core.context import MycoContext, Result
from myco.core.errors import MycoError
from myco.core.io_atomic import bounded_read_text

__all__ = ["run"]


def _identity_section(ctx: MycoContext) -> dict[str, Any]:
    c = ctx.substrate.canon
    return {
        "substrate_id": c.substrate_id,
        "contract_version": c.contract_version,
        "synced_contract_version": c.synced_contract_version,
        "tags": list(c.tags),
        "entry_point": c.entry_point,
        "root": str(ctx.substrate.root),
    }


def _hunger_section(ctx: MycoContext) -> dict[str, Any]:
    from myco.ingestion.hunger import compose_hunger_report

    report = compose_hunger_report(ctx)
    return report.as_dict()


def _immune_section(ctx: MycoContext) -> dict[str, Any]:
    """Run immune with a permissive exit policy and surface findings.

    Uses ``exit_on="never"`` so running ``brief`` never accidentally
    propagates a CI-gate exit. The finding list is capped at 10 so
    the human summary stays scannable.
    """
    from myco.homeostasis.kernel import run_immune
    from myco.homeostasis.registry import default_registry

    try:
        result = run_immune(ctx, default_registry(), exit_on="never", fix=False)
    except Exception as exc:
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "findings": [],
            "dimensions_run": [],
        }

    findings = []
    for f in result.findings[:10]:
        findings.append(
            {
                "dimension_id": f.dimension_id,
                "severity": f.severity.label(),
                "category": f.category.value,
                "message": f.message,
                "path": f.path,
            }
        )
    return {
        "ok": True,
        "dimensions_run": list(result.payload.get("dimensions_run", ())),
        "finding_count_total": len(result.findings),
        "findings": findings,
    }


def _notes_section(ctx: MycoContext) -> dict[str, Any]:
    root = ctx.substrate.paths.notes
    out = {"raw": 0, "integrated": 0, "distilled": 0}
    if not root.is_dir():
        return out
    for stage in ("raw", "integrated", "distilled"):
        d = root / stage
        if d.is_dir():
            out[stage] = sum(1 for p in d.glob("*.md") if p.is_file())
    return out


def _primordia_section(ctx: MycoContext, *, limit: int = 5) -> list[dict[str, Any]]:
    primordia_dir = ctx.substrate.root / "docs" / "primordia"
    if not primordia_dir.is_dir():
        return []
    entries: list[tuple[str, Path]] = []
    for path in primordia_dir.glob("*.md"):
        if path.is_file():
            entries.append((path.name, path))
    # Sort by filename (craft docs have a date stamp in the filename,
    # so name-sort is date-sort for well-formed crafts).
    entries.sort(key=lambda x: x[0], reverse=True)
    out = []
    for name, path in entries[:limit]:
        try:
            first_heading = ""
            for line in bounded_read_text(path).splitlines():
                if line.startswith("# "):
                    first_heading = line[2:].strip()
                    break
        except (OSError, MycoError):
            first_heading = ""
        out.append(
            {
                "name": name,
                "heading": first_heading,
                "rel": str(path.relative_to(ctx.substrate.root)),
            }
        )
    return out


def _local_plugins_section(ctx: MycoContext) -> dict[str, Any]:
    """Mirror the ``graft --list`` shape but trimmed to per-kind counts."""
    by_kind = {"dimension": 0, "adapter": 0, "schema_upgrader": 0, "overlay_verb": 0}
    errors: list[str] = list(ctx.substrate.local_plugin_errors)
    try:
        from myco.homeostasis.registry import default_registry as _reg

        by_kind["dimension"] = len(_reg().all())
    except Exception:
        pass
    try:
        from myco.ingestion.adapters import all_adapters

        by_kind["adapter"] = len(list(all_adapters()))
    except Exception:
        pass
    try:
        from myco.core.canon import schema_upgraders

        by_kind["schema_upgrader"] = len(schema_upgraders)
    except Exception:
        pass
    try:
        from myco.surface.manifest import (
            load_manifest,
            load_manifest_with_overlay,
        )

        merged = load_manifest_with_overlay(ctx.substrate.root)
        base_names = {c.name for c in load_manifest().commands}
        overlay = [c.name for c in merged.commands if c.name not in base_names]
        by_kind["overlay_verb"] = len(overlay)
    except Exception as exc:
        errors.append(f"manifest overlay parse failed: {exc}")
    return {
        "count": sum(by_kind.values()),
        "count_by_kind": by_kind,
        "errors": errors,
    }


def _suggest_next(
    immune: dict[str, Any],
    hunger: dict[str, Any],
    notes: dict[str, int],
) -> list[str]:
    """Three-or-fewer concrete next actions."""
    suggestions: list[str] = []
    # Highest-severity first.
    findings = immune.get("findings") or []
    critical = [f for f in findings if f.get("severity") == "critical"]
    high = [f for f in findings if f.get("severity") == "high"]
    if critical:
        suggestions.append(
            f"`myco immune --fix` — {len(critical)} critical finding(s) need attention"
        )
    elif high:
        suggestions.append(
            f"`myco immune --fix` — {len(high)} high-severity finding(s) fixable"
        )
    if notes.get("raw", 0) > 0 and notes.get("integrated", 0) == 0:
        suggestions.append(
            f"`myco assimilate` — {notes['raw']} raw note(s) awaiting promotion"
        )
    elif notes.get("raw", 0) > 10:
        suggestions.append(
            f"`myco assimilate` — {notes['raw']} raw notes (>10 threshold)"
        )
    if hunger.get("contract_drift"):
        suggestions.append(
            "`myco assimilate` — contract drift between canon and synced_contract_version"
        )
    if not suggestions:
        suggestions.append(
            "substrate quiet; no action required (next `myco hunger` will confirm)"
        )
    return suggestions[:3]


def _render_markdown(payload: Mapping[str, Any]) -> str:
    """Stable-order markdown rollup for human reading."""
    ident = payload["identity"]
    imm = payload["immune"]
    notes = payload["notes"]
    plugins = payload["local_plugins"]
    primordia = payload["primordia"]
    hunger = payload["hunger"]
    suggestions = payload["suggested_next"]

    lines: list[str] = []
    lines.append(f"# Myco brief — {ident['substrate_id']}")
    lines.append("")
    lines.append(f"*Generated {payload['generated_at']} at `{ident['root']}`.*")
    lines.append("")

    # 1. Identity
    lines.append("## 1. Identity")
    lines.append("")
    lines.append(f"- **substrate_id**: `{ident['substrate_id']}`")
    lines.append(f"- **contract_version**: `{ident['contract_version']}`")
    if ident.get("synced_contract_version"):
        lines.append(
            f"- **synced_contract_version**: `{ident['synced_contract_version']}`"
        )
    if ident.get("tags"):
        lines.append(f"- **tags**: `{', '.join(ident['tags'])}`")
    lines.append(f"- **entry_point**: `{ident['entry_point']}`")
    lines.append("")

    # 2. Hunger
    lines.append("## 2. Hunger")
    lines.append("")
    lines.append(f"- contract_drift: `{hunger.get('contract_drift', False)}`")
    lines.append(f"- raw_backlog: `{hunger.get('raw_backlog', 0)}`")
    if hunger.get("reflex_signals"):
        lines.append(f"- reflex_signals: `{', '.join(hunger['reflex_signals'])}`")
    if hunger.get("advice"):
        for a in hunger["advice"]:
            lines.append(f"- {a}")
    lines.append("")

    # 3. Immune
    lines.append("## 3. Immune")
    lines.append("")
    if imm.get("ok"):
        lines.append(
            f"- {len(imm.get('dimensions_run', []))} dimension(s) run, "
            f"{imm.get('finding_count_total', 0)} finding(s)"
        )
        if imm.get("findings"):
            lines.append("")
            lines.append("| ID | severity | category | message | path |")
            lines.append("|---|---|---|---|---|")
            for f in imm["findings"]:
                msg = (f.get("message") or "").replace("|", "\\|")
                path = f.get("path") or "-"
                lines.append(
                    f"| {f['dimension_id']} | {f['severity']} | "
                    f"{f['category']} | {msg} | {path} |"
                )
    else:
        lines.append(f"- **immune failed**: {imm.get('error', 'unknown error')}")
    lines.append("")

    # 4. Notes inventory
    lines.append("## 4. Notes")
    lines.append("")
    lines.append(
        f"- raw: `{notes['raw']}` | integrated: `{notes['integrated']}` | "
        f"distilled: `{notes['distilled']}`"
    )
    lines.append("")

    # 5. Primordia
    lines.append("## 5. Recent primordia")
    lines.append("")
    if primordia:
        for p in primordia:
            heading = p.get("heading") or p["name"]
            lines.append(f"- [`{p['name']}`]({p['rel']}) — {heading}")
    else:
        lines.append("- (none)")
    lines.append("")

    # 6. Local plugins
    lines.append("## 6. Local plugins")
    lines.append("")
    lines.append(f"- total: `{plugins['count']}`")
    for kind, n in plugins["count_by_kind"].items():
        lines.append(f"- {kind}: `{n}`")
    if plugins["errors"]:
        lines.append("")
        lines.append("**errors:**")
        for e in plugins["errors"]:
            lines.append(f"- {e}")
    lines.append("")

    # 7. Suggested next
    lines.append("## 7. Suggested next")
    lines.append("")
    for s in suggestions:
        lines.append(f"- {s}")
    lines.append("")

    return "\n".join(lines)


def run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """brief handler. Produces a stable-section markdown rollup
    of the substrate's current state for a single human reading
    moment. L0 principle 1's single carved exception — brief is
    the one verb specifically intended for a human audience."""
    del args  # no per-call flags; everything comes from ctx
    generated_at = datetime.now(timezone.utc).isoformat()

    payload: dict[str, Any] = {
        "generated_at": generated_at,
        "identity": _identity_section(ctx),
        "hunger": _hunger_section(ctx),
        "immune": _immune_section(ctx),
        "notes": _notes_section(ctx),
        "primordia": _primordia_section(ctx),
        "local_plugins": _local_plugins_section(ctx),
    }
    payload["suggested_next"] = _suggest_next(
        payload["immune"], payload["hunger"], payload["notes"]
    )
    payload["markdown"] = _render_markdown(payload)
    return Result(exit_code=0, payload=payload)
