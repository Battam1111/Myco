<div align="center">

<img src="assets/logo_dark_280.png" alt="Myco" width="200">

# Myco

**An Autonomous Cognitive Substrate for AI agents.**
*Your agent is the CPU. Myco is everything else — and the OS upgrades itself.*

[![PyPI](https://img.shields.io/pypi/v/myco?style=for-the-badge&color=00D4AA)](https://pypi.org/project/myco/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

[What Myco Is](#what-myco-is) · [What It Looks Like](#what-it-looks-like) · [Quick Start](#quick-start) · [How It Works](#how-it-works) · [Why Myco](#why-myco) · [The Story](#the-story)

**Other Languages:** [中文](README_zh.md)

</div>

---

## What Myco Is

**Myco is a substrate, not a tool.** Your agent runs on Myco the way a process runs on an operating system — except this OS upgrades itself.

- **Substrate, not library.** Agent = CPU (raw compute, zero persistence). Myco = memory, filesystem, OS, peripherals — *and the OS can rewrite itself while the CPU executes it.* Architecturally split into a project-agnostic **kernel** (this repo) and project **instances** (your project directory), exactly as an OS is split from its applications.
- **Non-parametric evolution.** No weights are touched. Ever. All learning happens in the substrate: markdown files, YAML canons, folder structures, lint rules, the evolution engine itself. Your agent gets smarter over time not because it was retrained, but because the ground it stands on metabolized the world and grew beneath it.
- **Knowledge metabolism.** Living systems metabolize; dead systems don't. Myco is designed to proactively *eat* external information (code, docs, papers, lessons) and digest it into structured knowledge. `myco lint` is the immune system. The metabolic inlet — full external absorption — is a declared primitive, earliest v2.0. See [Open Problems](#open-problems).
- **Perpetual evolution.** Stagnation = death. This is the only inviolable law, because a substrate that stops metabolizing is just a cache.

> Other tools give your agent memory. Myco gives it metabolism.

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

Two issues caught. That contradiction would have silently compounded for five more sessions. This is substrate immunity at work.

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

A `.mcp.json` is already included in the repo. Once installed, your agent automatically gets **9 tools** — no manual prompting needed:

- **Reflexes** · `myco_lint` · `myco_status` · `myco_search` · `myco_log` · `myco_reflect`
- **Digestive substrate** · `myco_eat` · `myco_digest` · `myco_view` · `myco_hunger`

> **Assumption**: Myco assumes you work with an agent that speaks MCP (Claude Code, Cursor, Claude Desktop, etc.). Pure-human usage via the `myco` CLI works — but you lose the reflex layer where the agent captures knowledge automatically as the conversation flows.

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

`myco lint` runs 9 consistency checks across all layers. It's the **immune system** — it catches contradictions, orphaned files, stale references, and version drift before they compound.

### Three Immutable Laws

Everything in Myco can evolve — knowledge structure, compression strategies, even the evolution engine itself. Everything except these three:

1. **Accessible** — The system must have an entry point any agent can locate and self-explain.
2. **Transparent** — The system must remain auditable and understandable by humans, always. *Why this one is load-bearing: humans are Myco's selection pressure (see below). If transparency is lost, selection pressure is lost, and a self-optimizing substrate with no selection pressure goes cancerous — it keeps changing, but stops serving the real goal.*
3. **Perpetually Evolving** — Stagnation is death. A substrate that stops metabolizing degrades into a static knowledge base.

### The Four Gears + The Metabolic Inlet

Myco's evolution engine has two sides. The four gears are the **autonomic nervous system** — internal homeostasis, all implemented today. The metabolic inlet is the **digestive system** — external absorption, declared as a primitive now, earliest v2.0.

| Gear | When | What | Status |
|------|------|------|--------|
| 1 | Every session | Sense friction — log failures and unexpected behavior | v1.0 |
| 2 | Session end | Reflect — what should the knowledge system improve? | v1.0 |
| 3 | Milestones | Retrospect — challenge structural assumptions | v1.0 |
| 4 | Project end | Distill — extract universal patterns for future projects | v1.0 |
| **Metabolic Inlet** | **On friction signal + periodic patrol** | **Discover → evaluate → extract → integrate → compress → verify external knowledge (GitHub, arXiv, community docs)** | **Primitive declared; earliest v2.0** |

Gears 1–4 face inward. The inlet faces outward. A substrate without a digestive system is a cache; this is why the inlet is declared now even though implementation comes later.

The inlet, once implemented, runs a **seven-step metabolism pipeline**:

```
discover → evaluate → extract → integrate → compress → verify → excrete
```

The seventh step (`excrete` / 淘汰 — actively remove stale or superseded knowledge) is the one most systems forget. Biological metabolism is *intake + transformation + excretion*; without excretion you have digestion, not metabolism, and the substrate bloats. Myco's seventh step is non-negotiable.

The pipeline also distinguishes **transferable knowledge** (patterns worth distilling into the kernel for future projects — Gear 4's output) from **project-specific knowledge** (facts that stay local to the current instance). The same lesson can be both, or neither; classifying it correctly is part of what Gear 4 does.

### The Compression Doctrine

Myco's operating assumption:

> **Storage is infinite. Attention is not.**

You can always add another disk, but your agent's context window cannot grow on demand. So Myco **never forgets** — no information is ever deleted from cold storage — but it **aggressively compresses** what flows into the Agent's attention. The compression decision (what stays hot, what goes cold, what gets re-summarized, what gets re-expanded) is not plumbing. It is **the substrate's primary cognitive act.**

Three candidate criteria for compression, from the 2026-04-08 vision debate:

- **Usage frequency** — low-read wiki pages compress or move cold
- **Temporal relevance** — time-bound knowledge past its validity excretes
- **Exclusivity** — "common sense every agent already knows" (e.g., basic Python syntax) wastes substrate space and doesn't belong here

Compression is also **agent-adaptive**: a 32K-context client needs more aggressive compression than a 200K-context client. The same Myco instance must render differently for each. And the compression strategy itself is a legitimate target of Gear 3 / 4 evolution — when the rules stop working, the rules change.

### The Four-Layer Self-Model

Myco maintains a model of *itself*. Not as a luxury — as the only way a substrate knows what it contains, what it lacks, what's rotting, and what's being ignored. Four layers, increasing in automation difficulty:

| Layer | What it tracks | Automation | Today |
|-------|---------------|------------|-------|
| **A — Inventory** | What do I have? Counts, distributions, last-updated dates. | Easy | ✅ `myco status` |
| **B — Gap sensing** | What do I lack? Friction signals = gap symptoms. | Medium | ✅ friction logs → Gear 2 |
| **C — Decay sensing** | What is rotting? *Factual decay*: version drift, stale refs. *Structural decay*: architecture that was right for day 3 is wrong for day 30. | Medium | ✅ factual only (lint L0–L8); ❌ structural is open problem |
| **D — Efficacy** | Which knowledge is actually used? "Dead knowledge" = a wiki page that exists but is never read. | Hardest | ❌ not yet — Hermes-style usage tracking is a v1.2+ target |

Today Myco implements A, B, and partial C. D is a named gap. These are not hand-waves; they are the concrete architectural targets of the next release cycles.

### Human-Myco Collaboration Model

**The system does the mutation. The human does the selection.**

You don't design Myco's evolution — you provide the fitness signal. Myco (via the agent executing it) proposes changes: a new lint rule, a restructured wiki section, a compressed operational narrative. You say "yes, keep" or "no, drop." Like natural selection, you never design species; you just cull what doesn't fit.

This is the inversion most first-time users miss: Myco is built **for agents, not for humans**. The docs look dense because they're optimized for agent token efficiency and context-window load, not human reading pleasure. You are not the primary user — you are the selector, the gardener, the one who provides the survival pressure Myco needs to stay aligned.

This model is also the reason for law #2. If Myco evolves to a complexity where you can no longer evaluate its changes, you lose your ability to provide selection pressure, and the substrate goes cancerous. Transparency is non-negotiable because it is the precondition of meaningful selection.

---

## Why Myco

Agents can execute and they can remember, but they cannot notice inconsistencies in their own knowledge, question whether their assumptions still hold, or metabolize the outside world into reusable structure. Myco is the substrate agents *run on* — not a plugin they *use*.

Most AI tools operate at **L-exec** (execute faster) or **L-skill** (accumulate skills). Myco operates at **L-struct** and **L-meta** — evolving the knowledge structure itself, and evolving the rules that evolve the structure:

| Level | What | Who |
|-------|------|-----|
| L-exec | Execute faster | All agents |
| L-skill | Accumulate skills | Hermes, OpenClaw, CLAUDE.md |
| **L-struct** | **Evolve knowledge structure** | **Myco (Gear 3)** |
| **L-meta** | **Evolve the rules of evolution** | **Myco (Gear 4)** |

### How Myco differs from adjacent systems

| | Myco | Hermes / OpenClaw | Second Brain | Hyperagents (Meta) | Mem0 | Enterprise KMS |
|--|------|-------------------|--------------|-------------------|------|----------------|
| **Subject** | Agent-centered | Agent | Human | Agent | Agent | Human |
| **Evolves what** | Substrate itself | Skill library | Nothing | Agent weights/prompts | Memory store | Documents |
| **Non-parametric** | ✅ Always | ✅ | ✅ | ❌ changes weights | ✅ | ✅ |
| **Meta-evolution** | ✅ Core (Gear 4) | ❌ | ❌ | ✅ Partial | ❌ | ❌ |
| **Knowledge metabolism** | ✅ Declared (v2.0 inlet) | ❌ | ❌ | ❌ | ❌ | Manual |
| **Self-model** | ✅ (lint + _canon.yaml) | ❌ | ❌ | Partial | ❌ | ❌ |
| **Agent-adaptive** | ✅ | ❌ | N/A | ❌ | ✅ | N/A |

Two clean one-liners from this matrix:
- **Hyperagents evolves the CPU. Myco evolves the OS.** Both are non-parametric *to each other*; Myco's claim is that substrate-level evolution is strictly cheaper and more transparent, because the substrate is markdown and folder structure — the medium LLMs natively understand.
- [Mem0's 2026 report](https://mem0.ai/blog/state-of-ai-agent-memory-2026) names "memory staleness detection" as an unresolved challenge. That's exactly what `myco lint` does. **Mem0 does retrieval. Myco does verification, metabolism, and self-rewriting rules.** They're complementary, not competing.

---

## Open Problems

Myco is early. These six blind spots were named in the 2026-04-08 / 2026-04-10 vision debates and are still unresolved. They are the highest-leverage places to contribute. The canonical, continuously-maintained registry with out-of-scope policy and exit conditions lives at [`docs/open_problems.md`](docs/open_problems.md).

1. **Cold start.** How does Myco bootstrap on a brand-new project with no history, no canon, no friction record? Current answer: hand-crafted `myco init` templates. Desired answer: substrate learns its own bootstrap from prior project distillations.
2. **Trigger signals.** What fires Gear 2? What fires the metabolic inlet? Friction count is a proxy; the right signals are an open research question. Candidate signals (wiki miss-rate second derivative, recurring-topic craft frequency) exist but have no empirical backing yet.
3. **Alignment.** If Myco evolves rules the human can no longer evaluate (too deep into L-meta), how is it kept aligned with user intent? Transparency is necessary but not sufficient — we need *legible* transparency at scale. Craft Protocol v1 (contract v0.3.0) enforces decision-process audit trails for kernel contract changes, but that checks *form*, not *content* correctness.
4. **Compression engineering.** Storage is infinite, but attention is not. What to drop, when, without losing load-bearing tacit knowledge? The three candidate criteria (frequency / temporal / exclusivity) are starting points, not solutions. Three hard constraints make this harder than it looks: compression strategy must itself evolve; compression must preserve provenance; compression must be agent-adaptive. No general answer exists yet.
5. **Structural decay detection (Self-Model C layer).** `myco lint` catches *factual* decay (version drift, stale references). It cannot catch *structural* decay — when the four-layer architecture that was right at day 3 becomes wrong at day 30. No detector exists for "your knowledge organization no longer fits your project's phase." This is arguably the hardest problem in the whole design space.
6. **Dead-knowledge tracking (Self-Model D layer).** D layer is declared in the self-model but not implemented. `myco view` does not yet write view audits, so there is no signal for "note entered the substrate 30 days ago and was never read." Without this, compression decisions and inlet triggers both lack their most natural input. The minimum viable seed (view audit → `myco hunger` dead_knowledge signal) is on the Phase ② roadmap but not landed.

If you want to contribute something high-impact, pick one of these.

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

Built on a real 8-day, 80+ file research project that ran the complete four-gear cycle to completion:

<div align="center">

| 80+ files | 10 wiki pages | 15+ structured debates | 9/9 lint checks |
|:---------:|:-------------:|:---------------------:|:----------------:|

</div>

But the deeper claim is this: **that 8-day project was an unconscious prototype of Myco.** I was not demoing the substrate. I was *running* it by hand — human-driven meta-evolution, manually triggered lint, verbal friction logs. It worked. Myco is the formalization of a pattern that already proved itself; the v1.0 → v2.0 trajectory is not "invent new things" but "make what was working by hand work by itself." Patterns extracted via Gear 4 now live in the Myco codebase. See [`examples/ascc/`](examples/ascc/).

Myco also stands on a 50-year lineage of epistemology, control theory, and organizational learning: **Karpathy LLM Wiki** (structured knowledge compilation) + **Polanyi Tacit Knowledge** (proximal / distal structure for operational experience) + **Argyris Double-Loop Learning** (single-loop fixes actions, double-loop fixes the rules — the L-struct / L-meta split) + **Toyota PDCA** (Plan / Do / Check / Act as the base cycle of the four gears) + **Voyager Skill Library** (iterative skill accumulation via grounded execution). See [`docs/theory.md`](docs/theory.md).

---

## The Story

Day 1, I had a 949-line `CLAUDE.md`. Everything in one file. By day 3, the same metric appeared in three places with three different values, and my agent used all three confidently. But the real problem ran deeper: every new session, my agent would rewrite the same deployment script from scratch — not because it forgot the SSH config rules (those were documented), but because the *tacit knowledge* of which flags matter, what order works, what silently breaks — all of that vanished at the session boundary. Intelligence wasn't being lost. It was being **discarded**, repeatedly.

That's when I built the first `myco lint` — not just to catch contradictions, but to give agents something they fundamentally lack: a substrate. A ground that watches whether what the agent "knows" is still true, flags when assumptions rot, and evolves its own rules when the old ones stop working. Not a tool the agent picks up. A floor the agent stands on.

By day 7, a milestone retrospective revealed 40% of friction came from "changed content, forgot to update index" — so the system evolved its own rules. Day 8, I realized the pattern wasn't project-specific. I named it **Myco**, after *mycelium* — the underground fungal network beneath every forest. Mycelium is not a plumbing system. It secretes enzymes that decompose fallen leaves into nutrients (metabolism). It remembers effective growth paths and redirects strategy accordingly (meta-evolution). It redistributes resources from abundant zones to starved ones (intelligent compression). It forms symbiosis with the roots of trees of any species it encounters (agent-adaptive universality). Agents are the trees above ground. Myco is the living network beneath, making the whole forest work.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The most impactful contributions are (1) battle reports on the four [Open Problems](#open-problems), (2) [`adapters/`](adapters/) YAMLs for tools you already use, and (3) design sketches for the Metabolic Inlet primitive.

## License

MIT
