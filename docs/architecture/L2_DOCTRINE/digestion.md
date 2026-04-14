# L2 — Digestion

> **Status**: APPROVED (2026-04-15, greenfield rewrite §9).
> **Layer**: L2. Subordinate to `L0_VISION.md` and `L1_CONTRACT/*`.
> **Upward mapping**: implements L1 R2 (ritualized end-of-session
> reflection) and the "self-validating substrate" invariant (L0 #2) via
> digest-time consistency checks.

---

## Responsibility

Digestion owns the transformation pipeline: **raw notes → integrated,
structured, cross-referenced knowledge**. It is the metabolic engine of
the substrate.

The pipeline is strictly directional. A note moves forward through stages;
it does not reverse. Stages are named biologically and are load-bearing.

## Stages

```
raw  →  digesting  →  integrated  →  distilled
```

- **raw**: as captured by `myco eat`. Owned by Ingestion before digest.
- **digesting**: claimed by a `myco reflect` invocation. Short-lived.
- **integrated**: finalized as an `n_*.md` note with frontmatter
  `status: integrated`, cross-referenced to canon, doctrine, and sibling
  notes.
- **distilled**: rare; a group of integrated notes whose shared insight
  has been lifted into an L2 doctrine doc or a new `_canon.yaml` field.
  Distilled notes are marked `status: distilled` and retained as history.

## Boundary

Digestion **does**:

- Run `myco reflect` to promote raw notes through the pipeline.
- Refuse to promote a note whose cross-references don't exist
  (self-validation at digest time).
- Run `myco digest <note-id>` for targeted single-note promotion.
- Run `myco distill <doctrine-target>` for the rare distillation step.

Digestion **does not**:

- Invent content not present in the raw note.
- Delete notes (even stale ones; retention is a Homeostasis question).
- Edit canon (distillation proposes canon changes; Homeostasis validates
  them on the next immune pass).

## Interfaces

```
myco reflect [--all | --note <id>] [--json]
myco digest  <note-id> [--dry-run]
myco distill <doctrine-slug>
```

All three are idempotent on already-integrated notes.

## Cross-subsystem contract

- Reads raw notes from Ingestion.
- Writes integrated notes with cross-references maintained by Circulation.
- Emits metabolic-category findings that Homeostasis surfaces at exit.

## On the legacy `propagate` command (§9 E4 redefinition)

`propagate` historically meant "push digested content from this Myco
substrate to a downstream project". That behavior does not belong in
Digestion — it is cross-substrate movement. Under v0.4.0 the redefined
`propagate` lives in **Circulation** (see `circulation.md` §"propagate").
Digestion has no `propagate` verb.
