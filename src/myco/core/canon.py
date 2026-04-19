"""Parse ``_canon.yaml`` against the L1 schema.

Governing doc: ``docs/architecture/L1_CONTRACT/canon_schema.md``.

Forward-compat parse semantics (v0.5+, updated from B.1 strict):

- Missing *required* top-level keys → ``CanonSchemaError``.
- Unknown ``schema_version`` → ``UserWarning`` (was: error).
  A registered entry in :data:`schema_upgraders` transforms the raw
  mapping to a known shape before the warning would fire; an unknown
  version with no upgrader is best-effort-read and the warning is
  surfaced to the caller.
- Known top-level keys are read into typed slots on ``Canon``.
- Unknown top-level keys are preserved in ``Canon.extras``.
- Unknown *nested* keys are silently ignored here; the immune kernel
  (Stage B.2) will re-scan the raw YAML for ``unknown key at known
  section`` as a ``mechanical:HIGH`` finding.

The v0.5 forward-compat flip is what lets "You never migrate again"
stand as a load-bearing README claim: a newer substrate read by an
older kernel, or an older substrate read by a newer kernel, warns
rather than failing. See ``docs/primordia/v0_5_0_major_6_10_craft_
2026-04-17.md`` for the audit trail.

This module only *reads* canon. Writing (contract bumps) is the
``myco bump`` verb's job (v0.5); fresh authoring is Genesis's
(Stage B.3).
"""

from __future__ import annotations

import warnings
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .errors import CanonSchemaError

__all__ = [
    "Canon",
    "load_canon",
    "KNOWN_SCHEMA_VERSIONS",
    "schema_upgraders",
]


#: Schema versions this kernel knows how to read without invoking the
#: upgrader chain. Bumping requires concurrent L1 ``canon_schema.md``
#: revision + a ``contract_changelog.md`` entry.
KNOWN_SCHEMA_VERSIONS: frozenset[str] = frozenset({"1"})

#: Registry of canon schema upgraders, forward-compat seam.
#:
#: Keyed by observed ``schema_version`` string. The callable receives the
#: raw canon mapping (a dict copy; safe to mutate) and MUST return a
#: mapping whose ``schema_version`` is either a
#: :data:`KNOWN_SCHEMA_VERSIONS` entry or another registered upgrader's
#: key (chained).
#:
#: Empty at v0.5 — schema v1 is the only shipped shape. This registry
#: makes the "no migration" promise *tenable*: when schema v2 lands,
#: the kernel that introduces v2 registers ``{"1": _v1_to_v2}`` and
#: every v1 substrate parses silently.
schema_upgraders: dict[str, Callable[[Mapping[str, Any]], Mapping[str, Any]]] = {}


def _demo_v0_to_v1(raw: Mapping[str, Any]) -> Mapping[str, Any]:
    """Demo upgrader registered at v0.5.5 (MAJOR-B).

    Promotes a hypothetical ``schema_version: "0"`` canon to the
    current ``"1"`` shape. The transformation is intentionally
    minimal — just stamps the version — because no substrate
    actually shipped under schema_version 0; v0.4.0 started at "1".
    The purpose is to exercise the chain-apply + warning-silencing
    path end-to-end, proving the forward-compat seam designed at
    v0.5.1 MAJOR-8 works when a real v1→v2 upgrader lands later.

    A substrate with ``schema_version: "0"`` parses cleanly through
    this path with no warning; without the upgrader the caller would
    see a ``UserWarning`` about the unknown version. Tests in
    ``tests/unit/core/test_canon_schema_upgrader_demo.py`` pin
    both modes.
    """
    data = dict(raw)
    data["schema_version"] = "1"
    return data


#: v0.5.5 registers the demo v0 → v1 upgrader unconditionally. Harmless
#: for production substrates because no real canon ever had
#: ``schema_version: "0"``; the entry serves as a canonical example of
#: how real v1→v2 upgraders should be registered when schema v2 ships.
schema_upgraders["0"] = _demo_v0_to_v1


def _apply_upgraders(
    version: str,
    raw: Mapping[str, Any],
    *,
    _seen: frozenset[str] | None = None,
) -> Mapping[str, Any]:
    """Chain-apply :data:`schema_upgraders` until version is known.

    Returns ``raw`` unchanged (same identity) if no upgrader matches
    the observed version, signalling the caller to emit a warning and
    proceed best-effort. Raises ``CanonSchemaError`` on cycles.
    """
    seen = _seen or frozenset()
    if version in seen:
        raise CanonSchemaError(f"schema_upgrader cycle detected at version {version!r}")
    upgrader = schema_upgraders.get(version)
    if upgrader is None:
        return raw
    upgraded = upgrader(dict(raw))
    next_version = str(upgraded.get("schema_version", version))
    if next_version in KNOWN_SCHEMA_VERSIONS:
        return upgraded
    return _apply_upgraders(next_version, upgraded, _seen=seen | {version})


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
        upgraded = _apply_upgraders(schema_version, raw)
        if upgraded is raw:
            # No upgrader registered. Warn and proceed best-effort —
            # v0.5 forward-compat contract. The ``.get(...)``-tolerant
            # downstream readers handle any shape drift.
            warnings.warn(
                f"_canon.yaml schema_version {schema_version!r} is not "
                f"recognized by this Myco kernel "
                f"(known: {sorted(KNOWN_SCHEMA_VERSIONS)}). "
                f"Proceeding best-effort. Register a "
                f"myco.core.canon.schema_upgraders entry to silence "
                f"and transform.",
                UserWarning,
                stacklevel=2,
            )
        else:
            raw = dict(upgraded)
            schema_version = str(raw.get("schema_version", schema_version))

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
