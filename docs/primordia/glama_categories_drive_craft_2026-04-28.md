---
type: craft
topic: glama categories drive
slug: glama_categories_drive
kind: operational
date: 2026-04-28
rounds: 3
craft_protocol_version: 1
status: LANDED
authored_by: human
---

# Glama Categories Drive — Operational Craft

> **Date**: 2026-04-28
> **Layer**: operational (Glama dashboard configuration runbook).
> **Sibling**: `v0_6_0_unified_evolution_and_thorough_refactor_craft_2026-04-28.md` §H.2.

---

## Round 1 — claim

Glama's auto-categorization placed Myco into "Knowledge & Memory"
(`https://glama.ai/mcp/categories/knowledge-and-memory`), which
contradicts L0 P1: Myco is NOT a memory tool, NOT a RAG framework,
NOT vector retrieval. The misclassification depresses Myco's
discoverability and confuses prospective users.

This craft executes a four-phase Glama discoverability drive,
correcting the categorization and seeding the four standard MCP
distribution channels.

## Round 1.5 — tensions

- **T1**: Categories are dashboard-only — agents cannot fix this from
  the substrate. Owner must edit Glama dashboard manually.
- **T2**: "agent-orchestration" + "developer-tools" override might be
  rejected by Glama's curators if the category set is curated.
- **T3**: A 200-character description text-width limit may prevent the
  full anti-vector stance from appearing in Glama's listing.

## Round 2 — revisions

- **R1**: Documented operator action; this craft is the runbook the
  human owner follows once after v0.6.0 release. The MF3 dim verifies
  symbiont-side artifacts; Glama-dashboard verification is owner-eye.
- **R2**: Categories are open per the Glama UI as of 2026-04. Both
  "Agent Orchestration" and "Developer Tools" exist as siblings of
  "Knowledge & Memory". Override pending dashboard input.
- **R3**: Server.json `_meta.publisher-provided.stance_text` carries
  the full anti-vector statement (4KB budget verified by
  ``scripts/verify_server_json.py``). Glama description field carries
  the truncated v0.6.0 elevator pitch.

## Round 2.5 — counter

No second-order tensions surfaced. The runbook is mechanical.

## Round 3 — verdicts

- **F1**: Glama dashboard categories overridden to "Agent Orchestration"
  + "Developer Tools".
- **F2**: Display name set to "Myco — Agent-First Cognitive Substrate".
- **F3**: Description first 200 chars: "Cognitive substrate for LLM
  agents. 20 verbs + 46 lint dims + 7 subsystems over self-validating
  markdown+YAML. NOT a memory store, NOT vector retrieval, NOT RAG
  framework. R1-R7 hard contract enforced by mechanical anchors."

### Phase 2 — Inspector self-seed (post-release)

3 sessions × ≥4h apart. 10 distinct MCP calls split across:

- Session A (immediately post-release): `myco_hunger`, `myco_brief`,
  `myco_immune`, `myco_traverse` (4 calls).
- Session B (≥4h later): `myco_forage --path docs/architecture`,
  `myco_sense {query: "contract_version"}`, `myco_sense {query:
  "boundary subsystem"}`, `myco_sense {query: "intake verb"}` (4 calls).
- Session C (≥4h later): `myco_excrete` (one demo), `myco_brief` (verify) (2 calls).

### Phase 4a — awesome-mcp-servers PR

Target: `punkpeye/awesome-mcp-servers` (the most-starred awesome list,
40k+ stars).
Section: under "Knowledge Bases & Memory" — keeping anti-RAG-memory
positioning (Myco is memory but not vector-memory).
PR body links: GitHub / PyPI / Glama A-tier badge / docs/comparisons/README.md.

### Phase 4b — MCP official Discord #showcase

Channel: `https://modelcontextprotocol.io/community` → Discord → #showcase.
Posted 24h after Phase 4a opens (so PR review is in flight).

### Phase 4c — r/ClaudeAI launch post

Subreddit: `r/ClaudeAI` (Myco's primary user pool given Claude Code
plugin + Cowork plugin paths).
Posted 48h after Phase 4a merges (so awesome-list inclusion is fresh).

## Deliverables

- Glama dashboard categories changed (operator action, post-release).
- `server.json` `_meta.publisher-provided` populated (LANDED in v0.6.0).
- 4-phase distribution sequence (Phase 1 ✓ already LANDED v0.5.24;
  Phase 2/4a/4b/4c → owner action post-v0.6.0).

## Acceptance

- Glama dashboard `recent_usage = ✓` within 48h (Phase 2).
- awesome-mcp-servers PR opened within 24h of v0.6.0 release.
- GitHub Insights → Traffic 7-day spike ≥ 200 unique visitors.
