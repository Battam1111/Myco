# Agent Protocol — Myco 运行契约

> **适用对象**：任何在 Myco 基质上运行的 AI agent（Claude、GPT、Codex、Cursor、自建 agent……）
> **状态**：[ACTIVE] · v1.0 · 2026-04-11
> **强制级别**：HARD — 此文档定义的是 agent 与基质之间的**行为契约**，违反任一条等同于污染基质。
> **执行**：L11 Write-Surface Lint + L10 Notes Schema Lint 会自动检测违约。

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
| `docs/current/*.md` | `myco_craft`（待实现）或人类明确授权 | 辩论/决策记录。允许 agent 在多轮 debate 任务中创建，但必须是 `*_craft_YYYY-MM-DD.md` 或 `*_debate_YYYY-MM-DD.md` 命名。 |
| `log.md` | `myco_log` MCP tool（append-only） | 只能追加。永远不要 rewrite 或删除历史条目。 |
| `MYCO.md` | `myco_integrate`（待实现）或人类明确授权 | 硬上限 300 行 (`system.myco_md_max_lines`)。只能 integrate 已经 extracted 的 note。 |
| `_canon.yaml` | 🛑 **人类明确授权** | Schema 的 Single Source of Truth。Agent 永远不能单独修改。 |
| `pyproject.toml` / `src/myco/__init__.py` 版本号 | 🛑 **人类明确授权** | 版本发布走 release 流程。 |
| `src/**` / `scripts/**` | ✅ 任务明确要求时 | 代码修改属于执行层，不是基质写入。 |
| 其它任何位置 | 🛑 **STOP — 问人类** | 如果你不知道一个文件应该写在哪，先 `myco eat` 把它作为 raw note，然后问。 |

### 🛑 Anti-patterns（L11 会报 CRITICAL）

- 在仓库根创建 `scratch.md`、`notes.md`、`TODO.md`、`MEMO.md`、`ideas.md`、`draft.md`、`summary.md`
- 创建顶层新目录（`thoughts/`、`my_notes/`、`tmp/`）
- 在 `wiki/` 下建非 markdown 文件或未在 `system.wiki_page_types` 中的类型
- 在 `docs/current/` 下建不符合命名模式的文件
- 绕过 `eat` 直接 `echo > notes/n_xxx.md`

**硬规则**：**如果不确定一个写入是否合法，先 `myco eat` 捕获它作为 raw note，然后问人类"这个应该 integrate 到哪里？"。** Zero-friction capture 就是为此设计的。

---

## 2. Tool Protocol — 9 个 MCP 工具的触发条件

每个工具都有 **WHEN to call** 的触发条件列表。如果匹配其中任一条，**必须**调用对应工具，不能用自由写入代替。

### 2.1 Reflexes（反射层，齿轮 1-4）

| Tool | 何时调用 | 禁止 |
|------|---------|------|
| `myco_status` | 新会话第一次动作之前 | 不能用 `cat MYCO.md` 代替 |
| `myco_log` | 完成一个非平凡任务后；解决一个 bug 后；做出一个决策后 | 不能 `echo >> log.md` |
| `myco_reflect` | 会话结束前；任一任务完成后；遇到意外结果时 | 不能只在心里反思 |
| `myco_retrospect` | 完成 "≥2 轮才解决" 的问题后；或 hunger 信号提示 `g4-candidate` 堆积时 | 不能跳过 |
| `myco_lint` | 长会话结束前；修改 `_canon.yaml` 后；引入新文档类型后 | 不能只看 "应该没问题" |

### 2.2 Digestive Substrate（消化层，Phase ①）

| Tool | 何时调用（trigger conditions） | 禁止 |
|------|------------------------------|------|
| `myco_eat` | (a) 刚写出能跑通的代码片段；(b) 做出有理由的决策；(c) 定位到 bug 根因；(d) 用户粘贴了一段长内容；(e) 自然萌生 "TIL / 原来如此 / 这个以后会忘" 的念头；(f) 任何硬学到的知识 | 不能把这些内容直接写进 `MYCO.md` 或 `wiki/` |
| `myco_digest` | (a) `myco_hunger` 报 `raw_backlog` 或 `stale_raw`；(b) 准备 extract 到 wiki 前；(c) 每次 `myco_reflect` 时顺便消化 1-2 条 | 不能跳过 digest 直接 extract |
| `myco_view` | (a) 开始新任务前扫 `--status raw --tag <topic>`；(b) 找之前吃过的某段代码/决策；(c) 人类问 "你记不记得……" 时 | 不能凭记忆回答 |
| `myco_hunger` | (a) 新会话开始（`myco_status` 之后）；(b) 会话中段自检；(c) 会话结束前 | 不能忽略其返回的信号 |

### 2.3 非线性生命周期跳转

`raw → digesting → {extracted | integrated | excreted}` 允许跨级跳转。合法场景：
- **raw → integrated**：note 内容已经足够成熟，可直接并入 canonical 结构。必须在 digest 步骤显式 `--to integrated` 并写 reason。
- **raw → excreted**：明显是噪音/重复/错误。必须填 `excrete_reason`。
- **digesting → excreted**：digest 过程中发现没有保留价值。必须填 `excrete_reason`。

**禁止**：跳过 `digest` 直接手改 frontmatter 的 `status` 字段。永远走工具。

---

## 3. Session Boot Sequence — 会话启动硬流程

每次新会话的前三步**按顺序**执行，不能省略：

```
1. myco_status             # 读 MYCO.md 热区 + 任务队列 + 身份锚点
2. myco_hunger             # 看消化系统健康度；优先处理 raw_backlog/stale_raw
3. （如果 hunger 建议）myco_digest 1-2 条最老的 raw note
4. 开始正式任务
```

**为什么**：身份锚点的 8 条和 hunger 报告共同决定"这次会话的姿态"。跳过 step 1 会触发愿景漂移（L9 会在之后发现但已经晚了）；跳过 step 2 会让 raw 永远堆积。

---

## 4. Session End Sequence — 会话结束硬流程

```
1. myco_reflect            # 本次会话学到了什么 / 哪里摩擦
2. myco_log                # 关键事件追加到 log.md（末尾视需要标 g4-candidate）
3. myco_hunger             # 再看一次，确保没留下 raw_backlog
4. （如果改动 ≥ 5 文件或改了 canon）myco_lint
5. （如果 MYCO.md 或 任务队列变了）更新 MYCO.md
```

**未完成的想法怎么办？** → `myco_eat` 一条 raw note，tags 带 `followup`。不要写进 `TODO.md`，不要写进 `MYCO.md`。

---

## 5. Phase ② 摩擦数据收集约定

v1.2 Phase ② 的驱动力是 Phase ① 产生的**真实摩擦数据**。Agent 在使用消化系统时遇到的任何"不顺手"都必须被捕获，否则 Phase ② 就是在盲设计。

**约定**：任何摩擦体验**必须** `myco eat` 一条 note，tags 里**必须**包含 `friction-phase2`。

触发摩擦捕获的例子：
- "我想 extract 但没有 `myco_extract` 工具"
- "digest 的 4 个问题太多了，对小 note 过度"
- "hunger 报告没提到 X 我想看的信号"
- "这条 note 应该放在 wiki 还是 notes？我不知道"
- "raw note 查找需要先列再 grep 太麻烦"

**格式模板**（`myco eat` 时用）：
```
[friction-phase2] <一句话症状>

触发场景：<什么时候遇到的>
期望行为：<我当时希望工具怎么做>
现在的 workaround：<临时怎么处理的>
```

Phase ② 开工的第一件事就是 `myco view --tag friction-phase2 --status raw`，把这些 note 聚类成新器官的需求。

---

## 6. 给 ASCC 等下游项目 agent 的迁移指引

如果你是 ASCC（或其他基于 Myco 的项目）的 agent，在 Myco kernel 升级到 v1.2 之后：

1. **重读项目 `MYCO.md`**：应该已经包含对本协议的引用。
2. **重读本文件**：`docs/agent_protocol.md`。
3. **检查 write_surface**：项目的 `_canon.yaml → system.write_surface` 列出的目录才是合法写入目标。
4. **遵守触发条件**：§2 的 9 个 tool trigger conditions 对你**同样生效**。
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
| 写入非白名单位置 | L11 Write-Surface Lint（CRITICAL）| 下次 `myco_lint` 直接红灯 |
| `notes/*.md` frontmatter 不合规 | L10 Notes Schema Lint（CRITICAL）| 同上 |
| 愿景漂移（README/MYCO.md 丢锚点）| L9 Vision Anchor Lint（CRITICAL）| 同上 |
| 跳过 `myco_log` 的关键事件 | 会在 `myco_retrospect` 时被发现 | Gear 4 数据缺失 |
| 摩擦未标 `friction-phase2` | Phase ② 启动时会被发现 | 数据丢失无法追回 |

**补救**：违约本身不是灾难，**隐瞒**才是。发现违约立刻 `myco_log` 记录 + `myco_eat` 一条 `friction-phase2` note 说明为什么违约（多半是工具/文档不够清楚）。

---

## 8. 演进

本协议本身也是 Myco 基质的一部分，随 Phase ② 一起迭代。

- 修改本文件 = 修改 agent-kernel 契约，需要在 `log.md` 记 `meta` 条目
- 新增写入白名单项 = 修改 `_canon.yaml → system.write_surface`，需要人类明确批准
- 发现新的 anti-pattern = `myco_eat` 标 `protocol-evolution`

> **一句话总结**：**Agent 把基质当产品，不是当草稿纸。**
