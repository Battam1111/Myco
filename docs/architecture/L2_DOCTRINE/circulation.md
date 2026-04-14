# L2 — Circulation

> **Status**: APPROVED (2026-04-15, greenfield rewrite §9).
> **Layer**: L2. Subordinate to `L0_VISION.md` and `L1_CONTRACT/*`.
> **Upward mapping**: implements L1 R5 (cross-reference on creation) and
> the "agent-first consumption" invariant (L0 #1) — an agent reads
> knowledge by traversing the mycelium graph, so the graph must be
> well-formed.

---

## Responsibility

Circulation owns the **mycelium graph**: the network of cross-references
connecting notes, doctrine docs, canon fields, and external artifacts.
Integrity of this graph is what lets an agent chase context without
dead-ending.

Circulation is also where **cross-substrate movement** lives: pushing
digested content from this Myco substrate to another host substrate (the
redefined `propagate`).

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

- Maintain an index of cross-references (built on demand, not stored).
- Run `myco perfuse` to inject missing cross-refs (with user review).
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
myco perfuse   [--dry-run] [--scope ...]
myco propagate --to <path-to-downstream-substrate> [--dry-run]
```

## `propagate` — redefined per §9 E4

### Semantics

`propagate` moves **digested, integrated knowledge** from this Myco
substrate into a downstream substrate. It is *not*:

- A file-sync tool (use `rsync`/`git`).
- A bidirectional sync (one direction only).
- A code deployment (that belongs in a project's own release pipeline).

It *is*: "publish the integrated notes and doctrine snapshots from this
host into that host's inbox, so that host's agent can digest them into
its own substrate on next reflect."

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
