# 传统手艺：系统一般化 + 自进化引擎设计
> **Status**: ARCHIVED (compiled to formal docs)

> **日期**：2026-04-07
> **轮数**：4 轮
> **最终置信度**：~85%
> **产出**：reusable_system_design.md v2.0 + wiki/evolution_engine.md + project_template/

---

## 辩论 1：一般化架构

### 初始主张

三支柱（Schema/Knowledge/Experience）+ 四层（L1→L3 + L0）本质已通用。一般化需要：抽取（分离 ASCC 特有内容）、参数化（项目身份/阶段/wiki 类型可配置）、提供梯度（最小可行版 → 逐步解锁）。

### 攻击 1：传统手艺不通用
W3 的 4 个案例全是论文场景。换成软件工程项目，触发信号、攻防案例全部失效。

### 防御
承认。修正：机制（多轮攻防 + 在线调研）是通用的，触发信号和案例必须参数化。一般化模板只提供抽象触发类别 + 空案例占位符。新增"触发信号校准"步骤（项目启动 2 周后回顾）。

### 攻击 2：CLAUDE.md 80 行硬限
Cursor 社区经验表明 >80 行模型开始忽略。ASCC 193 行矛盾。

### 防御
80 行限制来自 Cursor 的 rules 注入窗口，Claude 的 context window 远大于此。193 行在 ASCC 中工作良好。但信号值得重视——新增分级模板：Minimal ~50 行 / Standard ~150 行 / Full ~300 行上限。

### 攻击 3：_canon.yaml 混合参数
项目参数（P4 进度）和系统参数（wiki 页面数）混在一起，一般化时两类需分离。

### 防御
承认。修正：_canon.yaml 分 `system:` 和 `project:` 两节。

---

## 辩论 2：自进化引擎

### 初始主张

自进化需要四层：感知（哪里不好）→ 反思（怎么改）→ 行动（写入系统）→ 验证（下次用时确认）。

### 攻击 4：缺少 Double-loop
Argyris 核心洞察：人/系统倾向 Single-loop。W7 Lint 是典型 Single-loop——检查数字一致性，不质疑"为什么三处记录同一个数字"。缺少质疑架构假设的机制。

### 防御
这是最深刻的攻击。引入 Architecture Retrospective（Gear 3）作为 Double-loop：每个里程碑后回答三个问题（假设审查 / 摩擦聚类 / 重新设计）。产出不是修补文档，而是修改原则或 schema。

### 攻击 5：失败复盘不足
ERL 论文发现失败启发式 > 成功启发式。operational_narratives 仅 3 个，触发门槛 ≥2 次失败太高。

### 防御
部分承认。引入两级机制：Gear 1 Friction Sensing（一句话记录，门槛极低）+ 保持 operational_narratives 的 ≥2 次失败阈值。同类 friction ≥3 次自动升级。

---

## 在线调研关键发现

| 来源 | 关键洞察 | 采纳程度 |
|------|---------|---------|
| Voyager (FAIR 2023) | 技能库持续增长，代码即技能 | ✅ Pattern Names 机制 |
| ERL (ArXiv 2025) | 失败启发式 > 成功启发式，+7.8% | ✅ Friction Sensing 设计依据 |
| AutoAgent | Cognitive Evolution 闭环 | ✅ 四齿轮架构参考 |
| Argyris (1977) | Double-loop：改心智模型而非仅改行为 | ✅ Gear 3 设计依据 |
| Senge (1990) | 系统思维——看关系而非事件 | ✅ Gear 4 跨项目蒸馏依据 |
| Toyota PDCA | Plan-Do-Check-Act 持续循环 | ✅ 整体进化引擎的节奏参考 |
| CLAUDE.md 社区 | ≤60-80 行硬限 | ⚠️ 仅适用于 Cursor，Claude 可更长。采纳为分级模板 |
| SICA (2025) | Agent 直接编辑自身源码 | ⏳ 留作 v3.0+ 参考（当前太激进） |

---

## 风险评估

| 风险 | 概率 | 防御 |
|------|------|------|
| 过度工程化 | ~40% | 渐进式实现，先只加 Gear 1+2 |
| Bootstrap 成本过高 | ~30% | 分级 Bootstrap（Level 0/1/2） |
| 自进化→自腐化 | ~20% | 权限分级，核心原则需人类确认 |
| 跨项目丢失"为什么" | ~50% | 每个组件附 Design Rationale |

---

## 最终结论

**架构**：四支柱 + 自进化引擎（L-meta）
- Pillar 1 Schema（CLAUDE.md 分级 + _canon.yaml 分 system/project）
- Pillar 2 Knowledge（wiki + docs/primordia，传统手艺触发信号参数化）
- Pillar 3 Experience（叙事 + Priming + Pattern Names）
- Pillar 4 Timeline + Infrastructure（log.md 新增 friction/meta 类型）
- L-meta Evolution Engine（四齿轮：Friction → Reflection → Retrospective → Distillation）

**置信度**：~85%

**残余风险**：过度工程化是最大风险，用渐进实现对冲。
