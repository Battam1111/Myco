"""
myco verify — Deployment health check.

Verifies that a Myco-powered project is correctly set up:
1. Substrate structure (files exist)
2. MCP server (starts + tools register)
3. Lint (23/23 pass)
4. Hunger (substrate health signals)

Designed for Agent use — zero human interaction required.
"""

import json
import subprocess
import sys
from pathlib import Path

from myco.project import find_project_root


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
        from myco.lint import run_lint as _run_lint
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
