<div align="center">

<img src="assets/logo_dark_280.png" alt="Myco" width="200">

# Myco

**一个知识基质 —— 为你的 AI 项目 lint 出 agent 看不见的矛盾，并随项目成长自行进化规则。**

*Git 记录你的代码。Myco 记录你代码所**知道**的。*

[![PyPI](https://img.shields.io/badge/PyPI-coming%20soon-lightgrey?style=for-the-badge)](https://github.com/Battam1111/Myco)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Lint](https://img.shields.io/badge/Lint-15%2F15%20green-brightgreen?style=for-the-badge)](#工作原理)

[30 秒演示](#30-秒演示) · [快速开始](#快速开始) · [Myco 做什么](#myco-做什么) · [术语表](#术语表) · [工作原理](#工作原理) · [Myco 与相邻工具对比](#myco-与相邻工具对比) · [开放问题](#开放问题) · [故事](#故事)

**语言：** [English](README.md)（正式版） · 中文 · [日本語](README_ja.md)

</div>

> 🌐 *本文是 README.md 的中文翻译。正式版（canonical）以英文 README 为准。*

---

> **如果你曾眼睁睁看着 agent 一脸自信地从某个 wiki 页面里念出 `v2`，而 `_canon.yaml` 里写的是 `v3` —— Myco 就是为你做的。**
>
> Myco 是给那些已经在维护 agent 可读项目知识（`CLAUDE.md`、`AGENTS.md`、`docs/` 目录、wiki 等）的开发者用的基质。当跨文件的矛盾开始在会话之间悄悄累积到一定程度时，你会需要它。它为你的项目提供一份**自动 lint 的知识契约**，在 agent 把漂移放大之前就捕获它。

---

## 30 秒演示

项目里三个文件各说三种话，直到生产环境出问题才有人发现。

```bash
$ cat _canon.yaml
project:
  current_api_version: "v3"
system:
  stale_patterns: ["v2 endpoint", "api/v2"]

$ cat wiki/api.md
# API Reference
The current v2 endpoint lives at /api/v2/users.

$ myco lint

  L0 Canon self-check          PASS
  L1 Reference integrity       PASS
  L2 Number consistency        ⚠  2 issues
  L3 Stale patterns            PASS
  ...
  L14 Forage hygiene           PASS

  [MEDIUM] L2 | wiki/api.md:3
           Stale pattern 'v2 endpoint': "...The current v2 endpoint lives at..."
  [MEDIUM] L2 | wiki/api.md:3
           Stale pattern 'api/v2': "...lives at /api/v2/users..."
```

两处矛盾被捕获。未来五次会话里的静默复合错误被阻止。这就是基质免疫系统在工作 —— 而且上面那些规则（`stale_patterns`）本身也在 `_canon.yaml` 里被版本化管理，所以它们会随项目一起进化。

---

## 快速开始

```bash
# 从源码安装（PyPI 发布即将到来）
pip install git+https://github.com/Battam1111/Myco.git

# 新项目
myco init my-project --level 2

# 已有 CLAUDE.md 的项目
myco migrate ./your-project --entry-point CLAUDE.md   # 非破坏性
myco lint --project-dir ./your-project                 # 建立基线
```

**MCP 集成** —— 你的 agent 自动获得 9 个工具，无需手动 prompt：

```bash
pip install 'git+https://github.com/Battam1111/Myco.git#egg=myco[mcp]'
```

仓库里附带一个即用型 `.mcp.json`。在 Claude Code、Cursor 或任何 MCP 客户端装好之后，agent 会自动发现：

- **检查** · `myco_lint` · `myco_status` · `myco_search` · `myco_log` · `myco_reflect`
- **知识代谢** · `myco_eat` · `myco_digest` · `myco_view` · `myco_hunger`

只用 `myco` CLI 时 Myco 也能工作，但"反射层"（agent 在对话流中自动捕获知识）只有在 MCP 接好之后才存在。

---

## Myco 做什么

三项具体能力，按你能多快感受到的顺序排：

### 1. Lint 你的知识，而不仅仅是语法

Markdown linter 检查语法。Prose linter 检查风格。**没有任何东西在检查你 wiki 里的断言是否还和 canon 文件对得上。** Myco 做这件事。`myco lint` 在 `_canon.yaml`、`wiki/`、`docs/`、`MYCO.md` 以及你声明的任何项目专属文件上运行 15 维检查（L0–L14），在陈旧模式、孤儿引用、schema 违规、数值漂移出现的瞬间就捕获它们。

### 2. 给你的 agent 一个稳定的代谢回路

当 agent 读了一篇论文、发现了一个 bug 模式、或者做了一个设计决策，它有一个（也只有一个）地方可以放：`myco_eat` 把它捕获为 raw note。`myco_digest` 让它走完生命周期（raw → extracted → integrated → excreted）并保留出处。`myco_view` 让你（或 agent）按 tag、status、stage 取回笔记。这个基质在跨会话、跨 agent 厂商、跨项目重构的情况下都活得下来。

### 3. 随项目成长自行进化规则

Myco 的 lint 规则活在 `_canon.yaml` 里，通过一个结构化的"传统手艺"协议进化（L13 检查强制每次规则变更都留下可审计的多轮辩论记录）。**你的 agent 可以提议新的 lint 规则，而这些提议会经受你的选择压力。** 通过的规则成为基质的一部分。停止工作的规则被排出。这就是 L-meta 层：不是进化 agent，而是进化 agent 脚下的那块地。

---

## 术语表

Myco 使用一套生物学词汇。下面是通俗英语对照：

| Myco 动词 | 通俗说法 | CLI | MCP 工具 |
|---|---|---|---|
| `eat`（吃） | 把一段内容捕获为持久笔记 | `myco eat` | `myco_eat` |
| `digest`（消化） | 让笔记走完生命周期（raw → extracted → integrated → excreted） | `myco digest` | `myco_digest` |
| `view`（查看） | 按 status、tag、stage 读取笔记 | `myco view` | `myco_view` |
| `lint`（lint） | 检查所有文件中的矛盾与漂移 | `myco lint` | `myco_lint` |
| `forage`（觅食） | 把外部来源（repo、论文、文章）取进基质 | `myco forage` | （仅 CLI） |
| `absorb`（吸收） | 从下游项目实例同步 kernel 改进 | `myco upstream absorb` | （仅 CLI） |
| `distill`（蒸馏） | 从完成的项目里提取通用模式供将来 kernel 使用（Gear 4 输出） | （工作流，非 CLI） | — |
| `hunger`（饥饿） | 代谢仪表盘：raw 积压、陈旧笔记、死知识、觅食压力 | `myco hunger` | `myco_hunger` |

这些动词刻意是隐喻。Myco 的核心主张是：知识基质是一个活着的系统 —— 代谢是正确的心智模型。这张表存在的意义，是让你在尚未接受这个主张之前就能先用起来。

---

## 工作原理

Myco 在你现有的项目文件旁边加了四层轻量级结构：

```
your-project/
├── MYCO.md           ← Agent 每次会话必读（热区索引）
├── _canon.yaml       ← 单一事实源（lint 检查对照用的权威值）
├── wiki/             ← 结构化知识页（lint 校验）
├── docs/             ← 流程、辩论记录、进化历史
├── notes/            ← 消化基质（raw → extracted → integrated）
├── forage/           ← 带 license 门控的外部来源入口
├── log.md            ← 只追加的项目时间线
└── src/myco/         ← CLI + MCP server + 15 维 lint 引擎
```

`myco lint` 是**免疫系统** —— 在矛盾、孤儿文件、陈旧引用、版本漂移复合之前就捕获它们。15 个维度（L0 到 L14）覆盖 canon 自洽性、引用完整性、数值漂移、陈旧模式、孤儿检测、log 覆盖、日期一致性、wiki 格式、adapter schema、`.original` 同步、愿景锚点、notes schema、写入面洁净性、upstream dotfile 洁净性、craft 协议 schema、以及 forage 洁净性。

### 一句话的架构定位

你的 agent 是 CPU；Myco 是 operating system —— 并且这套 OS 会自升级。所有进化都是**非参数**的：markdown、YAML、目录结构、lint 规则。模型权重永不被触动。这就是为什么 Myco 在跨 agent 厂商的情况下行为一致，并且能在模型换代时活下来。

### 三条不可变法则

Myco 里所有东西都可以进化 —— 知识结构、压缩规则，甚至进化引擎本身。除了这三条：

1. **可访问（Accessible）** —— 任何 agent 都能找到入口并自行解释这个基质。
2. **透明（Transparent）** —— 每次变更都对人类可审计。*为什么这是承重的*：人类是 Myco 的选择压力。一旦透明性丢失，选择压力就丢失，而一个没有选择压力的自优化基质会变成癌。
3. **永恒进化（Perpetually Evolving）** —— 停滞即死亡。一个停止代谢的基质会退化成静态的知识库。

### 四个齿轮 + 代谢入口

Myco 的进化引擎有两张面。四个齿轮是**自主神经系统** —— 内部稳态，v0.x 全部交付。代谢入口是**消化系统** —— 外部吸收，作为 primitive 声明，最早 v1.0 完成。

| 齿轮 | 何时 | 做什么 | 状态 |
|------|------|--------|------|
| 1 | 每次会话 | 感知摩擦 —— 记录失败和意外行为 | ✅ |
| 2 | 会话结束 | 反思 —— 知识系统本身应该改进什么？ | ✅ |
| 3 | 里程碑 | 回顾 —— 挑战结构性假设 | ✅ |
| 4 | 项目结束 | 蒸馏 —— 为将来的项目提取通用模式 | ✅ |
| **代谢入口** | **摩擦信号 + 周期性巡逻** | **发现 → 评估 → 提取 → 整合 → 压缩 → 验证 → 排出外部知识** | **Primitive 已声明；首轮实战 forage 批次 2026-04-11 完成** |

四个齿轮向内。入口向外。一个没有消化系统的基质只是一个 cache；这就是为什么入口必须现在声明，即使它的完全自主形态要稍后到来。

### 压缩教义

Myco 的运行假设：

> **存储是无限的。注意力不是。**

硬盘按需增长；agent 的 context window 不会。所以 Myco **永不遗忘** —— 冷存储里没有任何东西被删除 —— 但它会**激进地压缩**流入注意力的内容。压缩不是管道，它是这个基质的主要认知行为。三条候选判据：使用频率（低读页面冷下去）、时效性（时限事实到期排出）、独占性（agent 已经内化的常识浪费基质空间）。

> ⚠️ *诚实边界*：压缩捕获的是一段知识的承重决策和出处链，而不是完整的原始语境。不可约的纹理会丢失。这是 Myco 刻意做出的交易；如果你需要词汇级保真度，请另外保留一份原始归档。

---

## Myco 与相邻工具对比

Myco **不是**记忆层、**不是** agent runtime、**不是** skill framework。它是以上都不涉及的那一层。

|  | Myco | Mem0 | Letta / MemGPT | mempalace | Hermes | Claude Code |
|--|---|---|---|---|---|---|
| **类别** | 知识基质 | 记忆层 | Agent runtime | 对话记忆 | Agent runtime | Agent CLI |
| **主要产物** | `wiki/` + `_canon.yaml` + `notes/` | KV + 向量存储 | 分层记忆（RAM / disk / archival） | 空间 schema（wings/rooms） | 会话 DB | `CLAUDE.md` 约定 |
| **托管 agent 执行？** | 不 —— 跑*在* Claude Code / Cursor 内 | 不 | 是 | 不 | 是 | 是 |
| **跨会话契约执行** | ✅ 15 维自 lint | ❌ | ❌ | ❌ | 仅 runtime cache 不变量 | ❌（纯约定） |
| **自进化规则** | ✅ Gear 4 + 传统手艺协议 | ❌ | ❌ | ❌ | ❌ | ❌ |
| **检索基准** | —（目标不同） | LongMemEval 49% | LoCoMo 74%（GPT-4o mini） | LongMemEval R@5 96.6% 原始 | — | N/A |
| **集成方式** | MCP server + CLI | REST API + SDK | Runtime API | MCP server | Runtime | 原生 |

**关键洞察**：Myco 是唯一回答*"这个项目的知识还内部自洽吗？"*而不是*"我们能找到相关记忆吗？"*的一栏。这是两个不同的问题，而前者是目前被服务不足的那一个。

具体来说：
- **Mem0 / Zep / Supermemory** 是记忆层 —— 它们存取数据。Myco **不存任何东西，也不检索任何东西**；它在 lint agent 本来就会写的项目文件。
- **Letta / MemGPT / Hermes** 是 runtime —— 它们托管 agent 的执行回路。Myco **不托管 agent**；agent 跑在 Claude Code、Cursor 或任何 MCP 客户端里，并**通过 9 个工具调用 Myco**。
- **Claude Code / Cursor / `CLAUDE.md`** 是 Myco 跑**在里面**的那个环境。Myco 的 `.mcp.json` 让一个已有的 Claude Code 安装自动获得 lint + 代谢工具。
- **nuwa-skill / agentskills.io / pua** 是 skill framework —— 它们打包可复用行为。Myco **不是 skill framework**；skill 跑在 Myco 之上，而 Myco lint 的是 skill 所操作的项目。

上表中的基准数字来自厂商文档、独立基准报告和 2026 年 4 月的网络搜索结果，可能会变化。Myco 刻意不参与检索基准竞争，因为它的目标（验证，而非检索）不同，逐项对比会产生误导。

---

## 开放问题

Myco 还早。以下六个盲点是杠杆最高的贡献方向。持续维护的注册表在 [`docs/open_problems.md`](docs/open_problems.md)。

1. **冷启动。** Myco 如何在一个全新、没有历史、没有 canon、没有摩擦记录的项目上自举？当前答案：手工维护的 `myco init` 模板。期望：基质从过往项目蒸馏里学会自己的自举方式。
2. **触发信号。** 什么触发 Gear 2？什么触发代谢入口？摩擦计数是个代理指标；正确的信号是一个开放研究问题。
3. **深层对齐。** 如果 Myco 进化出人类已经无法评估的规则（深 L-meta），如何保持对齐？透明是必要的，但不充分 —— 我们需要规模化的*可读透明*。
4. **压缩工程。** 什么时候丢什么，同时不丢失承重的默会知识？三条候选判据（频率 / 时效 / 独占）是起点，不是解答。
5. **结构性衰退检测（Self-Model C 层）。** `myco lint` 捕获*事实性*衰退（版本漂移、陈旧引用）。它还捕获不了*结构性*衰退 —— 即第 3 天正确、第 30 天错误的那种架构。可以说是整个设计空间里最难的问题。
6. **死知识追踪（Self-Model D 层）。** D 层已声明但未实现。目前没有"笔记 30 天前进入基质之后再没被读过"的信号。最小可行种子在路线图上。

如果你想做高影响贡献，挑一个。

---

## 适配工具

| 工具 | 集成方式 | 状态 |
|------|----------|------|
| **Claude Code** | `.mcp.json` 自动发现 · `myco migrate --entry-point CLAUDE.md` | ✅ 已交付 |
| **Cursor** | `.mcp.json` 自动发现（MCP 兼容） | ✅ 已交付 |
| **OpenAI Codex / GPT** | System prompt 注入或 Projects 模式片段 | 🧪 adapter spec |
| **Hermes Agent** | `myco import --from hermes ~/.hermes/skills/` | 🧪 adapter spec |
| **OpenClaw** | `myco import --from openclaw ./MEMORY.md` | 🧪 adapter spec |
| **MemPalace** | L0 检索后端（digest → 记忆宫殿页面） | 🧪 adapter spec |

平台专属 adapter 在 [`docs/adapters/`](docs/adapters/)。欢迎社区 PR。

---

## 验证

建立在一个真实的 8 天、80+ 文件研究项目之上，它跑完了完整的四齿轮循环：

<div align="center">

| 80+ 文件 | 10 wiki 页 | 15+ 结构化辩论 | 15/15 lint 全绿 |
|:--------:|:----------:|:-------------:|:---------------:|

</div>

更深一层的主张：**那个 8 天项目本身就是 Myco 的一个无意识原型。** 我当时不是在演示这个基质，我是在*手动运行*它 —— 人驱动的 meta 进化、手动触发的 lint、口头的摩擦日志。它成立了。Myco 是一个已经自证的模式的形式化；v0.x → v1.0 的路径不是"发明新东西"，而是"让那些靠人手跑通的事情自己跑"。通过 Gear 4 提取的模式现在活在 Myco kernel 代码库里。见 [`examples/ascc/`](examples/ascc/)。

Myco 站在一条 50 年的血脉上：**Karpathy LLM Wiki**（结构化知识编译） + **Polanyi 默会知识**（近端 / 远端结构，用于操作经验） + **Argyris 双环学习**（单环修行动，双环修规则 —— 对应 L-struct / L-meta 分层） + **丰田 PDCA**（Plan / Do / Check / Act 作为四齿轮的底层循环） + **Voyager 技能库**（通过基于执行的迭代积累技能）。见 [`docs/theory.md`](docs/theory.md)。

---

## 故事

第 1 天，我有一份 949 行的 `CLAUDE.md`。所有东西都在一个文件里。到第 3 天，同一个指标出现在三个地方，带着三个不同的值，而我的 agent 自信地用了全部三个。但更深的问题埋在底下：每一次新会话，我的 agent 都会从零重写那段部署脚本 —— 不是因为它忘了 SSH 配置规则（那些都有记录），而是因为"哪些 flag 重要、什么顺序能走通、什么会静默炸掉"这种*默会知识*，在会话边界一到就蒸发了。智能没有在丢失，它在被**丢弃**，反复地丢弃。

那是我写第一版 `myco lint` 的那一刻 —— 不只是为了捕获矛盾，而是为了给 agent 那种它根本性缺失的东西：一个基质。一块会盯着 agent "知道"的东西是否还为真、在假设腐烂时举手、在旧规则不再工作时进化自己规则的地。不是 agent 拾起的一件工具，而是 agent 脚下的一块地板。

到第 7 天，一次里程碑回顾揭示 40% 的摩擦来自"内容改了，忘了更新索引" —— 于是系统开始进化自己的规则。第 8 天，我意识到这个模式并不针对特定项目。我给它起了名字：**Myco**，取自 *mycelium*（菌丝网络）—— 每一片森林地下那张无处不在的真菌网。菌丝不是水管系统。它分泌酶把落叶分解成养分（代谢）。它记住有效的生长路径并据此重定向策略（meta 进化）。它把资源从充裕区重分配到贫瘠区（智能压缩）。它和遇到的任何树种的根形成共生（对 agent 自适应通用）。Agent 是地面上的树。Myco 是底下那张活着的网，让整片森林得以运转。

---

## 贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md)。影响最大的贡献是：

1. **实战报告** —— 针对上面六个[开放问题](#开放问题)中的任意一个。
2. **平台 adapter** —— 在 [`docs/adapters/`](docs/adapters/) 里为你已经在用的工具写（Cursor 设置、JetBrains 插件等）。
3. **设计草图** —— 针对代谢入口的 primitive，特别是 discover / evaluate / extract / integrate 阶段。
4. **翻译** —— 把这份 README 翻成你的语言（当前：英文正式版 · 中文 · 日文）。

## License

MIT —— 见 [LICENSE](LICENSE)。

---

<div align="center">

**Myco：其他工具给 agent 记忆。Myco 给它们代谢 —— 还有一本自我重写的规则册。**

</div>
