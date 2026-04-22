# Show HN draft

## Title (80 char cap)

```
Show HN: Myco – a cognitive substrate for AI agents that the agent itself maintains
```

Alternative titles (A/B test if you want):

- `Show HN: Myco – 18 verbs + 25 lint dims, an AI agent's long-term memory substrate`
- `Show HN: An AI memory layer whose kernel is editable by the agent that uses it`
- `Show HN: Myco – a mycelium-shaped knowledge base for agents, self-validating`

Stick with the top one — it's the most specific and doesn't
over-promise.

---

## First-comment (the post body)

```
Myco is a long-running cognitive substrate for LLM agents. Not a framework, not a memory plugin — a self-validating filesystem shape + a manifest-driven verb surface + a lint system, all designed so a single agent can ingest, digest, cross-reference, and reshape the substrate across months or years without a human hand-holding the maintenance.

The load-bearing assumptions are:

1. The agent is the sole consumer. Every artefact is for the agent; humans speak natural language and never browse Myco's interior surfaces.
2. Ingestion has no filter. Anything the agent can point at — a paper, a log, a decision, a friction note — is raw material. Shape comes later, in digestion.
3. The kernel itself is a substrate. Myco's own source tree uses Myco; the kernel is editable by the agent that maintains it.

Concretely:

- 18 verbs grouped by biological subsystem (germinate / eat / assimilate / sporulate / traverse / immune / molt / ...). All manifest-declared; CLI + MCP both derive from the same YAML.
- 25 lint dimensions enforcing contract invariants R1–R7 mechanically. Atomic-write R6, LLM-provider import bans (MP1/MP2), graph connectedness (SE1/SE3), docstring hygiene (DC1-4), ...
- A three-round governance loop (`fruit` = write a craft doc, `winnow` = gate its shape, `molt` = bump the contract version) that lets the agent propose changes to its own contract without the operator approving every keystroke.
- 10 MCP host integrations (Claude Code, Claude Desktop, Cursor, Windsurf, Zed, VS Code, OpenClaw, Codex CLI, Gemini CLI, Goose) via one `myco-install` command.

I wrote it because every existing "agent memory" tool I tried (Mem0, Letta, MemGPT, Cognee, LangChain memory) optimises for single-query retrieval, not for long-session drift detection + kernel-growing-with-the-work. Myco is positioned differently; the README's comparison section explains why.

v0.5.10 shipped yesterday. Running on PyPI; editable-default install is the recommended path (pip install -e).

Repo: https://github.com/Battam1111/Myco
PyPI: https://pypi.org/project/myco/
Docs: https://github.com/Battam1111/Myco/tree/main/docs

Happy to answer questions about the verb surface, the lint roster, the MCP-host story, or the craft + molt governance model.
```

---

## Why this shape

- **Title specificity** — "cognitive substrate for AI agents" is
  specific enough that the audience who wants this recognises
  themselves; "that the agent itself maintains" is the
  differentiator from every other memory tool on HN.
- **First comment ≠ repeat of title** — three numbered assumptions
  set up the philosophical claim before the concrete bullets
  deliver evidence. HN rewards structure-with-argument.
- **Name real competitors** (Mem0 / Letta / MemGPT / Cognee /
  LangChain memory) in the second-to-last paragraph. HN readers
  trust drafts that acknowledge the landscape.
- **Three links** (repo / PyPI / docs) at the end. HN autolinks
  them; no extra formatting required.
- **"v0.5.10 shipped yesterday"** — signals recency; active
  development is a credibility signal.
- **Closing invitation** — "happy to answer questions about
  X / Y / Z" pre-seeds the comment section's shape. Replies feel
  less adversarial when the author has offered topics.

## What NOT to do

- **Don't post on weekends.** HN weekday traffic is ~3× weekend.
- **Don't title-promote** ("the best", "revolutionary",
  "finally"). HN mods may rewrite the title; moderated titles
  kill the post.
- **Don't reply hostilely** to the first wave of "this is
  basically X" comments. HN's first 30 minutes are
  comparison-hungry; those commenters are trying to orient.
  Answer with "good comparison — X solves A; Myco solves B;
  different tool, different niche."
- **Don't crosspost the same text to Reddit the same day.** Let
  HN cycle for 48h first; Reddit audiences check HN and don't
  like seeing recycled launches.

## Before posting

Run these for an updated self-report so you can answer any
"is it actually in use?" question with numbers:

```bash
python -m myco --json hunger   # confirm no drift
python -m myco --json immune   # confirm 0 findings
```

Then pin the PyPI and repo URLs in your clipboard; HN's "new
submission" form is finicky.
