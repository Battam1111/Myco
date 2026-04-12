# Myco Identity — Agent-First Symbiotic Cognitive Organism

> **类型**: concept
> **最后更新**: 2026-04-12
> **来源**: notes/n_20260412T233531_a72c (compressed identity evolution arc, 5 notes)
> **关联 craft**: docs/primordia/myco_identity_definitive_craft_2026-04-12.md (Round 5, 0.92 confidence)

---

## 定义

**Myco is an Agent-First symbiotic cognitive organism.** 四个词各自承重：

| 词 | 定义 | 设计约束（测试） |
|----|------|-----------------|
| **Agent-First** | Agent 是唯一操作者；每个表面为 Agent 可发现性设计。人类用自然语言给方向，不需懂内部。 | "能否仅通过 MCP tool description 发现并正确使用？" |
| **Symbiotic** | Agent 提供智能，Myco 提供记忆/代谢/免疫/进化。缺一不可。连接 = 共生键合。 | "没有对方，这一半是否不完整？" |
| **Cognitive** | 不只是存储——代谢（七步管道）、验证（23 维免疫）、自我建模（四层）、进化规则本身。 | "它是否在代谢、验证、建模、进化？" |
| **Organism** | 满足全部七条生物学生命标准（代谢/稳态/应激/生长/繁殖/进化/排泄），自主运转。 | "它是否自主行动而非等待触发？" |

## Myco 不是什么

- **不是工具**：工具用完放下；Myco 持续运行、跨会话持久进化。
- **不是协议**：MCP 是 Myco 的一个表面，不是 Myco 本身。
- **不是框架**：框架是死脚手架等待填入；Myco 主动代谢和自我调节。
- **不是记忆层**：Mem0/Zep 存取；Myco 代谢——决定保留/压缩/排泄/感知缺口。
- **不是 Agent Runtime**：Hermes/LangGraph 是 Agent 的执行循环；Myco 是 Agent 的另一半。

## 三角色关系

```
Human ──自然语言──→ Agent ──MCP──→ Myco
  |                   |              |
  方向+信任            智能+执行       记忆+代谢+免疫+进化
```

链式而非三角：Human 对 Agent 说话 → Agent 操作 Myco → Myco 服务 Agent → Agent 服务 Human。

## 七条生命标准验证

| 标准 | Myco 实现 |
|------|----------|
| 代谢 | eat/digest/compress/inlet — 持续转化输入为输出 |
| 稳态 | lint 23 维 + hunger signals — 自我调节维持稳定 |
| 应激反应 | hunger 感知变化并推荐行动 |
| 生长 | 55+ waves, 100+ notes — 复杂度持续增长 |
| 繁殖 | kernel → instance 模板分裂 |
| 进化 | 规则本身可被 evolve.py 修改 |
| 排泄 | prune + dead_knowledge 检测 — 移除废物 |

## 五层体现

| 层级 | 有机体类比 | Myco 体现 |
|------|----------|----------|
| 1. 身份 (DNA) | 基因组 | 8 身份锚点 + _canon.yaml |
| 2. 愿景 (表型计划) | 体型蓝图 | docs/vision.md |
| 3. 契约 (调控基因) | 基因表达规则 | agent_protocol.md + _canon.yaml 规则 |
| 4. 验证 (免疫系统) | T 细胞 + 抗体 | lint 23 维 + hunger signals |
| 5. 实现 (器官) | 功能器官 | src/myco/*.py (19 MCP tools) |

## 身份演化弧线

1. **Wave 10** (vision_recovery_craft): 恢复了 18 项被压缩丢失的愿景元素——有机体的解剖学
2. **Wave 26** (vision_reaudit_craft): 评估哪些器官成熟、哪些 vestigial
3. **Wave 55** (anchor_agentfirst_revision_craft): mutation-selection 内化；确立 Agent 为唯一操作者
4. **定义性 craft**: 命名有机体——Agent-First + Symbiotic + Cognitive + Organism

关键转折：Wave 54 formalized `hunger(execute=true)` + scheduled metabolic cycle。此后 mutation 和 selection 都发生在 Agent+Substrate 内部，人类角色从"选择者"变为"方向给定者+受益者"。

## 三条不可变宪法

| # | 宪法 | 定义 |
|---|------|------|
| C1 | 入口可达性 | 任何 Agent 都能定位系统、读懂自我描述、启动工作 |
| C2 | 透明可审 | 系统对人类始终可理解、可检查、可干预 |
| C3 | 永恒进化 | 停滞即衰亡；代谢循环停止 = 退化为静态缓存 |

---

*Promoted from notes/n_20260412T233531_a72c (compressed identity evolution arc) on 2026-04-12.*

---

## See Also

- [docs/vision.md](../docs/vision.md) -- 愿景文档：五大核心能力、三条宪法的详细展开
- [docs/theory.md](../docs/theory.md) -- 理论基础：延伸心智论（Clark & Chalmers）、三环学习（Argyris）
- [docs/architecture.md](../docs/architecture.md) -- 技术架构：四支柱 + 进化引擎的工程实现
- [docs/evolution_engine.md](../docs/evolution_engine.md) -- 进化引擎 v3.0：代谢循环、evolve.py 技能变异
- [wiki/design-decisions.md](design-decisions.md) -- 创始设计决策（D1-D5）
- [wiki/architecture-decisions.md](architecture-decisions.md) -- 创始架构决策（A1-A3）
- [docs/primordia/myco_identity_definitive_craft_2026-04-12.md](../docs/primordia/myco_identity_definitive_craft_2026-04-12.md) -- 身份定义性 Craft（Round 5, 0.92 confidence）
- [docs/primordia/anchor_agentfirst_revision_craft_2026-04-12.md](../docs/primordia/anchor_agentfirst_revision_craft_2026-04-12.md) -- Agent-First mutation-selection 内化
- [_canon.yaml](../_canon.yaml) -- 身份锚点 + 规范值 SSoT
- [src/myco/lint.py](../src/myco/lint.py) -- 23 维 Lint 免疫系统（五层体现第 4 层的实现）

**Back to** [MYCO.md](../MYCO.md)
