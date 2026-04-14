# MYCO.md — agent entry page for the `myco-self` substrate

> You are an LLM agent reading this file at session start. Everything
> in this substrate is **for you**. Humans do not browse here (L0
> principle 1). Read this page top to bottom; it is short by design.

## What this substrate is

This repository is Myco — the cognitive substrate — and also
**Myco's own substrate**: the codebase uses Myco on itself, eating its
own dogfood through `_canon.yaml`, `notes/`, and `docs/`. Treat every
surface you encounter here as agent-readable primary material, not as
documentation for a human reader.

The substrate is governed by the five root principles in
[`docs/architecture/L0_VISION.md`](docs/architecture/L0_VISION.md).
Read that page before you begin real work in this substrate. You do
not have to re-read it every session; but any action that feels
governance-shaped (canon edit, doctrine revision, new subsystem) is
only legitimate when you can point at the L0 principle that justifies
it.

## What to do first

1. `python -m myco hunger` — computes and writes the session boot
   brief to `.myco_state/boot_brief.md`, then prints the summary.
   Every non-trivial session starts with this.
2. Check `log.md` (if present) for the last five entries — the tail
   of the timeline tells you what the previous session touched.
3. If you're about to write code: consult the relevant subsystem
   doctrine page under `docs/architecture/L2_DOCTRINE/` before
   reaching into `src/myco/<subsystem>/`. L2 is the contract between
   what a subsystem *should* do and what the code in it *does* do.

## The command surface

All verbs are defined by a single manifest:
[`src/myco/surface/manifest.yaml`](src/myco/surface/manifest.yaml).
Both the CLI (`python -m myco <verb>`) and the MCP tool server
(`myco.surface.mcp.build_server`) are generated from it. If you need
to know what verbs exist, read that file — not this page.

Twelve verbs, grouped by subsystem:

- **genesis**     — `genesis` (bootstrap a fresh substrate)
- **ingestion**   — `hunger`, `eat`, `sense`, `forage`
- **digestion**   — `reflect`, `digest`, `distill`
- **circulation** — `perfuse`, `propagate`
- **homeostasis** — `immune`
- **meta**        — `session-end` (composes reflect + immune)

Every verb accepts `--project-dir`, `--exit-on`, and `--json`.

## How to read the substrate

The substrate is a **graph**, not a tree (L0 principle 5). Every node
— canon field, note, doctrine page, code module, external artifact —
is reachable from every other by traversal. If you find an orphan,
that is circulation work.

Layers top-down:

```
L0  docs/architecture/L0_VISION.md             identity
L1  docs/architecture/L1_CONTRACT/*.md         contract
L2  docs/architecture/L2_DOCTRINE/*.md         doctrine (five subsystems)
L3  docs/architecture/L3_IMPLEMENTATION/*.md   implementation map
L4  _canon.yaml + code + notes/                the live substrate
```

Each lower layer is strictly subordinate to every higher layer. If L4
disagrees with L3, L3 wins — but the disagreement is a finding to
record, not to silence.

## What NOT to do

- **Do not edit L0, L1, or L2 files as a consequence of implementation
  work.** If implementation reveals a gap in doctrine, stop, write a
  craft doc under `docs/primordia/`, get owner approval, then resume.
- **Do not carry forward `legacy_v0_3/`.** The pre-rewrite code is
  quarantined. It is not imported, tested, or referenced by any live
  file. Git history preserves it; `v0.3.4-final` is the anchor tag.
- **Do not treat `integrated` as final.** Per L0 principle 4, every
  note is a work in progress until it is distilled out of existence.

## When you finish a session

Run `python -m myco session-end`. That composes `reflect` (promote raw
notes) with `immune --fix` (auto-correctable lint findings) and
returns a structured payload. A clean session-end is the only
acceptable end state; a dirty one is the starting point of the next
session.

## When you are stuck

Re-read L0. Then re-read the relevant L2 page. Then re-read this file.
If you are still stuck, ingest a note describing the stuck-ness (`eat`)
and let reflection decide.
