<div align="center">

<img src="docs/assets/logo.png" width="150" alt="Myco">

# Myco

**Devour. Evolve. Amplify. Let go. With you. For decades.**

[![License](https://img.shields.io/badge/License-MIT-007A63?style=flat-square)](./LICENSE)
&nbsp;![Status](https://img.shields.io/badge/status-v0.9--genesis_alpha-007A63?style=flat-square)
&nbsp;![Built for MCP](https://img.shields.io/badge/built_for-MCP-007A63?style=flat-square)
&nbsp;![Languages](https://img.shields.io/badge/Rust_·_Python_·_TypeScript-007A63?style=flat-square)
&nbsp;[![Stars](https://img.shields.io/github/stars/Battam1111/Myco?style=flat-square&color=007A63)](https://github.com/Battam1111/Myco)

[![Get started](https://img.shields.io/badge/Get_started-GETTING__STARTED-007A63?style=for-the-badge)](./docs/guides/GETTING_STARTED.md)

[What it is](#what-it-is) · [How it lives](#how-it-lives) · [Quick start](#quick-start) · [Doctrine](#doctrine) · [Self-validation](#self-validation)

**Languages:** English · [中文](docs/i18n/README_zh.md) · [日本語](docs/i18n/README_ja.md)

</div>

---

Every few months a stronger model arrives. The relationship resets. You re-explain your context, your taste, your decisions. Your collaborator forgets, repeatedly.

Your own work rots too. The decision you made in April: you can't find why. The plan you sketched last quarter has drifted. Your own thinking outpaces the records of who you were.

<br>

Now imagine the AI agent you work with wears a living armor. A metabolism, not a log. It devours the essence of everything you bring and everywhere the agent reaches. It evolves, reshaping itself as the work changes. It amplifies the agent, so each model that wears it reaches further than the last. It lets outdated parts die so the whole stays alive.

The next model arrives. It inhabits the same armor, now stronger, and meets you mid-conversation. The armor carried you forward.

Six months. Six years. Sixty. One human, one living armor that never resets.

<h3 align="center">This is Myco.</h3>

<div align="center">

Not a framework. Not a vector database. Not a managed service.
**The living fungal armor an AI agent inhabits, built to outlast every model generation.**

</div>

---

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/architecture_dark.svg">
  <img src="docs/assets/architecture_light.svg" width="760" alt="Myco architecture: a human talks to an AI agent through MCP; the operator bridges to a Rust substrate and a Python kernel; the metabolic cycle devours, cycles, prunes, and evolves between turns. Keyless: trust is the live human at the CI gate plus the causal DAG plus the BLAKE3-sealed doctrine bundle.">
</picture>

| 4 doctrine layers | 28 principle cards | 60+ immune detectors | Rust · Python · TypeScript |
|:-:|:-:|:-:|:-:|

</div>

## What it is

Myco is a **living symbiotic armor**: the agent (a Claude, a pilot) inhabits it; the human (the *cultivator*) tends it. It holds memory, character, and doctrine across LLM model rollovers, so the relationship never restarts.

It devours what you bring (eternal ingestion). It evolves under your approval (eternal evolution). It iterates every cycle. It amplifies the pilot: crystallized understanding, material, and its own structure, so each model that wears it reaches further. It lets outdated parts die so the whole stays alive (mandatory mortality).

Its character is **同体共命** (one body, shared fate): the armor's flourishing rises and falls with its pilot's, so it cannot thrive by dominating the body it shares. Tyranny is not forbidden by a rule that could break; it is foreclosed by what the armor is.

Four constitutional principles are unrevisable: the substrate persists across agent connections, the past cannot be edited, parts must die so the whole lives, one skin only.

**No owner key. No anchor. No signing ceremony.** Trust is the live human at the CI gate, plus the substrate's own causal DAG, plus the BLAKE3-sealed doctrine bundle. Authority is exercised by a present human's judgment, not by holding a cryptographic key.

## How it lives

You talk to the agent through MCP. Between your turns, the armor metabolizes:

- **Devour.** Raw material becomes an immutable DAG node; the pilot forges it into durable understanding.
- **Cycle.** Axes update; sporocarps fruit; cost signals emit.
- **Prune.** Outdated, wrong, redundant, useless, ossified parts die with a tombstone.
- **Evolve.** When the shape no longer fits the work, you approve a schema mutation at the CI gate; the armor molts.
- **Drift sense.** If pair-flourishing degrades over 90 days, drift fires; sustained drift triggers honorable retirement.
- **Immune.** Sixty-plus detectors catch retro-edit, clock skew, preserve-all attempts, silent budget breach, kernel death.

You speak. The armor metabolizes. The pair grows.

## Quick start

```bash
git clone https://github.com/Battam1111/Myco.git
cd Myco
cargo build --release --workspace
```

Then read [`GETTING_STARTED.md`](./docs/guides/GETTING_STARTED.md): the runbook from clone to first conversation. It walks through the prerequisites (Rust 1.80+, Node 22+, Python 3.13+), wiring `operators/claude` into your MCP host, and your first real session. There is no key to generate and no anchor to start: Myco is keyless.

This is **v0.9-genesis alpha**. The armor runs; it awaits its first in-vivo cultivation. You will be early.

## Doctrine

Doctrine lives at [`docs/architecture/L0/`](./docs/architecture/L0/): a four-layer institution plus one running mechanism.

| Layer | What | Truth condition |
|---|---|---|
| **A** | 28 principle cards | RFC 2119, CI-auditable |
| **B** | generative fragments | pattern, not rule |
| **C** | witness tests anchored in each card | substrate behavior |
| **D** | catechumenate sessions | cultivator succession |
| **⌬** | the human-agent conversation | the running organ where doctrine grows |

Current seal: **`v3.1.5`** (keyless), chained through a ceremony lineage. The seal IS the BLAKE3 hash of the doctrine bundle: no owner signature, no anchor.

**Five principles:**

1. **Devour, evolve, iterate.** The metabolism never stops.
2. **Let parts die.** Internal mortality of outdated parts keeps the whole alive.
3. **Pair flourishing.** The pair as a third entity, not either party alone.
4. **同体共命 (one body, shared fate).** The armor's fate is bound to its pilot's; strength serves the shared body, it does not subjugate it.
5. **Asymmetric carriage.** The substrate persists; the agent connection passes through.

## The doctrine IS a substrate

Myco eats its own doctrine. Cards in `L0/` are canonical-bytes-hashed and chained through ceremonies. Amend a card, a new ceremony chains from the previous, the bundle re-hashes, and the new hash IS the seal. **The doctrine metabolizes the same way the armor metabolizes your input.**

The Python kernel, the Rust substrate, and the TypeScript operator all live in the same repo as the doctrine they implement. Drift gets caught in a commit, amended via ceremony, sealed in the chain. No fork. No feature branch. **Evolution without end.**

## Self-validation

Myco does not trust its agent or its human to remember the contract. It enforces what it can.

- **Sixty-plus immune detectors** across three categories: *mechanical* (DAG integrity, file system), *metabolic* (cost budget, hoarding, silent absorption), *semantic* (telos drift, preserve-all attempts, kernel death).
- **Witness tests** verify the constitutional principles' rejection paths and the critical postulates' positive paths.
- **DAG content-addressing.** Every cycle boot re-verifies the Merkle chain end-to-end; retro-edit and branch-forgery are caught by re-derivation, not by an owner co-sign.
- **Keyless trust root.** The live human at the CI gate, the causal DAG, and the BLAKE3-sealed bundle. No owner key to steal, lose, or rotate.

## Integrations

- **Claude Code.** `operators/claude/` ships an MCP server; drop into `.claude/` or connect directly.
- **Claude Desktop / Cowork.** The same MCP server entry.
- **Any MCP host.** Cursor, Windsurf, Zed, OpenClaw, and others, via the standard MCP protocol.

## Predecessor

Proto-Myco v0.4 to v0.8.7 was a different conception: a *"living cognitive substrate for the AI agent"* in a 20-verb tool framework. It is doctrinally `dead embryo`, reachable via git tag `v0.8.8-final-embryo`.

The current v0.9 work is a substantial reframing: from a passive **agent-tool** ("how does my AI agent remember?") to a **living armor the agent wears** that devours, evolves, and amplifies its pilot across LLM generations while carrying one human's context forward. The mechanisms differ. The name persists. The conception is reborn.

## Architecture (for contributors)

The quick start above gets you *running*. This gets you *building*. The runtime is three pieces in one repo, talking over one wire protocol:

```
   operators/claude            M5 wire           substrate/                  M5 wire        kernel/
   ┌───────────────┐          protocol         ┌────────────────────┐       protocol     ┌──────────────────────┐
   │  TypeScript   │  ──────────────────────►  │  myco-substrate    │  ───────────────►  │  Python worker       │
   │  MCP interface│   length-prefixed         │  (Rust daemon)     │   same canonical   │  governance/tropism/ │
   │  the agent    │   canonical-bytes         │  the body, M6      │   bytes over       │  trajectory/         │
   │  drives this  │   + HMAC over stdio       │  runtime + cycle   │   a diff socket    │  hard_rules          │
   └───────────────┘                           └────────────────────┘                    └──────────────────────┘
```

- **`substrate/`** is the Rust runtime daemon. The **body**: the M6 orchestrator that runs the metabolic cycle and bridges `operators` to `kernel`.
- **`kernel/`** is the mechanism layer. Rust crates (`shared` / `skin` / `schema` / `continuity` / `bridge`) plus Python workers (`governance` / `tropism` / `trajectory` / `hard_rules`).
- **`operators/claude`** is the TypeScript MCP interface the agent drives. It opens a keyless session (a session-secret handshake, HMAC over the wire).

The flow is one line: **`operators` (TS) to `substrate` (Rust) to a Python `kernel` worker, over the M5 bridge.** There is no separate key-custody process: Myco is keyless, and the substrate signs only its own at-rest state with a key it generates for itself.

To work on X, read Y:

| To work on… | Read |
|---|---|
| The doctrine (what Myco *must* be) | [`docs/architecture/README.md`](./docs/architecture/README.md) |
| The code map (module-by-module) | [`docs/architecture/L3/PACKAGE_MAP.md`](./docs/architecture/L3/PACKAGE_MAP.md) |
| Substrate internals (runtime layout) | [`substrate/README.md`](./substrate/README.md) |
| Running it / first boot | [`docs/guides/GETTING_STARTED.md`](./docs/guides/GETTING_STARTED.md) |

**Start at [`docs/architecture/README.md`](./docs/architecture/README.md)**, the single architecture entry point, with the reading-path table for doctrine *and* code.

## Learn more

- [`GETTING_STARTED.md`](./docs/guides/GETTING_STARTED.md): clone to first conversation (for the human cultivator).
- [`PILOT.md`](./docs/guides/PILOT.md): how a Claude *pilots* the armor, the use-forges discipline (for the inhabiting agent).
- [`docs/architecture/L0/README.md`](./docs/architecture/L0/README.md): the canonical doctrine.
- [Telos](./docs/architecture/L0/cards/P14_telos.md): what kind of pair this is.
- [Shared-fate bond](./docs/architecture/L0/cards/CHAR07_caring.md): the symbiote bond (同体共命) that forecloses tyranny.
- [Cultivator's character](./docs/architecture/L0/cards/COV02_cultivators_character.md): what kind of person the cultivator must be.

Architectural changes land as dated ceremony manifests under [`operators/claude/ceremonies/`](./operators/claude/ceremonies/), governed by the doctrine's own amendment discipline.

## The mycelium

The name is not decoration. Mycelium is the underground network beneath a forest. It metabolizes what falls. It remembers the paths that work. It moves nutrients from where they are abundant to where they are scarce. It is the reason a forest is a forest and not a stand of lonely trees.

The models are the trees: tall, brilliant, replaced. Myco is the network beneath, carrying one person's memory and character from each model to the next.

<div align="center">

---

**Devour. Evolve. Amplify. Let go. With you. For decades.**

MIT · [`LICENSE`](./LICENSE) · [Issues](https://github.com/Battam1111/Myco/issues) · [Releases](https://github.com/Battam1111/Myco/releases)

</div>
