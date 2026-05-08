# Primordia — craft archive

> **Status**: live index. Append-only record of three-round craft
> documents that proposed + justified every L0/L1/L2/L3 change the
> substrate has absorbed since the greenfield rewrite (2026-04-15).
> **Layer**: L3 archive; these crafts predate or accompany the
> L0–L2 doctrine they govern.

---

## What a "primordium" is

A primordium is a three-round proposal document that stands between
a hypothetical change and a landed commit. Every mutation of L0
vision / L1 contract / L2 doctrine / L3 implementation shape passes
through one. The five rounds are:

1. **主张 (claim)** — the load-bearing assertion the change would
   rest on if approved.
2. **自我反驳 (self-rebuttal)** — the strongest tensions against the
   claim, numbered T1 / T2 / …. Adversarial. Do not defend yet.
3. **修正 (revision)** — answer each tension. Key each response
   R1 / R2 / … back to the numbered Ts. Unresolved tensions are
   kept honest.
4. **再驳 (counter-rebuttal)** — second-order tensions against the
   revisions.
5. **收敛 (convergence)** — the final shape the decision takes. Any
   surviving tension is documented as deferred, not buried.

`myco winnow` enforces the shape. `myco fruit` scaffolds new
primordia. Every primordium is a SSoT for its decision; L0/L1/L2/L3
files cross-reference these docs for provenance.

---

## Index (by era)

### v0.6.0 — 2026-04-28

| File | Kind | Role |
|---|---|---|
| [`v0_6_0_unified_evolution_and_thorough_refactor_craft_2026-04-28.md`](v0_6_0_unified_evolution_and_thorough_refactor_craft_2026-04-28.md) | design | Round 4 owner-amended unified evolution + thorough refactor |
| [`v0_6_0_living_bets_audit_craft_2026-04-28.md`](v0_6_0_living_bets_audit_craft_2026-04-28.md) | audit | Living-bets audit closing v0.6.0 |

### v0.6.11 — 2026-04-28

| File | Kind | Role |
|---|---|---|
| [`v0_6_11_subagents_and_commands_craft_2026-04-28.md`](v0_6_11_subagents_and_commands_craft_2026-04-28.md) | design | Subagents + slash commands (hypha / primordium / anamorph / stipe) |

### v0.6.14 — 2026-04-29

| File | Kind | Role |
|---|---|---|
| [`v0_6_14_cycle_autostart_fruit_winnow_molt_loop_craft_2026-04-29.md`](v0_6_14_cycle_autostart_fruit_winnow_molt_loop_craft_2026-04-29.md) | design | Cycle-自起 fruit—winnow—molt 闭环 orchestrator |

### v0.6.15 — 2026-04-29

| File | Kind | Role |
|---|---|---|
| [`v0_6_15_agent_first_default_for_cycle_autostart_loop_craft_2026-04-29.md`](v0_6_15_agent_first_default_for_cycle_autostart_loop_craft_2026-04-29.md) | design | Agent-First default for the cycle-autostart loop |

### v0.6.16 — 2026-04-29

| File | Kind | Role |
|---|---|---|
| [`v0_6_16_neat_freak_sweep_craft_2026-04-29.md`](v0_6_16_neat_freak_sweep_craft_2026-04-29.md) | design | Neat-freak sweep — surface tidiness pass |

### v0.7.0 — 2026-04-30

| File | Kind | Role |
|---|---|---|
| [`v0_7_0_major_autolysis_craft_2026-04-30.md`](v0_7_0_major_autolysis_craft_2026-04-30.md) | design | Major autolysis — archival moves + autolyze subagent |

### v0.7.1 — 2026-04-30

| File | Kind | Role |
|---|---|---|
| [`v0_7_1_shim_revival_craft_2026-04-30.md`](v0_7_1_shim_revival_craft_2026-04-30.md) | design | `myco.mcp` shim revival hotfix |

### v0.7.2 — 2026-04-30

| File | Kind | Role |
|---|---|---|
| [`v0_7_2_eternal_pruning_ratchets_craft_2026-04-30.md`](v0_7_2_eternal_pruning_ratchets_craft_2026-04-30.md) | design | 永恒删减 ratchet dims + recursion-cutter hardening |

### Glama drives — 2026-04-24 / 2026-04-28

| File | Kind | Role |
|---|---|---|
| [`glama_onboarding_runbook_craft_2026-04-24.md`](glama_onboarding_runbook_craft_2026-04-24.md) | design | Glama onboarding runbook |
| [`glama_usage_drive_craft_2026-04-24.md`](glama_usage_drive_craft_2026-04-24.md) | design | Glama usage drive |
| [`glama_categories_drive_craft_2026-04-28.md`](glama_categories_drive_craft_2026-04-28.md) | design | Glama categories drive |

---

## Archived (v0.4 + v0.5 — under `_landed/`)

The crafts below moved to `_landed/v0_4_x/` and `_landed/v0_5_x/` in
v0.7.0's archival pass. Provenance preserved; paths are relative
to this README.

### Greenfield rewrite — 2026-04-15

| File | Kind | Role |
|---|---|---|
| [`_landed/v0_4_x/greenfield_rewrite_craft_2026-04-15.md`](_landed/v0_4_x/greenfield_rewrite_craft_2026-04-15.md) | design | Umbrella argument for the v0.3 → v0.4 rewrite |
| [`_landed/v0_4_x/l0_identity_revision_craft_2026-04-15.md`](_landed/v0_4_x/l0_identity_revision_craft_2026-04-15.md) | design | L0 vision's five root principles |
| [`_landed/v0_4_x/contract_audit_craft_2026-04-15.md`](_landed/v0_4_x/contract_audit_craft_2026-04-15.md) | audit | Pre-rewrite contract drift audit |

### Stage A–C build-out — 2026-04-15

| File | Kind | Role |
|---|---|---|
| [`_landed/v0_4_x/stage_a_scaffold_craft_2026-04-15.md`](_landed/v0_4_x/stage_a_scaffold_craft_2026-04-15.md) | design | Repo scaffold + tool baseline |
| [`_landed/v0_4_x/stage_b1_core_craft_2026-04-15.md`](_landed/v0_4_x/stage_b1_core_craft_2026-04-15.md) | design | `core/` primitives (canon, context, errors) |
| [`_landed/v0_4_x/stage_b2_homeostasis_kernel_craft_2026-04-15.md`](_landed/v0_4_x/stage_b2_homeostasis_kernel_craft_2026-04-15.md) | design | Immune kernel + exit-policy ladder |
| [`_landed/v0_4_x/stage_b3_genesis_craft_2026-04-15.md`](_landed/v0_4_x/stage_b3_genesis_craft_2026-04-15.md) | design | `myco germinate` (one-shot bootstrap) |
| [`_landed/v0_4_x/stage_b4_ingestion_craft_2026-04-15.md`](_landed/v0_4_x/stage_b4_ingestion_craft_2026-04-15.md) | design | `eat` / `hunger` / `sense` / `forage` |
| [`_landed/v0_4_x/stage_b5_digestion_craft_2026-04-15.md`](_landed/v0_4_x/stage_b5_digestion_craft_2026-04-15.md) | design | `assimilate` / `digest` / `sporulate` pipeline |
| [`_landed/v0_4_x/stage_b6_circulation_craft_2026-04-15.md`](_landed/v0_4_x/stage_b6_circulation_craft_2026-04-15.md) | design | Mycelium graph + `traverse` / `propagate` |
| [`_landed/v0_4_x/stage_b7_surface_craft_2026-04-15.md`](_landed/v0_4_x/stage_b7_surface_craft_2026-04-15.md) | design | Manifest-driven CLI + MCP |
| [`_landed/v0_4_x/stage_b8_dimensions_craft_2026-04-15.md`](_landed/v0_4_x/stage_b8_dimensions_craft_2026-04-15.md) | design | First v0.4 dimension roster |
| [`_landed/v0_4_x/stage_c_materialization_craft_2026-04-15.md`](_landed/v0_4_x/stage_c_materialization_craft_2026-04-15.md) | design | Deliverable + release plumbing |

### v0.4 audit + handoff — 2026-04-15

| File | Kind | Role |
|---|---|---|
| [`_landed/v0_4_x/v0_4_1_audit_craft_2026-04-15.md`](_landed/v0_4_x/v0_4_1_audit_craft_2026-04-15.md) | audit | First full post-v0.4 immune sweep |
| [`_landed/v0_4_x/agent_handoff_v0_4_1_2026-04-15.md`](_landed/v0_4_x/agent_handoff_v0_4_1_2026-04-15.md) | design | Release playbook for agent maintainers |

### v0.5.0 — 2026-04-17

| File | Kind | Role |
|---|---|---|
| [`_landed/v0_5_x/v0_5_0_major_6_10_craft_2026-04-17.md`](_landed/v0_5_x/v0_5_0_major_6_10_craft_2026-04-17.md) | design | MAJOR 6–10 multi-thread release (entry-points discovery, symbiont protocol, etc.) |

### v0.5.2 — 2026-04-17

| File | Kind | Role |
|---|---|---|
| [`_landed/v0_5_x/v0_5_2_editable_default_craft_2026-04-17.md`](_landed/v0_5_x/v0_5_2_editable_default_craft_2026-04-17.md) | design | Editable-by-default install path |

### v0.5.3 — 2026-04-17

| File | Kind | Role |
|---|---|---|
| [`_landed/v0_5_x/v0_5_3_fungal_vocabulary_craft_2026-04-17.md`](_landed/v0_5_x/v0_5_3_fungal_vocabulary_craft_2026-04-17.md) | design | Verb rename (9 verbs, 2 packages) to fungal vocabulary |

### v0.5.5 — 2026-04-17

| File | Kind | Role |
|---|---|---|
| [`_landed/v0_5_x/v0_5_5_close_audit_loose_threads_craft_2026-04-17.md`](_landed/v0_5_x/v0_5_5_close_audit_loose_threads_craft_2026-04-17.md) | audit | MAJOR-A–J cleanup pass |

### v0.5.6 — 2026-04-17 / 2026-04-18

| File | Kind | Role |
|---|---|---|
| [`_landed/v0_5_x/v0_5_6_doctrine_realignment_craft_2026-04-17.md`](_landed/v0_5_x/v0_5_6_doctrine_realignment_craft_2026-04-17.md) | design | Panoramic doctrine sweep |
| [`_landed/v0_5_x/v0_5_6_mp1_mycelium_purity_craft_2026-04-18.md`](_landed/v0_5_x/v0_5_6_mp1_mycelium_purity_craft_2026-04-18.md) | design | MP1 dim — mechanical "Agent calls LLM; substrate does not" |

### v0.5.7 — 2026-04-19

| File | Kind | Role |
|---|---|---|
| [`_landed/v0_5_x/v0_5_7_senesce_quick_mode_craft_2026-04-19.md`](_landed/v0_5_x/v0_5_7_senesce_quick_mode_craft_2026-04-19.md) | design | Bimodal senesce (PreCompact full / SessionEnd --quick) |
| [`_landed/v0_5_x/v0_5_7_release_craft_2026-04-19.md`](_landed/v0_5_x/v0_5_7_release_craft_2026-04-19.md) | audit | v0.5.7 release closure |

### v0.5.8 — 2026-04-21

| File | Kind | Role |
|---|---|---|
| [`_landed/v0_5_x/v0_5_8_discipline_enforcement_craft_2026-04-21.md`](_landed/v0_5_x/v0_5_8_discipline_enforcement_craft_2026-04-21.md) | design | 14 new dims + 4 foundation helpers + R6 mechanical enforcement |
| [`_landed/v0_5_x/v0_5_8_release_craft_2026-04-21.md`](_landed/v0_5_x/v0_5_8_release_craft_2026-04-21.md) | audit | v0.5.8 release closure |

### v0.5.9 — 2026-04-21

| File | Kind | Role |
|---|---|---|
| [`_landed/v0_5_x/v0_5_9_immune_zero_craft_2026-04-21.md`](_landed/v0_5_x/v0_5_9_immune_zero_craft_2026-04-21.md) | design | Immune 121 → 0 findings baseline + JSON-Schema + migration guides |
| [`_landed/v0_5_x/v0_5_9_release_craft_2026-04-21.md`](_landed/v0_5_x/v0_5_9_release_craft_2026-04-21.md) | audit | v0.5.9 release closure |

> The v0.5.3 dogfood smoke craft (`_excreted/dogfood_v0_5_3_smoke_craft_2026-04-18.md`)
> was excreted in v0.6.0 §M1 (empty 9-day-stale DRAFT) and deleted
> outright in v0.7.0's archival pass.

---

## Crafts by kind

- **design (20)** — propose the shape of a change
- **audit (8)** — post-hoc review of a shipped change

Filter via:

```bash
grep -l 'kind: design' docs/primordia/*.md
grep -l 'kind: audit' docs/primordia/*.md
```

## Finding the right craft

- By version: see the "Index (by era)" table above.
- By topic: `myco sense --query <topic>` scans notes + docs + canon.
- By governing L2/L3 doc: read the doctrine page's frontmatter
  `Governing craft:` line; it cites the primordium by filename.

## Adding a new craft

```bash
myco fruit --topic "<slug>" --kind design --date 2026-04-22
```

Fills the three-round skeleton. Fill in each section, then:

```bash
myco winnow --proposal docs/primordia/<slug>_craft_<date>.md
```

`winnow` gates on craft-protocol shape (all five rounds present,
not still template boilerplate, frontmatter fields valid). Landed
crafts typically carry `status: APPROVED` in their frontmatter.

## v0.5.10 note — hotfix, no craft

The v0.5.10 release is a hotfix for four bugs surfaced by a
post-v0.5.9 seven-round audit. Hotfixes don't get their own craft;
the v0.5.9 crafts plus the audit record in the CHANGELOG are the
governance trail. See [`../_archive/CHANGELOG_pre_v0_6.md`](../_archive/CHANGELOG_pre_v0_6.md)
§ `[0.5.10]` for the full audit narrative.
