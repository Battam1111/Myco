# 传统手艺：B6 发布策略辩论
> **Status**: ARCHIVED (compiled to formal docs)
> 日期：2026-04-10 | 类型：launch-strategy | 状态：[ARCHIVED]
> 前置：brand_craft（B2 ✅），B5 ✅，Task 9 B6
> 目标：确定首发渠道、首发文案、冷启动策略

---

## 在线调研结果（Research Phase，2026-04-10）

### 调研 1：HN Show HN 成功模式
**来源：** bestofshowhn.com/2026, Hacker News trends 2025-2026

关键发现：
- 成功的 Show HN 工具共同点：**解决开发者真实痛点**（而非展示技术）
- "Claude Reflect" 类工具（自动将 Claude 修正转化为项目配置）获得了高度关注——与 Myco 价值主张高度相似
- 最成功的 AI 工具强调：local-first、无需账号/API 订阅、实际用例数据

### 调研 2：r/LocalLLaMA 社区特点
**来源：** agentsindex.ai, gummysearch r/LocalLLaMA 分析

关键发现：
- **266,500+ 成员（2026）**，以实践者为主
- 社区规则：**"punish hype"**（惩罚炒作）——空洞的 AI 产品会被直接无视
- 高互动帖子特征：技术深度 + 真实数据 + 解决具体问题 + 作者亲自互动回答问题
- "Agent Manifest" 类概念（结构化 agent 知识规范）已引起讨论
- 反感：付费墙、需要账号、仅展示不开源

---

## Round 1：首发渠道——同时多渠道 vs 单渠道冷启动

### 主张（多渠道同时）
HN + Reddit + Twitter/X 同时发布，最大化曝光：
- HN Show HN → 技术社区
- r/LocalLLaMA → AI agent 实践者
- Twitter/X → 快速传播

### 攻击
多渠道同时发布的问题：
1. 需要为每个渠道定制内容，稀释精力
2. 如果任何一个渠道初始反应不好，会损害其他渠道的第一印象（同步通知）
3. **Show HN 规则**：同一个项目不能在短期内重复提交，首次提交质量至关重要
4. r/LocalLLaMA 对"promotional post"有明确限制，需要深度技术内容

### 研究/证据（调研数据综合）
分析成功开发者工具的发布序列：
- **最佳实践**：HN Show HN 先行（技术精英社区，早期采用者密度最高），Reddit 次之（更广泛实践者），Twitter 同步辅助
- **时间窗口**：HN 工作日早上 9-11 点（美国东部时间）是最高流量时段
- **冷启动核心**：第一批 5-10 个用户的真实反馈 > 曝光量。找到能立刻说"这解决了我的问题"的用户。

### 辩护
**发布序列（确定）：**
1. **Week 0**：软发布——在 1-2 个 Claude Code 相关讨论帖（HN/Reddit）中自然提及 Myco，获得第一批有机用户和反馈
2. **Week 1**：**Show HN**（主发布）——周二上午发布，专注于"我用这个工具管理了一个 80+ 文件的研究项目，给你看看"
3. **Week 1-2**：r/LocalLLaMA + r/ClaudeAI — 发布深度技术帖（"How I built a self-evolving knowledge system for my AI agent"）
4. **Month 1**：Twitter/X 转发来自社区的 battle reports

**置信度：86%**

---

## Round 2：首发文案——技术深度 vs 用户故事

### 主张（技术深度）
HN Show HN 文案：
```
Show HN: Myco – Give your AI agent metabolism, not just memory

Most "AI memory" tools store information. Myco asks: is that information still true?
myco lint catches contradictions before they become bugs.
```

### 攻击（研究数据支持）
r/LocalLLaMA 数据：**高互动帖子 = 具体问题 + 作者自己踩坑的故事**。"我遇到了这个问题，花了两小时才发现 agent 在会话间产生了矛盾"比"Myco catches contradictions"更有说服力。

HN 规则：Show HN 帖子最好是 40-60 词，说清楚"什么"，不是"为什么"。"为什么" 留给评论区。

Mem0 2026 报告直接写道 "memory staleness detection is an unresolved challenge" ——这是**第三方验证**，在帖子中引用比自夸更有力。

### 研究/证据（在线调研综合）
成功的 Show HN 帖格式分析：
- **标题**：Show HN + 项目名 + 一句话核心功能（不夸大）
- **正文**：问题 → 我做了什么 → 现在能做什么 → 链接
- **不包括**：竞品比较（留给评论区回答）、夸大数据
- **关键 hook**：用你自己使用的真实数据（"80+ 文件，15+ 次辩论，Gear 4 完成"）

### 辩护
**最终首发文案（Show HN）：**

```
标题：
Show HN: Myco – lint checks for your AI agent's knowledge (catches stale assumptions)

正文（60词）：
I spent 8 days using Claude Code on a 80+ file research project. After day 3, 
the same metric appeared in three places with three different values. Nobody caught it.

Myco adds a knowledge layer to any project: wiki pages, canonical values, and 
9 lint checks that flag inconsistencies across sessions. pip install myco.

The memory staleness problem is real (Mem0's 2026 report names it explicitly). 
This is my attempt at a structural solution.
```

**r/LocalLLaMA 帖文案（周后发布，更长）：**

```
标题：
How I built a self-evolving knowledge system that catches AI agent contradictions 
across sessions (and open-sourced the framework)

核心结构：
- Day 3 真实事件（三处不一致的 metric）
- 系统如何运作（lint + canon + wiki）
- 8 天 80+ 文件 Gear 4 案例数据
- 与 Mem0/OpenClaw 的关系（补充，不竞争）
- "如果你用 CLAUDE.md：myco migrate 5 分钟内"
```

**置信度：88%**

---

## 最终决议（综合置信度 87%）

### 发布时间线

| 时间 | 行动 | 渠道 |
|------|------|------|
| W0 | 确认仓库 Public，确认 pip install myco 成功 | — |
| W1 周二 10AM ET | **Show HN 主发布** | Hacker News |
| W1 周四 | 深度技术帖 | r/LocalLLaMA |
| W1 周五 | Claude Code 用户帖 | r/ClaudeAI |
| W2+ | 收集第一批 battle reports，转发社区反馈 | Twitter/X |
| M2 | 第二波：根据早期反馈改进后再次发布 | HN/Medium |

### 首发文案（存档）

已内嵌在本文 Round 2 辩护部分（Show HN + r/LocalLLaMA 两版）。

### 冷启动种子用户
在 Show HN 前：找 3-5 个 Claude Code 重度用户私下试用，让他们在帖子发布后第一时间留下真实评论（不是"great job"，而是"遇到了 XYZ 问题，lint 发现了它"）。这是 HN 评论区启动的关键。

### 常见问题预案
| 问题 | 回答方向 |
|------|---------|
| "这和 CLAUDE.md 有什么区别？" | CLAUDE.md 是存储，Myco 是 CLAUDE.md 的验证和进化层 |
| "为什么不用 Mem0？" | Mem0 做检索，Myco 做一致性检验。互补，不竞争 |
| "这需要我改变工作流吗？" | `myco migrate` 5 分钟，非破坏性，CLAUDE.md 原样保留 |
| "只支持 Claude 吗？" | v1.0 已支持 Cursor/GPT/Hermes/OpenClaw，agent-agnostic |
| "有什么可视化工具吗？" | 目前纯 CLI，v1.2 计划 myco dashboard |

---

*传统手艺结束。综合置信度 87% ≥ 85% 阈值。*
*在线调研来源：bestofshowhn.com/2026 | agentsindex.ai/r-localllama | mem0.ai/blog/state-of-ai-agent-memory-2026*
