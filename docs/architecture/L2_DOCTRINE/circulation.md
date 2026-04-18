# L2 — Circulation

> **Status**: APPROVED (2026-04-15, greenfield rewrite §9; verb
> vocabulary revised at v0.5.3 per
> `docs/primordia/v0_5_3_fungal_vocabulary_craft_2026-04-17.md`).
> **Layer**: L2. Subordinate to `L0_VISION.md` and `L1_CONTRACT/*`.
> **Upward mapping**: implements L1 R5 (cross-reference on creation) and
> the "agent-first consumption" invariant (L0 #1) — an agent reads
> knowledge by traversing the mycelium graph, so the graph must be
> well-formed.

---

## Responsibility

Circulation is the subsystem that realizes L0 principle 5 (万物互联 —
universal interconnection, the mycelium network). It owns the **mycelium
graph**: the network of cross-references connecting notes, doctrine docs,
canon fields, external artifacts, and — across substrate boundaries —
peer substrates. Integrity of this graph is what lets an agent chase
context without dead-ending.

Circulation operates at two scales:

- **Intra-substrate**: the cross-reference graph inside one substrate.
- **Inter-substrate**: `propagate` moves integrated knowledge across
  substrates in a general-purpose federation (no project boundary — per
  L0 principle "通用型" framing).

## What "cross-reference" means precisely

A cross-reference is a markdown link or a `…_ref` YAML field that points
to a file or a file section. Circulation tracks them explicitly so lint
can detect:

- **Orphans**: files no cross-reference points to.
- **Dangling refs**: cross-references pointing to non-existent targets.
- **One-way refs**: where reciprocal linkage is expected (e.g. doctrine
  → code package should have a back-link).

## Boundary

Circulation **does**:

- Maintain an index of cross-references. The graph is built from the
  authoritative sources (canon + notes + docs + `src/**/*.py`) and
  persisted to `.myco_state/graph.json` at v0.5.5+ with a canon+src
  fingerprint; subsequent builds reuse the cache when the fingerprint
  still matches. The cache is always reconstructable — it is not a
  source of truth, just an acceleration.
- Cover Python source under `src/**` at v0.5.5+: each `.py` file is a
  graph node; `import` edges track internal module dependencies;
  `code_doc_ref` edges link module docstrings to the doctrine and
  primordia paths they cite (closing the v0.4.1 audit gap that left
  code outside the mycelium).

### Graph API (v0.5.5+)

The graph module exposes four callables that compose the build /
cache / persist surface:

- `build_graph(ctx, use_cache=True)` — build the mycelium graph.
  With `use_cache=True` (default) reuses
  `.myco_state/graph.json` when its fingerprint still matches
  observed state; with `use_cache=False` always rebuilds from
  scratch.
- `invalidate_graph_cache(substrate)` — delete the persisted cache
  so the next build starts fresh. Call sites: `molt` (contract
  bump invalidates), `ramify` (new verb / dimension / adapter
  invalidates), tests that mutate `src/` in-place.
- `load_persisted_graph(path)` — read `.myco_state/graph.json`
  and reconstruct the graph object without rebuilding. Used by
  `traverse` when the fingerprint matches.
- `persist_graph(graph, path)` — serialize the graph to
  `.myco_state/graph.json` after a rebuild.

**Fingerprint formula**: the cache fingerprint is
`sha256(canon_text) + sorted((path, mtime) for path in <root>/src/**/*.py)`.
Any canon mutation or any `.py` file mtime change invalidates the
cache; no other substrate change (notes, docs, primordia) triggers
a rebuild because those are re-read directly on every traverse.

**Cache location**: `<substrate_root>/.myco_state/graph.json`.
The file is written atomically (temp file + rename). Corrupt or
missing cache is a silent miss — traverse falls back to a full
build and overwrites.

**`traverse` payload** at v0.5.6 carries two new fields:
`src_node_count` (how many `.py` files are represented as graph
nodes) and `cached` (True when this call served from
`.myco_state/graph.json` without rebuild, False when the
fingerprint mismatched or the cache was absent).
- Run `myco traverse` to walk the mycelial graph and surface
  anastomotic health (dangling refs, orphans, one-way links).
- Run `myco propagate` — cross-substrate push (see §propagate below).
- Report graph health as a semantic-category finding at immune time.

Circulation **does not**:

- Own file contents (Ingestion/Digestion do).
- Rewrite prose to fit the graph (propose only; humans edit).
- Auto-create files to satisfy a missing cross-reference (that's accretion
  in the accretion direction; the right answer is usually to remove the
  dangling ref).

## Interfaces

```
myco traverse  [--scope canon|notes|docs|all]
myco propagate --to <path-to-downstream-substrate> [--dry-run]
```

The v0.5.2 alias `myco perfuse` still resolves to the `traverse`
handler throughout the 0.x line; alias removal is scheduled for
v1.0.0.

## `propagate` — redefined per §9 E4

### Semantics

`propagate` moves **digested, integrated knowledge** from this Myco
substrate into a downstream substrate. It is *not*:

- A file-sync tool (use `rsync`/`git`).
- A bidirectional sync (one direction only).
- A code deployment (that belongs in a project's own release pipeline).

It *is*: "publish the integrated notes and doctrine snapshots from this
host into that host's inbox, so that host's agent can digest them into
its own substrate on next `assimilate` (the v0.5.2 alias `reflect`
still resolves if a script has that name cached)."

### Boundary

Propagate **does**:

- Read the source substrate's `integrated` notes and optionally its
  distilled doctrine docs.
- Write them into the downstream substrate's `notes/` directory with a
  preserved source-trace frontmatter (`source: <src-project>@<commit>`,
  `ingest_state: raw`).
- Refuse to write if the downstream substrate's contract version is
  incompatible (major mismatch ⇒ error; minor mismatch ⇒ warn).

Propagate **does not**:

- Execute downstream digestion automatically (the downstream substrate's
  agent does that on its next session).
- Overwrite existing notes (duplicate-by-id is an error).
- Touch anything outside the downstream substrate's write-surface.

### Interface

```
myco propagate \
  --to <downstream-substrate-root> \
  [--select integrated|distilled|both] \
  [--since <contract-version|date>] \
  [--dry-run]
```

### No direct port of old implementation

Per §9 E4 the v0.3 `propagate` command will not be code-ported. The new
implementation is built fresh against this semantics page, against L3's
error model, and against the new Circulation package structure. Behavior
parity with v0.3 is not a goal; spec compliance with this doc is.

### Cross-substrate contract

- Reads: source substrate's `notes/` (integrated + optionally distilled)
  and `_canon.yaml::contract_version`.
- Writes: downstream's `notes/` only. Never touches downstream's canon;
  downstream's Homeostasis validates on next pass.

## Cross-subsystem contract (internal)

- Reads integrated notes from Digestion.
- Reports graph integrity findings to Homeostasis for exit-code
  classification.
- Uses Ingestion's path resolution for `--to` directory validation.
