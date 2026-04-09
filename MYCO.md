# Myco

> 最后更新：2026-04-09
> **知识系统**：[Myco](https://github.com/Battam1111/Myco) v0.9.0（框架自用）

---

## 🔥 热区

**项目**：Myco — 可自进化的 AI 延伸认知基质（框架本身）
**当前阶段**：Phase 1 — v0.9.0 已发布 PyPI，准备 v1.0

**框架开发中最容易出错的 N 件事** ⚠️：
1. 更新 `pyproject.toml` 版本号但忘记同步 `src/myco/__init__.py`（两处版本号必须一致）
2. 在 MYCO.md 里写"已实现"的功能，实际上是 roadmap（诚实原则）
3. 运行 `myco lint` 检查 Myco 自身时，`--project-dir` 指向 repo 根，不是 `src/` 子目录
4. 修改模板后忘记 rebuild + 重新 `pip install -e .`（本地测试时 importlib.resources 读的是 src/，无需 build；但 wheel 测试必须重建）

**对外定位一句话**（供 agent 快速了解 Myco 的市场位置）：
> "Other tools give AI agents memory. Myco gives them metabolism — consistency checking, structural evolution, and cross-project distillation that no other tool does."
> OpenClaw (346K stars) = 存储层验证；Myco = 进化层，不竞争，是升级路径。

**Agent 行为准则**：
- **即时沉淀** — 关键决策当下写入文档，不等会话结束
- **在线验证** — 数字型 claim 必须 WebSearch 交叉验证
- **Gear 4 意识** — 解决耗时 ≥2 轮的问题后，在 log 条目末尾标记 `→ g4-candidate`
- **自主权边界** — ✅ 技术执行/Bug/文档 | 📢 工作流微调 | 🛑 框架方向/API 设计/破坏性变更

**🎯 Operational Feel**：
Python 打包环境（hatchling + twine）。模板唯一来源：`src/myco/templates/`（打包入 wheel）。
`pip install -e .` 后 `myco` CLI 指向 `src/`，无需 build 即可测试。
上传 PyPI：`chcp 65001 && set PYTHONIOENCODING=utf-8 && python -m twine upload dist/*`

---

## 📋 任务队列（硬上限 5 项）

| # | 状态 | 任务 | 备注 |
|---|------|------|------|
| 1 | ✅ | v0.9.0 发布 PyPI | 完成 2026-04-09 |
| 2 | ✅ | Myco 自我应用（myco migrate self + Gear 3） | 完成 2026-04-09，lint L0-L8 全绿 |
| 3 | ✅ | 双模板单一化（删除顶层 templates/） | 完成 2026-04-09（Gear 3 A2） |
| 4 | ✅ | 深度竞品定位传统手艺（6 轮，92% 置信度） | 完成 2026-04-09，tagline→metabolism，Gear 4 已验证 |
| 5 | ✅ | ASCC/Myco 解耦（框架文档通用化，evolution_engine 4 处 + architecture 1 处） | 完成 2026-04-09，lint L0-L8 全绿 |
| 6 | ✅ | 一键采用 + 社区生态（adapters/ 目录 + CONTRIBUTING.md 四类型 + README Quick Start 重构） | 完成 2026-04-09 |
| 7 | ✅ | v1.0 发布（agent-agnostic 适配：cursor.yaml + gpt.yaml + migrate aha moment + 版本号 1.0.0） | 完成 2026-04-09 |
| 8 | ✅ | v1.1 CLI 自动化（myco config + myco import --from hermes/openclaw + _canon.yaml [adapters] 节） | 完成 2026-04-09 |
| 9 | 🔄 | **Public Release 准备**（B1-B6 进行中） | B1✅ B2✅ B3✅ B4✅ B5✅ B6✅ → 待 commit+push |

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
Phase 0  基础打包 + PyPI 上线     ✅ 完成 (2026-04-09)
Phase 1  自我应用 + 社区文件       🔄 进行中
Phase 2  非 ASCC 项目示例          ⏳ 待实现
Phase 3  v1.0 agent-agnostic 验证 ⏳ 待实现
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
| `docs/current/adoption_community_craft_2026-04-09.md` | [ACTIVE] | **一键采用+社区生态辩论（4轮，87%置信度）**：adapter YAML 接口、四类贡献体系、30秒采用路径、GitHub presence |
| `docs/current/v1_scope_craft_2026-04-09.md` | [ACTIVE] | **v1.0 scope 辩论（4轮，89%置信度）**：MVP三项充分条件（migrate aha moment / cursor+gpt adapter / agent-neutral声明升级）；v1.1推迟项（myco config/ingest/MemPalace CLI） |
| `docs/current/readme_craft_2026-04-10.md` | [ACTIVE] | **README 重写策略（4轮，87%置信度）**：Hero=问题→方案→tagline / Quick Start 两阶段展示 / 深度内容迁出至 architecture.md |
| `docs/current/brand_craft_2026-04-10.md` | [ACTIVE] | **B2 品牌视觉策略（4轮，88%置信度，在线调研支持）**：Metabolic Cartography 设计哲学、色彩系统 #0D1117+#00D4AA、Hyphal Node logo、Social Preview 1280×640 |
| `docs/current/launch_craft_2026-04-10.md` | [ACTIVE] | **B6 发布策略（2轮，87%置信度，在线调研支持）**：Show HN 先行 + r/LocalLLaMA 次之 + 首发文案 + 冷启动种子 + FAQ 预案 |

---

## Task 9 细项：Public Release 准备（B 阶段）

> 状态：🔄 执行中 | 优先级：高 | 前置：v1.1.0 ✅
> 目标：仓库从 Private → Public 时，第一印象足够好，能留住真实用户

### B1 — README 重写 ✅ 完成 2026-04-10
Hero = 问题→方案→tagline，Quick Start 两阶段展示，深度内容迁入 docs/architecture.md Appendix A-E。
详见 `docs/current/readme_craft_2026-04-10.md`

### B2 — 品牌形象 ✅ 完成 2026-04-10
- `assets/logo_dark.svg` + `assets/logo_light.svg`（Hyphal Node 菌根节点图标）
- `assets/social_preview.png`（1280×640，菌网图 + tagline + pip install）
- `assets/architecture.png`（四层架构图，嵌入 README）
详见 `docs/current/brand_craft_2026-04-10.md`

### B3 — GitHub 仓库元数据 ✅ 完成 2026-04-10
仓库 Public 时手动配置：
- About: "Metabolism for AI agents — lint checks, structural evolution, cross-project distillation."
- Topics: ai, agents, knowledge-management, self-evolving, claude, llm, memory, claude-code
- Social Preview: 上传 `assets/social_preview.png`
- Website: https://pypi.org/project/myco/

### B4 — examples/ 质量 ✅ 审查完成 2026-04-10
examples/ascc/ 内容已审查，无敏感信息，可公开。
待办：至少 1 个软件开发项目示例（v1.2 里程碑，非本次优先级）

### B5 — GitHub Community Files ✅ 完成 2026-04-10
- Issue templates：Bug / Feature / Battle Report / Adapter 提交（4 个）
- Discussion templates：Ideas / Show & Tell（2 个）
- SECURITY.md + CODE_OF_CONDUCT.md

### B6 — 发布时机策略 ✅ 完成 2026-04-10
Show HN（W1 周二）→ r/LocalLLaMA（W1 周四）→ r/ClaudeAI（W1 周五）→ Twitter/X（M1）
详见 `docs/current/launch_craft_2026-04-10.md`
- 首发文案草稿
- 首批 maintainer response 准备（FAQ、常见问题预案）

---

| `docs/current/v1_1_scope_craft_2026-04-09.md` | [ACTIVE] | **v1.1 scope 辩论（3轮，87%置信度）**：myco config（adapters.*隔离）/ myco import 半自动化设计 / headless兼容性确认；推迟：--adapter generic（v1.2）、MemPalace CLI（v1.2） |

---

## 4. 脚本索引

| 脚本 | 用途 |
|------|------|
| `scripts/lint_knowledge.py` | 9 维度自动化一致性检查（对照 `_canon.yaml`） |
| `scripts/pypi_upload.bat` | 一键上传至 PyPI（Windows，需 `~/.pypirc` 配置） |

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
