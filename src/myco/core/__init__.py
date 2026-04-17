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
from .context import MycoContext, Result
from .errors import (
    CanonSchemaError,
    ContractError,
    MycoError,
    SubstrateNotFound,
    UsageError,
)
from .paths import SubstratePaths
from .severity import Severity, downgrade
from .substrate import Substrate, find_substrate_root
from .version import ContractVersion, PackageVersion

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
