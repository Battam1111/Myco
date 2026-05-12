"""``python -m myco.mcp`` legacy entry point (v0.6.13+).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/boundary.md``.

Back-compat redirect to :func:`myco.boundary.mcp.main`. Importing
this module triggers the stderr deprecation pointer in
``myco/mcp/__init__.py``; we then delegate the actual server boot
to the canonical entry point so behaviour is byte-identical to
``python -m myco.boundary.mcp``.

See ``myco.mcp.__init__`` docstring for the full migration
rationale and removal schedule.

v0.7.2 telemetry hook (MB8 dim): record one JSONL line per CLI
invocation in ``.myco/state/shim_hits.json`` so the substrate has a
mechanically-verifiable signal for safe shim retirement (the
v0.7.1-named telemetry path of the public-API-deletion discipline).
The write is best-effort and try-except wrapped: read-only
substrates (CI snapshots, container rootfs, sandbox MCP hosts) MUST
NOT fail to boot the MCP server because of telemetry. v0.7.0 lesson.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# The import below triggers ``myco.mcp.__init__`` which emits the
# deprecation pointer to stderr exactly once per process spawn.
from myco.mcp import main


def _record_shim_hit() -> None:
    """Append one telemetry line to ``.myco/state/shim_hits.json``.

    Substrate root resolution (best-effort, in priority order):

    1. ``MYCO_PROJECT_DIR`` env var (per the multi-project hint at
       ``MYCO.md`` and the pulse `kwargs.project_dir` resolution chain).
    2. cwd (the directory the user spawned ``python -m myco.mcp`` from).

    If neither resolves to a directory containing ``_canon.yaml``,
    silently no-op — the shim still boots; we just lose this hit.
    Telemetry is best-effort; the substrate MUST always boot.
    """
    try:
        candidates = []
        env_dir = os.environ.get("MYCO_PROJECT_DIR")
        if env_dir:
            candidates.append(Path(env_dir))
        candidates.append(Path.cwd())
        substrate_root: Path | None = None
        for c in candidates:
            try:
                if (c / "_canon.yaml").is_file():
                    substrate_root = c
                    break
            except OSError:
                continue
        if substrate_root is None:
            return
        state_dir = substrate_root / ".myco/state"
        state_dir.mkdir(parents=True, exist_ok=True)
        hits_path = state_dir / "shim_hits.json"
        record = {
            "module": "myco.mcp",
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "session_id": str(uuid.uuid4()),
        }
        # Append-only JSONL: each line is one record. Race-safe under
        # POSIX append semantics; on Windows the GIL + small write
        # serialize concurrent invocations adequately for telemetry.
        with hits_path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:  # pragma: no cover - best-effort telemetry
        # Never raise from the shim's telemetry path. Read-only
        # substrate, missing canon, locked file, etc. all silent-fail.
        return


if __name__ == "__main__":  # pragma: no cover
    _record_shim_hit()
    sys.exit(main())
