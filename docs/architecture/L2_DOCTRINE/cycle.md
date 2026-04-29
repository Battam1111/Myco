# L2 — Cycle Doctrine

> **Status**: APPROVED (2026-04-28, v0.6.0 craft).
> **Layer**: L2. Subordinate to `L0_VISION.md` and `L1_CONTRACT/protocol.md`.
> **Governing craft**: `docs/primordia/v0_6_0_unified_evolution_and_thorough_refactor_craft_2026-04-28.md` §F2.
> **Maps to**: `src/myco/cycle/` (canonical 6th subsystem since v0.6.0; named by L0 since v0.5.3).

---

## What this subsystem does

Cycle composes the substrate's own shape change. The five biological
subsystems (Germination / Ingestion / Digestion / Circulation /
Homeostasis) drive the substrate's metabolism on stable form; Cycle
drives **transitions of the form itself**. When a contract bumps,
when a craft proposal lands, when a session closes, when a new
dimension scaffolds, when a substrate-local plugin is grafted — Cycle
is the package that runs the transition.

Cycle is the **only** subsystem that authors changes to the other
five. Every contract bump (`molt`), every doctrine evolution proposal
(`fruit`), every shape-validation gate (`winnow`), every code skeleton
generation (`ramify`), every session-boundary ritual (`senesce`),
every introspection of grafted plugins (`graft`), and the human-facing
rollup (`brief`) sits here.

## Verbs in this subsystem

| Verb | Action | v0.5.2 alias |
|------|--------|--------------|
| `germinate` | Bootstrap a new substrate | `genesis` |
| `senesce` | Session-end ritual (assimilate + immune --fix) | `session-end` |
| `fruit` | Author a 3-round craft proposal | `craft` |
| `winnow` | Gate a craft proposal's shape | `evolve` |
| `molt` | Ship a contract-version bump | `bump` |
| `ramify` | Scaffold a new dim / verb / adapter | `scaffold` |
| `graft` | Manage substrate-local plugins | (new at v0.5.3) |
| `brief` | Human-facing state rollup | (new at v0.5.5; L0 P1 exception #1) |

`germinate` lives in `src/myco/germination/` (its own subsystem) but
is *invoked through* the Cycle composer — birth is the first life-cycle
event. `senesce / fruit / molt / winnow / ramify / graft / brief` all
live in `src/myco/cycle/`.

## Core invariants

1. **Cycle authors transitions; subsystems do not author themselves.**
   Ingestion does not bump its own contract. Digestion does not author
   its own doctrine. Circulation does not validate its own primordia.
   Cycle owns those operations across all subsystems.

2. **Every Cycle verb is idempotent on a settled substrate.** Running
   `senesce` twice when nothing has changed produces no second action.
   Running `winnow` on an already-validated proposal returns pass with
   zero side effects. Running `molt` for a version equal to the current
   `contract_version` is a no-op.

3. **Cycle verbs respect R6 (write-surface).** Even though Cycle is
   the only subsystem authoring shape change, its writes are still
   gated by `_canon.yaml::system.write_surface.allowed`. The exceptions
   for `myco_excrete` (writes audit tombstones to `.myco_state/`) and
   for `myco_brief` (writes nothing — pure read) are both within
   write_surface.

4. **`fruit → winnow → molt`** is the canonical doctrine evolution
   loop. No L0/L1/L2 doctrine change lands without all three steps.
   v0.6.0 adds governance tiering (`risk_classifier.py`) which permits
   agent-self-winnow on low/medium-risk crafts after a session-counted
   public window.

## Cross-subsystem contract

- **Reads** from every subsystem (`graft` introspects all of them;
  `winnow` validates against L0/L1/L2/L3 doctrine across all).
- **Writes** to specific files in every subsystem (e.g. `molt` writes
  `_canon.yaml::contract_version` + `synced_contract_version` +
  `docs/contract_changelog.md`; `senesce` triggers `assimilate` in
  Digestion + `immune --fix` in Homeostasis).
- **Emits** primordia docs under `docs/primordia/<slug>_<kind>_<date>.md`
  via `fruit`; these are consumed by Homeostasis (RL1 dim ensures
  every R-rule is referenced in a craft) and Circulation (graph
  edge added on every fruit).

## Boundary with cross-cutting adapters

`surface/` (CLI + MCP), `install/` (myco-install for hosts),
`symbionts/` (per-host deep adapters), `mcp/` (MCP server entry-point),
and `core/` (canon loader + paths + write_surface guard) are
**cross-cutting adapter packages**, not subsystems. They do not appear
in `canon.subsystems`. They serve every subsystem (Cycle included)
without being part of any one.

This boundary is enforced by:
- **PA4** (mechanical, HIGH after promotion): `core/` may not import
  any subsystem package.
- **PA5** (mechanical, MEDIUM after promotion): cross-cutting adapter
  packages (cycle/surface/install/symbionts/mcp) may not be imported
  BY subsystems. (Note: cycle as 6th subsystem is now itself a
  subsystem, but PA5's intent is meta-subsystem layering — we treat
  cycle for PA5 purposes as both subsystem-of-record AND
  cross-cutting composer; the PA5 check excludes cycle from the
  forbidden-importer list because it legitimately authors all others.)

## Verb-by-verb references

- `germinate`: see `L2_DOCTRINE/genesis.md`.
- `senesce`: see `L2_DOCTRINE/digestion.md` (assimilate phase) and
  `L2_DOCTRINE/homeostasis.md` (immune --fix phase).
- `fruit`: this doctrine page.
- `winnow`: this doctrine page; gates G1-G6 documented in
  `src/myco/cycle/winnow.py` module docstring.
- `molt`: see `L1_CONTRACT/versioning.md` for the contract-bump
  semantics; this doctrine for the verb's role.
- `ramify`: see `L2_DOCTRINE/extensibility.md` for the two extension
  axes the scaffolds belong to.
- `graft`: see `L2_DOCTRINE/extensibility.md` for plugin discovery
  surface.
- `brief`: see `L0_VISION.md:36-49` for the human-facing carved
  exception (L0 P1 exception #1).

## v0.6.0 governance tiering

Per craft v0.6.0 §F25, `winnow` gains `--auto-approve-low-risk` mode
backed by `core/risk_classifier.py`. Risk classification:

- **High-risk** (owner gate required): L0 five principles wording,
  R1-R7 number/semantics, `canon.system.llm_policy` default flip,
  subsystem deletion.
- **Medium-risk** (agent self-winnow + 7-session-7-day public window):
  new dimension addition, new verb alias, fixable-set extension.
- **Low-risk** (agent self-winnow only): typo, JSON-Schema description,
  test fixtures.

`senesce` auto-LANDS expired no-veto proposals from
`canon.governance.last_winnowed_proposals[]` to `status: LANDED`.

Owner-veto via `vetoed_at` field on any pending proposal is
always-on — a missed window is impossible because veto can be
recorded at any time.

## Cycle 自起 fruit—winnow—molt 闭环 (v0.6.14+)

> **Governing craft**: `docs/primordia/v0_6_14_cycle_autostart_fruit_winnow_molt_loop_craft_2026-04-29.md`.
> **Triggering observation** (2026-04-29 owner remark, post neat-freak ingestion): "Myco 吃完之后似乎并不会直接进化自己的内核啊？"

Through v0.6.13 the metabolic flow (`eat → assimilate → sporulate`) and the morphogenetic flow (`fruit → winnow → molt`) were **doctrinally separated and procedurally bridged by 5 manual handoffs** of agent prose. Most insights captured in distilled never reached the kernel because the bridge was too long. v0.6.14 mechanizes 4 of those 5 handoffs while keeping owner-merge-gate as the single remaining synapse. **L0 P1 stays strict**: substrate kernel adds 0 lines of LLM dispatch; orchestration lives entirely in the Claude Code Agent layer (Agent tool sub-agent fanout — analogous host-mediated mechanism to the existing MCP `sampling` exception #2 for `myco fruit`).

### The auto-loop chain

`/myco-evolve <distilled-slug>` (a Claude Code slash command, not a substrate verb) orchestrates:

```
quarantine_distilled        # strip ASCII control + cap 32KB + UNTRUSTED-INPUT marker
        ↓
primordium (autonomous mode) # spawn 3 fungal-named critic sub-agents (mycoparasite /
        ↓                    #  saprotroph / mycorrhiza) via Agent tool with disjoint
        ↓                    #  visibility scopes; synthesize Round 1.5 T-tensions;
        ↓                    #  optional Round 2.5 second fanout
winnow                       # gate craft shape (G1-G6)
        ↓ if LANDED
hypha                        # feasibility trace against current src/
        ↓
anamorph                     # if schema delta needed
        ↓
stipe --branch-only          # branch fruiting/<slug>-<date>; implement; gate quintet;
        ↓                    #  commit; push branch (NOT main); gh pr create with
        ↓                    #  summary + repo-relative path link (NOT full craft text)
gh pr create                 # owner clicks merge or closes-without-merge
```

If owner closes-without-merge: `.github/workflows/auto_revert.yml` deletes the branch and posts a `vetoed_intent` comment on the substrate's auto-evolve tracking issue. The next `senesce` (in any session) reaps these comments and writes `vetoed_at: <timestamp>` into matching entries of `canon.governance.last_winnowed_proposals[]`.

### Sub-agent fanout as the canonical Round 1.5/2.5 critique protocol

The three fungal critic roles use **disjoint visibility scopes** as the diversity mechanism (single-host clones with shared visibility correlate ≈1; disjoint visibility decorrelates):

| Role | Reads | Looks for |
|------|-------|-----------|
| **mycoparasite** (寄生) | draft only (no doctrine, no src/) | break paths: invalid premises, prompt-injection, feedback loops, alert fatigue, single-point-of-failure |
| **saprotroph** (腐生) | L0/L1/L2 doctrine + canon + previous crafts (no draft, no src/) | doctrine drift, vocabulary violations, governance contradictions, schema parity, deprecated paths, dead code |
| **mycorrhiza** (菌根) | src/ + tests/ + .claude/ + .github/ + scripts/ (no draft, no doctrine) | impl traction, API boundaries, hook interfaces, mock infra, byte-identity tests, CI cell coverage |

Critic outputs are **veto votes**, not advisory: any HIGH-severity tension from any critic forces primordium to abort to DRAFT status; only owner override resumes. primordium does NOT adjudicate between conflicting HIGH critics.

### Governance path for auto-craft proposals

Auto-craft proposals are **forcibly classified high-risk** via `canon.governance.auto_evolve_force_high_risk: true`, which makes owner-gate mandatory regardless of content. The 7-session-7-day public-window auto-LAND path from v0.6.0 governance tiering is **explicitly bypassed** for auto-craft (`canon.governance.auto_evolve_pr_window_skip: true`). PR-merge becomes the **sole** gate.

**Two-step owner sign** is required for auto-craft PRs touching:
- L0 / L1 / L2 doctrine paths
- Full R-surface (verb count, dim count, schema_version)
- Multi-file diffs above an owner-set threshold

For these, owner must comment `/sign auto-craft` before clicking merge. Other auto-craft PRs allow normal merge.

### Convergence + budget guards

- `auto_evolve_min_wall_clock_seconds_between: 600` — rate limit, persisted in `.myco_state/last_auto_evolve.txt`, cross-process visible.
- `auto_evolve_distilled_hash_cooldown_senesce: 7` — same distilled-hash cannot trigger again within 7 senesce calls.
- stipe pre-flight refuses any PR diff modifying doctrine paths the originating distilled note references (anti-self-mutation guard).
- `auto_evolve_min_distilled_severity: medium` — LOW distilled does not trigger.
- `auto_evolve_daily_budget_usd: null` — owner sets cap; spend tracked in `.myco_state/auto_evolve_spend.json`.

### Mechanical L0 P1 evidence

MP1 dim extends in v0.6.14: every craft in `docs/primordia/*.md` must carry `authored_by:` frontmatter naming a recognized host (`claude-code-agent`, `cursor-agent`, `claude-desktop-agent`, `cowork-agent`, or `human`). Crafts without host signature → MP1 HIGH finding → winnow refuses entry. This is the mechanical guard that "no craft was authored inside the substrate process".

`grep -r 'Task\|sampling\|provider' src/myco/cycle/` returns **zero** v0.6.14-added hits post-implementation. The auto-loop's intelligence lives in `.claude/` markdown prose (Agent layer); substrate kernel binary unchanged in its provider-coupling stance.

## What Cycle does NOT do

- **Does not** call any LLM (per L0 P1; Cycle's L0 P1 exception #2
  for `myco fruit` content authoring is via MCP `sampling` capability
  OR — since v0.6.14 — via Claude Code's Agent tool sub-agent fanout
  in the auto-loop. Both are host-mediated mechanisms; substrate
  process never imports a provider SDK).
- **Does not** ingest external content (that's Ingestion).
- **Does not** lint individual notes or files (that's Homeostasis).
- **Does not** propagate to downstream substrates (that's Circulation,
  via `propagate`).
- **Does not** persist session state across sessions beyond what
  `senesce` writes (boot_brief.md, integrated notes promoted from raw,
  immune fix outcomes).

## Migration notes

- v0.5.3: package renamed `myco.meta` → `myco.cycle`. Shim at
  `myco.meta` re-exports for backward compat.
- v0.6.0: cycle promoted to 6th subsystem in `canon.subsystems`; this
  doctrine page authored. No verb signatures changed. v0.5.x
  substrates auto-upgrade canon via schema_upgrader v1→v2.
- v1.0.0 (planned): `myco.meta` shim removed; v0.5.2 verb aliases
  (genesis/reflect/distill/perfuse/session-end/craft/bump/evolve/
  scaffold) removed. See `digestion.md:120-122` for shared schedule.
