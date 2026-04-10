<div align="center">

<img src="assets/logo_dark_280.png" alt="Myco" width="200">

# Myco

**Other tools give your agent memory. Myco gives it metabolism.**

[![PyPI](https://img.shields.io/pypi/v/myco?style=for-the-badge&color=00D4AA)](https://pypi.org/project/myco/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

[What It Looks Like](#what-it-looks-like) · [Quick Start](#quick-start) · [How It Works](#how-it-works) · [Why Myco](#why-myco) · [The Story](#the-story)

**Other Languages:** [中文](README_zh.md)

</div>

---

## What It Looks Like

Day 3 of a project. Your agent references "v2 endpoint" in one wiki page, but `_canon.yaml` says v3. A deployment doc still mentions v1. Three places, three different truths. Nobody catches it.

```
$ myco lint

  L0 Canon self-check          PASS
  L1 Reference integrity       PASS
  L2 Numeric consistency       ⚠ 1 issue
  L3 Stale pattern scan        PASS
  L4 Orphan detection          ⚠ 1 issue
  L5 Log coverage              PASS
  L6 Date consistency          PASS
  L7 Wiki format               PASS
  L8 Adapter schema            PASS

  [HIGH] L2 | wiki/api_design.md
         "v2 endpoint" ≠ _canon.yaml current_api_version = "v3"

  [MEDIUM] L4 | wiki/deployment.md
           not indexed in MYCO.md
```

Two issues caught. That contradiction would have silently compounded for five more sessions.

---

## Quick Start

```bash
pip install myco
```

**Have a `CLAUDE.md`?**

```bash
myco migrate ./your-project --entry-point CLAUDE.md   # non-destructive
myco lint --project-dir ./your-project                 # establish baseline
```

**Starting fresh?**

```bash
myco init my-project --level 2
```

**Coming from another tool?**

```bash
myco import --from hermes ~/.hermes/skills/
myco import --from openclaw ./MEMORY.md
```

See [`adapters/`](adapters/) for Cursor, GPT, and other integrations.

**MCP Integration** (agent auto-discovers Myco tools):

```bash
pip install 'myco[mcp]'
```

A `.mcp.json` is already included in the repo. Once installed, your agent automatically gets 5 tools: `myco_lint`, `myco_status`, `myco_search`, `myco_log`, and `myco_reflect` — no manual prompting needed.

---

## How It Works

Myco adds four layers alongside your existing project files:

```
your-project/
├── MYCO.md            ← Agent reads this every session (hot-zone index)
├── _canon.yaml        ← Single Source of Truth (canonical values for lint)
├── wiki/              ← Structured knowledge pages (lint-verified)
├── docs/              ← Procedures, debate records, evolution history
├── log.md             ← Append-only project timeline
└── src/myco/          ← CLI + lint engine (9 checks, L0–L8)
```

`myco lint` runs 9 consistency checks across all layers. It's the immune system — it catches contradictions, orphaned files, stale references, and version drift.

Everything in Myco can evolve — knowledge structure, compression strategies, even the evolution engine itself. Everything except three immutable laws:

1. **Accessible** — The system must have an entry point any agent can locate and self-explain.
2. **Transparent** — The system must remain auditable and understandable by humans, always.
3. **Perpetually Evolving** — Stagnation is death. A system that stops evolving degrades into a static knowledge base.

A four-gear evolution engine keeps knowledge alive:

| Gear | When | What |
|------|------|------|
| 1 | Every session | Sense friction — log failures and unexpected behavior |
| 2 | Session end | Reflect — what should the knowledge system improve? |
| 3 | Milestones | Retrospect — challenge structural assumptions |
| 4 | Project end | Distill — extract universal patterns for future projects |

---

## Why Myco

Agents can execute and they can remember, but they cannot notice inconsistencies in their own knowledge, question whether their assumptions still hold, or extract patterns from one project to bootstrap the next. Myco is the **reflexive layer** agents lack — the external system that watches, validates, evolves, and teaches.

Most AI tools operate at **L-exec** (execute faster) or **L-skill** (accumulate skills). Myco operates at **L-struct** and **L-meta** — evolving the knowledge structure itself:

| Level | What | Who |
|-------|------|-----|
| L-exec | Execute faster | All agents |
| L-skill | Accumulate skills | Hermes, OpenClaw, CLAUDE.md |
| **L-struct** | **Evolve knowledge structure** | **Myco (Gear 3)** |
| **L-meta** | **Evolve the rules of evolution** | **Myco (Gear 4)** |

[Mem0's 2026 report](https://mem0.ai/blog/state-of-ai-agent-memory-2026) names "memory staleness detection" as an unresolved challenge. That's exactly what `myco lint` does. Mem0 does retrieval. Myco does verification and evolution. They're complementary.

---

## Works With

| Tool | Integration |
|------|-------------|
| **Claude Code** | `myco migrate --entry-point CLAUDE.md` |
| **Cursor** | File-aware coexistence — no migration needed |
| **GPT / OpenAI** | System prompt injection or ChatGPT Projects |
| **Hermes Agent** | `myco import --from hermes` |
| **OpenClaw** | `myco import --from openclaw` |
| **MemPalace** | L0 retrieval backend (adapter spec available) |

---

## Validation

Built on a real 8-day, 80+ file research project through the complete four-gear cycle:

<div align="center">

| 80+ files | 10 wiki pages | 15+ structured debates | 9/9 lint checks |
|:---------:|:-------------:|:---------------------:|:----------------:|

</div>

Patterns extracted via Gear 4 now live in the Myco codebase — the tool evolved from its first user's experience. See [`examples/ascc/`](examples/ascc/).

---

## The Story

Day 1, I had a 949-line `CLAUDE.md`. Everything in one file. By day 3, the same metric appeared in three places with three different values, and my agent used all three confidently. But the real problem ran deeper: every new session, my agent would rewrite the same deployment script from scratch — not because it forgot the SSH config rules (those were documented), but because the *tacit knowledge* of which flags matter, what order works, what silently breaks — all of that vanished at the session boundary. Intelligence wasn't being lost. It was being **discarded**, repeatedly.

That's when I built the first `myco lint` — not just to catch contradictions, but to give agents something they fundamentally lack: a reflexive layer. A system that watches whether what the agent "knows" is still true, flags when assumptions rot, and evolves its own rules when the old ones stop working.

By day 7, a milestone retrospective revealed 40% of friction came from "changed content, forgot to update index" — so the system evolved its own rules. Day 8, I realized the pattern wasn't project-specific. I named it Myco, after mycelium: the underground fungal network that breaks down matter into nutrients, remembers effective growth paths, redistributes resources where they're needed, and forms symbiosis with any species it encounters. Agents are the trees above ground. Myco is the living network beneath, making the whole forest work.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The most impactful contributions are battle reports and [`adapters/`](adapters/) YAMLs for tools you already use.

## License

MIT
