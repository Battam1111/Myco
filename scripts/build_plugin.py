#!/usr/bin/env python3
"""Build a Claude Desktop / Cowork ``.plugin`` bundle from ``.cowork-plugin/``.

Why this exists: Cowork persists third-party plugins only through the
Anthropic cloud marketplace, and the only user-facing way to upload
a third-party plugin there is Claude Desktop's drag-drop UI (which
accepts a ``.zip`` or ``.plugin`` file). v0.5.19's attempt to write
directly into ``rpm/`` was defeated by the cloud sync — see
``src/myco/install/plugin_bundle.py`` for the full mechanics.

Usage
-----

    # from repo root
    python scripts/build_plugin.py

    # write to a specific directory
    python scripts/build_plugin.py --out /tmp/builds

    # advertise a different version (won't match plugin.json — use
    # scripts/bump_version.py instead to move both in lockstep)
    python scripts/build_plugin.py --version 0.5.19

The CI workflow (``.github/workflows/release.yml``) runs this after
the bump-parity check, then uploads ``dist/myco-<version>.plugin`` as
a GitHub Release asset so users can ``curl -L -o myco.plugin
https://github.com/Battam1111/Myco/releases/latest/download/myco.plugin``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Put src/ on sys.path so this script runs from a repo checkout
# without requiring `pip install -e .` first. Mirrors what
# scripts/bump_version.py does.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

if sys.platform == "win32":
    # Windows consoles default to cp936/cp1252; non-ASCII chars in the
    # output (e.g. "→") would crash the print.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover - older Python / non-TTY
        pass

from myco.install.plugin_bundle import (  # noqa: E402
    BUNDLE_EXTENSION,
    PLUGIN_NAME,
    PluginBundleError,
    build_plugin_bundle,
)


def _read_package_version(repo_root: Path) -> str:
    """Cheap ``__version__`` extractor that avoids importing the package.

    We need this when run from a fresh checkout without ``pip install``
    — bump_version.py uses the same pattern.
    """
    init = repo_root / "src" / "myco" / "__init__.py"
    text = init.read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("__version__"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError(f"cannot locate __version__ in {init}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="build_plugin",
        description=(
            "Build a .plugin bundle from .cowork-plugin/. Drop the "
            "output file into Claude Desktop's Plugins → Upload UI to "
            "install it into your account's Cowork marketplace."
        ),
    )
    p.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Override the repo root (default: parent of this script's dir).",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Destination directory (default: <repo-root>/dist).",
    )
    p.add_argument(
        "--version",
        default=None,
        help=(
            "Version string for the output filename (default: "
            "myco.__version__ from src/myco/__init__.py). Must match "
            ".cowork-plugin/.claude-plugin/plugin.json::version."
        ),
    )
    p.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Error out if the output file already exists.",
    )
    args = p.parse_args(argv)

    repo_root = args.repo_root or _REPO_ROOT
    version = args.version or _read_package_version(repo_root)
    try:
        out_path = build_plugin_bundle(
            repo_root,
            version=version,
            dest_dir=args.out,
            overwrite=not args.no_overwrite,
        )
    except PluginBundleError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"built {out_path}")
    print()
    print(
        "Next step (Cowork users): drag this file into Claude Desktop.\n"
        "  1. Open Claude Desktop → Settings → Plugins (or Extensions) → Upload.\n"
        "  2. Select the file shown above.\n"
        "  3. Claude Desktop uploads it to your account's Cowork\n"
        "     marketplace (private to you). Restart any open Cowork\n"
        "     session — the plugin syncs down automatically and the\n"
        f"     '{PLUGIN_NAME}-substrate' skill activates whenever you\n"
        "     mention Myco or open a workspace with _canon.yaml.\n"
    )
    _ = BUNDLE_EXTENSION  # silence the unused-import lint
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
