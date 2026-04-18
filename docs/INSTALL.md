# Installing Myco

Two things need configuring: **(a)** Myco itself on your machine,
and **(b)** the MCP host(s) that will talk to it. Most users do both
in one shot.

The primary install path is **editable** (v0.5.2+). Kernel code
lives at a writable location the agent can mutate — this is what
makes 永恒进化 / 永恒迭代 real in code, not just README prose. A
classic read-only `pip install` still works for library consumers
and ephemeral containers; it's a second-class path documented later.

---

## 0. Primary path — `myco-install fresh`

One line, no git ceremony, no lingering bootstrap install:

```bash
pipx run --spec 'myco[mcp]' myco-install fresh ~/myco
```

Or two steps if you prefer:

```bash
pip install 'myco[mcp]'
myco-install fresh ~/myco
```

Both forms:

1. `git clone` this repo into `~/myco` (override with a positional
   `<target>`; the default is `~/myco`).
2. `pip install -e` the clone into the current Python environment
   (override extras with `--extras mcp,adapters,dev`).
3. Verify by running `python -m myco --help`.

Optional: configure one or more MCP hosts in the same step. The
flag is a shorthand — `--configure claude-code cursor` is exactly
equivalent to running `myco-install host claude-code` and
`myco-install host cursor` after `fresh` completes. Each listed
client goes through the same schema-aware writer documented in
section 1 (MCP host config), preserving any sibling servers already
present.

```bash
myco-install fresh ~/myco --configure claude-code cursor windsurf
```

Common flags:

| Flag | Meaning |
|---|---|
| `--target <path>` (positional) | Where to clone. Default: `~/myco`. |
| `--repo <url>` | Override clone source (e.g. a fork or mirror). |
| `--branch <ref>` | Check out a specific branch or tag. |
| `--depth <N>` | Shallow clone (history-audit evidence is lost). |
| `--extras mcp,dev,adapters` | Pip extras installed alongside. Default: `mcp`. |
| `--configure <client ...>` | Run `myco-install host <client>` for each after install. |
| `--force` | Overwrite a non-empty target (destructive). |
| `--dry-run` | Print every step; make no changes. |

Upgrade later with plain `git pull` inside `~/myco` (not
`pip install --upgrade`):

```bash
cd ~/myco && git pull
myco immune                       # verify no post-upgrade drift
```

Once installed, the agent germinates a downstream substrate anywhere:

```bash
myco germinate --project-dir /path/to/project --substrate-id my-project
```

`germinate` is the v0.5.3 canonical name; the legacy `genesis`
alias still resolves (with a one-shot `DeprecationWarning`) for
v0.5.2 cached invocations.

---

## 1. Per-host MCP config — `myco-install host`

Myco runs as an MCP server, so any host that speaks MCP can talk to
it. The wrinkle: the ecosystem **fragmented on config schema** —
`mcpServers` is most common, but several popular hosts use their own
key name (`servers`, `context_servers`, `extensions`) or their own
file format (TOML, YAML). Copy-paste one snippet everywhere does not
work. `myco-install host` writes the correct schema per host.

```bash
myco-install host <client>
```

Legacy form `myco-install <client>` (without the `host` subcommand)
still works — it's auto-routed to `host <client>` for backward
compatibility with v0.4/v0.5 scripts.

`myco-install` writes the **absolute Python interpreter path** plus
`-m myco.mcp` into the host's config. This sidesteps the most
common MCP failure: GUI apps (Claude Desktop, Cursor, Windsurf) do
NOT inherit the shell PATH, so the bare `mcp-server-myco` console
script is invisible to them. The absolute-path form works regardless
of PATH, venv, or `python` vs `python3` aliasing.

Supported clients (writes the correct schema, preserves any sibling
servers, idempotent, supports `--dry-run` and `--uninstall`):

| Client | Command | Notes |
|---|---|---|
| Claude Code | `myco-install host claude-code` | Writes project `.mcp.json`; `--global` writes `~/.claude.json` |
| Claude Desktop | `myco-install host claude-desktop` | OS-correct path (macOS / Windows / Linux) |
| Cursor | `myco-install host cursor` | Project `.cursor/mcp.json`; `--global` writes `~/.cursor/mcp.json` |
| Windsurf | `myco-install host windsurf` | `~/.codeium/windsurf/mcp_config.json` |
| Zed | `myco-install host zed` | Uses the `context_servers` key, not `mcpServers` |
| VS Code | `myco-install host vscode` | Uses the `servers` key in `.vscode/mcp.json` |
| OpenClaw | `myco-install host openclaw` | Shells out to `openclaw mcp set myco …`; CLI must be on PATH |
| Gemini CLI | `myco-install host gemini-cli` | `~/.gemini/settings.json`, standard `mcpServers` schema |
| Codex CLI | `myco-install host codex-cli` | `~/.codex/config.toml`, `[mcp_servers.myco]` table; block-level TOML surgery preserves comments and other tables |
| Goose | `myco-install host goose` | `~/.config/goose/config.yaml`, uses the `extensions` key, not `mcpServers` |

Run `myco-install host <client> --dry-run` first to see exactly
what will be written (works for every client above, including the
TOML-based Codex CLI and YAML-based Goose). Run `myco-install host
<client> --uninstall` to remove the entry and leave any sibling
servers untouched.

---

## 2. Manual path per host

If you would rather write the config file by hand, or the host is
not yet in the `myco-install` list, here is the exact snippet per
host.

### The common `mcpServers` snippet

Works on **Claude Code**, **Claude Desktop**, **Cursor**, **Windsurf**,
**Cline**, **Roo Code**, **Gemini CLI**, **Qwen Code**, **Augment Code**,
**JetBrains AI Assistant**, **AiderDesk**:

```json
{
  "mcpServers": {
    "myco": { "command": "mcp-server-myco", "args": [] }
  }
}
```

Config paths:

| Host | Path |
|---|---|
| Claude Code | `.mcp.json` (project) or `~/.claude.json` (global) |
| Claude Desktop (macOS) | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Claude Desktop (Windows) | `%APPDATA%\Claude\claude_desktop_config.json` |
| Claude Desktop (Linux) | `~/.config/Claude/claude_desktop_config.json` |
| Cursor | `.cursor/mcp.json` or `~/.cursor/mcp.json` |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` |
| Cline | `cline_mcp_settings.json` in VS Code's global storage |
| Roo Code | `mcp_settings.json` (global) or `.roo/mcp.json` (project) |
| Gemini CLI | `~/.gemini/settings.json` (also automated via `myco-install host gemini-cli`) |
| Qwen Code | `~/.qwen/settings.json` |
| AiderDesk | UI → Settings → MCP |

### VS Code GitHub Copilot (different key)

`.vscode/mcp.json` or `~/.vscode/mcp.json`:

```json
{
  "servers": {
    "myco": { "type": "stdio", "command": "mcp-server-myco", "args": [] }
  }
}
```

### Zed (different key)

`~/.config/zed/settings.json`:

```json
{
  "context_servers": {
    "myco": { "source": "custom", "command": "mcp-server-myco", "args": [] }
  }
}
```

### OpenClaw (nested key + CLI mutator)

```bash
openclaw mcp set myco '{"command": "mcp-server-myco", "args": []}'
```

Or edit config directly:

```json
{
  "mcp": {
    "servers": {
      "myco": { "command": "mcp-server-myco", "args": [] }
    }
  }
}
```

### OpenHands (TOML)

Append to `config.toml`:

```toml
[[mcp.stdio_servers]]
name = "myco"
command = "mcp-server-myco"
args = []
```

### OpenCode / Kilo Code (JSON, different key)

In `opencode.json` or `kilo.jsonc`:

```json
{
  "mcp": {
    "myco": {
      "type": "local",
      "command": ["mcp-server-myco"]
    }
  }
}
```

Kilo Code also accepts the legacy `mcpServers` schema in
`mcp_settings.json` (same as Cline / Roo).

### Codex CLI (TOML)

Append to `~/.codex/config.toml`:

```toml
[mcp_servers.myco]
command = "mcp-server-myco"
args = []
```

Or one-liner: `codex mcp add myco -- mcp-server-myco`.
(Also automated via `myco-install host codex-cli` — does block-level
TOML surgery so your other `[mcp_servers.*]` tables and comments
survive untouched.)

### Goose (YAML, different key)

In `~/.config/goose/config.yaml`:

```yaml
extensions:
  myco:
    type: stdio
    command: mcp-server-myco
    args: []
    enabled: true
```

(Also automated via `myco-install host goose` — preserves sibling
`extensions.*` entries and unrelated top-level keys.)

### Warp (cloud agent YAML)

```yaml
mcp_servers:
  myco:
    command: mcp-server-myco
    args: []
```

### Continue (YAML, one file per server)

`.continue/mcpServers/myco.yaml`:

```yaml
name: Myco
version: 0.4.1
schema: v1
mcpServers:
  - name: myco
    type: stdio
    command: mcp-server-myco
    args: []
```

### JetBrains AI Assistant / Junie

Settings → Tools → AI Assistant → MCP → Add server. Paste the
standard `mcpServers` snippet in the dialog.

### Devin (web UI only)

Settings → MCP Marketplace → Add Your Own. Fill the form fields:

- Name: `myco`
- Command: `mcp-server-myco`
- Args: `[]`

### Bolt.new / StackBlitz (web UI)

Same as Devin — web form, same field values.

---

## 3. Python-agent frameworks

These are not "MCP host config" — they are libraries that consume
MCP servers from Python.

### LangChain / LangGraph

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({
    "myco": {
        "transport": "stdio",
        "command": "mcp-server-myco",
        "args": [],
    }
})
tools = await client.get_tools()
```

### CrewAI

```python
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters

params = StdioServerParameters(command="mcp-server-myco", args=[])
adapter = MCPServerAdapter(params)
```

### DSPy

```python
import dspy
from mcp import StdioServerParameters

params = StdioServerParameters(command="mcp-server-myco", args=[])
tools = [dspy.Tool.from_mcp_tool(t, params) for t in ...]
```

### Smolagents

```python
from smolagents import ToolCollection
with ToolCollection.from_mcp(
    {"command": "mcp-server-myco", "args": []}
) as tools:
    ...
```

### Agno

```python
from agno.tools.mcp import MCPTools
tools = MCPTools(command="mcp-server-myco", args=[])
```

### PraisonAI

```python
from praisonai.tools import MCP
tools = [MCP("mcp-server-myco")]
```

### Microsoft Agent Framework (AutoGen successor)

```python
from agent_framework.mcp import McpWorkbench, StdioServerParams

params = StdioServerParams(command="mcp-server-myco", args=[])
workbench = McpWorkbench(params)
```

### Claude Agent SDK (Python or TypeScript)

```python
from claude_agent_sdk import ClaudeAgent

agent = ClaudeAgent(
    mcp_servers={
        "myco": {"command": "mcp-server-myco", "args": []}
    }
)
```

---

## 4. Hosts without first-class MCP support

- **Aider** (the CLI, not AiderDesk): no native MCP as of 2026-04
  (upstream issue [aider-ai/aider#4506](https://github.com/Aider-AI/aider/issues/4506)).
  Community bridge: [`mcpm-aider`](https://github.com/lutzleonhardt/mcpm-aider).
- **SWE-agent**: research-focused, no MCP. Superseded by
  `mini-swe-agent`.
- **Void editor**: project paused by maintainers; not recommended
  as a primary target.

---

## 5. Installing the MCP server itself

Three install routes:

```bash
pip install 'myco[mcp]'     # standard pip
pipx install 'myco[mcp]'    # isolated, recommended for end users
uvx mcp-server-myco         # zero-install, runs ephemerally
```

Verify with `mcp-server-myco --help` or `myco --version`.

---

## 6. Substrate-local plugins

A downstream substrate can carry its own lint dimensions, ingestion
adapters, schema upgraders, and even brand-new verbs without
forking Myco or publishing a PyPI package. The mechanism is two
paths under the substrate root:

| Path | Role |
|---|---|
| `<substrate>/.myco/plugins/__init__.py` | Auto-imported on `Substrate.load()`. Registration side effects (new `Dimension` subclass, new `Adapter`, new `schema_upgrader`, new verb handler) run here. |
| `<substrate>/.myco/manifest_overlay.yaml` | Merged into the runtime command manifest at `build_context()` time. Locally-authored verbs appear alongside built-ins. |

The agent scaffolds these via the extended `ramify` verb:

```bash
# Scaffold a local lint dimension (writes to .myco/plugins/dimensions/local1.py)
myco ramify --dimension LOCAL1 --category mechanical --severity medium

# Scaffold a local ingestion adapter
myco ramify --adapter jira --extensions .jira,.json

# Scaffold a local verb handler stub
myco ramify --verb mythinking
```

`--substrate-local` defaults ON when `canon.identity.substrate_id`
is not `myco-self` (i.e. any downstream substrate) OR when
`<substrate_root>/src/myco/` does not exist. On `myco-self` itself
the flag is OFF by default and `ramify` writes into the kernel
tree; pass `--substrate-local` explicitly to override.

Once plugins are in place, `myco graft` inspects them:

```bash
myco graft --list                 # Enumerate every loaded local plugin
myco graft --validate             # Re-run the import + registration gate
myco graft --explain <name>       # Source file + class docstring
```

The new `MF2` lint dimension (mechanical / HIGH) fires on broken
`.myco/plugins/` shape, missing `__init__.py`, manifest-overlay
YAML errors, or duplicate verb names across the overlay and the
packaged manifest. Magical imports stay audible.

---

## 7. Troubleshooting

### `spawn mcp-server-myco ENOENT` (most common)

**GUI apps (Claude Desktop, Cursor, Windsurf) do NOT inherit your
shell PATH.** The `mcp-server-myco` console script might be in
`~/.local/bin` or `C:\Users\...\Python313\Scripts`, but GUI apps
don't see those directories.

**Fix**: use `myco-install <client>` which writes the absolute
Python interpreter path into the config. If you prefer to configure
by hand, use this form instead of the bare console-script name:

```json
{
  "mcpServers": {
    "myco": {
      "command": "/absolute/path/to/python3",
      "args": ["-m", "myco.mcp"]
    }
  }
}
```

Find your absolute Python path with:

```bash
python -c "import sys; print(sys.executable)"
```

### `ModuleNotFoundError: No module named 'mcp'`

You installed `myco` without the MCP extra. Reinstall:

```bash
pip install 'myco[mcp]'
```

### "Server disconnected" with no details

Check the server can start manually:

```bash
python -m myco.mcp --help
```

If that fails, look at the error. Common causes: wrong Python
version (need >=3.10), or missing `mcp` dependency.
