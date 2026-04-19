"""``myco forage`` — inspect an external directory for ingestible material.

Forage is read-only. It lists files under a target directory that at
least one registered adapter can handle (per L0 principle 2: "no
filter on what enters"). Files that no adapter recognizes are still
reported in a ``skipped`` count so the user knows the listing is
intentionally narrowed, not silently lossy.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from myco.core.context import MycoContext, Result
from myco.core.errors import UsageError

__all__ = ["ForageItem", "list_candidates", "run"]


#: Cap on items listed (to avoid context bombs).
MAX_ITEMS: int = 500


@dataclass(frozen=True)
class ForageItem:
    path: str
    size: int
    suffix: str
    adapter: str


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
    for path in sorted(target_dir.rglob("*")):
        if not path.is_file():
            continue
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
                path=str(path),
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
