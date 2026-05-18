> **L0 doctrine reference (v3.1 transition note)**: this document was written against the prior monolithic L0 (DRAFT 9 SEALED, 2026-05-17). The canonical L0 doctrine is now `docs/architecture/L0/` (v3.1-stratigraphy, 2026-05-18). References in this document using the old `L0 §x.y` / `P2.a` / `I3` notation resolve to v3.1 cards via `docs/architecture/L0/PROVENANCE.md` §2 mapping table. Surgical update of these references to v3.1 citation form is deferred to a v0.9.x housekeeping pass (coupled with Layer C witness corpus implementation per META §5.4) — see `docs/architecture/OUTLINE.md` §3 for details.

---

# EWMA Salience Algorithm

> Extracted from L1/TROPISM §E. Normative spec lives at L1/TROPISM §E.4 (F25 CI-class).

## Form

```
salience: raw_material_kind × cycle_index → attention_weight ∈ [0, 1]

axis.update_rule(...) filters recent_deltas as:
  effective_delta_strength(δ, axis, cycle) = δ.raw_strength · salience(δ.kind, cycle)
```

## Bootstrap (uniform until N=100 samples)

1. Genesis: `salience(kind, 0) = 1.0` for every kind in spore-schema taxonomy.
2. `n_kind` = times raw material of `kind` was absorbed AND causally cited by a fruited sporocarp in same axis-fruiting window.
3. While `n_kind < N` (seed 100), salience uniformly 1.0.

## Steady-state EWMA (activates at `n_kind ≥ N`)

4. ```
   correlation_score(kind, cycle) =
       (cited_count_in_recent_W_cycles(kind) / total_ingested_in_W(kind))
       — baseline_uniform(K)
   ```
   `W` = EWMA window; `K` = distinct active kinds; `baseline_uniform(K) = 1/K`.

5. ```
   salience(kind, cycle+1) =
       (1 - α) · salience(kind, cycle)  +  α · normalize(correlation_score)
   ```
   Seed α=0.05/cycle. `normalize` = softmax across active kinds.

6. Anti-collapse floor: `salience(kind, cycle) ≥ ε > 0` (seed `ε = 1/(K · 4)`).

## Seeds

| Parameter | Seed | Notes |
|---|---|---|
| N (bootstrap sample count) | 100 | L1-tunable |
| α (EWMA decay) | 0.05/cycle | L1-tunable |
| W (correlation window) | EWMA window | L1-tunable |
| ε (anti-collapse floor) | 1/(K · 4) | K = active kinds |

## Anti-uniformity detection

`salience_entropy(cycle) = -Σ_kind salience(kind, cycle) · log₂(salience(kind, cycle))` over kinds with `n_kind ≥ N`.

| Condition | Grade |
|---|---|
| entropy ≥ `H_threshold = log₂(K_active) · 0.4` for ≥ `W_collapse` (seed 30) | daily |
| entropy ≥ 0.5 for ≥ `2·W_collapse` | elevated |
| entropy ≥ 0.6 for ≥ `4·W_collapse` | CRITICAL (L1/HARD_RULES C23) |

Inverted-logic note: salience COLLAPSING toward uniform = entropy HIGH ("collapse" = attention discipline collapsing).
