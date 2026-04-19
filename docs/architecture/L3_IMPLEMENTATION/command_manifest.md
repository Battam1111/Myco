# L3 — Command Manifest

> **Status**: APPROVED (2026-04-15, greenfield rewrite §9).
> **Layer**: L3. Subordinate to L0/L1/L2.
> **Mandate**: every verb the outside world can invoke is defined **once**
> in the manifest and surfaced through BOTH CLI and MCP with zero
> duplication. Divergence between CLI and MCP is an immune error.

---

## Why this exists

The pre-rewrite substrate defined each command twice: once in
`mcp_server.py` as an MCP tool, and once in `__main__.py` as a CLI
subparser. They drifted. Exit-code semantics differed. Flag names
differed. Documentation drift was inevitable.

The manifest is one YAML file read by both `surface/cli.py` and
`surface/mcp.py`. Adding or changing a verb touches one place.

## Location

`src/myco/surface/manifest.yaml` (packaged with the wheel; referenced by
canon as `commands.manifest_ref`).

## Schema

```yaml
# src/myco/surface/manifest.yaml
schema_version: "1"

commands:
  - name: "hunger"
    subsystem: "ingestion"
    handler: "myco.ingestion.hunger:run"
    summary: "Report substrate hunger and optionally patch entry-point."
    cli_aliases: []
    mcp_tool: "myco_hunger"
    args:
      - name: "execute"
        type: "bool"
        default: false
        help: "Also write boot brief and patch entry-point signals."
      - name: "json"
        type: "bool"
        default: false
        help: "Emit JSON instead of human-readable text."
      - name: "project-dir"
        type: "path"
        default: null
        help: "Override auto-detected project root."
    exit_policy: "inherits"    # uses L1 exit-code ladder
    returns: "hunger_report"   # schema in manifest:returns below

  - name: "eat"
    subsystem: "ingestion"
    handler: "myco.ingestion.eat:run"
    summary: "Capture a raw note."
    mcp_tool: "myco_eat"
    args:
      - name: "content"
        type: "str"
        required: true
      - name: "tags"
        type: "list[str]"
        default: []
      - name: "source"
        type: "str"
        default: "agent"

  # … sense, forage, assimilate, digest, sporulate,
  #    traverse, propagate, immune, germinate, senesce,
  #    fruit, molt, winnow, ramify, graft
  # (v0.5.2 aliases — reflect, distill, perfuse, genesis,
  #  session-end, craft, bump, evolve, scaffold — remain
  #  registered as cli_aliases + mcp_tool_aliases entries.)

returns:
  hunger_report:
    kind: "object"
    fields:
      contract_drift: "bool"
      raw_backlog: "int"
      reflex_signals: "list[str]"
      # …
  # other return schemas
```

## Invariants

1. **One handler per command.** `handler:` points at exactly one
   `module:function` address. No conditionals based on caller (CLI vs
   MCP).
2. **Shared arg schema.** CLI flags and MCP tool parameters derive from
   the same `args:` list. Type coercion lives in `surface/manifest.py`.
3. **Same exit policy.** Commands either `inherits` (default — L1 ladder)
   or declare their own category mapping. CLI exit code and MCP
   structured-result `status` come from the same computation.
4. **MCP tool name is explicit.** `mcp_tool:` is the canonical MCP name
   (currently `myco_<verb>`, but the manifest is the authority).
5. **Handler signature is fixed.**
   ```python
   def run(args: dict, *, ctx: MycoContext) -> Result:
       ...
   ```
   `args` is the parsed/validated dict. `ctx` carries project root,
   canon, and severity computer. `Result` is a dataclass with a
   `returns`-key matching the manifest's `returns:` schema.

## Generated surfaces

### CLI

`surface/cli.py` reads the manifest and builds an `argparse` tree. A
subcommand's help text comes from `summary` + per-arg `help` entries.
Exit code comes from the handler's `Result.exit_code()` per L1 ladder.

### MCP

`surface/mcp.py` reads the manifest and registers MCP tools using the
MCP SDK. Tool description comes from `summary`. Input schema comes from
`args`. Output schema comes from the `returns:` section.

## Immune check

A homeostasis dimension — "command surface parity" — verifies on every
lint run:

- Every `commands[*].handler` resolves to an importable callable.
- Every handler's actual signature matches `(args, *, ctx) -> Result`.
- No orphan commands in `src/myco/` that aren't in the manifest.
- No orphan entries in the manifest pointing at non-existent handlers.
- CLI subcommand set == MCP tool set (no divergence).

## Verb inventory (v0.5.7)

v0.4.0 shipped twelve verbs. v0.5.1 added four governance verbs
(MAJOR 9 and 10) to reach sixteen. v0.5.3 **renamed nine** existing
verbs to canonical fungal-bionic names (old names kept as
deprecated aliases throughout 0.x) and **added one** new verb
(`graft`), reaching seventeen. v0.5.5 added `brief` — the one
carved human-facing exception to L0 principle 1. Current total:
**eighteen verbs** (17 agent + 1 human).

At v0.5.6 the dimension roster that polices the manifest gained
**MP1** (mechanical/HIGH — "no LLM-provider import from inside
`src/myco/**` unless `canon.system.no_llm_in_substrate: false`").
MP1 is the mechanical guard behind the "Agent calls LLM; substrate
does not" invariant. See `L2_DOCTRINE/homeostasis.md` for the
dimension enumeration.

At v0.5.7 the `senesce` verb gains a `--quick` bool arg (default
false). Quick mode runs `assimilate` only; skips `immune --fix`.
Bound to the Claude Code `SessionEnd` hook (~1.5 s kill budget).
Full mode (no `--quick`) is unchanged and remains bound to
`PreCompact` (blocking). See
`docs/primordia/v0_5_7_senesce_quick_mode_craft_2026-04-19.md`.

| Subsystem | Verb | Alias (deprecated) | Handler |
|---|---|---|---|
| Germination | `germinate` | `genesis` | `myco.germination.germinate:run_cli` |
| Ingestion | `hunger` |  | `myco.ingestion.hunger:run` |
| Ingestion | `eat` |  | `myco.ingestion.eat:run` |
| Ingestion | `sense` |  | `myco.ingestion.sense:run` |
| Ingestion | `forage` |  | `myco.ingestion.forage:run` |
| Digestion | `assimilate` | `reflect` | `myco.digestion.assimilate:run` |
| Digestion | `digest` |  | `myco.digestion.digest:run` |
| Digestion | `sporulate` | `distill` | `myco.digestion.sporulate:run` |
| Circulation | `traverse` | `perfuse` | `myco.circulation.traverse:run` |
| Circulation | `propagate` |  | `myco.circulation.propagate:run` |
| Homeostasis | `immune` |  | `myco.homeostasis.kernel:run_cli` |
| Cycle | `senesce` | `session-end` | `myco.cycle.senesce:run` |
| Cycle | `fruit` | `craft` | `myco.cycle.fruit:run` |
| Cycle | `molt` | `bump` | `myco.cycle.molt:run` |
| Cycle | `winnow` | `evolve` | `myco.cycle.winnow:run` |
| Cycle | `ramify` | `scaffold` | `myco.cycle.ramify:run` |
| Cycle | `graft` |  | `myco.cycle.graft:run` |
| Cycle | `brief` |  | `myco.cycle.brief:run` |

The `cycle/` package (renamed from `meta/` at v0.5.3; shim package
preserves `from myco.meta import session_end_run`) houses every
life-cycle composer: the germinate / fruit / molt / winnow / ramify
/ senesce / graft / brief group. Each governance verb is its own
submodule.

### Alias mechanism

`CommandSpec.aliases: tuple[str, ...]` plus
`CommandSpec.mcp_tool_aliases: tuple[str, ...]` encode the backward-
compat surface in the manifest. `Manifest.by_name()` consults both
canonical and alias lists. CLI and MCP both surface each alias as
its own invocation path; invoking an alias fires a single
`DeprecationWarning` per alias per process. Alias removal is
scheduled for **v1.0.0** only — the entire 0.x line stays backward-
compatible.

## Governance verbs (Cycle subsystem)

Governance verbs let the agent perform contract-level changes that
were previously Markdown-social conventions or hand-edits:

- **`myco fruit --topic <phrase>`** (alias: `craft`) — fruit a
  dated primordia doc under `docs/primordia/<slug>_craft_<date>.md`
  from the three-round template. Biology: the fruiting body is the
  reproductive structure; a primordia doc is Myco's reproductive
  content. Does not enforce that all three rounds get filled in;
  that is the agent's job, and the `myco winnow` verb validates the
  shape after authoring.
- **`myco molt --contract <v>`** (alias: `bump`) — shed the old
  contract version for a new one. Line-patches `contract_version`
  and `synced_contract_version`, re-reads via `load_canon` to verify
  the result still parses, then prepends a new section to
  `docs/contract_changelog.md`. Restores the original canon text on
  any post-write parse error. Biology: molting is shedding an old
  form for a new stage.
- **`myco winnow --proposal <path>`** (alias: `evolve`) — selection
  pressure applied to a craft doc. Runs six gates (frontmatter
  type, title, body size bounds, round-marker count, per-round body
  floor, and `G6_template_boilerplate` — which rejects an unedited
  three-round skeleton emitted by `myco fruit` when the author has
  not yet filled it in; added at v0.5.4) and returns either
  `exit 0 + verdict: pass` or `exit 1 + violations`. Does not
  mutate anything; lint-style read.
- **`myco ramify --verb <name>`** (alias: `scaffold`) — auto-
  generate a handler stub for a verb that is already in the
  manifest but has no Python module. Biology: hyphae ramify
  (branch out) into new territory. Extended at v0.5.3 with
  `--dimension <id> --category <cat> --severity <sev>` (scaffold a
  lint dimension), `--adapter <name> --extensions <ext,ext>`
  (scaffold an ingestion adapter), and `--substrate-local` (write
  under `<substrate>/.myco/plugins/` instead of `src/myco/`; auto-
  on when `canon.identity.substrate_id != "myco-self"` OR
  `<substrate_root>/src/myco/` does not exist).
- **`myco graft --list | --validate | --explain <name>`** (new at
  v0.5.3) — enumerate, validate, or explain substrate-local
  plugins. Biology: hyphal anastomosis is the fusion of foreign
  hyphae onto the mycelial network. Introspection-only; authoring
  happens via `ramify --dimension` / `--adapter` / `--verb` with
  `--substrate-local`.
- **`myco senesce [--quick]`** (alias: `session-end`) — the end-
  of-session composer. Default (full) mode runs `assimilate` then
  `immune --fix`; bound to the PreCompact hook (blocking).
  `--quick` (v0.5.7) runs `assimilate` only; bound to the
  SessionEnd hook (~1.5 s kill). Biology: senescence is aging into
  dormancy before sleep — quick mode is fast-dormancy (close cell
  walls only), full mode is seasonal dormancy (close + prune +
  reinforce).

### Brief — the one carved human-facing exception

At v0.5.5 a single verb was carved out from the
"agent-only-consumption" rule (L0 principle 1):

- **`myco brief`** (no alias) — emit a markdown rollup of the
  substrate's current state, intended for the one human moment
  that is not avoidable: "what has happened since the last session
  I actually paid attention to?". The default output is markdown
  with **7 stable sections**: identity (substrate_id, contract
  version, package version), hunger snapshot, recent notes (raw
  + integrated counts + last-N titles), immune summary (category
  counts), graph health (orphans / dangling refs / one-way),
  governance activity (recent craft / molt / winnow events), and
  open reflex signals. `--format markdown|json` toggles the output
  representation; `markdown` is the default and the design target.

  `brief` **does not replace** any agent-side verb. `hunger`,
  `sense`, `traverse`, and `immune` remain the canonical agent
  consumption surfaces. `brief` is a derived read-only rollup
  that composes fields those verbs already surface; it writes
  nothing and is safe to call at any point. It is the single
  carved exception under L0 principle 1's addendum (see
  `L0_VISION.md` §"Addendum — declared exceptions"). A human who
  reads `brief` still does not become a Myco user — they remain a
  reader of a single scoped rollup produced on demand by the
  agent on their behalf.

  `brief` reads from the hunger payload (via `L2_DOCTRINE/ingestion.md`)
  plus immune findings plus traverse output, composing them into
  markdown; it performs no standalone scan.

`ramify` is what closes the v0.4-era "add a verb means write a
Python file by hand" friction. The intended order is still
**manifest first, handler second** — `ramify` refuses to act on a
kernel verb the manifest does not declare. For substrate-local
verbs, the overlay `<substrate>/.myco/manifest_overlay.yaml`
declares them; `ramify --verb <name> --substrate-local` writes both
the overlay entry and the handler stub.

## Substrate-local plugins (v0.5.3)

A substrate can carry its own dimensions, adapters, schema
upgraders, and verbs without forking Myco:

| Path | Role |
|---|---|
| `<substrate>/.myco/plugins/__init__.py` | Auto-imported on `Substrate.load()`. Registration side effects fire here. |
| `<substrate>/.myco/manifest_overlay.yaml` | Merged into the runtime manifest at `build_context()` time (not at `load_manifest()` — the manifest cache stays clean). |

Introspection is via `myco graft --list | --validate | --explain
<name>`. Authoring is via `myco ramify --dimension | --adapter |
--verb --substrate-local`. The `hunger` payload carries a
`local_plugins: {loaded, count_by_kind: {dimension, adapter,
schema_upgrader, overlay_verb}, errors, module}` block (v0.5.4+
shape) so the agent sees on every boot what has grafted on: whether
`.myco/plugins/__init__.py` imported (`loaded`), how many items
registered per kind (`count_by_kind`), any import-time errors
(`errors`), and the isolated module name (`module`). The `MF2`
lint dimension (mechanical / HIGH) fires on broken plugin shape
or overlay YAML errors.

## Change policy

Adding a verb: craft doc (via `myco fruit`) + contract bump (via
`myco molt`) + manifest entry + handler (via `myco ramify`, then
flesh out) + tests. Removing a verb: deprecation notice for one
minor version, then removal with a fruit + molt cycle. Renaming a
verb: add the new canonical name + keep the old as an alias for one
major-version tail (the v0.5.3 migration is the reference case).
Alias removal happens only at a major-version boundary.
