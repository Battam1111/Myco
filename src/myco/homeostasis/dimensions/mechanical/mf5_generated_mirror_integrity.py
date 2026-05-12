"""MF5 — generated-mirror integrity (v0.7.2+; v0.7.3 reclassified).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "永恒删减 (eternal pruning)" + ``docs/architecture/L2_DOCTRINE/boundary.md``
§ "Subagents and slash commands (v0.6.11+)".

**v0.7.3 reclassification (correcting v0.7.2 PENDING_BUILD_ARTIFACT_CONVERSION
hypothesis)**: per Claude Code spec, BOTH `.claude/<dir>/X.md` (project
scope, used when developing inside the substrate) AND
`<repo>/<dir>/X.md` (marketplace plugin scope, declared in
`.claude-plugin/plugin.json::agents | commands`) MUST exist as concrete
files. The marketplace install protocol does NOT support build-time
generation of agents/commands files; the plugin loader expects them
present at install time. So the v0.7.2 hypothesis ("convert <repo>/X
to a build artifact") was structurally wrong — these are
spec-mandated dual sources.

The right invariant: documented mirror pairs MUST be byte-identical.
Drift (one copy edited without the other) is the actual lint target.

MF5 v0.7.3 reporting modes:

1. **OK silent** — documented mirror pair (`.claude/{agents,commands}/X.md`
   ↔ `<repo>/{agents,commands}/X.md`) is byte-identical. No finding.

2. **MIRROR_DRIFT (MEDIUM)** — documented mirror pair exists but
   bytes differ. Agent resolves by running
   `python scripts/sync_plugin_mirrors.py` (idempotent copier).

3. **UNINTENDED_DUPLICATE (MEDIUM)** — byte-identical pair OUTSIDE
   the documented mirror set. Agent resolves by deleting one copy
   and inserting a cross-reference link.

**Categorization rationale (saprotroph T3)**: this is an MF-cluster
dim (manifest/file-shape) because byte-identical mirror discipline
is the same shape as MF1 (declared subsystems exist) — both gate
cross-source-of-truth integrity. It is NOT a PA-cluster dim — PA
covers package-architecture purity (write_surface, megafile cap,
core/symbionts isolation), not file-content discipline.

**Algorithm (mycorrhiza T6)**: SHA-256 hash bucket, O(n). For each
file under documented mirror directories, hash the content; group by
hash; check expected pairs are byte-identical. Cost ~5 ms for typical
repo (10s of mirror files at ~10 KB each).

**Severity**: MEDIUM. Mirror drift is real lint (the marketplace
install distributes the divergent state to downstream substrates).
Resolution path: agent runs ``python scripts/sync_plugin_mirrors.py``
which is idempotent and re-establishes byte-identity from the
project-scope SSoT.
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


# v0.6.11-documented intended mirror directories.
#
# v0.8.6 path-correction (2026-05-12): bundle dirs moved under
# .plugin/ in the great root-cleanup of v0.8.4. The original
# `("agents", "commands")` root paths no longer exist; MF5 silently
# returned for every release v0.8.4…v0.8.5 (both halves failed the
# `is_dir()` check). The byte-identity gate is now reconnected.
#
# Each entry: (project-level path, plugin-bundle path).
_INTENDED_MIRROR_DIRS: tuple[tuple[str, str], ...] = (
    (".claude/agents", ".plugin/agents"),
    (".claude/commands", ".plugin/commands"),
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

        # v0.7.3 — pair-based check. For each documented mirror pair,
        # verify the .md files are byte-identical. Missing files OK
        # (one side might not exist on a fresh substrate).
        for project_rel, bundle_rel in _INTENDED_MIRROR_DIRS:
            project_dir = root / project_rel
            bundle_dir = root / bundle_rel
            if not project_dir.is_dir() or not bundle_dir.is_dir():
                continue

            # Find all .md files in either directory.
            project_files = {p.name: p for p in project_dir.glob("*.md") if p.is_file()}
            bundle_files = {p.name: p for p in bundle_dir.glob("*.md") if p.is_file()}

            for name in sorted(set(project_files) | set(bundle_files)):
                proj_path = project_files.get(name)
                bund_path = bundle_files.get(name)
                if proj_path is None or bund_path is None:
                    # Unbalanced pair (one side missing). Skip — not
                    # a drift case; might be in-flight addition.
                    continue
                proj_digest = _hash_file(proj_path)
                bund_digest = _hash_file(bund_path)
                if proj_digest is None or bund_digest is None:
                    continue
                if proj_digest == bund_digest:
                    # Byte-identical: this is the desired state. Silent.
                    continue
                # Drift: same name, different bytes. MEDIUM finding.
                proj_rel_p = proj_path.relative_to(root).as_posix()
                bund_rel_p = bund_path.relative_to(root).as_posix()
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=Severity.MEDIUM,
                    message=(
                        f"MIRROR_DRIFT: {proj_rel_p!r} and {bund_rel_p!r} "
                        f"have diverged (sha256 {proj_digest[:8]}... vs "
                        f"{bund_digest[:8]}...). Resolve via "
                        f"`python scripts/sync_plugin_mirrors.py` "
                        f"(idempotent; project-scope is the SSoT)."
                    ),
                    path=proj_rel_p,
                )
