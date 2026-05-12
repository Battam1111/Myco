"""Tests for ``di_cluster`` — merged per-dim test files (v0.8.8).

Per-dim test files consolidated to mirror the src/ cluster
merge. Each `# === <stem>` section corresponds to one original
per-dim test file; git history preserves the per-dim state.
"""

from __future__ import annotations

import json
from pathlib import Path

from myco.core.identity_cluster import MycoContext
from myco.homeostasis.dimensions.mechanical.di_cluster import (
    DI1DisciplineHooksPresent,
)

# =========================================================================
# test_di1_discipline_hooks_present — see git history for original per-dim file
# =========================================================================


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
