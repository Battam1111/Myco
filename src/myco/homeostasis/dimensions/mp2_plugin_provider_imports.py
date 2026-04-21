"""MP2 — substrate-local plugins import no LLM provider SDK.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration" (v0.5.8 addition; companion to MP1).


Companion to :class:`MP1NoProviderImports`. MP1 scans the kernel
(``src/myco/**/*.py``); MP2 scans the substrate-local plugin tree
(``.myco/plugins/**/*.py``). The doctrine that motivates MP1 — L0
principle 1, "agents call LLMs; the substrate does not" — applies
equally to substrate-local plugins. A third-party dimension or
adapter that sneaks an ``import openai`` into the plugin tree
violates the same boundary, just on a different axis.

v0.5.8 (Lens 11 P1-MP-plug): the MP1 audit revealed that ``.myco/
plugins/`` was unscanned. ``myco ramify`` users who wrote a
well-intentioned adapter that pulled a provider SDK for preview
rendering had no mechanical signal that the act crossed the
boundary. MP2 closes that gap.

Severity:

- canon ``system.no_llm_in_substrate: true`` (default) + hit →
  MEDIUM (plugins have more latitude than the kernel; still a
  boundary crossing, but not a kernel-purity breach).
- canon ``system.no_llm_in_substrate: false`` + hit →
  LOW (substrate opted out; MP2 still reports so the agent sees
  the boundary is off).

Fixable: False. Removing an import changes surrounding semantics;
MP2 detects only.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity

from ..dimension import Dimension
from ..finding import Category, Finding
from .mp1_no_provider_imports import MP1NoProviderImports

__all__ = ["MP2PluginProviderImports"]


class MP2PluginProviderImports(Dimension):
    """Substrate-local plugins under ``.myco/plugins/`` import no LLM SDK."""

    id = "MP2"
    category = Category.MECHANICAL
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = False

    #: Reuse the MP1 blacklist verbatim — whatever the kernel isn't
    #: allowed to import, a plugin isn't allowed to import either.
    BLACKLIST: ClassVar[frozenset[str]] = MP1NoProviderImports.BLACKLIST

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        plugins_dir = ctx.substrate.root / ".myco" / "plugins"
        if not plugins_dir.is_dir():
            return
        system = ctx.substrate.canon.system or {}
        declared_no_llm = bool(system.get("no_llm_in_substrate", True))
        severity = Severity.MEDIUM if declared_no_llm else Severity.LOW
        for py_file in sorted(plugins_dir.rglob("*.py")):
            if self._should_skip(py_file):
                continue
            for rel_path, line, imported in self._scan_file(py_file, ctx):
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=severity,
                    message=(
                        f"plugin file imports LLM provider SDK "
                        f"{imported!r} (L0 principle 1: agents call "
                        f"LLMs; the substrate — including its plugins "
                        f"— does not)."
                    ),
                    path=rel_path,
                    line=line,
                )

    @staticmethod
    def _should_skip(py_file: Path) -> bool:
        for part in py_file.parts:
            if part == "__pycache__":
                return True
            # Allow ``.myco`` itself; only reject other hidden dirs.
            if part.startswith(".") and part not in {".", "..", ".myco"}:
                return True
        return False

    def _scan_file(
        self, py_file: Path, ctx: MycoContext
    ) -> Iterable[tuple[str, int, str]]:
        try:
            source = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return
        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            return
        try:
            rel_path = py_file.relative_to(ctx.substrate.root).as_posix()
        except ValueError:
            rel_path = py_file.as_posix()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if MP1NoProviderImports._matches_blacklist(alias.name):
                        yield (rel_path, node.lineno, alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    continue
                mod = node.module
                if mod is None:
                    continue
                if MP1NoProviderImports._matches_blacklist(mod):
                    yield (rel_path, node.lineno, mod)
