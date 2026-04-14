# Myco Identity — Agent-First Symbiotic Cognitive Substrate

> **类型**: concept
> **最后更新**: 2026-04-14
> **来源**: notes/n_20260412T233531_a72c + docs/primordia/substrate_identity_upgrade_craft_2026-04-14.md
> **关联 craft**: docs/primordia/myco_identity_definitive_craft_2026-04-12.md (Round 5, 0.92) + docs/primordia/substrate_identity_upgrade_craft_2026-04-14.md

---

## 定义

**Myco 是与 Agent 协同进化的 Agent-First 共生认知基质（substrate）。** 四个词各自承重：

| 词 | 定义 | 设计约束（测试） |
|----|------|-----------------|
| **Agent-First** | Agent 是唯一操作者，每个表面为 Agent 可发现性设计。人类用自然语言给方向，不需懂内部。 | "能否仅通过 MCP tool description 发现并正确使用？" |
| **Symbiotic** | Agent 提供智能，基质提供记忆、代谢、免疫、进化。缺一不可。连接即共生键合。 | "没有对方，这一半是否不完整？" |
| **Cognitive** | 不只是存储。代谢（七步管道），验证（29 维免疫），自我建模（四层），进化规则本身可变。 | "它是否在代谢、验证、建模、进化？" |
| **Substrate** | 满足全部七条生物学生命标准（代谢、稳态、应激、生长、繁殖、进化、排泄），同时具备基质的四项结构特征（见下节）。 | "它是否自主运转而非等待触发？它是否具备自生成性？" |

## 基质的四项结构特征（新增）

过去几轮身份迭代里，"infrastructure / 基础设施"的表述已经不足以承载 Myco 的实际性质。本轮升级正式引入四项结构特征，它们不替换原有的七条生命标准，而是补充基质之所以是基质的内在属性。

### 1. Autopoiesis（自生成）

基质的产物同时是它的组件。Lint 系统 lint 它自己的 lint 定义（L19 检测 dimension count 漂移）。Canon 约束自己的 schema（L0）。进化引擎可以修改进化规则。基质用它自己生成的概念词汇（wiki 页面标题）构建跨层互联地图（L25）。

这是 Maturana 与 Varela 意义上的 strange loop：Myco 不是"为 Agent 提供服务的系统"，而是"在 Agent 的协同下持续自我生成的基质"。

### 2. Selective permeability（选择性通透）

基质不是无差别吞噬，而是选择性吞噬。write surface 白名单、pinned prefixes、digest 的 absorption gate、29 维 immune lint 的交叉约束，共同构成基质的身份边界。免疫系统不是辅助模块，它定义了 Myco 之所以是 Myco。

### 3. Temporal organization（时间组织）

基质的核心是代谢节律，不是空间存储。七步管道的时间方向性、hunger signals 的实时反射、compression pressure 的累积动力学、dead_knowledge 的时间阈值、跨会话的 hot/warm/cold 层衰减，共同构成 Bergson 意义上的 durée（绵延）：流动、累积、有方向的持续。

### 4. Co-evolutionary niche（协同进化生态位）

Agent 通过 eat, digest, condense 改造基质的知识拓扑。基质通过 perfusion, synaptic_context, interconnection 改造 Agent 下一步的认知形态。这是两条纠缠的进化轨迹。"永恒进化"的主语不是 Myco 单独，而是 Agent 加 Myco 这个复合有机体（Niche Construction Theory，Odling Smee 1996）。

## Myco 不是什么

- **不是工具**：工具用完放下，基质持续运行、跨会话持久进化。
- **不是协议**：MCP 是基质的一个表面，不是基质本身。
- **不是框架**：框架是死脚手架等待填入，基质主动代谢和自我调节。
- **不是记忆层**：Mem0/Zep 提供存取，基质进行代谢（决定保留/压缩/排泄/感知缺口）。
- **不是 Agent Runtime**：Hermes/LangGraph 是 Agent 的执行循环，基质是 Agent 的另一半。
- **不是基础设施**：基础设施是被动的服务提供者，基质是与 Agent 协同进化的生成性母体。

## 三角色关系

```
Human  自然语言  Agent  MCP  Substrate
  |              |          |
  方向 + 信任     智能 + 执行   记忆 + 代谢 + 免疫 + 进化
```

链式而非三角：Human 对 Agent 说话，Agent 操作基质，基质服务 Agent，Agent 服务 Human。

## 七条生命标准验证

| 标准 | Myco 实现 |
|------|----------|
| 代谢 | eat / digest / condense / absorb，持续转化输入为输出 |
| 稳态 | immune 29 维 + hunger signals，自我调节维持稳定 |
| 应激反应 | hunger 感知变化并推荐行动 |
| 生长 | 60+ 版本迭代，100+ notes，复杂度持续增长 |
| 繁殖 | kernel 到 instance 的模板分裂 |
| 进化 | 规则本身可被 evolve.py 修改 |
| 排泄 | prune + dead_knowledge 检测，移除废物 |

## 五层体现

| 层级 | 生物学类比 | Myco 体现 |
|------|----------|----------|
| 1. 身份（DNA） | 基因组 | 8 身份锚点 + _canon.yaml |
| 2. 愿景（表型计划） | 体型蓝图 | docs/vision.md |
| 3. 契约（调控基因） | 基因表达规则 | agent_protocol.md + _canon.yaml 规则 |
| 4. 验证（免疫系统） | T 细胞 + 抗体 | immune 29 维 + hunger signals |
| 5. 实现（器官） | 功能器官 | src/myco/*.py（19 MCP tools） |

## 身份演化弧线

1. **v0.10 (vision_recovery_craft)**：恢复 18 项被压缩丢失的愿景元素，有机体的解剖学。
2. **v0.26 (vision_reaudit_craft)**：评估哪些器官成熟，哪些 vestigial。
3. **v0.40 (anchor_agentfirst_revision_craft)**：mutation-selection 内化，确立 Agent 为唯一操作者。
4. **v0.41 (identity_definitive_craft)**：命名有机体（Agent-First + Symbiotic + Cognitive + Organism）。
5. **v0.45 (substrate_identity_upgrade_craft)**：从 infrastructure 升级到 substrate，引入 autopoiesis / selective permeability / temporal organization / co-evolutionary niche 四项结构特征。

关键转折：hunger(execute=true) 加 scheduled metabolic cycle 之后，mutation 和 selection 都发生在 Agent 加基质内部，人类角色从"选择者"变为"方向给定者加受益者"。

## 三条不可变宪法

| # | 宪法 | 定义 |
|---|------|------|
| C1 | 入口可达性 | 任何 Agent 都能定位系统、读懂自我描述、启动工作 |
| C2 | 透明可审 | 系统对人类始终可理解、可检查、可干预 |
| C3 | 永恒进化 | 停滞即衰亡，代谢循环停止即退化为静态缓存 |

---

*Promoted from notes/n_20260412T233531_a72c on 2026-04-12. Substrate upgrade on 2026-04-14.*

---

## See Also

- [docs/vision.md](../docs/vision.md)：愿景文档，五大核心能力与三条宪法的详细展开
- [docs/theory.md](../docs/theory.md)：理论基础，延伸心智论（Clark & Chalmers）、三环学习（Argyris）
- [docs/architecture.md](../docs/architecture.md)：技术架构，四支柱 + 进化引擎的工程实现
- [docs/evolution_engine.md](../docs/evolution_engine.md)：进化引擎 v3.0
- [wiki/design-decisions.md](design-decisions.md)：创始设计决策 D1-D5
- [wiki/architecture-decisions.md](architecture-decisions.md)：创始架构决策 A1-A3
- [docs/primordia/myco_identity_definitive_craft_2026-04-12.md](../docs/primordia/myco_identity_definitive_craft_2026-04-12.md)：身份定义性 Craft（Round 5, 0.92）
- [docs/primordia/substrate_identity_upgrade_craft_2026-04-14.md](../docs/primordia/substrate_identity_upgrade_craft_2026-04-14.md)：基质身份升级 Craft
- [docs/primordia/anchor_agentfirst_revision_craft_2026-04-12.md](../docs/primordia/anchor_agentfirst_revision_craft_2026-04-12.md)：Agent-First mutation-selection 内化
- [_canon.yaml](../_canon.yaml)：身份锚点 + 规范值 SSoT
- src/myco/immune.py：29 维 Lint 免疫系统（五层体现第 4 层的实现）

**Back to** [MYCO.md](../MYCO.md)
