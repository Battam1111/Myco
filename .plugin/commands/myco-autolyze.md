---
description: "Sweep substrate for stale narrative references (version drift, deleted module paths, deprecated identifiers, numeric drift) via the autolysis subagent. Returns a deterministic patch table; does not apply patches."
argument-hint: "[category-filter]"
---

The user wants a stale-narrative sweep. Argument (if any): $ARGUMENTS

If $ARGUMENTS is empty: full sweep across all 5 categories (stale_version / stale_path / stale_identifier / numeric_drift / test_count).

If $ARGUMENTS is one of the category names: scope the sweep to that category only.

Dispatch the **autolysis** subagent (defined at `.claude/agents/autolysis.md`). Pass the category filter (if any) as the dynamic input. The subagent will:

1. Establish ground truth: read live `__version__`, verb count from manifest, dim count from `_canon_lint.yaml`, test count from `pytest --collect-only`, subsystem count from `_canon.yaml::subsystems`.
2. Run targeted Greps within the category scope, honoring the exclusion list (legacy_v0_3, notes/integrated/n_*, contract_changelog past sections, _excreted, etc.).
3. For each candidate, Read for context to confirm true staleness.
4. Produce a patch table: file:line:stale_string → replacement, classified by category.
5. Cap output at 100 findings; if cap hit, recommend the user split by category.
6. Surface (without proposing patches) any L0/L1/L2 doctrine hits — those require a craft, not a sweep.

When autolysis returns, relay the patch table verbatim to the user.

Do NOT apply any of the proposed patches yourself. The user reviews and approves (or applies in a separate turn). The patch table is the deliverable.
