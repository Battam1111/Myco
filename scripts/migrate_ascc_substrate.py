"""Migrate an ASCC (or any v0.3.x) substrate's ``_canon.yaml`` to
the v0.4.0 schema.

Usage::

    python scripts/migrate_ascc_substrate.py <path-to-old-canon.yaml>
    python scripts/migrate_ascc_substrate.py <path> --execute

Default is **dry-run**: the proposed v0.4.0 canon is printed to stdout
and NOT written. ``--execute`` writes the proposal to
``<source-dir>/_canon.yaml.v0_4_0_proposal.yaml`` beside the original,
leaving the original file untouched.

The script does **not** mutate the source substrate. Per L3
migration_strategy §9 E2 ("fresh re-export"), the operator reviews the
proposal, moves it into place manually, and handles any lost fields
by reading the mapping table printed at the end of the migration
report. This script's job is to do the mechanical translation; the
operator does the semantic judgement.

Exit codes:

* 0 — proposal produced cleanly.
* 1 — source canon read/parse error or unexpected schema shape
      (the script refuses to guess).
* 2 — ``--execute`` was passed but the target proposal file already
      exists (caller must resolve).
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

# Legacy keys that have no v0.4.0 analogue. Surfacing these so the
# operator knows what was dropped.
_DROPPED_LEGACY_KEYS = (
    "system.boot_brief",
    "system.boot_reflex",
    "system.session_end",
    "system.self_correction",
    "system.principles_count",
    "system.principles_label",
    "adapters",
    "package",  # replaced by top-level versioning block
)

# Default write-surface allow-list for a generic ASCC-style research
# substrate. Callers can edit after proposal.
_ASCC_DEFAULT_WRITE_SURFACE = (
    "_canon.yaml",
    "MYCO.md",
    "CLAUDE.md",
    "CHANGELOG.md",
    "README.md",
    "pyproject.toml",
    "notes/**",
    "docs/**",
    "src/**",
    "tests/**",
    "scripts/**",
    "research/**",
    "paper/**",
    ".claude/**",
)

# v0.4.0 lint-dimension inventory — mirrors the B.8 registry so a
# migrated substrate can run `myco immune` out of the box.
_V0_4_0_DIMENSIONS = {
    "M1": "mechanical",
    "M2": "mechanical",
    "M3": "mechanical",
    "SH1": "shipped",
    "MB1": "metabolic",
    "MB2": "metabolic",
    "SE1": "semantic",
    "SE2": "semantic",
}


def _require_mapping(node: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(node, dict):
        raise SystemExit(
            f"migrate: expected a mapping at {label!r}, got {type(node).__name__}"
        )
    return node


def _load_legacy_canon(path: Path) -> Mapping[str, Any]:
    if not path.is_file():
        raise SystemExit(f"migrate: source canon not found: {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise SystemExit(f"migrate: YAML parse error in {path}: {exc}") from exc
    return _require_mapping(raw, path.name)


def _derive_substrate_id(legacy: Mapping[str, Any], fallback: str) -> str:
    project = legacy.get("project") or {}
    if isinstance(project, dict):
        pid = project.get("id") or project.get("name")
        if isinstance(pid, str) and pid.strip():
            return pid.strip().lower().replace(" ", "-")
    pkg = legacy.get("package") or {}
    if isinstance(pkg, dict):
        name = pkg.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip().lower().replace(" ", "-")
    return fallback


def _derive_tags(legacy: Mapping[str, Any]) -> list[str]:
    project = legacy.get("project") or {}
    if isinstance(project, dict):
        tags = project.get("tags")
        if isinstance(tags, list):
            return [str(t) for t in tags if isinstance(t, (str, int))]
    return ["migrated-from-v0_3"]


def _derive_entry_point(legacy: Mapping[str, Any]) -> str:
    system = legacy.get("system") or {}
    if isinstance(system, dict):
        ep = system.get("entry_point")
        if isinstance(ep, str) and ep.strip():
            return ep
    return "MYCO.md"


def _derive_package_version_ref(legacy: Mapping[str, Any]) -> str | None:
    pkg = legacy.get("package") or {}
    if isinstance(pkg, dict):
        ref = pkg.get("version_ref") or pkg.get("path")
        if isinstance(ref, str) and ref.strip():
            return ref
    return None


def build_v0_4_0_canon(
    legacy: Mapping[str, Any], *, fallback_id: str
) -> dict[str, Any]:
    """Produce the v0.4.0 canon dict from a parsed v0.3.x canon."""
    substrate_id = _derive_substrate_id(legacy, fallback_id)
    tags = _derive_tags(legacy)
    entry_point = _derive_entry_point(legacy)
    pkg_ref = _derive_package_version_ref(legacy)

    canon: dict[str, Any] = {
        "schema_version": "1",
        "contract_version": "v0.4.0",
        "synced_contract_version": "v0.4.0",
        "identity": {
            "substrate_id": substrate_id,
            "tags": tags,
            "entry_point": entry_point,
        },
        "system": {
            "write_surface": {"allowed": list(_ASCC_DEFAULT_WRITE_SURFACE)},
            "hard_contract": {
                "rules_ref": "docs/architecture/L1_CONTRACT/protocol.md",
                "rule_count": 7,
            },
        },
        "versioning": {
            "package_version_ref": pkg_ref or "src/myco/__init__.py",
            "pyproject_dynamic": True,
        },
        "lint": {
            "categories": ["mechanical", "shipped", "metabolic", "semantic"],
            "dimensions": dict(_V0_4_0_DIMENSIONS),
            "exit_policy": {
                "default": (
                    "mechanical:critical,shipped:critical,"
                    "metabolic:never,semantic:never"
                ),
            },
            "skeleton_downgrade": {
                "marker": ".myco_state/autoseeded.txt",
                "affected_dimensions": [],
            },
        },
        "subsystems": {
            "genesis": {
                "doc": "docs/architecture/L2_DOCTRINE/genesis.md",
                "package": "src/myco/genesis/",
            },
            "ingestion": {
                "doc": "docs/architecture/L2_DOCTRINE/ingestion.md",
                "package": "src/myco/ingestion/",
            },
            "digestion": {
                "doc": "docs/architecture/L2_DOCTRINE/digestion.md",
                "package": "src/myco/digestion/",
            },
            "circulation": {
                "doc": "docs/architecture/L2_DOCTRINE/circulation.md",
                "package": "src/myco/circulation/",
            },
            "homeostasis": {
                "doc": "docs/architecture/L2_DOCTRINE/homeostasis.md",
                "package": "src/myco/homeostasis/",
            },
        },
        "commands": {
            "manifest_ref": "src/myco/surface/manifest.yaml",
        },
        "metrics": {"test_count": 0},
        "waves": {"current": 1, "log_ref": "docs/contract_changelog.md"},
    }
    return canon


def _render_report(
    *,
    source: Path,
    proposal: Mapping[str, Any],
    target: Path | None,
    executed: bool,
) -> str:
    lines: list[str] = [
        "# ASCC → v0.4.0 migration report",
        f"# source:   {source}",
        f"# target:   {target or '(dry-run; stdout only)'}",
        f"# executed: {executed}",
        "#",
        "# Dropped legacy keys (no v0.4.0 analogue):",
    ]
    for key in _DROPPED_LEGACY_KEYS:
        lines.append(f"#   - {key}")
    lines.append("#")
    lines.append("# Operator checklist before accepting:")
    lines.append("#   1. Review identity.substrate_id and tags.")
    lines.append("#   2. Review system.write_surface.allowed for this repo.")
    lines.append("#   3. Confirm versioning.package_version_ref resolves.")
    lines.append("#   4. Run `myco --json immune --exit-on never` and")
    lines.append("#      triage every finding.")
    lines.append("")
    yaml_text = yaml.safe_dump(
        proposal, sort_keys=False, default_flow_style=False, width=80
    )
    return "\n".join(lines) + "\n" + yaml_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="migrate_ascc_substrate",
        description=(
            "Propose a v0.4.0 `_canon.yaml` from an ASCC-style v0.3.x canon. "
            "Default is dry-run (stdout only). `--execute` writes the "
            "proposal beside the source without touching the original."
        ),
    )
    parser.add_argument(
        "source",
        type=Path,
        help="Path to the existing v0.3.x `_canon.yaml`.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help=(
            "Write the proposal to "
            "<source-dir>/_canon.yaml.v0_4_0_proposal.yaml. "
            "Refuses to overwrite an existing proposal file."
        ),
    )
    parser.add_argument(
        "--fallback-id",
        default="migrated-substrate",
        help=(
            "substrate_id to use when the source canon has no "
            "project.id / package.name (default: %(default)r)."
        ),
    )
    args = parser.parse_args(argv)

    legacy = _load_legacy_canon(args.source)
    proposal = build_v0_4_0_canon(legacy, fallback_id=args.fallback_id)

    target = args.source.parent / "_canon.yaml.v0_4_0_proposal.yaml"
    if args.execute:
        if target.exists():
            print(
                f"migrate: proposal already exists at {target}; "
                "refusing to overwrite. Remove it or pass a different dir.",
                file=sys.stderr,
            )
            return 2
        target.write_text(
            _render_report(
                source=args.source,
                proposal=proposal,
                target=target,
                executed=True,
            ),
            encoding="utf-8",
        )
        print(f"migrate: proposal written to {target}")
        return 0

    sys.stdout.write(
        _render_report(
            source=args.source,
            proposal=proposal,
            target=None,
            executed=False,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
