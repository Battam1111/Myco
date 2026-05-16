# Myco v0.9

> Branch: `v0.9-genesis`. **L0 DRAFT 9 SEALED** (2026-05-17, commit `e796451`).

Myco is a biology-rooted symbiotic digital substrate: an LLM agent + a substrate form an asymmetric pair under Cultivation by a human owner via out-of-band anchor surface. See [`docs/architecture/L0_VISION.md`](./docs/architecture/L0_VISION.md) for the canonical vision.

## Doctrine

Read in order: [`docs/architecture/OUTLINE.md`](./docs/architecture/OUTLINE.md) → L0 → L1 (mechanisms) → L2 (cross-cuts).

- **L0** (1 file): 12 principles + 11 invariants + Living Bets + anchor surface.
- **L1** (7 files): GOVERNANCE, SKIN, CONTINUITY, SCHEMA, TROPISM, TRAJECTORY, HARD_RULES.
- **L2** (3 files): TRUST_MODEL, FEDERATION, OBSERVABILITY.
- **Extracted refs**: `schemas/`, `algorithms/`, `diagrams/`.
- **Implementation map**: `docs/implementation/`.
- **Audit history**: `docs/audits/`.

## Implementation

- `myco_substrate/` — Rust substrate daemon (M25 + M26.0 cascade complete; doctrine refactor M27 complete).
- `kernel/` — shared canonical-bytes + bridge + schema + continuity + skin + governance + tropism crates.
- `operator_bindings/claude_code/` — TypeScript operator client.
- `anchor_client/` — TypeScript anchor surface client.

## Status

- L0 sealed; doctrine refactor M27 R1-R8 complete (6617 → 1293 doctrine lines, -80.5%).
- M25 5 critical bugs deferred to M26.1; M-anchor-1..5 anchor surface roadmap pending.
- See `docs/audits/draft_9_seal_provenance.md` for sealing history.

## Build + test

```bash
cargo test --workspace --release         # Rust (substrate + kernel)
cd operator_bindings/claude_code && npm test
cd anchor_client && npm test
cd kernel/tropism && pytest               # Python
```

## v0.4-v0.8 archaeology

Proto-Myco (v0.4-v0.8.7) is `dead embryo` per L0.5 Decision 3D. Reachable via git tag `v0.8.8-final-embryo`. Not part of v0.9 source tree.
