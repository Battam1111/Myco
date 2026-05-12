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
| v0.8.0 → v0.8.5 | _(no breaking changes; all v0.8.x deltas additive)_ | Canon-configurable substrate layout: three new `canon.system.{canon_filename, notes_dir, docs_dir}` fields. Absent fields fall through to legacy defaults `_canon.yaml` + `notes/` + `docs/`. Existing substrates work unmodified. v0.8.5 retired `boundary.host_integration` (14 adapter modules) + `surface.capability` + MF3 dim — all unreachable from production code paths; downstream consumers had zero call sites. |

### Pre-v0.6 (excreted at v0.8.5)

The v0.5.7→v0.5.8 (write_surface mechanical enforcement) and
v0.5.8→v0.5.9 (immune-zero baseline) migration guides were deleted
at v0.8.5 — the substrate has been on v0.6+ for 8 minor releases
and no live consumer paths upgrade across that boundary. The
contract-level deltas are recorded in `.docs/contract_changelog.md`
§§ v0.5.7-v0.5.9; full guide bodies recoverable via git history.

Always check [`../contract_changelog.md`](../contract_changelog.md)
for the full authoritative changelog. Migration guides translate
contract-level deltas into operator-visible upgrade steps.
