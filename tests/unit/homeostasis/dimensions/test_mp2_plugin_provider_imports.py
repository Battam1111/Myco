"""Tests for ``MP2PluginProviderImports``."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimensions.mp2_plugin_provider_imports import (
    MP2PluginProviderImports,
)


def test_no_plugins_dir_silent(seeded_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(MP2PluginProviderImports().run(ctx)) == []


def test_clean_plugins_no_findings(seeded_substrate: Path) -> None:
    plugins = seeded_substrate / ".myco" / "plugins"
    plugins.mkdir(parents=True)
    (plugins / "__init__.py").write_text("", encoding="utf-8")
    (plugins / "clean.py").write_text(
        "from pathlib import Path\n# local, fine\n", encoding="utf-8"
    )
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(MP2PluginProviderImports().run(ctx)) == []


def test_flags_plugin_importing_openai(seeded_substrate: Path) -> None:
    plugins = seeded_substrate / ".myco" / "plugins"
    plugins.mkdir(parents=True)
    (plugins / "bad.py").write_text("import openai\n", encoding="utf-8")
    ctx = MycoContext.for_testing(root=seeded_substrate)
    findings = list(MP2PluginProviderImports().run(ctx))
    assert len(findings) == 1
    assert findings[0].severity is Severity.MEDIUM
    assert "openai" in findings[0].message


def test_downgrades_when_substrate_opts_out(seeded_substrate: Path) -> None:
    plugins = seeded_substrate / ".myco" / "plugins"
    plugins.mkdir(parents=True)
    (plugins / "bad.py").write_text("import anthropic\n", encoding="utf-8")
    ctx = MycoContext.for_testing(root=seeded_substrate)
    # ``Canon`` is a frozen dataclass; bypass the frozen check via
    # ``object.__setattr__`` to simulate the opt-out without editing
    # the YAML on disk.
    object.__setattr__(ctx.substrate.canon, "system", {"no_llm_in_substrate": False})
    findings = list(MP2PluginProviderImports().run(ctx))
    assert len(findings) == 1
    assert findings[0].severity is Severity.LOW
