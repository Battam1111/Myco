"""
Partition A (Vision Closure, G5) — ``myco introspect`` command.

Engine Self-Evolution: Self-critique scanner for metabolic trends.

Authoritative design: docs/primordia/vision_closure_craft_2026-04-14.md §G5.

Usage:
    myco introspect [--project-dir .]
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime
from typing import Any

from myco.metabolism import read_metabolism_log, detect_worsening_metrics
from myco.project import resolve_project_dir




def run_introspect(args: Any) -> int:
    """Dispatch ``myco introspect`` subcommand.

    Reads metabolism.jsonl, detects worsening trends, outputs report.
    """
    root = resolve_project_dir(args, strict=False)

    entries = read_metabolism_log(root, lookback_days=30)
    if not entries:
        print("No metabolism data found. Run `myco hunger` a few times first.")
        return 0

    analysis = detect_worsening_metrics(entries)

    # Write report to docs/primordia/
    docs_dir = root / "docs" / "primordia"
    docs_dir.mkdir(parents=True, exist_ok=True)

    report_filename = (
        f"introspect_{datetime.now().strftime('%Y-%m-%dT%H%M%S')}.md"
    )
    report_path = docs_dir / report_filename

    worsening = analysis.get("worsening", [])
    stagnant = analysis.get("stagnant_signals", [])
    suspects = analysis.get("suspect_files", [])

    report_lines = [
        f"# Myco Self-Critique Report",
        f"\n> Generated: {datetime.now().isoformat()}",
        f"\n## Worsening Metrics",
    ]

    if worsening:
        for metric, descr in worsening:
            report_lines.append(f"- **{metric}**: {descr}")
    else:
        report_lines.append("(no worsening trends detected)")

    report_lines.extend([
        f"\n## Stagnant Signals",
    ])

    if stagnant:
        for signal_name, count in stagnant:
            report_lines.append(f"- **{signal_name}**: fired {count}+ times without resolution")
    else:
        report_lines.append("(no stagnant signals)")

    report_lines.extend([
        f"\n## Suspect Code Modules",
    ])

    if suspects:
        for module, reason in suspects:
            report_lines.append(f"- **{module}**: {reason}")
    else:
        report_lines.append("(no suspect modules identified)")

    report_lines.extend([
        f"\n## Recommended Investigation",
        f"",
        f"This report is automatically generated and serves as a starting point for human",
        f"or agent-driven investigation. No code changes are proposed here — that requires",
        f"explicit craft discussion. See docs/WORKFLOW.md for next steps.",
    ])

    report_text = "\n".join(report_lines) + "\n"
    try:
        report_path.write_text(report_text, encoding="utf-8")
        print(f"Report written to: {report_path}")
    except Exception as e:
        print(f"Error writing report: {e}", file=sys.stderr)
        return 1

    # Also print summary to stdout
    print(f"\n[Introspect Summary]")
    print(f"Metabolism entries analyzed: {len(entries)}")
    print(f"Worsening metrics: {len(worsening)}")
    print(f"Stagnant signals: {len(stagnant)}")
    print(f"Suspect modules: {len(suspects)}")

    return 0
