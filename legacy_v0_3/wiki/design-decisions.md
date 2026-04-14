# Founding Design Decisions

> **类型**: operations
> **最后更新**: 2026-04-12
> **来源**: notes/n_20260412T233541_e3c9 (compressed founding design decisions, 5 notes)

---

本页记录 Myco 最早期的五项原子设计决策。这些决策在 Wave 1 阶段确立，至今仍是系统行为的基石。

## D1: Hunger Signal 按紧迫度排序

**决策**: hunger 信号不按字母序或发现顺序返回，而是按紧迫度（urgency）排序——最需要立即处理的信号排在最前。

**理由**: Agent 的注意力有限（上下文窗口），必须先看到最紧急的事项。如果 Agent 只能处理一个信号就被中断，那个信号应该是最关键的。这是 Agent-First 的直接体现：为 Agent 的认知约束优化输出，而不是为数据结构的便利性优化。

**信号紧迫度阶梯**:
- `[REFLEX HIGH]` raw_backlog — 必须立即消化
- stale_raw — 旧的未处理 notes
- compression_pressure / compression_ripe — 压缩相关
- inlet_ripe — 知识缺口
- graph_orphans — 断联知识
- dead_knowledge — 终态 notes 老化
- healthy — 一切正常

## D2: 有信号时非零退出码

**决策**: `myco hunger` CLI 在检测到任何非 healthy 信号时返回非零退出码（exit code != 0）。

**理由**: 允许将 hunger 集成到 CI/CD 或 shell 脚本中。`myco hunger && echo "all good"` 只在基质健康时通过。这把代谢状态变成了可编程的门控条件，而不仅是人类阅读的报告。自动化友好是 Agent-First 的核心要求。

## D3: Note ID 格式 — 秒级时间戳 + 4位十六进制

**决策**: Note ID 格式为 `n_YYYYMMDDTHHmmss_XXXX`（ISO 秒 + 4 hex 随机后缀）。

**理由**: 权衡了三个方案——
- UUID: 太长，Agent 读不了、人类也读不了
- 纯序号: 无时间信息，跨实例合并时冲突
- 时间戳+短 hex: 人类可读（知道大概什么时候创建的），同秒碰撞概率 1/65536，足够低

**权衡**: 牺牲了全球唯一性（理论上同秒可碰撞）换取了可读性和简洁性。对于单实例场景（绝大多数用例）这个权衡是正确的。

## D4: 四命令最小可用循环

**决策**: Myco 的最小可用循环只需四个命令：`eat` → `digest` → `view` → `hunger`。

**理由**: 新用户（无论人类还是 Agent）的第一次体验必须在 4 步内闭环。`eat` 捕获知识，`digest` 推进生命周期，`view` 查看状态，`hunger` 感知下一步该做什么。这四步覆盖了"摄入→处理→查看→感知"的完整认知循环。

**设计约束**: 任何新功能如果破坏了这个四步闭环的可达性，就不应该加入核心路径。高级功能（condense, absorb, forage, assimilate）是加速器，不是前置条件。

## D5: 非线性生命周期跳转

**决策**: Note 的生命周期允许非线性跳转：raw 可以直接跳到 integrated，也可以直接跳到 excreted。不强制 raw → digesting → extracted → integrated 的线性路径。

**理由**: 实际使用中，有些知识一进来就很清楚该怎么处理（比如一个 bug fix 记录可以直接 integrate），有些一进来就知道是垃圾（比如重复的 note 可以直接 excrete）。强制线性路径会制造无意义的仪式感，浪费 Agent 的注意力。

**约束**: 所有非线性跳转必须通过 `myco digest` 工具执行，不允许手工编辑 frontmatter 的 status 字段。工具确保审计轨迹（digest_count 递增、last_touched 更新）不被绕过。

---

*Promoted from notes/n_20260412T233541_e3c9 (compressed founding design decisions) on 2026-04-12.*

---

## See Also

- [docs/architecture.md](../docs/architecture.md) -- 技术架构：四支柱 + 进化引擎（这些设计决策的全景上下文）
- [wiki/architecture-decisions.md](architecture-decisions.md) -- 创始架构决策（A1-A3）：物理结构层面的互补决策
- [wiki/identity.md](identity.md) -- Myco 身份定义：Agent-First 哲学（D1/D2/D4 决策的价值根基）
- [docs/theory.md](../docs/theory.md) -- 理论基础：Bitter Lesson 立场（D4 最小循环的理论支撑）
- [docs/vision.md](../docs/vision.md) -- 愿景文档：五大核心能力
- [docs/evolution_engine.md](../docs/evolution_engine.md) -- 进化引擎 v3.0：hunger signal 机制（D1 排序决策的运行时体现）
- [src/myco/notes.py](../src/myco/notes.py) -- Note 生命周期实现（D3 ID 格式、D5 非线性跳转的代码）
- [_canon.yaml](../_canon.yaml) -- 规范值 SSoT

**Back to** [MYCO.md](../MYCO.md)
