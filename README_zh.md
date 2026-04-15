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

> **v0.4.0 —— 从零重写（Greenfield Rewrite）。** 每一个 verb、每一个维度、每一层契约表面都从 L0 重新写过。从 v0.3.x 升级请看 [`CHANGELOG.md`](CHANGELOG.md) 和 [`scripts/migrate_ascc_substrate.py`](scripts/migrate_ascc_substrate.py)。

## 快速上手

```bash
pip install 'myco[mcp]'          # 包本体 + MCP SDK

cd /path/to/your/project
myco genesis . --substrate-id my-project
```

**Claude Code / Cowork**：装官方 plugin：

```
/plugin marketplace add Battam1111/Myco
/plugin install myco@myco
```

Plugin 一步到位把 MCP 服务器、SessionStart / PreCompact 钩子（boot 仪式 + session-end 仪式）、以及两个 slash skill（`/myco:hunger`、`/myco:session-end`）全部接好。零手工仪式。不想走 plugin 系统也行——把本仓库的 `.claude/` 拷进你的项目，同样的钩子，同样的行为。

**任何 MCP host**（Cursor、Continue、Zed ⋯）或直接启动：

```bash
python -m myco.mcp                      # stdio（默认）
python -m myco.mcp --transport sse      # HTTP SSE
```

库方式嵌入：

```python
from myco.mcp import build_server
build_server().run()
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

## 集成

- **Claude Code / Cowork** —— `/plugin marketplace add Battam1111/Myco` 再 `/plugin install myco@myco`，或者手工拷 `.claude/`。两条路都把 SessionStart → `hunger`、PreCompact → `session-end` 接好。
- **任何 MCP host** —— `python -m myco.mcp` 走 stdio，或者 `myco.mcp:build_server` 嵌库。
- **下游 substrate** —— `myco propagate` 发布；adapter 住在 `myco.symbionts`。

## 了解更多

[`L0_VISION.md`](docs/architecture/L0_VISION.md) · [`L1_CONTRACT/`](docs/architecture/L1_CONTRACT/) · [`L2_DOCTRINE/`](docs/architecture/L2_DOCTRINE/) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [Issues](https://github.com/Battam1111/Myco/issues)

贡献：`pip install -e ".[dev]"`；架构性改动落地为 [`docs/primordia/`](docs/primordia/) 下带日期的 craft 文档。

MIT · [`LICENSE`](LICENSE) · [PyPI](https://pypi.org/project/myco/) · [Releases](https://github.com/Battam1111/Myco/releases)
