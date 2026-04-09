# {{PROJECT_NAME}}

> 最后更新：{{DATE}}
> **知识系统**：[Myco](https://github.com/{{GITHUB_USER}}/myco) v0.x

---

## 🔥 热区

**项目**：{{PROJECT_DESCRIPTION}}
**当前阶段**：{{CURRENT_PHASE}}

**最容易出错的 N 件事** ⚠️：
1. [从实际踩坑中提炼——删除本占位符，在实践中积累]

**Agent 行为准则**：
- **即时沉淀** — 关键决策当下写入文档，不等会话结束
- **在线验证** — 数字型 claim 必须 WebSearch 交叉验证
- **Gear 4 意识** — 解决耗时 ≥2 轮的问题后，在 log 条目末尾标记 `→ g4-candidate`（客观判断，不需要评估通用性）
- **自主权边界** — ✅ 技术执行/Bug/文档 | 📢 工作流微调 | 🛑 项目方向/大资源决策

**🎯 Operational Feel**：
[≤5 行，用自然语言描述当前工具链的"手感"——首次遇到操作困难后填写]

**📁 目录挂载状态**（Cowork 会话必填）：
- 项目目录：`{项目路径}` → 已挂载 `/sessions/.../mnt/{项目名}/`
- Myco 源码：`{Myco路径}` → [ ] 未挂载 / [x] 已挂载（Gear 4 需要）
- 挂载方法：`docs/operational_narratives.md` § P-000

---

## 📋 任务队列（硬上限 5 项）

| # | 状态 | 任务 | 备注 |
|---|------|------|------|
| 1 | 🔄 | [当前最优先任务] | |
| 2 | ⏳ | [下一个任务] | |

---

## 📖 知识系统架构

| 层级 | 位置 | 加载方式 | 说明 |
|------|------|---------|------|
| **L1 Index** | 本文件（入口文档） | 自动加载 | 纯索引 + schema（适配 Claude/GPT 等 agent） |
| **L1.5 Wiki** | `wiki/*.md` | 按需读取 | 结构化知识页 |
| **L2 Docs** | `docs/*.md` + `docs/current/*.md` | 按需读取 | 工作流手册、辩论记录 |
| **L3 Code** | `src/`, `scripts/` | 按需读取 | 代码实现 |
| **Timeline** | `log.md` | 按需读取 | Append-only 时间线 |
| **Canon** | `_canon.yaml` | Lint 读取 | 规范值 Single Source of Truth |

---

## 0. 项目摘要

{{PROJECT_SUMMARY}}

---

## 1. 当前进度

```
Phase 0  Setup           ✅ 完成
Phase 1  [自定义]        🔄 进行中
Phase 2  [自定义]        ⏳ 待实现
```

---

## 2. Wiki 索引（L1.5 层）

| Wiki 页面 | 内容 | 关键信息速查 |
|-----------|------|-------------|
| [按需创建——不预建空页面] | | |

---

## 3. 文档索引（L2 层）

### 核心协议
| 文档 | 内容 |
|------|------|
| `docs/WORKFLOW.md` | 工作流手册（十二原则 W1-W12 + 会话流程 + 进化引擎） |

### 辩论记录
> 生命周期标签：`[ACTIVE]` 仍在使用 | `[COMPILED]` 结论已编译到 wiki | `[SUPERSEDED]` 被新版取代

| 文档 | 状态 | 内容 |
|------|------|------|
| [辩论记录在传统手艺执行后自然产生] | | |

---

## 4. 脚本索引

| 脚本 | 用途 |
|------|------|
| `scripts/lint_knowledge.py` | 自动化一致性检查（对照 _canon.yaml） |

---

## 5. 会话规程

**新会话启动**：读本文件热区 → 看任务队列 → 检查目录挂载状态（见"📁 目录挂载状态"）→ 按优先级工作。需要具体知识时读 wiki/ 页面。

**会话结束**：
1. **更新任务队列**（最优先）
2. **追加 log.md**（关键事件一行记录）
3. 更新 §1 进度
4. 新 Bug → wiki/ | 新决策/代码变更 → wiki/ 对应页面或 docs/current/
5. Gear 2 反思："系统本身哪里可以改进？" → log.md `meta` 条目
6. **Gear 4 sweep**：扫描 log.md 中本次会话的 `g4-candidate` 条目 → 每条写入 Myco docs 或标注 `g4-pass: [原因]`（无 g4-candidate 则跳过）
7. 长会话 → `python scripts/lint_knowledge.py --project-dir .`（L2+ 项目；L1 项目跳过此步）
