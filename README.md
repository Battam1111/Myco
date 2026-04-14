# Myco — v0.4.0 Greenfield Rewrite (in progress)

> **Audience**: the LLM agent. Per L0 principle 1 (Only For Agent —
> 人类无感知), this repository's interior surfaces are authored for agent
> consumption.

---

## Current state

Myco is mid-rewrite. The pre-rewrite kernel, substrate, tests, docs,
wiki, and all other v0.3 content have been quarantined into
[`legacy_v0_3/`](./legacy_v0_3/) so they do not influence the rewrite.
Only the new top-down architecture, its governing crafts, and the
Stage A+ build surface live at the top level.

```
/
├── docs/
│   ├── architecture/          # L0-L3 authoritative design (start here)
│   └── primordia/             # Governing craft docs
├── src/myco/                  # reborn Myco — THE myco (no v4 suffix)
├── tests/                     # unit + integration tests for the new kernel
├── pyproject.toml             # fresh build config (hatchling dynamic version)
├── legacy_v0_3/               # Frozen pre-rewrite snapshot (to be deleted at v0.4.0)
├── CHANGELOG.md
├── LICENSE
├── README.md
└── .git/
```

The `_canon.yaml` substrate and `MYCO.md` agent entry page do **not**
yet exist at the root; they are authored fresh at Stage C.

## For the agent

Read, in order:

1. [`docs/architecture/L0_VISION.md`](./docs/architecture/L0_VISION.md) —
   five root principles (Only For Agent / 永恒吞噬 / 永恒进化 / 永恒迭代 /
   万物互联).
2. [`docs/architecture/L1_CONTRACT/`](./docs/architecture/L1_CONTRACT/) —
   seven hard rules, versioning, exit codes, canon schema.
3. [`docs/architecture/L2_DOCTRINE/`](./docs/architecture/L2_DOCTRINE/) —
   five subsystems (Genesis / Ingestion / Digestion / Circulation /
   Homeostasis).
4. [`docs/architecture/L3_IMPLEMENTATION/`](./docs/architecture/L3_IMPLEMENTATION/) —
   package map, command manifest, migration strategy.
5. [`docs/primordia/greenfield_rewrite_craft_2026-04-15.md`](./docs/primordia/greenfield_rewrite_craft_2026-04-15.md) —
   the approved greenfield charter (§9 decisions are binding).
6. [`docs/primordia/l0_identity_revision_craft_2026-04-15.md`](./docs/primordia/l0_identity_revision_craft_2026-04-15.md) —
   the L0 identity revision (five root principles).

## What's in `legacy_v0_3/`

Everything the pre-rewrite Myco shipped — `src/myco/` v0.3 kernel, the
old `MYCO.md` / `CLAUDE.md` / READMEs, the old `_canon.yaml`, every
`notes/` and `wiki/` entry, every old craft doc, CI workflows, plugin
bundle, and assets. **None of it is referenced by the new architecture.**
It exists only so that:

- The history tag `v0.3.4-final` remains reviewable on disk (not just in
  git history) while the rewrite is in progress.
- The ASCC migration script (Stage C) has a local reference when it
  translates old substrate fields into the new schema.
- If a specific well-defined piece of v0.3 logic turns out to be worth
  re-authoring under v0.4 doctrine, the agent can read it — NOT port it
  verbatim.

The pre-rewrite directory will be **deleted** at the v0.4.0 release
commit (Stage C). Nothing inside it is a dependency of the rewrite.

## Upcoming work (per migration strategy)

The plan is laid out in
[`docs/architecture/L3_IMPLEMENTATION/migration_strategy.md`](./docs/architecture/L3_IMPLEMENTATION/migration_strategy.md):

- **Stage A** — scaffold `src/myco/` and `tests/` directly. No v4
  marker, no staging path — this IS the reborn Myco itself.
- **Stage B** — build the eight packages top-down (core → homeostasis
  kernel → genesis → ingestion → digestion → circulation → surface →
  dimensions).
- **Stage C** — fresh `_canon.yaml` + `MYCO.md`, ASCC migration
  script, delete `legacy_v0_3/`, tag `v0.4.0`.

Nothing is pushed to origin until v0.4.0 AND separate owner approval.
