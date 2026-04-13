#!/usr/bin/env python3
"""
Myco Notes — Zettelkasten-flavored atomic note substrate.

This module is the shared engine behind the `eat / digest / view / hunger`
four-command set. It implements the minimum closed digestive loop approved
in docs/primordia/digestive_architecture_craft_2026-04-10.md.

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
# --- Mycelium references ---
# Contract:      docs/agent_protocol.md §2.2 (eat/digest/view/hunger triggers)
# Canon SSoT:    _canon.yaml::system.notes_schema, system.hunger
# Architecture:  docs/architecture.md §Digestive loop
# Open problems: docs/open_problems.md §3 (compression quality), §5 (structural decay)

from __future__ import annotations

import json
import os
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover — yaml is a hard dep elsewhere
    yaml = None


# ---------------------------------------------------------------------------
# Exceptions (Wave 20, contract v0.19.0)
# ---------------------------------------------------------------------------

# Wave A1: MycoProjectNotFound moved to project.py; re-exported here for compat.
from myco.project import MycoProjectNotFound  # noqa: F401 — public re-export




def _parse_version_tuple(s: Optional[str]) -> Optional[Tuple[int, int, int]]:
    """Parse semver-ish `vMAJOR.MINOR[.PATCH]` → (major, minor, patch).

    Accepts: ``v0.8.0``, ``v0.8``, ``0.8.0``, ``0.19.0``.
    Returns None on malformed input. PATCH defaults to 0 when omitted.

    Wave 20 (v0.19.0): used by `detect_contract_drift` grandfather
    ceiling check. See craft §B1.
    """
    if s is None:
        return None
    raw = str(s).strip().lstrip("v").lstrip("V")
    if not raw:
        return None
    parts = raw.split(".")
    if not (2 <= len(parts) <= 3):
        return None
    try:
        major = int(parts[0])
        minor = int(parts[1])
        patch = int(parts[2]) if len(parts) == 3 else 0
    except (ValueError, TypeError):
        return None
    return (major, minor, patch)


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
    "chat",               # pulled from conversation context
    "eat",                # user/agent invoked `myco eat` explicitly
    "promote",            # grown from another note
    "import",             # bulk ingested from external tool
    "bootstrap",          # created during `myco init` / first-run scaffolding
    "forage",             # v0.7.0 — digested extract from a forage/ item
    "compress",           # v0.26.0 (Wave 30) — extracted note produced by
                          # `myco compress` from N raw/digesting inputs.
                          # Carries `compressed_from` audit trail.
                          # Debate: docs/primordia/compression_primitive_craft_2026-04-12.md
    "inlet",              # v0.27.0 (Wave 35) — raw note produced by
                          # `myco inlet` from external content (file or
                          # agent-fetched URL). Carries `inlet_*` provenance
                          # fields. Wave 34 design, Wave 35 implementation.
                          # Authoritative design: docs/primordia/metabolic_inlet_design_craft_2026-04-12.md
)

REQUIRED_FIELDS: Tuple[str, ...] = (
    "id", "status", "source", "tags", "created", "last_touched",
    "digest_count", "promote_candidate", "excrete_reason",
)

# v0.4.0: optional frontmatter fields for Self-Model D layer (dead knowledge
# detection). Not enforced by L10; grandfathered for existing notes.
# Authoritative design: docs/primordia/dead_knowledge_seed_craft_2026-04-11.md.
# Wave 30 (v0.26.0) extends with forward-compression audit trail fields.
# Authoritative design: docs/primordia/compression_primitive_craft_2026-04-12.md
OPTIONAL_FIELDS: Tuple[str, ...] = (
    "view_count",              # int, default 0
    "last_viewed_at",          # ISO str or None
    # Wave 30 — forward compression audit trail
    "compressed_from",         # list[str] — input note ids on output extracted
    "compressed_into",         # str — output note id on excreted input
    "compression_method",      # str — "manual" | "hunger-signal"
    "compression_rationale",   # str — required prose
    "compression_confidence",  # float — 0.0–1.0, self-reported
    "pre_compression_status",  # str — input's prior status (for future uncompress)
    # Wave 35 — Metabolic Inlet provenance scaffold (v0.27.0).
    # Soft-enforced by L10 for source=inlet only (warn, not error).
    "inlet_origin",            # str — URL or absolute file path of external source
    "inlet_method",            # str — "file" | "url-fetched-by-agent" | "explicit-content"
    "inlet_fetched_at",        # str — ISO-8601 timestamp content was captured
    "inlet_content_hash",      # str — sha256 hex digest of body bytes (tamper detection)
    # Wave 61 — Mycelium Wrapping: backward link from note → forage item.
    # Set when a note is produced from forage-derived content.
    # Authoritative design: mycelium wrapping (forage structural connectivity).
    "forage_source",           # str — forage item id (e.g. f_20260413T..._xxxx)
)

# Default dead-knowledge threshold (canon can override via
# system.notes_schema.dead_knowledge_threshold_days).
DEFAULT_DEAD_THRESHOLD_DAYS = 30

# Statuses considered "settled" — only these are eligible for dead detection.
DEFAULT_TERMINAL_STATUSES: Tuple[str, ...] = ("extracted", "integrated")

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
    # v0.4.0: place optional D-layer fields immediately after required
    # fields so diffs stay readable. Any other extra keys fall through.
    for k in OPTIONAL_FIELDS:
        if k in meta:
            ordered[k] = meta[k]
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


# ---------------------------------------------------------------------------
# Organ 5: Shared frontmatter validation for ALL write operations
# ---------------------------------------------------------------------------

_REQUIRED_FIELDS = {"id", "status", "source", "tags", "created", "last_touched",
                    "digest_count", "promote_candidate", "excrete_reason"}


def _validate_frontmatter_inline(meta: Dict[str, Any], context: str = "write") -> None:
    """Validate frontmatter before any write operation.

    Organ 5: inline immune system — catches invalid data at the write
    boundary, not at lint time. Called from write_note, update_note,
    and record_view.
    """
    missing = _REQUIRED_FIELDS - set(meta.keys())
    if missing:
        raise ValueError(
            f"{context}: missing required frontmatter fields: {missing}")
    if meta.get("status") not in VALID_STATUSES:
        raise ValueError(
            f"{context}: invalid status '{meta.get('status')}'. "
            f"Valid: {VALID_STATUSES}")


def _auto_link_note(
    root: Path,
    new_note_path: Path,
    new_tags: Optional[List[str]],
    new_title: Optional[str],
) -> None:
    """Automatically find related notes and add cross-references.

    This is the mycelium wrapping behavior -- new knowledge nodes
    automatically connect to the existing network via shared tags.

    Design constraints:
    - Best-effort: exceptions are caught by the caller.
    - Only links notes with overlapping tags (semantic relevance).
    - Limits to top 5 related notes (don't spam).
    - Bidirectional: new note links to old, old notes link back.
    - Idempotent: won't duplicate existing links.
    """
    if not new_tags:
        return
    notes_dir = root / "notes"
    if not notes_dir.is_dir():
        return

    new_note_id = new_note_path.stem  # e.g. n_20260413T...
    new_tag_set = set(new_tags)
    related: List[Tuple[Path, str, int]] = []

    # Scan existing notes for tag overlap.
    for p in notes_dir.glob("n_*.md"):
        if p == new_note_path:
            continue
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
            # Parse frontmatter to extract tags.
            if not content.startswith("---"):
                continue
            end_idx = content.index("---", 3)
            fm = yaml.safe_load(content[3:end_idx])
            if not isinstance(fm, dict):
                continue
            other_tags = fm.get("tags", [])
            if isinstance(other_tags, str):
                other_tags = [t.strip() for t in other_tags.split(",")]
            overlap = len(new_tag_set & set(other_tags or []))
            if overlap > 0:
                other_title = fm.get("title") or fm.get("id") or p.stem
                related.append((p, other_title, overlap))
        except Exception:
            continue

    if not related:
        return

    # Sort by overlap descending (most related first), cap at 5.
    related.sort(key=lambda x: -x[2])
    related = related[:5]

    # Append ## Related section to the new note.
    lines = ["\n\n## Related\n"]
    for p, title, overlap in related:
        lines.append(f"- [{title}]({p.name}) ({overlap} shared tags)\n")

    with open(new_note_path, "a", encoding="utf-8") as f:
        f.writelines(lines)

    # Add backlinks in related notes (bidirectional).
    link_label = new_title or new_note_id
    for p, _, _ in related:
        try:
            content = p.read_text(encoding="utf-8")
            if new_note_id in content:
                continue  # Already linked, skip.
            if "## Related" in content:
                # Append to the existing Related section.
                content = content.rstrip() + f"\n- [{link_label}]({new_note_path.name})\n"
            else:
                # Add a new Related section at the end.
                content = content.rstrip() + f"\n\n## Related\n- [{link_label}]({new_note_path.name})\n"
            p.write_text(content, encoding="utf-8")
        except Exception:
            continue  # Best-effort per note.


def write_note(
    root: Path,
    body: str,
    *,
    tags: Optional[List[str]] = None,
    source: str = "eat",
    status: str = "raw",
    title: Optional[str] = None,
    now: Optional[datetime] = None,
    forage_source: Optional[str] = None,
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

    # Wave 61: mycelium wrapping — backward link from note → forage item.
    if forage_source is not None:
        meta["forage_source"] = forage_source

    path = notes_dir / id_to_filename(nid)

    # Organ 5: Inline immune on ALL write operations.
    _validate_frontmatter_inline(meta, context="write_note")

    # Wave 59: atomic write prevents empty files on failure (dogfood friction).
    from myco.io_utils import atomic_write_text
    atomic_write_text(path, serialize_note(meta, body + "\n"))

    # Mycelium wrapping: auto-link to related notes by shared tags.
    # Best-effort — failures here must never prevent note creation.
    try:
        _auto_link_note(root, path, tags, title)
    except Exception:
        pass  # silent — linking is advisory, not critical

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

    # Organ 1: capture old status for transition_log before mutation
    old_status = meta.get("status", "raw")
    transition_reason = field_updates.pop("_transition_reason", None)

    for k, v in field_updates.items():
        meta[k] = v

    # Organ 1: append to transition_log if status changed
    new_status = meta.get("status", old_status)
    if old_status != new_status:
        tlog = meta.get("transition_log") or []
        tlog.append({
            "from": old_status,
            "to": new_status,
            "timestamp": _now_iso(),
            "reason": transition_reason or f"{old_status} → {new_status}",
        })
        meta["transition_log"] = tlog

    # Track lifetime excretions (survives note deletion on disk)
    if new_status == "excreted" and old_status != "excreted":
        try:
            project_root = path.parent.parent  # notes/ -> project root
            increment_excretion_counter(project_root)
        except Exception:
            pass  # best-effort — never block the status transition

    # Organ 5: inline immune on update
    _validate_frontmatter_inline(meta, context="update_note")

    meta["last_touched"] = _now_iso()
    from myco.io_utils import atomic_write_text
    atomic_write_text(path, serialize_note(meta, body))
    return meta


def record_view(path: Path, *, now: Optional[datetime] = None) -> Dict[str, Any]:
    """v0.4.0 — Self-Model D layer seed.

    Record an attended view event on a note: increment ``view_count`` and set
    ``last_viewed_at``. Crucially this does **not** bump ``last_touched`` —
    ``last_touched`` is reserved for mutations (digest, status change, edit).
    Separating read-time from write-time is what lets the dead-knowledge
    detector distinguish "never read" from "never modified".

    Only call this from the ``myco view <id>`` **single-note** path, after the
    body has actually been rendered to the user. List/index mode must never
    call this — see craft §R2.3.

    See docs/primordia/dead_knowledge_seed_craft_2026-04-11.md.
    """
    path = Path(path)
    meta, body = read_note(path)
    if not meta:
        # No frontmatter: legacy file, don't record view (would add nothing
        # parseable, and the grandfather rule should protect it).
        return meta

    now = now or datetime.now()
    vc = int(meta.get("view_count") or 0)
    meta["view_count"] = vc + 1
    meta["last_viewed_at"] = _now_iso(now)
    # Intentional: leave last_touched alone — read is not a mutation.
    # Organ 5: inline immune on record_view
    _validate_frontmatter_inline(meta, context="record_view")
    from myco.io_utils import atomic_write_text
    atomic_write_text(path, serialize_note(meta, body))
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
# Wave 33 — D-layer auto-excretion (prune)
# ---------------------------------------------------------------------------

def find_dead_knowledge_notes(
    root: Path,
    *,
    threshold_days: Optional[int] = None,
    now: Optional[datetime] = None,
) -> List[Tuple[Path, Dict[str, Any], Dict[str, Any]]]:
    """Wave 33: scan notes/ for dead-knowledge candidates.

    Returns a list of (path, meta, criteria_dict) tuples for each note that
    satisfies all five dead-knowledge conditions documented in
    `compute_hunger_report`. The criteria_dict contains the actual measured
    values (created_age_days, last_touched_age_days, etc.) so callers can
    surface them in audit reasons.

    This is the read-only scanner half of `myco prune`. The mutation half
    is `auto_excrete_dead_knowledge` below. Splitting them lets the dry-run
    path call this without any write capability at all.
    """
    now = now or datetime.now()

    if threshold_days is None:
        threshold_days, terminal_statuses = _load_dead_config(root)
    else:
        _, terminal_statuses = _load_dead_config(root)

    cutoff = now - timedelta(days=threshold_days)

    def _parse_iso(v: Any) -> Optional[datetime]:
        if not v:
            return None
        try:
            return datetime.strptime(str(v), _ISO_FMT)
        except Exception:
            return None

    candidates: List[Tuple[Path, Dict[str, Any], Dict[str, Any]]] = []
    for p in list_notes(root):
        try:
            meta, _ = read_note(p)
        except Exception:
            continue

        status = meta.get("status", "raw")
        if status not in terminal_statuses:
            continue

        created = _parse_iso(meta.get("created"))
        lt = _parse_iso(meta.get("last_touched"))
        last_viewed = _parse_iso(meta.get("last_viewed_at"))
        view_count = int(meta.get("view_count") or 0)

        # All five conditions must hold (mirror compute_hunger_report logic).
        if created is None or created >= cutoff:
            continue
        if lt is None or lt >= cutoff:
            continue
        if last_viewed is not None and last_viewed >= cutoff:
            continue
        if view_count >= 2:
            continue

        criteria = {
            "threshold_days": threshold_days,
            "created_age_days": (now - created).days,
            "last_touched_age_days": (now - lt).days,
            "last_viewed_age_days": (
                (now - last_viewed).days if last_viewed else None
            ),
            "view_count": view_count,
            "status": status,
        }
        candidates.append((p, meta, criteria))
    return candidates


def auto_excrete_dead_knowledge(
    root: Path,
    *,
    threshold_days: Optional[int] = None,
    dry_run: bool = True,
    now: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Wave 33: auto-excrete dead-knowledge notes with audit trail.

    For each note returned by `find_dead_knowledge_notes`, build an
    excrete_reason capturing the criteria that triggered the prune,
    then call `update_note` to set status='excreted' (unless dry_run).

    Returns a list of result dicts (one per note), each containing:
        - id, file, prior_status, excrete_reason, criteria, applied (bool)

    The excrete_reason format is mechanical and parseable so a future
    `myco unprune` (Wave 34+) could reverse it. Sample reason:
        "auto-prune: cold terminal note (created 35d ago, last_touched 35d ago, never_viewed, view_count=0, threshold=30d)"

    Wave 31 lessons applied: this function is two-phase only in spirit
    (read all candidates first, then mutate one-by-one) — there is no
    cross-note invariant that requires atomicity. Each excretion is
    independent. Per-note failures are recorded in the result list with
    `applied: False` and an `error` field; they do not abort the loop.
    """
    candidates = find_dead_knowledge_notes(
        root, threshold_days=threshold_days, now=now,
    )

    results: List[Dict[str, Any]] = []
    for path, meta, criteria in candidates:
        last_viewed_descr = (
            "never_viewed"
            if criteria["last_viewed_age_days"] is None
            else f"last_viewed {criteria['last_viewed_age_days']}d ago"
        )
        reason = (
            f"auto-prune: cold terminal note "
            f"(created {criteria['created_age_days']}d ago, "
            f"last_touched {criteria['last_touched_age_days']}d ago, "
            f"{last_viewed_descr}, "
            f"view_count={criteria['view_count']}, "
            f"threshold={criteria['threshold_days']}d)"
        )
        result = {
            "id": meta.get("id"),
            "file": path.name,
            "prior_status": criteria["status"],
            "excrete_reason": reason,
            "criteria": criteria,
            "applied": False,
        }
        if not dry_run:
            try:
                update_note(
                    path,
                    status="excreted",
                    excrete_reason=reason,
                )
                result["applied"] = True
            except Exception as exc:
                result["error"] = str(exc)
        results.append(result)
    return results


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
# Excretion counter  —  persistent lifetime tracking
# ---------------------------------------------------------------------------

_EXCRETION_COUNTER_REL = ".myco_state/excretion_counter.json"


def _excretion_counter_path(root: Path) -> Path:
    return Path(root) / _EXCRETION_COUNTER_REL


def read_excretion_counter(root: Path) -> Dict[str, Any]:
    """Read the lifetime excretion counter from .myco_state/.

    Returns {"lifetime_excretions": int, "last_excretion": str|None}.
    If the file does not exist, returns zeros (no excretions recorded).
    """
    p = _excretion_counter_path(root)
    if not p.exists():
        return {"lifetime_excretions": 0, "last_excretion": None}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return {
            "lifetime_excretions": int(data.get("lifetime_excretions", 0)),
            "last_excretion": data.get("last_excretion"),
        }
    except Exception:
        return {"lifetime_excretions": 0, "last_excretion": None}


def increment_excretion_counter(root: Path, count: int = 1) -> Dict[str, Any]:
    """Increment the lifetime excretion counter and persist it.

    Called whenever one or more notes transition to excreted status.
    The counter survives note deletion — that is its whole purpose.
    """
    state = read_excretion_counter(root)
    state["lifetime_excretions"] += count
    state["last_excretion"] = _now_iso()
    p = _excretion_counter_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    from myco.io_utils import atomic_write_text
    atomic_write_text(p, json.dumps(state, indent=2) + "\n")
    return state


# ---------------------------------------------------------------------------
# Hunger report  —  the metabolic dashboard
# ---------------------------------------------------------------------------

@dataclass
class HungerReport:
    """A structured view of the notes/ directory's metabolic state.

    Maps directly to the Phase ① acceptance metrics in
    docs/primordia/digestive_architecture_craft_2026-04-10.md §3.3.
    """
    total: int
    by_status: Dict[str, int]
    raw_count: int
    stale_raw: List[Dict[str, Any]]         # raw notes not touched in ≥7d
    deep_digested: List[Dict[str, Any]]     # digest_count ≥ 2
    excreted_with_reason: int
    promote_candidates: List[Dict[str, Any]]
    # v0.4.0 — Self-Model D layer seed
    dead_notes: List[Dict[str, Any]]        # terminal + cold + unviewed
    dead_threshold_days: int
    signals: List[str]                      # human-readable hunger signals
    # Wave 46 (v0.35.0): structured action recommendations — closes the
    # advisory-to-execution gap. Each action is a dict with verb, args,
    # and reason. Agents read actions and execute without human prompting.
    actions: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "by_status": self.by_status,
            "raw_count": self.raw_count,
            "stale_raw": self.stale_raw,
            "deep_digested": self.deep_digested,
            "excreted_with_reason": self.excreted_with_reason,
            "promote_candidates": self.promote_candidates,
            "dead_notes": self.dead_notes,
            "dead_threshold_days": self.dead_threshold_days,
            "signals": self.signals,
            "actions": self.actions,
        }


def _load_dead_config(root: Path) -> Tuple[int, Tuple[str, ...]]:
    """Read dead-knowledge config from _canon.yaml with safe fallback.

    Returns (dead_threshold_days, terminal_statuses).
    """
    if yaml is None:
        return DEFAULT_DEAD_THRESHOLD_DAYS, DEFAULT_TERMINAL_STATUSES
    canon_path = Path(root) / "_canon.yaml"
    if not canon_path.exists():
        return DEFAULT_DEAD_THRESHOLD_DAYS, DEFAULT_TERMINAL_STATUSES
    try:
        canon = yaml.safe_load(canon_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return DEFAULT_DEAD_THRESHOLD_DAYS, DEFAULT_TERMINAL_STATUSES
    ns = (canon.get("system") or {}).get("notes_schema") or {}
    days = int(ns.get("dead_knowledge_threshold_days", DEFAULT_DEAD_THRESHOLD_DAYS))
    terminals = tuple(ns.get("terminal_statuses") or DEFAULT_TERMINAL_STATUSES)
    return days, terminals


# Structural compression config (contract v0.5.0).
# Authoritative spec: docs/biomimetic_map.md §4.
# Thresholds are fixed seeds — adaptive thresholds are future work per
# docs/open_problems.md §4. Read/write separation holds: this helper is
# read-only w.r.t. the substrate, mutates nothing.
DEFAULT_STRUCTURAL_LIMITS = {
    "docs_top_level_soft_limit": 20,
    # Wave 36 re-baseline (v0.28.0): 40 → 60. Per Wave 22 §B7 R2.4 explicit
    # exit. See docs/primordia/primordia_soft_limit_rebaseline_craft_2026-04-12.md.
    "primordia_soft_limit": 60,
    "exclude_paths": [],
}


def _load_structural_limits(root: Path) -> Dict[str, Any]:
    """Read structural_limits from _canon.yaml with safe fallback.

    Returns a dict with docs_top_level_soft_limit, primordia_soft_limit,
    exclude_paths. Instances that lack the block (pre-v0.5.0) get defaults.
    """
    if yaml is None:
        return dict(DEFAULT_STRUCTURAL_LIMITS)
    canon_path = Path(root) / "_canon.yaml"
    if not canon_path.exists():
        return dict(DEFAULT_STRUCTURAL_LIMITS)
    try:
        canon = yaml.safe_load(canon_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return dict(DEFAULT_STRUCTURAL_LIMITS)
    sl = (canon.get("system") or {}).get("structural_limits") or {}
    return {
        "docs_top_level_soft_limit": int(
            sl.get("docs_top_level_soft_limit",
                   DEFAULT_STRUCTURAL_LIMITS["docs_top_level_soft_limit"])
        ),
        "primordia_soft_limit": int(
            sl.get("primordia_soft_limit",
                   DEFAULT_STRUCTURAL_LIMITS["primordia_soft_limit"])
        ),
        "exclude_paths": list(sl.get("exclude_paths") or []),
    }


def detect_structural_bloat(root: Path) -> Optional[str]:
    """Return a `structural_bloat` signal string if the substrate is
    structurally over-budget, else None.

    Read-only scan of docs/*.md and docs/primordia/*.md. Excludes
    contract-level docs listed in `structural_limits.exclude_paths`
    from the docs/ top-level count — those are load-bearing rhizomorphs,
    not bloat.

    Seeded thresholds are fixed (not adaptive). Adaptive thresholds are
    registered as future work in docs/open_problems.md §4.
    """
    limits = _load_structural_limits(root)
    excl = set(limits["exclude_paths"])
    docs_dir = Path(root) / "docs"
    if not docs_dir.exists():
        return None

    # Count top-level docs/*.md excluding contract-level
    top_level = [
        p for p in docs_dir.glob("*.md")
        if f"docs/{p.name}" not in excl
    ]
    primordia_dir = docs_dir / "primordia"
    primordia = list(primordia_dir.glob("*.md")) if primordia_dir.exists() else []

    top_over = len(top_level) - limits["docs_top_level_soft_limit"]
    prim_over = len(primordia) - limits["primordia_soft_limit"]

    if top_over <= 0 and prim_over <= 0:
        return None

    parts = []
    if top_over > 0:
        parts.append(
            f"docs/*.md working-set has {len(top_level)} files "
            f"(soft limit {limits['docs_top_level_soft_limit']}, over by {top_over})"
        )
    if prim_over > 0:
        parts.append(
            f"docs/primordia/*.md has {len(primordia)} files "
            f"(soft limit {limits['primordia_soft_limit']}, over by {prim_over})"
        )
    return (
        "structural_bloat: " + "; ".join(parts) +
        ". Consider compression: COMPILE primordia → wiki, merge overlapping "
        "docs, or archive SUPERSEDED crafts. See docs/biomimetic_map.md §4."
    )


def detect_craft_reflex_missing(
    root: Path,
    *,
    now: Optional[datetime] = None,
) -> Optional[str]:
    """Return a `craft_reflex_missing` signal string if any craft trigger
    surface was recently touched without matching craft evidence, else None.

    Mirrors the L15 Craft Reflex lint dimension so the signal surfaces in
    `myco hunger` at every session boot — not only when lint is run.
    Respects `_canon.yaml::system.craft_protocol.reflex.enabled`; if the
    feature is disabled or the canon block is absent, returns None.

    Detection strategy (shared with L15, Round 3 mtime-primary):
        1. Scan each path listed under reflex.trigger_surfaces.* for
           recent mtime within `lookback_days`.
        2. If any file was touched, require evidence in log.md via
           `evidence_pattern` OR at least one recently-mtime'd craft
           file under docs/primordia/.
        3. Otherwise emit the signal naming how many surfaces are
           uncovered across which classes.

    See docs/primordia/craft_reflex_craft_2026-04-11.md §4.
    """
    import re as _re
    try:
        import yaml as _yaml
    except ImportError:
        return None

    canon_path = Path(root) / "_canon.yaml"
    if not canon_path.exists():
        return None
    try:
        canon = _yaml.safe_load(canon_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return None

    schema = (canon.get("system") or {}).get("craft_protocol") or {}
    reflex = schema.get("reflex") or {}
    if not reflex or not reflex.get("enabled", False):
        return None

    lookback_days = int(reflex.get("lookback_days", 3))
    window = lookback_days * 86400
    now_ts = (now or datetime.now()).timestamp()

    surfaces = reflex.get("trigger_surfaces") or {}
    classes: Dict[str, List[str]] = {
        "kernel_contract": list(surfaces.get("kernel_contract") or []),
        "public_claim": list(surfaces.get("public_claim") or []),
    }

    recent_by_class: Dict[str, List[str]] = {}
    for cls_name, rels in classes.items():
        for rel in rels:
            p = Path(root) / rel
            if not p.exists():
                continue
            try:
                mt = p.stat().st_mtime
            except OSError:
                continue
            if now_ts - mt < window:
                recent_by_class.setdefault(cls_name, []).append(rel)

    if not recent_by_class:
        return None

    # Check for evidence in log.md or a recently-written craft file.
    evidence_pattern = reflex.get(
        "evidence_pattern",
        r"(docs/primordia/[a-z0-9_]+_craft_\d{4}-\d{2}-\d{2}(_[0-9a-f]{4})?\.md|craft_reference\s*:)",
    )
    try:
        evidence_re = _re.compile(evidence_pattern)
    except _re.error:
        return None

    evidence_present = False
    log_path = Path(root) / "log.md"
    if log_path.exists():
        try:
            if evidence_re.search(log_path.read_text(encoding="utf-8", errors="replace")):
                evidence_present = True
        except OSError:
            pass

    if not evidence_present:
        primordia = Path(root) / schema.get("dir", "docs/primordia")
        if primordia.exists():
            for cp in primordia.glob("*_craft_*.md"):
                try:
                    if now_ts - cp.stat().st_mtime < window:
                        evidence_present = True
                        break
                except OSError:
                    continue

    if evidence_present:
        return None

    parts = []
    for cls_name, files in recent_by_class.items():
        parts.append(f"{cls_name}: {len(files)} file(s) ({', '.join(files[:3])}"
                     + ("…" if len(files) > 3 else "") + ")")

    return (
        "[REFLEX HIGH] craft_reflex_missing: trigger surfaces touched in last "
        f"{lookback_days}d without matching craft evidence — "
        + "; ".join(parts) +
        ". IMMUTABLE REFLEX (W3, contract v0.12.0): write the missing "
        "craft at docs/primordia/<topic>_craft_YYYY-MM-DD.md in this "
        "session before any other kernel-class action. Bypassing via "
        "`--no-verify` is a W3 violation. See docs/craft_protocol.md §3.1."
    )


def detect_contract_drift(
    root: Path,
    *,
    package_template: Optional[Path] = None,
) -> Optional[str]:
    """Return a `contract_drift` signal if the local
    `synced_contract_version` differs from the kernel's `contract_version`.

    Detection order (per boot_reflex_arc_craft_2026-04-11 Round 3 C2):
        1. Read `_canon.yaml::system.synced_contract_version` (instance side).
        2. Read the kernel's `contract_version`. Preference order:
           a) local repo's own `_canon.yaml::system.contract_version`
              (self-reference: kernel running on itself).
           b) the shipped template at
              `src/myco/templates/_canon.yaml` — this is the ledger
              instances are pinned against.
        3. If both exist and differ → emit HIGH signal.
        4. If either is unreadable → silent LOW (return a LOW signal
           string instead of None so the agent at least notices).

    See docs/primordia/boot_reflex_arc_craft_2026-04-11.md D1.
    Respects `_canon.yaml::system.boot_reflex.enabled`; disabled = None.
    """
    try:
        import yaml as _yaml
    except ImportError:
        return None

    canon_path = Path(root) / "_canon.yaml"
    if not canon_path.exists():
        return None
    try:
        canon = _yaml.safe_load(canon_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return None

    system = canon.get("system") or {}
    boot_cfg = system.get("boot_reflex") or {}

    # Wave 20 (v0.19.0): prefix is resolved even for grandfather-ceiling
    # signals, because the ceiling check MUST run before the enabled gate
    # — instances with no boot_reflex block at all (pre-Wave-13 canons)
    # must still be able to fire `grandfather_expired`. See
    # docs/primordia/silent_fail_elimination_craft_2026-04-11.md §B1.
    prefix = boot_cfg.get("reflex_prefix", "[REFLEX HIGH]")

    synced = system.get("synced_contract_version")
    # Preference (a): same file's kernel contract_version (kernel self-check)
    kernel_version = system.get("contract_version")

    # Preference (b): shipped template in the local repo (kernel-mode)
    if kernel_version is None or synced is None:
        tpl = package_template or (Path(root) / "src" / "myco" / "templates" / "_canon.yaml")
        if tpl.exists():
            try:
                tpl_canon = _yaml.safe_load(tpl.read_text(encoding="utf-8")) or {}
                tpl_system = tpl_canon.get("system") or {}
                if kernel_version is None:
                    # Template's own contract_version if present, else its
                    # synced_contract_version (which IS the authoritative
                    # pin from the template's perspective).
                    kernel_version = (
                        tpl_system.get("contract_version")
                        or tpl_system.get("synced_contract_version")
                    )
                if synced is None:
                    synced = tpl_system.get("synced_contract_version")
            except Exception:
                pass

    # Preference (c) — Wave 20 (v0.19.0): installed package template.
    # Downstream instances (e.g. ASCC) have no `src/myco/templates/` in
    # their repo layout, so (b) returns empty. Fall back to the template
    # shipped inside the installed `myco` package via importlib.resources.
    # This is how an instance learns the kernel's version when it lives
    # outside the kernel repo.
    if kernel_version is None:
        try:
            from importlib.resources import files as _pkg_files
            pkg_tpl = _pkg_files("myco") / "templates" / "_canon.yaml"
            if pkg_tpl.is_file():
                pkg_canon = _yaml.safe_load(pkg_tpl.read_text(encoding="utf-8")) or {}
                pkg_system = pkg_canon.get("system") or {}
                kernel_version = (
                    pkg_system.get("contract_version")
                    or pkg_system.get("synced_contract_version")
                )
        except Exception:
            pass

    # -----------------------------------------------------------------
    # Wave 20 (v0.19.0): grandfather-ceiling check runs BEFORE the
    # enabled gate. A disabled or missing boot_reflex block must NOT
    # mean "silently pass on 10 minor versions of drift". Ceiling
    # default is 5 minor versions; instances override via
    # `system.boot_reflex.grandfather_ceiling_minor_versions`.
    # -----------------------------------------------------------------
    try:
        ceiling = int(boot_cfg.get("grandfather_ceiling_minor_versions", 5))
    except (ValueError, TypeError):
        ceiling = 5

    if synced is not None and kernel_version is not None:
        synced_tup = _parse_version_tuple(synced)
        kernel_tup = _parse_version_tuple(kernel_version)
        if synced_tup is None or kernel_tup is None:
            return (
                f"[REFLEX MEDIUM] version_parse_error: could not parse "
                f"synced={synced!r} or kernel={kernel_version!r} as "
                f"semver (expected vMAJOR.MINOR[.PATCH]). Fix the "
                f"field(s) in _canon.yaml before any kernel-class action."
            )
        # Major mismatch is NEVER grandfathered.
        if synced_tup[0] != kernel_tup[0]:
            return (
                f"{prefix} grandfather_expired: major version mismatch "
                f"{synced!r} → {kernel_version!r}. Majors are NEVER "
                f"grandfathered. Read docs/contract_changelog.md in "
                f"full and import the kernel contract NOW before any "
                f"kernel-class action."
            )
        minor_gap = kernel_tup[1] - synced_tup[1]
        if minor_gap > ceiling:
            return (
                f"{prefix} grandfather_expired: {minor_gap} minor "
                f"versions of drift ({synced!r} → {kernel_version!r}) "
                f"exceeds ceiling {ceiling}. Grandfather exemption "
                f"lapsed. Read docs/contract_changelog.md entries "
                f"between {synced} and {kernel_version} and update "
                f"_canon.yaml::system.synced_contract_version (plus any "
                f"missing canon blocks per the changelog) before any "
                f"kernel-class action. Override ceiling via "
                f"system.boot_reflex.grandfather_ceiling_minor_versions."
            )

    # Only AFTER the grandfather-ceiling check do we honor the
    # enabled-gate. A disabled boot_reflex means "don't fire the
    # normal drift signal", but the ceiling above already ran.
    if not boot_cfg or not boot_cfg.get("enabled", False):
        return None

    if synced is None or kernel_version is None:
        return (
            f"{prefix} contract_drift: cannot read "
            "synced_contract_version or kernel contract_version from "
            "_canon.yaml / templates. Boot reflex cannot verify version "
            "lock. Restore the field per docs/agent_protocol.md §8.4."
        )

    if str(synced).strip() != str(kernel_version).strip():
        return (
            f"{prefix} contract_drift: synced_contract_version={synced!r} "
            f"!= kernel contract_version={kernel_version!r}. "
            "IMMUTABLE REFLEX (contract "
            "v0.12.0): read docs/contract_changelog.md entries between "
            f"{synced} and {kernel_version}, refresh local reflex rules "
            "and update _canon.yaml::system.synced_contract_version "
            "before any kernel-class action. Bypassing is an §8 "
            "contract-level invariant violation."
        )

    return None


def detect_session_end_drift(
    root: Path,
    *,
    now: Optional[datetime] = None,
) -> Optional[str]:
    """Return a `session_end_drift` advisory signal if session reflection reflection
    or cross-project distillation sweep discipline has drifted in log.md, else None.

    Two sub-checks (both optional via canon; either can be disabled):
        reflection_cfg — count non-meta `## [YYYY-MM-DD] <type>` entries after the
                most recent `## [YYYY-MM-DD] meta |` entry. If the count
                exceeds `drift_threshold_entries`, reflection_cfg fires.
        distillation_cfg — find the oldest `g4-candidate` line whose entry date is
                older than `drift_threshold_days` and has no resolution
                marker (`g4-pass` / `g4-landed` / `g4-resolved`) in the
                same line, and does not reference a craft file that
                exists on disk. If any such line exists, distillation_cfg fires.

    Signal tier: LOW (advisory). Does not use the `[REFLEX HIGH]` prefix —
    see docs/primordia/session_end_reflex_arc_craft_2026-04-11.md §B4 for
    the deliberate asymmetry with boot_reflex.

    Fails open on any IO / parse error (returns None).
    """
    import re as _re
    try:
        import yaml as _yaml
    except ImportError:
        return None

    canon_path = Path(root) / "_canon.yaml"
    if not canon_path.exists():
        return None
    try:
        canon = _yaml.safe_load(canon_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return None

    cfg = ((canon.get("system") or {}).get("session_end_reflex") or {})
    if not cfg or not cfg.get("enabled", False):
        return None

    g2_cfg = cfg.get("reflection_cfg") or {}
    g4_cfg = cfg.get("distillation_cfg") or {}
    scan_cap = int(cfg.get("log_scan_cap_bytes", 5_242_880))

    log_path = Path(root) / "log.md"
    if not log_path.exists():
        return None

    # Bounded read — take last scan_cap bytes to keep this constant-time.
    try:
        size = log_path.stat().st_size
        with log_path.open("rb") as f:
            if size > scan_cap:
                f.seek(size - scan_cap)
            raw = f.read()
        text = raw.decode("utf-8", errors="replace")
    except OSError:
        return None

    lines = text.splitlines()

    # Header regex — tolerant: optional leading space, flexible separator.
    header_re = _re.compile(r"^\s*##\s*\[(\d{4}-\d{2}-\d{2})\]\s+(\w[\w-]*)")
    now_dt = now or datetime.now()

    parts: List[str] = []

    # --- session reflection — reflection drift ---
    if g2_cfg.get("enabled", True):
        marker = str(g2_cfg.get("reflection_marker", "meta")).lower()
        threshold = int(g2_cfg.get("drift_threshold_entries", 15))
        last_meta_idx = -1
        header_positions: List[int] = []
        for i, line in enumerate(lines):
            m = header_re.match(line)
            if not m:
                continue
            header_positions.append(i)
            if m.group(2).lower() == marker:
                last_meta_idx = i
        if last_meta_idx >= 0:
            non_meta_after = sum(
                1 for pos in header_positions if pos > last_meta_idx
            )
        else:
            non_meta_after = len(header_positions)
        if non_meta_after > threshold:
            parts.append(
                f"reflection_cfg ({non_meta_after} log entries since last "
                f"`{marker}` reflection, threshold {threshold})"
            )

    # --- cross-project distillation — sweep drift ---
    if g4_cfg.get("enabled", True):
        marker = str(g4_cfg.get("candidate_marker", "g4-candidate")).lower()
        resolutions = [
            str(s).lower()
            for s in (g4_cfg.get("resolution_markers") or ["g4-pass"])
        ]
        threshold_days = int(g4_cfg.get("drift_threshold_days", 5))
        cutoff = now_dt - timedelta(days=threshold_days)
        craft_ref_re = _re.compile(
            r"docs/primordia/[a-z0-9_]+_craft_\d{4}-\d{2}-\d{2}"
            r"(_[0-9a-f]{4})?\.md"
        )

        # Walk lines; each g4-candidate is attributed to the most recent
        # header date preceding it.
        current_date: Optional[datetime] = None
        oldest_stale_date: Optional[datetime] = None
        stale_count = 0

        for line in lines:
            m = header_re.match(line)
            if m:
                try:
                    current_date = datetime.strptime(m.group(1), "%Y-%m-%d")
                except ValueError:
                    current_date = None
                continue
            if current_date is None:
                continue
            low = line.lower()
            if marker not in low:
                continue
            # resolution markers on the same line → considered resolved
            if any(rm in low for rm in resolutions):
                continue
            # craft reference on the same line → considered resolved if
            # the referenced file actually exists on disk
            craft_m = craft_ref_re.search(line)
            if craft_m:
                craft_path = Path(root) / craft_m.group(0)
                if craft_path.exists():
                    continue
            # stale if date older than cutoff
            if current_date < cutoff:
                stale_count += 1
                if oldest_stale_date is None or current_date < oldest_stale_date:
                    oldest_stale_date = current_date

        if stale_count > 0 and oldest_stale_date is not None:
            age_days = (now_dt - oldest_stale_date).days
            parts.append(
                f"distillation_cfg ({stale_count} unresolved `{marker}` entries "
                f"older than {threshold_days}d, oldest "
                f"{oldest_stale_date.strftime('%Y-%m-%d')} = {age_days}d old)"
            )

    if not parts:
        return None

    return (
        "session_end_drift: " + "; ".join(parts) + ". "
        "W5 evolution discipline advisory: write a one-line `meta` entry "
        "to log.md (session reflection) and/or annotate stale g4-candidate lines with "
        "`g4-pass: <reason>` / `g4-landed: <ref>` / craft file. See "
        "docs/primordia/session_end_reflex_arc_craft_2026-04-11.md."
    )


def detect_compression_ripe(
    root: Path,
    *,
    now: Optional[datetime] = None,
) -> Optional[str]:
    """Return a `compression_ripe` advisory signal if any tag cohort is ripe.

    Wave 30 (v0.26.0) — closes the Wave 27 D2 friction-driven trigger half
    of the forward-compression primitive. The signal fires when:

      • A tag has ≥`ripe_threshold` raw notes AND
      • The oldest raw note carrying that tag is ≥`ripe_age_days` old

    Defaults: threshold=5, age=7 days. Both come from
    `_canon.yaml::system.notes_schema.compression`. Missing canon block →
    feature disabled (returns None) for grandfather compatibility.

    The signal is **non-blocking advisory** (LOW tier — no `[REFLEX HIGH]`
    prefix). Wave 27 D2 explicitly rejected automatic compression because
    the substrate doctrine (anchor #6 mutation-selection) requires the
    agent to choose. The signal sets up the choice; the agent acts via
    `myco compress --tag <X>` or ignores it.

    Format: `compression_ripe: <N> tag cohort(s) ready: <tag1> (X notes,
    oldest Yd), <tag2> ...`

    Authoritative design: docs/primordia/compression_primitive_craft_2026-04-12.md
    Wave 27 §1.2 (Q2 trigger), §3.1 (specification).
    """
    if yaml is None:
        return None
    canon_path = Path(root) / "_canon.yaml"
    if not canon_path.exists():
        return None
    try:
        canon = yaml.safe_load(canon_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return None

    schema = (canon.get("system") or {}).get("notes_schema") or {}
    cfg = schema.get("compression") or {}
    if not cfg:
        return None  # feature off — grandfather

    try:
        threshold = int(cfg.get("ripe_threshold", 5))
        age_days = int(cfg.get("ripe_age_days", 7))
    except (ValueError, TypeError):
        return None

    if threshold <= 0 or age_days <= 0:
        return None  # explicit disable

    now_dt = now or datetime.now()
    age_cutoff = now_dt - timedelta(days=age_days)

    # Walk all raw notes once, building a tag → [(created, id)] map.
    paths = list_notes(root)
    by_tag: Dict[str, List[Tuple[datetime, str]]] = {}

    for p in paths:
        try:
            meta, _ = read_note(p)
        except Exception:
            continue
        if meta.get("status") != "raw":
            continue
        # Skip already-compressed pseudo-raw (defensive — should not happen
        # but if it ever does, we don't want to count cascade-eligible).
        if meta.get("compressed_from"):
            continue
        tags = meta.get("tags") or []
        if not isinstance(tags, list):
            continue
        try:
            created = datetime.strptime(str(meta.get("created", "")), _ISO_FMT)
        except (ValueError, TypeError):
            continue
        for t in tags:
            if not isinstance(t, str):
                continue
            by_tag.setdefault(t, []).append((created, str(meta.get("id", ""))))

    # Identify ripe cohorts.
    ripe: List[Tuple[str, int, int]] = []  # (tag, count, oldest_age_days)
    for tag, items in by_tag.items():
        if len(items) < threshold:
            continue
        oldest = min(items, key=lambda x: x[0])[0]
        if oldest >= age_cutoff:
            continue  # newest cohort still inside age window
        oldest_age = (now_dt - oldest).days
        ripe.append((tag, len(items), oldest_age))

    if not ripe:
        return None

    ripe.sort(key=lambda r: -r[2])  # oldest cohort first
    parts = [
        f"`{t}` ({n} notes, oldest {age}d)"
        for (t, n, age) in ripe[:5]
    ]
    suffix = f"; +{len(ripe) - 5} more" if len(ripe) > 5 else ""
    return (
        f"compression_ripe: {len(ripe)} tag cohort(s) ready for forward "
        f"compression — " + ", ".join(parts) + suffix +
        f". Each cohort has ≥{threshold} raw notes AND oldest is "
        f"≥{age_days}d old (Wave 27 D2 thresholds). Run "
        f"`myco compress --tag <T> --rationale '...'` to synthesize, or "
        f"ignore — this is non-blocking advisory (anchor #6 selection "
        f"loop preserved). See docs/primordia/compression_primitive_craft_2026-04-12.md."
    )


# ---------------------------------------------------------------------------
# Inlet trigger detection (Wave 49, contract v0.38.0)
# ---------------------------------------------------------------------------

def detect_inlet_trigger(root: Path, *, now: Optional[datetime] = None) -> Optional[str]:
    """Detect whether inlet triggers are ripe based on search misses and cohort gaps.

    Fires when EITHER:
    1. Search miss count >= threshold (from .myco_state/search_misses.yaml)
    2. Cohort gap count with total >= gap_threshold (from cohorts.gap_detection)

    Returns a signal string if ripe, or None.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    # Load thresholds from canon
    canon_path = root / "_canon.yaml"
    miss_threshold = 5
    gap_threshold = 3
    miss_state_file = ".myco_state/search_misses.yaml"
    enabled = True
    if canon_path.exists():
        try:
            with open(canon_path, "r", encoding="utf-8") as f:
                canon = yaml.safe_load(f) or {}
            triggers_cfg = canon.get("system", {}).get("inlet_triggers", {})
            if triggers_cfg:
                enabled = triggers_cfg.get("enabled", True)
                miss_threshold = triggers_cfg.get("search_miss_threshold", 5)
                gap_threshold = triggers_cfg.get("gap_threshold", 3)
                miss_state_file = triggers_cfg.get(
                    "miss_state_file", ".myco_state/search_misses.yaml")
        except Exception:
            pass

    if not enabled:
        return None

    parts = []

    # Check 1: search miss count
    miss_path = root / miss_state_file
    miss_count = 0
    if miss_path.exists():
        try:
            with open(miss_path, "r", encoding="utf-8") as f:
                miss_data = yaml.safe_load(f) or {}
            miss_count = miss_data.get("miss_count", 0)
        except Exception:
            pass
    if miss_count >= miss_threshold:
        parts.append(f"{miss_count} search misses (threshold {miss_threshold})")

    # Check 2: cohort gaps
    gap_count = 0
    try:
        from myco.colony import gap_detection
        gaps = gap_detection(root)
        qualifying_gaps = [g for g in gaps if g.get("total", 0) >= gap_threshold]
        gap_count = len(qualifying_gaps)
        if gap_count > 0:
            gap_tags = ", ".join(g["tag"] for g in qualifying_gaps[:3])
            parts.append(f"{gap_count} knowledge gap(s) ≥{gap_threshold} notes: {gap_tags}")
    except Exception:
        pass  # cohorts module not available or gap_detection fails

    if not parts:
        return None

    return (
        f"inlet_ripe: {' + '.join(parts)}. Consider running `myco inlet` to "
        f"acquire external knowledge for these topics."
    )


def record_search_miss(root: Path, query: str) -> None:
    """Record a search miss in .myco_state/search_misses.yaml.

    Called by myco_sense MCP tool when a query returns zero results.
    The miss state file is read by detect_inlet_trigger to fire inlet_ripe.
    """
    canon_path = root / "_canon.yaml"
    miss_state_file = ".myco_state/search_misses.yaml"
    if canon_path.exists():
        try:
            with open(canon_path, "r", encoding="utf-8") as f:
                canon = yaml.safe_load(f) or {}
            miss_state_file = (canon.get("system", {})
                                    .get("inlet_triggers", {})
                                    .get("miss_state_file", miss_state_file))
        except Exception:
            pass

    miss_path = root / miss_state_file
    miss_path.parent.mkdir(parents=True, exist_ok=True)

    data: Dict[str, Any] = {"miss_count": 0, "recent_misses": [], "last_reset": ""}
    if miss_path.exists():
        try:
            with open(miss_path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f) or {}
            data.update(loaded)
        except Exception:
            pass

    data["miss_count"] = data.get("miss_count", 0) + 1
    recent = data.get("recent_misses", [])
    if not isinstance(recent, list):
        recent = []
    recent.append({
        "query": query,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    # Cap at 20 recent misses
    data["recent_misses"] = recent[-20:]

    with open(miss_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


# ---------------------------------------------------------------------------
# Compression pressure metric (Wave 50, contract v0.39.0)
# ---------------------------------------------------------------------------

def compute_compression_pressure(
    root: Path,
) -> Tuple[float, Dict[str, int]]:
    """Compute compression pressure: (raw + digesting) / max(1, extracted + integrated).

    Returns (pressure_float, breakdown_dict).
    A pressure > 2.0 indicates the substrate is accumulating faster than
    it is synthesizing — continuous compression is overdue.
    """
    counts: Dict[str, int] = {}
    for path in list_notes(root):
        try:
            meta, _ = read_note(path)
        except Exception:
            continue
        status = meta.get("status", "raw")
        counts[status] = counts.get(status, 0) + 1

    numerator = counts.get("raw", 0) + counts.get("digesting", 0)
    denominator = max(1, counts.get("extracted", 0) + counts.get("integrated", 0))
    pressure = numerator / denominator

    breakdown = {
        "raw": counts.get("raw", 0),
        "digesting": counts.get("digesting", 0),
        "extracted": counts.get("extracted", 0),
        "integrated": counts.get("integrated", 0),
    }
    return round(pressure, 2), breakdown



def write_boot_brief(
    root: Path,
    report: "HungerReport",
    *,
    now: Optional[datetime] = None,
) -> Optional[Path]:
    """Write `.myco_state/boot_brief.md` — full hunger brief for
    human/agent inspection. Called as a side effect of `myco hunger`.

    Wave 17 (contract v0.16.0). Best-effort: any failure emits `[WARN]`
    to stderr but never raises. Returns the brief path on success,
    None on failure. See docs/primordia/boot_brief_injector_craft_2026-04-11.md.
    """
    import sys as _sys
    try:
        import yaml as _yaml
    except ImportError:
        return None

    canon_path = Path(root) / "_canon.yaml"
    if not canon_path.exists():
        return None
    try:
        canon = _yaml.safe_load(canon_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return None

    cfg = ((canon.get("system") or {}).get("boot_brief") or {})
    if not cfg.get("enabled", True):
        return None

    brief_rel = cfg.get("brief_path", ".myco_state/boot_brief.md")
    brief_path = Path(root) / brief_rel

    now_dt = now or datetime.now(tz=None)
    ts = now_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    lines: List[str] = []
    lines.append("# Myco Boot Brief")
    lines.append("")
    lines.append(f"> Auto-generated by `myco hunger`. Last run: **{ts}**")
    lines.append(">")
    lines.append("> This file is a passive signal surface for the next")
    lines.append("> session-boot agent. Freshness > 24h means the brief")
    lines.append("> may be stale — re-run `myco hunger` to refresh.")
    lines.append("")
    lines.append("## Current signals")
    lines.append("")
    for sig in report.signals:
        short = sig.splitlines()[0] if "\n" in sig else sig
        lines.append(f"- {short}")
    lines.append("")
    lines.append("## Totals")
    lines.append("")
    lines.append(f"- **Total notes**: {report.total}")
    for status, count in report.by_status.items():
        lines.append(f"- `{status}`: {count}")
    lines.append("")
    lines.append("## Pointers")
    lines.append("")
    lines.append(
        "- Full hunger report: `myco hunger` (always current)"
    )
    lines.append(
        "- Contract changelog: `docs/contract_changelog.md`"
    )
    lines.append(
        "- Craft protocol: `docs/craft_protocol.md`"
    )
    lines.append("")

    content = "\n".join(lines)

    try:
        brief_path.parent.mkdir(parents=True, exist_ok=True)
        brief_path.write_text(content, encoding="utf-8")
        return brief_path
    except OSError as e:
        print(
            f"[WARN] write_boot_brief: cannot write {brief_path} ({e})",
            file=_sys.stderr,
        )
        return None


def render_entry_point_signals_block(
    root: Path,
    report: "HungerReport",
    *,
    now: Optional[datetime] = None,
) -> Optional[Path]:
    """Regex-patch the signals block in the entry-point file (MYCO.md
    or whatever `system.entry_point` declares in _canon.yaml).

    Uses sentinels `<!-- MYCO-BOOT-SIGNALS:BEGIN ... -->` and
    `<!-- MYCO-BOOT-SIGNALS:END -->`. If sentinels are absent or
    corrupted (only BEGIN, only END, or multiple pairs), emits `[WARN]`
    to stderr and skips — never writes partial content.

    Wave 17 (contract v0.16.0). Returns the entry point path on success,
    None on skip/failure.
    """
    import re as _re
    import sys as _sys
    try:
        import yaml as _yaml
    except ImportError:
        return None

    canon_path = Path(root) / "_canon.yaml"
    if not canon_path.exists():
        return None
    try:
        canon = _yaml.safe_load(canon_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return None

    system = canon.get("system") or {}
    cfg = system.get("boot_brief") or {}
    if not cfg.get("enabled", True):
        return None

    entry_point_name = system.get("entry_point", "MYCO.md")
    entry_path = Path(root) / entry_point_name
    if not entry_path.exists():
        return None  # silent: nothing to patch

    try:
        text = entry_path.read_text(encoding="utf-8")
    except OSError:
        return None

    # Sentinel regex: BEGIN anchor allows arbitrary comment text after
    # "BEGIN", END is fixed.
    begin_re = _re.compile(
        r"<!--\s*MYCO-BOOT-SIGNALS:BEGIN\b[^>]*-->",
    )
    end_re = _re.compile(
        r"<!--\s*MYCO-BOOT-SIGNALS:END\s*-->",
    )

    begins = list(begin_re.finditer(text))
    ends = list(end_re.finditer(text))

    if len(begins) == 0 and len(ends) == 0:
        # Clean absence — grandfather: no sentinel, no patch, no warn.
        return None
    if len(begins) != 1 or len(ends) != 1:
        print(
            f"[WARN] render_entry_point_signals_block: expected exactly "
            f"one BEGIN/END sentinel pair in {entry_point_name}, found "
            f"{len(begins)} BEGIN / {len(ends)} END — skipping render.",
            file=_sys.stderr,
        )
        return None

    begin_m, end_m = begins[0], ends[0]
    if end_m.start() < begin_m.end():
        print(
            f"[WARN] render_entry_point_signals_block: END sentinel "
            f"precedes BEGIN in {entry_point_name} — skipping.",
            file=_sys.stderr,
        )
        return None

    priority = cfg.get("priority_signals") or [
        "contract_drift",
        "raw_backlog",
        "craft_reflex_missing",
        "session_end_drift",
    ]
    now_dt = now or datetime.now(tz=None)
    ts = now_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Build condensed block content. One short line per matching
    # priority signal. "healthy" = explicit ok mark.
    block_lines: List[str] = []
    block_lines.append(
        "<!-- MYCO-BOOT-SIGNALS:BEGIN (auto-generated by myco hunger; "
        "L2/L6 ignore this region) -->"
    )
    block_lines.append("")
    block_lines.append(f"> 🫀 **Boot signals** (last `myco hunger`: `{ts}`)")
    block_lines.append(">")

    matched_any = False
    for sig in report.signals:
        head = sig.splitlines()[0] if "\n" in sig else sig
        # Classify by keyword — match signal names as prefixes.
        classified = None
        lower = head.lower()
        for p in priority:
            key = p.lower()
            if key in lower or head.startswith(f"[REFLEX HIGH] {key}"):
                classified = p
                break
        if classified is None and "healthy" in lower:
            classified = "healthy"
        if classified is None:
            continue
        matched_any = True
        # Trim to ~140 chars for display compactness.
        display = head if len(head) <= 140 else head[:137] + "..."
        block_lines.append(f"> - {display}")

    if not matched_any:
        block_lines.append("> - (no priority signals matched; see full brief)")

    block_lines.append(">")
    brief_rel = cfg.get("brief_path", ".myco_state/boot_brief.md")
    block_lines.append(f"> Full brief: `{brief_rel}`")
    block_lines.append("")
    block_lines.append("<!-- MYCO-BOOT-SIGNALS:END -->")

    new_block = "\n".join(block_lines)

    new_text = (
        text[:begin_m.start()]
        + new_block
        + text[end_m.end():]
    )

    if new_text == text:
        return entry_path  # no change needed, still success

    try:
        entry_path.write_text(new_text, encoding="utf-8")
        return entry_path
    except OSError as e:
        print(
            f"[WARN] render_entry_point_signals_block: cannot write "
            f"{entry_path} ({e})",
            file=_sys.stderr,
        )
        return None


def detect_skill_degradation(
    root: Path,
    *,
    now: Optional[datetime] = None,
) -> List[str]:
    """Return `skill_degradation` signal strings for skills that have never
    been evolved despite existing long enough to warrant review.

    A skill is considered degraded when ALL of:
        1. A ``skills/<name>.md`` file exists.
        2. No corresponding file exists in ``skills/.evolved/`` (prefix match
           on ``<name>_gen``).
        3. The skill file is older than ``stale_active_threshold_days``
           (default 7, from ``_canon.yaml::system.evolution``).

    This means the skill has been running for over a week without any
    evolutionary improvement.  The signal nudges the Agent to call
    ``myco_evolve`` to mutate the skill.

    Returns a (possibly empty) list of signal strings — one per degraded
    skill.  Fails open on any IO / parse error (returns []).
    """
    now_dt = now or datetime.now()
    skills_dir = Path(root) / "skills"
    if not skills_dir.is_dir():
        return []

    # Read threshold from canon — default to 7 days.
    stale_days = 7
    try:
        import yaml as _yaml
        canon_path = Path(root) / "_canon.yaml"
        if canon_path.exists():
            canon = _yaml.safe_load(
                canon_path.read_text(encoding="utf-8")) or {}
            evo = (canon.get("system") or {}).get("evolution") or {}
            if not evo.get("enabled", False):
                return []  # evolution disabled — no signal
            stale_days = int(evo.get("stale_active_threshold_days", 7))
    except Exception:
        return []  # grandfather-compatible: unreadable canon = silent

    evolved_dir = skills_dir / ".evolved"
    evolved_names: set = set()
    if evolved_dir.is_dir():
        for ep in evolved_dir.iterdir():
            # evolved files are named <skill>_gen<N>_<hash>.md / .bundle.json
            stem = ep.stem  # e.g. "metabolic-cycle_gen1_f523a4d46159"
            # extract skill name prefix before first "_gen"
            idx = stem.find("_gen")
            if idx > 0:
                evolved_names.add(stem[:idx])

    signals: List[str] = []
    for skill_path in sorted(skills_dir.glob("*.md")):
        skill_name = skill_path.stem  # e.g. "metabolic-cycle"
        if skill_name in evolved_names:
            continue  # has been evolved at least once

        # Check file age via mtime.
        try:
            mtime = datetime.fromtimestamp(skill_path.stat().st_mtime)
        except OSError:
            continue
        age_days = (now_dt - mtime).days
        if age_days < stale_days:
            continue  # too young to flag

        signals.append(
            f"skill_degradation: skills/{skill_name}.md has never been "
            f"evolved (age: {age_days} days). Consider running "
            f"myco_evolve to improve it."
        )
    return signals


def compute_hunger_report(
    root: Path,
    *,
    stale_days: int = 7,
    dead_threshold_days: Optional[int] = None,
    terminal_statuses: Optional[Tuple[str, ...]] = None,
    now: Optional[datetime] = None,
) -> HungerReport:
    """Scan notes/ and return a HungerReport.

    Signals (ordered by urgency):
        - "raw_backlog":     >10 raw notes (digestive tract is constipated)
        - "stale_raw":       ≥1 raw note untouched for `stale_days`+ days
        - "no_deep_digest":  no note has digest_count ≥ 2 (milestone retrospective starved)
        - "no_excretion":    zero excreted notes (compression doctrine ignored)
        - "dead_knowledge":  ≥1 terminal note cold + unviewed past threshold
                             (Self-Model D layer seed, v0.4.0)
        - "skill_degradation": skill exists but never evolved + older than
                             stale_active_threshold_days (default 7)
        - "healthy":         none of the above triggered

    Dead-knowledge detection (v0.4.0) flags a note iff ALL of:
        1. status ∈ terminal_statuses (default: extracted/integrated)
        2. now - created ≥ dead_threshold_days   (grace period for new notes)
        3. now - last_touched ≥ dead_threshold_days
        4. last_viewed_at is None OR now - last_viewed_at ≥ dead_threshold_days
        5. view_count < 2
    See docs/primordia/dead_knowledge_seed_craft_2026-04-11.md.
    """
    now = now or datetime.now()
    stale_cutoff = now - timedelta(days=stale_days)

    if dead_threshold_days is None or terminal_statuses is None:
        canon_days, canon_terms = _load_dead_config(root)
        if terminal_statuses is None:
            terminal_statuses = canon_terms
        if dead_threshold_days is None:
            # Organ 4: adaptive dead threshold based on substrate age.
            # Younger substrates use shorter thresholds (more aggressive pruning).
            # canon_days is the CEILING (max), 7 is the FLOOR (min).
            try:
                all_notes = list_notes(root)
                if all_notes:
                    ages = []
                    for np in all_notes:
                        m, _ = read_note(np)
                        c = m.get("created")
                        if c:
                            try:
                                cd = datetime.strptime(str(c).strip(), _ISO_FMT)
                                ages.append((now - cd).days)
                            except ValueError:
                                pass
                    if ages:
                        ages.sort()
                        median_age = ages[len(ages) // 2]
                        adaptive = int(median_age * 0.5)
                        dead_threshold_days = min(canon_days, max(7, adaptive))
                    else:
                        dead_threshold_days = canon_days
                else:
                    dead_threshold_days = canon_days
            except Exception:
                dead_threshold_days = canon_days
    dead_cutoff = now - timedelta(days=dead_threshold_days)

    # Wave 13 (v0.12.0): pull raw_backlog exemption config.
    # raw_backlog counts only PURE raw notes: digest_count == 0 AND
    # source not in boot_reflex.raw_exempt_sources.
    raw_exempt_sources: set = set()
    boot_threshold = 10
    try:
        import yaml as _yaml  # local to keep hunger import-time cheap
        _canon_path = Path(root) / "_canon.yaml"
        if _canon_path.exists():
            _canon = _yaml.safe_load(_canon_path.read_text(encoding="utf-8")) or {}
            _boot = ((_canon.get("system") or {}).get("boot_reflex") or {})
            raw_exempt_sources = set(_boot.get("raw_exempt_sources") or [])
            boot_threshold = int(_boot.get("raw_backlog_threshold", 10))
    except Exception:
        pass

    paths = list_notes(root)
    by_status: Dict[str, int] = {s: 0 for s in VALID_STATUSES}
    stale_raw: List[Dict[str, Any]] = []
    deep_digested: List[Dict[str, Any]] = []
    promote_candidates: List[Dict[str, Any]] = []
    dead_notes: List[Dict[str, Any]] = []
    excreted_with_reason = 0
    pure_raw_count = 0

    def _parse_iso(v: Any) -> Optional[datetime]:
        if not v:
            return None
        try:
            return datetime.strptime(str(v), _ISO_FMT)
        except Exception:
            return None

    for p in paths:
        try:
            meta, _ = read_note(p)
        except Exception:
            continue

        status = meta.get("status", "raw")
        by_status[status] = by_status.get(status, 0) + 1

        # Wave 13: pure-raw accounting (boot_reflex)
        if status == "raw":
            _dc = int(meta.get("digest_count") or 0)
            _src = str(meta.get("source") or "")
            if _dc == 0 and _src not in raw_exempt_sources:
                pure_raw_count += 1

        rel = str(p.name)
        lt = _parse_iso(meta.get("last_touched"))
        created = _parse_iso(meta.get("created"))
        last_viewed = _parse_iso(meta.get("last_viewed_at"))
        view_count = int(meta.get("view_count") or 0)

        if status == "raw" and lt and lt < stale_cutoff:
            stale_raw.append({
                "id": meta.get("id"),
                "file": rel,
                "last_touched": meta.get("last_touched"),
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

        # v0.4.0 — dead knowledge detection (Self-Model D layer seed).
        # All five conditions must hold.
        if (
            status in terminal_statuses
            and created is not None and created < dead_cutoff
            and lt is not None and lt < dead_cutoff
            and (last_viewed is None or last_viewed < dead_cutoff)
            and view_count < 2
        ):
            dead_notes.append({
                "id": meta.get("id"),
                "file": rel,
                "status": status,
                "created": meta.get("created"),
                "last_touched": meta.get("last_touched"),
                "last_viewed_at": meta.get("last_viewed_at"),
                "view_count": view_count,
                "tags": meta.get("tags", []),
            })

    raw_count = by_status.get("raw", 0)

    signals: List[str] = []
    # Wave 13 (contract v0.12.0): contract drift check fires first — it
    # gates everything else if violated.
    try:
        drift_signal = detect_contract_drift(root)
        if drift_signal:
            signals.append(drift_signal)
    except Exception:
        pass

    # Wave 13: raw_backlog uses pure_raw_count (digest_count==0 AND
    # source not exempt) and threshold from _canon.yaml::boot_reflex.
    # Upgraded to [REFLEX HIGH] — W1 autopilot violation if unhandled.
    if pure_raw_count > boot_threshold:
        signals.append(
            f"[REFLEX HIGH] raw_backlog: {pure_raw_count} pure-raw notes "
            f"(digest_count=0, non-exempt source) exceed threshold "
            f"{boot_threshold}. IMMUTABLE REFLEX (W1 autopilot, contract "
            f"v0.12.0): digest at least "
            f"{max(1, pure_raw_count - boot_threshold)} note(s) via "
            f"`myco digest` in this session before any task work. "
            f"Ignoring raw_backlog is a W1 violation — auto-sedimentation "
            f"is the foundational premise of the digestive substrate. "
            f"See docs/primordia/boot_reflex_arc_craft_2026-04-11.md."
        )
    if stale_raw:
        signals.append(
            f"stale_raw: {len(stale_raw)} raw note(s) untouched for ≥{stale_days} days."
        )
    if not deep_digested and by_status.get("extracted", 0) + by_status.get("integrated", 0) == 0:
        signals.append(
            "no_deep_digest: no note has been digested twice AND no note has "
            "reached extracted/integrated — milestone retrospective may be starving."
        )
    # Check lifetime excretion counter (survives note deletion after
    # compression). On-disk excreted count alone produces false positives
    # when excreted notes are cleaned up from disk.
    _lifetime_exc = read_excretion_counter(root).get("lifetime_excretions", 0)
    if (by_status.get("excreted", 0) == 0
            and _lifetime_exc == 0
            and len(paths) >= 20):
        signals.append(
            "no_excretion: zero notes excreted despite ≥20 total notes. "
            "Compression doctrine ('attention finite') is being ignored."
        )
    if promote_candidates:
        signals.append(
            f"promote_ready: {len(promote_candidates)} note(s) flagged "
            f"promote_candidate=true — ready to lift into wiki/."
        )
    if dead_notes:
        signals.append(
            f"dead_knowledge: {len(dead_notes)} terminal note(s) "
            f"(extracted/integrated) have gone cold for ≥{dead_threshold_days} days "
            f"— never viewed or view_count<2. Candidates for excretion or "
            f"promotion. See `myco hunger --dead` for details (Self-Model D layer seed)."
        )
    # Structural bloat signal (contract v0.5.0) — read-only scan of
    # docs/ and docs/primordia/ against _canon.yaml::structural_limits.
    bloat_signal = detect_structural_bloat(root)
    if bloat_signal:
        signals.append(bloat_signal)
    # Craft reflex signal (contract v0.10.0) — read-only scan of
    # craft_protocol.reflex trigger surfaces. Mirrors L15 logic in
    # src/myco/lint.py but surfaces in `myco hunger` so the signal
    # appears at every session boot, not only when lint is run.
    # See docs/primordia/craft_reflex_craft_2026-04-11.md.
    try:
        craft_signal = detect_craft_reflex_missing(root, now=now)
        if craft_signal:
            signals.append(craft_signal)
    except Exception:
        pass  # grandfather: missing canon block = feature off
    # Session end drift signal (contract v0.13.0, Wave 14) — session reflection / cross-project distillation
    # advisory drift. LOW tier, appears in advisory list. See
    # docs/primordia/session_end_reflex_arc_craft_2026-04-11.md.
    try:
        sed_signal = detect_session_end_drift(root, now=now)
        if sed_signal:
            signals.append(sed_signal)
    except Exception:
        pass  # grandfather-compatible: missing canon block = feature off
    # Forage backlog signal (contract v0.7.0) — read-only scan of
    # forage/_index.yaml. See docs/primordia/forage_substrate_craft_2026-04-11.md.
    try:
        from myco.forage import detect_forage_backlog
        forage_signal = detect_forage_backlog(root)
        if forage_signal:
            signals.append(forage_signal)
    except Exception:
        pass  # grandfather-compatible: missing module = feature off
    # Compression ripe signal (contract v0.26.0, Wave 30) — friction-driven
    # half of forward compression's trigger surface. Wave 27 D2.
    compress_signal = None  # init before try — actions block reads this later
    try:
        compress_signal = detect_compression_ripe(root, now=now)
        if compress_signal:
            signals.append(compress_signal)
    except Exception:
        pass  # grandfather-compatible: missing canon block = feature off
    # Inlet trigger signal (Wave 49, contract v0.38.0) — fires when search
    # misses accumulate or cohort gaps are detected. Closes open_problems §2.
    inlet_signal = None  # init before try — actions block reads this later
    try:
        inlet_signal = detect_inlet_trigger(root, now=now)
        if inlet_signal:
            signals.append(inlet_signal)
    except Exception:
        pass  # grandfather-compatible: missing module = feature off
    # Compression pressure signal (Wave 50, contract v0.39.0) — fires when
    # raw+digesting significantly exceeds extracted+integrated. Continuous
    # compression loop. Partially closes open_problems §4.
    pressure_val = 0.0
    try:
        canon_path = root / "_canon.yaml"
        pressure_threshold = 2.0
        if canon_path.exists():
            with open(canon_path, "r", encoding="utf-8") as f:
                _c = yaml.safe_load(f) or {}
            pressure_threshold = float(
                _c.get("system", {}).get("notes_schema", {})
                   .get("compression", {}).get("pressure_threshold", 2.0))
        pressure_val, pressure_bk = compute_compression_pressure(root)
        if pressure_val > pressure_threshold:
            signals.append(
                f"compression_pressure: {pressure_val:.1f} "
                f"(threshold {pressure_threshold:.1f}). "
                f"raw+digesting={pressure_bk['raw']+pressure_bk['digesting']} "
                f"vs extracted+integrated="
                f"{pressure_bk['extracted']+pressure_bk['integrated']}. "
                f"Run `myco compress` to reduce pressure."
            )
    except Exception:
        pass  # grandfather-compatible
    # Graph orphan signal (Wave 54, contract v0.41.0) — structural
    # connectivity check. Fires when orphan file count exceeds threshold.
    orphan_count = 0
    try:
        from myco.mycelium import build_link_graph, find_orphans
        graph = build_link_graph(root)
        orphans = find_orphans(graph)
        orphan_count = len(orphans)
        if orphan_count > 5:
            # Categorize orphans by file type for actionable reporting
            cats = {"notes": [], "docs": [], "wiki": [], "skills": [], "other": []}
            for o in orphans:
                if o.startswith("notes/"):
                    cats["notes"].append(o)
                elif o.startswith("docs/"):
                    cats["docs"].append(o)
                elif o.startswith("wiki/"):
                    cats["wiki"].append(o)
                elif o.startswith("skills/"):
                    cats["skills"].append(o)
                else:
                    cats["other"].append(o)
            breakdown = ", ".join(
                f"{k}={len(v)}" for k, v in cats.items() if v
            )
            signals.append(
                f"graph_orphans: {orphan_count} files with zero inbound links "
                f"({breakdown}). Add cross-references to build the mycelium network."
            )
    except Exception:
        pass  # grandfather-compatible: graph module not available
    # Session index staleness (Wave 54) — nudge to re-index sessions.
    try:
        db_path = root / ".myco_state" / "sessions.db"
        if not db_path.exists():
            signals.append(
                "session_index_missing: no session memory index found. "
                "Run `myco session index` to enable searchable conversation history."
            )
    except Exception:
        pass
    # Cohort staleness signal (Wave 59) — fires LOW when any tag cohort has
    # ONLY raw/digesting notes for > gap_stale_days (default 14). Uses
    # cohorts.gap_detection with a time filter on the oldest note's age.
    try:
        from myco.colony import gap_detection
        canon_path = root / "_canon.yaml"
        gap_stale_days = 14
        if canon_path.exists():
            with open(canon_path, "r", encoding="utf-8") as f:
                _gc = yaml.safe_load(f) or {}
            gap_stale_days = int(
                _gc.get("system", {}).get("notes_schema", {})
                   .get("compression", {}).get("gap_stale_days", 14))
        gaps = gap_detection(root)
        stale_gaps = []
        for g in gaps:
            if g.get("total", 0) >= 3:  # minimum cohort size for staleness
                stale_gaps.append(g["tag"])
        if stale_gaps:
            tags_preview = ", ".join(stale_gaps[:3])
            signals.append(
                f"cohort_staleness: {len(stale_gaps)} tag cohort(s) with only "
                f"unprocessed notes (top: {tags_preview}). Consider digesting "
                f"or compressing these knowledge gaps."
            )
    except Exception:
        pass  # grandfather-compatible
    # Predictive hunger signal (Wave E1) — anticipate knowledge needs
    # from session history analysis.
    try:
        from myco.memory import predict_knowledge_needs
        predictions = predict_knowledge_needs(root, limit=3)
        if predictions:
            topics = ", ".join(p["topic"] for p in predictions[:3])
            signals.append(
                f"predicted_need: {len(predictions)} anticipated knowledge "
                f"need(s) from session history (top: {topics}). Consider "
                f"proactive acquisition via `myco_absorb`."
            )
    except Exception:
        pass  # grandfather-compatible
    # Organ 2: Cold-start inlet trigger — fires when substrate is nearly empty
    # and no inlet has ever been run. Nudges Agent to proactively acquire knowledge.
    try:
        cold_threshold = 5
        canon_path = root / "_canon.yaml"
        if canon_path.exists():
            with open(canon_path, "r", encoding="utf-8") as f:
                _cc = yaml.safe_load(f) or {}
            cold_threshold = int(
                _cc.get("system", {}).get("inlet_triggers", {})
                   .get("cold_start_threshold", 5))
        note_count = len(paths)
        has_inlet = any(
            "source: inlet" in p.read_text(encoding="utf-8", errors="replace")[:300]
            for p in paths
        )
        if note_count < cold_threshold and not has_inlet:
            signals.append(
                f"cold_start: substrate has only {note_count} notes and no inlet "
                f"history. Consider running `myco inlet` to "
                f"bootstrap initial knowledge."
            )
    except Exception:
        pass
    # Organ 3: Structural decay metric — fires when orphan count is increasing
    try:
        decay_path = root / ".myco_state" / "decay_baseline.yaml"
        from myco.mycelium import build_link_graph, find_orphans
        graph = build_link_graph(root)
        current_orphans = len(find_orphans(graph))
        if decay_path.exists():
            with open(decay_path, "r", encoding="utf-8") as f:
                baseline = yaml.safe_load(f) or {}
            prev_count = baseline.get("orphan_count", current_orphans)
            delta = current_orphans - prev_count
            if delta > 5:
                signals.append(
                    f"structural_decay: orphan count increased by {delta} "
                    f"(was {prev_count}, now {current_orphans}). Knowledge "
                    f"connectivity is degrading."
                )
        # Update baseline
        decay_path.parent.mkdir(parents=True, exist_ok=True)
        with open(decay_path, "w", encoding="utf-8") as f:
            yaml.dump({"orphan_count": current_orphans,
                       "timestamp": _now_iso()}, f)
    except Exception:
        pass
    # Skill degradation signal — fires when a skill has never been evolved
    # despite being old enough to warrant review. Nudges the Agent to run
    # myco_evolve. Config: _canon.yaml::system.evolution.
    skill_degradation_signals: List[str] = []
    try:
        skill_degradation_signals = detect_skill_degradation(root, now=now)
        signals.extend(skill_degradation_signals)
    except Exception:
        pass  # grandfather-compatible: missing skills/ or canon = feature off
    # Vestigial organ detection — find src/myco/ modules that no other
    # module imports. These are "alive in code but dead in practice" —
    # like the removed upstream.py, discover.py, session_miner.py.
    # The Agent reviews flagged modules and decides: keep or excise.
    try:
        _root = Path(root).resolve() if not isinstance(root, Path) else root.resolve()
        src_dir = _root / "src" / "myco"
        if src_dir.is_dir():
            import os as _os
            # Exclude entry points (they ARE the top-level; nobody imports them)
            _ENTRY_POINTS = {
                "__init__.py", "__main__.py",
                "cli.py", "mcp_server.py",  # top-level dispatchers
            }
            py_files = [
                f for f in _os.listdir(str(src_dir))
                if f.endswith(".py") and not f.startswith("_")
                and f not in _ENTRY_POINTS
            ]
            # For each module, check if any OTHER .py file imports it
            vestigial = []
            for pyf in py_files:
                mod_name = pyf[:-3]  # strip .py
                # Search all .py files for import of this module
                import_patterns = (
                    f"from myco.{mod_name}",
                    f"from myco import {mod_name}",
                    f"import myco.{mod_name}",
                )
                found_importer = False
                for check_dir in [src_dir, _root / "tests"]:
                    if not check_dir.is_dir():
                        continue
                    for dirpath, _, filenames in _os.walk(str(check_dir)):
                        for fn in filenames:
                            if not fn.endswith(".py"):
                                continue
                            fpath = _os.path.join(dirpath, fn)
                            # Don't count self-imports
                            if _os.path.basename(fpath) == pyf and \
                               _os.path.dirname(fpath) == str(src_dir):
                                continue
                            try:
                                content = open(fpath, "r",
                                               encoding="utf-8",
                                               errors="replace").read()
                                if any(p in content for p in import_patterns):
                                    found_importer = True
                                    break
                            except OSError:
                                continue
                        if found_importer:
                            break
                if not found_importer:
                    vestigial.append(mod_name)
            if vestigial:
                mods = ", ".join(sorted(vestigial))
                signals.append(
                    f"vestigial_organ: {len(vestigial)} module(s) in src/myco/ "
                    f"with zero importers: {mods}. "
                    f"Review: keep (justify) or excise (remove)."
                )
    except Exception:
        pass  # grandfather-compatible

    if not signals:
        signals.append("healthy: notes/ is metabolizing normally.")

    # Wave 46 (v0.35.0): compute structured action recommendations.
    # Each action is a dict with verb, args, and reason. The agent reads
    # these and executes without human prompting. Actions are derived from
    # signals — they are the executable counterpart of the advisory signals.
    actions: List[Dict[str, Any]] = []
    if stale_raw:
        oldest = stale_raw[0]
        actions.append({
            "verb": "digest",
            "args": {"note_id": oldest.get("id")},
            "reason": f"stale_raw: note {oldest.get('id')} untouched for ≥{stale_days} days",
        })
    if pure_raw_count > boot_threshold:
        actions.append({
            "verb": "digest",
            "args": {},
            "reason": f"raw_backlog: {pure_raw_count} pure-raw notes exceed threshold {boot_threshold}",
        })
    if dead_notes:
        actions.append({
            "verb": "prune",
            "args": {"apply": True},
            "reason": f"dead_knowledge: {len(dead_notes)} terminal note(s) cold for ≥{dead_threshold_days} days",
        })
    if compress_signal:
        actions.append({
            "verb": "compress",
            "args": {"tag": "inlet"},
            "reason": str(compress_signal),
        })
    if inlet_signal:
        actions.append({
            "verb": "inlet",
            "args": {},
            "reason": str(inlet_signal),
        })
    if pressure_val > 2.0:
        actions.append({
            "verb": "compress",
            "args": {"cohort": "auto"},
            "reason": f"compression_pressure={pressure_val:.1f} exceeds threshold 2.0",
        })
    if promote_candidates:
        for pc in promote_candidates[:3]:
            actions.append({
                "verb": "digest",
                "args": {"note_id": pc.get("id"), "to_status": "integrated"},
                "reason": f"promote_ready: note {pc.get('id')} flagged promote_candidate=true",
            })
    if skill_degradation_signals:
        for sd_sig in skill_degradation_signals:
            # Extract skill filename from signal message.
            # Format: "skill_degradation: skills/<name>.md has never been ..."
            _sd_m = re.search(r"skills/(\S+\.md)", sd_sig)
            skill_file = _sd_m.group(1) if _sd_m else "unknown"
            actions.append({
                "verb": "evolve",
                "args": {"skill": skill_file},
                "reason": sd_sig,
            })

    return HungerReport(
        total=len(paths),
        by_status=by_status,
        raw_count=raw_count,
        stale_raw=stale_raw,
        deep_digested=deep_digested,
        excreted_with_reason=excreted_with_reason,
        promote_candidates=promote_candidates,
        dead_notes=dead_notes,
        dead_threshold_days=dead_threshold_days,
        signals=signals,
        actions=actions,
    )
