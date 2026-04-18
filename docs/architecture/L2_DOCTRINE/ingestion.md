# L2 — Ingestion

> **Status**: APPROVED (2026-04-15, greenfield rewrite §9).
> **Layer**: L2. Subordinate to `L0_VISION.md` and `L1_CONTRACT/*`.
> **Upward mapping**: implements L1 R1 (hunger), R3 (sense), R4 (eat).
> **v0.5.3 note**: the four Ingestion verbs (`hunger`, `eat`,
> `sense`, `forage`) kept their names through the fungal-vocabulary
> rename — each is already a biologically accurate term for what the
> verb does.

---

## Responsibility

Ingestion owns the **intake surface** of the substrate. It implements
L0 principle 2 (永恒吞噬 — eternal ingestion, devour everything): any
input the agent can point at is ingestible raw material, without filter
on what enters.

Ingestion captures raw material and reports back what the substrate is
currently hungry for. It does **not** transform what it captures —
transformation belongs to Digestion. Ingestion is therefore cheap and
permissive; rejection at intake is reserved for write-surface (R6)
violations, never for content judgment.

## Boundary

Ingestion **does**:

- Capture raw notes via `myco eat` with minimal, loss-preserving writes.
- Inspect the substrate and produce a hunger report (what's missing,
  what's stale) via `myco hunger`.
- Answer factual queries about substrate contents via `myco sense`.
- Maintain the boot-brief injection into the project's entry-point file
  (MYCO.md / CLAUDE.md signals block).

Ingestion **does not**:

- Digest, integrate, or consolidate notes (→ Digestion).
- Check invariants or raise lint errors (→ Homeostasis).
- Traverse cross-references (→ Circulation).
- Write outside `notes/` and `.myco_state/` (R6).

## Interfaces

Four commands, each with a CLI form and an MCP-tool form. Names retain the
biological metaphor per §9 E1.

```
myco eat     [--content <text> | --path <file_or_dir> | --url <url>] \
             [--tags <t1> <t2> ...] [--source <tag>]
myco hunger  [--execute] [--json]
myco sense   <query>    [--scope ...] [--format ...]
myco forage  [--path DIR] [--digest-on-read]
```

- **eat** (v0.5.4+ signature): append one or more raw notes. The
  source selector is exactly one of `--content` (literal text),
  `--path` (a file or directory ingested via the adapter registry —
  a directory produces one note per ingestible file), or `--url`
  (fetch + ingest via the URL adapter, requires the `adapters`
  extras). The three are mutually exclusive; passing more than one
  is a contract error. Never fails on content shape; failure is
  reserved for write-surface violations and for missing adapter
  extras on `--url`.
- **hunger**: compute the hunger report. `--execute` also writes the boot
  brief and patches the entry-point signals block.
- **sense**: read-only lookup, keyed by canon, notes, and doctrine docs.
- **forage**: inspect a candidate external directory for ingestible
  material; does not auto-write unless `--digest-on-read` is passed
  (which delegates to Digestion).

## Cross-subsystem contract

- Consumes the canon schema produced by Germination.
- Produces raw notes that Digestion transforms.
- Reads cross-references that Circulation maintains.
- Surfaces reflex signals that Homeostasis raises.
- Provides the `hunger` payload that `myco brief` (Cycle
  subsystem; L0 principle 1's single carved exception) reads and
  composes into its 7-section markdown rollup. `brief` performs no
  standalone scan — it is a read-only derivation of ingestion +
  homeostasis + circulation output.

## What changed from pre-rewrite

The old `hunger` command did a lot of things (detect drift, compute
backlog, patch entry-point, cache brief). In v0.4 these are still the
same four outputs, but their implementations are split by subsystem:
drift detection and reflex severity come from Homeostasis; hunger
composes them into a single user-visible report.

**v0.5.3** (shape stabilized v0.5.4): the hunger payload gains a
`local_plugins` block so the Agent sees on every boot what has
been grafted onto the substrate from `.myco/plugins/` — kept
visible so substrate-local extensions are never invisible magic.
The v0.5.4+ shape is:

```
local_plugins: {
  loaded:        bool,              # did `.myco/plugins/__init__.py` import?
  count_by_kind: {                  # registered items per kind
    dimension:         int,
    adapter:           int,
    schema_upgrader:   int,
    overlay_verb:      int,
  },
  errors:        list[str],         # import-time errors captured by
                                    # Substrate.local_plugin_errors
  module:        str | None,        # isolated module name, e.g.
                                    # "myco._substrate_plugins_<sid>_<hash>"
}
```

Field meanings:

- `loaded` — whether `.myco/plugins/__init__.py` successfully imported.
- `count_by_kind` — registered items per kind, broken out so the
  Agent can see at a glance what extension surface this substrate
  uses.
- `errors` — import-time errors captured by
  `Substrate.local_plugin_errors` (MF2 surfaces these as
  mechanical/HIGH findings; the hunger block is the user-readable
  form).
- `module` — the isolated module name Myco assigns the plugin
  tree (namespaced per substrate so two substrates with different
  plugins never collide in `sys.modules`).

**v0.5.6**: the `traverse` payload gains two companion fields —
`src_node_count` (how many `.py` files are in the graph) and
`cached` (whether this traverse call re-used the persisted
`.myco_state/graph.json` or rebuilt).
