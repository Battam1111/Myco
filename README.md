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

Imagine an AI that never forgets what you taught it. That devours every paper, every decision, every "I was wrong about that" you throw at it. That notices when its own understanding has gone stale and repairs itself. That connects today's idea to a half-forgotten note from three months back so you don't have to.

That's Myco.

Myco is a **living cognitive substrate for your AI agent** — a second half the agent feeds, digests, defends, and grows alongside you. Not a memory database, not an agent runtime, not a skill framework. It lives next to the agent and turns it into a partner that remembers.

### Five principles it rests on

- **Only for the agent.** You don't browse Myco. You talk to the agent; the agent reads Myco. Every surface — `_canon.yaml`, notes, doctrine pages, the boot brief — is primary material for the agent, not documentation for a reader.
- **Devour everything.** No filter on intake. Decisions, frictions, papers, logs, half-formed hunches — whatever shows up is captured raw. Shape comes later. The cost of missing a signal is always higher than the cost of eating too much.
- **Self-evolving shape.** Canon schema, lint dimensions, the contract itself — all mutable, first-class. A frozen substrate is a dead one. Evolution goes through governance (craft → PR → bump), never through drift.
- **Nothing is final.** `integrated` is a state, not an endpoint. A note digested today can be re-digested tomorrow when context sharpens. Reflection is a heartbeat, not a chore.
- **Mycelium network.** Every note, canon field, doctrine page links to every other by traversal. Orphans are dead tissue. The graph is how the agent reads — so the graph has to stay alive.

### Three roles, working together

**You** — set direction. Say what to do. Never memorize a CLI, never organize files, never re-explain your project.

**The agent** — brings intelligence. Reads your words, reads Myco, picks verbs, writes back.

**Myco** — runs a metabolism. Between turns it **hungers** (what's missing?), **eats** (raw in), **reflects / digests / distills** (raw → structured → doctrine), keeps an **immune** system against drift, and **propagates** learning across projects. Twelve verbs, one manifest, two surfaces: CLI for observation, MCP for the agent to drive.

> **Stable kernel, mutable substrate.** `pip install` locks the kernel at a released version; the substrate (`_canon.yaml`, `notes/`, `docs/primordia/`) evolves through the twelve MCP verbs. Kernel evolution is upstream governance.

## Quick Start

```bash
pip install 'myco[mcp]'
cd /path/to/your/project
myco genesis . --substrate-id my-project
```

Three scripts land on your PATH:

- `myco` — the 12-verb CLI.
- `mcp-server-myco` — the universal MCP stdio launcher. Drop it into any host.
- `myco-install` — one-command install into any of seven MCP hosts.

For **Claude Code / Cowork** — the official plugin wires MCP + hooks + slash skills in one step:

```
/plugin marketplace add Battam1111/Myco
/plugin install myco@myco
```

For **every other MCP host** — one helper writes the correct config for you:

```bash
myco-install cursor        # or: claude-desktop / windsurf / zed / vscode / openclaw
```

Or paste the universal snippet into the host's config — works across the `mcpServers` family (Claude Desktop, Cursor, Windsurf, Cline, Roo Code, Gemini CLI, Qwen Code, JetBrains AI, Augment Code, AiderDesk):

```json
{ "mcpServers": { "myco": { "command": "mcp-server-myco", "args": [] } } }
```

The eight hosts with different schemas — VS Code Copilot (`servers`), Zed (`context_servers`), OpenClaw (`mcp.servers` + CLI), OpenHands (TOML), OpenCode / Kilo Code (`mcp`), Codex CLI (TOML), Goose (YAML `extensions`), Continue (YAML block), Warp (`mcp_servers`) — each get their own exact snippet in [`docs/INSTALL.md`](docs/INSTALL.md), along with Python-framework adapters (LangChain · CrewAI · DSPy · Smolagents · Agno · PraisonAI · Microsoft Agent Framework · Claude Agent SDK).

For library embedding:

```python
from myco.mcp import build_server
build_server().run()                   # stdio (default)
build_server().run(transport="sse")    # HTTP SSE
```

Contributing or forking? Use editable install:

```bash
git clone https://github.com/Battam1111/Myco && cd Myco
pip install -e '.[dev,mcp]'
```

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

Seven hard rules (R1–R7) enforced partly by hooks, partly by the immune system, partly by agent discipline. Full contract: [`L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md).

## Cross-platform enforcement — no host left behind

R1–R7 are hook-enforced inside Claude Code / Cowork. Everywhere else — Cursor, Windsurf, Zed, Codex, Gemini, Continue, Claude Desktop, OpenClaw, OpenHands — they ride **inside the MCP server itself**:

- **Initialization instructions.** On `initialize`, every host receives a short R1–R7 summary linking to [`L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md). Agents that read instructions see the contract before the first tool call.
- **`substrate_pulse` sidecar.** Every tool response includes a `substrate_pulse` field carrying the current `contract_version`, `substrate_id`, and a rule hint that escalates from R1 (hunger not called) to R3 (sense before assert) once boot is confirmed. The sidecar is a server-side push — agents cannot accidentally forget the contract.

Zero host-side configuration. Works on every MCP client.

## Integrations

- **Claude Code / Cowork** — `/plugin marketplace add Battam1111/Myco` → `/plugin install myco@myco`. Or drop `.claude/` in by hand.
- **Any MCP host** — `myco-install <client>` for the seven most common hosts, `mcp-server-myco` stdio anywhere else. Exact per-host snippets in [`docs/INSTALL.md`](docs/INSTALL.md).
- **Python agent frameworks** — LangChain · CrewAI · DSPy · Smolagents · Agno · PraisonAI · Microsoft Agent Framework · Claude Agent SDK all consume Myco via `StdioServerParameters(command="mcp-server-myco")`.
- **Downstream substrates** — `myco propagate` publishes; adapters live in `myco.symbionts`.

## Learn more

[`L0_VISION.md`](docs/architecture/L0_VISION.md) · [`L1_CONTRACT/`](docs/architecture/L1_CONTRACT/) · [`L2_DOCTRINE/`](docs/architecture/L2_DOCTRINE/) · [`INSTALL.md`](docs/INSTALL.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [Issues](https://github.com/Battam1111/Myco/issues)

Contributing: `pip install -e ".[dev]"`; architectural changes land as dated craft docs under [`docs/primordia/`](docs/primordia/).

MIT · [`LICENSE`](LICENSE) · [PyPI](https://pypi.org/project/myco/) · [Releases](https://github.com/Battam1111/Myco/releases)
