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

## v0.4 + v0.5 history (excreted at v0.8.5)

The pre-v0.6 craft archive (25 files under `_landed/v0_4_x/` and
`_landed/v0_5_x/`, plus a v0.5.3 dogfood draft that was already
excreted at v0.6.0) was **deleted at v0.8.5** as part of the
"foundation-for-reform" cleanup pass. The crafts documented the
greenfield-rewrite + v0.5 multi-MAJOR sequence; their content is:

- **Summarised** in `.docs/contract_changelog.md` (per-version entries
  describe what each contract bump shipped — the authoritative trail).
- **Recoverable** via git history (`git log --all --diff-filter=D
  --name-only -- '.docs/primordia/_landed/**'` lists them; full
  body lives at the parent commits before deletion).

The substrate is at v0.8.5; the v0.4 / v0.5 crafts had no remaining
operational consumer beyond source-code docstring pointers (which
this pass updates to point at `.docs/contract_changelog.md` sections
instead). Per L0 P3 "永恒进化", contract crafts are immutable HISTORY
but history is preserved by git — file-tree presence is not the
mechanism.

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
the contract_changelog § v0.5.9 + § v0.5.10 entries carry the
governance trail. See `.docs/contract_changelog.md` for the full
audit narrative. (The pre-v0.6 `_archive/CHANGELOG_pre_v0_6.md`
that previously held the [0.5.10] section was excreted at v0.8.5;
content recoverable via git history.)
