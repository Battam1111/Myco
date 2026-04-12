# 工作流手册

> 本文件定义项目的工作原则和流程。从 Myco 通用模板生成——按项目需要启用/禁用章节。
> Myco 框架参考：https://github.com/Battam1111/Myco
> 最后更新：2026-04-09

---

## 核心原则（十三原则 W1-W13）

| 原则 | 代号 | 核心一句话 |
|------|------|-----------|
| 自动沉淀 | W1 | 关键决策当下写入，不等会话结束 |
| 项目整洁 | W2 | 目录结构规范 + 命名规范 |
| 传统手艺 | W3 | 影响项目方向的决策必须多轮辩论 |
| 在线验证 | W4 | 数字型 claim 必须交叉验证 |
| 持续进化 | W5 | 重复→脚本化，遗失→强化，失败→记录 |
| 近端丰富化 | W6 | 失败路径是最有价值的知识 |
| 系统化 Lint | W7 | 定期检查文档一致性 |
| Wiki 标准模板 | W8 | 页眉（类型+日期+盲点）+ 页脚（Back to） |
| 活跃张力 | W9 | ⚡ 标记架构级矛盾（非 Bug，真实 trade-off） |
| 编译协议 | W10 | 外部知识 5 步提取流程 |
| 验证范围 | W11 | 结论标注"在哪些条件下验证过" |
| 信息密度 | W12 | 按任务复杂度调整上下文加载深度 |
| Primordia 压缩 | W13 | 每个 wave 响应 structural_bloat：压缩 OR 审计痕迹延迟 |

---

## W1: 自动沉淀

- 发现新 Bug → 立即写入 wiki/ 对应页面
- 做出关键决策 → 立即写入 entry document (MYCO.md/CLAUDE.md/等) 热区或 wiki
- 结果出来 → 立即更新进度
- 会话结束清单是"兜底检查"，不是唯一的沉淀时机

---

## W2: 项目整洁

### 目录结构

```
project-root/
├── MYCO.md                # L1 索引（默认入口，可选 CLAUDE.md 等）
├── _canon.yaml            # 规范值 SSoT
├── log.md                 # 时间线
├── docs/
│   ├── WORKFLOW.md        # 本文件
│   ├── operational_narratives.md  # 操作过程知识（Procedures）
│   └── current/           # 辩论/决策记录（不可变）
├── wiki/                  # 编译型知识页
├── scripts/               # 工具脚本
└── src/                   # 源代码
```

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 辩论记录 | `topic_YYYY-MM-DD.md` | `naming_debate_2026-04-02.md` |
| 工具脚本 | `verb_noun.py` | `check_results.py` |

---

## W3: 传统手艺（Craft）

**触发信号**：
- 影响项目核心方向的决策
- 对某个结论的置信度 < 80%
- 外部利益相关者可能质疑的薄弱点
- 在线调研发现了与当前方向冲突的信息

**流程**：
1. 陈述主张
2. 自我攻击（最严苛批评者角度）
3. 在线调研（WebSearch，外部证据）
4. 防御/修正
5. 迭代至所有攻击点有可信防御
6. 收尾：① 更新任务队列 ② 完整记录 → docs/primordia/ ③ 结论萃取 → wiki/MYCO.md ④ log.md

> **详细规范**：上述为人类可读流程摘要。正式 schema（文件名、frontmatter、置信度阶梯、状态机、集成点、废弃标准）见 `docs/craft_protocol.md`（Craft Protocol v1，参见 docs/craft_protocol.md），由 L13 Craft Protocol Schema lint 强制执行。

---

## W4: 在线验证

引用数字型 claim → WebSearch 查找权威来源 → 记录到文档（含 URL）→ 对比验证。

---

## W5: 持续进化

| 信号 | 动作 |
|------|------|
| 同一操作执行 ≥3 次 | 提取为脚本 |
| 新会话发现上次决策未记录 | 强化 W1 流程 |
| 操作因已知原因失败 | 检查是否在 Bug 列表 |
| 某流程耗时超出预期 | 分析可否自动化 |

---

## W6: 近端丰富化

- **操作过程知识 (Procedures)**：触发条件 → 前置检查 → 步骤 → 已知陷阱 → 最终验证 → 历史执行
- **Context Priming**（MYCO.md 热区 ≤5 行）：工具手感描述
- **Pattern Names**：给反复出现的操作流赋予名字

---

## W7: 系统化 Lint

**频率**：长会话结束前 / 每 3 次短会话
**工具**：`scripts/lint_knowledge.py` + `_canon.yaml`
**运行方式**：`python scripts/lint_knowledge.py --project-dir .`（从 Myco repo 根目录）
**更新流程**：先改 _canon.yaml → 运行 Lint → 逐一修复 → 再跑确认

---

## W8: Wiki 页面模板

**页眉**（所有 wiki 页面）：

```markdown
# [页面标题]

> **类型**：[entity / concept / operations / analysis / craft]
> **最后更新**：[YYYY-MM-DD]
> **⚠️ 非直觉盲点**：[可选——仅当新会话不知此局限可能犯错时]
```

**页脚**：

```markdown
---
> **Back to**: `MYCO.md` | [相关页面链接]
```

### W8.1 内部结构模板（按页面类型）

**Entity（实体页）**：Overview → 枚举表格 → 详细说明 → API/接口 → 已知问题

**Concept（概念页）**：核心命题 → 机制/证据链 → 反论/局限 → 应用/操作化

**Operations（操作页）**：快速参考 → 详细步骤 → 陷阱记录 → 预防清单

**Analysis（分析页）**：Claims → 实验配置 → 数据/结果 → 验证状态 → 开放问题

---

## W9: 活跃张力标记

用 `⚡ 活跃张力` 标记架构级内在矛盾。解决后改为 `✅ 已解决`。

---

## W10: 外部知识编译协议

5 步：多通道收集（≥3 源） → 三重门控（跨源一致性/可操作性/独特性） → 框架萃取 → 局限标注 → 写入 wiki

---

## W11: 验证范围标签

传统手艺结论增加：`**验证范围**：[条件A] ✅ | [条件B] ⚠️ 未测 | [条件C] ❌`

---

## W12: 信息密度感知

Agent 根据任务复杂度自然调整加载深度：简单任务仅热区，默认加热区+相关 wiki，深度决策加载全量上下文。

## W13: Primordia 压缩检查点（Wave 22，v0.21.0）

每次 wave 在 session end 读取 `myco hunger`。如果报告中出现
`structural_bloat: primordia`（见 `src/myco/notes.py::detect_structural_bloat`），
该 wave **必须**在会话结束前选择下列之一：

（a）将 ≥N 个 [COMPILED]/[SUPERSEDED] craft 用 `git mv` 移到
    `docs/primordia/archive/`（N 足以让计数回到 soft limit 之下），
    并更新 `docs/primordia/README.md` 让被归档行指向新路径；或

（b）在 `log.md` 本次 wave 条目末尾追加一行
    `deferred: primordia-compression (<原因>)`，说明为什么此刻没有
    craft 到成熟期。

前者是行动，后者是有审计痕迹的延迟。**既不压缩也不声明延迟，
下一次 wave 的 `myco hunger` 会让违规再次显形——这是 W5（持续进化）违规**。
archive 目录设计为 append-only 历史档案：Gear 4 回顾、决策考古、
替代方案查询仍可读取；`detect_structural_bloat` 的非递归 glob 自然
排除 archive/。本规则的权威 craft 在
`docs/primordia/primordia_compression_craft_2026-04-12.md`。

---

## Wiki 创建清单（强制三步）

每新建一个 wiki 页面，**立即**执行：

| 步骤 | 操作 | 验证 |
|------|------|------|
| ① 索引 | MYCO.md Wiki 索引表添加新行 | grep 页面名 |
| ② 计数 | `_canon.yaml` → `wiki_pages` +1 | lint L0 |
| ③ 模板 | 应用 W8 模板 | lint L7 |

**执行顺序**：先 ①② 索引和计数，再 ③ 填充内容。索引先行防止遗忘。

---

## 临时脚本归档协议

**触发条件**（满足任一）：同一类型脚本 ≥2 次重写、≥3 步复合操作、审计/健康检查类、非显然 workaround

**流程**：评估价值 → 清理硬编码+注释 → 复制到 scripts/ → 更新 MYCO.md §4

---

## 文档生命周期标签

| 标签 | 含义 |
|------|------|
| `[ACTIVE]` | 仍在使用，可能被更新 |
| `[COMPILED]` | 结论已编译到 wiki，仅供溯源 |
| `[SUPERSEDED]` | 被更新版本取代 |

标注位置：MYCO.md §3 文档索引表。`[COMPILED]`/`[SUPERSEDED]` 文档通常不需要读取。

---

## 进化引擎

| 代谢阶段 | 频率 | 动作 |
|------|------|------|
| Gear 1: 摩擦感知 | 每次会话 | 遇到不顺畅 → `friction` 条目到 log.md |
| Reflection: 会话反思 | 会话结束 | "系统哪里可以改进？" → `meta` 条目 |
| Retrospective: 里程碑回顾 | 里程碑后 | 三个 Double-loop 问题 → 修改原则/架构 |
| Distillation: 跨项目蒸馏 | 项目结束 | 萃取通用模式 → 更新 Myco 模板 |

log.md 事件类型：`milestone / decision / debug / deploy / debate / system / friction / meta / contradiction / validation / script`

---

## 自主权边界

| 层级 | 范围 | 判断标准 |
|------|------|---------|
| ✅ 自主行动 | 技术执行、文档更新 | 改错了 10 分钟能修好 |
| 📢 做了再知会 | 工作流微调 | 改错了 1 小时能修好 |
| 🛑 必须等人类 | 框架方向、API 设计、破坏性变更 | 改错了 > 1 小时 |

---

## 会话标准流程

```
[开始] 自动加载 MYCO.md → 读热区 + 任务队列 → 工作
[进行中] W1 即时沉淀 | hunger 摩擦信号 | W3 传统手艺（如需）| W4 在线验证
[结束] ① 任务队列 ② log.md ③ 进度 ④ Gear 2 反思 ⑤ wiki/docs 更新 ⑥ Lint（长会话）
```
