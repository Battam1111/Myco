#!/usr/bin/env python3
"""derive_changelog.py — Hatch build hook deriving CHANGELOG (v0.6.0).

Per craft v0.6.0 §D7 / §M.4. At Hatchling build time, parse
``docs/contract_changelog.md`` for the section matching the current
package version (read from ``src/myco/__init__.py``), emit
``dist/CHANGELOG-derived.md``, and let release.yml inject this as
the GitHub Release ``--notes-file`` body.

This is the L0-P1-aligned solution to the v0.5.10+ CHANGELOG drift:
we don't backfill 15 versions of human-PyPI-changelog; instead we
auto-derive each release's notes from the agent-SSoT
contract_changelog.md.

Usage:
- Standalone:  ``python hooks/derive_changelog.py``
- Hatchling hook (registered in pyproject.toml):
  ``[tool.hatch.build.targets.sdist.hooks.custom]``
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def _read_version(repo_root: Path) -> str:
    init_py = repo_root / "src" / "myco" / "__init__.py"
    if not init_py.is_file():
        return "unknown"
    text = init_py.read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', text)
    return m.group(1) if m else "unknown"


def derive(repo_root: Path) -> str:
    version = _read_version(repo_root)
    changelog = repo_root / "docs" / "contract_changelog.md"
    if not changelog.is_file():
        return f"# Myco v{version}\n\n(no contract_changelog.md found)\n"
    text = changelog.read_text(encoding="utf-8")
    # Grab the section starting with `## v{version}` until the next
    # `## v` header or end of file.
    pattern = re.compile(
        rf"^## v{re.escape(version)}.*?(?=^## v|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(text)
    if not m:
        return f"# Myco v{version}\n\n(no matching section in contract_changelog.md)\n"
    body = m.group(0).strip()
    return f"# Myco v{version} release notes\n\n{body}\n"


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    output_path = repo_root / "dist" / "CHANGELOG-derived.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    body = derive(repo_root)
    output_path.write_text(body, encoding="utf-8")
    print(f"[derive_changelog] wrote {len(body)} chars to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
