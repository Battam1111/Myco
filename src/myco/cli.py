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
    # Wave 29 note: `myco lint` is the generic software-engineering term and
    # stays as a universal-discoverability verb. The biomimetic name for this
    # same operation is `myco immune` (Wave 29 adds it as a new verb that
    # runs the same 23-dimension substrate immune scan). Both verbs remain
    # primary — neither is deprecated. Design rationale:
    # `docs/primordia/biomimetic_nomenclature_craft_2026-04-12.md §1.3 + §2.3`.
    lint_parser = subparsers.add_parser(
        "lint",
        help="Run 23-dimension substrate immune scan (alias: `myco immune`)",
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

    # ── myco immune ────────────────────────────────────────────────
    # Wave 29 (Biomimetic Nomenclature rewrite, phase 1 additive): the
    # substrate's 23-dimension immune scan is the immune system of the
    # knowledge organism. `myco immune` is the biomimetic name; `myco lint`
    # is the universal software-engineering alias. Both dispatch to the
    # same handler. Craft: biomimetic_nomenclature_craft_2026-04-12.md.
    immune_parser = subparsers.add_parser(
        "immune",
        help="Run 23-dimension substrate immune scan (alias: `myco lint`)",
    )
    immune_parser.add_argument(
        "--quick", action="store_true",
        help="Quick mode: only L0-L3 checks",
    )
    immune_parser.add_argument(
        "--fix-report", action="store_true",
        help="Output fix suggestions",
    )
    immune_parser.add_argument(
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
    #
    # Wave 29 note: `myco molt` is the biomimetic alias for this verb.
    # Molt = shedding an outdated assertion like a fungus shedding aged
    # hyphae. Both verbs remain primary — neither is deprecated.
    # Biomimetic design: biomimetic_nomenclature_craft_2026-04-12.md.
    correct_parser = subparsers.add_parser(
        "correct",
        help=("Self-correction shortcut — eat a friction note with "
              "mandatory tags 'friction-phase2, on-self-correction' "
              "(Hard Contract rule #3). Biomimetic alias: `myco molt`."),
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

    # ── myco molt (Wave 29, Biomimetic Nomenclature rewrite) ──────
    # Biomimetic alias for `myco correct`. Molting is the organism's act
    # of shedding an outdated layer to reveal the new structure beneath —
    # exactly what a self-correction is at the substrate level. Both verbs
    # are primary and dispatch to the same handler (run_correct). Craft:
    #   docs/primordia/biomimetic_nomenclature_craft_2026-04-12.md
    molt_parser = subparsers.add_parser(
        "molt",
        help=("Self-correction shortcut (biomimetic alias for `myco correct`) "
              "— shed an outdated assertion by eating a friction note with "
              "mandatory tags 'friction-phase2, on-self-correction'."),
    )
    molt_parser.add_argument("--content", type=str, default=None,
        help="Inline content (alternative: --file or stdin)")
    molt_parser.add_argument("--file", type=str, default=None,
        help="Path to a file whose contents should be eaten")
    molt_parser.add_argument("--tags", type=str, default="",
        help="Additional tags, merged with the mandatory pair "
             "(friction-phase2, on-self-correction)")
    molt_parser.add_argument("--source", type=str, default="eat",
        choices=["chat", "eat", "promote", "import", "bootstrap"])
    molt_parser.add_argument("--title", type=str, default=None,
        help="Optional H1 title to prepend to the note body")
    molt_parser.add_argument("--json", action="store_true",
        help="Emit a machine-readable JSON result")
    molt_parser.add_argument("--project-dir", type=str, default=".",
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

    # ── Wave 32: anchor #3 step verbs (additive aliases per Wave 29 D2) ──
    # Each is a thin wrapper over digest with a fixed --to value, exposing
    # the seven-step pipeline as first-class CLI verbs. These do NOT
    # replace `myco digest --to <status>` — both forms are equal-peer per
    # Wave 28-29 doctrine. Step 1 (forage) and step 5 (compress) and step
    # 6 (eat) and step 7 (excrete via --excrete) already have native verbs;
    # steps 2/3/4 (evaluate/extract/integrate) were the missing surfaces.

    # ── myco evaluate ──────────────────────────────────────────────
    # Step 2: enter the digesting state and surface reflection prompts.
    # Equivalent to `myco digest <id>` (no --to).
    evaluate_parser = subparsers.add_parser(
        "evaluate",
        help="Step 2: transition raw→digesting and print reflection prompts",
    )
    evaluate_parser.add_argument(
        "note_id", nargs="?", default=None,
        help="Target note id (default: oldest raw note in queue)",
    )
    evaluate_parser.add_argument(
        "--project-dir", type=str, default=".",
        help="Project root (default: current directory)",
    )

    # ── myco extract ───────────────────────────────────────────────
    # Step 3: pull a digesting note out into the extracted layer.
    # Equivalent to `myco digest <id> --to extracted`.
    extract_parser = subparsers.add_parser(
        "extract",
        help="Step 3: transition a note to status=extracted",
    )
    extract_parser.add_argument(
        "note_id", type=str,
        help="Target note id (required for extract)",
    )
    extract_parser.add_argument(
        "--project-dir", type=str, default=".",
        help="Project root (default: current directory)",
    )

    # ── myco integrate ─────────────────────────────────────────────
    # Step 4: fold an extracted note into integrated canon.
    # Equivalent to `myco digest <id> --to integrated`.
    integrate_parser = subparsers.add_parser(
        "integrate",
        help="Step 4: transition a note to status=integrated",
    )
    integrate_parser.add_argument(
        "note_id", type=str,
        help="Target note id (required for integrate)",
    )
    integrate_parser.add_argument(
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

    # ── myco compress ──────────────────────────────────────────────
    # Wave 30 (kernel_contract, contract v0.26.0): forward compression —
    # take N raw/digesting notes and produce 1 extracted synthesis with a
    # full audit trail (compressed_from / compressed_into back-reference,
    # rationale, confidence). Anchor #4 ("compression-is-cognition") was
    # the lowest-coverage anchor at Wave 26 (0.35); this verb services it
    # directly. Authoritative design: docs/primordia/compression_primitive_craft_2026-04-12.md
    # (Wave 27, exploration 0.85). Implementation craft:
    # docs/primordia/compress_mvp_craft_2026-04-12.md (Wave 30, kernel_contract 0.90).
    compress_parser = subparsers.add_parser(
        "compress",
        help="Forward compression — synthesize N raw/digesting notes into "
             "1 extracted note with audit trail (anchor #4 service verb).",
    )
    compress_parser.add_argument(
        "note_ids", nargs="*", default=None,
        help="Explicit note ids to compress (manual bundle). Mutually "
             "exclusive with --tag.",
    )
    compress_parser.add_argument(
        "--tag", type=str, default=None,
        help="Compress all raw/digesting notes whose frontmatter tags "
             "include this value (primary cohort selector). Mutually "
             "exclusive with positional note ids.",
    )
    compress_parser.add_argument(
        "--rationale", type=str, default=None,
        help="REQUIRED. One-paragraph prose explaining what the synthesis "
             "preserves vs drops. Lands as `compression_rationale` in the "
             "output note's frontmatter (Wave 27 D4 audit trail).",
    )
    compress_parser.add_argument(
        "--status", type=str, default=None,
        help="Optional status filter applied to --tag cohort. Default: "
             "all non-excreted statuses (raw + digesting).",
    )
    compress_parser.add_argument(
        "--confidence", type=float, default=0.85,
        help="Self-reported compression confidence in [0.0, 1.0] "
             "(default 0.85). Lands in output frontmatter.",
    )
    compress_parser.add_argument(
        "--dry-run", dest="dry_run", action="store_true",
        help="Show what would be compressed (cohort + rationale) without "
             "writing anything. Wave 27 Attack G defense — observability "
             "for the fold-into-compress decision.",
    )
    compress_parser.add_argument(
        "--json", action="store_true",
        help="Emit machine-readable JSON result",
    )
    compress_parser.add_argument(
        "--project-dir", type=str, default=".",
        help="Project root (default: current directory)",
    )

    # ── myco uncompress ────────────────────────────────────────────
    # Wave 31: closes Wave 30 L4 limitation. Reverses a single compress
    # output: restores each input note to its `pre_compression_status`
    # and deletes the output extracted note. Bidirectional back-link
    # integrity is validated before any writes — refuses to operate on
    # an output whose audit chain is broken.
    uncompress_parser = subparsers.add_parser(
        "uncompress",
        help="Reverse a previous `myco compress` — restore each input from "
             "its pre_compression_status and delete the extracted output.",
    )
    uncompress_parser.add_argument(
        "output_id", type=str,
        help="The id of the extracted note to uncompress (e.g. "
             "n_20260412T060604_94cf).",
    )
    uncompress_parser.add_argument(
        "--json", action="store_true",
        help="Emit machine-readable JSON result",
    )
    uncompress_parser.add_argument(
        "--project-dir", type=str, default=".",
        help="Project root (default: current directory)",
    )

    # ── myco prune (Wave 33: D-layer auto-excretion) ──────────────
    # Closes the dead_knowledge hunger-signal loop. Default --dry-run is
    # SAFE (no writes); opt-in --apply mutates. Inverse asymmetry from
    # `myco compress --dry-run` (additive verb defaults to apply, opt-in
    # dry-run; destructive verb defaults to dry-run, opt-in apply).
    prune_parser = subparsers.add_parser(
        "prune",
        help="D-layer auto-excretion: scan for dead-knowledge notes "
             "(terminal status, cold, unviewed) and excrete them with "
             "audit trail. SAFE: defaults to --dry-run.",
    )
    prune_parser.add_argument(
        "--apply", action="store_true",
        help="Actually excrete the candidates (default: dry-run, no writes)",
    )
    prune_parser.add_argument(
        "--threshold-days", type=int, default=None,
        dest="threshold_days",
        help="Override dead_knowledge_threshold_days from canon (default: read from _canon.yaml)",
    )
    prune_parser.add_argument(
        "--json", action="store_true",
        help="Emit machine-readable JSON",
    )
    prune_parser.add_argument(
        "--project-dir", type=str, default=".",
        help="Project root (default: current directory)",
    )

    # ── myco inlet (Wave 35: Metabolic Inlet primitive scaffold) ──
    # Closes the longest-deferred gap in Myco's identity surface (anchor #3
    # Metabolic Inlet, declared Wave 10, scaffolded Wave 34, implemented Wave 35).
    # Verb shape locked in docs/primordia/metabolic_inlet_design_craft_2026-04-12.md §3.1.
    # Operator-deferred for all 4 open_problems §1-4 sub-problems.
    inlet_parser = subparsers.add_parser(
        "inlet",
        help="Metabolic Inlet: ingest external content (file or "
             "agent-piped URL body) as a raw note with provenance scaffold "
             "(inlet_origin, inlet_method, inlet_fetched_at, inlet_content_hash).",
    )
    inlet_parser.add_argument(
        "source", nargs="?", default=None, type=str,
        help="File path to inlet (or URL — URLs are rejected with a clear "
             "instruction; fetch via agent + pipe back via --content/--provenance)",
    )
    inlet_parser.add_argument(
        "--content", type=str, default=None,
        help="Explicit content body (use with --provenance). The "
             "agent-fetched-URL pattern: WebFetch the URL, then "
             "`myco inlet --content \"<body>\" --provenance \"<url>\"`.",
    )
    inlet_parser.add_argument(
        "--provenance", type=str, default=None,
        help="Origin string (URL or label) when using --content. Required "
             "alongside --content so inlet_origin is machine-traceable.",
    )
    inlet_parser.add_argument(
        "--tags", type=str, default=None,
        help="Comma-separated tags. If omitted, the canon default tag "
             "(`notes_schema.inlet.default_tag`, normally 'inlet') is applied "
             "so the existing `myco compress --tag inlet` chain works without "
             "operators having to remember the convention.",
    )
    inlet_parser.add_argument(
        "--json", action="store_true",
        help="Emit machine-readable JSON",
    )
    inlet_parser.add_argument(
        "--project-dir", type=str, default=".",
        help="Project root (default: current directory)",
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

    # Wave 29 biomimetic alias — dispatches to the same immune scan handler.
    if args.command == "immune":
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

    # Wave 29 biomimetic alias — dispatches to the same self-correction handler.
    if args.command == "molt":
        from myco.notes_cmd import run_correct
        sys.exit(run_correct(args))

    if args.command == "digest":
        from myco.notes_cmd import run_digest
        sys.exit(run_digest(args))

    # Wave 32: anchor #3 step verbs — thin wrappers over run_digest.
    # Each constructs a digest-shaped namespace with the right --to value
    # and dispatches. Per Wave 29 D2, these are equal-peer aliases (not
    # deprecated forms): both `myco extract <id>` and
    # `myco digest <id> --to extracted` are first-class verbs.
    if args.command in ("evaluate", "extract", "integrate"):
        from myco.notes_cmd import run_digest
        from types import SimpleNamespace
        target_status = {
            "evaluate": None,        # no transition; let digest handle raw→digesting
            "extract": "extracted",
            "integrate": "integrated",
        }[args.command]
        wrapped = SimpleNamespace(
            note_id=args.note_id,
            to=target_status,
            excrete=None,
            project_dir=args.project_dir,
        )
        sys.exit(run_digest(wrapped))

    if args.command == "view":
        from myco.notes_cmd import run_view
        sys.exit(run_view(args))

    if args.command == "hunger":
        from myco.notes_cmd import run_hunger
        sys.exit(run_hunger(args))

    # Wave 33: D-layer auto-excretion verb. Closes the dead_knowledge loop.
    if args.command == "prune":
        from myco.notes_cmd import run_prune
        sys.exit(run_prune(args))

    # Wave 30 (v0.26.0): forward compression verb. Anchor #4 service.
    if args.command == "compress":
        from myco.compress_cmd import run_compress
        sys.exit(run_compress(args))

    # Wave 31: reverse compression verb. Closes Wave 30 L4 limitation.
    if args.command == "uncompress":
        from myco.compress_cmd import run_uncompress
        sys.exit(run_uncompress(args))

    # Wave 35 (v0.27.0): Metabolic Inlet primitive. Anchor #3 service.
    # Closes the longest-deferred gap (declared Wave 10, scaffolded Wave 34).
    if args.command == "inlet":
        from myco.inlet_cmd import run_inlet
        sys.exit(run_inlet(args))

    if args.command == "forage":
        from myco.forage_cmd import run_forage
        sys.exit(run_forage(args))

    if args.command == "upstream":
        from myco.upstream_cmd import run_upstream
        sys.exit(run_upstream(args))


if __name__ == "__main__":
    main()
