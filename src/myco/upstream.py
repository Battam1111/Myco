#!/usr/bin/env python3
"""
Myco Upstream — kernel-side absorption of downstream friction bundles.

This module implements the kernel-side receiving dock for the Upstream
Protocol. Contract v0.9.0 landed this module; the protocol itself was
defined one wave earlier in v0.8.0's parent craft.

Authoritative designs:
    - Parent (protocol):   docs/primordia/upstream_protocol_craft_2026-04-11.md
    - This wave (impl):    docs/primordia/upstream_absorb_craft_2026-04-11.md

Public surface (keep stable — CLI depends on it):
    KERNEL_INBOX_DIRNAME, ABSORBED_SUBDIR, BUNDLE_FILENAME_RE
    kernel_inbox_path(root) -> Path
    scan_kernel_inbox(root) -> list[BundleRef]
    absorb_from_instance(root, instance_path) -> list[BundleRef]
    ingest_bundle(root, bundle_id) -> Path        # returns pointer note path
    compute_upstream_inbox_pressure(root, ceiling=5) -> float

Design decisions locked by the Wave 9 craft:
    D1: `.myco_upstream_inbox/` is a physical dotdir; L11 auto-exempt.
    D2: CLI triple = scan / absorb / ingest. No retire verb — ingest
        archives atomically into `absorbed/`.
    D3: ingest NEVER rewrites the bundle YAML as a note. It creates a
        pointer note carrying `source: upstream_absorbed` and
        `source_ref: .myco_upstream_inbox/<ts>_<id>.bundle.yaml`; the
        bundle body stays structurally intact in `absorbed/` as evidence.
    D4: `upstream_inbox_pressure` ∈ [0, 1] = min(count / ceiling, 1.0);
        ceiling defaults to 5 (bootstrap; pending friction data).
    D5: Instance not reachable → hard-fail with exit hint to the
        Courier Fallback flow in `docs/agent_protocol.md §8`.
"""

from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

from myco.notes import write_note

KERNEL_INBOX_DIRNAME = ".myco_upstream_inbox"
INSTANCE_OUTBOX_DIRNAME = ".myco_upstream_outbox"
ABSORBED_SUBDIR = "absorbed"

# Outbox bundle filename (as written by the instance):
#     n_YYYYMMDDTHHMMSS_<hex>.bundle.(yaml|yml|json)
OUTBOX_BUNDLE_RE = re.compile(
    r"^(?P<bundle_id>n_\d{8}T\d{6}_[0-9a-f]+)\.bundle\.(?P<ext>yaml|yml|json)$"
)

# Kernel-side bundle filename (absorb adds timestamp prefix so two
# instances with the same bundle_id don't collide, and so ordering is
# deterministic):
#     <absorb_ts>_<bundle_id>.bundle.(yaml|yml|json)
KERNEL_BUNDLE_RE = re.compile(
    r"^(?P<absorb_ts>\d{8}T\d{6})_(?P<bundle_id>n_\d{8}T\d{6}_[0-9a-f]+)"
    r"\.bundle\.(?P<ext>yaml|yml|json)$"
)

DEFAULT_INBOX_CEILING = 5


class UpstreamError(Exception):
    """Raised when an upstream operation cannot proceed safely."""


class BundleRef:
    """Lightweight descriptor for a bundle file (outbox or inbox side)."""

    __slots__ = ("path", "bundle_id", "absorb_ts", "summary", "severity",
                 "target_kernel_component", "source_project")

    def __init__(self, path: Path, bundle_id: str,
                 absorb_ts: Optional[str] = None) -> None:
        self.path = path
        self.bundle_id = bundle_id
        self.absorb_ts = absorb_ts
        self.summary: str = ""
        self.severity: str = ""
        self.target_kernel_component: str = ""
        self.source_project: str = ""

    def load_metadata(self) -> None:
        if yaml is None:
            return
        try:
            data = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        except Exception:
            return
        self.summary = str(data.get("summary", "")).strip()
        self.severity = str(data.get("severity", "")).strip()
        self.target_kernel_component = str(
            data.get("target_kernel_component", "")
        ).strip()
        self.source_project = str(data.get("source_project", "")).strip()

    def short_summary(self, width: int = 72) -> str:
        first_line = self.summary.splitlines()[0] if self.summary else ""
        if len(first_line) > width:
            return first_line[: width - 1] + "…"
        return first_line

    def to_dict(self) -> dict:
        return {
            "bundle_id": self.bundle_id,
            "path": str(self.path),
            "absorb_ts": self.absorb_ts,
            "summary": self.short_summary(),
            "severity": self.severity,
            "target_kernel_component": self.target_kernel_component,
            "source_project": self.source_project,
        }


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def kernel_inbox_path(root: Path) -> Path:
    return Path(root) / KERNEL_INBOX_DIRNAME


def kernel_absorbed_path(root: Path) -> Path:
    return kernel_inbox_path(root) / ABSORBED_SUBDIR


def instance_outbox_path(instance_root: Path) -> Path:
    return Path(instance_root) / INSTANCE_OUTBOX_DIRNAME


def _ensure_kernel_inbox(root: Path) -> Path:
    inbox = kernel_inbox_path(root)
    inbox.mkdir(exist_ok=True)
    (inbox / ABSORBED_SUBDIR).mkdir(exist_ok=True)
    return inbox


# ---------------------------------------------------------------------------
# Scan kernel inbox (single-mount default)
# ---------------------------------------------------------------------------

def scan_kernel_inbox(root: Path) -> List[BundleRef]:
    """List pending (non-absorbed) bundles in kernel inbox.

    Default verb for `myco upstream scan` — inventories what the kernel
    already has in hand and has not yet ingested into notes/.
    """
    inbox = kernel_inbox_path(root)
    if not inbox.exists():
        return []
    refs: List[BundleRef] = []
    for entry in sorted(inbox.iterdir()):
        if entry.is_dir():
            continue
        m = KERNEL_BUNDLE_RE.match(entry.name)
        if not m:
            continue
        ref = BundleRef(entry, m.group("bundle_id"), m.group("absorb_ts"))
        ref.load_metadata()
        refs.append(ref)
    return refs


def scan_instance_outbox(instance_root: Path) -> List[BundleRef]:
    """Inventory a downstream instance's outbox (used by absorb)."""
    outbox = instance_outbox_path(instance_root)
    if not outbox.exists():
        raise UpstreamError(
            f"Instance outbox not found: {outbox}. "
            "If the instance uses a non-default path or the kernel session "
            "has no access, follow the Courier Fallback flow in "
            "docs/agent_protocol.md §8."
        )
    refs: List[BundleRef] = []
    for entry in sorted(outbox.iterdir()):
        if entry.is_dir():
            continue
        m = OUTBOX_BUNDLE_RE.match(entry.name)
        if not m:
            continue
        ref = BundleRef(entry, m.group("bundle_id"))
        ref.load_metadata()
        refs.append(ref)
    return refs


# ---------------------------------------------------------------------------
# Absorb (instance outbox → kernel inbox, content-addressable filename)
# ---------------------------------------------------------------------------

def absorb_from_instance(root: Path,
                          instance_path: Path) -> List[BundleRef]:
    """Copy all bundles from instance outbox into kernel inbox.

    Does NOT delete from instance side. The instance agent is expected
    to clear its outbox in a separate chore commit after receiving
    confirmation from the kernel session. This two-side acknowledgement
    keeps the absorb operation idempotent-ish (re-running will see the
    same bundle_ids, and the kernel inbox will reject duplicates by
    bundle_id when ABSORBED_SUBDIR already contains them).

    Returns the list of newly-absorbed bundle refs (not including
    duplicates that were skipped).

    Raises UpstreamError if instance outbox is unreachable.
    """
    instance_path = Path(instance_path).resolve()
    if not instance_path.exists():
        raise UpstreamError(
            f"Instance path does not exist: {instance_path}. "
            "For cross-project transport without a shared mount, see the "
            "Courier Fallback flow in docs/agent_protocol.md §8."
        )
    outbox_refs = scan_instance_outbox(instance_path)
    if not outbox_refs:
        return []

    inbox = _ensure_kernel_inbox(root)
    absorbed_dir = kernel_absorbed_path(root)

    # Collect all bundle_ids already seen on kernel side (pending or
    # absorbed) so absorb is safe to re-run.
    seen_ids = set()
    for entry in inbox.iterdir():
        if entry.is_file():
            m = KERNEL_BUNDLE_RE.match(entry.name)
            if m:
                seen_ids.add(m.group("bundle_id"))
    if absorbed_dir.exists():
        for entry in absorbed_dir.iterdir():
            if entry.is_file():
                m = KERNEL_BUNDLE_RE.match(entry.name)
                if m:
                    seen_ids.add(m.group("bundle_id"))

    absorb_ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    new_refs: List[BundleRef] = []
    for ref in outbox_refs:
        if ref.bundle_id in seen_ids:
            continue
        ext = ref.path.suffix.lstrip(".")
        dest_name = f"{absorb_ts}_{ref.bundle_id}.bundle.{ext}"
        dest = inbox / dest_name
        shutil.copy2(ref.path, dest)
        new_ref = BundleRef(dest, ref.bundle_id, absorb_ts)
        new_ref.load_metadata()
        new_refs.append(new_ref)
    return new_refs


# ---------------------------------------------------------------------------
# Ingest (kernel inbox bundle → pointer note + archive to absorbed/)
# ---------------------------------------------------------------------------

def ingest_bundle(root: Path, bundle_id: str) -> Path:
    """Create a pointer note for a bundle and archive the bundle body.

    Never rewrites the bundle as a note. The pointer note carries:
        source: upstream_absorbed
        tags:   upstream-bundle, source-project-<X>, <severity>-severity,
                kernel-<target-component>
        body:   bundle.summary first paragraph + link to the evidence file
    The bundle YAML itself moves from `<inbox>/` to `<inbox>/absorbed/`
    as audit evidence. Future `myco upstream scan` will no longer list it.
    """
    inbox = kernel_inbox_path(root)
    if not inbox.exists():
        raise UpstreamError(f"Kernel inbox not found: {inbox}")

    # Locate the pending bundle by bundle_id (ignore extension differences).
    candidates: List[Path] = []
    for entry in inbox.iterdir():
        if not entry.is_file():
            continue
        m = KERNEL_BUNDLE_RE.match(entry.name)
        if m and m.group("bundle_id") == bundle_id:
            candidates.append(entry)
    if not candidates:
        raise UpstreamError(
            f"No pending bundle with id {bundle_id!r} in {inbox}. "
            "Already ingested? Check .myco_upstream_inbox/absorbed/."
        )
    if len(candidates) > 1:
        raise UpstreamError(
            f"Ambiguous bundle id {bundle_id!r}; multiple matches: "
            + ", ".join(c.name for c in candidates)
        )
    bundle_path = candidates[0]

    ref = BundleRef(bundle_path, bundle_id,
                    KERNEL_BUNDLE_RE.match(bundle_path.name).group("absorb_ts"))
    ref.load_metadata()

    # Archive first, then create the pointer note. We archive first so
    # that the pointer note's source_ref points at the canonical archived
    # path (not the transient inbox path).
    absorbed_dir = kernel_absorbed_path(root)
    absorbed_dir.mkdir(exist_ok=True)
    archived = absorbed_dir / bundle_path.name
    shutil.move(str(bundle_path), str(archived))

    rel_ref = str(archived.relative_to(Path(root)))

    # Build pointer note body.
    summary_line = ref.short_summary(width=160) or "(no summary)"
    lines = [
        f"**Upstream friction absorbed** — pointer note for bundle "
        f"`{bundle_id}`.",
        "",
        f"- source_project: `{ref.source_project or 'unknown'}`",
        f"- target_kernel_component: `{ref.target_kernel_component or 'unknown'}`",
        f"- severity: `{ref.severity or 'unknown'}`",
        f"- evidence: `{rel_ref}`",
        "",
        "**Summary**",
        "",
        summary_line,
        "",
        "See the evidence file for the full structured bundle (proposed "
        "fixes, workaround applied, downstream impact). This note is a "
        "*pointer* — it exists so the bundle can enter the 7-step "
        "metabolism without losing its structured form.",
    ]
    body = "\n".join(lines)

    tags = ["upstream-bundle"]
    if ref.source_project:
        tags.append(f"source-project-{_slugify(ref.source_project)}")
    if ref.severity:
        tags.append(f"{_slugify(ref.severity)}-severity")
    if ref.target_kernel_component:
        tags.append(f"kernel-{_slugify(ref.target_kernel_component)}")

    note_path = write_note(
        Path(root), body,
        tags=tags,
        source="upstream_absorbed",
        status="raw",
        title=f"Upstream: {summary_line[:60]}",
    )
    return note_path


def _slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "unknown"


# ---------------------------------------------------------------------------
# Pressure indicator
# ---------------------------------------------------------------------------

def compute_upstream_inbox_pressure(root: Path,
                                     ceiling: int = DEFAULT_INBOX_CEILING
                                     ) -> float:
    """Return the current upstream_inbox_pressure value in [0, 1].

    Pressure = pending bundle count / ceiling, clamped to 1.0.
    Bootstrap value when inbox is absent or empty = 0.0.
    """
    pending = scan_kernel_inbox(Path(root))
    if ceiling <= 0:
        return 0.0
    raw = len(pending) / float(ceiling)
    return min(raw, 1.0)
