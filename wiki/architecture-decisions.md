# Founding Architecture Decisions

> **类型**: operations
> **最后更新**: 2026-04-12
> **来源**: notes/n_20260412T233542_e1a9 (compressed founding architecture decisions, 3 notes)

---

本页记录 Myco 最早期的三项架构决策。它们定义了系统的物理结构，是所有后续技术选择的基础。

## A1: notes.py 是单一运行时 SSoT

**决策**: 所有 note 的读写、状态转换、frontmatter 验证都集中在 `src/myco/notes.py` 一个模块中。其他模块（hunger, compress, digest 等）通过 notes.py 的 API 访问 notes，绝不直接读写 `notes/*.md` 文件。

**理由**: Note 是 Myco 最核心的数据结构。如果多个模块各自直接读写 note 文件，frontmatter schema 的一致性就无法保证——一个模块可能写入 `status: raw`，另一个可能写入 `state: raw`。单一 SSoT 模块确保：
- Frontmatter schema 在一个地方定义和验证
- 所有写操作经过同一套 inline lint 检查
- Status 转换规则集中管理
- 审计字段（digest_count, last_touched）不会被遗漏

**依赖方向**: notes.py 不依赖任何其他 Myco 业务模块（hunger, compress 等）。依赖是单向的：其他模块 → notes.py。这防止循环依赖，也让 notes.py 成为最稳定的模块。

## A2: 三个 ASCC 痛点映射到三个架构缺口

**决策**: Myco 的架构直接从 ASCC（AI-Supervised Catalyst Combustion）项目的三个真实痛点推导出来，而非从理论框架自上而下设计。

| ASCC 痛点 | 根因诊断 | Myco 架构回应 |
|-----------|---------|-------------|
| 每次新会话 Agent 忘记之前学到的东西 | 没有跨会话持久化的知识层 | notes/ + digest 生命周期 |
| 文档和代码逐渐不一致 | 没有自动化的一致性验证 | lint 23 维免疫系统 |
| 相同的错误反复发生 | 没有 tacit knowledge（隐性知识）的结构化捕获 | eat + friction tag + operational_narratives |

**理由**: 自下而上比自上而下更可靠。从真实痛点出发确保每个架构组件都解决实际问题，而不是理论上"应该有"的问题。ASCC 是 Myco 的首个宿主项目（7 天深度验证），这三个痛点是在 80+ 文件、12+ 次 craft 辩论中反复观察到的。

**原则**: 未来添加新架构组件时，必须能指出"这解决了哪个已验证的真实痛点"。不接受"好像有用"级别的动机。

## A3: 扁平 notes 优于文件夹层级

**决策**: 所有 notes 都存放在 `notes/` 单一目录下，使用 frontmatter tags 进行分类，而非使用子文件夹层级（如 `notes/architecture/`, `notes/bugs/` 等）。

**理由**: 来自 Zettelkasten 研究的核心洞见——文件夹层级强制单一分类维度（一个 note 只能放在一个文件夹里），而 tags 支持多维分类（一个 note 可以同时是 `architecture` + `design` + `tradeoff`）。

**具体优势**:
- **多维查询**: `myco view --status=raw` 或按 tag 过滤——文件夹做不到跨类查询
- **无分类焦虑**: 不需要在创建 note 时就决定"这属于哪个类别"
- **压缩友好**: `myco compress --tag=architecture` 可以跨"类别"压缩相关 notes
- **可伸缩**: 100 个 notes 在扁平目录里 glob 搜索是 O(n)，和文件夹遍历一样快；1000 个 notes 时文件夹层级反而因为人工维护成本更高
- **简单性**: 文件系统操作只需处理一层，减少路径拼接错误

**权衡**: 牺牲了视觉上的"整洁感"（ls 看到一大堆文件），换取了灵活性和机器可操作性。对于 Agent-First 系统，机器可操作性优先于人类视觉美感。

---

*Promoted from notes/n_20260412T233542_e1a9 (compressed founding architecture decisions) on 2026-04-12.*

[Back to MYCO.md](../MYCO.md)
