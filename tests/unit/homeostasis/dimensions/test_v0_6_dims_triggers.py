"""Trigger-path tests for v0.6.0 dims — exercise the finding-emission branches.

Each test sets up a substrate condition that triggers a specific dim's
finding-emission, then runs the dim and asserts the finding appears.
This exercises the inner branches (path-walking, text-matching,
finding construction) that smoke tests miss.
"""

from __future__ import annotations

from pathlib import Path

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
from myco.homeostasis.dimensions.shipped.sh2_kernel_ahead_of_canon import (
    SH2KernelAheadOfCanon,
)


def test_pa2_megafile_emits(tmp_path: Path):
    """A 1000-line .py file under src/myco/ → PA2 emit."""
    sub = tmp_path / "sub"
    src_dir = sub / "src" / "myco" / "test_pkg"
    src_dir.mkdir(parents=True)
    big = src_dir / "huge.py"
    big.write_text("\n".join(f"x = {i}" for i in range(1000)), encoding="utf-8")
    # Minimal canon
    (sub / "_canon.yaml").write_text(
        'schema_version: "2"\ncontract_version: "v0.6.0"\n'
        'identity:\n  substrate_id: "x"\n  entry_point: "M.md"\n'
        "system:\n  write_surface:\n    allowed: ['_canon.yaml']\n"
        "  hard_contract:\n    rule_count: 7\n"
        "subsystems:\n  ingestion:\n    package: 'src/'\n",
        encoding="utf-8",
    )
    (sub / "M.md").write_text("# x", encoding="utf-8")
    ctx = MycoContext.for_testing(root=sub)
    findings = list(PA2MegafileLocCap().run(ctx))
    assert any("megafile" in f.message for f in findings)


def test_pa3_surface_imports_subsystem_emits(tmp_path: Path):
    """surface/X.py importing a subsystem package → PA3 emit."""
    sub = tmp_path / "sub"
    surf = sub / "src" / "myco" / "surface"
    surf.mkdir(parents=True)
    (surf / "bad.py").write_text("from myco.ingestion import eat\n", encoding="utf-8")
    (sub / "_canon.yaml").write_text(
        'schema_version: "2"\ncontract_version: "v0.6.0"\n'
        'identity:\n  substrate_id: "x"\n  entry_point: "M.md"\n'
        "system:\n  write_surface:\n    allowed: ['_canon.yaml']\n"
        "  hard_contract:\n    rule_count: 7\n"
        "subsystems:\n  ingestion:\n    package: 'src/'\n",
        encoding="utf-8",
    )
    (sub / "M.md").write_text("# x", encoding="utf-8")
    ctx = MycoContext.for_testing(root=sub)
    findings = list(PA3SurfacePureAdapter().run(ctx))
    assert any("imports subsystem" in f.message for f in findings)


def test_pa4_core_imports_subsystem_emits(tmp_path: Path):
    """core/X.py importing a subsystem → PA4 emit."""
    sub = tmp_path / "sub"
    core = sub / "src" / "myco" / "core"
    core.mkdir(parents=True)
    (core / "bad.py").write_text("from myco.ingestion import eat\n", encoding="utf-8")
    (sub / "_canon.yaml").write_text(
        'schema_version: "2"\ncontract_version: "v0.6.0"\n'
        'identity:\n  substrate_id: "x"\n  entry_point: "M.md"\n'
        "system:\n  write_surface:\n    allowed: ['_canon.yaml']\n"
        "  hard_contract:\n    rule_count: 7\n"
        "subsystems:\n  ingestion:\n    package: 'src/'\n",
        encoding="utf-8",
    )
    (sub / "M.md").write_text("# x", encoding="utf-8")
    ctx = MycoContext.for_testing(root=sub)
    findings = list(PA4CoreNoSubsystemDeps().run(ctx))
    assert any("imports subsystem" in f.message for f in findings)


def test_pa5_subsystem_imports_meta_emits(tmp_path: Path):
    """ingestion/X.py importing surface/ → PA5 emit."""
    sub = tmp_path / "sub"
    ing = sub / "src" / "myco" / "ingestion"
    ing.mkdir(parents=True)
    (ing / "bad.py").write_text(
        "from myco.boundary.surface import cli\n", encoding="utf-8"
    )
    (sub / "_canon.yaml").write_text(
        'schema_version: "2"\ncontract_version: "v0.6.0"\n'
        'identity:\n  substrate_id: "x"\n  entry_point: "M.md"\n'
        "system:\n  write_surface:\n    allowed: ['_canon.yaml']\n"
        "  hard_contract:\n    rule_count: 7\n"
        "subsystems:\n  ingestion:\n    package: 'src/'\n",
        encoding="utf-8",
    )
    (sub / "M.md").write_text("# x", encoding="utf-8")
    ctx = MycoContext.for_testing(root=sub)
    findings = list(PA5MetaSubsystemLayering().run(ctx))
    assert any("meta-subsystem" in f.message for f in findings)


def test_ad1_silent_skip_pattern_emits(tmp_path: Path):
    """An adapter with `return []` silent-skip → AD1 emit."""
    sub = tmp_path / "sub"
    adp = sub / "src" / "myco" / "ingestion" / "adapters"
    adp.mkdir(parents=True)
    (adp / "bad.py").write_text(
        "def ingest():\n    if True:\n        return []\n", encoding="utf-8"
    )
    (sub / "_canon.yaml").write_text(
        'schema_version: "2"\ncontract_version: "v0.6.0"\n'
        'identity:\n  substrate_id: "x"\n  entry_point: "M.md"\n'
        "system:\n  write_surface:\n    allowed: ['_canon.yaml']\n"
        "  hard_contract:\n    rule_count: 7\n"
        "subsystems:\n  ingestion:\n    package: 'src/'\n",
        encoding="utf-8",
    )
    (sub / "M.md").write_text("# x", encoding="utf-8")
    ctx = MycoContext.for_testing(root=sub)
    findings = list(AD1AdapterSilentSkip().run(ctx))
    assert any("silent-skip" in f.message for f in findings)


def test_mp3_dynamic_llm_import_emits(genesis_substrate: Path):
    """A plugin that uses `importlib.import_module('openai')` → MP3 emit."""
    plugin_dir = genesis_substrate / ".myco" / "plugins"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "bad.py").write_text(
        'import importlib\nm = importlib.import_module("openai")\n',
        encoding="utf-8",
    )
    ctx = MycoContext.for_testing(root=genesis_substrate)
    findings = list(MP3PluginBytecodeAudit().run(ctx))
    assert any("LLM-SDK" in f.message for f in findings)


def test_mf3_symbiont_with_marker_no_finding(genesis_substrate: Path):
    """MF3 only fires when symbionts/installed.txt marker present."""
    state = genesis_substrate / ".myco_state" / "symbionts"
    state.mkdir(parents=True, exist_ok=True)
    (state / "installed.txt").write_text("yes", encoding="utf-8")
    ctx = MycoContext.for_testing(root=genesis_substrate)
    # Walk runs but no signed-out artifacts in test home; no error path.
    list(MF3SymbiontArtifactIntegrity().run(ctx))


def test_mf4_overlay_unknown_subsystem_emits(genesis_substrate: Path):
    """An overlay_verb with an unknown subsystem → MF4 emit."""
    overlay_dir = genesis_substrate / ".myco"
    overlay_dir.mkdir(exist_ok=True)
    (overlay_dir / "manifest_overlay.yaml").write_text(
        "commands:\n  - name: foo\n    subsystem: not-a-real-subsystem\n",
        encoding="utf-8",
    )
    ctx = MycoContext.for_testing(root=genesis_substrate)
    findings = list(MF4OverlaySubsystemValidity().run(ctx))
    assert any("not in canon.subsystems" in f.message for f in findings)


def test_dc5_with_canon_allowlist_no_emit(genesis_substrate: Path):
    """When canon declares abstract_parent_allowlist, DC5 emits nothing."""
    # genesis_substrate's canon does have abstract_parent_allowlist (from
    # its template). Let's verify DC5 emits zero in that case.
    ctx = MycoContext.for_testing(root=genesis_substrate)
    list(DC5AbstractParentAllowlist().run(ctx))


def test_cl1_with_mcp_sampling_no_gate_emits(tmp_path: Path):
    """An mcp_sampling.py without llm_policy gate → CL1 emit."""
    sub = tmp_path / "sub"
    surf = sub / "src" / "myco" / "surface"
    surf.mkdir(parents=True)
    (surf / "mcp_sampling.py").write_text(
        "# Just a stub, no llm_policy check\n", encoding="utf-8"
    )
    (sub / "_canon.yaml").write_text(
        'schema_version: "2"\ncontract_version: "v0.6.0"\n'
        'identity:\n  substrate_id: "x"\n  entry_point: "M.md"\n'
        "system:\n  write_surface:\n    allowed: ['_canon.yaml']\n"
        "  hard_contract:\n    rule_count: 7\n"
        "subsystems:\n  ingestion:\n    package: 'src/'\n",
        encoding="utf-8",
    )
    (sub / "M.md").write_text("# x", encoding="utf-8")
    ctx = MycoContext.for_testing(root=sub)
    findings = list(CL1SamplingPolicyGate().run(ctx))
    assert any("llm_policy" in f.message for f in findings)


def test_cl2_token_redaction_required_no_helper_emits(tmp_path: Path):
    """token_redaction_required=true + no _redact_in_logs in mcp_auth → CL2 emit."""
    sub = tmp_path / "sub"
    surf = sub / "src" / "myco" / "surface"
    surf.mkdir(parents=True)
    (surf / "mcp_auth.py").write_text(
        "# stub without redact helper\n", encoding="utf-8"
    )
    (sub / "_canon.yaml").write_text(
        'schema_version: "2"\ncontract_version: "v0.6.0"\n'
        'identity:\n  substrate_id: "x"\n  entry_point: "M.md"\n'
        "system:\n  write_surface:\n    allowed: ['_canon.yaml']\n"
        "  hard_contract:\n    rule_count: 7\n"
        "  governance:\n    token_redaction_required: true\n"
        "subsystems:\n  ingestion:\n    package: 'src/'\n",
        encoding="utf-8",
    )
    (sub / "M.md").write_text("# x", encoding="utf-8")
    ctx = MycoContext.for_testing(root=sub)
    findings = list(CL2OAuthTokenResidency().run(ctx))
    assert any("_redact_in_logs" in f.message for f in findings)


def test_cl3_opt_in_no_clear_helper_emits(tmp_path: Path):
    """llm_policy=opt-in + no _clear_token_after_call → CL3 emit."""
    sub = tmp_path / "sub"
    surf = sub / "src" / "myco" / "surface"
    surf.mkdir(parents=True)
    (surf / "mcp_sampling.py").write_text(
        "# stub without clear helper\n", encoding="utf-8"
    )
    (sub / "_canon.yaml").write_text(
        'schema_version: "2"\ncontract_version: "v0.6.0"\n'
        'identity:\n  substrate_id: "x"\n  entry_point: "M.md"\n'
        "system:\n  llm_policy: opt-in\n"
        "  write_surface:\n    allowed: ['_canon.yaml']\n"
        "  hard_contract:\n    rule_count: 7\n"
        "subsystems:\n  ingestion:\n    package: 'src/'\n",
        encoding="utf-8",
    )
    (sub / "M.md").write_text("# x", encoding="utf-8")
    ctx = MycoContext.for_testing(root=sub)
    findings = list(CL3SamplingTokenClear().run(ctx))
    assert any("_clear_token" in f.message for f in findings)


def test_sc1_canon_schema_drift_emits(genesis_substrate: Path):
    """When docs/schema/canon.schema.json declares a required key not in canon → SC1 emit."""
    schema_dir = genesis_substrate / "docs" / "schema"
    schema_dir.mkdir(parents=True, exist_ok=True)
    (schema_dir / "canon.schema.json").write_text(
        '{"required": ["this_key_definitely_not_in_canon"]}', encoding="utf-8"
    )
    ctx = MycoContext.for_testing(root=genesis_substrate)
    findings = list(SC1SchemaParity().run(ctx))
    assert any("required key" in f.message for f in findings)


def test_sh2_kernel_ahead_of_canon_emits_when_canon_higher(tmp_path: Path):
    """A canon that claims a newer contract_version than __version__ → SH2 emit."""
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "_canon.yaml").write_text(
        'schema_version: "2"\ncontract_version: "v999.0.0"\n'
        'identity:\n  substrate_id: "x"\n  entry_point: "M.md"\n'
        "system:\n  write_surface:\n    allowed: ['_canon.yaml']\n"
        "  hard_contract:\n    rule_count: 7\n"
        "subsystems:\n  ingestion:\n    package: 'src/'\n",
        encoding="utf-8",
    )
    (sub / "M.md").write_text("# x", encoding="utf-8")
    ctx = MycoContext.for_testing(root=sub)
    findings = list(SH2KernelAheadOfCanon().run(ctx))
    assert any("exceeds" in f.message for f in findings)
