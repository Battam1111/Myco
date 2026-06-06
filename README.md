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

[What it is](#what-it-is) · [Quick start](#quick-start) · [How it works](#how-it-works) · [Learn more](#learn-more)

**Languages:** English · [中文](docs/i18n/README_zh.md) · [日本語](docs/i18n/README_ja.md)

</div>

---

Every few months a stronger model arrives. The relationship resets. You re-explain your context, your taste, your decisions. Your collaborator forgets, repeatedly.

Your own work rots too. The decision you made in April: you can't find why. Last quarter's plan has drifted. Your own thinking has outpaced the records of who you were.

<br>

Now imagine the AI agent you work with wears a living armor. A metabolism, not a log. It devours the essence of everything you bring and everywhere the agent reaches. It evolves as the work changes. It amplifies the agent, so each model that wears it reaches further than the last. It lets outdated parts die so the whole stays alive.

The next model arrives, inhabits the same armor (now stronger), and meets you mid-conversation. The armor carried you forward.

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
  <img src="docs/assets/architecture_light.svg" width="760" alt="Myco architecture: a human talks to an AI agent through MCP; the operator bridges to a Rust substrate and a Python kernel; the metabolic cycle devours, cycles, prunes, and evolves between turns. Keyless: trust is the live human at the gate plus the causal history plus the BLAKE3-sealed doctrine.">
</picture>

</div>

## What it is

Myco is a **living armor the AI agent inhabits**. Between your turns it metabolizes: it devours what you bring, evolves its own shape, amplifies the pilot, and lets stale parts die. Because the armor persists across model generations and carries your context, the relationship never restarts.

It is **keyless**: no owner key, no signing ceremony, nothing to set up or hold. Trust is the live human at the gate, plus the substrate's own tamper-evident causal history, plus a doctrine the system seals and enforces on itself.

Its character is **同体共命** (one body, shared fate): the armor's flourishing rises and falls with its pilot's, so it cannot thrive by dominating the body it shares. Strength serves the shared body; it does not subjugate it.

## Quick start

```bash
git clone https://github.com/Battam1111/Myco.git
cd Myco
cargo build --release --workspace
```

Then read [`GETTING_STARTED.md`](./docs/guides/GETTING_STARTED.md): the runbook from clone to first conversation (Rust 1.80+, Node 22+, Python 3.13+). There is no key to generate and nothing to hold: Myco is keyless.

This is **v0.9-genesis alpha**. The armor runs; it awaits its first real cultivation. You will be early.

## How it works

You talk to the AI agent through MCP. Between your turns, the armor runs one metabolic cycle: it ingests new material as immutable history, the pilot forges that into durable understanding, stale parts are pruned with a tombstone, and when the shape no longer fits the work you approve a reshaping at the gate. A self-checking immune layer catches tampering, drift, and runaway cost; if the pair stops flourishing, the armor retires with dignity rather than rotting on.

Three pieces in one repo, over one wire protocol: a **TypeScript** MCP operator the agent drives, a **Rust** substrate (the body), and a **Python** kernel (the mechanism). The doctrine that governs all of it lives in the same repo and is sealed by a hash chain, so the rules cannot silently drift from the code. The full picture is in the [architecture guide](./docs/architecture/README.md).

## Integrations

- **Claude Code.** `operators/claude/` ships an MCP server; drop it into `.claude/` or connect directly.
- **Claude Desktop / Cowork.** The same MCP server entry.
- **Any MCP host.** Cursor, Windsurf, Zed, OpenClaw, and others, over the standard MCP protocol.

## Learn more

- [`GETTING_STARTED.md`](./docs/guides/GETTING_STARTED.md): clone to first conversation, for the human.
- [`PILOT.md`](./docs/guides/PILOT.md): how a Claude pilots the armor, for the inhabiting agent.
- [Architecture](./docs/architecture/README.md): the runtime and the doctrine, module by module.
- [Doctrine (L0)](./docs/architecture/L0/README.md): the sealed constitution. What Myco must be.

## The mycelium

The name is not decoration. Mycelium is the underground network beneath a forest. It metabolizes what falls, remembers the paths that work, and moves nutrients from where they are abundant to where they are scarce. It is why a forest is a forest and not a stand of lonely trees.

The models are the trees: tall, brilliant, replaced. Myco is the network beneath, carrying one person's memory and character from each model to the next.

<div align="center">

---

**Devour. Evolve. Amplify. Let go. With you. For decades.**

MIT · [`LICENSE`](./LICENSE) · [Issues](https://github.com/Battam1111/Myco/issues) · [Releases](https://github.com/Battam1111/Myco/releases)

</div>
