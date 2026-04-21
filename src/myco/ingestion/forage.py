"""``myco forage`` — inspect an external directory for ingestible material.

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
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path

from myco.core.context import MycoContext, Result
from myco.core.errors import UsageError
from myco.core.skip_dirs import should_skip_dir

__all__ = ["ForageItem", "list_candidates", "run"]


#: Cap on items listed (to avoid context bombs).
MAX_ITEMS: int = 500


@dataclass(frozen=True)
class ForageItem:
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
            # Skip symlinks entirely to avoid cycles + to match the
            # graph walker's semantics (Lens 13 P1-13-9).
            continue
        if entry.is_dir():
            if should_skip_dir(entry.name):
                continue
            yield from _walk_forage(entry)
        elif entry.is_file():
            yield entry


def list_candidates(
    *,
    target_dir: Path,
    max_items: int = MAX_ITEMS,
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
                # Normalise to POSIX separators for cross-platform
                # payload consistency (Lens 10 P1-C).
                path=str(path).replace("\\", "/"),
                size=size,
                suffix=path.suffix.lower(),
                adapter=adapter.name,
            )
        )
        if len(items) >= max_items:
            break
    return tuple(items), skipped


def run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
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
