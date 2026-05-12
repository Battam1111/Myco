#!/usr/bin/env python3
"""sync_plugin_mirrors.py — idempotent mirror sync for v0.6.11 plugin scopes.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/boundary.md``
§ "Subagents and slash commands (v0.6.11+)" + ``L2_DOCTRINE/homeostasis.md``
§ "永恒删减 (eternal pruning)" — supports the v0.7.3 MF5 dim's
MIRROR_DRIFT detection.

The v0.6.11 plugin spec mandates that every subagent + slash-command
markdown file exist at TWO paths:

- ``.claude/{agents,commands}/<name>.md`` — project-scope, read by
  Claude Code when developing inside Myco-self.
- ``<repo>/{agents,commands}/<name>.md`` — plugin-bundle scope,
  declared in ``.claude-plugin/plugin.json::agents | commands`` and
  shipped to the marketplace install path.

Per Claude Code spec, the marketplace install loader does NOT support
build-time generation of these files; both paths must be concrete on
disk at install time. The two paths must therefore stay byte-identical;
drift = real lint (MF5 MEDIUM finding).

This script makes the project-scope copy the SSoT and idempotently
copies it to the bundle scope. Run with --check to detect drift
without mutating.

Wired into:

- ``scripts/bump_version.py`` post-bump (every release ensures synced
  mirrors before the molt commit).
- ``scripts/build_plugin.py`` pre-build (defense-in-depth).

Usage:
    python scripts/sync_plugin_mirrors.py            # apply (idempotent)
    python scripts/sync_plugin_mirrors.py --check    # detect drift; exit 1 if drift

Exit codes:
    0 — already in sync (or successfully synced when not --check)
    1 — drift detected (--check mode) or sync failed
    2 — usage error
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

#: Documented mirror pairs per v0.6.11 plugin contract.
#: Each entry: (project-scope source dir, bundle-scope target dir).
#: v0.8.4 root-cleanup (2026-05-12): bundle-scope targets relocated
#: from <repo>/{agents,commands}/ to <repo>/plugin/{agents,commands}/
#: per the plugin/ consolidation. Project-scope source (.claude/*) is
#: unchanged — Claude Code project config lives at .claude/ by spec.
_MIRROR_PAIRS: tuple[tuple[str, str], ...] = (
    (".claude/agents", ".plugin/agents"),
    (".claude/commands", ".plugin/commands"),
)


def _hash_file(path: Path) -> str:
    """Return SHA-256 hex digest of file content."""
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _detect_drift(
    repo_root: Path,
) -> list[tuple[str, str, str]]:
    """Return list of (source_rel, target_rel, kind) for any drift.

    kind ∈ {"missing_target", "drift", "orphan_target"}.
    """
    drift: list[tuple[str, str, str]] = []
    for proj_rel, bund_rel in _MIRROR_PAIRS:
        proj_dir = repo_root / proj_rel
        bund_dir = repo_root / bund_rel
        if not proj_dir.is_dir():
            continue
        if not bund_dir.is_dir():
            # Bundle dir entirely missing — every project file is a
            # missing-target case.
            for src in proj_dir.glob("*.md"):
                drift.append(
                    (
                        src.relative_to(repo_root).as_posix(),
                        f"{bund_rel}/{src.name}",
                        "missing_target",
                    )
                )
            continue

        proj_files = {p.name: p for p in proj_dir.glob("*.md") if p.is_file()}
        bund_files = {p.name: p for p in bund_dir.glob("*.md") if p.is_file()}

        # Missing or drifting bundle copies.
        for name, src in proj_files.items():
            tgt = bund_files.get(name)
            if tgt is None:
                drift.append(
                    (
                        src.relative_to(repo_root).as_posix(),
                        f"{bund_rel}/{name}",
                        "missing_target",
                    )
                )
                continue
            if _hash_file(src) != _hash_file(tgt):
                drift.append(
                    (
                        src.relative_to(repo_root).as_posix(),
                        tgt.relative_to(repo_root).as_posix(),
                        "drift",
                    )
                )
        # Orphan bundle copies (in bundle, not in project — should be
        # deleted to maintain SSoT discipline).
        for name in bund_files:
            if name not in proj_files:
                drift.append(
                    (
                        f"{proj_rel}/{name}",  # phantom source
                        bund_files[name].relative_to(repo_root).as_posix(),
                        "orphan_target",
                    )
                )
    return drift


def _apply_sync(repo_root: Path) -> tuple[int, int, int]:
    """Idempotent sync. Returns (copied, removed, ok_count)."""
    copied = 0
    removed = 0
    ok = 0
    for proj_rel, bund_rel in _MIRROR_PAIRS:
        proj_dir = repo_root / proj_rel
        bund_dir = repo_root / bund_rel
        if not proj_dir.is_dir():
            continue
        bund_dir.mkdir(parents=True, exist_ok=True)

        proj_files = {p.name: p for p in proj_dir.glob("*.md") if p.is_file()}
        bund_files = {p.name: p for p in bund_dir.glob("*.md") if p.is_file()}

        # Copy project → bundle for missing or divergent.
        for name, src in proj_files.items():
            tgt = bund_dir / name
            if tgt.exists() and _hash_file(src) == _hash_file(tgt):
                ok += 1
                continue
            shutil.copy2(src, tgt)
            copied += 1

        # Remove orphan bundle copies (not in project source).
        for name, tgt in bund_files.items():
            if name not in proj_files:
                tgt.unlink()
                removed += 1

    return copied, removed, ok


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="sync_plugin_mirrors",
        description=(
            "Idempotent sync of v0.6.11 plugin mirror pairs. "
            ".claude/{agents,commands}/X.md is the SSoT; "
            "<repo>/{agents,commands}/X.md is the bundle-scope mirror."
        ),
    )
    p.add_argument(
        "--check",
        action="store_true",
        help="Detect drift without mutating; exit 1 if any drift.",
    )
    p.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Override the repo root (default: parent of this script's dir).",
    )
    args = p.parse_args(argv)

    repo_root: Path = args.repo_root
    # v0.8.4 root-cleanup (2026-05-12): canon may be at .myco/canon.yaml
    # (Myco-self / v0.8.4+) or _canon.yaml (legacy / downstream).
    if not (
        (repo_root / ".myco" / "canon.yaml").is_file()
        or (repo_root / "_canon.yaml").is_file()
    ):
        print(
            f"error: not a Myco substrate root "
            f"(no .myco/canon.yaml or _canon.yaml): {repo_root}",
            file=sys.stderr,
        )
        return 2

    drift = _detect_drift(repo_root)

    if args.check:
        if not drift:
            print("[sync_plugin_mirrors] OK — all mirror pairs in sync")
            return 0
        print(f"[sync_plugin_mirrors] DRIFT detected ({len(drift)} entries):")
        for src, tgt, kind in drift:
            print(f"  {kind}: {src} ↔ {tgt}")
        print(
            "Run without --check to apply (project-scope is the SSoT).",
            file=sys.stderr,
        )
        return 1

    # Apply mode.
    if not drift:
        print("[sync_plugin_mirrors] OK — already in sync")
        return 0
    copied, removed, ok = _apply_sync(repo_root)
    print(
        f"[sync_plugin_mirrors] OK — synced ("
        f"{copied} copied, {removed} removed, {ok} unchanged)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
