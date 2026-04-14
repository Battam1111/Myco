"""``myco forage`` — inspect an external directory for ingestible material.

Forage is read-only by default. ``--digest-on-read`` delegates to
Digestion (Stage B.5); B.4 raises ``NotImplementedError`` on that path
so the flag surface is stable.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from myco.core.context import MycoContext, Result
from myco.core.errors import UsageError

__all__ = ["ForageItem", "list_candidates", "run"]


#: Extensions considered ingestible. Binary-ish types are skipped.
_INGESTIBLE_SUFFIXES: frozenset[str] = frozenset(
    {".md", ".txt", ".yaml", ".yml", ".json", ".rst", ".log"}
)

#: Cap on items listed (to avoid context bombs).
MAX_ITEMS: int = 200


@dataclass(frozen=True)
class ForageItem:
    path: str
    size: int
    suffix: str


def list_candidates(
    *,
    target_dir: Path,
    max_items: int = MAX_ITEMS,
) -> tuple[ForageItem, ...]:
    """List ingestible files under ``target_dir`` (read-only)."""
    target_dir = target_dir.resolve()
    if not target_dir.exists():
        raise UsageError(f"forage target does not exist: {target_dir}")
    if not target_dir.is_dir():
        raise UsageError(f"forage target is not a directory: {target_dir}")

    items: list[ForageItem] = []
    for path in sorted(target_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in _INGESTIBLE_SUFFIXES:
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
            )
        )
        if len(items) >= max_items:
            break
    return tuple(items)


def run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """Manifest handler: list candidates, optionally delegate to digest."""
    raw_path = args.get("path")
    if raw_path is None:
        target = ctx.substrate.root
    else:
        target = Path(str(raw_path))

    digest_on_read = bool(args.get("digest_on_read", False))
    if digest_on_read:
        raise NotImplementedError(
            "--digest-on-read requires Digestion (Stage B.5), "
            "which has not yet landed"
        )

    items = list_candidates(target_dir=target)
    return Result(
        exit_code=0,
        payload={
            "target": str(target.resolve()),
            "items": [
                {"path": it.path, "size": it.size, "suffix": it.suffix}
                for it in items
            ],
            "digest_on_read": digest_on_read,
        },
    )
