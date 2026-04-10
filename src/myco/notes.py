#!/usr/bin/env python3
"""
Myco Notes — Zettelkasten-flavored atomic note substrate.

This module is the shared engine behind the `eat / digest / view / hunger`
four-command set. It implements the minimum closed digestive loop approved
in docs/current/digestive_architecture_craft_2026-04-10.md.

Design principles (from the 4-round debate):
    1. Flat not tree:  notes/*.md, no sub-folders. Scale via metadata, not
       directory depth. (Zettelkasten / A-Mem / Obsidian Dataview lineage.)
    2. Status lifecycle, not type hierarchy:  a note moves through
       raw → digesting → {extracted | integrated | excreted}.  Non-linear
       jumps are allowed (e.g. raw→integrated directly when already mature).
    3. Metadata first-class:  every note has a machine-readable frontmatter
       block, so Dataview-style queries and L10 lint work without parsing
       prose.
    4. Dogfood-able:  helpers are pure functions so the Myco kernel itself
       can eat its own notes during bootstrap.

Public surface (keep stable — CLI, MCP tools, and L10 lint depend on it):
    VALID_STATUSES, VALID_SOURCES
    generate_id(now=None) -> str
    parse_frontmatter(text) -> (dict, str)
    serialize_note(meta, body) -> str
    ensure_notes_dir(root) -> Path
    write_note(root, body, *, tags=None, source="eat",
               status="raw", title=None, now=None) -> Path
    read_note(path) -> (dict, str)
    update_note(path, **field_updates) -> dict
    list_notes(root, *, status=None) -> list[Path]
    compute_hunger_report(root) -> dict
    validate_frontmatter(meta) -> list[str]   # returns error messages

Storage layout:
    <project_root>/notes/n_YYYYMMDDTHHMMSS_xxxx.md

This file MUST NOT import from myco.cli or myco.mcp_server (one-way
dependency: cli/mcp → notes, never the reverse).
"""

from __future__ import annotations

import os
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover — yaml is a hard dep elsewhere
    yaml = None


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_STATUSES: Tuple[str, ...] = (
    "raw",          # just ingested, not yet processed
    "digesting",    # currently being read/summarized/extracted
    "extracted",    # key claim has been lifted into wiki / MYCO.md
    "integrated",   # fully merged into canonical structures
    "excreted",     # deliberately removed from active rotation
)

VALID_SOURCES: Tuple[str, ...] = (
    "chat",         # pulled from conversation context
    "eat",          # user/agent invoked `myco eat` explicitly
    "promote",      # grown from another note
    "import",       # bulk ingested from external tool
    "bootstrap",    # created during `myco init` / first-run scaffolding
)

REQUIRED_FIELDS: Tuple[str, ...] = (
    "id", "status", "source", "tags", "created", "last_touched",
    "digest_count", "promote_candidate", "excrete_reason",
)

NOTES_DIRNAME = "notes"
NOTE_FILENAME_RE = re.compile(
    r"^n_(?P<ts>\d{8}T\d{6})_(?P<rand>[0-9a-f]{4})\.md$"
)

# ISO 8601-ish (we omit timezone for human-friendliness — Myco is single-user).
_ISO_FMT = "%Y-%m-%dT%H:%M:%S"


# ---------------------------------------------------------------------------
# ID & filename
# ---------------------------------------------------------------------------

def generate_id(now: Optional[datetime] = None) -> str:
    """Generate a note id: n_YYYYMMDDTHHMMSS_<4 hex>.

    The timestamp makes the id sortable and human-scannable; the 4-hex
    suffix avoids collisions when multiple notes are eaten in the same
    second (e.g. bulk import).
    """
    now = now or datetime.now()
    ts = now.strftime("%Y%m%dT%H%M%S")
    rand = secrets.token_hex(2)  # 4 hex chars
    return f"n_{ts}_{rand}"


def id_to_filename(note_id: str) -> str:
    return f"{note_id}.md"


def filename_to_id(filename: str) -> Optional[str]:
    m = NOTE_FILENAME_RE.match(os.path.basename(filename))
    return f"n_{m.group('ts')}_{m.group('rand')}" if m else None


# ---------------------------------------------------------------------------
# Frontmatter parsing / serialization
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(
    r"^---\s*\n(?P<fm>.*?\n)---\s*\n(?P<body>.*)$",
    re.DOTALL,
)


def parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    """Split a note file's text into (metadata dict, body string).

    Returns ({}, text) if no frontmatter block is present, so callers can
    still recover the body for display/debug.
    """
    if yaml is None:
        raise RuntimeError("PyYAML is required for note parsing")
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return ({}, text)
    try:
        meta = yaml.safe_load(m.group("fm")) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Malformed frontmatter: {e}") from e
    if not isinstance(meta, dict):
        raise ValueError("Frontmatter must be a YAML mapping")
    return (meta, m.group("body"))


def serialize_note(meta: Dict[str, Any], body: str) -> str:
    """Render (meta, body) back into a note file string.

    We normalize key order so diffs stay readable.
    """
    if yaml is None:
        raise RuntimeError("PyYAML is required for note serialization")
    ordered = {k: meta.get(k) for k in REQUIRED_FIELDS if k in meta}
    # Preserve any extra keys at the end so the schema can grow without
    # data loss (e.g. `links: [...]` once wiki cross-ref lands).
    for k, v in meta.items():
        if k not in ordered:
            ordered[k] = v
    fm = yaml.safe_dump(
        ordered,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
    if not body.endswith("\n"):
        body = body + "\n"
    return f"---\n{fm}---\n{body}"


# ---------------------------------------------------------------------------
# Filesystem
# ---------------------------------------------------------------------------

def ensure_notes_dir(root: Path) -> Path:
    """Ensure <root>/notes/ exists and return it."""
    notes_dir = Path(root) / NOTES_DIRNAME
    notes_dir.mkdir(parents=True, exist_ok=True)
    return notes_dir


def _now_iso(now: Optional[datetime] = None) -> str:
    return (now or datetime.now()).strftime(_ISO_FMT)


def write_note(
    root: Path,
    body: str,
    *,
    tags: Optional[List[str]] = None,
    source: str = "eat",
    status: str = "raw",
    title: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Path:
    """Create a new note on disk and return its path.

    `title`, if provided, is inserted as an H1 at the top of the body
    (unless the body already starts with one). The note's id is derived
    from `now` so callers can reproduce it in tests.
    """
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status {status!r}; expected one of {VALID_STATUSES}")
    if source not in VALID_SOURCES:
        raise ValueError(f"Invalid source {source!r}; expected one of {VALID_SOURCES}")

    notes_dir = ensure_notes_dir(root)
    now = now or datetime.now()
    nid = generate_id(now)

    # Guarantee unique filename (extremely rare collision).
    while (notes_dir / id_to_filename(nid)).exists():
        nid = generate_id(now)

    body = body.strip("\n")
    if title and not body.lstrip().startswith("#"):
        body = f"# {title}\n\n{body}"

    meta: Dict[str, Any] = {
        "id": nid,
        "status": status,
        "source": source,
        "tags": list(tags or []),
        "created": _now_iso(now),
        "last_touched": _now_iso(now),
        "digest_count": 0,
        "promote_candidate": False,
        "excrete_reason": None,
    }

    path = notes_dir / id_to_filename(nid)
    path.write_text(serialize_note(meta, body + "\n"), encoding="utf-8")
    return path


def read_note(path: Path) -> Tuple[Dict[str, Any], str]:
    text = Path(path).read_text(encoding="utf-8")
    return parse_frontmatter(text)


def update_note(path: Path, **field_updates: Any) -> Dict[str, Any]:
    """Apply partial updates to a note's frontmatter.

    Always refreshes `last_touched`. Pass `digest_count=+1` as a sentinel
    to increment rather than replace.
    """
    path = Path(path)
    meta, body = read_note(path)
    if not meta:
        raise ValueError(f"Cannot update note without frontmatter: {path}")

    # Special sentinel: +1 on digest_count
    inc = field_updates.pop("_increment_digest", False)
    if inc:
        meta["digest_count"] = int(meta.get("digest_count", 0)) + 1

    for k, v in field_updates.items():
        meta[k] = v

    if "status" in field_updates and field_updates["status"] not in VALID_STATUSES:
        raise ValueError(f"Invalid status {field_updates['status']!r}")

    meta["last_touched"] = _now_iso()
    path.write_text(serialize_note(meta, body), encoding="utf-8")
    return meta


def list_notes(root: Path, *, status: Optional[str] = None) -> List[Path]:
    notes_dir = Path(root) / NOTES_DIRNAME
    if not notes_dir.exists():
        return []
    paths = sorted(notes_dir.glob("n_*.md"))
    if status is None:
        return paths
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status filter {status!r}")
    out: List[Path] = []
    for p in paths:
        try:
            meta, _ = read_note(p)
        except Exception:
            continue
        if meta.get("status") == status:
            out.append(p)
    return out


# ---------------------------------------------------------------------------
# Validation (used by L10 lint)
# ---------------------------------------------------------------------------

def validate_frontmatter(meta: Dict[str, Any]) -> List[str]:
    """Return a list of human-readable error messages for a note meta dict.

    Empty list == valid. Used by L10 notes-schema lint.
    """
    errors: List[str] = []
    if not isinstance(meta, dict):
        return ["frontmatter is not a mapping"]

    for field in REQUIRED_FIELDS:
        if field not in meta:
            errors.append(f"missing required field: {field}")

    status = meta.get("status")
    if status is not None and status not in VALID_STATUSES:
        errors.append(
            f"invalid status {status!r}; expected one of {list(VALID_STATUSES)}"
        )

    source = meta.get("source")
    if source is not None and source not in VALID_SOURCES:
        errors.append(
            f"invalid source {source!r}; expected one of {list(VALID_SOURCES)}"
        )

    tags = meta.get("tags")
    if tags is not None and not isinstance(tags, list):
        errors.append("tags must be a list")

    dc = meta.get("digest_count")
    if dc is not None and not isinstance(dc, int):
        errors.append("digest_count must be an integer")

    pc = meta.get("promote_candidate")
    if pc is not None and not isinstance(pc, bool):
        errors.append("promote_candidate must be a boolean")

    nid = meta.get("id")
    if nid is not None and not re.match(r"^n_\d{8}T\d{6}_[0-9a-f]{4}$", str(nid)):
        errors.append(
            f"id {nid!r} does not match n_YYYYMMDDTHHMMSS_xxxx pattern"
        )

    # Status-conditioned checks
    if status == "excreted" and not meta.get("excrete_reason"):
        errors.append("excreted notes must have a non-empty excrete_reason")

    return errors


# ---------------------------------------------------------------------------
# Hunger report  —  the metabolic dashboard
# ---------------------------------------------------------------------------

@dataclass
class HungerReport:
    """A structured view of the notes/ directory's metabolic state.

    Maps directly to the Phase ① acceptance metrics in
    docs/current/digestive_architecture_craft_2026-04-10.md §3.3.
    """
    total: int
    by_status: Dict[str, int]
    raw_count: int
    stale_raw: List[Dict[str, Any]]         # raw notes not touched in ≥7d
    deep_digested: List[Dict[str, Any]]     # digest_count ≥ 2
    excreted_with_reason: int
    promote_candidates: List[Dict[str, Any]]
    signals: List[str]                      # human-readable hunger signals

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "by_status": self.by_status,
            "raw_count": self.raw_count,
            "stale_raw": self.stale_raw,
            "deep_digested": self.deep_digested,
            "excreted_with_reason": self.excreted_with_reason,
            "promote_candidates": self.promote_candidates,
            "signals": self.signals,
        }


def compute_hunger_report(
    root: Path,
    *,
    stale_days: int = 7,
    now: Optional[datetime] = None,
) -> HungerReport:
    """Scan notes/ and return a HungerReport.

    Signals (ordered by urgency):
        - "raw_backlog": >10 raw notes (digestive tract is constipated)
        - "stale_raw":   ≥1 raw note untouched for `stale_days`+ days
        - "no_deep_digest": no note has digest_count ≥ 2 (Gear 3 starved)
        - "no_excretion": zero excreted notes (compression doctrine ignored)
        - "healthy":     none of the above triggered
    """
    now = now or datetime.now()
    stale_cutoff = now - timedelta(days=stale_days)

    paths = list_notes(root)
    by_status: Dict[str, int] = {s: 0 for s in VALID_STATUSES}
    stale_raw: List[Dict[str, Any]] = []
    deep_digested: List[Dict[str, Any]] = []
    promote_candidates: List[Dict[str, Any]] = []
    excreted_with_reason = 0

    for p in paths:
        try:
            meta, _ = read_note(p)
        except Exception:
            continue

        status = meta.get("status", "raw")
        by_status[status] = by_status.get(status, 0) + 1

        rel = str(p.name)
        last_touched = meta.get("last_touched")
        try:
            lt = datetime.strptime(str(last_touched), _ISO_FMT)
        except Exception:
            lt = None

        if status == "raw" and lt and lt < stale_cutoff:
            stale_raw.append({
                "id": meta.get("id"),
                "file": rel,
                "last_touched": last_touched,
                "tags": meta.get("tags", []),
            })

        dc = int(meta.get("digest_count") or 0)
        if dc >= 2:
            deep_digested.append({
                "id": meta.get("id"),
                "file": rel,
                "digest_count": dc,
                "status": status,
            })

        if meta.get("promote_candidate"):
            promote_candidates.append({
                "id": meta.get("id"),
                "file": rel,
                "tags": meta.get("tags", []),
            })

        if status == "excreted" and meta.get("excrete_reason"):
            excreted_with_reason += 1

    raw_count = by_status.get("raw", 0)

    signals: List[str] = []
    if raw_count > 10:
        signals.append(
            f"raw_backlog: {raw_count} raw notes (>10) — digestive tract "
            f"is constipated. Run `myco digest` or trigger Gear 3."
        )
    if stale_raw:
        signals.append(
            f"stale_raw: {len(stale_raw)} raw note(s) untouched for ≥{stale_days} days."
        )
    if not deep_digested and by_status.get("extracted", 0) + by_status.get("integrated", 0) == 0:
        signals.append(
            "no_deep_digest: no note has been digested twice AND no note has "
            "reached extracted/integrated — Gear 3 may be starving."
        )
    if by_status.get("excreted", 0) == 0 and len(paths) >= 20:
        signals.append(
            "no_excretion: zero notes excreted despite ≥20 total notes. "
            "Compression doctrine ('attention finite') is being ignored."
        )
    if promote_candidates:
        signals.append(
            f"promote_ready: {len(promote_candidates)} note(s) flagged "
            f"promote_candidate=true — ready to lift into wiki/."
        )
    if not signals:
        signals.append("healthy: notes/ is metabolizing normally.")

    return HungerReport(
        total=len(paths),
        by_status=by_status,
        raw_count=raw_count,
        stale_raw=stale_raw,
        deep_digested=deep_digested,
        excreted_with_reason=excreted_with_reason,
        promote_candidates=promote_candidates,
        signals=signals,
    )
