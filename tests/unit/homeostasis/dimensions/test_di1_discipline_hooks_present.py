"""Tests for ``DI1DisciplineHooksPresent``."""

from __future__ import annotations

import json
from pathlib import Path

from myco.core.context import MycoContext
from myco.homeostasis.dimensions.di1_discipline_hooks_present import (
    DI1DisciplineHooksPresent,
)


def test_no_claude_dir_silent(seeded_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(DI1DisciplineHooksPresent().run(ctx)) == []


def test_hooks_json_present_clean(seeded_substrate: Path) -> None:
    claude = seeded_substrate / ".claude"
    claude.mkdir()
    (claude / "hooks.json").write_text("{}", encoding="utf-8")
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(DI1DisciplineHooksPresent().run(ctx)) == []


def test_settings_with_hooks_key_clean(seeded_substrate: Path) -> None:
    claude = seeded_substrate / ".claude"
    claude.mkdir()
    (claude / "settings.json").write_text(json.dumps({"hooks": {}}), encoding="utf-8")
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(DI1DisciplineHooksPresent().run(ctx)) == []


def test_claude_dir_without_hooks_fires(seeded_substrate: Path) -> None:
    claude = seeded_substrate / ".claude"
    claude.mkdir()
    (claude / "README.md").write_text("nothing useful", encoding="utf-8")
    ctx = MycoContext.for_testing(root=seeded_substrate)
    findings = list(DI1DisciplineHooksPresent().run(ctx))
    assert len(findings) == 1
    assert "hooks.json" in findings[0].message
