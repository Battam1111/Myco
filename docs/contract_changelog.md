# Contract Changelog

Append-only record of contract-version bumps. A contract bump is
required whenever R1–R7 change, subsystem definitions change, the
exit-code policy grammar changes, the lint-dimension inventory changes
semantics, or the command manifest changes a verb's shape. Adding a
new lint dimension inside an existing category is a changelog line but
not a bump.

Format: one section per `contract_version`, newest first.

---

## v0.5.10 — 2026-04-21 — Audit-response hotfix (no contract-shape change)

Contract-layer molt with **zero contract-surface deltas**, exactly
like v0.5.9. This molt pairs a version number to four bug fixes
surfaced by a seven-round post-release audit of v0.5.9.

### What changed

- **Nothing in the R1–R7 rule text.** No rule added, removed, or
  semantically modified.
- **Nothing in the category enum, the exit-policy grammar, or the
  exit-code ladder** (3 / 4 / 5).
- **Nothing in the 18-verb manifest surface.**
- **Nothing in the dimension roster count** (still 25).

### Bugs fixed (audit response)

1. **``SubstrateNotFound`` exit-code preserved** — `build_context`
   no longer wraps the exception in `UsageError`, restoring the
   v0.5.8 contract-promised exit 4. Scripts that check `exit == 4`
   for "no substrate at this path" now actually work.
2. **Fresh-substrate lint noise removed** — the canon template
   trimmed of kernel-path `_ref` fields that produced 5 MEDIUM
   findings on every freshly-germinated substrate. Fresh
   substrates now report 0 immune findings out of the box.
3. **RL1 skips on missing protocol.md** — RL1 requires
   ``docs/architecture/L1_CONTRACT/protocol.md`` to exist; fresh
   substrates without it produce no RL1 findings.
4. **Canon JSON-Schema ``subsystems.*.doc`` made optional** to
   match the Python kernel validator's actual requirements.

### Added (non-contract, additive)

- ``.myco_state/unsafe_writes.log`` — best-effort audit trail that
  `guarded_write` appends to on every `MYCO_ALLOW_UNSAFE_WRITE=1`
  bypass. Resolves a v0.5.9 deferred TODO.

### Break from v0.5.9

None at the contract layer. Operators upgrading from v0.5.9
require **no code changes, no canon edits, no script adjustments**.

Observable differences for new germinations:
- The canon template is smaller: `versioning`, `commands.manifest_ref`,
  `subsystems.*.doc`, `hard_contract.rules_ref`, `waves.log_ref` are
  no longer stamped by default. Kernel-like substrates that want
  them back add them manually.
- Fresh substrates get 0 immune findings (was 10 on v0.5.9).

Existing v0.5.9 substrates with the full canon shape continue to
load and lint cleanly under v0.5.10.

---

## v0.5.9 — 2026-04-21 — Immune-zero cleanup release (no contract-shape change)

Contract-layer release with **zero contract-surface deltas**. This
molt exists solely to pair a version number to the immune-zero
baseline substrate state + the JSON-Schema / migration-guide
ecosystem additions.

Governing crafts:
[`docs/primordia/v0_5_9_immune_zero_craft_2026-04-21.md`](primordia/v0_5_9_immune_zero_craft_2026-04-21.md)
(design) and
[`docs/primordia/v0_5_9_release_craft_2026-04-21.md`](primordia/v0_5_9_release_craft_2026-04-21.md)
(release closure).

### What changed

- **Nothing in the R1–R7 rule text.** No rule added, removed, or
  semantically modified.
- **Nothing in the category enum** (`mechanical` / `shipped` /
  `metabolic` / `semantic` unchanged) or the exit-policy grammar.
- **Nothing in the 18-verb manifest surface** (no new verb, no
  arg-shape change, no alias retirement).
- **Nothing in the dimension roster count** (still 25). One dim's
  _implementation_ refined (DC2 exempts `@property` +
  abstract-protocol overrides, matching its v0.5.8 docstring
  intent); no change to its id, category, or severity.
- **Nothing in the MycoError exit-code ladder** (3 / 4 / 5
  unchanged from v0.5.8).

### Added (non-contract, additive)

- Canon JSON-Schema at `docs/schema/canon.schema.json` (Draft
  2020-12). Second mechanical check alongside
  `myco.core.canon.load_canon`.
- Migration guides at `docs/migration/v0_5_7_to_v0_5_8.md` +
  `docs/migration/v0_5_8_to_v0_5_9.md`.
- Public `check_write_allowed` + `unsafe_bypass_enabled` API in
  `myco.core.write_surface` (promoted from private naming).
- Doctrine-ref anchors in 32 pre-v0.5.8 kernel module docstrings
  (completes the code → doctrine mycelium edges).

### Break from v0.5.8

None at the contract layer. Operators upgrading from v0.5.8
require **no code changes, no canon edits, no script adjustments**.
Everything additive; every old behavior preserved.

The only observable difference at the lint layer: `myco immune` on
the self-substrate now reports 0 findings where v0.5.8 reported
121 LOW. Downstream substrates will see their own DC2/DC4/CG1/CG2
findings reduced proportionally (the DC2 refinement in particular
drops findings for every adapter / dimension subclass).

---

## v0.5.8 — 2026-04-21 — Cleanup release: 14-dim lint expansion + foundation helpers

Contract-layer release with one visible contract-surface delta
(two `MycoError` exit codes differentiated within the `≥3` band)
and a substantial lint-roster expansion (11 → 25 dims, all within
existing categories).

Governing crafts:
`docs/primordia/v0_5_8_discipline_enforcement_craft_2026-04-21.md`
(14-dim expansion + 4 foundation helpers design) and
`docs/primordia/v0_5_8_release_craft_2026-04-21.md` (release
closure craft).

### What changed

- **Lint dimension inventory: 11 → 25.** All 14 new dims land in
  existing categories (no new `Category` enum values; no
  exit-policy grammar change). Per v0.5.7 policy, adding a dim
  inside an existing category is a changelog line but not a
  hard-contract change — the bump from v0.5.7 to v0.5.8 is
  motivated by the *exit-code differentiation* below, not the
  dim count. New dims:

  | ID | Category | Severity | Summary |
  |---|---|---|---|
  | `MP2` | mechanical | MEDIUM | Plugin-tree LLM-SDK import ban |
  | `DC1` | mechanical | LOW | Module docstring present |
  | `DC2` | mechanical | LOW | Public function/method docstring |
  | `DC3` | mechanical | LOW | Public class docstring |
  | `DC4` | mechanical | LOW | Non-trivial module references doctrine |
  | `CS1` | mechanical | HIGH (fixable) | `synced_contract_version` sync |
  | `FR1` | mechanical | HIGH/MEDIUM | Fresh-substrate directory invariants |
  | `PA1` | mechanical | MEDIUM | `write_surface.allowed` coverage |
  | `CG1` | mechanical | LOW | L2 doctrine has src reference |
  | `CG2` | mechanical | LOW | src subpackage has doctrine link |
  | `DI1` | mechanical | MEDIUM | `.claude/hooks.json` present |
  | `MB3` | metabolic | HIGH (fixable) | Raw-notes high watermark |
  | `SE3` | semantic | LOW | Graph has no self-cycles |
  | `RL1` | semantic | LOW | R1-R7 rules each referenced |

- **Exit-code differentiation.**
  - `SubstrateNotFound.exit_code` was `3`; is now `4`.
  - `CanonSchemaError.exit_code` was `3`; is now `5`.
  - All other `MycoError` subclasses unchanged (`ContractError`,
    `UsageError`: `3`).
  - Both new codes stay within the `≥3` operational-failure band
    the L1 exit-code contract reserves. CI scripts that check
    `exit != 0` see no change; scripts that special-case `== 3`
    for substrate/canon failures now see `== 4` / `== 5`.

- **Fresh-substrate directory invariants pre-provisioned.**
  `myco germinate` now creates `notes/raw/` and
  `notes/integrated/` up front (was: lazy on first
  `eat`/`assimilate`). No contract-surface impact on existing
  substrates; only fresh germinations see the new layout.

- **Canon schema `lint.dimensions` block expanded.** The canonical
  roster at `_canon.yaml::lint.dimensions` now declares all 25
  dims. Substrates upgrading from v0.5.7 continue to parse
  cleanly — unknown dim ids in the canon are tolerated (MF1
  cross-checks but does not reject).

### Break from v0.5.7

- **Exit codes**: any downstream script that string-matches on
  `exit == 3` for `SubstrateNotFound` or `CanonSchemaError` sees
  different behaviour at v0.5.8. The new codes are additive
  within the contract band; scripts checking `exit != 0` are
  unaffected.
- **Lint surface**: a substrate that ran `myco immune` clean at
  v0.5.7 may see new MEDIUM/LOW findings at v0.5.8 from the 14
  new dims. The default CI gate
  (`--exit-on=mechanical:critical,shipped:critical,…`) is
  unaffected; operators who gate at MEDIUM or lower should
  review the new findings.
- **Fresh-substrate shape**: new germinations include
  `notes/raw/` + `notes/integrated/`. Substrates relying on
  "notes/ empty until first eat" as a signal of freshness should
  switch to the `.myco_state/autoseeded.txt` marker (canonical
  since v0.4.0).

Everything else — R1-R7 text, category enum, exit-policy grammar,
manifest shapes, the 18-verb surface — is unchanged from v0.5.7.

---

## v0.5.7 — 2026-04-19 — Bimodal senesce + v0.5.6 postponement closure

Contract-layer release with one user-visible contract-surface delta
(R2 now names both PreCompact-full and SessionEnd-quick paths) and
one new payload invariant (every `senesce` Result carries a `mode`
key and a shape-stable `immune` field).

Governing crafts:
`docs/primordia/v0_5_7_senesce_quick_mode_craft_2026-04-19.md` (the
bimodal-senesce design) and
`docs/primordia/v0_5_7_release_craft_2026-04-19.md` (the release-
closure audit that bundles all four v0.5.7 audit streams).

### Contract surface at v0.5.7

- **18 verbs** unchanged from v0.5.6 (17 agent + 1 human `brief`).
  No new verb. The `senesce` verb gains one bool arg (`quick`,
  default false) — manifest-level addition, not a verb addition.
- **11 lint dimensions** unchanged from v0.5.6.
- **R2 wording** expanded: *"Every session ends with `myco senesce`
  — full (assimilate + immune --fix) on PreCompact, quick
  (assimilate only) on SessionEnd. The canonical session-end is
  the full form; quick is defense-in-depth for short-budget
  hosts."* R1, R3-R7 unchanged.
- **New payload invariant (promise across v0.5.x):** every
  `senesce` Result payload has shape `{reflect: {...}, immune:
  {...}, mode: "full"|"quick"}`. In quick mode, `immune` is
  `{skipped: true, reason: <str>}`. In full mode, `immune` is the
  full `run_immune` payload dict. Downstream consumers (`brief`,
  hunger sidecar, MCP initialize echo) read `payload["immune"]`
  unconditionally; both modes produce a dict.
- **Hook layout: three hooks (was two)** — SessionStart,
  PreCompact, SessionEnd — documented in `.claude/hooks/*.md`,
  `hooks/hooks.json` description, and the L1 R2 enforcement
  table.

### What changed

1. **R2 text upgrade** in `L1_CONTRACT/protocol.md` to name both
   hook-bound execution paths and the full/quick split.
2. **MCP instructions template** (`src/myco/surface/mcp.py`) —
   the R2 echo updated to match the new L1 wording verbatim.
   Every non-Claude-Code MCP client sees the upgraded contract at
   `initialize`. Canonical verb name in the echo is now
   `myco_senesce` (was `myco_session_end`) and `assimilate` (was
   `reflect`).
3. **`senesce` payload `mode` key** — additive, backward-
   compatible. Old readers ignore it; new readers can switch on
   it. The `immune: {skipped: true, ...}` shape in quick mode is
   the invariant downstream consumers key on.
4. **Editorial drift cleanup from v0.5.6 postponements** —
   seventeen → eighteen verbs, ten → eleven dimensions, seven →
   ten hosts, stale `metrics.test_count` in canon, plugin.json
   description, R2 enforcement table across all 19+ doctrine /
   surface files.
5. **Mechanical CI baseline** — `.github/workflows/ci.yml` runs
   ruff + mypy + pytest + immune + build + twine on push/PR.
   Baseline lets the next release cycle depend on mechanical
   enforcement of what v0.5.7 had to clean up by hand.

### Break from v0.5.6

None for substrate readers. v0.5.6 canons parse under v0.5.7
unchanged. Every v0.5.6 verb invocation still resolves. The only
user-visible behavior change is that installing the Myco plugin in
Claude Code now registers a third SessionEnd hook — which simply
runs `senesce --quick` at session exit. If a downstream has
customized its Claude Code hooks config, the upgrade is additive
(drop in the third hook block).

### Doctrine files touched

- `L1_CONTRACT/protocol.md` — R2 prose + enforcement table.
- `L1_CONTRACT/versioning.md` — Current state block v0.5.6 →
  v0.5.7.
- `L1_CONTRACT/canon_schema.md` — Example YAML shape v0.5.6 →
  v0.5.7 (dimension roster + affected_dimensions annotations).
- `L1_CONTRACT/exit_codes.md` — `At v0.5.6 that list is empty` →
  `v0.5.7`.
- `L3_IMPLEMENTATION/command_manifest.md` — Verb inventory header
  + senesce row `--quick` arg annotation.
- `L3_IMPLEMENTATION/package_map.md` — Layout header + providers/
  + symbionts/ + install/ state annotations.
- `L3_IMPLEMENTATION/symbiont_protocol.md` — "Automated hosts at
  v0.5.6" → v0.5.7.
- `src/myco/surface/mcp.py` — `_INSTRUCTIONS_TEMPLATE` R2 line.
- `src/myco/cycle/senesce.py` — quick-mode implementation + full
  module docstring.
- `MYCO.md` — finish-a-session block names both hooks.
- Trilingual READMEs — verb table + daily-flow paragraph name
  the SessionEnd/senesce-quick path.

---

## v0.5.6 — 2026-04-17 — Doctrine realignment + mechanical LLM-boundary guard + bitter-lesson appendix

A contract-layer release with two user-visible contract-surface
deltas + a deep doctrine realignment across all L0-L3 pages.

Governing craft:
`docs/primordia/v0_5_6_doctrine_realignment_craft_2026-04-17.md`.

### Contract surface at v0.5.6

- **18 verbs** unchanged from v0.5.5 (17 agent + 1 human-facing
  `brief`). No new verb ships at v0.5.6.
- **11 lint dimensions** (was 10): **MP1** added (mechanical /
  HIGH / not fixable). "No LLM-provider import from `src/myco/**`
  unless `canon.system.no_llm_in_substrate: false`." Mechanically
  enforces the v0.5.5 L0-principle-1 addendum "Agent calls the
  LLM; the substrate does not".
- **New canon field** `system.no_llm_in_substrate: bool`. Default
  `true`. Opt-out requires `false` + populating
  `src/myco/providers/` + contract bump. Graceful on v0.5.5 canons
  (optional-with-default).
- **New L2 doctrine page** `L2_DOCTRINE/extensibility.md`. Single-
  source for the two orthogonal extension axes (per-substrate
  `.myco/plugins/` ⊥ per-host `src/myco/symbionts/`). Cross-linked
  from L0 principle 5 and L2 homeostasis.
- **L0 principle 1 addendum** — declared exceptions (`brief` human
  window + Agent-calls-LLM boundary) written inline.
- **L0 bitter-lesson appendix** — names the review cadence for the
  coordination-surface bet (every MAJOR re-audits) and the
  redesign trigger.

### What changed

1. **MP1 mechanical guard** — scans `src/myco/` for provider-SDK
   imports; cross-checks canon `no_llm_in_substrate`; HIGH
   finding when declared-true-but-violated. Bitter-lesson-aligned
   (keeps Myco compute-scale-invariant).
2. **`system.no_llm_in_substrate` canon field** — declared
   intent, backed by MP1 mechanical scan.
3. **`src/myco/providers/` reserved package** — declared opt-in
   escape hatch for future LLM-coupling. Empty at v0.5.6.
4. **34 doctrine alignment edits** — every S1/S2/S3 from the
   v0.5.5 panoramic audit landed as concrete corrections across
   L0/L1/L2/L3 + architecture README. Top items: 18-verb
   inventory (was 17), 11-dimension enumeration table, fixable-
   dimension + safe-fix discipline doctrine, hunger payload shape
   correction, sporulate output-shape doctrine, graph API
   doctrine, package_map refresh.
5. **Bitter-lesson appendix** at L0 — holds principles 3 and 4
   accountable to a review cadence rather than treating the
   current structure as eternal truth.

### Break from v0.5.5

None for substrate readers. v0.5.5 canons parse under v0.5.6
unchanged (new field is optional-with-default-true). Every v0.5.5
verb invocation still works. Every v0.5.x alias still resolves.

One visible contract-surface addition: **fresh substrates
authored via `myco germinate` at v0.5.6 now include
`system.no_llm_in_substrate: true` explicitly** in their canon,
declaring their posture on the Agent-LLM-boundary invariant.

### Doctrine files touched

- `L0_VISION.md` — principle 1 addendum + bitter-lesson appendix
  + principle 5 extended with src graph + two-axes; biological-
  metaphor table refreshed
- `L1_CONTRACT/canon_schema.md` — 4 example corrections + new
  field + demo-upgrader note + dangling-ref removal
- `L1_CONTRACT/versioning.md` — current-state v0.5.6 row; "clean
  reflect" → "clean assimilate"
- `L1_CONTRACT/exit_codes.md` — `DIMENSION_CATEGORY` ref removed;
  skeleton-downgrade-now-empty clarified
- `L1_CONTRACT/protocol.md` — two-axes cross-link near R1-R7
- `L2_DOCTRINE/genesis.md` — M2-fix cross-link
- `L2_DOCTRINE/ingestion.md` — eat 3-mode signature + hunger
  payload shape + brief cross-link
- `L2_DOCTRINE/digestion.md` — sporulate output-shape + MP1 guard
- `L2_DOCTRINE/circulation.md` — graph API + fingerprint + cache
  semantics
- `L2_DOCTRINE/homeostasis.md` — 11-dimension table + fixable
  protocol + safe-fix discipline + MP1 section
- `L2_DOCTRINE/extensibility.md` — **NEW** cross-cutting doctrine
- `L3_IMPLEMENTATION/command_manifest.md` — 18-verb table + brief
  sub-section + six gates + payload fixes
- `L3_IMPLEMENTATION/package_map.md` — src tree + mapping matrix
  refresh + providers/ row
- `L3_IMPLEMENTATION/migration_strategy.md` — historical-note
  banner + senesce canonical
- `L3_IMPLEMENTATION/symbiont_protocol.md` — 10-host inventory
- `docs/architecture/README.md` — full rewrite

---

## v0.5.5 — 2026-04-17 — Close every audit loose thread

Eight MAJORs merged into one release. No contract-surface shape
change: 17 verbs + 10 lint dimensions + 5 subsystems + cycle/
package unchanged. The `meta.py` → `meta/` shim, the 9 verb
aliases (`genesis`/`reflect`/`distill`/`perfuse`/`session-end`/
`craft`/`bump`/`evolve`/`scaffold`), the schema_version-permissive
canon reader, and the substrate-local `.myco/plugins/` seam all
keep working.

Governing craft:
`docs/primordia/v0_5_5_close_audit_loose_threads_craft_2026-04-17.md`.

### Contract surface at v0.5.5

- **17 verbs** (was 16, +1 for `brief`). The new `brief` is the
  one explicit human-facing verb — L0 principle 1's single carved
  exception. Does NOT replace any agent-side verb; rolls up their
  outputs for a human review moment.
- **10 dimensions** unchanged count-wise, but **M2 and MB1** are
  now **fixable** — the first real implementations of a feature
  the `immune --fix` flag has promised since v0.4.0. A safe-fix
  discipline (idempotent / narrow / non-destructive / write-
  surface-bounded) is added to L2 homeostasis as new doctrine.
- **5 subsystems + cycle/ package** unchanged. The `symbionts/`
  package is formally defined at v0.5.5 as per-host Agent-sugar
  adapters (orthogonal to substrate-local `.myco/plugins/`); no
  concrete symbiont ships at v0.5.5 but the L3
  `symbiont_protocol.md` documents the slot.
- **`schema_upgraders`** gains its first registered entry: a demo
  `v0→v1` upgrader under key `"0"` (a version never shipped in
  real canons). Substrates with `schema_version: "0"` parse
  silently through the chain-apply path. Real v1→v2 upgrader
  (when schema v2 ships) will register the same way.
- **`myco-install host`** covers 10 hosts (was 7): adds
  gemini-cli (JSON), codex-cli (TOML via block-level surgery),
  goose (YAML with `extensions:` key).
- **Circulation graph** now covers `src/**` (AST-based import +
  docstring-doc-reference edges) and persists to
  `.myco_state/graph.json` with a canon+src fingerprint.

### What changed

- `sporulate` doctrine explicitly bounded: prepares scaffolding,
  does NOT call an LLM. Agent writes the synthesis prose. L0
  principle 1 invariant ("Agent calls LLM, substrate does not")
  now has an explicit doctrine anchor.
- L3 `symbiont_protocol.md` added; `symbionts/__init__.py` rewrites
  to reflect the per-host framing; pre-v0.5.5 "downstream-substrate
  adapters" framing superseded.

### Break from v0.5.4

None. No verb renamed, no manifest shape changed, no canon field
removed. Every v0.5.4 invocation resolves unchanged.

---

## v0.5.4 — 2026-04-17 — Dogfood-session patch (seven bugs fixed)

Patch release; no contract-surface change. Yanjun asked the Agent
to dogfood Myco on the Myco repo; the end-to-end pass surfaced two
critical bugs (broken `ramify` subcommand parsing + broken
substrate-local plugin auto-registration) plus five smaller ones.
All seven are fixed and pinned with regression tests.

### Contract surface at v0.5.4

Unchanged from v0.5.3: R1-R7, 17 verbs (9 with aliases), 10 lint
dimensions, 5 subsystems plus cycle/ package. The substrate-local
plugin seam (`.myco/plugins/` + `manifest_overlay.yaml`) now
actually works end-to-end; before v0.5.4, dimensions registered via
`ramify` were silently invisible to every verb that reads the
registry.

### What changed

1. `myco --version` / `-V` added.
2. Multi-value list flags (`--tags a b c`) parse naturally.
3. Subparser dest renamed from `verb` to `_subcmd` so `ramify
   --verb <name>` no longer clobbers the subcommand selector.
4. `ramify` template fixed: `{{__name__}}` → `{__name__}`.
5. `hunger` payload gains `local_plugins.count_by_kind`.
6. `--json` output gains a top-level `findings: [...]` array.
7. `winnow` gains `G6_template_boilerplate` gate.

### Break from v0.5.3

None. Every v0.5.3 invocation keeps working. The dogfood bugs
were covered-up gaps that only surfaced when the full verb surface
was exercised end-to-end; pre-release tests happened to not cover
these specific paths.

---

## v0.5.3 — 2026-04-17 — Fungal vocabulary + Agent-First + substrate-local plugins

Three concerns merged into one MINOR release. None of them breaks
the v0.5.2 contract surface; every prior invocation keeps working.
Governing craft:
`docs/primordia/v0_5_3_fungal_vocabulary_craft_2026-04-17.md`.

### Contract surface at v0.5.3

- **R1–R7** unchanged.
- **Exit-code grammar** unchanged.
- **Five subsystems** unchanged: Germination (was Genesis),
  Ingestion, Digestion, Circulation, Homeostasis. Cross-cutting
  `cycle/` package (was `meta/`) houses the life-cycle composers.
- **Seventeen verbs** (was sixteen): the v0.5.2 set with nine
  renamed to canonical fungal-biology terms, plus one new verb
  `graft`. Canonical / alias pairs: `germinate` / `genesis`,
  `assimilate` / `reflect`, `sporulate` / `distill`, `traverse` /
  `perfuse`, `senesce` / `session-end`, `fruit` / `craft`, `molt` /
  `bump`, `winnow` / `evolve`, `ramify` / `scaffold`. `hunger`,
  `eat`, `sense`, `forage`, `digest`, `propagate`, `immune` kept
  their v0.4-era names — each is already a biologically accurate
  fungal term.
- **Ten lint dimensions** (was nine): `MF2` added
  (mechanical / HIGH — substrate-local plugin health).

### What changed

1. **Fungal vocabulary rename.** Nine verbs and two packages
   (`myco.genesis` → `myco.germination`, `myco.meta` →
   `myco.cycle`) moved to fungal-biology terms whose semantics
   match the verb's behavior. Old names register as CLI aliases
   and as MCP tool aliases; the Python shim packages at the old
   paths re-export every name from the new location. Cycle's
   `fruit.md.tmpl` replaces `craft.md.tmpl`.
2. **Agent-First framing fix.** Trilingual READMEs, `MYCO.md`,
   `INSTALL.md`, and the L1/L2/L3 doctrine pages audited for
   sentences that said "when you run `myco X`" or "the user runs
   X". L0 principle 1 (只为 Agent) says humans speak natural
   language and the Agent invokes verbs — every verb-invoking
   sentence now names the Agent as the grammatical subject.
3. **Substrate-local plugin loading.** `Substrate.load()` auto-
   imports `<root>/.myco/plugins/__init__.py` under an isolated
   module name; `load_manifest_with_overlay(substrate_root)`
   merges `<root>/.myco/manifest_overlay.yaml` into the packaged
   manifest at `build_context()` time. The new `graft` verb
   (`--list | --validate | --explain <name>`) is the Agent's
   introspection surface; the extended `ramify` verb
   (`--dimension | --adapter | --verb --substrate-local`) is the
   authoring surface. `MF2` lint dimension surfaces shape errors.
   `hunger` payload carries a `local_plugins: {loaded,
   count_by_kind, errors, module}` block so the Agent sees on
   every boot what has grafted onto the substrate.

### Break from v0.5.2

None. Every v0.5.2 `_canon.yaml` parses under v0.5.3 unchanged.
Every v0.5.2 CLI invocation resolves (one-shot `DeprecationWarning`
per alias). Every v0.5.2 MCP tool name (`myco_genesis`,
`myco_reflect`, etc.) remains registered. Every v0.5.2 Python
import path (`from myco.genesis import ...`, `from myco.meta import
session_end_run`) keeps working through its shim package. Alias
removal is scheduled for **v1.0.0** only — the entire 0.x line
stays backward-compatible.

---

## v0.5.2 — 2026-04-17 — Editable-by-default install model

The "Stable kernel, mutable substrate" framing introduced at v0.4.1
— paraphrased as "`pip install` locks the kernel at a released
version" — contradicts L0 principles 3 (永恒进化) and 4 (永恒迭代):
read-only `site-packages` prevents the agent from authoring kernel
code, but L0 principle 1 (只为 Agent) says the agent IS the author.
v0.5.2 flips the documented primary install path to editable and
adds the `myco-install fresh` subcommand to make that path one
command for new users.

### Contract surface at v0.5.2

- **R1–R7** unchanged.
- **Exit-code grammar** unchanged.
- **Subsystems** unchanged (5 + `meta/` package from v0.5.1).
- **Sixteen verbs** unchanged.
- **Nine lint dimensions** unchanged.
- **`myco-install`** — new subcommand layout (`fresh` + `host`);
  legacy `myco-install <client>` still works via auto-route.

### What changed

- Primary documented install: `pipx run --spec 'myco[mcp]'
  myco-install fresh ~/myco` (or the two-step equivalent).
- `pip install myco` demoted to a secondary, library-consumer
  path. Not deprecated — still produces a working install; just
  does not deliver on L0 principle 3/4 because the kernel at
  `<site-packages>/myco/` is read-only.
- Kernel upgrades migrate from `pip install --upgrade` to
  `git pull` inside the editable clone + `myco immune` to verify
  no drift.
- Legacy `myco-install <client>` form kept working via a
  first-arg-is-a-known-client sniff that routes to
  `host <client>`.

### Break from v0.5.1

None for substrate readers. `_canon.yaml` emitted by v0.5.1 parses
under v0.5.2 unchanged. No verb signatures changed. No manifest
edits needed in downstream substrates. Only user-facing doc and
the `myco-install` CLI's subcommand shape moved.

---

## v0.5.1 — 2026-04-17 — 永恒进化 delivered in code (MAJOR 6–10)

*(The v0.5.0 wheel filename was burned on PyPI prior to first
successful upload; v0.5.1 is the first released wheel carrying
this contract. Semantic content is identical to the v0.5.0 plan.)*


Closes all five MAJOR gaps from the v0.4.1 post-release audit
(`docs/primordia/v0_4_1_audit_craft_2026-04-15.md`). The README's
"the substrate changes shape with the work" and "you never migrate
again" claims are now backed by mechanisms, not aspirational prose.

### Contract surface at v0.5.0

- **R1–R7** unchanged from v0.4.x.
- **Exit-code grammar** unchanged.
- **Five subsystems** unchanged (genesis / ingestion / digestion /
  circulation / homeostasis), joined by a cross-cutting `meta/`
  package (not a subsystem; houses `session-end`, `craft`, `bump`,
  `evolve`, `scaffold`).
- **Sixteen verbs** (was twelve): the v0.4 set plus `craft`, `bump`,
  `evolve`, `scaffold`. `immune` gained `--list` and `--explain`.
- **Nine lint dimensions** (was eight): `MF1` added
  (mechanical / HIGH — declared subsystems exist on disk).

### Break from v0.4.x

This is **not** a backward-incompatible release for substrate
readers. Every v0.4.x `_canon.yaml` parses under v0.5 unchanged; the
forward-compat seam means a future v0.6-schema canon will also parse
(with a warning) under a v0.5 kernel. The one user-visible code
change: `session-end`'s manifest handler string moved from
`myco.meta:session_end_run` to `myco.meta.session_end:run` when the
single-file `meta.py` module was promoted to a package. The
`from myco.meta import session_end_run` re-export is preserved in
`meta/__init__.py` for any out-of-tree caller that pinned the old
import path.

### New mechanisms

- **MAJOR 6 — Dimension registration via entry-points.**
  `[project.entry-points."myco.dimensions"]` in `pyproject.toml` is
  now the source of truth for built-in dimensions; the hardcoded
  `ALL` tuple (renamed `_BUILT_IN`) is a dev-checkout fallback
  only. Third-party substrates register their own dimensions by
  declaring the same entry-points group in their own `pyproject.toml`
  — no fork of Myco required. `myco immune --list` and
  `myco immune --explain <dim>` surface the registry catalog.
- **MAJOR 7 — Subsystem/package cross-check.** The `MF1` dimension
  validates every `canon.subsystems.<name>.package` resolves to an
  existing directory under substrate root. `tests/test_scaffold.py`
  switched from a hardcoded `PACKAGES` list to
  `pkgutil.walk_packages` — adding a subsystem no longer forces a
  test edit.
- **MAJOR 8 — Forward-compatible canon reader.** An unknown
  `schema_version` in `_canon.yaml` now emits a `UserWarning`
  instead of raising `CanonSchemaError`. A new module-level
  `schema_upgraders: dict[str, Callable]` registry in
  `myco.core.canon` is the seam for future v1→v2 in-code upgraders;
  empty at v0.5, populated when schema v2 lands.
- **MAJOR 9 — Governance as verbs.** `craft / bump / evolve` became
  real agent-callable verbs:
  - `myco craft <topic>` authors a dated three-round primordia doc
    from a template.
  - `myco bump --contract <v>` is the first code path in Myco that
    mutates a post-genesis `_canon.yaml`; line-patches
    `contract_version` and `synced_contract_version`, re-validates
    via `load_canon`, appends a section to this changelog.
  - `myco evolve --proposal <path>` runs shape gates on a craft or
    proposal doc (frontmatter type, title, body size, round-marker
    count, per-round floor).
- **MAJOR 10 — Handler auto-scaffolding.**
  `myco scaffold --verb <name>` generates a stub handler file at
  the filesystem path derived from the manifest's `handler:`
  string. The stub returns a well-formed `Result` with
  `payload.stub = True` and emits a `DeprecationWarning` on every
  invocation, so unfinished verbs are neither crashes nor silent
  successes.

### Doctrine updates

- `docs/architecture/L1_CONTRACT/canon_schema.md` rule 4 — permissive
  schema-version language (warn + upgraders chain).
- `docs/architecture/L2_DOCTRINE/homeostasis.md` — entry-points-driven
  registration, `MF1` in the inventory, `--list` / `--explain`
  surface documented.
- `docs/architecture/L3_IMPLEMENTATION/command_manifest.md` —
  governance-verbs section added, inventory table updated.
- `docs/architecture/L3_IMPLEMENTATION/package_map.md` — `meta/` as a
  package (was single-file `meta.py`).

---

## v0.4.0 — 2026-04-15 — Greenfield rewrite

First entry in the post-rewrite lineage. Resets `waves.current` to
`1` per the directive recorded in
`docs/architecture/L3_IMPLEMENTATION/migration_strategy.md` §9 E5.

### Contract surface at v0.4.0

- **R1–R7** as defined in `docs/architecture/L1_CONTRACT/protocol.md`.
- **Exit-code grammar** as defined in
  `docs/architecture/L1_CONTRACT/exit_codes.md`.
- **Five subsystems** as defined in
  `docs/architecture/L2_DOCTRINE/` (genesis, ingestion, digestion,
  circulation, homeostasis).
- **Twelve verbs** as defined in `src/myco/surface/manifest.yaml`
  (genesis, hunger, eat, sense, forage, reflect, digest, distill,
  perfuse, propagate, immune, session-end).
- **Eight lint dimensions** authored fresh (not ported from the v0.3
  30-dim table):
  - Mechanical: M1 (canon identity), M2 (entry-point exists),
    M3 (write-surface declared).
  - Shipped: SH1 (package-version ref resolves).
  - Metabolic: MB1 (raw-notes backlog), MB2 (no integrated yet).
  - Semantic: SE1 (dangling refs), SE2 (orphan integrated).

### Break from v0.3.x

This is **not** an in-place upgrade from any v0.3.x contract. The
pre-rewrite codebase is preserved at tag `v0.3.4-final`; consumers
(e.g. ASCC) remain pinned there until they migrate through the fresh
re-export path (`scripts/migrate_ascc_substrate.py`, landing in Stage
C.3). No v0.3.x contract version is honored by the v0.4.0 kernel.

### Version-line monotonicity reset

Pre-rewrite tags exhibited non-monotone versioning
(`v0.46.0 → v0.6.0 → v0.45.0`, per the audit recorded in L1
`versioning.md`). The `v0.4.0` release begins a clean, strictly
increasing sequence. Future bumps follow SemVer.
