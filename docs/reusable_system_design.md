# LLM Agent 知识系统：通用架构与自进化引擎

> **版本**：2.1（一般化版 + Nuwa/Caveman 知识质量机制）
> **目标**：任何项目均可 bootstrap 的 LLM Agent 跨会话知识系统，内置自进化能力
> **理论基础**：Karpathy LLM Wiki + Polanyi Tacit Knowledge + Argyris Double-Loop Learning + Toyota PDCA + Voyager Skill Library
> **来源**：Myco 核心文档，ASCC 项目 Gear 4 蒸馏写入（2026-04-09）
> **实战验证（ASCC v1）**：7 天，~80 文件，~13,500 行，12+ 次传统手艺辩论，首次 Gear 3 实战执行

---

## 核心问题与解决思路

LLM Agent 跨会话工作时面临的根本问题：**每次新会话都从零开始**。

解决方案不是"写更多文档"，而是构建一个让 Agent 能在 30 秒内重建工作状态的知识系统，并让这个系统在使用过程中**自我进化**。

**三个互补的思想来源**：

- **Karpathy LLM Wiki**（2026）：知识应被编译一次并持续维护，不是每次重新推导。结构化 wiki + index + lint。
- **Polanyi Tacit Knowledge**（1966）：显性规则不够——还需要提供丰富的 proximal terms（失败路径、操作叙事），让 Agent 建立 from-to structure。
- **Argyris Double-Loop Learning**（1977）：Single-loop 改行动，Double-loop 改心智模型。系统不仅要修正错误，还要质疑自身架构假设。

---

## 系统架构：四支柱 + 进化引擎

```
┌─────────────────────────────────────────────────────────────┐
│                   L-meta: Evolution Engine                    │
│         (Friction Sensing → Reflection → Retrospective       │
│          → Cross-Project Distillation)                       │
├──────────┬──────────────┬──────────────┬────────────────────┤
│ Pillar 1 │   Pillar 2   │   Pillar 3   │    Pillar 4        │
│ Schema   │  Knowledge   │  Experience  │    Timeline +      │
│ Layer    │  Layer       │  Layer       │    Infrastructure   │
│          │              │              │                     │
│CLAUDE.md │ wiki/*.md    │ operational  │ log.md             │
│WORKFLOW  │ docs/primordia │ _narratives  │ _canon.yaml        │
│.md       │              │ Context      │ lint_knowledge.py  │
│          │              │ Priming      │                     │
└──────────┴──────────────┴──────────────┴────────────────────┘
```

### Pillar 1: Schema Layer（元协议）

**角色**：Agent 的"操作系统"——每次新会话自动加载，定义行为边界。

**核心文件**：

| 文件 | 加载方式 | 说明 |
|------|---------|------|
| `CLAUDE.md` | ✅ 自动加载 | 纯索引 + schema + 当前状态 |
| `docs/WORKFLOW.md` | 按需读取 | 完整原则定义 + 流程详述 |

**CLAUDE.md 分级模板**：

| 级别 | 行数 | 适用场景 | 包含内容 |
|------|------|---------|---------|
| **Minimal** | ~50 | 小项目、IDE 集成（Cursor 等） | 项目身份 + 任务队列 + 3 条核心规则 |
| **Standard** | ~150 | 中等复杂度项目 | + 知识索引 + 会话规程 + 自主权边界 |
| **Full** | ~300 | 长期/复杂项目（如学术论文） | + 详细热区 + 脚本索引 + 进度表 |

> **Design Rationale**: CLAUDE.md 越短，新会话启动越快。分级避免了小项目背负大系统的开销。300 行上限来自 ASCC 经验——193 行工作良好，但不应继续膨胀。

**CLAUDE.md 热区结构**（Standard 及以上）：

```markdown
## 🔥 热区
**项目**：[一句话描述]
**当前阶段**：[Phase X — 具体状态]

**最容易出错的 N 件事** ⚠️：
1. [从实际踩坑中提炼，不是理论预防]

**Agent 行为准则**：
- [项目特定的核心规则]

**🎯 Operational Feel**：
[≤5 行工具环境手感描述]
```

> **Design Rationale**: 热区是 Agent 最先读到的内容。"最容易出错的事"必须来自真实失败——ASCC 中每一条都对应至少一次真实踩坑。Operational Feel 是 W6 近端丰富化的入口，帮助 Agent "住进" 工具环境。

**辅助文件**：

- **`_canon.yaml`**：所有规范值的 Single Source of Truth。分为 `system:` 和 `project:` 两节——前者跨项目通用，后者项目特有。

> **Design Rationale**: 同一个数字散落在多处时必然漂移。ASCC 中 P4 进度一度在三处记录了三个不同的值。_canon.yaml 建立"先改 canon → 再改其他"的严格顺序。

**自主权边界**（三层，可按项目调整）：

| 层级 | 范围 | 判断标准 |
|------|------|---------|
| ✅ 自主行动 | 技术执行、Bug 记录、文档更新 | 改错了 10 分钟能修好 |
| 📢 做了再知会 | 工作流微调、监控异常处理 | 改错了 1 小时能修好 |
| 🛑 必须等人类 | 项目方向变更、大资源决策 | 改错了 > 1 小时 |

### Pillar 2: Knowledge Layer（结构化知识库）

**角色**：LLM 维护的编译型知识 + 不可变的原始推理记录。

**两类文件**：

| 类型 | 位置 | 可变性 | 说明 |
|------|------|--------|------|
| Wiki 页面 | `wiki/*.md` | ✅ 可修改 | 编译后的知识——随项目演进更新 |
| 辩论/决策记录 | `docs/primordia/*.md` | ❌ 不可修改 | 完整推理过程——只追加不修改 |

**五种 Wiki 页面类型**（按项目需要选择，不预建）：

| 类型 | 示例 | 何时创建 |
|------|------|---------|
| **实体页** | 算法变体、API 列表、硬件配置 | 项目有多个核心实体需要追踪时 |
| **概念页** | 理论框架、策略选择、设计哲学 | 项目有需要多轮辩论才能确立的概念时 |
| **操作页** | 已知 Bug、部署流程、环境配置 | 同一操作出错 ≥2 次时 |
| **分析页** | 实验结果、根因调查、竞品分析 | 产出需要跨会话持续引用的分析结论时 |
| **技法页** | 写作技法、代码规范、评审清单 | 编译外部最佳实践为项目可用工具时 |

> **Design Rationale**: 不预建空页面——ASCC 的 7 个 wiki 页面全部在需要时自然产生，没有一个是预先规划的。需求驱动创建，避免维护空壳的浪费。

**三种知识获取模式**：

| 模式 | 触发 | 流程 | 频率 |
|------|------|------|------|
| **编译** | 有外部输入（论文、指南、竞品报告） | LLM 读取 → 萃取 → 更新/新建 wiki 页面 | 不定 |
| **沉淀** | Agent 在操作中发现新知识 | 即时写入 wiki/docs → 更新 CLAUDE.md 索引 | 每次会话多次 |
| **维护** | 定期健康检查 | 运行 Lint → 修复不一致 | 每 1-3 次会话 |

**传统手艺（深度辩论式决策）**：

用于影响项目方向的重大决策。机制是通用的，触发信号按项目类型配置。

| 步骤 | 动作 |
|------|------|
| 第一轮 | 清晰陈述主张 |
| 第二轮 | 站在最严苛批评者角度自我攻击 |
| 穿插 | 在线调研（WebSearch），确保有外部证据 |
| 第三轮 | 防御可防的，修正防不了的 |
| 第 N 轮 | 迭代直到所有攻击点有可信防御 |
| 收尾 | ① 更新任务队列 ② 完整记录 → docs/primordia/ ③ 结论萃取 → wiki/CLAUDE.md ④ 追加 log.md |

**触发信号（通用版，项目启动 2 周后校准）**：
- 影响项目核心方向的决策
- 对某个结论的置信度 < 80%
- 外部利益相关者（reviewer/客户/上级）可能质疑的薄弱点
- 在线调研发现了与当前方向冲突的信息

**结论萃取增强**（v2.1）：置信度后增加一维**验证范围**：`[条件] ✅/⚠️/❌`。

**外部知识编译协议**（v2.1，来自 Nuwa-Skill）：从外部来源系统性提取知识时使用 5 步流程：多通道收集（≥3 独立来源） → 三重门控（跨源一致性/实践可操作性/非常识独特性） → 框架萃取（3-7 核心模型） → 局限标注 → 写入 wiki。详见 `docs/WORKFLOW.md` §6.10。

**Wiki 页面标准模板**（v2.1）：轻量级页眉（类型+日期+可选非直觉盲点）+ 页脚（Back to）。渐进迁移。详见 `docs/WORKFLOW.md` §6.8。

**活跃张力标记**（v2.1，来自 Nuwa-Skill 矛盾保留法）：用 `⚡` 标记架构级内在矛盾。详见 `docs/WORKFLOW.md` §6.9。

### Pillar 3: Experience Layer（操作经验）

**角色**：Polanyi 的 from-to structure——提供丰富的失败路径（proximal terms），让 Agent 无需亲自撞墙就能感知墙的存在。

> **Design Rationale**: 这一层是纯 Karpathy 体系中缺失的。Karpathy 的 LLM 角色是图书馆员（读、整理）；我们的 LLM 是操作员兼图书馆员。操作经验只有操作员在实践中才能产生。

**三个机制**：

**A. Operational Narratives（操作叙事）**：`docs/operational_narratives.md`

不是规则列表，而是完整的操作故事。格式："尝试 A → 失败因为 X → 尝试 B → 失败因为 Y → 最终方案 C，关键约束是 Z。"

触发条件：操作经历了 ≥2 次失败后成功时。ROI 导向——不为每个操作都写。

**B. Context Priming Blocks（上下文启动块）**：CLAUDE.md 热区

≤5 行的"工具手感"描述。不是规则，而是帮助新会话快速"住进"工具环境的启动文字。

**C. Pattern Names（命名模式）**

给反复出现的操作流赋予名字 + 一句 origin story。命名本身是 Polanyi 的 focal integration——把分散的 subsidiary awareness 整合为可引用的整体。

### Pillar 4: Timeline + Infrastructure

**log.md（时间线）**：append-only，每次关键事件一行。

```
## [YYYY-MM-DD] type | description
```

Type 枚举（可扩展）：`milestone` / `decision` / `debug` / `deploy` / `debate` / `system` / `friction` / `meta` / `contradiction` / `validation`

> 注意 `friction` 和 `meta` 是 v2.0 新增的进化引擎类型——见下节。

**_canon.yaml（规范值 SSoT）**：

```yaml
system:                              # 跨项目通用
  principles_count: 13               # W1-W12（十三原则）
  principles_label: "十三原则"
  wiki_page_types: [entity, concept, operations, analysis, craft]
  lint_dimensions: 23                # L0-L22 (current substrate)
  claude_md_max_lines: 300
  stale_patterns: ["五原则", "六原则", "七原则"]  # 已知过时表述

architecture:
  layers: 4                          # L1 + L1.5 + L2 + L3
  wiki_pages: 0                      # 初始为 0，按需创建

project:                             # 项目特有
  name: "My Project"
  phase: "Phase 2"
  # ... 项目特定的数字、名称、阈值
```

**lint_knowledge.py（自动化 Lint）**：

对照 _canon.yaml 检查全局一致性。建议检查维度（按项目裁剪）：
1. L0 Canon 自检（_canon.yaml 完整性）
2. L1 引用完整性（索引的文件是否存在）
3. L2 数字一致性（关键数字与 canon 对照 + stale pattern 检测）
4. L3 过时模式（搜索已知 stale patterns）
5. L4 孤儿文档（未被索引的页面）
6. L5 log.md 覆盖度
7. L6 日期一致性
8. L7 Wiki W8 格式一致性
9. L8 .original 同步检查（v2.5，检查双层架构时间戳）

**compress_original.py（v2.5 压缩脚本）**：

将人类编写的 `.original.md` 文档自动压缩为 Agent 优化版。压缩规则：去冗余空行、列表转表格、段落去重，同时保护代码块/数字/URL/公式等不可压缩区域。含验证功能确保关键信息不丢失。

---

## 自进化引擎（Evolution Engine）

**核心理念**：系统不仅存储知识，还持续改进自身。进化不是独立模块，而是贯穿整个工作流的元能力。

**理论根基**：

- **Toyota PDCA**：Plan → Do → Check → Act 循环
- **Argyris 双环学习**：Single-loop 改行为（修改文档内容），Double-loop 改假设（质疑架构设计）
- **Voyager 技能库**：从经验中提取可复用模式，越用越强
- **ERL（2025）**：失败启发式比成功启发式更有价值

### 四个齿轮

```
Gear 1 (每次会话)          Gear 2 (每次会话结束)
  Friction Sensing     →     Session Reflection
  记录操作摩擦点              回答"系统哪里可以改进？"
       │                            │
       ▼                            ▼
Gear 3 (每个里程碑)          Gear 4 (项目结束)
  Milestone Retrospective →  Cross-Project Distillation
  审视累积的 friction/meta      萃取通用模式，更新模板
  质疑架构假设 (Double-loop)
```

#### Gear 1: Friction Sensing（摩擦感知）

**频率**：每次会话中，实时。
**类比**：Toyota Andon Cord——生产线工人拉绳停线报告异常。
**机制**：Agent 在操作中遇到不顺畅时，追加一行到 log.md：

```
## [2026-04-07] friction | 部署文件到 HPC 花了 20 分钟试错四条路径
```

**触发条件**（门槛故意设低——宁可多记不可漏记）：
- 一个操作花费时间 > 预期的 2 倍
- 需要查阅 > 1 个文档才能完成一个本应简单的操作
- 文档描述与实际行为不一致
- 重复手动执行了一个应该被脚本化的操作
- "差点犯错"的操作——即使最终做对了，但中间犹豫
- 信息需要"翻找"——知道答案在系统里但不能一步定位

**与 Operational Narratives 的关系**：friction 是轻量级记录（一行），叙事是重量级（完整故事）。同类 friction 累积 ≥3 次 → 升级为需要写叙事或修改流程。

#### Gear 2: Session Reflection（会话反思）

**频率**：每次会话结束时。
**类比**：Argyris Single-loop Learning——检查行为是否符合目标。
**机制**：在执行会话结束清单时，增加一个必答问题：

> "这次会话中，系统本身（不是项目内容）有什么可以改进的？"

回答追加到 log.md：

```
## [2026-04-07] meta | 发现脚本索引不完整——17 个脚本只索引了 7 个
```

**重要区分**：这里反思的是**系统**而非**项目**。不是"这个实验参数应该调一下"，而是"文档索引机制是否有效"、"知识获取模式是否覆盖了实际需求"。

#### Gear 3: Milestone Retrospective（里程碑回顾）

**频率**：每个项目里程碑后（Phase 转换、重大交付、截止日期）。
**类比**：Argyris Double-loop Learning——质疑 governing variables。
**机制**：回顾自上一个里程碑以来累积的所有 `friction` 和 `meta` 条目，回答三个问题：

1. **假设审查**："哪个架构假设在这个阶段被违反了？"
   - 例：ASCC 中假设"P4 进度只需记录在热区"——实际在三处记录了三个不同值
2. **摩擦聚类**："哪类操作产生了不成比例的摩擦？"
   - 例：HPC 部署操作占了全部 friction 的 60%
3. **重新设计**："如果重新设计这个阶段，我会改变什么？"
   - 例：应该从一开始就建立 _canon.yaml 而不是在发现漂移后才补建

**产出**：不是修补文档（那是 Single-loop），而是修改 WORKFLOW.md 的原则、调整 CLAUDE.md 的架构、新增/拆分 wiki 页面、甚至修改进化引擎自身的规则。

**⚠️ 修改权限分级**：

| 可修改对象 | 权限 | 说明 |
|-----------|------|------|
| Wiki 内容、log 条目、_canon 数字 | ✅ Agent 自主 | 低风险，错了容易回滚 |
| WORKFLOW.md 原则、CLAUDE.md 架构 | 🛑 需人类确认 | 高风险，错误会影响后续所有会话 |
| 进化引擎自身的规则 | 🛑 需人类确认 | 最高风险——自我修改的元规则 |

> **Design Rationale**: 防止自进化变成自腐化。类比操作系统的内核态 vs 用户态——核心原则是内核态，只有人类可以 commit。

#### Gear 4: Cross-Project Distillation（跨项目蒸馏）

**频率**：项目结束时。
**类比**：Senge 系统思维——从单一经验中提取可迁移的模式。
**机制**：

1. 回顾项目完整的 log.md 演进历史
2. 识别哪些 Pattern Names 在其他项目中也有价值
3. 哪些 wiki 页面类型在实践中最有用 vs 哪些从未被创建
4. 哪些原则被频繁违反（说明原则不实用或表述不清）
5. 更新本模板（reusable_system_design.md）

**ASCC v1 → v2 蒸馏实例**：
- 发现 _canon.yaml 需要分 system/project 两节 → v2 模板更新
- 发现 CLAUDE.md 80 行 vs 300 行取决于使用场景 → v2 新增分级模板
- 发现缺少 Double-loop 机制 → v2 新增 Gear 3
- 发现 friction 记录门槛太高 → v2 新增 Gear 1

### 进化引擎与工作流的集成

进化引擎不是独立运作的——它嵌入在现有工作流中：

```
[会话开始]
  1. 自动加载 CLAUDE.md
  2. 读 log.md 最后 10 行（包含 friction/meta 条目）

[工作进行中]
  3. W1 即时沉淀（正常知识流动）
  4. Gear 1: 遇到摩擦 → 记录 friction 条目

[会话结束]
  5. 标准结束清单（更新任务队列、log.md、进度）
  6. Gear 2: 回答 meta-reflection 问题（1 句话）

[里程碑节点]
  7. Gear 3: 架构回顾（回答三个 Double-loop 问题）
  8. 必要时修改 WORKFLOW.md / CLAUDE.md 架构（需人类确认）

[项目结束]
  9. Gear 4: 蒸馏通用模式，更新本模板
```

---

## 项目 Bootstrap 指南

### Level 0: 快速启动（5 分钟）

适用于小型项目、探索性工作。

```
mkdir my-project && cd my-project
创建 CLAUDE.md（Minimal 版，~50 行）
创建 log.md（第一行：## [日期] milestone | 项目启动）
```

仅此两个文件。wiki/ 和 WORKFLOW.md 等到需要时再创建。

### Level 1: 标准启动（30 分钟）

适用于多周期项目（会话数 > 5）。

```
在 Level 0 基础上：
创建 docs/WORKFLOW.md（从本模板裁剪，保留适用的原则）
创建 wiki/（第一个页面在首次需要时创建）
创建 _canon.yaml（project: 节）
```

### Level 2: 完整启动（2 小时）

适用于长期/复杂项目（如学术论文、大型软件项目）。

```
在 Level 1 基础上：
CLAUDE.md 升级为 Full 版（~300 行）
创建 docs/operational_narratives.md（首次 ≥2 失败后填充）
复制并适配 scripts/lint_knowledge.py
创建 _canon.yaml（含 system: + project: 两节）
在 WORKFLOW.md 中启用进化引擎（四个齿轮全部激活）
```

### Bootstrap 后的自然生长

不要预建空页面或空机制。让系统在实践中有机生长：

| 信号 | 动作 |
|------|------|
| 同一个 Bug 出现第 2 次 | 创建 wiki/known_bugs.md |
| 需要对外部文献做萃取 | 创建第一个技法页 |
| 同类 friction ≥3 次 | 写操作叙事或修改流程 |
| 关键数字出现漂移 | 在 _canon.yaml 中添加该数字 |
| 达到项目里程碑 | 执行 Gear 3 里程碑回顾 |

---

## 项目类型适配指南

系统的通用机制可以适配不同类型的项目。关键差异在于**传统手艺的触发信号**和 **wiki 页面类型**。

| 项目类型 | 传统手艺触发 | 常用 Wiki 页面 | 推荐 Level |
|---------|-------------|---------------|-----------|
| **学术论文** | 论文方向、理论 claim、reviewer 可能的攻击 | 理论框架、论文策略、实验设计、写作技法 | Level 2 |
| **软件产品** | 架构设计、技术选型、用户体验决策 | API 设计、已知 Bug、部署流程、用户反馈 | Level 1-2 |
| **数据分析** | 方法论选择、结论解释、偏差来源 | 数据源、分析方法、可视化规范 | Level 1 |
| **学习计划** | 学习路径、资源评估 | 知识图谱、进度追踪 | Level 0-1 |
| **创业项目** | 商业模式、融资策略、产品定位 | 市场分析、竞品对比、用户画像 | Level 1-2 |

---

## 与参考系统对比

| 维度 | 本系统 v2.0 | 纯 CLAUDE.md | Karpathy Wiki | Cursor Rules | Voyager |
|------|------------|-------------|---------------|-------------|---------|
| 索引/内容分离 | ✅ 四层 | ❌ 单文件 | ✅ Index+Pages | ❌ 单文件 | ❌ 无索引 |
| 隐性知识 | ✅ Experience Layer | ❌ | ❌ | ❌ | ⚠️ 仅代码层 |
| 自动一致性检查 | ✅ Lint + SSoT | ❌ | ❌ | ❌ | ❌ |
| 深度决策机制 | ✅ 传统手艺 | ❌ | ❌ | ❌ | ❌ |
| 自进化引擎 | ✅ 四齿轮 | ❌ | ❌ | ❌ | ⚠️ 技能库增长 |
| Double-loop | ✅ Gear 3 | ❌ | ❌ | ❌ | ❌ |
| 分级复杂度 | ✅ L0/L1/L2 | ❌ | ❌ | ⚠️ 文件拆分 | ❌ |
| 跨项目复用 | ✅ 模板+蒸馏 | ❌ | ✅ 通用方法 | ⚠️ 社区共享 | ❌ |

---

## 演进历史

| 版本 | 日期 | 关键变化 |
|------|------|---------|
| v1.0 | 2026-04-07 | 三支柱架构（Schema/Knowledge/Experience）+ Lint，从 ASCC 实践提炼 |
| v2.0 | 2026-04-07 | +第四支柱（Timeline+Infra 独立）、+进化引擎（四齿轮）、一般化（去 ASCC 专属）、分级 Bootstrap、项目类型适配、_canon 分 system/project |
| v2.1 | 2026-04-07 | +知识质量机制（来自 Nuwa-Skill/Caveman 调研）：Wiki 标准模板(W8)、活跃张力标记(W9)、外部知识编译协议(W10)、验证范围标签(W11)、信息密度感知(W12)、log.md 新增 contradiction/validation 类型。路线图新增 v2.5(.original 双层)/v3.0(表达 DNA) |
| v2.1+ | 2026-04-07 | **首次 Gear 3 实战** + v2.5 前置工具就绪。详见下方实战经验回写。 |

---

## ASCC 实战经验回写（Gear 3 → 通用化）

> 以下发现来自 ASCC 项目首次 Gear 3 里程碑回顾（P4 中期），已泛化为通用建议。

### 发现 1：文档一致性漂移是最大摩擦源

ASCC 中 40% 的摩擦来自"先改内容，后（或忘记）更新索引"。根因是操作顺序反了。

**通用对策**：Wiki 创建清单协议（已写入 WORKFLOW.md 模板）。每新建 wiki 页面，强制先更新索引（CLAUDE.md + _canon.yaml），再写内容。"索引先行"违反直觉但有效防止遗忘。

### 发现 2：进化引擎需要刻意激活

ASCC 中 Gear 1 friction 条目 = 0（首次 Gear 3 发现时），说明引擎存在于文档中但未活在工作流中。原因：friction 触发门槛设得太高（"花费 > 预期 3 倍"），日常微摩擦全被过滤了。

**通用对策**：门槛降低至"差点犯错"和"需要多想一步"级别。宁可多记（一行成本可忽略），不可漏记（摩擦数据缺失导致 Gear 3 分析失效）。

### 发现 3：模板必须经过 dry-run 才可声称"可用"

project_template 在 ASCC 之外从未被测试过。声称通用但缺乏验证。

**通用对策**：每次修改模板后，用一个假想的非当前类型项目做 Level 0 → Level 1 bootstrap 心智模拟。检查：是否有项目特有假设泄漏？占位符是否清晰？

### v2.5 前置工具就绪状态

| 工具 | 状态 | 说明 |
|------|------|------|
| `scripts/compress_original.py` | ✅ 原型就绪 | 6 条压缩规则 + 保护区域 + 验证功能 |
| `lint_knowledge.py` L8 | ✅ 已集成 | .original 时间戳差异检测 |
| `.original.md` 工作流 | ⏳ 待实战 | 需要在一个真实文档上验证完整流程 |

**v2.5 启动条件**：选一个现有 wiki 页面，创建其 `.original.md` 版本，验证 compress → lint → 编辑 → 重新 compress 的完整闭环。

---

*本文档本身遵循 Gear 4（Cross-Project Distillation）——每个使用本系统的项目结束时，都应将新发现回写到此处。*
