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

> **Stable kernel, mutable substrate.** A `pip install` locks the kernel at a released version; everything the agent evolves day-to-day lives in your substrate (`_canon.yaml`, `notes/`, `docs/primordia/`), driven by the 12 MCP verbs. Kernel evolution is upstream governance: craft → PR → bump.

## Quick Start

```bash
pip install 'myco[mcp]'          # package + MCP SDK + console scripts
cd /path/to/your/project
myco genesis . --substrate-id my-project
```

Two console scripts land on your PATH:

- `myco` — the 12-verb CLI.
- `mcp-server-myco` — the universal MCP stdio launcher. Drop it into any host.

For **Claude Code / Cowork**, install the official plugin (hooks + skills + MCP wired in one step):

```
/plugin marketplace add Battam1111/Myco
/plugin install myco@myco
```

For **any other MCP host**, the same line works everywhere — Myco ships a stable console script so you never have to reason about `python` vs `python3` or which venv the host will spawn:

```json
{ "mcpServers": { "myco": { "command": "mcp-server-myco", "args": [] } } }
```

| Host | Config path | Install action |
|---|---|---|
| **Cursor** | `.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global) | paste the snippet above |
| **Windsurf** | `~/.codeium/windsurf/mcp_config.json` | paste the snippet above |
| **Zed** | `~/.config/zed/settings.json` → `context_servers.myco` | `{"source":"custom","command":"mcp-server-myco","args":[]}` |
| **Codex CLI** | one-liner or `~/.codex/config.toml` | `codex mcp add myco -- mcp-server-myco` |
| **Gemini CLI** | `~/.gemini/settings.json` → `mcpServers.myco` | paste the snippet above |
| **Continue** | `.continue/mcpServers/myco.yaml` | `name: Myco` · `type: stdio` · `command: mcp-server-myco` |
| **Claude Desktop** | `claude_desktop_config.json` → `mcpServers.myco` | paste the snippet above |
| **LangChain / CrewAI / DSPy / Agent Framework** | Python | `StdioServerParameters(command="mcp-server-myco")` |

*Aider does not support MCP natively yet (see aider-ai/aider #4506); a community bridge such as `mcpm-aider` works in the meantime.*

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

Three roles — **you** set direction, **agent** brings intelligence, **Myco** brings memory and continuity. Seven hard rules (R1–R7) enforced partly by hooks, partly by the immune system, partly by agent discipline. Full contract: [`L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md).

## Cross-platform enforcement

R1–R7 are hook-enforced inside Claude Code / Cowork. Everywhere else, they ride inside the MCP server itself:

- **Initialization instructions.** On `initialize`, every host receives a short R1–R7 summary linking to [`L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md). Agents that read instructions see the contract before the first tool call.
- **`substrate_pulse` sidecar.** Every tool response includes a `substrate_pulse` field carrying the current `contract_version`, the `substrate_id`, and a rule hint that escalates from R1 (hunger not yet called) to R3 (sense before assert) once boot is confirmed. The sidecar is a server-side push — agents cannot accidentally forget the contract.

The sidecar works on Cursor, Windsurf, Zed, Codex, Gemini, Continue, and Claude Desktop without any host-side configuration.

## Integrations

- **Claude Code / Cowork** — `/plugin marketplace add Battam1111/Myco` then `/plugin install myco@myco`, or drop `.claude/` in by hand. Both routes wire SessionStart → `hunger` and PreCompact → `session-end`.
- **Any MCP host** — `mcp-server-myco` console script over stdio (or `--transport sse` for HTTP), or `myco.mcp:build_server` for library embedding.
- **Downstream substrates** — `myco propagate` publishes; adapters live in `myco.symbionts`.

## Learn more

[`L0_VISION.md`](docs/architecture/L0_VISION.md) · [`L1_CONTRACT/`](docs/architecture/L1_CONTRACT/) · [`L2_DOCTRINE/`](docs/architecture/L2_DOCTRINE/) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [Issues](https://github.com/Battam1111/Myco/issues)

Contributing: `pip install -e ".[dev]"`; architectural changes land as dated craft docs under [`docs/primordia/`](docs/primordia/).

MIT · [`LICENSE`](LICENSE) · [PyPI](https://pypi.org/project/myco/) · [Releases](https://github.com/Battam1111/Myco/releases)
