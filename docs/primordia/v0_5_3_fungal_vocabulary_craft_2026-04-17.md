---
type: craft
topic: v0.5.3 fungal vocabulary + Agent-First framing + substrate-local plugins
slug: v0_5_3_fungal_vocabulary
kind: design
date: 2026-04-17
rounds: 3
craft_protocol_version: 1
status: COMPILED
---

# v0.5.3 — Fungal Vocabulary, Agent-First Framing, and Substrate-Local Plugins Craft

> **Date**: 2026-04-17.
> **Layer**: L2 (vocabulary — subsystem/verb names) + L3 (manifest
> surface + package layout) + L4 (install model + docs). **Not** a
> contract break: old verb names remain available via deprecation
> aliases for the entire 0.x line; they go away at v1.0.0.
> **Upward**: L0 principle 1 (只为 Agent), principle 3 (永恒进化),
> principle 4 (永恒迭代), principle 5 (万物互联); L1 R1-R7 unchanged.
> **Governs**: `src/myco/surface/manifest.yaml`, every handler module
> that is renamed, the trilingual READMEs, every L2/L3 doctrine doc,
> `CHANGELOG.md`, `docs/contract_changelog.md`, `docs/INSTALL.md`,
> `hooks/hooks.json`, `.claude/settings.local.json`, the new
> `.myco/plugins/` substrate-local extension path.

---

## Round 1 — 主张 (claim)

v0.5.2 audited v0.4.1's "stable kernel" slip. v0.5.3 audits two
deeper slips that surfaced immediately after:

1. **Fungal vocabulary drift.** Six verbs (`genesis`, `craft`,
   `bump`, `evolve`, `scaffold`, `session-end`) and three edge-case
   ones (`reflect`, `distill`, `perfuse`) are theological /
   artisanal / mechanical / construction / cognitive / chemical —
   not fungal-bionic, despite the project being named **Myco**
   (fungus). A project whose entire identity rests on a biological
   metaphor cannot carry six construction-era verbs without that
   metaphor turning decorative. v0.5.3 migrates every verb to a
   fungal term whose biology actually matches the verb's
   semantics.
2. **Agent-First framing slip.** Internal rhetoric (READMEs, my
   own pitches in prior turns) regularly says "when you run
   `myco X`" / "the user runs X". L0 principle 1 (只为 Agent)
   says: humans speak natural language, the Agent invokes verbs.
   Verb-invoking sentences must name the Agent as the subject.
   Every such slip is rewritten.

Plus a merged scope item from the prior v0.5.3/v0.5.4 split:

3. **Substrate-local plugin loading.** v0.5 plugin discovery
   works only via PyPI-published entry-points. For a *downstream*
   substrate (what the Agent creates via `myco germinate --project-
   dir ~/proj`), there is no way to register a project-specific
   lint dimension / ingestion adapter / schema upgrader / local
   verb without forking Myco or publishing a package. A
   `.myco/plugins/` directory on each substrate plus a
   `.myco/manifest_overlay.yaml` merged into `load_manifest()`
   closes this gap end-to-end.

Single release (v0.5.3), three concerns, one coherent message:
**Myco is a fungus from the inside. The Agent germinates it,
fruits it, molts it, winnows it, ramifies it, senesces it,
assimilates and sporulates from it, and grafts onto it — the
vocabulary matches what actually happens in mycology.**

### Rename table (canonical)

| Current | New | Biology rationale |
|---|---|---|
| `genesis` | `germinate` | Spore germination begins a new colony |
| `craft` | `fruit` | Fruiting body produces visible reproductive structure (3-round doc is the reproductive content) |
| `bump` | `molt` | Sheds an old form for a new stage — fits contract-version transition |
| `evolve` | `winnow` | Selection pressure separates viable from unviable (proposal shape validation) |
| `scaffold` | `ramify` | Hyphae ramify — branch out — into new territory |
| `session-end` | `senesce` | Aging into dormancy: run reflect + immune --fix before sleep |
| `reflect` | `assimilate` | Assimilation of absorbed nutrients into the organism (raw → integrated) |
| `distill` | `sporulate` | Concentrating accumulated resources into dispersible spores (synthesis) |
| `perfuse` | `traverse` | Walking the mycelium network to check anastomotic integrity (graph health) |

Subsystems:

| Current | New | Rationale |
|---|---|---|
| `genesis/` | `germination/` | Matches the verb name |
| `meta/` | `cycle/` | Life cycle — all the composer verbs (germinate/fruit/molt/winnow/ramify/senesce/graft) fit under "life cycle events" |

New verb for substrate-local extensions:

- **`myco graft --list/--validate/--explain [--name <x>]`** — enumerate / validate / describe substrate-local plugins. Biology: grafting is hyphal anastomosis (mycelium fusing with substrate-specific content).

New flags on existing `ramify`:

- **`myco ramify --verb <name>`** (was `scaffold --verb`, unchanged semantics)
- **`myco ramify --dimension <id> --category <cat> --severity <sev>`** (new) — scaffold a local Dimension subclass
- **`myco ramify --adapter <name> --extensions <ext,ext>`** (new) — scaffold a local Adapter subclass
- **`myco ramify --substrate-local`** defaults ON when the substrate isn't Myco-self (no `src/myco/` + substrate_id ≠ "myco-self")

## Round 1.5 — 自我反驳 (self-rebuttal)

- **T1**: renaming nine verbs at once is a huge churn. Every doc,
  every test, every example in README, every hook config, every
  MCP tool name. Agents with cached v0.5.2 invocations break.
- **T2**: `sporulate`, `assimilate`, `winnow`, `ramify`, `senesce`
  are less googlable than `distill`, `reflect`, `evolve`,
  `scaffold`, `session-end`. A new user reading the help text
  will have to learn biology vocab before the tool makes sense.
- **T3**: `perfuse` → `traverse` is actually a less specific
  word. Perfusion carries the connotation of fluid distribution;
  traverse just means "walk". The rename narrows the metaphor.
- **T4**: `molt` for contract version bumping is a stretch —
  molting is typically animal/arthropod, not fungal. Fungi have
  hyphal maturation but no "molt" per se.
- **T5**: backward compat via aliases is extra code. The
  manifest has to carry `aliases:` on every command; CLI has to
  resolve the canonical form with a DeprecationWarning; MCP tool
  registration has to emit both the canonical and aliased tool
  names so existing MCP clients don't break. Test burden grows.
- **T6**: `graft` for "substrate-local plugins" is a stretch of
  its own. Grafting is horticultural; fungal anastomosis is a
  closer match but "anastomosis" is a bad verb. "graft" is a
  compromise.
- **T7**: the `meta/` → `cycle/` package rename is not a clean
  semantic improvement. "meta" at least says "cross-cutting";
  "cycle" overclaims — not every verb in there is a life-cycle
  event.
- **T8**: v0.5.2 just shipped. Users who just `pipx run
  myco-install fresh` saw a README and learned a vocabulary.
  Renaming it 48 hours later is disrespectful to their recent
  onboarding.
- **T9**: primordia history (`docs/primordia/*.md`) uses the old
  verb names throughout. Leaving them unmodified (as audit
  records) means docs mix old and new vocab indefinitely.
- **T10**: substrate-local plugin loading adds a magical
  import-at-substrate-load path. That is implicit behavior — the
  Agent might not realize a `.myco/plugins/__init__.py` is being
  executed. Magic = bugs.
- **T11**: `myco graft` is a **plugins-oriented** verb. Fungal
  or not, is it an introspection verb (list / validate / explain)
  or an authoring verb (register / unregister / update)? The
  pitch only did introspection; authoring happens via `ramify
  --dimension` et al. Is the split clean?

## Round 2 — 修正 (revision)

- **R1** (addresses T1, T5, T8): backward-compat aliases are
  mandatory, not optional. Every old verb name remains invokable
  across v0.5.x and v0.6.x — with a DeprecationWarning. MCP tool
  names keep old `myco_X` and ADD new `myco_Y` both resolving to
  the same handler. A migration cheat sheet lives prominently in
  the v0.5.3 CHANGELOG + README. Alias removal is scheduled for
  v1.0.0 only, giving the 0.x tail full backward compatibility.
- **R2** (addresses T2): Myco's L0 is biology from day one. A
  learning curve of five new vocabulary items is part of the
  onboarding cost and is justified by the identity the project
  wants to project. The `myco <verb> --help` + `myco graft
  --explain <old_name>` (new alias lookup) cover the discovery
  path — the old name is still documented as "deprecated alias
  for <new_name>".
- **R3** (addresses T3): `traverse` is chosen because the action
  is graph walking (not circulation of content). If the subsystem
  metaphor (`circulation`) still carries the "fluids move" frame,
  the VERB doesn't need to — different layer, different noun. Kept.
- **R4** (addresses T4): fungi do have hyphal differentiation
  events (septation, sporophore maturation). `molt` is the
  closest English verb. Alternatives considered: `mature`,
  `differentiate`, `septate`. `molt` is punchier and conveys
  "loses old form for new" which is exactly what contract_version
  bumping does. Kept.
- **R5** (addresses T5): the alias mechanism is **one place**:
  `CommandSpec.aliases: tuple[str, ...]` plus `Manifest.by_name()`
  consulting aliases. CLI and MCP both derive their surfaces
  from the manifest; both pick up aliases for free. Total new
  Python: ~30 LoC. Deprecation warning fires once per process
  per aliased verb (cached flag).
- **R6** (addresses T6): `graft` is the best English verb for
  "attach locally-authored content to the mycelium". Alternatives
  (`anastomose`, `fuse`, `hyphal-extend`) are either bad as CLI
  verbs or too specialized. `graft` sits at a similar abstraction
  level to `ramify` (branch out — the mycelium grows) and pairs
  well in docstrings ("`ramify` creates; `graft` enumerates").
- **R7** (addresses T7): `cycle` is chosen because every verb
  currently under `meta/` really IS a life-cycle event:
  - `germinate` starts the cycle
  - `fruit` produces doctrine proposals
  - `molt` advances the cycle to a new contract stage
  - `winnow` selects which proposals enter the canon
  - `ramify` grows into new territory (new verbs/dimensions/adapters)
  - `senesce` closes the active session (sleep)
  - `graft` attaches locally-authored code to the cycle
  The one semi-exception (`senesce` also runs `immune --fix`) is
  still a cycle event — it's the preparation-for-sleep step.
  Kept.
- **R8** (addresses T9): primordia docs stay unmodified.
  `v0_5_3_fungal_vocabulary_craft_2026-04-17.md` (THIS doc) is
  the record that the vocabulary changed. Earlier craft records
  are read as "what was true at the time"; they don't need
  retroactive rewrites, and retroactive rewrites would destroy
  the audit history.
- **R9** (addresses T10): substrate-local plugin loading is
  loud, not magical. Every time `Substrate.load()` auto-imports
  `.myco/plugins/`, the `hunger` report includes a
  `local_plugins: {count, health}` summary so the Agent sees what
  was loaded. The new `MF2` lint dimension fires on any import
  errors or broken registrations. `myco graft --list` enumerates
  every registered local extension by source file and
  registration kind.
- **R10** (addresses T11): `graft` is strictly introspection +
  validation (`--list`, `--validate`, `--explain`). Authoring
  happens via `ramify --dimension`, `--adapter`, `--verb` (plus
  `--substrate-local` flag or its smart default). Clean split:
  `ramify` is the branch-out creator; `graft` is the mycelial
  observer of what has grafted on.

## Round 2.5 — 再驳 (counter-rebuttal)

- **T12**: if backward-compat aliases carry a DeprecationWarning,
  every existing test that invokes `myco_X` (old MCP names) would
  trigger the warning noise. Fix: `filterwarnings` in pytest for
  the deprecation category during tests OR emit warnings only at
  CLI/MCP entry, not at dispatcher.
- **T13**: renaming `src/myco/meta/` → `src/myco/cycle/` breaks
  the `from myco.meta import session_end_run` backward-compat
  re-export that v0.5 explicitly promised. Fix: keep
  `src/myco/meta/__init__.py` as a shim package that re-exports
  from `myco.cycle.*` + emits a DeprecationWarning. External
  callers never see a broken import.
- **T14**: `graft` as a new top-level verb plus `ramify
  --dimension/--adapter/--verb` IS a lot of new surface for one
  release. Can we defer `graft --validate` and `graft --explain`
  to v0.5.4? **No** — they're three subactions of one verb
  (same manifest entry, three flags); complexity is already
  bounded.
- **T15**: the substrate-local `.myco/manifest_overlay.yaml`
  merging into `load_manifest()` interacts with the `@lru_cache`
  on `load_manifest`. If the substrate changes, the cached
  manifest is stale. Fix: `load_manifest()` accepts an optional
  `substrate_root` param; the cache key becomes (substrate_root
  or None). Or: invalidate the cache in `build_context()` right
  before each dispatch.

## Round 3 — 反思 (reflection and decision)

All tensions resolved. v0.5.3 ships the full merged scope:

1. **Rename mechanism**: `CommandSpec.aliases: tuple[str, ...]`.
   `Manifest.by_name()` consults canonical + aliases. CLI/MCP
   surfaces expose both. A single DeprecationWarning fires per
   aliased verb per process.

2. **Nine verb renames**, with aliases:
   - `genesis` → `germinate`
   - `craft` → `fruit`
   - `bump` → `molt`
   - `evolve` → `winnow`
   - `scaffold` → `ramify`
   - `session-end` → `senesce`
   - `reflect` → `assimilate`
   - `distill` → `sporulate`
   - `perfuse` → `traverse`

3. **Two package renames**:
   - `src/myco/genesis/` → `src/myco/germination/` (shim kept
     at old path for one-release deprecation window — actually
     no; genesis is a public package in pyproject and renaming
     it is a breaking-adjacent event; keeping shim)
   - `src/myco/meta/` → `src/myco/cycle/` (shim kept at old path
     re-exporting session_end_run + emitting DeprecationWarning)

4. **Handler file renames** inside those packages (as in the
   rename table above).

5. **Substrate-local plugin loading**:
   - `Substrate.load()` adds `<root>/.myco/` to `sys.path` if
     `.myco/plugins/__init__.py` exists, then imports
     `plugins` to trigger registration side effects.
   - `Manifest` gains overlay support: if
     `<root>/.myco/manifest_overlay.yaml` exists, it is merged
     at `build_context()` time (not at `load_manifest()` time —
     the manifest cache is kept clean).
   - `MF2` dimension (mechanical/HIGH) fires on broken
     `.myco/plugins/` shape, missing `__init__.py`, manifest_
     overlay YAML errors, or duplicate verb names across the
     overlay and the packaged manifest.

6. **`myco graft` verb** (new; introspection only):
   - `--list` → payload with every loaded local plugin (kind,
     name, source path)
   - `--validate` → re-run the import + registration gate,
     report any errors in payload
   - `--explain <name>` → source file + class docstring for a
     specific local plugin

7. **`myco ramify` verb** extensions:
   - `--verb <name>` (unchanged)
   - `--dimension <id> --category <cat> --severity <sev>` (new)
   - `--adapter <name> --extensions <ext,ext>` (new)
   - `--substrate-local` flag; defaults ON when
     `canon.identity.substrate_id != "myco-self"` OR
     `<substrate_root>/src/myco/` does not exist

8. **`hunger` payload** includes `local_plugins: {count, health}`
   so the Agent immediately sees what has grafted onto this
   substrate.

9. **Agent-First framing fix**: every README sentence that
   invokes a verb is rewritten so the Agent is the subject.
   "You run `myco X`" → "the Agent runs `myco X` after you say
   X in natural language". Not pedantic — load-bearing.

10. **Trilingual READMEs, INSTALL.md, L2/L3 doctrine, hooks
    configs, canon template, self-canon** all updated with new
    vocabulary. Primordia docs unmodified (historical records).

11. **Contract changelog v0.5.3 entry** records the vocabulary
    migration + substrate-local plugin surface as a non-breaking
    contract refinement (aliases preserve every prior
    invocation).

### What this craft revealed

1. The v0.4.1 "stable kernel" slip and the v0.5.0 "user runs"
   slips and the construction-era verb slips all have the same
   shape: they accepted the default framing of Python packaging /
   CLI tools / construction software vocabulary without
   interrogating whether the framing matches Myco's L0 identity.
   Every such default must be held up against L0 principles 1 /
   3 / 4 / 5 before it's adopted.
2. The biggest surprise was that `reflect`, `distill`, `perfuse`
   — which I had classified as "edge cases, maybe keep" — are
   actually the clearest fungal mis-matches once you look at
   what the verbs DO. `reflect` is doing assimilation (uptake
   into the organism proper), not cognitive reflection.
   `distill` is doing sporulation (concentrating accumulated
   resources into dispersible units), not alchemical distilling.
   `perfuse` is walking a graph, not distributing fluid. All
   three deserve the rename.
3. `graft` as "substrate-local plugins" is the single coinage
   with the weakest biological support. We keep it because the
   alternative (retaining "plugins" as a CS-generic term) is
   worse for Myco's identity. The cost is documentable.
4. Substrate-local plugin loading, delayed to v0.5.4 in the
   original plan, is folded into v0.5.3 specifically because the
   rename release is the right place to land the new verb
   (`graft`) and the new flags (`ramify --dimension/--adapter`).
   Shipping them in two separate releases 48 hours apart would
   be process theater.

## Deliverables

- `src/myco/surface/manifest.py` — `CommandSpec.aliases: tuple[str, ...]`.
- `src/myco/surface/manifest.yaml` — 9 renames + aliases + new
  verb `graft` + new flags on `ramify`.
- `src/myco/surface/cli.py` — alias resolution with DeprecationWarning.
- `src/myco/surface/mcp.py` — register both canonical and aliased MCP tools.
- `src/myco/core/substrate.py` — `.myco/plugins/` auto-import + sys.path.
- `src/myco/core/paths.py` — `SubstratePaths.local_plugins` / `manifest_overlay`.
- `src/myco/homeostasis/dimensions/mf2_substrate_local_plugin_health.py` — new dim.
- `src/myco/homeostasis/dimensions/__init__.py` — MF2 registered.
- `src/myco/homeostasis/registry.py` — `register_external_dimension(cls)` public API.
- `src/myco/ingestion/adapters/__init__.py` — expose `register()` as public substrate-local API.
- `src/myco/core/canon.py` — `schema_upgraders` already public; unchanged here.
- `src/myco/cycle/` — new package (was `meta/`).
  - `cycle/__init__.py`
  - `cycle/senesce.py` (was `meta/session_end.py`)
  - `cycle/fruit.py` (was `meta/craft.py`)
  - `cycle/molt.py` (was `meta/bump.py`)
  - `cycle/winnow.py` (was `meta/evolve.py`)
  - `cycle/ramify.py` (was `meta/scaffold.py`, extended)
  - `cycle/graft.py` (new)
  - `cycle/templates/fruit.md.tmpl` (was `meta/templates/craft.md.tmpl`)
- `src/myco/meta/__init__.py` — shim re-exporting from `myco.cycle.*`.
- `src/myco/germination/` — new package (was `genesis/`).
  - `germination/__init__.py`
  - `germination/germinate.py` (was `genesis/genesis.py`)
  - `germination/templates/` moved intact.
- `src/myco/genesis/__init__.py` — shim re-exporting from `myco.germination.*`.
- `src/myco/digestion/assimilate.py` (was `reflect.py`).
- `src/myco/digestion/sporulate.py` (was `distill.py`).
- `src/myco/circulation/traverse.py` (was `perfuse.py`).
- `src/myco/ingestion/hunger.py` — `local_plugins` block in payload.
- `pyproject.toml` — entry_points for MF2; console scripts unchanged.
- `_canon.yaml` — `contract_version: v0.5.3`, `subsystems.germination`
  (renamed from `genesis`), `lint.dimensions.MF2`.
- `src/myco/genesis/templates/canon.yaml.tmpl` → moved to
  `src/myco/germination/templates/canon.yaml.tmpl` with
  subsystems using new names.
- Trilingual READMEs (en/zh/ja) — full rewrite: new verb table,
  Agent-First framing, fungal vocab, editable-first preserved
  from v0.5.2, 16+1 verbs (graft) = 17 total.
- `docs/INSTALL.md` — verb references updated.
- `docs/architecture/L2_DOCTRINE/*.md` — verb references updated.
- `docs/architecture/L3_IMPLEMENTATION/command_manifest.md` — new
  verb table (17 verbs, aliases shown in a dedicated column).
- `docs/architecture/L3_IMPLEMENTATION/package_map.md` — `cycle/`
  + `germination/` + note about shim packages.
- `docs/contract_changelog.md` — v0.5.3 section.
- `CHANGELOG.md` — v0.5.3 section with migration cheat sheet.
- `docs/primordia/v0_5_3_fungal_vocabulary_craft_2026-04-17.md`
  (THIS file).
- `hooks/hooks.json` + `.claude/settings.local.json` — `senesce`
  canonical (legacy `session-end` alias still works).
- `.claude-plugin/plugin.json` — version 0.5.3 + description
  updated.
- Tests:
  - `tests/unit/surface/test_aliases.py` — alias resolution +
    DeprecationWarning.
  - `tests/unit/core/test_substrate_plugins.py` — .myco/plugins/
    auto-import + sys.path + MF2.
  - `tests/unit/surface/test_manifest_overlay.py` — overlay
    merging.
  - `tests/unit/cycle/test_graft.py` — graft verb.
  - `tests/unit/cycle/test_ramify_dimension.py` +
    `test_ramify_adapter.py` — new ramify flags.
  - Every existing test file updated for new module names.

## Acceptance

- **pytest**: full suite green; new tests cover graft, ramify
  extensions, substrate-local plugins, alias resolution, MF2.
- **behavioral**:
  - `myco germinate --project-dir ~/p --substrate-id p` works
    (new canonical name).
  - `myco genesis --project-dir ~/p --substrate-id p` still
    works with a DeprecationWarning on stderr.
  - `myco immune --list` shows MF1 + MF2 (9 → 10 dims).
  - `myco ramify --dimension LOCAL1 --category mechanical
    --severity medium` in a downstream substrate creates
    `.myco/plugins/dimensions/local1.py`.
  - `myco graft --list` enumerates what got registered.
  - `myco winnow --proposal docs/primordia/v0_5_3_fungal_
    vocabulary_craft_2026-04-17.md` (THIS doc) returns
    `verdict: pass`.
- **non-regression**:
  - Every v0.5.2 verb invocation still works (alias path).
  - MCP tool names `myco_genesis`, `myco_craft`, etc. still
    exist; new canonical `myco_germinate`, `myco_fruit`, etc.
    also exist.
  - `from myco.meta import session_end_run` still imports (via
    shim) with DeprecationWarning.
  - `_canon.yaml` emitted by v0.5.2 (schema_version: "1",
    contract_version: "v0.5.2") still parses under v0.5.3.
