"""``ingestion.intake`` — bulk forage + eat composer (v0.6.0).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
single-responsibility extension; v0.6.0 craft §F (work E.1) replaces
the unimplemented ``forage --digest-on-read`` flag with this dedicated
verb.

``intake --path <dir> [--filter <regex>] [--max <int>] [--dry-run]
[--strict]`` walks the directory via ``forage.list_candidates``, then
calls ``eat.append_note`` on each ForageItem. The two-step composition
preserves single-responsibility:

- ``forage`` stays read-only (lists candidates, no writes).
- ``eat`` stays single-note ingest.
- ``intake`` is the bulk composer.

Failure semantics (per craft §F22 / J Adapter visibility):

- Default: any per-file ingest failure produces a ``status: failed``
  stub note in ``notes/raw/`` and is reported in the result payload's
  ``failures`` list. Other files continue processing.
- ``--strict``: any per-file ingest failure raises ``MycoError``
  (exit_code=2) — agent gets exit_on=critical-equivalent gate.

Returns: ``Result`` with payload ``{ingested, failed, failures,
notes, dry_run}``.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from myco.core.context import MycoContext, Result
from myco.core.errors import MycoError

from . import eat as _eat
from . import forage as _forage

__all__ = ["intake_directory", "run", "run_cli"]


def run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """Manifest-dispatched entry point.

    Standard verb-handler signature: ``run(args, *, ctx) -> Result``.
    Translates the manifest's typed dict into ``intake_directory`` kwargs.
    """
    path = args.get("path")
    if not isinstance(path, (str, Path)):
        raise MycoError("intake: --path is required")
    payload = intake_directory(
        ctx,
        path=str(path),
        filter_pattern=_as_str_or_none(args.get("filter")),
        max_count=_as_int_or_none(args.get("max")),
        dry_run=bool(args.get("dry_run", False)),
        strict=bool(args.get("strict", False)),
    )
    exit_code = int(payload.get("exit_code", 0))
    return Result(exit_code=exit_code, payload=payload)


def run_cli(args: Any, ctx: MycoContext) -> Result:
    """CLI entry point. Translates argparse Namespace into the
    standard ``run`` invocation."""
    return run(
        {
            "path": getattr(args, "path", None),
            "filter": getattr(args, "filter", None),
            "max": getattr(args, "max", None),
            "dry_run": getattr(args, "dry_run", False),
            "strict": getattr(args, "strict", False),
        },
        ctx=ctx,
    )


def _as_str_or_none(v: object) -> str | None:
    if v is None:
        return None
    return str(v)


def _as_int_or_none(v: object) -> int | None:
    if v is None:
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        try:
            return int(v)
        except ValueError:
            return None
    return None


def intake_directory(
    ctx: MycoContext,
    path: str,
    *,
    filter_pattern: str | None = None,
    max_count: int | None = None,
    dry_run: bool = False,
    strict: bool = False,
) -> dict[str, Any]:
    """Bulk-ingest a directory: list candidates then eat each.

    Args:
        ctx: substrate context.
        path: absolute or substrate-relative directory to scan.
        filter_pattern: optional regex; only candidates whose path
            matches are ingested.
        max_count: optional hard cap on ingest count.
        dry_run: if True, list intended actions without writing.
        strict: if True, any per-file failure raises MycoError.

    Returns:
        v0.6.0 verb-result payload dict.
    """
    target = Path(path)
    if not target.is_absolute():
        target = ctx.substrate.root / target
    if not target.exists():
        raise MycoError(f"intake: path not found: {target}")
    if not target.is_dir():
        raise MycoError(
            f"intake: path is not a directory: {target}; use myco_eat for single files"
        )

    # Step 1: forage the candidates via the public helper.
    items, _skipped = _forage.list_candidates(target_dir=target)

    pat: re.Pattern[str] | None = None
    if filter_pattern:
        try:
            pat = re.compile(filter_pattern)
        except re.error as exc:
            raise MycoError(
                f"intake: bad --filter pattern {filter_pattern!r}: {exc}"
            ) from exc

    ingested: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for item in items:
        if max_count is not None and len(ingested) >= max_count:
            break
        item_path = str(item.path) if hasattr(item, "path") else None
        if not item_path:
            continue
        if pat is not None and not pat.search(item_path):
            continue
        if dry_run:
            ingested.append({"path": item_path, "status": "dry_run"})
            continue
        try:
            # Read the file content and append it as a raw note. We use
            # ``append_note`` directly (not ``eat.run``) to compose at the
            # helper level rather than re-routing through the verb dispatcher.
            try:
                file_text = Path(item_path).read_text(
                    encoding="utf-8", errors="replace"
                )
            except OSError as exc:
                raise MycoError(f"read failed: {exc}") from exc
            outcome = _eat.append_note(
                ctx=ctx,
                content=file_text,
                source=str(item_path),
                tags=("intake",),
            )
            ingested.append(
                {
                    "path": item_path,
                    "status": "ok",
                    "note_path": str(outcome.path)
                    if hasattr(outcome, "path")
                    else None,
                }
            )
        except MycoError as exc:
            failure_record = {"path": item_path, "reason": str(exc)}
            failures.append(failure_record)
            if strict:
                raise MycoError(
                    f"intake --strict: ingest of {item_path!r} failed: {exc}"
                ) from exc
        except Exception as exc:
            failure_record = {
                "path": item_path,
                "reason": f"{type(exc).__name__}: {exc}",
            }
            failures.append(failure_record)
            if strict:
                raise MycoError(
                    f"intake --strict: ingest of {item_path!r} raised "
                    f"{type(exc).__name__}: {exc}"
                ) from exc

    return {
        "exit_code": 0 if (not failures or not strict) else 2,
        "ingested": len(ingested),
        "failed": len(failures),
        "failures": failures,
        "notes": ingested,
        "dry_run": dry_run,
    }
