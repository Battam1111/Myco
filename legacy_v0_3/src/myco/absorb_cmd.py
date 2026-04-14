#!/usr/bin/env python3
"""Metabolic Inlet — `myco inlet` verb implementation.

**Wave 35 (kernel_contract, contract v0.27.0)** — closes the longest-deferred
gap in Myco's identity surface: anchor #3 declared a Metabolic Inlet primitive
in Wave 10's vision recovery, but no implementation existed before this wave.
Wave 26 §2.3 catalogued the gap, Wave 34 designed the scaffold, and Wave 35
implements the MVP.

**Authoritative design**: docs/primordia/archive/metabolic_inlet_design_craft_2026-04-12.md
(Wave 34, exploration 0.85, 8 design questions answered, 6 attacks defended).

**Implementation craft**: docs/primordia/archive/inlet_mvp_craft_2026-04-12.md
(Wave 35, kernel_contract 0.90, validates Wave 34's scaffold under impl pressure).

**Verb shape** (locked in Wave 34 §3.1):

  myco inlet <path>                          # file form (most common)
  myco inlet --content STR --provenance STR  # explicit content form (agent piping)
  myco inlet --content STR --provenance STR --tags T1,T2
  myco inlet <https://...>                   # URL form — errors with clear instruction

**Behavior** (Wave 34 §1.4 specification, 4 sub-problems deferred to operator):

  1. Resolve input source: file path, --content/--provenance pair, or URL
     (URL form is rejected with a clear error pointing the operator at the
     agent-fetch + --content pipe pattern, per Wave 34 D2 + zero-deps contract)
  2. Compute provenance metadata: sha256 hash of body, ISO-8601 capture
     timestamp, inlet_method enum value
  3. Apply default tag from canon (`notes_schema.inlet.default_tag`) if
     --tags is not provided, so the existing `myco compress --tag inlet`
     chain works without operators having to remember the convention
  4. Build a raw note frontmatter dict that includes the 4 inlet_* provenance
     fields, write atomically via `atomic_write_text` (mirrors compress
     phase-2 ordering on a single output)
  5. Print the new note id + file path on success (or JSON if --json given)

**Provenance contract** (Wave 34 §1.6):

  inlet_origin       — required. Absolute path or URL string.
  inlet_method       — required enum: "file" | "url-fetched-by-agent" | "explicit-content"
  inlet_fetched_at   — required ISO-8601 timestamp.
  inlet_content_hash — required sha256 hex digest of body bytes (tamper detection).

**Operator-deferred sub-problems** (Wave 34 §2.4 — NOT solved here):

  open_problems §1 (cold start)               — defers to operator's choice of seed
  open_problems §2 (trigger signals)          — defers to operator-as-daemon
  open_problems §3 (alignment)                — defers to operator's evaluate step
  open_problems §4 (continuous compression)   — defers to existing `myco compress`

These four sub-problems were the reason Wave 34 stayed scaffold-only. Wave 35
ships the scaffold; Wave 36+ may revisit each as separate friction-driven waves.

**Zero-deps doctrine**: URL fetch is NOT in the kernel. The kernel exposes
`--content` + `--provenance` so agent wrappers (with HTTP clients) can fetch
externally and pipe content back without violating the no-stdlib-deps contract.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from myco.io_utils import atomic_write_text
from myco.notes import (
    MycoProjectNotFound,
    NOTES_DIRNAME,
    generate_id,
    id_to_filename,
    serialize_note,
)


# ---------------------------------------------------------------------------
# Project root resolution — now centralized in project.py
# ---------------------------------------------------------------------------

from myco.project import resolve_project_dir




# ---------------------------------------------------------------------------
# Default-tag resolver (reads canon at call time so test fixtures override cleanly)
# ---------------------------------------------------------------------------

def _resolve_default_tag(root: Path) -> str:
    """Read `notes_schema.inlet.default_tag` from canon, fall back to 'inlet'.

    Wave 34 D6 — keep the default tag canon-driven so a future operator can
    rename it without code changes. Read at call time (not import time) so
    test fixtures that swap canon take effect immediately.
    """
    try:
        import yaml  # type: ignore

        canon = yaml.safe_load((root / "_canon.yaml").read_text(encoding="utf-8")) or {}
    except (OSError, ImportError):
        # Missing canon file or missing PyYAML — safe default. YAML parse
        # errors are NOT silenced; a corrupt canon should surface.
        return "inlet"
    notes_schema = (canon.get("system") or {}).get("notes_schema") or {}
    inlet_cfg = notes_schema.get("inlet") or {}
    tag = inlet_cfg.get("default_tag")
    if isinstance(tag, str) and tag.strip():
        return tag.strip()
    return "inlet"


# ---------------------------------------------------------------------------
# Input resolution
# ---------------------------------------------------------------------------

def _resolve_inlet_input(args) -> Tuple[str, str, str]:
    """Resolve the inlet input from CLI args.

    Returns (content, provenance, method) where:
      content    = the body bytes to land in the new note
      provenance = the inlet_origin value (file path or URL or '<explicit>')
      method     = inlet_method enum: "file" | "url-fetched-by-agent" | "explicit-content"

    Resolution rules (Wave 34 §3.1):
      1. If positional <source> is given AND it looks like a URL → reject with
         a clear instruction to fetch via agent + pipe back via --content.
      2. If positional <source> is given AND it points to a real file → read
         the file, set method='file', provenance=absolute path.
      3. If --content + --provenance pair is given → method='explicit-content',
         provenance comes from --provenance verbatim. If --provenance starts
         with 'http' the method becomes 'url-fetched-by-agent' (this is the
         agent-wrapper pattern: agent fetches URL via WebFetch, then invokes
         `myco inlet --content "<body>" --provenance "<url>"`).
      4. Anything else → usage error.

    Raises:
      ValueError with a stderr-grade message on any unresolvable input.
    """
    source = getattr(args, "source", None)
    content = getattr(args, "content", None)
    provenance = getattr(args, "provenance", None)

    # Form 1: positional <source>
    if source:
        # URL form — explicit reject per Wave 34 D2 (zero-deps contract)
        if source.startswith(("http://", "https://")):
            raise ValueError(
                f"inlet: URL form is not supported by the kernel "
                f"(zero-stdlib-deps contract). To inlet a URL, fetch the "
                f"content via an agent wrapper (Claude WebFetch, curl, etc.) "
                f"and pipe it back as:\n"
                f"  myco inlet --content \"<body>\" --provenance \"{source}\"\n"
                f"This preserves provenance (inlet_origin={source}) while "
                f"keeping URL fetch out of the kernel."
            )
        # File form
        path = Path(source).expanduser()
        if not path.exists():
            raise ValueError(
                f"inlet: file not found: {source}. Pass an existing file "
                f"path or use --content/--provenance for explicit content."
            )
        if not path.is_file():
            raise ValueError(
                f"inlet: {source} is not a regular file."
            )
        try:
            body = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(
                f"inlet: {source} is not valid UTF-8: {exc}. The Metabolic "
                f"Inlet kernel only handles text. Convert binary content "
                f"externally before inlet."
            ) from exc
        return (body, str(path.resolve()), "file")

    # Form 2: --content + --provenance pair
    if content is not None or provenance is not None:
        if content is None:
            raise ValueError(
                "inlet: --provenance was given but --content was not. "
                "Both must be provided together (the explicit-content form)."
            )
        if provenance is None:
            raise ValueError(
                "inlet: --content was given but --provenance was not. "
                "Provenance is required so the inlet_origin field is "
                "machine-traceable. Pass --provenance \"<url-or-path>\"."
            )
        # Auto-detect agent-fetched URL pattern
        if provenance.startswith(("http://", "https://")):
            method = "url-fetched-by-agent"
        else:
            method = "explicit-content"
        return (content, provenance, method)

    # No form matched
    raise ValueError(
        "inlet: must provide either a file path or --content + --provenance. "
        "Examples:\n"
        "  myco inlet ./paper.md\n"
        "  myco inlet --content \"...\" --provenance \"https://example.com/article\"\n"
        "  myco inlet --content \"...\" --provenance \"manual-paste\""
    )


# ---------------------------------------------------------------------------
# Frontmatter builder
# ---------------------------------------------------------------------------

def _build_inlet_meta(
    note_id: str,
    content: str,
    provenance: str,
    method: str,
    tags: List[str],
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Construct the frontmatter dict for the new inlet note.

    Required-fields shape comes from `notes.py::REQUIRED_FIELDS` so the
    note passes L10. Wave 35 inlet_* provenance fields are appended.

    Wave 34 D3: `status: raw` (NOT pre-digested — operator's evaluate step
    is the alignment gate). Wave 34 D4: `source: inlet`.
    """
    now = now or datetime.now()
    iso = now.strftime("%Y-%m-%dT%H:%M:%S")
    body_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    return {
        "id": note_id,
        "status": "raw",
        "source": "inlet",
        "tags": list(tags),
        "created": iso,
        "last_touched": iso,
        "digest_count": 0,
        "promote_candidate": False,
        "excrete_reason": None,
        # Wave 35 provenance scaffold (registered in _canon.yaml::optional_fields):
        "inlet_origin": provenance,
        "inlet_method": method,
        "inlet_fetched_at": iso,
        "inlet_content_hash": body_hash,
    }


def _build_inlet_body(content: str, provenance: str, method: str) -> str:
    """Build the markdown body for an inlet note.

    Format: a short header citing the provenance + method, then the raw
    content verbatim. The header is human-scannable for `myco view`; the
    content is byte-identical to the input so the sha256 hash matches.

    Wave 34 §1.7 — body must preserve the input bytes so future tamper
    detection works. Adding a header at the top doesn't break this because
    the inlet_content_hash is computed over `content`, not over the
    markdown-rendered note body.
    """
    return (
        f"# Inlet — {method}\n"
        f"\n"
        f"**Origin**: `{provenance}`\n"
        f"\n"
        f"---\n"
        f"\n"
        f"{content}\n"
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def run_inlet(args) -> int:
    """`myco inlet` — Wave 35 Metabolic Inlet primitive.

    Wires the CLI subparser to the input resolver + frontmatter builder +
    atomic writer.

    Exit codes (locked in Wave 34 §3.1):
      0 — success
      2 — usage error (missing/conflicting args, URL-form rejected)
      3 — input validation error (file not UTF-8, file is a directory)
      5 — io error (cannot read project, cannot write notes/)
    """
    try:
        root = resolve_project_dir(args, strict=True)
    except MycoProjectNotFound as e:
        print(f"inlet: {e}", file=sys.stderr)
        return 5

    # ---- Resolve input ----
    try:
        content, provenance, method = _resolve_inlet_input(args)
    except ValueError as exc:
        msg = str(exc)
        print(msg, file=sys.stderr)
        # URL-form rejection is a usage error (2). UTF-8 / file-type errors
        # are content-validation errors (3). Discriminate by message marker.
        if "URL form is not supported" in msg or "must provide either" in msg or "was given but" in msg:
            return 2
        return 3

    # ---- Resolve tags (apply canon default if --tags missing) ----
    raw_tags = getattr(args, "tags", None)
    if raw_tags:
        if isinstance(raw_tags, str):
            tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
        else:
            tags = [str(t).strip() for t in raw_tags if str(t).strip()]
    else:
        tags = [_resolve_default_tag(root)]

    # ---- Generate id (collision-safe in same-second runs) ----
    notes_dir = root / NOTES_DIRNAME
    notes_dir.mkdir(parents=True, exist_ok=True)
    note_id = generate_id()
    while (notes_dir / id_to_filename(note_id)).exists():
        note_id = generate_id()
    note_path = notes_dir / id_to_filename(note_id)

    # ---- Build frontmatter + body ----
    meta = _build_inlet_meta(note_id, content, provenance, method, tags)
    body = _build_inlet_body(content, provenance, method)
    text = serialize_note(meta, body)

    # ---- Atomic write ----
    try:
        atomic_write_text(note_path, text)
    except Exception as exc:
        print(f"inlet: cannot write {note_path}: {exc}", file=sys.stderr)
        return 5

    # ---- Report ----
    rel = note_path.relative_to(root)
    json_out = bool(getattr(args, "json", False))
    if json_out:
        print(json.dumps({
            "status": "ok",
            "note_id": note_id,
            "note_file": str(rel),
            "inlet_origin": provenance,
            "inlet_method": method,
            "inlet_content_hash": meta["inlet_content_hash"],
            "tags": tags,
        }, ensure_ascii=False))
    else:
        print(f"\n🍄 myco inlet — DONE")
        print(f"────────────────────")
        print(f"  note:    {note_id}")
        print(f"  file:    {rel}")
        print(f"  status:  raw")
        print(f"  source:  inlet")
        print(f"  method:  {method}")
        print(f"  origin:  {provenance}")
        print(f"  tags:    {', '.join(tags)}")
        print(f"  hash:    {meta['inlet_content_hash'][:16]}…")
        print(f"\n  Next: `myco evaluate {note_id}` to begin digestion.")
    return 0
