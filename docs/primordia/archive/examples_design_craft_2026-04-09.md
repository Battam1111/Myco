# 传统手艺：examples/ 设计——Gear 4 回路的社区闭环

> **文档状态**：[ACTIVE] | 创建：2026-04-09
> **置信度**：（逐轮更新）
> **决策范围**：examples/ 的定位、结构、第一个非 ASCC 示例、社区贡献流
> **背景**：Myco 的核心价值不是 CLI 工具的易用性，而是随着更多项目跑完 Gear 4，框架知识库变得越来越丰富——菌丝网络在树木之间传递养分。当前 examples/ 仅有一个 ASCC README 描述，缺乏让社区看到和复制 Gear 4 回路的能力。
> **为什么需要辩论**：examples/ 的设计直接决定了社区能否理解 Myco 的核心价值主张。设计成"教程文件夹"和设计成"Gear 4 蒸馏容器"，后续的一切决策都不一样。

---

## 核心问题清单（辩论前预设）

- Q1：examples/ 的定位——onboarding 教程还是 Gear 4 生命周期展示？
- Q2：每个 example 应该包含什么——README 描述还是可运行的项目快照？
- Q3：现有 ASCC example 需要怎样升级？
- Q4：第一个非 ASCC 示例选什么项目类型、如何真实而非虚构？
- Q5：社区 battle report → example 的贡献管线怎么设计？

---

## Round 1：examples/ 的定位

### 立场 A（Gear 4 生命周期展示）

examples/ 的首要目的不是教人"怎么用 myco init"——README 和 CLI help 已经做了这件事。examples/ 的首要目的是让用户看到 **Myco 生命周期的完整形态**，特别是 Gear 4 蒸馏回路：

1. 一个项目如何从 `myco init` 开始
2. wiki、docs/primordia、log.md 如何在项目进行中有机生长
3. 项目结束时 Gear 4 蒸馏产出了什么
4. 蒸馏产物如何回流进 Myco 的框架知识库（docs/）

这不是"教程"，这是"示范 Myco 的核心价值主张"。

理由：
- Myco 与其他知识工具的差异点不在"初始化更方便"，而在"知识会进化 + 跨项目传递"
- 如果 examples/ 只展示 init 的输出，用户看到的是一个"脚手架工具"，看不到"基质"
- ASCC 的 Gear 4 已经产出了 `research_paper_craft.md` 和 `reusable_system_design.md`——但从 examples/ascc/README.md 里完全看不到这个连接

### 攻击 A1：Gear 4 展示太重，新用户会被吓跑

**攻击**：一个还没用过 Myco 的人，看到 examples/ 里是一个 80+ 文件的项目快照，第一反应是"太复杂了"。教程的价值就是低门槛——让人 5 分钟内跑起来。

**防御**：这个攻击成立，但结论不是"做成教程"，而是**分层**。`myco init --level 0/1/2` 已经有 bootstrap 分层，examples/ 也应该分层：

- **L0 example**（5 分钟快速体验）：存在于 README 的 Quick Start 里，不需要 examples/ 目录
- **L1-L2 example**（完整生命周期）：这是 examples/ 真正应该承载的内容——一个项目从 L1 启动到 Gear 4 结束的全貌

所以 examples/ 不需要承担"入门引导"的职责。README + CLI 已经覆盖了。examples/ 的目标用户是**已经跑了几个会话、开始问"然后呢？"的人**。

### 攻击 A2：Gear 4 还没有被多个项目验证过，展示它是否过早？

**攻击**：目前只有 ASCC 跑完了 Gear 4。如果把 examples/ 定位为"Gear 4 展示"，但只有一个数据点，看起来像是在推销未经验证的概念。

**防御**：
- 只有一个数据点是事实。但这正是为什么需要第二个——examples/ 的设计应该**催生** Gear 4 实践，而不是等到有了足够的 Gear 4 案例再来展示。
- ASCC 的 Gear 4 产物（`research_paper_craft.md`、`reusable_system_design.md`）已经是真实的、有价值的知识单元，不是概念验证。
- 诚实原则：可以在 examples/ 里明确标注"这是 v0.x 的第一/第二个 Gear 4 实践"——坦承数量少，但展示质量高。

**Round 1 结论**：examples/ 定位为 **Gear 4 生命周期展示**，不是 onboarding 教程。置信度 **88%**。

剩余 12%：分层设计的具体边界（什么放 README、什么放 examples/）需要更多用户反馈才能确认。

---

## Round 2：每个 example 应该包含什么？

### 立场 B（"种子 → 收获"双视图）

每个 example 应该包含两个视图：

**Seed（种子）**：项目用 `myco init` 启动时的初始状态——空模板、初始 canon、空 wiki。
**Harvest（收获）**：项目经历完整生命周期后的最终状态——填充过的 MYCO.md、有机生长的 wiki 页面、docs/primordia/ 里的辩论记录、log.md 时间线、以及最关键的——**Gear 4 蒸馏产物和它在 Myco 框架中的落点**。

对比这两个状态，用户能直观看到"Myco 让我的知识系统发生了什么变化"。

### 攻击 B1：Seed 视图没有价值，它就是 `myco init` 的输出

**攻击**：用户自己跑 `myco init --level 1 my-project` 就能得到 Seed。把它放在 examples/ 里是重复。

**防御**：同意。Seed 不需要作为独立目录存在，用一个 README 段落描述"初始状态"即可。真正的价值在 Harvest。

**修正**：每个 example 的核心内容是 **Harvest 快照**（实际文件），辅以 README 叙述从 Seed 到 Harvest 的关键转折点。

### 攻击 B2：Harvest 快照放真实文件，内容可能涉密

**攻击**：ASCC 是学术研究项目，wiki 里有实验方法、数据分析、论文策略——这些可能是发表前的敏感内容。完整快照不现实。

**防御**：
- ASCC 已经有敏感性问题。解法是**脱敏快照**——保留结构和 Myco 机制的运作痕迹，替换具体领域内容。
- 但这引入了一个新风险：脱敏后的 example 会失去"真实感"，变成又一个虚构的 demo。
- **折中方案**：Harvest 快照分为"结构文件"（完整保留）和"内容文件"（脱敏或仅保留前 N 行 + 说明）。重点是让用户看到 **Myco 机制的运作痕迹**（log.md 的事件类型分布、wiki 的有机生长轨迹、canon 的 lint 通过状态），而不是项目的具体内容。

### 攻击 B3：快照是静态的，但 Myco 的价值是"活的"

**攻击**：一个目录里的快照文件只能展示最终状态，看不到"生长过程"。而 Myco 的核心卖点就是"知识在生长"。

**防御**：这是一个真实的限制。弥补方式：
1. `log.md` 本身就是时间线——即使是快照，log.md 展示了完整的生长历史
2. README 里的 "Evolution Timeline" 段落可以用文字叙述关键转折
3. git history 如果可用，是最佳的"生长过程"展示——但对 examples/ 子目录来说，git history 是 Myco repo 自身的，不是示例项目的

**额外方案**：如果某个 example 是一个真正的开源项目，可以直接链接到该项目的 GitHub repo，让用户看到真实的 git history。examples/ 里只放精简快照 + 链接。

**Round 2 结论**：每个 example 包含三部分：
1. **README.md** — 项目背景 + Evolution Timeline（从 Seed 到 Harvest 的关键转折）+ **Gear 4 产物及其在 Myco 框架中的落点**
2. **Harvest 快照** — 结构文件完整保留（MYCO.md, _canon.yaml, log.md, WORKFLOW.md），内容文件脱敏或截断
3. **反向链接** — 明确标注"本项目的 Gear 4 蒸馏产物已写入 Myco docs/xxx.md"

置信度 **82%**。

剩余 18%：脱敏方案的具体颗粒度需要实操检验；"反向链接"的展示形式（README 段落 vs 独立文件 vs Myco docs 里的反向引用）尚未确定。

---

## Round 3：现有 ASCC example 需要怎样升级？

### 当前状态

`examples/ascc/README.md` — 65 行描述性文字，列出了项目统计、目录结构、关键学习。没有任何实际的 Myco 文件，没有提到 Gear 4 蒸馏产物。

### 缺失的关键信息

1. **Gear 4 反向链接完全缺失**：ASCC 的 Gear 4 产出了 `research_paper_craft.md` 和 `reusable_system_design.md`，现在住在 `Myco/docs/` 里——但 ASCC 的 README 里一个字都没提。用户看到 examples/ascc/ 和 Myco/docs/ 是两个孤立的东西，看不到"养分传递"。

2. **Harvest 快照缺失**：用户无法看到一个"跑完 Myco 的项目长什么样"。

3. **Evolution Timeline 缺失**：Day 1-8 的 bootstrap history 是有的，但没有展示 Gear 1-4 的实际运作。

### 攻击 C1：ASCC 项目是私有的，能放多少真实文件？

**攻击**：ASCC 是 ongoing 学术研究，不能公开实验细节。升级 ASCC example 的空间有限。

**防御**：
- 结构文件（MYCO.md 的索引结构、_canon.yaml 的 schema、log.md 的事件类型统计）不涉及实验细节，可以完整展示
- wiki 页面的**页眉**（类型、日期、盲点标注）不涉及内容，可以展示——甚至这本身就是 W8 模板的最佳示范
- 辩论记录的**标题和置信度**可以展示，具体论点脱敏
- 关键：重点展示 **Myco 机制的运作痕迹**，不是项目内容

**Round 3 结论**：ASCC example 升级计划：

| 升级项 | 内容 | 优先级 |
|--------|------|--------|
| Gear 4 反向链接 | README 新增段落："本项目的 Gear 4 产物" + 链接到 Myco docs/ | HIGH |
| Evolution Timeline | 展示 Gear 1-4 的实际触发和产出 | HIGH |
| 结构文件快照 | 脱敏版 MYCO.md（索引结构）、_canon.yaml、log.md 统计 | MEDIUM |
| wiki 页眉展示 | 10 个 wiki 页面的 W8 页眉（不含正文） | LOW |

置信度 **85%**。

---

## Round 4：第一个非 ASCC 示例——什么项目类型？如何真实？

### 候选项目类型

README Project Adaptation 表列出了四种：

| 类型 | 用户基数 | Gear 4 蒸馏潜力 | 验证难度 |
|------|----------|-----------------|---------|
| Academic Paper | ✅ 已有 ASCC | — | — |
| **Software Product** | 最大 | 高（API 设计模式、部署知识、bug 分类法） | 中 |
| Data Analysis | 中 | 中（方法论、数据源评估） | 低 |
| Learning Plan | 小 | 低（较个人化） | 低 |

### 立场 D（Software Product）

第一个非 ASCC 示例应该是 **Software Product** 类型，理由：

1. **用户基数最大**：绝大多数 Claude Code / Cursor 用户在做软件项目
2. **Gear 4 蒸馏潜力高**：软件项目有很多可提炼的通用模式（API 设计决策、依赖管理、部署流水线、性能调优经验）
3. **与 ASCC 互补**：ASCC 是学术研究，Software Product 覆盖另一个大类
4. **验证 agent-agnostic**：软件项目是 Cursor / GPT 用户最常见的场景，如果 example 足够好，能吸引非 Claude 用户

### 攻击 D1："Myco 自身"就是一个 Software Product——为什么不直接用它？

**攻击**：Myco 自己就是一个 Python 开源框架项目，刚刚完成了 `myco migrate self`，有完整的 MYCO.md、_canon.yaml、log.md、Gear 3 回顾。为什么不直接把 Myco 自身作为 Software Product 类型的 example？

**防御考察**：
- 这是一个非常好的攻击。Myco 自身确实是一个 software product，而且它是**已经跑通了 Myco 生命周期的真实项目**——不是虚构的 demo。
- MYCO.md 有框架开发的真实 hot zone、_canon.yaml 有 package 节、log.md 从今天开始、Gear 3 产出了真实的修复。
- **但**：Myco 自用有严重的递归问题——它是"用 Myco 管理 Myco 开发"，用户会困惑"这是在展示 Myco 的功能还是在展示怎么开发 Myco"。
- **更关键的是**：Myco 自身的 Gear 4 尚未完成（它还在 Phase 1）。作为 example，它展示的是一个"正在进行中的项目"，而不是一个"跑完完整周期的项目"。

**结论**：Myco 自身**不适合**作为 examples/ 中的示例。它的递归性质会模糊边界。但它的存在是有价值的——README 可以提到"Myco 自身用 Myco 管理，详见根目录 MYCO.md"。

### 攻击 D2：没有真实跑过 Myco 的软件项目，example 只能是虚构的

**攻击**：ASCC 之所以有价值，是因为它是真实项目的真实经历。一个虚构的"假装用了 Myco 的软件项目"没有说服力。

**防御**：这是最关键的攻击。三条可能的路：

**路径 1（虚构 demo）**：创造一个假项目（比如"TODO app"），假装它经历了 Myco 生命周期。
- ❌ 违反诚实原则。虚构的 log.md 和辩论记录读起来会感觉"假"。

**路径 2（等待社区）**：不急，等第一个社区用户在真实软件项目上用 Myco 并提交 battle report。
- ⚠️ 鸡生蛋问题：没有 example 展示 → 社区不知道 Gear 4 长什么样 → 没人提交 battle report → 没有 example

**路径 3（自造真实项目）**：自己真实地用 Myco 做一个小而完整的软件项目（比如开发一个 CLI 工具、一个 MCP server、或一个小型 library），跑完 Gear 1-4 的完整周期，然后将其作为 example。
- ✅ 真实、可控、可完整展示
- 需要时间投入，但项目本身可以有独立价值
- 如果选得好，这个项目还能成为"Myco 生态"的一部分（比如一个 Myco 的辅助工具）

**防御结论**：**路径 3** 是唯一满足"真实 + 可控 + 可展示"的路径。

### 攻击 D3：路径 3 的项目选什么？

**考量维度**：
1. 项目规模足够小（1-2 周能跑完全周期）但不是 trivial（有真实的设计决策）
2. 有真实的 Gear 4 蒸馏潜力（能产出对其他软件项目有用的模式）
3. 最好对 Myco 生态有直接贡献（双赢）

**候选**：
- **A. Myco Adapter for GPT**：v1.0 goal 之一，有真实需求，能蒸馏出"agent adapter 设计模式"
- **B. Myco VS Code Extension**：IDE 集成，有真实需求，能蒸馏出"VS Code extension 开发模式"
- **C. 独立小型 CLI 工具**：比如一个 Markdown linter 或文件组织器，与 Myco 无直接关系，展示"纯第三方项目如何用 Myco"

**各候选的 trade-off**：

| 候选 | 真实需求 | Myco 生态贡献 | 展示"第三方用 Myco" | Gear 4 蒸馏潜力 |
|------|----------|-------------|-------------------|----------------|
| A. GPT Adapter | ✅ 高 | ✅ 高 | ❌ 还是 Myco 自身 | 中（adapter 模式） |
| B. VS Code Ext | ✅ 中 | ✅ 中 | ⚠️ 半内半外 | 中（extension 模式） |
| C. 独立 CLI 工具 | ⚠️ 需设计 | ❌ 无直接 | ✅ 最佳 | 高（通用软件模式） |

**Round 4 初步结论**：首选 **C（独立小型 CLI 工具）**。

理由：它是唯一能向社区展示"我不是 Myco 开发者，但我可以在自己的软件项目上用 Myco"这个信息的选项。如果 example 还是 Myco 生态内部的东西，社区看到的信号是"Myco 只适合开发 Myco"，这与 agent-agnostic 的定位矛盾。

但具体选什么 CLI 工具——**暂不在此轮决定**，需要另一轮辩论或用户指定。

置信度 **80%**。

剩余 20%：具体项目选择影响很大（trivial 项目蒸馏不出有价值的 Gear 4 产物），需要更细致的评估。

---

## Round 5：社区 battle report → example 的贡献管线

### 当前状态

`CONTRIBUTING.md` 已经强调了 battle report 是最有价值的贡献。`.github/ISSUE_TEMPLATE/battle_report.md` 和 `.github/DISCUSSION_TEMPLATE/show-and-tell.yml` 也已就位。

但：**从 battle report 到 examples/ 的升级路径不存在。**

### 立场 E（三级管线）

battle report → example 的升级应该是一个明确的三级管线：

**Level 1: Discussion Post**（低门槛）
- 用户在 GitHub Discussions "Show and Tell" 里发帖
- 内容：项目背景 + 用了哪些 Myco 功能 + 学到了什么
- 门槛：一段文字就够
- **任何人都可以做，不需要 Gear 4**

**Level 2: Battle Report**（中门槛）
- 用户提交 battle_report issue 或更详细的 Discussion
- 内容：项目统计 + Evolution Timeline + 关键学习 + 改进建议
- 门槛：需要跑完至少一个 Gear 3
- **维护者将优秀 battle report 编辑后纳入某个索引页**

**Level 3: Featured Example**（高门槛）
- 用户（或维护者）将完整生命周期整理为 examples/ 子目录
- 内容：完整的 Harvest 快照 + Gear 4 蒸馏产物 + 反向链接
- 门槛：必须跑完 Gear 4，且蒸馏产物被 Myco 框架接受
- **这是 Myco 知识库"生长"的最直接证据**

### 攻击 E1：三级太复杂，社区还没有足够的活跃度

**攻击**：Myco 是 v0.x，可能几个月内只有个位数的外部用户。三级管线是过度设计。

**防御**：
- 三级管线不需要一次性实现。Level 1（Discussion）和 Level 2（Battle Report）已经有 infrastructure。Level 3（Featured Example）是未来的事。
- 关键是**现在就把升级路径写清楚**——在 CONTRIBUTING.md 里明确说"你的 battle report 有可能成为 Featured Example"，给贡献者一个期望目标。
- 实际运维：前 6 个月，维护者（你）手动管理就够了。自动化是后面的事。

### 攻击 E2：Gear 4 蒸馏产物的"接受标准"是什么？

**攻击**：Level 3 要求"蒸馏产物被 Myco 框架接受"——谁来判断？标准是什么？

**防御**：这是一个必须回答但暂时可以简化的问题。
- v0.x 阶段：维护者判断。标准是"这个蒸馏产物对至少两种项目类型有用"。
- v1.0 后：可以引入 peer review（类似学术期刊的同行评审）。
- 现在不需要过度定义，但需要在 CONTRIBUTING.md 里给出方向性描述。

**Round 5 结论**：三级管线设计合理，但 v0.x 阶段只需实现 Level 1-2（已有基础设施），Level 3 在第一个社区 Gear 4 出现时再正式落地。置信度 **83%**。

---

## 终局收敛

| 决策 | 结论 | 置信度 |
|------|------|--------|
| Q1: examples/ 定位 | Gear 4 生命周期展示（不是 onboarding 教程） | 88% |
| Q2: example 内容 | Harvest 快照（结构文件完整 + 内容脱敏）+ README 叙述 + Gear 4 反向链接 | 82% |
| Q3: ASCC 升级 | 补 Gear 4 反向链接 + Evolution Timeline + 结构文件快照 | 85% |
| Q4: 首个非 ASCC | Software Product 类型；真实独立项目（路径 3）；具体项目待定 | 80% |
| Q5: 社区管线 | 三级（Discussion → Battle Report → Featured Example）；v0.x 只需前两级 | 83% |

**综合置信度：84%**

剩余 16% 不确定性来自：
- Q4 具体项目选择（影响 Gear 4 蒸馏质量的关键变量，暂未决定）
- Q2 脱敏方案的实操可行性（需要对 ASCC 真实文件做一遍才知道）
- Q5 Level 3 的接受标准（v0.x 靠维护者判断，v1.0 后需要更明确的机制）

---

## 立即可执行的行动项

| ID | 内容 | 依赖 |
|----|------|------|
| E1 | 升级 examples/ascc/README.md：补 Gear 4 反向链接 + Evolution Timeline | 无 |
| E2 | CONTRIBUTING.md 补充"从 battle report 到 Featured Example"的升级路径描述 | 无 |
| E3 | 选定第一个非 ASCC 真实项目（需要用户参与） | Q4 具体项目讨论 |
| E4 | 用 Myco 从零开始做该项目，跑完 Gear 1-4 | E3 |
| E5 | 将完成的项目整理为 examples/ 子目录 | E4 |

**E1 和 E2 可以现在做。E3 需要你的输入——你有没有一个"刚好要做的小型软件项目"可以同时作为 Myco 的第二个真实验证？**
