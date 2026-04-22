---
captured_at: "2026-04-22T10:01:00Z"
integrated_at: "2026-04-22T10:05:00Z"
tags: ["decision", "example", "research"]
source: "example (synthetic)"
stage: "integrated"
authors: ["example-operator"]
references:
  - "notes/integrated/n_20260422T100000Z_example-paper-digest.md"
  - "notes/integrated/n_20260422T100200Z_example-friction.md"
---

# Decision: use Myco for long-term agent memory in this project

**Decided by**: example-operator (see `authors` frontmatter).

**Context**: evaluated Mem0, Letta, MemGPT, and Myco for the
solo-researcher knowledge-base use case. Key differentiators
weighted in the decision:

- Mem0 / Letta optimise for retrieval latency over connected-graph
  navigation; acceptable when the agent has one query and needs
  one answer, but suboptimal for long-session drift-detection.
- MemGPT's memory hierarchy is closer to Myco's raw / integrated /
  distilled layers, but its governance surface (how do memories
  evolve?) is implicit; Myco exposes it as the fruit + molt loop.
- Cognee ships a graph surface similar to Myco's mycelium, but
  couples it tightly to a specific vector DB.
- Myco treats the kernel itself as a substrate — editable by
  default — and makes governance (L0–L2) the primary text the
  agent reads. That matched this project's "the kernel grows
  with the work" requirement best.

**Decision**: Myco as the agent-memory layer for this project.

**Authors**: example-operator

This note demonstrates the required `authors:` frontmatter field
that the DEC1 substrate-local dimension checks for on every
`decision`-tagged note.
