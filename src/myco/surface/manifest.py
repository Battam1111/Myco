"""Command manifest loader + dispatcher.

Governing doctrine: ``docs/architecture/L3_IMPLEMENTATION/command_manifest.md``
(the canonical verb surface declaration).

Reads ``manifest.yaml`` from the package resources, validates each
entry against a small schema, resolves each ``handler`` into an
importable callable, and exposes:

- :class:`Manifest`: typed view of the manifest contents.
- :func:`load_manifest`: load + validate (cached).
- :func:`build_context`: construct a :class:`MycoContext` for a given
  invocation (discovers the substrate root unless the verb is
  ``pre_substrate``).
- :func:`dispatch`: run a verb by name with a dict of args and return
  the handler's :class:`Result`.

Arg naming convention:

- Manifest authors write dash-case names (``project-dir``).
- Runtime handler dicts receive snake_case keys (``project_dir``).
- Argparse flags are ``--dash-case``; MCP tool params are snake_case.
"""

from __future__ import annotations

import importlib
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from importlib.resources import files as _pkg_files
from pathlib import Path
from typing import Any

import yaml

from myco.core.context import MycoContext, Result
from myco.core.errors import (
    ContractError,
    SubstrateNotFound,
    UsageError,
)
from myco.core.substrate import Substrate, find_substrate_root

__all__ = [
    "ArgSpec",
    "CommandSpec",
    "Manifest",
    "load_manifest",
    "load_manifest_with_overlay",
    "build_context",
    "dispatch",
    "dash_to_snake",
]


_VALID_TYPES: frozenset[str] = frozenset({"str", "bool", "int", "path", "list[str]"})


def dash_to_snake(name: str) -> str:
    """Convert dash-cased ``name`` to snake_case (manifest arg name adapter)."""
    return name.replace("-", "_")


@dataclass(frozen=True)
class ArgSpec:
    """Typed view of a single manifest arg."""

    name: str  # dash-case
    type: str
    required: bool = False
    default: Any = None
    help: str = ""

    @property
    def snake(self) -> str:
        return dash_to_snake(self.name)

    def coerce(self, raw: Any) -> Any:
        """Coerce ``raw`` to this arg's declared type."""
        if raw is None:
            return None
        t = self.type
        if t == "str":
            return str(raw)
        if t == "bool":
            if isinstance(raw, bool):
                return raw
            if isinstance(raw, str):
                return raw.lower() in {"1", "true", "yes", "on"}
            return bool(raw)
        if t == "int":
            return int(raw)
        if t == "path":
            return Path(str(raw))
        if t == "list[str]":
            if isinstance(raw, (list, tuple)):
                return tuple(str(x) for x in raw)
            if isinstance(raw, str):
                return (raw,)
            raise UsageError(
                f"arg {self.name!r}: expected list[str], got {type(raw).__name__}"
            )
        raise ContractError(f"unknown arg type {t!r} for {self.name!r}")


@dataclass(frozen=True)
class CommandSpec:
    """Typed view of a single manifest command."""

    name: str
    subsystem: str
    handler: str  # "module:function"
    summary: str
    mcp_tool: str
    args: tuple[ArgSpec, ...] = ()
    pre_substrate: bool = False
    #: Deprecated aliases. Invoking any of these resolves to this
    #: canonical command and emits a ``DeprecationWarning`` once per
    #: alias per process. Added at v0.5.3 for the fungal-vocabulary
    #: migration; aliases are scheduled to be removed at v1.0.0.
    aliases: tuple[str, ...] = ()
    #: Deprecated MCP tool names. Same story as ``aliases`` but for
    #: the MCP surface — new MCP clients use ``mcp_tool``; old
    #: clients still see the legacy name.
    mcp_tool_aliases: tuple[str, ...] = ()

    def resolve_handler(self) -> Callable[..., Result]:
        """Import and return the handler callable."""
        if ":" not in self.handler:
            raise ContractError(
                f"handler for {self.name!r} must be 'module:function', "
                f"got {self.handler!r}"
            )
        module_name, func_name = self.handler.split(":", 1)
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            raise ContractError(
                f"handler module for {self.name!r} not importable: {module_name}"
            ) from exc
        func = getattr(module, func_name, None)
        if func is None or not callable(func):
            raise ContractError(
                f"handler for {self.name!r} not found or not callable: {self.handler}"
            )
        return func


@dataclass(frozen=True)
class Manifest:
    """Parsed command manifest."""

    schema_version: str
    commands: tuple[CommandSpec, ...] = field(default_factory=tuple)

    def by_name(self, name: str) -> CommandSpec:
        """Resolve ``name`` to a CommandSpec.

        Matches canonical ``name`` first, then ``aliases`` (emitting
        a ``DeprecationWarning`` once per alias per process). Raises
        :class:`UsageError` for any name that matches neither.
        """
        for c in self.commands:
            if c.name == name:
                return c
        for c in self.commands:
            if name in c.aliases:
                _warn_alias(name, c.name)
                return c
        raise UsageError(f"unknown command: {name!r}")

    def names(self) -> tuple[str, ...]:
        """Return the canonical verb names (aliases excluded)."""
        return tuple(c.name for c in self.commands)

    def all_names_including_aliases(self) -> tuple[str, ...]:
        """Every invokable verb (canonical + alias). Used by the CLI
        parser so legacy invocations still surface in ``--help``
        (marked as deprecated)."""
        out: list[str] = []
        for c in self.commands:
            out.append(c.name)
            out.extend(c.aliases)
        return tuple(out)


_ALIAS_WARNED: set[str] = set()


def _warn_alias(alias: str, canonical: str) -> None:
    """Emit a one-shot DeprecationWarning for an aliased verb.

    Cached per alias per process so a long-running MCP server does
    not spam warnings on every tool call.
    """
    import warnings as _w

    if alias in _ALIAS_WARNED:
        return
    _ALIAS_WARNED.add(alias)
    _w.warn(
        f"myco verb {alias!r} is a deprecated alias for {canonical!r}; "
        f"both work across v0.5.x and v0.6.x but the alias is "
        f"scheduled for removal at v1.0.0. Migrate at your leisure.",
        DeprecationWarning,
        stacklevel=3,
    )


def _parse_command(raw: Mapping[str, Any]) -> CommandSpec:
    for required in ("name", "subsystem", "handler", "summary", "mcp_tool"):
        if required not in raw:
            raise ContractError(f"manifest command missing {required!r}: {raw}")
    args_raw = raw.get("args") or ()
    if not isinstance(args_raw, (list, tuple)):
        raise ContractError(f"manifest command {raw['name']!r}: args must be a list")
    args: list[ArgSpec] = []
    for a in args_raw:
        if not isinstance(a, Mapping):
            raise ContractError(
                f"manifest command {raw['name']!r}: arg must be a mapping"
            )
        if "name" not in a or "type" not in a:
            raise ContractError(
                f"manifest command {raw['name']!r}: arg missing name or type"
            )
        if a["type"] not in _VALID_TYPES:
            raise ContractError(
                f"manifest command {raw['name']!r}: "
                f"arg {a['name']!r} has unknown type {a['type']!r}"
            )
        args.append(
            ArgSpec(
                name=str(a["name"]),
                type=str(a["type"]),
                required=bool(a.get("required", False)),
                default=a.get("default"),
                help=str(a.get("help", "")),
            )
        )
    aliases_raw = raw.get("aliases") or ()
    if not isinstance(aliases_raw, (list, tuple)):
        raise ContractError(f"manifest command {raw['name']!r}: aliases must be a list")
    mcp_aliases_raw = raw.get("mcp_tool_aliases") or ()
    if not isinstance(mcp_aliases_raw, (list, tuple)):
        raise ContractError(
            f"manifest command {raw['name']!r}: mcp_tool_aliases must be a list"
        )
    return CommandSpec(
        name=str(raw["name"]),
        subsystem=str(raw["subsystem"]),
        handler=str(raw["handler"]),
        summary=str(raw["summary"]),
        mcp_tool=str(raw["mcp_tool"]),
        args=tuple(args),
        pre_substrate=bool(raw.get("pre_substrate", False)),
        aliases=tuple(str(a) for a in aliases_raw),
        mcp_tool_aliases=tuple(str(a) for a in mcp_aliases_raw),
    )


@lru_cache(maxsize=1)
def load_manifest() -> Manifest:
    """Load + validate the bundled ``manifest.yaml``."""
    text = (
        _pkg_files("myco.surface").joinpath("manifest.yaml").read_text(encoding="utf-8")
    )
    try:
        raw = yaml.safe_load(text) or {}
    except yaml.YAMLError as exc:
        raise ContractError(f"manifest.yaml is not valid YAML: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise ContractError("manifest.yaml top level must be a mapping")
    schema_version = str(raw.get("schema_version", ""))
    if schema_version != "1":
        raise ContractError(f"unknown manifest schema_version: {schema_version!r}")
    commands_raw = raw.get("commands") or ()
    if not isinstance(commands_raw, (list, tuple)):
        raise ContractError("manifest commands must be a list")
    commands = tuple(_parse_command(c) for c in commands_raw)
    names = [c.name for c in commands]
    if len(names) != len(set(names)):
        raise ContractError(f"manifest has duplicate command names: {sorted(names)}")
    # Check aliases do not collide with any canonical name or any
    # other alias — the dispatcher has to deterministically route a
    # single token to a single handler.
    all_names: dict[str, str] = {n: n for n in names}
    for c in commands:
        for a in c.aliases:
            if a in all_names:
                raise ContractError(
                    f"manifest alias {a!r} collides with existing verb {all_names[a]!r}"
                )
            all_names[a] = c.name
    return Manifest(schema_version=schema_version, commands=commands)


def load_manifest_with_overlay(
    substrate_root: Path | None,
) -> Manifest:
    """Load the packaged manifest and merge in a per-substrate overlay.

    v0.5.3 substrate-local plugin contract: a downstream substrate may
    ship ``<root>/.myco/manifest_overlay.yaml`` declaring extra verbs
    that the local plugins subpackage implements. This function:

    1. Reads the packaged manifest via :func:`load_manifest` (unchanged,
       still ``@lru_cache``'d).
    2. If ``substrate_root`` is ``None`` or the overlay file is missing,
       returns the packaged manifest unmodified.
    3. Otherwise parses the overlay, validates shape, and concatenates
       the overlay commands. Overlay verb names MUST NOT collide with
       any packaged canonical name OR any packaged alias — a collision
       raises :class:`ContractError` rather than silently shadowing.

    Overlay schema mirrors ``manifest.yaml``: ``commands: [ {name,
    subsystem, handler, summary, mcp_tool, args?, aliases?,
    mcp_tool_aliases?, pre_substrate?} ]``. The ``schema_version`` of
    the overlay is optional but if present must equal ``"1"``.
    """
    base = load_manifest()
    if substrate_root is None:
        return base
    overlay_path = substrate_root / ".myco" / "manifest_overlay.yaml"
    if not overlay_path.is_file():
        return base

    try:
        raw = yaml.safe_load(overlay_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ContractError(
            f"manifest_overlay.yaml is not valid YAML at {overlay_path}: {exc}"
        ) from exc
    if not isinstance(raw, Mapping):
        raise ContractError(
            f"manifest_overlay.yaml top level must be a mapping: {overlay_path}"
        )
    schema_version = raw.get("schema_version")
    if schema_version is not None and str(schema_version) != "1":
        raise ContractError(
            f"manifest_overlay.yaml: unknown schema_version {schema_version!r}"
        )
    commands_raw = raw.get("commands") or ()
    if not isinstance(commands_raw, (list, tuple)):
        raise ContractError("manifest_overlay.yaml: commands must be a list")
    overlay_commands: list[CommandSpec] = []
    for c in commands_raw:
        if not isinstance(c, Mapping):
            raise ContractError(
                "manifest_overlay.yaml: every command entry must be a mapping"
            )
        overlay_commands.append(_parse_command(c))

    # Collision gate: packaged canonical + packaged aliases + already-
    # registered overlay verbs must all be disjoint from any new
    # overlay verb name AND its declared aliases.
    reserved: dict[str, str] = {}
    for c in base.commands:
        reserved[c.name] = c.name
        for a in c.aliases:
            reserved[a] = f"alias of {c.name}"
    for oc in overlay_commands:
        if oc.name in reserved:
            raise ContractError(
                f"overlay verb name {oc.name!r} collides with packaged "
                f"verb {reserved[oc.name]!r}"
            )
        reserved[oc.name] = f"overlay {oc.name}"
        for a in oc.aliases:
            if a in reserved:
                raise ContractError(
                    f"overlay alias {a!r} (for {oc.name!r}) collides "
                    f"with packaged verb {reserved[a]!r}"
                )
            reserved[a] = f"alias of overlay {oc.name}"

    merged = base.commands + tuple(overlay_commands)
    return Manifest(schema_version=base.schema_version, commands=merged)


def build_context(
    *,
    project_dir: Path | None = None,
    pre_substrate: bool = False,
    now: datetime | None = None,
) -> MycoContext | None:
    """Build a :class:`MycoContext` for invocation.

    Returns ``None`` for pre_substrate verbs (genesis); they don't need
    a loaded substrate.

    Substrate resolution chain (highest precedence first):

    1. Explicit ``project_dir`` argument — CLI ``--project-dir`` or
       MCP ``kwargs.project_dir`` lands here. The MCP surface also
       uses ``roots/list`` to fill this in automatically on hosts
       that expose workspace roots (v0.5.14+).
    2. ``MYCO_PROJECT_DIR`` env var — explicit Myco pin. v0.5.13+.
    3. ``CLAUDE_PROJECT_DIR`` env var — Claude Code injects this in
       hook processes (SessionStart, PreCompact, etc.). Reusing it
       means a shared ``~/myco`` + hook setup needs zero Myco-specific
       configuration. v0.5.14+.
    4. ``Path.cwd()`` — legacy behaviour. Claude Code's shell cwd
       flows through this path; nothing breaks for existing setups.

    ``~`` expansion runs on the env-var paths so operators can write
    ``MYCO_PROJECT_DIR=~/project`` without worrying about shell
    expansion on Windows.
    """
    if pre_substrate:
        return None
    if project_dir is None:
        for env_var in ("MYCO_PROJECT_DIR", "CLAUDE_PROJECT_DIR"):
            env_dir = os.environ.get(env_var, "").strip()
            if env_dir:
                project_dir = Path(env_dir).expanduser()
                break
    start = (project_dir or Path.cwd()).resolve()
    try:
        root = find_substrate_root(start)
    except SubstrateNotFound as exc:
        # v0.5.10 fix: re-raise ``SubstrateNotFound`` with the helpful
        # message rather than wrapping in ``UsageError``. The previous
        # wrap silently downgraded exit code 4 → 3 and broke the
        # v0.5.8 contract-promised exit-code differentiation.
        #
        # v0.5.14: error message now enumerates every detection path
        # that was tried so operators can tell whether env vars were
        # ignored vs set-but-wrong, MCP roots were queried vs unavailable,
        # etc. This cut debugging time from ~30 min to ~30 s in the
        # C3-substrate setup dogfood session.
        tried: list[str] = []
        if project_dir is not None:
            tried.append(f"explicit project_dir → {start}")
        for env_var in ("MYCO_PROJECT_DIR", "CLAUDE_PROJECT_DIR"):
            env_val = os.environ.get(env_var, "").strip()
            if env_val:
                tried.append(f"${env_var}={env_val!r}")
        if not tried:
            tried.append(f"cwd → {start}")
        lines = ["no Myco substrate found. Tried:"]
        for t in tried:
            lines.append(f"  - {t}")
        lines.append("")
        lines.append("No _canon.yaml at or above any of these. Fix one of:")
        lines.append(
            "  - germinate a new substrate: "
            "`myco germinate --project-dir <dir> --substrate-id <slug>`"
        )
        lines.append(
            "  - cd into an existing substrate (CLI), or set "
            "MYCO_PROJECT_DIR in the host's MCP server env (MCP hosts)"
        )
        lines.append(
            "  - on MCP hosts that expose `roots/list` (Cowork, Cursor, "
            "Zed, Windsurf, …), just open the substrate folder as a "
            "workspace — Myco auto-discovers it via protocol."
        )
        raise SubstrateNotFound("\n".join(lines)) from exc
    substrate = Substrate.load(root)
    import sys

    return MycoContext(
        substrate=substrate,
        now=now or datetime.now(timezone.utc),
        env=dict(os.environ),
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


def build_handler_args(spec: CommandSpec, raw: Mapping[str, Any]) -> dict[str, Any]:
    """Coerce and default the input dict for a command.

    Keys in ``raw`` may be dash-case or snake_case; the returned dict
    has snake_case keys (what the handler receives).
    """
    normalized: dict[str, Any] = {}
    # Accept either form from caller; rewrite to snake.
    snake_raw = {dash_to_snake(k): v for k, v in raw.items()}
    for arg in spec.args:
        if arg.snake in snake_raw:
            normalized[arg.snake] = arg.coerce(snake_raw[arg.snake])
        elif arg.required:
            raise UsageError(f"{spec.name}: missing required arg {arg.name!r}")
        else:
            normalized[arg.snake] = (
                arg.coerce(arg.default) if arg.default is not None else None
            )
    # Preserve unknown keys (for future forward-compat) as-is.
    extra = set(snake_raw) - {a.snake for a in spec.args}
    for k in extra:
        normalized[k] = snake_raw[k]
    return normalized


def dispatch(
    name: str,
    raw_args: Mapping[str, Any] | None = None,
    *,
    manifest: Manifest | None = None,
    ctx: MycoContext | None = None,
    project_dir: Path | None = None,
) -> Result:
    """Resolve ``name`` in the manifest and invoke its handler.

    v0.5.3 order-of-operations:

    1. If ``ctx`` was not supplied and the verb is not pre-substrate,
       build the context first so the substrate root is known.
    2. Ask :func:`load_manifest_with_overlay` for the effective
       manifest (packaged + per-substrate overlay merged).
    3. Resolve ``name`` against the effective manifest.

    This means overlay-declared verbs work out-of-the-box on any
    substrate with a ``.myco/manifest_overlay.yaml`` — including when
    the caller did NOT pre-load a manifest.
    """
    # Step 1: discover substrate root (if relevant) to compute the
    # effective manifest. Pre-substrate verbs never see overlay.
    substrate_root: Path | None = None
    effective_manifest: Manifest

    if manifest is not None:
        effective_manifest = manifest
    else:
        # Build ctx first when possible so the overlay is available.
        if ctx is not None:
            substrate_root = ctx.substrate.root
            effective_manifest = load_manifest_with_overlay(substrate_root)
        else:
            # We don't know yet whether the verb is pre-substrate; peek
            # at the packaged manifest to learn.
            base = load_manifest()
            try:
                peek = base.by_name(name)
            except UsageError:
                # Unknown verb on the packaged side — maybe an overlay
                # verb. We need a substrate root to resolve that, so fall
                # back to the normal cwd walk-up.
                try:
                    substrate_root = find_substrate_root(
                        (project_dir or Path.cwd()).resolve()
                    )
                except SubstrateNotFound:
                    # No substrate found — let the packaged manifest's
                    # by_name surface the UsageError.
                    effective_manifest = base
                else:
                    effective_manifest = load_manifest_with_overlay(substrate_root)
            else:
                if peek.pre_substrate:
                    effective_manifest = base
                else:
                    try:
                        substrate_root = find_substrate_root(
                            (project_dir or Path.cwd()).resolve()
                        )
                    except SubstrateNotFound:
                        # Usage error will propagate from build_context()
                        # below — keep the packaged manifest so the peek
                        # resolution remains valid.
                        effective_manifest = base
                    else:
                        effective_manifest = load_manifest_with_overlay(substrate_root)

    spec = effective_manifest.by_name(name)
    args = build_handler_args(spec, raw_args or {})
    handler = spec.resolve_handler()

    if ctx is None:
        ctx = build_context(project_dir=project_dir, pre_substrate=spec.pre_substrate)

    if spec.pre_substrate:
        # Genesis-shaped handlers accept only args.
        result = handler(args)
    else:
        result = handler(args, ctx=ctx)

    if not isinstance(result, Result):
        raise ContractError(f"handler {spec.handler} did not return a Result")
    return result
