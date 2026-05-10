---
proposed_doctrine: v0-6-x-unified-evolution-and-cycle-autostart-retrospective
sources:
- notes/integrated/n_20260510T145228Z.md
- notes/integrated/n_20260510T145229Z.md
- notes/integrated/n_20260510T145231Z.md
- notes/integrated/n_20260510T145233Z.md
- notes/integrated/n_20260510T145234Z.md
- notes/integrated/n_20260510T145235Z.md
distilled_at: '2026-05-10T14:52:50Z'
stage: distilled
ingest_state: distilled
synthesis_authored_at: '2026-05-10T14:55:00Z'
---

# Distillation: v0.6.x Unified Evolution + Cycle Autostart Retrospective

> 6 v0.6.x crafts (mid-to-late April 2026) — the architectural inflection of mature Myco. Where v0.5.x layered discipline atop the v0.4.x scaffold, v0.6.x reorganized the scaffold itself.

## The 6 v0.6.x doctrinal landings

1. **v0.6.0 — Unified evolution + thorough refactor**: the largest single craft of the project's history. Schema v1 → v2 (bool→enum llm_policy + federation_peers field + lint.dimensions sub-file extraction). Boundary subsystem promoted from "cross-cutting adapter package" to a 7th canonical subsystem alongside the 6 fungal-bionic ones (germination/ingestion/digestion/circulation/homeostasis/cycle). 80+ project-internal imports rewritten via `scripts/myco_migrate.py`. The first L0-mandated *structural unification*, removing v0.5.x's surface/install/mcp/symbionts ad-hoc layering.

2. **v0.6.0 — Living Bets audit (initial)**: bundled inside the unified evolution craft rather than standalone. The bet stood; the appendix was reaffirmed. v0.7.5 backfilled this as a standalone craft retroactively.

3. **v0.6.11 — Subagents + slash commands**: 5 fungal-named specialist subagents (primordium / hypha / autolysis / stipe / anamorph) under `.claude/agents/` with byte-identical mirrors at `<repo>/agents/`. 5 `/myco-*` slash commands as thin orchestrators. v0.6.11 §A1 amendment carved an exception to L0:185-186 strict-fungal-naming for Boundary subsystem English names; subagent names stay strictly fungal.

4. **v0.6.14 — Cycle 自起 (autostart) fruit-winnow-molt loop**: governance fields under `_canon.yaml::governance` for auto-craft generation triggered by distilled→sporulated→fruit→winnow→molt closed-loop. PR-merge as the sole gate for medium-risk auto-crafts; owner-veto via `vetoed_at` on any pending entry is always-on.

5. **v0.6.15 — Agent-first default for cycle autostart**: flipped v0.6.14's `auto_evolve_force_high_risk: true` (which had Owner-First-inverted L0 P1) to `false`. Risk class derived from craft CONTENT via `core.risk_classifier` (path_allowlist superset + recursion-cutter for crafts modifying classifier itself). The 5-critic L0 P1-P5 fanout protocol (chytrid / rhizomorph / mycoparasite / saprotroph / mycorrhiza, one per principle) introduced for autonomous-mode crafts.

6. **v0.6.16 — Neat freak sweep**: the largest single round of inherited-cruft removal pre-v0.7.x. Deleted ~5 KLOC of unused modules, consolidated lint dim registration, removed dead test fixtures. The first taste of "structural compaction as a release type" that v0.7.0 would weaponize at scale.

## Five themes v0.6.x cemented

1. **Schema migration as a normal operation, not a crisis** (v0.6.0 introduces v1→v2; v0.7.5 introduces v2→v3 routinely).
2. **Boundary as a subsystem** (v0.6.0; the only English-named subsystem; v0.6.11 §A1's carve-out justified by the *outward-facing* semantics).
3. **Substrate as governance system** (v0.6.14/.15; the cycle autostart loop makes the substrate's own evolution executable, not just doctrinal).
4. **Path-allowlist risk classification** (v0.6.15; auto-classification + recursion-cutter prevent the substrate from auto-crafting changes to its own auto-craft machinery without owner gate).
5. **Structural compaction as release class** (v0.6.16 prototype; v0.7.0 production).

## What v0.6.x cemented for v0.7.10

The 7-subsystem shape (6 fungal + boundary) is stable through v0.7.x and into v0.7.10. The schema_upgrader chain established at v0.6.0 carried forward: v2 → v3 at v0.7.5 used the same partial-+-composer pattern. The 5-critic L0 P1-P5 fanout from v0.6.15 was used at v0.7.5 (P1 craft) and v0.7.10 (omnibus craft) for self-rebuttal structure. The auto-craft loop from v0.6.14/.15 was *available* through v0.7.x but wasn't triggered (every v0.7.x craft was owner-initiated; auto-mode is dormant infrastructure waiting for a real trigger event).

## Source notes (graph back-references)

- [v0_6_0_living_bets_audit_craft](../integrated/n_20260510T145228Z.md)
- [v0_6_0_unified_evolution_craft](../integrated/n_20260510T145229Z.md)
- [v0_6_11_subagents_and_commands_craft](../integrated/n_20260510T145231Z.md)
- [v0_6_14_cycle_autostart_loop_craft](../integrated/n_20260510T145233Z.md)
- [v0_6_15_agent_first_default_craft](../integrated/n_20260510T145234Z.md)
- [v0_6_16_neat_freak_sweep_craft](../integrated/n_20260510T145235Z.md)
