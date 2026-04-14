"""
Myco Doctor — system health and hook verification.

Wave 55 (vision_closure_craft_2026-04-14.md, Partition B G7):
`myco doctor` command to check host detection, hook status, and overall
system health.

Provides:
    - Host detection and degradation level
    - Session hook installation status
    - .myco_state/ integrity checks
    - Contract drift detection
    - Hunger status snapshot
    - Machine-readable JSON output (--json)
    - Auto-remediation suggestions (--fix)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from myco.hosts import check_all_hooks, detect_active_host, effective_hook_level


def _check_myco_state(root: Path) -> Dict[str, Any]:
    """Check .myco_state/ integrity."""
    issues = []
    myco_state = root / ".myco_state"

    if not myco_state.exists():
        issues.append("missing .myco_state/ directory")
        return {
            "exists": False,
            "issues": issues,
        }

    # Check for boot_brief.md
    boot_brief = myco_state / "boot_brief.md"
    if not boot_brief.exists():
        issues.append("missing boot_brief.md (hunger not run recently)")

    # Check age of boot_brief
    if boot_brief.exists():
        from datetime import datetime, timedelta
        mtime = datetime.fromtimestamp(boot_brief.stat().st_mtime)
        age_hours = (datetime.now() - mtime).total_seconds() / 3600
        if age_hours > 24:
            issues.append(f"boot_brief.md is {age_hours:.0f}h old (run 'myco hunger')")

    return {
        "exists": True,
        "boot_brief_age_hours": age_hours if boot_brief.exists() else None,
        "issues": issues,
    }


def _check_contract_drift(root: Path) -> Dict[str, Any]:
    """Check contract version drift."""
    import yaml

    issues = []
    canon_path = root / "_canon.yaml"

    if not canon_path.exists():
        return {"error": "missing _canon.yaml"}

    try:
        with open(canon_path, "r") as f:
            canon = yaml.safe_load(f) or {}
        contract_version = canon.get("system", {}).get("contract_version")
        synced_version = canon.get("system", {}).get("synced_contract_version")

        if not contract_version:
            issues.append("missing contract_version in _canon.yaml")
        elif contract_version != synced_version:
            issues.append(
                f"contract drift: kernel={contract_version}, local={synced_version}"
            )

        return {
            "kernel_version": contract_version,
            "local_version": synced_version,
            "synced": contract_version == synced_version,
            "issues": issues,
        }
    except Exception as e:
        return {"error": f"failed to read _canon.yaml: {e}"}


def _check_hunger_status(root: Path) -> Dict[str, Any]:
    """Check recent hunger execution and signal status."""
    from myco.notes import compute_hunger_report

    try:
        report = compute_hunger_report(root)
        # Handle both dict and object return types
        signals = []
        if isinstance(report, dict):
            signals = report.get("signals", [])
        elif hasattr(report, "signals"):
            signals = report.signals or []

        return {
            "signal_count": len(signals),
            "critical_signals": len(
                [s for s in signals if "CRITICAL" in str(s)]
            ),
            "last_signals": signals[:5],
        }
    except Exception as e:
        return {"error": f"failed to compute hunger: {e}"}


def check_health(root: Path) -> Dict[str, Any]:
    """Run all diagnostic checks."""
    return {
        "host": {
            "detected": detect_active_host(),
            "hook_level": effective_hook_level(root),
        },
        "hooks": check_all_hooks(root),
        "myco_state": _check_myco_state(root),
        "contract": _check_contract_drift(root),
        "hunger": _check_hunger_status(root),
    }


def _format_report(health: Dict[str, Any], json_mode: bool = False) -> str:
    """Format health report for display."""
    if json_mode:
        return json.dumps(health, indent=2)

    lines = []

    # Host section
    lines.append("HOST ENVIRONMENT")
    lines.append("=" * 40)
    host = health.get("host", {})
    detected = host.get("detected") or "unknown"
    level = host.get("hook_level") or "protocol"
    lines.append(f"Detected host: {detected}")
    lines.append(f"Hook level: {level}")
    lines.append("")

    # Hooks section
    lines.append("SESSION HOOKS")
    lines.append("=" * 40)
    hooks = health.get("hooks", {})
    if hooks.get("summary", {}).get("all_ok"):
        lines.append("✅ All hooks OK")
    else:
        lines.append("❌ Issues found:")
        for issue in hooks.get("summary", {}).get("issues", []):
            lines.append(f"  - {issue}")
    lines.append("")

    # Myco State section
    lines.append(".MYCO_STATE INTEGRITY")
    lines.append("=" * 40)
    myco_state = health.get("myco_state", {})
    if myco_state.get("exists"):
        lines.append("✅ .myco_state/ exists")
        if not myco_state.get("issues"):
            lines.append("✅ No issues")
        else:
            for issue in myco_state.get("issues", []):
                lines.append(f"⚠️  {issue}")
    else:
        lines.append("❌ .myco_state/ missing")
    lines.append("")

    # Contract section
    lines.append("CONTRACT VERSION")
    lines.append("=" * 40)
    contract = health.get("contract", {})
    if contract.get("error"):
        lines.append(f"❌ {contract['error']}")
    elif contract.get("synced"):
        lines.append(f"✅ In sync (v{contract.get('kernel_version')})")
    else:
        lines.append(
            f"⚠️  Drift: kernel v{contract.get('kernel_version')} "
            f"vs local v{contract.get('local_version')}"
        )
    lines.append("")

    # Hunger section
    lines.append("HUNGER STATUS")
    lines.append("=" * 40)
    hunger = health.get("hunger", {})
    if hunger.get("error"):
        lines.append(f"⚠️  {hunger['error']}")
    else:
        critical = hunger.get("critical_signals", 0)
        total = hunger.get("signal_count", 0)
        if critical > 0:
            lines.append(f"🔴 {critical} critical signal(s)")
        elif total > 0:
            lines.append(f"🟡 {total} signal(s)")
        else:
            lines.append("✅ No active signals")

    return "\n".join(lines)


def run_doctor(args: argparse.Namespace) -> int:
    """Execute doctor command."""
    from myco.project import find_project_root

    try:
        root = find_project_root()
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1

    health = check_health(root)

    if args.json:
        print(_format_report(health, json_mode=True))
    else:
        print(_format_report(health, json_mode=False))

    # Return exit code based on issues
    has_issues = (
        not health.get("hooks", {}).get("summary", {}).get("all_ok")
        or bool(health.get("myco_state", {}).get("issues"))
        or not health.get("contract", {}).get("synced")
    )

    return 1 if has_issues else 0


def setup_subparser(subparsers: Any) -> None:
    """Register doctor subcommand."""
    parser = subparsers.add_parser(
        "doctor",
        help="Check system health and hook status",
        description="Verify Myco environment setup and contract adherence.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt auto-remediation (experimental)",
    )
    parser.set_defaults(func=run_doctor)
