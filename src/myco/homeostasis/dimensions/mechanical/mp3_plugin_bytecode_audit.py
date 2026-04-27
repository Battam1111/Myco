"""MP3 — plugin bytecode/string-pattern LLM-SDK audit.

Governing doctrine: per craft ``v0_5_6_doctrine_realignment_craft_2026-04-17.md``
§MP1 / MP2-bytecode promise; v0.6.0 finally lands the deeper scan.

MP1 is import-name based (catches direct `import openai`); MP2 scans
plugin trees for the same. MP3 scans bytecode/string-literal patterns
for indirect SDK invocation (e.g. dynamic ``importlib.import_module``
of a provider name, or string-encoded module names that go through
``__import__``).

Severity: LOW at land, ramps to HIGH after 30 sessions.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.core.skip_dirs import should_skip_dir
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["MP3PluginBytecodeAudit"]

_SUSPICIOUS_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"importlib\.import_module\(\s*['\"](openai|anthropic|google\.generativeai|cohere|mistralai)"
    ),
    re.compile(
        r"__import__\(\s*['\"](openai|anthropic|google\.generativeai|cohere|mistralai)"
    ),
)


class MP3PluginBytecodeAudit(Dimension):
    """Plugin trees must not dynamically import LLM provider SDKs."""

    id = "MP3"
    category = Category.MECHANICAL
    default_severity = Severity.HIGH
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        plugin_root = ctx.substrate.root / ".myco" / "plugins"
        if not plugin_root.is_dir():
            return
        for path in plugin_root.rglob("*.py"):
            if any(should_skip_dir(p.name) for p in path.parents):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for pat in _SUSPICIOUS_PATTERNS:
                m = pat.search(text)
                if m:
                    rel = path.relative_to(ctx.substrate.root).as_posix()
                    yield Finding(
                        dimension_id=self.id,
                        category=self.category,
                        severity=self.default_severity,
                        message=(
                            f"plugin uses dynamic LLM-SDK import "
                            f"({m.group(0)[:60]}...); plugins must not "
                            f"call provider SDKs (L0 P1)"
                        ),
                        path=rel,
                    )
                    break
