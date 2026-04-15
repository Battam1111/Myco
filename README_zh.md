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

想象一个 AI——它从不忘记你教过它什么。它吞噬你抛过来的每一篇论文、每一个决定、每一句"我之前搞错了"。它会注意到自己的理解已经过期，然后自己修好。它把今天的想法和三个月前你早就忘掉的那条笔记连在一起，这样你不用自己记。

这就是 Myco。

Myco 是 **你那位 AI Agent 的活体认知底物**——Agent 的另一半，由它来喂养、消化、守护、陪你一起长。不是记忆数据库、不是 Agent 运行时、不是技能框架。它活在 Agent 旁边，把 Agent 变成一个**会记事的搭档**。

### 它立在五条原则之上

- **只为 Agent 而生。** 你不浏览 Myco。你和 Agent 说话；Agent 读 Myco。每一个表面——`_canon.yaml`、notes、doctrine 文档、boot brief——都是写给 Agent 读的主材料，不是给人看的文档。
- **吞噬万物。** 摄入不设过滤。决策、摩擦、论文、日志、半成型的念头——谁来谁进，raw 留着。形状以后再说。错过信号的代价永远高于吃多的代价。
- **形态在演化。** canon schema、lint 维度、连契约本身都是一等可变对象。僵死的底物就是死的底物。演化走治理（craft → PR → bump），不是走漂移。
- **没有"最终版"。** `integrated` 是状态不是终点。今天消化完的笔记，明天 context 锐化了可以再消化一遍。反思是心跳，不是家务。
- **菌丝网络。** 每条 note、每个 canon 字段、每份 doctrine 页都靠遍历连到别的上。孤儿就是死组织。这个图就是 Agent 读知识的方式——所以它必须一直活着。

### 三种角色，合作着干活

**你** —— 定方向。说要做什么。不记 CLI、不整理文件、不向第二个会话重新解释你的项目。

**Agent** —— 出智能。读你说的话，读 Myco，挑 verb，写回去。

**Myco** —— 跑代谢。你说完一句话到下一句话之间，它 **hunger**（缺什么？）、**eat**（raw 进来）、**reflect / digest / distill**（raw → 结构化 → doctrine）、用 **immune** 系统防漂移、用 **propagate** 把学到的跨项目扩散。12 个 verb、1 份 manifest、两个面：CLI 给你观察，MCP 让 Agent 自己开。

> **kernel 稳定，substrate 可变。** `pip install` 把 kernel 锁在一个已发布版本；substrate（`_canon.yaml`、`notes/`、`docs/primordia/`）由 12 个 MCP verb 驱动日常演化。kernel 的演化走 upstream 治理。

## 快速上手

```bash
pip install 'myco[mcp]'
cd /path/to/your/project
myco genesis . --substrate-id my-project
```

三个控制台脚本进 PATH：

- `myco` —— 12 个 verb 的 CLI。
- `mcp-server-myco` —— 通用 MCP stdio 启动器，插进任何 host 都能跑。
- `myco-install` —— 一条命令装进七个主流 MCP host。

**Claude Code / Cowork** 官方 plugin 一步装好（MCP + hooks + slash skills）：

```
/plugin marketplace add Battam1111/Myco
/plugin install myco@myco
```

**其他 MCP host** 一条命令搞定：

```bash
myco-install cursor        # 也可以：claude-desktop / windsurf / zed / vscode / openclaw
```

或者把通用片段贴进 host 的配置文件——适用 `mcpServers` 家族（Claude Desktop、Cursor、Windsurf、Cline、Roo Code、Gemini CLI、Qwen Code、JetBrains AI、Augment Code、AiderDesk）：

```json
{ "mcpServers": { "myco": { "command": "mcp-server-myco", "args": [] } } }
```

配置 schema 不一样的 8 个 host —— VS Code Copilot（`servers`）、Zed（`context_servers`）、OpenClaw（`mcp.servers` + CLI）、OpenHands（TOML）、OpenCode / Kilo Code（`mcp`）、Codex CLI（TOML）、Goose（YAML `extensions`）、Continue（YAML block）、Warp（`mcp_servers`）—— 每个都有自己精确的片段，在 [`docs/INSTALL.md`](docs/INSTALL.md)，连带 Python 框架 adapter（LangChain · CrewAI · DSPy · Smolagents · Agno · PraisonAI · Microsoft Agent Framework · Claude Agent SDK）。

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

7 条硬契约（R1–R7）由 hook、免疫系统、Agent 自律三方共同强制。完整条文：[`L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md)。

## 跨平台强制机制 —— 一个都不漏

R1–R7 在 Claude Code / Cowork 里是 hook 强制的。其它 host —— Cursor、Windsurf、Zed、Codex、Gemini、Continue、Claude Desktop、OpenClaw、OpenHands —— 强制**藏在 MCP server 本身**：

- **初始化指令。** `initialize` 阶段每个 host 都收到一份简短的 R1–R7 摘要，链到 [`L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md)。读 instructions 的 Agent 在首次调 tool 前就看到契约。
- **`substrate_pulse` 边车字段。** 每个 tool 响应都携带 `substrate_pulse`，包含当前 `contract_version`、`substrate_id`，以及一条会从 R1（hunger 未调）升级到 R3（sense before assert）的 rule hint。这是服务端主动推——Agent 想忘也忘不了。

host 侧零配置，每个 MCP 客户端都生效。

## 集成

- **Claude Code / Cowork** —— `/plugin marketplace add Battam1111/Myco` → `/plugin install myco@myco`。或者手工拷 `.claude/`。
- **任何 MCP host** —— 七个常见 host 用 `myco-install <client>`，其它地方用 `mcp-server-myco` stdio。精确的 per-host 片段见 [`docs/INSTALL.md`](docs/INSTALL.md)。
- **Python agent 框架** —— LangChain · CrewAI · DSPy · Smolagents · Agno · PraisonAI · Microsoft Agent Framework · Claude Agent SDK 都通过 `StdioServerParameters(command="mcp-server-myco")` 消费 Myco。
- **下游 substrate** —— `myco propagate` 发布；adapter 住在 `myco.symbionts`。

## 了解更多

[`L0_VISION.md`](docs/architecture/L0_VISION.md) · [`L1_CONTRACT/`](docs/architecture/L1_CONTRACT/) · [`L2_DOCTRINE/`](docs/architecture/L2_DOCTRINE/) · [`INSTALL.md`](docs/INSTALL.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [Issues](https://github.com/Battam1111/Myco/issues)

贡献：`pip install -e ".[dev]"`；架构性改动落地为 [`docs/primordia/`](docs/primordia/) 下带日期的 craft 文档。

MIT · [`LICENSE`](LICENSE) · [PyPI](https://pypi.org/project/myco/) · [Releases](https://github.com/Battam1111/Myco/releases)
