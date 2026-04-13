# Agent Protocol — Myco 运行契约

> **适用对象**：任何在 Myco 基质上运行的 AI agent（Claude、GPT、Codex、Cursor、自建 agent……）
> **状态**：[ACTIVE] · v1.0 · 2026-04-11
> **强制级别**：HARD — 此文档定义的是 agent 与基质之间的**行为契约**，违反任一条等同于污染基质。
> **执行**：L11 Write-Surface Lint + L10 Notes Schema Lint 会自动检测违约。

---

## 0.5 两条入口：CLI 和 MCP 任选其一

Myco 的 19 个工具都有**两套等价入口**，底层共享 `src/myco/notes.py`
和 src/myco/immune.py，落盘文件完全一致。

| 能力 | CLI（shell 命令） | MCP tool |
|---|---|---|
| 捕获 | `myco eat --content "..."` | `myco_eat` |
| 消化 | `myco digest <id> --to integrated` | `myco_digest` |
| 查看 | `myco observe --status raw` | `myco_observe` |
| 饥饿度 | `myco hunger` | `myco_hunger` |
| Lint | `myco immune` | `myco_immune` |
| 状态/日志/反思 | （待实现 CLI）| `myco_pulse` / `myco_trace` / `myco_reflect` |

**推荐安装**（可编辑模式，支持自进化）：
```bash
git clone https://github.com/Battam1111/Myco.git && cd Myco && pip install -e ".[mcp]"
```
装完就有 `myco` CLI。**任何能跑 shell 的 agent 都能用**，包括
Cowork 下的 agent（通过 Bash 工具调用）。
快速预览：`pip install myco`（冻结快照，进化受限）。

**可选**：在 agent host 的 MCP 配置里注册 `python -m myco.mcp_server`。
注册后 19 个工具会以原生 MCP tool 的形式出现在 agent 的工具列表里，
带详细 trigger-condition 描述和结构化参数。Cowork 用户在桌面应用的
MCP 设置里加一条即可（一次性，持久生效）。

**本文档中的命名约定**：凡是出现 `myco_eat` / `myco_digest` 之类
下划线形式的名字，指的是**同一个工具的任一入口**——读者可以自动替
换为对应的 CLI 命令 `myco eat` / `myco digest`。两种写法等价。

**Cowork 运行环境的一个实际区别**：
- CLI 路径：每次会话需要确保 `myco` 已在 Python 环境中（`pip install -e`
  是否持久取决于 Cowork 的 sandbox 卷策略）。不持久时把安装步骤写进
  session boot hook 或 `CLAUDE.md`。
- MCP 路径：一次配置永久有效，无 sandbox 重建问题。跨会话零成本。

对 ASCC 等下游项目的建议：**先用 CLI 起跑**（零配置，今天就能跑），
**稳定后切到 MCP**（零摩擦，适合长期）。两条路径也可以共存。

---

## 0. 为什么需要这份文档

Myco v1.2 Phase ① 引入了消化系统（`eat / digest / view / hunger` + `notes/`）。
没有契约的情况下，agent 会默认按"最像人类的方式"处理信息：
- 随手建 `scratch.md` / `TODO.md` / `memo.txt` 在仓库根
- 把思考粘贴进 `MYCO.md` 或随便一个 `wiki/*.md`
- 跳过 `eat`，直接手写 `notes/xxx.md` 违反 schema
- 在 `log.md` 外另起一个 `diary.md`
- 把 digest 结果写成 markdown 正文而不是走 frontmatter 生命周期

**后果**：
1. 消化系统的摩擦信号（Phase ② 的驱动力）全部失真
2. L9/L10 lint 误报或漏报
3. 基质熵增，下一次压缩时丢掉真正重要的东西

**根本原则**：**Structure > Prose**。Agent 不靠 "记得小心点" 保持纪律，而是靠 **lint + 写入白名单 + 工具协议** 把错误前置拦截。

---

## 1. Write Surface — 写入白名单

**唯一真理源**：`_canon.yaml → system.write_surface`
**强制执行**：L11 Write-Surface Lint

下表是 kernel 默认契约。每个项目实例可以在 `_canon.yaml` 里**扩展**（不能删除）。

| 目标位置 | 合法写入通道 | 说明 |
|----------|-------------|------|
| `notes/n_*.md` | `myco eat` / `myco digest` / MCP `myco_eat`, `myco_digest` | **永远**不要手写 notes 文件。必须经由工具生成，保证 frontmatter 合规。 |
| `wiki/*.md` | `myco_extract`（待实现）或人类明确授权 | 结构化知识页。agent 自主写入前必须先 `digest → extracted` 一条 note。 |
| `docs/primordia/*.md` | `myco_craft`（待实现）或人类明确授权 | 辩论/决策记录。允许 agent 在多轮 debate 任务中创建，但必须是 `*_craft_YYYY-MM-DD.md` 或 `*_debate_YYYY-MM-DD.md` 命名。 |
| `log.md` | `myco_trace` MCP tool（append-only） | 只能追加。永远不要 rewrite 或删除历史条目。 |
| `MYCO.md` | `myco_integrate`（待实现）或人类明确授权 | 硬上限 300 行 (`system.myco_md_max_lines`)。只能 integrate 已经 extracted 的 note。 |
| `_canon.yaml` | 🛑 **人类明确授权** | Schema 的 Single Source of Truth。Agent 永远不能单独修改。 |
| `pyproject.toml` / `src/myco/__init__.py` 版本号 | 🛑 **人类明确授权** | 版本发布走 release 流程。 |
| `src/**` / `scripts/**` | ✅ 任务明确要求时 | 代码修改属于执行层，不是基质写入。 |
| 其它任何位置 | 🛑 **STOP — 问人类** | 如果你不知道一个文件应该写在哪，先 `myco eat` 把它作为 raw note，然后问。 |

### 🛑 Anti-patterns（L11 会报 CRITICAL）

- 在仓库根创建 `scratch.md`、`notes.md`、`TODO.md`、`MEMO.md`、`ideas.md`、`draft.md`、`summary.md`
- 创建顶层新目录（`thoughts/`、`my_notes/`、`tmp/`）
- 在 `wiki/` 下建非 markdown 文件或未在 `system.wiki_page_types` 中的类型
- 在 `docs/primordia/` 下建不符合命名模式的文件
- 绕过 `eat` 直接 `echo > notes/n_xxx.md`

**硬规则**：**如果不确定一个写入是否合法，先 `myco eat` 捕获它作为 raw note，然后问人类"这个应该 integrate 到哪里？"。** Zero-friction capture 就是为此设计的。

---

## 2. Tool Protocol — 20 个 MCP 工具的触发条件

每个工具都有 **WHEN to call** 的触发条件列表。如果匹配其中任一条，**必须**调用对应工具，不能用自由写入代替。

### 2.1 Reflexes（反射层，代谢阶段）

| Tool | 何时调用 | 禁止 |
|------|---------|------|
| `myco_pulse` | 新会话第一次动作之前 | 不能用 `cat MYCO.md` 代替 |
| `myco_trace` | 完成一个非平凡任务后；解决一个 bug 后；做出一个决策后 | 不能 `echo >> log.md` |
| `myco_reflect` | 会话结束前；任一任务完成后；遇到意外结果时 | 不能只在心里反思 |
| `myco_immune` | 长会话结束前；修改 `_canon.yaml` 后；引入新文档类型后 | 不能只看 "应该没问题" |

### 2.2 Digestive Substrate（消化层，Phase ①）

| Tool | 何时调用（trigger conditions） | 禁止 |
|------|------------------------------|------|
| `myco_eat` | (a) 刚写出能跑通的代码片段；(b) 做出有理由的决策；(c) 定位到 bug 根因；(d) 用户粘贴了一段长内容；(e) 自然萌生 "TIL / 原来如此 / 这个以后会忘" 的念头；(f) 任何硬学到的知识 | 不能把这些内容直接写进 `MYCO.md` 或 `wiki/` |
| `myco_digest` | (a) `myco_hunger` 报 `raw_backlog` 或 `stale_raw`；(b) 准备 extract 到 wiki 前；(c) 每次 `myco_reflect` 时顺便消化 1-2 条 | 不能跳过 digest 直接 extract |
| `myco_observe` | (a) 开始新任务前扫 `--status raw --tag <topic>`；(b) 找之前吃过的某段代码/决策；(c) 人类问 "你记不记得……" 时 | 不能凭记忆回答 |
| `myco_hunger` | (a) 新会话开始（`myco_pulse` 之后）；(b) 会话中段自检；(c) 会话结束前 | 不能忽略其返回的信号 |

### 2.3 Compression Pipeline（压缩管道，Wave 30-33）

| Tool | 何时调用（trigger conditions） | 禁止 |
|------|------------------------------|------|
| `myco_condense` | (a) `myco_hunger` 报 `compression_ripe`（tag cohort ≥5 raw notes 且最老 ≥7d）；(b) `compression_pressure` > 2.0；(c) Agent 判断多条笔记应合成；(d) `myco_colony suggest` 返回建议 | 不能手动合并笔记内容到 wiki 而不走 compress 审计轨迹 |
| `myco_expand` | 发现某次压缩遗失了重要内容，需要恢复输入笔记 | 极少使用；不能直接手改 excreted 笔记的 status |
| `myco_prune` | (a) `myco_hunger` 报 `dead_knowledge`（terminal 状态笔记 ≥30d 未查看）；(b) 主动清理积压 | 不能手动删除 notes/*.md 文件 |

### 2.4 External Metabolism（外部代谢，Wave 35-52）

| Tool | 何时调用（trigger conditions） | 禁止 |
|------|------------------------------|------|
| `myco_absorb` | (a) `myco_hunger` 报 `inlet_ripe`（搜索缺失 + 知识缺口）；(b) Agent 有外部文件/内容要摄入；(c) 人类提供了参考资料 | 不能把外部内容直接粘贴进 notes/ 而不走 inlet 来源追踪 |
| `myco_forage` | (a) Agent 发现相关论文/仓库/文章；(b) 人类说"去看看 X"；(c) `myco_hunger` 报 `forage_backlog` | 不能把外部资料存在 notes/ 里，forage/ 是暂存区 |
| `myco_sense` | (a) **回答任何项目事实性问题之前**；(b) 开始新功能/修 bug 前查已有知识；(c) 人类问"有没有……" | 不能凭记忆回答——基质是事实来源 |

### 2.5 Structural Intelligence（结构智能，Wave 47-52）

| Tool | 何时调用（trigger conditions） | 禁止 |
|------|------------------------------|------|
| `myco_mycelium` | (a) 想知道谁引用了某个文件；(b) 检测知识孤岛/断裂；(c) 重构前评估影响范围；(d) `myco_hunger` 报 `graph_orphans` | 不能靠手动 grep 替代结构化链接分析 |
| `myco_colony` | (a) 准备压缩时选择最佳分组（`myco_colony suggest`）；(b) 检测知识缺口（`myco_colony gaps`）；(c) 分析 tag 共现关系 | 不能凭直觉选压缩对象 |
| `myco_memory` | (a) 需要回忆之前对话的具体内容；(b) 人类问"上次我们讨论了什么"；(c) 跨会话延续工作 | 不能说"我不记得之前的对话" |

### 2.6 Evolution Engine（进化引擎）

| Tool | 何时调用（trigger conditions） | 禁止 |
|------|------------------------------|------|
| `myco_evolve` | (a) 代谢循环检测到某 skill 成功率低于 `system.evolution.skill_success_threshold`；(b) Agent 在工作中发现某 skill 可以改进；(c) 吸收外部模式后发现可应用于现有 skill。分两步：先 `action='propose'` 获取当前内容，Agent 施加智能改进，再 `action='apply'` 提交并通过约束门 | 不能手动编辑 `skills/*.md` 来"进化"——必须走 evolve 工具的门控流程 |
| `myco_evolve_list` | (a) 进化前查看可用 skill 及当前状态；(b) 进化后验证新变体已保存；(c) 审查进化健康度（代数计数、漂移） | 不能盲目进化——先看再改 |

### 2.7 非线性生命周期跳转

`raw → digesting → {extracted | integrated | excreted}` 允许跨级跳转。合法场景：
- **raw → integrated**：note 内容已经足够成熟，可直接并入 canonical 结构。必须在 digest 步骤显式 `--to integrated` 并写 reason。
- **raw → excreted**：明显是噪音/重复/错误。必须填 `excrete_reason`。
- **digesting → excreted**：digest 过程中发现没有保留价值。必须填 `excrete_reason`。

**禁止**：跳过 `digest` 直接手改 frontmatter 的 `status` 字段。永远走工具。

### 2.6 纵向追溯导航（Wave 56）

**`_canon.yaml::system.traceability`** 是 Agent 的纵向导航图。

**规程**：修改任何内核表面之前，读 traceability.anchors 找到完整影响路径。
例如：要修改 anchor #3（自主代谢管道）→ 追溯告诉你：vision.md §三 + 
agent_protocol.md §2.2/§3/§4 + _canon.yaml::notes_schema + lint L10/L18/L22 + 
notes.py/condense_cmd.py/absorb_cmd.py + hunger raw_backlog/stale_raw/
compression_ripe/compression_pressure 全部可能需要同步更新。

**目的**：防止"改了一层、漏了另一层"的漂移（如 MCP 工具从 9 增到 18 但 README 
腐烂 10+ 个 wave 未发现）。追溯索引不是 lint——它是给 Agent 的智能导航，Agent 
用自己的判断力决定哪些下游层需要更新。

### 2.8 配置优先级（absorbed from claude-code-best-practice）

Myco 配置遵循五级优先级（从高到低）：

1. **Session override** — 当前会话的临时覆盖
2. **Project `.claude/settings.json`** — 项目级团队共享
3. **Project `_canon.yaml`** — Myco kernel 契约（SSoT）
4. **User `~/.claude/settings.json`** — 个人全局默认
5. **Organization managed settings** — 组织级强制

**Deny rules 优先级最高**——任何级别的 deny 都不可被下级覆盖。
**Array values（如 permissions.allow）跨级别合并去重。**

---

## 3. Session Boot Sequence — 会话启动硬流程

每次新会话**只需一步**：

```
1. myco_hunger(execute=true)   # THE boot call. 检查全部信号 + 自动执行推荐 actions
2. 阅读返回的 signals — 如有 [REFLEX HIGH] 手动处理
3. 开始正式任务
```

**Wave 54 (v0.41.0) Agent-First 重写**：`myco_hunger(execute=true)` 取代了
原来的 `myco_pulse → 手动处理信号` 两步。一次调用完成：检查 hunger + 自动
digest 过期笔记 + 自动 compress 积压 + 自动 prune 死知识。返回的 JSON 含
`signals`（全部信号）、`actions`（推荐动作）、`execution_results`（自动执行
结果）。只有 [REFLEX HIGH] 级别的信号需要人工/Agent 判断。

**为什么**：Agent-First 原则——人类只会自然语言，Agent 是唯一操作者。一个调用
完成全部 boot 工作，零人类参与。
Craft：`docs/primordia/anchor_agentfirst_revision_craft_2026-04-12.md`。

**Skill resolution**：Boot 和后续任务中 Agent 可调用 `skills/` 目录下的技能文档：
- `skills/metabolic-cycle.md` — boot ritual 的详细步骤（hunger → execute → re-check）
- `skills/sprint-pipeline.md` — 非平凡开发任务的 7 步流水线
- `skills/discovery-loop.md` — 主动知识获取（inlet_ripe / cohort_staleness 驱动）
- `skills/agent-routing.md` — 子 agent 模型选择与工具隔离策略
- `skills/learning-loop.md` — 执行后学习捕获与技能晋升

---

## 4. Session End Sequence — 会话结束硬流程

Wave 14 (contract v0.13.0) 把这一段从 5 步 prose 改为 **2 步反射弧**，
与 §3 Boot Sequence 镜像对称。具体动作由 hunger advisory 信号驱动：

```
1. myco_hunger             # 看 session_end_drift 与其它 advisory 信号
2. 处理 session_end_drift  # reflect / sweep / update log / commit
```

**`session_end_drift` 的两个子信号**（都是 LOW，不阻塞任务，只对抗遗忘）：

- **reflection**：`## [YYYY-MM-DD] meta |` 反射条目之后累计了 ≥15 条非 meta 日志
  → 写一条 `meta` 条目（一句话即可，reflection 价值在"看"的仪式本身，不在
  每次都发现缺陷）。
- **distillation**：`log.md` 里有 `g4-candidate` 条目 age ≥5 天且无 `g4-pass` /
  `g4-landed` / 在磁盘存在的 craft 引用 → 为每条补注解。最小决议形式是
  inline `g4-pass: <一句话 rationale>`；正式决议是写 craft 并引用。

两个子信号都可以在 `_canon.yaml::system.session_end_reflex` 里按 instance
关闭或调阈值。与 Wave 13 的 HIGH 反射不同，本反射**刻意 LOW** — W5
（持续进化）是一个 drive，不是 W1 级的 data-loss constraint；过度升级会
让 agent 学会忽视整个 advisory 列表。见
`docs/primordia/session_end_reflex_arc_craft_2026-04-11.md §B4`.

**传统的 5 步流程（仍然有效，但由 hunger 驱动而非记硬背）**：
`myco_reflect` → `myco_trace` → `myco_hunger` → `myco_immune`（改动 ≥5 文件
或改了 canon 时）→ 更新 MYCO.md（任务队列或 §1 进度变了时）。

**未完成的想法怎么办？** → `myco_eat` 一条 raw note，tags 带 `followup`。不要写进 `TODO.md`，不要写进 `MYCO.md`。

---

## 5. Phase ② 摩擦数据收集约定

v1.2 Phase ② 的驱动力是 Phase ① 产生的**真实摩擦数据**。Agent 在使用消化系统时遇到的任何"不顺手"都必须被捕获，否则 Phase ② 就是在盲设计。

**约定**：任何摩擦体验**必须** `myco eat` 一条 note，tags 里**必须**包含 `friction-phase2`。

### 5.1 触发点清单

**(a) 会话两端**：boot sequence 的 hunger 信号、end sequence 的 reflect 步骤。

**(b) 工具不够用的时刻**：
- "我想 extract 但没有 `myco_extract` 工具"
- "digest 的 4 个问题太多了，对小 note 过度"
- "hunger 报告没提到 X 我想看的信号"
- "这条 note 应该放在 wiki 还是 notes？我不知道"
- "raw note 查找需要先列再 grep 太麻烦"

**(c) 🆕 on-self-correction（自承错误触发点，v1.2.0 新增）**：

当 agent 在输出中承认了一个错误——任何形如"我之前说的 X 是错的 / 刚才那个判断错了 / 这里我搞混了 / 我之前理解偏了"的句子——**必须立即** `myco_eat` 捕获这次错误 + 上下文 + 修正动作，**然后再继续输出**。不能等会话结束再回顾。

**为什么**：错误发生的那一刻是最原位、信息损失最小的捕获时点。延迟到 end sequence 时捕获会丢失：当时的推理链、错误形成的直接原因、修正时的内部思路。这三样是 Phase ② 最想要的原材料。

**硬规则**：
- 触发词识别：agent 自己的输出中包含"我错了 / 我之前说的 X 是错的 / 搞混了 / 理解偏了 / 刚才的判断不对 / I was wrong / correction:"等显式自承错误的表达
- 立即动作：在**同一个 assistant turn 内**先 `myco_eat` 再继续说话
- note tags 必须包含：`friction-phase2` + `on-self-correction` + 错误类型 tag（如 `reference-error` / `misinterpretation` / `logic-error`）
- note 内容遵循 §5.2 格式模板
- **ergonomic shortcut (Wave 19, v0.18.0)**：`myco correct` CLI 命令把上述强制 tag 对 (`friction-phase2, on-self-correction`) 打包进一个动词；自承错误时**优先使用** `myco correct --content "..."`（可再追加 `--tags reference-error` 等错误类型 tag），比 `myco eat --tags friction-phase2,on-self-correction,...` 的记忆成本低一个数量级。canon source-of-truth：`system.self_correction.mandatory_tags`。

**来源溯源**：此触发点由 ASCC 项目 agent 于 2026-04-11 通过 note `n_20260411T013756_ca9e` 捕获的元级 friction 提出，经传统手艺辩论后落地。

### 5.2 格式模板（`myco eat` 时用）

```
[friction-phase2] <一句话症状>

触发场景：<什么时候遇到的>
期望行为：<我当时希望工具怎么做>
workaround：<临时怎么处理的>
根因分析：<为什么会发生>
```

Phase ② 开工的第一件事就是 `myco observe --tag friction-phase2 --status raw`，把这些 note 聚类成新器官的需求。

---

## 6. 给 ASCC 等下游项目 agent 的迁移指引

如果你是 ASCC（或其他基于 Myco 的项目）的 agent，在 Myco kernel 升级到 v1.2 之后：

1. **重读项目 `MYCO.md`**：应该已经包含对本协议的引用。
2. **重读本文件**：`docs/agent_protocol.md`。
3. **检查 write_surface**：项目的 `_canon.yaml → system.write_surface` 列出的目录才是合法写入目标。
4. **遵守触发条件**：§2 的 20 个 tool trigger conditions 对你**同样生效**。
5. **摩擦 = `friction-phase2` tag**：ASCC 运行中发现 Myco 的任何不顺手，立刻 eat。这些 note 会直接喂给 Phase ②。

**ASCC agent 的 3 条铁律**（粘贴到 ASCC 自己的 `MYCO.md` 或 `CLAUDE.md`）：

> 🔒 **铁律 1 — 不确定就 eat**：任何内容不知道往哪放，先 `myco_eat` 为 raw，tags 标清楚来源，然后继续任务。事后再 digest。
>
> 🔒 **铁律 2 — 不绕过工具**：不要手写 `notes/*.md`、不要手改 frontmatter `status`、不要直接 `echo >> log.md`、不要在仓库根建新文件/目录。
>
> 🔒 **铁律 3 — 摩擦必捕**：遇到 Myco 工具不够用 → `myco_eat` + `friction-phase2` tag。这是 Phase ② 的粮食，漏一条 = 盲设计一次。

---

## 7. 违约的检测与代价

| 违约类型 | 检测者 | 代价 |
|---------|--------|------|
| 写入非白名单位置 | L11 Write-Surface Lint（CRITICAL）| 下次 `myco_immune` 直接红灯 |
| `notes/*.md` frontmatter 不合规 | L10 Notes Schema Lint（CRITICAL）| 同上 |
| 愿景漂移（README/MYCO.md 丢锚点）| L9 Vision Anchor Lint（CRITICAL）| 同上 |
| 跳过 `myco_trace` 的关键事件 | 会在 `myco_reflect` 时被发现 | Cross-Project Distillation 数据缺失 |
| 摩擦未标 `friction-phase2` | Phase ② 启动时会被发现 | 数据丢失无法追回 |

**补救**：违约本身不是灾难，**隐瞒**才是。发现违约立刻 `myco_trace` 记录 + `myco_eat` 一条 `friction-phase2` note 说明为什么违约（多半是工具/文档不够清楚）。

---

## 8. 演进

本协议本身也是 Myco 基质的一部分，随 Phase ② 一起迭代。

- 修改本文件 = 修改 agent-kernel 契约，需要在 `log.md` 记 `meta` 条目
- 新增写入白名单项 = 修改 `_canon.yaml → system.write_surface`，需要人类明确批准
- 发现新的 anti-pattern = `myco_eat` 标 `protocol-evolution`

> **一句话总结**：**Agent 把基质当产品，不是当草稿纸。基质是 CPU 以外的一切，包括这份契约本身。**
