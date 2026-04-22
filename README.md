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
  <a href="#what-it-is">What it is</a> · <a href="#how-it-lives">How it lives</a> · <a href="#quick-start">Quick start</a> · <a href="#the-eighteen-verbs">Verbs</a> · <a href="#self-validation">Self-validation</a>
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

Everything the agent reads or writes — code, papers, decisions, frictions — lives on your filesystem as markdown + YAML, linked into a mycelial graph. The agent eats raw material, digests it into integrated knowledge, immune-checks against drift, propagates learning across projects, and — when your work outgrows the old shape — reshapes the substrate itself. The kernel that runs all this *is itself a substrate*: editable by default, maintained by the same agent that uses it.

Not a framework. Not a vector DB. Not a managed service. A living filesystem for an agent you talk to.

This works now, not because the idea is new, but because agents are finally smart enough to maintain the system themselves. Earlier attempts died because humans could not keep up. Myco bakes "the maintainer is an agent" into every surface, every verb, every rule.

## How it lives

You speak. The agent listens. Between your turns, Myco runs a metabolism:

- **Ingestion.** `hunger` asks what's missing. `eat` absorbs whatever you point at — a path, a URL, a paragraph. `sense` and `forage` scan what's already here.
- **Digestion.** `assimilate` cooks raw notes into integrated knowledge. `sporulate` concentrates integrated notes into a dispersible proposal.
- **Circulation.** `traverse` walks the mycelial graph for anastomotic health. `propagate` publishes learnings to a downstream substrate.
- **Homeostasis.** `immune` runs a 25-dimension lint against the seven hard rules. `senesce` gracefully winds down each session.
- **Evolution.** When the substrate's shape no longer fits — a canon field is missing, a lint dimension is needed, a verb must change — `fruit` drafts a three-round craft proposal, `winnow` gates its shape, `molt` ships the contract bump.

Eighteen verbs, one manifest, two faces (a CLI for observation, an MCP server for the agent). You memorize nothing; the agent drives.

## Five principles

- **Only for the agent.** Every surface is primary material for the agent, not documentation for a human reader.
- **Devour everything.** No filter on intake. Missing a signal costs more than eating one too many.
- **Self-evolving shape.** Canon, lint dimensions, verbs, the contract itself — all mutable through a governed craft loop.
- **Nothing is final.** `integrated` is a state, not an endpoint. Today's conclusion is tomorrow's raw material.
- **Mycelium network.** Every node links to every other by traversal. Orphans are dead tissue.

## The kernel IS a substrate

Myco's own source tree is a substrate. `_canon.yaml` at the root. `MYCO.md` as the agent entry page. `docs/primordia/` holds the three-round craft doc that justifies every contract bump. The Python code under `src/myco/` is the innermost ring of its own ecosystem, not a read-only artifact someone else wrote.

So the normal install clones the source and `pip install -e`s it. The agent that uses Myco is the same agent that maintains Myco; if it needs a new lint dimension, it scaffolds one with `myco ramify`, proposes with `myco fruit`, ships with `myco molt`. No fork. No waiting PR. **永恒进化.**

PyPI exists for bootstrap + library-consumer use — not as the normal install.

## Quick start

```bash
pipx run --spec 'myco[mcp]' myco-install fresh ~/myco
```

Clones the repo to `~/myco`, `pip install -e`s it, leaves you with a writable kernel. Then germinate a substrate for any project:

```bash
cd your-project
myco germinate . --substrate-id your-project
```

Hook Myco into your agent host in one command:

- **Claude Code** — `/plugin marketplace add Battam1111/Myco`, then `/plugin install myco@myco`.
- **Claude Desktop / Cowork** — `myco-install host cowork` writes the MCP entry *and* installs the `myco-substrate` onboarding skill into every Cowork workspace.
- **Any other MCP host** — `myco-install host <cursor | windsurf | zed | vscode | openclaw | claude-desktop | gemini-cli | codex-cli | goose>`, or `--all-hosts` to auto-detect every host on this machine.
- **Via the official MCP Registry** — [`io.github.Battam1111/myco`](https://registry.modelcontextprotocol.io/v0/servers?search=Battam1111) for clients that auto-resolve namespaces.

Per-host snippets for the nine hosts with divergent schemas, Python-framework adapters (LangChain / CrewAI / DSPy / Smolagents / Agno / PraisonAI / MS Agent Framework / Claude Agent SDK), and library-embedding examples live in [`INSTALL.md`](docs/INSTALL.md).

## The eighteen verbs

Six subsystems. Every name is a fungal-biology term whose meaning tracks its action.

- **Germination** — `germinate` starts a fresh substrate.
- **Ingestion** — `hunger` (what's missing?), `eat` (absorb raw), `sense` (keyword search), `forage` (scan ingestible paths).
- **Digestion** — `assimilate` (raw → integrated), `digest` (promote a single note), `sporulate` (integrated → dispersible proposal).
- **Circulation** — `traverse` (walk the graph), `propagate` (publish downstream).
- **Homeostasis** — `immune` (25-dimension lint, `--fix` repairs mechanically).
- **Cycle** — `senesce` (session dormancy), `fruit` (three-round craft), `winnow` (gate the craft), `molt` (ship the contract bump), `ramify` (scaffold new dim / verb / adapter), `graft` (manage substrate-local plugins), `brief` (human-facing state rollup).

Every verb lives in [`src/myco/surface/manifest.yaml`](src/myco/surface/manifest.yaml). The CLI (`myco VERB`) and the MCP tool surface both derive from it mechanically — one source of truth for both faces. A downstream substrate can `ramify` its own dimensions or verbs into `.myco/plugins/` without forking Myco.

## Self-validation

Myco does not trust its agent to remember the contract. It enforces it.

- **25 lint dimensions** across four categories — *mechanical* (canon invariants, write-surface, LLM-boundary), *shipped* (package ↔ canon version parity), *metabolic* (raw backlog, stale integrated notes), *semantic* (graph connectedness, orphan detection). `myco immune --fix` repairs mechanically where it can.
- **Seven hard rules (R1–R7)** govern every session — boot ritual, session-end, sense-before-assert, eat-on-friction, cross-reference-on-creation, write-surface discipline, top-down layering. Full contract at [`L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md).
- **Pulse sidecar.** Every MCP tool response carries a `substrate_pulse` echoing the current contract version and a rule hint that escalates (R1 → R3 → …) as the session progresses. A server-side push: the agent cannot accidentally forget.
- **Write-surface enforcement.** Any write outside `_canon.yaml::system.write_surface.allowed` is refused with `WriteSurfaceViolation`. Discipline as a mechanism, not as a request.

Zero host-side configuration. R1–R7 ride inside the MCP server itself, so every client — Claude Code, Cursor, Windsurf, Zed, Codex, Gemini, Continue, Claude Desktop, OpenClaw, OpenHands — gets the same contract on boot.

## Integrations

- **Claude Code.** Official plugin wires MCP + hooks + slash skills in one command. Or drop `.claude/` in by hand.
- **Cowork (Claude Desktop local-agent-mode).** `myco-install host cowork` installs MCP + the `myco-substrate` onboarding skill so the Cowork agent follows R1-R7 the moment it sees `_canon.yaml`. Cowork doesn't expose hooks, so the boot ritual rides on a skill instead — see [`INSTALL.md`](docs/INSTALL.md) and `.cowork-plugin/README.md` for rationale.
- **Any MCP host.** Ten automated via `myco-install`; another nine with per-host snippets in [`INSTALL.md`](docs/INSTALL.md); any other client via `mcp-server-myco` over stdio.
- **Python agent frameworks.** LangChain, CrewAI, DSPy, Smolagents, Agno, PraisonAI, MS Agent Framework, Claude Agent SDK all consume Myco via `StdioServerParameters(command="mcp-server-myco")`.
- **Downstream substrates.** `myco propagate` publishes; adapters live in `myco.symbionts`.

## Learn more

[`L0_VISION.md`](docs/architecture/L0_VISION.md) · [`L1_CONTRACT/`](docs/architecture/L1_CONTRACT/) · [`L2_DOCTRINE/`](docs/architecture/L2_DOCTRINE/) · [`INSTALL.md`](docs/INSTALL.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [Issues](https://github.com/Battam1111/Myco/issues)

Architectural changes land as dated craft docs under [`docs/primordia/`](docs/primordia/). Every release is governed by a three-round debate, then a `molt`, then an auto-published fan-out to PyPI + MCP Registry + GitHub release.

MIT · [`LICENSE`](LICENSE) · [PyPI](https://pypi.org/project/myco/) · [Releases](https://github.com/Battam1111/Myco/releases)

<!-- mcp-name: io.github.Battam1111/myco -->

