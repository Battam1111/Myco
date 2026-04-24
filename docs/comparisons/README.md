# Myco vs alternatives

Honest comparison against the five closest tools in the
"agent memory / long-term context" space: **LangChain memory**,
**MemGPT / Letta**, **Mem0**, **Cognee**, and **LlamaIndex
memory**. No "we win at everything" narrative. Each tool
solves a real problem; Myco solves a different one.

Use this doc to decide: do you want Myco, or do you want one of
the others (or both)?

## One-sentence positioning for each

| Tool | Primary target |
|---|---|
| **LangChain memory** | Retrieval-in-chain: hand relevant chunks to a chain on each call |
| **MemGPT / Letta** | Tiered memory (main context + archival) with recall hooks; pioneered OS-inspired memory paging for LLMs |
| **Mem0** | Managed memory API: POST/GET memories, they handle the vector DB, pay-per-call |
| **Cognee** | Knowledge graph + vector DB dual store; document-heavy use cases |
| **LlamaIndex memory** | Chat-history management inside a LlamaIndex pipeline; query + index abstractions |
| **Myco** | Self-validating filesystem substrate + verb surface + lint system for long-running agents |

## The scatterplot

```
                    retrieval-optimised ← → drift-resistance-optimised

 managed-service  │ Mem0
                  │
                  │
                  │
                  │                                         Myco
 self-hosted      │ Letta      LlamaIndex-mem
                  │            LangChain-mem
                  │                             Cognee
                  │
```

Myco is in the upper-right: self-hosted, drift-resistance-over-
retrieval-latency. It's the corner of the design space nobody
else is sitting in. Every other tool prioritises retrieval
quality over substrate integrity.

## Detailed comparisons

### Myco vs LangChain memory

| Axis | LangChain memory | Myco |
|---|---|---|
| Lifetime | Tied to chain object | Tied to filesystem (survives every process lifetime) |
| Retrieval | Embedding similarity | Explicit cross-reference + keyword (`myco sense`) |
| Drift detection | None built-in | 25 lint dimensions |
| Governance | None | `fruit` → `winnow` → `molt` 3-round loop |
| Multi-host | One-chain-one-memory | One filesystem, many hosts |
| Churn | Fast (LangChain minor bumps frequently) | Slow (R1-R7 contract stable across 10+ molts) |

**Pick LangChain memory when**: memory lives inside one chain +
retrieval-per-call is the primary access pattern + you're OK
with memory dying when the chain dies.

**Pick Myco when**: memory needs to outlive chain rewrites +
cross-session/cross-project continuity matters + you want
mechanical checks for substrate coherence.

**Use both when**: LangChain is your orchestration layer;
Myco is the persistent store underneath. LangChain chains can
call Myco's MCP tools or shell out to its CLI.

### Myco vs MemGPT / Letta

| Axis | MemGPT / Letta | Myco |
|---|---|---|
| Core abstraction | Memory paging (main / archival) | Filesystem graph + 19 verbs |
| Retrieval | Embedding + recall triggers | Graph traversal + keyword grep |
| Governance | Implicit (the agent decides when to page) | Explicit (`fruit` / `winnow` / `molt` loop) |
| Graph | Not primary, memory is a store | Primary, substrate IS a graph |
| Extension | Agent types + tools | Entry-points-driven dims + adapters + verbs |

MemGPT's tiered-memory paper was one of Myco's inspirations;
the raw → integrated → distilled pipeline is similar. Where
Myco goes further: the contract layer. MemGPT has memories;
Myco has memories + a contract that explicitly describes how
memories may evolve, enforced by lint.

**Pick Letta when**: you want a polished "give my LLM a long
context window" product with multi-agent support.

**Pick Myco when**: you want the agent to maintain the kernel
that maintains the memory: editable by default, doctrine-
first, self-validating.

### Myco vs Mem0

| Axis | Mem0 | Myco |
|---|---|---|
| Deployment | Managed API (SaaS) | On-disk, self-hosted |
| Cost | Per-call | Zero (infrastructure only) |
| Data locality | Their cloud | Your filesystem |
| Lock-in risk | "Can I export if they pivot?" | MIT-licensed, all data is markdown+YAML |
| Integration | HTTP client | CLI + MCP server |

**Pick Mem0 when**: zero-config memory + can ship data to their
cloud + per-call cost is acceptable.

**Pick Myco when**: you want to own the substrate entirely +
no egress cost + MIT-licensed transparency.

### Myco vs Cognee

| Axis | Cognee | Myco |
|---|---|---|
| Primary target | Document knowledge graphs (RAG++) | Agent substrate |
| Graph source | LLM-extracted entities + vector similarity | Explicit cross-refs (canon `_ref` fields, markdown links, AST imports) |
| Determinism | Embedding-based (probabilistic) | Reference-based (deterministic) |
| Lint | None | 25 dimensions |
| Use case fit | Doc-heavy RAG | Long-session agent memory |

Cognee is excellent for document-heavy RAG. Myco's graph is
not embedding-derived, so the two serve different targets.

**Pick Cognee when**: your use case is "ingest thousands of
docs and ask questions against them" + you want a graph view
in addition to vector retrieval.

**Pick Myco when**: your use case is "an agent that grows a
knowledge base across months" + you want the graph to be
explicit + auditable.

### Myco vs LlamaIndex memory

| Axis | LlamaIndex memory | Myco |
|---|---|---|
| Scope | Chat-session / pipeline | Substrate-wide |
| Integration | Inside LlamaIndex pipeline | Standalone CLI + MCP server |
| Persistence | Optional (via storage backends) | Default (filesystem) |
| Graph | Not primary | Primary |

LlamaIndex's memory abstractions handle chat-history well.
Myco's scope is wider. A substrate outlives any single
LlamaIndex session.

**Pick LlamaIndex memory when**: you're already on LlamaIndex
+ chat-history + RAG pipelines are the stack.

**Pick Myco when**: memory is cross-session, cross-project,
cross-host.

## When Myco is wrong

Myco is a badly-matched tool when:

1. **Your memory fits in one LLM context window.** A session
   with < 500 KB of material works great with vanilla context.
   Myco's overhead only pays off at scale.
2. **You need sub-100 ms retrieval latency.** Myco's
   `myco sense` is grep. Fast for < 100 MB substrates,
   slower than optimized vector DBs for GB-scale corpora.
3. **You want a managed service.** Myco is self-hosted; if the
   operator doesn't want to install anything, Mem0 or Letta's
   hosted tier is better.
4. **Your agent is single-session and stateless by design.**
   Persistence is the whole point; a stateless agent doesn't
   need it.

If any of the above applies, use the tool in the right column
of the relevant comparison table above. Myco is not universal.

## The honest table

| Strength | Mem0 | Letta | LangChain | Cognee | LlamaIndex | **Myco** |
|---|---|---|---|---|---|---|
| Retrieval latency | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ |
| Drift resistance | ⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ |
| Self-host | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Graph determinism | ⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| Multi-host | ⭐⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ |
| Contract governance | n/a | n/a | n/a | n/a | n/a | ⭐⭐⭐ |

Myco wins on drift-resistance, graph determinism, multi-host
operation, and contract governance, because those are the axes
it was built to optimise. It loses on retrieval latency because
it doesn't try. Pick on your axis.

## If you're still deciding

Read the [L0_VISION.md](../architecture/L0_VISION.md)'s five
root principles. If those five sentences describe what you
want from your agent's memory layer, Myco is a fit. If any
one of them strikes you as unnecessary structure, use one of
the simpler tools above. You'll be happier.

Myco is opinionated on purpose. That's not for everyone.
