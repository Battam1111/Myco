#!/usr/bin/env python3
"""
Myco CLI — Unified command-line interface.

Usage:
    myco init <name> [--level 0|1|2] [--entry-point MYCO.md] [--dir /path]
    myco migrate <project_dir> [--level 0|1|2] [--entry-point MYCO.md] [--dry-run]
    myco lint [--quick] [--fix-report] [--project-dir /path]

    # Digestive substrate (four-command set):
    myco eat     [--content ... | --file ... | <stdin>] [--tags t1,t2] [--title "…"]
    myco digest  [<note_id>] [--to STATUS | --excrete REASON]
    myco view    [<note_id>] [--status STATUS] [--limit N] [--json]
    myco hunger  [--json]

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
        help="Entry point filename. Default: MYCO.md. For Claude Code / "
             "Cowork users whose agent auto-loads CLAUDE.md, pass "
             "'--entry-point CLAUDE.md'. For GPT-based agents, 'GPT.md'. "
             "The choice writes through to _canon.yaml::system.entry_point "
             "and L1 scans. (ASCC ce72 friction — v0.9.0 discoverability fix)",
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
        "lint", help="Run 15-dimension consistency checks on project knowledge"
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

    # ── myco eat ───────────────────────────────────────────────────
    # Digestive substrate — the four-command set (eat/digest/view/hunger).
    # Authoritative design: docs/primordia/digestive_architecture_craft_2026-04-10.md
    eat_parser = subparsers.add_parser(
        "eat",
        help="Ingest a chunk of content as a raw atomic note (zero-friction capture)",
    )
    eat_parser.add_argument(
        "--content", type=str, default=None,
        help="Inline content to eat (alternative: --file or stdin)",
    )
    eat_parser.add_argument(
        "--file", type=str, default=None,
        help="Path to a file whose contents should be eaten",
    )
    eat_parser.add_argument(
        "--tags", type=str, default="",
        help="Comma-separated tags (e.g. --tags vision,lint)",
    )
    eat_parser.add_argument(
        "--source", type=str, default="eat",
        choices=["chat", "eat", "promote", "import", "bootstrap"],
        help="Provenance label (default: eat)",
    )
    eat_parser.add_argument(
        "--title", type=str, default=None,
        help="Optional H1 title to prepend to the note body",
    )
    eat_parser.add_argument(
        "--json", action="store_true",
        help="Emit a machine-readable JSON result",
    )
    eat_parser.add_argument(
        "--project-dir", type=str, default=".",
        help="Project root (default: current directory; walks up for _canon.yaml)",
    )

    # ── myco correct (Wave 19, contract v0.18.0) ───────────────────
    # Ergonomic shortcut for Hard Contract rule #3 special clause:
    # a self-correction must be eaten in the same turn with mandatory
    # tags 'friction-phase2, on-self-correction'. This verb force-merges
    # the tag pair so the agent only has to remember one word.
    # Craft of record:
    #   docs/primordia/myco_correct_shortcut_craft_2026-04-11.md
    correct_parser = subparsers.add_parser(
        "correct",
        help=("Self-correction shortcut — eat a friction note with "
              "mandatory tags 'friction-phase2, on-self-correction' "
              "(Hard Contract rule #3)"),
    )
    correct_parser.add_argument("--content", type=str, default=None,
        help="Inline content (alternative: --file or stdin)")
    correct_parser.add_argument("--file", type=str, default=None,
        help="Path to a file whose contents should be eaten")
    correct_parser.add_argument("--tags", type=str, default="",
        help="Additional tags, merged with the mandatory pair "
             "(friction-phase2, on-self-correction)")
    correct_parser.add_argument("--source", type=str, default="eat",
        choices=["chat", "eat", "promote", "import", "bootstrap"])
    correct_parser.add_argument("--title", type=str, default=None,
        help="Optional H1 title to prepend to the note body")
    correct_parser.add_argument("--json", action="store_true",
        help="Emit a machine-readable JSON result")
    correct_parser.add_argument("--project-dir", type=str, default=".",
        help="Project root (default: current directory)")

    # ── myco digest ────────────────────────────────────────────────
    digest_parser = subparsers.add_parser(
        "digest",
        help="Move a note along the lifecycle (raw→digesting→extracted/integrated/excreted)",
    )
    digest_parser.add_argument(
        "note_id", nargs="?", default=None,
        help="Target note id (default: oldest raw note in queue)",
    )
    digest_parser.add_argument(
        "--to", type=str, default=None,
        help="Explicit transition target status",
    )
    digest_parser.add_argument(
        "--excrete", type=str, default=None, metavar="REASON",
        help="Shortcut: mark as excreted with the given reason",
    )
    digest_parser.add_argument(
        "--project-dir", type=str, default=".",
        help="Project root (default: current directory)",
    )

    # ── myco view ──────────────────────────────────────────────────
    view_parser = subparsers.add_parser(
        "view",
        help="List notes (optionally filtered by status) or show a single note",
    )
    view_parser.add_argument(
        "note_id", nargs="?", default=None,
        help="Show a single note by id (default: list mode)",
    )
    view_parser.add_argument(
        "--status", type=str, default=None,
        help="Filter by status: raw | digesting | extracted | integrated | excreted",
    )
    view_parser.add_argument(
        "--limit", type=int, default=50,
        help="Max notes to list (default: 50)",
    )
    view_parser.add_argument(
        "--json", action="store_true",
        help="Emit JSON",
    )
    view_parser.add_argument(
        "--project-dir", type=str, default=".",
        help="Project root (default: current directory)",
    )
    # Wave 21 (v0.20.0) — agent-facing surfaces (closes NH-7).
    # Authoritative craft: docs/primordia/observability_integrity_craft_2026-04-12.md
    view_parser.add_argument(
        "--next-raw", action="store_true", dest="next_raw",
        help="Show the body of the oldest raw note (digest-queue head). "
             "Zero-arg target for the raw→digesting loop.",
    )
    view_parser.add_argument(
        "--tag", type=str, default=None,
        help="Filter notes whose frontmatter tags contain this value "
             "(exact match). Sorted by last_touched desc.",
    )

    # ── myco hunger ────────────────────────────────────────────────
    hunger_parser = subparsers.add_parser(
        "hunger",
        help="Metabolic dashboard — raw backlog, stale notes, digestion depth, excretion rate",
    )
    hunger_parser.add_argument(
        "--json", action="store_true",
        help="Emit JSON",
    )
    hunger_parser.add_argument(
        "--project-dir", type=str, default=".",
        help="Project root (default: current directory)",
    )

    # ── myco forage ────────────────────────────────────────────────
    # External reference material intake — the inbound channel
    # (forage/foraging/exoenzyme phase). Contract v0.7.0.
    # Authoritative design: docs/primordia/forage_substrate_craft_2026-04-11.md
    forage_parser = subparsers.add_parser(
        "forage",
        help="Intake external reference material (papers, repos, articles) "
             "into forage/ for pre-digestion",
    )
    forage_sub = forage_parser.add_subparsers(
        dest="forage_subcommand", help="Forage subcommand"
    )

    forage_add = forage_sub.add_parser(
        "add", help="Register a new foraged item in the manifest"
    )
    forage_add.add_argument("--source-url", required=True, type=str,
                            help="Upstream URL (required)")
    forage_add.add_argument("--source-type", required=True, type=str,
                            choices=["paper", "repo", "article", "other"],
                            help="Item category")
    forage_add.add_argument("--local-path", type=str, default="",
                            help="Local path under forage/ (optional; "
                                 "manifest-only entry is allowed)")
    forage_add.add_argument("--license", required=True, type=str,
                            help="SPDX identifier or short label. Use "
                                 "'unknown' to auto-quarantine.")
    forage_add.add_argument("--why", required=True, type=str,
                            help="Intent statement — why is this being "
                                 "foraged? (required, prevents hoarding)")
    forage_add.add_argument("--project-dir", type=str, default=".",
                            help="Project root (default: .)")

    forage_list = forage_sub.add_parser(
        "list", help="List foraged items, optionally filtered by status"
    )
    forage_list.add_argument("--status", type=str, default=None,
                             help="Filter by status: raw/digesting/digested/"
                                  "absorbed/discarded/quarantined")
    forage_list.add_argument("--project-dir", type=str, default=".",
                             help="Project root (default: .)")

    forage_digest = forage_sub.add_parser(
        "digest",
        help="Flip a foraged item's status (after producing digest notes)"
    )
    forage_digest.add_argument("item_id", type=str,
                               help="Forage item id (f_YYYYMMDDTHHMMSS_xxxx)")
    forage_digest.add_argument("--status", required=True, type=str,
                               choices=["digesting", "digested", "absorbed",
                                        "discarded", "quarantined"],
                               help="Target status")
    forage_digest.add_argument("--digest-target", action="append", default=[],
                               metavar="NOTE_ID",
                               help="Note id produced from this item "
                                    "(repeatable). Required for "
                                    "digested/absorbed.")
    forage_digest.add_argument("--project-dir", type=str, default=".",
                               help="Project root (default: .)")

    # ── myco upstream ───────────────────────────────────────────────
    # Kernel-side reception of downstream friction bundles — the
    # returning leg of the outbound channel. Contract v0.9.0.
    # Authoritative design: docs/primordia/upstream_absorb_craft_2026-04-11.md
    upstream_parser = subparsers.add_parser(
        "upstream",
        help="Absorb downstream friction bundles into kernel inbox + ingest "
             "into notes/ as pointer notes",
    )
    upstream_sub = upstream_parser.add_subparsers(
        dest="upstream_subcommand", help="Upstream subcommand"
    )

    up_scan = upstream_sub.add_parser(
        "scan", help="List pending bundles in the kernel inbox"
    )
    up_scan.add_argument("--project-dir", type=str, default=".",
                         help="Project root (default: .)")
    up_scan.add_argument("--json", action="store_true",
                         help="Emit machine-readable JSON")

    up_absorb = upstream_sub.add_parser(
        "absorb",
        help="Copy bundles from a downstream instance's .myco_upstream_outbox/ "
             "into kernel .myco_upstream_inbox/"
    )
    up_absorb.add_argument("instance_path", type=str,
                           help="Absolute or relative path to the downstream "
                                "instance root (must contain "
                                ".myco_upstream_outbox/). Use the Courier "
                                "Fallback in docs/agent_protocol.md §8 if "
                                "the instance is not accessible from this "
                                "session.")
    up_absorb.add_argument("--project-dir", type=str, default=".",
                           help="Kernel project root (default: .)")
    up_absorb.add_argument("--json", action="store_true",
                           help="Emit machine-readable JSON")

    up_ingest = upstream_sub.add_parser(
        "ingest",
        help="Create a pointer note for a bundle and archive bundle body "
             "to .myco_upstream_inbox/absorbed/"
    )
    up_ingest.add_argument("bundle_id", type=str,
                           help="Bundle id, e.g. n_20260411T004215_ce72")
    up_ingest.add_argument("--project-dir", type=str, default=".",
                           help="Kernel project root (default: .)")
    up_ingest.add_argument("--json", action="store_true",
                           help="Emit machine-readable JSON")

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

    if args.command == "eat":
        from myco.notes_cmd import run_eat
        sys.exit(run_eat(args))

    if args.command == "correct":
        from myco.notes_cmd import run_correct
        sys.exit(run_correct(args))

    if args.command == "digest":
        from myco.notes_cmd import run_digest
        sys.exit(run_digest(args))

    if args.command == "view":
        from myco.notes_cmd import run_view
        sys.exit(run_view(args))

    if args.command == "hunger":
        from myco.notes_cmd import run_hunger
        sys.exit(run_hunger(args))

    if args.command == "forage":
        from myco.forage_cmd import run_forage
        sys.exit(run_forage(args))

    if args.command == "upstream":
        from myco.upstream_cmd import run_upstream
        sys.exit(run_upstream(args))


if __name__ == "__main__":
    main()
