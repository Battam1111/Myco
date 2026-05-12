---
description: "Investigate one or more myco_immune findings via the hypha subagent (root-cause trace + minimal-fix proposal). Read-only; does not apply fixes."
argument-hint: "[finding-id-or-pattern]"
---

The user wants to investigate immune findings. Argument (if any): $ARGUMENTS

If $ARGUMENTS is empty or "all": run `myco immune` first, parse findings, then for each finding (capped at 10) invoke the hypha subagent to investigate.

If $ARGUMENTS is a dim ID like `SE2` or `MB6`: investigate every current finding for that dim.

If $ARGUMENTS is a path pattern (e.g., `notes/integrated/n_*`): investigate every current finding whose location matches the pattern.

For each invocation, dispatch the **hypha** subagent (defined at `.claude/agents/hypha.md`). Pass the finding's full record (dim id, severity, path, message) as the dynamic input. The subagent will:

1. Run `myco immune --explain <DIM_ID>` to load the dim's intent.
2. Read the cited file + run Grep to trace cross-references.
3. Classify root cause (5 categories: stale_narrative / doctrine_drift / missing_implementation / false_positive / real_defect).
4. Propose a minimal patch description (file path + before/after snippet + rationale).
5. Note any follow-up that should route to autolysis or primordium.

After all hypha invocations complete, aggregate the reports into a single summary table: finding-count by classification, root-cause clusters, recommended fix priority order.

Do NOT apply any patches. The user reviews and applies (or routes to a separate fix turn).
