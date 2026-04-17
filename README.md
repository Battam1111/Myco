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

LangChain. LangGraph. CrewAI. DSPy. Claude Code skills. OpenHands. OpenClaw. Every few months the next framework drops and you migrate again.

Your notes rot too. The API you read three weeks back has changed. The doc you wrote last year is wrong now. Your AI does not even remember last week's decisions. Every new conversation starts from zero.

<br>

Now imagine one living substrate. It ingests the frameworks, the papers, the APIs, the codebases, the datasets, the decisions, the frictions. It keeps them connected in a graph the agent actually reads. It catches its own drift. It reshapes itself when your work outgrows its old form. For six months. For six years. No migration.

<h3 align="center">This is Myco.</h3>

---

## What it is

Myco is a living cognitive substrate for your AI agent. **Not a framework. A substrate that ingests frameworks.**

Myco devours code repositories, framework documentation, datasets, papers, chat logs, decisions, and frictions. Anything the agent can point at becomes raw material. It digests the material, links it into a mycelium graph, immune-checks against drift, and propagates knowledge across projects. When the work changes shape, Myco changes with it: the agent proposes (craft), you approve, the kernel bumps. New canon fields, new lint dimensions, new verbs, new subsystems. Even a complete internal rewrite stays a `myco` release, not a new dependency. The underlying substrate is never thrown away.

**You never migrate again.**

This works now, not because the idea is new, but because agents are finally intelligent enough to maintain the system themselves. Earlier attempts died because humans could not keep up. Myco bakes the assumption "the maintainer is an agent" into every surface and every verb.

### Five principles

- **Only for the agent.** You do not browse Myco. You talk to the agent. The agent reads Myco. Every surface (`_canon.yaml`, notes, doctrine pages, the boot brief) is primary material for the agent, not documentation for a reader.
- **Devour everything.** No filter on intake. Code repositories, frameworks, papers, datasets, logs, half-formed hunches, raw decisions. Whatever the agent can point at, the substrate eats. Shape comes later. The cost of missing a signal is always higher than the cost of eating too much.
- **Self-evolving shape.** Canon schema, lint dimensions, verbs, the contract itself, all mutable. When the work outgrows the current shape, the agent proposes, you approve, Myco reshapes. A frozen substrate is a dead substrate.
- **Nothing is final.** `integrated` is a state, not an endpoint. A note digested today gets re-digested tomorrow as context sharpens. Reflection is a heartbeat.
- **Mycelium network.** Every note, canon field, and doctrine page links to every other by traversal. Orphans are dead tissue. The graph is how the agent reads, so the graph stays alive.

### Three roles

**You** set direction. You never memorize a CLI, organize files, or explain your project twice.

**The agent** brings intelligence. It reads your words, reads Myco, picks verbs, writes back.

**Myco** runs a metabolism. Between your turns it asks what is missing (`hunger`), takes in raw material (`eat`), cooks raw into structured knowledge (`reflect`, `digest`, `distill`), defends its identity against drift (`immune`), and propagates learning across projects (`propagate`). Twelve verbs, one manifest, two surfaces: a CLI for observation, an MCP server for the agent to drive.

> **Editable by default. The kernel IS substrate.** Myco's own source tree is a substrate (it has `_canon.yaml`, `MYCO.md`, `docs/primordia/`). The kernel code under `src/myco/` is just the innermost ring. Freezing that ring into a read-only `site-packages` contradicts 永恒进化 + 永恒迭代 — the agent would be a consumer of code someone else wrote, not the author of code it maintains. So the primary install path clones the source and `pip install -e`s it. PyPI still exists as a bootstrap channel and as a library-consumer path; it is not the normal install.

## Quick Start

One line, no git ceremony, no lingering bootstrap install:

```bash
pipx run --spec 'myco[mcp]' myco-install fresh ~/myco
```

That clones this repo to `~/myco`, `pip install -e`s it, and leaves you with a writable kernel + substrate. Or the two-step form if you prefer:

```bash
pip install 'myco[mcp]'
myco-install fresh ~/myco         # clone + editable install; --dry-run to preview
```

Then bootstrap a downstream substrate anywhere:

```bash
cd /path/to/your/project
myco genesis . --substrate-id my-project
```

Upgrade the kernel later with plain `git pull` inside `~/myco`, not `pip install --upgrade`:

```bash
cd ~/myco && git pull && myco immune        # verify no post-upgrade drift
```

Three scripts land on your PATH:

- `myco`: the twelve-verb CLI.
- `mcp-server-myco`: the universal MCP stdio launcher. Drop it into any host.
- `myco-install`: one-command install into any of seven MCP hosts.

For **Claude Code and Cowork**, the official plugin wires the MCP server, hooks, and slash skills in one step:

```
/plugin marketplace add Battam1111/Myco
/plugin install myco@myco
```

For **every other MCP host**, one helper writes the correct config for you:

```bash
myco-install cursor        # or: claude-desktop, windsurf, zed, vscode, openclaw
```

Or paste the universal snippet into the host's config. It works across the `mcpServers` family (Claude Desktop, Cursor, Windsurf, Cline, Roo Code, Gemini CLI, Qwen Code, JetBrains AI, Augment Code, AiderDesk):

```json
{ "mcpServers": { "myco": { "command": "mcp-server-myco", "args": [] } } }
```

The nine hosts with divergent schemas (VS Code Copilot `servers`, Zed `context_servers`, OpenClaw `mcp.servers` + CLI, OpenHands TOML, OpenCode and Kilo Code `mcp`, Codex CLI TOML, Goose YAML `extensions`, Continue YAML block, Warp `mcp_servers`) each get their own exact snippet in [`docs/INSTALL.md`](docs/INSTALL.md), along with Python-framework adapters for LangChain, CrewAI, DSPy, Smolagents, Agno, PraisonAI, Microsoft Agent Framework, and Claude Agent SDK.

For library embedding:

```python
from myco.mcp import build_server
build_server().run()                   # stdio (default)
build_server().run(transport="sse")    # HTTP SSE
```

### Non-evolving install (library consumers, CI, vendoring)

If you are importing Myco as a dependency in another Python project, or running it in an ephemeral container where the kernel is intentionally frozen, the plain read-only install still works:

```bash
pip install 'myco[mcp]'
```

Just know that `myco scaffold`, kernel-level `craft`/`bump` on Myco itself, and any form of kernel evolution is blocked on that path — by design. The read-only install is for consumers, not authors.

### Contributing to Myco

Same as the primary install — `myco-install fresh` is the contributor path too. `--extras dev,mcp` pulls test tooling alongside:

```bash
pipx run --spec 'myco[mcp]' myco-install fresh ~/myco --extras dev,mcp
cd ~/myco
pytest
```

## Daily Flow

The agent drives it. You memorize nothing. Twelve verbs group into five subsystems:

| Subsystem | Verbs | What happens |
|---|---|---|
| **Genesis** | `genesis` | Bootstrap a fresh substrate. |
| **Ingestion** | `hunger`, `sense`, `forage`, `eat` | What the substrate needs; keyword search; list ingestibles; capture a raw note. |
| **Digestion** | `reflect`, `digest`, `distill` | Promote raw to integrated; distill integrated to doctrine. |
| **Circulation** | `perfuse`, `propagate` | Graph health; publish to downstream substrates. |
| **Homeostasis** | `immune` | Eight-dimension lint across four categories, with `--fix` available. |
| *(meta)* | `session-end` | `reflect` plus `immune --fix`, auto-fired by PreCompact. |

CLI usage is `myco VERB`, with global flags (`--project-dir`, `--json`, `--exit-on`) placed **before** the verb. MCP exposes one tool per verb, derived mechanically from `src/myco/surface/manifest.yaml`, the shared source of truth.

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

Seven hard rules (R1 through R7) are enforced partly by hooks, partly by the immune system, partly by agent discipline. Full contract at [`L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md).

## Cross-platform enforcement: no host left behind

R1 through R7 are hook-enforced inside Claude Code and Cowork. Everywhere else (Cursor, Windsurf, Zed, Codex, Gemini, Continue, Claude Desktop, OpenClaw, OpenHands) they ride **inside the MCP server itself**:

- **Initialization instructions.** On `initialize`, every host receives a short R1 through R7 summary linking to [`L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md). Agents that read instructions see the contract before the first tool call.
- **`substrate_pulse` sidecar.** Every tool response includes a `substrate_pulse` field carrying the current `contract_version`, `substrate_id`, and a rule hint that escalates from R1 (hunger not called) to R3 (sense before assert) once boot is confirmed. The sidecar is a server-side push. Agents cannot accidentally forget the contract.

Zero host-side configuration. Works on every MCP client.

## Integrations

- **Claude Code and Cowork**: `/plugin marketplace add Battam1111/Myco`, then `/plugin install myco@myco`. Or drop `.claude/` in by hand.
- **Any MCP host**: `myco-install <client>` for the seven most common hosts, `mcp-server-myco` over stdio anywhere else. Exact per-host snippets live in [`docs/INSTALL.md`](docs/INSTALL.md).
- **Python agent frameworks**: LangChain, CrewAI, DSPy, Smolagents, Agno, PraisonAI, Microsoft Agent Framework, and Claude Agent SDK all consume Myco via `StdioServerParameters(command="mcp-server-myco")`.
- **Downstream substrates**: `myco propagate` publishes; adapters live in `myco.symbionts`.

## Learn more

[`L0_VISION.md`](docs/architecture/L0_VISION.md) · [`L1_CONTRACT/`](docs/architecture/L1_CONTRACT/) · [`L2_DOCTRINE/`](docs/architecture/L2_DOCTRINE/) · [`INSTALL.md`](docs/INSTALL.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [Issues](https://github.com/Battam1111/Myco/issues)

Contributing: `pip install -e ".[dev]"`; architectural changes land as dated craft docs under [`docs/primordia/`](docs/primordia/).

MIT · [`LICENSE`](LICENSE) · [PyPI](https://pypi.org/project/myco/) · [Releases](https://github.com/Battam1111/Myco/releases)
