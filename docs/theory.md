# Myco 理论基础

> 文档状态：[ACTIVE] | 版本：v0.1 | 创建：2026-04-09
> 基于：4 轮在线文献调研 + 2 轮传统手艺辩论

---

## 一、Myco 是什么——核心定义

**Myco 是可自进化的 AI 延伸认知基质（Self-Evolving Extended Cognitive Substrate for AI Agents）。**

这个定义由两个支柱构成：

**支柱一：延伸认知（Extended Cognition）**
来自 Clark & Chalmers（1998）的延伸心智论：认知系统不止于大脑/模型内部，外部结构若满足"耦合条件"即成为认知系统的有机组成部分。

> Otto 患有阿尔茨海默症，他随身携带一本笔记本。每当学到新信息就写下来，每当需要旧信息就查阅。对 Otto 而言，笔记本承担了生物记忆通常承担的功能。
> — Clark & Chalmers, *The Extended Mind*, 1998

Myco 之于 AI agent 正是 Otto 笔记本之于 Otto：CLAUDE.md 是自动加载的认知入口（永远可访问），lint + _canon.yaml 保证内容可信赖（不比内部推理更不可靠），分层架构让访问成本极低（自动认可，不需要反复提示）。

**支柱二：自进化（Self-Evolution）**
这是 Myco 超越 Otto 笔记本、超越所有现有 agent 记忆系统的核心贡献。Myco 不只是存储，它通过四齿轮进化引擎持续改善自身：

```
知识代谢（Gear 1/2）→ 架构质疑（Gear 3）→ 跨项目蒸馏（Gear 4）
         ↑                                              │
         └──────────── 更新 bootstrap 模板 ←────────────┘
```

这对应 Argyris（1977）三环学习的工程实现：
- Gear 1（摩擦感知）= 单环：修正具体行为
- Gear 2（会话反思）= 双环：质疑底层假设
- Gear 3（里程碑回顾）= 双环在系统层：挑战架构假设
- Gear 4（跨项目蒸馏）= **三环**：质疑"探究原则本身"，更新所有未来项目的起点

---

## 二、与现有系统的核心差异

### 现有 Agent 记忆系统的共同局限

当前主流系统（MemGPT, A-MEM, RAG + 向量数据库等）解决的是**信息持久化问题**——如何让 agent 在下一次对话时还记得上一次的内容。这是必要的，但只覆盖认知需求的第一层。

### 四层认知需求模型

| 层次 | 问题 | 现有系统 | Myco |
|------|------|---------|------|
| **L1 记忆** | 记住了什么？ | ✅ MemGPT, A-MEM, RAG | ✅ 四层知识架构 |
| **L2 质量** | 知识是否一致、准确、未腐烂？ | ❌ 无机制 | ✅ Lint + _canon.yaml + 生命周期标签 |
| **L3 经验** | 操作摩擦/失败路径是否被捕获？ | ❌ 仅 semantic 事实 | ✅ Friction log + Operational narratives |
| **L4 进化** | 认知基础设施本身是否在改进？ | ❌ 架构固定 | ✅ Gear 3/4：架构自进化 + 跨项目蒸馏 |

### 具体对比

**vs. MemGPT（2023）**：MemGPT 以操作系统分页为隐喻，将信息在上下文窗口（主存）和外部存储（磁盘）之间调度。这是**IO 层优化**——它让 agent 能处理更长的上下文，但不改变知识的质量，不捕获操作经验，不进化自身架构。Myco 和 MemGPT 不在同一个问题层次上。

**vs. A-MEM（2025）**：A-MEM 实现了"主动改善自身记忆"——对存储的语义记忆进行整合和优化。这触及 L2 的边缘，但仍然局限于**单个 agent 实例的语义记忆**。A-MEM 无法捕获 Polanyi 意义上的隐性操作知识（"使用错误的二进制工具会导致静默失败"），也没有跨项目蒸馏机制。

**vs. Obsidian / Zettelkasten**：这些是为**人类**设计的知识管理系统，缺少 agent 自动写入、lint 验证、bootstrap 协议、和进化引擎。它们是静态图书馆，Myco 是活的代谢网络。

**vs. 向量数据库 + RAG**：RAG 解决的是**检索精度**问题，不是认知架构问题。它没有知识质量控制，没有经验显性化，没有进化机制。

---

## 三、Myco 解决的核心认知问题

### 问题一：持久性断裂（Persistent Discontinuity）
LLM agent 天生无状态——每次会话是一张白纸。现有记忆系统修复了"记住了什么"，但没有修复"学会了什么"（经验）和"进化了什么"（架构改进）。

### 问题二：隐性知识流失（Tacit Knowledge Erosion）
Polanyi（1966）："我们能知道的比能说出来的多。" AI agent 在操作中积累的经验——哪条路通，哪条路会踩坑，哪种操作模式可靠——大量以隐性形式存在于对话流中。每次新会话，这些知识全部消失，agent 从零开始重新踩坑。Myco 的 Friction log + Operational narratives 是专门把这类隐性知识**显性化**的机制。

### 问题三：知识腐烂（Knowledge Decay）
随时间推移，外部文档会与实际系统状态产生 drift：过时的配置、被废弃的协议、不再准确的数字。现有系统没有检测机制。Myco 的 lint（尤其 L0-L3 维度）+ _canon.yaml SSoT + 生命周期标签（ACTIVE/COMPILED/SUPERSEDED）系统性地应对知识腐烂。

### 问题四：迁移损耗（Transfer Loss）
每个新项目都从零开始积累操作经验。即使同一个 agent 在多个项目上工作，各项目的学习也是孤立的。Myco 的 Gear 4 通过跨项目蒸馏，将个别项目的经验提炼为通用 bootstrap 模板，实现知识的**跨域迁移**。

---

## 四、与认知科学的理论对应

| Myco 机制 | 认知科学理论 | 对应关系 |
|-----------|-------------|---------|
| 四层知识架构（L1-L4） | Tulving（1985）情节/语义记忆区分 | L3 Code ≈ 程序性记忆；L1.5 Wiki ≈ 语义记忆；L0 Archive ≈ 情节记忆 |
| Friction log + Operational narratives | Polanyi（1966）隐性知识 | 将隐性操作知识显性化的正式机制 |
| Gear 1-4 四齿轮进化引擎 | Argyris & Schön（1978）双环/三环学习 | Gear 1/2 = 单/双环；Gear 3 = 系统层双环；Gear 4 = 三环 |
| 整体架构 | Clark & Chalmers（1998）延伸心智论 | Myco 是满足 Otto 条件的 AI 延伸认知系统 |
| Bitter Lesson 立场 | Sutton（2019）；元学习理论 | W1-W12 是合法的 bootstrap 热启动，终极目标是被系统发现的规则取代 |

---

## 五、核心主张（Claims）

**C1（本质）**：Myco 是可自进化的 AI 延伸认知基质——第一个在工程层面实现三环学习的 agent 认知外部化系统。

**C2（差异）**：现有 agent 记忆系统（MemGPT, A-MEM, RAG）解决"记住了什么"；Myco 解决"知识质量、操作经验显性化、认知架构自进化"这三个更高层次的问题。

**C3（普遍性）**：Myco 的架构是 agent-agnostic 的——它不依赖特定模型或工具，任何具备上下文读取能力的 agent 都可以从 Myco 受益。

**C4（可验证性）**：Myco 的效果可以通过具体指标验证：跨会话知识一致性（lint pass rate）、操作经验复用率（pattern复用数）、跨项目 bootstrap 时间缩短。

---

## 六、开放张力（Active Tensions）⚡

⚡ **T1：手工规则 vs. Bitter Lesson**
W1-W12 是手工制定的规则。Sutton 的 Bitter Lesson 认为手工规则终将被学习到的规则超越。Myco 的立场是：W1-W12 是"合法的 bootstrap 热启动"——基于实战蒸馏的初始化，不是终态。但如何在实践中推进这个过渡，是 v1.0+ 的核心问题。

⚡ **T2：显性化 vs. 表达损耗**
将隐性知识显性化是 Myco 的核心目标之一，但 Polanyi 的洞察也指出：显性化必然伴随损耗（the act of articulation changes what is articulated）。如何在 operational narratives 中最大程度保留原始摩擦的全貌，而不是过度抽象化？

⚡ **T3：通用性 vs. 深度**
Myco 声称是 agent-agnostic 的通用框架，但目前只在一个项目上验证。通用性主张需要至少 3 个不同类型项目的实战验证才能成立。

---

## 七、参考文献

- Clark, A., & Chalmers, D. (1998). The Extended Mind. *Analysis*, 58(1), 7-19.
- Argyris, C., & Schön, D. (1978). *Organizational Learning: A Theory of Action Perspective*. Addison-Wesley.
- Polanyi, M. (1966). *The Tacit Dimension*. Doubleday.
- Packer, C., et al. (2023). MemGPT: Towards LLMs as Operating Systems. *arXiv:2310.08560*.
- Xu, et al. (2025). A-MEM: Agentic Memory for LLM Agents. *arXiv:2502.12110*.
- Sutton, R. (2019). The Bitter Lesson. *Incomplete Ideas (blog)*.
- Liu, S., et al. (2024). Memory in the Age of AI Agents. *arXiv:2512.13564*.
- Weger, U., et al. (2025). Extending Minds with Generative AI. *Nature Communications*.
