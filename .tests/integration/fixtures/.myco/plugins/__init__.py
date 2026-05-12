"""Substrate-local plugin entry point — reference fixture.

This file is what :func:`myco.core.substrate.load_local_plugins` imports
when a substrate copies this fixture tree into its own ``.myco/``. The
loader keys off ``<substrate_root>/.myco/plugins/__init__.py``; whatever
this module does at import time is the substrate's per-substrate
extensibility surface.

Single responsibility: import the ``example_overlay`` subpackage so its
side-effect registration (one dimension via
:func:`myco.homeostasis.registry.register_external_dimension`; one
overlay-verb handler exposed at module attribute
``example_echo_handler``) fires inside the loader's isolated module
namespace.

If ``example_overlay`` raises on import, the exception propagates to
:func:`load_local_plugins`, which captures it on
``Substrate.local_plugin_errors`` (and surfaces it on the next
``myco hunger`` call as ``local_plugins.errors``). That's the L0 P5
"per-substrate axis" promise made concrete: a broken plugin is loud,
not silent.
"""

from __future__ import annotations

from . import example_overlay as _example_overlay  # noqa: F401  (side-effect import)
