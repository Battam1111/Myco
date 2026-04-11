# 传统手艺：LLM Wiki Pattern × 我们的知识系统

> **日期**：2026-04-07
> **触发**：Yanjun 分享 Andrej Karpathy 的 LLM Wiki pattern（2026-04-03 GitHub Gist）
> **目标**：评估 LLM Wiki 对 ASCC 项目和可复制系统的价值
> **在线调研**：有限（确认发布时间和社区反响）

---

## 背景

Karpathy（2026-04-03）发布了 LLM Wiki 模式——一种用 LLM 增量构建和维护个人知识库的方法。核心架构：三层（Raw Sources / Wiki / Schema），三操作（Ingest / Query / Lint），两个特殊文件（index.md / log.md）。社区反响大，已有多个开源实现（obsidian-wiki, llm-wiki-compiler）。

来源：
- GitHub Gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- X/Twitter: https://x.com/karpathy/status/2039805659525644595

---

## 第一轮：精确映射

### Karpathy 三层 vs 我们的层级

| Karpathy | 我们的系统 | 对应程度 |
|----------|-----------|---------|
| **Raw Sources**（不可变原始资料） | L0 会话历史（JSONL）+ docs/primordia/（辩论记录） | 部分。我们的"原始资料"是会话对话，不是外部文献 |
| **Wiki**（LLM 维护的结构化知识） | L1 CLAUDE.md + L2 WORKFLOW.md / operational_narratives.md | 部分。但我们的"wiki"只有极少页面，不是互联知识网 |
| **Schema**（LLM 操作配置） | CLAUDE.md 热区 + WORKFLOW.md（六原则）+ SESSION_PROTOCOL.md | 高度对应 |

### Karpathy 三操作 vs 我们的操作

| 操作 | Karpathy | 我们 | 差距 |
|------|---------|------|------|
| **Ingest** | 新文档 → 更新多个 wiki 页面 | 传统手艺 → 写入 CLAUDE.md + docs/primordia/ | 有 ingest，但写入位置靠惯例非协议 |
| **Query** | 读 index → 定位页面 → 综合回答 | 新会话读 CLAUDE.md → 按索引找 L2 | 类似，但 CLAUDE.md 混杂索引和内容 |
| **Lint** | 定期健康检查 | 临时发起的审计 | 有 lint 能力，但不系统化 |

---

## 第二轮：深挖 Karpathy 的核心洞察

### 洞察 1："编译一次，不要每次重新推导"

我们的 CLAUDE.md 确实编译了知识摘要。但**执行模板**（如 HPC 部署脚本）每次仍临时生成。N-001 操作叙事提供了知识但不提供可复用的执行器。

### 洞察 2："好的分析应回流为独立页面"

传统手艺辩论产生了高质量分析（λ 根因调查、RPG 威胁评估），但散落在长文档中。未来查询"λ 为什么不行"需要翻辩论记录而非直接查独立页面。这是我们做得**最差**的环节。

### 洞察 3："Index/Content 分离"

CLAUDE.md ~900 行，同时是 index、log、summary、schema、bug list。违反单一职责。Karpathy 明确分离 index.md（导航）和 log.md（时间线）。

**反驳**：CLAUDE.md 是唯一自动加载文件，必须身兼数职——否则新会话需读多文件。
**再反驳**：如果 CLAUDE.md 只保留索引+schema（~300行），具体内容移到 wiki 页面，context window 利用率更高，反而加速启动。

---

## 第三轮：危险审视——不应照搬的

### 陷阱 1：过度结构化

Karpathy 的模式适合信息密集型场景（100+ 论文）。我们是执行密集型——大部分时间在写代码、调试、部署。过度 wiki 维护违反 NeurIPS 锚点。

### 陷阱 2：Raw Sources 不明确

我们的"原始资料"（实验结果、代码、会话对话）不是 Karpathy 设想的"drop into raw/"然后编译的文件。LLM Wiki 编译管线不太适用。

### 陷阱 3：Obsidian 假设不成立

知识消费者是下一个 Claude 会话，不是人类 Obsidian 用户。Graph view、Dataview 无用。但 index.md 作为导航枢纽非常适合 Claude。

---

## 第四轮：综合——应该和不应该采纳的

### ✅ 应该采纳（高 ROI）

**A. CLAUDE.md 瘦身 + Index/Content 分离**（置信度 ~80%）

当前 ~900 行 → 目标 ~300 行。将具体内容移到 wiki/ 目录下的独立页面：
- §5 Bug 列表 → wiki/known_bugs.md
- §8 理论框架 → wiki/theoretical_framework.md
- §9/9A/9.5 论文策略 → wiki/paper_strategy.md
- §10 实验设计 → wiki/experiment_design.md

CLAUDE.md 只保留：热区（当前状态 + schema + 任务队列）+ 精简的文档索引表。

**B. Lint 系统化**（置信度 ~85%）

纳入 WORKFLOW.md 作为 W5 的具体执行：每次长会话结束前或每 3 次会话后，跑一次 lint pass（检查过时引用、数字一致性、孤儿文档、缺失交叉引用）。

**C. 增加 log.md（append-only 时间线）**（置信度 ~75%）

记录：传统手艺完成时间、关键决策时间、阶段完成时间。任务队列只保留当前状态，log.md 保留完整历史。

### ✅ 应该改造后采纳（中 ROI）

**D. 传统手艺结论萃取**（置信度 ~70%）

辩论结束后，除完整记录外，萃取 1-2 段结论卡片写入 CLAUDE.md 或 wiki 索引页。降低未来查询成本。

### ❌ 不应该采纳（低 ROI 或不适用）

**E. 完整 wiki 编译管线**（置信度 ~80%）：知识主要来自内部实践，不是外部文献
**F. Obsidian/qmd 工具链**（置信度 ~90%）：消费者是 Claude 会话，不是人类

---

## 第五轮：超越 ASCC——可复制系统

### 核心洞察：两种解法，同一个问题

问题：如何让 LLM agent 跨会话保持知识？

- **Karpathy 的解法（信息架构驱动）**：结构化 wiki + index + lint
- **我们的解法（实践架构驱动）**：session protocol + 操作叙事 + proximal enrichment

两者互补。Karpathy 解决了显性知识的组织问题，W6 解决了隐性知识的传递问题。

### 可复制系统的三个支柱

1. **Schema Layer**（Karpathy schema + 我们的 WORKFLOW.md）：元协议——告诉 agent 如何操作
2. **Knowledge Layer**（Karpathy wiki + 我们的 L1/L2）：结构化知识库——持久化、可检索
3. **Experience Layer**（我们的 W6 独有）：操作叙事、失败路径、工具手感——这是 Karpathy 体系中缺失的

### "编译" vs "沉淀"两种模式

- **编译模式**（Karpathy Ingest）：有新外部输入时，LLM 编译为 wiki 页面——批处理
- **沉淀模式**（我们的 W1）：agent 操作中发现新知识时，即时写入——流式处理

**可复制系统应同时支持两种模式。**

### Experience Layer 为什么是独有的

Karpathy 的 LLM 是**图书馆员**——读、整理、索引。不做事，不踩坑。
我们的 LLM 是**操作员兼图书馆员**——做事、踩坑、解决问题、然后记录。
操作经验只有操作员才能产生。这是架构级别的差异。

---

## 第六轮：最终结论（置信度标注）

| 结论 | 置信度 |
|------|--------|
| CLAUDE.md 应瘦身，将内容页分离到独立 wiki 文件 | ~80% |
| 应增加 log.md（append-only 时间线） | ~75% |
| Lint 应系统化为定期操作 | ~85% |
| 传统手艺结论应萃取为索引级摘要 | ~70% |
| 不需要完整 wiki 编译管线 | ~80% |
| Experience Layer（W6）是我们对 LLM Wiki 的独有补充 | ~85% |
| 可复制系统应融合编译模式和沉淀模式 | ~75% |
| 不应引入 Obsidian/qmd 等外部工具 | ~90% |

---

## 可执行建议（需 Yanjun 拍板）

### 建议 1：CLAUDE.md 重构（Index/Content 分离）
- 将 §5/§8/§9/§9A/§9.5/§10 等内容节移到 `wiki/` 目录
- CLAUDE.md 瘦身为 ~300 行的纯索引+schema
- **时机**：P4 完成后、论文写作前（~2026-04-11）
- **风险**：重构期间如果出错可能影响新会话启动

### 建议 2：增加 log.md
- 在项目根目录创建 `log.md`，append-only
- 每次传统手艺、阶段完成、关键决策后追加一行
- **时机**：可立即开始

### 建议 3：Lint 纳入常规操作
- 在 WORKFLOW.md 中新增 lint 协议
- 每 3 次会话或每次长会话结束前执行
- **时机**：可立即纳入

### 建议 4：传统手艺结论萃取步骤
- 辩论后新增"结论卡片"步骤：1-2 段摘要 + 索引链接
- 纳入 WORKFLOW.md §3 传统手艺流程
- **时机**：可立即纳入

### 建议 5：可复制系统框架文档化
- 创建 `docs/reusable_system_design.md`，记录三支柱架构
- 作为未来新项目的 bootstrap 模板
- **时机**：P4 完成后，作为项目副产品
