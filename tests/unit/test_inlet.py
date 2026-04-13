"""Wave 35 seed tests — ``myco inlet`` Metabolic Inlet primitive invariants.

Five focused tests covering the load-bearing paths of the Wave 34 §3.1
specification. Same scar-class rationale as the Wave 25 / Wave 30 / Wave 33
seed tests: each test guards one Wave 34 design decision under
implementation pressure.

Wave 34 design coverage:

- ``test_inlet_file_creates_raw_note_with_provenance`` guards Wave 34 D1
  (file form is the most common) + D3 (status: raw, NOT pre-digested) + D4
  (source: inlet, new enum) + the 4-field provenance scaffold (D6). If
  the provenance contract regresses, every downstream cross-ref/audit on
  inlet notes would silently lose attribution.

- ``test_inlet_explicit_content_creates_raw_note`` guards Wave 34 D2 (zero-
  deps URL contract): the agent-fetch + ``--content``/``--provenance``
  pipe pattern is the only way to inlet URL content into the kernel. If
  this path breaks, the entire scaffold's "URL is operator-deferred"
  argument collapses.

- ``test_inlet_url_form_rejected_with_clear_message`` guards Wave 34 D2
  reject branch + the user-facing error message contract. The instruction
  in the error must point at the agent-fetch pattern; without that, an
  operator hitting this error has no path forward and the scaffold
  becomes a dead end instead of a deferred sub-problem.

- ``test_inlet_default_tag_applied_when_tags_missing`` guards Wave 34 D6
  (canon-driven default tag) + the operator UX contract: a fresh inlet
  with no ``--tags`` flag should immediately be eligible for ``myco
  compress --tag inlet`` without operator memory burden.

- ``test_inlet_lints_clean_under_l10`` guards the soft inlet provenance
  check added to L10 in Wave 35: a freshly-inletted note must lint clean
  on all 4 inlet_* fields. Without this, the soft check could silently
  warn on every kernel-produced inlet (the opposite of its design intent).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from myco import notes
from myco.inlet_cmd import (
    _build_inlet_meta,
    _resolve_default_tag,
    _resolve_inlet_input,
    run_inlet,
)
from myco.lint import lint_notes_schema, load_canon


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_inlet_args(**kwargs) -> SimpleNamespace:
    """Build a fake argparse Namespace for run_inlet."""
    defaults = {
        "source": None,
        "content": None,
        "provenance": None,
        "tags": None,
        "json": False,
        "project_dir": ".",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _extend_canon_with_notes_schema(project: Path) -> None:
    """The minimal conftest canon doesn't include notes_schema. Tests that
    exercise L10 lint must extend it. Mirrors what Wave 35's contract
    bump requires for schema validation.
    """
    extended = """\
system:
  principles_count: 13
  principles_label: "十三原則"
  entry_point: MYCO.md
  contract_version: "v0.27.0"
  synced_contract_version: "v0.27.0"
  notes_schema:
    dir: notes
    filename_pattern: '^n_\\d{8}T\\d{6}_[0-9a-f]{4}\\.md$'
    required_fields:
      - id
      - status
      - source
      - tags
      - created
      - last_touched
      - digest_count
      - promote_candidate
      - excrete_reason
    valid_statuses:
      - raw
      - digesting
      - extracted
      - integrated
      - excreted
    valid_sources:
      - chat
      - eat
      - promote
      - import
      - bootstrap
      - forage
      - compress
      - inlet
    inlet:
      default_tag: "inlet"
architecture:
  layers: 4
  wiki_pages: 0
project:
  name: TestProject
"""
    (project / "_canon.yaml").write_text(extended, encoding="utf-8")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_inlet_file_creates_raw_note_with_provenance(
    _isolate_myco_project: Path,
) -> None:
    """Wave 35 D1: ``myco inlet <path>`` creates a raw note whose
    frontmatter has source=inlet and all 4 inlet_* provenance fields populated.
    """
    project = _isolate_myco_project

    # Stage a source file outside notes/ so the inlet has a real provenance.
    src_path = project / "external_paper.md"
    src_body = "# External Paper\n\nKey claim: load-bearing test passes.\n"
    src_path.write_text(src_body, encoding="utf-8")

    args = _make_inlet_args(source=str(src_path), project_dir=str(project))
    rc = run_inlet(args)
    assert rc == 0, "inlet file form must succeed"

    # Find the new note (only one in the dir).
    notes_dir = project / "notes"
    new_notes = sorted(notes_dir.glob("n_*.md"))
    assert len(new_notes) == 1, f"expected 1 note, got {len(new_notes)}"

    meta, body = notes.read_note(new_notes[0])
    assert meta["source"] == "inlet"
    assert meta["status"] == "raw"
    # All 4 provenance fields populated
    assert meta["inlet_origin"] == str(src_path.resolve())
    assert meta["inlet_method"] == "file"
    assert meta["inlet_fetched_at"]  # ISO timestamp, non-empty
    expected_hash = hashlib.sha256(src_body.encode("utf-8")).hexdigest()
    assert meta["inlet_content_hash"] == expected_hash
    # Body preserves the original content (header is rendered above)
    assert "Key claim: load-bearing test passes." in body
    # Default tag applied
    assert meta["tags"] == ["inlet"]


def test_inlet_explicit_content_creates_raw_note(
    _isolate_myco_project: Path,
) -> None:
    """Wave 35 D2: ``myco inlet --content STR --provenance URL`` is the
    agent-fetch pipe pattern. Method must be ``url-fetched-by-agent``
    when --provenance is a URL, and ``explicit-content`` otherwise.
    """
    project = _isolate_myco_project

    # URL provenance → method url-fetched-by-agent
    args_url = _make_inlet_args(
        content="Body fetched from external API by Claude.",
        provenance="https://example.com/article/42",
        tags="api,wave35-test",
        project_dir=str(project),
    )
    rc = run_inlet(args_url)
    assert rc == 0

    notes_dir = project / "notes"
    after_url = sorted(notes_dir.glob("n_*.md"))
    assert len(after_url) == 1
    meta_url, _ = notes.read_note(after_url[0])
    assert meta_url["inlet_method"] == "url-fetched-by-agent"
    assert meta_url["inlet_origin"] == "https://example.com/article/42"
    assert set(meta_url["tags"]) == {"api", "wave35-test"}

    # Non-URL provenance → method explicit-content
    args_paste = _make_inlet_args(
        content="Pasted from clipboard.",
        provenance="manual-paste",
        project_dir=str(project),
    )
    rc = run_inlet(args_paste)
    assert rc == 0

    after_paste = sorted(notes_dir.glob("n_*.md"))
    assert len(after_paste) == 2
    # The new one is whichever wasn't there before
    new_paste = [p for p in after_paste if p not in after_url][0]
    meta_paste, _ = notes.read_note(new_paste)
    assert meta_paste["inlet_method"] == "explicit-content"
    assert meta_paste["inlet_origin"] == "manual-paste"


def test_inlet_url_form_rejected_with_clear_message(
    _isolate_myco_project: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """Wave 35 D2: ``myco inlet https://...`` (positional URL form) is
    rejected with exit code 2 and a clear instruction pointing at the
    agent-fetch pipe pattern.

    Without the instruction the operator has no path forward; the scaffold
    becomes a dead end instead of a deferred sub-problem.
    """
    project = _isolate_myco_project

    args = _make_inlet_args(
        source="https://example.com/article/99",
        project_dir=str(project),
    )
    rc = run_inlet(args)
    assert rc == 2, "URL form must be a usage error (exit 2)"

    captured = capsys.readouterr()
    err = captured.err
    assert "URL form is not supported" in err
    assert "--content" in err and "--provenance" in err
    # The error must include the URL itself so operator can copy-paste
    assert "https://example.com/article/99" in err

    # No note was created
    notes_dir = project / "notes"
    assert list(notes_dir.glob("n_*.md")) == []


def test_inlet_default_tag_applied_when_tags_missing(
    _isolate_myco_project: Path,
) -> None:
    """Wave 35 D6: when --tags is omitted, the canon default tag is
    applied so the existing ``myco compress --tag inlet`` chain works
    without operator memory burden.

    With the conftest's minimal canon (no notes_schema.inlet block),
    _resolve_default_tag falls back to "inlet". This test verifies BOTH
    the fallback path and the canon-extended path produce the same tag.
    """
    project = _isolate_myco_project

    # Path 1: minimal canon → fallback to "inlet"
    fallback_tag = _resolve_default_tag(project)
    assert fallback_tag == "inlet"

    # Path 2: extended canon with notes_schema.inlet.default_tag → reads canon
    _extend_canon_with_notes_schema(project)
    canon_tag = _resolve_default_tag(project)
    assert canon_tag == "inlet"

    # End-to-end: a note with no --tags gets the default tag applied
    args = _make_inlet_args(
        content="some content",
        provenance="manual-test",
        project_dir=str(project),
    )
    rc = run_inlet(args)
    assert rc == 0

    notes_dir = project / "notes"
    new_notes = sorted(notes_dir.glob("n_*.md"))
    assert len(new_notes) == 1
    meta, _ = notes.read_note(new_notes[0])
    assert meta["tags"] == ["inlet"], (
        "default tag must apply when --tags is omitted"
    )


def test_inlet_lints_clean_under_l10(_isolate_myco_project: Path) -> None:
    """Wave 35: a freshly-inletted note passes L10 (notes schema) including
    the new soft inlet provenance check.

    Failure here would mean the kernel produces inlet notes that its own
    lint flags — a contract drift between writer and validator. The Wave
    35 soft check is supposed to warn only on retroactively-tagged
    inlets, never on kernel-produced ones.
    """
    project = _isolate_myco_project
    _extend_canon_with_notes_schema(project)

    # Create one inlet note via the verb
    args = _make_inlet_args(
        content="lint smoke test body",
        provenance="https://example.com/lint-test",
        project_dir=str(project),
    )
    rc = run_inlet(args)
    assert rc == 0

    # Run L10 lint over the project
    canon = load_canon(project)
    issues = lint_notes_schema(canon, project)

    # The fresh inlet note must produce ZERO L10 issues.
    notes_dir = project / "notes"
    inlet_notes = list(notes_dir.glob("n_*.md"))
    assert len(inlet_notes) == 1
    inlet_path_rel = str(inlet_notes[0].relative_to(project))

    related = [i for i in issues if i[2] == inlet_path_rel]
    assert related == [], (
        f"fresh inlet note must lint clean, got: {related}"
    )
