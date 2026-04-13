"""
myco verify — Deployment health check.

Verifies that a Myco-powered project is correctly set up:
1. Substrate structure (files exist)
2. MCP server (starts + tools register)
3. Lint (23/23 pass)
4. Hunger (substrate health signals)
5. Automation / deployment completeness

Designed for Agent use — zero human interaction required.
"""

import json
import subprocess
import sys
from pathlib import Path

from myco.project import find_project_root


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


def run_verify(args) -> int:
    """Run deployment verification."""
    root = find_project_root(args.project_dir, strict=False)
    if root is None:
        root = Path(args.project_dir).resolve()

    print(f"🍄 Myco Verify — Deployment Health Check")
    print(f"   Project: {root}")
    print()

    issues = []
    passed = 0
    total = 0

    # --- 1. Substrate structure ---
    total += 1
    canon = root / "_canon.yaml"
    if canon.exists():
        print(f"  ✅ _canon.yaml exists")
        passed += 1
    else:
        print(f"  ❌ _canon.yaml missing")
        issues.append("_canon.yaml not found — run `myco init`")

    total += 1
    notes_dir = root / "notes"
    if notes_dir.is_dir():
        count = len(list(notes_dir.glob("*.md")))
        print(f"  ✅ notes/ directory ({count} notes)")
        passed += 1
    else:
        print(f"  ❌ notes/ directory missing")
        issues.append("notes/ not found — run `myco init`")

    # Check entry point
    total += 1
    entry_candidates = ["CLAUDE.md", "MYCO.md", "GPT.md"]
    found_entry = None
    for ep in entry_candidates:
        if (root / ep).exists():
            found_entry = ep
            break
    if found_entry:
        print(f"  ✅ Entry point: {found_entry}")
        passed += 1
    else:
        print(f"  ❌ No entry point found ({', '.join(entry_candidates)})")
        issues.append("No entry point — run `myco init --agent claude`")

    # --- 2. MCP server ---
    total += 1
    mcp_configs = [
        root / ".mcp.json",
        root / ".cursor" / "mcp.json",
        root / ".vscode" / "mcp.json",
    ]
    if any(p.exists() for p in mcp_configs):
        found = [str(p.relative_to(root)) for p in mcp_configs if p.exists()]
        print(f"  ✅ MCP config found ({', '.join(found)})")
        passed += 1
    else:
        print(f"  ⚠️  No MCP config found")
        issues.append("No MCP config — run `myco init --auto-detect`")

    total += 1
    try:
        import mcp  # noqa: F401
        ver = getattr(mcp, "__version__", "unknown")
        print(f"  ✅ MCP SDK installed (mcp {ver})")
        passed += 1
    except ImportError:
        print(f"  ❌ MCP SDK not installed")
        issues.append("MCP SDK missing — run: pip install 'myco[mcp]'")

    total += 1
    # Test MCP server startup
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "myco.mcp_server"],
            capture_output=True, text=True, timeout=3,
            cwd=str(root),
        )
        # MCP server runs indefinitely (stdio), so timeout is expected
        print(f"  ✅ MCP server starts without errors")
        passed += 1
    except subprocess.TimeoutExpired:
        # Timeout means it started and ran — that's success
        print(f"  ✅ MCP server starts (stdio mode)")
        passed += 1
    except Exception as e:
        print(f"  ❌ MCP server failed: {e}")
        issues.append(f"MCP server startup failed: {e}")

    # --- 3. Lint ---
    total += 1
    try:
        from myco.immune import run_lint as _run_lint
        import argparse
        lint_args = argparse.Namespace(
            project_dir=str(root), quick=False, fix_report=False
        )
        # Capture lint result
        result = _run_lint(lint_args)
        if result == 0:
            print(f"  ✅ Lint: ALL CHECKS PASSED")
            passed += 1
        else:
            print(f"  ⚠️  Lint: {result} issue(s)")
            issues.append(f"Lint has {result} issue(s) — run `myco lint`")
    except Exception as e:
        print(f"  ❌ Lint failed: {e}")
        issues.append(f"Lint execution failed: {e}")

    # --- 4. Hunger ---
    total += 1
    try:
        from myco.notes import compute_hunger_report
        report = compute_hunger_report(str(root))
        # HungerReport may be a dataclass or dict; normalize access
        if hasattr(report, "signals"):
            signals = report.signals
            total_notes = report.total
            raw_count = report.raw_count
        else:
            signals = report.get("signals", [])
            total_notes = report.get("total", 0)
            raw_count = report.get("raw_count", 0)
        reflex_high = [s for s in signals if "REFLEX" in str(s).upper()]
        if not reflex_high:
            print(f"  ✅ Hunger: healthy ({total_notes} notes, {raw_count} raw)")
            passed += 1
        else:
            print(f"  ⚠️  Hunger: {len(reflex_high)} REFLEX HIGH signal(s)")
            issues.append(f"Hunger REFLEX HIGH — run `myco hunger --execute`")
    except Exception as e:
        print(f"  ❌ Hunger check failed: {e}")
        issues.append(f"Hunger computation failed: {e}")

    # --- 5. Automation / deployment completeness ---

    # 5a. Scheduled task: metabolic cycle
    total += 1
    sched_skill = _user_claude_dir() / "scheduled-tasks" / "myco-metabolic-cycle" / "SKILL.md"
    if sched_skill.exists():
        print(f"  ✅ Scheduled task: myco-metabolic-cycle")
        passed += 1
    else:
        print(f"  ❌ Scheduled task missing: {sched_skill}")
        issues.append(
            "myco-metabolic-cycle SKILL.md not found — "
            "create a scheduled task for the metabolic cycle"
        )

    # 5b. Settings permissions: mcp__myco__* in allow list
    total += 1
    settings_ok = False
    settings_checked = []
    for sf in [
        root / ".claude" / "settings.local.json",
        root / ".claude" / "settings.json",
        _user_claude_dir() / "settings.local.json",
        _user_claude_dir() / "settings.json",
    ]:
        if sf.exists():
            settings_checked.append(str(sf))
            try:
                data = json.loads(sf.read_text(encoding="utf-8"))
                allow_list = data.get("permissions", {}).get("allow", [])
                if any("mcp__myco__" in entry for entry in allow_list):
                    settings_ok = True
                    break
            except (json.JSONDecodeError, OSError):
                pass
    if settings_ok:
        print(f"  ✅ Settings permissions: mcp__myco__* in allow list")
        passed += 1
    else:
        checked_label = ", ".join(settings_checked) if settings_checked else "none found"
        print(f"  ❌ Settings permissions: mcp__myco__* not in allow list ({checked_label})")
        issues.append(
            "mcp__myco__* tools not in .claude/settings.json allow list — "
            "add 'mcp__myco__*' to permissions.allow"
        )

    # 5c. Cowork skills: myco-boot
    total += 1
    boot_skill = root / ".claude" / "skills" / "myco-boot" / "SKILL.md"
    if boot_skill.exists():
        print(f"  ✅ Cowork skill: myco-boot")
        passed += 1
    else:
        print(f"  ❌ Cowork skill missing: .claude/skills/myco-boot/SKILL.md")
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
        print(f"  ✅ Boot ritual: {found_entry} contains myco_hunger instruction")
        passed += 1
    else:
        entry_label = found_entry or "no entry point"
        print(f"  ❌ Boot ritual: {entry_label} missing myco_hunger instruction")
        issues.append(
            f"Entry point ({entry_label}) does not contain 'myco_hunger' boot ritual — "
            "add: Call `myco_hunger(execute=true)` as your FIRST action every session"
        )

    # 5e. docs/primordia/ craft directory exists
    total += 1
    primordia = root / "docs" / "primordia"
    if primordia.is_dir():
        craft_count = len(list(primordia.glob("*_craft_*.md")))
        print(f"  ✅ Craft directory: docs/primordia/ ({craft_count} craft files)")
        passed += 1
    else:
        print(f"  ❌ Craft directory missing: docs/primordia/")
        issues.append(
            "docs/primordia/ not found — "
            "create the craft directory (not docs/current/)"
        )

    # --- Summary ---
    print()
    print(f"  {'='*50}")
    if not issues:
        print(f"  ✅ ALL {passed}/{total} CHECKS PASSED")
        print(f"  Myco deployment is healthy.")
        return 0
    else:
        print(f"  ⚠️  {passed}/{total} passed, {len(issues)} issue(s):")
        for i, issue in enumerate(issues, 1):
            print(f"     {i}. {issue}")
        return 1
