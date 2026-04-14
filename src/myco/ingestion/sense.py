"""``myco sense`` — read-only lookup across canon, notes, docs.

Minimal B.4 implementation: case-insensitive substring search over
Markdown/YAML files, capped to avoid context bombs. Each hit carries
path, line number, and snippet. Walking each tree is done lazily so
the cap can short-circuit large substrates.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal, Mapping

from myco.core.context import MycoContext, Result
from myco.core.errors import UsageError

__all__ = ["SenseHit", "search_substrate", "run"]


#: Cap on total hits returned. Keeps the caller's context bounded.
MAX_HITS: int = 50

#: File extensions considered searchable.
_SEARCHABLE_SUFFIXES = frozenset({".md", ".yaml", ".yml", ".txt"})

Scope = Literal["canon", "notes", "docs", "all"]
_VALID_SCOPES: frozenset[str] = frozenset({"canon", "notes", "docs", "all"})


@dataclass(frozen=True)
class SenseHit:
    path: str
    line: int
    snippet: str


def search_substrate(
    *,
    ctx: MycoContext,
    query: str,
    scope: Scope = "all",
    max_hits: int = MAX_HITS,
) -> tuple[SenseHit, ...]:
    """Search the substrate for ``query``.

    Returns at most ``max_hits`` hits in traversal order. Empty query
    raises ``UsageError``.
    """
    if not query.strip():
        raise UsageError("sense query must be non-empty")
    if scope not in _VALID_SCOPES:
        raise UsageError(
            f"unknown sense scope {scope!r}; "
            f"expected one of {sorted(_VALID_SCOPES)}"
        )

    needle = query.lower()
    paths = ctx.substrate.paths
    roots: list[Path] = []
    if scope in ("canon", "all"):
        if paths.canon.is_file():
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


def run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
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
                {"path": h.path, "line": h.line, "snippet": h.snippet}
                for h in hits
            ],
        },
    )


# --- helpers ---------------------------------------------------------------


def _walk_searchable(root: Path) -> Iterable[Path]:
    if root.is_file():
        if root.suffix.lower() in _SEARCHABLE_SUFFIXES:
            yield root
        return
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in _SEARCHABLE_SUFFIXES:
            yield path


def _scan_file(
    path: Path, needle: str, substrate_root: Path
) -> Iterable[SenseHit]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return
    rel = path.relative_to(substrate_root) if path.is_absolute() else path
    for lineno, line in enumerate(text.splitlines(), start=1):
        if needle in line.lower():
            yield SenseHit(
                path=str(rel).replace("\\", "/"),
                line=lineno,
                snippet=line.strip(),
            )
