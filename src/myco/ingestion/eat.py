"""``myco eat`` — append a raw note.

Per L2 ingestion.md: cheap, permissive, loss-preserving. Content is
never rejected on shape; rejection is reserved for write-surface
violations + empty-input + multi-intake-mode conflicts.

v0.5.8:
* Switched frontmatter rendering from a hand-rolled f-string to
  ``yaml.safe_dump`` so hostile ``source`` / ``tags`` values cannot
  inject arbitrary YAML keys (P0 prompt-injection fix).
* Added explicit validation that exactly one of
  ``--content`` / ``--path`` / ``--url`` is supplied, with
  ``UsageError`` instead of silently producing empty notes or
  silently dropping ``--content`` when ``--path`` is also passed.
* Same-second filename collisions now use atomic ``O_EXCL`` create
  so concurrent ``eat`` calls can't silently overwrite each other
  (P0 concurrency fix).
* Merged tags are sorted for deterministic note output across
  processes.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

from myco.core.context import MycoContext, Result
from myco.core.errors import UsageError

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

    tags_t = tuple(str(t) for t in tags)
    body = _render_note(
        captured_at=now,
        tags=tags_t,
        source=source,
        content=content,
    )

    # v0.5.8: atomic O_EXCL-create collision-resolution loop. Before
    # this fix, two concurrent `eat` calls with identical content +
    # same-second timestamp could both observe `path.exists() == False`
    # and both `write_text` to the same path — second overwrites first,
    # silent data loss. Now: try create-exclusive; on FileExistsError
    # bump the counter and retry.
    path = raw_dir / f"{base_name}.md"
    counter = 2
    while True:
        try:
            # O_EXCL guarantees atomicity on both POSIX and NTFS.
            fd = os.open(
                str(path),
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o644,
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(body)
            except BaseException:
                # Clean up on any post-open failure.
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    pass
                raise
            break
        except FileExistsError:
            path = raw_dir / f"{base_name}_{counter}.md"
            counter += 1
            if counter > 10_000:
                # Runaway collision loop — shouldn't happen at any
                # realistic concurrency level, but prevents an infinite
                # loop on a pathological filesystem.
                raise UsageError(
                    "eat: unable to find a unique filename after 10000 "
                    "attempts; is notes/raw/ accepting writes?"
                )

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

    # v0.5.8 P0 FIX: validate intake-mode mutex + non-empty. Previously
    # `myco eat` with no args silently wrote an empty note, and
    # `--content "" --path X` silently dropped --content. Both are
    # now explicit UsageError.
    _content_supplied = bool(content and str(content))
    _path_supplied = bool(path_arg)
    _url_supplied = bool(url_arg)
    _mode_count = (
        (1 if _content_supplied else 0)
        + (1 if _path_supplied else 0)
        + (1 if _url_supplied else 0)
    )
    if _mode_count == 0:
        raise UsageError(
            "eat: must pass one of --content '<text>' | --path "
            "<file-or-dir> | --url <url>. Pass --content '' "
            "explicitly only if you really want an empty note."
        )
    if _mode_count > 1:
        raise UsageError(
            "eat: --content, --path, and --url are mutually "
            "exclusive; pass only one."
        )

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
            # v0.5.8 FIX: sort merged tags so output is deterministic
            # across processes (Python hash randomization would
            # otherwise shuffle set iteration order per-process).
            merged_tags = tuple(sorted(set(tags) | set(r.tags)))
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
    """Render a raw note's frontmatter + body.

    v0.5.8 P0 fix: uses ``yaml.safe_dump`` to render the frontmatter
    dict. Previously hand-rolled with f-string interpolation, which
    allowed a hostile ``source`` value (e.g. from ``eat --url
    http://evil.tld/x``) to inject arbitrary top-level YAML keys by
    embedding ``"\\n...\\n"`` in the quoted scalar.

    The ``source`` and tag values are also sanitised via
    :func:`myco.core.trust.safe_frontmatter_field` so control
    characters and newlines never reach the YAML serialiser in the
    first place (defense-in-depth against a yaml.safe_dump edge case
    where a carefully-crafted scalar still survives).
    """
    from myco.core.trust import safe_frontmatter_field

    stamp = captured_at.strftime("%Y-%m-%dT%H:%M:%SZ")
    body = content.rstrip("\n") + "\n"
    frontmatter: dict[str, object] = {
        "captured_at": stamp,
        "tags": [safe_frontmatter_field(str(t)) for t in tags],
        "source": safe_frontmatter_field(str(source)),
        "stage": "raw",
    }
    # default_flow_style=False → block-style lists + mappings. Matches
    # the shape that `pipeline.render_note` (the integrated-note
    # renderer) already emits, so raw → integrated round-trip is
    # shape-stable.
    rendered = yaml.safe_dump(
        frontmatter,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=True,
    )
    return f"---\n{rendered}---\n{body}"
