# Myco Architecture — v0.6.15

> **Status**: updated through v0.6.15 (2026-04-29). Top-down-refinement
> active; doctrine pages track the canonical v0.6.15 state. See
> `docs/contract_changelog.md` for contract-level history.
> **Audience**: the **agent**. Per L0 principle 1 (Only For Agent —
> 人类无感知), these pages are authored for agent consumption. Humans
> may read them to approve craft-doc changes, but are not the design
> target. The single carved exception is `myco brief` (see L0 §"Addendum
> — declared exceptions").
> **Governing crafts** (recent v0.6.x sequence; the full pre-v0.5.8
> ledger lives in `docs/contract_changelog.md`):
> - `docs/primordia/v0_5_8_discipline_enforcement_craft_2026-04-21.md` (14-dim expansion → 25-dim roster)
> - `docs/primordia/v0_5_9_immune_zero_craft_2026-04-21.md` (CRITICAL-gate baseline at exit-zero)
> - `docs/primordia/v0_6_0_unified_evolution_and_thorough_refactor_craft_2026-04-28.md` (schema v2 + 7th boundary subsystem + 25→46 dim expansion)
> - `docs/primordia/v0_6_0_living_bets_audit_craft_2026-04-28.md` (5 living-bets discipline rituals)
> - `docs/primordia/v0_6_11_subagents_and_commands_craft_2026-04-28.md` (5 fungal subagents + 5 `/myco-` slash commands)
> - `docs/primordia/v0_6_14_cycle_autostart_fruit_winnow_molt_loop_craft_2026-04-29.md` (Cycle 自起 fruit—winnow—molt 闭环 + 3-critic fanout)
> - `docs/primordia/v0_6_15_agent_first_default_for_cycle_autostart_loop_craft_2026-04-29.md` (Agent-First default + 5-critic L0-P1-P5 refactor + Winnow G7 path_allowlist + risk_classifier recursion-cutter)
> - `docs/primordia/v0_6_16_neat_freak_sweep_craft_2026-04-29.md` (this release: 27-patch sweep + autopoietic-loop IOU split rationale)

This directory is the **authoritative architecture**. Every layer is
subordinate to the layer above it. In any conflict, the upper layer wins.

## Layer order

| Layer | Path | Meaning |
|-------|------|---------|
| **L0 Vision** | `L0_VISION.md` | What Myco is — five root principles + three derived invariants + bitter-lesson appendix |
| **L1 Contract** | `L1_CONTRACT/` | Seven hard rules (`protocol.md`) + `versioning.md` + `exit_codes.md` + `canon_schema.md` |
| **L2 Doctrine** | `L2_DOCTRINE/` | Seven biological subsystems: `genesis.md` (Germination) / `ingestion.md` / `digestion.md` / `circulation.md` / `homeostasis.md` / `cycle.md` (6th, v0.6.0+) / `boundary.md` (7th, v0.6.0+); plus `extensibility.md` (the two orthogonal extension axes) |
| **L3 Implementation** | `L3_IMPLEMENTATION/` | `package_map.md` + `command_manifest.md` + `migration_strategy.md` (historical) |
| **L4 Substrate** | `_canon.yaml`, `notes/`, `docs/*` | The live instance |

Note on filenames: `L2_DOCTRINE/genesis.md` keeps its v0.4.0 filename
even though the subsystem renamed to Germination at v0.5.3 — doctrine
filenames are preserved across verb renames so governance history stays
legible. The doc's content uses the canonical v0.5.3+ name.

`L2_DOCTRINE/extensibility.md` is the canonical doc for the two
orthogonal extension axes: per-substrate `.myco/plugins/` (v0.5.3+) and
per-host `src/myco/boundary/host_integration/` (v0.6.0+, renamed from
the pre-v0.6.0 `src/myco/symbionts/` path).

`L2_DOCTRINE/boundary.md` (v0.6.0 NEW) is the doctrine for the 7th
subsystem — the unified outward-interface layer that physically merged
the legacy `surface/` (CLI/MCP/manifest) + `install/` (host writers) +
`mcp/` (MCP launcher) + `symbionts/` (per-host adapters) packages into
`src/myco/boundary/<sub>/`. See its "Sixth seam" and "Subagents and
slash commands" sections for the v0.6.11+ + v0.6.14+ cross-cutting
extensions.

## Reading order (new agent)

1. `L0_VISION.md` — five root principles (Only For Agent / 永恒吞噬 /
   永恒进化 / 永恒迭代 / 万物互联) + three derived invariants + the
   bitter-lesson appendix.
2. `L1_CONTRACT/protocol.md` — seven rules you must follow.
3. `L1_CONTRACT/exit_codes.md` — when commands succeed and fail.
4. `L1_CONTRACT/canon_schema.md` — the SSoT shape of `_canon.yaml`.
5. `L2_DOCTRINE/*.md` — the seven subsystems in this order:
   Germination → Ingestion → Digestion → Circulation → Homeostasis →
   Cycle (6th) → Boundary (7th).
6. `L3_IMPLEMENTATION/package_map.md` — where code lives.
7. `L3_IMPLEMENTATION/command_manifest.md` — how the 20 verbs are
   registered (19 agent + 1 human-facing `brief`, single carved L0 P1
   exception per v0.5.5).

## Contract version discipline

Any change to L0, L1, or L2 is a **contract change** and requires:

1. A new craft doc under `docs/primordia/` (author via `myco fruit`).
2. Explicit owner approval recorded in the craft.
3. A `_canon.yaml::contract_version` bump (author via `myco molt`).
4. A `docs/contract_changelog.md` entry.

L3 changes within an existing L2 doctrine are ordinary code changes and
do not require a contract bump (but must still land with tests and
changelog lines).

## What v0.6.15 means

- **Version**: `__version__ = "0.6.15"`, `contract_version = "v0.6.15"`,
  `schema_version = "2"`.
- **20 verbs**: 19 agent + 1 human-facing `brief` (single L0 P1 exception).
- **46 lint dimensions**: 31 mechanical + 2 shipped + 6 metabolic + 7 semantic
  (full roster in `_canon_lint.yaml`; `myco immune --list` prints the live IDs).
- **7 subsystems**: Germination, Ingestion, Digestion, Circulation,
  Homeostasis, Cycle (6th, v0.6.0+), Boundary (7th, v0.6.0+).
- **Bimodal senesce**: full mode (`assimilate + immune --fix`, blocking
  PreCompact) + quick mode (`assimilate` only, SessionEnd within ~1.5 s).
- **LLM boundary** (v0.6.14 enum reduction from 3 → 2 values):
  `system.llm_policy: "forbidden"` (default) or `"opt-in"`. MP1/MP2/MP3
  + CL1/CL2/CL3 dims cooperate to enforce. The `providers/` opt-in
  package was excreted at v0.6.14 — never populated through 7 minor
  releases (v0.5.6 → v0.6.13).
- **Agent-First default for governance** (v0.6.15+): risk-classified
  craft proposals can land via agent-self-winnow + 7-session/7-day
  public window; owner-veto via `governance.last_winnowed_proposals[].vetoed_at`
  is always-on but observer-mode-by-default. Winnow gate G7 requires
  every craft frontmatter to declare `path_allowlist: list[str]` so
  `core.risk_classifier` can derive the tier from craft content.
- **Plugin marketplace surface** (v0.6.11+): 5 fungal subagents
  (`primordium`, `hypha`, `autolysis`, `stipe`, `anamorph`) + 5
  `/myco-` slash commands at `.claude/{agents,commands}/` (project)
  and `<repo>/{agents,commands}/` (plugin-bundle, declared in
  `.claude-plugin/plugin.json::agents` + `::commands`).
- **10 automated MCP hosts** via `myco-install host <client>`:
  Claude Code, Claude Desktop, Cursor, Windsurf, Zed, VS Code,
  OpenClaw, Gemini CLI, Codex CLI, Goose. The 14 host adapters live
  under `boundary/host_integration/` (renamed from `symbionts/` at v0.6.0).
- **Tooling baseline**: `pyproject.toml` carries `[tool.mypy]` and
  `[tool.ruff]`; CI runs pytest + ruff + mypy + build + twine check
  + per-package coverage floors (`scripts/coverage_floors.py`) on
  every push/PR.
