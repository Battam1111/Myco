<p align="center">
  <a href="https://github.com/Battam1111/Myco">
    <img src="https://raw.githubusercontent.com/Battam1111/Myco/main/assets/logo_light_512.png" width="160" alt="Myco">
  </a>
</p>

<h1 align="center">Myco</h1>

<p align="center"><b>吞噬万物。永恒进化。你只管说话。</b></p>

<p align="center">
  <a href="https://pypi.org/project/myco/"><img src="https://img.shields.io/pypi/v/myco?style=flat&cache_seconds=0" alt="PyPI"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=flat" alt="License"></a>
  <a href="https://github.com/Battam1111/Myco"><img src="https://img.shields.io/github/stars/Battam1111/Myco?style=flat" alt="Stars"></a>
</p>

<p align="center">
  <a href="#快速上手">快速上手</a> · <a href="#日常流程">日常流程</a> · <a href="#系统架构">系统架构</a> · <a href="#集成">集成</a>
</p>

<p align="center">
  <b>Languages:</b> <a href="README.md">English</a> · 中文 · <a href="README_ja.md">日本語</a>
</p>

---

LangChain。LangGraph。CrewAI。DSPy。Hermes。每个月都有新框架承诺"就是它了"。你花在挑工具上的时间，比实际用工具做东西的时间还多。

而且不只是框架。论文、API、最佳实践——天天都在刷新。笔记 App 里攒了 500 条，上次整理：三个月前，也许更久。那些精心写下的笔记？正在腐烂。三周前那个 API？版本变了。**没有任何东西在替你检查。**

你的 AI 也不记得你上周做了什么决定。每次对话，都是从零开始。

<br>

现在想象另一种活法：你就像正常人一样说话。不整理、不比较、不追论文、不重新解释项目。半年之后，你的 AI 比任何人的都锋利——它自己去吞噬了你领域里最新的工作，自己发现了自己的盲区，自己扔掉了不再成立的旧知识，自己把不够用的运作规则重写了。

<h3 align="center">这就是 Myco。</h3>

---

## Myco 是什么

Myco 是一个 **面向 Agent 的共生认知底物**——*你那位 Agent 的另一半*。不是记忆层、不是 Agent 运行时、不是技能框架。它是一个 **自创生底物（autopoietic substrate）**：Agent 带来智能；Myco 带来记忆、免疫、代谢、自我模型，以及它自身的进化。少了哪一半都不完整。

> **kernel 稳定，substrate 可变。** `pip install` 把 kernel 锁在一个已发布版本；Agent 日常演化的所有东西（`_canon.yaml`、`notes/`、`docs/primordia/`）都在你的 substrate 里，由 12 个 MCP verb 驱动。kernel 的演化走 upstream 治理：craft → PR → bump。

## 快速上手

```bash
pip install 'myco[mcp]'          # 包 + MCP SDK + 控制台脚本
cd /path/to/your/project
myco genesis . --substrate-id my-project
```

两个控制台脚本会进 PATH：

- `myco` —— 12 个 verb 的 CLI。
- `mcp-server-myco` —— 通用 MCP stdio 启动器，插进任何 host 都能跑。

**Claude Code / Cowork** 装官方 plugin（hooks + skills + MCP 一步到位）：

```
/plugin marketplace add Battam1111/Myco
/plugin install myco@myco
```

**任何其他 MCP host** 一行配置通吃——Myco 提供稳定的控制台脚本，你不用再纠结 `python` 还是 `python3`、host 会 spawn 到哪个 venv：

```json
{ "mcpServers": { "myco": { "command": "mcp-server-myco", "args": [] } } }
```

| Host | 配置路径 | 安装动作 |
|---|---|---|
| **Cursor** | `.cursor/mcp.json`（项目）或 `~/.cursor/mcp.json`（全局） | 粘贴上面那段 |
| **Windsurf** | `~/.codeium/windsurf/mcp_config.json` | 粘贴上面那段 |
| **Zed** | `~/.config/zed/settings.json` → `context_servers.myco` | `{"source":"custom","command":"mcp-server-myco","args":[]}` |
| **Codex CLI** | 一行或 `~/.codex/config.toml` | `codex mcp add myco -- mcp-server-myco` |
| **Gemini CLI** | `~/.gemini/settings.json` → `mcpServers.myco` | 粘贴上面那段 |
| **Continue** | `.continue/mcpServers/myco.yaml` | `name: Myco` · `type: stdio` · `command: mcp-server-myco` |
| **Claude Desktop** | `claude_desktop_config.json` → `mcpServers.myco` | 粘贴上面那段 |
| **LangChain / CrewAI / DSPy / Agent Framework** | Python | `StdioServerParameters(command="mcp-server-myco")` |

*Aider 目前原生不支持 MCP（见 aider-ai/aider #4506），社区 bridge `mcpm-aider` 可以过渡。*

库方式嵌入：

```python
from myco.mcp import build_server
build_server().run()                   # stdio（默认）
build_server().run(transport="sse")    # HTTP SSE
```

想贡献或 fork？走 editable install：

```bash
git clone https://github.com/Battam1111/Myco && cd Myco
pip install -e '.[dev,mcp]'
```

## 日常流程

Agent 自己去驱动，你什么都不用背。12 个 verb 按 5 个 subsystem 分组如下：

| Subsystem | Verbs | 做什么 |
|---|---|---|
| **Genesis** | `genesis` | 起一个新 substrate。 |
| **Ingestion** | `hunger` · `sense` · `forage` · `eat` | 当前需要什么；关键词搜索；列出可摄入文件；记录一条 raw note。 |
| **Digestion** | `reflect` · `digest` · `distill` | raw → integrated；integrated → doctrine 蒸馏。 |
| **Circulation** | `perfuse` · `propagate` | 交叉引用图健康度；发布到下游 substrate。 |
| **Homeostasis** | `immune` | 4 类 / 8 维一致性 lint（支持 `--fix`）。 |
| *（meta）* | `session-end` | `reflect` + `immune --fix`；由 PreCompact 自动触发。 |

CLI：`myco VERB`——全局 flag（`--project-dir`、`--json`、`--exit-on`）必须放在 verb **之前**。MCP：一 verb 一 tool，参数由 `src/myco/surface/manifest.yaml` 机械派生（CLI 和 MCP 的 SSoT）。

## 系统架构

```
你 ──▶ Agent ──▶ Myco substrate
                   ├── _canon.yaml        SSoT：identity · 写面 · lint 策略
                   ├── MYCO.md            Agent 入口页（R1）
                   ├── notes/{raw,integrated,distilled}/
                   ├── docs/architecture/ L0 vision · L1 contract · L2 doctrine · L3 impl
                   ├── src/myco/          genesis · ingestion · digestion · circulation · homeostasis · surface
                   └── .claude/hooks/     SessionStart → hunger · PreCompact → session-end
```

三种角色——**你** 定方向，**Agent** 带智能，**Myco** 带记忆和连续性。7 条硬契约（R1–R7）由 hook、免疫系统、Agent 自律三方共同强制。完整条文：[`L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md)。

## 跨平台强制机制

R1–R7 在 Claude Code / Cowork 里是 hook 强制的。其它 host 没有 hook 概念——但强制藏在 MCP server 本身：

- **初始化指令。** `initialize` 阶段每个 host 都收到一份简短的 R1–R7 摘要，链到 [`L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md)。读 instructions 的 Agent 在首次调 tool 前就看到契约。
- **`substrate_pulse` 边车字段。** 每个 tool 响应都携带 `substrate_pulse`，包含当前 `contract_version`、`substrate_id`，以及一条会从 R1（hunger 未调）升级到 R3（sense before assert）的 rule hint。这是服务端主动推——Agent 想忘也忘不了。

边车机制在 Cursor、Windsurf、Zed、Codex、Gemini、Continue、Claude Desktop 上都生效，host 侧零配置。

## 集成

- **Claude Code / Cowork** —— `/plugin marketplace add Battam1111/Myco` 再 `/plugin install myco@myco`，或者手工拷 `.claude/`。两条路都把 SessionStart → `hunger`、PreCompact → `session-end` 接好。
- **任何 MCP host** —— `mcp-server-myco` 控制台脚本走 stdio（或 `--transport sse` 走 HTTP），或者 `myco.mcp:build_server` 嵌库。
- **下游 substrate** —— `myco propagate` 发布；adapter 住在 `myco.symbionts`。

## 了解更多

[`L0_VISION.md`](docs/architecture/L0_VISION.md) · [`L1_CONTRACT/`](docs/architecture/L1_CONTRACT/) · [`L2_DOCTRINE/`](docs/architecture/L2_DOCTRINE/) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [Issues](https://github.com/Battam1111/Myco/issues)

贡献：`pip install -e ".[dev]"`；架构性改动落地为 [`docs/primordia/`](docs/primordia/) 下带日期的 craft 文档。

MIT · [`LICENSE`](LICENSE) · [PyPI](https://pypi.org/project/myco/) · [Releases](https://github.com/Battam1111/Myco/releases)
