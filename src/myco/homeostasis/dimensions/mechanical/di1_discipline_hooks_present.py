"""DI1 — discipline-enforcement hooks are declared.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration" (v0.5.8 addition).


R1-R7 are enforced in Claude Code / Cowork via the ``.claude/
hooks.json`` mechanism. Other MCP hosts carry the discipline via
the MCP ``initialization`` block that :mod:`myco.boundary.surface.mcp`
emits. DI1 confirms that — for substrates that ship with a
Claude-family host declaration — the hooks file is present and
points at a real handler.

Scope: the dimension fires only when the substrate root contains
a ``.claude/`` directory (indicating the operator has adopted the
Claude-family flow). On substrates without ``.claude/``, DI1 is a
silent no-op — the host is presumably relying on MCP
initialization alone, which is a supported configuration.

Severity: MEDIUM. A missing hooks file on a ``.claude/``-present
substrate is a real discipline-regression risk: R1 won't auto-
trigger, and the session must rely on the agent's vigilance. But
it isn't a kernel-level contract break, so we stop at MEDIUM.

Fixable: v0.6.0 §F18. NARROW: only when ``.claude/hooks.json`` is
COMPLETELY ABSENT — fix writes a minimal R1+R2 hooks template.
Existing files are never overwritten (preserves operator
customization per pre-v0.6.0 reasoning).
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any, ClassVar

from myco.core.context import MycoContext
from myco.core.io_atomic import atomic_utf8_write
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["DI1DisciplineHooksPresent"]


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
