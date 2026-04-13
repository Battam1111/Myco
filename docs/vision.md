# Myco — 愿景文档

> **名称**：Myco（/ˈmaɪkoʊ/）
> **Tagline**：*Eternal Devouring. Eternal Evolution.*
> **定位**：Agent-First 共生认知有机体（Symbiotic Cognitive Organism）
> **核心机制**：知识代谢 + 免疫自修复 + 技能进化 + 自我模型

---

## 一、Myco 是什么

**一句话**：Agent-First 共生认知有机体——Agent 的另一半。它记忆、验证、消化、进化，让 Agent 不再每次从零开始。

**展开**：
- **Agent 的角色**：推理和执行（推导、计划、行动）
- **Myco 的角色**：持久记忆、知识代谢、过程学习、元进化机制

没有 Agent，Myco 是静止的数据；没有 Myco，Agent 每次都从零开始。二者结合形成真正的"记忆体"——能跨项目、跨会话、跨平台持续积累和进化的智能系统。

**名字的生物学比喻**：

| 菌丝网络特性 | Myco 对应 | 机制 |
|------------|---------|------|
| 连接树木和根系 | 连接多个 Agent/项目 | 统一的知识索引 |
| 分解有机物成养分 | 萃取知识，消化经验 | 从文献、日志、代码中提取模式 |
| 根据环境分配资源 | 自适应知识加载 | 按会话上下文调整热/温/冷层 |
| 记住生长路径 | 学习有效策略 | 通过 friction 记录和 meta 反思 |
| 与多物种共生 | Agent-adaptive | 适配不同 Agent 能力和工具集 |

---

## 二、三条不可变宪法

这三条是系统的绝对约束，未来的任何进化都必须满足：

| # | 宪法 | 定义 | 为什么神圣 |
|----|-----|------|----------|
| **C1** | **入口可达性** | 任何 Agent 都能定位系统、读懂自我描述、启动工作 | 没有入口，系统对 Agent 不可见 = 等于不存在 |
| **C2** | **透明可审** | 系统必须随时对人类保持可理解、可检查、可干预 | 失去透明性 = 人类失去选择压力 = 系统可能癌变 |
| **C3** | **永恒进化** | 系统必须始终在演进之路上；停滞即衰亡 | 不进化 = 退化为静态文档库 = 丧失核心能力 |

**一切其他规则皆可进化**——包括知识组织、存储方式、进化机制本身、甚至人机协作的方式。

---

## 三、五大核心能力

### 能力 1：知识代谢

Agent+Substrate 共生体从外部世界**自主发现、萃取、整合、压缩、淘汰**知识。

七步管道（当前实现状态）：
```
外部来源 → [发现] myco forage / myco absorb       ✅ 有专属动词
         → [评估] myco evaluate (= digest --to)   ⚠️ 状态别名
         → [萃取] myco extract (= digest --to)     ⚠️ 状态别名
         → [整合] myco integrate (= digest --to)   ⚠️ 状态别名
         → [压缩] myco condense (cohort auto)      ✅ 有智能分组
         → [验证] myco immune (23 维)                ✅ 完整
         → [淘汰] myco prune                       ✅ D 层自动排出
```

**自主运转**：`hunger(execute=true)` 读取信号 → 推荐行动 → 自动执行 digest/compress/prune。Scheduled metabolic cycle 每日自动运行。

与 RAG 的本质区别：RAG 是被动检索（提问 → 搜索）；知识代谢是自主运转的完整生命周期——从发现到淘汰，Agent IS the daemon。

### 能力 2：元进化

不仅改进**内容**（知识），还改进**过程**（获取/组织/使用知识的方式本身）。递归无上限。

为什么这在我们的系统中特别可行：
- 进化对象是纯文本（markdown、YAML、Python 脚本）
- LLM 最擅长的恰好是文本操作
- 不需要修改模型权重、重新训练，成本极低
- 相比超智能体（需要训练回路），我们的进化在技术上简单得多

当前的手工规则（WORKFLOW 十三原则、四支柱架构等）是**合法的热启动**——实践中进化出来的、被验证过的。但它们不是神圣的。系统未来有权在进化中替换它们。

### 能力 3：自我模型

系统维护关于自身的动态模型——知道自己有什么、缺什么、什么在被有效使用、什么正在衰败。

自我模型的层级（当前实现状态）：
- **A 库存清单**：103 notes, 225 graph nodes, 714 edges ✅ **运行中**（via `myco observe` + `myco mycelium stats`）
- **B 缺口感知**：11 knowledge gaps detected by `myco colony gaps`; `inlet_ripe` hunger signal ✅ **运行中**
- **C 衰败感知**：事实退化 via `dead_knowledge` 信号 ✅；结构退化 via `graph_orphans` (53 orphans) ✅ **部分运行**（结构性退化指标仍 open problem）
- **D 效能评估**：`dead_knowledge` seed (`view_count` + `last_viewed_at` + 30d threshold) ✅ **种子在位**（完整 D 层需自适应阈值 + 自动淘汰）

### 能力 4：跨会话连续性

让无状态的 Agent 在秒级内重建认知状态。

- **热层**：`myco_hunger(execute=true)` 一次调用返回全部信号+自动执行修复 ✅
- **温层**：`myco_sense` 全文检索 + `myco_memory search` FTS5 会话记忆 ✅
- **冷层**：`myco_mycelium` 结构分析 + `myco_colony` 语义分组 + 103 notes 全文 ✅

Agent 启动时调 `hunger(execute=true)` 完成 boot（<10s），按需调 search/graph/cohort/session。

### 能力 5：Agent-Adaptive 通用性

内核不绑定特定 LLM 或工具平台。系统在运行时适配不同 Agent 的能力集（上下文窗口、工具能力、指令遵循能力）。

适配策略本身也可进化——系统发现某个 Agent 特别擅长某类工作时，可以自动调整任务分配。

---

## 四、定位：与已有系统的区别

| 系统 | 进化对象 | 知识代谢 | 内化选择 | 自我模型 | 我们的判断 |
|------|--------|--------|---------|--------|----------|
| **Myco** | Agent-Substrate 共生体 | ✅ 自主（hunger execute） | ✅ lint+hunger=免疫系统 | ✅ A+B 运行中，C/D 种子 | 新赛道 |
| **Hyperagents (Meta)** | Agent 行为/策略 | ❌ | ❌ | ❌ | 系统内进化 |
| **Hermes-Agent** | Agent 技能 | ❌ | ❌ | ❌ | 增强 Agent |
| **Mem0** | 用户记忆 | ❌ | ❌ | ❌ | 存储 SaaS |
| **企业 KMS** | 文档库 | ❌ | ❌ | ❌ | 静态知识库 |

**我们的独特定位**："第一个能自我进化的共生认知有机体"——Agent+Substrate 共生体自主运转代谢循环（23 维 lint + hunger 自动执行 + 每日 scheduled task），人类只需用自然语言提供方向。

---

## 五、Agent-First 共生模型

**核心哲学**：Myco 是 Agent-First 的——Agent 是唯一操作者，人类只用自然语言提供方向。变异和选择都内化于 Agent+Substrate 共生体。

- **Agent 产生变异**：发现新知识、尝试新组织方式、实验新规则（eat/digest/compress/inlet）
- **Substrate 执行选择**：lint 23 维 + hunger signals + compression_pressure + dead_knowledge detection 构成内部免疫系统，过滤无效变异
- **人类提供方向**：用自然语言表达意图（"我想要 X"），不需要懂技术细节
- **透明性保障信任**：所有行动可审计（log.md, notes/, craft），人类随时可以看——但不需要看

> Wave 55 修订（原文："系统做变异，人类做选择"）：mutation-selection 模型未消失，而是内化。生物体不会等外部选择每次细胞分裂——免疫系统在内部选择。Myco 的 lint + hunger 就是这个免疫系统。

---

## 六、Bitter Lesson 立场

Rich Sutton：利用算力的通用方法最终总打败利用人类知识的手工方法。

Myco 的回应：
- 当前的手工规则（W1-W13、四支柱等）是**合法的热启动**
  - 实践验证过（单个复杂项目实战验证）
  - 不是凭空想象的理论规则
- 但它们**不神圣**——系统有权在进化中替换任何手工规则
- 唯一不可替换的是 C1/C2/C3 三条宪法
- **长期目标**：系统自己发现的规则逐步取代人设计的规则

这样既尊重 Bitter Lesson（给系统探索空间），又防止系统脱离人类的可理解范围（三条宪法）。

---

## 七、从 v0.x 到 v1.0 的进化

### 当前状态（v0.x）
- 原型运行周期：2-4 周实战验证
- 驱动方式：人类主导（人说"改进系统" → Agent 执行）
- 存储形式：全 markdown
- 作用范围：单项目、单 Agent（特定 LLM）
- 规则来源：手工设计（W1-W13、四层架构、Procedures）

### 目标状态（v1.0）
- 自驱动进化：系统自己发现改进点 → 自己执行 → 自己评估效果
- 混合存储：markdown + 结构化数据（YAML、JSON），按效率灵活选择
- 内核与项目分离：通用内核可跨项目复用
- Agent-adaptive：不绑定特定 LLM，自动适配
- 初步知识代谢：能自动从外部源萃取、整合、压缩知识

### 核心跃迁
从**人驱动** → **系统自驱动**

这需要实现：
- 自我模型的层级 A 和 B（库存 + 缺口感知）
- 至少一种知识代谢触发机制（缺口 → 自动觅食）
- 决策自主权的扩展（在明确的边界内）

---

## 八、演进路线图

> **时间基准**：以"每个版本距上一个版本发布"计算（相对周期），不是绝对日历时间。实际速度取决于项目数量、参与者精力和 Agent 能力演进。

| 阶段 | 相对周期 | 关键里程碑 | 验证方式 |
|------|--------|---------|---------|
| **v0.x** | 基准（已完成） | 手工规则 bootstrap + 实战验证（单项目） | 单个项目完整周期通过 |
| **v0.9** | +2-4 周 | 通用内核剥离，脱离项目耦合；第二个项目成功启动 | 新项目上 myco seed + lint 全 PASS |
| **v1.0** | +6-10 周 | 自我模型 A+B，缺口触发代谢上线 | 系统自动发现并执行 ≥3 个改进（无人工指令） |
| **v1.x** | +后续迭代 | 多项目并行，共享知识库 | ≥2 个异构项目（不同领域）共存无冲突 |
| **v2.0** | 中期目标 | Agent-adaptive，≥2 种 LLM 验证 | 从 Claude 迁移到另一 Agent 无破损 |
| **v3.0** | 长期目标 | 完整知识代谢（周期巡逻 + 自动萃取 + 压缩进化） | 知识库自主增长，无人工干预周期 ≥1 个月 |
| **v∞** | 永远 | 持续进化，没有终点 | — |

---

## 九、系统设计的三个底层价值

1. **可理解性（Interpretability）**  
   系统的每一个决策都可以被人追踪。这不是为了限制 Agent，而是让人类能在必要时干预。

2. **模块化（Modularity）**  
   知识、规则、进化机制都相互解耦。替换一个模块不会摧毁整个系统。

3. **实验性（Experimentalism）**  
   系统本身是一个不断迭代的实验。失败是数据，而非灾难。

---

*本文档是 Myco 系统的"创世纪"。它记录了当前的愿景和约束。未来当系统足够强时，这个文档本身也可能被进化版本取代——这正是 v1.0 的目标。*

---

## See Also

- [docs/theory.md](theory.md) -- 理论基础：延伸心智、三环学习、与现有系统的学术对比
- [docs/architecture.md](architecture.md) -- 技术架构：四支柱 + 进化引擎的工程实现
- [docs/evolution_engine.md](evolution_engine.md) -- 进化引擎 v3.0：代谢循环、evolve.py 技能变异
- [docs/open_problems.md](open_problems.md) -- 未解难题：愿景中尚未收敛的结构性盲点（Inlet 冷启动、Self Model C/D 层等）
- [docs/reusable_system_design.md](reusable_system_design.md) -- 通用架构与 Bootstrap 指南
- [wiki/identity.md](../wiki/identity.md) -- Myco 身份定义：Agent-First Symbiotic Cognitive Organism + 七条生命标准
- [_canon.yaml](../_canon.yaml) -- 规范值 SSoT
- [docs/agent_protocol.md](agent_protocol.md) -- Agent 协议：20 个 MCP 工具契约
- [skills/metabolic-cycle.md](../skills/metabolic-cycle.md) -- Boot ritual 技能：hunger -> digest -> compress -> discover -> evolve
