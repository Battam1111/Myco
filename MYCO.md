# Myco

> 最后更新：2026-04-10
> **知识系统**：[Myco](https://github.com/Battam1111/Myco) v0.9.0（框架自用）

---

## 🔥 热区

**项目**：Myco — 可自进化的 AI 延伸认知基质（框架本身）
**当前阶段**：v1.1.0 released — preparing public launch + v1.2 roadmap

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
8. **永久锚点文档**：详细愿景恢复记录见 `docs/current/vision_recovery_craft_2026-04-10.md`——这是防漂移的永久锚点，18 项丢失元素全部在里面有原文引证。**任何一次上下文压缩后第一件事是重读它。**

**Agent 行为准则**：
- **即时沉淀** — 关键决策当下写入文档，不等会话结束
- **在线验证** — 数字型 claim 必须 WebSearch 交叉验证
- **Gear 4 意识** — 解决耗时 ≥2 轮的问题后，在 log 条目末尾标记 `→ g4-candidate`
- **自主权边界** — ✅ 技术执行/Bug/文档 | 📢 工作流微调 | 🛑 框架方向/API 设计/破坏性变更

**🎯 Operational Feel**：
Python 打包环境（hatchling + twine）。模板唯一来源：`src/myco/templates/`（打包入 wheel）。
`pip install -e .` 后 `myco` CLI 指向 `src/`，无需 build 即可测试。

---

## 📋 任务队列（硬上限 5 项）

| # | 状态 | 任务 | 备注 |
|---|------|------|------|
| 1 | ✅ | **v1.2 消化道 Phase ① 消化道闭环** ▰▰▱：eat/digest/view/hunger + notes/ + L10 + MCP ×4 | **落地 2026-04-10**，22 notes、3 deep-digest、1 非线性 raw→integrated、1 excreted with reason、L10 绿灯 |
| 2 | ⏳ | v1.2 消化道 Phase ② 摩擦驱动迭代 ▰▰▱：根据 ① 真实数据决定 extract/integrate 等新器官 | 门槛：Phase ① 验收 ≥ 50% |
| 3 | ⏳ | v1.2 消化道 Phase ③ Commons 上线 ▰▰▰：commons/ + promote/craft use + L11/L12 + HPC lesson 洗仓 | 门槛：Phase ② 收敛稳定 |
| 4 | 📐 | **Metabolic Inlet 原语（身份级声明）** | v2.0，不阻塞 Phase ①-③ |

> **节奏说明**：Phase 之间的切换由**硬验收指标**触发，不由日历驱动。我们的推进速度由 Gear 1 摩擦信号决定——可能数小时，可能数日。任一 Phase 验收 < 50% 即回炉。

### 任务 4 详述 · Metabolic Inlet

**性质**：身份级 primitive 声明，不是功能承诺。理由：齿轮 1-4 完全内向（friction → reflect → retrospect → distill），没有任何一档朝向外部世界。一个没有消化系统的基质只是缓存，不是基质。现在不声明，外部贡献者会把 Myco 建成"更好的 CLAUDE.md"；声明后但不提前实现，避免违反 Bitter Lesson 立场（机制必须从第一性原理浮现，不能手工设计）。

**形状**（草图，v2.0 设计辩论时再细化）：
- **触发**：摩擦信号（agent 在 wiki/canon/log 找不到答案）OR 周期巡逻（时间/事件驱动）
- **目标源**：GitHub 仓库、arXiv、社区文档、上游工具发布说明
- **管道**：发现 → 评估（相关性/质量/新颖性）→ 萃取（模式，不是复制）→ 整合（融入 wiki/canon，不追加）→ 压缩 → 验证（lint）
- **不变量**：所有摄取过的内容必须通过现有 9 维 lint；任何降低 lint pass 率的摄取必须被拒绝
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

## 📖 知识系统架构

| 层级 | 位置 | 加载方式 | 说明 |
|------|------|---------|------|
| **L1 Index** | 本文件（MYCO.md） | 自动加载 | 纯索引 + schema，agent-agnostic |
| **L1.5 Wiki** | `wiki/*.md` | 按需读取 | 结构化知识页（有机生长，现为空） |
| **L2 Docs** | `docs/*.md` + `docs/current/*.md` | 按需读取 | 框架文档、辩论记录 |
| **L3 Code** | `src/myco/` + `scripts/` | 按需读取 | 包源码 + 工具脚本 |
| **Timeline** | `log.md` | 按需读取 | Append-only 时间线 |
| **Canon** | `_canon.yaml` | Lint 读取 | 规范值 Single Source of Truth |

---

## 0. 项目摘要

Myco 是一个可自进化的 AI 延伸认知基质框架。它给 AI agent 提供持久记忆、结构化知识和跨会话的自进化能力。v0.9.0 已发布 PyPI（`pip install myco`），提供 `myco init / migrate / lint` CLI。

核心设计：agent-agnostic（Claude、GPT、Codex 等均可运行），框架本身通过 Myco 管理自身的知识。

---

## 1. 当前进度

```
Phase 0  基础打包 + PyPI 上线        ✅ 完成 (v0.9.0, 2026-04-09)
Phase 1  自我应用 + 社区文件 + v1.0  ✅ 完成 (v1.0.0, 2026-04-09)
Phase 1b CLI 自动化 + v1.1           ✅ 完成 (v1.1.0, 2026-04-10)
Phase 2  Public Release              🔄 准备中
Phase 3  非 ASCC 项目示例            ⏳ v1.2 目标
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

### 辩论记录（docs/current/）
> 生命周期标签：`[ACTIVE]` 仍在使用 | `[COMPILED]` 结论已编译到 wiki | `[SUPERSEDED]` 被新版取代

| 文档 | 状态 | 内容 |
|------|------|------|
| `docs/current/positioning_craft_2026-04-09.md` | [ACTIVE] | **深度定位辩论（6 轮，92% 置信度）**：OpenClaw 威胁分析、tagline→metabolism、Gear 4 已验证 |
| `docs/current/decoupling_craft_2026-04-09.md` | [ACTIVE] | **ASCC/Myco 解耦辩论（3 轮，93% 置信度）**：边界判断 + 通用化替换策略 |
| `docs/current/decoupling_positioning_debate_2026-04-09.md` | [ACTIVE]（定位部分已被 positioning_craft supersede） | 解耦审计（13 CRITICAL 项）+ 热启动设计 + 早期定位辩论 |
| `docs/current/myco_self_apply_craft_2026-04-09.md` | [ACTIVE] | Myco 自我应用设计辩论（6 项决策，综合置信度 88%） |
| `docs/current/gear3_v090_milestone_2026-04-09.md` | [ACTIVE] | Gear 3 里程碑回顾：3 项被证伪假设 + 5 项行动（全部 ✅） |
| `docs/current/examples_design_craft_2026-04-09.md` | [ACTIVE] | examples/ 设计辩论：Gear 4 生命周期展示定位 + 社区管线，置信度 84% |
| `docs/current/adoption_community_craft_2026-04-09.md` | [LOCAL] | 一键采用+社区生态辩论（4轮，87%置信度）|
| `docs/current/v1_scope_craft_2026-04-09.md` | [LOCAL] | v1.0 scope 辩论（4轮，89%置信度）|
| `docs/current/v1_1_scope_craft_2026-04-09.md` | [LOCAL] | v1.1 scope 辩论（3轮，87%置信度）|
| `docs/current/readme_craft_2026-04-10.md` | [LOCAL] | README 重写策略（4轮，87%置信度）|
| `docs/current/brand_craft_2026-04-10.md` | [LOCAL] | 品牌视觉策略（4轮，88%置信度）|
| `docs/current/launch_craft_2026-04-10.md` | [LOCAL] | 发布策略（2轮，87%置信度）|
| `docs/current/vision_recovery_craft_2026-04-10.md` | **[ACTIVE] [ANCHOR]** | **愿景恢复辩论（4轮，≥92%置信度）**：三次递归 extraction 发现 **18 项**被压缩丢失的愿景元素，含 substrate / CPU / 非参数进化 / 代谢入口 / 七步管道含淘汰 / 压缩即认知 / 四层自我模型 / kernel-instance split / mutation-selection / anti-cancer / 盲点列表 / 理论血统。**每次上下文压缩后必读**。 |

> `[LOCAL]` 标签表示仅存在于本地，不纳入远端仓库（.gitignore 排除）。

---

## 4. 脚本索引

| 脚本 | 用途 |
|------|------|
| `scripts/lint_knowledge.py` | 9 维度自动化一致性检查（对照 `_canon.yaml`） |
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
4. 新 Bug/决策 → `wiki/` 对应页面或 `docs/current/`
5. Gear 2 反思："框架本身哪里可以改进？" → `log.md` `meta` 条目
6. **Gear 4 sweep**：扫描 log.md 中 `g4-candidate` 条目 → 写入 `docs/` 或标注 `g4-pass: [原因]`
7. 长会话 → `python scripts/lint_knowledge.py --project-dir .`
