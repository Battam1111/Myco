#!/usr/bin/env python3
"""Forward compression — `myco compress` verb implementation.

**Wave 30 (kernel_contract, contract v0.26.0)** — answers the substrate's
most doctrine-weighted gap: anchor #4 (compression-is-cognition). Prior to
Wave 30, the only substrate compression that existed was *reverse* compression
(the `excreted` status + `excrete_reason`). Forward compression — *take N raw
notes and produce 1 extracted synthesis with audit trail* — is what makes
"storage infinite, attention finite" actionable rather than aspirational.

**Authoritative design**: `docs/primordia/compression_primitive_craft_2026-04-12.md`
(Wave 27, exploration 0.85, 7 design questions answered).

**Implementation craft**: docs/primordia/compress_mvp_craft_2026-04-12.md
(Wave 30, kernel_contract 0.90, validates Wave 27's design under impl pressure).

**Verb shape** (locked in Wave 27 D1-D9):

  myco compress --tag <TAG> --rationale "..." [--status raw|digesting]
  myco compress --tag <TAG> --rationale "..." --dry-run
  myco compress <note_id1> <note_id2> ... --rationale "..."

**Behavior** (Wave 27 §3.1 specification):

  1. Resolve cohort: tag-filter scan OR explicit ID list (mutually exclusive)
  2. Reject empty cohort (exit 4 — nothing to compress)
  3. Reject any input that already carries `compressed_from` (cascade prevention,
     Wave 27 §2.1 defense #4 — "compression-on-compression" is a hallucination
     amplifier and is structurally forbidden at the schema layer)
  4. Reject any input that is already in terminal `excreted` status (would
     double-excrete a note that the user/agent already retired)
  5. If --dry-run: print cohort + proposed rationale + proposed output id, exit 0
  6. Otherwise execute the two-phase commit:
     a. Phase 1: write the new extracted note (with all audit fields) AND
        compute the new content of every input note. Both via temp files.
        If any phase-1 step fails, delete temps and abort with non-zero exit.
     b. Phase 2: rename all temps to final paths via `atomic_write_text`.
        If a phase-2 rename fails, log a warning but the substrate may be
        left torn — manual recovery required.

**Audit trail** (Wave 27 §1.4):

  Output extracted note frontmatter:
    compressed_from: [<id1>, <id2>, ...]    # required, ordered list
    compression_method: manual              # "manual" | "hunger-signal"
    compression_rationale: |                # required prose
      <agent's explanation of what was preserved vs dropped>
    compression_confidence: <float>         # self-reported 0.0-1.0

  Mutated input note frontmatter (per input):
    status: excreted
    excrete_reason: "compressed into <output_id> as part of <N>-note cohort"
    compressed_into: <output_id>
    pre_compression_status: <prior status>  # for future uncompress

**Idempotence** (Wave 27 §1.7): re-running `myco compress --tag X` after a
successful compress is a no-op (the cohort is empty because the original
inputs are now `excreted`). If new raw notes have been added with the tag
since, the second run compresses only the new ones.

**Atomicity**: best-effort via two-phase commit (`io_utils.atomic_write_text`).
True transactional atomicity is a non-goal — see `io_utils` module docstring.

**Hallucination risk**: bounded, not eliminated. See Wave 27 §2.1 defense
list and Wave 27 L1 known limitation. The mitigations Wave 30 ships:
  • L18 lint enforces bidirectional link integrity (output ↔ inputs)
  • L18 lint blocks cascade (no compressing already-compressed notes)
  • Wave 27 hunger signal `compression_ripe` (deferred to Wave 30 hunger
    extension) sets a friction floor at N≥5 to discourage easy fabrication
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from myco.io_utils import atomic_write_text
from myco.notes import (
    MycoProjectNotFound,
    NOTES_DIRNAME,
    VALID_STATUSES,
    generate_id,
    id_to_filename,
    list_notes,
    read_note,
    serialize_note,
)


# ---------------------------------------------------------------------------
# Project root resolution — now centralized in project.py
# ---------------------------------------------------------------------------

from myco.project import resolve_project_dir




# ---------------------------------------------------------------------------
# Cohort resolution
# ---------------------------------------------------------------------------

def _resolve_cohort_by_tag(
    root: Path,
    tag: str,
    status_filter: Optional[str] = None,
) -> List[Path]:
    """Return note paths whose frontmatter tags include `tag`.

    Wave 27 D1: tag-scoped is the primary cohort selector. Status filter
    is optional and defaults to ``{"raw", "digesting"}`` — both pre-terminal
    metabolic states are compressible. Notes already past the metabolic
    threshold (``extracted``, ``integrated``, ``excreted``, ``dead``) are
    structurally ineligible:
      • ``extracted`` / ``integrated`` are *downstream* of compression — the
        Wave 27 §1.7 idempotence guarantee depends on the OUTPUT of a prior
        compress NOT being a candidate for the next compress on the same
        tag (otherwise re-running ``myco compress --tag X`` would attempt
        cascade and fail with exit 3 instead of exit 4 / no-op).
      • ``excreted`` notes are already-retired; compressing one would be a
        double-excretion at best.
      • ``dead`` notes are by definition not alive enough to compress.

    Notes with ``compressed_from`` already set are also rejected here as a
    belt-and-suspenders defense against cascade (the same check exists in
    ``_validate_cohort`` and L18 lint).
    """
    matches: List[Path] = []
    eligible_default = {"raw", "digesting"}
    for p in list_notes(root):
        try:
            meta, _ = read_note(p)
        except (OSError, ValueError, RuntimeError):
            continue
        tags = meta.get("tags") or []
        if not isinstance(tags, list):
            continue
        if tag not in tags:
            continue
        # Cascade defense: skip already-compressed outputs.
        if meta.get("compressed_from"):
            continue
        status = meta.get("status", "raw")
        if status_filter is not None:
            if status != status_filter:
                continue
        else:
            if status not in eligible_default:
                continue
        matches.append(p)
    # Sort by created timestamp to get a stable order for the audit trail.
    matches.sort(key=lambda p: p.stem)
    return matches


def _resolve_cohort_by_ids(root: Path, note_ids: List[str]) -> List[Path]:
    """Return note paths for each id in `note_ids`, in the order given.

    Wave 27 D1: manual bundle is the escape hatch. The order specified by
    the caller is preserved in the output's `compressed_from` list because
    Wave 27 Attack H defense #2 mandated ordering preservation.

    Raises `FileNotFoundError` listing all missing ids if any are absent.
    """
    notes_dir = root / NOTES_DIRNAME
    paths: List[Path] = []
    missing: List[str] = []
    for nid in note_ids:
        candidate = notes_dir / id_to_filename(nid)
        if candidate.exists():
            paths.append(candidate)
        else:
            missing.append(nid)
    if missing:
        raise FileNotFoundError(
            f"compress: cannot find note(s): {', '.join(missing)}"
        )
    return paths


# ---------------------------------------------------------------------------
# Validation pre-checks (Wave 27 §3.1 steps 3-4)
# ---------------------------------------------------------------------------

def _validate_cohort(cohort: List[Path]) -> List[str]:
    """Return a list of validation errors. Empty list = ready to compress.

    Enforces:
      • Cohort non-empty (caller-side; this only catches double-checking)
      • No input has `compressed_from` field (cascade prevention, Wave 27
        §2.1 defense #4)
      • No input has status `excreted` (already-retired note can't be
        re-compressed)
    """
    errors: List[str] = []
    if not cohort:
        errors.append("cohort is empty — nothing to compress")
        return errors

    for p in cohort:
        rel = p.name
        try:
            meta, _ = read_note(p)
        except Exception as exc:
            errors.append(f"{rel}: cannot read frontmatter: {exc}")
            continue
        if meta.get("compressed_from"):
            errors.append(
                f"{rel}: already has `compressed_from` — cascade compression "
                f"is rejected at schema time (Wave 27 D4). Use a different "
                f"input cohort that does not include compressed notes."
            )
        if meta.get("status") == "excreted":
            errors.append(
                f"{rel}: status is already `excreted` — cannot compress an "
                f"already-retired note."
            )
    return errors


# ---------------------------------------------------------------------------
# Output construction
# ---------------------------------------------------------------------------

def _build_output_body(cohort: List[Path], rationale: str) -> str:
    """Render the body of the new extracted note.

    The body is intentionally simple in Wave 30 MVP: a header + the rationale
    + a list of input note ids with their tags. The agent that runs `myco
    compress` is expected to fill `--rationale` with the actual synthesis
    prose; this body is the audit-trail scaffolding around it.

    Future waves may make this richer (e.g. extract the most-frequent tags,
    sample sentences from each input). Wave 30 ships the minimal scaffold
    so that the verb is correct first, fancy second.
    """
    lines: List[str] = []
    lines.append(f"# Compressed synthesis of {len(cohort)} note(s)")
    lines.append("")
    lines.append("## Rationale")
    lines.append("")
    lines.append(rationale.strip())
    lines.append("")
    lines.append("## Source cohort")
    lines.append("")
    for p in cohort:
        try:
            meta, _ = read_note(p)
        except (OSError, ValueError, RuntimeError):
            lines.append(f"- `{p.stem}` (read error)")
            continue
        tags = ", ".join(meta.get("tags") or [])
        lines.append(
            f"- `{p.stem}` — status before compress: "
            f"`{meta.get('status', 'unknown')}`"
            + (f", tags: {tags}" if tags else "")
        )
    lines.append("")
    lines.append(
        "_Generated by `myco compress` Wave 30. Inputs are preserved on "
        "disk with `status: excreted` + `compressed_into` back-reference. "
        "See `compressed_from` frontmatter for the canonical input list._"
    )
    lines.append("")
    return "\n".join(lines)


def _build_output_meta(
    output_id: str,
    cohort: List[Path],
    rationale: str,
    confidence: float,
    method: str,
    now: datetime,
) -> Dict[str, Any]:
    """Construct the frontmatter dict for the new extracted note.

    Required-fields shape comes from `notes.py::REQUIRED_FIELDS` so the
    note passes L10 lint. Audit fields (Wave 30 additions) are appended.

    Wave 27 D3: `status: extracted` (NOT `integrated` — integration is a
    separate downstream decision). Wave 27 D4: `source: compress` (new
    enum value added to `_canon.yaml::valid_sources` in this same wave).
    """
    iso = now.strftime("%Y-%m-%dT%H:%M:%S")
    cohort_ids = [p.stem for p in cohort]

    # Aggregate tags from inputs (deduplicate, preserve first-seen order).
    aggregated_tags: List[str] = []
    seen = set()
    for p in cohort:
        try:
            meta, _ = read_note(p)
        except (OSError, ValueError, RuntimeError):
            continue
        for t in (meta.get("tags") or []):
            if t not in seen:
                seen.add(t)
                aggregated_tags.append(t)

    return {
        "id": output_id,
        "status": "extracted",
        "source": "compress",
        "tags": aggregated_tags,
        "created": iso,
        "last_touched": iso,
        "digest_count": 0,
        "promote_candidate": False,
        "excrete_reason": None,
        # Wave 30 audit fields (registered in _canon.yaml::optional_fields):
        "compressed_from": cohort_ids,
        "compression_method": method,
        "compression_rationale": rationale.strip(),
        "compression_confidence": float(confidence),
    }


def _build_input_update(
    input_meta: Dict[str, Any],
    output_id: str,
    cohort_size: int,
    now: datetime,
) -> Dict[str, Any]:
    """Compute the new frontmatter dict for an input note being excreted.

    Wave 27 D5: preserve `pre_compression_status` so a future `myco
    uncompress` can restore the original status. Wave 27 D3: status →
    excreted, excrete_reason cites the output id and cohort size.
    """
    iso = now.strftime("%Y-%m-%dT%H:%M:%S")
    new_meta = dict(input_meta)
    pre_status = new_meta.get("status", "raw")
    new_meta["pre_compression_status"] = pre_status
    new_meta["status"] = "excreted"
    new_meta["excrete_reason"] = (
        f"compressed into {output_id} as part of {cohort_size}-note cohort"
    )
    new_meta["compressed_into"] = output_id
    new_meta["last_touched"] = iso
    return new_meta


# ---------------------------------------------------------------------------
# Two-phase commit
# ---------------------------------------------------------------------------

def _execute_compression(
    root: Path,
    cohort: List[Path],
    rationale: str,
    confidence: float,
    method: str,
    *,
    now: Optional[datetime] = None,
) -> Tuple[Path, List[Path]]:
    """Phase 1 + Phase 2: produce the output note and excrete the inputs.

    Returns (output_path, [input_paths]). Raises on any phase-1 failure.
    Phase-2 failures emit `[WARN]` to stderr but the function still
    returns the partial result so the caller can report it.

    The function is intentionally tested in tests/unit/test_compress.py
    via direct calls (bypassing argparse) — that is the unit-of-work
    boundary where atomicity matters.
    """
    now = now or datetime.now()

    # ---- Generate output id (collision-safe in same-second runs) ----
    notes_dir = root / NOTES_DIRNAME
    output_id = generate_id(now)
    while (notes_dir / id_to_filename(output_id)).exists():
        output_id = generate_id(now)
    output_path = notes_dir / id_to_filename(output_id)

    # ---- Build output content ----
    body = _build_output_body(cohort, rationale)
    meta = _build_output_meta(
        output_id, cohort, rationale, confidence, method, now,
    )
    output_text = serialize_note(meta, body)

    # ---- Build input updates ----
    pending_updates: List[Tuple[Path, str]] = []
    for p in cohort:
        try:
            input_meta, input_body = read_note(p)
        except Exception as exc:
            raise RuntimeError(
                f"compress phase-1: cannot read {p.name}: {exc}"
            ) from exc
        new_meta = _build_input_update(input_meta, output_id, len(cohort), now)
        new_text = serialize_note(new_meta, input_body)
        pending_updates.append((p, new_text))

    # ---- Phase 2: atomic writes ----
    # Output first — if this fails the inputs are unchanged.
    atomic_write_text(output_path, output_text)

    # Now flip each input. If any input write fails, the substrate is
    # left torn (output exists, some inputs flipped, others not). Best-
    # effort: emit a warning per failed input but keep going so the
    # caller's error report is complete.
    failed_inputs: List[str] = []
    for in_path, in_text in pending_updates:
        try:
            atomic_write_text(in_path, in_text)
        except Exception as exc:
            failed_inputs.append(f"{in_path.name} ({exc})")

    if failed_inputs:
        print(
            f"[WARN] myco compress: {len(failed_inputs)} input(s) failed "
            f"to update after output was written. Substrate is in a torn "
            f"state. Manual recovery: edit each failed input's frontmatter "
            f"to set status: excreted + compressed_into: {output_id}. "
            f"Failed: {'; '.join(failed_inputs)}",
            file=sys.stderr,
        )

    # Track lifetime excretions (survives note deletion on disk).
    # Compression bypasses update_note, so we must increment here.
    excretion_count = len(pending_updates) - len(failed_inputs)
    if excretion_count > 0:
        try:
            from myco.notes import increment_excretion_counter
            increment_excretion_counter(root, count=excretion_count)
        except (OSError, ImportError, ValueError):
            pass  # best-effort — never block compression

    return output_path, [p for p, _ in pending_updates]


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def run_compress(args) -> int:
    """`myco compress` — Wave 30 forward compression verb.

    Wires the CLI subparser to the `_execute_compression` worker. Handles
    all the argparse-level concerns (cohort source XOR, dry-run, JSON
    output) before delegating the actual mutation to the worker.

    Exit codes:
      0 — success (or successful dry-run)
      2 — usage error (missing rationale, both --tag and ids given, etc.)
      3 — validation error (cascade rejected, excreted input rejected)
      4 — empty cohort (nothing to compress)
      5 — io error (cannot read project, cannot write notes/)
    """
    try:
        root = resolve_project_dir(args, strict=True)
    except MycoProjectNotFound as e:
        print(f"compress: {e}", file=sys.stderr)
        return 5

    # ---- Validate input arguments ----
    tag = getattr(args, "tag", None)
    note_ids = list(getattr(args, "note_ids", None) or [])
    rationale = getattr(args, "rationale", None) or ""
    dry_run = bool(getattr(args, "dry_run", False))
    status_filter = getattr(args, "status", None)
    confidence = float(getattr(args, "confidence", 0.85) or 0.85)
    json_out = bool(getattr(args, "json", False))
    cohort_mode = getattr(args, "cohort", None)

    # Wave 48: --cohort auto resolves tag from cohort intelligence
    if cohort_mode == "auto":
        if tag or note_ids:
            print(
                "compress: --cohort auto is mutually exclusive with --tag "
                "and positional note ids",
                file=sys.stderr,
            )
            return 2
        try:
            from myco.colony import compression_cohort_suggest
            suggestions = compression_cohort_suggest(root)
            if not suggestions:
                print("compress: --cohort auto found no ripe cohorts", file=sys.stderr)
                return 4
            tag = suggestions[0]["tag"]
            print(f"compress: --cohort auto selected tag '{tag}' "
                  f"({suggestions[0]['note_count']} notes, "
                  f"score {suggestions[0]['cohort_score']})")
        except Exception as e:
            print(f"compress: --cohort auto failed: {e}", file=sys.stderr)
            return 5

    if tag and note_ids:
        print(
            "compress: --tag and positional note ids are mutually exclusive",
            file=sys.stderr,
        )
        return 2
    if not tag and not note_ids:
        print(
            "compress: must provide either --tag <TAG>, positional note ids, "
            "or --cohort auto",
            file=sys.stderr,
        )
        return 2
    if status_filter is not None and status_filter not in VALID_STATUSES:
        print(
            f"compress: --status {status_filter!r} is not a valid status "
            f"({', '.join(VALID_STATUSES)})",
            file=sys.stderr,
        )
        return 2
    if not rationale.strip():
        print(
            "compress: --rationale is required (Wave 27 D4 audit trail). "
            "Pass a one-paragraph explanation of what the synthesis "
            "preserves vs drops.",
            file=sys.stderr,
        )
        return 2
    if not (0.0 <= confidence <= 1.0):
        print(
            f"compress: --confidence {confidence} must be in [0.0, 1.0]",
            file=sys.stderr,
        )
        return 2

    # ---- Resolve cohort ----
    if tag:
        cohort = _resolve_cohort_by_tag(root, tag, status_filter)
    else:
        try:
            cohort = _resolve_cohort_by_ids(root, note_ids)
        except FileNotFoundError as exc:
            print(str(exc), file=sys.stderr)
            return 5

    # ---- Validate cohort ----
    if not cohort:
        msg = (
            f"compress: empty cohort for tag {tag!r}"
            if tag
            else "compress: empty cohort (no notes resolved from given ids)"
        )
        print(msg, file=sys.stderr)
        return 4

    errors = _validate_cohort(cohort)
    if errors:
        for e in errors:
            print(f"compress: {e}", file=sys.stderr)
        return 3

    # ---- Dry run: print plan and exit ----
    if dry_run:
        plan = {
            "cohort_size": len(cohort),
            "cohort_ids": [p.stem for p in cohort],
            "rationale": rationale.strip(),
            "confidence": confidence,
            "method": "manual",
            "would_create": "<new extracted note id, generated at execution>",
            "would_excrete": [p.stem for p in cohort],
        }
        if json_out:
            print(json.dumps(plan, ensure_ascii=False, indent=2))
        else:
            print(f"\n🍄 myco compress — DRY RUN")
            print(f"───────────────────────────")
            print(f"  cohort size: {len(cohort)}")
            print(f"  rationale:   {rationale.strip()[:80]}"
                  f"{'...' if len(rationale.strip()) > 80 else ''}")
            print(f"  confidence:  {confidence:.2f}")
            print(f"  method:      manual")
            print(f"  inputs to be excreted:")
            for cid in [p.stem for p in cohort]:
                print(f"    - {cid}")
            print(f"  output: <new extracted note, id assigned at execution>")
            print(f"\n  Run again without --dry-run to execute.")
        return 0

    # ---- Execute compression ----
    try:
        output_path, input_paths = _execute_compression(
            root,
            cohort,
            rationale.strip(),
            confidence,
            "manual",
        )
    except Exception as exc:
        print(f"compress: execution failed: {exc}", file=sys.stderr)
        return 5

    output_id = output_path.stem
    rel = output_path.relative_to(root)

    if json_out:
        print(json.dumps({
            "status": "ok",
            "output_id": output_id,
            "output_file": str(rel),
            "compressed_from": [p.stem for p in input_paths],
            "cohort_size": len(input_paths),
            "method": "manual",
            "confidence": confidence,
        }, ensure_ascii=False))
    else:
        print(f"\n🍄 myco compress — DONE")
        print(f"───────────────────────")
        print(f"  output:    {output_id}")
        print(f"  file:      {rel}")
        print(f"  status:    extracted")
        print(f"  source:    compress")
        print(f"  compressed_from ({len(input_paths)} input(s)):")
        for p in input_paths:
            print(f"    - {p.stem}")
        print(f"\n  Inputs are preserved on disk with status: excreted")
        print(f"  + compressed_into: {output_id} (Wave 27 D5 reversibility).")
    return 0


# ---------------------------------------------------------------------------
# Wave 31: `myco uncompress` — closes Wave 30 L4 limitation
# ---------------------------------------------------------------------------
#
# Wave 30 L4 said: "myco uncompress verb is still vapor. Wave 27 D5 deferred
# to Wave 29+. Wave 30 preserves the data (pre_compression_status field is
# written), but no uncompress verb exists."
#
# Wave 31 implements the verb. Mechanically simple because Wave 30 D2 + D5
# preserved everything needed:
#   - inputs are still on disk (status excreted, not deleted)
#   - inputs carry pre_compression_status (the prior status to restore)
#   - inputs carry compressed_into (back-link to verify the chain)
#   - the output's compressed_from list is the canonical input enumeration
#
# Two-phase commit, output-LAST ordering (mirror of compress's output-first):
#   Phase 1: validate the output is a real compress output, validate every
#            input back-link, build all restored input contents in memory.
#   Phase 2: write each restored input via atomic_write_text, THEN delete
#            the output. If any input write fails, the output still exists
#            and the partial restoration is recoverable. L18 lint will not
#            fire because compressed_from members still exist; the only
#            sign of partial uncompress is some inputs flipped and others
#            still excreted — visible to myco view but not a lint violation.

def _build_input_restore(input_meta: Dict[str, Any]) -> Dict[str, Any]:
    """Compute the restored frontmatter for an excreted input being uncompressed.

    Wave 31 D2: this is the inverse of `_build_input_update`. It restores
    `status` from `pre_compression_status`, clears the four compression
    audit fields on the input side, and refreshes `last_touched`. The
    excrete_reason is also cleared because the note is no longer excreted.
    """
    iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    new_meta = dict(input_meta)
    pre_status = new_meta.get("pre_compression_status", "raw")
    new_meta["status"] = pre_status
    new_meta["last_touched"] = iso
    # Clear all four compression-related fields by setting to None;
    # serialize_note will drop None values from the frontmatter.
    new_meta["pre_compression_status"] = None
    new_meta["compressed_into"] = None
    new_meta["excrete_reason"] = None
    return new_meta


def _execute_uncompression(
    root: Path,
    output_path: Path,
) -> Tuple[Path, List[Path]]:
    """Phase 1 + Phase 2 inverse of `_execute_compression`.

    Returns (deleted_output_path, [restored_input_paths]).
    Raises on phase-1 validation failure with a clear stderr-grade message.
    Phase-2 per-input write failures emit a `[WARN]` to stderr but the
    function still returns the partial result so the caller can report it.
    """
    notes_dir = root / NOTES_DIRNAME

    # ---- Phase 1: validate output ----
    try:
        out_meta, _ = read_note(output_path)
    except Exception as exc:
        raise RuntimeError(f"uncompress: cannot read output {output_path.name}: {exc}") from exc

    if out_meta.get("status") != "extracted":
        raise RuntimeError(
            f"uncompress: {output_path.name} status is {out_meta.get('status')!r}, "
            f"not 'extracted' — only compress outputs are uncompressible"
        )
    if out_meta.get("source") != "compress":
        raise RuntimeError(
            f"uncompress: {output_path.name} source is {out_meta.get('source')!r}, "
            f"not 'compress' — only compress outputs are uncompressible"
        )
    cohort_ids = out_meta.get("compressed_from") or []
    if not isinstance(cohort_ids, list) or not cohort_ids:
        raise RuntimeError(
            f"uncompress: {output_path.name} has no compressed_from list — "
            f"not a valid compress output"
        )
    output_id = out_meta.get("id")
    if not output_id:
        raise RuntimeError(f"uncompress: {output_path.name} has no id field")

    # ---- Phase 1: validate each input back-link, build restored content ----
    pending_restores: List[Tuple[Path, str]] = []
    for input_id in cohort_ids:
        in_path = notes_dir / id_to_filename(input_id)
        if not in_path.exists():
            raise RuntimeError(
                f"uncompress: input note {input_id} listed in {output_path.name}'s "
                f"compressed_from is missing from notes/ — broken audit chain. "
                f"Run `myco immune` for details (L18 should have caught this earlier)."
            )
        try:
            in_meta, in_body = read_note(in_path)
        except Exception as exc:
            raise RuntimeError(
                f"uncompress: cannot read input {in_path.name}: {exc}"
            ) from exc
        back_link = in_meta.get("compressed_into")
        if back_link != output_id:
            raise RuntimeError(
                f"uncompress: input {input_id} compressed_into is {back_link!r}, "
                f"not {output_id!r} — broken back-link, refusing to restore"
            )
        if in_meta.get("status") != "excreted":
            raise RuntimeError(
                f"uncompress: input {input_id} status is {in_meta.get('status')!r}, "
                f"not 'excreted' — already restored or in unexpected state"
            )
        new_meta = _build_input_restore(in_meta)
        new_text = serialize_note(new_meta, in_body)
        pending_restores.append((in_path, new_text))

    # ---- Phase 2: atomic writes (inputs first, output deletion last) ----
    failed_inputs: List[str] = []
    restored_paths: List[Path] = []
    for in_path, in_text in pending_restores:
        try:
            atomic_write_text(in_path, in_text)
            restored_paths.append(in_path)
        except Exception as exc:
            failed_inputs.append(f"{in_path.name} ({exc})")

    if failed_inputs:
        print(
            f"[WARN] myco uncompress: {len(failed_inputs)} input(s) failed "
            f"to restore. Output note NOT deleted to preserve recovery anchor. "
            f"Failed: {'; '.join(failed_inputs)}",
            file=sys.stderr,
        )
        # Do NOT delete the output if any input failed — the output is the
        # only remaining recovery anchor for the failed inputs.
        return output_path, restored_paths

    # All inputs restored — safe to delete the output.
    try:
        output_path.unlink()
    except Exception as exc:
        print(
            f"[WARN] myco uncompress: all inputs restored but output deletion "
            f"failed: {exc}. Substrate is in an unusual state — output exists "
            f"but its compressed_from members no longer point back. L18 will "
            f"flag this as orphan back-link on next lint.",
            file=sys.stderr,
        )

    return output_path, restored_paths


def run_uncompress(args) -> int:
    """`myco uncompress <output_id>` — Wave 31 reverse compression verb.

    Closes Wave 30 L4 limitation. Reverses a single compress output:
    restores each input note to its `pre_compression_status` and deletes
    the output extracted note. Bidirectional back-link integrity is
    validated before any writes.

    Exit codes:
      0 — success
      2 — usage error (missing output_id)
      3 — validation error (not an extracted compress output, broken
          back-link, missing input)
      5 — io error (cannot read project, cannot write notes/)
    """
    try:
        root = resolve_project_dir(args, strict=True)
    except MycoProjectNotFound as e:
        print(f"uncompress: {e}", file=sys.stderr)
        return 5

    output_id = getattr(args, "output_id", None)
    if not output_id:
        print(
            "uncompress: must provide output note id positional argument",
            file=sys.stderr,
        )
        return 2

    json_out = bool(getattr(args, "json", False))
    notes_dir = root / NOTES_DIRNAME
    output_path = notes_dir / id_to_filename(output_id)
    if not output_path.exists():
        print(f"uncompress: output note {output_id} not found", file=sys.stderr)
        return 5

    try:
        deleted_output, restored_paths = _execute_uncompression(root, output_path)
    except RuntimeError as exc:
        print(f"uncompress: {exc}", file=sys.stderr)
        return 3
    except Exception as exc:
        print(f"uncompress: execution failed: {exc}", file=sys.stderr)
        return 5

    restored_ids = [p.stem for p in restored_paths]
    if json_out:
        print(json.dumps({
            "status": "ok",
            "deleted_output": output_id,
            "restored_inputs": restored_ids,
            "restored_count": len(restored_ids),
        }, ensure_ascii=False))
    else:
        print(f"\n🍄 myco uncompress — DONE")
        print(f"─────────────────────────")
        print(f"  deleted output: {output_id}")
        print(f"  restored inputs ({len(restored_ids)}):")
        for rid in restored_ids:
            print(f"    - {rid}")
        print(f"\n  Each input's status is restored from pre_compression_status.")
        print(f"  The compressed_from audit chain is now broken (output gone).")
    return 0
