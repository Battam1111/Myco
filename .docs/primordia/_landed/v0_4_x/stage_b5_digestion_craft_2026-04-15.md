# Stage B.5 — Digestion Craft

> **Date**: 2026-04-15.
> **Governs**: `src/myco/digestion/` + `tests/unit/digestion/`.
> **Upward**: L2 `digestion.md`.

---

## Round 1 — 主张

Four modules per L3 package map:

```
src/myco/digestion/
├── __init__.py
├── pipeline.py     # stage state machine (raw / digesting / integrated / distilled)
├── reflect.py      # bulk-promote raw notes
├── digest.py       # single-note promotion, with --dry-run
└── distill.py      # rare distillation proposal
```

Pipeline semantics:

- `raw` notes live at `notes/raw/<name>.md`.
- `integrated` notes live at `notes/integrated/n_<stem>.md`.
- Promotion: read raw, parse frontmatter, validate `references:` (if
  present) point at extant paths, rewrite frontmatter with
  `stage: integrated`, move file to `notes/integrated/`.
- Distillation writes a proposal file under `notes/distilled/` listing
  source note paths and the proposed doctrine slug. Does **not** edit
  canon or docs (Homeostasis would later surface inconsistencies).

## Round 1.5 — 自我反驳

T1. **Frontmatter parsing shape-match.** Ingestion wrote a fixed YAML
frontmatter in Stage B.4. If Digestion's parser is sloppy (regex on
`---` markers), it'll drift from the writer. Should I factor out a
shared frontmatter helper in `core/`?

T2. **Move vs in-place.** Moving the file changes its path; any existing
cross-reference elsewhere (doctrine doc citing
`notes/raw/<name>.md`) now breaks. But leaving it in-place means the
directory name lies about the stage. Doctrine says the frontmatter
`status` is the source of truth, not the directory — so
in-place is defensible. Yet the `n_*.md` naming convention in L2
doctrine signals a directory-structural change.

T3. **Reference validation scope.** "Cross-references" could mean
canonical paths inside the substrate, URLs, or note-ids. Stage B.5
handles only substrate-relative paths; external URLs are ignored
(not errors).

T4. **Idempotency on already-integrated notes.** L2 says `digest` is
idempotent. Re-digesting an integrated note should no-op and succeed
(not raise). But the source (raw) is gone — where does `digest`
locate an already-integrated note? By **note-id** — the filename
stem with or without the `n_` prefix.

T5. **Distill's output shape.** L2 says distillation proposes an L2
doctrine doc. But B.5 shouldn't author doctrine — that's a human/L0
craft decision. So `distill` produces a *proposal note* under
`notes/distilled/` summarizing the intent; actual doctrine authorship
stays out-of-band.

T6. **`raw` directory may not exist.** `reflect --all` on a fresh
substrate (no eats yet) should not error. It just reports zero
promoted.

T7. **Concurrent `reflect` and `eat`?** Not a real concern at B.5 —
Myco is single-tenant per process. Skip.

## Round 2 — 修正

R1 (T1). Factor a small frontmatter helper into
`myco.digestion.pipeline` (not `core/`; only digestion reads/writes
frontmatter after ingestion). Shape: `parse_note(text) -> Note` and
`render_note(note) -> str`, where `Note` carries the frontmatter as a
dict plus the body text. Eat's rendering stays in ingestion (writer
side); digestion owns the read/rewrite side.

R2 (T2). Move the file. Reasons: (a) directory filter is the cheapest
way for other subsystems to ask "show me integrated notes"; (b) L2
doctrine's `n_*.md` naming is explicit; (c) cross-references outside
the substrate pointing at `notes/raw/…` are not a supported use case
— notes are internal state, not API. The integrated note retains the
original stem as the primary id: `notes/integrated/n_<stem>.md`.

R3 (T3). Reference validation validates only strings that look like
relative paths (not starting with `http`, `https`, `#`, or `/`).
Unknown-shape strings are tolerated. The check is existence only;
content match is B.6 circulation's job.

R4 (T4). `digest <note-id>` first looks up `notes/raw/<id>.md`,
`notes/raw/<id>*.md` (stem match), then `notes/integrated/n_<id>.md`.
If found integrated, it's a no-op with exit 0. If found raw, promote.
If found in neither: `UsageError`.

R5 (T5). `distill <slug>` creates
`notes/distilled/d_<slug>.md` with frontmatter
`{sources: [...], proposed_doctrine: <slug>, stage: "distilled"}` and
a body listing the source notes' first-line slugs as bullet points.
Refuses to overwrite an existing distilled file.

R6 (T6). `reflect --all` treats missing `notes/raw/` as "zero notes
to promote" and returns `Result(exit_code=0, payload={"promoted": 0})`.

## Round 2.5 — 再驳

T8. R2's move is irreversible without a restore path. Is there a case
where the user wants to undo promotion? v0.4.0 alpha — we don't owe
undo. Note remaining under new path with old frontmatter is the
record; downstream analysis of integrated content uses that.

T9. R4's lookup cascade could match multiple candidates (glob
`raw/<id>*`). Make it strict: `<id>` must match a filename's stem
exactly, or the first component before `_` in the stamp-prefixed
filename. Actually simpler: `<id>` is the **exact stem** of an existing
file under raw/ or integrated/. No glob. User constructs the id from
`sense` hits.

T10. R5's `distill` assumes `notes/distilled/` exists. It should
auto-create, parallel to eat's auto-create for raw.

## Round 3 — 反思

F8. No undo, documented in the craft.
F9. Lookup by exact stem. CLI surface in B.7 accepts both `<stamp>_<slug>`
and the `n_<stamp>_<slug>` form and strips the prefix before lookup.
F10. Auto-create all `notes/<stage>/` directories lazily.

### What this craft revealed

- Frontmatter read/write asymmetry (ingestion writes, digestion
  reads+rewrites) justifies duplicating the small frontmatter helper
  only on the digestion side. `core/` stays subsystem-neutral.
- Distillation is deliberately weak at B.5. Actual doctrine
  authorship is a human/craft act; B.5 ships the proposal
  mechanism only.
- No L0/L1/L2 edits needed.

## Deliverables

```
src/myco/digestion/
├── __init__.py
├── pipeline.py       # Note + parse_note + render_note + promote
├── reflect.py        # bulk + single-note entry via run()
├── digest.py         # single-note promote with dry-run
└── distill.py        # proposal writer

tests/unit/digestion/
├── __init__.py
├── test_pipeline.py
├── test_reflect.py
├── test_digest.py
└── test_distill.py
```

## Acceptance

- `pytest tests/unit/digestion/` green.
- Full suite still green (164 prior + digestion additions).
- End-to-end: eat three notes → reflect --all → all three land under
  `notes/integrated/` with `stage: integrated` frontmatter.
- Re-digesting an integrated note by id is a no-op (exit 0).
