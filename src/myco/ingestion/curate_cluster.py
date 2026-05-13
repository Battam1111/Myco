"""Cluster module — v0.8.8 pass-4 merge of sense, forage, intake, excrete.

=== sense ===
``myco sense`` — read-only lookup across canon, notes, docs.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Sense" (L1 R3's mechanical half — agents sense before asserting).

Minimal B.4 implementation: case-insensitive substring search over
Markdown/YAML files, capped to avoid context bombs. Each hit carries
path, line number, and snippet. Walking each tree is done lazily so
the cap can short-circuit large substrates.

=== forage ===
``myco forage`` — inspect an external directory for ingestible material.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Forage" (read-only reconnaissance verb; prelude to ``eat --path``).

Forage is read-only. It lists files under a target directory that at
least one registered adapter can handle (per L0 principle 2: "no
filter on what enters"). Files that no adapter recognizes are still
reported in a ``skipped`` count so the user knows the listing is
intentionally narrowed, not silently lossy.

v0.5.8 (Lens 7 P0-02 / Lens 4 P1-10): the walker now honors
``myco.core.skip_dirs`` so ``myco forage`` in a real-world project
no longer stats every file in ``.git`` / ``.venv`` / ``node_modules``.
Previous behavior on this repo took 5.5-6.4 seconds (87% of which
was .git traversal); now the walker prunes those subtrees at their
roots. Also switched from ``sorted(rglob)`` (which materialises the
full listing before the cap triggers) to a manual DFS that yields
files incrementally so the cap short-circuits correctly.

=== intake ===
``ingestion.intake`` — bulk forage + eat composer (v0.6.0).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
single-responsibility extension; v0.6.0 craft §F (work E.1) replaces
the unimplemented ``forage --digest-on-read`` flag with this dedicated
verb.

``intake --path <dir> [--filter <regex>] [--max <int>] [--dry-run]
[--strict]`` walks the directory via ``forage.list_candidates``, then
calls ``eat.append_note`` on each ForageItem. The two-step composition
preserves single-responsibility:

- ``forage`` stays read-only (lists candidates, no writes).
- ``eat`` stays single-note ingest.
- ``intake`` is the bulk composer.

Failure semantics (per craft §F22 / J Adapter visibility):

- Default: any per-file ingest failure produces a ``status: failed``
  stub note in ``notes/raw/`` and is reported in the result payload's
  ``failures`` list. Other files continue processing.
- ``--strict``: any per-file ingest failure raises ``MycoError``
  (exit_code=2) — agent gets exit_on=critical-equivalent gate.

Returns: ``Result`` with payload ``{ingested, failed, failures,
notes, dry_run}``.

=== excrete ===
``myco excrete`` — safe deletion of a raw note from the substrate.

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

- **Atomic move to ``.myco/state/excreted/``** (tombstone), not
  ``os.unlink``. The note is preserved there with frontmatter
  annotated with ``excreted_at`` + ``excreted_reason`` + original
  path, so an operator can audit what was thrown away. The
  tombstone dir is gitignored (``.myco/state/`` isn't written to
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
      "to_path": ".myco/state/excreted/<stem>.md",
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

import re
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass

# v0.8.8 — intake's eat/forage references resolve to in-cluster
# helpers (forage in this same module; eat in capture_cluster).
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from myco.core.identity_cluster import MycoContext, MycoError, Result, UsageError
from myco.core.io_cluster import bounded_read_text, should_skip_dir
from myco.core.trust_cluster import check_write_allowed

# =========================================================================
# === sense — formerly sense.py
# =========================================================================

MAX_HITS: int = 50

_SEARCHABLE_SUFFIXES = frozenset({".md", ".yaml", ".yml", ".txt"})

Scope = Literal["canon", "notes", "docs", "all"]

_VALID_SCOPES: frozenset[str] = frozenset({"canon", "notes", "docs", "all"})


@dataclass(frozen=True)
class SenseHit:
    """One grep match returned by ``myco sense``.

    ``path`` is substrate-relative (POSIX separators); ``line`` is
    1-based; ``snippet`` is the matching line's text with surrounding
    context trimmed to keep payloads agent-readable.
    """

    path: str
    line: int
    snippet: str


def search_substrate(
    *, ctx: MycoContext, query: str, scope: Scope = "all", max_hits: int = MAX_HITS
) -> tuple[SenseHit, ...]:
    """Search the substrate for ``query``.

    Returns at most ``max_hits`` hits in traversal order. Empty query
    raises ``UsageError``.
    """
    if not query.strip():
        raise UsageError("sense query must be non-empty")
    if scope not in _VALID_SCOPES:
        raise UsageError(
            f"unknown sense scope {scope!r}; expected one of {sorted(_VALID_SCOPES)}"
        )
    needle = query.lower()
    paths = ctx.substrate.paths
    roots: list[Path] = []
    if scope in ("canon", "all") and paths.canon.is_file():
        roots.append(paths.canon)
    if scope in ("notes", "all") and paths.notes.is_dir():
        roots.append(paths.notes)
    if scope in ("docs", "all") and paths.docs.is_dir():
        roots.append(paths.docs)
    hits: list[SenseHit] = []
    for root in roots:
        for path in _walk_searchable(root):
            for hit in _scan_file(path, needle, ctx.substrate.root):
                hits.append(hit)
                if len(hits) >= max_hits:
                    return tuple(hits)
    return tuple(hits)


def sense_run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """Manifest handler: search the substrate."""
    query = str(args.get("query", ""))
    scope_arg = str(args.get("scope", "all"))
    if scope_arg not in _VALID_SCOPES:
        raise UsageError(f"unknown sense scope {scope_arg!r}")
    hits = search_substrate(ctx=ctx, query=query, scope=scope_arg)  # type: ignore[arg-type]
    return Result(
        exit_code=0,
        payload={
            "query": query,
            "scope": scope_arg,
            "hits": [
                {"path": h.path, "line": h.line, "snippet": h.snippet} for h in hits
            ],
        },
    )


def _walk_searchable(root: Path) -> Iterable[Path]:
    if root.is_file():
        if root.suffix.lower() in _SEARCHABLE_SUFFIXES:
            yield root
        return
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in _SEARCHABLE_SUFFIXES:
            yield path


def _scan_file(path: Path, needle: str, substrate_root: Path) -> Iterable[SenseHit]:
    try:
        text = bounded_read_text(path)
    except (OSError, UnicodeDecodeError, MycoError):
        return
    rel = path.relative_to(substrate_root) if path.is_absolute() else path
    for lineno, line in enumerate(text.splitlines(), start=1):
        if needle in line.lower():
            yield SenseHit(
                path=str(rel).replace("\\", "/"), line=lineno, snippet=line.strip()
            )


# =========================================================================
# === forage — formerly forage.py
# =========================================================================

MAX_ITEMS: int = 500


@dataclass(frozen=True)
class ForageItem:
    """One row in ``myco forage`` output.

    Describes a single file the walker claims is ingestible. ``path``
    is POSIX-normalised (cross-platform payload invariant); ``size``
    is bytes; ``suffix`` is lower-cased extension (``.md``, ``.py``);
    ``adapter`` is the registered adapter name that will handle the
    file if ``myco eat --path <path>`` is invoked.
    """

    path: str
    size: int
    suffix: str
    adapter: str


def _walk_forage(root: Path) -> Iterator[Path]:
    """Manual DFS with skip-dir pruning.

    Yields files in sorted order within each directory so the listing
    is deterministic, but prunes ``should_skip_dir`` subtrees (``.git``,
    ``.venv``, ``node_modules`` etc.) before descending — avoids the
    Lens 7 P0-02 cliff where forage on a repo root scanned ~10k
    git-object files.
    """
    try:
        entries = sorted(root.iterdir())
    except OSError:
        return
    for entry in entries:
        if entry.is_symlink():
            continue
        if entry.is_dir():
            if should_skip_dir(entry.name):
                continue
            yield from _walk_forage(entry)
        elif entry.is_file():
            yield entry


def list_candidates(
    *, target_dir: Path, max_items: int = MAX_ITEMS
) -> tuple[tuple[ForageItem, ...], int]:
    """List ingestible files under ``target_dir`` (read-only).

    Returns ``(items, skipped_count)``. ``skipped_count`` is the
    number of files no adapter claimed; reporting it prevents the
    silent-loss bug that existed in v0.4.1.
    """
    from myco.ingestion.adapters import find_adapter

    target_dir = target_dir.resolve()
    if not target_dir.exists():
        raise UsageError(f"forage target does not exist: {target_dir}")
    if not target_dir.is_dir():
        raise UsageError(f"forage target is not a directory: {target_dir}")
    items: list[ForageItem] = []
    skipped = 0
    for path in _walk_forage(target_dir):
        adapter = find_adapter(str(path))
        if adapter is None:
            skipped += 1
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        items.append(
            ForageItem(
                path=str(path).replace("\\", "/"),
                size=size,
                suffix=path.suffix.lower(),
                adapter=adapter.name,
            )
        )
        if len(items) >= max_items:
            break
    return (tuple(items), skipped)


def forage_run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """Manifest handler: list candidates."""
    raw_path = args.get("path")
    target = ctx.substrate.root if raw_path is None else Path(str(raw_path))
    items, skipped = list_candidates(target_dir=target)
    return Result(
        exit_code=0,
        payload={
            "target": str(target.resolve()),
            "count": len(items),
            "skipped": skipped,
            "items": [
                {
                    "path": it.path,
                    "size": it.size,
                    "suffix": it.suffix,
                    "adapter": it.adapter,
                }
                for it in items
            ],
        },
    )


# =========================================================================
# === intake — formerly intake.py
# =========================================================================


def intake_run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """Manifest-dispatched entry point.

    Standard verb-handler signature: ``run(args, *, ctx) -> Result``.
    Translates the manifest's typed dict into ``intake_directory`` kwargs.
    """
    path = args.get("path")
    if not isinstance(path, (str, Path)):
        raise MycoError("intake: --path is required")
    payload = intake_directory(
        ctx,
        path=str(path),
        filter_pattern=_as_str_or_none(args.get("filter")),
        max_count=_as_int_or_none(args.get("max")),
        dry_run=bool(args.get("dry_run", False)),
        strict=bool(args.get("strict", False)),
    )
    exit_code = int(payload.get("exit_code", 0))
    return Result(exit_code=exit_code, payload=payload)


def intake_run_cli(args: Any, ctx: MycoContext) -> Result:
    """CLI entry point. Translates argparse Namespace into the
    standard ``run`` invocation."""
    return intake_run(
        {
            "path": getattr(args, "path", None),
            "filter": getattr(args, "filter", None),
            "max": getattr(args, "max", None),
            "dry_run": getattr(args, "dry_run", False),
            "strict": getattr(args, "strict", False),
        },
        ctx=ctx,
    )


def _as_str_or_none(v: object) -> str | None:
    if v is None:
        return None
    return str(v)


def _as_int_or_none(v: object) -> int | None:
    if v is None:
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        try:
            return int(v)
        except ValueError:
            return None
    return None


def intake_directory(
    ctx: MycoContext,
    path: str,
    *,
    filter_pattern: str | None = None,
    max_count: int | None = None,
    dry_run: bool = False,
    strict: bool = False,
) -> dict[str, Any]:
    """Bulk-ingest a directory: list candidates then eat each.

    Args:
        ctx: substrate context.
        path: absolute or substrate-relative directory to scan.
        filter_pattern: optional regex; only candidates whose path
            matches are ingested.
        max_count: optional hard cap on ingest count.
        dry_run: if True, list intended actions without writing.
        strict: if True, any per-file failure raises MycoError.

    Returns:
        v0.6.0 verb-result payload dict.
    """
    target = Path(path)
    if not target.is_absolute():
        target = ctx.substrate.root / target
    if not target.exists():
        raise MycoError(f"intake: path not found: {target}")
    if not target.is_dir():
        raise MycoError(
            f"intake: path is not a directory: {target}; use myco_eat for single files"
        )
    items, _skipped = list_candidates(target_dir=target)
    pat: re.Pattern[str] | None = None
    if filter_pattern:
        try:
            pat = re.compile(filter_pattern)
        except re.error as exc:
            raise MycoError(
                f"intake: bad --filter pattern {filter_pattern!r}: {exc}"
            ) from exc
    ingested: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for item in items:
        if max_count is not None and len(ingested) >= max_count:
            break
        item_path = str(item.path) if hasattr(item, "path") else None
        if not item_path:
            continue
        if pat is not None and (not pat.search(item_path)):
            continue
        if dry_run:
            ingested.append({"path": item_path, "status": "dry_run"})
            continue
        try:
            try:
                file_text = Path(item_path).read_text(
                    encoding="utf-8", errors="replace"
                )
            except OSError as exc:
                raise MycoError(f"read failed: {exc}") from exc
            # Lazy-import to avoid circular dep on capture_cluster.
            from .capture_cluster import append_note as _append_note

            outcome = _append_note(
                ctx=ctx, content=file_text, source=str(item_path), tags=("intake",)
            )
            ingested.append(
                {
                    "path": item_path,
                    "status": "ok",
                    "note_path": str(outcome.path)
                    if hasattr(outcome, "path")
                    else None,
                }
            )
        except MycoError as exc:
            failure_record = {"path": item_path, "reason": str(exc)}
            failures.append(failure_record)
            if strict:
                raise MycoError(
                    f"intake --strict: ingest of {item_path!r} failed: {exc}"
                ) from exc
        except Exception as exc:
            failure_record = {
                "path": item_path,
                "reason": f"{type(exc).__name__}: {exc}",
            }
            failures.append(failure_record)
            if strict:
                raise MycoError(
                    f"intake --strict: ingest of {item_path!r} raised {type(exc).__name__}: {exc}"
                ) from exc
    return {
        "exit_code": 0 if not failures or not strict else 2,
        "ingested": len(ingested),
        "failed": len(failures),
        "failures": failures,
        "notes": ingested,
        "dry_run": dry_run,
    }


# =========================================================================
# === excrete — formerly excrete.py
# =========================================================================


def excrete_run(args: Mapping[str, Any], *, ctx: MycoContext) -> Result:
    """Handler for ``myco excrete`` / ``myco_excrete``.

    Moves a single raw note out of ``notes/raw/`` into
    ``.myco/state/excreted/``, with frontmatter annotated for audit.
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
            "excrete: --note-id is required. Pass the stem of the raw note to delete (e.g. '20260424T080500Z_typo-capture')."
        )
    if not reason or not str(reason).strip():
        raise UsageError(
            "excrete: --reason is required. Describe why this note is being removed (typo, accidental-ingest, duplicate, etc.) — the audit trail in .myco/state/excreted/ records this text."
        )
    stem = str(note_id).strip()
    raw_dir = ctx.substrate.paths.notes / "raw"
    source = raw_dir / f"{stem}.md"
    if not source.is_file():
        alt = raw_dir / stem
        if alt.is_file():
            source = alt
        else:
            raise UsageError(
                f"excrete: note_id {stem!r} not found in notes/raw/. Use myco_forage --path notes/raw to list available raw note stems."
            )
    try:
        source.resolve().relative_to(raw_dir.resolve())
    except ValueError as exc:
        raise UsageError(
            f"excrete: resolved path {source} is outside notes/raw/; refusing to delete. Only raw notes can be excreted."
        ) from exc
    tombstone_dir = ctx.substrate.root / ".myco/state" / "excreted"
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
    try:
        check_write_allowed(ctx, destination, verb="excrete")
    except Exception as exc:
        raise UsageError(
            f"excrete: write_surface does not allow writing to {to_rel}. Add '.myco/state/**' to _canon.yaml::system.write_surface.allowed and retry. Original: {exc}"
        ) from exc
    tombstone_dir.mkdir(parents=True, exist_ok=True)
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
    text: str, *, excreted_at: str, excreted_reason: str, excreted_from: str
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
        new_fm = f"---\nexcreted_at: '{excreted_at}'\nexcreted_reason: '{_yaml_escape(excreted_reason)}'\nexcreted_from: '{excreted_from}'\n---\n\n"
        return new_fm + text
    end = text.find("\n---\n", 4)
    if end == -1:
        return text
    injection = f"excreted_at: '{excreted_at}'\nexcreted_reason: '{_yaml_escape(excreted_reason)}'\nexcreted_from: '{excreted_from}'\n"
    return text[: end + 1] + injection + text[end + 1 :]


def _yaml_escape(s: str) -> str:
    """Escape a single-quoted YAML scalar (double any apostrophe)."""
    return s.replace("'", "''")
