"""Immune-kernel orchestrator.

One entry point — :func:`run_immune` — that the ``myco immune``
handler invokes with a single call.

Design choices (per Stage B.2 craft Round 2.5, extended at v0.5.5):

- Per-dimension exceptions propagate during ``run``. A crashing
  dimension is a bug, not a finding.
- When ``fix=True`` the kernel re-iterates each dimension's findings
  and calls ``dim.fix(ctx, finding)`` only for dimensions where
  ``type(dim).fixable is True``. Unexpected failures in ``fix`` are
  **captured**, not raised — one broken fixable dimension must not
  brick the whole immune run.
- Unknown selected dimension ids surface as :class:`UsageError` with a
  clean message (exit 3).
- Every fix is preceded by a safety guard that checks its declared
  target path is inside ``canon.system.write_surface.allowed``. A
  target outside the write surface is recorded as ``applied=False``
  with ``error="outside write surface"``.
"""

from __future__ import annotations

import fnmatch
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

from myco.core.context import MycoContext, Result
from myco.core.errors import UsageError

from .dimension import Dimension
from .exit_policy import parse_exit_policy
from .finding import Finding
from .registry import DimensionRegistry, default_registry
from .skeleton import apply_skeleton_downgrade

__all__ = ["run_immune", "run_cli", "run_list", "run_explain"]


def _write_surface_patterns(ctx: MycoContext) -> tuple[str, ...]:
    """Return the canon-declared write-surface glob patterns, if any.

    Empty tuple when the canon declares no write surface (caller treats
    the absence as "permissive / no guard" — but an explicit fixable
    dimension that runs in that mode still logs the call so the user
    can see what happened).
    """
    system = ctx.substrate.canon.system or {}
    ws = system.get("write_surface") or {}
    if not isinstance(ws, dict):
        return ()
    allowed = ws.get("allowed")
    if not isinstance(allowed, list):
        return ()
    return tuple(str(p) for p in allowed if isinstance(p, str))


def _path_is_under_write_surface(
    target: Path,
    substrate_root: Path,
    patterns: Sequence[str],
) -> bool:
    """Return True iff ``target`` lies under one of the glob patterns.

    Matching is done on substrate-relative POSIX strings against each
    pattern in ``patterns``. A pattern ending in ``/**`` matches any
    path whose first segment equals the pattern's prefix (so
    ``"docs/**"`` matches ``"docs/a/b.md"``). A pattern with no wildcards
    matches exactly one path.

    When ``patterns`` is empty we return True — the caller has
    decided to permit all writes (either because no write surface is
    declared, or because the guard is disabled). This function never
    accesses the filesystem.
    """
    if not patterns:
        return True
    try:
        rel = target.resolve().relative_to(substrate_root.resolve())
    except ValueError:
        # target is not under substrate root at all; outside any
        # reasonable write surface.
        return False
    rel_str = PurePosixPath(*rel.parts).as_posix()
    for pat in patterns:
        # "dir/**" semantics: treat the pattern as matching the dir
        # prefix plus anything under it. fnmatch alone doesn't handle
        # "**" as multi-segment by default, so explicitly fan out.
        if pat.endswith("/**"):
            prefix = pat[:-3]
            if rel_str == prefix or rel_str.startswith(prefix + "/"):
                return True
            continue
        if pat.endswith("/"):
            if rel_str.startswith(pat):
                return True
            continue
        if fnmatch.fnmatchcase(rel_str, pat):
            return True
    return False


def _fix_target_path(finding: Finding, ctx: MycoContext) -> Path | None:
    """Best-effort guess of the absolute path a fix would write to.

    Uses ``finding.path`` (substrate-relative) when present. Returns
    None if the finding has no path — in which case the write-surface
    guard is skipped (the fix is responsible for declaring its own
    target; see :meth:`Dimension.fix`).
    """
    if finding.path is None:
        return None
    p = Path(finding.path)
    if p.is_absolute():
        return p
    return ctx.substrate.root / p


def _apply_fix(
    dim: Dimension,
    ctx: MycoContext,
    finding: Finding,
    *,
    patterns: Sequence[str],
) -> dict[str, Any]:
    """Run ``dim.fix`` with the write-surface guard + error capture.

    Return shape (one entry in ``payload["fixes"]``):

        {
            "dimension_id": "M2",
            "path": "MYCO.md" | None,
            "applied": True | False,
            "detail": "…",          # optional, present when known
            "error":  "…",          # optional, present on guard skip
                                    # or exception
        }
    """
    entry: dict[str, Any] = {
        "dimension_id": dim.id,
        "path": finding.path,
        "applied": False,
    }

    target = _fix_target_path(finding, ctx)
    if target is not None and not _path_is_under_write_surface(
        target, ctx.substrate.root, patterns
    ):
        entry["error"] = "outside write surface"
        return entry

    try:
        outcome = dim.fix(ctx, finding)
    except Exception as exc:
        entry["error"] = f"{type(exc).__name__}: {exc}"
        return entry

    if not isinstance(outcome, dict):
        entry["error"] = (
            f"fix returned non-dict ({type(outcome).__name__}); "
            f"dimensions must return "
            f'{{"applied": bool, "detail": str}}'
        )
        return entry

    entry["applied"] = bool(outcome.get("applied", False))
    detail = outcome.get("detail")
    if detail is not None:
        entry["detail"] = str(detail)
    # Let fixes surface structured extras (e.g. MB1 wants to report
    # how many notes it promoted) without forcing a new top-level
    # schema on payload["fixes"].
    for key, value in outcome.items():
        if key in ("applied", "detail"):
            continue
        entry.setdefault(key, value)
    return entry


def run_immune(
    ctx: MycoContext,
    registry: DimensionRegistry,
    *,
    selected: Sequence[str] | None = None,
    exit_on: str = "critical",
    fix: bool = False,
) -> Result:
    """Run the immune kernel over ``ctx.substrate``.

    ``selected`` — if given, run only these dimension ids.
    ``exit_on`` — ``--exit-on`` spec string.
    ``fix``     — when True, invoke ``dim.fix(ctx, finding)`` for every
                  finding whose source dimension has ``fixable=True``.
                  Results appear in ``payload["fixes"]`` (always
                  present on the payload when ``fix=True`` — empty
                  list if nothing fired).
    """
    if selected is not None:
        dims = []
        for dim_id in selected:
            if not registry.has(dim_id):
                raise UsageError(f"unknown dimension: {dim_id!r}")
            dims.append(registry.get(dim_id))
    else:
        dims = list(registry.all())

    findings: list[Finding] = []
    # Track which dimension emitted each finding so we can dispatch
    # fix() without having to ask the registry to look up by id (the
    # registry doesn't have a "by id" helper because this is the only
    # caller that cares).
    origins: list[Dimension] = []
    for dim in dims:
        dim_findings = list(dim.run(ctx))
        findings.extend(dim_findings)
        origins.extend([dim] * len(dim_findings))

    findings_t = apply_skeleton_downgrade(findings, ctx=ctx)

    fixes: list[dict[str, Any]] = []
    if fix:
        patterns = _write_surface_patterns(ctx)
        # Pair the post-downgrade findings back up with their origin
        # dimension. ``apply_skeleton_downgrade`` preserves order and
        # does not add or drop findings (only rewrites severity), so
        # the index alignment is stable.
        for origin, finding_t in zip(origins, findings_t, strict=False):
            if not getattr(type(origin), "fixable", False):
                continue
            fixes.append(_apply_fix(origin, ctx, finding_t, patterns=patterns))

    policy = parse_exit_policy(exit_on)
    exit_code = policy.compute(findings_t)

    payload: dict[str, Any] = {
        "dimensions_run": tuple(d.id for d in dims),
        "skeleton_downgrade_applied": ctx.substrate.is_skeleton,
        "exit_on": exit_on,
        "fix": fix,
    }
    if fix:
        # Always present on fix runs so callers can count / iterate
        # without conditional key presence.
        payload["fixes"] = fixes

    return Result(
        exit_code=exit_code,
        findings=findings_t,
        payload=payload,
    )


def run_list(registry: DimensionRegistry) -> Result:
    """Enumerate every registered dimension (id, category, severity).

    Consumed by ``myco immune --list``. Does not run any dimension.
    Output is stable across invocations (sorted by dimension id).
    """
    dims = registry.all()
    return Result(
        exit_code=0,
        payload={
            "mode": "list",
            "count": len(dims),
            "dimensions": [
                {
                    "id": d.id,
                    "category": d.category.value,
                    "default_severity": d.default_severity.label(),
                    "summary": _first_line(d.explain),
                }
                for d in dims
            ],
        },
    )


def run_explain(registry: DimensionRegistry, dim_id: str) -> Result:
    """Return the prose description for a single dimension.

    Consumed by ``myco immune --explain <dim>``. Raises ``UsageError``
    for unknown ids so the CLI surface renders a clean message and
    exits ``3`` rather than tracebacks.
    """
    if not registry.has(dim_id):
        available = ", ".join(d.id for d in registry.all())
        raise UsageError(
            f"unknown dimension: {dim_id!r}. "
            f"Available: {available}. "
            f"Run `myco immune --list` for full details."
        )
    dim = registry.get(dim_id)
    return Result(
        exit_code=0,
        payload={
            "mode": "explain",
            "id": dim.id,
            "category": dim.category.value,
            "default_severity": dim.default_severity.label(),
            "explain": dim.explain,
        },
    )


def _first_line(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    return text.splitlines()[0].strip()


def run_cli(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """Manifest-shaped handler for ``myco immune``.

    Dispatches among three modes:

    - ``--list`` → enumerate dimensions (never runs them).
    - ``--explain <dim>`` → prose description of one dimension.
    - (default) → run all (or a ``--dimensions`` subset) and return
      findings + computed exit code.

    ``--list`` and ``--explain`` are mutually exclusive. Passing both
    raises :class:`UsageError` (exit ``3``).
    """
    list_mode = bool(args.get("list", False))
    explain_raw = args.get("explain")
    explain_id = str(explain_raw) if explain_raw else None

    if list_mode and explain_id:
        raise UsageError("immune: --list and --explain are mutually exclusive")

    if list_mode or explain_id:
        registry = default_registry()
        if list_mode:
            return run_list(registry)
        assert explain_id is not None  # for type-checker
        return run_explain(registry, explain_id)

    dims_raw = args.get("dimensions") or ()
    selected: Sequence[str] | None
    if isinstance(dims_raw, (list, tuple)) and dims_raw:
        selected = tuple(str(d) for d in dims_raw)
    else:
        selected = None
    fix = bool(args.get("fix", False))
    exit_on = str(args.get("exit_on") or "critical")
    return run_immune(
        ctx,
        default_registry(),
        selected=selected,
        exit_on=exit_on,
        fix=fix,
    )
