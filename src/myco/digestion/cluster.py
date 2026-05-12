"""Digestion verbs cluster (v0.8.8 pass-4 merge).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/digestion.md``.

Merged home of four digestion modules that previously lived in their
own per-verb / per-primitive files (``pipeline.py``, ``digest.py``,
``assimilate.py``, ``sporulate.py``). Cluster-merge per v0.8.8 owner
directive (maximum aggressive file-count cut). Section markers
``# === <stem> — ...`` preserve per-file review boundaries; git
history holds the original per-file state.

Layout:

* Pipeline primitives — ``Note``, ``parse_note``, ``render_note``,
  ``promote_to_integrated``, ``NOTE_STAGES``.
* ``digest`` verb — ``digest_one``, ``digest_run`` (was ``run``).
* ``assimilate`` verb — ``reflect``, ``assimilate`` (alias),
  ``_sync_contract_version``, ``assimilate_run`` (was ``run``).
* ``sporulate`` verb — ``distill_proposal``, ``sporulate_run``
  (was ``run``).

Manifest dispatch (``boundary/surface/manifest.yaml``) points at the
``<verb>_run`` entry-points in this cluster.
"""

from __future__ import annotations

import re as _re
from collections.abc import Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from myco.core.identity_cluster import (
    ContractError,
    MycoContext,
    MycoError,
    Result,
    UsageError,
)
from myco.core.io_cluster import atomic_utf8_write, bounded_read_text
from myco.core.trust_cluster import check_write_allowed

__all__ = [
    # Pipeline primitives
    "Note",
    "parse_note",
    "render_note",
    "promote_to_integrated",
    "NOTE_STAGES",
    # digest verb
    "digest_one",
    "digest_run",
    # assimilate verb
    "reflect",
    "assimilate",
    "assimilate_run",
    # sporulate verb
    "distill_proposal",
    "sporulate_run",
]


# =========================================================================
# === pipeline — formerly digestion/pipeline.py (203 LOC)
# =========================================================================

#: Known ``stage`` values in a note's frontmatter.
NOTE_STAGES: frozenset[str] = frozenset(
    {
        "raw",
        "digesting",
        "integrated",
        "distilled",
        "sporulated",  # v0.6.0
        "re_raw",  # v0.6.0
    }
)


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
    """Parse a note file's contents into a :class:`Note`."""
    if not text.startswith("---\n"):
        return Note(frontmatter={"stage": "raw"}, body=text)
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
    """Promote ``raw_path`` to ``notes/integrated/n_<stem>.md``."""
    raw_path = raw_path.resolve()
    root = ctx.substrate.root.resolve()
    raw_dir = (ctx.substrate.paths.notes / "raw").resolve()

    if not raw_path.is_file():
        raise UsageError(f"note not found: {raw_path}")
    try:
        raw_path.relative_to(raw_dir)
    except ValueError as exc:
        raise UsageError(f"note is not under notes/raw/: {raw_path}") from exc

    text = bounded_read_text(raw_path)
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

    # v0.8.6 ordering fix: write-surface check before any filesystem mutation.
    check_write_allowed(ctx, target, verb="digest")
    integrated_dir.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise ContractError(
            f"integrated target already exists: {target}; "
            f"promote aborted to avoid data loss"
        )
    atomic_utf8_write(target, rendered)
    raw_path.unlink()
    return target


# =========================================================================
# === digest — formerly digestion/digest.py (73 LOC)
# =========================================================================


def _normalize_id(note_id: str) -> str:
    """Strip an optional ``n_`` integrated-prefix so callers can use either form."""
    return note_id[2:] if note_id.startswith("n_") else note_id


def digest_one(
    *,
    ctx: MycoContext,
    note_id: str,
    dry_run: bool = False,
) -> dict[str, object]:
    """Promote a single note by ``note_id`` (filename stem, with or without ``n_``)."""
    stem = _normalize_id(note_id)
    raw_path = ctx.substrate.paths.notes / "raw" / f"{stem}.md"
    integrated_path = ctx.substrate.paths.notes / "integrated" / f"n_{stem}.md"

    if integrated_path.is_file():
        return {
            "status": "already_integrated",
            "path": str(integrated_path),
            "dry_run": dry_run,
            "note_id": stem,
        }

    if not raw_path.is_file():
        raise UsageError(
            f"unknown note id: {note_id} (looked for {raw_path} and {integrated_path})"
        )

    target = promote_to_integrated(ctx=ctx, raw_path=raw_path, dry_run=dry_run)
    return {
        "status": "dry_run" if dry_run else "promoted",
        "path": str(target),
        "dry_run": dry_run,
        "note_id": stem,
    }


def digest_run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """Manifest handler: promote a single raw note by id."""
    note_id = str(args.get("note_id") or args.get("note-id") or "")
    if not note_id:
        raise UsageError("digest requires a note-id")
    dry_run = bool(args.get("dry_run", False))
    outcome = digest_one(ctx=ctx, note_id=note_id, dry_run=dry_run)
    return Result(exit_code=0, payload=outcome)


# =========================================================================
# === assimilate — formerly digestion/assimilate.py (183 LOC)
# =========================================================================


def _sync_contract_version(ctx: MycoContext) -> bool:
    """Write ``synced_contract_version = contract_version`` to canon."""
    canon = ctx.substrate.canon
    synced = canon.synced_contract_version
    if synced == canon.contract_version:
        return False
    canon_path = ctx.substrate.paths.canon
    if not canon_path.is_file():
        return False
    text = bounded_read_text(canon_path)
    pattern = _re.compile(
        r'^(?P<prefix>synced_contract_version:\s*)(?P<q>["\'])[^"\']*(?P=q)\s*$',
        _re.MULTILINE,
    )
    new_text, n = pattern.subn(rf'\g<prefix>"{canon.contract_version}"', text, count=1)
    if n == 0:
        return False
    check_write_allowed(ctx, canon_path, verb="assimilate:sync_contract_version")
    atomic_utf8_write(canon_path, new_text)
    return True


def _list_raw(ctx: MycoContext) -> list[Path]:
    raw = ctx.substrate.paths.notes / "raw"
    if not raw.is_dir():
        return []
    return sorted(p for p in raw.glob("*.md") if p.is_file())


def reflect(*, ctx: MycoContext, note_id: str | None = None) -> dict[str, object]:
    """Promote raw notes (bulk if note_id is None, else single)."""
    if note_id is not None:
        outcomes: list[dict[str, object]] = []
        errors: list[dict[str, str]] = []
        try:
            outcomes.append(digest_one(ctx=ctx, note_id=note_id))
        except MycoError as exc:
            errors.append({"note_id": note_id, "error": str(exc)})
        return {
            "promoted": sum(1 for o in outcomes if o.get("status") == "promoted"),
            "already_integrated": sum(
                1 for o in outcomes if o.get("status") == "already_integrated"
            ),
            "errors": errors,
            "outcomes": outcomes,
        }

    raw_paths = _list_raw(ctx)
    outcomes_all: list[dict[str, object]] = []
    errors_all: list[dict[str, str]] = []
    for path in raw_paths:
        stem = path.stem
        try:
            outcomes_all.append(digest_one(ctx=ctx, note_id=stem))
        except MycoError as exc:
            errors_all.append({"note_id": stem, "error": str(exc)})

    return {
        "promoted": sum(1 for o in outcomes_all if o.get("status") == "promoted"),
        "already_integrated": sum(
            1 for o in outcomes_all if o.get("status") == "already_integrated"
        ),
        "errors": errors_all,
        "outcomes": outcomes_all,
    }


#: Fungal-vocabulary alias for :func:`reflect`.
assimilate = reflect


def assimilate_run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """Manifest handler: bulk-promote raw notes (or a single ``note_id``)."""
    note_id = args.get("note_id") or args.get("note")
    note_id_str = str(note_id) if note_id else None
    summary = reflect(ctx=ctx, note_id=note_id_str)

    total = len(summary["outcomes"]) + len(summary["errors"])  # type: ignore[arg-type]
    exit_code = 1 if (total > 0 and not summary["outcomes"]) else 0

    synced_updated = False
    if exit_code == 0 and not summary["errors"]:
        try:
            synced_updated = _sync_contract_version(ctx)
        except OSError:
            synced_updated = False

    payload = dict(summary)
    payload["synced_contract_version_updated"] = synced_updated
    return Result(exit_code=exit_code, payload=payload)


# =========================================================================
# === sporulate — formerly digestion/sporulate.py (200 LOC)
# =========================================================================

_SLUG_RE = _re.compile(r"^[a-z][a-z0-9_-]{0,63}$")


def _integrated_notes(ctx: MycoContext) -> list[Path]:
    d = ctx.substrate.paths.notes / "integrated"
    if not d.is_dir():
        return []
    return sorted(p for p in d.glob("n_*.md") if p.is_file())


def _summary_line(path: Path) -> str:
    try:
        text = bounded_read_text(path)
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
    """Create ``notes/distilled/d_<slug>.md`` with a proposal body."""
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

    all_tags: dict[str, int] = {}
    summaries: list[str] = []
    for path in source_paths:
        note = parse_note(bounded_read_text(path))
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
    check_write_allowed(ctx, target, verb="sporulate")
    atomic_utf8_write(target, render_note(note))
    return target


def sporulate_run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """Manifest handler: bundle integrated notes into a proposal skeleton."""
    slug = str(args.get("slug") or "")
    if not slug:
        raise UsageError("distill requires a slug")
    raw_sources = args.get("sources")
    sources: Sequence[str] | None
    if raw_sources is None:
        sources = None
    elif isinstance(raw_sources, (list, tuple)):
        sources = tuple(str(s) for s in raw_sources) or None
    else:
        raise UsageError("distill sources must be a list")
    path = distill_proposal(ctx=ctx, slug=slug, sources=sources)
    return Result(
        exit_code=0,
        payload={"path": str(path), "slug": slug},
    )
