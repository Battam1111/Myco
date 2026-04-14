# Myco Architecture — v0.4.0 Rewrite

> **Status**: top-down design APPROVED 2026-04-15. Implementation in progress.
> **Audience**: the **agent**. Per L0 principle 1 (Only For Agent —
> 人类无感知), these pages are authored for agent consumption. Humans may
> read them to approve craft-doc changes, but are not the design target.
> **Governing crafts**:
> - `docs/primordia/greenfield_rewrite_craft_2026-04-15.md` (§9 approved decisions)
> - `docs/primordia/l0_identity_revision_craft_2026-04-15.md` (L0 revised to five root principles)

This directory is the **authoritative architecture**. Every layer is
subordinate to the layer above it. In any conflict, the upper layer wins.

## Layer order

| Layer | Path | Meaning |
|-------|------|---------|
| **L0 Vision** | `L0_VISION.md` | What Myco is, three invariants |
| **L1 Contract** | `L1_CONTRACT/` | Seven hard rules + versioning + exit codes + canon schema |
| **L2 Doctrine** | `L2_DOCTRINE/` | Five biological subsystems: responsibility + boundary + interface |
| **L3 Implementation** | `L3_IMPLEMENTATION/` | Package map + command manifest |
| **L4 Substrate** | `_canon.yaml`, `notes/`, `docs/*` | The live instance — re-exported fresh at v0.4.0 |

## Reading order (new agent)

1. `L0_VISION.md` — five root principles (Only For Agent / 永恒吞噬 /
   永恒进化 / 永恒迭代 / 万物互联) + three derived invariants.
2. `L1_CONTRACT/protocol.md` — seven rules you must follow.
3. `L1_CONTRACT/exit_codes.md` — when commands succeed and fail.
4. `L2_DOCTRINE/*.md` — the five subsystems in this order:
   Genesis → Ingestion → Digestion → Circulation → Homeostasis.
5. `L3_IMPLEMENTATION/package_map.md` — where code lives.
6. `L3_IMPLEMENTATION/command_manifest.md` — how commands are registered.

## Contract version discipline

Any change to L0, L1, or L2 is a **contract change** and requires:

1. A new craft doc under `docs/primordia/`.
2. Explicit owner approval recorded in the craft.
3. A `_canon.yaml::contract_version` bump.
4. A `docs/contract_changelog.md` entry.

L3 changes within an existing L2 doctrine are ordinary code changes and
do not require a contract bump (but must still land with tests and
changelog lines).

## What v0.4.0 means

- No code carried forward from v0.3 unless explicitly re-authored against
  this architecture.
- No substrate data carried forward — `_canon.yaml` and `notes/` are
  re-exported clean (per §9 E2).
- Wave numbering resets to Wave 1 (per §9 E5).
- No `legacy/v0.3` branch retained. `v0.3.4-final` tag is the only
  history anchor (per §9 E6).
