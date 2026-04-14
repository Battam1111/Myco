"""Parse ``_canon.yaml`` against the L1 schema.

Governing doc: ``docs/architecture/L1_CONTRACT/canon_schema.md``.

Strict-parse semantics (Stage B.1):

- Missing *required* top-level keys → ``CanonSchemaError``.
- Unknown ``schema_version`` → ``CanonSchemaError``.
- Known top-level keys are read into typed slots on ``Canon``.
- Unknown top-level keys are preserved in ``Canon.extras``.
- Unknown *nested* keys are silently ignored here; the immune kernel
  (Stage B.2) will re-scan the raw YAML for ``unknown key at known
  section`` as a ``mechanical:HIGH`` finding.

This module only *reads* canon. Writing (fresh authoring) is Genesis's
job (Stage B.3).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from .errors import CanonSchemaError

__all__ = ["Canon", "load_canon", "KNOWN_SCHEMA_VERSIONS"]


#: Schema versions this kernel knows how to read.
KNOWN_SCHEMA_VERSIONS: frozenset[str] = frozenset({"1"})

#: Top-level keys that MUST be present for a canon to be considered valid.
_REQUIRED_TOP_LEVEL: tuple[str, ...] = (
    "schema_version",
    "contract_version",
    "identity",
    "system",
    "subsystems",
)

#: Top-level keys known to the schema. Anything else goes into ``extras``.
_KNOWN_TOP_LEVEL: frozenset[str] = frozenset(
    {
        "schema_version",
        "contract_version",
        "synced_contract_version",
        "identity",
        "system",
        "versioning",
        "lint",
        "subsystems",
        "commands",
        "metrics",
        "waves",
    }
)


@dataclass(frozen=True)
class Canon:
    """Parsed ``_canon.yaml`` contents.

    Fields mirror the schema in ``canon_schema.md``. Nested sections are
    retained as nested mappings; typed accessors are provided for the
    fields Stage B.1 callers actually need. The immune kernel (B.2) and
    each subsystem may add richer typed views in follow-up stages.
    """

    schema_version: str
    contract_version: str
    identity: Mapping[str, Any]
    system: Mapping[str, Any]
    subsystems: Mapping[str, Any]

    synced_contract_version: str | None = None
    versioning: Mapping[str, Any] = field(default_factory=dict)
    lint: Mapping[str, Any] = field(default_factory=dict)
    commands: Mapping[str, Any] = field(default_factory=dict)
    metrics: Mapping[str, Any] = field(default_factory=dict)
    waves: Mapping[str, Any] = field(default_factory=dict)

    #: Any top-level keys not recognized by this schema. Preserved
    #: round-trip so agents can extend canon without breaking readers.
    extras: Mapping[str, Any] = field(default_factory=dict)

    @property
    def substrate_id(self) -> str:
        """Shorthand for ``identity.substrate_id``; empty string if missing."""
        return str(self.identity.get("substrate_id", ""))

    @property
    def tags(self) -> tuple[str, ...]:
        """Free-form affiliation tags (per L0: NOT boundaries)."""
        raw = self.identity.get("tags") or ()
        return tuple(str(t) for t in raw)

    @property
    def entry_point(self) -> str:
        """The agent-entry filename (``MYCO.md`` by default)."""
        return str(self.identity.get("entry_point", "MYCO.md"))


def load_canon(path: Path) -> Canon:
    """Load + validate ``_canon.yaml`` at ``path``.

    Raises ``CanonSchemaError`` on any structural break (missing file,
    non-mapping root, missing required field, unknown schema version).
    """
    if not path.exists():
        raise CanonSchemaError(f"_canon.yaml not found: {path}")

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise CanonSchemaError(f"_canon.yaml is not valid YAML: {exc}") from exc

    if raw is None:
        raise CanonSchemaError(f"_canon.yaml is empty: {path}")
    if not isinstance(raw, dict):
        raise CanonSchemaError(
            f"_canon.yaml top level must be a mapping, got {type(raw).__name__}"
        )

    missing = [k for k in _REQUIRED_TOP_LEVEL if k not in raw]
    if missing:
        raise CanonSchemaError(
            f"_canon.yaml missing required key(s): {', '.join(missing)}"
        )

    schema_version = str(raw["schema_version"])
    if schema_version not in KNOWN_SCHEMA_VERSIONS:
        raise CanonSchemaError(
            f"unknown schema_version {schema_version!r} "
            f"(known: {sorted(KNOWN_SCHEMA_VERSIONS)})"
        )

    def _mapping(key: str) -> Mapping[str, Any]:
        val = raw.get(key, {})
        if val is None:
            return {}
        if not isinstance(val, dict):
            raise CanonSchemaError(
                f"_canon.yaml::{key} must be a mapping, got {type(val).__name__}"
            )
        return val

    identity = _mapping("identity")
    system = _mapping("system")
    subsystems = _mapping("subsystems")
    if not identity:
        raise CanonSchemaError("_canon.yaml::identity must not be empty")
    if not system:
        raise CanonSchemaError("_canon.yaml::system must not be empty")
    if not subsystems:
        raise CanonSchemaError("_canon.yaml::subsystems must not be empty")

    synced = raw.get("synced_contract_version")
    if synced is not None:
        synced = str(synced)

    extras = {k: v for k, v in raw.items() if k not in _KNOWN_TOP_LEVEL}

    return Canon(
        schema_version=schema_version,
        contract_version=str(raw["contract_version"]),
        identity=identity,
        system=system,
        subsystems=subsystems,
        synced_contract_version=synced,
        versioning=_mapping("versioning"),
        lint=_mapping("lint"),
        commands=_mapping("commands"),
        metrics=_mapping("metrics"),
        waves=_mapping("waves"),
        extras=extras,
    )
