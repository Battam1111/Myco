"""Digestion pipeline primitives.

Parses the YAML frontmatter written by ingestion (see
``myco.ingestion.eat._render_note``), validates cross-references, and
promotes a raw note to ``integrated`` state by moving it from
``notes/raw/`` to ``notes/integrated/`` with updated frontmatter.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from myco.core.context import MycoContext
from myco.core.errors import ContractError, UsageError
from myco.core.io_atomic import atomic_utf8_write
from myco.core.write_surface import check_write_allowed

__all__ = [
    "Note",
    "parse_note",
    "render_note",
    "promote_to_integrated",
    "NOTE_STAGES",
]

#: Known ``stage`` values in a note's frontmatter.
NOTE_STAGES: frozenset[str] = frozenset({"raw", "digesting", "integrated", "distilled"})


@dataclass(frozen=True)
class Note:
    """A parsed note: frontmatter dict + body string."""

    frontmatter: Mapping[str, Any]
    body: str

    @property
    def stage(self) -> str:
        return str(self.frontmatter.get("stage", "raw"))

    @property
    def references(self) -> tuple[str, ...]:
        raw = self.frontmatter.get("references") or ()
        if not isinstance(raw, (list, tuple)):
            return ()
        return tuple(str(r) for r in raw)


def parse_note(text: str) -> Note:
    """Parse a note file's contents into a :class:`Note`.

    Accepts files with or without frontmatter. A missing frontmatter
    yields ``Note(frontmatter={"stage": "raw"}, body=text)``.
    """
    if not text.startswith("---\n"):
        return Note(frontmatter={"stage": "raw"}, body=text)
    # Find the closing fence.
    body_start = text.find("\n---\n", 4)
    if body_start == -1:
        raise ContractError("note frontmatter missing closing '---'")
    fm_text = text[4:body_start]
    body = text[body_start + len("\n---\n") :]
    try:
        parsed = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as exc:
        raise ContractError(f"note frontmatter is not valid YAML: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ContractError(
            f"note frontmatter must be a mapping, got {type(parsed).__name__}"
        )
    return Note(frontmatter=parsed, body=body)


def render_note(note: Note) -> str:
    """Render a :class:`Note` back to on-disk form."""
    fm_text = yaml.safe_dump(
        dict(note.frontmatter),
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
    ).strip("\n")
    body = note.body if note.body.endswith("\n") else note.body + "\n"
    return f"---\n{fm_text}\n---\n{body}"


def _is_substrate_ref(s: str) -> bool:
    """True if ``s`` looks like a substrate-relative path ref."""
    if not s:
        return False
    lowered = s.lower()
    return not lowered.startswith(("http://", "https://", "mailto:", "#", "/"))


def _validate_references(note: Note, *, substrate_root: Path) -> None:
    for ref in note.references:
        if not _is_substrate_ref(ref):
            continue
        target = (substrate_root / ref).resolve()
        try:
            target.relative_to(substrate_root.resolve())
        except ValueError as exc:
            raise ContractError(f"note reference escapes substrate: {ref}") from exc
        if not target.exists():
            raise ContractError(f"note reference does not exist: {ref}")


def _now_iso(now: datetime | None) -> str:
    now = now or datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


def promote_to_integrated(
    *,
    ctx: MycoContext,
    raw_path: Path,
    dry_run: bool = False,
    now: datetime | None = None,
) -> Path:
    """Promote ``raw_path`` to ``notes/integrated/n_<stem>.md``.

    Updates frontmatter (``stage``, ``integrated_at``), validates
    references, and (unless ``dry_run``) moves the file.

    Returns the integrated path (whether or not ``dry_run``).

    Raises:
        UsageError: if ``raw_path`` isn't under ``notes/raw/`` or not a
            ``.md`` file.
        ContractError: if the note frontmatter is broken, or a
            reference doesn't resolve.
    """
    raw_path = raw_path.resolve()
    root = ctx.substrate.root.resolve()
    raw_dir = (ctx.substrate.paths.notes / "raw").resolve()

    if not raw_path.is_file():
        raise UsageError(f"note not found: {raw_path}")
    try:
        raw_path.relative_to(raw_dir)
    except ValueError as exc:
        raise UsageError(f"note is not under notes/raw/: {raw_path}") from exc

    text = raw_path.read_text(encoding="utf-8")
    note = parse_note(text)
    _validate_references(note, substrate_root=root)

    new_fm: MutableMapping[str, Any] = dict(note.frontmatter)
    new_fm["stage"] = "integrated"
    new_fm["integrated_at"] = _now_iso(now)
    new_note = Note(frontmatter=new_fm, body=note.body)
    rendered = render_note(new_note)

    integrated_dir = ctx.substrate.paths.notes / "integrated"
    target = integrated_dir / f"n_{raw_path.stem}.md"

    if dry_run:
        return target

    integrated_dir.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise ContractError(
            f"integrated target already exists: {target}; "
            f"promote aborted to avoid data loss"
        )
    # v0.5.8 guarded rollout: enforce write_surface on the integrated
    # target. The raw-path unlink that follows is not surface-gated
    # because removing content the substrate already owns is a
    # different semantic axis (it's under notes/raw/ by construction
    # and assimilate's contract says the raw copy moves, not duplicates).
    check_write_allowed(ctx, target, verb="digest")
    atomic_utf8_write(target, rendered)
    raw_path.unlink()
    return target
