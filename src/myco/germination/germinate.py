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

#: Default agent-entry filename. Symbiont substrates (e.g. ASCC under
#: Claude Code) may override via the ``entry_point`` argument to match
#: the host tooling's expectation (``CLAUDE.md``).
DEFAULT_ENTRY_POINT: str = "MYCO.md"

#: Slug-like pattern for substrate ids. Mixed case allowed (to match
#: real-world names like ``ASCC-research``); whitespace and leading
#: digit/punct rejected.
_SUBSTRATE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")

#: Windows reserved filesystem names (case-insensitive). Writing to
#: these paths silently black-holes content (Windows redirects them to
#: device files). Reject in ``_validate_entry_point`` and in
#: substrate_id validation.
_WINDOWS_RESERVED: frozenset[str] = frozenset(
    name.upper()
    for name in (
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5",
        "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5",
        "LPT6", "LPT7", "LPT8", "LPT9",
    )
)


def _resolve_default_contract_version() -> str:
    """Return the contract-version string freshly-germinated substrates
    should stamp.

    v0.5.8 fix: reads ``myco.__version__`` at call time (not at import
    time) so a substrate germinated by kernel vX.Y.Z gets
    ``contract_version: vX.Y.Z`` instead of the previous hard-coded
    ``v0.4.0-alpha.1`` stamp. Previously every new substrate was born
    6+ versions stale and never triggered drift detection.
    """
    from myco import __version__ as _myco_version
    return f"v{_myco_version}"


def _is_windows_reserved(name: str) -> bool:
    """Return True if ``name`` (bare filename, no extension) is a
    Windows reserved device name. Matches case-insensitively; also
    matches ``CON.md`` (stem is ``CON``)."""
    stem = Path(name).stem if "." in name else name
    return stem.upper() in _WINDOWS_RESERVED


# Back-compat public alias. ``DEFAULT_CONTRACT_VERSION`` is consumed
# by a few tests + legacy callers; they now get the live-resolved
# value on every access.
class _ContractVersionDescriptor:
    """Module-level descriptor so ``from myco.germination import
    DEFAULT_CONTRACT_VERSION`` returns the live value, not a cached
    import-time constant."""

    def __repr__(self) -> str:
        return _resolve_default_contract_version()

    def __str__(self) -> str:
        return _resolve_default_contract_version()

    def __eq__(self, other: object) -> bool:
        return str(self) == other

    def __hash__(self) -> int:
        return hash(str(self))


# Expose a module-level string-like sentinel. Most callers that read
# this value immediately stringify; the descriptor supports that.
# NOTE: callers that compare `foo == DEFAULT_CONTRACT_VERSION` get the
# expected equality via the dunder.
DEFAULT_CONTRACT_VERSION = _ContractVersionDescriptor()


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
    if _is_windows_reserved(substrate_id):
        raise UsageError(
            f"substrate_id {substrate_id!r} is a Windows reserved "
            f"filesystem name (CON/PRN/AUX/NUL/COM1-9/LPT1-9). "
            f"Pick a different id."
        )

    # v0.5.8 P0 FIX: validate entry-point path safety + Windows
    # reserved names. Path traversal via "../../evil" and reserved
    # stems like "CON.md" silently black-hole on Windows.
    _ep = Path(entry_point)
    if (
        _ep.is_absolute()
        or ".." in _ep.parts
        or "/" in entry_point
        or "\\" in entry_point
    ):
        raise UsageError(
            f"invalid entry_point {entry_point!r}: must be a single "
            f"filename (no path separators, no parent-dir traversal)"
        )
    if _is_windows_reserved(entry_point):
        raise UsageError(
            f"entry_point {entry_point!r} is a Windows reserved "
            f"filesystem name (CON/PRN/AUX/NUL/COM1-9/LPT1-9). "
            f"Pick a different filename."
        )

    # v0.5.8 P0 FIX: resolve project_dir safely (previously raised
    # uncaught PermissionError on restricted paths like ``/``). We try
    # to create it (idempotently) then validate. If the OS refuses
    # access the user gets a clean UsageError, not a raw traceback.
    try:
        project_dir.mkdir(parents=True, exist_ok=True)
        project_dir = project_dir.resolve()
    except PermissionError as exc:
        raise UsageError(
            f"cannot access project_dir {project_dir}: permission "
            f"denied ({exc}). Pick a writable location."
        ) from exc
    except OSError as exc:
        raise UsageError(
            f"cannot prepare project_dir {project_dir}: {exc}"
        ) from exc
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
        f"autoseeded by myco germinate at {generated_at}\nsubstrate_id={substrate_id}\n"
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
