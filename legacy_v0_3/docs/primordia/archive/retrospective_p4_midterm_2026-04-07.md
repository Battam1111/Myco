# Gear 3 Milestone Retrospective: P4 Mid-Term
> **Status**: ARCHIVED (compiled to formal docs)

> **日期**：2026-04-07
> **里程碑**：P4 主实验中期（~421/900, 46.8%）
> **类型**：首次 Gear 3 实战执行
> **参与者**：Agent + Yanjun（Yanjun 触发，Agent 执行分析）

---

## Q1: 假设审查 — "哪个架构假设在这个阶段被违反了？"

### 已修复的违反

1. **"CLAUDE.md 可以同时做索引和内容"** → 949行→185行重构，L1/L1.5 分离
2. **"七原则够用"** → 需要 W8-W12，升级为十二原则
3. **"_canon.yaml 修改会被记住"** → Lint 覆盖了但发现延迟。修复：增加 stale pattern 检测

### 未修复的违反（本次发现）

4. **"进化引擎齿轮会自然运转"** — Gear 1 friction 条目 = 0，说明要么门槛太高，要么 Agent 忘记了。Gear 2 仅执行 1 次。引擎存在于文档中但未活在工作流中。

5. **"project_template 建好就能用"** — 从未在非 ASCC 项目中测试。一般化承诺缺乏验证。

---

## Q2: 摩擦聚类 — "哪类操作产生了不成比例的摩擦？"

| 类别 | 频次 | 占比 | 代表事件 |
|---|---|---|---|
| 文档一致性漂移 | ~6 | 40% | P4 数字三处不同、principles 7→12 漂移 |
| 缺少基础设施 | ~3 | 20% | tab_main_results 生成器、results.md、environments.md |
| 系统文档开销集中 | ~3 | 20% | 一天内 20+ 条 system 日志 |
| SSH/HPC 操作 | ~3 | 20% | 已通过 3 个操作叙事稳定 |

**最显著模式**：文档一致性漂移占 40%，是最大摩擦源。核心原因是"先改文档内容，后（或忘记）更新 _canon.yaml"——顺序反了。

---

## Q3: 重新设计 — "如果重新设计这个阶段，我会改变什么？"

### 改变 1：Wiki 创建清单协议

每新建一个 wiki 页面，**立即**执行以下 3 步（写入 WORKFLOW.md 作为强制协议）：
- [ ] 添加 CLAUDE.md 索引行
- [ ] 更新 _canon.yaml `wiki_pages` 计数
- [ ] 应用 W8 模板（header type+date + footer back-to）

### 改变 2：Gear 1 门槛降低

当前 friction 日志条目 = 0 说明门槛太高。新规则：
- 任何"差点犯错"的操作都值得记录
- 任何需要翻阅 >1 个文档的简单操作都值得记录
- 格式仍然是一行——开销可忽略

### 改变 3：Template Dry-Run 验证

在声称 project_template 可用之前，应该用一个真实的 mini-project 做一次完整的 Level 0→Level 1 bootstrap 测试。

---

## 行动项

| # | 行动 | 优先级 | 负责 |
|---|------|--------|------|
| A1 | 将 Wiki 创建清单写入 WORKFLOW.md 作为强制协议 | HIGH | Agent ✅ |
| A2 | 降低 Gear 1 门槛描述，更新 evolution_engine.md | HIGH | Agent ✅ |
| A3 | 用 mini-project 对 project_template 做 dry-run | MEDIUM | Agent ✅ |
| A4 | 推进 v2.5 压缩脚本（已在路线图） | MEDIUM | Agent ✅ |

---

## 反思：Gear 3 协议本身的评价

首次执行 Gear 3 花了约 15 分钟（含数据收集 + 分析 + 写文档）。三个问题确实引导出了有价值的 Double-loop 发现——特别是"进化引擎名存实亡"这个问题，如果没有 Q1 的系统性审查不会被发现。

**改进建议**：Q2 摩擦聚类在 friction 条目为 0 时效果有限——依赖 system 日志的间接推断。如果 Gear 1 运转正常（有足够的 friction 数据），Q2 的分析会更精准。

> 本文档为不可变记录。行动项的执行状态跟踪在 CLAUDE.md 任务队列和 log.md 中。
