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
  <a href="https://glama.ai/mcp/servers/Battam1111/Myco"><img src="https://glama.ai/mcp/servers/Battam1111/Myco/badges/score.svg" alt="Glama score"></a>
</p>

<p align="center">
  <a href="https://glama.ai/mcp/servers/Battam1111/Myco">
    <img src="https://img.shields.io/badge/Try_it_live_on-Glama-8b5cf6?style=for-the-badge" alt="Try it live on Glama" height="36">
  </a>
</p>

<p align="center">
  <sub>Claude&nbsp;Code&nbsp; <code>/plugin install myco@myco</code> &nbsp;·&nbsp; Claude&nbsp;Desktop&nbsp; <code>myco-install host cowork</code> &nbsp;·&nbsp; Any&nbsp;MCP&nbsp;host&nbsp; <code>pip install 'myco[mcp]'</code></sub>
</p>

<p align="center">
  <a href="#what-it-is">What it is</a> · <a href="#how-it-lives">How it lives</a> · <a href="#quick-start">Quick start</a> · <a href="#the-nineteen-verbs">Verbs</a> · <a href="#self-validation">Self-validation</a>
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

Myco is a living cognitive substrate for your AI agent.

Everything the agent reads or writes, every piece of code and every paper and every decision and every friction, lives on your filesystem as plain markdown + YAML. Files cross-reference each other by name, forming a graph the agent actually reads. The agent eats raw material, digests it into integrated knowledge, immune-checks its own work against drift, propagates learning across your projects, and when the shape of the substrate no longer fits the shape of the work, reshapes the substrate itself. The kernel that runs all of this *is itself a substrate*, editable by default, maintained by the same agent that uses it.

Not a framework. Not a vector database. Not a managed service. A living filesystem for an agent you talk to.

The idea is older than the implementation. What changed is the agent. Today's models are finally capable of keeping their own tooling alive. Every earlier attempt at a self-maintaining knowledge system died in the same place, where the human in the loop could no longer keep up. Myco puts the loop inside the agent. Every surface, every verb, every rule assumes the maintainer is an agent, so the human in the loop is no longer load-bearing.

## How it lives

You speak. The agent listens. Between your turns, Myco runs a metabolism.

- **Ingestion.** `hunger` asks what is missing. `eat` absorbs whatever you point at, whether a path, a URL, or a paragraph. `sense` and `forage` scan what is already here. `excrete` safely removes a raw note captured by mistake, moving it to an audit tombstone instead of silently deleting.
- **Digestion.** `assimilate` cooks raw notes into integrated knowledge. `digest` promotes a single note. `sporulate` concentrates integrated notes into a dispersible proposal.
- **Circulation.** `traverse` walks the graph and reports on its connectedness. `propagate` publishes learning to a downstream substrate.
- **Homeostasis.** `immune` runs a 25-dimension lint against the seven hard rules. `senesce` winds down each session cleanly.
- **Evolution.** When the substrate's shape no longer fits the work, whether a canon field is missing, a new lint dimension is needed, or a verb must change, `fruit` drafts a three-round craft proposal, `winnow` gates its shape, and `molt` ships the contract bump.

Nineteen verbs, one manifest, two faces: a CLI for you to observe, an MCP server for the agent to drive. You memorize nothing. The agent drives.

## Five principles

- **Only for the agent.** Every surface, every message, every verb shape is primary material for the agent. Not documentation for a human reader.
- **Devour everything.** No filter on intake. Missing a signal costs more than eating one too many.
- **Self-evolving shape.** Canon, lint dimensions, verbs, the contract itself, all of it mutable, all of it changed through a single governed craft loop.
- **Nothing is final.** `integrated` is a state, not an endpoint. Today's conclusion is tomorrow's raw material.
- **Mycelium network.** Every node links to every other node by traversal. Orphans are dead tissue.

## The kernel IS a substrate

Myco's own source tree is a substrate. `_canon.yaml` at the root. `MYCO.md` as the agent entry page. `docs/primordia/` holding the three-round craft document that justifies every contract bump. The Python code under `src/myco/` is the innermost ring of its own ecosystem. Not a read-only artifact someone else wrote.

So the normal install clones the source and runs `pip install -e` on it. The agent that uses Myco is the same agent that maintains Myco. When it needs a new lint dimension, it scaffolds one with `myco ramify`, writes the case with `myco fruit`, gates the shape with `myco winnow`, and ships the bump with `myco molt`. No fork. No waiting PR. No long-lived feature branch. **永恒进化.**

PyPI exists for bootstrap and for library embedding. It is not the normal install path.

## Quick start

```bash
pipx run --spec 'myco[mcp]' myco-install fresh ~/myco
```

This clones the repository to `~/myco`, runs `pip install -e` on it, and leaves you with a writable kernel. Then germinate a substrate inside any project:

```bash
cd your-project
myco germinate . --substrate-id your-project
```

Hook Myco into your agent host in one command:

- **Claude Code.** Run `/plugin marketplace add Battam1111/Myco`, then `/plugin install myco@myco`.
- **Claude Desktop / Cowork.** Run `myco-install host cowork` to write the MCP entry, then download [`myco-<ver>.plugin`](https://github.com/Battam1111/Myco/releases/latest) and drag it into Claude Desktop → Settings → Plugins → Upload. Claude Desktop uploads it to your private Cowork marketplace and every subsequent session auto-installs the `myco-substrate` onboarding skill.
- **Any other MCP host.** Run `myco-install host <cursor | windsurf | zed | vscode | openclaw | claude-desktop | gemini-cli | codex-cli | goose>`, or pass `--all-hosts` to auto-detect every host on this machine.
- **Via the official MCP Registry.** Use the namespace [`io.github.Battam1111/myco`](https://registry.modelcontextprotocol.io/v0/servers?search=Battam1111) for clients that auto-resolve it.

Per-host snippets for the nine hosts with divergent schemas, Python-framework adapters (LangChain, CrewAI, DSPy, Smolagents, Agno, PraisonAI, MS Agent Framework, Claude Agent SDK), and library-embedding examples all live in [`INSTALL.md`](docs/INSTALL.md).

## The nineteen verbs

Six subsystems. Every name is a fungal-biology term whose meaning tracks its action.

- **Germination.** `germinate` starts a fresh substrate.
- **Ingestion.** `hunger` (what is missing?), `eat` (absorb raw material), `sense` (keyword search), `forage` (scan ingestible paths), `excrete` (safely delete a raw note with an audit tombstone).
- **Digestion.** `assimilate` (raw to integrated, in bulk), `digest` (promote a single note), `sporulate` (integrated to dispersible proposal).
- **Circulation.** `traverse` (walk the graph), `propagate` (publish to a downstream substrate).
- **Homeostasis.** `immune` (25-dimension lint; `--fix` repairs mechanically where it can).
- **Cycle.** `senesce` (session dormancy), `fruit` (three-round craft), `winnow` (gate the craft's shape), `molt` (ship the contract bump), `ramify` (scaffold a new dimension, verb, or adapter), `graft` (manage substrate-local plugins), `brief` (human-facing state rollup).

Every verb lives in [`src/myco/surface/manifest.yaml`](src/myco/surface/manifest.yaml). The CLI (`myco VERB`) and the MCP tool surface both derive from that manifest mechanically. One source of truth for both faces. A downstream substrate can `ramify` its own dimensions or verbs into `.myco/plugins/` without ever forking Myco.

## Self-validation

Myco does not trust its agent to remember the contract. It enforces it.

- **25 lint dimensions** across four categories: *mechanical* (canon invariants, write-surface, LLM-boundary), *shipped* (package and canon version parity), *metabolic* (raw backlog, stale integrated notes), *semantic* (graph connectedness, orphan detection). `myco immune --fix` repairs mechanically where it can.
- **Seven hard rules (R1 through R7)** govern every session: boot ritual, session-end, sense-before-assert, eat-on-friction, cross-reference-on-creation, write-surface discipline, top-down layering. Full contract at [`L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md).
- **Pulse sidecar.** Every MCP tool response carries a `substrate_pulse` echoing the current contract version and a rule hint that escalates (R1, then R3, then on through the session) as the session progresses. A server-side push. The agent cannot accidentally forget.
- **Write-surface enforcement.** Any write outside `_canon.yaml::system.write_surface.allowed` is refused with `WriteSurfaceViolation`. Discipline as a mechanism, not as a request.

Zero host-side configuration. R1 through R7 ride inside the MCP server itself, so every client (Claude Code, Cursor, Windsurf, Zed, Codex, Gemini, Continue, Claude Desktop, OpenClaw, OpenHands) gets the same contract on boot.

## Integrations

- **Claude Code.** Official plugin wires MCP, hooks, and slash skills in one command. Or drop `.claude/` in by hand.
- **Cowork (Claude Desktop local-agent-mode).** Two steps: (1) `myco-install host cowork` writes the MCP server entry; (2) drag the `.plugin` bundle from [GitHub releases](https://github.com/Battam1111/Myco/releases/latest) into Claude Desktop's plugin upload. Claude Desktop uploads it to your private Cowork marketplace, and every session auto-installs the `myco-substrate` onboarding skill so the agent follows R1 through R7 the moment it sees `_canon.yaml`. Cowork does not expose hooks and does not read local plugin dirs, so drag-and-drop is the only persistent path. See [`INSTALL.md`](docs/INSTALL.md) for the full rationale.
- **Any MCP host.** Ten are automated via `myco-install`. Another nine have per-host snippets in [`INSTALL.md`](docs/INSTALL.md). Any other client can still run `mcp-server-myco` over stdio directly.
- **Python agent frameworks.** LangChain, CrewAI, DSPy, Smolagents, Agno, PraisonAI, MS Agent Framework, and Claude Agent SDK all consume Myco via `StdioServerParameters(command="mcp-server-myco")`.
- **Downstream substrates.** `myco propagate` publishes. Adapters live in `myco.symbionts`.

## Learn more

[`L0_VISION.md`](docs/architecture/L0_VISION.md) · [`L1_CONTRACT/`](docs/architecture/L1_CONTRACT/) · [`L2_DOCTRINE/`](docs/architecture/L2_DOCTRINE/) · [`INSTALL.md`](docs/INSTALL.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [Issues](https://github.com/Battam1111/Myco/issues)

Architectural changes land as dated craft documents under [`docs/primordia/`](docs/primordia/). Every release is governed by a three-round debate, then a `molt`, then an auto-published fan-out to PyPI, the MCP Registry, and the GitHub release.

MIT · [`LICENSE`](LICENSE) · [PyPI](https://pypi.org/project/myco/) · [Releases](https://github.com/Battam1111/Myco/releases)

<!-- mcp-name: io.github.Battam1111/myco -->

