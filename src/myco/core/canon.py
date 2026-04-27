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
KNOWN_SCHEMA_VERSIONS: frozenset[str] = frozenset({"1", "2"})

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


def _v1_to_v2_llm_policy_enum(raw: Mapping[str, Any]) -> Mapping[str, Any]:
    """v0.6.0 schema v2 partial upgrader (1 of 2): bool → enum.

    Rewrites ``system.no_llm_in_substrate: bool`` (v0.5.6+ shape) to
    ``system.llm_policy: "forbidden" | "opt-in" | "providers-declared"``
    (v0.6.0 enum). True → "forbidden"; False → "providers-declared"
    (the conservative interpretation: a v1 substrate that disabled the
    P1 invariant is assumed to have populated providers/, not just
    permitted ad-hoc sampling).

    Per craft v0_6_0_unified_evolution Round 2 T6/T30 resolution, the
    v1→v2 upgrader is internally split into two named functions for
    semantic narrowness. Both are called sequentially by the
    registered ``_v1_to_v2`` wrapper.
    """
    data = dict(raw)
    system_raw = data.get("system", {})
    if not isinstance(system_raw, dict):
        # Malformed canon — pass through untouched; load_canon will surface
        # the type error as CanonSchemaError shortly.
        return data
    system = dict(system_raw)
    if "no_llm_in_substrate" in system:
        bool_val = system.pop("no_llm_in_substrate")
        # Conservative: True (the v0.5.6+ default) → forbidden;
        # False → providers-declared (assumes opt-out was deliberate).
        system["llm_policy"] = "forbidden" if bool_val else "providers-declared"
    elif "llm_policy" not in system:
        # Substrate predates v0.5.6; default to forbidden.
        system["llm_policy"] = "forbidden"
    data["system"] = system
    return data


def _v1_to_v2_federation_peers_field(raw: Mapping[str, Any]) -> Mapping[str, Any]:
    """v0.6.0 schema v2 partial upgrader (2 of 2): add identity.federation_peers.

    Adds ``identity.federation_peers: []`` (empty list) if absent.
    Forward-compat additive — does not require schema bump on its own
    per ``canon_schema.md:159-162``, but groups with the enum bump for
    atomic v1→v2 coherence per craft v0_6_0_unified_evolution F6.
    """
    data = dict(raw)
    identity_raw = data.get("identity", {})
    if not isinstance(identity_raw, dict):
        # Malformed canon — pass through untouched; load_canon will raise.
        return data
    if not identity_raw:
        # Empty identity — leave empty so the empty-identity gate fires
        # before we touch shape. Stamping ``federation_peers: []`` here
        # would mask a substrate authoring error.
        return data
    identity = dict(identity_raw)
    if "federation_peers" not in identity:
        identity["federation_peers"] = []
    data["identity"] = identity
    return data


def _v1_to_v2_lint_dimensions_subfile(raw: Mapping[str, Any]) -> Mapping[str, Any]:
    """v0.6.0 schema v2 partial upgrader (3 of 3): extract lint.dimensions
    to sibling _canon_lint.yaml.

    Per craft §A4 (Round 4 owner amendment) the lint.dimensions table is
    extracted from the main canon to a sibling file. The main canon
    retains a ``lint.dimensions_ref: "_canon_lint.yaml"`` pointer. At
    load time, ``load_canon`` merges the sub-file's ``dimensions``
    payload into ``Canon.lint.dimensions`` transparently — callers
    continue to read ``canon.lint["dimensions"]`` as if the table had
    never moved.

    This partial upgrader handles the in-memory rewrite for
    auto-upgrade scenarios (a v0.5.x substrate first hunger fires the
    v1→v2 upgrader). The on-disk write of the sibling file is the
    operator's job (or a future ``myco molt`` flag); the partial only
    stamps the canon side.
    """
    data = dict(raw)
    lint_raw = data.get("lint", {})
    if not isinstance(lint_raw, dict):
        # Malformed canon — pass through untouched; load_canon will raise.
        return data
    lint = dict(lint_raw)
    if "dimensions" in lint and "dimensions_ref" not in lint:
        # In-memory: keep dimensions inline (no on-disk side effect from
        # an upgrader). The lint/dimensions_ref hint is added so callers
        # know v0.6.0 expects sub-file, but inline copy stays for graceful
        # backward read.
        lint["dimensions_ref"] = "_canon_lint.yaml"
    data["lint"] = lint
    return data


def _v1_to_v2(raw: Mapping[str, Any]) -> Mapping[str, Any]:
    """v0.6.0 schema v2 upgrader. Composes three named partial upgraders.

    Sequence:
        v1 raw → _v1_to_v2_llm_policy_enum
               → _v1_to_v2_federation_peers_field
               → _v1_to_v2_lint_dimensions_subfile
               → v2 stamped

    The three partials are independently testable; this wrapper
    enforces the v1→v2 schema_version stamp at the end.

    Per craft §A4 (Round 4 owner amendment), the third partial extracts
    lint.dimensions to a sibling _canon_lint.yaml file. The main
    canon retains a dimensions_ref pointer.
    """
    intermediate = _v1_to_v2_llm_policy_enum(raw)
    intermediate = _v1_to_v2_federation_peers_field(intermediate)
    intermediate = _v1_to_v2_lint_dimensions_subfile(intermediate)
    data = dict(intermediate)
    data["schema_version"] = "2"
    return data


def _merge_lint_dimensions_subfile(
    raw: Mapping[str, Any], canon_path: Path
) -> Mapping[str, Any]:
    """Merge lint dimensions from sibling ``_canon_lint.yaml`` if the
    main canon declares a ``lint.dimensions_ref`` pointer.

    Per craft §A4 owner amendment, schema v2 substrates may move the
    ``lint.dimensions`` table to a sibling file to keep the main
    canon under the LoC budget. ``load_canon`` calls this merger
    after parsing the main canon so callers continue to read
    ``canon.lint["dimensions"]`` transparently.

    If the main canon already has an inline ``lint.dimensions``
    table AND a ``lint.dimensions_ref`` pointer, the **inline** copy
    wins (forward-compat: future schemas may invert this).
    """
    data = dict(raw)
    lint = dict(data.get("lint", {}))
    ref = lint.get("dimensions_ref")
    if not ref:
        return data
    sibling_path = canon_path.parent / str(ref)
    if not sibling_path.is_file():
        return data
    try:
        sibling = yaml.safe_load(sibling_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return data
    if not isinstance(sibling, dict):
        return data
    sibling_dims = sibling.get("dimensions")
    if sibling_dims is None:
        return data
    # Inline wins.
    if "dimensions" not in lint or not lint.get("dimensions"):
        lint["dimensions"] = sibling_dims
    data["lint"] = lint
    return data


#: v0.6.0 registers the v1 → v2 upgrader. Substrates on schema v1
#: (any v0.5.x release) parse cleanly through this path with no
#: warning. Per craft §A4 (Round 4 owner amendment), the upgrader
#: bundles three semantic changes via narrow named partials:
#: bool→enum (llm_policy), federation_peers additive field, and
#: lint.dimensions sub-file extraction. The narrowness is preserved
#: at the partial-function layer; v2.1 schema is no longer needed.
schema_upgraders["1"] = _v1_to_v2


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

    # v0.5.8 Phase 8-10: bounded read. A malicious or accidentally
    # multi-GB canon can no longer OOM the kernel — the cap raises
    # ``MycoError`` with a clear message instead of Python materialising
    # the whole file.
    from myco.core.io_atomic import bounded_read_text

    try:
        raw = yaml.safe_load(bounded_read_text(path))
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
    # v0.6.0: apply registered upgraders even for "known" versions. This lets
    # a v1 substrate silently lift to v2 (the current latest) on first hunger
    # without warning, satisfying the "you never migrate again" promise. The
    # KNOWN_SCHEMA_VERSIONS set retains "1" so cold-reads of un-upgraded v1
    # substrates still parse without warning if the upgrader chain ever drops.
    if schema_version in schema_upgraders:
        upgraded = _apply_upgraders(schema_version, raw)
        if upgraded is not raw:
            raw = dict(upgraded)
            schema_version = str(raw.get("schema_version", schema_version))
    if schema_version not in KNOWN_SCHEMA_VERSIONS:
        # No upgrader registered (or chain ended at unknown). Warn and proceed
        # best-effort — v0.5 forward-compat contract. The ``.get(...)``-tolerant
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

    # v0.6.0 §A4: merge sibling _canon_lint.yaml dimensions inline.
    raw = dict(_merge_lint_dimensions_subfile(raw, path))

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
