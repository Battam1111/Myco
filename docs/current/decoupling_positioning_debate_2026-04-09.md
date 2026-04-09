# 传统手艺：Myco 解耦 + 差异化定位 + 生态策略

> 文档状态：[ACTIVE] | 版本：v0.1 | 创建：2026-04-09
> 参与者：创始人（方向定调）+ Claude（辩论+执行）
> 前置调研：竞品调研（8 个框架/产品深度分析）+ 代码审计（11 个 CRITICAL、4 个 MEDIUM、4 个 LOW 级 [原始项目] 残留）

---

## 预备：竞品全景（辩论素材）

在开始辩论之前，先整理我们面对的竞争格局：

### 1. 记忆层（Memory Layer）

| 项目 | 核心方法 | 特征 | Stars |
|------|----------|------|-------|
| **MemPalace** | 空间隐喻（Wing/Room/Hall）+ ChromaDB 向量存储 + 知识图谱 | 存一切再检索，LongMemEval 96.6% R@5，完全本地，$0 | 28.4k |
| **Letta (MemGPT)** | OS 式三层内存（core/archival/recall）+ agent 主动管理 | Agent 通过函数调用管理自己的记忆，无限上下文 | ~30k |
| **Mem0** | 即插即用记忆 API（bolt-on） | 最大开发者社区，专注简单集成 | ~25k |
| **Zep** | 云端记忆服务 | 企业级，$20-200/月 | ~10k |

### 2. Agent 框架 + Harness

| 项目 | 核心方法 | 特征 |
|------|----------|------|
| **Hermes Agent** | MEMORY.md(2200字符) + USER.md + 自动 Skill 生成 | "自改善"——任务完成后自动写 skill markdown，33k stars |
| **Claude Code Harness** | CLAUDE.md 三层记忆 + 60+ tools + context compression | Anthropic 官方，CLAUDE.md ≤200行，按需加载 |
| **Claude Managed Agents** | 云托管 agent 基础设施（沙箱+检查点+凭证+追踪） | 平台级，不是知识管理工具 |
| **OpenClaw** | MEMORY.md + SOUL.md + daily logs | 145k stars，文件式记忆的标杆 |

### 3. Skill / Protocol

| 项目 | 核心方法 | 特征 |
|------|----------|------|
| **Nuwa-Skill** | SKILL.md 作为过程性记忆 + NCP 能力发现协议 | Agent-centric computing 愿景 |
| **MCP (Anthropic)** | 工具集成协议 | 事实标准，不是知识管理 |

### 4. 文件式记忆的"趋同进化"

来自调研的一个关键发现：**Manus ($2B 被 Meta 收购)、OpenClaw (145k stars)、Claude Code 三个完全独立的项目都趋同到了文件式记忆（markdown files）**。这不是巧合——这是最优解的信号。

---

## Round 1：Myco 到底和它们有什么不同？

### 1.1 我的初始立场（Claude）

观察到的竞品景观可以按一个维度排列：**关注点在哪里**。

```
存储层 ←————————————————————→ 进化层
  │                                │
  MemPalace  Letta  Mem0      Hermes  Myco
  (存一切)   (OS式)  (API)   (skill)  (???)
```

**假设 H1**：当前市场分成两大阵营——
- **记忆阵营**（MemPalace/Letta/Mem0/Zep）：核心问题是"怎么存，怎么检索"
- **框架阵营**（Hermes/Claude Code/OpenClaw）：核心问题是"怎么让 agent 工作得更好"

Myco 声称自己不是记忆系统，也不是 agent 框架。它是"延伸认知基质"。但这个定位听起来很学术，很模糊。

### 1.2 对 H1 的挑战

**挑战 C1**：Hermes Agent 也声称"自改善"——它的 skill 自动生成难道不就是 Myco 的 Gear 1/2 吗？

回应：仔细看 Hermes 的"自改善"机制——
- MEMORY.md 硬限 2200 字符，USER.md 限 1375 字符——**这是记忆管理，不是知识进化**
- Skill 生成是"任务→文档"的单向过程——**没有 skill 自身的版本演进、质疑、替换**
- 没有 lint，没有 _canon.yaml，没有一致性保障——**skill 可以互相矛盾而不被检测**
- 没有 Gear 3（架构质疑）——**系统永远不会质疑自己的运作方式**

关键差异：**Hermes 的"自改善"是单循环学习（single-loop）——做事→记住怎么做。Myco 的进化引擎是三环学习——做事→反思怎么做→质疑为什么这样做→改变做事的规则**。

**挑战 C2**：MemPalace 的检索能力远超 Myco（96.6% R@5 vs Myco 的 grep）。Myco 在记忆检索上怎么竞争？

回应：**Myco 根本不应该和 MemPalace 在检索层竞争。** MemPalace 是一个优秀的 L0 存储引擎——Myco 可以 *使用* MemPalace 作为它的 L0 Archive 层，就像菌丝网络使用土壤。

这正是 创始人 说的"吞噬能力"——**Myco 不替代它们，Myco 消化它们**。

**挑战 C3**：Claude Code 的 CLAUDE.md + harness 模式已经是事实标准。Myco 加了什么？

回应：Claude Code 的 CLAUDE.md 模式解决的是 **L1 记忆入口**问题。它做得很好——200 行限制、自动加载、三层记忆。但它 **没有**：
- 进化引擎（CLAUDE.md 不会自己改善 CLAUDE.md 的结构）
- 一致性保障（没有 _canon.yaml + lint）
- 传统手艺（没有结构化辩论协议）
- 操作叙事（没有失败路径外化）
- 跨项目蒸馏（每个项目的 CLAUDE.md 都是孤立的）

**CLAUDE.md 是 Myco L1 层的一个特例（特化为 Claude agent 的版本）。Myco 是完整的四层 + 进化引擎。**

### 1.3 Round 1 结论

**核心洞察**：竞品都在解决"静态"问题（怎么存、怎么检索、怎么组织）。Myco 解决的是"动态"问题——**知识系统如何自我改善**。

**初步定位公式**：
> Myco = 文件式知识架构（和大家一样）+ 自进化引擎（只有 Myco 有）+ 生态吞噬能力（理论独有）

**置信度：55%**——公式方向对了，但"自进化"和"吞噬"还需要更精确的表达。

---

## Round 2：精炼差异——一句话说清卖点

### 2.1 挑战 Round 1 结论

**挑战 C4**：说"只有 Myco 有自进化"是不是太绝对了？Hermes 的 skill refinement 难道不算？

回应（更精确的表述）：

进化有**层次**：

| 层次 | 描述 | 谁有 |
|------|------|------|
| **L-exec** 执行优化 | 做同样的事越做越快 | 所有 agent（上下文学习） |
| **L-skill** 技能积累 | 新任务→新 skill | Hermes, OpenClaw |
| **L-struct** 结构演进 | 改变知识的组织方式 | **只有 Myco（Gear 3）** |
| **L-meta** 元规则进化 | 改变进化规则本身 | **只有 Myco（Gear 4 + Bitter Lesson 立场）** |

Hermes 做到了 L-skill。**Myco 做到了 L-meta。** 这不是程度差异，是质的差异。

**挑战 C5**：用户不关心"元进化"——他们关心"能不能让我的 agent 更好用"。如何把学术概念翻译成用户语言？

这是最关键的挑战。让我用三组对比来表达：

**用户视角的差异**：

1. **Hermes**：你的 agent 学会了做新事情（accumulate skills）
2. **MemPalace**：你的 agent 记住了一切（accumulate memories）  
3. **Myco**：你的 agent 学会了如何更好地学习（evolve the learning process itself）

更具体地说：
- 用 Hermes 100 天后，你有 100 个 skills——但它们可能互相矛盾、过时、冗余
- 用 MemPalace 100 天后，你有完整的历史——但检索出什么取决于你问什么
- **用 Myco 100 天后，你的整个知识系统比第 1 天更聪明地组织、更严格地自检、更高效地工作**

### 2.2 一句话卖点候选

A. "The only knowledge system that evolves itself, not just its contents"
B. "Other tools remember. Myco learns how to remember better."
C. "Markdown files that get smarter over time"
D. "The immune system for your agent's knowledge"

**辩论**：
- A 太学术（"evolves itself" 对用户无感）
- B 很好但"learns how to remember"还是容易和记忆系统混淆
- C 朗朗上口但 oversimplify——Myco 不只是 markdown files
- D 有趣但"immune system"暗示防御，Myco 更像是生长

**新候选**：
E. "Other tools give agents memory. Myco gives agents **metabolism**."

metabolism（代谢）——不只存储，而是分解、消化、重组、排泄。这正是 Myco 做的：friction sensing（感知）→ lint（消化检验）→ compression（排泄）→ evolution（生长）。

**挑战 C6**：但 metabolism 这个词对技术用户来说太生物学了。能不能更接地气？

回应——**用两层表述**：

**tagline（给快速扫描的人）**：
> "Other tools give your agent memory. Myco teaches it to think."

**subtitle（给停下来读的人）**：
> "A self-evolving knowledge substrate that doesn't just store — it metabolizes, verifies, and grows."

### 2.3 Round 2 结论

**核心卖点三要素**：
1. **自进化**：不是积累内容，而是改善知识系统本身（L-struct + L-meta）
2. **一致性保障**：lint + _canon.yaml = agent 的知识不会悄悄腐烂（没有其他开源工具做这个）
3. **生态吞噬**：Myco 不替代 MemPalace/Hermes/CLAUDE.md，它消化它们——它们成为 Myco 的"器官"

**置信度：72%**——卖点清晰了，但"吞噬"机制还需要具体化（不能只是说说）。

---

## Round 3：生态吞噬——从理论到机制

### 3.1 "吞噬"到底怎么实现？

创始人 的直觉：Myco 理论上能把其他工具全部吃掉，变成 Myco 的一部分。这是最大的卖点。

让我把这个直觉变成具体的架构：

```
┌─────────────────────────────────────────┐
│              Myco Core                   │
│  (四层架构 + 进化引擎 + lint + craft)     │
│                                          │
│  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ Adapter: │  │ Adapter: │  │Adapter:│ │
│  │MemPalace │  │ Hermes   │  │Claude  │ │
│  │ (L0层)   │  │ (Skill)  │  │ (入口) │ │
│  └──────────┘  └──────────┘  └────────┘ │
│                                          │
│  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ Adapter: │  │ Adapter: │  │Adapter:│ │
│  │ Letta    │  │ MCP      │  │  ...   │ │
│  │ (记忆)   │  │ (工具)   │  │        │ │
│  └──────────┘  └──────────┘  └────────┘ │
└─────────────────────────────────────────┘
```

**Adapter 模式**：每个外部工具通过一个薄适配层接入 Myco 的四层架构：

| 外部工具 | 接入层 | 适配方式 |
|---------|--------|----------|
| MemPalace | L0 Archive | Myco 调用 MemPalace API 做深度检索，结果进入 Myco 的知识代谢流 |
| Hermes Skills | L1.5 Wiki 或 L2 Docs | 导入 Hermes skill markdown → lint 检查一致性 → 纳入进化周期 |
| CLAUDE.md | L1 Entry | Myco 的 MYCO.md 就是增强版 CLAUDE.md，零摩擦兼容 |
| Letta | L0 Archive + L1.5 | Letta 的 archival memory 作为 L0，core memory 映射到 L1 |
| MCP Servers | L3 Code (工具层) | MCP tools 作为 Myco agent 的执行工具 |

**关键洞察**：Myco 不需要*替换*这些工具——它提供一个 **进化框架**，让这些工具的输出被代谢、验证、进化。就像菌丝网络不替代土壤中的细菌，而是将它们分解的养分纳入自己的网络。

### 3.2 挑战吞噬机制

**挑战 C7**：这个 Adapter 架构在 v0.x 里是 vaporware 吗？如果是，README 里不能写。

诚实回应：**是的，v0.x 没有任何 adapter 的代码实现。** 

但这并不意味着吞噬是空话。v0.x 的吞噬是**协议级**的，不是代码级的：
- Myco 的四层架构是一个**分类标准**——任何外部知识都能被归入 L0/L1/L1.5/L2/L3
- 进化引擎是一个**处理协议**——任何新内容都进入 friction → lint → evolve 循环
- 这两样在 v0.x 已经可以手动操作

**v0.x 的诚实定位**：
- ✅ 协议级吞噬（人工操作：把 Hermes skill 复制到 wiki/，运行 lint）
- ⏳ 工具级吞噬（v1.0 目标：`myco import --from hermes-skills ./skills/`）
- 🔮 自动化吞噬（v2.0 愿景：Myco agent 自动发现、评估、集成外部知识源）

**挑战 C8**：如果 v0.x 的吞噬只是"手动复制+lint"，那用户凭什么选 Myco 而不是直接用 Hermes？

这是致命问题。回应：

v0.x 的真正竞争力不在 adapter，而在 **进化引擎是唯一的**。即使你今天手动把 Hermes skill 复制进来，Myco 会：
1. lint 检查它和已有知识的一致性（Hermes 不会）
2. 在 Gear 2 反思时评估它是否被实际使用（Hermes 不会）
3. 在 Gear 3 质疑它的底层假设是否还成立（Hermes 不会）
4. 在 Gear 4 跨项目时判断它是否值得蒸馏为通用模板（Hermes 不会）

**Hermes 给你的 skill 是不朽的——它永远不会被质疑、淘汰或重组。Myco 给你的知识是活的——它会衰老、被检验、被替换、被进化。**

### 3.3 Round 3 结论

**吞噬的三阶段路线图**已清晰：
- v0.x：协议级吞噬（手动 + lint 验证）
- v1.0：工具级吞噬（CLI import 命令）
- v2.0：自动化吞噬（agent 驱动的知识发现+集成）

**置信度：80%**

---

## Round 4：解耦架构 + 热启动模块设计

### 4.1 审计结论汇总

代码审计发现以下 [原始项目] 残留：

**CRITICAL（必须删除/重写）：**
1. `examples/ascc/README.md` — 整个文件都是 [原始项目] 专属内容
2. `README.md` — lines 116-122 [原始项目] 统计数据 + line 31 个人 GitHub 用户名
3. `LICENSE` — "创始人" 个人名字
4. `docs/theory.md` — 项目特定示例和个人引用
5. `docs/v09_planning_debate_2026-04-09.md` — 整个文件是 [原始项目] 规划辩论
6. `docs/vision.md`（如果存在）— "Proven in Practice" 虚假多项目验证
7. `docs/evolution_engine.md` — 算法/实验/环境特定细节
8. `docs/architecture.md` — line 6 虚假多项目声明

**MEDIUM（需要通用化）：**
9. `docs/evolution_engine.md` — 项目特定风味的摩擦示例
10. `templates/WORKFLOW.md` — CLAUDE.md 残留引用
11. `templates/MYCO.md` — [原始项目] 行内注释

**LOW（可选清理）：**
12. `scripts/lint_knowledge.py` — "paper" 日志类型
13. `scripts/compress_original.py` — "Caveman Project" 引用

### 4.2 解耦方案

**原则**：开源仓库 = 纯框架。[原始项目] 相关内容全部迁移到 `examples/ascc/`（作为案例研究），并且案例研究也要脱敏。

**具体操作**：

**A. 删除/重写（CRITICAL）**
1. `examples/ascc/` → 重写为脱敏案例研究（不提 [顶会]、不提具体算法名、不提日期）
2. `README.md` → 删除 §"Proven in Practice" 中的 [原始项目] 统计，替换为通用"battle-tested on a complex research project"
3. `LICENSE` → 改为 "Myco Contributors"
4. `docs/theory.md` → 删除项目特定示例，将 [原始项目] 引用替换为"[a multi-month research project]"
5. `docs/v09_planning_debate_2026-04-09.md` → **整个移到 [原始项目] 仓库或删除**（这是 Myco 项目自身的内部规划，不该在开源框架里）
6. `docs/architecture.md` line 6 → 删除"多项目实战"虚假声明，改为"Validated through intensive single-project use; generalization ongoing"
7. `docs/evolution_engine.md` → 将 [原始项目] 具体例子替换为通用化示例

**B. 热启动模块设计**

这是 创始人 提出的关键需求：闭源项目如何从混杂状态迁移到使用 Myco 的理想状态。

设计：`myco_init.py` 新增 `--migrate` 模式：

```
# 场景 1：全新项目
myco init my-project --level 2

# 场景 2：已有项目想引入 Myco（热启动）
myco migrate ./existing-project --level 2
```

`--migrate` 的行为：
1. **扫描**：分析已有目录结构，识别已存在的 CLAUDE.md / MEMORY.md / SKILL.md 等文件
2. **映射**：将识别到的文件映射到 Myco 四层架构
   - 发现 CLAUDE.md → 提示：是否作为 L1 入口（重命名/保留/合并）
   - 发现 MEMORY.md → 提示：导入为 wiki/ 知识页
   - 发现 skill 目录 → 提示：导入为 docs/ 操作叙事
3. **生成骨架**：创建缺失的 Myco 组件（_canon.yaml, lint, log.md 等）
4. **不破坏**：所有操作都是非破坏性的——不删除已有文件，只添加 Myco 层

**对 [原始项目] 的具体热启动路径**：
```
myco migrate /path/to/ascc --level 2 --entry-point CLAUDE.md
```
这会：
- 保留 [原始项目] 已有的 CLAUDE.md（因为它已经是完善的 L1 入口）
- 识别 wiki/, docs/, scripts/ 已存在 → 跳过创建
- 只补充缺失的 _canon.yaml 模板字段、WORKFLOW.md 更新等
- 生成一个 `migration_report.md` 说明做了什么、建议下一步

### 4.3 Round 4 结论

**解耦方案**：13 个 CRITICAL 项 + 4 个 MEDIUM 项 + 3 个 LOW 项，全部有具体操作方案。
**热启动模块**：`myco migrate` 命令，非破坏性，识别已有知识文件并映射到 Myco 架构。

**置信度：85%**

---

## Round 5：一键使用 + 社区策略

### 5.1 当前的采用障碍

1. **安装复杂度**：需要 git clone + python 脚本——比 `npx` / `pip install` 门槛高
2. **概念负载**：四层架构 + 十二原则 + 四齿轮——新用户看到就退
3. **无社区入口**：没有 Discord、没有 issue 模板、没有 contributing guide
4. **无集成点**：不能一键和 Claude Code / Hermes / Cursor 集成

### 5.2 一键使用方案

**目标**：30 秒内从 0 到"Myco 在工作"。

**方案 A：pip 安装**
```bash
pip install myco
myco init my-project
```

**方案 B：npx（零安装）**
```bash
npx create-myco my-project
```

**方案 C：Claude Code marketplace skill**
```
/install myco
```

**推荐：A + C 并行**。pip 覆盖 Python 生态（学术/数据/ML），marketplace 覆盖 Claude 生态。npx 可以延后。

**渐进式上手**：
```
Step 1 (30秒): myco init → 得到 MYCO.md + log.md
Step 2 (自然发生): 工作中遇到摩擦 → Myco 提示记录 → Gear 1 启动
Step 3 (几天后): 第一次 session end → Gear 2 自动触发反思
Step 4 (几周后): 知识库长大 → lint 开始有价值 → Gear 3 在里程碑触发
```

**关键设计原则**：**不要在第 1 天教用户四层架构和十二原则。让他们在第 30 天自己发现。**

### 5.3 社区策略

**核心洞察**：Myco 的社区不应该是"讨论 Myco 怎么用"的社区，而应该是**"分享 Myco 进化出了什么"的社区**。

- **Gear 4（跨项目蒸馏）本身就是社区机制**：用户在自己的项目里用 Myco → 进化出独特的 workflow / wiki 模板 / lint 规则 → 提交为 community template → 其他用户 `myco import --template community/xxx`

这意味着 Myco 的 community 贡献不是代码 PR，而是**知识进化的产物**：
- 新的 wiki 模板（"我在做前端项目时发现这种 wiki 结构最好"）
- 新的 lint 规则（"我发现检查 X 可以防止 Y 类错误"）
- 新的 workflow 原则（"我发现 W13: xxx 在数据分析项目中很有用"）
- 新的 adapter（"这是我写的 MemPalace → Myco L0 适配器"）

**这是 Myco 最独特的社区模型**：其他开源项目的社区贡献是代码。**Myco 的社区贡献是进化后的知识本身。**

### 5.4 与现有生态的"接洽"策略

**而不是"竞争"策略**——这是关键心态。

| 生态 | 接洽方式 | 价值主张 |
|------|---------|---------|
| **Claude Code** | Myco 作为 CLAUDE.md 的"升级路径"——用户现有的 CLAUDE.md 直接兼容 | "你的 CLAUDE.md 已经是 Myco L1 了，只需要 `myco migrate` 解锁 L1.5-L3 + 进化引擎" |
| **Hermes Agent** | Myco 导入 Hermes skills 并加入进化周期 | "你的 skills 不会过时了——Myco 让它们自动演进" |
| **MemPalace** | Myco 使用 MemPalace 作为 L0 检索后端 | "MemPalace 存一切，Myco 让存下来的东西活起来" |
| **Cursor / Windsurf** | Myco 作为项目级知识层，IDE 无关 | "换 IDE 不丢知识——Myco 不住在你的编辑器里" |

### 5.5 Round 5 结论

**一键使用**：pip install + Claude marketplace，渐进式上手（不在第 1 天暴露复杂度）
**社区**：知识进化产物即社区贡献（template, lint rule, workflow principle, adapter）
**生态**：接洽而非竞争——Myco 是升级路径，不是替代品

**置信度：82%**

---

## Round 6：统一收敛——终极定位

### 6.1 综合三个方向

经过 5 轮辩论，三个方向已经收敛到一个统一的愿景：

**Myco 的一句话定位**：
> **Myco 是唯一一个能自我进化的 AI 知识基底——它不替代你现有的工具，它让你现有的工具产生的知识活过来。**

**英文版**：
> **Myco is a self-evolving knowledge substrate for AI agents. It doesn't replace your tools — it makes their knowledge come alive.**

### 6.2 三层价值叙事

**30 秒版（README 顶部）**：
> Other tools give your agent memory. Myco teaches it to think.

**3 分钟版（README 正文）**：
> 你的 agent 用 CLAUDE.md 记住项目上下文，用 Hermes skills 记住操作步骤，用 MemPalace 记住所有对话。但谁来检查这些记忆是否互相矛盾？谁来淘汰过时的知识？谁来质疑底层假设是否还成立？谁来把一个项目的经验蒸馏到下一个项目？
>
> Myco 做这些事。它是你的 agent 的知识代谢系统——不是又一个记忆工具，而是让所有记忆工具产生的知识保持活性、一致性和进化性的基底层。

**30 分钟版（docs/theory.md + architecture.md）**：
> 完整的理论基础（Clark & Chalmers 延伸心智 + Argyris 三环学习 + Polanyi 隐性知识）+ 四层架构 + 进化引擎详述。

### 6.3 最终挑战

**挑战 C9（自我挑战）**：以上定位有没有"皇帝的新衣"风险——我们声称的东西 v0.x 真的做到了吗？

诚实审计：

| 声称 | v0.x 现实 | 诚实度 |
|------|-----------|--------|
| 自进化引擎 | Gear 1-3 有协议定义，在 [原始项目] 上验证过 Gear 1-3 | ✅ 真实（Gear 4 未验证） |
| 一致性保障 | lint 9维 + _canon.yaml 在 [原始项目] 上运行 | ✅ 真实 |
| Agent 无关 | 模板用 {{ENTRY_POINT}}，支持 MYCO.md/CLAUDE.md | ✅ 真实（但只在 Claude 上测试过） |
| 生态吞噬 | **零代码实现**，只有协议级描述 | ⚠️ 愿景级——必须标注为 roadmap |
| "teaches it to think" | 进化引擎改善知识结构，但不改善 agent 的推理 | ⚠️ 夸张——需要降调 |
| 社区知识贡献 | 零社区、零用户 | ⚠️ 愿景级——必须标注 |

**修正后的诚实定位**：

> **Myco v0.x** is a battle-tested knowledge architecture with a self-evolution protocol, validated on one intensive research project. It provides what no other tool does: automated consistency checking, structured knowledge metabolism, and a protocol for your knowledge system to evolve itself over time.
>
> **What's proven**: Four-layer architecture, 9-dimension lint, three gears of evolution (friction → reflection → retrospective), agent-independent entry point.
>
> **What's roadmap**: Ecosystem adapters, pip install, community templates, Gear 4 cross-project distillation.

### 6.4 终极收敛

**定位**：Self-evolving knowledge substrate（不是 memory tool，不是 agent framework）
**卖点（已验证）**：lint + canon + evolution gears = 知识不腐烂
**卖点（愿景级）**：生态吞噬 + 社区知识贡献
**一键使用路径**：pip install → myco init → 渐进发现
**社区模型**：进化产物即贡献
**解耦策略**：13 CRITICAL 清理 + `myco migrate` 热启动
**与竞品关系**：接洽而非竞争，升级路径而非替代品

**最终置信度：90%**

剩余 10% 不确定性来自：
- Gear 4 未经实战验证
- "teaches it to think" tagline 可能需要再推敲
- v0.x 的真实用户反馈 = 0（只有创作者自用）

---

## 行动项（辩论→执行）

### P1：立即执行（解耦清理）
1. 清理 README.md 中所有 [原始项目] 引用
2. 清理 docs/ 中所有 [原始项目] 泄漏
3. 重写 examples/ascc/ 为脱敏案例研究
4. 删除 docs/v09_planning_debate_2026-04-09.md（内部规划文档）
5. LICENSE 改为 "Myco Contributors"
6. templates/ 中的 [原始项目] 残留注释

### P2：本轮实现（热启动）
7. myco_init.py 添加 --migrate 模式
8. migration_report.md 模板

### P3：下一轮（v0.9 准备）
9. pip 包化 + pyproject.toml
10. README 重写（三层价值叙事）
11. CONTRIBUTING.md + issue 模板
12. GitHub Discussions 开启

### P4：未来（v1.0 roadmap）
13. Adapter 接口定义
14. `myco import` CLI 命令
15. Community template registry
