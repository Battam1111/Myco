"""Tests for ``mp_cluster`` — merged per-dim test files (v0.8.8).

Per-dim test files consolidated to mirror the src/ cluster
merge. Each `# === <stem>` section corresponds to one original
per-dim test file; git history preserves the per-dim state.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimensions import _BUILT_IN
from myco.homeostasis.dimensions.mechanical.mp_cluster import (
    MP1NoProviderImports,
    MP2PluginProviderImports,
)
from myco.homeostasis.finding import Category

# =========================================================================
# test_mp1_no_provider_imports — see git history for original per-dim file
# =========================================================================

_MINIMAL_CANON = textwrap.dedent(
    """\
    schema_version: "1"
    contract_version: "v0.5.6"
    identity:
      substrate_id: "mp1-test"
      entry_point: "MYCO.md"
    system:
      hard_contract:
        rule_count: 7
      no_llm_in_substrate: true
    subsystems:
      homeostasis:
        doc: "docs/architecture/L2_DOCTRINE/homeostasis.md"
    """
)
_CANON_OPTED_OUT = textwrap.dedent(
    """\
    schema_version: "1"
    contract_version: "v0.5.6"
    identity:
      substrate_id: "mp1-optout"
      entry_point: "MYCO.md"
    system:
      hard_contract:
        rule_count: 7
      no_llm_in_substrate: false
    subsystems:
      homeostasis:
        doc: "docs/architecture/L2_DOCTRINE/homeostasis.md"
    """
)


def _seed_substrate(root: Path, canon: str = _MINIMAL_CANON) -> MycoContext:
    """Write a canon + an empty ``src/myco/`` skeleton and return a ctx."""
    (root / "_canon.yaml").write_text(canon, encoding="utf-8")
    (root / "src" / "myco").mkdir(parents=True)
    (root / "src" / "myco" / "__init__.py").write_text(
        '"""Kernel test fixture."""\n', encoding="utf-8"
    )
    return MycoContext.for_testing(root=root)


def test_mp1_is_registered_in_built_in() -> None:
    """``_BUILT_IN`` includes ``MP1NoProviderImports`` for dev checkouts."""
    assert MP1NoProviderImports in _BUILT_IN


def test_mp1_dimension_attributes() -> None:
    """id / category / default_severity / fixable match the spec."""
    assert MP1NoProviderImports.id == "MP1"
    assert MP1NoProviderImports.category is Category.MECHANICAL
    assert MP1NoProviderImports.default_severity is Severity.HIGH
    assert MP1NoProviderImports.fixable is False


def test_mp1_clean_kernel_no_findings(tmp_path: Path) -> None:
    """Stdlib-only imports produce no MP1 finding."""
    ctx = _seed_substrate(tmp_path)
    (tmp_path / "src" / "myco" / "foo.py").write_text(
        textwrap.dedent(
            """\
            from pathlib import Path
            from datetime import datetime, timezone

            def now() -> datetime:
                return datetime.now(timezone.utc)
            """
        ),
        encoding="utf-8",
    )
    findings = list(MP1NoProviderImports().run(ctx))
    assert findings == []


def test_mp1_detects_openai_import(tmp_path: Path) -> None:
    """``import openai`` in a kernel file → HIGH finding."""
    ctx = _seed_substrate(tmp_path)
    evil = tmp_path / "src" / "myco" / "evil.py"
    evil.write_text("import openai\n", encoding="utf-8")
    findings = list(MP1NoProviderImports().run(ctx))
    assert len(findings) == 1
    f = findings[0]
    assert f.dimension_id == "MP1"
    assert f.severity is Severity.HIGH
    assert f.category is Category.MECHANICAL
    assert "openai" in f.message
    # Path is reported in POSIX form so downstream tooling can
    # compare it without platform drift.
    assert f.path is not None and f.path.endswith("src/myco/evil.py")
    assert f.line == 1


def test_mp1_detects_from_anthropic_import(tmp_path: Path) -> None:
    """``from anthropic import Client`` → HIGH finding."""
    ctx = _seed_substrate(tmp_path)
    (tmp_path / "src" / "myco" / "bridge.py").write_text(
        "from anthropic import Client\n",
        encoding="utf-8",
    )
    findings = list(MP1NoProviderImports().run(ctx))
    assert len(findings) == 1
    assert findings[0].severity is Severity.HIGH
    assert "anthropic" in findings[0].message


def test_mp1_detects_nested_langchain(tmp_path: Path) -> None:
    """``from langchain_openai.chat_models import ChatOpenAI`` fires."""
    ctx = _seed_substrate(tmp_path)
    (tmp_path / "src" / "myco" / "chains.py").write_text(
        "from langchain_openai.chat_models import ChatOpenAI\n",
        encoding="utf-8",
    )
    findings = list(MP1NoProviderImports().run(ctx))
    assert len(findings) == 1
    assert findings[0].severity is Severity.HIGH
    # The blacklist root is reported — ``langchain_openai.chat_models``
    # matches because the top-level ``langchain_openai`` is blacklisted.
    assert "langchain_openai.chat_models" in findings[0].message


def test_mp1_ignores_relative_imports(tmp_path: Path) -> None:
    """``from .pipeline import x`` is a relative import; MP1 ignores it."""
    ctx = _seed_substrate(tmp_path)
    (tmp_path / "src" / "myco" / "pipeline.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "myco" / "consumer.py").write_text(
        "from .pipeline import x  # noqa\n",
        encoding="utf-8",
    )
    findings = list(MP1NoProviderImports().run(ctx))
    assert findings == []


def test_mp1_no_longer_ignores_providers_directory(tmp_path: Path) -> None:
    """v0.6.14: ``src/myco/providers/`` path-skip removed.

    Per v0.6.14 craft Round 2 R-T17: the directory was reserved at v0.5.6
    as a named escape hatch but never populated through 7 minor releases.
    v0.6.14 excretes the directory from Myco-self and removes the MP1
    path-skip. If a synthetic substrate (e.g. a downstream test fixture
    or a contrarian fork) recreates the directory, MP1 now scans it
    like any other kernel path. The declared opt-in via
    ``llm_policy: opt-in`` flips findings to LOW severity; default
    ``forbidden`` keeps them HIGH (CI gates).

    This test asserts the new behavior: providers/ contents ARE scanned
    when llm_policy is forbidden. The previous test (path-skip behavior)
    is preserved as a comment for archaeology.
    """
    ctx = _seed_substrate(tmp_path)  # default canon: llm_policy = forbidden
    providers_dir = tmp_path / "src" / "myco" / "providers"
    providers_dir.mkdir()
    (providers_dir / "__init__.py").write_text("", encoding="utf-8")
    (providers_dir / "openai_bridge.py").write_text("import openai\n", encoding="utf-8")
    findings = list(MP1NoProviderImports().run(ctx))
    # v0.6.14: providers/ is no longer path-skipped; the import IS detected.
    provider_findings = [f for f in findings if "openai" in (f.message or "")]
    assert len(provider_findings) >= 1, (
        "v0.6.14: MP1 must NOT skip src/myco/providers/. The path-skip was "
        "removed when the directory was excreted from Myco-self. A synthetic "
        "substrate that recreates providers/ should still trigger MP1."
    )
    # Severity must be HIGH because llm_policy is the default `forbidden`.
    assert provider_findings[0].severity.value >= 3, (
        f"Expected HIGH severity for forbidden-policy + provider import; "
        f"got {provider_findings[0].severity}"
    )


def test_mp1_ignores_pycache(tmp_path: Path) -> None:
    """``__pycache__`` and dotted directories are skipped during walk."""
    ctx = _seed_substrate(tmp_path)
    cache_dir = tmp_path / "src" / "myco" / "__pycache__"
    cache_dir.mkdir()
    (cache_dir / "evil.cpython-312.py").write_text("import openai\n", encoding="utf-8")
    hidden_dir = tmp_path / "src" / "myco" / ".hidden"
    hidden_dir.mkdir()
    (hidden_dir / "sneaky.py").write_text("import openai\n", encoding="utf-8")
    findings = list(MP1NoProviderImports().run(ctx))
    assert findings == []


def test_mp1_syntax_error_does_not_crash(tmp_path: Path) -> None:
    """A ``.py`` with a parse error is skipped silently (no crash, no finding)."""
    ctx = _seed_substrate(tmp_path)
    (tmp_path / "src" / "myco" / "broken.py").write_text(
        "def broken(:\n  pass\n",
        encoding="utf-8",
    )
    # Must not raise; must not yield a finding for the broken file.
    findings = list(MP1NoProviderImports().run(ctx))
    assert findings == []


def test_mp1_severity_is_low_when_canon_opts_out(tmp_path: Path) -> None:
    """``no_llm_in_substrate: false`` → LOW severity + opt-out message."""
    ctx = _seed_substrate(tmp_path, canon=_CANON_OPTED_OUT)
    (tmp_path / "src" / "myco" / "bridge.py").write_text(
        "import openai\n", encoding="utf-8"
    )
    findings = list(MP1NoProviderImports().run(ctx))
    assert len(findings) == 1
    f = findings[0]
    assert f.severity is Severity.LOW
    assert "opt" in f.message.lower() or "opted" in f.message.lower()
    assert "openai" in f.message


def test_mp1_scope_is_kernel_only(tmp_path: Path) -> None:
    """``.myco/plugins/`` files are not MP1's concern (MF2 territory)."""
    ctx = _seed_substrate(tmp_path)
    plugins = tmp_path / ".myco" / "plugins" / "handlers"
    plugins.mkdir(parents=True)
    (plugins / "bad.py").write_text("import openai\n", encoding="utf-8")
    findings = list(MP1NoProviderImports().run(ctx))
    assert findings == []


_CANON_V0_6_14 = textwrap.dedent(
    """\
    schema_version: "2"
    contract_version: "v0.6.14"
    identity:
      substrate_id: "mp1-craft-test"
      entry_point: "MYCO.md"
    system:
      hard_contract:
        rule_count: 7
      llm_policy: "forbidden"
      governance:
        recognized_authoring_hosts:
          - "claude-code-agent"
          - "human"
    subsystems:
      homeostasis:
        doc: "docs/architecture/L2_DOCTRINE/homeostasis.md"
    """
)


def _seed_v0_6_14(tmp_path: Path) -> MycoContext:
    """Substrate with v0.6.14 governance block + empty docs/primordia/."""
    (tmp_path / "_canon.yaml").write_text(_CANON_V0_6_14, encoding="utf-8")
    (tmp_path / "src" / "myco").mkdir(parents=True)
    (tmp_path / "src" / "myco" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "docs" / "primordia").mkdir(parents=True)
    return MycoContext.for_testing(root=tmp_path)


def _write_craft(
    tmp_path: Path,
    name: str,
    *,
    type_: str = "craft",
    authored_by: str | None = "human",
    extra_frontmatter: str = "",
) -> Path:
    """Helper: write a craft markdown with optional `authored_by:`."""
    fm_lines = [f"type: {type_}"] if type_ else []
    if authored_by is not None:
        fm_lines.append(f"authored_by: {authored_by}")
    if extra_frontmatter:
        fm_lines.append(extra_frontmatter)
    fm = "\n".join(fm_lines)
    body = f"---\n{fm}\n---\n\n# {name}\n\nbody.\n"
    path = tmp_path / "docs" / "primordia" / f"{name}.md"
    path.write_text(body, encoding="utf-8")
    return path


def test_mp1_craft_with_recognized_host_passes(tmp_path: Path) -> None:
    """type: craft + authored_by: human → no finding."""
    ctx = _seed_v0_6_14(tmp_path)
    _write_craft(tmp_path, "ok_craft", authored_by="human")
    findings = list(MP1NoProviderImports().run(ctx))
    craft_findings = [f for f in findings if "ok_craft" in (f.path or "")]
    assert craft_findings == []


def test_mp1_craft_missing_authored_by_emits_high(tmp_path: Path) -> None:
    """type: craft + no authored_by → HIGH finding."""
    ctx = _seed_v0_6_14(tmp_path)
    _write_craft(tmp_path, "no_signature", authored_by=None)
    findings = list(MP1NoProviderImports().run(ctx))
    matches = [f for f in findings if "no_signature" in (f.path or "")]
    assert len(matches) == 1
    assert matches[0].severity is Severity.HIGH
    assert "authored_by" in matches[0].message


def test_mp1_craft_with_unrecognized_host_emits_high(tmp_path: Path) -> None:
    """type: craft + authored_by: <unrecognized> → HIGH finding."""
    ctx = _seed_v0_6_14(tmp_path)
    _write_craft(tmp_path, "bad_host", authored_by="rogue-bot-9000")
    findings = list(MP1NoProviderImports().run(ctx))
    matches = [f for f in findings if "bad_host" in (f.path or "")]
    assert len(matches) == 1
    assert matches[0].severity is Severity.HIGH
    assert "rogue-bot-9000" in matches[0].message


def test_mp1_non_craft_primordia_exempt(tmp_path: Path) -> None:
    """type: handoff (not craft) without authored_by → no finding (exempt)."""
    ctx = _seed_v0_6_14(tmp_path)
    _write_craft(tmp_path, "handoff_doc", type_="handoff", authored_by=None)
    findings = list(MP1NoProviderImports().run(ctx))
    matches = [f for f in findings if "handoff_doc" in (f.path or "")]
    assert matches == []


def test_mp1_excreted_directory_exempt(tmp_path: Path) -> None:
    """Crafts under docs/primordia/_excreted/ are exempt."""
    ctx = _seed_v0_6_14(tmp_path)
    excreted = tmp_path / "docs" / "primordia" / "_excreted"
    excreted.mkdir()
    (excreted / "stale_craft.md").write_text(
        "---\ntype: craft\n---\n\n# old draft, no signature\n",
        encoding="utf-8",
    )
    findings = list(MP1NoProviderImports().run(ctx))
    matches = [f for f in findings if "stale_craft" in (f.path or "")]
    assert matches == []


def test_mp1_no_frontmatter_exempt(tmp_path: Path) -> None:
    """Markdown file with no frontmatter is exempt (non-craft)."""
    ctx = _seed_v0_6_14(tmp_path)
    raw_path = tmp_path / "docs" / "primordia" / "narrative.md"
    raw_path.write_text("# free-form narrative, no frontmatter\n", encoding="utf-8")
    findings = list(MP1NoProviderImports().run(ctx))
    matches = [f for f in findings if "narrative" in (f.path or "")]
    assert matches == []


def test_mp1_malformed_frontmatter_exempt(tmp_path: Path) -> None:
    """Markdown file with unclosed frontmatter is exempt (treated as non-craft)."""
    ctx = _seed_v0_6_14(tmp_path)
    bad_path = tmp_path / "docs" / "primordia" / "bad_fm.md"
    bad_path.write_text("---\ntype: craft\n# no closing ---\n", encoding="utf-8")
    findings = list(MP1NoProviderImports().run(ctx))
    matches = [f for f in findings if "bad_fm" in (f.path or "")]
    assert matches == []


def test_mp1_quoted_authored_by_value_recognized(tmp_path: Path) -> None:
    """authored_by: 'human' (single-quoted) is parsed correctly."""
    ctx = _seed_v0_6_14(tmp_path)
    p = tmp_path / "docs" / "primordia" / "quoted.md"
    p.write_text(
        "---\ntype: craft\nauthored_by: 'human'\n---\n\n# quoted\n",
        encoding="utf-8",
    )
    findings = list(MP1NoProviderImports().run(ctx))
    matches = [f for f in findings if "quoted" in (f.path or "")]
    assert matches == []


def test_mp1_no_primordia_dir_no_crash(tmp_path: Path) -> None:
    """Substrate without docs/primordia/ → no crash, no findings on craft scan."""
    (tmp_path / "_canon.yaml").write_text(_CANON_V0_6_14, encoding="utf-8")
    (tmp_path / "src" / "myco").mkdir(parents=True)
    (tmp_path / "src" / "myco" / "__init__.py").write_text("", encoding="utf-8")
    # Intentionally do NOT create docs/primordia/.
    ctx = MycoContext.for_testing(root=tmp_path)
    findings = list(MP1NoProviderImports().run(ctx))
    # No craft-related findings.
    craft_findings = [f for f in findings if "primordia" in (f.path or "")]
    assert craft_findings == []


def test_mp1_no_kernel_dir_silent_exit(tmp_path: Path) -> None:
    """Substrate without src/myco/ — documentation-only substrate.

    Per MP1 docstring: "Substrate does not ship a kernel tree under the
    canonical path (e.g. a documentation-only substrate). Nothing to
    check; silent exit." Covers the early-return branch at line ~218.
    """
    (tmp_path / "_canon.yaml").write_text(_CANON_V0_6_14, encoding="utf-8")
    # Intentionally NO src/myco/ directory.
    (tmp_path / "docs" / "primordia").mkdir(parents=True)
    ctx = MycoContext.for_testing(root=tmp_path)
    findings = list(MP1NoProviderImports().run(ctx))
    # Only the craft-scan part runs (which is also empty); kernel-import
    # scan silently returns. No exceptions.
    provider_findings = [
        f for f in findings if "kernel file imports" in (f.message or "")
    ]
    assert provider_findings == []


def test_mp1_kernel_import_stmt_non_provider_no_finding(tmp_path: Path) -> None:
    """`import json` (Import node, non-provider) → no MP1 finding.

    Covers the branch where ``ast.Import`` is hit but the imported
    top-level dotted path doesn't match the provider blacklist
    (line 426 False branch in mp1_no_provider_imports.py).
    """
    ctx = _seed_substrate(tmp_path)
    (tmp_path / "src" / "myco" / "foo.py").write_text(
        textwrap.dedent(
            """\
            import json
            import os.path

            def use_json():
                return json.dumps({})
            """
        ),
        encoding="utf-8",
    )
    findings = list(MP1NoProviderImports().run(ctx))
    assert findings == []


def test_mp1_uses_canon_recognized_hosts(tmp_path: Path) -> None:
    """The host whitelist is read from canon, not hardcoded.

    Custom canon with only "human" recognized → claude-code-agent must
    fail. Confirms MP1 reads the dynamic list, not a hardcoded constant.
    """
    custom_canon = textwrap.dedent(
        """\
        schema_version: "2"
        contract_version: "v0.6.14"
        identity:
          substrate_id: "mp1-strict-test"
          entry_point: "MYCO.md"
        system:
          hard_contract:
            rule_count: 7
          llm_policy: "forbidden"
          governance:
            recognized_authoring_hosts:
              - "human"
        subsystems:
          homeostasis:
            doc: "docs/architecture/L2_DOCTRINE/homeostasis.md"
        """
    )
    (tmp_path / "_canon.yaml").write_text(custom_canon, encoding="utf-8")
    (tmp_path / "src" / "myco").mkdir(parents=True)
    (tmp_path / "src" / "myco" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "docs" / "primordia").mkdir(parents=True)
    ctx = MycoContext.for_testing(root=tmp_path)
    _write_craft(tmp_path, "claude_authored", authored_by="claude-code-agent")
    findings = list(MP1NoProviderImports().run(ctx))
    # claude-code-agent NOT in this canon's recognized list → fires.
    matches = [f for f in findings if "claude_authored" in (f.path or "")]
    assert len(matches) == 1
    assert matches[0].severity is Severity.HIGH


# =========================================================================
# test_mp2_plugin_provider_imports — see git history for original per-dim file
# =========================================================================


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
