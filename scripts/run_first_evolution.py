#!/usr/bin/env python3
"""First real execution of Myco's skill evolution system.

This script exercises the full evolve.py code path on the
metabolic-cycle.md skill. Since mutate_skill requires an llm_fn
callable and we cannot invoke an LLM from a standalone script, we
create the mutation manually but use the SkillVariant dataclass
structure to track it properly through all constraint gates.

Mutation: Add error handling for when MCP tools are unavailable.
Target:  skills/metabolic-cycle.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure src/ is importable
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from myco.evolve import (
    SkillVariant,
    check_gates,
    diff_variants,
    export_evolved_skill,
    mutate_skill,
    parse_skill,
    serialize_skill,
)


def main() -> int:
    skill_path = REPO_ROOT / "skills" / "metabolic-cycle.md"
    if not skill_path.exists():
        print(f"ERROR: skill not found at {skill_path}")
        return 1

    # ------------------------------------------------------------------
    # Step 1: Parse the original skill
    # ------------------------------------------------------------------
    print("=" * 60)
    print("STEP 1: Parse original skill")
    print("=" * 60)
    original = parse_skill(skill_path)
    print(f"  Name:        {original.meta.get('name', '(no name in frontmatter)')}")
    print(f"  Body length: {len(original.body)} chars")
    print(f"  Hash:        {original.content_hash}")
    print(f"  Generation:  {original.generation}")
    print()

    # ------------------------------------------------------------------
    # Step 2: Exercise mutate_skill with a mock llm_fn
    # ------------------------------------------------------------------
    print("=" * 60)
    print("STEP 2: Exercise mutate_skill() with mock llm_fn")
    print("=" * 60)

    # The mock llm_fn returns the manually-crafted mutation body.
    # This is the improved version with error handling for MCP tool
    # unavailability -- a real improvement that makes the skill more
    # robust in production.
    MUTATED_BODY = """\
# Metabolic Cycle — Boot Ritual Skill

> Wave 50 (contract v0.39.0). This skill replaces the need for a daemon:
> every agent session begins with `myco hunger` → sees actions → executes them.
> The agent IS the daemon. Frequency = session frequency.

## When to execute

At session boot, immediately after `myco hunger` (the second call of every
session per `docs/agent_protocol.md` §3).

## Steps

1. **Read hunger actions**: Run `myco hunger --json` and parse the `actions` array.
   - **If MCP tools are unavailable**: Fall back to direct CLI invocation
     (`python -m myco.mcp_server hunger`). Log a friction entry via
     `myco log --type friction "MCP tools unavailable, using CLI fallback"`.
2. **Execute each action in order**:
   - `verb: "digest"` → run `myco digest <note_id>` (or bulk if no note_id)
   - `verb: "compress"` → run `myco compress --tag <tag> --rationale "<auto>"` (or `--cohort auto` if args.cohort is present)
   - `verb: "prune"` → run `myco prune --apply`
   - `verb: "inlet"` → log the recommendation for human/agent decision (inlet is not fully autonomous yet)
   - **On tool failure**: Catch the error, log it via `myco log --type friction`,
     skip the failed action, and continue with the remaining actions.
     Do NOT abort the entire cycle for a single action failure.
3. **Re-check hunger**: Run `myco hunger` again to confirm pressure reduced.
   - **If re-check fails**: Log the failure but still proceed to session work.
     A stale hunger reading is better than a blocked session.
4. **Proceed with session work** once hunger reports healthy or only low-severity signals.

4. **Discover** (Wave D2): If hunger signals include `inlet_ripe` or `cohort_staleness`,
   run the Discovery Loop skill (`skills/discovery-loop.md`) to proactively acquire
   external knowledge for detected gaps.

5. **Evolve** (Wave E2): If `_canon.yaml::system.evolution.enabled` is true
   AND session count > `min_sessions_before_evolve`, check skill performance.
   If any skill's success rate < `skill_success_threshold`, call `evolve.mutate_skill`
   with the Agent's llm_fn, run constraint gates, score, and if improved,
   atomically replace + git commit. Max `max_mutations_per_cycle` per run.

## Error Handling

When any MCP tool call fails during the metabolic cycle:
1. **Log the failure** — `myco log --type friction "<tool> failed: <error>"`
2. **Try CLI fallback** — if the MCP server is down, invoke via `python -m myco.mcp_server`
3. **Skip and continue** — a single failed action must not block the rest of the cycle
4. **Report at end** — summarize all failures in the session's closing hunger re-check

## Thresholds

All thresholds are in `_canon.yaml`:
- `system.boot_reflex.raw_backlog_threshold` — triggers digest action
- `system.notes_schema.compression.pressure_threshold` — triggers compress action (default 2.0)
- `system.notes_schema.compression.ripe_threshold` / `ripe_age_days` — triggers compression_ripe
- `system.inlet_triggers.search_miss_threshold` / `gap_threshold` — triggers inlet_ripe

## Bitter Lesson compliance

This skill is a **procedure**, not code. The agent's intelligence decides
whether and how to execute each step. If the agent improves, execution
improves — without changing this document. Myco provides the scaffolding
(signals, actions, thresholds); the agent provides the judgment."""

    def mock_llm_fn(prompt: str) -> str:
        """Mock LLM that returns the manually-crafted mutation."""
        return MUTATED_BODY

    mutated = mutate_skill(
        skill_path,
        "Add error handling for when MCP tools are unavailable",
        llm_fn=mock_llm_fn,
    )

    print(f"  Mutated body length: {len(mutated.body)} chars")
    print(f"  Mutated hash:        {mutated.content_hash}")
    print(f"  Parent hash:         {mutated.parent_hash}")
    print(f"  Generation:          {mutated.generation}")
    print(f"  Meta preserved:      {mutated.meta == original.meta}")
    print()

    # ------------------------------------------------------------------
    # Step 3: Run constraint gates
    # ------------------------------------------------------------------
    print("=" * 60)
    print("STEP 3: Run check_gates()")
    print("=" * 60)
    failures = check_gates(original, mutated)
    if failures:
        print(f"  GATE FAILURES ({len(failures)}):")
        for f in failures:
            print(f"    - {f}")
        print("\n  Mutation REJECTED by gates.")
        return 1
    else:
        print("  All gates PASSED:")
        print("    - frontmatter_preserved: OK")
        print("    - body_nonempty: OK")
        print("    - no_secret_leak: OK")
        print("    - size_growth: OK")
    print()

    # ------------------------------------------------------------------
    # Step 4: Compute structured diff
    # ------------------------------------------------------------------
    print("=" * 60)
    print("STEP 4: diff_variants()")
    print("=" * 60)
    diff = diff_variants(original, mutated)
    for k, v in diff.items():
        print(f"  {k}: {v}")
    print()

    # ------------------------------------------------------------------
    # Step 5: Export as upstream-compatible bundle
    # ------------------------------------------------------------------
    print("=" * 60)
    print("STEP 5: export_evolved_skill()")
    print("=" * 60)
    bundle = export_evolved_skill(
        mutated,
        source_project="Myco",
        evolution_metrics={
            "mutation_prompt": "Add error handling for when MCP tools are unavailable",
            "gates_passed": True,
            "gate_count": 4,
        },
    )
    print(f"  Bundle type:    {bundle['type']}")
    print(f"  Bundle version: {bundle['version']}")
    print(f"  Content hash:   {bundle['content_hash']}")
    print(f"  Generation:     {bundle['generation']}")
    print(f"  Source:         {bundle['source_project']}")
    print()

    # ------------------------------------------------------------------
    # Step 6: Save the evolved variant
    # ------------------------------------------------------------------
    print("=" * 60)
    print("STEP 6: Save evolved variant")
    print("=" * 60)
    output_dir = REPO_ROOT / "skills" / ".evolved"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"metabolic-cycle_gen{mutated.generation}_{mutated.content_hash}.md"
    output_path.write_text(serialize_skill(mutated), encoding="utf-8")
    print(f"  Saved to: {output_path}")
    print()

    # Also save the bundle as JSON for cross-instance transfer
    bundle_path = output_dir / f"metabolic-cycle_gen{mutated.generation}_{mutated.content_hash}.bundle.json"
    bundle_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print(f"  Bundle:   {bundle_path}")
    print()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("=" * 60)
    print("EVOLUTION COMPLETE")
    print("=" * 60)
    print(f"  Skill:      metabolic-cycle.md")
    print(f"  Mutation:   Add error handling for MCP tool unavailability")
    print(f"  Gates:      4/4 passed")
    print(f"  Size delta: +{diff['size_delta']} chars ({diff['size_delta'] / max(diff['old_body_len'], 1):.1%} growth)")
    print(f"  Lineage:    gen {original.generation} ({original.content_hash}) -> gen {mutated.generation} ({mutated.content_hash})")
    print(f"  Output:     {output_path.relative_to(REPO_ROOT)}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
