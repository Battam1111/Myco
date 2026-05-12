"""Built-in lint dimensions + entry-points discovery (v0.6.0 reorganized).

One module per dimension, organized into category subdirectories per
craft v0.6.0 §R2 (Round 4 owner amendment):

- ``mechanical/`` — 32 dims (M1-3, MF1+MF2+MF4+MF5, MP1-3, DC1-5,
  CS1, FR1, PA1-6, CG1-2, DI1-2, SC1, AD1, CL1-3).
- ``shipped/`` — 2 dims (SH1, SH2).
- ``metabolic/`` — 6 dims (MB1-4, MB6, MB8).
- ``semantic/`` — 7 dims (SE1-3, SE5, LB1, LB2, RL1).

v0.8.5 retired MF3 (with `boundary.host_integration/` excretion) and
MB7 (with `boundary.surface.mcp_resources` excretion — the dim read
a metric file that the never-wired-in-build_server stub never wrote).
v0.8.6 retired SE4 (white-list shipped permanently empty since v0.6.0),
RL2 + RL3 (read `.myco/state/session_calls.jsonl` that no production
code has ever written — dead-letter checkers since landing). All
three emitted zero findings for the full v0.6.0…v0.8.5 window.
Live roster: **47 dims**.

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

from ..dimension import Dimension

# ---- Mechanical (31) ------------------------------------------------
from .mechanical.ad1_adapter_silent_skip import AD1AdapterSilentSkip
from .mechanical.cg1_doctrine_has_src_reference import CG1DoctrineHasSrcReference
from .mechanical.cg2_subpackage_has_doctrine_link import CG2SubpackageHasDoctrineLink
from .mechanical.cl1_sampling_policy_gate import CL1SamplingPolicyGate
from .mechanical.cl2_oauth_token_residency import CL2OAuthTokenResidency
from .mechanical.cl3_sampling_token_clear import CL3SamplingTokenClear
from .mechanical.cs1_contract_version_sync import CS1ContractVersionSync
from .mechanical.dc1_module_docstring import DC1ModuleDocstring
from .mechanical.dc2_public_function_docstring import DC2PublicFunctionDocstring
from .mechanical.dc3_public_class_docstring import DC3PublicClassDocstring
from .mechanical.dc4_module_doc_ref import DC4ModuleDocRef
from .mechanical.dc5_abstract_parent_allowlist import DC5AbstractParentAllowlist
from .mechanical.di1_discipline_hooks_present import DI1DisciplineHooksPresent
from .mechanical.di2_discipline_hooks_content import DI2DisciplineHooksContent
from .mechanical.fr1_fresh_substrate_invariants import FR1FreshSubstrateInvariants
from .mechanical.m1_canon_identity_fields import M1CanonIdentityFields
from .mechanical.m2_entry_point_exists import M2EntryPointExists
from .mechanical.m3_write_surface_declared import M3WriteSurfaceDeclared
from .mechanical.mf1_declared_subsystems_exist import MF1DeclaredSubsystemsExist
from .mechanical.mf2_substrate_local_plugin_health import MF2SubstrateLocalPluginHealth
from .mechanical.mf4_overlay_subsystem_validity import MF4OverlaySubsystemValidity
from .mechanical.mf5_generated_mirror_integrity import MF5GeneratedMirrorIntegrity
from .mechanical.mp1_no_provider_imports import MP1NoProviderImports
from .mechanical.mp2_plugin_provider_imports import MP2PluginProviderImports
from .mechanical.mp3_plugin_bytecode_audit import MP3PluginBytecodeAudit
from .mechanical.pa1_write_surface_coverage import PA1WriteSurfaceCoverage
from .mechanical.pa2_megafile_loc_cap import PA2MegafileLocCap
from .mechanical.pa3_surface_pure_adapter import PA3SurfacePureAdapter
from .mechanical.pa4_core_no_subsystem_deps import PA4CoreNoSubsystemDeps
from .mechanical.pa5_meta_subsystem_layering import PA5MetaSubsystemLayering
from .mechanical.pa6_repo_bloat import PA6RepoBloat
from .mechanical.sc1_schema_parity import SC1SchemaParity

# ---- Metabolic (6) --------------------------------------------------
from .metabolic.mb1_raw_notes_backlog import MB1RawNotesBacklog
from .metabolic.mb2_no_integrated_yet import MB2NoIntegratedYet
from .metabolic.mb3_raw_notes_high_watermark import MB3RawNotesHighWatermark
from .metabolic.mb4_sporulated_reabsorbed import MB4SporulatedReabsorbed
from .metabolic.mb6_stale_draft_or_distilled import MB6StaleDraftOrDistilled
from .metabolic.mb8_shim_hit_counter import MB8ShimHitCounter

# ---- Semantic (7) ---------------------------------------------------
# v0.8.6 — SE4/RL2/RL3 excreted (永恒删减; see module docstring above).
from .semantic.lb1_living_bets_overdue import LB1LivingBetsOverdue
from .semantic.lb2_living_bets_regime import LB2LivingBetsRegime
from .semantic.rl1_rules_referenced import RL1RulesReferenced
from .semantic.se1_dangling_refs import SE1DanglingRefs
from .semantic.se2_orphan_integrated import SE2OrphanIntegrated
from .semantic.se3_link_self_cycle import SE3LinkSelfCycle
from .semantic.se5_version_anchor_freshness import SE5VersionAnchorFreshness

# ---- Shipped (2) ----------------------------------------------------
from .shipped.sh1_package_version_ref import SH1PackageVersionRef
from .shipped.sh2_kernel_ahead_of_canon import SH2KernelAheadOfCanon

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
