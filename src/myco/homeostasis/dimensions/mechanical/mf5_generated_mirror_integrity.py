"""MF5 — generated-mirror integrity (v0.7.2+).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "永恒删减 (eternal pruning)" + ``docs/architecture/L2_DOCTRINE/boundary.md``
§ "Subagents and slash commands (v0.6.11+)".

The v0.6.11 craft documented `<repo>/agents/` and `<repo>/commands/`
as plugin-bundle-scope mirrors of `.claude/agents/` and
`.claude/commands/`, with the v0.6.12 IOU to extend
`scripts/build_plugin.py` to generate the mirrors at bundle-build
time. The IOU never landed; the mirrors are still hand-maintained
duplicate sources.

MF5 closes the loop: it walks the working tree, hashes every file by
SHA-256, and reports byte-identical pairs across documented mirror
directories. Two reporting modes:

1. **PENDING_BUILD_ARTIFACT_CONVERSION** (LOW): the v0.6.11-documented
   pairs (`.claude/{agents,commands}/X.md` ↔ `<repo>/{agents,commands}/X.md`)
   are reported as the v0.7.3 IOU. They are NOT redundancy — they are
   intended-but-not-yet-build-artifact'd mirrors.

2. **UNINTENDED_DRIFT** (MEDIUM): byte-identical pairs OUTSIDE the
   v0.6.11-documented mirror set. These are unplanned duplication
   (e.g. someone copied a doctrine page to two locations). The agent
   resolves by deleting one copy and inserting a cross-reference link.

**Categorization rationale (saprotroph T3)**: this is an MF-cluster
dim (manifest/file-shape) because byte-identical mirror discipline
is the same shape as MF1 (declared subsystems exist) — both gate
cross-source-of-truth integrity. It is NOT a PA-cluster dim — PA
covers package-architecture purity (write_surface, megafile cap,
core/symbionts isolation), not file-content discipline.

**Algorithm (mycorrhiza T6)**: SHA-256 hash bucket, O(n). For each
file under documented mirror directories, hash the content; group by
hash; report buckets with ≥ 2 entries. Cost ~5 ms for typical repo
(10s of mirror files at ~10 KB each).

**Severity ramp (mycorrhiza T5)**: LOW at v0.7.2 land — both reporting
modes start LOW so kernel CI doesn't explode on first immune run after
v0.7.2 ships (the v0.6.11 mirrors are tracked as PENDING_BUILD_ARTIFACT_CONVERSION
findings, not failures). Will promote to MEDIUM after v0.7.3 build-artifact
conversion lands (the conversion eliminates the LOW finding; only
unintended-drift cases remain at MEDIUM).
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from pathlib import Path
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["MF5GeneratedMirrorIntegrity"]


# v0.6.11-documented intended mirror directories. Files under these
# pairs are PENDING_BUILD_ARTIFACT_CONVERSION (LOW), not redundancy.
# Each entry: (project-level path under repo root, plugin-bundle path).
_INTENDED_MIRROR_DIRS: tuple[tuple[str, str], ...] = (
    (".claude/agents", "agents"),
    (".claude/commands", "commands"),
)


def _hash_file(path: Path) -> str | None:
    """SHA-256 hex digest of file content; None on read failure."""
    try:
        h = hashlib.sha256()
        with path.open("rb") as fp:
            for chunk in iter(lambda: fp.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


class MF5GeneratedMirrorIntegrity(Dimension):
    """Detect byte-identical pairs in documented mirror directories."""

    id = "MF5"
    category = Category.MECHANICAL
    default_severity = Severity.LOW
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        root = ctx.substrate.root

        for project_rel, bundle_rel in _INTENDED_MIRROR_DIRS:
            project_dir = root / project_rel
            bundle_dir = root / bundle_rel
            if not project_dir.is_dir() or not bundle_dir.is_dir():
                continue

            # Hash all .md files in both directories; bucket by digest.
            buckets: dict[str, list[str]] = {}
            for d in (project_dir, bundle_dir):
                for path in d.glob("*.md"):
                    if not path.is_file():
                        continue
                    digest = _hash_file(path)
                    if digest is None:
                        continue
                    rel = path.relative_to(root).as_posix()
                    buckets.setdefault(digest, []).append(rel)

            for _digest, paths in buckets.items():
                if len(paths) < 2:
                    continue
                # Documented mirror pair: at least one path in project_rel
                # AND at least one in bundle_rel.
                has_project = any(p.startswith(project_rel + "/") for p in paths)
                has_bundle = any(p.startswith(bundle_rel + "/") for p in paths)
                if has_project and has_bundle:
                    # Intended v0.6.11 mirror; PENDING_BUILD_ARTIFACT_CONVERSION (LOW).
                    yield Finding(
                        dimension_id=self.id,
                        category=self.category,
                        severity=Severity.LOW,
                        message=(
                            f"PENDING_BUILD_ARTIFACT_CONVERSION: "
                            f"v0.6.11 documented mirror pair byte-identical "
                            f"({sorted(paths)}); v0.7.3 IOU is to extend "
                            f"scripts/build_plugin.py to generate "
                            f"<repo>/{bundle_rel}/ at bundle-build time + "
                            f"gitignore the bundle path."
                        ),
                        path=paths[0],
                    )
                else:
                    # Unintended drift: byte-identical pair NOT in
                    # the v0.6.11 mirror contract.
                    yield Finding(
                        dimension_id=self.id,
                        category=self.category,
                        severity=Severity.MEDIUM,
                        message=(
                            f"UNINTENDED_DRIFT: byte-identical files "
                            f"{sorted(paths)}. Resolve by deleting one "
                            f"copy and inserting a cross-reference link."
                        ),
                        path=paths[0],
                    )
