#!/usr/bin/env python3
"""Install / uninstall the Myco plugin for Claude Desktop's Cowork mode.

Cowork (local-agent-mode) loads plugins from a per-workspace registry
at ``<CLAUDE_APPDATA>/local-agent-mode-sessions/<owner>/<workspace>/rpm/``.
Marketplace installs populate that directory automatically. We don't
have a Cowork marketplace for Myco today, so this script is the
equivalent: it copies the `.cowork-plugin/` template tree into every
``rpm/`` directory it can find on this machine, and upserts a
``plugins`` entry in every ``rpm/manifest.json``.

Why a skill, not a hook? Cowork does not implement Claude Code's
session-hook contract. Agent behavior is shaped by Skills — markdown
files with YAML frontmatter that Cowork matches against user intent
+ agent context. The single skill we ship, ``myco-substrate``, carries
the full onboarding brief (what Myco is, 18 verbs, R1-R7, pulse
reading, multi-project pattern) and triggers whenever the user
mentions Myco, opens a workspace containing ``_canon.yaml``, or a
prior tool response referenced a substrate.

Install path per OS:

    Windows:  %APPDATA%\\Claude\\local-agent-mode-sessions\\...
    macOS:    ~/Library/Application Support/Claude/local-agent-mode-sessions/...
    Linux:    ~/.config/Claude/local-agent-mode-sessions/...

This script is a thin shim over ``myco.install.cowork_plugin``. The
library module does all the work; the script exposes the CLI so users
with the repo checked out can run the installer without needing
``pip install -e .`` first.

Usage
-----

    # preview what would change (no writes)
    python scripts/install_cowork_plugin.py --dry-run

    # install / re-install (idempotent; safe to run twice)
    python scripts/install_cowork_plugin.py

    # uninstall
    python scripts/install_cowork_plugin.py --uninstall

Equivalent ``myco-install`` subcommands (same library calls):

    myco-install cowork-plugin
    myco-install cowork-plugin --uninstall
    myco-install cowork-plugin --dry-run

After install, restart Claude Desktop. On the next Cowork session
start the agent will see a skill named ``myco-substrate`` and follow
the R1-R7 boot ritual whenever Myco is mentioned or a workspace
contains ``_canon.yaml``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make Windows consoles happy with the decorative glyphs we print for status.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover - older Python / non-TTY
        pass

# Put the repo's src/ on sys.path so we can import myco without requiring
# the user to have run `pip install -e .` first. This mirrors what
# `scripts/bump_version.py` does for the same reason.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from myco.install.cowork_plugin import (  # noqa: E402
    PLUGIN_ID,
    claude_appdata_root,
    discover_rpm_dirs,
    install_cowork_plugin,
    uninstall_cowork_plugin,
)


# ---------------------------------------------------------------------------
# Re-exports used by the test-suite, which imports this script as a module
# via ``importlib.util.spec_from_file_location``. Keeping the symbols here
# lets the tests treat the script as the single public surface while the
# heavy lifting lives in ``myco.install.cowork_plugin``.
# ---------------------------------------------------------------------------


def _claude_appdata_root(env=None):
    return claude_appdata_root(env)


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------


def _parse_argv(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="install_cowork_plugin",
        description=(
            "Install the Myco plugin into every Cowork workspace registry on "
            "this machine. Idempotent — safe to run repeatedly."
        ),
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without writing anything.",
    )
    p.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove the Myco plugin from every Cowork workspace registry.",
    )
    p.add_argument(
        "--cowork-root",
        type=Path,
        default=None,
        help=(
            "Override the Claude Desktop application-data root (default: "
            "OS-specific — %%APPDATA%%/Claude on Windows, ~/Library/"
            "Application Support/Claude on macOS, ~/.config/Claude on Linux)."
        ),
    )
    p.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help=(
            "Override the Myco repo root (default: the parent of this "
            "script's directory)."
        ),
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_argv(argv)
    repo_root = args.repo_root or _REPO_ROOT
    cowork_root = args.cowork_root or claude_appdata_root()
    template = repo_root / ".cowork-plugin"
    targets = discover_rpm_dirs(cowork_root)
    print(f"Claude Desktop root: {cowork_root}")
    print(f"Myco repo root:      {repo_root}")
    print(f"Discovered {len(targets)} Cowork workspace(s).")
    if args.uninstall:
        result = uninstall_cowork_plugin(targets, dry_run=args.dry_run)
    else:
        result = install_cowork_plugin(template, targets, dry_run=args.dry_run)
    if result < 0:
        return 1
    if not args.dry_run and result > 0 and not args.uninstall:
        print(
            f"\nNext step: restart Claude Desktop. On the next Cowork session "
            f"the agent will see the `{PLUGIN_ID[len('plugin_'):]}-substrate` "
            f"skill and follow the R1-R7 boot ritual whenever Myco is "
            f"mentioned or a workspace contains `_canon.yaml`."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
