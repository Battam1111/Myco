# Migration guides

Version-to-version upgrade instructions for operators of downstream
Myco substrates. Each file covers one release boundary where the
kernel contract or behavioural defaults changed in a way that
matters at upgrade time.

| Boundary | Guide | Headline |
|---|---|---|
| v0.5.24 → v0.6.0 | [`v0_5_24_to_v0_6_0.md`](v0_5_24_to_v0_6_0.md) | Round 4 owner-amended single-shot release; thorough refactor + unified evolution |
| v0.7.4 → v0.7.5 | [`v0_7_4_to_v0_7_5.md`](v0_7_4_to_v0_7_5.md) | P0-P6 omnibus; canon schema v2→v3 (`metrics.lint_dim_count` field); upgrader chain walks to latest |
| v0.7.x → v0.8.0 | [`v0_7_x_to_v0_8_0.md`](v0_7_x_to_v0_8_0.md) | First L0 amendment since v0.4.x (Living Bets persistence-budget refinement); canon schema v3→v4 (`system.governance.last_living_bets_audit_at` + `persistence_metrics` cache fields for LB1/LB2) |

### Archived (pre-v0.6 — under `_pre_v0_6/`)

| Boundary | Guide | Headline |
|---|---|---|
| v0.5.7 → v0.5.8 | [`_pre_v0_6/v0_5_7_to_v0_5_8.md`](_pre_v0_6/v0_5_7_to_v0_5_8.md) | write_surface now mechanically enforced; exit codes 4/5 differentiated |
| v0.5.8 → v0.5.9 | [`_pre_v0_6/v0_5_8_to_v0_5_9.md`](_pre_v0_6/v0_5_8_to_v0_5_9.md) | Immune cleanup release (121 → 0 LOW findings); no breaking changes |

Always check [`../contract_changelog.md`](../contract_changelog.md)
for the full authoritative changelog. Migration guides translate
contract-level deltas into operator-visible upgrade steps.
