"""Command manifest loader + dispatcher.

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
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from importlib.resources import files as _pkg_files
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import yaml

from myco.core.context import MycoContext, Result
from myco.core.errors import (
    ContractError,
    MycoError,
    SubstrateNotFound,
    UsageError,
)
from myco.core.substrate import Substrate, find_substrate_root

__all__ = [
    "ArgSpec",
    "CommandSpec",
    "Manifest",
    "load_manifest",
    "build_context",
    "dispatch",
    "dash_to_snake",
]


_VALID_TYPES: frozenset[str] = frozenset(
    {"str", "bool", "int", "path", "list[str]"}
)


def dash_to_snake(name: str) -> str:
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
                f"handler for {self.name!r} not found or not callable: "
                f"{self.handler}"
            )
        return func


@dataclass(frozen=True)
class Manifest:
    """Parsed command manifest."""

    schema_version: str
    commands: tuple[CommandSpec, ...] = field(default_factory=tuple)

    def by_name(self, name: str) -> CommandSpec:
        for c in self.commands:
            if c.name == name:
                return c
        raise UsageError(f"unknown command: {name!r}")

    def names(self) -> tuple[str, ...]:
        return tuple(c.name for c in self.commands)


def _parse_command(raw: Mapping[str, Any]) -> CommandSpec:
    for required in ("name", "subsystem", "handler", "summary", "mcp_tool"):
        if required not in raw:
            raise ContractError(
                f"manifest command missing {required!r}: {raw}"
            )
    args_raw = raw.get("args") or ()
    if not isinstance(args_raw, (list, tuple)):
        raise ContractError(
            f"manifest command {raw['name']!r}: args must be a list"
        )
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
    return CommandSpec(
        name=str(raw["name"]),
        subsystem=str(raw["subsystem"]),
        handler=str(raw["handler"]),
        summary=str(raw["summary"]),
        mcp_tool=str(raw["mcp_tool"]),
        args=tuple(args),
        pre_substrate=bool(raw.get("pre_substrate", False)),
    )


@lru_cache(maxsize=1)
def load_manifest() -> Manifest:
    """Load + validate the bundled ``manifest.yaml``."""
    text = (
        _pkg_files("myco.surface").joinpath("manifest.yaml").read_text(
            encoding="utf-8"
        )
    )
    try:
        raw = yaml.safe_load(text) or {}
    except yaml.YAMLError as exc:
        raise ContractError(f"manifest.yaml is not valid YAML: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise ContractError("manifest.yaml top level must be a mapping")
    schema_version = str(raw.get("schema_version", ""))
    if schema_version != "1":
        raise ContractError(
            f"unknown manifest schema_version: {schema_version!r}"
        )
    commands_raw = raw.get("commands") or ()
    if not isinstance(commands_raw, (list, tuple)):
        raise ContractError("manifest commands must be a list")
    commands = tuple(_parse_command(c) for c in commands_raw)
    names = [c.name for c in commands]
    if len(names) != len(set(names)):
        raise ContractError(
            f"manifest has duplicate command names: {sorted(names)}"
        )
    return Manifest(schema_version=schema_version, commands=commands)


def build_context(
    *,
    project_dir: Path | None = None,
    pre_substrate: bool = False,
    now: datetime | None = None,
) -> MycoContext | None:
    """Build a :class:`MycoContext` for invocation.

    Returns ``None`` for pre_substrate verbs (genesis); they don't need
    a loaded substrate.
    """
    if pre_substrate:
        return None
    start = (project_dir or Path.cwd()).resolve()
    try:
        root = find_substrate_root(start)
    except SubstrateNotFound as exc:
        raise UsageError(
            f"no Myco substrate found at or above {start}. "
            f"Run `myco genesis --project-dir <dir> --substrate-id <id>` first."
        ) from exc
    substrate = Substrate.load(root)
    import sys
    return MycoContext(
        substrate=substrate,
        now=now or datetime.now(timezone.utc),
        env=dict(os.environ),
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


def build_handler_args(
    spec: CommandSpec, raw: Mapping[str, Any]
) -> dict[str, Any]:
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
            raise UsageError(
                f"{spec.name}: missing required arg {arg.name!r}"
            )
        else:
            normalized[arg.snake] = arg.coerce(arg.default) if arg.default is not None else None
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

    If ``ctx`` is supplied, use it (tests). Otherwise, build one
    (unless the command is ``pre_substrate``).
    """
    m = manifest or load_manifest()
    spec = m.by_name(name)
    args = build_handler_args(spec, raw_args or {})
    handler = spec.resolve_handler()

    if ctx is None:
        ctx = build_context(
            project_dir=project_dir, pre_substrate=spec.pre_substrate
        )

    if spec.pre_substrate:
        # Genesis-shaped handlers accept only args.
        result = handler(args)
    else:
        result = handler(args, ctx=ctx)

    if not isinstance(result, Result):
        raise ContractError(
            f"handler {spec.handler} did not return a Result"
        )
    return result
