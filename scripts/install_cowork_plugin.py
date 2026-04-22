#!/usr/bin/env python3
"""DEPRECATED in v0.5.20 — kept as a redirector so people who saved
the v0.5.19 command line still get useful output.

v0.5.19 shipped this script as an installer that wrote plugin
metadata into Claude Desktop's ``rpm/`` directory. That approach was
wrong: Cowork regenerates ``rpm/`` from its cloud marketplace on
every session start, so the writes were immediately undone.

The real permanent-install path is:

    python scripts/build_plugin.py          # build myco-<ver>.plugin
    # then drag the produced file into Claude Desktop:
    #   Settings → Plugins → Upload → select myco-<ver>.plugin

This script redirects to ``build_plugin.py`` when called without
``--uninstall``, and runs the v0.5.19 cleanup path when called with
``--uninstall``. Either way it prints a pointer to the canonical
entry points (``myco-install cowork-plugin`` and ``scripts/build_plugin.py``).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover
        pass

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="install_cowork_plugin",
        description=(
            "[Deprecated in v0.5.20] Redirects to scripts/build_plugin.py + "
            "manual drag-drop into Claude Desktop. The v0.5.19 rpm/ writer "
            "is gone — Cowork's cloud sync defeats any filesystem-level "
            "install. With --uninstall, scrubs v0.5.19-era cruft."
        ),
    )
    p.add_argument(
        "--uninstall",
        action="store_true",
        help=(
            "Remove v0.5.19 plugin_myco/ dirs + manifest rows from every "
            "Cowork workspace on this machine (harmless if never installed)."
        ),
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would happen without making changes.",
    )
    p.add_argument(
        "--cowork-root",
        type=Path,
        default=None,
        help="Override Claude Desktop's appdata root (diagnostic use).",
    )
    # Swallow deprecated v0.5.19 flags for backwards compat (they do
    # nothing under the new model but we don't want argparse to error).
    p.add_argument("--repo-root", type=Path, default=None, help=argparse.SUPPRESS)
    args = p.parse_args(argv)

    from myco.install.cowork_plugin import (
        claude_appdata_root,
        cleanup_legacy_rpm_install,
        discover_rpm_dirs,
    )

    print(
        "[install_cowork_plugin] This script is deprecated in v0.5.20.\n"
        "The Cowork plugin install path is now:\n"
        "    1. python scripts/build_plugin.py           (builds myco-<ver>.plugin)\n"
        "    2. Drag the produced file into Claude Desktop Plugin upload.\n"
        "    3. Restart any open Cowork session.\n"
        "See docs/INSTALL.md § Cowork for details.\n"
    )

    if args.uninstall:
        claude_root = args.cowork_root or claude_appdata_root()
        targets = discover_rpm_dirs(claude_root)
        if not targets:
            print("No Cowork workspaces found — nothing to clean up.")
            return 0
        print(f"Scanning {len(targets)} Cowork workspace(s) for v0.5.19 cruft...")
        changed = cleanup_legacy_rpm_install(targets, dry_run=args.dry_run)
        verb = "would remove" if args.dry_run else "removed"
        if changed == 0:
            print("No v0.5.19-era plugin_myco/ entries found.")
        else:
            print(f"{verb} v0.5.19 entries from {changed} workspace(s).")
        return 0

    # Non-uninstall path: build the bundle via the canonical script so
    # both entry points stay in lockstep.
    print("Running scripts/build_plugin.py for you...")
    print()
    from build_plugin import main as build_main  # type: ignore[import-not-found]

    return build_main([])


if __name__ == "__main__":
    raise SystemExit(main())
