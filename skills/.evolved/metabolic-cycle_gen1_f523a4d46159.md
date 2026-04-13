---
{}
---

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
     `myco trace --type friction "MCP tools unavailable, using CLI fallback"`.
2. **Execute each action in order**:
   - `verb: "digest"` → run `myco digest <note_id>` (or bulk if no note_id)
   - `verb: "compress"` → run `myco condense --tag <tag> --rationale "<auto>"` (or `--cohort auto` if args.cohort is present)
   - `verb: "prune"` → run `myco prune --apply`
   - `verb: "inlet"` → log the recommendation for human/agent decision (inlet is not fully autonomous yet)
   - **On tool failure**: Catch the error, log it via `myco trace --type friction`,
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
1. **Log the failure** — `myco trace --type friction "<tool> failed: <error>"`
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
(signals, actions, thresholds); the agent provides the judgment.
