"""Built-in lint dimensions + entry-points discovery.

One module per dimension. Discovery is driven by
``importlib.metadata.entry_points(group="myco.dimensions")`` at v0.5+
(per ``docs/primordia/v0_5_0_major_6_10_craft_2026-04-17.md`` MAJOR 6).
Third-party substrates (symbionts) register their own dimensions by
declaring ``[project.entry-points."myco.dimensions"]`` in their
``pyproject.toml`` — no code edit to Myco required.

The ``_BUILT_IN`` tuple below mirrors the entry-points table in
Myco's ``pyproject.toml``. It serves as a **fallback** for checkouts
that have not been ``pip install -e .``'d (where entry-points
metadata has not been materialized). When the fallback fires, a
``DeprecationWarning`` is emitted so dev-mode users know to install.

Dimension categories (v0.5):

- **Mechanical** — M1 (canon identity), M2 (entry-point exists),
  M3 (write-surface declared), MF1 (declared subsystems exist),
  MF2 (substrate-local plugin health), MP1 (no LLM provider imports
  in the substrate kernel — v0.5.6 mycelium-purity seam),
  **v0.5.8**: MP2 (same purity, plugin scope), DC1-DC4 (docstring
  hygiene), CS1 (contract-version sync), FR1 (fresh-substrate
  invariants), PA1 (write-surface coverage), CG1/CG2 (code<->doctrine
  linkage), DI1 (discipline hooks).
- **Shipped**    — SH1 (package-version ref resolves).
- **Metabolic**  — MB1 (raw-note backlog), MB2 (nothing integrated yet),
  **v0.5.8**: MB3 (raw-notes high watermark).
- **Semantic**   — SE1 (dangling refs), SE2 (orphan integrated notes),
  **v0.5.8**: SE3 (graph self-cycle), RL1 (R1-R7 referenced).

Adding a built-in dimension: add the file, import the class here,
append to ``_BUILT_IN`` and ``__all__``, add a row to
``pyproject.toml::[project.entry-points."myco.dimensions"]``, and
write a test under ``tests/unit/homeostasis/dimensions/``.

Adding a third-party dimension: subclass ``myco.homeostasis.dimension
.Dimension``, publish a package that declares
``[project.entry-points."myco.dimensions"] my_id = "pkg.mod:MyClass"``,
and ``pip install`` it. Discovery is automatic.
"""

from __future__ import annotations

import warnings
from collections.abc import Iterator
from importlib.metadata import entry_points

from ..dimension import Dimension
from .cg1_doctrine_has_src_reference import CG1DoctrineHasSrcReference
from .cg2_subpackage_has_doctrine_link import CG2SubpackageHasDoctrineLink
from .cs1_contract_version_sync import CS1ContractVersionSync
from .dc1_module_docstring import DC1ModuleDocstring
from .dc2_public_function_docstring import DC2PublicFunctionDocstring
from .dc3_public_class_docstring import DC3PublicClassDocstring
from .dc4_module_doc_ref import DC4ModuleDocRef
from .di1_discipline_hooks_present import DI1DisciplineHooksPresent
from .fr1_fresh_substrate_invariants import FR1FreshSubstrateInvariants
from .m1_canon_identity_fields import M1CanonIdentityFields
from .m2_entry_point_exists import M2EntryPointExists
from .m3_write_surface_declared import M3WriteSurfaceDeclared
from .mb1_raw_notes_backlog import MB1RawNotesBacklog
from .mb2_no_integrated_yet import MB2NoIntegratedYet
from .mb3_raw_notes_high_watermark import MB3RawNotesHighWatermark
from .mf1_declared_subsystems_exist import MF1DeclaredSubsystemsExist
from .mf2_substrate_local_plugin_health import MF2SubstrateLocalPluginHealth
from .mp1_no_provider_imports import MP1NoProviderImports
from .mp2_plugin_provider_imports import MP2PluginProviderImports
from .pa1_write_surface_coverage import PA1WriteSurfaceCoverage
from .rl1_rules_referenced import RL1RulesReferenced
from .se1_dangling_refs import SE1DanglingRefs
from .se2_orphan_integrated import SE2OrphanIntegrated
from .se3_link_self_cycle import SE3LinkSelfCycle
from .sh1_package_version_ref import SH1PackageVersionRef

__all__ = [
    "ALL",
    "discover_dimension_classes",
    "M1CanonIdentityFields",
    "M2EntryPointExists",
    "M3WriteSurfaceDeclared",
    "MF1DeclaredSubsystemsExist",
    "MF2SubstrateLocalPluginHealth",
    "MP1NoProviderImports",
    "SH1PackageVersionRef",
    "MB1RawNotesBacklog",
    "MB2NoIntegratedYet",
    "SE1DanglingRefs",
    "SE2OrphanIntegrated",
    # v0.5.8 additions:
    "MP2PluginProviderImports",
    "DC1ModuleDocstring",
    "DC2PublicFunctionDocstring",
    "DC3PublicClassDocstring",
    "DC4ModuleDocRef",
    "CS1ContractVersionSync",
    "RL1RulesReferenced",
    "FR1FreshSubstrateInvariants",
    "PA1WriteSurfaceCoverage",
    "SE3LinkSelfCycle",
    "MB3RawNotesHighWatermark",
    "CG1DoctrineHasSrcReference",
    "CG2SubpackageHasDoctrineLink",
    "DI1DisciplineHooksPresent",
]


#: Built-in dimension classes shipped with Myco. Mirrors the entry-
#: points table in ``pyproject.toml``. Used as a fallback when
#: entry-points discovery returns empty (dev checkouts without
#: ``pip install -e .``).
_BUILT_IN: tuple[type[Dimension], ...] = (
    M1CanonIdentityFields,
    M2EntryPointExists,
    M3WriteSurfaceDeclared,
    MF1DeclaredSubsystemsExist,
    MF2SubstrateLocalPluginHealth,
    MP1NoProviderImports,
    SH1PackageVersionRef,
    MB1RawNotesBacklog,
    MB2NoIntegratedYet,
    SE1DanglingRefs,
    SE2OrphanIntegrated,
    # v0.5.8 additions:
    MP2PluginProviderImports,
    DC1ModuleDocstring,
    DC2PublicFunctionDocstring,
    DC3PublicClassDocstring,
    DC4ModuleDocRef,
    CS1ContractVersionSync,
    RL1RulesReferenced,
    FR1FreshSubstrateInvariants,
    PA1WriteSurfaceCoverage,
    SE3LinkSelfCycle,
    MB3RawNotesHighWatermark,
    CG1DoctrineHasSrcReference,
    CG2SubpackageHasDoctrineLink,
    DI1DisciplineHooksPresent,
)


#: Deprecated alias for :data:`_BUILT_IN`. Kept so existing code that
#: imported ``from myco.homeostasis.dimensions import ALL`` keeps
#: working. Third-party callers should switch to
#: :func:`discover_dimension_classes` or let
#: :func:`myco.homeostasis.registry.default_registry` handle it.
ALL: tuple[type[Dimension], ...] = _BUILT_IN


def discover_dimension_classes() -> tuple[type[Dimension], ...]:
    """Discover every registered dimension class.

    Order of precedence:

    1. ``importlib.metadata.entry_points(group="myco.dimensions")`` —
       this picks up both Myco's built-ins (once the package is
       installed, including editable installs via ``pip install -e .``)
       and any third-party packages that declare their own entries.
    2. Gap-fill: any ``_BUILT_IN`` class whose ``id`` was not already
       supplied by entry-points is appended. This protects dev
       checkouts whose ``pyproject.toml`` added a new dimension but
       whose installed metadata is still stale (common mid-release
       when the wheel hasn't been rebuilt). Previously this was only
       the full-empty fallback; v0.5.8 widens it to a per-id union so
       a single stale install doesn't drop the whole new dimension
       set.
    3. Full fallback: if entry-points returns empty AND _BUILT_IN has
       items, use _BUILT_IN and warn. This path is the dev-checkout
       "never installed" case.

    Broken entry-points (import errors, non-``Dimension`` loads) are
    skipped with a ``UserWarning`` rather than killing the immune
    kernel — a single bad third-party plugin must not brick lint.
    """
    discovered: list[type[Dimension]] = []
    seen_names: set[str] = set()
    seen_ids: set[str] = set()

    try:
        eps = entry_points(group="myco.dimensions")
    except TypeError:  # pragma: no cover — 3.9 and older shape
        eps = ()  # type: ignore[assignment]

    for ep in eps:
        try:
            cls = ep.load()
        except Exception as exc:
            warnings.warn(
                f"myco.dimensions entry-point {ep.name!r} failed to "
                f"load: {type(exc).__name__}: {exc}. Skipping.",
                UserWarning,
                stacklevel=2,
            )
            continue
        if not (isinstance(cls, type) and issubclass(cls, Dimension)):
            warnings.warn(
                f"myco.dimensions entry-point {ep.name!r} did not "
                f"resolve to a Dimension subclass "
                f"(got {type(cls).__name__}). Skipping.",
                UserWarning,
                stacklevel=2,
            )
            continue
        if ep.name in seen_names:
            # Entry-points uniqueness is up to distribution packagers;
            # duplicates can arise from competing installs. Skip later
            # wins so Myco's built-ins are never silently shadowed.
            continue
        seen_names.add(ep.name)
        seen_ids.add(cls.id)
        discovered.append(cls)

    if discovered:
        # v0.5.8: gap-fill from ``_BUILT_IN`` so a new built-in added
        # since the last editable-install refresh still shows up. The
        # installed metadata (stale) supplies everything it knows
        # about; _BUILT_IN fills in anything whose id it hasn't seen.
        for cls in _BUILT_IN:
            if cls.id in seen_ids:
                continue
            seen_ids.add(cls.id)
            discovered.append(cls)
        return tuple(discovered)

    # Fallback: no entry-points found. Likely a dev checkout without
    # ``pip install -e .``. Use the compile-time ``_BUILT_IN`` tuple
    # and warn once so the user can fix the environment.
    warnings.warn(
        "myco.dimensions entry-points table is empty — falling back "
        "to the hardcoded built-in dimension set. This usually means "
        "Myco was imported from a source checkout without "
        "`pip install -e .`. Third-party dimension plugins will NOT "
        "be discovered on this fallback path.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _BUILT_IN


def _iter_builtins_for_help() -> Iterator[type[Dimension]]:
    """Yield built-in dimension classes for ``--list`` / ``--explain``
    scenarios where entry-points discovery may not have run yet."""
    yield from _BUILT_IN
