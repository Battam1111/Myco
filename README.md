[![PyPI version](https://img.shields.io/pypi/v/myco.svg)](https://pypi.org/project/myco/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

# Myco 🍄

**Your AI agent made a decision last week. Today it made the opposite one. Nobody noticed.**

Most tools give your agent memory — somewhere to put what it learned. But memory doesn't ask: *is that still true? does it contradict this? what changed since last time?*

Myco gives your agent **metabolism** — the ability to verify, evolve, and distill knowledge across sessions and projects.

> *Other tools give your agent memory. Myco gives it metabolism.*

---

## Quick Start

```bash
pip install myco
```

**Already have a `CLAUDE.md`?** *(Most common path)*

```bash
# Non-destructive — your CLAUDE.md is preserved, Myco layers added on top
myco migrate ./your-project --entry-point CLAUDE.md

# Establish your baseline (expect: zero issues on a fresh scaffold)
myco lint --project-dir ./your-project
```

After a few working sessions, lint starts catching real things:

```
$ myco lint --project-dir ./your-project
❌ L2: wiki/api_design.md references "v2 endpoint" but _canon.yaml says current = v3
❌ L4: wiki/deployment.md exists but is not indexed in MYCO.md
→ 2 issues found — that's Myco working for you
```

**Starting fresh?**

```bash
myco init my-project --level 2
myco lint --project-dir ./my-project
```

**Coming from Hermes, OpenClaw, or Cursor?**

```bash
myco import --from hermes ~/.hermes/skills/   # semi-automated import
myco import --from openclaw ./MEMORY.md
```

See [`adapters/`](adapters/) for full integration guides.

---

## Why Myco?

Most AI dev tools operate at **L-exec** or **L-skill** — they help your agent execute faster or accumulate new skills. Myco is the only tool that operates at **L-struct** and **L-meta**:

| Evolution Level | What It Does | Who Does It |
|----------------|--------------|-------------|
| L-exec | Execute faster over time | All agents |
| L-skill | Accumulate new skills | Hermes, OpenClaw, CLAUDE.md |
| **L-struct** | **Evolve knowledge structure** | **Myco (Gear 3)** |
| **L-meta** | **Evolve the rules of evolution** | **Myco (Gear 4)** |

**L-struct (Gear 3)** means Myco can detect when your assumptions are wrong — not just when facts are missing — and restructure your knowledge system accordingly. No other tool does this.

**L-meta (Gear 4)** means Myco distills patterns from one project into reusable frameworks for future projects. Your ASCC knowledge becomes the foundation your next project starts from, not dust in a closed folder.

Meta-evolution isn't vaporware: Myco targets text files — the medium LLMs operate best in — not model parameters. No gradient descent. No training loops. Works today.

---

## Works With Your Existing Tools

Myco doesn't replace your existing tools — it metabolizes them.

| Tool | How | Value |
|------|-----|-------|
| **Claude Code** (`CLAUDE.md`) | `myco migrate --entry-point CLAUDE.md` | Unlock consistency checking + evolution engine |
| **Cursor** | File-aware coexistence — no migration needed | `.cursorrules` + Myco live in the same project |
| **GPT / OpenAI API** | System prompt injection or ChatGPT Projects | Structured context in every session |
| **Hermes Agent** | `myco import --from hermes ~/skills/` | Skills get lint-verified and evolution-tracked |
| **OpenClaw** | `myco import --from openclaw MEMORY.md` | Memory gets structured and consistency-checked |
| **MemPalace** | L0 retrieval backend (design spec, v1.1) | Semantic search over Myco-managed knowledge |

---

## How It Works

Myco creates a four-layer knowledge architecture alongside your existing project files:

```
MYCO.md              ← L1: Entry point (or CLAUDE.md / CURSOR.md)
_canon.yaml          ← Single Source of Truth for canonical values
wiki/                ← L1.5: Compiled knowledge pages (lint-verified)
docs/                ← L2: Procedures, debates, evolution records
log.md               ← Append-only project timeline
```

A four-gear evolution engine keeps knowledge alive:

- **Gear 1** (every session): Sense friction — log repeated failures and unexpected behavior
- **Gear 2** (session end): Reflect — what can the knowledge system improve?
- **Gear 3** (milestones): Retrospect — challenge structural assumptions with double-loop learning
- **Gear 4** (project end): Distill — extract universal patterns, contribute back to Myco

`myco lint` runs 9 consistency checks (L0–L8) across all layers. It's the immune system.

---

## Real-World Validation

Myco has been intensively validated on a 7-day, 80+ file research project through the complete four-gear evolution cycle — including **Gear 4 cross-project distillation**. Universal patterns extracted from that project now live in [`docs/research_paper_craft.md`](docs/research_paper_craft.md) and [`docs/reusable_system_design.md`](docs/reusable_system_design.md), available to every future project that uses Myco.

That's the loop working: one project's hard-won knowledge becomes another project's starting point.

---

## Status

**v1.1.0** — Production-ready.

Agent compatibility: **Claude Code** (primary, fully validated) · **Cursor** (v1.0, file-aware) · **GPT API** (v1.0, system prompt) · **Hermes / OpenClaw** (v1.0, import adapters). Python 3.8+.

Generalization to additional project types is ongoing — battle reports and adapter contributions are the most valuable thing the community can provide right now.

---

## Contributing

The most valuable contributions aren't code — they're **knowledge evolution products** that came from real use: adapter integrations, wiki templates, lint rules, and workflow principles.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the four formal contribution types and their acceptance criteria. The fastest path to a merged PR is writing a [`adapters/`](adapters/) YAML for a tool you already use.

---

## License

MIT. See [LICENSE](LICENSE).
