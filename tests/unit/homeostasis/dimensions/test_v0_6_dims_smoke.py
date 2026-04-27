"""Smoke tests for all 21 v0.6.0 lint dimensions.

Each dim's run() is invoked against a fresh genesis substrate. The
goal is coverage breadth, not behavioral depth — each dim should at
least execute its run() without raising, returning either an empty
generator (no findings) or yielding finding stubs the kernel can
list().
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from myco.core.context import MycoContext
from myco.homeostasis.dimensions.mechanical.ad1_adapter_silent_skip import (
    AD1AdapterSilentSkip,
)
from myco.homeostasis.dimensions.mechanical.cl1_sampling_policy_gate import (
    CL1SamplingPolicyGate,
)
from myco.homeostasis.dimensions.mechanical.cl2_oauth_token_residency import (
    CL2OAuthTokenResidency,
)
from myco.homeostasis.dimensions.mechanical.cl3_sampling_token_clear import (
    CL3SamplingTokenClear,
)
from myco.homeostasis.dimensions.mechanical.dc5_abstract_parent_allowlist import (
    DC5AbstractParentAllowlist,
)
from myco.homeostasis.dimensions.mechanical.di2_discipline_hooks_content import (
    DI2DisciplineHooksContent,
)
from myco.homeostasis.dimensions.mechanical.mf3_symbiont_artifact_integrity import (
    MF3SymbiontArtifactIntegrity,
)
from myco.homeostasis.dimensions.mechanical.mf4_overlay_subsystem_validity import (
    MF4OverlaySubsystemValidity,
)
from myco.homeostasis.dimensions.mechanical.mp3_plugin_bytecode_audit import (
    MP3PluginBytecodeAudit,
)
from myco.homeostasis.dimensions.mechanical.pa2_megafile_loc_cap import (
    PA2MegafileLocCap,
)
from myco.homeostasis.dimensions.mechanical.pa3_surface_pure_adapter import (
    PA3SurfacePureAdapter,
)
from myco.homeostasis.dimensions.mechanical.pa4_core_no_subsystem_deps import (
    PA4CoreNoSubsystemDeps,
)
from myco.homeostasis.dimensions.mechanical.pa5_meta_subsystem_layering import (
    PA5MetaSubsystemLayering,
)
from myco.homeostasis.dimensions.mechanical.sc1_schema_parity import SC1SchemaParity
from myco.homeostasis.dimensions.metabolic.mb4_sporulated_reabsorbed import (
    MB4SporulatedReabsorbed,
)
from myco.homeostasis.dimensions.metabolic.mb6_stale_draft_or_distilled import (
    MB6StaleDraftOrDistilled,
)
from myco.homeostasis.dimensions.metabolic.mb7_resource_watch_quota import (
    MB7ResourceWatchQuota,
)
from myco.homeostasis.dimensions.semantic.rl2_sense_discipline_signal import (
    RL2SenseDisciplineSignal,
)
from myco.homeostasis.dimensions.semantic.rl3_eat_discipline_signal import (
    RL3EatDisciplineSignal,
)
from myco.homeostasis.dimensions.semantic.se4_reciprocal_backlink import (
    SE4ReciprocalBacklink,
)
from myco.homeostasis.dimensions.shipped.sh2_kernel_ahead_of_canon import (
    SH2KernelAheadOfCanon,
)


@pytest.fixture
def ctx(genesis_substrate: Path) -> MycoContext:
    return MycoContext.for_testing(root=genesis_substrate)


# Mechanical (14 new) ---------------------------------------------------------


def test_pa2_runs(ctx: MycoContext):
    list(PA2MegafileLocCap().run(ctx))


def test_pa3_runs(ctx: MycoContext):
    list(PA3SurfacePureAdapter().run(ctx))


def test_pa4_runs(ctx: MycoContext):
    list(PA4CoreNoSubsystemDeps().run(ctx))


def test_pa5_runs(ctx: MycoContext):
    list(PA5MetaSubsystemLayering().run(ctx))


def test_sc1_runs(ctx: MycoContext):
    list(SC1SchemaParity().run(ctx))


def test_dc5_runs(ctx: MycoContext):
    list(DC5AbstractParentAllowlist().run(ctx))


def test_mf3_runs(ctx: MycoContext):
    list(MF3SymbiontArtifactIntegrity().run(ctx))


def test_di2_runs(ctx: MycoContext):
    list(DI2DisciplineHooksContent().run(ctx))


def test_di2_with_hooks_file(genesis_substrate: Path):
    """Exercise the hooks.json content-check path."""
    hooks_dir = genesis_substrate / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    hooks_path = hooks_dir / "hooks.json"
    hooks_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [{"command": "myco hunger"}],
                    "PreCompact": [{"command": "myco senesce"}],
                }
            }
        ),
        encoding="utf-8",
    )
    ctx = MycoContext.for_testing(root=genesis_substrate)
    findings = list(DI2DisciplineHooksContent().run(ctx))
    # No findings expected when both hooks present.
    assert findings == []


def test_di2_missing_hunger_emits(genesis_substrate: Path):
    hooks_dir = genesis_substrate / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    (hooks_dir / "hooks.json").write_text(
        '{"hooks": {"PreCompact": [{"command": "x"}]}}', encoding="utf-8"
    )
    ctx = MycoContext.for_testing(root=genesis_substrate)
    findings = list(DI2DisciplineHooksContent().run(ctx))
    assert any("R1" in f.message for f in findings)


def test_di2_invalid_json_emits(genesis_substrate: Path):
    hooks_dir = genesis_substrate / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    (hooks_dir / "hooks.json").write_text("{ NOT JSON", encoding="utf-8")
    ctx = MycoContext.for_testing(root=genesis_substrate)
    findings = list(DI2DisciplineHooksContent().run(ctx))
    assert any("parse" in f.message for f in findings)


def test_ad1_runs(ctx: MycoContext):
    list(AD1AdapterSilentSkip().run(ctx))


def test_mp3_runs(ctx: MycoContext):
    list(MP3PluginBytecodeAudit().run(ctx))


def test_cl1_runs(ctx: MycoContext):
    list(CL1SamplingPolicyGate().run(ctx))


def test_cl2_runs(ctx: MycoContext):
    list(CL2OAuthTokenResidency().run(ctx))


def test_cl3_runs(ctx: MycoContext):
    list(CL3SamplingTokenClear().run(ctx))


def test_mf4_runs(ctx: MycoContext):
    list(MF4OverlaySubsystemValidity().run(ctx))


# Semantic (3 new) ------------------------------------------------------------


def test_se4_runs(ctx: MycoContext):
    findings = list(SE4ReciprocalBacklink().run(ctx))
    # SE4 v0.6.0 emits zero findings (whitelist empty by design)
    assert findings == []


def test_rl2_runs(ctx: MycoContext):
    list(RL2SenseDisciplineSignal().run(ctx))


def test_rl2_risky_verb_without_sense_emits(genesis_substrate: Path):
    log_dir = genesis_substrate / ".myco_state"
    log_dir.mkdir(exist_ok=True)
    log = log_dir / "session_calls.jsonl"
    log.write_text(
        "\n".join(
            json.dumps(e)
            for e in [
                {"verb": "hunger"},
                {"verb": "molt"},
                {"verb": "brief"},
            ]
        ),
        encoding="utf-8",
    )
    ctx = MycoContext.for_testing(root=genesis_substrate)
    findings = list(RL2SenseDisciplineSignal().run(ctx))
    assert any("R3" in f.message for f in findings)


def test_rl3_runs(ctx: MycoContext):
    list(RL3EatDisciplineSignal().run(ctx))


def test_rl3_high_decision_ratio_emits(genesis_substrate: Path):
    log_dir = genesis_substrate / ".myco_state"
    log_dir.mkdir(exist_ok=True)
    log = log_dir / "session_calls.jsonl"
    log.write_text(
        "\n".join(
            json.dumps(e)
            for e in [
                {"verb": "sense", "msg": "decided to use python 3.13"},
                {"verb": "molt", "msg": "decided to bump"},
                {"verb": "brief", "msg": "decided again"},
                {"verb": "winnow", "msg": "decided once more"},
            ]
        ),
        encoding="utf-8",
    )
    ctx = MycoContext.for_testing(root=genesis_substrate)
    findings = list(RL3EatDisciplineSignal().run(ctx))
    # 4 decisions / 0 eats = inf ratio; should emit
    assert findings  # non-empty


# Metabolic (3 new) -----------------------------------------------------------


def test_mb4_runs(ctx: MycoContext):
    list(MB4SporulatedReabsorbed().run(ctx))


def test_mb4_sporulated_without_propagated_doctrine_emits(genesis_substrate: Path):
    distilled_dir = genesis_substrate / "notes" / "distilled"
    distilled_dir.mkdir(parents=True, exist_ok=True)
    (distilled_dir / "d_orphan.md").write_text(
        "---\nstage: sporulated\n---\nbody\n", encoding="utf-8"
    )
    ctx = MycoContext.for_testing(root=genesis_substrate)
    findings = list(MB4SporulatedReabsorbed().run(ctx))
    assert any("propagated_doctrine" in f.message for f in findings)


def test_mb6_runs(ctx: MycoContext):
    list(MB6StaleDraftOrDistilled().run(ctx))


def test_mb6_old_draft_emits(genesis_substrate: Path):
    """A 60-day-old DRAFT craft should emit a stale finding."""
    pri = genesis_substrate / "docs" / "primordia"
    pri.mkdir(parents=True, exist_ok=True)
    # Use a date well in the past
    (pri / "stale_topic_craft_2025-01-01.md").write_text(
        "---\nstatus: DRAFT\ndate: 2025-01-01\n---\nbody\n",
        encoding="utf-8",
    )
    ctx = MycoContext.for_testing(root=genesis_substrate)
    findings = list(MB6StaleDraftOrDistilled().run(ctx))
    assert findings


def test_mb6_fix_returns_advisory(ctx: MycoContext):
    """Fix at v0.6.0 is informational only."""
    dim = MB6StaleDraftOrDistilled()
    from myco.homeostasis.finding import Finding

    out = dim.fix(
        ctx,
        Finding(
            dimension_id="MB6",
            category=dim.category,
            severity=dim.default_severity,
            message="test",
            path="test",
        ),
    )
    assert out["applied"] is False


def test_mb7_runs(ctx: MycoContext):
    list(MB7ResourceWatchQuota().run(ctx))


def test_mb7_quota_pressure_emits(genesis_substrate: Path):
    state_dir = genesis_substrate / ".myco_state"
    state_dir.mkdir(exist_ok=True)
    (state_dir / "resource_watch_count.json").write_text(
        '{"active": 95}', encoding="utf-8"
    )
    ctx = MycoContext.for_testing(root=genesis_substrate)
    findings = list(MB7ResourceWatchQuota().run(ctx))
    # Default max_per_substrate from canon is 100; 95/100 = 95% > 80%
    assert findings


# Shipped (1 new) -------------------------------------------------------------


def test_sh2_runs(ctx: MycoContext):
    list(SH2KernelAheadOfCanon().run(ctx))
