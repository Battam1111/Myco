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
#:
#: v0.7.5 adds ``"3"`` for the ``metrics.lint_dim_count`` field
#: introduced by craft
#: ``docs/primordia/v0_7_5_p0_to_p6_omnibus_craft_2026-05-10.md`` (P2).
#: v0.8.0 adds ``"4"`` for the additive ``governance.last_living_bets_audit_at``
#: marker + ``governance.persistence_metrics`` cache block, introduced by
#: ``docs/primordia/v0_8_0_living_bets_amendment_2026-05-10.md`` (the L0
#: amendment opening v0.8.0 MAJOR) and authorised as schema-bump item E
#: by the v0.8.0 omnibus craft.
#: The frozenset retains ``"1"``, ``"2"`` and ``"3"`` so cold-reads of
#: un-upgraded older substrates remain warning-free even if the
#: upgrader chain is ever unregistered for testing.
KNOWN_SCHEMA_VERSIONS: frozenset[str] = frozenset({"1", "2", "3", "4"})

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
    ``.tests/unit/core/test_canon_schema_upgrader_demo.py`` pin
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


def _v2_to_v3_lint_dim_count_field(raw: Mapping[str, Any]) -> Mapping[str, Any]:
    """v0.7.5 schema v3 partial upgrader (1 of 1): add metrics.lint_dim_count.

    Adds ``metrics.lint_dim_count: int | null`` to canons that pre-date
    schema v3. The field is the canon-cited count of registered lint
    dimensions, kept in sync by ``.scripts/bump_version.py`` on every
    contract bump (per craft P2 wiring). On a v2 substrate observed
    cold (no recent ``myco molt`` run), the field defaults to ``None``;
    a fresh ``myco germinate`` populates it directly from the live
    immune registry.

    Behaviour:

    - If ``metrics`` is absent or non-dict, an empty ``{}`` mapping is
      seeded so the field has a place to live; this matches the
      forward-compat additive style used by
      ``_v1_to_v2_federation_peers_field``.
    - If ``metrics.lint_dim_count`` is already present (the operator
      hand-edited the canon, or a fresh germinate stamped it), the
      existing value is preserved untouched — idempotent.
    - The ``schema_version`` stamp is the registered ``_v2_to_v3``
      wrapper's job; this partial only mutates ``metrics``.

    Per craft v0.7.5 omnibus (item P2) this is a single-semantic
    upgrader; the v0.6.0 narrowness principle (one partial = one
    semantic) is preserved trivially because v3 introduces only one
    field. Future v3.x partials in the same upgrader generation MUST
    each occupy their own ``_v2_to_v3_<purpose>`` function.

    Cross-references:

    - L1 doctrine: ``docs/architecture/L1_CONTRACT/canon_schema.md``
      § "v0.6.0+ schema v2 additions" (extended at v0.7.5 to cover
      ``metrics.lint_dim_count``).
    - Governing craft: ``docs/primordia/v0_7_5_p0_to_p6_omnibus_craft_
      2026-05-10.md`` § "P2 — First real schema migration since v0.6.0".
    """
    data = dict(raw)
    metrics_raw = data.get("metrics")
    if not isinstance(metrics_raw, dict):
        # Absent OR malformed (string/list/etc.). Seed a fresh dict so
        # the field has a home; load_canon's ``_mapping("metrics")``
        # check would have raised on a non-dict anyway, but the
        # upgrader runs *before* that check, so we guard defensively.
        metrics_raw = {}
    metrics = dict(metrics_raw)
    if "lint_dim_count" not in metrics:
        metrics["lint_dim_count"] = None
    data["metrics"] = metrics
    return data


def _v2_to_v3(raw: Mapping[str, Any]) -> Mapping[str, Any]:
    """v0.7.5 schema v3 upgrader. Composes one named partial upgrader.

    Sequence:
        v2 raw → _v2_to_v3_lint_dim_count_field
               → v3 stamped

    A single-partial upgrader looks like overkill compared to v1→v2's
    three-partial chain, but the wrapper structure is preserved so
    future v3.x semantic additions (should they arrive before v4)
    have an obvious place to insert. Per craft v0.7.5 omnibus (P2)
    the narrowness principle holds: one partial = one semantic.
    """
    intermediate = _v2_to_v3_lint_dim_count_field(raw)
    data = dict(intermediate)
    data["schema_version"] = "3"
    return data


#: v0.7.5 registers the v2 → v3 upgrader. Substrates on schema v2
#: (any v0.6.x or v0.7.0-v0.7.4 release) parse cleanly through this
#: path with no warning. The chain is ``v1 → v2 → v3`` —
#: ``_apply_upgraders`` walks recursively, so a v1 substrate first
#: lifts to v2 via ``schema_upgraders["1"]`` and then to v3 via
#: ``schema_upgraders["2"]`` in a single ``load_canon`` call.
schema_upgraders["2"] = _v2_to_v3


def _v3_to_v4_living_bets_audit_marker_field(
    raw: Mapping[str, Any],
) -> Mapping[str, Any]:
    """v0.8.0 schema v4 partial upgrader (1 of 2): add
    ``system.governance.last_living_bets_audit_at``.

    Adds ``system.governance.last_living_bets_audit_at: str | null``
    (ISO 8601 UTC timestamp) to canons that pre-date schema v4. The
    field is the canon-cited marker for the most-recent Living Bets
    re-audit doc landing under ``docs/primordia/`` — populated by
    ``myco molt`` at each contract bump (v0.8.x and later anamorph
    extension; out of scope for the v0.8.0 partial itself).

    Purpose: the LB1 dim (shipped v0.7.5) currently filesystem-walks
    ``docs/primordia/**/*living_bets_audit*.md`` at every immune run,
    which is filesystem-O(N). With this field populated, LB1 (and the
    sibling LB2 regime classifier) reads the timestamp from canon
    directly. Backward compat: LB1 falls back to the filesystem scan
    when the field is ``null`` or missing — no behavioural break for
    v3 substrates.

    Field placement: under ``system.governance`` (the canonical home
    of the governance block per L1 ``canon_schema.md`` § "v0.6.0+
    schema v2 additions" → ``system.governance``). The user-facing
    shorthand "governance.last_living_bets_audit_at" in the v0.8.0
    omnibus craft refers to this nested path.

    Behaviour:

    - If ``system`` is absent or non-dict, the partial returns the raw
      mapping untouched — ``load_canon``'s downstream
      ``_mapping("system")`` check would have raised on a non-dict
      anyway, and seeding a fresh ``system`` block here would mask a
      substrate authoring error. (Matches the
      ``_v1_to_v2_federation_peers_field`` empty-identity precedent.)
    - If ``system.governance`` is absent or non-dict, an empty ``{}``
      mapping is seeded so the field has a place to live; the field is
      additive and tolerated by all v0.6.0+ consumers via
      ``.get(...)`` defaults.
    - If ``system.governance.last_living_bets_audit_at`` is already
      present (the operator hand-edited the canon, or a fresh
      ``myco molt`` stamped it), the existing value is preserved
      untouched — idempotent.
    - Per the v0.6.0 narrowness principle (one partial = one semantic),
      this partial does NOT touch ``system.governance.persistence_metrics``;
      that lives in its sibling partial.
    - The ``schema_version`` stamp is the registered ``_v3_to_v4``
      wrapper's job; this partial only mutates ``system.governance``.

    Cross-references:

    - L1 doctrine: ``docs/architecture/L1_CONTRACT/canon_schema.md``
      § "v0.6.0+ schema v2 additions" → ``system.governance`` block
      (extended at v0.8.0 to cover ``last_living_bets_audit_at``).
    - Governing craft: ``docs/primordia/v0_8_0_living_bets_amendment_
      2026-05-10.md`` (L0 amendment opening v0.8.0 MAJOR) and the
      v0.8.0 omnibus craft authorising the schema bump as item E.
    - Consumer: ``src/myco/homeostasis/dimensions/semantic/
      lb1_living_bets_overdue.py`` (v0.8.x extension reads canon-side
      marker before falling back to filesystem walk).
    """
    data = dict(raw)
    system_raw = data.get("system")
    if not isinstance(system_raw, dict):
        # Malformed canon — pass through untouched; load_canon will
        # surface the type error as CanonSchemaError shortly.
        return data
    system = dict(system_raw)
    governance_raw = system.get("governance")
    if not isinstance(governance_raw, dict):
        # Absent OR malformed — seed a fresh dict so the new field
        # has a home. Downstream consumers tolerate the empty block.
        governance_raw = {}
    governance = dict(governance_raw)
    if "last_living_bets_audit_at" not in governance:
        governance["last_living_bets_audit_at"] = None
    system["governance"] = governance
    data["system"] = system
    return data


def _v3_to_v4_persistence_metrics_field(
    raw: Mapping[str, Any],
) -> Mapping[str, Any]:
    """v0.8.0 schema v4 partial upgrader (2 of 2): add
    ``system.governance.persistence_metrics``.

    Adds ``system.governance.persistence_metrics: dict`` with sub-shape
    ``{ session_count: int | null, host_count: int | null,
    peer_count: int | null }`` (all default ``null``) to canons that
    pre-date schema v4. The field caches the substrate's last-known
    persistence-budget signals so the LB2 regime classifier (sibling
    dim shipping in the same v0.8.0 wave) does not have to recompute
    them on every immune run.

    Purpose: feeds the LB2 dim (regime classifier;
    ``src/myco/homeostasis/dimensions/semantic/lb2_living_bets_
    regime.py``). Instead of LB2 re-walking ``.myco/state/*.jsonl`` for
    distinct ``session_id`` values + recounting host adapters + peer
    list every immune call, the cached counts are read here. LB2 may
    either trust the cache (fast path) or recompute when the cache
    age exceeds a TTL (slow path) — that policy lives in LB2, not in
    this upgrader.

    Field placement: under ``system.governance`` (matches the sibling
    partial's placement and the L1 doctrine).

    Behaviour:

    - If ``system`` is absent or non-dict, the partial returns the raw
      mapping untouched (matches the sibling partial's defensive
      precedent).
    - If ``system.governance`` is absent or non-dict, an empty ``{}``
      mapping is seeded.
    - If ``system.governance.persistence_metrics`` is already a dict,
      the partial **preserves any existing values** and only fills in
      missing sub-keys with ``None``. This is the explicit
      "partial-existing-metrics" semantic: a substrate that has
      observed ``session_count`` but not yet ``host_count`` keeps the
      observed ``session_count`` value (idempotency-friendly under
      partial cache writes).
    - If ``system.governance.persistence_metrics`` is present but
      non-dict (string, list, etc.), it is replaced with a fresh dict
      carrying all three ``None`` sub-keys; no silent data loss
      because the malformed shape would have failed downstream
      consumer reads anyway.
    - Per the v0.6.0 narrowness principle, this partial is independent
      of its sibling and is safe to run alone (e.g. for unit testing).

    Cross-references:

    - L1 doctrine: ``docs/architecture/L1_CONTRACT/canon_schema.md``
      § ``system.governance`` block (extended at v0.8.0 to cover
      ``persistence_metrics``).
    - Governing craft: ``docs/primordia/v0_8_0_living_bets_amendment_
      2026-05-10.md`` (L0 amendment opening v0.8.0 MAJOR; T2
      rhizomorph resolution explicitly mentions a future LB2 dim
      that "measures session-count + host-count + peer-count and
      reports the regime") and the v0.8.0 omnibus craft authorising
      the schema bump as item E.
    - Consumer: ``src/myco/homeostasis/dimensions/semantic/
      lb2_living_bets_regime.py`` (reads the three cached counts to
      avoid filesystem-O(N) recomputation).
    """
    _PM_KEYS: tuple[str, ...] = ("session_count", "host_count", "peer_count")

    data = dict(raw)
    system_raw = data.get("system")
    if not isinstance(system_raw, dict):
        return data
    system = dict(system_raw)
    governance_raw = system.get("governance")
    if not isinstance(governance_raw, dict):
        governance_raw = {}
    governance = dict(governance_raw)
    pm_raw = governance.get("persistence_metrics")
    if not isinstance(pm_raw, dict):
        # Absent OR malformed — seed a fresh shape with all None
        # sub-keys.
        pm: dict[str, Any] = dict.fromkeys(_PM_KEYS)
    else:
        # Preserve any existing sub-key values; only fill missing keys
        # with None. Canonical "partial-existing-metrics" semantic.
        pm = dict(pm_raw)
        for k in _PM_KEYS:
            if k not in pm:
                pm[k] = None
    governance["persistence_metrics"] = pm
    system["governance"] = governance
    data["system"] = system
    return data


def _v3_to_v4(raw: Mapping[str, Any]) -> Mapping[str, Any]:
    """v0.8.0 schema v4 upgrader. Composes two named partial upgraders.

    Sequence:
        v3 raw → _v3_to_v4_living_bets_audit_marker_field
               → _v3_to_v4_persistence_metrics_field
               → v4 stamped

    The two partials are independently testable and touch disjoint keys
    (``governance.last_living_bets_audit_at`` vs
    ``governance.persistence_metrics``); the order is therefore
    irrelevant to correctness, but is fixed here for deterministic
    diff reading. Per the v0.6.0 narrowness principle, additional
    v4.x semantic additions MUST each occupy their own
    ``_v3_to_v4_<purpose>`` function.

    Cross-references:

    - L1 doctrine: ``docs/architecture/L1_CONTRACT/canon_schema.md``
      § ``system.governance`` block (extended at v0.8.0).
    - Governing craft: ``docs/primordia/v0_8_0_living_bets_amendment_
      2026-05-10.md`` and the v0.8.0 omnibus craft (item E).
    """
    intermediate = _v3_to_v4_living_bets_audit_marker_field(raw)
    intermediate = _v3_to_v4_persistence_metrics_field(intermediate)
    data = dict(intermediate)
    data["schema_version"] = "4"
    return data


#: v0.8.0 registers the v3 → v4 upgrader. Substrates on schema v3
#: (any v0.7.5 - v0.7.10 release) parse cleanly through this path
#: with no warning. The chain is ``v1 → v2 → v3 → v4`` —
#: ``_apply_upgraders`` walks recursively, so a v1 substrate first
#: lifts to v2 via ``schema_upgraders["1"]``, then to v3 via
#: ``schema_upgraders["2"]``, then to v4 via ``schema_upgraders["3"]``
#: in a single ``load_canon`` call. The "you never migrate again"
#: promise from L0 P3 holds across N=4 chained versions.
schema_upgraders["3"] = _v3_to_v4


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
    """Chain-apply :data:`schema_upgraders` to the latest registered version.

    Walks the upgrader chain until no further upgrader applies,
    naturally terminating at the latest schema version this kernel
    knows how to mint. Raises ``CanonSchemaError`` on cycles.

    v0.7.5 amendment: the previous implementation early-exited when
    ``next_version in KNOWN_SCHEMA_VERSIONS``. That was sound at v0.6.0
    (when v2 was simultaneously the latest AND the only chained-into
    version), but became wrong at v0.7.5 — a v1 substrate would have
    lifted to v2 and stopped, missing the v3 ``metrics.lint_dim_count``
    field. The natural-termination rule (``upgrader is None``) preserves
    the "you never migrate again" promise across N≥3 chained versions
    without needing to track which version is "latest" separately. Old
    versions stay in ``KNOWN_SCHEMA_VERSIONS`` for cold-read backward
    compatibility (their absence-of-upgrader is what stops the chain).

    Returns ``raw`` unchanged (same identity) if no upgrader matches
    the observed version at the very first call; later steps may have
    applied transformations and we return the most-upgraded shape.
    """
    seen = _seen or frozenset()
    if version in seen:
        raise CanonSchemaError(f"schema_upgrader cycle detected at version {version!r}")
    upgrader = schema_upgraders.get(version)
    if upgrader is None:
        return raw
    upgraded = upgrader(dict(raw))
    next_version = str(upgraded.get("schema_version", version))
    # A self-pointing upgrader (next_version == version) IS a cycle and
    # must surface as CanonSchemaError, not silently terminate. The
    # `seen` set at the recursive entry catches it on the next visit.
    # v0.7.5 retraction of an over-defensive early-exit that masked
    # ``test_schema_upgrader_cycle_raises``.
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
