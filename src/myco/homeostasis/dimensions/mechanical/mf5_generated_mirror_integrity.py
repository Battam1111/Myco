"""MF5 — generated-mirror integrity (v0.7.2 → v0.8.8 simplification).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "永恒删减 (eternal pruning)" + ``docs/architecture/L2_DOCTRINE/boundary.md``
§ "Subagents and slash commands".

**v0.8.8 simplification (correcting v0.7.3 over-engineering)**: the
v0.7.3 craft argued for **byte-identical dual sources** at
`.claude/{agents,commands}/X.md` (project scope) AND
`<repo>/{agents,commands}/X.md` (plugin-bundle scope), on the
premise that "Claude Code spec requires both paths". Re-reading the
official docs (https://code.claude.com/docs/en/plugins § "Convert
existing configurations to plugins") refutes that premise — the
docs explicitly say:

    "After migrating, you can remove the original files from `.claude/`
    to avoid duplicates. The plugin version will take precedence when
    loaded."

The v0.7.3 craft's "MUST exist as concrete files" claim was an
inference, not a doc quote. v0.8.8 acts on the doc's actual guidance:
**single source of truth**. ``plugin.json`` now references
``./.claude/agents/`` and ``./.claude/commands/`` directly; the
``.plugin/agents/`` and ``.plugin/commands/`` mirror directories
have been deleted; ``sync_plugin_mirrors.py`` has been excreted
(no mirror = nothing to sync).

MF5 is retained as a **drift detector for unintended duplicates**:
if a future change resurrects a mirror copy under any path, MF5
fires a MEDIUM finding pointing at the byte-identical pair so the
duplicate can be reconciled. Both halves of the previous "intended
mirror pair" set are gone; the dim now actively guards against
*re-introducing* a mirror.

**Severity**: MEDIUM. Unintended file duplication (same content
under two paths the substrate doesn't model as a mirror) leads to
drift-by-divergent-edit; MF5 catches it before the drift lands.

**Algorithm**: SHA-256 hash bucket over the standalone-scope dirs.
Two files with identical bytes in different directories trigger a
finding.
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


# v0.8.8 — directories under which a byte-identical duplicate would
# indicate accidental mirror resurrection. Pairs of (canonical_scope,
# forbidden_duplicate_scope). MF5 fires when a file with identical
# bytes appears in BOTH paths.
_FORBIDDEN_DUPLICATE_PAIRS: tuple[tuple[str, str], ...] = (
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
    """Detect accidental byte-identical duplicates under retired mirror paths."""

    id = "MF5"
    category = Category.MECHANICAL
    default_severity = Severity.LOW
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        root = ctx.substrate.root

        # v0.8.8 — if a forbidden duplicate path exists at all, every
        # file under it is a candidate. Canonical-scope content stays
        # silent (it's the single source of truth); duplicates trigger
        # the dim.
        for canon_rel, forbidden_rel in _FORBIDDEN_DUPLICATE_PAIRS:
            forbidden_dir = root / forbidden_rel
            canon_dir = root / canon_rel
            if not forbidden_dir.is_dir():
                # Forbidden path is absent — the desired state.
                continue
            if not canon_dir.is_dir():
                # Canonical source missing entirely is a separate
                # invariant problem; MF5 doesn't claim that surface.
                continue

            canon_files = {p.name: p for p in canon_dir.glob("*.md") if p.is_file()}
            forbidden_files = {
                p.name: p for p in forbidden_dir.glob("*.md") if p.is_file()
            }

            for name in sorted(forbidden_files):
                fpath = forbidden_files[name]
                cpath = canon_files.get(name)
                f_digest = _hash_file(fpath)
                if f_digest is None:
                    continue
                c_digest = _hash_file(cpath) if cpath is not None else None
                f_rel = fpath.relative_to(root).as_posix()
                c_rel = (
                    cpath.relative_to(root).as_posix() if cpath is not None else None
                )
                if c_digest is None:
                    # Only the forbidden copy exists. Still
                    # surface — the file lives at the retired path.
                    yield Finding(
                        dimension_id=self.id,
                        category=self.category,
                        severity=Severity.MEDIUM,
                        message=(
                            f"MIRROR_RESURRECTED: {f_rel!r} lives at the "
                            f"retired mirror path. The v0.8.8 doctrine "
                            f"named {canon_rel!r} as the single source of "
                            f"truth — move the file there and remove "
                            f"{forbidden_rel!r}."
                        ),
                        path=f_rel,
                    )
                    continue
                if c_digest == f_digest:
                    yield Finding(
                        dimension_id=self.id,
                        category=self.category,
                        severity=Severity.MEDIUM,
                        message=(
                            f"UNINTENDED_DUPLICATE: {f_rel!r} is byte-"
                            f"identical to {c_rel!r}. The v0.8.8 doctrine "
                            f"retired the {forbidden_rel!r} mirror — "
                            f"plugin.json now references "
                            f"{canon_rel!r} directly. Delete the "
                            f"duplicate at {f_rel!r}."
                        ),
                        path=f_rel,
                    )
                else:
                    yield Finding(
                        dimension_id=self.id,
                        category=self.category,
                        severity=Severity.MEDIUM,
                        message=(
                            f"MIRROR_DRIFT: {c_rel!r} and {f_rel!r} have "
                            f"diverged (sha256 {c_digest[:8]}... vs "
                            f"{f_digest[:8]}...). The {forbidden_rel!r} "
                            f"mirror was retired at v0.8.8; this file "
                            f"is stale doctrine. Delete {f_rel!r} to "
                            f"restore the single-source-of-truth state."
                        ),
                        path=f_rel,
                    )
