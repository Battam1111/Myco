# Learning Loop — Non-Parametric Learning from Execution

> Absorbed from gstack /retro and /learn patterns.

## When to Execute

- After completing any multi-step task
- At session end (part of metabolic cycle step 7: Reflect)
- When a task failed and was eventually resolved

## Steps

1. **Capture**: `myco_eat` with tag `execution-learning`:
   - What was the task?
   - What approach worked? What didn't?
   - What was surprising or non-obvious?
   - Would you do it differently next time?

2. **Pattern check**: `myco_sense` for similar past learnings.
   - If this is a REPEATED lesson → it should become a skill or a reflex
   - If this is NEW → raw note is sufficient

3. **Skill candidate**: If the same lesson appears 3+ times:
   - Promote to a skill in `skills/`
   - Or add to an existing skill's procedure

4. **Prune stale learnings**: During metabolic cycle, check if old
   execution-learning notes are still relevant. If the pattern has been
   encoded into a skill or lint dimension, excrete the note.

## Bitter Lesson Compliance

This skill captures WHAT the Agent learned, not HOW to learn. The Agent's
intelligence decides what's worth capturing. Myco provides the persistence
layer. If the Agent gets smarter, the learnings get better — without
changing this protocol.

## References

- `src/myco/evolve.py` — evolution engine that promotes repeated learnings into skill mutations
- `skills/metabolic-cycle.md` — metabolic cycle step 7 (Reflect) is when this loop typically fires
