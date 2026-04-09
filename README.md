<div align="center">

<img src="assets/logo_dark_280.png" alt="Myco" width="280">

# Myco

### Other tools give your agent memory. Myco gives it metabolism.

<br>

Every conversation you have with an AI — every decision, every debugging session, every architecture debate — disappears when the session ends. Some tools try to fix this by adding "memory." But memory alone doesn't ask: *is that still true? does it contradict what we decided last week? what changed since then?*

Myco adds a **metabolic layer** to your AI agent — the ability to verify knowledge across sessions, evolve its own structure when assumptions break, and distill hard-won patterns into reusable frameworks for your next project.

<br>

[![PyPI](https://img.shields.io/pypi/v/myco?style=for-the-badge&color=00D4AA)](https://pypi.org/project/myco/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

<br>

[See It Work](#what-it-looks-like) · [Quick Start](#quick-start) · [How It Works](#how-it-works) · [Why Myco](#why-myco) · [The Story](#the-story-behind-myco)

<br>

**Other Languages:** [中文](README_zh.md)

</div>

---

## What It Looks Like

Day 3 of a research project. You're using Claude Code with a `CLAUDE.md` that's grown to 900+ lines. Your agent confidently references "the v2 API endpoint" in one wiki page — but `_canon.yaml` says the current version is v3. A deployment doc still mentions the v1 migration. Three places, three different truths. Nobody catches it.

With Myco:

```
$ myco lint --project-dir ./my-research

============================================================
  Myco Knowledge System Lint
============================================================

  Checking L0 Canon 自检...           → PASS
  Checking L1 引用完整性...           → PASS
  Checking L2 数字一致性...           → ⚠ 1 issue
  Checking L3 过时模式扫描...         → PASS
  Checking L4 孤儿文档检测...         → ⚠ 1 issue
  Checking L5 log.md 覆盖度...        → PASS
  Checking L6 日期一致性...           → PASS
  Checking L7 Wiki 格式一致性...      → PASS
  Checking L8 .original 同步检查...   → PASS

  ⚠ 2 issue(s): 0 CRITICAL, 1 HIGH, 1 MEDIUM

  [HIGH] L2 | wiki/api_design.md
         references "v2 endpoint" but _canon.yaml says current_api_version = "v3"

  [MEDIUM] L4 | wiki/deployment.md
           exists but is not indexed in MYCO.md wiki_pages list
```

That's Myco working. The inconsistency that would have silently compounded over the next five sessions — caught in seconds.

This isn't a hypothetical. This is the actual format of `myco lint` output on a real project with real contradictions. The tool that caught it is the same tool you install with `pip install myco`.

---

## Quick Start

```bash
pip install myco
```

**Already have a `CLAUDE.md`?** This is the most common path.

```bash
# Non-destructive — your CLAUDE.md is preserved, Myco layers added on top
myco migrate ./your-project --entry-point CLAUDE.md

# Establish your baseline (a fresh scaffold shows zero issues — that's expected)
myco lint --project-dir ./your-project
```

Work for a few sessions. Make decisions. Change your mind. Then lint again — and watch it catch the inconsistencies your agent didn't notice.

**Starting fresh?**

```bash
myco init my-project --level 2
```

**Coming from another tool?**

```bash
myco import --from hermes ~/.hermes/skills/     # Hermes Agent skills → Myco wiki stubs
myco import --from openclaw ./MEMORY.md          # OpenClaw memory → structured knowledge
```

See [`adapters/`](adapters/) for Cursor, GPT, and other integration guides.

---

## How It Works

Myco creates a four-layer knowledge architecture alongside your existing project files:

<div align="center">
<img src="assets/architecture.png" alt="Myco Architecture — four knowledge layers verified by myco lint" width="800">
</div>

<br>

<table>
<tr>
<td><b>MYCO.md</b></td>
<td>Entry point your agent reads every session. Hot-zone index of what matters right now.</td>
</tr>
<tr>
<td><b>wiki/</b></td>
<td>Structured knowledge pages — each lint-verified against <code>_canon.yaml</code>, the Single Source of Truth.</td>
</tr>
<tr>
<td><b>docs/</b></td>
<td>Procedures, debate records (传统手艺), evolution history. The project's institutional memory.</td>
</tr>
<tr>
<td><b>src/myco/</b></td>
<td>CLI, lint engine (9 checks, L0–L8), migrate, import, adapters. The immune system.</td>
</tr>
</table>

A four-gear **evolution engine** keeps knowledge alive — not just stored:

| Gear | When | What |
|------|------|------|
| **Gear 1** | Every session | Sense friction — log repeated failures and unexpected behavior |
| **Gear 2** | Session end | Reflect — what can the knowledge system itself improve? |
| **Gear 3** | Milestones | Retrospect — challenge structural assumptions (double-loop learning) |
| **Gear 4** | Project end | Distill — extract universal patterns, contribute back to Myco |

---

## Why Myco

Most AI dev tools operate at **L-exec** (execute faster) or **L-skill** (accumulate skills). Myco is the only tool that operates at **L-struct** and **L-meta** — evolving the knowledge structure itself, and evolving the rules of evolution:

| Level | What It Does | Who Does It |
|-------|-------------|-------------|
| L-exec | Execute faster over time | All agents |
| L-skill | Accumulate new skills | Hermes, OpenClaw, CLAUDE.md |
| **L-struct** | **Evolve knowledge structure** | **Myco (Gear 3)** |
| **L-meta** | **Evolve the rules of evolution** | **Myco (Gear 4)** |

[Mem0's 2026 State of AI Agent Memory report](https://mem0.ai/blog/state-of-ai-agent-memory-2026) explicitly names "memory staleness detection" as an unresolved challenge — systems struggle to identify when high-relevance memories become outdated. That is precisely what `myco lint` solves: 9 structural checks that flag inconsistencies, contradictions, and drift across sessions.

This isn't about replacing memory tools. Mem0 does retrieval brilliantly. Myco does verification and evolution. They're complementary layers.

---

## Works With Your Existing Tools

Myco doesn't replace your stack — it metabolizes it.

| Tool | Integration | What You Get |
|------|-------------|-------------|
| **Claude Code** | `myco migrate --entry-point CLAUDE.md` | Consistency checking + evolution engine on top of your existing CLAUDE.md |
| **Cursor** | File-aware coexistence — no migration needed | `.cursorrules` + Myco live in the same project, no conflicts |
| **GPT / OpenAI** | System prompt injection or ChatGPT Projects | Structured context in every session |
| **Hermes Agent** | `myco import --from hermes ~/skills/` | Skills get lint-verified and evolution-tracked |
| **OpenClaw** | `myco import --from openclaw MEMORY.md` | Memory gets structured and consistency-checked |
| **MemPalace** | L0 retrieval backend (adapter spec available) | Semantic search over Myco-managed knowledge |

---

## Real-World Validation

Myco was born from a real project — an 8-day, 80+ file academic research initiative that went through the complete four-gear evolution cycle. The numbers:

<table>
<tr>
<td align="center"><b>80+</b><br><sub>files managed</sub></td>
<td align="center"><b>10</b><br><sub>wiki pages evolved</sub></td>
<td align="center"><b>15+</b><br><sub>rounds of structured debate</sub></td>
<td align="center"><b>9/9</b><br><sub>lint checks passing</sub></td>
</tr>
</table>

The framework patterns extracted through Gear 4 distillation now live in the Myco codebase itself — the tool literally evolved from its first user's experience. See [`examples/ascc/`](examples/ascc/) for the full lifecycle walkthrough.

---

## The Story Behind Myco

<!-- 
  NOTE TO MAINTAINER: Personalize this section with your own voice.
  The story below is based on the real ASCC project origin. Edit freely.
-->

Day 1. I had a single `CLAUDE.md` — 949 lines, growing with every session. It was everything: project context, decisions, instructions, warnings, all in one file. It worked fine until it didn't.

Day 2. I couldn't find anything. 949 lines and no structure. I split it into layers — an entry point, wiki pages, procedure docs, source code.

Day 3. The moment that changed everything. The same metric appeared in three different places with three different values. My agent had been confidently working with all three. Nobody caught it — not the agent, not me. That's when I built the first version of `myco lint`.

Day 5. Wiki pages were inconsistent. Missing headers, orphaned files, broken references. I added more lint checks — L0 through L8 — and a canonical values file (`_canon.yaml`) as the Single Source of Truth.

Day 7. First milestone retrospective. I discovered that 40% of all friction came from "changed content, forgot to update index." Double-loop learning: the knowledge system evolved its own rules.

Day 8. I realized this system wasn't project-specific. The four layers, the lint checks, the evolution gears — they were universal patterns. I named it Myco, after mycelium: the underground network that keeps entire ecosystems alive by metabolizing nutrients between organisms.

The framework I extracted from that first project now helps every project that uses Myco. That's Gear 4 working — one project's hard-won knowledge becomes another project's starting point.

---

## Contributing

The most valuable contributions aren't code — they're **knowledge evolution products** from real use: battle reports, adapter integrations, wiki templates, and workflow principles.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the four contribution types. The fastest path to a merged PR is a battle report sharing how Myco worked (or didn't) on your project, or an [`adapters/`](adapters/) YAML for a tool you already use.

---

## License

MIT. See [LICENSE](LICENSE).
