"""``myco germinate`` — one-shot substrate bootstrap.

v0.5.3 renamed ``genesis`` → ``germinate`` (spore germination starts
the fungal colony). The legacy ``myco genesis`` invocation still
works via a manifest alias; the shim package ``myco.genesis``
re-exports this module.

Governing doc: ``docs/architecture/L2_DOCTRINE/genesis.md`` (the
file keeps its v0.4 filename until the next doctrine-file pass;
the content refers to the new verb name).
Craft: ``docs/primordia/stage_b3_genesis_craft_2026-04-15.md``.

Germinate creates a minimal, lint-clean substrate skeleton from
scratch. It is invoked exactly once per project lifetime. Re-
running it on an established substrate raises ``ContractError``.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from importlib.resources import files as _pkg_files
from pathlib import Path
from string import Template

from myco.core.context import Result
from myco.core.errors import ContractError, UsageError

__all__ = [
    "bootstrap",
    "run_cli",
    "DEFAULT_CONTRACT_VERSION",
    "DEFAULT_ENTRY_POINT",
]

#: Contract version stamped into freshly-authored canons. Surface layer
#: (Stage B.7) may override via CLI flag; the default is the SSoT.
DEFAULT_CONTRACT_VERSION: str = "v0.4.0-alpha.1"

#: Default agent-entry filename. Symbiont substrates (e.g. ASCC under
#: Claude Code) may override via the ``entry_point`` argument to match
#: the host tooling's expectation (``CLAUDE.md``).
DEFAULT_ENTRY_POINT: str = "MYCO.md"

#: Slug-like pattern for substrate ids. Mixed case allowed (to match
#: real-world names like ``ASCC-research``); whitespace and leading
#: digit/punct rejected.
_SUBSTRATE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")


def bootstrap(
    *,
    project_dir: Path,
    substrate_id: str,
    tags: Sequence[str] = (),
    entry_point: str = DEFAULT_ENTRY_POINT,
    contract_version: str = DEFAULT_CONTRACT_VERSION,
    dry_run: bool = False,
    now: datetime | None = None,
) -> Result:
    """Create the initial substrate state at ``project_dir``.

    On success (``dry_run=False``), the following are written:

    - ``_canon.yaml`` at the root (from ``templates/canon.yaml.tmpl``).
    - ``.myco_state/autoseeded.txt`` marker (enables skeleton-mode
      severity downgrade in homeostasis).
    - ``notes/`` and ``docs/`` directories (created only if missing;
      pre-existing non-empty directories are left untouched).
    - The entry-point file (``MYCO.md`` by default).

    Returns a :class:`Result` whose payload carries:

    - ``files_created``: tuple of relative paths written.
    - ``preview``: mapping of relative path → rendered content
      (populated regardless of ``dry_run`` so callers can diff).
    - ``dry_run``: bool.
    - ``project_dir``: resolved path.
    - ``substrate_id``: the slug.

    Raises:
        UsageError: if ``substrate_id`` is not a valid slug.
        ContractError: if the substrate already exists (canon present,
            or partial genesis state).
    """
    if not _SUBSTRATE_ID_RE.match(substrate_id):
        raise UsageError(
            f"invalid substrate_id {substrate_id!r}: must match "
            f"[A-Za-z][A-Za-z0-9_-]{{0,63}}"
        )

    project_dir = project_dir.resolve()
    if not project_dir.exists():
        raise UsageError(f"project_dir does not exist: {project_dir}")
    if not project_dir.is_dir():
        raise UsageError(f"project_dir is not a directory: {project_dir}")

    canon_path = project_dir / "_canon.yaml"
    state_dir = project_dir / ".myco_state"
    marker_path = state_dir / "autoseeded.txt"
    entry_path = project_dir / entry_point

    # Refuse on existing substrate / partial state.
    if canon_path.exists():
        raise ContractError(
            f"substrate already exists at {project_dir} "
            f"(_canon.yaml present); genesis is one-shot"
        )
    if marker_path.exists():
        raise ContractError(
            f"partial genesis state at {project_dir}: "
            f".myco_state/autoseeded.txt exists without _canon.yaml; "
            f"resolve manually before rerunning genesis"
        )
    if entry_path.exists():
        raise ContractError(
            f"entry-point {entry_path.name!r} already exists at "
            f"{project_dir}; refusing to clobber"
        )

    now = now or datetime.now(timezone.utc)
    generated_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    canon_text = _render_canon(
        substrate_id=substrate_id,
        tags=tuple(tags),
        entry_point=entry_point,
        contract_version=contract_version,
        generated_at=generated_at,
    )
    entry_text = _render_entry_point(
        substrate_id=substrate_id,
        entry_point=entry_point,
        generated_at=generated_at,
    )
    marker_text = (
        f"autoseeded by myco genesis at {generated_at}\nsubstrate_id={substrate_id}\n"
    )

    preview: dict[str, str] = {
        "_canon.yaml": canon_text,
        entry_point: entry_text,
        ".myco_state/autoseeded.txt": marker_text,
    }

    files_created: tuple[str, ...] = ()
    if not dry_run:
        # Directories first.
        state_dir.mkdir(exist_ok=True)
        (project_dir / "notes").mkdir(exist_ok=True)
        (project_dir / "docs").mkdir(exist_ok=True)
        # Files.
        canon_path.write_text(canon_text, encoding="utf-8")
        entry_path.write_text(entry_text, encoding="utf-8")
        marker_path.write_text(marker_text, encoding="utf-8")
        files_created = (
            "_canon.yaml",
            entry_point,
            ".myco_state/autoseeded.txt",
        )

    return Result(
        exit_code=0,
        findings=(),
        payload={
            "files_created": files_created,
            "preview": preview,
            "dry_run": dry_run,
            "project_dir": str(project_dir),
            "substrate_id": substrate_id,
        },
    )


# --- template rendering ---------------------------------------------------


def _load_template(name: str) -> str:
    """Read a template asset from ``myco.germination.templates``."""
    pkg = _pkg_files("myco.germination.templates")
    return (pkg / name).read_text(encoding="utf-8")


def _yaml_flow_list(items: Sequence[str]) -> str:
    """Render a Python sequence as a YAML flow-style list.

    Empty input renders as ``[]``; non-empty as ``["a", "b"]``. Entries
    are strict-quoted and double-quotes inside entries are escaped.
    """
    if not items:
        return "[]"
    parts = [
        f'"{str(x).replace(chr(92), chr(92) * 2).replace(chr(34), chr(92) + chr(34))}"'
        for x in items
    ]
    return "[" + ", ".join(parts) + "]"


def _render_canon(
    *,
    substrate_id: str,
    tags: Sequence[str],
    entry_point: str,
    contract_version: str,
    generated_at: str,
) -> str:
    tmpl = Template(_load_template("canon.yaml.tmpl"))
    return tmpl.substitute(
        substrate_id=substrate_id,
        tags_flow=_yaml_flow_list(tags),
        entry_point=entry_point,
        contract_version=contract_version,
        generated_at=generated_at,
    )


def _render_entry_point(
    *,
    substrate_id: str,
    entry_point: str,
    generated_at: str,
) -> str:
    # Title stems from the filename without extension, uppercased.
    stem = Path(entry_point).stem or entry_point
    title = stem.upper()
    tmpl = Template(_load_template("entry_point.md.tmpl"))
    return tmpl.substitute(
        entry_point_title=title,
        substrate_id=substrate_id,
        generated_at=generated_at,
    )


def run_cli(args: Mapping[str, object]) -> Result:
    """Manifest-shaped handler for ``myco genesis``.

    Genesis predates the substrate, so this handler deliberately does
    not accept a ``ctx``; the :mod:`myco.surface.manifest` dispatcher
    short-circuits context construction for ``pre_substrate`` verbs.
    """
    project_dir_raw = args.get("project_dir")
    if project_dir_raw is None:
        raise UsageError("genesis requires --project-dir")
    substrate_id = str(args.get("substrate_id") or "")
    if not substrate_id:
        raise UsageError("genesis requires --substrate-id")
    tags_raw = args.get("tags") or ()
    tags = (
        tuple(str(t) for t in tags_raw) if isinstance(tags_raw, (list, tuple)) else ()
    )
    entry_point = str(args.get("entry_point") or DEFAULT_ENTRY_POINT)
    dry_run = bool(args.get("dry_run", False))
    return bootstrap(
        project_dir=Path(str(project_dir_raw)),
        substrate_id=substrate_id,
        tags=tags,
        entry_point=entry_point,
        dry_run=dry_run,
    )
