# Myco

> 最后更新：2026-04-09
> **知识系统**：[Myco](https://github.com/Battam1111/Myco) v0.9.0（框架自用）

---

## 🔥 热区

**项目**：Myco — 可自进化的 AI 延伸认知基质（框架本身）
**当前阶段**：Phase 1 — v0.9.0 已发布 PyPI，准备 v1.0

**框架开发中最容易出错的 N 件事** ⚠️：
1. 修改 `src/myco/templates/` 后忘记同步 `templates/`（两处模板，必须同步）
2. 更新 `pyproject.toml` 版本号但忘记同步 `src/myco/__init__.py`
3. 在 MYCO.md 里写"已实现"的功能，实际上是 roadmap（诚实原则）
4. 运行 `myco lint` 检查 Myco 自身时，`--project-dir` 指向 repo 根，不是 `src/` 子目录

**Agent 行为准则**：
- **即时沉淀** — 关键决策当下写入文档，不等会话结束
- **在线验证** — 数字型 claim 必须 WebSearch 交叉验证
- **Gear 4 意识** — 解决耗时 ≥2 轮的问题后，在 log 条目末尾标记 `→ g4-candidate`
- **自主权边界** — ✅ 技术执行/Bug/文档 | 📢 工作流微调 | 🛑 框架方向/API 设计/破坏性变更

**🎯 Operational Feel**：
Python 打包环境（hatchling + twine）。模板有**两处**：`templates/`（开发源）和 `src/myco/templates/`（打包入 wheel），改模板必须同步两处。
`pip install -e .` 后 `myco` CLI 指向 `src/`，无需 build 即可测试。
上传 PyPI：`chcp 65001 && set PYTHONIOENCODING=utf-8 && python -m twine upload dist/*`

---

## 📋 任务队列（硬上限 5 项）

| # | 状态 | 任务 | 备注 |
|---|------|------|------|
| 1 | ✅ | v0.9.0 发布 PyPI | 已完成 2026-04-09 |
| 2 | 🔄 | 完成 Myco 自我应用（myco migrate self） | 传统手艺已完成，文件写入中 |
| 3 | ⏳ | examples/ 非 ASCC 软件项目示例 | 后续会话规划 |
| 4 | ⏳ | v1.0 发布（agent-agnostic 验证 + GPT/Cursor adapter） | 中期目标 |

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
| `docs/current/decoupling_positioning_debate_2026-04-09.md` | [ACTIVE] | 6 轮竞品分析 + 定位辩论，置信度 90% |
| `docs/current/myco_self_apply_craft_2026-04-09.md` | [ACTIVE] | Myco 自我应用设计辩论（6 项决策，综合置信度 88%） |

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
