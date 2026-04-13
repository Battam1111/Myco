"""Atomic-write helpers for the substrate.

**Wave 30 (kernel_contract, contract v0.26.0)**: introduces `atomic_write_text`
and `atomic_write_yaml` as the substrate's first general-purpose atomic-write
helpers. Created as a declared dependency of `myco compress` (per Wave 27 D8 +
Wave 30 craft §3.1) — `compress` is a multi-file mutation that must be
all-or-nothing across N input notes + 1 output note.

**Why this module exists** (hermes catalog C2 — atomic writes):

The compress operation writes one new extracted note AND mutates N input notes
(flips status → excreted + adds back-reference frontmatter). If any single write
fails midway through, the substrate is left in a torn state: the output note
exists but some inputs are not yet excreted, OR some inputs are excreted but
the output is missing. Both shapes are corrupt — agents reading the substrate
between writes would see internally-inconsistent compression metadata.

The standard way to make a single file write atomic on POSIX-compatible
filesystems (including modern Windows) is **temp-file + rename**:

  1. Write the new content to a sibling temp file in the same directory
  2. Call `os.replace(tmp, target)` — POSIX guarantees this is atomic
  3. Either the old content or the new content is visible at `target`,
     never partial content

For multi-file atomicity (the compress case), the helper here is
**single-file atomic only**. Multi-file atomicity is achieved at a higher
level by `compress_cmd.py` via the **two-phase commit** pattern:

  Phase 1: write all new files + new content for mutated files to temp paths.
           If any phase-1 write fails, delete all temp files and abort.
  Phase 2: rename all temp paths to their final targets. Renames are
           almost always successful when phase-1 succeeded, so phase 2
           usually completes. If a phase-2 rename fails, log a warning —
           the substrate is in a torn state and requires manual recovery.

This is **best-effort atomicity**, not transactional. True multi-file
transactional atomicity requires fsync discipline + filesystem-level
journaling that Myco does not implement. The two-phase commit is enough
to make crash-during-compress recoverable in practice.

**Module surface** (intentionally minimal — Wave 30 ships only what
`myco compress` needs; future waves can extend as friction demands):

  - `atomic_write_text(path, text, *, encoding="utf-8")` — write str → file
  - `atomic_write_yaml(path, data)` — write dict → YAML file via PyYAML

**Not in Wave 30 scope**:

  - General-purpose retrofit of `notes.py::write_note`, `forage.py::add_item`,
    etc. Those file writers stay as-is and may be retrofitted as friction demands. The
    surface here is small enough that future retrofits can copy the pattern
    without depending on this module.
  - File locking (concurrent-write coordination). The substrate is single-
    user single-session by design; locking is a non-goal until proven
    necessary. The two-phase commit's snapshot-cohort design handles
    concurrent `myco eat` calls during compress (the snapshot is taken
    before any writes, so a concurrent eat just becomes part of the next
    compression run).
  - fsync flushes. POSIX `os.replace` is atomic but does not guarantee
    durability on system crash before the kernel flushes its page cache.
    Adding fsync would slow compress noticeably and is unjustified for
    Myco's single-user trust model.

**Authoritative craft**: docs/primordia/compress_mvp_craft_2026-04-12.md
(Wave 30, kernel_contract, 0.90).

**Lineage**: hermes catalog C2 (forage/repos/hermes-agent atomic-write helper),
absorbed in Wave 25 hermes_absorption_craft, declared as Wave 30 dependency
in Wave 27 D8.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Union

try:
    import yaml
except ImportError:  # pragma: no cover — PyYAML is a hard dep elsewhere
    yaml = None


def atomic_write_text(
    path: Union[str, Path],
    text: str,
    *,
    encoding: str = "utf-8",
) -> Path:
    """Atomically write `text` to `path` via temp-file + rename.

    Guarantees: either the OLD content or the NEW content is visible at
    `path` at all times. Never partial content. Crash-safe to the extent
    that POSIX `os.replace` is atomic on the local filesystem.

    Implementation:
      1. Create a NamedTemporaryFile in the SAME directory as `path` (so
         the rename stays on one filesystem — cross-fs renames degrade to
         copy+delete and lose atomicity).
      2. Write the text + flush.
      3. Call `os.replace(tmp, target)` — atomic on POSIX and modern
         Windows (Python 3.3+ uses MoveFileExW with replacement semantics).

    Returns the final `Path` on success. Raises on any IO error after
    cleaning up the temp file.

    Wave 30 (v0.26.0) — added as a declared dependency of `myco compress`
    per the Wave 27 design craft §3.1 + the Wave 30 implementation craft
    §2.2 atomicity requirements.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    # NamedTemporaryFile in same dir keeps rename on one filesystem.
    # delete=False because we manage cleanup ourselves around os.replace.
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=str(target.parent),
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="") as f:
            f.write(text)
            # No fsync — Myco's single-user trust model accepts the small
            # window between successful write and OS page-cache flush.
            # See module docstring for the rationale.
        # os.replace is atomic on POSIX and Python 3.3+ Windows.
        os.replace(str(tmp_path), str(target))
    except Exception:
        # Cleanup the orphan temp before bubbling the exception up.
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass
        raise
    return target


def atomic_write_yaml(
    path: Union[str, Path],
    data: Dict[str, Any],
) -> Path:
    """Atomically write a dict as YAML to `path`.

    Convenience wrapper over `atomic_write_text` that serializes via PyYAML
    with stable, diff-friendly formatting (sort_keys=False, allow_unicode,
    block style).

    Used by `myco compress` for any future YAML output (e.g. compression
    audit sidecars). Wave 30 itself only writes Markdown notes via the
    text helper, but ships the YAML helper for completeness so consumers
    don't have to reach into PyYAML directly.

    Raises `RuntimeError` if PyYAML is not installed (matches the rest
    of the substrate, where PyYAML is a hard dependency).
    """
    if yaml is None:
        raise RuntimeError(
            "PyYAML is required for atomic_write_yaml; install via `pip install pyyaml`"
        )
    text = yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
    return atomic_write_text(path, text)
