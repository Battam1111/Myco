# Myco Symbionts — Multi-Platform Adapter Coverage

Myco adapts seamlessly to 9 IDE/agent environments. Each adapter detects its host and installs hooks at the appropriate level (native, daemon, or protocol fallback).

## Platform Coverage

| Host | Hook Level | Detection | Config Path | install_hooks() |
|------|-----------|-----------|-------------|-----------------|
| **Cowork** | native | `COWORK_SESSION` env or `/sessions/` cwd | `.claude/settings.json` | ✅ Session hooks + MCP |
| **Claude Code** | native | `.claude/` dir or `CLAUDE_CODE` env | `.mcp.json` + `.claude/settings.json` | ✅ MCP + rules |
| **Cursor** | native | `.cursor/` dir or `CURSOR_SESSION` env | `.cursor/mcp.json` + `.cursorrules` | ✅ Rules + MCP |
| **VS Code** | protocol | `.vscode/` dir or `code` CLI | `.vscode/mcp.json` (Copilot) | ✅ MCP only |
| **Continue** | protocol | `.continue/` dir | `.continue/config.json` | ✅ MCP + rules |
| **Zed** | protocol | `.zed/` dir or `zed` CLI | `.zed/settings.json` | ✅ MCP + rules |
| **Codex** | native* | `~/.codex/` dir or `codex` CLI | `~/.codex/config.toml` + `hooks.json` | ✅ Native (Unix) / protocol (Windows) |
| **Cline** | protocol | global `cline_mcp_settings.json` exists | OS-specific path (see below) | ✅ MCP only |
| **Windsurf** | native | `~/.codeium/windsurf/` or `windsurf` CLI | `.windsurf/rules/*.md` | ✅ Rules files |

*Codex hook level is "native" on Unix/macOS (supports hooks.json), "protocol" on Windows (no native hooks).

## OS-Specific Paths

### Cline MCP Settings
- **Windows**: %APPDATA%/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
- **macOS**: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
- **Linux**: `~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

### Myco Home
- **Windows**: `%APPDATA%\Myco`
- **macOS/Linux**: `$XDG_CONFIG_HOME/myco` (fallback `~/.config/myco`)

## Auto-Setup

When you run `myco` for the first time in a project:

1. **Auto-detect** scans environment variables, project directories, and CLI tools in priority order
2. **Prompt** (TTY-aware): asks permission to install hooks
3. **Dispatch** calls matching adapter's `install_hooks(root)` method
4. **Mark** writes `.init-complete` marker in Myco home to skip future runs
5. **Skip** if `MYCO_NO_AUTOINSTALL=1` env var is set

## For Developers: Adapter API

Each adapter module (`src/myco/hosts/*.py`) exports:

```python
def detect() -> bool:
    """Return True if this host environment is active."""

def check_hooks(root: Path) -> Dict[str, Any]:
    """Return status dict: {host, hook_level, issues, notes, ...}"""

def install_hooks(root: Path) -> Dict[str, Any]:
    """Install Myco hooks; return {installed, hook_level, notes}."""
```

See `src/myco/symbionts/common.py` for shared utilities:
- `user_config_dir()`, `user_data_dir()`, `vscode_global_storage_dir()`
- `json_merge_write()`, `toml_merge_write()`, `ensure_marker_block()`
- `HOOK_LEVEL_*` constants
