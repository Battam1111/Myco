"""``myco sporulate <slug>`` (alias ``distill``) — bundle integrated
notes into a proposal skeleton.

v0.5.5 (MAJOR-C) writes the doctrine boundary explicitly: sporulate
**prepares material**; the Agent **writes synthesis**. That is:

- sporulate SELECTS the contributing integrated notes (by ``--sources``
  or auto-discovers them by shared tags).
- sporulate EXTRACTS the shared-tag theme + first-line claims.
- sporulate WRITES ``notes/distilled/d_<slug>.md`` with the selected
  sources, the extracted theme, a first-line-per-note seed list, and
  a TODO for the Agent to replace with real synthesis prose.

sporulate does **NOT** call an LLM or any external synthesis model.
Per L0 principle 1, the Agent calls its own model and writes the
synthesis back into the proposal file. The substrate stays provider-
agnostic (works with any Agent on any Claude/GPT/local model) and
the "Agent calls LLM, substrate does not" invariant stays intact.

Does **not** touch canon or ``docs/architecture/``. Promoting the
proposal into real doctrine is a follow-up ``fruit`` (craft) + ``molt``
(contract bump) pair, done by the Agent.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/digestion.md``
§"Digestion does not" — sporulate boundary added at v0.5.5.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path

from myco.core.context import MycoContext, Result
from myco.core.errors import ContractError, UsageError

from .pipeline import Note, parse_note, render_note

__all__ = ["distill_proposal", "run"]


_SLUG_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")


def _integrated_notes(ctx: MycoContext) -> list[Path]:
    d = ctx.substrate.paths.notes / "integrated"
    if not d.is_dir():
        return []
    return sorted(p for p in d.glob("n_*.md") if p.is_file())


def _summary_line(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return path.name
    note = parse_note(text)
    first = (note.body.splitlines() or [""])[0].strip()
    return first or path.name


def distill_proposal(
    *,
    ctx: MycoContext,
    slug: str,
    sources: Sequence[str] | None = None,
    now: datetime | None = None,
) -> Path:
    """Create ``notes/distilled/d_<slug>.md`` with a proposal body.

    When ``sources`` is None, all integrated notes are treated as
    sources. When explicit, only those substrate-relative paths are
    used (each must exist).
    """
    if not _SLUG_RE.match(slug):
        raise UsageError(
            f"invalid distill slug {slug!r}: must match [a-z][a-z0-9_-]{{0,63}}"
        )

    distilled_dir = ctx.substrate.paths.notes / "distilled"
    target = distilled_dir / f"d_{slug}.md"
    if target.exists():
        raise ContractError(f"distilled proposal already exists: {target}")

    if sources is None:
        source_paths = _integrated_notes(ctx)
    else:
        source_paths = []
        for rel in sources:
            p = (ctx.substrate.root / rel).resolve()
            try:
                p.relative_to(ctx.substrate.root.resolve())
            except ValueError as exc:
                raise ContractError(f"distill source escapes substrate: {rel}") from exc
            if not p.is_file():
                raise ContractError(f"distill source missing: {rel}")
            source_paths.append(p)

    if not source_paths:
        raise ContractError(
            "no integrated notes found to sporulate from; "
            "run `myco assimilate` first or pass explicit --source"
        )

    now = now or datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    root = ctx.substrate.root.resolve()
    rel_sources = [
        str(p.resolve().relative_to(root)).replace("\\", "/") for p in source_paths
    ]

    # Derive shared tags and a theme sentence from sources
    all_tags: dict[str, int] = {}
    summaries: list[str] = []
    for path in source_paths:
        note = parse_note(path.read_text(encoding="utf-8"))
        for tag in note.frontmatter.get("tags", []):
            all_tags[tag] = all_tags.get(tag, 0) + 1
        first = (note.body.splitlines() or [""])[0].strip()
        if first:
            summaries.append(first)

    top_tags = sorted(all_tags, key=lambda t: -all_tags[t])[:5]
    theme_line = (
        f"Theme: {', '.join(top_tags)}" if top_tags else "Theme: (no shared tags)"
    )

    body_lines = [
        f"# Distillation proposal: {slug}",
        "",
        theme_line,
        f"Sources: {len(source_paths)} integrated notes",
        "",
        "## Source summaries",
        "",
    ]
    for path, rel in zip(source_paths, rel_sources, strict=False):
        body_lines.append(f"- `{rel}` — {_summary_line(path)}")
    body_lines.append("")
    if summaries:
        body_lines.append("## Synthesis seed")
        body_lines.append("")
        body_lines.append(
            "The following first-line claims from the sources suggest "
            "the doctrine page should address:"
        )
        body_lines.append("")
        for s in summaries[:10]:
            body_lines.append(f"- {s}")
        body_lines.append("")
    body_lines.append(
        "Promote to L2 doctrine via craft (see `docs/architecture/L2_DOCTRINE/`)."
    )
    body = "\n".join(body_lines) + "\n"

    note = Note(
        frontmatter={
            "proposed_doctrine": slug,
            "sources": rel_sources,
            "distilled_at": stamp,
            "stage": "distilled",
        },
        body=body,
    )
    distilled_dir.mkdir(parents=True, exist_ok=True)
    target.write_text(render_note(note), encoding="utf-8")
    return target


def run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    slug = str(args.get("slug") or "")
    if not slug:
        raise UsageError("distill requires a slug")
    raw_sources = args.get("sources")
    sources: Sequence[str] | None
    if raw_sources is None:
        sources = None
    elif isinstance(raw_sources, (list, tuple)):
        # Fix: empty list should mean "use all integrated", not "zero sources".
        sources = tuple(str(s) for s in raw_sources) or None
    else:
        raise UsageError("distill sources must be a list")
    path = distill_proposal(ctx=ctx, slug=slug, sources=sources)
    return Result(
        exit_code=0,
        payload={"path": str(path), "slug": slug},
    )
