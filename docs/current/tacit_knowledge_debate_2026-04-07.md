# 传统手艺：Tacit Knowledge 与知识管理系统改进

> 日期：2026-04-07
> 触发：Yanjun 提出 Michael Polanyi 的 Tacit Knowledge 概念，要求深度分析其对项目知识管理系统的意义
> 轮数：5 轮（提出 → 自我攻击 → 防御修正 → 深化 → 最终审视）
> 结论：新增 W6 近端丰富化原则（Proximal Enrichment Protocol）

---

## 在线调研素材

### Polanyi 原著核心概念（The Tacit Dimension, 1966）
- **核心命题**："We can know more than we can tell." — 隐性知识不是"还没写下来的显性知识"，而是本质上不可完全言说的。
- **From-to structure**：一切 tacit knowing 都有 proximal term（近端：辅助意识中的细节线索）和 distal term（远端：焦点意识中的整体意义）。我们 *从* 近端 *到* 远端。
- **Subsidiary vs Focal awareness**：辅助意识关注细节线索，焦点意识关注整体意义。两者动态切换——钢琴家演奏时手指是 subsidiary，练习时手指变 focal。
- **Indwelling（内居）**：通过反复使用工具，我们把工具"纳入自身"，工具成为身体的延伸。
- **四个面向**：功能面向（from-to）、现象面向（近端感觉转化为远端意义）、语义面向（近端获得远端赋予的意义）、本体面向（整合产生涌现整体）。

来源：
- Wikipedia: Tacit knowledge
- Polanyi Society: mp-structure.htm
- New World Encyclopedia: Michael_Polanyi
- Isabell's EdTech Insights: Polanyi - Tacit Knowledge and Its Aspects

### Nonaka-Takeuchi SECI 模型（1990/1995）及其对 Polanyi 的误读
- SECI = Socialization（隐→隐）、Externalization（隐→显）、Combination（显→显）、Internalization（显→隐）
- 核心假设：隐性知识可以被"转化"为显性知识（Externalization）
- **批评**：多个学者指出 Nonaka 对 Polanyi 的解读是错误的——Polanyi 认为隐性知识本质上不可完全言说，不是"等待翻译"的知识。SECI 模型把"不可言说"变成了"可以转化"，这是概念上的偷换。

来源：
- Wikipedia: SECI model of knowledge dimensions
- Polanyisociety.org: Knowledge Management and Polanyi (Straw, 2016)

### AI 与 Polanyi's Paradox
- 现代 AI（特别是大语言模型）可能部分克服 Polanyi's Paradox——通过从非结构化数据中发现模式来捕捉隐性知识
- 实例：AI 教练工具分析顶级客服代表的对话记录，提升整体生产力 14%，最不熟练的员工提升 34%
- 关键挑战：数据可用性——高价值的隐性知识通常没有被记录

来源：
- Exponential View: Why AI might finally break Polanyi's Paradox

### 软件工程中的隐性知识
- 实证：~80% 的员工知识是隐性的
- 美国大型企业平均每年因知识共享低效损失 4700 万美元
- 软件开发中的隐性知识：调试"直觉"、设计决策的"感觉"、团队动态的"不言自明"
- AI 编码助手面临的核心挑战：它们快但缺乏上下文——而人类程序员的上下文大量来自隐性学习

来源：
- knowledgefabric.io: Tacit Knowledge - The secret sauce in software development
- arxiv.org/html/2603.14805: Knowledge Activation: AI Skills as Institutional Knowledge Primitive

---

## 第一轮：提出主张

我们的三层知识持久化系统（L0-L3）只捕获显性知识。项目中大量隐性知识（操作手感、调试直觉、判断力）在会话边界处丢失。引入 Polanyi 的 Tacit Knowledge 框架可以改善。

初步提案：Operational Recipes（操作食谱）、Named Patterns（命名模式）、Apprenticeship Checks（学徒检查）。

## 第二轮：自我攻击

**攻击 1**：操作食谱本质上还是 Externalization（隐→显转化），这是 Nonaka 式的误读，Polanyi 自己否定了这条路。

**攻击 2**：Claude 没有 Polanyi 意义上的 embodiment（身体性）和 temporal continuity（时间连续性）。Indwelling 依赖持续的身体，但 Claude 每次新会话是全新的意识。"学徒检查"可能只是多跑了一步命令，不是真正获得隐性知识。

**攻击 3**：加入更多文档会让 CLAUDE.md 更臃肿，挤占工作记忆，反而损害显性知识的传递效率。

**攻击 4**：W1-W5 已经足够好了，新增原则可能是过度工程化。

## 第三轮：防御与修正

**对攻击 1**：关键认识修正——Polanyi 的核心不是"隐性 vs 显性"二分法，而是 **from-to 的动态关系**。操作食谱应该重新定义为"操作叙事"——不是把隐性知识变成规则，而是**提供失败路径作为 proximal terms**。失败路径让新会话获得对问题空间的 subsidiary awareness，from-to structure 自然涌现。

**对攻击 2**：修正"学徒检查"概念。Claude 没有持续身体，但有**上下文性**——loaded context 可以类比为"临时身体"。正确问题不是"如何让 Claude 获得隐性知识"，而是"如何让新会话最快建立起丰富的上下文"。**放弃学徒检查，改为 Context Priming Blocks**。

**对攻击 3**：正确。解决方案：操作叙事放在 L2 层（`docs/operational_narratives.md`），不放入 L1。CLAUDE.md 只加一个 ≤5 行的 Context Priming Block + 一条索引。

**对攻击 4**：W1-W5 解决"信息不丢失"，不解决"经验不重建"。实证：SSH 规则完整记录在 §3，但 analyze_results.py 部署仍花大量时间试错。

## 第四轮：深化——修正后的框架

**旧认知**：引入 Polanyi → 尝试显性化 → 操作食谱、命名模式、学徒检查
**新认知**：忠于 Polanyi 原意 → 不做显性化 → **丰富 proximal terms 让 from-to structure 自然涌现**

三个执行机制：
- **机制 A：Operational Narratives**（操作叙事）— 完整操作故事含失败路径
- **机制 B：Context Priming Blocks**（上下文启动块）— CLAUDE.md 热区的 ≤5 行手感描述
- **机制 C：Pattern Names with Stories**（带故事的命名模式）— 命名 = focal integration

## 第五轮：最终审视

NeurIPS 锚点检查：这是工作流改进，不是直接推进论文。但后续会话（P4 分析、P5 部署、论文写作）可因更好的知识留存减少试错时间。ROI 为正。

边界：限制改进范围，避免过度工程化。只写高 ROI 的叙事，Context Priming Block 严格 ≤5 行。

---

## 结论与置信度

| 结论 | 置信度 |
|------|--------|
| Polanyi 的核心贡献是 from-to structure，不是"隐性 vs 显性"二分法 | ~85% |
| SECI 模型的"Externalization"是对 Polanyi 的误读 | ~75% |
| 我们的系统缺的不是"更多规则"而是"更丰富的近端素材（proximal terms）" | ~80% |
| Claude 没有 Polanyi 意义上的 embodiment，但上下文可以类比为"临时身体" | ~70% |
| Operational Narratives > Operational Recipes（叙事 > 食谱） | ~85% |
| Context Priming Blocks > Apprenticeship Checks（上下文启动 > 学徒检查） | ~80% |
| 改进应限制在高 ROI 的小范围内，避免过度工程化 | ~90% |

## 产出

1. WORKFLOW.md §0: 五原则 → 六原则（+W6 近端丰富化）
2. WORKFLOW.md §6.5: 近端丰富化协议完整说明
3. `docs/operational_narratives.md`: 第一批 3 个操作叙事（N-001 ~ N-003）
4. CLAUDE.md 热区: Operational Feel 启动块 + 文档索引更新
