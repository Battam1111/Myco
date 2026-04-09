#!/usr/bin/env python3
"""
Myco CLI — Unified command-line interface.

Usage:
    myco init <name> [--level 0|1|2] [--entry-point MYCO.md] [--dir /path]
    myco migrate <project_dir> [--level 0|1|2] [--entry-point MYCO.md] [--dry-run]
    myco lint [--quick] [--fix-report] [--project-dir /path]
    myco version
"""

import argparse
import sys

from myco import __version__


def _ensure_utf8() -> None:
    """
    Force UTF-8 output on Windows where the default console encoding (GBK/cp936)
    cannot render rich's progress bar characters (e.g. U+2022 •).

    Called once at CLI entry-point before any output is produced.
    """
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass  # Python < 3.7 — best effort
    if sys.stderr.encoding and sys.stderr.encoding.lower() not in ("utf-8", "utf8"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass


def main():
    _ensure_utf8()
    parser = argparse.ArgumentParser(
        prog="myco",
        description="Myco — Self-Evolving Knowledge Substrate for AI Agents",
    )
    parser.add_argument(
        "--version", action="version", version=f"myco {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ── myco init ──────────────────────────────────────────────────
    init_parser = subparsers.add_parser(
        "init", help="Initialize a new Myco-powered project"
    )
    init_parser.add_argument("name", help="Project name")
    init_parser.add_argument(
        "--level", type=int, default=1, choices=[0, 1, 2],
        help="Bootstrap level: 0=minimal, 1=standard (default), 2=full",
    )
    init_parser.add_argument(
        "--dir", type=str, default=None,
        help="Target directory (default: ./<name>)",
    )
    init_parser.add_argument(
        "--entry-point", type=str, default="MYCO.md",
        help="Entry point filename (default: MYCO.md, alternative: CLAUDE.md)",
    )
    init_parser.add_argument(
        "--github-user", type=str, default="your-username",
        help="GitHub username for Myco link in entry point document",
    )

    # ── myco migrate ───────────────────────────────────────────────
    migrate_parser = subparsers.add_parser(
        "migrate", help="Migrate an existing project to Myco (non-destructive)"
    )
    migrate_parser.add_argument("project_dir", help="Path to existing project")
    migrate_parser.add_argument(
        "--level", type=int, default=1, choices=[0, 1, 2],
        help="Bootstrap level: 0=minimal, 1=standard (default), 2=full",
    )
    migrate_parser.add_argument(
        "--entry-point", type=str, default="MYCO.md",
        help="Entry point filename (default: MYCO.md)",
    )
    migrate_parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be done without making changes",
    )

    # ── myco lint ──────────────────────────────────────────────────
    lint_parser = subparsers.add_parser(
        "lint", help="Run 9-dimension consistency checks on project knowledge"
    )
    lint_parser.add_argument(
        "--quick", action="store_true",
        help="Quick mode: only L0-L3 checks",
    )
    lint_parser.add_argument(
        "--fix-report", action="store_true",
        help="Output fix suggestions",
    )
    lint_parser.add_argument(
        "--project-dir", type=str, default=".",
        help="Project root directory (default: current directory)",
    )

    # ── myco config ────────────────────────────────────────────────
    config_parser = subparsers.add_parser(
        "config", help="Read/write adapter configuration in _canon.yaml [adapters] section"
    )
    config_parser.add_argument(
        "--project-dir", type=str, default=".",
        help="Project root directory (default: current directory)",
    )
    config_group = config_parser.add_mutually_exclusive_group(required=True)
    config_group.add_argument(
        "--set", nargs=2, metavar=("KEY", "VALUE"),
        help="Set adapters.* key (e.g. --set adapters.mempalace.endpoint http://localhost:8765)",
    )
    config_group.add_argument(
        "--get", metavar="KEY",
        help="Get value of adapters.* key",
    )
    config_group.add_argument(
        "--list", nargs="?", const="", metavar="SECTION",
        help="List all config, or a specific section (e.g. --list adapters)",
    )
    config_group.add_argument(
        "--unset", metavar="KEY",
        help="Remove an adapters.* key",
    )

    # ── myco import ────────────────────────────────────────────────
    import_parser = subparsers.add_parser(
        "import", help="Semi-automated content import from external tools (Hermes, OpenClaw)"
    )
    import_parser.add_argument(
        "--from", dest="from_tool", required=True, metavar="TOOL",
        choices=["hermes", "openclaw"],
        help="Source tool: hermes | openclaw",
    )
    import_parser.add_argument(
        "source", nargs="?", default=None,
        help="Source path (directory for hermes, file for openclaw). Default: tool-specific.",
    )
    import_parser.add_argument(
        "--project-dir", type=str, default=".",
        help="Myco project root (default: current directory)",
    )
    import_parser.add_argument(
        "--all", action="store_true",
        help="Import all candidates without interactive confirmation",
    )
    import_parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be imported without making changes",
    )

    # ── myco version (explicit subcommand) ─────────────────────────
    subparsers.add_parser("version", help="Show version")

    # ── Parse and dispatch ─────────────────────────────────────────
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "version":
        print(f"myco {__version__}")
        sys.exit(0)

    if args.command == "init":
        from myco.init_cmd import run_init
        sys.exit(run_init(args))

    if args.command == "migrate":
        from myco.migrate import run_migrate
        sys.exit(run_migrate(args))

    if args.command == "lint":
        from myco.lint import run_lint
        sys.exit(run_lint(args))

    if args.command == "config":
        from myco.config_cmd import run_config
        sys.exit(run_config(args))

    if args.command == "import":
        from myco.import_cmd import run_import
        sys.exit(run_import(args))


if __name__ == "__main__":
    main()
