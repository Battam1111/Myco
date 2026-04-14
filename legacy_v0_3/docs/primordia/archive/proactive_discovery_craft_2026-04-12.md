---
type: craft
status: ARCHIVED
created: 2026-04-12
target_confidence: 0.75
current_confidence: 0.75
rounds: 2
craft_protocol_version: 1
decision_class: exploration
---

# Proactive Knowledge Discovery — Design Craft (Wave 51)

## §0 Problem Statement

Myco's metabolism is reactive: knowledge enters only when a human or agent
explicitly calls `myco eat`, `myco inlet`, or `myco forage add`. The ideal
vision (6-point directive #6) requires **proactive acquisition**: Myco+Agent
silently discovers, evaluates, and absorbs relevant external knowledge without
human prompting.

### Dependencies (all landed)
- Wave 47: Link graph provides structural connectivity map
- Wave 48: Cohort intelligence detects knowledge gaps
- Wave 49: Inlet triggers fire `inlet_ripe` when gaps accumulate
- Wave 50: Metabolic-cycle skill executes hunger actions at boot

### Missing capability
The agent must autonomously:
1. Read the knowledge graph + cohort gaps
2. Search the internet for relevant sources
3. Evaluate relevance, quality, and alignment
4. Pipe results through `myco inlet` with provenance
5. Let the metabolic pipeline digest/compress/integrate

This depends on **host agent capabilities** (Claude Code web search, session
scheduling) that Myco cannot force — it can only recommend.

## §1 Round 1 — Protocol Design

### D1: Discovery trigger

The `inlet_ripe` signal (Wave 49) provides the trigger. When hunger reports
`inlet_ripe` with a reason (search misses or cohort gaps), the discovery
protocol activates. The agent reads the reason string to understand WHAT
knowledge is missing.

### D2: Source selection

The agent uses its web search capability to find candidates. Search queries
are derived from:
- Cohort gap tags (e.g., gap in "compression" → search "knowledge compression techniques")
- Recent search misses (queries that returned zero results)
- Craft reference misses (external sources cited but not in forage)

### D3: Evaluation criteria

Before `myco inlet`, the agent evaluates:
- **Relevance**: Does this address the identified gap?
- **Quality**: Is the source authoritative? (papers > blog posts > forum threads)
- **Novelty**: Is this already in the substrate? (search existing notes first)
- **Alignment**: Does this contradict existing doctrine? (if so, flag for human review)

### D4: Ingestion protocol

For each approved source:
1. `myco inlet <local_file> --tags <gap_tag>` with provenance metadata
2. Log the decision in `log.md`: `decision | proactive-discovery: ingested <source> for <gap>`
3. The existing metabolic pipeline handles the rest (digest → compress → integrate)

### D5: Audit trail

All proactive acquisitions are auditable:
- Notes carry `source: inlet` + `inlet_origin` + `inlet_method: url-fetched-by-agent`
- Log entries record the decision chain
- Human can review via `myco view --tag inlet` or `myco cohort gaps`

## §2 Round 2 — Attack Surface Analysis

### A1: Quality noise

**Attack**: Agent ingests low-quality sources that pollute the substrate.
**Defense**: Quality gate before inlet. If uncertainty > threshold, skip
and log the skip reason. Compression doctrine eventually excretes low-value
notes via dead_knowledge detection.

### A2: Deduplication

**Attack**: Agent ingests the same source multiple times.
**Defense**: `inlet_content_hash` field detects duplicate content. Before
inlet, agent checks existing notes for matching `inlet_origin` or hash.

### A3: Rate limiting

**Attack**: Agent ingests 50 sources in one session, overwhelming compression.
**Defense**: Session-level cap (e.g., max 5 inlets per session). The
`compression_pressure` metric (Wave 50) will fire if intake >> compression.

### A4: Alignment drift

**Attack**: Ingested knowledge carries assumptions that conflict with
doctrine (e.g., a paper claiming "memory layers are sufficient" when Myco
doctrine says "verification layer is needed").
**Defense**: This is **open_problems §3** — no automated detector exists.
Mitigation: all inlet notes start as `raw` and must pass through human/agent
digest before integration. The selection layer (mutation-selection model)
is preserved.

### A5: Platform dependency

**Attack**: Design assumes Claude Code web search exists and is reliable.
**Defense**: The protocol is a recommendation, not a hard dependency. If
web search is unavailable, the agent skips discovery gracefully. All other
metabolic functions continue working.

## §3 Conclusion

**Protocol shape**: `inlet_ripe` → agent reads gap description → web search
→ evaluate (relevance, quality, novelty, alignment) → `myco inlet` with
provenance → metabolic pipeline → audit trail.

**Implementation status**: Design only (this craft). No code changes.
Implementation depends on host agent capabilities:
- Claude Code `WebSearch` tool for source discovery
- Session scheduling for periodic discovery runs (currently: session-boot only)
- `.claude/scheduled_tasks.json` or similar for recurring execution

**Honest limitation**: Proactive discovery is the highest-dependency feature
in Myco's roadmap. It requires the host agent to have web access, autonomous
session creation, and quality judgment. Myco provides the scaffolding (signals,
intake pipeline, audit trail); the agent provides the intelligence. This is
the ultimate Bitter Lesson application.
