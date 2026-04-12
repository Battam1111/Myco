<p align="center">
  <img src="assets/myco-logo.svg" width="180" alt="Myco">
</p>

<h1 align="center">Myco</h1>

<p align="center"><b>Metabolize — not just memorize — your agent's knowledge.</b></p>

<p align="center">
  <a href="https://pypi.org/project/myco/"><img src="https://img.shields.io/pypi/v/myco?style=flat&label=PyPI" alt="PyPI"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.8+-blue?style=flat" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=flat" alt="License"></a>
  <a href="https://github.com/Battam1111/Myco"><img src="https://img.shields.io/github/stars/Battam1111/Myco?style=flat" alt="Stars"></a>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> · <a href="#why-myco">Why Myco</a> · <a href="docs/theory.md">Theory</a> · <a href="docs/agent_protocol.md">Agent Protocol</a> · <a href="docs/architecture.md">Architecture</a>
</p>

---

Your agent forgets everything between sessions. Myco fixes that — not by storing conversations, but by **metabolizing** knowledge: digesting it, compressing it, verifying it, excreting what's dead, and evolving its own rules. The result is an agent that gets smarter every session without touching model weights.

## Quick Start

```bash
git clone https://github.com/Battam1111/Myco.git
cd Myco && pip install -e ".[mcp]"
myco init --agent claude my-project
```

Three commands. Your agent now has persistent, self-evolving cognition. Editable install — the entire system can mutate, not just the content.

## Why Myco

Other systems store or compile knowledge. Myco **metabolizes** it.

| | Store (Mem0, Zep) | Compile (LLM Wiki) | **Metabolize (Myco)** |
|---|---|---|---|
| **Lifecycle** | dump in, search out | ingest, compile | raw → digest → extract → integrate → **excrete** |
| **Self-check** | none | basic contradiction | 23-dimension lint immune system |
| **Self-evolve** | none | none | kernel code mutates via `myco_evolve` |
| **Dead knowledge** | accumulates forever | accumulates forever | **auto-detected and excreted** |

> A system without excretion is a tumor. Myco is the first knowledge system with a complete digestive tract.

## What It Does

- 🧬 **Knowledge metabolism** — 7-step pipeline from discovery to excretion. Knowledge has a lifecycle; dead knowledge is removed.
- 🛡️ **23-dimension immune system** — lint catches inconsistencies, stale claims, orphaned files, structural decay. Mechanical, not manual.
- 🔄 **Self-evolution** — `myco_evolve` mutates skills, lint rules, hunger signals. Editable install means the engine itself evolves.
- 🧠 **Self-model** — the substrate knows what it has, what it's missing, what's decaying, and what's dead.
- 🍄 **Mycelium network** — every file is a node, every reference is an edge. Orphans are detected. Density is tracked.
- 🤖 **Agent-First** — 21 MCP tools auto-discovered. Human speaks natural language. Agent operates everything.

## Architecture

```
Human (natural language)
  ↓
Agent (Claude / Cursor / GPT)
  ↓ 21 MCP tools
Myco Substrate
  ├── notes/    → knowledge atoms (lifecycle: raw→integrated→excreted)
  ├── wiki/     → long-term refined knowledge (promoted from notes)
  ├── docs/     → architecture, theory, protocol
  ├── skills/   → operational procedures (evolvable)
  ├── src/myco/ → kernel code (editable, mutatable)
  └── _canon.yaml → single source of truth
```

## Three Laws (immutable)

1. **Accessible** — any agent can discover, understand, and start using the system
2. **Transparent** — every action is auditable by humans, always
3. **Perpetually evolving** — stasis is decay; the metabolic cycle never stops

## Open Problems

Myco is honest about what it hasn't solved:

1. **Cold start** — how does a substrate bootstrap with zero history?
2. **Structural decay** — how to detect when organization patterns rot over time?
3. **Cross-project distillation** — how to transfer knowledge between projects reliably?

These are research problems, not feature requests. If you solve one, you advance the field. → [Full list](docs/open_problems.md)

## Design Philosophy

Myco stands on: Clark & Chalmers' Extended Mind (the substrate IS cognition), Sutton's Bitter Lesson (don't limit what can evolve), Argyris' Double-Loop Learning (evolve the rules, not just behavior), and the Toyota PDCA cycle. → [Full theory](docs/theory.md)

## Contributing

```bash
git clone https://github.com/Battam1111/Myco.git
cd Myco && pip install -e ".[mcp,dev]"
pytest tests/
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. Every contribution — code, docs, or a single friction report — makes the organism stronger.

## License

MIT — [LICENSE](LICENSE)
