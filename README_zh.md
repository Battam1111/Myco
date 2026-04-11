<div align="center">

<img src="assets/logo_dark_280.png" alt="Myco" width="200">

# Myco

**Myco 是为 AI Agent 设计的自主认知基质（Autonomous Cognitive Substrate）。**
*你的 Agent 是 CPU。Myco 是其他所有——而且这个操作系统会自己升级自己。*

[![PyPI](https://img.shields.io/pypi/v/myco?style=for-the-badge&color=00D4AA)](https://pypi.org/project/myco/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

[Myco 是什么](#myco-是什么) · [看效果](#看效果) · [快速开始](#快速开始) · [工作原理](#工作原理) · [为什么选-myco](#为什么选-myco) · [故事](#故事)

**Other Languages:** [English](README.md)

</div>

---

## Myco 是什么

**Myco 是一个基质，不是一个工具。** 你的 Agent 运行在 Myco 上，就像进程运行在操作系统上——不同之处在于，这个操作系统会自己升级自己。

- **基质而非库。** Agent = CPU（纯算力，零持久性）。Myco = 内存、文件系统、操作系统、外设——*而且操作系统可以在 CPU 执行它的同时重写自己*。架构上分为项目无关的**内核**（本仓库）与项目**实例**（你的项目目录），就像操作系统与应用程序的关系一样。
- **非参数进化。** 权重永远不会被动到。所有学习都发生在基质里：markdown 文件、YAML canon、目录结构、lint 规则、进化引擎本身。你的 Agent 随时间变强，不是因为被重新训练，而是因为它脚下的地面消化了世界，在它底下生长起来。
- **知识代谢。** 活的系统代谢，死的系统不代谢。Myco 被设计成主动"吞噬"外部信息（代码、文档、论文、教训）并将其消化为结构化知识。`myco lint` 是免疫系统。完整的外部摄取——代谢入口（Metabolic Inlet）——是一项已声明的原语（primitive），最早在 v2.0 实现。详见 [开放问题](#开放问题)。
- **永恒进化。** 停滞即死亡。这是唯一不可违反的法则，因为一个停止代谢的基质只是一个缓存。

> 别的工具给你的 agent 记忆。Myco 给它代谢。

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

两个问题被抓住。那个矛盾本来会在接下来五个会话里默默地扩大。这就是基质的免疫系统在工作。

---

## 快速开始

```bash
pip install myco
```

**已经有 `CLAUDE.md`？**

```bash
myco migrate ./your-project --entry-point CLAUDE.md   # 非破坏性
myco lint --project-dir ./your-project                 # 建立基线
```

**全新项目？**

```bash
myco init my-project --level 2
```

**从其他工具迁移？**

```bash
myco import --from hermes ~/.hermes/skills/
myco import --from openclaw ./MEMORY.md
```

Cursor、GPT 等集成请看 [`docs/adapters/`](docs/adapters/)。

**MCP 集成**（Agent 自动发现 Myco 工具）：

```bash
pip install 'myco[mcp]'
```

仓库里已经带了 `.mcp.json`。安装后，你的 agent 会自动获得 **9 个工具**——无需手动提示：

- **反射层** · `myco_lint` · `myco_status` · `myco_search` · `myco_log` · `myco_reflect`
- **消化系统** · `myco_eat` · `myco_digest` · `myco_view` · `myco_hunger`

> **前提假设**：Myco 假设你使用的是支持 MCP 的 agent（Claude Code、Cursor、Claude Desktop 等）。纯人手通过 `myco` CLI 也能用，但会失去反射层——那一层的核心价值是 agent 在对话流中自动捕获知识，不需要你开口。

---

## 工作原理

Myco 在你现有的项目文件旁边增加四层：

```
your-project/
├── MYCO.md            ← Agent 每个会话都读（hot-zone 索引）
├── _canon.yaml        ← 单一事实源（lint 的 canonical values）
├── wiki/              ← 结构化知识页（lint 校验）
├── docs/              ← 流程、辩论记录、进化历史
├── log.md             ← 只追加的项目时间线
└── src/myco/          ← CLI + lint 引擎（9 项检查，L0–L8）
```

`myco lint` 在所有层之间运行 9 项一致性检查。它是**免疫系统**——抓矛盾、孤立文件、过时引用、版本漂移，在它们复合之前。

### 三条不可变宪法

Myco 里的一切都可以进化——知识组织方式、压缩策略、甚至进化引擎本身。只有这三条例外：

1. **入口可达** — 系统必须有一个任何 Agent 都能定位并自解释的入口。
2. **透明可理解** — 系统必须始终对人类保持可审查、可理解。*为什么这条是承重墙：人类是 Myco 的选择压力（详见下文人机协作模型）。如果透明性丧失，选择压力就丧失；一个没有选择压力的自我优化基质会走向癌变——它还在改变，但已经不再服务于真实目标。*
3. **永恒进化** — 停滞即死亡。一个停止代谢的基质会退化成静态知识库。

### 四档齿轮 + 代谢入口

Myco 的进化引擎有两面。四档齿轮是**自主神经系统**——内部稳态，今天已全部实现。代谢入口是**消化系统**——对外摄取，现在作为原语声明，最早 v2.0 实现。

| 齿轮 | 触发时机 | 做什么 | 状态 |
|------|---------|--------|------|
| 1 | 每个会话 | 感知摩擦——记录失败和意外行为 | v1.0 |
| 2 | 会话结束 | 反思——知识系统该改进什么？ | v1.0 |
| 3 | 里程碑 | 回顾——挑战结构性假设 | v1.0 |
| 4 | 项目结束 | 蒸馏——为未来项目提取通用模式 | v1.0 |
| **代谢入口** | **摩擦信号触发 + 周期巡逻** | **发现 → 评估 → 萃取 → 整合 → 压缩 → 验证 外部知识（GitHub、arXiv、社区文档）** | **原语已声明；最早 v2.0** |

1–4 档朝内。入口朝外。一个没有消化系统的基质只是缓存；这就是为什么代谢入口现在就必须被声明，哪怕实现在后面。

代谢入口一旦实现，会运行一条**七步代谢管道**：

```
发现 → 评估 → 萃取 → 整合 → 压缩 → 验证 → 淘汰
```

第七步（`淘汰` / excrete——主动清除过时或被取代的知识）是大多数系统忘记的一步。生物代谢是*摄入 + 转化 + 排泄*；没有排泄你得到的只是消化，不是代谢，基质会膨胀。Myco 的第七步不可省略。

这条管道还区分**可迁移知识**（值得蒸馏进内核以备未来项目使用的模式——齿轮 4 的输出）与**项目专属知识**（仅对当前实例有效的事实）。同一条教训可能同时是两者，也可能都不是；正确分类本身就是齿轮 4 的工作。

### 压缩原则

Myco 的运行假设：

> **存储无限。注意力有限。**

你永远可以多加一块硬盘，但 Agent 的上下文窗口不会按需增长。所以 Myco **永不遗忘**——没有信息会从冷存储里被删除——但它**主动压缩**那些流入 Agent 注意力的内容。压缩决策（什么留热、什么入冷、什么被重新摘要、什么按需重展）不是管道工作。它是**基质的首要认知行为**。

来自 2026-04-08 愿景辩论的三条压缩判据：

- **使用频率** — 低阅读的 wiki 页压缩或转冷
- **时效** — 过期的时间敏感知识淘汰
- **排他性** — "所有 Agent 都已经知道的常识"（比如 Python 基础语法）浪费基质空间，不应该存在这里

压缩还是 **Agent-adaptive** 的：32K 上下文的客户端需要比 200K 的更激进的压缩。同一个 Myco 实例必须为每种 Agent 以不同方式呈现自己。而且压缩策略本身也是齿轮 3 / 4 合法的进化目标——当规则停止工作，规则就改变。

### 四层自我模型

Myco 维护一个关于*自己*的模型。不是锦上添花——而是一个基质知道自己含有什么、缺什么、什么在腐烂、什么被忽略的*唯一*方式。四层，自动化难度递增：

| 层 | 追踪什么 | 自动化 | 今天 |
|----|---------|-------|------|
| **A — 库存** | 我有什么？数量、分布、更新时间。 | 容易 | ✅ `myco status` |
| **B — 缺口感知** | 我缺什么？摩擦信号 = 缺口症状。 | 中等 | ✅ friction logs → 齿轮 2 |
| **C — 退化感知** | 什么在腐烂？*事实性退化*：版本漂移、过时引用。*结构性退化*：第 3 天对的架构到第 30 天已经错了。 | 中等 | ✅ 仅事实性（lint L0–L8）；❌ 结构性是开放问题 |
| **D — 效能评估** | 哪些知识真的被用了？"死知识" = 一个 wiki 页存在但从未被读取。 | 最难 | ❌ 尚未——Hermes 式的使用追踪是 v1.2+ 目标 |

今天 Myco 实现了 A、B 和部分 C。D 是一个命名的缺口。这些不是挥手带过的概念，是后续版本周期的具体架构目标。

### 人机协作模型

**系统做变异（mutation），人类做选择（selection）。**

你不设计 Myco 的进化——你提供适应度信号。Myco（通过执行它的 Agent）提出变化：一条新的 lint 规则、一次 wiki 版块重构、一段被压缩的操作叙事。你说"留"或"丢"。就像自然选择从不设计物种，只淘汰不适应的。

这是大多数第一次接触 Myco 的人会忽略的反转：**Myco 是为 Agent 而不是为人类设计的**。文档看起来密集，是因为它们在为 Agent 的 token 效率和上下文窗口加载量优化，不是为人类的阅读愉悦。你不是 Myco 的主要用户——你是选择者、园丁、提供生存压力让 Myco 保持对齐的那一方。

这个模型也是第 2 条宪法的由来。如果 Myco 进化到你无法评估它的变化的复杂度，你就失去了提供选择压力的能力，基质就会癌变。透明性不可谈判，因为它是"有意义的选择"的前提条件。

---

## 为什么选 Myco

Agent 会执行，也会记忆，但它们无法注意到自己知识中的矛盾、质疑自己的假设是否仍然成立、或者把外部世界消化成可复用的结构。Myco 是 Agent *运行在其上的基质*——不是它们*使用的*一个插件。

大多数 AI 工具在 **L-exec**（执行得更快）或 **L-skill**（积累技能）层面工作。Myco 在 **L-struct** 和 **L-meta** 层面工作——进化知识结构本身，并进化那些进化结构的规则：

| 层级 | 做什么 | 谁 |
|------|-------|----|
| L-exec | 执行得更快 | 所有 Agent |
| L-skill | 积累技能 | Hermes、OpenClaw、CLAUDE.md |
| **L-struct** | **进化知识结构** | **Myco（齿轮 3）** |
| **L-meta** | **进化进化的规则** | **Myco（齿轮 4）** |

### Myco 与邻近系统的区别

| | Myco | Hermes / OpenClaw | Second Brain | Hyperagents (Meta) | Mem0 | 企业 KMS |
|--|------|-------------------|--------------|-------------------|------|---------|
| **主体** | Agent 为中心 | Agent | 人 | Agent | Agent | 人 |
| **进化什么** | 基质本身 | 技能库 | 无 | Agent 权重/prompts | 记忆存储 | 文档 |
| **非参数** | ✅ 始终 | ✅ | ✅ | ❌ 改权重 | ✅ | ✅ |
| **元进化** | ✅ 核心（齿轮 4） | ❌ | ❌ | ✅ 部分 | ❌ | ❌ |
| **知识代谢** | ✅ 已声明（v2.0 入口） | ❌ | ❌ | ❌ | ❌ | 人工 |
| **自我模型** | ✅（lint + _canon.yaml） | ❌ | ❌ | 部分 | ❌ | ❌ |
| **Agent-adaptive** | ✅ | ❌ | N/A | ❌ | ✅ | N/A |

从这张表里能拉出两句干净的定位句：
- **Hyperagents 进化 CPU。Myco 进化操作系统。** 两者相互非参数；Myco 的主张是：基质层的进化结构性地更便宜、更透明，因为基质是 markdown 和目录结构——LLM 天然擅长操作的介质。
- [Mem0 的 2026 报告](https://mem0.ai/blog/state-of-ai-agent-memory-2026) 把"memory staleness detection"列为未解问题。这正是 `myco lint` 在做的事。**Mem0 做检索。Myco 做校验、代谢和自我改写规则。** 两者互补，不竞争。

---

## 开放问题

Myco 还早。以下四个盲点在 2026-04-08 的愿景辩论中被命名，至今未解。它们是杠杆最大的贡献点：

1. **冷启动。** Myco 如何在一个全新的、没有历史、没有 canon、没有摩擦记录的项目上引导自己？当前答案：手工的 `myco init` 模板。期望答案：基质从过往项目的蒸馏中学会自己的引导流程。
2. **触发信号。** 什么触发齿轮 2？什么触发代谢入口？摩擦计数是一个代理信号，正确的信号是开放研究问题。
3. **对齐。** 如果 Myco 进化出人类无法评估的规则（深入 L-meta），如何保持它与用户意图的对齐？透明是必要但不充分——我们需要*规模化的可阅读的透明*。
4. **压缩工程。** 存储无限，但注意力不是。什么时候丢什么，而不损失承重的 tacit knowledge？三条候选判据（频率 / 时效 / 排他性）是起点，不是解法。目前没有通用答案。
5. **结构性退化检测。** `myco lint` 能抓*事实性*退化（版本漂移、过时引用）。它抓不住*结构性*退化——当第 3 天对的四层架构到第 30 天已经错了。没有任何检测器能告诉你"你的知识组织方式已经不再匹配你项目的阶段"。这可能是整个设计空间里最难的问题。

如果你想贡献一些高影响力的东西，从这五个里挑一个。

---

## 适配

| 工具 | 集成方式 |
|------|---------|
| **Claude Code** | `myco migrate --entry-point CLAUDE.md` |
| **Cursor** | 文件感知共存——不需要迁移 |
| **GPT / OpenAI** | System prompt 注入或 ChatGPT Projects |
| **Hermes Agent** | `myco import --from hermes` |
| **OpenClaw** | `myco import --from openclaw` |
| **MemPalace** | L0 检索后端（适配规范可用） |

---

## 验证

建立在一个真实的 8 天、80+ 文件的研究项目之上，完整跑过了四档齿轮的循环：

<div align="center">

| 80+ 文件 | 10 个 wiki 页 | 15+ 次结构化辩论 | 9/9 lint 检查 |
|:-------:|:-----------:|:-----------:|:-----------:|

</div>

但更深的主张是：**那个 8 天的项目是 Myco 的一次不自觉的原型运行**。我不是在演示基质。我是在*手动运行*它——人类驱动的元进化、手工触发 lint、口述摩擦日志。它有效。Myco 是一个已经自我证明的模式的形式化；v1.0 → v2.0 的路线不是"发明新东西"，而是"让原本手动有效的东西自动有效"。通过齿轮 4 蒸馏出的模式现在已经在 Myco 代码库里。见 [`examples/ascc/`](examples/ascc/)。

Myco 还站在 50 年认识论、控制论与组织学习的肩膀上：**Karpathy LLM Wiki**（结构化知识编译）+ **Polanyi Tacit Knowledge**（操作经验的 proximal / distal 结构）+ **Argyris Double-Loop Learning**（单环修正行动，双环修正规则——正是 L-struct / L-meta 的区分）+ **Toyota PDCA**（Plan / Do / Check / Act 是四档齿轮的基础循环）+ **Voyager Skill Library**（通过落地执行进行迭代技能积累）。详见 [`docs/theory.md`](docs/theory.md)。

---

## 故事

第一天，我有一份 949 行的 `CLAUDE.md`。所有东西都在一个文件里。到第三天，同一个指标在三个地方有三个不同的值，我的 agent 自信地同时使用了三个。但更深的问题是：每一个新会话，我的 agent 都会从头重写同一个部署脚本——不是因为它忘了 SSH 配置规则（那些都文档化了），而是因为那些*tacit knowledge*——哪些 flag 真的要紧、什么顺序能跑、什么会悄悄失败——所有这些，都在会话边界处蒸发了。智能不是被丢失了，是在被**丢弃**，一次又一次。

那是我写下第一个 `myco lint` 的时候——不只是为了抓矛盾，而是为了给 agent 一个它根本上缺乏的东西：一块基质。一个观察着 agent "知道的" 是否还真实、标记假设何时开始腐烂、并在旧规则停止工作时进化自己的规则的地面。不是 agent 拎起来的一个工具。是 agent 站在上面的一块地板。

到第七天，一次里程碑回顾发现 40% 的摩擦来自"内容改了，忘了更新索引"——于是系统进化出了自己的规则。第八天，我意识到这个模式不是项目特定的。我把它命名为 **Myco**，来自 *mycelium*（菌丝网络）——森林地下那张看不见的活网。菌丝不只是连接树木的管道：它分泌酶将落叶分解为养分（代谢），记住有效的生长路径并据此调整策略（元进化），根据需求将资源从丰裕区域调往匮乏区域（智能压缩），并与不同树种的根系都能形成共生（Agent-adaptive 通用性）。Agent 是地面上的树，Myco 是地下让整片森林成活的网络。

---

## 贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md)。影响力最大的贡献是（1）针对[开放问题](#开放问题)的战报，（2）你已经在用的工具的 [`docs/adapters/`](docs/adapters/) YAML，（3）代谢入口原语的设计草图。

## License

MIT
