# Migration guides

Version-to-version upgrade instructions for operators of downstream
Myco substrates. Each file covers one release boundary where the
kernel contract or behavioural defaults changed in a way that
matters at upgrade time.

| Boundary | Guide | Headline |
|---|---|---|
| v0.5.24 → v0.6.0 | [`v0_5_24_to_v0_6_0.md`](v0_5_24_to_v0_6_0.md) | Round 4 owner-amended single-shot release; thorough refactor + unified evolution |

### Archived (pre-v0.6 — under `_pre_v0_6/`)

| Boundary | Guide | Headline |
|---|---|---|
| v0.5.7 → v0.5.8 | [`_pre_v0_6/v0_5_7_to_v0_5_8.md`](_pre_v0_6/v0_5_7_to_v0_5_8.md) | write_surface now mechanically enforced; exit codes 4/5 differentiated |
| v0.5.8 → v0.5.9 | [`_pre_v0_6/v0_5_8_to_v0_5_9.md`](_pre_v0_6/v0_5_8_to_v0_5_9.md) | Immune cleanup release (121 → 0 LOW findings); no breaking changes |

Always check [`../contract_changelog.md`](../contract_changelog.md)
for the full authoritative changelog. Migration guides translate
contract-level deltas into operator-visible upgrade steps.
