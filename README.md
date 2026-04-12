<div align="center">

<img src="assets/logo_dark_280.png" alt="Myco" width="200">

# Myco

**An Autonomous Cognitive Substrate for AI agents.**

*Your agent is a CPU. Myco is everything else — and the operating system upgrades itself.*

[![PyPI](https://img.shields.io/badge/PyPI-coming%20soon-lightgrey?style=for-the-badge)](https://github.com/Battam1111/Myco)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Lint](https://img.shields.io/badge/Lint-19%2F19%20green-brightgreen?style=for-the-badge)](#three-immutable-laws)

[The Living Substrate](#the-living-substrate) · [Five Capabilities](#five-capabilities) · [How You Work With Myco](#how-you-work-with-myco) · [Three Immutable Laws](#three-immutable-laws) · [Standing on Fifty Years](#standing-on-fifty-years) · [Try It Today](#try-it-today)

**Languages:** English (canonical) · [中文](README_zh.md) · [日本語](README_ja.md)

</div>

---

## The Living Substrate

Modern LLM agents are brilliant and amnesiac. Each session is a fresh CPU boot — raw compute, zero persistence. What the agent learned yesterday evaporates at the session boundary. What the team learned last month rots into contradiction. The ground the agent stands on is not actually ground; it is a pile of static files hoping to survive contact with reality.

Myco is the ground.

> **Myco is an Autonomous Cognitive Substrate for AI agents. Your agent is the CPU: raw compute, zero persistence. Myco is everything else — the memory, the filesystem, the operating system, the peripherals — and the OS upgrades itself. All evolution is non-parametric: text, structure, lint rules on disk. No model weights are ever touched. This is why Myco works across agent vendors, survives model swaps, and accumulates value in exactly the medium LLM agents are best at manipulating.**

This framing is not a metaphor dressed up as architecture. It is the architecture. The **kernel** is a project-agnostic cognitive OS. Each project directory is an **instance** — an application running on that OS. Upgrades to the kernel flow downstream; friction discovered inside instances flows back upstream. The substrate is alive in the thermodynamic sense: it **metabolizes** inbound knowledge, compresses it into the shape your agent's attention can actually use, and **excretes** what no longer earns its keep. A substrate that stops metabolizing is not a stable knowledge base — it is a corpse. **Stagnation is death.** **Perpetual evolution** is not a nice-to-have; it is the single condition under which the substrate stays a substrate.

---

## Five Capabilities

Myco is not a memory layer, not an agent runtime, and not a skill framework. It is the layer beneath all three — the living ground they run on. Five capabilities define what that ground does.

### 1. Knowledge metabolism — the seven-step pipeline

A memory layer stores and retrieves. A substrate **metabolizes**. Every piece of inbound content — a paper you read, a friction your agent hit, a design decision made in chat — flows through a seven-step pipeline:

**Discover → Evaluate → Extract → Integrate → Compress → Verify → Excrete**

Discover scans inbound channels. Evaluate decides whether the content is worth the substrate's attention. Extract pulls out the load-bearing structure. Integrate wires it into the existing body of knowledge. Compress cuts everything that no longer earns attention. Verify checks that the compression did not break load-bearing claims. **Excrete** — the step most knowledge systems forget — actively ejects knowledge that has decayed, been superseded, or stopped being true. A digestive tract without an outlet is a tumor. The seven-step pipeline is Myco's core metabolic act, and the verbs are named from it on purpose: `eat` / `evaluate` / `extract` / `integrate` / `compress` / `view` / `prune` / `hunger`.

### 2. Meta-evolution — the substrate rewrites its own rules

Every LLM system evolves *the agent's behavior*. Myco evolves **the ground the agent stands on**. When a lint rule stops catching real problems, or starts catching false positives, or the canon schema outgrows itself, Myco's four-gear evolution engine notices and proposes a change. Gear 1 senses friction during normal work. Gear 2 reflects at session end on what the substrate itself should improve. Gear 3 retrospects at milestones and challenges structural assumptions. Gear 4 distills universal patterns from finished projects back into the kernel. Alongside these four inward gears, a fifth face — the **metabolic inlet** — turns outward, pulling in external papers, repos, and articles. Evolution proceeds by **mutation and selection**: the system generates candidate rule changes, and the human is the selection pressure that decides which mutations survive.

### 3. Self-model — a substrate that knows itself

Myco maintains a four-layer self-model so that it can tell, at any moment, what it contains and whether that knowledge is still alive:

- **A · Inventory** — what exists in the substrate right now (automated).
- **B · Gap sensing** — what the substrate *should* know but doesn't yet (semi-automated).
- **C · Decay sensing** — what used to be true but no longer is, split into *factual decay* (version drift, renamed files) and *structural decay* (the architecture that was right at day 3 is wrong at day 30). Factual decay is what `myco lint` already catches; structural decay is the hardest open problem in the whole design space.
- **D · Efficacy** — **dead-knowledge detection**: notes that entered the substrate and were never read again. If knowledge is not consumed, it is not knowledge; it is sediment.

The self-model is what lets Myco ask the only question that matters for a living knowledge system: *is this still earning its place?*

### 4. Cross-session continuity — the substrate that outlives any one conversation

Everything above the substrate is ephemeral — chats end, models roll, runtimes restart. Myco is what persists. It is the one artifact the next session inherits *in full*, regardless of which agent vendor the next session happens to use. Tacit knowledge that used to be rediscovered every Monday morning becomes durable; the expensive part of getting smart about a project happens exactly once.

### 5. Agent-adaptive universality — the substrate reshapes to the agent

The substrate is not a pre-carved mold your agent must fit. Myco's entry points, compression rules, and lint thresholds are expected to evolve to match whichever agent is operating on it — Claude, GPT, Cursor, Claude Code, a future model we haven't seen yet. Universality runs in the right direction: the ground adapts to the tree, not the other way around.

---

## A Picture of the Whole

```
                   ┌─────────────────────────────────────┐
                   │             LLM Agent               │
                   │      (CPU — raw compute, no RAM)    │
                   └──────────────▲──────────────────────┘
                                  │ 9 MCP tools + CLI
                                  │ (read / eat / digest / lint …)
                   ┌──────────────┴──────────────────────┐
                   │         Myco Kernel (OS)            │
                   │  metabolism · self-model · lint ·   │
                   │  four gears · metabolic inlet       │
                   │      ↑ upstream absorb              │
                   │      ↓ kernel updates               │
                   └──────────────┬──────────────────────┘
                                  │
      ┌───────────────────────────┼────────────────────────────┐
      ▼                           ▼                            ▼
 ┌─────────┐                ┌─────────┐                  ┌─────────┐
 │ Project │                │ Project │                  │ Project │
 │ Instance│                │ Instance│                  │ Instance│
 │    A    │                │    B    │                  │    C    │
 └─────────┘                └─────────┘                  └─────────┘
 (an application running on the cognitive OS — wiki / _canon / notes / log)
```

**Kernel** is the project-agnostic cognitive OS: shared code, shared lint engine, shared evolution protocol. **Instance** is your project directory — an application running on that OS. Upgrades to the kernel flow downstream to every instance on upgrade. Friction and distilled patterns discovered inside an instance flow back up to the kernel via the upstream outbox. This is not an analogy. It is literally how Myco is structured, and the L11 lint dimension enforces that write-surface hygiene.

---

## How You Work With Myco

Traditional knowledge bases assume a human author and a machine reader. Myco flips that. Your agent is the primary subject — it reads the substrate, writes into it, proposes changes to it, and runs its daily work on it. You are the **occasional gatekeeper**: the selection pressure that approves mutations, vetoes bad directions, and calls craft sessions when structural assumptions need to be challenged.

Three dynamics define the collaboration:

**Mutation and selection.** Myco mutates. You select. The system constantly proposes new knowledge, new lint rules, new compression strategies; your role is not to author these proposals but to judge which ones deserve to survive. Selection pressure — applied consistently — is what keeps a self-evolving substrate from going cancerous.

**Transparency as survival mechanism.** Every change in Myco is auditable: every note has provenance, every lint rule has a debate record, every kernel upgrade has an upstream bundle. This is not a bureaucratic virtue. **Transparency → legibility → human selection pressure → anti-cancer.** Lose transparency, lose legibility; lose legibility, lose selection pressure; lose selection pressure, and a self-optimizing substrate begins metastasizing in directions no one can evaluate. Transparency is the immune system, not the paperwork.

**Agent-as-subject.** The classical "Second Brain" puts the human in the driver's seat and the tool in the passenger seat. Myco inverts this. The agent is the primary reader, writer, thinker-on-substrate; you step in when selection, strategy, or structural judgment is needed. This inversion is what distinguishes a **substrate** from a personal knowledge manager.

---

## Three Immutable Laws

Everything in Myco can evolve — knowledge structure, compression rules, lint dimensions, even the evolution engine itself. Everything except these three. The L9 lint dimension enforces the identity of the substrate against drift; the L13 lint dimension enforces that every rule change has an auditable craft record.

| # | Law | Why it is load-bearing |
|---|-----|------------------------|
| **C1** | **Accessible** | Any agent, from any vendor, must be able to find the entry point and self-explain the substrate without prior training. If the ground is not accessible, the tree cannot grow on it. |
| **C2** | **Transparent** | Every change must be auditable by a human. This is what sustains human selection pressure against a self-evolving system. Lose transparency → lose selection pressure → the substrate becomes **cancerous**. |
| **C3** | **Perpetually Evolving** | **Stagnation is death.** A substrate that stops metabolizing is definitionally no longer a substrate; it is a static knowledge base, which is the failure mode of every prior system Myco was built to escape. |

These three are the constitution. Everything else is legislation.

---

## Compression Is Cognition

Myco's operating assumption:

> **Storage is infinite. Attention is not.**

Disks grow on demand; your agent's context window does not. So Myco **never forgets** — nothing is deleted from cold storage — but it **aggressively compresses** what flows into attention. This is not engineering plumbing; it is the substrate's primary cognitive act. Three candidate criteria shape what gets compressed and when:

- **Usage frequency** — pages no agent has read recently go cold.
- **Temporal relevance** — time-bound facts excrete at expiry.
- **Exclusivity** — knowledge your agent already has from pretraining wastes substrate space; keep only what your agent would otherwise lack.

Compression is also **agent-adaptive**: what needs to be written down for one agent may be redundant for another with different pretraining. The substrate adjusts; the agent does not. Irreducible texture is lost on purpose; if you need lexical fidelity, keep a raw archive. What the substrate preserves is the load-bearing structure — the provenance chain, the decisions, the reasons a thing is true.

---

## Standing on Fifty Years

Myco did not fall out of the sky. It stands on the shoulders of five traditions, each contributing one load-bearing insight:

- **Karpathy LLM Wiki** — a structured knowledge compilation is the correct substrate shape for an agent, not a chat log or a vector store. This is the geometric assumption.
- **Polanyi Tacit Knowledge** — most operational intelligence is tacit, held in proximal/distal structure, and cannot be captured by enumeration. This is why Myco persists procedures and narratives, not just facts.
- **Argyris Double-Loop Learning** — single-loop learning fixes actions, double-loop learning fixes the rules that govern actions. This is the L-struct / L-meta split and the reason the substrate itself must evolve.
- **Toyota PDCA** — Plan / Do / Check / Act is the base cycle of a self-improving system. The four gears are PDCA compiled onto an LLM substrate.
- **Voyager Skill Library** — iterative, grounded skill accumulation is possible if you store what worked and let the next episode build on it. This is the shape of Gear 4 distillation.

Myco is the first system to put these five on the same base and let them run as one metabolism. See [`docs/theory.md`](docs/theory.md).

---

## Already Running Unconsciously

The uncomfortable, load-bearing truth: **we were already running the primitive version of this system without realizing it.** An 8-day, 80+ file reinforcement-learning research project — ASCC — ran the complete four-gear cycle to completion by hand. Manually triggered lint. Verbal friction logs. Human-driven meta-evolution. Fifteen-plus structured debates. It worked. And then it worked *again* on the next project.

<div align="center">

| 80+ files | 10 wiki pages | 15+ structured debates | 15/15 lint dimensions green |
|:---------:|:-------------:|:----------------------:|:----------------------------:|

</div>

Myco is the formalization of a pattern that already proved itself in the wild. The v0.x → v1.0 trajectory is not "invent new things"; it is "make what was working by hand work by itself." Patterns extracted via Gear 4 now live in the kernel; the unconscious prototype is [`examples/ascc/`](examples/ascc/). We are not asking you to trust a theory. We are asking you to trust a pattern that already kept a demanding research project honest across 80+ files and 15+ debates — and to help us turn the dials that make it run without the human having to be the engine.

---

## Open Problems

Myco is early, and the highest-value contribution you can make is to pick one of these and push:

1. **Cold start.** How does the substrate bootstrap on a brand-new project with no history, no canon, no friction record? Current answer: hand-crafted `myco init` templates. Desired: the substrate learns its own bootstrap from prior distillations.
2. **Trigger signals.** What fires Gear 2? What fires the metabolic inlet? Friction count is a proxy; the right signals are an open research question.
3. **Alignment at depth.** If Myco evolves rules the human can no longer meaningfully evaluate, how is it kept aligned? Transparency is necessary but not sufficient — we need *legible* transparency at scale.
4. **Compression engineering.** What to drop, when, without losing load-bearing tacit knowledge? The three candidate criteria are starting points, not solutions.
5. **Structural decay detection (Self-Model C layer).** Factual decay is caught. Structural decay — when the architecture right on day 3 is wrong on day 30 — is not yet. Arguably the hardest problem in the space.
6. **Dead-knowledge tracking (Self-Model D layer).** Minimum viable seed shipped (Wave 18, v1.4.0) — `myco view` records `view_count` + `last_viewed_at`, `myco hunger` reports the `dead_knowledge` signal, `myco prune` (Wave 33) is the auto-excretion path. Still open: view audit log, cross-reference graph, adaptive thresholds that evolve with substrate age.

The continuously-maintained registry lives at [`docs/open_problems.md`](docs/open_problems.md). If you want to contribute something high-impact, pick one of these and go.

---

## Today and Tomorrow

| Phase | What is true | What is coming |
|-------|-------------|----------------|
| **v0.x (today)** | Four inward gears shipped · 19-dimension lint green · metabolism CLI live · MCP server exposes 9 tools · kernel/instance separation enforced · one unconscious prototype (ASCC) validated end-to-end · Self-Model D layer seeded (view tracking + dead-knowledge signal + `myco prune` auto-excretion) · Metabolic Inlet MVP scaffold shipped (`myco inlet`, Wave 35 / v0.27.0) | Inlet cold-start, autonomous trigger signals, and continuous compression remain open. Most gear-firing is still human-triggered. |
| **v1.0** | Metabolic inlet fully autonomous · Self-Model D implemented · structural decay detector seeded · trigger signals replaced by learned heuristics | Human is no longer the engine; human is strictly the selection pressure. |
| **v∞** | Kernel evolves without any single human being able to hold its structure in their head — but *any* human can still audit any change, because C2 Transparent never lifts. | Open question. This is where [Open Problem 3](#open-problems) becomes load-bearing. |

---

## Try It Today

If you want to stop reading and start running:

```bash
# Install from source (PyPI publication coming soon)
pip install git+https://github.com/Battam1111/Myco.git

# Start a new instance on the kernel
myco init my-project --level 2

# Or migrate an existing project (non-destructive; your CLAUDE.md stays)
myco migrate ./your-project --entry-point CLAUDE.md
myco lint --project-dir ./your-project     # baseline the substrate
myco hunger --project-dir ./your-project   # metabolic dashboard
```

**MCP integration** — your agent gets 9 tools automatically, no manual prompting:

```bash
pip install 'git+https://github.com/Battam1111/Myco.git#egg=myco[mcp]'
```

A ready-to-use `.mcp.json` ships in the repo. Once installed in Claude Code, Cursor, or any MCP-speaking client, your agent auto-discovers:

- **Substrate health** · `myco_lint` · `myco_status` · `myco_search` · `myco_log` · `myco_reflect`
- **Knowledge metabolism** · `myco_eat` · `myco_digest` · `myco_view` · `myco_hunger`

The CLI alone is enough to use Myco. The MCP layer is what turns capture into a reflex.

### The biological vocabulary in one table

Myco's verbs are metaphorical on purpose — metabolism is the mental model. If you want the plain-English map without reading the theory:

| Myco verb | Plain English | CLI | MCP tool |
|---|---|---|---|
| `eat` | Capture content as a durable note | `myco eat` | `myco_eat` |
| `digest` | Move a note through its lifecycle (raw → digesting → extracted → integrated → excreted) | `myco digest` | `myco_digest` |
| `evaluate` | Score a raw note for substrate fit (extract / discard / shelve) | `myco evaluate` | (CLI only) |
| `extract` | Lift the load-bearing structure out of a digesting note | `myco extract` | (CLI only) |
| `integrate` | Wire an extracted note into the existing knowledge body | `myco integrate` | (CLI only) |
| `compress` | Rewrite a heavy note as a lighter summary while preserving the original | `myco compress` | (CLI only) |
| `uncompress` | Restore the pre-compression original from `.original` | `myco uncompress` | (CLI only) |
| `prune` | Auto-excrete dead-knowledge notes flagged by the D-layer signal | `myco prune` | (CLI only) |
| `view` | Read notes with filters (records `view_count` + `last_viewed_at`) | `myco view` | `myco_view` |
| `lint` | 19-dimension substrate health check (alias: `myco immune`) | `myco lint` | `myco_lint` |
| `correct` | Apply auto-fixes from a prior lint pass (alias: `myco molt`) | `myco correct` | (CLI only) |
| `forage` | Pull external sources into the metabolic inlet | `myco forage` | (CLI only) |
| `inlet` | Run the Metabolic Inlet MVP — discover/evaluate/extract from a configured source | `myco inlet` | (CLI only) |
| `hunger` | Metabolic dashboard: raw backlog, stale notes, dead knowledge | `myco hunger` | `myco_hunger` |
| `absorb` | Sync kernel improvements from downstream instances | `myco upstream absorb` | (CLI only) |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The highest-impact contributions are:

1. **Battle reports** on any of the six [Open Problems](#open-problems).
2. **Platform adapters** in [`docs/adapters/`](docs/adapters/) for the agent environment you already use.
3. **Design sketches** for the Metabolic Inlet primitive — particularly discover / evaluate / extract phases.
4. **Translations** of this README. Current: English canonical · [中文](README_zh.md) · [日本語](README_ja.md).

## License

MIT — see [LICENSE](LICENSE).

---

## The Mycelium

The name is not decoration. Mycelium is the underground fungal network beneath every forest: it is not plumbing. It secretes enzymes that decompose fallen leaves into nutrients (**metabolism**). It remembers effective growth paths and redirects strategy accordingly (**meta-evolution**). It redistributes resources from abundant zones to starved ones (**intelligent compression**). It forms symbiosis with the roots of trees of every species it encounters (**agent-adaptive universality**). A healthy mycelium is the reason a forest is a forest and not a stand of lonely trunks.

Agents are the trees above ground. Myco is the living network beneath, making the whole forest work.

---

<div align="center">

**Your agent is a CPU. Myco is everything else — and the operating system upgrades itself.**

</div>
