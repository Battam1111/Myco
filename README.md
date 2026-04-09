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

A four-gear evolution engine keeps knowledge alive:

| Gear | When | What |
|------|------|------|
| 1 | Every session | Sense friction — log failures and unexpected behavior |
| 2 | Session end | Reflect — what should the knowledge system improve? |
| 3 | Milestones | Retrospect — challenge structural assumptions |
| 4 | Project end | Distill — extract universal patterns for future projects |

---

## Why Myco

Most AI tools operate at **L-exec** (execute faster) or **L-skill** (accumulate skills). Myco operates at **L-struct** and **L-meta** — evolving the knowledge structure itself:

| Level | What | Who |
|-------|------|-----|
| L-exec | Execute faster | All agents |
| L-skill | Accumulate skills | Hermes, OpenClaw, CLAUDE.md |
| **L-struct** | **Evolve knowledge structure** | **Myco (Gear 3)** |
| **L-meta** | **Evolve the rules of evolution** | **Myco (Gear 4)** |

[Mem0's 2026 report](https://mem0.ai/blog/state-of-ai-agent-memory-2026) names "memory staleness detection" as an unresolved challenge. That's what `myco lint` solves. Mem0 does retrieval. Myco does verification and evolution. They're complementary.

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

Day 1, I had a 949-line `CLAUDE.md`. Everything in one file. Day 3, the same metric appeared in three places with three different values. My agent used all three confidently. That's when I built the first `myco lint`.

By day 5, I had canonical values, wiki pages, and 8 lint checks. By day 7, a milestone retrospective revealed 40% of friction came from "changed content, forgot to update index" — so the system evolved its own rules.

Day 8, I realized the pattern wasn't project-specific. Four layers, lint checks, evolution gears — they're universal. I named it Myco, after mycelium: the underground network that metabolizes nutrients between organisms, keeping entire ecosystems alive.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The most impactful contributions are battle reports and [`adapters/`](adapters/) YAMLs for tools you already use.

## License

MIT
