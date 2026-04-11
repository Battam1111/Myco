#!/usr/bin/env python3
"""
Myco Upstream CLI — `myco upstream scan / absorb / ingest` verb family.

Thin dispatcher over `myco.upstream`. Business logic lives there; this
module handles argument parsing, output formatting, exit codes.

Authoritative design:
    docs/primordia/upstream_absorb_craft_2026-04-11.md (Wave 9)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from myco.upstream import (
    UpstreamError,
    absorb_from_instance,
    ingest_bundle,
    scan_kernel_inbox,
)


def _project_root(args) -> Path:
    raw = getattr(args, "project_dir", None) or "."
    root = Path(raw).resolve()
    for candidate in [root] + list(root.parents):
        if (candidate / "_canon.yaml").exists():
            return candidate
    return root


def _color(code: str, s: str) -> str:
    return f"\033[{code}m{s}\033[0m"


def run_upstream(args) -> int:
    sub = getattr(args, "upstream_subcommand", None)
    if sub is None:
        print("myco upstream: specify a subcommand "
              "(scan | absorb | ingest). See --help.", file=sys.stderr)
        return 2

    if sub == "scan":
        return _cmd_scan(args)
    if sub == "absorb":
        return _cmd_absorb(args)
    if sub == "ingest":
        return _cmd_ingest(args)

    print(f"myco upstream: unknown subcommand {sub!r}", file=sys.stderr)
    return 2


def _cmd_scan(args) -> int:
    root = _project_root(args)
    refs = scan_kernel_inbox(root)
    if getattr(args, "json", False):
        print(json.dumps(
            {"pending": [r.to_dict() for r in refs],
             "count": len(refs)},
            ensure_ascii=False, indent=2,
        ))
        return 0

    if not refs:
        print(_color("32", "🍄 Upstream inbox clean — 0 pending bundles."))
        return 0
    print(_color("36;1", f"🍄 Upstream inbox — {len(refs)} pending bundle(s)"))
    print("─" * 60)
    for r in refs:
        line = (f"  {r.bundle_id}  "
                f"[{r.severity or '?'}] "
                f"{r.target_kernel_component or '?'}\n"
                f"    {r.short_summary()}\n"
                f"    file: {r.path.name}")
        print(line)
    print()
    print(_color("2", "  Next: `myco upstream ingest <bundle-id>` "
                      "to produce pointer notes."))
    return 0


def _cmd_absorb(args) -> int:
    root = _project_root(args)
    instance_path = Path(getattr(args, "instance_path")).expanduser()
    try:
        new_refs = absorb_from_instance(root, instance_path)
    except UpstreamError as e:
        print(f"myco upstream absorb: {e}", file=sys.stderr)
        return 2

    if getattr(args, "json", False):
        print(json.dumps(
            {"absorbed": [r.to_dict() for r in new_refs],
             "count": len(new_refs)},
            ensure_ascii=False, indent=2,
        ))
        return 0

    if not new_refs:
        print(_color("33", "🍄 Absorb no-op — instance outbox is empty or "
                           "all bundles were already absorbed."))
        return 0
    print(_color("36;1", f"🍄 Absorbed {len(new_refs)} new bundle(s) from "
                         f"{instance_path}"))
    print("─" * 60)
    for r in new_refs:
        print(f"  + {r.bundle_id}  [{r.severity or '?'}] "
              f"→ {r.path.name}")
        if r.short_summary():
            print(f"    {r.short_summary()}")
    print()
    print(_color("2", "  Next: `myco upstream ingest <bundle-id>` for each."))
    return 0


def _cmd_ingest(args) -> int:
    root = _project_root(args)
    bundle_id = getattr(args, "bundle_id")
    try:
        note_path = ingest_bundle(root, bundle_id)
    except UpstreamError as e:
        print(f"myco upstream ingest: {e}", file=sys.stderr)
        return 2

    rel = note_path.relative_to(root)
    if getattr(args, "json", False):
        print(json.dumps(
            {"bundle_id": bundle_id,
             "note": str(rel),
             "status": "ok"},
            ensure_ascii=False,
        ))
        return 0
    print(_color("36;1", f"🍄 Ingested {bundle_id}"))
    print(f"  pointer note: {rel}")
    print(f"  evidence:     .myco_upstream_inbox/absorbed/")
    print()
    print(_color("2", "  Next: `myco digest <note-id>` when you're ready to "
                      "process the pointer note."))
    return 0
