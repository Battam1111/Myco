# Myco v0.9

> Branch: `v0.9-genesis`. **L0 v3.1.1.1** (2026-05-19) — descriptive amendments + cross-reference path cleanup chained from v3.1.1 mortality refinement.

Myco is a biology-rooted symbiotic digital substrate: an LLM agent + a substrate form an asymmetric pair under Cultivation by a human owner via out-of-band anchor surface. See [`docs/architecture/L0/README.md`](./docs/architecture/L0/README.md) for the canonical L0 doctrine.

**New cultivator?** Start at [`GETTING_STARTED.md`](./GETTING_STARTED.md) — the runbook from clone to first conversation.

## Doctrine

Read in order: [`docs/architecture/OUTLINE.md`](./docs/architecture/OUTLINE.md) → [`docs/architecture/L0/`](./docs/architecture/L0/) (META + cards + chengyu + dilemma corpus) → L1 (mechanisms) → L2 (cross-cuts).

- **L0 doctrine** ([`L0/`](./docs/architecture/L0/)): 4-layer stratigraphy — 26 principle cards (P / COV / CHAR / specialized) + 50 chengyu fragments + 49 canonical dilemmas + catechumenate placeholder + META form spec + PROVENANCE chain.
- **L1** (7 files): GOVERNANCE, SKIN, CONTINUITY, SCHEMA, TROPISM, TRAJECTORY, HARD_RULES.
- **L2** (3 files): TRUST_MODEL, FEDERATION, OBSERVABILITY.
- **Extracted refs**: `schemas/`, `algorithms/`, `diagrams/`.
- **Implementation map**: `docs/architecture/L3/`.
- **Audit history**: `docs/audits/` (Phase α/β/γ/δ + DRAFT 9 sealing + v3.1-stratigraphy genesis).

## Implementation

- `substrate/` — Rust substrate daemon (M25 + M26.0 cascade complete; doctrine refactor M27 complete; M-anchor-1..5 anchor surface complete).
- `kernel/` — shared canonical-bytes + bridge + schema + continuity + skin + governance + tropism crates.
- `operators/claude/` — TypeScript operator client.
- `anchor/host/` — owner Ed25519 key custody process (M-anchor-1).
- `anchor/client/` — TypeScript anchor surface client.

## Status

- **L0 v3.1-stratigraphy** sealed 2026-05-18: monolithic DRAFT 9 → 4-layer doctrine institution. Phase 1+2 11-stream research + 3 craft rounds + Phase 3 unknown-unknown hunt. Old `L0_VISION.md` removed; full prior-L0 mapping at [`L0/PROVENANCE.md`](./docs/architecture/L0/PROVENANCE.md) §2. Historical text recoverable via git (`git show e796451:docs/architecture/L0_VISION.md`).
- M-anchor-1..5 anchor surface 100% mechanically realized (§9 sub-mechanisms all LIVE).
- **v3.1 transition ceremony** ([`operators/claude/ceremonies/v3_1_transition/`](./operators/claude/ceremonies/v3_1_transition/)) — dry-run verified end-to-end. Production ceremony pending v3.1-genesis substrate bootstrap. Canonical hashes pinned in `manifest.json`:
  - `prior_l0_hash` (SHA-256 @ e796451) = `5eacf3e7bbb9f8633bcf05266aef24fc27d9ed35bc941c8c2ed50f38233c7f66`
  - `new_l0_hash` (BLAKE3 of canonical-bytes v3.1 bundle) = `b1bec59acc8c5061020640a265a9772e734604425b6eda4b5da1759f9987c699`
- M25 5 critical bugs deferred to M26.1.
- Acknowledged debts named in [`L0/PROVENANCE.md`](./docs/architecture/L0/PROVENANCE.md) §8: Layer C witness tests, Layer B commentary entries, Claude-of-record readings on canonical dilemmas, catechumenate sessions (zero until succession preparation), L1/L2 cross-reference surgical updates (deferred to v0.9.x witness milestone), L1/SKIN backup encryption.

## Build + test

```bash
cargo test --workspace --release         # Rust (substrate + kernel + anchor-surface-host)
cd operators/claude && npm test           # TypeScript operator
cd anchor/client && npm test              # TypeScript anchor surface client
cd kernel/tropism && pytest               # Python (substitute any kernel/* Python crate)
```

## v0.4-v0.8 archaeology

Proto-Myco (v0.4-v0.8.7) is `dead embryo` per L0.5 Decision 3D. Reachable via git tag `v0.8.8-final-embryo`. Not part of v0.9 source tree.
