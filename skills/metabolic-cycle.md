# Metabolic Cycle — Boot Ritual Skill

> Wave 50 (contract v0.39.0). This skill replaces the need for a daemon:
> every agent session begins with `myco hunger` → sees actions → executes them.
> The agent IS the daemon. Frequency = session frequency.

## When to execute

At session boot, immediately after `myco hunger` (the second call of every
session per `docs/agent_protocol.md` §3).

## Steps

1. **Read hunger actions**: Run `myco hunger --json` and parse the `actions` array.
2. **Execute each action in order**:
   - `verb: "digest"` → run `myco digest <note_id>` (or bulk if no note_id)
   - `verb: "compress"` → run `myco compress --tag <tag> --rationale "<auto>"` (or `--cohort auto` if args.cohort is present)
   - `verb: "prune"` → run `myco prune --apply`
   - `verb: "inlet"` → log the recommendation for human/agent decision (inlet is not fully autonomous yet)
3. **Re-check hunger**: Run `myco hunger` again to confirm pressure reduced.
4. **Proceed with session work** once hunger reports healthy or only low-severity signals.

4. **Discover** (Wave D2): If hunger signals include `inlet_ripe` or `cohort_staleness`,
   run the Discovery Loop skill (`skills/discovery-loop.md`) to proactively acquire
   external knowledge for detected gaps.

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
