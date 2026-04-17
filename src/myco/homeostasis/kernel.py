"""Immune-kernel orchestrator.

One entry point — :func:`run_immune` — that a future ``myco immune``
handler (Stage B.7) invokes with a single call.

Design choices (per Stage B.2 craft Round 2.5):

- Per-dimension exceptions propagate. A crashing dimension is a bug,
  not a finding. B.8 may opt-in to exception handling if a need
  emerges.
- ``fix=True`` is plumbed through but does nothing at Stage B.2. The
  first fixable dimension lands in B.8.
- Unknown selected dimension ids surface as :class:`UsageError` with a
  clean message (exit 3).
"""

from __future__ import annotations

from typing import Mapping, Sequence

from myco.core.context import MycoContext, Result
from myco.core.errors import UsageError

from .exit_policy import parse_exit_policy
from .finding import Finding
from .registry import DimensionRegistry, default_registry
from .skeleton import apply_skeleton_downgrade

__all__ = ["run_immune", "run_cli", "run_list", "run_explain"]


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
    ``fix``     — plumbed but no-op at Stage B.2.
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
    for dim in dims:
        findings.extend(dim.run(ctx))

    findings_t = apply_skeleton_downgrade(findings, ctx=ctx)

    policy = parse_exit_policy(exit_on)
    exit_code = policy.compute(findings_t)

    return Result(
        exit_code=exit_code,
        findings=findings_t,
        payload={
            "dimensions_run": tuple(d.id for d in dims),
            "skeleton_downgrade_applied": ctx.substrate.is_skeleton,
            "exit_on": exit_on,
            "fix": fix,  # echo back; no effect at B.2
        },
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
        raise UsageError(
            "immune: --list and --explain are mutually exclusive"
        )

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
