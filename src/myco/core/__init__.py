"""``myco.core`` — L1 primitives shared across every subsystem.

Stage B.1 surface. Stable re-exports only — implementation lives in
private submodules. See
``docs/architecture/L3_IMPLEMENTATION/package_map.md`` for the full
package map.
"""

from __future__ import annotations

from .canon import (
    KNOWN_SCHEMA_VERSIONS,
    Canon,
    load_canon,
    schema_upgraders,
)
from .identity_cluster import (
    CanonSchemaError,
    ContractError,
    ContractVersion,
    MycoContext,
    MycoError,
    PackageVersion,
    Result,
    Severity,
    SubstrateNotFound,
    UsageError,
    downgrade,
)
from .io_cluster import SubstratePaths
from .substrate_cluster import Substrate, find_substrate_root

__all__ = [
    # canon
    "Canon",
    "load_canon",
    "KNOWN_SCHEMA_VERSIONS",
    "schema_upgraders",
    # context
    "MycoContext",
    "Result",
    # errors
    "MycoError",
    "ContractError",
    "CanonSchemaError",
    "SubstrateNotFound",
    "UsageError",
    # paths
    "SubstratePaths",
    # severity
    "Severity",
    "downgrade",
    # substrate
    "Substrate",
    "find_substrate_root",
    # version
    "PackageVersion",
    "ContractVersion",
]
