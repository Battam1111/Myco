"""Wave 30 seed tests — ``myco compress`` forward-compression invariants.

Five focused tests covering the load-bearing paths of the compress verb
and L18 lint integrity. These extend the Wave 25 seed in
``tests/unit/test_notes.py`` and follow the same scar-class rationale:
each test guards a specific Wave 27 / Wave 30 design decision.

Wave 27 design coverage:

- ``test_compress_consumptive_with_audit`` exercises Wave 27 D3 (output
  shape: extracted note + N excreted inputs with bidirectional links)
  and Wave 27 D4 (audit fields: compressed_from, compression_method,
  compression_rationale, compression_confidence). Failure means the
  output shape regressed silently.
- ``test_compress_dry_run_no_writes`` exercises Wave 27 Attack G defense:
  ``--dry-run`` must NOT touch any file. Without this test the dry-run
  could regress to a "writes anyway, prints success" — same shape as
  the prior `--no-verify` Goodhart class.
- ``test_compress_cascade_rejected`` exercises Wave 27 §2.1 defense #4:
  compression-on-compression is structurally rejected. This is the
  hallucination-amplification firewall — without it, every compress
  cycle could drift further from the originals.
- ``test_compress_idempotent_empty_cohort`` exercises Wave 27 §1.7:
  re-running ``myco compress --tag X`` after success is a no-op
  (cohort is empty because inputs are now excreted). Without this
  test the verb could re-compress its own output (cascade) or
  silently produce a duplicate output note.
- ``test_lint_compression_integrity_catches_orphan`` exercises L18
  Wave 30 lint dimension: tampering with `compressed_into` to point
  at a non-existent output is caught at lint time. Without this test
  the audit chain could silently corrupt and Wave 27 D5 reversibility
  would be aspirational, not enforceable.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from myco import notes
from myco.compress_cmd import (
    _execute_compression,
    _resolve_cohort_by_tag,
    run_compress,
)
from myco.lint import lint_compression_integrity, load_canon


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _eat_n(project: Path, n: int, tag: str) -> list[Path]:
    """Helper: write N raw notes carrying the given tag, return their paths.

    Each note has unique body so the synthesis can prove inputs were
    distinct. Tags are a single-element list per note (the cohort tag)
    so we don't accidentally pull in cross-tag pollution.
    """
    paths = []
    for i in range(n):
        p = notes.write_note(
            project,
            body=f"input note {i} for cohort {tag}",
            tags=[tag],
            source="eat",
            status="raw",
            title=f"Cohort {tag} note {i}",
        )
        paths.append(p)
    return paths


def _make_args(**kwargs) -> SimpleNamespace:
    """Helper: build a fake argparse Namespace for run_compress."""
    defaults = {
        "tag": None,
        "note_ids": None,
        "rationale": None,
        "status": None,
        "confidence": 0.85,
        "dry_run": False,
        "json": False,
        "project_dir": ".",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_compress_consumptive_with_audit(_isolate_myco_project: Path) -> None:
    """Wave 27 D3 + D4: output is extracted + inputs are excreted with
    bidirectional back-references and full audit metadata.
    """
    project = _isolate_myco_project

    inputs = _eat_n(project, 3, "wave30-test")
    cohort = _resolve_cohort_by_tag(project, "wave30-test")
    assert len(cohort) == 3, "tag-resolver should pick up all 3 inputs"

    output_path, input_paths = _execute_compression(
        project,
        cohort,
        rationale="3-note synthesis test cohort for Wave 30",
        confidence=0.85,
        method="manual",
    )

    # ---- Output shape ----
    assert output_path.exists()
    out_meta, out_body = notes.read_note(output_path)
    assert out_meta["status"] == "extracted", "Wave 27 D3: status must be extracted"
    assert out_meta["source"] == "compress", "Wave 27 D4: source must be compress"
    assert out_meta["compression_method"] == "manual"
    assert out_meta["compression_rationale"].startswith("3-note synthesis test")
    assert out_meta["compression_confidence"] == 0.85
    assert isinstance(out_meta["compressed_from"], list)
    assert len(out_meta["compressed_from"]) == 3
    output_id = out_meta["id"]

    # ---- Input shape ----
    for in_path in input_paths:
        in_meta, _ = notes.read_note(in_path)
        assert in_meta["status"] == "excreted", \
            "Wave 27 D3: each input must be excreted"
        assert in_meta["compressed_into"] == output_id, \
            "Wave 27 D4: bidirectional link must point at output"
        assert in_meta["pre_compression_status"] == "raw", \
            "Wave 27 D5: prior status must be preserved for uncompress"
        assert "compressed into" in in_meta["excrete_reason"]
        assert in_meta["id"] in out_meta["compressed_from"]

    # ---- L18 lint must accept this fresh substrate ----
    canon = load_canon(project)
    issues = lint_compression_integrity(canon, project)
    assert issues == [], f"L18 must accept a freshly-compressed cohort: {issues}"


def test_compress_dry_run_no_writes(_isolate_myco_project: Path) -> None:
    """Wave 27 Attack G defense: --dry-run must NOT mutate disk.

    Captures the cohort + rationale before/after the dry-run and
    asserts every note's mtime + content + frontmatter is identical.
    """
    project = _isolate_myco_project

    inputs = _eat_n(project, 4, "dry-run-test")
    snapshot_before = {}
    for p in inputs:
        snapshot_before[p.name] = (p.read_text(encoding="utf-8"), p.stat().st_mtime_ns)

    args = _make_args(
        tag="dry-run-test",
        rationale="should not write anything",
        dry_run=True,
        project_dir=str(project),
    )
    rc = run_compress(args)
    assert rc == 0, "dry-run with valid cohort must exit 0"

    # Same files exist with same content + same mtime
    for p in inputs:
        assert p.exists()
        new_text, new_mtime = p.read_text(encoding="utf-8"), p.stat().st_mtime_ns
        assert new_text == snapshot_before[p.name][0], \
            f"dry-run mutated {p.name} content"
        assert new_mtime == snapshot_before[p.name][1], \
            f"dry-run touched {p.name} mtime"

    # No new note files were created
    notes_dir = project / "notes"
    note_paths = sorted(notes_dir.glob("n_*.md"))
    assert len(note_paths) == 4, \
        f"dry-run must not create new files; found {len(note_paths)}"


def test_compress_cascade_rejected(_isolate_myco_project: Path) -> None:
    """Wave 27 §2.1 defense #4: compressing already-compressed notes
    is rejected at validation time, BEFORE any writes happen.
    """
    project = _isolate_myco_project

    # First compression cycle: 3 inputs → 1 output
    _eat_n(project, 3, "cycle1")
    cohort1 = _resolve_cohort_by_tag(project, "cycle1")
    output1, _ = _execute_compression(
        project, cohort1,
        rationale="cycle 1", confidence=0.85, method="manual",
    )
    out1_meta, _ = notes.read_note(output1)
    assert out1_meta["compressed_from"]
    output1_id = out1_meta["id"]

    # Second cycle attempt: explicit ids targeting the cycle 1 OUTPUT
    # This should be rejected because cycle 1 output has compressed_from set.
    args = _make_args(
        note_ids=[output1_id],
        rationale="should be rejected — cascade",
        project_dir=str(project),
    )
    rc = run_compress(args)
    assert rc == 3, \
        f"cascade compression must be rejected with exit 3 (validation), got {rc}"

    # Output 1 must still be intact (no extra mutation, no new note created)
    out1_meta_after, _ = notes.read_note(output1)
    assert out1_meta_after == out1_meta, \
        "rejected compression must not mutate the targeted note"


def test_compress_idempotent_empty_cohort(_isolate_myco_project: Path) -> None:
    """Wave 27 §1.7: re-running compress on an already-compressed tag
    cohort is a no-op (cohort is empty because inputs are now excreted).
    """
    project = _isolate_myco_project

    _eat_n(project, 5, "idempotent")

    # First run: should succeed
    args1 = _make_args(
        tag="idempotent",
        rationale="first compression run",
        project_dir=str(project),
    )
    rc1 = run_compress(args1)
    assert rc1 == 0, "first compress must succeed"

    notes_dir = project / "notes"
    notes_after_first = sorted(notes_dir.glob("n_*.md"))
    assert len(notes_after_first) == 6, \
        "after first run: 5 inputs (excreted) + 1 output extracted = 6"

    # Second run: empty cohort because all inputs are now excreted
    args2 = _make_args(
        tag="idempotent",
        rationale="second compression run — should be no-op",
        project_dir=str(project),
    )
    rc2 = run_compress(args2)
    assert rc2 == 4, \
        f"second compress on already-compressed cohort must exit 4, got {rc2}"

    notes_after_second = sorted(notes_dir.glob("n_*.md"))
    assert len(notes_after_second) == 6, \
        "second compress (empty cohort) must not create new files"


def test_lint_compression_integrity_catches_orphan(
    _isolate_myco_project: Path,
) -> None:
    """L18 (Wave 30): if a note's `compressed_into` points to a non-existent
    output, L18 must fire HIGH. This is the bidirectional-integrity guard
    that makes Wave 27 D5 reversibility enforceable rather than aspirational.
    """
    project = _isolate_myco_project

    inputs = _eat_n(project, 3, "orphan-test")
    cohort = _resolve_cohort_by_tag(project, "orphan-test")
    output_path, input_paths = _execute_compression(
        project, cohort,
        rationale="orphan test", confidence=0.85, method="manual",
    )

    # Tamper: delete the output note, leaving inputs with dangling
    # compressed_into. This is the exact shape that would result from
    # a partial filesystem corruption or out-of-band manual deletion.
    output_path.unlink()

    canon = load_canon(project)
    issues = lint_compression_integrity(canon, project)

    assert issues, "L18 must catch orphan compressed_into pointers"
    high_issues = [i for i in issues if i[1] == "HIGH"]
    assert high_issues, "orphan must be HIGH severity"
    msgs = " ".join(issue[3] for issue in high_issues)
    assert "broken audit chain" in msgs or "unknown" in msgs, \
        f"L18 issue should mention broken chain: {msgs}"
