#!/usr/bin/env python3
"""
Bump Myco version per semver.

Wave 55 (vision_closure_craft_2026-04-14.md §G9).

Reads current version from pyproject.toml, bumps it, optionally writes back
to pyproject.toml and src/myco/__init__.py.

Usage:
    python scripts/bump_version.py --level patch|minor|major [--write]
    python scripts/bump_version.py --explicit 0.41.0 --write
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
INIT = ROOT / "src" / "myco" / "__init__.py"


def read_version() -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not m:
        raise RuntimeError("Could not find version in pyproject.toml")
    return m.group(1)


def bump(version: str, level: str) -> str:
    parts = version.split(".")
    if len(parts) != 3:
        raise ValueError(f"Version must be MAJOR.MINOR.PATCH, got {version}")
    major, minor, patch = (int(p) for p in parts)
    if level == "major":
        major += 1
        minor = 0
        patch = 0
    elif level == "minor":
        minor += 1
        patch = 0
    elif level == "patch":
        patch += 1
    else:
        raise ValueError(f"Unknown bump level: {level}")
    return f"{major}.{minor}.{patch}"


def write_version(new_version: str) -> None:
    # pyproject.toml
    text = PYPROJECT.read_text(encoding="utf-8")
    new_text = re.sub(
        r'^version\s*=\s*"[^"]+"',
        f'version = "{new_version}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    PYPROJECT.write_text(new_text, encoding="utf-8")

    # src/myco/__init__.py — optional __version__
    if INIT.exists():
        init_text = INIT.read_text(encoding="utf-8")
        if "__version__" in init_text:
            init_text = re.sub(
                r'__version__\s*=\s*"[^"]+"',
                f'__version__ = "{new_version}"',
                init_text,
                count=1,
            )
        else:
            init_text = init_text.rstrip() + f'\n\n__version__ = "{new_version}"\n'
        INIT.write_text(init_text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Bump Myco version.")
    ap.add_argument("--level", choices=["patch", "minor", "major"], default=None)
    ap.add_argument("--explicit", type=str, default=None, help="Explicit version string")
    ap.add_argument("--write", action="store_true", help="Write back to files")
    args = ap.parse_args()

    current = read_version()
    if args.explicit:
        new = args.explicit
    elif args.level:
        new = bump(current, args.level)
    else:
        ap.error("--level or --explicit required")
        return 2

    print(f"Current: {current}")
    print(f"New:     {new}")

    if args.write:
        write_version(new)
        print(f"Wrote {new} to pyproject.toml + src/myco/__init__.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
