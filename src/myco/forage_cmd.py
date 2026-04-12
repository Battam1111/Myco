#!/usr/bin/env python3
"""
Myco Forage CLI — `myco forage add / list / digest` verb family.

Delegates all substrate-touching work to `myco.forage`. This module is
the thin CLI dispatcher; business logic lives in forage.py.

Debate of record: docs/primordia/forage_substrate_craft_2026-04-11.md
"""

from __future__ import annotations

import sys
from pathlib import Path

from myco.forage import (
    add_item,
    list_items,
    load_manifest,
    update_item_status,
    _load_forage_schema,
)


def _project_dir(args) -> Path:
    """Wave A1: delegates to centralized find_project_root."""
    from myco.project import find_project_root
    return find_project_root(getattr(args, "project_dir", None), strict=False)


def _color(code: str, s: str) -> str:
    return f"\033[{code}m{s}\033[0m"


def run_forage_add(args) -> int:
    root = _project_dir(args)
    try:
        item = add_item(
            root,
            source_url=args.source_url,
            source_type=args.source_type,
            local_path=args.local_path or "",
            license=args.license,
            why=args.why,
        )
    except ValueError as e:
        print(_color("91", f"error: {e}"), file=sys.stderr)
        return 2
    except Exception as e:
        print(_color("91", f"error: {type(e).__name__}: {e}"), file=sys.stderr)
        return 2

    print(_color("92", f"forage: added {item['id']}"))
    print(f"  source_url:  {item['source_url']}")
    print(f"  source_type: {item['source_type']}")
    print(f"  local_path:  {item['local_path'] or '(none)'}")
    print(f"  license:     {item['license']}")
    print(f"  status:      {item['status']}")
    print(f"  why:         {item['why']}")
    if item['status'] == 'quarantined':
        print(_color(
            "93",
            "  ⚠ license=unknown → auto-quarantined. Resolve license before digesting."
        ))
    return 0


def run_forage_list(args) -> int:
    root = _project_dir(args)
    status = getattr(args, "status", None)
    items = list_items(root, status=status)
    if not items:
        msg = "forage/ is empty"
        if status:
            msg = f"no items with status={status}"
        print(_color("96", msg))
        return 0

    # Display summary
    schema = _load_forage_schema(root)
    manifest = load_manifest(root)
    total = len(manifest.get("items") or [])
    by_status: dict = {}
    total_size = 0
    for it in (manifest.get("items") or []):
        by_status[it.get("status", "?")] = by_status.get(it.get("status", "?"), 0) + 1
        try:
            total_size += int(it.get("size_bytes") or 0)
        except (TypeError, ValueError):
            pass

    print(_color("1", f"forage manifest — {total} item(s)"))
    print(f"  by status: " + ", ".join(f"{k}={v}" for k, v in sorted(by_status.items())))
    print(f"  disk footprint: {total_size // (1024*1024)} MiB "
          f"(budget {int(schema['total_budget_bytes']) // (1024*1024)} MiB)")
    print()

    for it in items:
        print(_color("96", f"• {it.get('id')}  [{it.get('status')}]"))
        print(f"    source_url:  {it.get('source_url')}")
        print(f"    source_type: {it.get('source_type')}")
        print(f"    local_path:  {it.get('local_path') or '(none)'}")
        print(f"    license:     {it.get('license')}")
        print(f"    size:        {int(it.get('size_bytes') or 0)} bytes")
        acq = it.get('acquired_at') or "?"
        print(f"    acquired_at: {acq}")
        dt = it.get('digest_target') or []
        if dt:
            print(f"    digest_target: {', '.join(dt)}")
        why = it.get('why')
        if why:
            print(f"    why:         {why}")
        print()
    return 0


def run_forage_digest(args) -> int:
    """Flip an item's status — used after the agent has produced the
    digest note(s). Does NOT auto-extract content (Wave 8+ work)."""
    root = _project_dir(args)
    try:
        digest_target = args.digest_target or []
        item = update_item_status(
            root,
            args.item_id,
            args.status,
            digest_target=digest_target if digest_target else None,
        )
    except (KeyError, ValueError) as e:
        print(_color("91", f"error: {e}"), file=sys.stderr)
        return 2

    print(_color("92", f"forage: {item['id']} → status={item['status']}"))
    dt = item.get('digest_target') or []
    if dt:
        print(f"  digest_target: {', '.join(dt)}")
    return 0


def run_forage(args) -> int:
    """Top-level dispatcher for `myco forage ...`."""
    sub = getattr(args, "forage_subcommand", None)
    if sub == "add":
        return run_forage_add(args)
    if sub == "list":
        return run_forage_list(args)
    if sub == "digest":
        return run_forage_digest(args)
    print(_color("91", "error: subcommand required (add | list | digest)"),
          file=sys.stderr)
    return 2
