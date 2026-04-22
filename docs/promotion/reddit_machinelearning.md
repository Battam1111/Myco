# r/MachineLearning post draft

> **Note**: r/MachineLearning is stricter than most ML subs. Posts
> marked `[P]` (project) need to be substantive + technical. If
> you can link to an arXiv-style write-up, that raises the bar the
> post can clear; without one, submit with a self-aware tone.

## Title

```
[P] Myco — a self-validating cognitive substrate for long-running LLM agents (25 lint dims, AST-derived mycelium graph, no vector DB)
```

## Body

```
I've been building Myco (https://github.com/Battam1111/Myco), a long-lived filesystem shape + lint system + verb surface for LLM agents that persists across sessions, projects, and model versions. Posting here because the "agent memory" space has diverged into retrieval-latency optimisation (Mem0, Letta) and MemGPT-style tiered-context, and Myco takes a third shape that might interest this audience.

Design thesis

Most agent-memory systems optimise a retrieval metric (precision@k, latency, relevant-chunks-returned). Myco optimises a different variable: drift resistance under continuous edit. After six months of unstructured-text-file memory the failure mode isn't "the agent couldn't find the right chunk" — it's "the substrate contradicts itself and nobody noticed". Myco's primary mechanism for this is a 25-dimension lint system enforced mechanically:

- 18 mechanical dims (canon shape, write-surface, subsystem presence, docstring hygiene, ...)
- 1 shipped dim (package-version sync)
- 3 metabolic dims (raw-backlog, integration progress)
- 3 semantic dims (graph connectedness, canon ↔ reality drift, self-cycles) + 1 rule-reference dim

Every dim is one file under src/myco/homeostasis/dimensions/; registration is entry-points-driven so third-party substrates add their own lint rules without forking.

Graph representation

The mycelium graph is not embedding-derived. Nodes are substrate-relative paths; edges come from four explicit sources:

1. YAML `_ref`-suffixed fields in _canon.yaml
2. Frontmatter `references:` lists in notes/**/*.md
3. Markdown `[text](path)` links in markdown bodies (fenced code skipped)
4. AST import edges between Python modules under src/**/*.py + docstring doc-ref edges from module docstrings

That makes the graph deterministic + debuggable — "why did the agent miss this connection?" becomes "which of the four sources should have carried the edge?" instead of "which embedding-similarity threshold needs tuning?".

Contract evolution

The contract itself is first-class mutable. Three verbs compose the governance loop:

- fruit: scaffolds a three-round craft doc (claim → rebuttal → revision → counter-rebuttal → convergence) under docs/primordia/
- winnow: gates the craft's shape against a protocol (all five rounds present + not boilerplate + frontmatter well-formed)
- molt: mutates _canon.yaml's contract_version in lockstep with synced_contract_version, appends to docs/contract_changelog.md, increments waves.current

v0.5.10 is 10 molts past v0.5.0 (2026-04-17). Every molt has a craft doc trail; no silent contract drift.

Concrete numbers

- 757 pytest passing
- 0 immune findings on the self-substrate (v0.5.9 + v0.5.10 cleanup baseline)
- 10 MCP host integrations via one `myco-install` command
- 3 exit-code bands (0-2 lint-driven, 3 operational, 4 substrate-not-found, 5 canon-schema)

What this is not

- Not a paper with formal evaluations. It's engineering.
- Not benchmarked against Mem0/Letta/MemGPT on a shared metric; the target variables differ (drift resistance vs retrieval latency).
- Not production-battle-tested beyond my own use. Early 2026, pre-adoption.

Repo + PyPI + doctrine:
- https://github.com/Battam1111/Myco
- https://pypi.org/project/myco/
- https://github.com/Battam1111/Myco/tree/main/docs/architecture

Questions / critiques welcome — especially on where the 25-dim surface is over-engineered or under-engineered for the drift-resistance target.
```

---

## Why this shape

- **`[P]` tag** is mandatory for project posts; without it
  moderators will flag.
- **"Design thesis" → "Graph representation" → "Contract
  evolution" → "Concrete numbers" → "What this is not"** is the
  r/MachineLearning-friendly structure. Thesis first, evidence
  second, honest-limits last.
- **The "what this is not" section** matters more here than on
  r/LocalLLaMA. Saying "not benchmarked" + "not production-
  battle-tested" preempts the predictable "where's the
  evaluation?" critique without defensiveness.
- **No marketing superlatives.** This sub will downvote anything
  that feels pitch-y.
- **Direct link to doctrine tree** — readers who want to verify
  the claims can click through to the actual L0/L1/L2 markdown.

## Reality check

r/MachineLearning engagement on agent-tooling posts is hit or miss.
If the post gets < 20 upvotes in the first hour, let it decay;
don't crosspost or bump. Not every audience is the right audience.
