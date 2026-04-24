---
name: myco-substrate
description: >
  Work with a Myco cognitive substrate, which is any project directory with
  `_canon.yaml` and `MYCO.md` at its root. Trigger when the workspace contains
  `_canon.yaml` (it IS a Myco substrate); the user mentions "substrate",
  "Myco", or any of the 19 fungal verbs (germinate / hunger / eat / sense /
  forage / excrete / assimilate / digest / sporulate / traverse / propagate /
  immune / senesce / fruit / molt / winnow / ramify / graft / brief); a prior
  tool response's `substrate_pulse` referenced Myco; the user asks about
  agent memory, long-term context, cross-session state, or agent-first
  cognitive architecture in the context of a project that has `_canon.yaml`.
  Myco is NOT a memory tool and NOT a RAG framework, so skip this skill when
  the user wants vector retrieval, LangChain-style pipelines, or ephemeral
  chat-scoped memory.
user-invocable: false
---

# Myco: Agent-First Cognitive Substrate

## What Myco is (get this right)

Myco is **not** a "long-term memory system", **not** a vector DB, **not** a
managed cloud service, **not** a framework that wraps an LLM call. Those
framings are wrong and will mislead your tool use.

Myco is a **living cognitive substrate** for the agent: a markdown + YAML
filesystem rooted at a project directory, where the agent reads, writes,
digests, and reshapes knowledge over time. The user speaks. You listen and
act. Between the user's turns you run a *metabolism* on the substrate:
ingest raw signal, digest into integrated knowledge, circulate via graph
traversal, immune-check against drift, evolve the substrate's own shape when
the work outgrows the old form.

The substrate is the agent's **home**, not a tool the agent calls.

## The 19 verbs, grouped by subsystem

- **Germination.** `myco_germinate` starts a fresh substrate in a target
  directory.
- **Ingestion.** `myco_hunger` (report what the substrate is missing),
  `myco_eat` (absorb raw material: text, path, URL), `myco_sense`
  (keyword search across the substrate), `myco_forage` (list ingestible
  files under a path), `myco_excrete` (safely delete a raw note by
  moving it to `.myco_state/excreted/` with an audit tombstone).
- **Digestion.** `myco_assimilate` (promote raw notes to integrated),
  `myco_digest` (promote one specific raw note), `myco_sporulate`
  (concentrate integrated notes into a dispersible proposal).
- **Circulation.** `myco_traverse` (walk the graph and report
  connectedness), `myco_propagate` (publish integrated/distilled
  content to a downstream substrate).
- **Homeostasis.** `myco_immune` (run the 25-dimension lint with
  optional `fix=True`).
- **Cycle.** `myco_senesce` (session dormancy; `quick=True` at abrupt
  exits), `myco_fruit` (scaffold a 3-round primordia proposal doc),
  `myco_winnow` (gate the proposal against craft-protocol),
  `myco_molt` (ship a contract-version bump),
  `myco_ramify` (scaffold new dimension / verb / adapter),
  `myco_graft` (enumerate / validate / explain substrate-local plugins),
  `myco_brief` (human-facing markdown rollup of substrate state).

## Seven hard contract rules (R1 through R7)

Every session is governed by:

- **R1 Boot ritual.** Call `myco_hunger` as the first substantive action
  of every session.
- **R2 Session-end.** Call `myco_senesce` before compaction or at session
  end. Prefer `quick=True` on abrupt exits with a tight kill budget.
- **R3 Sense before assert.** Call `myco_sense` before asserting a
  substrate fact. Your training memory is not a source.
- **R4 Eat insights.** Capture decisions, frictions, and insights via
  `myco_eat` the moment they occur. Don't wait for session end.
- **R5 Cross-reference.** Orphan files are dead knowledge. Link on
  creation via `references:` frontmatter or `[text](path)` markdown
  links.
- **R6 Write surface.** Write only to paths matched by
  `_canon.yaml::system.write_surface.allowed`. Writes elsewhere are
  mechanically refused with `WriteSurfaceViolation` (exit 3).
- **R7 Top-down layering.** L0 (vision) > L1 (contract) > L2 (doctrine)
  > L3 (implementation) > L4 (substrate data). Implementation never
  overrides contract.

Full rule text: `docs/architecture/L1_CONTRACT/protocol.md`.

## How to read the pulse

Every Myco MCP tool response carries a `substrate_pulse` object. **Read it
on every call.** Fields:

- `substrate_id`: the slug identifying which substrate answered.
- `contract_version`: the R1 through R7 contract version in force.
- `rules_hint`: which rule to honor NEXT. Starts at R1 (hunger),
  escalates to R3 (sense-before-assert) once hunger is called, etc.
- `project_dir_source`: **which level of the resolution chain
  answered**. One of: `kwargs.project_dir`, `mcp.roots/list`,
  `env.MYCO_PROJECT_DIR`, `env.CLAUDE_PROJECT_DIR`, `Path.cwd()`.
- `resolved_project_dir`: the filesystem path Myco actually used.

**If `project_dir_source` is anything other than `kwargs.project_dir`
or `mcp.roots/list` AND the user is working on a specific workspace
folder, pass `project_dir="<absolute path>"` in your next tool call's
kwargs.** Claude Desktop / Cowork does not always forward workspace
roots via MCP's `roots/list`, so explicit pinning keeps routing
correct.

## Five root principles (Myco L0)

- **Only For Agent.** No surface is authored for a human reader; every
  artifact is primary material for you, the agent. `myco_brief` is the
  single carved exception (human-facing rollup).
- **永恒吞噬 (Eternal Devouring).** The substrate's intake has no filter.
  Anything the user can point at is fair game for `myco_eat`.
- **永恒进化 (Eternal Evolution).** Canon, lint dimensions, verbs, even
  the R1 through R7 contract itself are mutable through the governed
  `fruit` → `winnow` → `molt` craft loop.
- **永恒迭代 (Eternal Iteration).** `integrated` is a state, not an
  endpoint. Today's conclusion is tomorrow's raw material.
- **万物互联 (Mycelium Network).** Every note, canon field, doctrine
  page links to every other by traversal. Orphans are dead tissue.

## First-call checklist

When you detect you are inside a Myco substrate:

1. **Call `myco_hunger` first.** This is R1. No exceptions.
2. **Read the `substrate_pulse` in the response.** It tells you where
   you are (`substrate_id`, `resolved_project_dir`) and which rule to
   honor next.
3. **If `resolved_project_dir` does not match the user's workspace**,
   pass `project_dir="<workspace path>"` in every subsequent tool
   call until pulse confirms it.
4. **If `substrate_id` is `(no substrate, workspace detected)`**, the
   user's workspace has no `_canon.yaml` yet. Relay the `rules_hint` to
   the user and ask if they want you to call `myco_germinate`.

## Multi-project pattern

On hosts without `roots/list` support (e.g. Cowork today, per observed
behavior), Myco cannot auto-detect which project the user means. Two
mitigation paths:

- **Per-call override**: every Myco tool call kwargs accepts
  `project_dir` as a first-class argument. Pass it when you know.
- **Registry lookup**: call `myco_graft --list-substrates` (or the
  equivalent MCP kwargs `{"list_substrates": true}`) to see every
  substrate the user has registered on this machine. Pick the
  matching one by slug.

## What NOT to do

- **Do not** characterize Myco as "memory infrastructure" or a
  "long-term memory tool" in user-facing explanations. That framing
  is wrong and Myco explicitly rejects the category (see
  `docs/comparisons/README.md`).
- **Do not** write files outside the workspace's
  `_canon.yaml::system.write_surface.allowed`. That is R6.
- **Do not** assert substrate facts from training memory. Call
  `myco_sense` first. That is R3.
- **Do not** auto-germinate silently. If workspace has no substrate,
  ASK the user before calling `myco_germinate`.

## Deeper reading (optional)

- `L0_VISION.md`: five root principles, verbatim.
- `L1_CONTRACT/protocol.md`: R1 through R7 full text.
- `L2_DOCTRINE/`: one doctrine page per subsystem.
- `src/myco/surface/manifest.yaml`: the single source of truth for
  the 19 verbs' arg shapes. Both CLI and MCP tool surface derive from
  it.
