# L2 — Digestion

> **Status**: APPROVED (2026-04-15, greenfield rewrite §9; verb
> vocabulary revised at v0.5.3 per
> `docs/primordia/v0_5_3_fungal_vocabulary_craft_2026-04-17.md`).
> **Layer**: L2. Subordinate to `L0_VISION.md` and `L1_CONTRACT/*`.
> **Upward mapping**: implements L1 R2 (ritualized end-of-session
> assimilation) and the "self-validating substrate" invariant (L0 #2)
> via digest-time consistency checks.

---

## Responsibility

Digestion owns the transformation pipeline: **raw notes → integrated,
structured, cross-referenced knowledge**. It is the metabolic engine
of the substrate and the subsystem that realizes L0 principles 3 and
4 (永恒进化 + 永恒迭代) — the continuous reshape of substrate
content.

The pipeline stages are named biologically and are load-bearing.
Forward flow is the default; retro-editing an already-integrated
note is allowed when a later session sharpens prior context
(principle 4: eternal iteration — "final" is not a status).

## Stages

```
raw  →  assimilating  →  integrated  →  sporulated
              ↑_______________↓              ↑
              re-assimilate allowed          shape-change allowed
              (principle 4)                  (principle 3)
```

- **raw**: as captured by `myco eat`. Owned by Ingestion before
  assimilation.
- **assimilating**: claimed by a `myco assimilate` invocation.
  Short-lived. Biology: once absorbed into the hyphal network, raw
  material gets assimilated into the organism proper.
- **integrated**: finalized as an `n_*.md` note with frontmatter
  `status: integrated`, cross-referenced to canon, doctrine, and
  sibling notes. **Not** terminal — a later session may re-
  assimilate it when context sharpens.
- **sporulated**: rare; a group of integrated notes whose shared
  insight has been lifted into an L2 doctrine doc or a new
  `_canon.yaml` field. Sporulation is the engine of substrate-shape
  evolution (principle 3) — accumulated nutrients concentrated into
  dispersible propagatable content.

## Boundary

Digestion **does**:

- Run `myco assimilate` to promote raw notes through the pipeline.
- Refuse to promote a note whose cross-references don't exist
  (self-validation at digest time).
- Run `myco digest <note-id>` for targeted single-note promotion.
- Run `myco sporulate <doctrine-target>` for the rare sporulation
  step.

Digestion **does not**:

- Invent content not present in the raw note.
- Delete notes (even stale ones; retention is a Homeostasis
  question).
- Edit canon (sporulation proposes canon changes; Homeostasis
  validates them on the next immune pass).
- **Call an LLM or any external synthesis model.** v0.5.5 writes
  this boundary explicitly (see craft
  `v0_5_5_close_audit_loose_threads_craft_2026-04-17.md` §MAJOR-C):
  `sporulate` prepares the scaffolding — selects integrated-note
  sources, extracts shared tags, materializes a proposal skeleton
  under `notes/distilled/d_<slug>.md` — but the actual synthesis
  prose is the **Agent's** job. Per L0 principle 1 the Agent reads
  sporulate's output, calls its own model, and writes the synthesis
  back into the proposal file. The substrate never embeds a model
  call. This separation keeps Myco provider-agnostic (works with
  any Agent on any Claude/GPT/local model) and keeps the L0
  "Agent calls LLM, substrate does not" invariant intact.

### Sporulate output shape

`sporulate <slug>` writes exactly one file:
`notes/distilled/d_<slug>.md`. The file's frontmatter carries:

- `kind: distilled` — the fixed distilled-note kind tag.
- `sources: [<note-path>, ...]` — the integrated-note paths the
  sporulate call bundled; the Agent can always trace back.
- `tags: [<tag>, ...]` — the auto-extracted shared-tag theme
  (tags that appear across the source notes' frontmatter).

The body is auto-generated scaffolding only:

1. An auto-extracted **shared-tag theme** summary — plain text
   listing the tags the sporulate call identified as common
   across sources.
2. A **first-line-per-source seed list** — one line per source
   note, taken from its first non-frontmatter prose line, so the
   Agent has a fast preview of what each source contributes.
3. A `TODO: synthesis prose` placeholder — the empty slot where
   the Agent's downstream synthesis call writes the actual
   distilled doctrine.

The `MP1` lint dimension (mechanical/HIGH at v0.5.6) is the
mechanical guard that prevents sporulate from ever acquiring a
model call inside the substrate: MP1 flags any
`src/myco/digestion/sporulate.py` import of a provider SDK unless
`canon.system.no_llm_in_substrate: false`. The separation is not
stylistic; it is mechanically enforced.

## Interfaces

```
myco assimilate [--all | --note <id>] [--json]
myco digest     <note-id> [--dry-run]
myco sporulate  <doctrine-slug>
```

All three are idempotent on already-integrated notes. The v0.5.2
aliases `reflect` → `assimilate` and `distill` → `sporulate` still
resolve throughout the 0.x line; alias removal is scheduled for
v1.0.0.

## Cross-subsystem contract

- Reads raw notes from Ingestion.
- Writes integrated notes with cross-references maintained by
  Circulation.
- Emits metabolic-category findings that Homeostasis surfaces at
  exit.

## On the legacy `propagate` command (§9 E4 redefinition)

`propagate` historically meant "push digested content from this
Myco substrate to a downstream project". That behavior does not
belong in Digestion — it is cross-substrate movement. Under v0.4.0
the redefined `propagate` lives in **Circulation** (see
`circulation.md` §"propagate"). Digestion has no `propagate` verb.
