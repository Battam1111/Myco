"""``myco eat`` — append a raw note.

Per L2 ingestion.md: cheap, permissive, loss-preserving. Content is
never rejected on shape; rejection is reserved for write-surface
violations (which don't exist yet — Stage B.8 will add that check).
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from myco.core.context import MycoContext, Result

__all__ = ["append_note", "EatOutcome", "run"]


_SLUG_RE = re.compile(r"[^a-z0-9]+")
_SLUG_MAX = 40


@dataclass(frozen=True)
class EatOutcome:
    """Typed result of a successful eat."""

    path: Path
    captured_at: datetime
    tags: tuple[str, ...]
    source: str


def append_note(
    *,
    ctx: MycoContext,
    content: str,
    tags: Sequence[str] = (),
    source: str = "agent",
    now: datetime | None = None,
) -> EatOutcome:
    """Append ``content`` as a raw note under ``notes/raw/``.

    Auto-creates ``notes/`` and ``notes/raw/`` if either is missing
    (per craft R5 — ingestion is cheap and permissive).

    Filename: ``<UTC_ISO>_<slug>.md``. Collisions resolved by suffix
    ``_2``, ``_3``, ….
    """
    now = now or datetime.now(timezone.utc)
    notes_dir = ctx.substrate.paths.notes
    raw_dir = notes_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    slug = _slugify(content)
    base_name = f"{stamp}_{slug}" if slug else stamp

    path = raw_dir / f"{base_name}.md"
    counter = 2
    while path.exists():
        path = raw_dir / f"{base_name}_{counter}.md"
        counter += 1

    tags_t = tuple(str(t) for t in tags)
    body = _render_note(
        captured_at=now,
        tags=tags_t,
        source=source,
        content=content,
    )
    path.write_text(body, encoding="utf-8")

    return EatOutcome(path=path, captured_at=now, tags=tags_t, source=source)


def run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """Manifest handler: append a note and return a Result.

    Three intake modes (mutually exclusive):

    1. ``--content "..."`` — literal string, written verbatim.
    2. ``--path ./file-or-dir`` — dispatched through the adapter
       registry. A single file produces one note; a directory
       produces one note per ingestible file inside it.
    3. ``--url https://...`` — fetched and dispatched by the URL
       adapter (requires ``httpx`` from ``[adapters]`` extras).

    The adapter populates ``source`` with the real provenance
    (file path, URL, repo root) instead of the default ``"agent"``.
    """
    content = args.get("content")
    path_arg = args.get("path")
    url_arg = args.get("url")

    raw_tags = args.get("tags") or ()
    if not isinstance(raw_tags, (list, tuple)):
        raw_tags = ()
    tags = [str(t) for t in raw_tags]
    source = str(args.get("source", "agent"))

    # --- Mode: adapter dispatch (path or url) ----------------------

    if path_arg or url_arg:
        target = str(path_arg or url_arg)
        from myco.ingestion.adapters import find_adapter

        adapter = find_adapter(target)
        if adapter is None:
            return Result(
                exit_code=2,
                payload={
                    "error": (
                        f"No adapter can handle {target!r}. "
                        "Install 'myco[adapters]' for PDF, HTML, and "
                        "URL support, or point at a text/code file."
                    ),
                },
            )
        results = adapter.ingest(target)
        outcomes = []
        for r in results:
            merged_tags = tuple(set(tags) | set(r.tags))
            outcome = append_note(
                ctx=ctx,
                content=r.body,
                tags=merged_tags,
                source=r.source or source,
            )
            outcomes.append(
                {
                    "path": str(outcome.path),
                    "captured_at": outcome.captured_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "title": r.title,
                    "source": r.source,
                }
            )
        return Result(
            exit_code=0,
            payload={
                "adapter": adapter.name,
                "notes_created": len(outcomes),
                "notes": outcomes,
            },
        )

    # --- Mode: literal content (existing behavior) -----------------

    outcome = append_note(
        ctx=ctx,
        content=str(content or ""),
        tags=tuple(tags),
        source=source,
    )
    return Result(
        exit_code=0,
        payload={
            "path": str(outcome.path),
            "captured_at": outcome.captured_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tags": outcome.tags,
            "source": outcome.source,
        },
    )


# --- helpers ---------------------------------------------------------------


def _slugify(text: str) -> str:
    """Produce a filesystem-safe slug from the first line of ``text``."""
    first_line = (text.splitlines() or [""])[0].strip().lower()
    slug = _SLUG_RE.sub("-", first_line).strip("-")
    return slug[:_SLUG_MAX]


def _render_note(
    *,
    captured_at: datetime,
    tags: tuple[str, ...],
    source: str,
    content: str,
) -> str:
    tags_flow = "[]" if not tags else ("[" + ", ".join(f'"{t}"' for t in tags) + "]")
    stamp = captured_at.strftime("%Y-%m-%dT%H:%M:%SZ")
    body = content.rstrip("\n") + "\n"
    return (
        "---\n"
        f'captured_at: "{stamp}"\n'
        f"tags: {tags_flow}\n"
        f'source: "{source}"\n'
        'stage: "raw"\n'
        "---\n"
        f"{body}"
    )
