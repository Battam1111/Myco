---
type: craft
status: ARCHIVED
created: 2026-04-12
target_confidence: 0.90
current_confidence: 0.90
rounds: 2
craft_protocol_version: 1
decision_class: kernel_contract
---

# Tool Trigger Contract — 18/18 MCP Tool Documentation (Wave 57)

## §0 Problem Statement

agent_protocol.md §2 claimed "18 个 MCP 工具的触发条件" but only documented
triggers for 9 tools (§2.1: status/log/reflect/retrospect/lint; §2.2:
eat/digest/view/hunger). The remaining 9 tools (compress, uncompress, prune,
inlet, forage, upstream, search, graph, cohort, session) had trigger
conditions ONLY in their MCP docstrings, not in the normative contract.

This meant any Agent reading agent_protocol.md would not know WHEN to call
50% of the available tools — violating the Agent-First principle.

## §1 Round 1 — Design

### D1: Add §2.3 Compression Pipeline (compress, uncompress, prune)
Triggers derived from hunger signals: compression_ripe, compression_pressure,
dead_knowledge. All three tools already have MCP docstrings with WHEN TO CALL;
the contract mirrors this information in the table format of §2.1-§2.2.

### D2: Add §2.4 External Metabolism (inlet, forage, upstream, search)
Triggers: inlet_ripe, forage_backlog, upstream_scan_stale, plus the universal
"search before answering" rule. search is the most important: it must be
called BEFORE answering any factual question about the project.

### D3: Add §2.5 Structural Intelligence (graph, cohort, session)
Triggers: graph_orphans hunger signal, compression preparation (cohort
suggest), cross-session context recovery (session search). These are
Wave 47-52 tools that had zero contract documentation.

### D4: Add §2.6 Traceability Navigation (Wave 56)
Already landed in Wave 56. References _canon.yaml::system.traceability.

## §2 Round 2 — Attack Surface

### A1: "Too many tools overwhelm the Agent"
Defense: The 18 tools are organized into 5 functional groups (Reflexes,
Digestive, Compression, External, Intelligence). Each group has clear
trigger conditions. The Agent doesn't need to memorize all 18 — it reads
hunger signals and the contract tells it which tool to call.

### A2: "Trigger conditions may become stale"
Defense: The traceability index (Wave 56) maps each anchor to its tools.
When anchors change, the Agent follows the traceability path to update
trigger conditions. This is better than the previous state where triggers
existed only in MCP docstrings (completely invisible to contract review).

## §3 Conclusion

All 18 MCP tools now have documented trigger conditions in the normative
contract (agent_protocol.md §2.1-§2.5). Contract bump v0.42.0 → v0.43.0.
