"""Tests for ``MP1NoProviderImports`` (v0.5.6 mycelium-purity seam).

Pins the behavior described in
``docs/primordia/v0_5_6_mp1_mycelium_purity_craft_2026-04-18.md`` and
the class docstring on
``myco.homeostasis.dimensions.mp1_no_provider_imports.MP1NoProviderImports``.

Covers:

- class-attribute contract (id, category, default_severity, fixable);
- registration in the built-in tuple;
- clean substrate → zero findings;
- ``import openai`` and ``from anthropic import …`` → HIGH findings;
- nested ``from langchain_openai.chat_models import ChatOpenAI``
  → HIGH finding on the blacklist root;
- relative imports (``from .pipeline import x``) → no finding;
- ``src/myco/providers/`` subtree is scan-exempt;
- ``__pycache__`` / hidden directories are skipped;
- syntax errors in a scanned file → no crash, no finding;
- ``canon.system.no_llm_in_substrate: false`` → same imports fire at
  LOW severity with an opt-out message;
- ``.myco/plugins/`` is **out of scope** (MF2 governs that axis).
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimensions import _BUILT_IN
from myco.homeostasis.dimensions.mechanical.mp1_no_provider_imports import (
    MP1NoProviderImports,
)
from myco.homeostasis.finding import Category

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


# ---------------------------------------------------------------------------
# Static / registration contract
# ---------------------------------------------------------------------------


def test_mp1_is_registered_in_built_in() -> None:
    """``_BUILT_IN`` includes ``MP1NoProviderImports`` for dev checkouts."""
    assert MP1NoProviderImports in _BUILT_IN


def test_mp1_dimension_attributes() -> None:
    """id / category / default_severity / fixable match the spec."""
    assert MP1NoProviderImports.id == "MP1"
    assert MP1NoProviderImports.category is Category.MECHANICAL
    assert MP1NoProviderImports.default_severity is Severity.HIGH
    assert MP1NoProviderImports.fixable is False


# ---------------------------------------------------------------------------
# Scan: clean kernel
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Scan: violations
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Scan: false-positive guards
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Canon cross-check: opt-out downgrades severity
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Scope: plugins live under a different axis
# ---------------------------------------------------------------------------


def test_mp1_scope_is_kernel_only(tmp_path: Path) -> None:
    """``.myco/plugins/`` files are not MP1's concern (MF2 territory)."""
    ctx = _seed_substrate(tmp_path)
    plugins = tmp_path / ".myco" / "plugins" / "handlers"
    plugins.mkdir(parents=True)
    (plugins / "bad.py").write_text("import openai\n", encoding="utf-8")
    findings = list(MP1NoProviderImports().run(ctx))
    assert findings == []
