---
type: craft
status: ACTIVE
created: 2026-04-12
target_confidence: 0.75
current_confidence: 0.75
rounds: 2
craft_protocol_version: 1
decision_class: exploration
---

# Subagent Orchestration Protocol — Design Craft (Wave 53)

## §0 Problem Statement

Complex metabolic operations (e.g., "compress all 20 raw notes tagged
'forage-digest' into 5 extracted notes") involve multiple steps that could
benefit from parallel execution. Currently, a single agent session executes
them sequentially. Subagent delegation (inspired by hermes-agent's
`delegate_tool.py`) could parallelize this.

Myco cannot control the host agent's subagent mechanism — it can only
recommend task decomposition. This craft establishes the protocol.

## §1 Round 1 — Decomposition Protocol

### D1: When to recommend decomposition

Myco recommends task decomposition when:
- Hunger actions contain > 3 items of the same verb
- A compression cohort has > 10 notes (significant synthesis effort)
- Multiple independent cohorts are ripe simultaneously

The recommendation appears in `HungerReport.actions` as a meta-action:
```json
{
  "verb": "orchestrate",
  "args": {"subtasks": [...]},
  "reason": "3+ independent compress cohorts ripe — parallel execution recommended"
}
```

### D2: Subtask shape

Each subtask is a self-contained Myco verb invocation:
```json
{
  "verb": "compress",
  "args": {"tag": "forage-digest", "rationale": "auto-generated"},
  "isolation": "none",
  "depends_on": []
}
```

Fields:
- `verb` + `args`: the MCP tool call to execute
- `isolation`: "none" (shared workspace) or "worktree" (isolated copy)
- `depends_on`: list of subtask indices that must complete first

### D3: Result collection

After all subtasks complete:
1. Each subtask reports success/failure + output summary
2. The orchestrator runs `myco lint` to verify substrate integrity
3. If any subtask failed, the orchestrator reports the failure chain

### D4: Host agent integration

The orchestration protocol produces a task list that maps to the host
agent's subagent mechanism:
- Claude Code: `Agent` tool with `subagent_type="general-purpose"`
- Each subagent gets a self-contained prompt with one `myco_*` MCP call
- Worktree isolation for write operations (prevents file conflicts)

## §2 Round 2 — Attack Surface

### A1: Parallel write conflicts

**Attack**: Two subagents try to modify the same note simultaneously.
**Defense**: `isolation: "worktree"` for any verb that writes to notes/.
The orchestrator merges results back to main workspace.

### A2: Cascade failure

**Attack**: Subtask 2 depends on subtask 1's output, but subtask 1 fails.
**Defense**: `depends_on` field enforces ordering. Failed dependencies
cascade failure to dependents. Independent subtasks continue.

### A3: Over-orchestration

**Attack**: Decomposing trivially small tasks wastes context on subagent overhead.
**Defense**: Minimum threshold (>3 actions or >10 notes) before recommending
decomposition. Below threshold, sequential execution is fine.

## §3 Conclusion

**Protocol shape**: Hunger actions → decomposition check → subtask list →
host agent's subagent mechanism → result collection → lint verification.

**Implementation status**: Design only (this craft). No code changes.
The protocol produces a task decomposition that ANY host agent with subagent
capabilities can execute. Myco provides the structure; the host provides
the parallelism.

**Open question**: Should the `orchestrate` meta-action be a first-class
hunger action, or should the host agent's boot ritual decide independently
whether to parallelize? Current recommendation: first-class action, because
the decomposition logic requires Myco's knowledge of cohort sizes and
dependencies that the host agent doesn't have.
