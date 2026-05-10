---
proposed_doctrine: v0-5-x-discipline-and-fungal-vocabulary-retrospective
sources:
- notes/integrated/n_20260510T145212Z_3.md
- notes/integrated/n_20260510T145212Z_4.md
- notes/integrated/n_20260510T145212Z_5.md
- notes/integrated/n_20260510T145212Z_6.md
- notes/integrated/n_20260510T145212Z_7.md
- notes/integrated/n_20260510T145212Z_8.md
- notes/integrated/n_20260510T145212Z_9.md
- notes/integrated/n_20260510T145212Z_10.md
- notes/integrated/n_20260510T145212Z_11.md
- notes/integrated/n_20260510T145212Z_12.md
- notes/integrated/n_20260510T145212Z_13.md
- notes/integrated/n_20260510T145212Z_14.md
distilled_at: '2026-05-10T14:52:50Z'
stage: distilled
ingest_state: distilled
synthesis_authored_at: '2026-05-10T14:55:00Z'
---

# Distillation: v0.5.x Discipline + Fungal Vocabulary Canonicalization

> 12 crafts span v0.5.0 → v0.5.9 (mid-to-late April 2026). The arc is *discipline maturation*: layering enforcement on top of the v0.4.x scaffold so the substrate's contract becomes mechanical rather than aspirational.

## The five v0.5.x doctrinal landings

1. **v0.5.3 — Fungal vocabulary canonicalization**: `genesis` → `germination`, `perfuse` → `traverse`, `reflect` / `distill` → `assimilate` / `digest` / `sporulate`. Old aliases continue to resolve at the dispatcher layer (1-cycle deprecation), but the canonical vocabulary is now strictly mycological per L0 §"Biological metaphor (authoritative)". Future doctrine docs and substrate-internal references must use the canonical names. This was *vocabulary as enforcement* — the rename forced every prior craft to be reread under new terms, surfacing inconsistencies that a `s/genesis/germination/g` couldn't catch.

2. **v0.5.6 — MP1 Mycelium Purity dim**: mechanical / HIGH dim refusing any LLM-provider import inside `src/myco/**`. Codifies L0 §1's "Agent calls the LLM; the substrate does not" carved exception. The `system.no_llm_in_substrate: false` opt-out gate exists but stays UNUSED through the entire v0.5.x cycle (and into v0.6.x). MP1 is the substrate's first *opt-in machinery that nobody opts in to* — the discipline holds.

3. **v0.5.7 — Senesce quick mode**: `myco senesce --quick` for the SessionEnd hook's ~1.5s kill budget. Quick mode performs only `assimilate` (not `immune --fix`). The full senesce ritual runs at next SessionStart. This was a *reality-meets-OS* compromise — Claude Code's hook budget is finite; Myco's protocol must fit.

4. **v0.5.8 — Discipline enforcement**: the credential deny-list (`.env*`, `id_rsa*`, `*.pem`, etc.) added to text_file adapter after a real incident where `myco eat ~/project` ingested an `.env` containing AWS credentials into raw notes. This is the prototype for v0.7.x's "external bug workaround discipline" — when the substrate did the harmful thing, fix the substrate's surface, codify the deny-list, regression-test the workaround.

5. **v0.5.9 — Immune-zero**: the moment the substrate's own `myco immune` count hit 0 findings. This was the first proof that the homeostasis kernel could converge — that "self-validating substrate under continuous change" is a reachable state, not just a contract claim. Every subsequent cycle (v0.6.x, v0.7.x) treats immune-zero as the release gate.

## What v0.5.x cemented for v0.7.10

The discipline maturation here is the foundation for everything ratchet-shaped in v0.7.x. MB8 (shim hits) is a v0.5.6-MP1-style mechanical anchor. The credential deny-list grew across adapters (chat-log, sqlite, email, git-history all inherit it). Senesce quick mode + immune-zero together define what "release-clean" means at the per-cycle level. The v0.5.9 immune-zero gate became the implicit pre-flight that the gate quintet enforces today.

## Source notes (graph back-references)

- [v0_5_0_major_6_10_craft](../integrated/n_20260510T145212Z_3.md)
- [v0_5_2_editable_default_craft](../integrated/n_20260510T145212Z_4.md)
- [v0_5_3_fungal_vocabulary_craft](../integrated/n_20260510T145212Z_5.md)
- [v0_5_5_close_audit_loose_threads_craft](../integrated/n_20260510T145212Z_6.md)
- [v0_5_6_doctrine_realignment_craft](../integrated/n_20260510T145212Z_7.md)
- [v0_5_6_mp1_mycelium_purity_craft](../integrated/n_20260510T145212Z_8.md)
- [v0_5_7_release_craft](../integrated/n_20260510T145212Z_9.md)
- [v0_5_7_senesce_quick_mode_craft](../integrated/n_20260510T145212Z_10.md)
- [v0_5_8_discipline_enforcement_craft](../integrated/n_20260510T145212Z_11.md)
- [v0_5_8_release_craft](../integrated/n_20260510T145212Z_12.md)
- [v0_5_9_immune_zero_craft](../integrated/n_20260510T145212Z_13.md)
- [v0_5_9_release_craft](../integrated/n_20260510T145212Z_14.md)
