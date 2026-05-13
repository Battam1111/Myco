# Myco v0.9 — Ground-up rewrite

> **Branch**: `v0.9-genesis` (orphan; zero shared history with `main`).
> **Status**: GENESIS in progress. The first artifact (this branch's L0)
> exists; the rest of the substrate is being designed from α.

## What this branch is

Per L0.5 Decision 3D (recorded in the `main` branch at commit `e47118f`,
authored 2026-05-13), the v0.4 → v0.8.7 line of Myco is **proto-Myco /
dead embryo / failed gestation attempts**. The actual Myco that
satisfies α was never born in those iterations; this branch is the
first attempt at **mature Myco birth**.

This branch starts from an empty file tree (orphan branch, no parent
commit on `main`). It inherits:

- **L0's 5 root principles** (碎条根本原则: 只为 Agent / 永恒吞噬 /
  永恒进化 / 永恒迭代 / 万物互联) — verbatim, per L0's "No alternate
  vocabulary" rule.
- **L0.5's 5 owner-arbitrated decisions** (1A agent-substrate
  symbiosis, 2A MAJOR/MINOR governance gate, 3D dead-embryo
  framing, 4B Living Bets observatory, 5E essence-layer lifecycle).
- **L0.5's 3 derived reinforcements** (P1.a self-hosting,
  P1.b'/P1.b'' two-tier human-loop, P2.a inclusion).
- **The brainstorm's 10 fix-Hs** as design constraints.

It does NOT inherit any v0.8.x source code, tests, scripts, schema,
specific verb names, specific lint dimension names, specific
subsystem partition, or specific protocol surfaces. These are all
β-layer choices that v0.9 redesigns from α.

## Archaeology

- [`_archive/proto_myco_v0_8/L0_VISION_proto.md`](./_archive/proto_myco_v0_8/L0_VISION_proto.md) —
  v0.8.x's L0 vision (now retitled "proto" per L0.5 3D).
- [`_archive/proto_myco_v0_8/L0_5_ESSENCE.md`](./_archive/proto_myco_v0_8/L0_5_ESSENCE.md) —
  v0.8 → v0.9 transitional doctrine that carried the 5 decisions.
- [`_archive/proto_myco_v0_8/ESSENCE_BRAINSTORM.md`](./_archive/proto_myco_v0_8/ESSENCE_BRAINSTORM.md) —
  the deliberation log (4 self-corrections + 100%-confidence loop +
  20 candidate holes + 10 fix-Hs).

These three are read-only references. They are NOT the v0.9 doctrine.

## v0.9 doctrine (under construction)

- [`docs/architecture/L0_VISION.md`](./docs/architecture/L0_VISION.md) —
  the new L0 (first artifact in v0.9).

L1, L2, L3 doctrine + src/, tests/, scripts/, schema, canon-equivalent,
entry-page-equivalent, protocol surfaces — all to be designed AFTER
L0 is owner-approved.

## How to follow this branch

```bash
git checkout v0.9-genesis
```

The branch is intentionally orphan; switching from `main` to
`v0.9-genesis` and back wipes/restores entire file trees because
the two branches share no commits.

## When v0.9 ships

At v0.9 launch:

- This branch becomes `main`'s new history (force-push or
  fast-forward via owner decision)
- The old `main` HEAD (`e47118f`, last v0.8.x commit) is preserved
  via a tag `v0.8.8-final-embryo` for archaeological access
- The 14 + 1 = 15 v0.8.x cleanup commits + the full v0.4 → v0.8
  development history live in that tag's reachability
