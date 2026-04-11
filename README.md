<div align="center">

<img src="assets/logo_dark_280.png" alt="Myco" width="200">

# Myco

**A knowledge substrate that lints your AI project for contradictions your agent can't see — and evolves its own rules as the project grows.**

*Git tracks your code. Myco tracks what your code **knows**.*

[![PyPI](https://img.shields.io/badge/PyPI-coming%20soon-lightgrey?style=for-the-badge)](https://github.com/Battam1111/Myco)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Lint](https://img.shields.io/badge/Lint-15%2F15%20green-brightgreen?style=for-the-badge)](#how-it-works)

[30-Second Demo](#30-second-demo) · [Quick Start](#quick-start) · [What Myco Does](#what-myco-does) · [Glossary](#glossary) · [How It Works](#how-it-works) · [Myco vs Adjacent Tools](#myco-vs-adjacent-tools) · [Open Problems](#open-problems) · [The Story](#the-story)

**Languages:** English (canonical) · [中文](README_zh.md) · [日本語](README_ja.md)

</div>

---

> **If you've ever watched your agent confidently quote `v2` from one wiki page while `_canon.yaml` says `v3` — Myco is for you.**
>
> Myco is a substrate for developers who already maintain agent-readable project knowledge (a `CLAUDE.md`, `AGENTS.md`, a `docs/` tree, a wiki) and have hit the point where cross-file contradictions silently compound across sessions. It gives your project a **self-linting knowledge contract** that catches drift before your agent amplifies it.

---

## 30-Second Demo

Three files in your project say three different things. Nobody notices until production.

```bash
$ cat _canon.yaml
project:
  current_api_version: "v3"
system:
  stale_patterns: ["v2 endpoint", "api/v2"]

$ cat wiki/api.md
# API Reference
The current v2 endpoint lives at /api/v2/users.

$ myco lint

  L0 Canon self-check          PASS
  L1 Reference integrity       PASS
  L2 Number consistency        ⚠  2 issues
  L3 Stale patterns            PASS
  ...
  L14 Forage hygiene           PASS

  [MEDIUM] L2 | wiki/api.md:3
           Stale pattern 'v2 endpoint': "...The current v2 endpoint lives at..."
  [MEDIUM] L2 | wiki/api.md:3
           Stale pattern 'api/v2': "...lives at /api/v2/users..."
```

Two contradictions caught. Five future sessions of silent compounding prevented. This is substrate immunity at work — and the rules above (`stale_patterns`) are themselves versioned in `_canon.yaml`, so they evolve with your project.

---

## Quick Start

```bash
# Install from source (PyPI publication coming soon)
pip install git+https://github.com/Battam1111/Myco.git

# New project
myco init my-project --level 2

# Existing project with a CLAUDE.md
myco migrate ./your-project --entry-point CLAUDE.md   # non-destructive
myco lint --project-dir ./your-project                 # establish baseline
```

**MCP Integration** — your agent gets 9 tools automatically, no manual prompting:

```bash
pip install 'git+https://github.com/Battam1111/Myco.git#egg=myco[mcp]'
```

A ready-to-use `.mcp.json` is included in the repo. Once installed in Claude Code, Cursor, or any MCP-speaking client, your agent auto-discovers:

- **Checks** · `myco_lint` · `myco_status` · `myco_search` · `myco_log` · `myco_reflect`
- **Knowledge metabolism** · `myco_eat` · `myco_digest` · `myco_view` · `myco_hunger`

Myco works with the `myco` CLI alone, but the reflex layer (agent automatically capturing knowledge as the conversation flows) only exists when MCP is wired up.

---

## What Myco Does

Three concrete capabilities, in order of how quickly you'll feel them:

### 1. Lints your knowledge, not just your syntax

Markdown linters check syntax. Prose linters check style. **Nothing checks whether the claims in your wiki still match your canon file.** Myco does. `myco lint` runs 15 dimensions of checks (L0–L14) across `_canon.yaml`, `wiki/`, `docs/`, `MYCO.md`, and any project-specific files you declare — catching stale patterns, orphaned references, schema violations, and numeric drift the moment they appear.

### 2. Gives your agent a stable metabolic loop

When your agent reads a paper, discovers a bug pattern, or makes a design decision, it has exactly one place to put it: `myco_eat` captures it as a raw note. `myco_digest` moves it through a lifecycle (raw → extracted → integrated → excreted) with provenance retained. `myco_view` lets you (or the agent) retrieve notes by tag, status, or stage. The substrate survives across sessions, across agent vendors, and across project restructurings.

### 3. Evolves its own rules as the project grows

Myco's lint rules live in `_canon.yaml` and evolve via a structured craft protocol (the L13 check enforces that every rule change has an auditable multi-round debate record). **Your agent can propose new lint rules, and those proposals survive selection pressure from you.** The rules that pass become part of the substrate. The rules that stop working get excreted. This is the L-meta level: not evolving the agent, evolving the ground the agent stands on.

---

## Glossary

Myco uses a biological vocabulary. Here's the plain-English map:

| Myco verb | Plain English | CLI | MCP tool |
|---|---|---|---|
| `eat` | Capture a piece of content as a durable note | `myco eat` | `myco_eat` |
| `digest` | Move a note through its lifecycle (raw → extracted → integrated → excreted) | `myco digest` | `myco_digest` |
| `view` | Read notes with filters (status, tags, stage) | `myco view` | `myco_view` |
| `lint` | Check all files for contradictions and drift | `myco lint` | `myco_lint` |
| `forage` | Fetch external sources (repos, papers, articles) into the substrate | `myco forage` | (CLI only) |
| `absorb` | Sync kernel improvements from downstream project instances | `myco upstream absorb` | (CLI only) |
| `distill` | Extract universal patterns from a finished project for future kernel use (Gear 4 output) | (workflow, not CLI) | — |
| `hunger` | Metabolic dashboard: raw backlog, stale notes, dead knowledge, forage pressure | `myco hunger` | `myco_hunger` |

These verbs are metaphorical on purpose. Myco's thesis is that a knowledge substrate is a living system — metabolism is the right mental model. The table exists so you don't have to take that thesis on faith before you can use the tools.

---

## How It Works

Myco adds four lightweight layers alongside your existing project files:

```
your-project/
├── MYCO.md           ← Agent reads this every session (hot-zone index)
├── _canon.yaml       ← Single Source of Truth (canonical values lint checks against)
├── wiki/             ← Structured knowledge pages (lint-verified)
├── docs/             ← Procedures, debate records, evolution history
├── notes/            ← Digestive substrate (raw → extracted → integrated)
├── forage/           ← License-gated inbound channel for external sources
├── log.md            ← Append-only project timeline
└── src/myco/         ← CLI + MCP server + 15-dimension lint engine
```

`myco lint` is the **immune system** — it catches contradictions, orphaned files, stale references, and version drift before they compound. 15 dimensions (L0 through L14) cover canon consistency, reference integrity, number drift, stale patterns, orphan detection, log coverage, date consistency, wiki format, adapter schema, `.original` sync, vision anchor, notes schema, write-surface hygiene, upstream dotfile hygiene, craft protocol schema, and forage hygiene.

### A One-Line Architectural Frame

Your agent is the CPU; Myco is the operating system — and the OS upgrades itself. All evolution is **non-parametric**: markdown, YAML, folder structure, lint rules. No model weights are ever touched. This is why Myco works identically across agent vendors and survives model swaps.

### Three Immutable Laws

Everything in Myco can evolve — knowledge structure, compression rules, even the evolution engine itself. Everything except these three:

1. **Accessible** — Any agent can find the entry point and self-explain the substrate.
2. **Transparent** — Every change is auditable by a human. *Why this is load-bearing*: humans are Myco's selection pressure. If transparency is lost, selection pressure is lost, and a self-optimizing substrate with no selection pressure goes cancerous.
3. **Perpetually Evolving** — Stagnation is death. A substrate that stops metabolizing degrades into a static knowledge base.

### The Four Gears + The Metabolic Inlet

Myco's evolution engine has two faces. The four gears are the **autonomic nervous system** — internal homeostasis, all shipped in v0.x. The metabolic inlet is the **digestive system** — external absorption, declared as a primitive, earliest v1.0 completion.

| Gear | When | What | Status |
|------|------|------|--------|
| 1 | Every session | Sense friction — log failures and unexpected behavior | ✅ |
| 2 | Session end | Reflect — what should the knowledge system improve? | ✅ |
| 3 | Milestones | Retrospect — challenge structural assumptions | ✅ |
| 4 | Project end | Distill — extract universal patterns for future projects | ✅ |
| **Metabolic Inlet** | **On friction signal + periodic patrol** | **Discover → evaluate → extract → integrate → compress → verify → excrete external knowledge** | **Primitive declared; first-live forage batch completed 2026-04-11** |

Gears 1–4 face inward. The inlet faces outward. A substrate without a digestive system is a cache; this is why the inlet is declared now even though its fully autonomous form comes later.

### The Compression Doctrine

Myco's operating assumption:

> **Storage is infinite. Attention is not.**

Disks grow on demand; your agent's context window does not. So Myco **never forgets** — nothing is deleted from cold storage — but it **aggressively compresses** what flows into attention. Compression is not plumbing; it is the substrate's primary cognitive act. Three candidate criteria: usage frequency (low-read pages go cold), temporal relevance (time-bound facts excrete at expiry), and exclusivity (common knowledge your agent already has wastes substrate space).

> ⚠️ *Honest limit*: compression captures the load-bearing decisions and provenance chain of a piece of knowledge, not the full raw context. Irreducible texture is lost. This is a trade Myco makes on purpose; if you need lexical fidelity, keep a raw archive.

---

## Myco vs Adjacent Tools

Myco is **not** a memory layer, **not** an agent runtime, and **not** a skill framework. It's the layer none of those address.

|  | Myco | Mem0 | Letta / MemGPT | mempalace | Hermes | Claude Code |
|--|---|---|---|---|---|---|
| **Category** | Knowledge substrate | Memory layer | Agent runtime | Conversation memory | Agent runtime | Agent CLI |
| **Primary artifact** | `wiki/` + `_canon.yaml` + `notes/` | Key-value + vector store | Tiered memory (RAM / disk / archival) | Spatial schema (wings/rooms) | Session DB | `CLAUDE.md` convention |
| **Hosts agent execution?** | No — runs *inside* Claude Code / Cursor | No | Yes | No | Yes | Yes |
| **Cross-session contract enforcement** | ✅ 15-dimension self-linting | ❌ | ❌ | ❌ | Runtime cache invariants only | ❌ (pure convention) |
| **Self-evolving rules** | ✅ Gear 4 + craft protocol | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Retrieval benchmark** | — (different objective) | LongMemEval 49% | LoCoMo 74% (GPT-4o mini) | LongMemEval R@5 96.6% raw | — | N/A |
| **Integration** | MCP server + CLI | REST API + SDKs | Runtime API | MCP server | Runtime | Native |

**The key insight**: Myco is the only column that answers *"is this project's knowledge still internally consistent?"* rather than *"can we find the relevant memory?"* These are different questions, and the first is under-served.

Concretely:
- **Mem0 / Zep / Supermemory** are memory layers — they store and retrieve. Myco **stores nothing and retrieves nothing**; it lints the project files your agent already writes to.
- **Letta / MemGPT / Hermes** are runtimes — they host the agent's execution loop. Myco does **not host agents**; agents run on Claude Code, Cursor, or any MCP client and **call into Myco via 9 tools**.
- **Claude Code / Cursor / `CLAUDE.md`** are the environments Myco runs **inside**. Myco's `.mcp.json` makes an existing Claude Code installation gain the lint + metabolism tools automatically.
- **nuwa-skill / agentskills.io / pua** are skill frameworks — they package reusable behaviors. Myco is **not a skill framework**; skills run above Myco, and Myco lints the project the skills operate on.

Benchmark numbers cited above are from vendor documentation, independent benchmark reports, and web search results as of April 2026; they may shift. Myco deliberately does not compete on retrieval benchmarks because its objective (verification, not retrieval) is different and an apples-to-apples comparison would be misleading.

---

## Open Problems

Myco is early. These six blind spots are the highest-leverage places to contribute. The continuously-maintained registry lives at [`docs/open_problems.md`](docs/open_problems.md).

1. **Cold start.** How does Myco bootstrap on a brand-new project with no history, no canon, no friction record? Current answer: hand-crafted `myco init` templates. Desired: substrate learns its own bootstrap from prior project distillations.
2. **Trigger signals.** What fires Gear 2? What fires the metabolic inlet? Friction count is a proxy; the right signals are an open research question.
3. **Alignment at depth.** If Myco evolves rules the human can no longer evaluate (deep L-meta), how is it kept aligned? Transparency is necessary but not sufficient — we need *legible* transparency at scale.
4. **Compression engineering.** What to drop, when, without losing load-bearing tacit knowledge? The three candidate criteria (frequency / temporal / exclusivity) are starting points, not solutions.
5. **Structural decay detection (Self-Model C layer).** `myco lint` catches *factual* decay (version drift, stale refs). It cannot yet catch *structural* decay — when the architecture that was right at day 3 is wrong at day 30. Arguably the hardest problem in the whole design space.
6. **Dead-knowledge tracking (Self-Model D layer).** D layer is declared but not implemented. No signal yet for "note entered the substrate 30 days ago and was never read." Minimum viable seed is on the roadmap.

If you want to contribute something high-impact, pick one of these.

---

## Works With

| Tool | Integration | Status |
|------|-------------|--------|
| **Claude Code** | `.mcp.json` auto-discovery · `myco migrate --entry-point CLAUDE.md` | ✅ Shipped |
| **Cursor** | `.mcp.json` auto-discovery (MCP-compatible) | ✅ Shipped |
| **OpenAI Codex / GPT** | System-prompt injection or Projects-mode snippet | 🧪 Adapter spec |
| **Hermes Agent** | `myco import --from hermes ~/.hermes/skills/` | 🧪 Adapter spec |
| **OpenClaw** | `myco import --from openclaw ./MEMORY.md` | 🧪 Adapter spec |
| **MemPalace** | L0 retrieval backend (digest → memory palace pages) | 🧪 Adapter spec |

Platform-specific adapters live in [`docs/adapters/`](docs/adapters/). Community PRs welcome.

---

## Validation

Built on a real 8-day, 80+ file research project that ran the complete four-gear cycle to completion:

<div align="center">

| 80+ files | 10 wiki pages | 15+ structured debates | 15/15 lint dimensions green |
|:---------:|:-------------:|:---------------------:|:----------------------------:|

</div>

The deeper claim: **that 8-day project was an unconscious prototype of Myco.** I wasn't demoing the substrate; I was *running* it by hand — human-driven meta-evolution, manually triggered lint, verbal friction logs. It worked. Myco is the formalization of a pattern that already proved itself; the v0.x → v1.0 trajectory is not "invent new things" but "make what was working by hand work by itself." Patterns extracted via Gear 4 now live in the Myco kernel codebase. See [`examples/ascc/`](examples/ascc/).

Myco stands on a 50-year lineage: **Karpathy LLM Wiki** (structured knowledge compilation) + **Polanyi Tacit Knowledge** (proximal / distal structure for operational experience) + **Argyris Double-Loop Learning** (single-loop fixes actions, double-loop fixes the rules — the L-struct / L-meta split) + **Toyota PDCA** (Plan / Do / Check / Act as the base cycle of the four gears) + **Voyager Skill Library** (iterative skill accumulation via grounded execution). See [`docs/theory.md`](docs/theory.md).

---

## The Story

Day 1, I had a 949-line `CLAUDE.md`. Everything in one file. By day 3, the same metric appeared in three places with three different values, and my agent used all three confidently. But the deeper problem ran beneath that: every new session, my agent would rewrite the same deployment script from scratch — not because it forgot the SSH config rules (those were documented), but because the *tacit knowledge* of which flags mattered, what order worked, what silently broke — all of that vanished at the session boundary. Intelligence wasn't being lost. It was being **discarded**, repeatedly.

That's when I built the first `myco lint` — not just to catch contradictions, but to give agents something they fundamentally lack: a substrate. A ground that watches whether what the agent "knows" is still true, flags when assumptions rot, and evolves its own rules when the old ones stop working. Not a tool the agent picks up. A floor the agent stands on.

By day 7, a milestone retrospective revealed that 40% of friction came from "changed content, forgot to update the index" — so the system evolved its own rules. Day 8, I realized the pattern wasn't project-specific. I named it **Myco**, after *mycelium* — the underground fungal network beneath every forest. Mycelium is not a plumbing system. It secretes enzymes that decompose fallen leaves into nutrients (metabolism). It remembers effective growth paths and redirects strategy accordingly (meta-evolution). It redistributes resources from abundant zones to starved ones (intelligent compression). It forms symbiosis with the roots of trees of any species it encounters (agent-adaptive universality). Agents are the trees above ground. Myco is the living network beneath, making the whole forest work.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The highest-impact contributions are:

1. **Battle reports** on any of the six [Open Problems](#open-problems) above.
2. **Platform adapters** in [`docs/adapters/`](docs/adapters/) for tools you already use (Cursor setups, JetBrains plugins, etc.).
3. **Design sketches** for the Metabolic Inlet primitive — particularly the discover/evaluate/extract/integrate phases.
4. **Translations** of this README to your language (current: English canonical · Chinese · Japanese).

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">

**Myco: Other tools give agents memory. Myco gives them metabolism — and a self-rewriting rulebook.**

</div>
