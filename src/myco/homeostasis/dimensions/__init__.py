"""Built-in lint dimensions + entry-points discovery.

47 dimensions across 4 category subdirectories. v0.8.8 reverted the
v0.6.0 craft §R2 owner amendment "one module per dim" — letter-cluster
families (M/MF/MP/DC/PA/CG/DI/CL/MB/LB/SE/SH) consolidated into single
``<letter>_cluster.py`` files; the mechanical singletons
(AD1/CS1/FR1/SC1) also collapsed into ``singletons_cluster.py`` at
v0.8.8 pass-3; RL1 remains a true semantic singleton. Per L1
protocol.md, §R2 is an L3 organization choice; cluster-merge lands
without a molt. Section markers ``# === <DIM_ID> — ...`` inside each
cluster preserve doctrine-by-doctrine review (the original §R2
rationale).

- ``mechanical/`` — 32 dims across 9 files:
  m_cluster (M1-3), mf_cluster (MF1+2+4+5), mp_cluster (MP1-3),
  dc_cluster (DC1-5), cg_cluster (CG1-2), di_cluster (DI1-2),
  pa_cluster (PA1-6), cl_cluster (CL1-3),
  singletons_cluster (AD1+CS1+FR1+SC1).
- ``shipped/`` — 2 dims (sh_cluster: SH1+SH2).
- ``metabolic/`` — 6 dims (mb_cluster: MB1-MB4 + MB6 + MB8).
- ``semantic/`` — 7 dims: se_cluster (SE1-3+SE5) + lb_cluster (LB1-2)
  + rl1 (singleton).

v0.8.5 retired MF3 (with `boundary.host_integration/` excretion) and
MB7 (with `boundary.surface.mcp_resources` excretion — the dim read
a metric file that the never-wired-in-build_server stub never wrote).
v0.8.6 retired SE4 (white-list shipped permanently empty since v0.6.0),
RL2 + RL3 (read `.myco/state/session_calls.jsonl` that no production
code has ever written — dead-letter checkers since landing). Live
roster: **47 dims**.

Discovery is driven by
``importlib.metadata.entry_points(group="myco.dimensions")`` at v0.5+
(per ``docs/contract_changelog.md`` § v0.5.0 MAJOR 6).
Third-party substrates (symbionts) register their own dimensions by
declaring ``[project.entry-points."myco.dimensions"]`` in their
``pyproject.toml`` — no code edit to Myco required.

The ``_BUILT_IN`` tuple below mirrors the entry-points table in
Myco's ``pyproject.toml``. It serves as a **fallback** for checkouts
that have not been ``pip install -e .``'d (where entry-points
metadata has not been materialized). When the fallback fires, a
``DeprecationWarning`` is emitted so dev-mode users know to install.

Adding a built-in dimension: add the file under the appropriate
category subdirectory, import the class here, append to ``_BUILT_IN``
and ``__all__``, add a row to
``pyproject.toml::[project.entry-points."myco.dimensions"]`` with the
new dotted-path, and write a test under
``.tests/unit/homeostasis/dimensions/``.
"""

from __future__ import annotations

import warnings
from collections.abc import Iterator
from importlib.metadata import entry_points

from ..primitives_cluster import Dimension

# ---- Mechanical (31) ------------------------------------------------
from .mechanical.cg_cluster import (
    CG1DoctrineHasSrcReference,
    CG2SubpackageHasDoctrineLink,
)
from .mechanical.cl_cluster import (
    CL1SamplingPolicyGate,
    CL2OAuthTokenResidency,
    CL3SamplingTokenClear,
)
from .mechanical.dc_cluster import (
    DC1ModuleDocstring,
    DC2PublicFunctionDocstring,
    DC3PublicClassDocstring,
    DC4ModuleDocRef,
    DC5AbstractParentAllowlist,
)
from .mechanical.di_cluster import DI1DisciplineHooksPresent, DI2DisciplineHooksContent
from .mechanical.m_cluster import (
    M1CanonIdentityFields,
    M2EntryPointExists,
    M3WriteSurfaceDeclared,
)
from .mechanical.mf_cluster import (
    MF1DeclaredSubsystemsExist,
    MF2SubstrateLocalPluginHealth,
    MF4OverlaySubsystemValidity,
    MF5GeneratedMirrorIntegrity,
)
from .mechanical.mp_cluster import (
    MP1NoProviderImports,
    MP2PluginProviderImports,
    MP3PluginBytecodeAudit,
)
from .mechanical.pa_cluster import (
    PA1WriteSurfaceCoverage,
    PA2MegafileLocCap,
    PA3SurfacePureAdapter,
    PA4CoreNoSubsystemDeps,
    PA5MetaSubsystemLayering,
    PA6RepoBloat,
)

# v0.8.8 pass-2: 4 mechanical singletons (AD1/CS1/FR1/SC1) consolidated
# into ``singletons_cluster.py`` for file-count parity with other clusters.
from .mechanical.singletons_cluster import (
    AD1AdapterSilentSkip,
    CS1ContractVersionSync,
    FR1FreshSubstrateInvariants,
    SC1SchemaParity,
)

# ---- Metabolic (6) --------------------------------------------------
from .metabolic.mb_cluster import (
    MB1RawNotesBacklog,
    MB2NoIntegratedYet,
    MB3RawNotesHighWatermark,
    MB4SporulatedReabsorbed,
    MB6StaleDraftOrDistilled,
    MB8ShimHitCounter,
)

# ---- Semantic (7) ---------------------------------------------------
# v0.8.6 — SE4/RL2/RL3 excreted (永恒删减; see module docstring above).
from .semantic.lb_cluster import LB1LivingBetsOverdue, LB2LivingBetsRegime
from .semantic.rl1_rules_referenced import RL1RulesReferenced
from .semantic.se_cluster import (
    SE1DanglingRefs,
    SE2OrphanIntegrated,
    SE3LinkSelfCycle,
    SE5VersionAnchorFreshness,
)

# ---- Shipped (2) ----------------------------------------------------
from .shipped.sh_cluster import SH1PackageVersionRef, SH2KernelAheadOfCanon

__all__ = [
    "ALL",
    "discover_dimension_classes",
    # Mechanical
    "M1CanonIdentityFields",
    "M2EntryPointExists",
    "M3WriteSurfaceDeclared",
    "MF1DeclaredSubsystemsExist",
    "MF2SubstrateLocalPluginHealth",
    "MF4OverlaySubsystemValidity",
    "MF5GeneratedMirrorIntegrity",
    "MP1NoProviderImports",
    "MP2PluginProviderImports",
    "MP3PluginBytecodeAudit",
    "DC1ModuleDocstring",
    "DC2PublicFunctionDocstring",
    "DC3PublicClassDocstring",
    "DC4ModuleDocRef",
    "DC5AbstractParentAllowlist",
    "CS1ContractVersionSync",
    "FR1FreshSubstrateInvariants",
    "PA1WriteSurfaceCoverage",
    "PA2MegafileLocCap",
    "PA3SurfacePureAdapter",
    "PA4CoreNoSubsystemDeps",
    "PA5MetaSubsystemLayering",
    "PA6RepoBloat",
    "CG1DoctrineHasSrcReference",
    "CG2SubpackageHasDoctrineLink",
    "DI1DisciplineHooksPresent",
    "DI2DisciplineHooksContent",
    "SC1SchemaParity",
    "AD1AdapterSilentSkip",
    "CL1SamplingPolicyGate",
    "CL2OAuthTokenResidency",
    "CL3SamplingTokenClear",
    # Shipped
    "SH1PackageVersionRef",
    "SH2KernelAheadOfCanon",
    # Metabolic
    "MB1RawNotesBacklog",
    "MB2NoIntegratedYet",
    "MB3RawNotesHighWatermark",
    "MB4SporulatedReabsorbed",
    "MB6StaleDraftOrDistilled",
    "MB8ShimHitCounter",
    # Semantic
    "LB1LivingBetsOverdue",
    "LB2LivingBetsRegime",
    "SE1DanglingRefs",
    "SE2OrphanIntegrated",
    "SE3LinkSelfCycle",
    "SE5VersionAnchorFreshness",
    "RL1RulesReferenced",
]


_BUILT_IN: tuple[type[Dimension], ...] = (
    # Mechanical
    M1CanonIdentityFields,
    M2EntryPointExists,
    M3WriteSurfaceDeclared,
    MF1DeclaredSubsystemsExist,
    MF2SubstrateLocalPluginHealth,
    MF4OverlaySubsystemValidity,
    MF5GeneratedMirrorIntegrity,
    MP1NoProviderImports,
    MP2PluginProviderImports,
    MP3PluginBytecodeAudit,
    DC1ModuleDocstring,
    DC2PublicFunctionDocstring,
    DC3PublicClassDocstring,
    DC4ModuleDocRef,
    DC5AbstractParentAllowlist,
    CS1ContractVersionSync,
    FR1FreshSubstrateInvariants,
    PA1WriteSurfaceCoverage,
    PA2MegafileLocCap,
    PA3SurfacePureAdapter,
    PA4CoreNoSubsystemDeps,
    PA5MetaSubsystemLayering,
    PA6RepoBloat,
    CG1DoctrineHasSrcReference,
    CG2SubpackageHasDoctrineLink,
    DI1DisciplineHooksPresent,
    DI2DisciplineHooksContent,
    SC1SchemaParity,
    AD1AdapterSilentSkip,
    CL1SamplingPolicyGate,
    CL2OAuthTokenResidency,
    CL3SamplingTokenClear,
    # Shipped
    SH1PackageVersionRef,
    SH2KernelAheadOfCanon,
    # Metabolic
    MB1RawNotesBacklog,
    MB2NoIntegratedYet,
    MB3RawNotesHighWatermark,
    MB4SporulatedReabsorbed,
    MB6StaleDraftOrDistilled,
    MB8ShimHitCounter,
    # Semantic
    LB1LivingBetsOverdue,
    LB2LivingBetsRegime,
    SE1DanglingRefs,
    SE2OrphanIntegrated,
    SE3LinkSelfCycle,
    SE5VersionAnchorFreshness,
    RL1RulesReferenced,
)


ALL: tuple[type[Dimension], ...] = _BUILT_IN


def discover_dimension_classes() -> tuple[type[Dimension], ...]:
    """Discover every registered dimension class.

    Order of precedence:

    1. ``importlib.metadata.entry_points(group="myco.dimensions")``.
    2. Gap-fill: any ``_BUILT_IN`` class whose ``id`` was not already
       supplied by entry-points is appended.
    3. Full fallback: if entry-points returns empty AND _BUILT_IN has
       items, use _BUILT_IN and warn.
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
            continue
        seen_names.add(ep.name)
        seen_ids.add(cls.id)
        discovered.append(cls)

    if discovered:
        for cls in _BUILT_IN:
            if cls.id in seen_ids:
                continue
            seen_ids.add(cls.id)
            discovered.append(cls)
        return tuple(discovered)

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
    """Yield built-in dimension classes for ``--list`` / ``--explain``."""
    yield from _BUILT_IN
