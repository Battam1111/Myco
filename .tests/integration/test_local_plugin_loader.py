"""Integration tests for the substrate-local plugin loader (L0 P5).

Background
----------

L0 principle 5 says substrates extend along two orthogonal axes:

- **Per-substrate** (``<root>/.myco/plugins/``) — project-specific
  dimensions, adapters, schema_upgraders, and overlay verbs that
  belong to *this* substrate.
- **Per-host** (``boundary/install/clients.py::JsonClientSpec``
  table) — host-process integrations (CLAUDE.md writers, Cowork
  plugin bundler, etc.) shared across every substrate the host
  opens. (The v0.6.0 ``boundary/host_integration/`` adapter package
  was excreted at v0.8.5 as never-wired-into-production.)

The per-substrate axis has been wired since v0.5.3 (the AD1 dim
recognises ``.myco/plugins/``; ``Substrate.load`` auto-imports the
package; ``hunger.local_plugins`` and ``brief`` summarise its
contributions; ``graft`` enumerates and validates) but no production
plugin had ever shipped against it as of v0.7.5 — the v0.7.5 brief
reports ``local_plugins.count: 0`` because no substrate in the wild
was exercising the axis. This integration suite ships the first one,
the ``example_overlay`` reference plugin, and pins the contract end-
to-end.

Plugin layout under test
------------------------

::

    tests/integration/fixtures/.myco/
    ├── manifest_overlay.yaml         (declares example-echo overlay verb)
    └── plugins/
        ├── __init__.py               (loader entry — imports example_overlay)
        └── example_overlay/
            ├── __init__.py           (validates plugin.json, registers XYZ1,
            │                          exposes example_echo_handler)
            ├── plugin.json           (manifest)
            └── xyz1_raw_note_threshold.py  (SEMANTIC/LOW dim,
                                              fires when raw_backlog > 100)

Each test below germinates a tmp substrate, copies the fixture's
``.myco/`` tree into it, and exercises one slice of the loader
contract. The ``_isolated_plugin_state`` fixture wipes both
``_EXTERNAL_DIMENSION_CLASSES`` and the ``sys.modules`` entry that
``load_local_plugins`` registers, so each test sees a clean process
state regardless of run order or pytest-xdist parallelism.
"""

from __future__ import annotations

import json
import shutil
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from myco.boundary.surface.manifest import (
    dispatch,
    load_manifest_with_overlay,
)
from myco.core.identity_cluster import MycoContext
from myco.core.substrate_cluster import (
    Substrate,
    _substrate_plugin_module_name,
    load_local_plugins,
)
from myco.cycle.canon_cluster import graft_run
from myco.germination import bootstrap
from myco.homeostasis.kernel import run_immune
from myco.homeostasis.primitives_cluster import (
    _EXTERNAL_DIMENSION_CLASSES,
    default_registry,
)
from myco.ingestion.capture_cluster import compose_hunger_report

# ---------------------------------------------------------------------------
# Fixture paths — the reference plugin tree lives next to this test module.
# ---------------------------------------------------------------------------


FIXTURE_MYCO: Path = Path(__file__).resolve().parent / "fixtures" / ".myco"
FIXTURE_OVERLAY_PLUGIN: Path = FIXTURE_MYCO / "plugins" / "example_overlay"


# ---------------------------------------------------------------------------
# Process-state isolation — _EXTERNAL_DIMENSION_CLASSES is module-global
# and ``sys.modules`` caches plugin packages across tests. Wipe both
# before AND after every test so XYZ1 registrations do not leak between
# tests (they must look like a fresh process to default_registry()).
# ---------------------------------------------------------------------------


def _purge_substrate_plugin_modules() -> None:
    """Drop every ``myco._substrate_plugins_*`` entry from sys.modules.

    The loader registers each substrate's plugin package under a
    process-unique name derived from the substrate root path — so two
    tests pointing at different tmp substrates never collide on the
    same key. But within a single test, a re-load must observe a fresh
    import; popping the cached module forces ``importlib`` to re-run
    the package body and trigger registration side-effects again.
    """
    for key in list(sys.modules):
        if key.startswith("myco._substrate_plugins_"):
            sys.modules.pop(key, None)


@pytest.fixture(autouse=True)
def _isolated_plugin_state() -> Iterator[None]:
    """Reset per-process plugin registries before AND after each test."""
    _EXTERNAL_DIMENSION_CLASSES.clear()
    _purge_substrate_plugin_modules()
    try:
        yield
    finally:
        _EXTERNAL_DIMENSION_CLASSES.clear()
        _purge_substrate_plugin_modules()


# ---------------------------------------------------------------------------
# Substrate construction — germinate a fresh tmp substrate, then copy
# the fixture .myco tree into it. ``copytree(dirs_exist_ok=True)`` lets
# each test optionally pre-create ``.myco/`` first (e.g. to inject a
# broken __init__.py for the malformed-plugin test) without colliding
# with the copy.
# ---------------------------------------------------------------------------


def _make_substrate_with_plugin(
    root: Path,
    *,
    plugin_src: Path = FIXTURE_MYCO,
    extra_raw_notes: int = 0,
) -> MycoContext:
    """Germinate ``root`` and copy ``plugin_src`` into ``<root>/.myco/``.

    Returns a fresh :class:`MycoContext`. Optionally seeds ``<root>/
    notes/raw/`` with ``extra_raw_notes`` placeholder ``.md`` files so
    XYZ1's threshold (>100) can be exercised both ways.
    """
    bootstrap(project_dir=root, substrate_id="local-plugin-test")

    # Copy the fixture .myco tree on top of whatever bootstrap created.
    # ``germinate`` does not write under .myco/ so this is a clean copy
    # with no overlap; ``dirs_exist_ok=True`` covers the (rare) case
    # where a future template change starts seeding .myco/.
    target_myco = root / ".myco"
    if plugin_src.is_dir():
        shutil.copytree(plugin_src, target_myco, dirs_exist_ok=True)

    if extra_raw_notes > 0:
        raw_dir = root / "notes" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        for i in range(extra_raw_notes):
            (raw_dir / f"note_{i:04d}.md").write_text(
                f"# raw note {i}\n\nfixture content\n", encoding="utf-8"
            )

    # Reload the substrate so the loader picks up the freshly-copied
    # plugin tree. Build a context the handlers expect.
    return MycoContext.for_testing(root=root)


# ---------------------------------------------------------------------------
# Test 1 — myco hunger reports the plugin
# ---------------------------------------------------------------------------


def test_local_plugin_loader_discovers_example_overlay(tmp_path: Path) -> None:
    """A tmp substrate that ships the fixture plugin must surface it on
    ``hunger.local_plugins``: count >=1, dimension count==1, overlay
    verb list contains ``example-echo``. This is the v0.7.5 gap-closure
    test — the brief used to report ``local_plugins.count: 0`` because
    no substrate exercised the axis."""
    ctx = _make_substrate_with_plugin(tmp_path)

    report = compose_hunger_report(ctx)
    summary = report.local_plugins

    assert summary.count >= 1, (
        f"hunger.local_plugins.count should be >=1, "
        f"got {summary.count} (errors={list(summary.errors)})"
    )
    # XYZ1 dimension + the overlay verb together count as 2.
    assert summary.count_by_kind["dimension"] == 1, summary.count_by_kind
    assert summary.count_by_kind["overlay_verb"] == 1, summary.count_by_kind
    assert summary.count_by_kind["adapter"] == 0
    assert summary.count_by_kind["schema_upgrader"] == 0
    assert list(summary.overlay_verbs) == ["example-echo"], summary.overlay_verbs
    assert summary.errors == ()  # no errors on a happy-path load.

    # The graft --list path agrees: scope=substrate for both contributions.
    list_result = graft_run({"list": True}, ctx=ctx)
    substrate_scoped = [
        e for e in list_result.payload["plugins"] if e["scope"] == "substrate"
    ]
    names = sorted(e["name"] for e in substrate_scoped)
    assert names == ["XYZ1", "example-echo"], names


# ---------------------------------------------------------------------------
# Test 2 — overlay verb is callable end-to-end via manifest dispatch
# ---------------------------------------------------------------------------


def test_overlay_verb_callable_via_graft(tmp_path: Path) -> None:
    """``example-echo`` resolves through the live manifest+overlay loader
    and reaches ``example_echo_handler`` with the supplied message.

    The user prompt mentions ``myco_graft`` for this leg — but ``graft``
    is the *audit* verb, not a dispatcher. The actual dispatch path for
    overlay verbs is :func:`myco.boundary.surface.manifest.dispatch`,
    which builds the effective manifest via
    ``load_manifest_with_overlay`` and resolves the handler module via
    ``importlib``. We exercise that path here (it's what the CLI and
    MCP surface call too) and use ``graft`` separately to confirm the
    overlay verb shows up in the introspection list.
    """
    ctx = _make_substrate_with_plugin(tmp_path)

    # ``graft --explain example-echo`` confirms the overlay verb is
    # registered with scope=substrate before we try to dispatch it.
    explain = graft_run({"explain": "example-echo"}, ctx=ctx)
    assert explain.exit_code == 0
    assert explain.payload["kind"] == "overlay_verb"
    assert explain.payload["name"] == "example-echo"

    # Now actually invoke the verb via the live dispatcher. We pass
    # ``ctx`` so ``dispatch`` doesn't try to walk up from ``cwd`` —
    # tmp_path isn't on the harness cwd path on Windows runners.
    result = dispatch(
        "example-echo",
        {"message": "hello from L0 P5"},
        ctx=ctx,
    )
    assert result.exit_code == 0
    assert result.payload["verb"] == "example-echo"
    assert result.payload["message"] == "hello from L0 P5"
    assert result.payload["echoed"] == "hello from L0 P5"
    assert result.payload["plugin"] == "example_overlay"
    assert result.payload["plugin_version"] == "0.1.0"


# ---------------------------------------------------------------------------
# Test 3 — XYZ1 fires above the threshold
# ---------------------------------------------------------------------------


def test_overlay_dim_fires_on_threshold(tmp_path: Path) -> None:
    """Substrate with 101 raw notes + the fixture plugin must produce
    one XYZ1 finding when immune runs."""
    ctx = _make_substrate_with_plugin(tmp_path, extra_raw_notes=101)

    registry = default_registry()
    assert registry.has("XYZ1"), (
        f"XYZ1 not registered; registry.all() = {[d.id for d in registry.all()]}"
    )

    immune_result = run_immune(ctx, registry, exit_on="never", fix=False)
    xyz1_findings = [f for f in immune_result.findings if f.dimension_id == "XYZ1"]
    assert len(xyz1_findings) == 1, [
        (f.dimension_id, f.message) for f in immune_result.findings
    ]
    finding = xyz1_findings[0]
    assert "101" in finding.message
    assert finding.path == "notes/raw/"
    assert finding.severity.label() == "low"
    assert finding.category.value == "semantic"


# ---------------------------------------------------------------------------
# Test 4 — XYZ1 silent below the threshold
# ---------------------------------------------------------------------------


def test_overlay_dim_silent_below_threshold(tmp_path: Path) -> None:
    """Substrate with 50 raw notes + the fixture plugin must NOT emit
    any XYZ1 finding (50 <= 100 threshold)."""
    ctx = _make_substrate_with_plugin(tmp_path, extra_raw_notes=50)

    registry = default_registry()
    assert registry.has("XYZ1")

    immune_result = run_immune(ctx, registry, exit_on="never", fix=False)
    xyz1_findings = [f for f in immune_result.findings if f.dimension_id == "XYZ1"]
    assert xyz1_findings == [], xyz1_findings


# ---------------------------------------------------------------------------
# Test 5 — malformed plugin surfaces as hunger error, immune still runs
# ---------------------------------------------------------------------------


def test_malformed_plugin_reports_error_in_brief_not_crash(
    tmp_path: Path,
) -> None:
    """A plugin whose ``__init__.py`` raises on import must:

    1. NOT brick ``Substrate.load`` (the load returns; errors are
       captured on ``local_plugin_errors`` per the v0.5.3 contract).
    2. Surface in ``hunger.local_plugins.errors`` so ``brief`` shows it
       to the operator.
    3. Leave the immune kernel runnable — a broken plugin is loud, not
       fatal (homeostasis doctrine § "substrate-local plugin health").

    We construct a substrate with a deliberately-broken
    ``.myco/plugins/__init__.py`` (raises ImportError on import). The
    fixture plugin is NOT used here — we want to test the failure
    mode, not the happy path.
    """
    bootstrap(project_dir=tmp_path, substrate_id="malformed-plugin-test")
    plugins_dir = tmp_path / ".myco" / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    # Syntactically valid Python that raises at import time — covers
    # the most realistic failure mode (a real plugin's logic crashes
    # during registration). A SyntaxError would also work but tests
    # the parser; this tests the loader's exception capture.
    (plugins_dir / "__init__.py").write_text(
        'raise ImportError("intentional breakage for malformed plugin test")\n',
        encoding="utf-8",
    )

    # 1. Substrate.load() captures the error rather than raising.
    sub = Substrate.load(tmp_path)
    assert sub.local_plugins_loaded is False
    assert sub.local_plugin_errors, sub.local_plugin_errors
    err_text = " ".join(sub.local_plugin_errors)
    assert "ImportError" in err_text or "intentional breakage" in err_text

    # 2. hunger.local_plugins.errors carries the error too (it reads
    # from Substrate.local_plugin_errors and from any enumeration
    # hiccup at compose-time).
    ctx = MycoContext.for_testing(substrate=sub)
    report = compose_hunger_report(ctx)
    assert report.local_plugins.errors, report.local_plugins.errors
    assert any(
        "ImportError" in e or "intentional breakage" in e
        for e in report.local_plugins.errors
    )
    # And no contributions counted, since registration never ran.
    assert report.local_plugins.count == 0
    assert report.local_plugins.count_by_kind["dimension"] == 0

    # 3. Immune still runs — the broken plugin doesn't poison the run.
    # A clean process never registered XYZ1, so the registry contains
    # only kernel dimensions; we just check no exception escapes.
    registry = default_registry()
    immune_result = run_immune(ctx, registry, exit_on="never", fix=False)
    # The kernel produced *some* result (its findings/exit_code
    # depend on what the freshly-germinated substrate looks like, so
    # we don't pin specific findings — just the absence of a crash).
    assert immune_result.exit_code in (0, 1, 2)


# ---------------------------------------------------------------------------
# Test 6 — plugin manifest required-field validation
# ---------------------------------------------------------------------------


def test_plugin_manifest_required_fields_validated(tmp_path: Path) -> None:
    """A plugin.json with a missing required field (``name``) must cause
    the plugin to surface a ContractError on ``hunger.local_plugins.errors``.

    We copy the happy-path fixture, then mutate plugin.json to drop the
    ``name`` field (writing a clean JSON object without it). The
    plugin's ``__init__.py`` re-runs ``_load_and_validate_manifest``
    on import and raises ``ContractError`` with a message that names
    the missing field — the error then flows through the loader's
    capture path into ``local_plugins.errors``.
    """
    ctx = _make_substrate_with_plugin(tmp_path)

    # Mutate the manifest in-place to drop the ``name`` field.
    manifest_path = tmp_path / ".myco" / "plugins" / "example_overlay" / "plugin.json"
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw.pop("name")
    manifest_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")

    # ``graft --validate`` only pops the top-level substrate plugin
    # package from ``sys.modules`` before re-importing it; submodules
    # like ``...example_overlay`` remain cached, so the mutated
    # plugin.json would never be re-read. The operator-equivalent
    # workflow is "edit the plugin, restart the process, run hunger
    # again" — to simulate that within one test we wipe the whole
    # subtree of cached substrate-plugin submodules. ``_EXTERNAL_-
    # DIMENSION_CLASSES`` is also drained so XYZ1 doesn't re-register
    # at the new (broken) import (the broken __init__.py raises before
    # ``register_external_dimension`` is reached, but if we left the
    # earlier registration in place graft --validate would see XYZ1
    # already present).
    _purge_substrate_plugin_modules()
    _EXTERNAL_DIMENSION_CLASSES.clear()

    # Now graft --validate forces a clean re-import. The plugin's
    # __init__.py runs _load_and_validate_manifest, which raises
    # ContractError because ``name`` is missing — the loader captures
    # that on the LoadResult.errors tuple, which surfaces here.
    validate_result = graft_run({"validate": True}, ctx=ctx)
    assert validate_result.exit_code == 1, validate_result.payload
    errors = validate_result.payload["errors"]
    assert errors, errors
    err_text = " ".join(errors)
    assert "name" in err_text, err_text
    # The error message should name the offending plugin so the
    # operator knows what to fix without reading source.
    assert "example_overlay" in err_text or "plugin.json" in err_text, err_text

    # And hunger sees the same error (it reads from
    # Substrate.local_plugin_errors, which graft --validate just
    # re-populated). Purge again so the second Substrate.load below
    # observes a clean process state — otherwise it returns the
    # cached LoadResult with no errors.
    _purge_substrate_plugin_modules()
    _EXTERNAL_DIMENSION_CLASSES.clear()
    sub = Substrate.load(tmp_path)
    assert sub.local_plugin_errors, sub.local_plugin_errors
    hunger_ctx = MycoContext.for_testing(substrate=sub)
    report = compose_hunger_report(hunger_ctx)
    assert report.local_plugins.errors


# ---------------------------------------------------------------------------
# Bonus — proves the overlay verb name appears in load_manifest_with_overlay
# (the manifest layer is what dispatch() calls on every verb invocation;
# this covers the ``manifest_overlay.yaml`` parse path explicitly).
# ---------------------------------------------------------------------------


def test_overlay_verb_appears_in_effective_manifest(tmp_path: Path) -> None:
    """``load_manifest_with_overlay(<root>)`` returns a manifest whose
    ``commands`` tuple contains the fixture's ``example-echo`` verb,
    and the verb's handler resolves to a real callable."""
    _make_substrate_with_plugin(tmp_path)

    # Pop the cached load_manifest result is not needed; the lru_cache
    # is on load_manifest (the packaged base, no per-substrate state),
    # and load_manifest_with_overlay is NOT cached so it re-reads the
    # overlay file on every call.
    manifest = load_manifest_with_overlay(tmp_path)
    names = manifest.names()
    assert "example-echo" in names, names

    spec = manifest.by_name("example-echo")
    assert spec.handler == "plugins.example_overlay:example_echo_handler"
    assert spec.subsystem == "ext"
    assert spec.mcp_tool == "myco_example_echo"
    # Required arg must be declared so dispatch's UsageError fires
    # cleanly when callers omit it.
    arg_names = [a.name for a in spec.args]
    assert arg_names == ["message"]
    assert spec.args[0].required is True
    assert spec.args[0].type == "str"


# ---------------------------------------------------------------------------
# Bonus — load_local_plugins direct contract (idempotent across reloads)
# ---------------------------------------------------------------------------


def test_load_local_plugins_idempotent_across_reloads(tmp_path: Path) -> None:
    """The loader is documented as idempotent: a second
    :func:`load_local_plugins` call against the same root returns the
    cached module (``loaded=True``, no errors, same module name)."""
    _make_substrate_with_plugin(tmp_path)

    sub = Substrate.load(tmp_path)
    assert sub.local_plugins_loaded is True
    assert sub.local_plugin_errors == ()

    expected_mod_name = _substrate_plugin_module_name(tmp_path, sub.canon)
    assert sub.local_plugins_module == expected_mod_name
    assert expected_mod_name in sys.modules

    # Re-call the loader. The substrate plugin module is in sys.modules
    # so the loader returns the cached LoadResult without re-running
    # the package body.
    result_again = load_local_plugins(tmp_path, canon=sub.canon)
    assert result_again.loaded is True
    assert result_again.errors == ()
    assert result_again.module_name == expected_mod_name
