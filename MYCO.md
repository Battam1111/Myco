# Myco

> 最后更新：2026-04-11
> **知识系统**：[Myco](https://github.com/Battam1111/Myco) v0.2.0（框架自用，pre-release；kernel contract v0.9.0）
> **⚠️ Wave 8 re-baseline**：历史上 v1.x 的包版本号和 v1.x.y 的 contract 版本号在 2026-04-11 全部下调到 0 开头，因为 Myco 尚未进行过真正的 1.0 正式发布。历史记录中的 v1.x 标识符保持不动作为 immutable history；当前生效版本一律以 v0.x 计。详见 `docs/primordia/pre_release_rebaseline_craft_2026-04-11.md` 与 `docs/contract_changelog.md` 顶部 banner。

---

## 🔥 热区

**项目**：Myco — 可自进化的 AI 延伸认知基质（框架本身）
**当前阶段**：v0.2.0 pre-release — public launch 准备中（尚未 1.0）；Phase 2 消化道迭代进行中（Upstream Protocol v1 + Craft Protocol v1 + Self-Model D 层种子 + 仿生结构 overlay + lint SSoT 合流 + forage substrate inbound channel + Wave 8 量化指标体系 + 全量版本 re-baseline + **Wave 9 upstream absorb 收割回路**（scan/absorb/ingest + pointer-note + L1 context-aware）已落地，kernel contract v0.9.0）

**框架开发中最容易出错的 N 件事** ⚠️：
1. 更新 `pyproject.toml` 版本号但忘记同步 `src/myco/__init__.py`（两处版本号必须一致）
2. 在 MYCO.md 里写"已实现"的功能，实际上是 roadmap（诚实原则）
3. 运行 `myco lint` 检查 Myco 自身时，`--project-dir` 指向 repo 根，不是 `src/` 子目录
4. 修改模板后忘记 rebuild + 重新 `pip install -e .`（本地测试时 importlib.resources 读的是 src/，无需 build；但 wheel 测试必须重建）

**对外定位一句话**（供 agent 快速了解 Myco 的市场位置）：
> "Myco is an Autonomous Cognitive Substrate for AI agents. Your agent is the CPU — Myco is everything else, and the OS upgrades itself. All evolution is non-parametric: markdown, YAML, folder structure, lint rules. No weights ever touched."
> 次级 tagline："Other tools give memory. Myco gives metabolism."
> OpenClaw = 存储层验证；Hyperagents = 进化 CPU；Myco = 进化操作系统。互补，不竞争。

**🧭 身份锚点**（抗漂移——每次上下文压缩后 agent 必须重读）：
1. **基质 vs 工具**：Myco 是基质（substrate），不是工具。Agent 运行在 Myco 上，不是 Agent 使用 Myco。架构上：项目无关的**内核**（本仓库）+ 项目**实例**（你的项目目录），正如 OS 与应用的关系。
2. **非参数进化**：Agent 权重永不改动，所有学习在基质里（md/yaml/目录结构）。
3. **代谢 + 七步管道**：齿轮 1-4 是自主神经系统（内向稳态）；代谢入口是消化系统（外向摄取，v2.0 原语）。完整管道：发现→评估→萃取→整合→压缩→验证→**淘汰**。没有第七步就不是代谢，是消化。
4. **压缩即认知**：存储无限，注意力有限。"不遗忘，只压缩" 是 doctrine 不是工程细节——压缩决策是基质的首要认知行为。三条判据：频率 · 时效 · 排他性。压缩是 Agent-adaptive 的（32K vs 200K 策略不同），压缩策略本身也进化。
5. **四层自我模型**：A 库存 · B 缺口 · C 退化（仅事实性，结构性退化是开放问题）· D 效能（"死知识"追踪，未实现）。今天 Myco 实现 A+B+partial C。
6. **人机协作**：系统做变异（mutation），人类做选择（selection）。透明性是选择压力的前提，所以不可变——没透明就没选择压力，就会癌变。**永恒进化**（Perpetual Evolution）是三条不可变律之一：**停滞即死**，停止代谢的基质会退化为静态缓存。
7. **理论血统**：Karpathy LLM Wiki + Polanyi Tacit + Argyris Double-Loop + Toyota PDCA + Voyager Skill Library。详见 `docs/theory.md`。
8. **永久锚点文档**：详细愿景恢复记录见 `docs/primordia/vision_recovery_craft_2026-04-10.md`——这是防漂移的永久锚点，18 项丢失元素全部在里面有原文引证。**任何一次上下文压缩后第一件事是重读它。**

**Agent 行为准则**：
- **📜 硬契约** — 运行前必读 [`docs/agent_protocol.md`](docs/agent_protocol.md)（write surface / tool protocol / boot-end sequence / anti-patterns / §8 Upstream Protocol）。**L11** write surface + **L12** upstream dotfile hygiene + **L13** Craft Protocol schema 自动执行，违约 = 基质污染。
- **🛠️ Craft Protocol (W3)** — 影响 kernel 契约 / 实例架构 / 置信度 < 0.80 的决策必须走 [`docs/craft_protocol.md`](docs/craft_protocol.md) 规范的结构化自对抗辩论；产物写入 `docs/primordia/<topic>_craft_YYYY-MM-DD.md` 并含 `craft_protocol_version: 1` frontmatter。L13 强制 schema。kernel_contract 决策 floor 0.90 / instance_contract 0.85 / exploration 0.75。
- **即时沉淀** — 关键决策当下 `myco_eat` 为 raw note，不手建 scratch/TODO/MEMO 文件
- **在线验证** — 数字型 claim 必须 WebSearch 交叉验证
- **Gear 4 意识** — 解决耗时 ≥2 轮的问题后，在 log 条目末尾标记 `→ g4-candidate`
- **摩擦必捕** — Myco 工具不顺手 → `myco_eat` + `friction-phase2` tag（Phase ② 的粮食）。**🆕 自承错误触发点**：同一 turn 内说出"我之前说的 X 是错的"类表述，**立即** `myco_eat` + `on-self-correction` tag。
- **自主权边界** — ✅ 技术执行/Bug/文档 | 📢 工作流微调 | 🛑 框架方向/API 设计/破坏性变更/`_canon.yaml` 修改/**kernel contract 变更（必须 craft + `[contract:*]` commit）**

**🎯 Operational Feel**：
Python 打包环境（hatchling + twine）。模板唯一来源：`src/myco/templates/`（打包入 wheel）。
`pip install -e .` 后 `myco` CLI 指向 `src/`，无需 build 即可测试。

---

## 📋 任务队列（硬上限 5 项）

| # | 状态 | 任务 | 备注 |
|---|------|------|------|
| 1 | ✅ | **v1.2 消化道 Phase ① 消化道闭环** ▰▰▰：eat/digest/view/hunger + notes/ + L10 + MCP ×4 | **落地 2026-04-10**，22 notes、3 deep-digest、1 非线性 raw→integrated、1 excreted with reason、L10 绿灯 |
| 2 | 🔄 | v1.2 消化道 Phase ② 摩擦驱动迭代 ▰▰▰：根据 ① 真实数据决定 extract/integrate 等新器官 | **四波落地**：Upstream Protocol v1.0 (L12, v1.2.0) + Craft Protocol v1 (L13, v1.3.0) + Self-Model D 层 dead_knowledge 种子 (v1.4.0) + 仿生结构 overlay + structural_bloat 信号 (v1.5.0) |
| 3 | ⏳ | v1.2 消化道 Phase ③ Commons 上线 ▰▱▱：commons/ + promote/craft use + HPC lesson 洗仓 | 门槛：Phase ② 收敛稳定 |
| 4 | 📐 | **Metabolic Inlet 原语（身份级声明）** ▱▱▱ | v2.0，不阻塞 Phase ①-③ |

> **节奏说明**：Phase 之间的切换由**硬验收指标**触发，不由日历驱动。我们的推进速度由 Gear 1 摩擦信号决定——可能数小时，可能数日。任一 Phase 验收 < 50% 即回炉。

### 任务 4 详述 · Metabolic Inlet

**性质**：身份级 primitive 声明，不是功能承诺。理由：齿轮 1-4 完全内向（friction → reflect → retrospect → distill），没有任何一档朝向外部世界。一个没有消化系统的基质只是缓存，不是基质。现在不声明，外部贡献者会把 Myco 建成"更好的 CLAUDE.md"；声明后但不提前实现，避免违反 Bitter Lesson 立场（机制必须从第一性原理浮现，不能手工设计）。

**形状**（草图，v2.0 设计辩论时再细化）：
- **触发**：摩擦信号（agent 在 wiki/canon/log 找不到答案）OR 周期巡逻（时间/事件驱动）
- **目标源**：GitHub 仓库、arXiv、社区文档、上游工具发布说明
- **管道**：发现 → 评估（相关性/质量/新颖性）→ 萃取（模式，不是复制）→ 整合（融入 wiki/canon，不追加）→ 压缩 → 验证（lint）
- **不变量**：所有摄取过的内容必须通过现有 14 维 lint；任何降低 lint pass 率的摄取必须被拒绝
- **v2.0 bootstrap 约束**：用户审批种子源 → agent 执行摄取 → lint 验证整合。v2.5 之前不允许完全自主的源发现。

**阻塞 / 开放问题**：
- Self-Evolving Agents survey 明确说"proactive knowledge acquisition from the environment"无现有实现
- 冷启动问题（没有 friction 历史时如何触发？）
- 对齐问题（摄取的知识可能带来新的假设，人类能评估吗？）
- 压缩工程（摄取速度 >> 压缩速度 → 膨胀）

**不会做**：
- 在 v1.2 实现代谢入口（违反第一性原理立场）
- 在 v1.2 之前用其他名字隐藏这个原语（违反身份完整性）
- 把这个任务降级为 "feature backlog"（这是 identity commitment，不是 feature）

---

## 📊 指标面板（Wave 8 量化指标体系）

> Schema 在 `_canon.yaml::system.indicators`（SSoT）；**本面板是 authoritative value location**；历史波动记录在 `log.md` milestone 条目里。
> 区间 `[0.0, 1.0]`，合法后缀 `_progress / _confidence / _maturity / _saturation / _pressure`，rationale 必填，stale_after_days=90。
> 无外部证据时 bootstrap 置信度天花板 = **0.70**（下调随意，上调需 log.md milestone + commit hash 支撑）。
> 未来 L15 Indicators Lint 会强制 diff 证据规则（Wave 9+ 非目标）。

| 指标 | 值 | rationale | 证据锚 |
|------|----|-----------|--------|
| `v1_launch_progress` | 0.55 | 包/契约/lint/模板/文档已 v0.2.0 pre-release 就位；但 PyPI 未发布、README 的 v1 里程碑未对齐、dist/ 仍含 1.1.0 wheel（Wave 8 清理中） | 本 wave Face C/E |
| `three_channel_maturity` | 0.70 | inbound (forage v0.7.0) + internal (notes v0.4.0) + outbound/outbound→inbound (upstream v0.3.0) schema & lint 全部在位；Wave 9 首次闭环 absorb 验证（ce72+3356 从 ASCC 吸收 → pointer-note 落地），n=1；**Wave 9 first-live forage batch 完成 6/6**（nuwa+gbrain+hermes+mempalace+CMA+karpathy 全部 raw→digested，产出 6 条 extracted notes，跨项目 convergent pattern 3 条进入 Wave 10/11 预留），inbound 通道首次 end-to-end 真实负载验证 | contract v0.9.0, L14/L10/L12, forage manifest 6× digested, `n_20260411T1831..185410_*` |
| `lint_coverage_confidence` | 0.68 | 15 维 L0-L14 全绿，双路径（myco.lint + scripts/lint_knowledge.py shim）一致；bootstrap ceiling 限制 0.70 以内 | L13/L14 craft + 双路径验证 |
| `compression_discipline_maturity` | 0.40 | 七步管道到"淘汰"已有结构但真实 excretion 只发生过 1 次；dead_knowledge 信号未触发过 | n_20260411T*.md 态势 |
| `identity_anchor_confidence` | 0.70 | 身份锚点 8 条稳定多 wave；L9 Vision Anchor 执行中；但自评偏差无外部独立确认 | vision_recovery craft |
| `forage_backlog_pressure` | 0.00 | Wave 9 first-live batch 6 items 全部 digested（空 raw backlog）；manifest schema_version=1 稳定 | L14, forage/_index.yaml |
| `notes_digestion_pressure` | 0.18 | 少量 raw 未 digest 但无 stale；健康范围 | myco hunger |
| `upstream_inbox_pressure` | 0.00 | Wave 9 CLI 落地后首次 dogfood：ce72+3356 absorb → ingest 完成，bundle 已归档至 `.myco_upstream_inbox/absorbed/`，active inbox 归零；ceiling=5 为 bootstrap 值，pending friction data | contract v0.9.0, `myco upstream scan` |

**自评偏差护栏**（Wave 8 craft R2.2）：以上数值在无外部 evidence 情况下都以 0.70 为软顶。下调可随时，上调任何一项都需要在 `log.md` 追加一条 milestone + 关联 commit hash。**不要把 dashboard 当成奖杯榜**。

---

## 📖 知识系统架构

| 层级 | 位置 | 加载方式 | 说明 |
|------|------|---------|------|
| **L1 Index** | 本文件（MYCO.md） | 自动加载 | 纯索引 + schema，agent-agnostic |
| **L1.5 Wiki** | `wiki/*.md` | 按需读取 | 结构化知识页（有机生长，现为空） |
| **L2 Docs** | `docs/*.md` + `docs/primordia/*.md` | 按需读取 | 框架文档、辩论记录 |
| **L3 Code** | `src/myco/` + `scripts/` | 按需读取 | 包源码 + 工具脚本 |
| **Timeline** | `log.md` | 按需读取 | Append-only 时间线 |
| **Canon** | `_canon.yaml` | Lint 读取 | 规范值 Single Source of Truth |

---

## 0. 项目摘要

Myco 是一个可自进化的 AI 延伸认知基质框架。它给 AI agent 提供持久记忆、结构化知识和跨会话的自进化能力。v1.1.0 已发布 PyPI（`pip install myco`），提供 `myco init / migrate / lint / eat / digest / view / hunger` CLI。当前 kernel contract v1.3.0（含 Upstream Protocol v1.0 + Craft Protocol v1）。

核心设计：agent-agnostic（Claude、GPT、Codex 等均可运行），框架本身通过 Myco 管理自身的知识。

---

## 1. 当前进度

```
Phase 0   基础打包 + PyPI 上线               ✅ 完成 (v0.9.0, 2026-04-09)
Phase 1   自我应用 + 社区文件 + v1.0          ✅ 完成 (v1.0.0, 2026-04-09)
Phase 1b  CLI 自动化 + v1.1                   ✅ 完成 (v1.1.0, 2026-04-10)
Phase 2   Public Release                      🔄 准备中
Phase 3   非 ASCC 项目示例                    ⏳ v1.2 目标
—— 消化道（Digestive Tract）----------------
Phase ①   eat/digest/view/hunger 闭环        ✅ 完成 (2026-04-10)
Phase ②   摩擦驱动迭代                       🔄 进行中
           · Upstream Protocol v1.0 (L12)    ✅ contract v1.2.0 (2026-04-11)
           · Craft Protocol v1 (L13)          ✅ contract v1.3.0 (2026-04-11)
           · 其他 friction-driven 器官        ⏳ 摩擦数据累积中
Phase ③   Commons 上线                       ⏳ 门槛：Phase ② 收敛
—— 身份级声明（非 v1.x） --------------------
v2.0      Metabolic Inlet 原语               📐 已声明，不实现
```

---

## 2. Wiki 索引（L1.5 层）

| Wiki 页面 | 内容 | 关键信息速查 |
|-----------|------|-------------|
| [按需创建——不预建空页面] | | |

> wiki/ 当前为空，遵循"有机生长"原则。

---

## 3. 文档索引（L2 层）

### 核心协议
| 文档 | 内容 | 状态 |
|------|------|------|
| `docs/agent_protocol.md` | **Agent 运行硬契约** — write surface / tool protocol / boot-end sequence / anti-patterns（由 L11 lint 执行） | **[ACTIVE] [CONTRACT]** |
| `docs/craft_protocol.md` | **W3 Craft Protocol v1 正式规范** — 文件名/frontmatter schema、置信度阶梯（kernel 0.90 / instance 0.85 / exploration 0.75）、状态机、集成矩阵、grandfather 规则、废弃标准（由 L13 lint 执行） | **[ACTIVE] [CONTRACT]** |
| `docs/WORKFLOW.md` | 工作流手册（十二原则 W1-W12 + 进化引擎 + 会话流程） | [ACTIVE] |

### 框架知识文档
| 文档 | 内容 | 状态 |
|------|------|------|
| `docs/theory.md` | Clark & Chalmers + Argyris + Polanyi 理论基础 | [ACTIVE] |
| `docs/architecture.md` | 四支柱 + 进化引擎技术细节 + 文档总索引 | [ACTIVE] |
| `docs/vision.md` | 愿景 + 定位 + 菌丝比喻 | [ACTIVE] |
| `docs/evolution_engine.md` | 四齿轮详述 (v2.1)，权限级别说明 | [ACTIVE] |
| `docs/reusable_system_design.md` | 通用知识系统架构 v2.1，Bootstrap 指南（来自 ASCC Gear 4 蒸馏） | [ACTIVE] |
| `docs/research_paper_craft.md` | 科研绘图方法 + 写作技法（适用于学术项目类型，来自 ASCC Gear 4 蒸馏） | [ACTIVE] |
| `docs/open_problems.md` | **诚实登记册** — 结构性 blind spots（inlet 冷启动 / 触发信号 / 对齐 / 压缩工程 / Self Model C 结构退化 / D 死知识）。不是 feature backlog；是 **尚未收敛到可辩论阶段** 的根本盲点 | [ACTIVE] |

### 辩论记录（docs/primordia/）
> 生命周期标签：`[ACTIVE]` 仍在使用 | `[COMPILED]` 结论已编译到 wiki | `[SUPERSEDED]` 被新版取代

| 文档 | 状态 | 内容 |
|------|------|------|
| `docs/primordia/positioning_craft_2026-04-09.md` | [ACTIVE] | **深度定位辩论（6 轮，92% 置信度）**：OpenClaw 威胁分析、tagline→metabolism、Gear 4 已验证 |
| `docs/primordia/decoupling_craft_2026-04-09.md` | [ACTIVE] | **ASCC/Myco 解耦辩论（3 轮，93% 置信度）**：边界判断 + 通用化替换策略 |
| `docs/primordia/decoupling_positioning_debate_2026-04-09.md` | [ACTIVE]（定位部分已被 positioning_craft supersede） | 解耦审计（13 CRITICAL 项）+ 热启动设计 + 早期定位辩论 |
| `docs/primordia/myco_self_apply_craft_2026-04-09.md` | [ACTIVE] | Myco 自我应用设计辩论（6 项决策，综合置信度 88%） |
| `docs/primordia/gear3_v090_milestone_2026-04-09.md` | [ACTIVE] | Gear 3 里程碑回顾：3 项被证伪假设 + 5 项行动（全部 ✅） |
| `docs/primordia/examples_design_craft_2026-04-09.md` | [ACTIVE] | examples/ 设计辩论：Gear 4 生命周期展示定位 + 社区管线，置信度 84% |
| `docs/primordia/adoption_community_craft_2026-04-09.md` | [LOCAL] | 一键采用+社区生态辩论（4轮，87%置信度）|
| `docs/primordia/v1_scope_craft_2026-04-09.md` | [LOCAL] | v1.0 scope 辩论（4轮，89%置信度）|
| `docs/primordia/v1_1_scope_craft_2026-04-09.md` | [LOCAL] | v1.1 scope 辩论（3轮，87%置信度）|
| `docs/primordia/readme_craft_2026-04-10.md` | [LOCAL] | README 重写策略（4轮，87%置信度）|
| `docs/primordia/brand_craft_2026-04-10.md` | [LOCAL] | 品牌视觉策略（4轮，88%置信度）|
| `docs/primordia/launch_craft_2026-04-10.md` | [LOCAL] | 发布策略（2轮，87%置信度）|
| `docs/primordia/vision_recovery_craft_2026-04-10.md` | **[ACTIVE] [ANCHOR]** | **愿景恢复辩论（4轮，≥92%置信度）**：三次递归 extraction 发现 **18 项**被压缩丢失的愿景元素，含 substrate / CPU / 非参数进化 / 代谢入口 / 七步管道含淘汰 / 压缩即认知 / 四层自我模型 / kernel-instance split / mutation-selection / anti-cancer / 盲点列表 / 理论血统。**每次上下文压缩后必读**。 |
| `docs/primordia/upstream_protocol_craft_2026-04-11.md` | [ACTIVE] | **Upstream Protocol v1.0 辩论**（实例→内核回灌通道，contract v1.2.0 落地） |
| `docs/primordia/craft_formalization_craft_2026-04-11.md` | **[ACTIVE] [CONTRACT]** | **W3 Craft Protocol 形式化辩论（3轮，91%置信度）**：Craft 正式命名为 Craft Protocol v1，配套 schema + L13 lint + grandfather 规则。meta-dogfood（bootstrap 豁免 `craft_protocol_version`）。contract v1.3.0 落地。 |

> `[LOCAL]` 标签表示仅存在于本地，不纳入远端仓库（.gitignore 排除）。

---

## 4. 脚本索引

| 脚本 | 用途 |
|------|------|
| `scripts/lint_knowledge.py` | 14 维度自动化一致性检查（对照 `_canon.yaml`） |
| `scripts/myco_init.py` | 项目初始化脚本 |
| `scripts/myco_migrate.py` | 从 CLAUDE.md 等迁移 |
| `scripts/compress_original.py` | 知识压缩工具 |

---

## 5. 会话规程

**新会话启动**：读本文件热区 → 看任务队列 → 按优先级工作。需要具体知识时读 `docs/` 或 `wiki/` 页面。

**会话结束**：
1. **更新任务队列**（最优先）
2. **追加 log.md**（关键事件一行记录）
3. 更新 §1 进度
4. 新 Bug/决策 → `wiki/` 对应页面或 `docs/primordia/`
5. Gear 2 反思："框架本身哪里可以改进？" → `log.md` `meta` 条目
6. **Gear 4 sweep**：扫描 log.md 中 `g4-candidate` 条目 → 写入 `docs/` 或标注 `g4-pass: [原因]`
7. 长会话 → `python scripts/lint_knowledge.py --project-dir .`
