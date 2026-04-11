# 传统手艺：ASCC/Myco 解耦 — 边界与执行策略

> **文档状态**：[ACTIVE] | 创建：2026-04-09
> **置信度目标**：>90%
> **前置审计**：全代码库 ASCC 残留扫描（今日执行）
> **关系**：decoupling_positioning_debate_2026-04-09.md 中已有 13 CRITICAL 审计清单；本文档补充"边界判断辩论"——确定哪些内容必须删除、哪些合法保留、用什么替换。

---

## 审计现状（今日扫描结果）

大部分 CRITICAL 项已在前序会话中清理完毕：

| 原 CRITICAL 项 | 当前状态 |
|--------------|---------|
| examples/ascc/README.md 整体 | ✅ 已重写为脱敏案例研究 + Gear 4 反向链接 |
| README.md ASCC 统计数据 | ✅ 已替换为 "a multi-month research project" |
| LICENSE 个人名字 | ✅ 已改为 "Myco Contributors" |
| docs/theory.md | ✅ 完全通用化，零 ASCC 特定内容 |
| docs/vision.md | ✅ 完全通用化 |
| docs/v09_planning_debate | ✅ 该文件不存在于开源仓库 |

**仍存在 ASCC 特定内容的文件：**

| 文件 | 级别 | 具体泄漏 |
|-----|------|---------|
| `docs/evolution_engine.md` | MEDIUM | g4-candidate 示例（badge/axes/ylim）、Gear 4 萃取示例（算法消融/实验调度器/三层axes）、事例 2（固定参数/消融组/P4/P5）、roadmap"(来自 Caveman)" |
| `docs/architecture.md` | LOW | Header "ASCC 项目深度验证" + 触发示例 "实验阶段完成（P3/P4/P5）" |
| `docs/primordia/` ASCC-era debates | 待定 | 3 个文件含 ASCC 项目特定上下文（P4 midterm, system_state, llm_wiki, nuwa_caveman） |

---

## Round 1：边界辩论 — "什么必须零容忍"

### 1.1 零容忍边界（必须删除/替换）

**主张**：以下类型的内容必须从开源框架文档中清零：

1. **未脱敏的 ASCC 专有技术术语**（算法消融设计、大规模实验调度器、P4/P5 阶段编号、badge/axes/ylim matplotlib 专属词）
2. **"Caveman"项目名称**（是 ASCC 的代号，不应出现在通用框架文档中）
3. **暗示 Myco "只在 ASCC 验证"的声明**（architecture.md header 只提 ASCC 项目验证）

**挑战 C1**：examples/ascc/ 作为案例研究已经合法化了 ASCC 的存在，为什么 framework docs 里的 ASCC 示例就是问题？

**回应**：区别在于**读者的引导效果**：
- examples/ascc/ = "这是一个用 Myco 做的项目，看它是怎么用的" → 合法
- evolution_engine.md 中的"badge 被 axes ylim 截断" = "这是 Myco 框架的用法示例，用了学术图表专属术语" → 导致用户误解 Myco 是学术图表工具

框架文档的示例应该让**任何项目类型**的用户产生共鸣。学术图表专属术语排斥了软件开发者、数据分析师等用户。

**结论**：零容忍边界成立。置信度 95%。

### 1.2 允许保留的内容

**主张**：以下内容允许保留：

1. **docs/primordia/ 中的 ASCC-era 辩论记录**——这些是 Myco 框架设计历史，不是 ASCC 项目知识：
   - `system_evolution_debate_2026-04-08.md`（Myco 命名辩论 + 进化引擎设计）✅
   - `generalization_debate_2026-04-07.md`（通用化架构设计）✅
   - `tacit_knowledge_debate_2026-04-07.md`（W6 近端丰富化设计）✅
   - `vision_debate_2026-04-08.md`（愿景设计）✅

2. **对 ASCC 项目的通用性引用**（如 architecture.md 改为"a complex research project (ASCC, examples/ascc/)"——这是透明的来源标注，不是泄漏）

**挑战 C2**：docs/primordia/ 中有 4 个文件名明确含 ASCC 意味（retrospective_p4_midterm, system_state_assessment, llm_wiki_debate, nuwa_caveman）——它们应该留在这里吗？

**回应**：关键判断标准——这些文件的**主题**是什么？
- `retrospective_p4_midterm_2026-04-07.md`：这是 ASCC Phase 4 的回顾，不是 Myco 框架辩论 → 应该属于 ASCC 项目仓库，但作为 Myco 设计史料可以保留（有 ASCC 项目使用 Myco 的原始记录价值）
- `nuwa_caveman_integration_2026-04-07.md`：讨论将 Nuwa/Caveman 机制集成到 Myco → 是 Myco 设计辩论，合法保留
- `llm_wiki_debate_2026-04-07.md`：讨论 LLM wiki 结构 → 是 Myco wiki 系统设计，合法保留
- `system_state_assessment_2026-04-07.md`：ASCC 系统状态评估 → 含较多 ASCC 专属内容

**裁判**：以下 4 个文件的保留策略：

| 文件 | 判断 | 处理 |
|-----|------|------|
| `retrospective_p4_midterm_2026-04-07.md` | ASCC 项目记录 > Myco 框架设计 | 在 docs/primordia/README.md 中标注"[ASCC-era project record, historical reference]"即可保留 |
| `system_state_assessment_2026-04-07.md` | 明显 ASCC 专属 | 同上处理（不删除，但明确标注） |
| `nuwa_caveman_integration_2026-04-07.md` | Myco 框架设计辩论 | 保留 [ACTIVE] 标签 |
| `llm_wiki_debate_2026-04-07.md` | Myco 框架设计辩论 | 保留 [ACTIVE] 标签 |

**结论**：docs/primordia/ 文件全部保留，通过 README.md 标签区分 Myco 框架记录 vs ASCC 项目记录。置信度 90%。

---

## Round 2：替换策略 — 用什么替代 ASCC 具体示例？

### 2.1 原则

好的通用示例必须满足：
- **覆盖三种项目类型**：学术/研究型、软件产品型、数据分析型
- **不能都是研究场景**（原 ASCC 例子全是研究场景）
- **保留示例的教学功能**（示例要能准确说明 Friction 和 Gear 4 的运作方式）

### 2.2 evolution_engine.md 的替换方案

**位置 1：g4-candidate 示例**（当前：badge 被 axes ylim 截断）

替换为两个示例（覆盖研究和软件两种场景）：
```
## [2026-04-09] friction | [操作摩擦] API 限流机制重构了两次才稳定；第三次发现需要指数退避 → g4-candidate
## [2026-04-09] friction | [知识断裂] 配置文件格式变化导致三个模块同时失效；找根因花了 40 分钟 → g4-candidate
```

**位置 2：Gear 4 萃取示例**（当前：axes 布局、算法消融、实验调度器）

替换为：
```
✅ "API 限流退避策略"（通用）→ reusable_system_design.md
✅ "跨平台脚本字符编码验证协议"（通用）→ reusable_system_design.md
❌ "特定数据库的表结构设计"（项目特定）→ 保留在项目 wiki
❌ "产品 A 的竞品分析"（项目特定）→ 存档，不通用化
```

**位置 3：事例 2 Gear 3 决策循环**（当前：固定参数/消融组/P4）

替换为软件项目场景：
```
[2026-04-15] meta | "模块间耦合度过高"的假设被证伪；架构重构耗时远超预期 → 触发 Gear 3

Gear 3 Q1：假设"微服务拆分足够解耦"被证伪 ✓
Gear 3 Q2：wiki/api_design.md 中接口定义有 3 处已废弃 ✓
Gear 3 Q3：Agent 权限不够修改跨模块 API 文档，导致发现延迟 ✓
结果：重构接口设计规范，权限扩展至 Agent 可更新接口文档
```

**位置 4：路线图 "(来自 Caveman)"**

替换为：
```
v2.5: `.original.md` 双层架构——人类编辑原始版，自动压缩为 Agent 版
```
（去掉"来自 Caveman"，只保留机制描述）

### 2.3 architecture.md 的替换方案

**位置 1：Header 验证基础**
```
当前：ASCC 项目深度验证（7天，80+文件，12+次传统手艺）；多项目泛化进行中
替换：一个复杂研究项目深度验证（7天，80+文件，12+次传统手艺，含完整四齿轮进化）；泛化验证进行中。参见 examples/ascc/
```

**位置 2：Gear 3 触发**
```
当前：触发周期：重大发布 / P4 完成 / 外部评审等
替换：触发周期：重大发布 / Phase 转换完成 / 外部评审等
```

**位置 3：Gear 2 log 示例**
```
当前：## [2026-04-08] meta | 实验参数调整需要改 5 个文件同步，易出错
替换：## [2026-04-08] meta | 配置项修改需要更新 5 个文件同步，易出错；建议统一到 _canon.yaml
```

### 2.4 Round 2 结论

替换策略清晰：用三种项目类型（研究/软件/数据）的通用示例替代 ASCC 专属内容。置信度 92%。

---

## Round 3：关于 docs/primordia/ 中 ASCC-era 辩论文件的最终决策

**挑战 C3（自我挑战）**：`retrospective_p4_midterm_2026-04-07.md` 这类文件不只是"有点 ASCC 的味道"——它们的标题就是 ASCC 项目活动记录。开源框架 repo 里留着 "P4 midterm retrospective" 对新用户是什么信号？

**回应**：

这是一个 README 工程问题，不是内容删除问题。

当前 docs/primordia/ 没有 README.md 区分文件性质。只要在 docs/primordia/README.md 中清晰说明：
> "The files below marked [ASCC-era] are historical records from the project that incubated Myco. They document real evolution decisions — the design rationale they contain is authentic — but they reference an internal project called 'ASCC'. These are kept for research transparency, not as usage examples."

这样开源用户就能理解这些文件的性质。不需要删除。

**检查**：docs/primordia/ 是否有 README.md？从上面的 ls 结果看——有！`README.md` 已经在列表里。

需要更新该 README.md 添加分类标签。

**最终决策**：
- evolution_engine.md: 替换 4 处 ASCC 专属内容 → 通用化示例
- architecture.md: 修改 3 处（header + P4/P5 + meta 示例）
- docs/primordia/README.md: 添加 ASCC-era 文件分类说明

**综合置信度：93%**

---

## 行动清单（传统手艺 → 执行）

| # | 文件 | 操作 | 优先级 |
|---|------|------|--------|
| A1 | docs/evolution_engine.md | 替换 4 处 ASCC 专属内容（g4-candidate示例、萃取示例、事例2、Caveman引用） | CRITICAL |
| A2 | docs/architecture.md | 修改 3 处（验证header、触发P3/P4/P5、meta log示例） | LOW |
| A3 | docs/primordia/README.md | 添加 ASCC-era 文件分类说明 | LOW |
