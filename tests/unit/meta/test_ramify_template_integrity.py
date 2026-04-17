"""Regression test for v0.5.4 bug #7.

``ramify`` writes a ``.myco/plugins/dimensions/__init__.py`` that calls
``register_external_dimension`` on every Dimension subclass it finds in
the subpackage. Before v0.5.4 the template contained ``{{__name__}}``
(double braces intended for a ``.format`` call that never happened);
the generated code therefore tried to import a module literally named
``{__name__}.local1``, raised ``ModuleNotFoundError``, and the outer
plugins/__init__.py silently swallowed the exception — every substrate-
local dimension registered via ``ramify`` was invisible to
``default_registry()`` and ``graft --list``.

This test pins the fixed template shape by rendering ramify into a
tmp substrate, importing the generated ``dimensions/__init__.py``
under a synthetic module name, and asserting ``register_all`` runs
without raising.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from myco.core.context import MycoContext
from myco.cycle.ramify import run as ramify_run


def _ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


def test_dimensions_init_template_imports_cleanly(
    genesis_substrate: Path,
) -> None:
    """After ramify --dimension, the generated dimensions/__init__.py
    imports its siblings via an f-string that resolves the current
    package name — not the literal token ``{__name__}``."""
    ctx = _ctx(genesis_substrate)
    # genesis_substrate's substrate_id is "test-substrate" so the
    # autodetect picks substrate-local mode for dimension ramify.
    result = ramify_run(
        {
            "dimension": "DT1",
            "category": "mechanical",
            "severity": "low",
            "verb": None,
            "adapter": None,
            "extensions": [],
            "substrate_local": True,
            "force": False,
        },
        ctx=ctx,
    )
    assert result.exit_code == 0
    assert result.payload["written"] is True

    pkg_init = genesis_substrate / ".myco" / "plugins" / "__init__.py"
    dims_init = genesis_substrate / ".myco" / "plugins" / "dimensions" / "__init__.py"
    dims_leaf = genesis_substrate / ".myco" / "plugins" / "dimensions" / "dt1.py"
    assert pkg_init.is_file()
    assert dims_init.is_file()
    assert dims_leaf.is_file()

    # The generated file must NOT carry the literal f-string escape
    # that caused bug #7.
    dims_body = dims_init.read_text(encoding="utf-8")
    assert "{{__name__}}" not in dims_body, (
        "dimensions/__init__.py still has the broken double-brace "
        "template; bug #7 has regressed"
    )
    assert "f\"{__name__}." in dims_body, (
        "dimensions/__init__.py should reference __name__ via a real "
        "f-string"
    )


def test_substrate_load_auto_imports_dimension(
    genesis_substrate: Path,
) -> None:
    """After ramify writes a substrate-local dimension, reloading the
    substrate must register the dimension via
    ``register_external_dimension`` so ``default_registry`` surfaces it."""
    # First run ramify to create the plugin.
    ctx = _ctx(genesis_substrate)
    ramify_run(
        {
            "dimension": "DT2",
            "category": "semantic",
            "severity": "medium",
            "verb": None,
            "adapter": None,
            "extensions": [],
            "substrate_local": True,
            "force": False,
        },
        ctx=ctx,
    )

    # Then reload the substrate (simulating a fresh CLI process).
    # Clear any previous plugin-module residue to force a real import.
    from myco.core.substrate import Substrate, _substrate_plugin_module_name
    from myco.homeostasis.registry import _EXTERNAL_DIMENSION_CLASSES

    # Reset external-registration state so this test is independent
    # of ordering.
    _EXTERNAL_DIMENSION_CLASSES.clear()
    mod_name = _substrate_plugin_module_name(
        genesis_substrate, ctx.substrate.canon
    )
    sys.modules.pop(mod_name, None)

    fresh = Substrate.load(genesis_substrate)
    assert fresh.local_plugins_loaded is True
    assert not fresh.local_plugin_errors, fresh.local_plugin_errors

    from myco.homeostasis.registry import default_registry

    reg = default_registry()
    assert reg.has("DT2"), (
        f"substrate-local dimension DT2 not registered; "
        f"registry.all() = {[d.id for d in reg.all()]}"
    )
