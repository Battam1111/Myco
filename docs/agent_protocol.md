# Agent Protocol — Myco 运行契约

> **适用对象**：任何在 Myco 基质上运行的 AI agent（Claude、GPT、Codex、Cursor、自建 agent……）
> **状态**：[ACTIVE] · v1.0 · 2026-04-11
> **强制级别**：HARD — 此文档定义的是 agent 与基质之间的**行为契约**，违反任一条等同于污染基质。
> **执行**：L11 Write-Surface Lint + L10 Notes Schema Lint 会自动检测违约。

---

## 0.5 两条入口：CLI 和 MCP 任选其一

Myco 的 9 个工具都有**两套等价入口**，底层共享 `src/myco/notes.py`
和 `src/myco/lint.py`，落盘文件完全一致。

| 能力 | CLI（shell 命令） | MCP tool |
|---|---|---|
| 捕获 | `myco eat --content "..."` | `myco_eat` |
| 消化 | `myco digest <id> --to integrated` | `myco_digest` |
| 查看 | `myco view --status raw` | `myco_view` |
| 饥饿度 | `myco hunger` | `myco_hunger` |
| Lint | `myco lint` | `myco_lint` |
| 状态/日志/反思/回顾 | （待实现 CLI）| `myco_status` / `myco_log` / `myco_reflect` / `myco_retrospect` |

**必装**：`pip install myco`（或开发版 `pip install -e /path/to/Myco`）。
装完就有 `myco` CLI。**任何能跑 shell 的 agent 都能用**，包括
Cowork 下的 agent（通过 Bash 工具调用）。

**可选**：在 agent host 的 MCP 配置里注册 `python -m myco.mcp_server`。
注册后 9 个工具会以原生 MCP tool 的形式出现在 agent 的工具列表里，
带详细 trigger-condition 描述和结构化参数。Cowork 用户在桌面应用的
MCP 设置里加一条即可（一次性，持久生效）。

**本文档中的命名约定**：凡是出现 `myco_eat` / `myco_digest` 之类
下划线形式的名字，指的是**同一个工具的任一入口**——读者可以自动替
换为对应的 CLI 命令 `myco eat` / `myco digest`。两种写法等价。

**Cowork 运行环境的一个实际区别**：
- CLI 路径：每次会话需要确保 `myco` 已在 Python 环境中（`pip install`
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

**来源溯源**：此触发点由 ASCC 项目 agent 于 2026-04-11 通过 note `n_20260411T013756_ca9e` 捕获的元级 friction 提出，经 `docs/current/upstream_protocol_craft_2026-04-11.md` 传统手艺辩论后作为首次 upstream 回灌落地。

### 5.2 格式模板（`myco eat` 时用）

```
[friction-phase2] <一句话症状>

触发场景：<什么时候遇到的>
期望行为：<我当时希望工具怎么做>
workaround：<临时怎么处理的>
根因分析：<为什么会发生>
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

## 8. 回灌协议（Upstream Protocol v1.0）

**这是 Myco kernel 与 downstream instance 之间的元级代谢通道**——instance 发现的"契约本身的缺陷"如何流回 kernel 并生效。

**定位**：Myco 有三层代谢同心圆：
- **最内层（本节）**：instance → kernel 回灌 —— downstream 项目发现的 Myco 工具/契约/lint 缺陷，升级 kernel
- **中间层（v1.2 Phase ③ Commons）**：instance ↔ instance 横向共享 —— craft / pattern / snippet 跨项目迁移
- **最外层（v2.0 Metabolic Inlet）**：世界 → substrate —— 从 GitHub / arXiv / 社区主动吞噬新知

本节定义最内层。**它复用既有 7 步管道**：发现 → 评估 → 萃取 → 整合 → 压缩 → 验证 → 淘汰。

**设计源**：`docs/current/upstream_protocol_craft_2026-04-11.md`（传统手艺 3 轮辩论，85% 置信度）

### 8.1 核心原则（五条硬性）

1. **生成零门槛 + inline confirm**：对齐开源 20 年 PR 共识。机械步骤自动化，决策步骤保留人类。
2. **结构性约束先于置信度**：通道分类基于文件路径（`git diff --name-only`），agent 无法操纵。**最严类 wins**——patch 触及任何一个类 Z 文件，整个 patch 走最严通道。
3. **版本锁 + 反向撤回广播**：`system.contract_version` 双向追踪，Conventional Commits 前缀自动 bump。首次手动 bootstrap，之后全自动。
4. **结构化元数据可过滤污染**：auto-append 带前缀 `[auto-upstream:<note-id>]`，auto-written notes 带 `source: auto-upstream`，bundle 带完整 provenance。
5. **两阶段 bootstrap**：协议 v1.0 本身手动落地（避免自引用递归），首次真实 dogfood 留给未来的非协议 friction。

### 8.2 三通道处置矩阵

通道由 `_canon.yaml → system.upstream_channels` 显式定义的文件路径决定：

| 通道 | 触发条件 | 用户动作 | 7 步管道映射 |
|---|---|---|---|
| **Auto** | 类 X 全部 + 类 Y 的 append-only | 无 | 发现→评估→萃取→整合→压缩→**验证**→（无淘汰步） |
| **Confirm** | 类 Y 修改 + 类 Z 的 append-only | 按 `yes/no/skip` | 全 7 步，淘汰=rejected |
| **Review** | 类 Z 修改 | 看 diff + 按 `yes/no/skip` | 全 7 步 + 前置人类 selection |

**明确不做**（Round 1-3 辩论后否决）：
- ❌ 置信度作为硬门槛（LLM calibration 研究否决 + Goodhart 陷阱）
- ❌ 纯自动 merge（开源 PR 共识反对）
- ❌ 假设下游与 kernel 同时 mount（ASCC 反例）

**置信度评分**从 gate 降级为 **sort key + audit log**——决定展示顺序和审计溯源，不决定是否执行。

### 8.3 状态机（下游 note 生命周期）

```
raw → upstream-candidate → bundle-generated
  ↓ (用户 Confirm/Review)
  ├─ yes    → integrated  + upstream_commit: <sha> + receipt
  ├─ no     → upstream-rejected (terminal for current contract_version)
  │           + reject_reason + rejected_at_version
  │           → 排除在未来 upstream 扫描之外
  │           → Phase ② digest 仍可本地 integrate
  │           → kernel bump 新 contract_version 时自动重评一次
  └─ skip   → 保留 upstream-candidate，下次 boot 重评
```

**mutation-selection 映射**：生成 bundle = mutation（substrate 做），inline confirm = selection（人类做）。这是 `docs/current/vision_recovery_craft_2026-04-10.md` §1.6 的协作模型在回灌通道的具体实现。

**craft_reference 字段**（v1.3.0 起）：bundle 若落入 class_z（kernel contract）通道，其 yaml 元数据 MUST 包含 `craft_reference: <path>`，指向一个 ACTIVE/COMPILED 状态的 craft 文件，其 `decision_class` ≥ bundle 对应的置信度阶梯（见 `docs/craft_protocol.md` §4）。class_x/class_y bundle 可选填。缺失 craft_reference 的 class_z bundle 会在 Upstream Phase 被 kernel 自动拒绝并返回 receipt reason=`missing_craft_reference`。

### 8.4 版本锁协议

**kernel 侧**：
- `_canon.yaml → system.contract_version: "vX.Y.Z"`（当前 v1.3.0）
- Conventional Commits 前缀 `[contract:{patch|minor|major}] <description>` 自动 bump
- `docs/contract_changelog.md` 追加每次 bump 的 diff 摘要 + 影响范围
- commit 无前缀 → 不 bump

**下游侧**：
- `_canon.yaml → system.synced_contract_version: "vX.Y.Z"`
- boot sequence 比对两边版本，不同则提示"kernel 契约有 N 个版本更新，是否同步？"
- 同步操作走 Confirm/Review 通道（改下游 CLAUDE.md/MYCO.md）

**撤回机制**：
- `docs/contract_changelog.md` 可标记某版本为 `revoked: true` + `revoke_reason`
- 下游 boot 看到自己的 synced_version 被 revoke → 强制提示用户回滚
- 撤回传播确定性 = boot 频率（通常一两天内全部下游收到）

### 8.5 传输层：会话内授权

**主路径**：下游 agent 生成 bundle 写到本地 `.myco_upstream_outbox/<note-id>.bundle.yaml`，通知用户。用户确认后：
- 双 mount 场景：agent 直接投递到 kernel 的 `.myco_upstream_inbox/`
- 单 mount 场景：agent 生成紧凑"喂料包"，用户在 kernel 会话里一次粘贴触发

**注**：`.myco_upstream_*` 是点目录，L11 自动豁免。L12（点目录协议卫生）防止垃圾累积。

**升级路径**（Phase ③）：`myco upstream serve` 守护进程 + HTTP 端点，下游直接 POST。v1.0 不做。

### 8.6 触发词与反射规则

下游 agent 在 `myco eat` 时，**自动**对满足以下条件的 note 追加 `upstream-candidate` tag：
- 内容明确指向 kernel 文件（`docs/agent_protocol.md` / `scripts/lint_knowledge.py` / `src/myco/lint.py` / `src/myco/mcp_server.py` / `_canon.yaml` / `src/myco/templates/**`）
- 根因分析段落出现"契约 / protocol / lint / canon / template / kernel"关键词
- tags 已包含 `friction-phase2`

打 tag 是低成本操作——**宁可多打不可漏打**，因为后续评分和通道分类会兜底。

### 8.7 Bootstrapping（v1.0 首次落地，本 commit）

协议 v1.0 本身 **不走协议**。本 commit 是手动 bootstrap：
- 手动 bump `contract_version: "v1.2.0"`
- 手动追加 `docs/contract_changelog.md` v1.2.0 初始条目
- 使用 Conventional Commit prefix `[contract:minor]`
- 本次改动包含：§5.1 on-self-correction + §8 upstream protocol + L12 lint + `upstream_channels` canon + 模板同步

**首次真实 dogfood**：预留给未来某条**非协议相关**的元级 friction note。不使用 `n_20260411T013756_ca9e` 作为 dogfood（避免协议执行自己时修改自己的递归陷阱）。

### 8.8 验收标准（多指标，非单 metric）

- 首次 bootstrap 成功落地 + L13 lint 全绿（验收 A）
- 首次真实 dogfood 完成 + receipt 正常生成（验收 B，延后）
- 一周内无 thrash（同一 upstream-candidate 反复卡住）（验收 C，延后）
- 任一项失败 → 该部分设计回炉

---

## 9. 演进

本协议本身也是 Myco 基质的一部分，随 Phase ② 一起迭代。

- 修改本文件 = 修改 agent-kernel 契约，需要在 `log.md` 记 `meta` 条目
- 新增写入白名单项 = 修改 `_canon.yaml → system.write_surface`，需要人类明确批准
- 修改 `system.upstream_channels` 路径列表 = 改变通道分类边界，需要 Conventional Commit `[contract:minor]` 以上
- 发现新的 anti-pattern = `myco_eat` 标 `protocol-evolution`

> **一句话总结**：**Agent 把基质当产品，不是当草稿纸。基质是 CPU 以外的一切，包括这份契约本身。**
