---
captured_at: '2026-04-27T17:03:33Z'
source: agent
stage: integrated
tags:
- v0.6.0
- owner-approved
- plan
- refactor
- ChatGPT-Gemini-review
- decision
integrated_at: '2026-04-27T17:07:50Z'
---
v0.6.0 unified-evolution plan APPROVED by owner (2026-04-28).

Plan file location: C:\Users\10350\.claude\plans\myco-chatgpt-gemini-velvet-ullman.md (~12k 字)

# Owner-binding decisions (D1-D10)

D1 — Version pacing: SINGLE v0.6.0 release封口, no v0.5.25/.26/.27 progressive cuts. 0.x SemVer permits MINOR-internal breaks (precedent: v0.5.24 MCP-alias purge). One-shot cut keeps full ChatGPT/Gemini review surface visible.
D2 — Refactor depth: THOROUGH REWRITE permitted on L4 implementation. L0/L1/L2/L3 doctrine UNCHANGED (sacred). Targets: surface unification, dimensions reorg, alias purge, providers/symbionts cleanup.
D3 — Sampling: default opt-in via canon.system.llm_policy enum (forbidden | opt-in | providers-declared). Replaces v0.5.6 no_llm_in_substrate: bool. CL1 dim guards.
D4 — DC1/DC4 fixable: stub with `_AGENT_TODO_DOCSTRING_` marker (RL3-recoverable signal). Tradeoff: 121 LOW noise worse than templated stub.
D5 — DRAFT craft dogfood_v0_5_3_smoke: EXCRETE (9 days stalled, topic superseded by v0_5_3_fungal_vocabulary_craft). MB6 dim auto-handles future stale DRAFTs at 30+ days.
D6 — Distilled d_legacy_alias_test + d_v0_5_3_dogfood_notes: EXCRETE (no doctrine payload, event-records only).
D7 — CHANGELOG.md: AUTO-DERIVE from contract_changelog.md via hooks/derive_changelog.py at hatch build time. No backfill, no termination — derivation respects audience split.
D8 — Public window: 7 days (matches weekly cadence + Glama promotion cycle). Owner-veto via canon.governance.last_winnowed_proposals[].vetoed_at always-on.
D9 — Alias removal: v0.5.2 names (genesis/reflect/distill/perfuse/session-end/craft/bump/evolve/scaffold) FULLY DELETED at v0.6.0. v0.5.24 deprecated MCP aliases also gone. New tool myco-migrate <user-script> assists.
D10 — Canon schema v2: LANDS at v0.6.0 (not v0.7.0). Refactor window co-locates dimensions sub-file extraction + llm_policy enum + identity.federation_peers field.

# Architectural pivots (R1-R9 refactors)

R1 — surface/ unified Capability abstraction (build_server ≤50 LOC).
R2 — homeostasis/dimensions/ split into mechanical/shipped/metabolic/semantic/ subdirs.
R3 — cycle/ promoted to subsystem `governance`; surface/install/symbionts/mcp grouped into `boundary` subsystem. canon.subsystems 5 → 7. New L2 doctrine: governance.md + boundary.md.
R4 — install/ + symbionts/ merged into boundary/host_integration/<host>.py with discover/install_basic/install_deep/uninstall four-fn protocol.
R5 — Canon schema v2 (dimensions sub-file + llm_policy enum + federation_peers).
R6 — Alias全删, myco-migrate tool delivered.
R7 — tests/unit reorganized into verbs/ + internals/.
R8 — providers/ stays empty (P1 escape hatch); mp1 cross-check guards.
R9 — v0.5.x transitional code purged (~500-1000 LOC).

# Scope summary
- 42 lint dimensions (was 25, +17 new)
- 13 fixable (was 4, +9)
- 20 verbs (was 19, +intake; deprecate forage --digest-on-read)
- 7 MCP capabilities (tools + resources + prompts + sampling + progress + elicitation + Server Card)
- 2 transports (stdio + Streamable HTTP/OAuth 2.1)
- 11 host symbiont deep adapters
- 8 framework demos (LangChain/LangGraph/CrewAI/DSPy/Smolagents/Agno/PraisonAI/MS-Agent-Framework/Claude-SDK)
- 7 subsystems (5 biological + governance + boundary)
- ~120 files modified (60 new + 50 rewritten + 15 deleted)

# Implementation roadmap (post-approval)
1. Fruit主 craft `v0_6_0_unified_evolution_craft_<date>.md` (high-risk owner approval).
2. Three-round dialectic with parallel ChatGPT-as-critic + Gemini-as-critic injections.
3. Winnow → owner approval.
4. 22 sub-PR sequence (13 work-streams + 9 refactors); each PR independently passes verify_mcp_boot + verify_mcp_capabilities + verify_install_examples + immune-zero + coverage gate.
5. 1-week integration period dogfooding myco-self.
6. bump_version.py 0.6.0 + myco molt --contract v0.6.0.
7. v0.6.0 tag push triggers 4-channel fan-out (PyPI / MCP Registry / GitHub Release / .plugin bundle).
8. Glama Phase 4a/4b/4c execution within 24h.
9. 1-week observation period for v0.6.1 candidate items.

# ChatGPT/Gemini adversarial review prep
11 anticipated objections + reasoned reb rebuttals documented in plan §7. Honest non-zero-compromise points flagged in §9.

Tags: v0.6.0, owner-approved, plan, refactor, ChatGPT-Gemini-review
