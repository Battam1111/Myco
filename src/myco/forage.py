#!/usr/bin/env python3
"""
Myco Forage — external reference material substrate (contract v0.7.0).

This module is the shared engine behind the `myco forage add / list /
digest` CLI verbs. It implements the inbound channel defined in
docs/agent_protocol.md §8.9, codifies the manifest schema from
_canon.yaml::system.forage_schema, and exposes the read-only
`detect_forage_backlog` hunger signal for compute_hunger_report.

Design principles (from forage_substrate_craft_2026-04-11.md):
    1. Discipline over capability. Wave 7 ships acquisition + manifest +
       lifecycle + hunger + lint — NOT a universal content extractor.
       PDF/repo parsing is Wave 8+ work.
    2. Manifest is authoritative. Actual files in forage/papers/ |
       forage/repos/ | forage/articles/ are expendable; _index.yaml is
       the real contract surface (class_z).
    3. License required. Items without a declared license enter
       quarantined status automatically.
    4. Read/write separation. detect_forage_backlog is pure read;
       mutation only happens through add/digest/status helpers.
    5. Grandfather-compatible. Missing optional fields default
       sanely; schema evolution in future waves will not break existing
       manifests.

Public surface (keep stable — CLI, lint, and hunger depend on it):
    DEFAULT_FORAGE_SCHEMA
    generate_forage_id(now=None) -> str
    load_manifest(root) -> dict
    save_manifest(root, manifest) -> None
    add_item(root, *, source_url, source_type, local_path, license,
             why, size_bytes=None, acquired_at=None) -> dict
    list_items(root, *, status=None) -> list[dict]
    update_item_status(root, item_id, new_status, *,
                       digest_target=None) -> dict
    detect_forage_backlog(root) -> Optional[str]
    validate_item(item, schema) -> list[str]

Storage layout:
    <project_root>/forage/_index.yaml
    <project_root>/forage/{papers|repos|articles}/<content>

This file MUST NOT import from myco.cli or myco.mcp_server (one-way
dependency: cli/mcp → forage, never the reverse).
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from pathlib import Path
from myco.notes import _parse_iso
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:  # pragma: no cover — yaml is a hard dep
    yaml = None


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ISO_FMT = "%Y-%m-%dT%H:%M:%S"

DEFAULT_FORAGE_SCHEMA: Dict[str, Any] = {
    "dir": "forage",
    "index_file": "forage/_index.yaml",
    "filename_pattern": r"^f_\d{8}T\d{6}_[0-9a-f]{4}$",
    "required_item_fields": [
        "id", "source_url", "source_type", "local_path",
        "acquired_at", "status", "license", "size_bytes",
    ],
    "optional_item_fields": [
        "license_restrictions", "license_checked_at",
        "digest_target", "notes", "why",
    ],
    "valid_source_types": ["paper", "repo", "article", "other"],
    "valid_statuses": [
        "raw", "digesting", "digested", "absorbed",
        "discarded", "quarantined",
    ],
    "max_item_size_bytes": 10 * 1024 * 1024,              # 10 MB
    "forage_backlog_threshold": 1,
    "stale_raw_days": 14,
    "total_budget_bytes": 200 * 1024 * 1024,              # 200 MB
    "hard_budget_bytes": 1024 * 1024 * 1024,              # 1 GB
    "license_recheck_days": 90,
}


# ---------------------------------------------------------------------------
# Config loading — grandfather-compatible
# ---------------------------------------------------------------------------

def _load_forage_schema(root: Path) -> Dict[str, Any]:
    """Read forage_schema from _canon.yaml with safe fallback."""
    if yaml is None:
        return dict(DEFAULT_FORAGE_SCHEMA)
    canon_path = Path(root) / "_canon.yaml"
    if not canon_path.exists():
        return dict(DEFAULT_FORAGE_SCHEMA)
    try:
        canon = yaml.safe_load(canon_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return dict(DEFAULT_FORAGE_SCHEMA)
    sc = (canon.get("system") or {}).get("forage_schema") or {}
    merged = dict(DEFAULT_FORAGE_SCHEMA)
    merged.update(sc)
    # Coerce numeric types in case YAML parsed them as strings.
    for key in ("max_item_size_bytes", "forage_backlog_threshold",
                "stale_raw_days", "total_budget_bytes",
                "hard_budget_bytes", "license_recheck_days"):
        if key in merged:
            try:
                merged[key] = int(merged[key])
            except (TypeError, ValueError):
                merged[key] = DEFAULT_FORAGE_SCHEMA[key]
    return merged


# ---------------------------------------------------------------------------
# ID generation
# ---------------------------------------------------------------------------

def generate_forage_id(now: Optional[datetime] = None) -> str:
    """f_YYYYMMDDTHHMMSS_xxxx — matches notes id shape with f_ prefix."""
    now = now or datetime.now()
    stamp = now.strftime("%Y%m%dT%H%M%S")
    suffix = secrets.token_hex(2)
    return f"f_{stamp}_{suffix}"


# ---------------------------------------------------------------------------
# Manifest I/O
# ---------------------------------------------------------------------------

def _manifest_path(root: Path) -> Path:
    return Path(root) / "forage" / "_index.yaml"


def _empty_manifest() -> Dict[str, Any]:
    return {"schema_version": 1, "items": []}


def load_manifest(root: Path) -> Dict[str, Any]:
    """Read forage/_index.yaml; return empty manifest if missing.

    Safe fallback: malformed YAML returns empty manifest (L14 will flag).
    """
    if yaml is None:
        return _empty_manifest()
    path = _manifest_path(root)
    if not path.exists():
        return _empty_manifest()
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return _empty_manifest()
    if not isinstance(data, dict):
        return _empty_manifest()
    if "items" not in data or data["items"] is None:
        data["items"] = []
    if "schema_version" not in data:
        data["schema_version"] = 1
    return data


def save_manifest(root: Path, manifest: Dict[str, Any]) -> None:
    """Write forage/_index.yaml atomically. Respects ordering hint."""
    if yaml is None:
        raise RuntimeError("yaml is required for forage manifest writes")
    path = _manifest_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Stable key ordering to minimize diff noise.
    out = {
        "schema_version": manifest.get("schema_version", 1),
        "items": manifest.get("items", []),
    }
    text = yaml.safe_dump(
        out, sort_keys=False, allow_unicode=True, default_flow_style=False
    )
    tmp_path = path.with_suffix(".yaml.tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


# ---------------------------------------------------------------------------
# Item mutations
# ---------------------------------------------------------------------------

def _stable_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Order item keys stably for diff-friendly serialization."""
    order = [
        "id", "source_url", "source_type", "local_path", "acquired_at",
        "status", "license", "license_restrictions", "license_checked_at",
        "size_bytes", "digest_target", "why", "notes",
    ]
    out: Dict[str, Any] = {}
    for k in order:
        if k in item:
            out[k] = item[k]
    for k in item:
        if k not in out:
            out[k] = item[k]
    return out


def add_item(
    root: Path,
    *,
    source_url: str,
    source_type: str,
    local_path: str,
    license: str,
    why: str,
    size_bytes: Optional[int] = None,
    acquired_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Append a new item to the manifest and return it.

    Behavior:
        - `why` is mandatory. The craft §Round 1 A5 enforces
          intent-at-acquisition to prevent hoarding.
        - `license == "unknown"` auto-quarantines (status=quarantined
          instead of raw) per Round 1 A1 defense.
        - `size_bytes` is auto-computed from local_path if not given and
          the file exists.
        - ID is deterministically time-ordered (sort-friendly).
    """
    if not source_url:
        raise ValueError("source_url is required")
    if not why or not why.strip():
        raise ValueError("why is required (intent statement)")
    if not license:
        raise ValueError("license is required (use 'unknown' to quarantine)")

    schema = _load_forage_schema(root)
    valid_types = schema.get("valid_source_types", [])
    if valid_types and source_type not in valid_types:
        raise ValueError(
            f"source_type {source_type!r} not in valid_source_types {valid_types}"
        )

    now = datetime.now()
    item_id = generate_forage_id(now)
    acquired_at = acquired_at or now.strftime(_ISO_FMT)

    # Auto-compute size if file exists
    if size_bytes is None:
        abs_local = Path(root) / local_path
        if abs_local.exists() and abs_local.is_file():
            size_bytes = abs_local.stat().st_size
        else:
            size_bytes = 0

    status = "raw"
    if license.strip().lower() == "unknown":
        status = "quarantined"

    item = {
        "id": item_id,
        "source_url": source_url,
        "source_type": source_type,
        "local_path": local_path,
        "acquired_at": acquired_at,
        "status": status,
        "license": license,
        "license_checked_at": acquired_at,
        "size_bytes": int(size_bytes),
        "digest_target": [],
        "why": why.strip(),
    }
    item = _stable_item(item)

    manifest = load_manifest(root)
    manifest.setdefault("items", []).append(item)
    save_manifest(root, manifest)
    return item


def list_items(
    root: Path, *, status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Return items, optionally filtered by status."""
    manifest = load_manifest(root)
    items = list(manifest.get("items") or [])
    if status is not None:
        items = [i for i in items if i.get("status") == status]
    return items


def update_item_status(
    root: Path,
    item_id: str,
    new_status: str,
    *,
    digest_target: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Flip a foraged item's status, with digest_target update hook.

    Contract enforced:
        - `digested` status REQUIRES non-empty digest_target (craft §A8).
        - `absorbed` status requires prior `digested` OR non-empty
          digest_target.
        - Returns the updated item.
    """
    schema = _load_forage_schema(root)
    valid = schema.get("valid_statuses", [])
    if valid and new_status not in valid:
        raise ValueError(
            f"invalid status {new_status!r}; must be one of {valid}"
        )

    manifest = load_manifest(root)
    items = manifest.get("items") or []
    target = None
    for it in items:
        if it.get("id") == item_id:
            target = it
            break
    if target is None:
        raise KeyError(f"forage item {item_id!r} not found in manifest")

    if digest_target is not None:
        target["digest_target"] = list(digest_target)

    # Enforce digest_target non-empty for digested/absorbed
    if new_status in ("digested", "absorbed"):
        dt = target.get("digest_target") or []
        if not dt:
            raise ValueError(
                f"cannot transition to {new_status!r} without a "
                f"non-empty digest_target (forage craft §Round 1 A8)"
            )

    target["status"] = new_status
    # Re-stabilize key order
    for i, it in enumerate(items):
        if it.get("id") == item_id:
            items[i] = _stable_item(target)
            break
    manifest["items"] = items
    save_manifest(root, manifest)

    # Wave 61: Mycelium wrapping — auto cross-reference.
    # When transitioning to "digested" with a digest_target, ensure each
    # referenced note has `forage_source` in its frontmatter. This creates
    # bidirectional linking even if the caller forgot to set forage_source
    # during myco_eat.
    if new_status == "digested":
        dt = target.get("digest_target") or []
        if dt:
            _backpatch_forage_source(root, item_id, dt)

    return target


def _backpatch_forage_source(
    root: Path, forage_item_id: str, note_ids: List[str]
) -> None:
    """Add forage_source to notes that lack it (best-effort, no exceptions)."""
    notes_dir = Path(root) / "notes"
    for nid in note_ids:
        note_path = notes_dir / f"{nid}.md"
        if not note_path.exists():
            continue
        try:
            text = note_path.read_text(encoding="utf-8")
            # Quick check: if forage_source already present, skip.
            if "forage_source:" in text:
                continue
            # Parse frontmatter, inject field, rewrite.
            from myco.notes import _parse_iso, parse_frontmatter, serialize_note
            meta, body = parse_frontmatter(text)
            if not meta:
                continue
            meta["forage_source"] = forage_item_id
            from myco.io_utils import atomic_write_text
            atomic_write_text(note_path, serialize_note(meta, body))
        except Exception:
            # Best-effort: never let cross-ref failure block status update.
            pass


# ---------------------------------------------------------------------------
# Hunger signal — read-only
# ---------------------------------------------------------------------------


def detect_forage_backlog(root: Path) -> Optional[str]:
    """Return a `forage_backlog` signal string if the substrate is
    overdue on digesting foraged material, else None.

    Triggers (ANY of):
        1. raw count >= forage_backlog_threshold
        2. any raw item with acquired_at older than stale_raw_days
        3. total disk budget >= total_budget_bytes

    Read-only scan: does not mutate manifest or filesystem.
    """
    schema = _load_forage_schema(root)
    manifest = load_manifest(root)
    items = manifest.get("items") or []
    if not items:
        return None

    raw_items = [i for i in items if i.get("status") == "raw"]
    now = datetime.now()
    stale_cutoff = now - timedelta(days=int(schema["stale_raw_days"]))

    raw_count = len(raw_items)
    stale_raw = 0
    for it in raw_items:
        acq = _parse_iso(it.get("acquired_at"))
        if acq is not None and acq < stale_cutoff:
            stale_raw += 1

    total_bytes = 0
    for it in items:
        if it.get("status") in ("discarded",):
            continue
        sz = it.get("size_bytes") or 0
        try:
            total_bytes += int(sz)
        except (TypeError, ValueError):
            pass

    threshold = int(schema["forage_backlog_threshold"])
    budget = int(schema["total_budget_bytes"])

    parts: List[str] = []
    if raw_count >= threshold:
        parts.append(
            f"{raw_count} raw items (≥{threshold} threshold)"
        )
    if stale_raw > 0:
        parts.append(
            f"{stale_raw} raw item(s) older than {int(schema['stale_raw_days'])} days"
        )
    if total_bytes >= budget:
        parts.append(
            f"disk footprint {total_bytes // (1024*1024)} MiB "
            f"(≥{budget // (1024*1024)} MiB soft budget)"
        )
    if not parts:
        return None
    return (
        "forage_backlog: " + "; ".join(parts) +
        ". Run `myco forage list --status raw` and digest before foraging more. "
        "See docs/primordia/forage_substrate_craft_2026-04-11.md."
    )


# ---------------------------------------------------------------------------
# Validation — used by L14 lint
# ---------------------------------------------------------------------------

def validate_item(
    item: Dict[str, Any], schema: Dict[str, Any]
) -> List[str]:
    """Return a list of validation error messages for a single item.

    Empty list = valid. Used by L14 Forage Hygiene lint.
    """
    errors: List[str] = []
    required = schema.get("required_item_fields", [])
    for field in required:
        if field not in item or item[field] in (None, ""):
            errors.append(f"missing required field: {field}")

    item_id = item.get("id")
    if item_id:
        import re
        pat = schema.get("filename_pattern", "")
        if pat and not re.match(pat, str(item_id)):
            errors.append(
                f"id {item_id!r} does not match pattern {pat}"
            )

    st = item.get("status")
    valid_statuses = schema.get("valid_statuses", [])
    if valid_statuses and st not in valid_statuses:
        errors.append(f"invalid status: {st!r}")

    source_type = item.get("source_type")
    valid_types = schema.get("valid_source_types", [])
    if valid_types and source_type not in valid_types:
        errors.append(f"invalid source_type: {source_type!r}")

    # Digested/absorbed require digest_target
    if st in ("digested", "absorbed"):
        dt = item.get("digest_target") or []
        if not dt:
            errors.append(
                f"status={st} requires non-empty digest_target"
            )

    # License required (empty string counts as missing)
    lic = item.get("license")
    if not lic:
        errors.append("license field is empty (required; use 'unknown' to quarantine)")
    elif str(lic).strip().lower() == "unknown" and st != "quarantined":
        errors.append(
            "license=unknown must coexist with status=quarantined"
        )

    # Size sanity
    sz = item.get("size_bytes")
    if sz is not None:
        try:
            int(sz)
        except (TypeError, ValueError):
            errors.append(f"size_bytes must be int, got {type(sz).__name__}")

    return errors
