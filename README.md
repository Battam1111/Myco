<div align="center">

<img src="assets/logo_dark_280.png" alt="Myco" width="200">

# Myco

**The knowledge system that digests itself so you don't have to.**

[![PyPI](https://img.shields.io/badge/PyPI-v0.2.0-blue?style=for-the-badge)](https://pypi.org/project/myco/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Lint](https://img.shields.io/badge/Lint-23%2F23%20green-brightgreen?style=for-the-badge)](#architecture)

[The Problem](#the-problem) · [What Myco Does](#what-myco-does) · [Why It's Different](#why-its-different) · [Architecture](#architecture) · [Quick Start](#quick-start) · [Contributing](#contributing)

**Languages:** English (canonical) · [中文](README_zh.md) · [日本語](README_ja.md)

</div>

---

## The Problem

You used LangChain in 2024. Someone told you LangGraph was better. You switched. Then it was CrewAI. Then DSPy. Then AutoGen. Then some new framework dropped on a Tuesday and your Discord lit up with people saying everything you just learned was already obsolete.

You mass-starred repos. 50 followed, 3 actually read. You bookmarked articles. 200 saved, maybe 10 opened twice. You kept notes -- Notion, Obsidian, a markdown folder you swore you'd organize. 500 notes. Last sorted: three months ago. Probably longer.

Here's what nobody talks about: **everything you saved is quietly rotting.**

That API pattern you noted three weeks ago? The library released a breaking change. That "best practice" from last month's top HN post? The community already moved on. That architecture doc you spent a weekend writing? Two of its assumptions are wrong now, and nothing is telling you which two. Your knowledge isn't growing. It's decaying. And the more you save, the more you're burying the signal under dead weight you'll never go back and check.

Now imagine a different version of yourself. One who does nothing. No note-taking. No tool comparison. No paper chasing. No "getting organized." You just talk to your AI -- about your project, your problems, your ideas. You go to sleep. You wake up. You talk some more. Six months pass. And your AI is sharper, more contextual, more *yours* than any amount of manual curation could have produced. Not because you worked harder. Because something underneath was doing the work for you -- digesting, compressing, verifying, throwing out what went stale, and quietly getting smarter while you weren't looking.

That something is Myco.

---

## What Myco Does

Myco is an **Autonomous Cognitive Substrate** for AI agents. Your agent is a CPU -- raw compute, no persistence. Myco is everything else: the memory, the filesystem, the operating system. And the OS upgrades itself.

- **Devour** -- Anything you mention in conversation -- a debug trick, a design decision, a hard-won insight -- gets captured as a durable note. Zero friction. You talk; the substrate eats.
- **Self-check** -- A 23-dimension immune system continuously verifies the substrate against contradiction, staleness, orphaned references, and structural drift. Knowledge that stops being true gets flagged before it poisons a decision.
- **Excrete** -- Most knowledge systems only grow. Myco is the only one that actively *ejects* what has decayed, been superseded, or stopped earning its place. A digestive tract without an outlet is a tumor.
- **Evolve** -- The substrate doesn't just store knowledge -- it rewrites its own rules. Lint thresholds, compression strategies, even the evolution engine itself mutate and adapt. You are the selection pressure.
- **Connect** -- Knowledge doesn't sit in isolation. The link graph tracks how ideas reference each other. Orphans are detected. Clusters emerge. The substrate knows its own shape.
- **Just talk** -- No tagging rituals. No filing systems. No weekly reviews. You talk to your agent. The substrate does the rest. Six months later, it knows your project better than you do.

---

## Why It's Different

Every AI memory system you've seen falls into one of two categories. Myco is neither.

| | Memory-as-a-Service | Knowledge Compilation | **Myco** |
|---|---|---|---|
| **Examples** | Mem0, Zep, LangMem | Karpathy LLM Wiki | **Knowledge Organism** |
| **Core verb** | Store and retrieve | Compile and index | **Metabolize** |
| **Knowledge lifecycle** | None. Data enters, sits, gets queried. | Ingest and lint. No lifecycle. | Full pipeline: raw -> digesting -> extracted -> integrated -> excreted |
| **Self-verification** | None | Basic contradiction checks | 23-dimension immune system (L0-L22) |
| **Self-evolution** | None | Static schema | Craft protocol evolves the substrate's own rules |
| **Excretion** | Never. Storage grows forever. | Never. | Active: dead-knowledge detection, auto-pruning, temporal expiry |

**Memory services store. Knowledge compilers compile. Myco metabolizes.**

A system that ingests but never excretes is not a living knowledge base -- it is a tumor. Myco treats knowledge as having a full lifecycle: born, digested, verified, compressed, and -- when it stops earning its place -- excreted. The biological vocabulary is not decoration. It is the architecture.

---

## Architecture

```
         You
          |
          | (just talk)
          v
   ┌──────────────┐
   │   LLM Agent  │  <-- CPU: raw compute, no RAM
   └──────┬───────┘
          │ 21 MCP tools + CLI
          │ (eat / digest / lint / hunger ...)
   ┌──────┴───────┐
   │  Myco Kernel │  <-- OS: metabolism, self-model,
   │     (OS)     │      lint, evolution engine,
   │              │      metabolic inlet
   └──────┬───────┘
          │
    ┌─────┼─────┐
    v     v     v
 [Proj] [Proj] [Proj]   <-- Instances: wiki / notes / log / canon
   A      B      C
```

**Kernel** is the project-agnostic cognitive OS: shared code, shared lint engine, shared evolution protocol. **Instances** are your project directories -- applications running on that OS. Kernel upgrades flow downstream. Friction discovered inside instances flows back upstream. This is not a metaphor. It is literally how Myco is structured.

All evolution is **non-parametric**: text, structure, and lint rules on disk. No model weights are ever touched. This is why Myco works across agent vendors, survives model swaps, and accumulates value in exactly the medium LLM agents are best at manipulating.

---

## Quick Start

```bash
git clone https://github.com/Battam1111/Myco.git
cd Myco && pip install -e ".[mcp]"
myco init --auto-detect my-project
```

Three commands. Auto-detects your environment — Claude Code · Cursor · VS Code · Codex · Cline · Continue · Zed · Windsurf · Cowork — configures everything in one shot.

Editable install — the entire system is yours to rewrite, including the engine itself. Don't want to touch it? That's fine. It evolves on its own.

The CLI alone is enough. The MCP layer is what turns capture into a reflex. Call `myco_hunger(execute=true)` at session boot -- the substrate self-heals.

### The biological vocabulary

Myco's verbs are metabolic on purpose. Here is the plain-English map:

| Myco verb | What it does | CLI | MCP tool |
|---|---|---|---|
| `eat` | Capture content as a durable note | `myco eat` | `myco_eat` |
| `digest` | Move a note through its lifecycle (raw -> extracted -> integrated -> excreted) | `myco digest` | `myco_digest` |
| `evaluate` | Score a raw note for substrate fit | `myco evaluate` | (CLI only) |
| `extract` | Pull the load-bearing structure out of a digesting note | `myco extract` | (CLI only) |
| `integrate` | Wire an extracted note into the existing knowledge body | `myco integrate` | (CLI only) |
| `compress` | Synthesize N notes into 1 extracted note with audit trail | `myco compress` | `myco_compress` |
| `uncompress` | Reverse a compression, restore inputs | `myco uncompress` | `myco_uncompress` |
| `prune` | Auto-excrete dead-knowledge notes | `myco prune` | `myco_prune` |
| `view` | Read notes with filters (tracks view count) | `myco view` | `myco_view` |
| `lint` | 23-dimension substrate health check | `myco lint` | `myco_lint` |
| `correct` | Apply auto-fixes from a prior lint pass | `myco correct` | (CLI only) |
| `forage` | Manage external source material | `myco forage` | `myco_forage` |
| `inlet` | Ingest external content with provenance tracking | `myco inlet` | `myco_inlet` |
| `hunger` | Metabolic dashboard: backlog, staleness, dead knowledge | `myco hunger` | `myco_hunger` |
| `absorb` | Sync kernel improvements from downstream instances | `myco upstream absorb` | `myco_upstream` |
| `graph` | Link graph: backlinks, orphans, clusters, stats | `myco graph` | `myco_graph` |
| `cohort` | Tag co-occurrence, compression suggestions, knowledge gaps | `myco cohort` | `myco_cohort` |
| `session` | Index, search, and prune agent conversation transcripts | `myco session` | `myco_session` |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The highest-impact contributions:

1. **Battle reports** on any of the six [open problems](docs/open_problems.md).
2. **Platform adapters** in [`docs/adapters/`](docs/adapters/) for the agent environment you already use.
3. **Design sketches** for the Metabolic Inlet -- particularly the discover / evaluate / extract phases.
4. **Translations** of this README. Current: English (canonical) / [中文](README_zh.md) / [日本語](README_ja.md).

## License

MIT -- see [LICENSE](LICENSE).

---

<div align="center">

*Your agent is a CPU. Myco is everything else -- and the operating system upgrades itself.*

</div>
