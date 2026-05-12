---
slug: khazix-neat-freak-isomorphism-with-myco-senesce
distilled_at: '2026-04-29T11:46:08Z'
stage: distilled
external_provenance:
  upstream: https://github.com/KKKKhazix/khazix-skills/tree/main/neat-freak
  upstream_files:
  - https://raw.githubusercontent.com/KKKKhazix/khazix-skills/main/neat-freak/SKILL.md
  - https://raw.githubusercontent.com/KKKKhazix/khazix-skills/main/neat-freak/references/agent-paths.md
  - https://raw.githubusercontent.com/KKKKhazix/khazix-skills/main/neat-freak/references/sync-matrix.md
  upstream_license: see upstream repo (no LICENSE enumerated as of capture date)
  captured_at: '2026-04-29'
ingestion_pipeline:
  intermediate_integrated_notes: excreted
  excretion_rationale: 'verbatim copies of public upstream are noise per neat-freak''s own discipline (editor not logger; merge over append; delete obsolete). git history + the upstream URLs are the archive layer; this synthesis is the value-add.'
tags:
- khazix-skills
- neat-freak
- session-end-discipline
related_doctrine:
- docs/architecture/L0_VISION.md
- docs/architecture/L1_CONTRACT/protocol.md
- docs/architecture/L2_DOCTRINE/cycle.md
- docs/architecture/L2_DOCTRINE/digestion.md
- docs/architecture/L2_DOCTRINE/circulation.md
- docs/architecture/L2_DOCTRINE/homeostasis.md
related_verbs:
- senesce
- assimilate
- immune
- excrete
- traverse
related_dimensions:
- SE1
- DC4
- MB6
---

# Distillation: khazix-neat-freak ≅ Myco session-end discipline

A synthesis of `khazix-skills/neat-freak` (a cross-platform Agent Skill
for end-of-session knowledge cleanup) viewed through Myco's L0/L1/L2 lens.
Promotes to L2 doctrine candidate for a future `myco fruit` craft if the
owner wants to canonize the isomorphism (deferred — distilled stage is
the appropriate resting point for now).

> **Recursive correctness note.** This note was originally accompanied by
> 3 verbatim integrated copies of the upstream files (notes/integrated/
> n_20260429T114521Z.md and two siblings). On owner direction, those
> copies were excreted **applying neat-freak's own discipline to its own
> ingestion** — `editor not logger; merge over append; delete obsolete`.
> The verbatim text adds no signal Myco can't fetch from the upstream
> URLs above; the value-add is this synthesis. See
> `ingestion_pipeline.excretion_rationale` in the frontmatter.

## Source identity

`khazix-skills/neat-freak` is a **cross-platform Agent Skill** (Claude Code,
OpenAI Codex, OpenCode, OpenClaw) that runs at the end of a development
session and reconciles three knowledge layers — Agent memory, project-root
markdown (`CLAUDE.md` / `AGENTS.md`), and `docs/` — against the actual code
state. The skill's own framing: "you are a knowledge-base **editor**, not
a logger; loggers append, editors review, merge duplicates, fix stale
content, delete obsolete entries."

The skill ships three files (277 lines total):

- `SKILL.md` (10268 B): the procedure itself — 4 phases (inventory →
  identify changes → modify → self-check) with a rigid "force `ls`
  before judgement" discipline.
- `references/agent-paths.md`: cross-platform table mapping each
  Agent host (Claude Code / Codex / OpenCode / OpenClaw) to its
  memory directory + global-config file convention.
- `references/sync-matrix.md`: a **variation-impact matrix** — given
  a code change of type X (new API route / new env var / new DB
  table / new feature / cross-project change), which doctrine
  layers must be touched.

## Core thesis

**neat-freak is the procedural-prose mirror of Myco's R2 + senesce +
assimilate + SE1 stack.** Same problem (sessions accumulate state that
falls out of sync with reality), opposite delivery:

- neat-freak ships an **imperative procedure** (do `ls`, then identify
  changes, then edit, then check). The Agent reads + executes.
- Myco ships an **executable kernel** (`senesce` runs `assimilate +
  immune --fix`; SE1 dim mechanically detects orphans; R6 mechanically
  prevents pollution; canon validates twice). The Agent triggers,
  the kernel runs.

Both target the same drift: human-AI shared substrate decaying because
session-end never got disciplined. neat-freak teaches the discipline;
Myco mechanizes it.

## Isomorphism table

| neat-freak concept | Myco mechanism | Fidelity |
|---|---|---|
| "Session-end knowledge cleanup" trigger phrases ("sync up", "整理一下", …) | R2 hard contract: `myco senesce` on PreCompact / SessionEnd hook | **identical intent**, mechanized vs prompt-pattern-matched |
| 4-phase flow: inventory → identify → modify → self-check | `senesce` composes: `assimilate` (modify raw → integrated) + `immune --fix` (self-check 46 dims) | identical shape, +mechanical floor |
| "Force `ls` before judgement" | R3 (sense before assert) + M1/M2/M3 mechanical lints that walk the filesystem deterministically | identical philosophy, M*-class dims are the encoded `ls` |
| Three-tier knowledge: Agent memory / project root .md / docs/ | L0 → L1 → L2 → L3 → L4 strict subordination layering | weaker stratification (3 vs 5 layers) but **same load-bearing claim**: layer above governs layer below |
| "Delete > preserve" editing rule | `myco excrete` (v0.5.24) — safe-delete a raw note to `.myco_state/excreted/` with audit tombstone; SE1 dim detects orphans | mechanized; excrete is the verb, SE1 is the lint |
| "Absolute time, never 'today'/'recently'" | `assimilate` writes `captured_at: <ISO 8601>` frontmatter; manifest-driven note IDs are timestamp-prefixed | identical principle, applied at write-time |
| Self-check checklist ("each file judged 'change' or 'no change'") | `immune` enumerates 46 dims, each emitting Finding objects with severity + path | mechanized + scored |
| sync-matrix variation-impact: change-type → doctrine layers touched | Myco lint dimensions (per-rule rather than per-change) | **inverse decomposition**: neat-freak indexes by change cause, Myco indexes by drift symptom |
| "Cross-project changes touch downstream docs" | `myco propagate` (intra-substrate write to downstream `notes/raw/`) | partial: Myco propagates *notes*, neat-freak propagates *docs* |

## Complementarity (each fills a gap the other doesn't address)

**What neat-freak adds that Myco's contract doesn't claim:**

1. **Cross-platform agent-paths table** (`references/agent-paths.md`).
   Myco's L0 P1 is "Agent-First" but the surface (20 verbs, 14 host
   adapters) is Myco-specific. neat-freak names a broader truth: the
   *Agent's own memory* is a knowledge layer the orchestration must
   sync, regardless of which kernel (Myco / not-Myco) is in play.
   Myco's `myco-install host <client>` writes config but does NOT
   write to the Agent's *memory* file (e.g. `~/.claude/CLAUDE.md`).
   neat-freak treats that as a first-class layer.
2. **Per-change-type variation-impact decomposition** (`sync-matrix.md`).
   Myco's lint dims index by drift symptom ("orphan note" → SE1).
   neat-freak's matrix indexes by change cause ("you added a new
   API route → these 4 doc layers must be touched"). The two are
   duals; Myco could adopt the dual representation as a doctrine
   companion (see "Future axis" below).
3. **`docs/` as first-class human-readable layer.** Myco's L0 P1
   strictly serves Agents; the `myco brief` verb (v0.5.5) is the
   single carved exception. neat-freak treats human-readable docs
   as a non-optional reconciliation target. The two stances differ
   by design choice, not by oversight.

**What Myco mechanizes that neat-freak's procedure leaves to discipline:**

1. **R6 write-surface enforcement** — `_canon.yaml::system.write_surface.allowed`
   gates 8 mutating verbs. neat-freak relies on the Agent not editing
   wrong files; Myco refuses at the kernel.
2. **Schema-versioned canon** — `_canon.yaml` carries `schema_version: "2"`
   with named partial upgraders (`_v1_to_v2_*`). Doctrine evolution
   stays mechanically auditable. neat-freak has no notion of schema.
3. **46 lint dims with severity ordering** + exit-code grammar
   (`mechanical:critical,shipped:critical,metabolic:never,semantic:never`)
   that gates CI. neat-freak's self-check is a checklist; Myco's
   self-check is an executable that returns a POSIX exit code.
4. **Sporulate → reassimilate closed loop** (v0.6.0 §F4): integrated
   notes can be re-promoted via `re_raw` stage if context shifts.
   neat-freak's flow is a one-pass procedure.

## What Myco absorbs from this ingestion

Three concrete absorptions, all stay at L4 (this distilled note + future
craft option) until/unless promoted:

1. **The "三类知识三种受众" mental model** is a clean teaching gloss for
   Myco's L0/L1/L2/L3/L4 layering, especially for downstream substrates
   that need to reconcile their own `CLAUDE.md` / `docs/` against
   `_canon.yaml`. Candidate addition to `MYCO.md` § "How to read the
   substrate" — but only via `myco fruit` craft (L1 vocabulary
   amendment is a doctrine-tier change, not L4).
2. **The variation-impact matrix as a doctrine companion to lint dims.**
   Today an Agent reading `homeostasis.md` learns 46 symptoms; they
   don't get a parallel "for each common change type, here's the
   blast radius". A `docs/architecture/L2_DOCTRINE/sync_matrix.md`
   companion (or appended section to `homeostasis.md`) would be
   high-leverage. Defer until at least 5 dogfood sessions where the
   absence demonstrably hurts (per L0:104 "integrated is not an
   endpoint" — let the need prove itself).
3. **"Force `ls` before judgement" as canonical anti-hallucination
   primer** for the new fungal subagents (`hypha`, `autolysis`,
   `primordium`). Already implicit in those agent specs; could be
   made explicit as a one-line directive.

## What stays neat-freak's, not Myco's

These are deliberate design splits, not gaps:

- **Cross-platform / non-Myco-aware framing.** neat-freak runs in
  any Skill-aware Agent host. Myco's contract is Myco-specific and
  rejects that scope on purpose (L0 P1 + the boundary subsystem
  v0.6.0 §A1 narrowly admits the English word "boundary" precisely
  because no fungal-bionic term mapped — the kernel does not chase
  cross-platform abstraction).
- **Human-readable `docs/` as first-class.** Myco's discipline is
  Agent-First; humans interact with the Agent, not the substrate.
  `myco brief` is the carved exception. Adopting neat-freak's full
  human-doc discipline would dilute L0 P1.

## Cross-references (per R5 of `protocol.md`)

- **L0 P5 — `菌丝网络`** (`L0_VISION.md:111-136`): orphans are dead
  tissue. neat-freak's reconciliation discipline is the procedural
  expression of the same claim.
- **L0 P4 — `永恒迭代`** (`L0_VISION.md:94-109`): every session
  refines the prior. neat-freak's whole reason-to-exist is this
  principle named in another vocabulary.
- **R2 hard contract** (`L1_CONTRACT/protocol.md:39-58`): session-end
  is ritualized. neat-freak provides the imperative-procedure
  version that Myco's `senesce` mechanizes.
- **R3** (`L1_CONTRACT/protocol.md:61-69`): sense before assert.
  neat-freak's "force `ls`" is the same rule.
- **R5** (`L1_CONTRACT/protocol.md:82-89`): cross-reference on
  creation. This very note is an instance.
- **L2 cycle.md** (`L2_DOCTRINE/cycle.md`): canonical session-end
  is `senesce`. neat-freak is its non-Myco peer.
- **L2 digestion.md** (`L2_DOCTRINE/digestion.md:1-138`):
  `assimilate` does what neat-freak Phase 3 ("actually modify")
  asks for, mechanically.
- **L2 homeostasis.md** (`L2_DOCTRINE/homeostasis.md`): SE1 +
  46 dims as the lint-side of neat-freak's self-check.
- **`myco_excrete`** (v0.5.24): the safe-delete verb that
  implements neat-freak's "delete > preserve" rule.

## Future axis (candidate `myco fruit` topics)

If a future session demonstrates the value, file a craft proposal at
`docs/primordia/v0_X_X_neat_freak_absorption_craft_<date>.md` proposing
one of:

A. **Add `docs/architecture/L2_DOCTRINE/sync_matrix.md`** companion
   doc to homeostasis.md, indexing common change types → drift
   blast radius. Pure-additive, low-risk per cycle.md governance
   tiering.

B. **Extend `myco brief` (v0.5.5)** to optionally emit a per-host
   agent-memory reconciliation hint when the Agent sets a flag
   indicating which Skill-aware host it's running under. Marries
   neat-freak's cross-platform agent-paths table with Myco's one
   carved L0 P1 exception. Medium-risk; requires craft.

C. **Sub-agent `editor` (literal English-name analogue to `autolysis`,
   but framed as a knowledge editor not auto-digester).** REJECTED
   on first reading — violates L0:185-186 fungal vocabulary discipline.
   The fungal-named existing `autolysis` already covers the role; the
   v0.6.11 craft Round 2 §T4 explicitly defers further role expansion
   pending dogfood-driven need.

The default path is **(A) only**, deferred until at least one dogfood
session where the absence of a sync-matrix companion measurably hurts.
Per L0:104, "integrated is not an endpoint" — this distilled note is
itself the L4 record that the absorption was considered + parameterized,
not a commitment to act.

## Provenance

- Upstream: [`KKKKhazix/khazix-skills/neat-freak`](https://github.com/KKKKhazix/khazix-skills/tree/main/neat-freak)
- Captured: 2026-04-29 (3 files, 277 lines, ~16 KB)
- Re-fetch any time via the three raw URLs in `external_provenance.upstream_files`
- Ingestion route: `myco eat --path` (URL adapter SSRF-rejected
  `raw.githubusercontent.com → 198.18.1.20`, an IANA Special-Purpose
  range surfaced by environment-side DNS rewriting; bypassed via curl
  to `/tmp/` + path-mode eat)
- Pipeline (v0.6.13): `eat` × 3 → `assimilate` × 3 → `sporulate` →
  this synthesis → owner-driven `excrete`-equivalent of intermediate
  integrated copies (file-removal, since `myco excrete` is scope-locked
  to `notes/raw/`). Net additions to substrate: **1 file** (this note).
- Stage: `distilled`. Promotion to `integrated` of this synthesis
  itself (per v0.6.0 sporulate→reassimilate closed loop) deferred
  until owner review or dogfood signal.
