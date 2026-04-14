"""
myco pulse — System health diagnostics and deployment verification.

Merges doctor (session-hook health) and diagnose (deployment completeness)
into a unified health check command.

Merged from:
  - doctor_cmd.py: host detection, hook status, contract drift, hunger signals
  - diagnose_cmd.py: MCP server, lint, substrate integrity, automation setup

Wave 56 (architecture refactor, merged 2026-04-14):
Consolidates two redundant health-check commands into one unified `pulse`.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional


# ============================================================================
# SESSION HOOK & HOST DIAGNOSTICS (from doctor)
# ============================================================================

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
        from datetime import datetime
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
        with open(canon_path, "r", encoding="utf-8") as f:
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


# ============================================================================
# DEPLOYMENT VERIFICATION (from diagnose)
# ============================================================================

def _resolve_claude_dir(root: Path) -> Path:
    """Return the .claude directory for the project.

    Checks project-level first, then falls back to user-level (~/.claude).
    """
    project_claude = root / ".claude"
    if project_claude.is_dir():
        return project_claude
    return Path.home() / ".claude"


def _user_claude_dir() -> Path:
    """Return the user-level ~/.claude directory."""
    return Path.home() / ".claude"


def _verify_deployment(root: Path) -> Dict[str, Any]:
    """Run full deployment verification (from diagnose_cmd.run_verify)."""
    issues = []
    passed = 0
    total = 0

    # --- 1. Substrate structure ---
    total += 1
    canon = root / "_canon.yaml"
    if canon.exists():
        passed += 1
    else:
        issues.append("_canon.yaml not found — run `myco seed`")

    total += 1
    notes_dir = root / "notes"
    if notes_dir.is_dir():
        passed += 1
    else:
        issues.append("notes/ not found — run `myco seed`")

    # Check entry point
    total += 1
    entry_candidates = ["CLAUDE.md", "MYCO.md", "GPT.md"]
    found_entry = None
    for ep in entry_candidates:
        if (root / ep).exists():
            found_entry = ep
            break
    if found_entry:
        passed += 1
    else:
        issues.append("No entry point — run `myco seed --agent claude`")

    # --- 2. MCP server ---
    total += 1
    mcp_configs = [
        root / ".mcp.json",
        root / ".cursor" / "mcp.json",
        root / ".vscode" / "mcp.json",
    ]
    if any(p.exists() for p in mcp_configs):
        passed += 1
    else:
        issues.append("No MCP config — run `myco seed --auto-detect`")

    total += 1
    try:
        import mcp  # noqa: F401
        passed += 1
    except ImportError:
        issues.append("MCP SDK missing — run: pip install 'myco[mcp]'")

    total += 1
    # Test MCP server startup
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "myco.mcp_server"],
            capture_output=True, text=True, timeout=3,
            cwd=str(root),
        )
        passed += 1
    except subprocess.TimeoutExpired:
        passed += 1  # Timeout means it started
    except Exception as e:
        issues.append(f"MCP server startup failed: {e}")

    # --- 3. Lint ---
    total += 1
    try:
        from myco.immune import run_lint as _run_lint
        import argparse
        lint_args = argparse.Namespace(
            project_dir=str(root), quick=False, fix_report=False
        )
        result = _run_lint(lint_args)
        if result == 0:
            passed += 1
        else:
            issues.append(f"Lint has {result} issue(s) — run `myco immune`")
    except Exception as e:
        issues.append(f"Lint execution failed: {e}")

    # --- 4. Hunger ---
    total += 1
    try:
        from myco.notes import compute_hunger_report
        report = compute_hunger_report(str(root))
        if hasattr(report, "signals"):
            signals = report.signals
        else:
            signals = report.get("signals", [])
        reflex_high = [s for s in signals if "REFLEX" in str(s).upper()]
        if not reflex_high:
            passed += 1
        else:
            issues.append(f"Hunger REFLEX HIGH — run `myco hunger --execute`")
    except Exception as e:
        issues.append(f"Hunger computation failed: {e}")

    # --- 5. Automation / deployment completeness ---

    # 5a. Scheduled task: metabolic cycle
    total += 1
    sched_skill = _user_claude_dir() / "scheduled-tasks" / "myco-metabolic-cycle" / "SKILL.md"
    if sched_skill.exists():
        passed += 1
    else:
        issues.append(
            "myco-metabolic-cycle SKILL.md not found — "
            "create a scheduled task for the metabolic cycle"
        )

    # 5b. Settings permissions: mcp__myco__* in allow list
    total += 1
    settings_ok = False
    for sf in [
        root / ".claude" / "settings.local.json",
        root / ".claude" / "settings.json",
        _user_claude_dir() / "settings.local.json",
        _user_claude_dir() / "settings.json",
    ]:
        if sf.exists():
            try:
                data = json.loads(sf.read_text(encoding="utf-8"))
                allow_list = data.get("permissions", {}).get("allow", [])
                if any("mcp__myco__" in entry for entry in allow_list):
                    settings_ok = True
                    break
            except (json.JSONDecodeError, OSError):
                pass
    if settings_ok:
        passed += 1
    else:
        issues.append(
            "mcp__myco__* tools not in .claude/settings.json allow list — "
            "add 'mcp__myco__*' to permissions.allow"
        )

    # 5c. Cowork skills: myco-boot
    total += 1
    boot_skill = root / ".claude" / "skills" / "myco-boot" / "SKILL.md"
    if boot_skill.exists():
        passed += 1
    else:
        issues.append(
            "myco-boot cowork skill not found — "
            "create .claude/skills/myco-boot/SKILL.md with boot instructions"
        )

    # 5d. Entry point contains boot ritual (myco_hunger)
    total += 1
    boot_ritual_found = False
    if found_entry:
        try:
            content = (root / found_entry).read_text(encoding="utf-8")
            if "myco_hunger" in content or "myco hunger" in content:
                boot_ritual_found = True
        except OSError:
            pass
    if boot_ritual_found:
        passed += 1
    else:
        entry_label = found_entry or "no entry point"
        issues.append(
            f"Entry point ({entry_label}) does not contain 'myco_hunger' boot ritual — "
            "add: Call `myco_hunger(execute=true)` as your FIRST action every session"
        )

    # 5e. docs/primordia/ craft directory exists
    total += 1
    primordia = root / "docs" / "primordia"
    if primordia.is_dir():
        passed += 1
    else:
        issues.append(
            "docs/primordia/ not found — "
            "create the craft directory (not docs/current/)"
        )

    # 5f. External file tool name consistency
    total += 1
    external_stale = []
    try:
        import re as _re
        mcp_path = root / "src" / "myco" / "mcp_server.py"
        if mcp_path.exists():
            mcp_content = mcp_path.read_text(encoding="utf-8", errors="replace")
            actual_tools = set(_re.findall(r'name="(myco_\w+)"', mcp_content))
            actual_mcp = {f"mcp__myco__{t}" for t in actual_tools}

            sched_dir = _user_claude_dir() / "scheduled-tasks"
            if sched_dir.is_dir():
                for skill_file in sched_dir.rglob("SKILL.md"):
                    skill_text = skill_file.read_text(encoding="utf-8", errors="replace")
                    refs = set(_re.findall(r"mcp__myco__myco_\w+", skill_text))
                    stale = refs - actual_mcp
                    for s in stale:
                        external_stale.append(f"{skill_file.name}: {s}")

            skills_dir = root / ".claude" / "skills"
            if skills_dir.is_dir():
                for skill_file in skills_dir.rglob("SKILL.md"):
                    skill_text = skill_file.read_text(encoding="utf-8", errors="replace")
                    refs = set(_re.findall(r"myco_\w+", skill_text))
                    tool_refs = {r for r in refs if r.startswith("myco_") and r != "myco_hunger"}
                    stale = tool_refs - actual_tools - {"myco_hunger"}
                    for s in stale:
                        external_stale.append(f"{skill_file.parent.name}/SKILL.md: {s}")
    except Exception:
        pass

    if not external_stale:
        passed += 1
    else:
        issues.append(
            f"{len(external_stale)} stale tool name(s) in ~/.claude/ files — "
            "re-run `myco seed --auto-detect` or manually update"
        )

    return {
        "passed": passed,
        "total": total,
        "issues": issues,
    }


# ============================================================================
# UNIFIED HEALTH CHECK
# ============================================================================

def check_health(root: Path) -> Dict[str, Any]:
    """Run all diagnostic checks (merged doctor + diagnose)."""
    from myco.symbionts import check_all_hooks, detect_active_symbiont, effective_hook_level

    return {
        "symbiont": {
            "detected": detect_active_symbiont(),
            "hook_level": effective_hook_level(root),
        },
        "hooks": check_all_hooks(root),
        "myco_state": _check_myco_state(root),
        "contract": _check_contract_drift(root),
        "hunger": _check_hunger_status(root),
        "deployment": _verify_deployment(root),
    }


def _format_report(health: Dict[str, Any], json_mode: bool = False) -> str:
    """Format health report for display."""
    if json_mode:
        return json.dumps(health, indent=2)

    lines = []

    # Symbiont section
    lines.append("SYMBIONT ENVIRONMENT")
    lines.append("=" * 40)
    symbiont = health.get("symbiont", {})
    detected = symbiont.get("detected") or "unknown"
    level = symbiont.get("hook_level") or "protocol"
    lines.append(f"Detected symbiont: {detected}")
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
    lines.append("")

    # Deployment section
    lines.append("DEPLOYMENT VERIFICATION")
    lines.append("=" * 40)
    deploy = health.get("deployment", {})
    passed = deploy.get("passed", 0)
    total = deploy.get("total", 0)
    issues = deploy.get("issues", [])
    if not issues:
        lines.append(f"✅ ALL {passed}/{total} CHECKS PASSED")
    else:
        lines.append(f"⚠️  {passed}/{total} passed, {len(issues)} issue(s):")
        for i, issue in enumerate(issues[:5], 1):
            lines.append(f"     {i}. {issue}")

    return "\n".join(lines)


def run_pulse(args: argparse.Namespace) -> int:
    """Execute pulse command."""
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
        or bool(health.get("deployment", {}).get("issues"))
    )

    return 1 if has_issues else 0


def setup_subparser(subparsers: Any) -> None:
    """Register pulse subcommand."""
    parser = subparsers.add_parser(
        "pulse",
        help="System health and deployment verification",
        description="Check Myco environment setup, contract adherence, and deployment completeness.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON",
    )
    parser.add_argument(
        "--project-dir", type=str, default=".",
        help="Project root (default: current directory)",
    )
    parser.set_defaults(func=run_pulse)
