"""``myco excrete`` — safe deletion of a raw note from the substrate.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Excretion as the counterpart to ingestion" (v0.5.24 addition).

Why a dedicated verb for deletion
---------------------------------

Before v0.5.24 the substrate had no explicit way to remove a raw
note that should never have been captured (accidental paste, wrong
substrate routed by a stale ``project_dir``, duplicated ingest).
The workarounds — hand-editing the filesystem — bypass Myco's write-
surface guard and leave no audit trail. Glama's TDQS scoring called
this out as a coherence-completeness gap ("lacks explicit tools for
deletion or direct editing of raw notes"), scored 3/5 at v0.5.23.

``excrete`` closes that gap without violating any Myco invariant:

- **Scope-locked to ``notes/raw/``.** Integrated notes are by
  definition the substrate's stable knowledge; excreting them would
  silently rewrite history, which violates R4 (eat insights — no
  silent deletes) and R7 (top-down layering — integrated is a lower
  layer than raw, and you cannot delete from a lower layer without
  a contract bump). Attempts to target ``notes/integrated/`` or
  ``notes/distilled/`` are refused with ``UsageError``.

- **Atomic move to ``.myco_state/excreted/``** (tombstone), not
  ``os.unlink``. The note is preserved there with frontmatter
  annotated with ``excreted_at`` + ``excreted_reason`` + original
  path, so an operator can audit what was thrown away. The
  tombstone dir is gitignored (``.myco_state/`` isn't written to
  the write_surface).

- **Reason field is required.** ``myco_excrete --note-id X`` with
  no reason is a UsageError — enforced at the CLI + MCP layer so
  the agent can't accidentally drop material without explaining why.
  Audit-trail requirement parallels ``myco_molt``'s reason field.

- **Dry-run mode** returns the exact path that would be moved and
  the tombstone destination, without touching disk. Use before
  destructive calls.

Return shape
------------

    {
      "exit_code": 0,
      "note_id": "<stem>",
      "from_path": "notes/raw/<stem>.md",
      "to_path": ".myco_state/excreted/<stem>.md",
      "reason": "<supplied>",
      "excreted_at": "2026-04-24T08:15:00Z",
      "dry_run": false,
    }

``exit_code`` is 3 (UsageError) when the note_id doesn't resolve to
an existing raw note, when the target is outside ``notes/raw/``, or
when the reason is missing. 0 on success (including dry-run).

Pipeline placement: excrete sits in the ingestion subsystem — same
layer as eat, because it's the inverse operation on the same
layer (raw). It does NOT belong under digestion (integrated) or
cycle (session lifecycle).
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from myco.core.context import MycoContext, Result
from myco.core.errors import UsageError
from myco.core.write_surface import check_write_allowed

__all__ = ["run"]


def run(args: Mapping[str, Any], *, ctx: MycoContext) -> Result:
    """Handler for ``myco excrete`` / ``myco_excrete``.

    Moves a single raw note out of ``notes/raw/`` into
    ``.myco_state/excreted/``, with frontmatter annotated for audit.
    Refuses targets outside ``notes/raw/`` (integrated / distilled
    are protected by the ingestion doctrine's append-only rule).

    Required args: ``note_id``, ``reason``.
    Optional args: ``dry_run`` (default False).

    See module docstring for the full contract + return shape.
    """
    note_id = args.get("note_id") or args.get("note-id")
    reason = args.get("reason")
    dry_run = bool(args.get("dry_run") or args.get("dry-run") or False)

    if not note_id:
        raise UsageError(
            "excrete: --note-id is required. Pass the stem of the raw "
            "note to delete (e.g. '20260424T080500Z_typo-capture')."
        )
    if not reason or not str(reason).strip():
        raise UsageError(
            "excrete: --reason is required. Describe why this note is "
            "being removed (typo, accidental-ingest, duplicate, etc.) — "
            "the audit trail in .myco_state/excreted/ records this text."
        )

    stem = str(note_id).strip()
    raw_dir = ctx.substrate.paths.notes / "raw"
    source = raw_dir / f"{stem}.md"

    if not source.is_file():
        # Try with .md already in the stem (forgiving)
        alt = raw_dir / stem
        if alt.is_file():
            source = alt
        else:
            raise UsageError(
                f"excrete: note_id {stem!r} not found in notes/raw/. "
                f"Use myco_forage --path notes/raw to list available "
                f"raw note stems."
            )

    # Second-line-of-defense: refuse if the resolved path is NOT
    # under notes/raw/ (symlink escape, path traversal, etc.).
    try:
        source.resolve().relative_to(raw_dir.resolve())
    except ValueError as exc:
        raise UsageError(
            f"excrete: resolved path {source} is outside notes/raw/; "
            "refusing to delete. Only raw notes can be excreted."
        ) from exc

    # Compute tombstone destination.
    tombstone_dir = ctx.substrate.root / ".myco_state" / "excreted"
    destination = tombstone_dir / source.name
    excreted_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    from_rel = source.relative_to(ctx.substrate.root).as_posix()
    to_rel = destination.relative_to(ctx.substrate.root).as_posix()

    if dry_run:
        return Result(
            exit_code=0,
            payload={
                "note_id": stem,
                "from_path": from_rel,
                "to_path": to_rel,
                "reason": str(reason),
                "excreted_at": excreted_at,
                "dry_run": True,
            },
        )

    # Write-surface check: we're writing to .myco_state/excreted/.
    # Allow when the substrate's write_surface includes
    # ``.myco_state/**`` or a covering pattern; otherwise refuse.
    try:
        check_write_allowed(ctx, destination, verb="excrete")
    except Exception as exc:
        raise UsageError(
            f"excrete: write_surface does not allow writing to "
            f"{to_rel}. Add '.myco_state/**' to "
            f"_canon.yaml::system.write_surface.allowed and retry. "
            f"Original: {exc}"
        ) from exc

    tombstone_dir.mkdir(parents=True, exist_ok=True)

    # Read the note, prepend excretion metadata to frontmatter, write
    # to tombstone. Then unlink original. We use shutil.copy + unlink
    # rather than Path.rename so the operation survives cross-device
    # layouts (.myco_state/ could be on a different volume in some
    # Dockerfile / tmpfs combinations).
    original_text = source.read_text(encoding="utf-8")
    annotated = _annotate_frontmatter(
        original_text,
        excreted_at=excreted_at,
        excreted_reason=str(reason),
        excreted_from=from_rel,
    )
    destination.write_text(annotated, encoding="utf-8")
    source.unlink()

    return Result(
        exit_code=0,
        payload={
            "note_id": stem,
            "from_path": from_rel,
            "to_path": to_rel,
            "reason": str(reason),
            "excreted_at": excreted_at,
            "dry_run": False,
        },
    )


def _annotate_frontmatter(
    text: str,
    *,
    excreted_at: str,
    excreted_reason: str,
    excreted_from: str,
) -> str:
    """Add ``excreted_*`` keys to the note's YAML frontmatter.

    The note's frontmatter is expected to be a ``---``-bounded YAML
    block at the top of the file (eat.py writes this shape via
    ``yaml.safe_dump``). We insert three new keys before the closing
    ``---`` delimiter; if the note lacks frontmatter, we prepend a
    new block that carries only the excretion metadata.

    Not using ``yaml.safe_dump`` round-trip here to avoid re-
    serialising the whole frontmatter (which would rearrange keys,
    rename single-quoted scalars, etc.). Textual injection preserves
    original formatting.
    """
    if not text.startswith("---\n"):
        # No frontmatter; prepend a minimal one.
        new_fm = (
            "---\n"
            f"excreted_at: '{excreted_at}'\n"
            f"excreted_reason: '{_yaml_escape(excreted_reason)}'\n"
            f"excreted_from: '{excreted_from}'\n"
            "---\n\n"
        )
        return new_fm + text
    # Find closing --- delimiter (first occurrence after the opening).
    end = text.find("\n---\n", 4)
    if end == -1:
        # Malformed frontmatter — treat as no frontmatter.
        return text
    # Insert new keys just before the closing delimiter.
    injection = (
        f"excreted_at: '{excreted_at}'\n"
        f"excreted_reason: '{_yaml_escape(excreted_reason)}'\n"
        f"excreted_from: '{excreted_from}'\n"
    )
    return text[: end + 1] + injection + text[end + 1 :]


def _yaml_escape(s: str) -> str:
    """Escape a single-quoted YAML scalar (double any apostrophe)."""
    return s.replace("'", "''")
