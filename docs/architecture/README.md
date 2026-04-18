# Myco Architecture — v0.5.6

> **Status**: updated through v0.5.6 (2026-04-17). Top-down-refinement
> active; doctrine pages track the canonical v0.5.6 state. See
> `docs/contract_changelog.md` for contract-level history.
> **Audience**: the **agent**. Per L0 principle 1 (Only For Agent —
> 人类无感知), these pages are authored for agent consumption. Humans
> may read them to approve craft-doc changes, but are not the design
> target. The single carved exception is `myco brief` (see L0 §"Addendum
> — declared exceptions").
> **Governing crafts** (recent):
> - `docs/primordia/greenfield_rewrite_craft_2026-04-15.md` (§9 approved decisions)
> - `docs/primordia/l0_identity_revision_craft_2026-04-15.md` (L0 revised to five root principles)
> - `docs/primordia/v0_5_3_fungal_vocabulary_craft_2026-04-17.md` (fungal verb rename)
> - `docs/primordia/v0_5_5_close_audit_loose_threads_craft_2026-04-17.md` (8 MAJORs — brief, safe-fix, symbiont protocol, src-in-graph, LLM-boundary, …)
> - `docs/primordia/v0_5_6_doctrine_realignment_craft_2026-04-17.md` (MP1 + doctrine-alignment pass)

This directory is the **authoritative architecture**. Every layer is
subordinate to the layer above it. In any conflict, the upper layer wins.

## Layer order

| Layer | Path | Meaning |
|-------|------|---------|
| **L0 Vision** | `L0_VISION.md` | What Myco is — five root principles + three derived invariants + bitter-lesson appendix |
| **L1 Contract** | `L1_CONTRACT/` | Seven hard rules (`protocol.md`) + `versioning.md` + `exit_codes.md` + `canon_schema.md` |
| **L2 Doctrine** | `L2_DOCTRINE/` | Five biological subsystems: `genesis.md` (Germination) / `ingestion.md` / `digestion.md` / `circulation.md` / `homeostasis.md`; plus `extensibility.md` (in-progress — two orthogonal extension axes) |
| **L3 Implementation** | `L3_IMPLEMENTATION/` | `package_map.md` + `command_manifest.md` + `migration_strategy.md` (historical) + `symbiont_protocol.md` |
| **L4 Substrate** | `_canon.yaml`, `notes/`, `docs/*` | The live instance |

Note on filenames: `L2_DOCTRINE/genesis.md` keeps its v0.4.0 filename
even though the subsystem renamed to Germination at v0.5.3 — doctrine
filenames are preserved across verb renames so governance history stays
legible. The doc's content uses the canonical v0.5.3+ name.

`L2_DOCTRINE/extensibility.md` is authored by a parallel task; when it
lands it will be the canonical doc for the two orthogonal extension
axes (per-substrate `.myco/plugins/` and per-host `src/myco/symbionts/`).
This README references it so future readers follow the cross-link.

## Reading order (new agent)

1. `L0_VISION.md` — five root principles (Only For Agent / 永恒吞噬 /
   永恒进化 / 永恒迭代 / 万物互联) + three derived invariants + the
   bitter-lesson appendix.
2. `L1_CONTRACT/protocol.md` — seven rules you must follow.
3. `L1_CONTRACT/exit_codes.md` — when commands succeed and fail.
4. `L2_DOCTRINE/*.md` — the five subsystems in this order:
   Germination → Ingestion → Digestion → Circulation → Homeostasis.
5. `L3_IMPLEMENTATION/package_map.md` — where code lives.
6. `L3_IMPLEMENTATION/command_manifest.md` — how commands (18 verbs
   at v0.5.6: 17 agent + 1 human `brief`) are registered.
7. `L3_IMPLEMENTATION/symbiont_protocol.md` — per-host Agent-sugar
   seam (defined-but-empty at v0.5.6).

## Contract version discipline

Any change to L0, L1, or L2 is a **contract change** and requires:

1. A new craft doc under `docs/primordia/` (author via `myco fruit`).
2. Explicit owner approval recorded in the craft.
3. A `_canon.yaml::contract_version` bump (author via `myco molt`).
4. A `docs/contract_changelog.md` entry.

L3 changes within an existing L2 doctrine are ordinary code changes and
do not require a contract bump (but must still land with tests and
changelog lines).

## What v0.5.6 means

- **Version**: `__version__ = "0.5.6"`, `contract_version = "v0.5.6"`.
- **18 verbs**: 17 agent verbs + 1 human-facing `brief` (L0 principle 1's
  single carved exception).
- **11 lint dimensions**: M1, M2 (fixable), M3, MF1, MF2, MP1 (v0.5.6
  NEW), SH1, MB1 (fixable), MB2, SE1, SE2.
- **LLM boundary**: Agent calls the LLM; the substrate does not.
  Mechanically enforced via MP1 + `canon.system.no_llm_in_substrate: true`
  (default true; opt-out is `false` + populating `src/myco/providers/`
  + a contract-bumping molt).
- **Safe-fix discipline**: four rules — idempotent / narrow /
  non-destructive / bounded-by-write-surface. See
  `L2_DOCTRINE/homeostasis.md` §"Safe-fix discipline".
- **Mycelium graph covers `src/**/*.py`**: AST import + docstring
  doc-reference edges; persisted at `.myco_state/graph.json` with a
  `sha256(canon_text) + sorted(src_py_mtimes)` fingerprint.
- **10 automated MCP hosts** via `myco-install host <client>`:
  Claude Code, Claude Desktop, Cursor, Windsurf, Zed, VS Code,
  OpenClaw, Gemini CLI, Codex CLI (TOML), Goose (YAML).
