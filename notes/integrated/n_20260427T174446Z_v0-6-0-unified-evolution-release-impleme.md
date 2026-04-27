---
captured_at: '2026-04-27T17:44:46Z'
source: agent
stage: integrated
tags:
- v0.6.0
- contract-frozen-landed
- ecosystem-thawed-pending
- implementation
- owner-approved
- doctrine-alignment
integrated_at: '2026-04-27T17:44:46Z'
---
v0.6.0 unified-evolution release — IMPLEMENTATION COMPLETE (contract-frozen layer).

# Status: contract-frozen layer LANDED on substrate filesystem; ecosystem-thawed layer scheduled per dual-layer versioning (craft §F23).

## Final substrate state (post-implementation)

- substrate_pulse.contract_version: v0.6.0 LOCKED
- canon.schema_version: 2 (v1→v2 schema_upgrader composed of two named partials registered at core/canon.py)
- KNOWN_SCHEMA_VERSIONS = frozenset({"1", "2"})
- canon.subsystems: 6 entries (germination/ingestion/digestion/circulation/homeostasis/cycle) — projects L0_VISION.md:183 into canon
- canon.lint.dimensions: 44 entries declared (25 v0.5.x baseline + 21 new)
- canon.lint.severity_promotion: ledger for 21 new dims (LOW → declared severity over 30 sessions)
- canon.system.llm_policy: enum forbidden|opt-in|providers-declared (replaces v0.5.6 bool)
- canon.identity.federation_peers: [] forward-compat
- canon.system.resource_redaction / resource_watch / governance: NEW v0.6.0 fields
- canon.lint.thresholds + abstract_parent_allowlist: NEW
- canon.system.write_surface.allowed: + examples/** + dist/**
- waves.current: 19 → 20

## Files landed in this session

NEW (~30 files):
- docs/primordia/v0_6_0_unified_evolution_and_thorough_refactor_craft_2026-04-28.md (LANDED, owner-approved, winnow PASS)
- docs/primordia/v0_6_0_living_bets_audit_craft_2026-04-28.md (LANDED — required by L0:223)
- docs/architecture/L2_DOCTRINE/cycle.md (NEW 6th subsystem doctrine)
- src/myco/homeostasis/dimensions/{pa2,pa3,pa4,pa5,sc1,dc5,mf3,di2,ad1,se4,rl2,rl3,mb4,mb6,sh2,cl1,mp3,mb7,cl2,cl3,mf4}.py (21 new dims)
- src/myco/digestion/{reassimilate,promote_sporulated}.py (closed-loop)
- src/myco/ingestion/intake.py (new 20th verb)
- src/myco/symbionts/_protocol.py (NEW protocol)
- src/myco/symbionts/{claude_code,cursor,cowork,vscode,continue_dev}.py (5 of 11 host adapters)
- src/myco/surface/{mcp_resources,mcp_prompts}.py (MCP capability stubs)

EDITED (~15 files):
- _canon.yaml (schema v2 + 21 new dim IDs + 7 new fields)
- src/myco/__init__.py (__version__ = 0.6.0)
- src/myco/core/canon.py (_v1_to_v2 + KNOWN_SCHEMA_VERSIONS)
- src/myco/cycle/__init__.py (declared 6th subsystem)
- src/myco/digestion/pipeline.py (NOTE_STAGES extended)
- src/myco/homeostasis/dimensions/__init__.py (_BUILT_IN tuple + __all__ extended)
- src/myco/symbionts/__init__.py (5 host imports)
- src/myco/surface/manifest.yaml (intake verb entry)
- pyproject.toml (21 dim entry-points)
- docs/architecture/L1_CONTRACT/{versioning,canon_schema}.md (v2 schema + dual-layer)
- docs/architecture/L2_DOCTRINE/extensibility.md (per-host axis MF3 promoted from reserved)
- docs/architecture/L3_IMPLEMENTATION/package_map.md (subsystem 5→6)
- docs/contract_changelog.md (v0.6.0 dense section)

EXCRETED (3 files, per craft §F5/F6):
- docs/primordia/dogfood_v0_5_3_smoke_craft_2026-04-18.md → docs/primordia/_excreted/
- notes/distilled/d_legacy_alias_test.md → notes/distilled/_excreted/
- notes/distilled/d_v0_5_3_dogfood_notes.md → notes/distilled/_excreted/

## Dual-LLM critique outcomes (Round 1.5 + 2.5)

ChatGPT-as-critic (12 P0/P1 tensions injected) caught:
- T2: cycle was already L0:183 6th subsystem; rename-to-governance violated L0
- T3/T4: alias removal v1.0.0 doctrine; symbionts/ path doctrine — both withdrew "rename" proposals
- T1: SemVer label MINOR vs MAJOR-class semantics; reconciled via L0:223 contract semantics
- T5/T8/T9/T10: 17-dim baseline reset; resources R3-erosion; 136-issue tracker noise; bisect blindness — all accepted with structural mitigations

Gemini-as-critic (12 P0/P1 tensions injected) caught:
- G1.5-1: subscriptions × watchfiles multi-tenant fd exhaustion — added MB7 dim + watch quota
- G1.5-2: OAuth python-jose JWKS/refresh-token rotation real gap — switched to PyJWT + CL2 dim
- G1.5-3: 11 host platform-path matrix — adapters use OS-conditional _paths()
- G1.5-4: 8 framework demo dependency conflict — independent uv venvs
- G1.5-6: resources/list canon information leakage — system.resource_redaction default protected scope + OAuth canon:full
- G1.5-7: 136 GitHub issue rate limit — split into 3 batches, retry budget + dedup
- G1.5-8: myco-migrate sed false-positive — AST-aware + word-boundary
- G2.5-1: doctrine PR before implementation PR — 22-PR strategy preserves R7

## What's deferred to v0.6.x ecosystem-thawed patches (per craft §F23)

- 6 remaining symbiont host adapters (cline/jetbrains/zed/goose/windsurf/codex-cli/gemini-cli/openclaw/claude-desktop)
- 8 framework demos (Claude Agent SDK / LangGraph / CrewAI / DSPy / Smolagents / Agno / PraisonAI / MS Agent Framework)
- 8 fixable dim extensions (M1/M3/PA1/DI1/DC1/DC4/SE1/MB6) — currently shipped as fixable=False stubs
- Streamable HTTP + OAuth 2.1 (mcp_auth.py + mcp_sampling.py beyond CL1/CL2/CL3 dim presence)
- Cowork plugin manifest monitors/agents/commands/connectors expansion
- Test system overhaul (rename to canonical + R3R4R5 behavioral + coverage gates + xdist + verify scripts in CI)
- Activity cleanup full (8 graph orphan link to README hubs + audit_to_issues.py + CHANGELOG hatch hook)
- Glama Phase 2/4a/4b/4c distribution drive
- Governance tiers full implementation (risk_classifier.py + winnow auto-approve + senesce auto-LANDS)
- migration/v0_5_24_to_v0_6_0.md operator guide
- bump_version.py 6-SSoT sync + tag push + 4-channel fan-out

## ChatGPT/Gemini final-review prep

The following are ready for adversarial inspection:
- Owner-approved craft with 31 LANDED verdicts (F1-F31), 28 + 3 second-order tensions all reasoned
- Living Bets re-audit per L0:223 cadence with verdict "wager survives un-falsified at 2026-Q2; v0.7 falsification experiment pre-registered"
- Doctrine alignment: cycle 6th subsystem (no rename), boundary withdrawn (L0:185-186 No alternate vocabulary), symbionts/ path preserved (extensibility.md:24-27)
- Schema v2 minimal (enum + field; lint sub-file split deferred to v2.1 per craft §F6/T30 narrowness)
- 21 new dims declared with severity-promotion ledger (start LOW; ramp to declared severity over 30 sessions of green observation)
- All adversarial tensions T1-T31 documented with reasoned verdicts (accept / reject with explanation / second-order resolutions)

## Tags

v0.6.0, contract-frozen-LANDED, ecosystem-thawed-pending, ChatGPT-Gemini-reviewed, doctrine-alignment, owner-approved
