# Myco

**The Living Substrate — Self-Evolving Cognition for AI Agents**

Myco is an autonomous cognitive substrate that gives AI agents persistent memory, structured knowledge, and self-evolving capabilities across sessions. Named after mycelium — the underground fungal network that decomposes, remembers, reallocates, signals, and symbioses with any tree species — Myco is the invisible infrastructure that makes the whole forest work.

Agents are the trees. Myco is the network underground.

## What Myco Is

Myco is **not** an agent, and it does **not** contain an agent. It is everything *outside* the agent that enables persistent cognition:

- A four-layer knowledge architecture (Index → Wiki → Docs → Archive)
- A self-evolution engine with four gears (Friction Sensing → Session Reflection → Milestone Retrospective → Cross-Project Distillation)
- An automated consistency checker (Lint) backed by a Single Source of Truth (_canon.yaml)
- A structured debate protocol (传統手藝 / Craft) for high-stakes decisions
- Operational experience capture (Procedures, Context Priming, Pattern Names)

Myco works with **any** AI agent system — Claude, GPT, Codex, or future systems. The core is agent-independent; at runtime it adapts to specific agent capabilities (context window, tool access, etc.).

## Three Immutable Laws

1. **Entry point is always accessible** — An agent can always find its way in through `CLAUDE.md`
2. **Transparent to humans** — Every piece of knowledge is readable, auditable, and editable by humans
3. **Perpetual evolution** — The system evolves itself, including the rules of evolution

## Quick Start

```bash
# Clone the repo
git clone https://github.com/Battam1111/myco
cd myco

# Initialize a new Myco-powered project (creates ../my-project/)
python scripts/myco_init.py ../my-project

# Or with a specific bootstrap level (recommended for multi-session projects)
python scripts/myco_init.py ../my-project --level 2

# Or initialize into a specific directory
python scripts/myco_init.py /path/to/my-project --level 1
```

This creates a project scaffold with the knowledge system pre-configured:

```
my-project/
├── CLAUDE.md              # L1 Index (auto-loaded by agent)
├── _canon.yaml            # Canonical values (Single Source of Truth)
├── log.md                 # Append-only timeline
├── docs/
│   ├── WORKFLOW.md        # Twelve principles (W1-W12) + session protocol
│   └── operational_narratives.md  # Procedure knowledge (created on demand)
├── wiki/                  # Compiled knowledge pages (created on demand)
└── scripts/
    └── lint_knowledge.py  # Automated 9-dimension consistency checker
```

## Bootstrap Levels

| Level | Time | For | What You Get |
|-------|------|-----|-------------|
| **L0** | 5 min | Small projects, exploration | `CLAUDE.md` (minimal) + `log.md` |
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

## Proven in Practice

Myco v0.x was battle-tested over 8 days on the [ASCC project](examples/ascc/) (Action Shaping in Continuous Control, targeting NeurIPS 2026):

- System grew from a single 949-line file to 17,000+ lines across 80+ files
- 10 wiki pages, 15+ debate records, 7 procedures
- 12+ rounds of 传統手藝 debate with online research validation
- First Gear 3 milestone retrospective executed successfully
- Automated lint: 9 dimensions, canonical value enforcement

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

Myco is in early development (v0.x). Contributions welcome — especially battle reports from using it on new project types.

---

*"菌丝不只是连接树木的管道：它分泌酶将落叶分解为养分，记住有效的生长路径并据此调整策略，根据需求将资源从丰裕区域调往匮乏区域，并与不同树种的根系都能形成共生。"*
