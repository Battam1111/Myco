<div align="center">

<img src="assets/logo_dark_280.png" alt="Myco" width="200">

# Myco

**别的工具给你的 AI agent 记忆。Myco 给它代谢。**

[![PyPI](https://img.shields.io/pypi/v/myco?style=for-the-badge&color=00D4AA)](https://pypi.org/project/myco/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

[看效果](#看效果) · [快速开始](#快速开始) · [工作原理](#工作原理) · [为什么选-myco](#为什么选-myco) · [故事](#故事)

**Other Languages:** [English](README.md)

</div>

---

## 看效果

项目第三天。你的 agent 在一个 wiki 页里引用了"v2 endpoint"，但 `_canon.yaml` 里写的是 v3。部署文档还提着 v1。三个地方，三个不同的事实。没人发现。

```
$ myco lint

  L0 Canon self-check          PASS
  L1 Reference integrity       PASS
  L2 Numeric consistency       ⚠ 1 issue
  L3 Stale pattern scan        PASS
  L4 Orphan detection          ⚠ 1 issue
  L5 Log coverage              PASS
  L6 Date consistency          PASS
  L7 Wiki format               PASS
  L8 Adapter schema            PASS

  [HIGH] L2 | wiki/api_design.md
         "v2 endpoint" ≠ _canon.yaml current_api_version = "v3"

  [MEDIUM] L4 | wiki/deployment.md
           not indexed in MYCO.md
```

两个问题被捕获。这个矛盾本来会在接下来五个会话中悄悄累积。

---

## 快速开始

```bash
pip install myco
```

**已有 `CLAUDE.md`？**

```bash
myco migrate ./your-project --entry-point CLAUDE.md   # 非破坏性
myco lint --project-dir ./your-project                 # 建立基线
```

**从头开始？**

```bash
myco init my-project --level 2
```

**从其他工具迁移？**

```bash
myco import --from hermes ~/.hermes/skills/
myco import --from openclaw ./MEMORY.md
```

详见 [`adapters/`](adapters/)。

---

## 工作原理

Myco 在现有项目文件旁添加四个层级：

```
your-project/
├── MYCO.md            ← agent 每次会话都读（热区索引）
├── _canon.yaml        ← 唯一真相源（lint 的校验基准）
├── wiki/              ← 结构化知识页（lint 验证）
├── docs/              ← 流程、辩论记录、进化历史
├── log.md             ← 仅追加的项目时间线
└── src/myco/          ← CLI + lint 引擎（9 项检查，L0–L8）
```

`myco lint` 跨所有层级运行 9 项一致性检查——捕获矛盾、孤儿文件、过时引用和版本漂移。

四齿轮进化引擎让知识保持活力：

| 齿轮 | 何时 | 做什么 |
|------|------|--------|
| 1 | 每次会话 | 感知摩擦——记录失败和意外行为 |
| 2 | 会话结束 | 反思——知识系统本身该改进什么？ |
| 3 | 里程碑 | 回顾——挑战结构性假设 |
| 4 | 项目结束 | 蒸馏——提取普适模式给未来项目 |

---

## 为什么选 Myco

大多数 AI 工具在 **L-exec**（执行更快）或 **L-skill**（积累技能）层运作。Myco 在 **L-struct** 和 **L-meta** 层运作——进化知识结构本身：

| 层级 | 做什么 | 谁在做 |
|------|--------|--------|
| L-exec | 执行更快 | 所有 agent |
| L-skill | 积累技能 | Hermes、OpenClaw、CLAUDE.md |
| **L-struct** | **进化知识结构** | **Myco（Gear 3）** |
| **L-meta** | **进化进化规则** | **Myco（Gear 4）** |

[Mem0 的 2026 报告](https://mem0.ai/blog/state-of-ai-agent-memory-2026)将"记忆过时检测"列为未解决挑战。这正是 `myco lint` 做的事。Mem0 做检索，Myco 做验证和进化，互补。

---

## 兼容工具

| 工具 | 集成方式 |
|------|---------|
| **Claude Code** | `myco migrate --entry-point CLAUDE.md` |
| **Cursor** | 文件感知共存，无需迁移 |
| **GPT / OpenAI** | 系统提示注入或 ChatGPT Projects |
| **Hermes Agent** | `myco import --from hermes` |
| **OpenClaw** | `myco import --from openclaw` |
| **MemPalace** | L0 检索后端（适配器规范已提供） |

---

## 验证

基于一个真实的 8 天、80+ 文件研究项目，走完了完整四齿轮周期：

<div align="center">

| 80+ 文件 | 10 个 wiki 页 | 15+ 轮结构化辩论 | 9/9 lint 检查 |
|:--------:|:------------:|:----------------:|:-------------:|

</div>

Gear 4 蒸馏出的模式现在就在 Myco 代码库中。详见 [`examples/ascc/`](examples/ascc/)。

---

## 故事

第一天，我有一个 949 行的 `CLAUDE.md`，什么都在里面。第三天，同一个指标出现在三个地方，三个不同的值，agent 自信地全用了。那一刻我写了第一版 `myco lint`。

到第五天，有了 canonical values、wiki 页和 8 项 lint 检查。第七天的里程碑回顾发现 40% 的摩擦来自"改了内容忘了更新索引"——系统进化了自己的规则。

第八天我意识到这个模式不是项目特定的。命名为 Myco，来自 mycelium（菌丝体）——地下网络，在生物体之间代谢养分，维持整个生态系统。

---

## 贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md)。最有价值的贡献是实战报告和 [`adapters/`](adapters/) YAML。

## 许可证

MIT
