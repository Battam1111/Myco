"""``myco assimilate`` — bulk-promote raw notes into the organism.

v0.5.3: renamed from ``reflect`` (module + verb). In fungal biology,
assimilation is the uptake of absorbed (``eat``-en) nutrients into
the mycelium proper — the raw → integrated transition that this
verb performs. The legacy ``myco reflect`` invocation still works
via a manifest alias through v1.0.0. The internal function is still
named ``reflect()`` to minimize internal churn; downstream Python
callers may use ``from myco.digestion.assimilate import reflect``
either path works.

With no ``--note-id`` (the default), every file under
``notes/raw/*.md`` is promoted. With ``--note-id <id>`` only one
note is promoted. A missing ``notes/raw/`` directory yields zero
promotions.

Each promotion that raises a recoverable error (bad frontmatter,
unresolved reference, existing integrated target) is recorded in
the ``errors`` list of the payload; the call itself still returns
exit 0 unless *every* candidate errored, in which case the caller
gets ``exit_code = 1`` so CI gates notice. This matches the L1
"high" exit semantics.

v0.5.8: after a successful reflect pass (no errors on every
candidate), ``assimilate`` also updates
``_canon.yaml::synced_contract_version`` to equal
``contract_version``. This closes the "hunger reports drift →
advice says run assimilate → assimilate was a no-op on synced"
gap that Lens 11 P0-5 identified. The update uses the same
line-level regex patch molt uses, so it preserves comments and
ordering.
"""

from __future__ import annotations

import re as _re
from collections.abc import Mapping
from pathlib import Path

from myco.core.context import MycoContext, Result
from myco.core.errors import MycoError
from myco.core.io_atomic import atomic_utf8_write
from myco.core.write_surface import check_write_allowed

from .digest import digest_one

__all__ = ["reflect", "assimilate", "run"]


def _sync_contract_version(ctx: MycoContext) -> bool:
    """Write ``synced_contract_version = contract_version`` to canon.

    Returns True if a write occurred (drift was resolved), False if
    canon was already synced or the file could not be patched safely.

    Uses the same line-level regex patch molt uses so comments and
    ordering are preserved. Silent no-op if the canon doesn't carry a
    ``synced_contract_version:`` line (legacy substrates pre-v0.5.8).
    """
    canon = ctx.substrate.canon
    synced = canon.synced_contract_version
    if synced == canon.contract_version:
        return False
    canon_path = ctx.substrate.paths.canon
    if not canon_path.is_file():
        return False
    text = canon_path.read_text(encoding="utf-8")
    pattern = _re.compile(
        r'^(?P<prefix>synced_contract_version:\s*)(?P<q>["\'])[^"\']*(?P=q)\s*$',
        _re.MULTILINE,
    )
    new_text, n = pattern.subn(rf'\g<prefix>"{canon.contract_version}"', text, count=1)
    if n == 0:
        # Legacy canon missing the synced field — leave alone. molt
        # will add it on the next contract bump; meanwhile drift
        # reporting degrades gracefully (hunger reports canon's own
        # stated value).
        return False
    # v0.5.8 guarded rollout: canon is in the default write surface
    # but narrower canons may exclude it; the check makes the refusal
    # loud instead of silent.
    check_write_allowed(ctx, canon_path, verb="assimilate:sync_contract_version")
    atomic_utf8_write(canon_path, new_text)
    return True


def _list_raw(ctx: MycoContext) -> list[Path]:
    raw = ctx.substrate.paths.notes / "raw"
    if not raw.is_dir():
        return []
    return sorted(p for p in raw.glob("*.md") if p.is_file())


def reflect(*, ctx: MycoContext, note_id: str | None = None) -> dict[str, object]:
    """Promote raw notes.

    When ``note_id`` is ``None``, all raw notes are considered.
    Otherwise only the specified id. Errors are collected per-note;
    the overall call succeeds unless every candidate errors.
    """
    if note_id is not None:
        outcomes: list[dict[str, object]] = []
        errors: list[dict[str, str]] = []
        try:
            outcomes.append(digest_one(ctx=ctx, note_id=note_id))
        except MycoError as exc:
            errors.append({"note_id": note_id, "error": str(exc)})
        return {
            "promoted": sum(1 for o in outcomes if o.get("status") == "promoted"),
            "already_integrated": sum(
                1 for o in outcomes if o.get("status") == "already_integrated"
            ),
            "errors": errors,
            "outcomes": outcomes,
        }

    raw_paths = _list_raw(ctx)
    outcomes_all: list[dict[str, object]] = []
    errors_all: list[dict[str, str]] = []
    for path in raw_paths:
        stem = path.stem
        try:
            outcomes_all.append(digest_one(ctx=ctx, note_id=stem))
        except MycoError as exc:
            errors_all.append({"note_id": stem, "error": str(exc)})

    return {
        "promoted": sum(1 for o in outcomes_all if o.get("status") == "promoted"),
        "already_integrated": sum(
            1 for o in outcomes_all if o.get("status") == "already_integrated"
        ),
        "errors": errors_all,
        "outcomes": outcomes_all,
    }


#: Fungal-vocabulary alias for :func:`reflect`. The v0.5.3 rename
#: kept the internal function name (too much call-site churn) but
#: added this alias for code that prefers the canonical verb name.
assimilate = reflect


def run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    note_id = args.get("note_id") or args.get("note")
    note_id_str = str(note_id) if note_id else None
    summary = reflect(ctx=ctx, note_id=note_id_str)

    # Exit 1 only when we tried and *every* candidate errored.
    total = len(summary["outcomes"]) + len(summary["errors"])  # type: ignore[arg-type]
    exit_code = 1 if (total > 0 and not summary["outcomes"]) else 0

    # v0.5.8 P0 FIX (Lens 11 P0-5): on a clean reflect pass (zero
    # errors), sync the contract_version marker so subsequent hunger
    # calls stop reporting a false drift. This is the mechanism that
    # makes "hunger says run assimilate" actually resolve the drift
    # condition instead of looping forever. Silent no-op if canon
    # was already synced, which keeps the operation idempotent.
    synced_updated = False
    if exit_code == 0 and not summary["errors"]:
        try:
            synced_updated = _sync_contract_version(ctx)
        except OSError:
            # Best-effort. Failing the assimilate call because the
            # synced-marker write failed would regress the primary
            # operation. Hunger will re-surface the drift next run.
            synced_updated = False

    payload = dict(summary)
    payload["synced_contract_version_updated"] = synced_updated
    return Result(exit_code=exit_code, payload=payload)
