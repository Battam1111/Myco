<p align="center">
  <a href="https://github.com/Battam1111/Myco">
    <img src="https://raw.githubusercontent.com/Battam1111/Myco/main/assets/logo_light_512.png" width="160" alt="Myco">
  </a>
</p>

<h1 align="center">Myco</h1>

<p align="center"><b>Devour everything. Evolve forever. You just talk.</b></p>

<p align="center">
  <a href="https://pypi.org/project/myco/"><img src="https://img.shields.io/pypi/v/myco?style=flat&cache_seconds=0" alt="PyPI"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=flat" alt="License"></a>
  <a href="https://github.com/Battam1111/Myco"><img src="https://img.shields.io/github/stars/Battam1111/Myco?style=flat" alt="Stars"></a>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> · <a href="#daily-flow">Daily Flow</a> · <a href="#architecture">Architecture</a> · <a href="#integrations">Integrations</a>
</p>

<p align="center">
  <b>Languages:</b> English · <a href="README_zh.md">中文</a> · <a href="README_ja.md">日本語</a>
</p>

---

LangChain. LangGraph. CrewAI. DSPy. Hermes. Every month a new framework promises to be the one. You spend more time picking tools than building with them.

And it's not just frameworks. Papers, APIs, best practices — everything refreshes daily. Your note app has 500 entries. Last organized: three months ago, maybe longer. Those carefully written notes? They're rotting. That API from three weeks back? Version changed. **Nothing is checking for you.**

Your AI doesn't remember last week's decisions either. Every new conversation, back to zero.

<br>

Now imagine you just talk. No organizing, no comparing frameworks, no re-explaining your project. Six months later your AI is sharper than anyone's — it devoured the latest work in your field on its own, found its own blind spots, threw out what stopped being true, and rewrote its own operating rules when they weren't good enough.

<h3 align="center">This is Myco.</h3>

---

## What it is

Myco is an **Agent-First symbiotic cognitive substrate** — your agent's other half. Not a memory layer, not an agent runtime, not a skill framework. An **autopoietic substrate**: the agent brings intelligence; Myco brings memory, immunity, metabolism, self-model, and its own evolution. Neither is whole without the other.

> **v0.4.0 — Greenfield Rewrite.** Every verb, every dimension, every contract surface re-authored from L0. Upgrading from v0.3.x: see [`CHANGELOG.md`](CHANGELOG.md) and [`scripts/migrate_ascc_substrate.py`](scripts/migrate_ascc_substrate.py).

## Quick Start

```bash
pip install myco

cd /path/to/your/project
myco genesis . --substrate-id my-project
```

For **Claude Code / Cowork**, copy this repo's `.claude/` folder into your project — SessionStart fires `myco hunger`, PreCompact fires `myco session-end`. Zero manual ceremony.

For **any MCP host** (Cursor, Continue, Zed, …), Myco ships a manifest-driven MCP server:

```python
from myco.surface.mcp import build_server
build_server().run()          # requires `pip install mcp`
```

A `python -m myco.mcp` launcher, a `[mcp]` extras target, and an official `.plugin` bundle ship in **v0.4.1**.

## Daily Flow

Your agent drives it; you don't memorize anything. The 12 verbs group into 5 subsystems:

| Subsystem | Verbs | What happens |
|---|---|---|
| **Genesis** | `genesis` | Bootstrap a fresh substrate. |
| **Ingestion** | `hunger` · `sense` · `forage` · `eat` | What the substrate needs; keyword search; list ingestibles; capture a raw note. |
| **Digestion** | `reflect` · `digest` · `distill` | Promote raw → integrated; distill integrated → doctrine. |
| **Circulation** | `perfuse` · `propagate` | Graph health; publish to downstream substrates. |
| **Homeostasis** | `immune` | Eight-dimension lint across 4 categories (`--fix` available). |
| *(meta)* | `session-end` | `reflect` + `immune --fix`; auto-fired by PreCompact. |

CLI: `myco VERB` — global flags (`--project-dir`, `--json`, `--exit-on`) go **before** the verb. MCP: one tool per verb, derived mechanically from `src/myco/surface/manifest.yaml` (the shared SSoT).

## Architecture

```
You ──▶ Agent ──▶ Myco substrate
                    ├── _canon.yaml        SSoT: identity · write-surface · lint policy
                    ├── MYCO.md            agent entry page (R1)
                    ├── notes/{raw,integrated,distilled}/
                    ├── docs/architecture/ L0 vision · L1 contract · L2 doctrine · L3 impl
                    ├── src/myco/          genesis · ingestion · digestion · circulation · homeostasis · surface
                    └── .claude/hooks/     SessionStart → hunger · PreCompact → session-end
```

Three roles — **you** set direction, **agent** brings intelligence, **Myco** brings memory and continuity. Seven hard rules (R1–R7) enforced partly by hooks, partly by the immune system, partly by agent discipline. Full contract: [`L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md).

## Integrations

- **Claude Code / Cowork** — drop in `.claude/`, done. Official `.plugin` bundle in v0.4.1.
- **Any MCP host** — wire `myco.surface.mcp:build_server()` into the host's config.
- **Downstream substrates** — `myco propagate` publishes; adapters live in `myco.symbionts`.

## Learn more

[`L0_VISION.md`](docs/architecture/L0_VISION.md) · [`L1_CONTRACT/`](docs/architecture/L1_CONTRACT/) · [`L2_DOCTRINE/`](docs/architecture/L2_DOCTRINE/) · [`CONTRIBUTING.md`](CONTRIBUTING.md) *(v0.4.1)* · [Issues](https://github.com/Battam1111/Myco/issues)

Contributing: `pip install -e ".[dev]"`; architectural changes land as dated craft docs under [`docs/primordia/`](docs/primordia/).

MIT · [`LICENSE`](LICENSE) · [PyPI](https://pypi.org/project/myco/) · [Releases](https://github.com/Battam1111/Myco/releases)
