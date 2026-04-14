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
  <a href="#quick-start">Quick Start</a> · <a href="#daily-flow">Daily Flow</a> · <a href="#what-it-does">What It Does</a> · <a href="#why-its-different">Why It's Different</a> · <a href="#architecture">Architecture</a> · <a href="#integrations">Integrations</a>
</p>

<p align="center">
  <b>Languages:</b> English · <a href="README_zh.md">中文</a> · <a href="README_ja.md">日本語</a>
</p>

---

You used LangChain in 2024. Someone said LangGraph was better. Then CrewAI. Then DSPy. Then Hermes. Every month a new framework promised to be the one. You spent more time picking tools than building anything with them.

And it wasn't just frameworks. Papers, blog posts, best practices, new models, new APIs, new paradigms, everything refreshing every single day. You followed 50 repos, read 3. Bookmarked 200 articles, opened 10. Your note app had 500 entries. Last organized: three months ago. Maybe longer.

It's not that you're lazy. **The world is moving faster than anyone can keep up with.**

Here's the part that really stings. Those notes you carefully organized, those lessons you wrote down, those "how did I do this last time" entries, they're rotting. That API call you documented three weeks ago? Version changed. That best practice from last month? The community already moved on. Your knowledge base keeps growing, but how much of it is still true? Nobody knows. **Nothing is checking for you.**

Your notes don't tell you "this one's outdated." Your bookmarks don't merge duplicates on their own. Your AI doesn't remember what you decided last week. Every new conversation, back to zero.

<br>

Now imagine living differently.

You don't organize notes. You don't compare frameworks. You don't chase papers. You don't re-explain your project to your AI every time. You just talk like a normal person.

But six months later, your AI is sharper than anyone else's. It knows the full history of every project you've touched. It devoured the latest papers and tools in your field on its own. It found its own blind spots and filled them in. It checked every piece of old knowledge to see if it was still true, whatever wasn't, it threw out. It even rewrote its own operating rules, because the old ones weren't good enough anymore.

<h3 align="center">This is Myco.</h3>

---

## Quick Start

**Default is editable install.** Myco mutates itself — skills rewrite themselves, rules evolve, the engine itself is substrate. A pinned PyPI install freezes you at one snapshot; editable install means every mutation lands in your working tree for free. That's the whole point. Zero config either way — Myco **auto-seeds** a substrate on first contact, so there's no `myco seed` step to remember.

**Step 1 — clone and install the engine (editable):**

```bash
git clone https://github.com/Battam1111/Myco.git
cd Myco && pip install -e ".[mcp]"
```

One command, any host. The engine lives in your clone, mutates in place, and `git pull` brings in upstream mutations without reinstalling.

**Step 2 — wire it to your agent.**

**Cowork / Claude Code** — plugin bundle ships in the repo:

```bash
# After cloning, install the plugin:
# - Cowork: drag plugin/myco-v0.3.3.plugin into the app
# - Claude Code: /plugin install plugin/myco-v0.3.3.plugin
```

Open any project. The `SessionStart` hook fires `myco hunger --execute`, which silently germinates a minimal substrate in the project directory the first time it runs. After that, every metabolism verb — `eat`, `digest`, `reflect`, `immune` — just works.

**Any other MCP-speaking agent** — Cursor, Continue, Zed, Codex, Cline, Windsurf, VS Code, …:

```bash
myco seed --auto-detect my-project                  # one-shot config for every host it finds
```

`myco seed` detects every supported host on your machine and writes the right config files for each. Nine hosts today; more as the ecosystem expands.

**Prefer a pinned release?** `pip install 'myco>=0.3.3'` also works, but you give up in-tree mutation. Use this only when you want Myco as a stable dependency rather than a living substrate.

**Opt-outs.** `MYCO_NO_AUTOSEED=1` disables the silent first-contact seed. `MYCO_PROJECT_DIR=/path/to/shared/substrate` switches from per-project to a single global substrate shared across every project.

## Daily Flow

Once installed, you mostly don't think about Myco — your agent drives it via MCP tools. But the six verbs worth knowing:

| You say / type | What it does |
|---|---|
| `myco hunger` | Health dashboard: raw notes, stale knowledge, digest backlog, signals. `--execute` auto-heals. |
| `myco eat <content>` | Capture a decision, insight, friction point, or piece of external material as a raw note. |
| `myco digest <id>` | Promote a matured raw note into durable knowledge (wiki / MYCO.md / code). |
| `myco search <query>` | Semantic + structural search across the whole substrate. |
| `myco reflect` | Consolidate the session's learnings. Runs automatically at context compaction. |
| `myco immune --fix` | 29-dimension consistency lint, with mechanical auto-fix. Runs automatically at session end. |

All six are also MCP tools (`myco_hunger`, `myco_eat`, …) so your agent calls them directly. 25 tools total, full list in [`docs/agent_protocol.md`](docs/agent_protocol.md).

## What It Does

- 🧬 **Devour everything**. Papers, code, blog posts, conversations. Feed it anything and it digests it into capability, not files.
- 🛡️ **Self-check**. A 29-dimension immune lint runs every session end. Stale facts, broken cross-references, contradictions — caught and fixed mechanically.
- 💀 **Kill what's dead**. Untouched, unread, terminal-status notes get auto-excreted. A knowledge system without excretion is a tumor.
- 🔄 **Evolve forever**. Not just the content evolving — the engine's own rules, skills, and operating procedures mutate too. The whole system is alive.
- 🍄 **Connect everything**. Every file is a node in a mycelial graph. Orphan notes get auto-linked. Knowledge isn't isolated records, it's a web that grows denser over time.
- 🤖 **You just talk**. 25 MCP tools, 13 operating principles, fully automated. Humans don't need to understand a single technical detail.

## Why It's Different

|  | Store and forget | Compile and hope | **Myco** |
|---|---|---|---|
| After ingestion | Sits there | Gets organized once | **Digested → verified → compressed → connected → excreted** |
| When knowledge goes stale | Nobody notices | Nobody notices | **Immune lint catches it. Auto-fix applies.** |
| As knowledge grows | Bloated | Bloated | **Distilled — raw atoms compressed into durable truths** |
| When new tools appear | You switch manually | You migrate manually | **It devours the best parts on its own** |
| When you open a fresh project | Blank slate | Blank slate | **Auto-seeds. Session starts with substrate already alive.** |
| Over time | Messier | Staler | **Smarter** |

## Architecture

```
You (just talk)
  │
  ▼
AI Agent (thinks, executes)   ←────┐
  │  auto-connected via MCP        │
  ▼                                │
Myco substrate                     │
  ├── notes/             raw atoms, lifecycle-aware (raw → digesting → extracted → integrated → excreted)
  ├── wiki/              refined long-term knowledge distilled from atoms
  ├── _canon.yaml        single source of truth for every number, name, path
  ├── skills/            self-evolving operating procedures
  ├── src/myco/          engine code (editable, mutable — yes, even this evolves)
  └── immune system      29-dimension consistency lint, auto-fix on session end
  │                                │
  └────── metabolism loop ─────────┘
          (eat → digest → reflect → immune → prune)
```

Three roles: **you** set direction, the **agent** brings intelligence, **Myco** brings memory and evolution. Each is useless without the other two.

The metabolism loop runs continuously. `SessionStart` → `hunger --execute` surfaces what needs attention. Every decision you make gets `eat`'d immediately. Matured raw notes `digest` into wiki entries. `PreCompact` → `reflect` + `immune --fix` consolidate before context compaction. Dead knowledge gets `prune`d. Repeat forever.

## Integrations

**9 agents auto-detected** by `myco seed --auto-detect`:

| Cowork | Claude Code | Cursor | VS Code | Codex | Cline | Continue | Zed | Windsurf |
|---|---|---|---|---|---|---|---|---|

**Plugin bundle** (Cowork + Claude Code): single `myco-v0.3.3.plugin` file ships the MCP server, 8 skills (`myco:boot` / `:eat` / `:digest` / `:hunger` / `:reflect` / `:search` / `:observe` / `:absorb`), and two hooks (`SessionStart`, `PreCompact`) that enforce the hard contract. Lives in the repo at `plugin/myco-v0.3.3.plugin` — clone once, install in Cowork or Claude Code.

**MCP server**: `python -m myco.mcp_server` — stdio server exposing all 25 tools. Standard MCP; works with any compliant host.

**Hard contract** (enforced automatically):
1. Every session starts with `myco_hunger(execute=true)` — SessionStart hook.
2. Every session ends with `myco_reflect` + `myco_immune(fix=true)` — PreCompact hook.
3. Before any factual claim about the project, call `myco_sense` first.
4. Every decision / insight / friction point gets `myco_eat`'d immediately.
5. After creating any new file, add cross-references (orphans are dead knowledge).
6. Write only to paths in `_canon.yaml::system.write_surface.allowed`.

Rules 1–2 are mechanical. Rules 3–6 are agent discipline, surfaced by immune lint dimensions L26–L28.

## Troubleshooting

**`ModuleNotFoundError: No module named 'myco'`** — the engine isn't installed in the Python environment the plugin's MCP/hooks run in. Run `pip install -e ".[mcp]"` from your Myco clone (or `pip install 'myco>=0.3.3'` for a pinned install) in that environment.

**Agent says "Myco source is not mounted"** — bug in agent reasoning. Myco is a PyPI package; no source tree needs to be mounted. Point the agent at `$CLAUDE_PROJECT_DIR/_canon.yaml`.

**`SessionStart` hook times out** — a very large substrate (10k+ notes, dense mycelium graph) may exceed the 60s default. Raise `timeout` in `hooks/hooks.json` or run `myco hunger --fast`.

**Auto-seed refused in an empty dir** — intentional. Myco refuses to seed dirs without at least one project marker (`.git`, `pyproject.toml`, `package.json`, `README.md`, …) to protect against polluting home / system dirs. Create one marker or run `myco seed --level 1` explicitly.

## Contributing

```bash
git clone https://github.com/Battam1111/Myco.git
cd Myco && pip install -e ".[mcp,dev]"
pytest tests/              # unit tests across every verb and dimension
myco immune --project-dir . # self-lint Myco with its own immune system
```

Issues, PRs, and new host adapters welcome. See [`CONTRIBUTING.md`](CONTRIBUTING.md), the [agent protocol](docs/agent_protocol.md), and the [craft protocol](docs/craft_protocol.md) for how kernel changes get proposed and reviewed.

MIT · [`LICENSE`](LICENSE) · [PyPI](https://pypi.org/project/myco/) · [Releases](https://github.com/Battam1111/Myco/rel