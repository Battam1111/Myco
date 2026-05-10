---
proposed_doctrine: v0-4-x-greenfield-rewrite-retrospective
sources:
- notes/integrated/n_20260510T145212Z_agent-handoff-myco-v0-4-0-v0-4-1.md
- notes/integrated/n_20260510T145212Z.md
- notes/integrated/n_20260510T145212Z_2.md
- notes/integrated/n_20260510T145212Z_l0-identity-revision-2026-04-15.md
- notes/integrated/n_20260510T145212Z_stage-a-scaffold-implementation-craft.md
- notes/integrated/n_20260510T145212Z_stage-b-1-core-implementation-craft.md
- notes/integrated/n_20260510T145212Z_stage-b-2-homeostasis-kernel-implementat.md
- notes/integrated/n_20260510T145212Z_stage-b-3-genesis-bootstrap-craft.md
- notes/integrated/n_20260510T145212Z_stage-b-4-ingestion-craft.md
- notes/integrated/n_20260510T145212Z_stage-b-5-digestion-craft.md
- notes/integrated/n_20260510T145212Z_stage-b-6-circulation-craft.md
- notes/integrated/n_20260510T145212Z_stage-b-7-surface-craft.md
- notes/integrated/n_20260510T145212Z_stage-b-8-craft-fresh-dimensions.md
- notes/integrated/n_20260510T145212Z_stage-c-craft-materialization.md
- notes/integrated/n_20260510T145212Z_v0-4-1-post-release-audit-craft.md
distilled_at: '2026-05-10T14:52:50Z'
stage: distilled
ingest_state: distilled
synthesis_authored_at: '2026-05-10T14:55:00Z'
---

# Distillation: v0.4.x Greenfield Rewrite Retrospective

> Synthesizes 15 crafts from the v0.4.0 → v0.4.1 stretch (mid-April 2026). The decisions captured here are the *load-bearing constitutional moments* of post-rewrite Myco.

## The 4-stage shape of the v0.4.x greenfield

The v0.4.x cycle rewrote Myco from scratch on top of an audit of the pre-v0.4 (legacy) shape. Four named stages structured the work:

- **Stage A — Scaffold**: minimal package skeleton, `_canon.yaml` schema v1, `MYCO.md` entry-point doctrine, single passing test. The substrate became *self-validating* on day one.
- **Stage B — Core subsystems** (8 sub-crafts, B.1–B.8): germination, ingestion, digestion, circulation, homeostasis, surface, dimensions, kernel. Each subsystem authored as a craft before any code lands; each ends with a passing test against its contract.
- **Stage C — Materialization**: stitches the subsystems into the verb manifest + MCP server + CLI; first end-to-end `myco hunger` → `myco eat` → `myco assimilate` chain runs.
- **Audit** (post-Stage C): the v0.4.1 audit re-scrutinizes every shipped surface and surfaces the loose threads that v0.5.x will close.

## Five doctrinal anchors v0.4.x cemented

1. **Doctrine layered before code** (R7 top-down). Each subsystem craft is written, winnowed, and approved BEFORE its source code is authored. The `craft → code` order makes contract-violating implementations literally unwriteable: the contract fails review before the code exists.

2. **Biological metaphor as authoritative vocabulary** (per the L0 amendment). Subsystem names are mycological/biological terms whose meaning tracks the operation: germination, ingestion, digestion, circulation, homeostasis. *Alternate names are forbidden*. This is not aesthetics — it's a Schelling point for cross-session vocabulary stability.

3. **Self-validating substrate** (the three invariants). The substrate validates itself at every lint pass. Agent-only consumption + self-validation under change + strict top-down + graph density. v0.4.x's homeostasis kernel is the immune system that makes drift mechanical-not-aspirational.

4. **L0 identity revision** (mid-stretch, 2026-04-15). The five root principles condensed into their canonical form: Only For Agent / Eternal Devour / Eternal Evolution / Eternal Iteration / Universal Interconnection. The Living Bets appendix was added as a *self-acknowledged non-eternal commitment*.

5. **Greenfield over migration** (the audit's big call). The pre-v0.4 substrate was deemed un-rescuable; v0.4.0 starts a fresh tag sequence (`v0.4.0-final` is the legacy preserved tag). The cost was permanent: no migration path from v0.3.x. The benefit was 7-month-of-substrate-evolution headroom that retrofit could not have produced.

## What the retrospective sees from v0.7.10

The v0.4.x scaffold's bet on *layered doctrine* has held: every cycle since (v0.5.x discipline, v0.6.x unified evolution, v0.7.x ratchet maturation) extended the layers without touching the L0 invariants. The greenfield call paid off — the substrate is more legible, more lint-able, and more agent-readable at v0.7.10 than any retrofit could have made it.

## Source notes (graph back-references)

- [agent-handoff-v0_4_1](../integrated/n_20260510T145212Z_agent-handoff-myco-v0-4-0-v0-4-1.md)
- [contract_audit_craft](../integrated/n_20260510T145212Z.md)
- [greenfield_rewrite_craft](../integrated/n_20260510T145212Z_2.md)
- [l0_identity_revision_craft](../integrated/n_20260510T145212Z_l0-identity-revision-2026-04-15.md)
- [stage_a_scaffold](../integrated/n_20260510T145212Z_stage-a-scaffold-implementation-craft.md)
- [stage_b1_core](../integrated/n_20260510T145212Z_stage-b-1-core-implementation-craft.md)
- [stage_b2_homeostasis](../integrated/n_20260510T145212Z_stage-b-2-homeostasis-kernel-implementat.md)
- [stage_b3_genesis](../integrated/n_20260510T145212Z_stage-b-3-genesis-bootstrap-craft.md)
- [stage_b4_ingestion](../integrated/n_20260510T145212Z_stage-b-4-ingestion-craft.md)
- [stage_b5_digestion](../integrated/n_20260510T145212Z_stage-b-5-digestion-craft.md)
- [stage_b6_circulation](../integrated/n_20260510T145212Z_stage-b-6-circulation-craft.md)
- [stage_b7_surface](../integrated/n_20260510T145212Z_stage-b-7-surface-craft.md)
- [stage_b8_dimensions](../integrated/n_20260510T145212Z_stage-b-8-craft-fresh-dimensions.md)
- [stage_c_materialization](../integrated/n_20260510T145212Z_stage-c-craft-materialization.md)
- [v0_4_1_audit](../integrated/n_20260510T145212Z_v0-4-1-post-release-audit-craft.md)
