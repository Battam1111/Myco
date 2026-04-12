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
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from myco.upstream import (
    UpstreamError,
    absorb_from_instance,
    ingest_bundle,
    scan_kernel_inbox,
)


# Wave 16 (contract v0.15.0) — upstream scan timestamp write path.
# See docs/primordia/upstream_scan_timestamp_craft_2026-04-11.md.
# Surgical regex edit, NOT yaml.dump (would destroy comments). Matches
# exactly one line; zero/multi match → WARN, bail, scan still succeeds.
_SCAN_TS_RE = re.compile(
    r"^(?P<indent>\s*)upstream_scan_last_run\s*:\s*.*$",
    re.MULTILINE,
)


def _update_scan_timestamp(root: Path) -> None:
    """Write `system.upstream_scan_last_run` to current UTC ISO-8601.

    Best-effort: any failure logs a warning to stderr but does not
    raise. Called at the end of a successful `myco upstream scan`.
    The timestamp records scan freshness, not scan result — zero-pending
    scans still update the field (see craft §1 A2-A4).
    """
    canon_path = root / "_canon.yaml"
    try:
        text = canon_path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"[WARN] upstream scan timestamp: cannot read _canon.yaml "
              f"({e})", file=sys.stderr)
        return

    matches = list(_SCAN_TS_RE.finditer(text))
    if len(matches) != 1:
        print(f"[WARN] upstream scan timestamp: expected exactly 1 "
              f"`upstream_scan_last_run:` line in _canon.yaml, found "
              f"{len(matches)} — skipping update (scan still OK).",
              file=sys.stderr)
        return

    ts = (datetime.now(timezone.utc)
          .replace(microsecond=0)
          .strftime("%Y-%m-%dT%H:%M:%SZ"))
    m = matches[0]
    indent = m.group("indent")
    new_line = f'{indent}upstream_scan_last_run: "{ts}"'
    new_text = text[:m.start()] + new_line + text[m.end():]
    try:
        canon_path.write_text(new_text, encoding="utf-8")
    except OSError as e:
        print(f"[WARN] upstream scan timestamp: cannot write _canon.yaml "
              f"({e})", file=sys.stderr)


def _project_root(args) -> Path:
    """Wave A1: delegates to centralized find_project_root."""
    from myco.project import find_project_root
    return find_project_root(getattr(args, "project_dir", None), strict=False)


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
    # Wave 16 (v0.15.0): record scan freshness. Records the attempt,
    # not the result — zero-pending scans still update. See craft
    # docs/primordia/upstream_scan_timestamp_craft_2026-04-11.md.
    _update_scan_timestamp(root)
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
