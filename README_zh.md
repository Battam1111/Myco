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

LangChain。LangGraph。CrewAI。DSPy。Claude Code skills。OpenHands。OpenClaw。每隔几个月下一个框架又掉下来，你又迁移一次。

你的笔记也在烂。三周前读的 API 已经改了。去年写的那份文档现在是错的。你的 AI 连上周的决定都不记得。每次新对话，都是从零开始。

<br>

现在想象一套活底物。它吞噬那些框架、论文、API、代码仓库、数据集、决策、摩擦。它把这些东西保留在一张 Agent 能真正读的图里。它自己发现自己的漂移并修好。当你的工作超出了它旧的形状，它自己重塑形状。用半年。用六年。不需要迁移。

<h3 align="center">这就是 Myco。</h3>

---

## Myco 是什么

Myco 是你那位 AI Agent 的活体认知底物。**不是框架。是吞噬框架的底物。**

Myco 吞噬代码仓库、框架文档、数据集、论文、聊天记录、决策和摩擦。Agent 能指向的任何东西都成为原料。它把这些消化掉，接入菌丝图，用免疫系统防漂移，把知识跨项目扩散。当工作改变形状时，Myco 跟着改：Agent 提议（craft），你批准，kernel bump。新的 canon 字段、新的 lint 维度、新的 verb、新的 subsystem。哪怕整个内部完全重写，也只是一次 `myco` 的版本升级，不是换一个依赖。底层的底物永远不被扔掉。

**你从此不需要再迁移。**

这件事现在能做到，不是因为想法新，而是因为 Agent 终于聪明到能自己维护这套系统。以前的尝试都死在人跟不上上面。Myco 从第一个表面到最后一个 verb，都把"维护者是 Agent"当作设计前提。

### 五条原则

- **只为 Agent 而生。** 你不浏览 Myco。你和 Agent 说话，Agent 读 Myco。每个表面（`_canon.yaml`、notes、doctrine 文档、boot brief）都是写给 Agent 读的主材料，不是给人看的文档。
- **吞噬万物。** 摄入不设过滤。代码仓库、框架、论文、数据集、日志、半成型的念头、raw 决策。Agent 能指向什么，底物就吃什么。形状以后再说。错过信号的代价，永远高于多吃一点的代价。
- **形态在演化。** canon schema、lint 维度、verb、连契约本身都可变。工作超出旧形状时，Agent 提议，你批准，Myco 重塑。僵死的底物就是死的底物。
- **没有"最终版"。** `integrated` 是状态不是终点。今天消化完的笔记，明天 context 锐化了可以再消化一遍。反思是心跳。
- **菌丝网络。** 每条 note、每个 canon 字段、每份 doctrine 页都靠遍历连到别的上。孤儿就是死组织。这张图就是 Agent 读知识的方式，所以它必须一直活着。

### 三种角色

**你** 定方向。不记 CLI、不整理文件、不在新会话里重新解释项目。

**Agent** 出智能。读你的话，读 Myco，挑 verb，写回去。

**Myco** 跑代谢。你说完一句话到下一句话之间，它问缺什么（`hunger`）、吃进原料（`eat`）、把 raw 煮成结构化知识（`reflect`、`digest`、`distill`）、用免疫系统防漂移（`immune`）、跨项目扩散学到的（`propagate`）。12 个 verb、1 份 manifest、两个面：CLI 给你观察，MCP 给 Agent 自己开。

> **默认可编辑安装，kernel 本身就是 substrate。** Myco 自己的源码树就是一个 substrate（有 `_canon.yaml`、`MYCO.md`、`docs/primordia/`）。`src/myco/` 下的 kernel 代码只是这个 substrate 最里层的一圈。把这一圈锁进 `site-packages` 只读，就违反了 永恒进化 + 永恒迭代——Agent 变成别人代码的消费者，而不是自己维护的代码的作者。所以主路径是 clone 源码后 `pip install -e` 装成可编辑。PyPI 还在，只作为 bootstrap 通道和纯库消费路径，不再是正常安装路径。

## 快速上手

一条命令，不用预先 `git clone`，也不留任何 bootstrap 残留：

```bash
pipx run --spec 'myco[mcp]' myco-install fresh ~/myco
```

把本仓库 clone 到 `~/myco`，`pip install -e` 装成可编辑，留给你一份可写的 kernel + substrate。两步版也行：

```bash
pip install 'myco[mcp]'
myco-install fresh ~/myco         # clone + 可编辑安装；--dry-run 可预览
```

然后在任意项目内 bootstrap 下游 substrate：

```bash
cd /path/to/your/project
myco genesis . --substrate-id my-project
```

以后升级 kernel 直接在 `~/myco` 里 `git pull`，不是 `pip install --upgrade`：

```bash
cd ~/myco && git pull && myco immune        # 升级后跑免疫确认没漂移
```

三个控制台脚本进 PATH：

- `myco`：12 个 verb 的 CLI。
- `mcp-server-myco`：通用 MCP stdio 启动器，插进任何 host 都能跑。
- `myco-install`：一条命令装进七个主流 MCP host。

**Claude Code / Cowork** 官方 plugin 一步装好（MCP 服务器、hooks、slash skills 一起接线）：

```
/plugin marketplace add Battam1111/Myco
/plugin install myco@myco
```

**其他 MCP host** 一条命令搞定：

```bash
myco-install cursor        # 也可以：claude-desktop, windsurf, zed, vscode, openclaw
```

或者把通用片段贴进 host 的配置文件。适用 `mcpServers` 家族（Claude Desktop、Cursor、Windsurf、Cline、Roo Code、Gemini CLI、Qwen Code、JetBrains AI、Augment Code、AiderDesk）：

```json
{ "mcpServers": { "myco": { "command": "mcp-server-myco", "args": [] } } }
```

配置 schema 不一样的 9 个 host（VS Code Copilot `servers`、Zed `context_servers`、OpenClaw `mcp.servers` + CLI、OpenHands TOML、OpenCode / Kilo Code `mcp`、Codex CLI TOML、Goose YAML `extensions`、Continue YAML block、Warp `mcp_servers`）每个都有自己精确的片段，在 [`docs/INSTALL.md`](docs/INSTALL.md)。同一份 INSTALL.md 也覆盖 Python 框架 adapter（LangChain、CrewAI、DSPy、Smolagents、Agno、PraisonAI、Microsoft Agent Framework、Claude Agent SDK）。

库方式嵌入：

```python
from myco.mcp import build_server
build_server().run()                   # stdio（默认）
build_server().run(transport="sse")    # HTTP SSE
```

### 非演化安装（库消费者、CI、vendor）

如果你是把 Myco 作为依赖引入到另一个 Python 项目、或者在容器里要一份故意冻结的 kernel，普通只读安装仍然可用：

```bash
pip install 'myco[mcp]'
```

但 `myco scaffold`、Myco 自身的 kernel-level `craft`/`bump`、任何形式的 kernel 演化在这条路上都被堵死——这是设计，不是 bug。只读安装是给消费者用的，不是给作者用的。

### 想贡献 Myco

和主安装路径一样——`myco-install fresh` 就是贡献者路径。`--extras dev,mcp` 顺便拉测试工具：

```bash
pipx run --spec 'myco[mcp]' myco-install fresh ~/myco --extras dev,mcp
cd ~/myco
pytest
```

## 日常流程

Agent 自己驱动，你什么都不用背。12 个 verb 按 5 个 subsystem 分组如下：

| Subsystem | Verbs | 做什么 |
|---|---|---|
| **Genesis** | `genesis` | 起一个新 substrate。 |
| **Ingestion** | `hunger`、`sense`、`forage`、`eat` | 当前需要什么；关键词搜索；列出可摄入文件；记录一条 raw note。 |
| **Digestion** | `reflect`、`digest`、`distill` | raw 升到 integrated；integrated 蒸馏为 doctrine。 |
| **Circulation** | `perfuse`、`propagate` | 交叉引用图健康度；发布到下游 substrate。 |
| **Homeostasis** | `immune` | 4 类 / 8 维一致性 lint，支持 `--fix`。 |
| *（meta）* | `session-end` | `reflect` 加 `immune --fix`，由 PreCompact 自动触发。 |

CLI 用法是 `myco VERB`，全局 flag（`--project-dir`、`--json`、`--exit-on`）放在 verb **之前**。MCP 一 verb 一 tool，参数由 `src/myco/surface/manifest.yaml` 机械派生，CLI 和 MCP 共用这份 SSoT。

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

7 条硬契约（R1 到 R7）由 hook、免疫系统、Agent 自律三方共同强制。完整条文在 [`L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md)。

## 跨平台强制机制：一个都不漏

R1 到 R7 在 Claude Code 和 Cowork 里是 hook 强制的。其它 host（Cursor、Windsurf、Zed、Codex、Gemini、Continue、Claude Desktop、OpenClaw、OpenHands）强制**藏在 MCP server 本身**：

- **初始化指令。** `initialize` 阶段每个 host 都收到一份简短的 R1 到 R7 摘要，链到 [`L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md)。读 instructions 的 Agent 在首次调 tool 前就看到契约。
- **`substrate_pulse` 边车字段。** 每个 tool 响应都携带 `substrate_pulse`，包含当前 `contract_version`、`substrate_id`，以及一条会从 R1（hunger 未调）升级到 R3（sense before assert）的 rule hint。这是服务端主动推，Agent 想忘也忘不了。

host 侧零配置，每个 MCP 客户端都生效。

## 集成

- **Claude Code 和 Cowork**：`/plugin marketplace add Battam1111/Myco`，然后 `/plugin install myco@myco`。或者手工拷 `.claude/`。
- **任何 MCP host**：七个常见 host 用 `myco-install <client>`，其它地方用 `mcp-server-myco` stdio。精确的 per-host 片段见 [`docs/INSTALL.md`](docs/INSTALL.md)。
- **Python agent 框架**：LangChain、CrewAI、DSPy、Smolagents、Agno、PraisonAI、Microsoft Agent Framework、Claude Agent SDK 都通过 `StdioServerParameters(command="mcp-server-myco")` 消费 Myco。
- **下游 substrate**：`myco propagate` 发布，adapter 住在 `myco.symbionts`。

## 了解更多

[`L0_VISION.md`](docs/architecture/L0_VISION.md) · [`L1_CONTRACT/`](docs/architecture/L1_CONTRACT/) · [`L2_DOCTRINE/`](docs/architecture/L2_DOCTRINE/) · [`INSTALL.md`](docs/INSTALL.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [Issues](https://github.com/Battam1111/Myco/issues)

贡献：`pip install -e ".[dev]"`；架构性改动落地为 [`docs/primordia/`](docs/primordia/) 下带日期的 craft 文档。

MIT · [`LICENSE`](LICENSE) · [PyPI](https://pypi.org/project/myco/) · [Releases](https://github.com/Battam1111/Myco/releases)
