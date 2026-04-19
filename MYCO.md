# MYCO.md — agent entry page for the `myco-self` substrate

> You are an LLM agent reading this file at session start. Everything
> in this substrate is **for you**. Humans do not browse here (L0
> principle 1 — 只为 Agent). They speak natural language; you invoke
> the verbs. Read this page top to bottom; it is short by design.

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

1. Call `python -m myco hunger` yourself (or rely on the
   SessionStart hook, which already fired it). This is R1 of the hard
   contract; it computes and writes the session boot brief to
   `.myco_state/boot_brief.md`, then prints the summary. Every non-
   trivial session starts with this. The human never calls `hunger` —
   you do.
2. Check `log.md` (if present) for the last five entries — the tail
   of the timeline tells you what the previous session touched.
3. If you are about to write code: consult the relevant subsystem
   doctrine page under `docs/architecture/L2_DOCTRINE/` before
   reaching into `src/myco/<subsystem>/`. L2 is the contract between
   what a subsystem *should* do and what the code in it *does* do.

## The command surface

All verbs are defined by a single manifest:
[`src/myco/surface/manifest.yaml`](src/myco/surface/manifest.yaml).
Both the CLI (`python -m myco <verb>`) and the MCP tool server
(`myco.surface.mcp.build_server`) are generated from it. If you need
to know what verbs exist, read that file — not this page.

Eighteen verbs (v0.5.7: 17 agent + 1 human-facing `brief`), grouped
by subsystem. Every v0.5.2 alias still resolves through v1.0.0 with
a one-shot `DeprecationWarning`; the canonical form is what you
should emit in new calls:

- **germination**  — `germinate` (was `genesis`)
- **ingestion**    — `hunger`, `eat`, `sense`, `forage`
- **digestion**    — `assimilate` (was `reflect`), `digest`, `sporulate` (was `distill`)
- **circulation**  — `traverse` (was `perfuse`), `propagate`
- **homeostasis**  — `immune`
- **cycle**        — `senesce` (was `session-end`; `--quick` flag at v0.5.7 for SessionEnd hook), `fruit` (was `craft`), `molt` (was `bump`), `winnow` (was `evolve`), `ramify` (was `scaffold`), `graft` (new at v0.5.3), `brief` (new at v0.5.5 — the one human-facing exception to L0 principle 1)

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

## Substrate-local plugins (v0.5.3)

A downstream substrate (any substrate whose `canon.identity.substrate_id`
is not `myco-self`) can carry its own lint dimensions, ingestion
adapters, schema upgraders, and even brand-new verbs without forking
Myco. Scaffold them with `myco ramify --dimension <ID>`,
`--adapter <name>`, or `--verb <name>` (pass `--substrate-local`
explicitly to override autodetection). They land under
`<substrate>/.myco/plugins/` and are auto-imported on
`Substrate.load()`; any verb the overlay at
`<substrate>/.myco/manifest_overlay.yaml` declares appears alongside
the built-ins. You inspect what has grafted on with
`myco graft --list | --validate | --explain <name>`. The `MF2` lint
dimension (mechanical / HIGH) keeps the auto-import audible — it
fires on shape errors, overlay-YAML errors, or verb-name collisions.

**Note for `myco-self`**: this repository IS the kernel. There is no
`.myco/plugins/` tree here, and `ramify` defaults `--substrate-local`
OFF so new kernel verbs / dimensions land inside `src/myco/`. Pass
`--substrate-local` only if you need to dogfood the overlay path.

## What NOT to do

- **Do not edit L0, L1, or L2 files as a consequence of implementation
  work.** If implementation reveals a gap in doctrine, stop, fruit a
  craft doc under `docs/primordia/` (via `myco fruit`), get owner
  approval, then resume.
- **Do not carry forward `legacy_v0_3/`.** The pre-rewrite code is
  quarantined. It is not imported, tested, or referenced by any live
  file. Git history preserves it; `v0.3.4-final` is the anchor tag.
- **Do not treat `integrated` as final.** Per L0 principle 4, every
  note is a work in progress until it is sporulated out of existence.

## When you finish a session

Run `python -m myco senesce` yourself (or rely on the PreCompact hook,
which already fires it at `/compact`). That composes `assimilate`
(promote raw notes) with `immune --fix` (auto-correctable lint
findings) and returns a structured payload. For non-compact session
exits (`/exit`, Ctrl+D, window-close), the SessionEnd hook fires
`python -m myco senesce --quick` (assimilate only) to stay inside
Claude Code's ~1.5 s SessionEnd kill budget — `immune` runs on the
next boot. A clean senesce (either mode) is the acceptable end state;
a dirty one is the starting point of the next session. The legacy
`session-end` alias still resolves if you find it in an older script.

## When you are stuck

Re-read L0. Then re-read the relevant L2 page. Then re-read this file.
If you are still stuck, ingest a note describing the stuck-ness (call
`myco eat`) and let the next assimilation decide.
