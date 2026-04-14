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
        subparser.add_argument(
            flag, action="append", default=None, help=arg.help,
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
    parser = argparse.ArgumentParser(
        prog="myco",
        description="Myco v0.4.0 — agent-first symbiotic substrate.",
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
    subparsers = parser.add_subparsers(dest="verb", metavar="VERB")
    subparsers.required = True
    for spec in m.commands:
        sp = subparsers.add_parser(spec.name, help=spec.summary)
        for arg in spec.args:
            _add_arg(sp, arg)
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
    spec = manifest.by_name(ns.verb)

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
        out = {
            "exit_code": result.exit_code,
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


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
