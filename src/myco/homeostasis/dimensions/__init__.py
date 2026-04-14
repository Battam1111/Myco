"""Built-in lint dimensions.

One module per dimension. ``ALL`` enumerates the classes registered by
:func:`myco.homeostasis.default_registry`.

Stage B.8 authors the v0.4.0 set fresh against L1/L2 needs:

- **Mechanical** — M1 (canon identity), M2 (entry-point exists),
  M3 (write-surface declared).
- **Shipped**    — SH1 (package-version ref resolves).
- **Metabolic**  — MB1 (raw-note backlog), MB2 (nothing integrated yet).
- **Semantic**   — SE1 (dangling refs), SE2 (orphan integrated notes).

Adding a dimension: add the file, import the class here, append to
``ALL`` and ``__all__``, and write a test under
``tests/unit/homeostasis/dimensions/``.
"""

from __future__ import annotations

from ..dimension import Dimension
from .m1_canon_identity_fields import M1CanonIdentityFields
from .m2_entry_point_exists import M2EntryPointExists
from .m3_write_surface_declared import M3WriteSurfaceDeclared
from .sh1_package_version_ref import SH1PackageVersionRef
from .mb1_raw_notes_backlog import MB1RawNotesBacklog
from .mb2_no_integrated_yet import MB2NoIntegratedYet
from .se1_dangling_refs import SE1DanglingRefs
from .se2_orphan_integrated import SE2OrphanIntegrated

__all__ = [
    "ALL",
    "M1CanonIdentityFields",
    "M2EntryPointExists",
    "M3WriteSurfaceDeclared",
    "SH1PackageVersionRef",
    "MB1RawNotesBacklog",
    "MB2NoIntegratedYet",
    "SE1DanglingRefs",
    "SE2OrphanIntegrated",
]


#: Every built-in dimension class registered by :func:`default_registry`.
ALL: tuple[type[Dimension], ...] = (
    M1CanonIdentityFields,
    M2EntryPointExists,
    M3WriteSurfaceDeclared,
    SH1PackageVersionRef,
    MB1RawNotesBacklog,
    MB2NoIntegratedYet,
    SE1DanglingRefs,
    SE2OrphanIntegrated,
)
