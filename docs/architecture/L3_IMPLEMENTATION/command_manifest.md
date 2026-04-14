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

The v0.4.0 manifest includes exactly these eleven verbs, grouped by
subsystem:

| Subsystem | Verbs |
|-----------|-------|
| Genesis | `genesis` |
| Ingestion | `hunger`, `eat`, `sense`, `forage` |
| Digestion | `reflect`, `digest`, `distill` |
| Circulation | `perfuse`, `propagate` |
| Homeostasis | `immune` |
| (meta) | `session-end` — orchestrates `reflect` + `immune --fix`; lives in `surface/` |

## Change policy

Adding a verb: craft doc + contract bump + manifest entry + handler +
tests. Removing a verb: deprecation notice for one minor version, then
removal with a craft + contract bump. Renaming a verb: a removal + an
add (no silent rename).
