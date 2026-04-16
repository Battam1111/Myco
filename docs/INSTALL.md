# Installing Myco into your MCP host

Myco runs as an MCP server, so any host that speaks MCP can talk to
it. The wrinkle: the ecosystem **fragmented on config schema** —
`mcpServers` is most common, but seven popular hosts use their own
key name or their own file format. Copy-paste one snippet everywhere
does not work. This doc lists every host, the correct command or
snippet, and whether `myco-install` can do it for you.

---

## 1. One-command path — `myco-install`

```bash
pip install 'myco[mcp]'
myco-install <client>
```

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
| Claude Code | `myco-install claude-code` | Writes project `.mcp.json`; `--global` writes `~/.claude.json` |
| Claude Desktop | `myco-install claude-desktop` | OS-correct path (macOS / Windows / Linux) |
| Cursor | `myco-install cursor` | Project `.cursor/mcp.json`; `--global` writes `~/.cursor/mcp.json` |
| Windsurf | `myco-install windsurf` | `~/.codeium/windsurf/mcp_config.json` |
| Zed | `myco-install zed` | Uses the `context_servers` key, not `mcpServers` |
| VS Code | `myco-install vscode` | Uses the `servers` key in `.vscode/mcp.json` |
| OpenClaw | `myco-install openclaw` | Shells out to `openclaw mcp set myco …`; CLI must be on PATH |

Run `myco-install <client> --dry-run` first to see exactly what
will be written. Run `myco-install <client> --uninstall` to remove
the entry.

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
| Gemini CLI | `~/.gemini/settings.json` |
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

## 6. Troubleshooting

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
