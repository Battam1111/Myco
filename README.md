# Myco

**The Living Substrate — Self-Evolving Cognition for AI Agents**

Myco is an autonomous cognitive substrate that gives AI agents persistent memory, structured knowledge, and self-evolving capabilities across sessions. Named after mycelium — the underground fungal network that decomposes, remembers, reallocates, signals, and symbioses with any tree species — Myco is the invisible infrastructure that makes the whole forest work.

Agents are the trees. Myco is the network underground.

> **30-second version:** Other tools give your agent memory. Myco gives it metabolism.

## What Myco Is

Myco is **not** an agent, and it does **not** contain an agent. It is everything *outside* the agent that enables persistent cognition:

- A four-layer knowledge architecture (Index → Wiki → Docs → Archive)
- A self-evolution engine with four gears (Friction Sensing → Session Reflection → Milestone Retrospective → Cross-Project Distillation)
- An automated consistency checker (Lint) backed by a Single Source of Truth (_canon.yaml)
- A structured debate protocol (传统手艺 / Craft) for high-stakes decisions
- Operational experience capture (Procedures, Context Priming, Pattern Names)

Myco is designed to work with **any** AI agent system — Claude, GPT, Codex, or future systems. The core is agent-independent; at runtime it adapts to specific agent capabilities (context window, tool access, etc.). Integration guides for Claude Code, Cursor, GPT, Hermes, OpenClaw, and MemPalace are available in [`adapters/`](adapters/).

## Three Immutable Laws

1. **Entry point is always accessible** — An agent can always find its way in through `MYCO.md`
2. **Transparent to humans** — Every piece of knowledge is readable, auditable, and editable by humans
3. **Perpetual evolution** — The system evolves itself, including the rules of evolution

## Why Myco?

Most knowledge tools solve the **storage problem**: how do I remember what my agent has done? Claude.md provides hot memory. Hermes skills capture repeatable actions. MemPalace retrieves long-term facts.

Myco solves a different problem: the **metabolism problem**. How does knowledge *evolve*? How do I detect when my assumptions are stale? How do I catch contradictions before they cascade? How do I extract timeless patterns from project-specific experience and apply them elsewhere?

Other tools answer: *where did I put that?*

Myco answers: *is that still true? does it connect to this? what changed since last time?*

### Evolution Landscape

| Evolution Level | Description | Who Does It |
|----------------|-------------|-------------|
| L-exec | Execute faster over time | All agents |
| L-skill | Accumulate new skills | Hermes, OpenClaw |
| L-struct | Evolve knowledge structure | **Myco (Gear 3)** |
| L-meta | Evolve the rules of evolution | **Myco (Gear 4)** |

Myco doesn't replace storage tools — it makes them *productive*. Every decision recorded in CLAUDE.md can be checked for consistency. Every skill in Hermes gets verified and refined through the evolution cycle. Every fact in MemPalace decays gracefully when conditions change.

## Works With Your Existing Tools

| Tool | Integration | Value |
|------|------------|-------|
| Claude Code (CLAUDE.md) | `myco migrate --entry-point CLAUDE.md` upgrades your existing CLAUDE.md | Unlock evolution engine + lint |
| Hermes Agent | Import skills into Myco's evolution cycle | Skills get verified and refined |
| MemPalace | Use as L0 retrieval backend | Store everything, metabolize with Myco |
| Any IDE (Cursor, VS Code) | IDE-independent project knowledge | Switch IDEs without losing knowledge |

## Quick Start

```bash
pip install myco
```

**Already have a Claude Code project with a CLAUDE.md?** *(Most common path)*

```bash
# Non-destructive migration — your CLAUDE.md is preserved, Myco layers added on top
myco migrate ./your-project --entry-point CLAUDE.md

# Run lint — the first inconsistency it catches is your "aha moment"
myco lint --project-dir ./your-project
```

**Starting fresh?**

```bash
# Initialize a new Myco-powered project (level 2 recommended for multi-session work)
myco init my-project --level 2

# Run consistency checks
myco lint --project-dir ./my-project
```

**Coming from Hermes, OpenClaw, or another tool?** See [`adapters/`](adapters/) for integration guides.

**Windows users** — after `pip install myco`, verify the CLI is in PATH:

```cmd
where myco
```

If `myco` is not found, add Python's Scripts directory to PATH:

```cmd
# Find Scripts path
python -c "import sys; print(sys.exec_prefix + r'\Scripts')"

# Or run via module as fallback
python -m myco lint --project-dir .
```

This creates a project scaffold with the knowledge system pre-configured:

```
my-project/
├── MYCO.md                # L1 Index (auto-loaded entry point)
├── _canon.yaml            # Canonical values (Single Source of Truth)
├── log.md                 # Append-only timeline
├── docs/
│   ├── WORKFLOW.md        # Twelve principles (W1-W12) + session protocol
│   └── operational_narratives.md  # Procedure knowledge (created on demand)
├── wiki/                  # Compiled knowledge pages (created on demand)
└── scripts/
    └── lint_knowledge.py  # Automated 9-dimension consistency checker
```

**Myco framework-level knowledge** (in `Myco/docs/`, available to all projects):

| Doc | Contents |
|-----|----------|
| `reusable_system_design.md` | Full architecture spec + Bootstrap guide (L0/L1/L2) + project type adaptation |
| `research_paper_craft.md` | Scientific figure toolchain + 10 writing principles (for research projects) |
| `evolution_engine.md` | Four-gear detailed mechanics + permission levels |
| `architecture.md` | System overview + docs index |

## Bootstrap Levels

| Level | Time | For | What You Get |
|-------|------|-----|-------------|
| **L0** | 5 min | Small projects, exploration | `MYCO.md` (minimal) + `log.md` |
| **L1** | 30 min | Multi-session projects (5+ sessions) | + `WORKFLOW.md` + `_canon.yaml` + `wiki/` |
| **L2** | 2 hours | Long-term complex projects (papers, products) | + Full WORKFLOW + Lint + Evolution Engine (all 4 gears) |

Don't pre-build empty structures. Let the system grow organically — create wiki pages when you need them, write procedures when you've failed twice.

## Five Core Capabilities

| Capability | What It Does | How |
|-----------|-------------|-----|
| **Knowledge Metabolism** | Decomposes external information into system nutrients | W10 Compilation Protocol + Wiki pages |
| **Meta-Evolution** | Evolves the evolution mechanism itself | Four-gear engine + Double-loop learning |
| **Self-Model** | Knows what it knows and what it doesn't | Lint + _canon.yaml + blind spot annotations |
| **Cross-Session Continuity** | Maintains coherent cognition across sessions | Four-layer architecture + hot zone |
| **Agent-Adaptive Universality** | Works with any AI agent system | Agent-independent core + runtime adaptation |

## The Twelve Principles (W1-W12)

| # | Principle | One-liner |
|---|-----------|-----------|
| W1 | Immediate Capture | Write decisions now, not at session end |
| W2 | Project Hygiene | Directory structure + naming conventions |
| W3 | Craft (传统手艺) | Multi-round debate for directional decisions |
| W4 | Online Verification | Cross-check numerical claims with search |
| W5 | Continuous Evolution | Repeat → script, lost → reinforce, fail → record |
| W6 | Proximal Enrichment | Failure paths are the most valuable knowledge |
| W7 | Systematic Lint | Periodic automated consistency checks |
| W8 | Wiki Templates | Typed headers + footers for knowledge pages |
| W9 | Active Tensions | Mark unresolved architectural trade-offs with ⚡ |
| W10 | Compilation Protocol | 5-step external knowledge extraction |
| W11 | Verification Scope | Label what conditions conclusions were verified under |
| W12 | Information Density | Adapt context loading depth to task complexity |

## Evolution Engine

```
Gear 1 (every session)          Gear 2 (session end)
  Friction Sensing          →     Session Reflection
  Record operational snags          "What can improve?"
       │                                │
       ▼                                ▼
Gear 3 (milestones)              Gear 4 (project end)
  Milestone Retrospective    →   Cross-Project Distillation
  Challenge architecture             Extract universal patterns
  assumptions (Double-loop)          Update Myco templates
```

## Philosophy

Myco takes the **Bitter Lesson** (Rich Sutton, 2019) seriously: hand-crafted rules should eventually be replaceable by system-discovered rules. The current W1-W12 principles are a legitimate bootstrap hot-start from practice — but every one of them is meant to be gradually replaced or refined by rules the system discovers through its own evolution.

Meta-evolution isn't vaporware here: Myco's evolution targets text files — the medium LLMs operate best in — not model parameters. This makes true meta-evolution achievable today without gradient descent or training loops.

## Status

Myco v1.0 has been intensively validated on a multi-month research project (ASCC) spanning 80+ files, 10 wiki pages, 15+ structured debates, and 7 operational procedures. The full four-gear evolution cycle — including **Gear 4 cross-project distillation** — has been completed: universal patterns from the ASCC project now live in Myco's `docs/` as `research_paper_craft.md` and `reusable_system_design.md`, available to all future projects.

Agent compatibility: **Claude Code** (primary, fully validated) · **Cursor** (file-aware coexistence, v1.0) · **GPT API** (system prompt injection, v1.0) · **Hermes/OpenClaw** (content import adapters, v1.0). See [`adapters/`](adapters/) for integration guides. Generalization to additional project types is ongoing — contributions and battle reports welcome.

## Project Adaptation

| Project Type | Craft Triggers | Common Wiki Pages | Level |
|-------------|---------------|-------------------|-------|
| Academic Paper | Theory claims, reviewer attacks | Framework, strategy, experiments | L2 |
| Software Product | Architecture, tech choice, UX | API design, bugs, deployment | L1-2 |
| Data Analysis | Methodology, conclusions, bias | Data sources, methods, visualizations | L1 |
| Learning Plan | Learning path, resource evaluation | Knowledge graph, progress tracking | L0-1 |

## License

MIT

## Contributing

Myco v1.0 is production-ready for Claude Code projects and agent-agnostic for Cursor, GPT, and any agent that can read project files. Contributions welcome — especially adapters and battle reports from new project types. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

The most valuable contributions aren't just code — they're **knowledge evolution products**: wiki templates, lint rules, workflow principles, and adapter integrations that emerged from real-world use.

---
