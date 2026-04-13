# Sprint Pipeline — Myco-Native Development Loop

> Absorbed from gstack sprint methodology, adapted to Myco's metabolic model.

## When to Execute

At the start of any non-trivial development task (feature, bugfix, refactor).

## Pipeline Steps

### 1. Think
- `myco_hunger(execute=true)` — substrate health check
- `myco_cohort(action="gaps")` — what knowledge is missing?
- `myco_search` — what does the substrate already know about this topic?

### 2. Plan
- If confidence < 0.80 on approach → start a Craft (structured debate)
- If confidence >= 0.80 → write a brief plan in `myco_eat` note
- Read traceability index before touching kernel surfaces

### 3. Build
- Implement the change
- `myco_eat` each significant decision as it happens
- Use `myco_search` before answering factual questions

### 4. Review
- `myco_lint` — mechanical immune check (23 dims)
- Read Agent Review items — semantic alignment check
- Check traceability index for downstream impact

### 5. Test
- `pytest tests/` — all tests pass
- Verify with evidence (run commands, paste output)

### 6. Ship
- `git commit` with descriptive message
- Contract bump if kernel surfaces changed
- `git push`

### 7. Reflect
- `myco_eat` — capture what worked, what didn't, what surprised
- `myco_reflect` — session-end reflection
- Digest decision notes to extracted
- `myco_hunger` — confirm healthy end state

## Constraint

Every step that changes code must be verified with evidence before claiming "done."
"I think it works" is not evidence. "Here's the output" is.

## References

- `docs/agent_protocol.md` — contract that governs tool trigger conditions used in every pipeline step
- `docs/WORKFLOW.md` — project-level workflow context this pipeline operates within
