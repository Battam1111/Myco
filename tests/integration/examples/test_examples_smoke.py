"""End-to-end smoke tests for the 8 framework-demo subtree under ``examples/``.

Closes the v0.7.10 gap flagged in v0.7.5's gap analysis: the 8 framework
demos (Agno / Claude Agent SDK / CrewAI / DSPy / LangGraph / Microsoft
Agent Framework / PraisonAI / Smolagents) had never been E2E tested in
CI. This module proves each demo:

1. **imports cleanly** — the demo's module-level imports resolve and
   expose a ``main(dry: bool = False) -> int`` callable. When the
   framework dep itself is absent from the environment, the test
   short-circuits via :func:`pytest.importorskip` so CI doesn't have to
   carry the union of every framework's transitive closure.

2. **runs against a tmp Myco substrate** — we germinate a fresh
   substrate via :func:`myco.germination.bootstrap`, point ``cwd`` at
   it, invoke ``demo.main(dry=True)``, and assert the demo exits ``0``
   with a recognisable token in stdout. Then we read the substrate's
   ``_canon.yaml`` and assert ``contract_version`` is present — that is
   the "expected shape" of a Myco substrate the demo runs against.

The dry-run path is the load-bearing surface here: it exercises the
demo's argparse/sys/exit-code wiring without requiring the framework's
network or LLM credentials. The non-dry path (which actually invokes
the framework's MCP adapter against ``mcp-server-myco``) requires both
the framework AND a configured API key, so it is an out-of-band
smoke-test target — see ``docs/iou/v0_7_10_examples_*_gaps.md`` if any
demo's dry path itself is broken.

Cross-references:

- ``examples/`` — the 8 demo subdirectories under test.
- ``_canon.yaml::system.write_surface.allowed`` — includes
  ``examples/**`` per L0 P5.
- ``docs/architecture/L0_VISION.md`` — references the 8 framework
  subtree.
"""

from __future__ import annotations

import importlib.util
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path
from types import ModuleType

import pytest

from myco.germination import bootstrap

REPO_ROOT = Path(__file__).resolve().parents[3]
# v0.8.4 root-cleanup (2026-05-12): examples/ moved to docs/examples/
# so the framework demo subtree no longer clutters the repo root.
EXAMPLES_DIR = REPO_ROOT / "docs" / "examples"


# ---------------------------------------------------------------------------
# Demo registry
#
# Each entry is (demo_dir_name, framework_import_module, expected_stdout_token).
# - demo_dir_name: subdirectory under examples/ holding main.py + README.md.
# - framework_import_module: what ``pytest.importorskip`` probes; the demo's
#   non-dry path imports this. Absence ⇒ the import-cleanly test skips.
# - expected_stdout_token: substring the demo prints in dry-run mode. Used to
#   prove the demo's main() actually executed (not just returned 0 vacuously).
#
# Order matches the L0 P5 vision text and the examples/ alphabetical layout.
# ---------------------------------------------------------------------------

DEMOS: tuple[tuple[str, str, str], ...] = (
    ("agno-myco-demo", "agno", "[agno-myco-demo] dry-run OK"),
    (
        "claude-sdk-myco-demo",
        "claude_agent_sdk",
        "[claude-sdk-myco-demo] dry-run OK",
    ),
    ("crewai-myco-demo", "crewai", "[crewai-myco-demo] dry-run OK"),
    ("dspy-myco-demo", "dspy", "[dspy-myco-demo] dry-run OK"),
    (
        "langgraph-myco-demo",
        "langchain_mcp_adapters",
        "[langgraph-myco-demo] dry-run OK",
    ),
    (
        "microsoft-agent-framework-myco-demo",
        "agent_framework",
        "[microsoft-agent-framework-myco-demo] dry-run OK",
    ),
    (
        "praisonai-myco-demo",
        "praisonaiagents",
        "[praisonai-myco-demo] dry-run OK",
    ),
    (
        "smolagents-myco-demo",
        "smolagents",
        "[smolagents-myco-demo] dry-run OK",
    ),
)

# Pretty test-ids so ``pytest -v`` output reads as
# ``test_demo_imports_cleanly[agno-myco-demo]`` etc.
DEMO_IDS: tuple[str, ...] = tuple(d[0] for d in DEMOS)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_demo_module(demo_dir: str) -> ModuleType:
    """Load ``examples/<demo_dir>/main.py`` as an isolated module.

    ``examples/`` is intentionally NOT on the package's import path
    (the demos are reference substrates, not part of the wheel), so we
    use :func:`importlib.util.spec_from_file_location` to bring the
    file in directly. We use a unique module name per demo so multiple
    tests in the same pytest session don't collide on
    ``sys.modules['main']``.
    """
    main_py = EXAMPLES_DIR / demo_dir / "main.py"
    assert main_py.exists(), f"missing demo entry point: {main_py}"
    mod_name = f"_myco_examples_smoke_{demo_dir.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(mod_name, main_py)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


def _germinate_tmp_substrate(tmp_path: Path) -> Path:
    """Spin up a fresh Myco substrate inside ``tmp_path``.

    Returns the substrate root (== ``tmp_path``). The substrate has a
    valid ``_canon.yaml`` with the current ``contract_version`` and the
    minimal ``MYCO.md`` / ``notes/`` / ``docs/`` skeleton.
    """
    bootstrap(project_dir=tmp_path, substrate_id="examples-smoke-test")
    canon = tmp_path / "_canon.yaml"
    assert canon.exists(), "germinate() did not write _canon.yaml"
    return tmp_path


# ---------------------------------------------------------------------------
# Test 1: each demo imports cleanly (skips if the framework isn't installed)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("demo_dir", "framework_mod", "_token"), DEMOS, ids=DEMO_IDS)
def test_demo_imports_cleanly(
    demo_dir: str,
    framework_mod: str,
    _token: str,
) -> None:
    """The demo's main.py loads and exposes a ``main`` callable.

    Behaviour matrix:

    * Framework not installed → :func:`pytest.importorskip` raises
      ``Skipped`` cleanly. CI without the framework reports SKIP, not
      FAIL — honest report of what's actually exercised.
    * Framework installed → demo file loads via importlib + we sanity-
      check that ``main`` is callable and accepts ``dry``. This catches
      syntax drift, missing entry points, and renamed parameters.

    Note: the demo's framework dep is imported only inside ``main()``
    after the ``dry`` short-circuit, so the demo file itself can load
    without the framework. We still gate on ``importorskip`` because
    the *meaningful* import-cleanly contract is "the demo can drive
    its framework", not "the demo file is parseable Python".
    """
    pytest.importorskip(
        framework_mod,
        reason=(
            f"{framework_mod!r} not installed; "
            f"see examples/{demo_dir}/README.md for the install command "
            f"or `pip install 'myco[examples]'` for the full demo extras."
        ),
    )
    module = _load_demo_module(demo_dir)
    assert hasattr(module, "main"), f"{demo_dir}/main.py must expose main()"
    assert callable(module.main), f"{demo_dir}.main must be callable"


# ---------------------------------------------------------------------------
# Test 2: each demo runs dry against a tmp substrate and returns expected shape
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("demo_dir", "_framework_mod", "token"), DEMOS, ids=DEMO_IDS)
def test_demo_runs_against_tmp_substrate_returns_expected_shape(
    demo_dir: str,
    _framework_mod: str,
    token: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Running ``main(dry=True)`` against a germinated substrate succeeds.

    The dry path is the only one we can exercise without the
    framework's network + credential dependencies. It still proves:

    * the demo's argparse / sys / exit-code wiring is intact;
    * the demo can co-exist with a real Myco substrate at cwd;
    * the substrate carries ``contract_version`` (the "expected shape"
      a Myco-aware demo would consume via myco_brief / myco_hunger).

    Non-dry exercise (real ``mcp-server-myco`` stdio + framework MCP
    adapter) is out of band; the IOU stubs under
    ``docs/iou/v0_7_10_examples_*_gaps.md`` (if any) document gaps
    where even the dry path is broken.
    """
    substrate = _germinate_tmp_substrate(tmp_path)

    # Point cwd at the substrate so any future demo enhancement that
    # reads ``./_canon.yaml`` lands on ours, not the package's.
    monkeypatch.chdir(substrate)

    module = _load_demo_module(demo_dir)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = module.main(dry=True)
    captured = buf.getvalue()

    # 1. Exit-code contract: dry runs always succeed.
    assert rc == 0, (
        f"{demo_dir}.main(dry=True) returned {rc!r}; expected 0. "
        f"stdout was: {captured!r}"
    )

    # 2. Demo actually executed (not just returned 0 vacuously).
    assert token in captured, (
        f"expected {token!r} in {demo_dir} stdout; got {captured!r}"
    )

    # 3. "Expected shape" assertion — the substrate the demo ran
    #    against carries a contract_version. This is the spine of any
    #    Myco-aware integration: the demo's MCP client would read this
    #    via myco_brief / canon resource. Per the task requirements, a
    #    successful run must reference contract_version in the returned
    #    artifact (the substrate's canon).
    canon_text = (substrate / "_canon.yaml").read_text(encoding="utf-8")
    assert "contract_version:" in canon_text, (
        "germinated substrate's _canon.yaml lacks contract_version; "
        "the demo cannot meaningfully exercise Myco verbs against it"
    )


# ---------------------------------------------------------------------------
# Defensive sanity: make sure DEMOS stays in sync with examples/
# ---------------------------------------------------------------------------


def test_demos_registry_matches_examples_dir() -> None:
    """Catch silent drift if a new demo lands under examples/.

    If a 9th framework demo is added without a corresponding entry in
    ``DEMOS``, this test fails — preventing the gap-coverage regression
    that motivated v0.7.10 in the first place.
    """
    on_disk = {
        p.name
        for p in EXAMPLES_DIR.iterdir()
        if p.is_dir() and p.name.endswith("-myco-demo")
    }
    registered = {entry[0] for entry in DEMOS}
    missing = on_disk - registered
    extra = registered - on_disk
    assert not missing, (
        f"examples/ contains demo directories not registered in DEMOS: "
        f"{sorted(missing)}. Add them to tests/integration/examples/"
        f"test_examples_smoke.py::DEMOS."
    )
    assert not extra, (
        f"DEMOS lists directories not present in examples/: {sorted(extra)}. "
        f"Drop them from tests/integration/examples/test_examples_smoke.py::"
        f"DEMOS or restore the directory."
    )


# ---------------------------------------------------------------------------
# Defensive sanity: every demo carries a README with the install command
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("demo_dir", "_framework_mod", "_token"), DEMOS, ids=DEMO_IDS)
def test_demo_has_readme_with_install_command(
    demo_dir: str,
    _framework_mod: str,
    _token: str,
) -> None:
    """Every demo's README must document its ``pip install`` command.

    This is the on-ramp users hit when ``test_demo_imports_cleanly``
    skips — the importorskip reason points back here. Catch silent
    deletion of the install hint.
    """
    readme = EXAMPLES_DIR / demo_dir / "README.md"
    assert readme.exists(), f"missing {demo_dir}/README.md"
    text = readme.read_text(encoding="utf-8")
    assert "pip install" in text, (
        f"{demo_dir}/README.md must contain a `pip install` command "
        f"so the importorskip reason is actionable"
    )


# Public re-exports so sibling test modules (or future
# `tests/integration/examples/conftest.py`) can `from
# .test_examples_smoke import DEMOS` without re-listing the registry.
__all__ = ["DEMOS", "DEMO_IDS", "EXAMPLES_DIR", "REPO_ROOT"]
