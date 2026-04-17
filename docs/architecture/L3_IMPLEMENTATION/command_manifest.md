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

  # … sense, forage, reflect, digest, distill,
  #    perfuse, propagate, immune, genesis, session-end

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

## Initial verb inventory

The v0.4.0 manifest included exactly eleven verbs + one meta-composer.
**v0.5 adds four governance verbs** (MAJOR 9 and 10). Current inventory:

| Subsystem | Verbs |
|-----------|-------|
| Genesis | `genesis` |
| Ingestion | `hunger`, `eat`, `sense`, `forage` |
| Digestion | `reflect`, `digest`, `distill` |
| Circulation | `perfuse`, `propagate` |
| Homeostasis | `immune` |
| Meta (package, v0.5+) | `session-end`, `craft`, `bump`, `evolve`, `scaffold` |

The `meta` package (new at v0.5) replaces the single-file `meta.py`
that held only `session_end_run` in v0.4. Each governance verb is its
own submodule under `src/myco/meta/`.

## Governance verbs (v0.5+, MAJOR 9 and 10)

Governance verbs let the agent perform contract-level changes that
were previously Markdown-social conventions or hand-edits:

- **`myco craft <topic>`** — scaffold a dated primordia doc under
  `docs/primordia/<slug>_craft_<date>.md` from the three-round
  template. Does not enforce that all three rounds get filled in;
  that is the agent's job, and the `myco evolve` verb validates the
  shape after authoring.
- **`myco bump --contract <v>`** — the first code path that mutates
  a post-genesis `_canon.yaml`. Line-patches `contract_version` and
  `synced_contract_version`, re-reads via `load_canon` to verify the
  result still parses, then prepends a new section to
  `docs/contract_changelog.md`. Restores the original canon text on
  any post-write parse error.
- **`myco evolve --proposal <path>`** — shape validator for a
  proposal/craft doc. Runs five gates (frontmatter type, title,
  body size bounds, round-marker count, per-round body floor) and
  returns either `exit 0 + verdict: pass` or `exit 1 + violations`.
  Does not mutate anything; this is a lint-style read.
- **`myco scaffold --verb <name>`** — auto-generate a handler stub
  for a verb that is already in the manifest but has no Python
  module. Derives the target filesystem path from the manifest's
  `handler:` string (not the `subsystem:` tag, which is purely
  descriptive). The stub returns an `exit 0` `Result` with
  `payload.stub = True` and emits a `DeprecationWarning` on every
  invocation so unfinished verbs are not silently benign.

`scaffold` is what closes the v0.4-era "add a verb means write a
Python file by hand" friction. The intended order is still
**manifest first, handler second** — `scaffold` refuses to act on a
verb the manifest does not declare.

## Change policy

Adding a verb: craft doc (via `myco craft`) + contract bump (via
`myco bump`) + manifest entry + handler (via `myco scaffold`, then
flesh out) + tests. Removing a verb: deprecation notice for one
minor version, then removal with a craft + contract bump. Renaming a
verb: a removal + an add (no silent rename).
