# Myco — 技术架构

> **版本**：v1.2 | **文档修订**：2.3
> **最后更新**：2026-04-12（Wave 58：新增 Appendix F Structural Intelligence Subsystem — graph/cohorts/sessions）
> **范围**：通用框架（项目无关）
> **理论基础**：Karpathy LLM Wiki + Polanyi Tacit Knowledge + Argyris Double-Loop Learning + Toyota PDCA + Rich Sutton Bitter Lesson
> **验证基础**：一个复杂研究项目深度验证（7天，80+文件，12+次传统手艺，含完整四metabolic phase进化）；多项目泛化进行中。

---

## docs/ 目录索引（新项目启动必读）

| 文档 | 类型 | 用途 |
|------|------|------|
| `architecture.md` | 框架架构 | 本文件——四支柱 + 进化引擎全景 |
| `evolution_engine.md` | 进化协议 | 四metabolic phase详细机制（Hunger Sensing-4）、触发条件、权限分级 |
| `reusable_system_design.md` | **核心系统设计** | ⭐ 通用架构详解 + Bootstrap 指南（Level 0/1/2）+ 项目类型适配 |
| `theory.md` | 理论基础 | 认知科学/学习理论支撑 |
| `vision.md` | 愿景文档 | Myco 长期演进方向 |
| `research_paper_craft.md` | **研究型项目专用** | 科研绘图工具链 + 论文写作十大原则 + 9位大师技法速查 |

---

## 核心架构：四支柱 + 进化引擎

```
┌──────────────────────────────────────────────────────────────┐
│          L-meta: 自进化引擎                                    │
│   (摩擦感知 → 会话反思 → 里程碑回顾 → 跨项目蒸馏)              │
├─────────────┬──────────────┬──────────────┬─────────────────┤
│ 支柱 1      │   支柱 2     │   支柱 3     │   支柱 4        │
│ 元协议      │  知识库      │   经验层     │  时间线+基础设施 │
│             │              │              │                 │
│MYCO.md      │ wiki/*.md    │ operational  │ log.md          │
│WORKFLOW.md  │ docs/primordia │ _narratives  │ _canon.yaml     │
│ (50-300行)  │              │ (失败路径)   │ lint脚本        │
└─────────────┴──────────────┴──────────────┴─────────────────┘
```

---

## 支柱 1：元协议层 (Schema Layer)

**角色**：Agent 的"操作系统"——新会话自动加载，定义行为边界和导航方式。

### MYCO.md：索引 + 当前状态

**三级模板**（按项目复杂度选择）：

| 级别 | 行数 | 适用 | 核心内容 |
|------|------|------|---------|
| **Mini** | ~50 | 小型探索项目 | 项目身份 + 3 条核心规则 + 任务 |
| **Standard** | ~150 | 中等项目（会话数 > 5） | + 知识索引 + 会话规程 + 自主权边界 |
| **Full** | ~300 | 长期复杂项目 | + 详细热区 + 脚本索引 + 进度表 |

**MYCO.md 必含部分**：

```markdown
# 项目名

## 🔥 热区（Agent 最先读的）
**项目身份**：[一句话]
**当前阶段**：[Phase X — 具体状态]

**最容易出错的 N 件事** ⚠️：
1. [从真实踩坑中提炼，不是理论预防]

**Agent 行为准则**：
- [项目特定的 3-5 条核心规则]

## 📋 知识索引
## 📖 会话规程  
## 🔒 自主权边界
```

**设计理由**：
- 热区让 Agent 用 30 秒了解全局状态
- "最容易出错的事"必须来自真实失败
- Operational Feel (工具手感) 是 W6 近端丰富化入口，包含环境特有的操作约束

### WORKFLOW.md：原则库

包含 10-15 条项目工作原则（W1-W13 通用原则 + 项目特定原则）。例：
- W1：即时沉淀——关键决策当下就写入文档
- W3：传统手艺——重大决策需多轮深度辩论
- W6：近端丰富化——提供丰富的失败路径和操作细节
- ... 等

### _canon.yaml：规范值的 SSoT

单一信息源原则——同一个数字只在一处记录。

```yaml
system:
  principles_count: 13
  workflow_sections: 12
  wiki_page_types: [entity, concept, operations, analysis, craft]
  lint_dimensions: 23               # L0-L22 (L12 removed)
  entry_point: "MYCO.md"    # Entry point filename (primary) — alternative names may exist per project
  myco_md_max_lines: 300

project:                    # 项目启动时填充
  name: "My Project"
  current_phase: "Phase 2"
  total_runs: 900           # 例：实验总数
  current_progress: 449     # 例：已完成
  key_date: "2026-04-15"    # 交付日期
```

---

## 支柱 2：知识库层 (Knowledge Layer)

**角色**：编译后的知识 + 完整的推理记录。

### Wiki 页面（`wiki/*.md`）

**五种类型**（需要时才创建）：

| 类型 | 示例 | 何时创建 |
|------|------|--------|
| **实体页** | 算法变体、API 列表、环境配置 | 多个核心实体需追踪 |
| **概念页** | 理论框架、策略选择、设计哲学 | 需要多轮辩论才能确立概念 |
| **操作页** | 已知 Bug、部署流程、快速参考 | 同一操作出错 ≥2 次 |
| **分析页** | 实验结果、根因调查、竞品对比 | 需要跨会话持续引用 |
| **技法页** | 代码规范、评审清单、写作技巧 | 编译外部最佳实践 |

**设计理由**：不预建空页面。需求驱动创建避免维护成本。

### 决策记录（`docs/primordia/*.md`）

**原则**：
- 位置：`docs/primordia/` 下
- 可变性：追加不修改（append-only）
- 标签：[ACTIVE] / [COMPILED] / [SUPERSEDED]
  - ACTIVE：仍在使用的决策
  - COMPILED：结论已编入 wiki，原文存档
  - SUPERSEDED：被更新版本取代

**触发条件**（"传统手艺" 决策）：
- 影响项目核心方向
- 对某结论的置信度 < 80%
- 外部利益相关者可能质疑

**流程**：
1. 清晰陈述主张
2. 自我批判（最严苛角度）
3. 在线验证（WebSearch）
4. 防御和修正（迭代）
5. 完整记录 + 结论萃取 → wiki

---

## 支柱 3：经验层 (Experience Layer)

**角色**：Polanyi 的 from-to structure——让 Agent 无需亲自撞墙就能学到教训。

**三个机制**：

### A. 操作叙事（Operational Narratives）

**格式**："尝试 A → 失败因为 X → 尝试 B → 失败因为 Y → 最终方案 C，关键约束是 Z"

**何时写**：操作经历 ≥2 次失败后成功时

**位置**：`docs/operational_narratives.md`

**示例框架**：
```
## 部署/集成失败路径

尝试方案 1（直接操作）→ 失败：[原因]
尝试方案 2（替代方案）→ 失败：[原因]
最终方案 3（成功方案）
  关键约束：[环境或工具强加的限制]
  验证步骤：[如何验证方案正确性]
  何时适用：[什么条件下用这个方案]
```

具体内容因项目而异。例如学术项目可能是"复杂部署流程"，软件项目可能是"CI/CD pipeline 集成"，数据项目可能是"数据库权限管理"。

### B. 上下文启动块（Context Priming）

**位置**：MYCO.md 热区

**形式**：≤5 行的工具手感描述（不是规则）

**目的**：帮助新会话快速"住进"工具环境和操作约束

**示例框架**：
```
🎯 Operational Feel：
你的环境有 [具体约束，如"远程无 X 访问"]。
[核心操作模式，如"需通过 Y → Z 双跳"]。
[大文件/重操作用什么方案]。
详见 docs/operational_narratives.md。
```

具体示例可因项目而异：学术项目可能涉及复杂环境访问、软件项目可能涉及 CI/CD pipeline、数据分析项目可能涉及数据库权限等。关键是让新会话一眼看清"我的操作环境有什么特殊约束"。

### C. 命名模式（Pattern Names）

给反复出现的操作赋予名字 + origin story。

**示例**（项目特定）：
- P-001：大文件部署模式（git-lfs + staging）
- P-005：后台长任务执行模式（根据环境差异实现）

**意义**：统一术语使得操作叙事中的引用更精准，也便于团队沟通。同一个操作在不同项目中可能名字相同但实现不同。

---

## 支柱 4：时间线 + 基础设施

### log.md：Append-only 时间线

**格式**：
```
## [YYYY-MM-DD] type | description
```

**类型**（可扩展）：
- `milestone`：项目重大节点
- `decision`：重要决策
- `debug`：Bug 修复
- `deploy`：部署事项
- `friction`：操作摩擦（Hunger Sensing）
- `meta`：系统反思（Session Reflection）
- `contradiction`：架构矛盾
- `validation`：验证/交叉检查

### _canon.yaml：规范值

防止关键数字散落多处导致漂移。

---

## 自进化引擎（四个metabolic phase）

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐      ┌─────────────┐
│   Hunger Sensing    │      │   Session Reflection     │      │   Milestone Retrospective    │      │   Cross-Project Distillation    │
│  摩擦感知   │ →    │  会话反思    │ →    │ 里程碑回顾  │ →    │ 跨项目蒸馏  │
│ (每次会话)  │      │ (会话结束)   │      │ (Phase 转换)│      │ (项目完成)  │
└─────────────┘      └──────────────┘      └─────────────┘      └─────────────┘
```

### Hunger Sensing：摩擦感知 (Friction Sensing)

**频率**：每次会话中，实时

**触发门槛**（故意设低）：
- 操作花费 > 预期 2 倍
- 需查阅 > 1 个文档完成简单操作
- 文档与实际不一致
- 重复手动执行应该自动化的操作
- "差点犯错"的操作

**记录**：一行到 log.md
```
## [YYYY-MM-DD] friction | [具体操作] 花了 [N 倍时间] 试错，因为 [原因]
```

**示例**（不同项目可能差异很大）：
- 学术项目："复杂系统部署花了 20 分钟试错四条路径"
- 软件项目："UI 表单验证逻辑花了 3 倍时间，因为 edge case 未文档化"
- 数据项目："数据导入失败，需查阅 2 个数据源文档才能修复"

### Session Reflection：会话反思 (Session Reflection)

**频率**：每次会话结束

**必答问题**：
> "这次会话中，系统本身（不是项目内容）有什么可以改进的？"

**记录**：一行到 log.md
```
## [2026-04-08] meta | 发现脚本索引不完整——17 个脚本只索引 7 个
```

**重点**：反思的是**系统架构**而非**项目内容**。

### Milestone Retrospective：里程碑回顾 (Milestone Retrospective)

**频率**：每个 Phase 转换后

**三个必答问题**：

1. **假设审查**：哪个架构假设被违反了？
2. **摩擦聚类**：哪类操作产生了不成比例的摩擦？
3. **重新设计**：如果从头开始这个 Phase，我会改什么？

**产出**：修改架构（不是修补内容）
- 新增 / 拆分 wiki 页面
- 调整 WORKFLOW.md 原则
- 优化进化引擎规则

**权限分级**：
| 修改对象 | 权限 | 理由 |
|---------|------|------|
| Wiki 内容、log、_canon 值 | ✅ Agent 自主 | 错了 10 分钟能回滚 |
| WORKFLOW 原则、MYCO.md 结构 | 🛑 需人类确认 | 错误影响后续所有会话 |
| 进化引擎规则本身 | 🛑 需人类确认 | 自修改的元规则风险最高 |

### Cross-Project Distillation：跨项目蒸馏 (Cross-Project Distillation)

**频率**：项目结束时

**目标**：从单个项目经验中提取可迁移的通用模式。

**流程**：
1. 回顾完整 log.md 演进
2. 识别哪些模式在其他项目也有价值
3. 哪类 wiki 页面最常创建 vs 从未创建
4. 哪些原则被频繁违反（表述不清或不实用）
5. 更新本模板和 MYCO.md 分级标准（需人类确认）

---

## Bootstrap 指南：三个启动层级

### Level 0：快速启动（5 分钟）

**适用**：小型探索项目

```
创建：
  MYCO.md (Minimal，~50 行)
  log.md (第一行：里程碑记录)
```

仅此。wiki/ 和 WORKFLOW.md 等到需要时再创建。

### Level 1：标准启动（30 分钟）

**适用**：中等项目（会话 > 5 次）

```
在 Level 0 基础上：
  MYCO.md 升级为 Standard (~150 行)
  创建 docs/WORKFLOW.md (从模板裁剪)
  创建 wiki/ 目录 (首页面按需创建)
  创建 _canon.yaml (project: 节)
```

### Level 2：完整启动（2 小时）

**适用**：长期复杂项目（学术论文、大系统）

```
在 Level 1 基础上：
  MYCO.md 升级为 Full (~300 行)
  创建 docs/operational_narratives.md
  复制 lint_knowledge.py
  完整 _canon.yaml (system: + project:)
  WORKFLOW.md 启用四个metabolic phase
```

### 自然生长信号

不预建空页面。按这些信号创建：

| 信号 | 动作 |
|------|------|
| 同一个 Bug 出现第 2 次 | 创建 wiki/known_bugs.md |
| 需对外部文献萃取 | 创建第一个技法页 |
| 同类 friction ≥3 次 | 写操作叙事或修改流程 |
| 关键数字出现漂移 | 添加到 _canon.yaml |
| 达到项目里程碑 | 执行 Milestone Retrospective |

---

## 项目类型适配

**通用框架可适配不同项目类型**。关键差异在于传统手艺触发信号和 wiki 页面侧重：

| 项目类型 | 传统手艺触发 | 常用 Wiki 页面 | 推荐 Level |
|---------|-----------|--------------|----------|
| **学术论文** | 论文方向、理论 claim、reviewer 攻击 | 理论框架、论文策略、实验设计、写作技法 | L2 |
| **软件产品** | 架构、技术选型、UX 决策 | API 设计、Bug、部署流程、反馈 | L1-2 |
| **数据分析** | 方法论、结论解释、偏差 | 数据源、分析方法、可视化规范 | L1 |
| **学习计划** | 学习路径、资源评估 | 知识图谱、进度追踪 | L0-1 |
| **创业项目** | 商业模式、融资、定位 | 市场分析、竞品对比、用户画像 | L1-2 |

**注**：每个项目类型的"传统手艺触发"和 wiki 页面侧重都不同，因为决策风险点不同。学术论文的核心风险在理论 claim，软件项目的核心风险在架构决策，数据分析的核心风险在方法论，等等。

---

## 与参考系统对比

| 维度 | 本系统 v2.1 | 纯元文件 | Karpathy Wiki | Cursor Rules | Voyager |
|------|-----------|------------|--------------|-------------|---------|
| 索引/内容分离 | ✅ 四层 | ❌ 单文件 | ✅ Index+Pages | ❌ 单文件 | ❌ |
| 隐性知识编码 | ✅ 经验层 | ❌ | ❌ | ❌ | ⚠️ 代码层仅 |
| 自动一致性检查 | ✅ Lint + SSoT | ❌ | ❌ | ❌ | ❌ |
| 深度决策机制 | ✅ 传统手艺 | ❌ | ❌ | ❌ | ❌ |
| 自进化引擎 | ✅ 四metabolic phase | ❌ | ❌ | ❌ | ⚠️ 技能库 |
| Double-loop | ✅ Milestone Retrospective | ❌ | ❌ | ❌ | ❌ |
| 分级复杂度 | ✅ L0/L1/L2 | ❌ | ❌ | ⚠️ 文件拆 | ❌ |
| 跨项目复用 | ✅ 模板+蒸馏 | ❌ | ✅ 通用方法 | ⚠️ 社区共享 | ❌ |

---

## 实战经验回写

### 发现 1：一致性漂移是最大摩擦源

问题：同一个数据在 MYCO.md、_canon.yaml、log.md 中散落，导致值不一致。

对策：**索引先行协议**——新建 wiki 页面时，强制先更新索引（MYCO.md + _canon.yaml），再写内容。

### 发现 2：摩擦触发门槛要降低

问题：初始设定"花费 3 倍时间"才记录 friction，结果日常微摩擦全漏掉。

对策：门槛降至"差点犯错"和"需多想一步"。宁可过量记录，不可漏记（数据缺失 → Milestone Retrospective 失效）。

### 发现 3：模板需 dry-run 验证

问题：声称通用但未在多项目验证。

对策：修改模板后，用假想的非当前类型项目做心智模拟（L0 → L1）。检查：项目特有假设泄漏？占位符清晰？

### 发现 4：环境特定内容应集中存放

问题：操作约束（如远程配置、端口号、工具约束）散落在 MYCO.md 热区、操作叙事、工作流中，导致难以跨项目迁移。

对策：将所有环境/工具特定内容集中到 `docs/operational_narratives.md`，并在 MYCO.md 热区仅保留"指向性"的参考（如端口、部署工具等）。

---

*本文档遵循 Cross-Project Distillation——每个使用本系统的项目结束时，新发现都应回写到此处。*

---

## Appendix A — Three Immutable Laws

> Moved from README for depth readers. These are the non-negotiable invariants.

1. **Entry point is always accessible** — An agent can always find its way in through `MYCO.md` (or whatever entry point was configured at init/migrate time). No hidden state.
2. **Transparent to humans** — Every piece of knowledge is readable, auditable, and editable by humans without any tool intermediary. Plain text, plain Markdown.
3. **Perpetual evolution** — The system evolves itself, including the rules of evolution. W1-W13 are a bootstrap, not a ceiling.

---

## Appendix B — Philosophy

> Moved from README for depth readers.

Myco takes the **Bitter Lesson** (Rich Sutton, 2019) seriously: hand-crafted rules should eventually be replaceable by system-discovered rules. The current W1-W13 principles are a legitimate bootstrap hot-start from practice — but every one of them is meant to be gradually replaced or refined by rules the system discovers through its own evolution.

Meta-evolution isn't vaporware here: Myco's evolution targets text files — the medium LLMs operate best in — not model parameters. This makes true meta-evolution achievable today without gradient descent or training loops.

---

## Appendix C — The Thirteen Principles (W1-W13)

> Moved from README. Full details in `docs/WORKFLOW.md`.

| # | Principle | One-liner |
|---|-----------|-----------|
| W1 | Immediate Capture | Write decisions now, not at session end |
| W2 | Project Hygiene | Directory structure + naming conventions |
| W3 | Craft (传统手艺) | Multi-round debate for directional decisions |
| W4 | Online Verification | Cross-check numerical claims with search |
| W5 | Continuous Evolution | Repeat → script, lost → reinforce, fail → record |
| W6 | Proximal Enrichment | Failure paths are the most valuable knowledge |
| W7 | Systematic Lint | Periodic automated consistency checks |
| W8 | Wiki Templates | Typed headers + footers for knowledge pages |
| W9 | Active Tensions | Mark unresolved architectural trade-offs with ⚡ |
| W10 | Compilation Protocol | 5-step external knowledge extraction |
| W11 | Verification Scope | Label what conditions conclusions were verified under |
| W12 | Information Density | Adapt context loading depth to task complexity |
| W13 | Primordia Compression | Respond to structural_bloat: compress OR audit-trail deferral |

---

## Appendix D — Bootstrap Levels

| Level | Time | For | What You Get |
|-------|------|-----|-------------|
| **L0** | 5 min | Small projects, exploration | `MYCO.md` (minimal) + `log.md` |
| **L1** | 30 min | Multi-session projects (5+ sessions) | + `WORKFLOW.md` + `_canon.yaml` + `wiki/` |
| **L2** | 2 hours | Long-term complex projects | + Full WORKFLOW + Lint + Evolution Engine (all 4 metabolic phases) |

Don't pre-build empty structures. Create wiki pages when you need them, write procedures when you've failed twice.

---

## Appendix E — Project Adaptation

| Project Type | Craft Triggers | Common Wiki Pages | Level |
|-------------|---------------|-------------------|-------|
| Academic Paper | Theory claims, reviewer attacks | Framework, strategy, experiments | L2 |
| Software Product | Architecture, tech choice, UX | API design, bugs, deployment | L1-2 |
| Data Analysis | Methodology, conclusions, bias | Data sources, methods, visualizations | L1 |
| Learning Plan | Learning path, resource evaluation | Knowledge graph, progress tracking | L0-1 |

---

## Appendix F — Structural Intelligence Subsystem (Wave 47-52)

Waves 47-52 added three cross-cutting intelligence modules that don't fit
neatly into the four-pillar diagram. They serve the Self-Model (Anchor #5)
and the Autonomous Pipeline (Anchor #3) by providing sensing and analysis
capabilities that feed into the hunger signal pipeline.

### F.1 Link Graph (`src/myco/graph.py`, Wave 47)

On-demand structural link graph across all .md files. No cache — computed
from the file system each time (same philosophy as lint).

- **extract_links**: Parse markdown links, backtick paths, YAML frontmatter refs, note IDs
- **build_link_graph**: Two-pass (forward links → invert to backlinks)
- **find_orphans**: Files with zero inbound links (structural roots excluded)
- **find_clusters**: Connected components via BFS (detect knowledge islands)
- **graph_stats**: Hub (most referenced), authority (most referencing), totals

**Self-Model role**: C-layer structural awareness. `graph_orphans` hunger
signal fires when orphan count > 10, prompting the Agent to investigate
disconnected knowledge.

### F.2 Cohort Intelligence (`src/myco/cohorts.py`, Wave 48)

Tag-based semantic analysis for compression intelligence and gap detection.

- **tag_cooccurrence**: Pairwise tag co-occurrence matrix (which topics appear together?)
- **compression_cohort_suggest**: Recommend groups of notes for compression
  (tag + count + age + score, using `_canon.yaml::notes_schema.compression` thresholds)
- **gap_detection**: Tags where ALL notes are raw/digesting (unprocessed knowledge domains)

**Self-Model role**: B-layer gap sensing. `inlet_ripe` hunger signal uses
gap_detection to identify unprocessed domains. `myco compress --cohort auto`
uses cohort suggestions for intelligent grouping.

### F.3 Session Memory (`src/myco/sessions.py`, Wave 52)

FTS5 full-text index of Claude Code conversation transcripts stored in
`.myco_state/sessions.db` (SQLite).

- **index_sessions**: Scan `~/.claude/projects/*/` .jsonl files, extract user/assistant turns
- **search_sessions**: FTS5 MATCH query with snippet extraction and ranking
- **prune_sessions**: Remove old entries (configurable max_age_days)

**Self-Model role**: D-layer temporal awareness. Cross-session context
recovery — "what did we discuss about X?" becomes a searchable query instead
of lost context.

### F.4 How They Compose

```
hunger signals ← graph_orphans (structural disconnection)
               ← inlet_ripe (via cohort gap_detection)
               ← compression_pressure (via notes status counts)
               ← session_index_missing (no FTS5 index)
                       ↓
              hunger(execute=true)
                       ↓
              Agent auto-executes recommended actions
```

The three modules are **sensing instruments** — they provide data to the
hunger signal pipeline, which provides recommendations to the Agent. The
Agent's intelligence decides execution. This is the Bitter Lesson applied:
Myco provides scaffolding, the Agent provides judgment.

---

## See Also

- [docs/theory.md](theory.md) -- 理论基础：延伸心智论、三环学习、认知科学对应
- [docs/vision.md](vision.md) -- 愿景文档：五大核心能力、三条宪法、演进路线图
- [docs/evolution_engine.md](evolution_engine.md) -- 进化引擎 v3.0：代谢循环详细机制、evolve.py 技能变异
- [docs/reusable_system_design.md](reusable_system_design.md) -- 通用架构与 Bootstrap 指南（蒸馏版本）
- [docs/open_problems.md](open_problems.md) -- 未解难题：架构中已知的结构性盲点
- [docs/agent_protocol.md](agent_protocol.md) -- Agent 协议：MCP 工具契约与写面规则
- [wiki/architecture-decisions.md](../wiki/architecture-decisions.md) -- 创始架构决策（A1-A3）：notes.py SSoT、痛点驱动、扁平 notes
- [wiki/design-decisions.md](../wiki/design-decisions.md) -- 创始设计决策（D1-D5）：hunger 排序、非零退出码、四命令最小循环
- [_canon.yaml](../_canon.yaml) -- 规范值 SSoT：所有关键数字的单一信息源
- [src/myco/lint.py](../src/myco/lint.py) -- 23 维 Lint 免疫系统实现
- [src/myco/notes.py](../src/myco/notes.py) -- Note 生命周期 SSoT（A1 决策的实现）
- [src/myco/graph.py](../src/myco/graph.py) -- Link Graph 结构智能（Appendix F.1）
- [src/myco/cohorts.py](../src/myco/cohorts.py) -- Cohort Intelligence 语义分析（Appendix F.2）
- [src/myco/sessions.py](../src/myco/sessions.py) -- Session Memory FTS5 索引（Appendix F.3）
