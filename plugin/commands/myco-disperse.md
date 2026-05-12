---
description: "Run the full Myco release pipeline (pre-flight + bump + commit + push + tag + ci.yml + release.yml + post-release verification) via the stipe subagent. Spores disperse from the cap once the stipe holds it aloft."
argument-hint: "<target-version>"
---

The user is shipping Myco at version: $ARGUMENTS

If $ARGUMENTS is empty or not a clean PEP 440 string (regex `^\d+\.\d+\.\d+(?:[.-]post\d+)?$`), refuse and ask the user for an explicit version like `0.6.11` or `0.7.0`.

Dispatch the **stipe** subagent (defined at `.claude/agents/stipe.md`). Pass the target version string as the only dynamic input. The subagent will:

1. **Phase 1 (baseline)**: confirm clean worktree; confirm target version is fresh on PyPI (paranoia check); confirm current `__version__`.
2. **Phase 2 (pre-flight gate)**: ruff check + ruff format check + mypy + pytest -q -x + myco immune + verify_mcp_boot.py. ALL must exit 0.
3. **Phase 3 (build dry-run)**: `py -m build && py -m twine check dist/*`.
4. **Phase 4 (atomic bump)**: `py scripts/bump_version.py --to <TARGET>` — runs molt + the gate quintet automatically.
5. **Phase 5 (auto-stub discard)**: scan `docs/contract_changelog.md` for the molt-generated stub block (heading shape `## v<X.Y.Z> - <date> - Contract molt via myco molt` containing `(Fill in: ...)` placeholders) and delete it via Edit, leaving only the curated v<TARGET> entry.
6. **Phase 6 (commit)**: stage all + atomic commit using the canonical v<TARGET> commit message template.
7. **Phase 7 (push main + ci.yml watch)**: push origin main; watch ci.yml exit-status.
8. **Phase 8 (tag + release.yml watch)**: tag v<TARGET>; push tag; watch release.yml exit-status.
9. **Phase 9 (post-release verification)**: PyPI JSON API check; gh release view; MCP Registry curl; fresh-venv smoke install (pip install + mcp-server-myco --help).

If ANY phase fails, the subagent halts and reports the failing phase + the recovery procedure.

When stipe returns, relay its full structured report verbatim to the user, including:
- Pipeline phase-by-phase status
- URLs (PyPI, GitHub Release, ci.yml run, release.yml run)
- Final SHIPPED / REFUSED / PARTIAL verdict

Do NOT second-guess stipe's halt decisions — the subagent's halt-on-fail logic is intentional. If stipe halts at Phase 2 with an immune CRITICAL finding, the user needs to fix that finding (perhaps via `/myco-hypha`) before retrying `/myco-disperse`.

Do NOT push or tag yourself if stipe halts. You are the orchestrator, not the executor.
