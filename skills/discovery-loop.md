# Discovery Loop — Proactive Knowledge Acquisition Skill

> Wave D2. The organism doesn't wait for food to arrive — it hunts.

## When to Execute

- During metabolic cycle (after hunger check, before session work)
- When `myco_hunger` reports `inlet_ripe` or `cohort_staleness`
- When `myco_colony(action="gaps")` returns non-empty results

## Steps

1. **Detect gaps**: Call `myco_colony(action="gaps")` to get prioritized knowledge gaps.
2. **For each candidate** (top 3 by priority):
   a. **Search**: Use WebSearch to find relevant sources (papers, docs, articles)
   b. **Evaluate**: Is the source relevant (≥0.6)? Is it high quality? Is it novel (not already in substrate)?
   c. **Ingest**: If passes evaluation, call `myco_absorb` with the content + provenance
   d. **Log**: Record the decision in `myco_trace` (what was found, why ingested/rejected)
3. **Verify**: Call `myco_hunger` to confirm signals improved.

## Constraints

- Max 3 ingestions per session (prevent bloat)
- Always check `myco_sense` first to avoid duplicates
- Redact secrets before ingesting (automatic via inlet provenance)
- Log ALL decisions (ingested AND rejected) for auditability

## Bitter Lesson Compliance

This skill is a PROTOCOL, not code. The Agent's intelligence decides:
- What to search for (derived from gap descriptions)
- Whether a source is relevant (Agent judgment, not keyword matching)
- How to extract useful knowledge (Agent summarization)
Myco provides: gap detection, ingestion pipeline, audit trail.

## References

- src/myco/cohorts.py — implementation of `myco_colony` gap detection and analysis
- `docs/open_problems.md` — cold-start problem and other open questions that motivate discovery
- `notes/` (tag: `inlet`) — ingested notes produced by this loop; search with `myco_observe --status raw --tag inlet`
