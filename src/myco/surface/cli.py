"""Manifest-driven argparse CLI.

Builds one subparser per verb from :func:`myco.surface.manifest.load_manifest`.
Global flags: ``--project-dir`` (passed into context discovery),
``--exit-on`` (forwarded to ``immune`` verb), ``--json`` (structured
output).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from myco.core.context import Result
from myco.core.errors import MycoError, UsageError

from .manifest import (
    ArgSpec,
    CommandSpec,
    Manifest,
    build_context,
    build_handler_args,
    dash_to_snake,
    dispatch,
    load_manifest,
)

__all__ = ["main", "build_parser"]


def _add_arg(subparser: argparse.ArgumentParser, arg: ArgSpec) -> None:
    flag = f"--{arg.name}"
    if arg.type == "bool":
        subparser.add_argument(
            flag, action="store_true", default=bool(arg.default or False),
            help=arg.help,
        )
    elif arg.type == "list[str]":
        # v0.5.3-fix: ``nargs="*"`` + ``action="extend"`` lets users
        # write either ``--tags a b c`` (natural) or ``--tags a
        # --tags b --tags c`` (explicit). Before: only the repeated
        # form worked; the natural form errored with "unrecognized
        # arguments". See dogfood bug #3.
        subparser.add_argument(
            flag, nargs="*", action="extend", default=None, help=arg.help,
        )
    elif arg.type == "int":
        subparser.add_argument(
            flag,
            type=int,
            required=arg.required,
            default=arg.default,
            help=arg.help,
        )
    elif arg.type == "path":
        subparser.add_argument(
            flag,
            type=Path,
            required=arg.required,
            default=arg.default,
            help=arg.help,
        )
    else:  # "str"
        subparser.add_argument(
            flag,
            required=arg.required,
            default=arg.default,
            help=arg.help,
        )


def build_parser(manifest: Manifest | None = None) -> argparse.ArgumentParser:
    m = manifest or load_manifest()
    from myco import __version__ as _mv
    parser = argparse.ArgumentParser(
        prog="myco",
        description=f"Myco v{_mv} — agent-first symbiotic substrate.",
    )
    # v0.5.3-fix: ``--version`` / ``-V`` prints the package version
    # and exits 0, matching standard CLI convention. Before: no
    # --version flag existed so ``myco --version`` errored with
    # "VERB required". See dogfood bug #1.
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"myco {_mv}",
    )
    parser.add_argument(
        "--project-dir", type=Path, default=None,
        help="Override substrate discovery start directory.",
    )
    parser.add_argument(
        "--exit-on", default="critical",
        help="Exit-policy spec for `immune` (default: critical).",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Emit structured JSON instead of human-readable text.",
    )
    # Use a private-looking dest name so the subparser's stored verb
    # identifier never collides with a manifest arg named ``verb``
    # (e.g. ``ramify --verb <name>``). Before v0.5.3-fix this collision
    # silently overwrote the subcommand with the inner --verb default,
    # making ``myco ramify --dimension ...`` fail with "unknown
    # command: None". See dogfood bug #6.
    subparsers = parser.add_subparsers(dest="_subcmd", metavar="VERB")
    subparsers.required = True
    for spec in m.commands:
        # Canonical subparser.
        sp = subparsers.add_parser(spec.name, help=spec.summary)
        for arg in spec.args:
            _add_arg(sp, arg)
        # Aliased subparsers — same args, help text marks them as
        # deprecated so users see it in --help output immediately.
        for alias in spec.aliases:
            alias_sp = subparsers.add_parser(
                alias,
                help=f"[deprecated alias for {spec.name!r}] {spec.summary}",
            )
            for arg in spec.args:
                _add_arg(alias_sp, arg)
    return parser


def _extract_args(spec: CommandSpec, namespace: argparse.Namespace) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for arg in spec.args:
        val = getattr(namespace, arg.snake, None)
        if val is None and arg.type == "list[str]":
            val = []
        out[arg.snake] = val
    return out


def _render_human(result: Result) -> str:
    lines = [f"exit_code: {result.exit_code}"]
    if result.payload:
        for k, v in result.payload.items():
            lines.append(f"  {k}: {v}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    manifest = load_manifest()
    parser = build_parser(manifest)
    ns = parser.parse_args(argv)
    subcmd = getattr(ns, "_subcmd", None)
    if not subcmd:
        parser.print_help(sys.stderr)
        return 2
    spec = manifest.by_name(subcmd)

    raw_args = _extract_args(spec, ns)
    # Forward --exit-on to immune / session-end if they accept it.
    if spec.name == "immune":
        raw_args["exit_on"] = ns.exit_on

    try:
        result = dispatch(
            spec.name,
            raw_args,
            manifest=manifest,
            project_dir=ns.project_dir,
        )
    except MycoError as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return exc.exit_code
    except KeyboardInterrupt:  # pragma: no cover
        return 130

    if ns.json:
        # v0.5.4-fix: findings list is now surfaced in the JSON output
        # so the Agent sees WHY an exit was nonzero (which dimension
        # fired at what severity on which path) without a follow-up
        # verb call. Empty list when the handler produced no findings.
        out = {
            "exit_code": result.exit_code,
            "findings": [_finding_to_dict(f) for f in result.findings],
            "payload": _jsonable(result.payload),
        }
        print(json.dumps(out, default=str, indent=2))
    else:
        print(_render_human(result))
    return result.exit_code


def _jsonable(obj: Any) -> Any:
    if isinstance(obj, Mapping):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, Path):
        return str(obj)
    return obj


def _finding_to_dict(finding: Any) -> dict[str, Any]:
    """Serialize a :class:`myco.homeostasis.finding.Finding` (or a dict
    shaped like one) for the ``--json`` output. Kept tolerant of non-
    Finding values so handlers that return free-form finding-like
    mappings still render."""
    if isinstance(finding, Mapping):
        return {str(k): _jsonable(v) for k, v in finding.items()}
    # Finding dataclass has `dimension_id`, `category`, `severity`,
    # `message`, `path`, `line`, `fixable` — all attributes.
    out: dict[str, Any] = {}
    for attr in (
        "dimension_id", "category", "severity",
        "message", "path", "line", "fixable",
    ):
        if hasattr(finding, attr):
            val = getattr(finding, attr)
            # Category/Severity are enums; render as their lowercase
            # label (matches the --list payload shape).
            if hasattr(val, "value") and isinstance(val.value, str):
                out[attr] = val.value
            elif hasattr(val, "label") and callable(val.label):
                out[attr] = val.label()
            else:
                out[attr] = _jsonable(val)
    return out


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
