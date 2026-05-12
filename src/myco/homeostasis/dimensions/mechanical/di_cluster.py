"""DI-cluster — merged dimensions (DI1, DI2).

v0.8.8 merged: this file consolidates the per-dim files that previously
lived as one file per dimension under ``homeostasis/dimensions/mechanical/``.
Class names and behaviour are byte-equivalent — only file locations
changed. Per L1 protocol.md: L3 organization choices are ordinary
code changes; no contract bump required. Original per-dim files are
preserved in git history at parent commits.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration".
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any, ClassVar

from myco.core.identity_cluster import MycoContext, Severity
from myco.core.io_cluster import atomic_utf8_write
from myco.homeostasis.primitives_cluster import Category, Dimension, Finding

__all__ = [
    "DI1DisciplineHooksPresent",
    "DI2DisciplineHooksContent",
]


# =========================================================================
# DI1 — see module docstring + original git history at parent commits
# =========================================================================

_MINIMAL_HOOKS = {
    "hooks": {
        "SessionStart": [
            {
                "command": 'python -m myco --json --project-dir "$CLAUDE_PROJECT_DIR" hunger'
            }
        ],
        "PreCompact": [
            {
                "command": 'python -m myco --json --project-dir "$CLAUDE_PROJECT_DIR" senesce'
            }
        ],
        "SessionEnd": [
            {
                "command": 'python -m myco --json --project-dir "$CLAUDE_PROJECT_DIR" senesce --quick'
            }
        ],
    }
}


class DI1DisciplineHooksPresent(Dimension):
    """``.claude/hooks.json`` present when a ``.claude/`` directory is present."""

    id = "DI1"
    category = Category.MECHANICAL
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = True

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        claude_dir = ctx.substrate.root / ".claude"
        if not claude_dir.is_dir():
            # No Claude-family host declared; silent no-op.
            return
        # hooks.json or settings.json with a ``hooks`` key — either is
        # accepted. We prefer hooks.json because it is the canonical
        # shape ``myco install claude-code`` writes.
        hooks_path = claude_dir / "hooks.json"
        settings_path = claude_dir / "settings.json"
        if hooks_path.is_file():
            return
        if settings_path.is_file():
            try:
                text = settings_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                text = ""
            if '"hooks"' in text:
                return
        yield Finding(
            dimension_id=self.id,
            category=self.category,
            severity=self.default_severity,
            message=(
                ".claude/hooks.json (or settings.json with a 'hooks' "
                "key) is missing; R1-R7 auto-triggering relies on "
                "this. Re-run `myco install claude-code` to restore."
            ),
            path=".claude",
        )

    def fix(self, ctx: MycoContext, finding: Finding) -> dict[str, Any]:
        """Write minimal hooks.json template.

        NARROW: only when ``.claude/hooks.json`` is COMPLETELY ABSENT
        and ``.claude/settings.json`` does NOT carry a 'hooks' key.
        Existing files are never overwritten.
        """
        claude_dir = ctx.substrate.root / ".claude"
        if not claude_dir.is_dir():
            return {"applied": False, "detail": ".claude/ not present"}
        hooks_path = claude_dir / "hooks.json"
        if hooks_path.is_file():
            return {"applied": False, "detail": "hooks.json already present"}
        settings_path = claude_dir / "settings.json"
        if settings_path.is_file():
            try:
                if '"hooks"' in settings_path.read_text(encoding="utf-8"):
                    return {
                        "applied": False,
                        "detail": "settings.json carries hooks key",
                    }
            except (OSError, UnicodeDecodeError):
                pass
        body = json.dumps(_MINIMAL_HOOKS, indent=2) + "\n"
        atomic_utf8_write(hooks_path, body)
        return {
            "applied": True,
            "detail": f"created {hooks_path.name} ({len(body)} bytes)",
        }


# =========================================================================
# DI2 — see module docstring + original git history at parent commits
# =========================================================================


class DI2DisciplineHooksContent(Dimension):
    """hooks.json must include SessionStart→hunger and PreCompact→senesce lines."""

    id = "DI2"
    category = Category.MECHANICAL
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        root = ctx.substrate.root
        # v0.8.6 path-correction: the Cowork bundle moved under .plugin/
        # at v0.8.4 (root cleanup). The original `hooks/hooks.json` at
        # substrate root has not existed since v0.8.4; DI2 silently
        # no-op'd for v0.8.4…v0.8.5. Real binding is declared in
        # `.claude-plugin/plugin.json::hooks` → `./.plugin/hooks/hooks.json`.
        hooks_path = root / ".plugin" / "hooks" / "hooks.json"
        if not hooks_path.is_file():
            return
        try:
            data = json.loads(hooks_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=f"hooks.json failed to parse: {exc}",
                path=".plugin/hooks/hooks.json",
            )
            return
        text = json.dumps(data) if isinstance(data, dict | list) else str(data)
        # R1: SessionStart fires hunger.
        if "SessionStart" not in text or "hunger" not in text:
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    "hooks.json does not bind SessionStart → myco hunger "
                    "(R1 boot ritual)"
                ),
                path=".plugin/hooks/hooks.json",
            )
        # R2: PreCompact fires senesce.
        if "PreCompact" not in text or "senesce" not in text:
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    "hooks.json does not bind PreCompact → myco senesce "
                    "(R2 session-end ritual)"
                ),
                path=".plugin/hooks/hooks.json",
            )
