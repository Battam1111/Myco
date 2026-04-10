---
类型: craft
最后更新: 2026-04-10
状态: in-progress (Round 1)
置信度目标: ≥90%
---

# Craft: Myco 消化结构与跨项目架构辩论

> **缘起**：2026-04-10 Yanjun 在 L9 lint 上线后提出两条质疑——(1) 跨项目经验无处安放（HPC lesson 被误写进 kernel 仓）；(2) Myco 目前只有"胃"（wiki）没有完整消化道，ASCC 实践暴露三大摩擦：没法把内容消化进 Myco、没法很好地使用 Myco、甚至意识不到要用 Myco。
>
> **本 debate 要决断的七件事**：
> 1. Commons 层是否存在？形态？
> 2. kernel/commons/instance 提升与召唤机制？
> 3. 消化道是否物理化？器官数量？
> 4. 代谢触发：pull / push / 混合？
> 5. 摄食门槛低于聊天的量化约束？
> 6. 现有 wiki/docs/log 的迁移与兼容？
> 7. ASCC 已暴露摩擦的 must-solve vs defer 清单？
>
> **方法**：传统手艺协议 ≥4 轮 (Claim → Attack → Research → Defense → Revise)，全程比对 MemOS / A-Mem / Letta / MemGPT / Voyager / Mem0 / MemPalace。

---

## Round 1 — Claim

**初始主张（等待被攻击）**：

Myco 应采用 **三层架构 + 七器官消化道 + 混合触发**，具体为：

### 1.1 三层架构
```
Myco kernel (github.com/Battam1111/Myco, pip-installable)
    └── gears / lint / MCP / templates / _canon schema
Myco commons (github.com/Battam1111/MycoCommons, independent repo)
    └── crafts / patterns / cross-project wiki
    └── itself a Myco instance (eats dogfood)
Myco instances (ASCC / NextProject / ...)
    └── each one: inbox/ digesting/ extracted/ wiki/ compressed/ log.md
```

### 1.2 七器官物理消化道（每个 instance 内）
```
inbox/       # 口 — 零门槛投放
digesting/   # 胃 — 反复咀嚼中
extracted/   # 小肠 — 结构化原子
wiki/        # 组织 — 已整合
compressed/  # 结肠 — 压缩摘要
log.md       # 排泄记录
(immune = lint, 横贯所有层)
```

### 1.3 命令表
- `myco eat <path|paste|url>` — 零门槛摄食进 inbox
- `myco digest` — 开咀嚼 session
- `myco extract` — 从 digesting 抽原子到 extracted
- `myco integrate <atom>` — 升级到 wiki 或 craft promote
- `myco excrete <path> --reason` — 正式淘汰
- `myco hunger` — 可视化代谢压力
- `myco craft promote <path>` — instance → commons
- `myco craft use <name>` — commons → instance reference
- `myco craft diff <name>` — 漂移检测

### 1.4 触发机制
- **Pull**: 所有上面命令
- **Push (Claude Code hook)**: session stop hook 自动扫描 transcript → 生成 eat 候选项 → y/n 交互
- **Ambient (hunger)**: `myco status` 每次运行都显示消化负载

### 1.5 约束
- 摄食成本 ≤ 和 Claude 聊天的成本（<10 秒 <10 字符）
- 向后兼容：现有 wiki/docs/log 不动，只加新目录
- ASCC 作为第一个吃螃蟹的 instance，一周内必须完成 dogfood

**置信度自评**：35%（许多组件是凭直觉拍的，特别是七器官数量和独立仓决定）

---

## Round 1 — Attack

**A1 · 七器官过度设计 (severity: HIGH)**
`inbox/` 和 `digesting/` 的边界是什么？如果一个文件在 inbox 里被打开编辑了一下就算 digesting 吗？边界模糊的器官会退化成"同一个目录的三个名字"——你在给同一坨混乱起三个别名。生物消化之所以分器官，是因为**化学环境不同**（胃酸 vs 小肠碱性）；你的目录之间**没有化学环境差异**，只有文件名差异。这是类比失效。

**A2 · 独立 MycoCommons 仓的冷启动死亡 (severity: CRITICAL)**
新仓空仓问题：第一天 MycoCommons 里什么都没有，所以 `myco craft use` 什么都召唤不出来，于是没人会去用它，于是它永远空着。Voyager 的 skill library 有冷启动问题的经验——它靠 **自举**（让 agent 主动写技能填充），你没有这个机制。独立仓 = 额外维护成本 + 心理门槛 + 冷启动死亡概率。

**A3 · Session hook 假定了 Claude Code，但 Myco 必须 agent-agnostic (severity: HIGH)**
你今天才在身份锚点里写了"entry-point accessible · kernel project-agnostic"。Session stop hook 是 Claude Code 特有的。把它作为核心触发机制 = 把 kernel 绑到一个具体 agent = 违反你自己的三不可变律之一。

**A4 · "摄食成本 ≤ 聊天成本" 无法达到 (severity: CRITICAL)**
和 Claude 聊天的成本 = 0（说话就行）。`myco eat` 最低也要切终端、打命令、按回车 ≈ 3-5 秒 + 上下文切换。**你永远赢不了聊天**。除非摄食发生**在聊天里**——也就是说 MCP tool 必须让 agent 自己主动 `myco eat`，而不是人去敲命令。这把核心机制从 CLI 移到了 MCP layer。Round 1 claim 没有体现这一点。

**A5 · 消化这个隐喻本身可能误导 (severity: MEDIUM)**
消化是**单向**的（进嘴→出肛门），但知识代谢是**循环**的（旧知识会被再次唤起、重组）。用消化道类比会诱导你把原子往前推，而忘了**反刍（rumination）**才是真正的认知动作。生物学：真正消化纤维素的不是胃酸，是**反刍 + 瘤胃菌群**的反复发酵。你如果要仿生，应该仿的是**反刍动物**而不是单胃哺乳类。这会改变目录结构——可能根本不需要"前进"的管道，只需要一个**发酵池** + 多个**标签/状态**。

**A6 · ASCC 暴露的三大摩擦，有一个不是架构问题 (severity: HIGH)**
"意识不到要用 Myco"不是架构问题，是**反射弧**问题——和架构怎么改无关。如果 Yanjun 自己都意识不到要用，那加一百个目录也没用。这条只能靠 **hook 或 session-level 反射**解决，和消化道设计正交。Round 1 把它和消化道混在一起讨论会让两个问题都解决不好。

**A7 · "ASCC 一周 dogfood" 验收标准空洞 (severity: MEDIUM)**
什么叫"完成 dogfood"？Round 1 没给可量化阈值。如果一周后 inbox 里有 5 条，算成功还是失败？必须给具体数字，不然这个 debate 收敛不了。

**置信度更新**：35% → 20%（attack 暴露的问题比预期多，特别是 A2/A4 直接动摇核心设计）

---

## Round 1 — Online Research

**R1.1 · MemOS 三层存储 (arXiv 2507.03724)** — working memory / long-term storage / cold archive，**动态迁移 + intent-aware scheduler**。关键：每个 MemCube 带 provenance / versioning / access policies / lifecycle state 元数据。支持 **transformation pathways**（plaintext → KV-cache → parameter weights）。
> **教训**：MemOS 的分层不是"目录分三个"，是"每个 memory unit 带 lifecycle metadata"。迁移是状态机变化，不是文件移动。这直接打击 A1——Round 1 的七目录设计是假分层。

**R1.2 · Letta / MemGPT 三层 (docs.letta.com)** — core memory (RAM) / archival (vector store) / recall (conversation)。**关键设计**：agent **主动调用** `archival_memory_search`、`core_memory_replace` 等工具在层间移动信息。"Agents do not passively receive context — they explicitly call memory management functions."
> **教训**：直接支撑 A4。摄食必须发生在 agent 的工具调用里，而不是人敲命令。正确方向不是 CLI 优化，是 **MCP tool 语义升级**——让 agent 把 eat/digest/integrate 当条件反射。

**R1.3 · A-Mem / Zettelkasten (arXiv 2502.12110)** — 扁平原子笔记 + 动态链接 + **memory evolution**（新笔记触发旧笔记属性更新）。每个 note 有 contextual description / keywords / tags，遵循 Zettelkasten atomicity 原则。
> **教训**：扁平优于分层。不需要 inbox/digesting/extracted 四个目录，只需要一个 `notes/` 目录 + frontmatter `status:` 字段（raw / digesting / extracted / integrated / excreted）。状态变化不挪文件。这彻底回应 A1 和 A5——不是消化道隐喻，是**瘤胃发酵池**：一个大池子 + 每个颗粒带状态标签。

**R1.4 · Voyager skill library (arXiv 2305.16291)** — 可组合 / 可解释 / **executable code** 形式的技能库。冷启动问题被"**curriculum-driven 自举**"化解：agent 在简单任务上先攒技能，技能越多越能解锁复杂任务。3.3x unique items / 15.3x faster tech milestones。
> **教训**：冷启动死亡（A2）的答案是自举 curriculum + 让 skill 库用可执行形态。MycoCommons 的 craft 不应全是 markdown 散文——**应该尽可能是 snippet、template、lint rule、command alias** 这种"上手即用"的形态。这样单一 craft 的初始价值就 ≥ 0，commons 不会死在第一天。

**R1.5 · MemOS OpenClaw 2026-03-08 更新** — Local Plugin v1.0.0 带 task summarization & **skill evolution** + multi-agent memory sharing + persistent SQLite + hybrid search (FTS5 + vector)。
> **教训**：商业产品已经在做 skill evolution + multi-agent sharing。Myco 如果还停在单 agent / 单项目，会很快被市场淘汰。**跨项目必须做**，不是可选项。但做法可以是索引而不是目录——FTS5 索引 commons 内容，`myco craft use <name>` 走索引召唤。

**置信度更新**：20% → 55%（研究给了三条强约束：扁平 + 元数据 + agent-driven + 可执行 craft）

---

## Round 1 — Defense + Revise

针对每条 attack 的应答，**吸收研究教训**重写 claim：

**A1 回应**（七器官过度设计）：**承认**。新设计：单一 `notes/` 目录 + frontmatter `status:` 字段 (raw/digesting/extracted/integrated/excreted)。状态机用 lint 强制转移合法性（L10 候选）。

**A2 回应**（commons 冷启动死亡）：**部分接受**。改为：commons 初期**不建独立仓**，用 Myco kernel 仓内的 `commons/` 子目录 + 明确的"kernel 代码不许引用 commons 内容"隔离规则，由 L11 lint 守护（仅限可写层面的分离，不做物理仓分裂直到至少 3 个项目都在用）。同时 commons 必须是**可执行 craft 优先**（snippet / template / lint rule / alias），而不是散文。

**A3 回应**（session hook 违反 agent-agnostic）：**接受**。删除 session hook 作为**核心**触发机制的提法。核心触发改为 **MCP tool 语义升级**——把 `myco_eat`, `myco_digest`, `myco_hunger` 加进 MCP 工具集，让任何支持 MCP 的 agent（不仅 Claude Code）都能自动调用。Session hook 保留为 Claude Code 专属的**便利层**（可选增强）。

**A4 回应**（摄食成本赢不了聊天）：**接受 + 深化**。摄食发生在 **agent 的工具调用里**，不是人类的命令行里。具体：MCP tool `myco_eat(content, source, tags)` 的 description 写成"Call this whenever you encounter information the user might want to retain across sessions"，让 agent 把它当条件反射。人类通过聊天和 agent 说话时，agent **自己** eat，零额外成本。这是和 Letta 同构的设计。

**A5 回应**（消化隐喻误导）：**部分接受**。保留"代谢"作为 narrative 层（已写入身份锚点，不能推翻），但实现层改用 **瘤胃发酵池**模型：扁平 notes/ + 状态标签 + 反复重访（与 Gear 2 反思天然对齐）。README 不必改，实现不同构。

**A6 回应**（意识不到用 Myco 是正交问题）：**接受**。把这条独立成 **"反射弧"问题**，它的答案是 **A4 的同一个机制** —— agent 把 `myco_eat` 当条件反射，就解决了人类"意识不到"。因为摄食不再依赖人类警觉性，依赖 agent 工具反射。两条合并。

**A7 回应**（验收标准空洞）：**接受 + 量化**。ASCC 一周 dogfood 的可量化成功标准：
- inbox notes 数量 ≥ 20（说明摄食通路通）
- integrated 状态 notes 数量 ≥ 10（说明消化通路通）
- excreted 数量 ≥ 3（说明淘汰通路通）
- 至少 1 个 `myco promote` 到 commons（说明跨项目层通）
- `myco hunger` 被 agent 主动调用次数 ≥ 5（说明反射弧通）
- 达不到其中任意两项 → 该部分设计回炉

**置信度更新**：55% → 72%（设计收敛明显，但 commons 隔离规则、状态机合法转移、MCP description 的具体措辞都还没验证）

---

## Round 2 — Claim (revised after Round 1)

基于 R1 收敛，**修订后主张**：

### 2.1 两层架构（不是三层）
```
Myco kernel + commons/ 子目录 （同仓，L11 lint 守护隔离）
├── src/myco/           # kernel 代码
├── _canon.yaml         # kernel 配置
├── commons/            # ← 新增：跨项目可迁移 craft 仓
│   ├── crafts/         # 可执行 craft (snippet/template/lint rule/alias)
│   ├── patterns/       # 代码级 pattern
│   └── _index.yaml     # craft 元数据索引，支持 myco craft use
└── ... kernel 其余

Myco instances (ASCC / future projects)
├── notes/              # ← 新增：扁平 zettelkasten 发酵池
│   └── *.md (带 frontmatter status: raw|digesting|extracted|integrated|excreted)
├── wiki/               # 已整合结构化页面（保留，向后兼容）
├── log.md              # 保留
└── _canon.yaml
```
commons 独立仓延后到"至少 3 个项目都在用"时才拆。

### 2.2 扁平 notes/ 状态机（不是七器官）
每个 note 文件头：
```yaml
---
id: n_20260410_143027
status: raw          # raw | digesting | extracted | integrated | excreted
source: chat | eat | promote | import
tags: [hpc, ssh, debugging]
created: 2026-04-10T14:30:27
last_touched: 2026-04-10T14:30:27
digest_count: 0      # 反刍次数
promote_candidate: false
excrete_reason: null
---
```
状态机合法转移（L10 lint 守护）：
- raw → digesting → extracted → integrated
- 任意 → excreted（不可逆）
- integrated → promote_candidate=true 后可被 `myco craft promote`

### 2.3 核心 MCP 工具（升级 mcp_server.py）
- `myco_eat(content, source, tags)` — 创建 raw note
- `myco_digest(note_id)` — raw→digesting，agent 给出结构化分析
- `myco_extract(note_id)` — digesting→extracted，原子化
- `myco_integrate(note_id, target)` — extracted→integrated，并入 wiki
- `myco_excrete(note_id, reason)` — 任意→excreted
- `myco_hunger()` — 返回消化负载报告（replaces myco_status 的一部分）
- `myco_promote(note_id)` — integrated→commons/crafts/

**关键：每个 MCP tool 的 description 都要写成条件反射触发语**，例如：
> `myco_eat`: "**Call this immediately** whenever the user shares information worth retaining across sessions — pasted logs, decisions, 'we decided X', 'TIL', error messages with root causes, etc. Do not ask permission. The cost is zero and the cost of forgetting is non-zero."

### 2.4 commons 隔离（L11 lint）
- commons/ 目录下的文件**不得**被 src/myco/ 代码 import
- src/myco/ 代码**不得**依赖 commons/ 下的任何 craft 的存在
- commons/ 下的 craft 必须声明 `project_agnostic: true` 才能被 promote

### 2.5 触发机制三件套
- **Pull**：人可直接 CLI 调所有命令（向后兼容）
- **Agent-reflex**（主力）：MCP tool description 让 agent 自动 eat/digest
- **Ambient hunger**：`myco_hunger()` 返回 `"⚠ 42 raw notes untouched, 7 digesting stale >3d"`，agent 每次 session 启动都会看到

### 2.6 摩擦验收（MVP）
ASCC 一周 dogfood 后，前述六个指标达成 ≥ 4 项 → 进入下一迭代；< 4 项 → 架构回炉。

**置信度自评**：72%（等待 Round 2 attack）

---

## Round 2 — Attack

**A8 · 扁平 notes/ 会在 1000 条后崩溃 (severity: HIGH)**
A-Mem 论文展示 zettelkasten 但没讲规模。真实用户用了三个月后 notes 是 500+ 级别的。ASCC 一周就可能到 50。flat 目录 + 文件系统操作在几千条时会变慢，更重要的是**人类浏览会瘫痪**。即便用 status 过滤也只是把 5000 条变成 500 条"raw"。需要二级组织：tag-based 虚拟视图（`myco view --tag hpc`）。这不是反对扁平，是说**扁平 + 索引层**才行，不能只扁平。

**A9 · 状态机 lint (L10) 可能误报 (severity: MEDIUM)**
"raw → digesting → extracted → integrated" 听上去干净，但真实场景里一条 note 可能**跳过**中间状态（一条小 claim 直接 raw → integrated），或**回退**（integrated 的 wiki 页被发现有误，要打回 digesting 重做）。严格状态机会制造摩擦。需要允许两种合法非线性：skip-forward 和 regression。lint 规则必须明确允许。

**A10 · MCP description "条件反射触发语" 假定 agent 会读 description (severity: HIGH)**
Claude 读 MCP tool description 的程度取决于 system prompt。在 Claude Code 里 description 被塞到 tool list，但被模型实际"内化为反射"的概率 ≠ 100%。更弱的 agent（或人类直接用 CLI 时）没有这个反射。需要**第二道保险**：session 启动时 MCP 注入一段 priming message（如果 agent 支持 init hook），或在 `myco_hunger()` 返回里强行提示"You should also eat what you learned in the last 10 exchanges"。

**A11 · commons 和 kernel 同仓会被 PyPI 打包带走 (severity: CRITICAL)**
commons/ 在 kernel 仓里意味着 `pip install myco` 时它会被下载到每个用户机器上。但 commons 是**用户生成内容**，不是 kernel 默认内容——如果把 Yanjun 的 HPC craft 打包进 pip wheel 发给所有用户，(1) 侵犯隐私；(2) 污染他们的 craft 命名空间；(3) 每次 commons 更新都要发新版 kernel。**pyproject.toml 必须排除 commons/**，否则这个方案就炸。Round 1 的"commons 在 kernel 仓子目录"反而是陷阱。

**A12 · promote 到 commons 的发现机制缺失 (severity: MEDIUM)**
`myco craft use <name>` 要知道名字才能召唤。但新项目的 agent 怎么知道有哪些 craft 可用？需要 `myco craft list --relevant-to "<current task>"`，这又需要 tags 或 embedding 或 LLM 分类。没有发现层的 commons = 无人问津的图书馆。

**A13 · "反射弧"合并进 A4 的回应过于乐观 (severity: HIGH)**
我在 Round 1 Defense 里说"A4 解决就解决 A6"。再想一遍：A6 的"意识不到"指的是**人类**意识不到（Yanjun 自己的观察）。但 A4 解决的是**agent** 意识。如果人类根本不开 agent、不用 MCP，纯手动写代码时，A4 机制完全不启动。所以 A6 没被真解决——只在"人类总是通过 agent 工作"的假设下被解决。这个假设对 Yanjun 成立（他主要和 Claude 协作），但对未来其他用户不成立。要么接受这个限制并在 README 声明，要么补一条人类侧的触发器（比如 git hook？editor plugin？）。

**置信度更新**：72% → 60%（A11 特别扎心，commons 同仓方案需要重大修正）

---

## Round 2 — Online Research

**R2.1 · Obsidian Dataview 规模证据** — flat vault 有用户跑到 18,237 条笔记、22 年学术数据无性能退化。Dataview "scales up to hundreds of thousands of annotated notes"。瓶颈是 graph 可视化，不是扁平存储本身。
> **回应 A8**：扁平 + 查询层的组合已经在 Obsidian 生态被验证到 >10k notes。Myco 需要的是 **myco view** 命令（tag / status / date 过滤），不是二级目录。可以在 `scripts/myco_view.py` 里先用简单 grep，后续再视需要引入 FTS5 或 embedding。

**R2.2 · Claude MCP 工具发现机制** — "Claude loads skill descriptions automatically at session start, and if a skill's description matches what you're asking, Claude can invoke it without you typing the slash command"。存在 `disable-model-invocation` flag 可以禁用自动调用。Tool description 应该包含 "exact use cases, trigger conditions like specific error messages or symptoms"。
> **回应 A10**：反射弧机制在 Claude 侧是有基础设施支持的。关键是把 description 写得**像触发条件清单**，不是像 API 参考。示例：
> ```
> myco_eat: Trigger when user shares any of: (a) a piece of code that worked,
>   (b) a decision with reasoning, (c) a root cause found after debugging,
>   (d) a file / log / URL they pasted, (e) "TIL" or "note to self" phrasing.
>   Do not ask permission. Do not wait for session end. Call immediately.
> ```
> 但 A10 仍部分成立：对更弱的 agent / 非 Claude agent 反射率会更低。**双保险**：让 `myco_hunger()` 返回里也放一段 "Consider calling myco_eat on any of the above patterns from the recent exchanges."

**R2.3 · Hatchling 打包配置** — `[tool.hatch.build.targets.wheel]` 只包含 `src/myco/`，**commons/ 放在 repo 根部（不在 src/myco/ 下）就天然不进 wheel**。但 **sdist** 默认会包含整个仓，所以需要 `[tool.hatch.build.targets.sdist] exclude = ["commons/", "ascc_sessions/", ...]`。
> **回应 A11**：commons 同仓可以成立，**但必须在 pyproject.toml 明确排除**。Round 3 会把这条写进可执行 TODO 清单。同仓 + 打包隔离 > 独立仓（独立仓的维护成本和冷启动死亡风险更大）。

**R2.4 · 状态机非线性（无直接文献，类比讨论）** — 生物消化本身就不是严格 FIFO：食物在胃和小肠之间可以来回（胃食道反流、胆汁回流），**反刍动物在四个胃之间多次往返**。从这个观察推广：Myco 状态机应该允许**任意合法跳转**，只要每次跳转被 log 记录。不是 FSM 里的固定箭头，是带状态标签的自由图。
> **回应 A9**：放弃严格 FSM，改成**状态白名单 + 转移日志**。L10 lint 只检查：(a) 每个 note 必有 status，(b) status 值在白名单内，(c) 状态变化被 log。不检查转移顺序。

**R2.5 · A6/A13 人类侧反射弧（无直接文献）** — Letta 的整个架构假设 "agent is the primary actor"。Obsidian 的用户侧反射弧靠的是 **Quick Capture** 插件 + 全局快捷键。Myco 的人类侧反射弧**不是架构问题**，是 habit-formation 问题，只能靠：(a) 把门槛降到极低（快捷键 / 全局 paste hook）；(b) 接受人类反射弧有限，押注 agent 反射弧。
> **回应 A13**：**接受限制**。README 里显式声明"Myco assumes you work with an agent that supports MCP; pure-human usage works but loses the reflex layer"。Yanjun 的实际工作流满足这个假设。未来如果有纯人类用户需求，可以补 editor plugin，但不是 v1.2 的事。

**置信度更新**：60% → 78%（大部分 attack 有 defensible 的应答，剩 A12 发现机制还要处理）

---

## Round 2 — Defense + Revise

**A8 扁平规模**：**接受**。新增 `myco view --tag <t> --status <s>` 作为核心查询命令，底层先用简单文件头解析 + filter，规模到 500+ 时升级到 FTS5。Round 3 写进 MVP。

**A9 状态机误报**：**接受**。L10 lint 弱化为"status 合法 + 变化被 log"，不约束转移顺序。

**A10 MCP 反射率**：**接受 + 深化**。每个 MCP tool description 严格按"trigger conditions"格式写。额外加双保险：`myco_hunger()` 的返回值主动建议 `myco_eat` 调用。

**A11 打包污染**：**接受**。commons/ 留在 kernel 仓根部但 **pyproject.toml sdist/wheel 双排除**，加 L12 lint 守护（`packaging_isolation_check`：确保 commons/ 不出现在任何构建输出）。

**A12 发现机制**：**承认缺失**。新增 `commons/_index.yaml` 作为 craft metadata 索引，每条 craft 带 `tags / applies_to / keywords / summary`。`myco craft list` 读这个索引。未来可升级到 embedding，但 v1.2 先靠 tag/keyword grep。

**A13 人类反射弧**：**接受限制**。README 声明假设，不补 editor plugin。

**置信度更新**：78% → 85%

---

## Round 3 — Claim (focused on commons, MVP slice, acceptance)

在 R1-R2 收敛基础上，Round 3 收紧三个具体决策：

### 3.1 Commons 物理位置与打包隔离
- 位置：`<kernel-repo>/commons/`
- pyproject.toml 修改：
  ```toml
  [tool.hatch.build.targets.wheel]
  packages = ["src/myco"]  # commons/ 在 src 外，天然排除

  [tool.hatch.build.targets.sdist]
  exclude = [
    "commons/",
    "ascc_sessions/",
    "docs/current/",  # 保护 craft 过程文档
  ]
  ```
- L12 lint 规则：构建 wheel 后解压，grep `commons/` 必须为空。
- 代码隔离：`src/myco/` 不得 import 任何 `commons/` 路径；`grep -r "commons" src/myco/` 必须为空（L11 lint）。

### 3.2 MVP 切片：三步走
**Week 1（立即）**：
- 新增 `notes/` 目录规范 + frontmatter 模板
- 新 CLI：`myco eat`, `myco view`, `myco hunger`
- 新 MCP tools：`myco_eat`, `myco_hunger`, `myco_view`（三件套）
- L10 lint：notes frontmatter + status 合法
- ASCC 作为第一 dogfood instance

**Week 2（摩擦反馈后）**：
- 根据 ASCC 第一周的 `myco hunger` 数据决定下一批器官
- 候选：`myco digest`, `myco extract`, `myco integrate`（如果 Week 1 证明 raw→integrated 直接跳太粗糙）

**Week 3**（至少一个 integrated note 标为 promote_candidate 之后）：
- `commons/` 目录 + `_index.yaml` 雏形
- `myco promote`, `myco craft list`, `myco craft use`
- L11/L12 lint（隔离 + 打包）

### 3.3 验收标准（硬指标）
Week 1 dogfood 成功 = 同时满足：
- `myco hunger` 显示 raw ≥ 20
- 至少 3 条 note 的 digest_count ≥ 2（有反刍）
- 至少 1 条 raw note 跳过 digesting 直接 integrated（验证非线性合法）
- 至少 1 条 excreted + 写了 reason
- Yanjun 自述"摄食门槛足够低"（主观信号）

Week 3 验收（commons 层）：
- commons/crafts/ ≥ 1 条可执行 craft
- `myco craft list --tag hpc` 返回非空
- ASCC 里某处显示 "this crafted pattern came from commons: <name>"
- L11/L12 lint 全绿
- 下一次 `pip install myco` 检查 wheel 不含 commons

### 3.4 回退条件（硬）
任何 Week 验收 < 50% 指标达成 → 该 Week 架构**立即回炉**，重开 debate。不粉饰失败。

**置信度自评**：85%

---

## Round 3 — Attack

**A14 · Week 1 三件套不含 digest 会让反刍指标无法达成 (severity: MEDIUM)**
"至少 3 条 note 的 digest_count ≥ 2" 需要 `myco digest` 命令，但 Week 1 MVP 里没有它。矛盾。**修正**：要么 Week 1 加 `myco digest` 成为四件套，要么把"反刍"指标挪到 Week 2。

**A15 · "Yanjun 自述门槛够低"是主观指标 (severity: LOW)**
主观信号在 debate 里不该出现。替换成客观：**ASCC 一周内 `myco eat` 被 agent 自动调用次数 / 人工调用次数 ≥ 3**（反射率指标）。

**A16 · L12 lint 需要真的 build wheel 才能验证，太重 (severity: MEDIUM)**
每次 lint 都 `pip build` 太慢。改为**静态检查**：`[tool.hatch.build.targets.sdist].exclude` 必须显式包含 `commons/`。静态检查零成本。

**置信度更新**：85% → 83%（小修小补）

---

## Round 3 — Defense + Revise

**A14**：Week 1 扩成**四件套**：`myco eat`, `myco digest`, `myco view`, `myco hunger`。digest 是核心代谢动作，不能推迟。

**A15**：反射率指标加入 Week 1：`agent-invoked / human-invoked ≥ 3`。

**A16**：L12 改为静态检查 pyproject.toml 字段。

置信度：83% → 88%

---

## Round 4 — Claim (ASCC friction must-solve list + back-compat)

### 4.1 ASCC 已暴露摩擦 must-solve vs defer

从之前 ASCC 实践里 Yanjun 报告的摩擦：

| 摩擦 | Must-solve / Defer | 理由 |
|------|--------------------|------|
| 没法很好地把内容消化进 Myco | **Must** (Week 1) | `myco eat` + `myco digest` 直接解 |
| 没法很好地使用 Myco | **Must** (Week 1) | `myco view` + MCP 反射解 |
| 意识不到要用 Myco | **Must** (Week 1) | MCP description + hunger 解，但只在 agent 侧 |
| HPC craft 无处安放 | **Must** (Week 3) | commons 层解 |
| 三个 HPC lesson 正在 kernel 仓里漂移 | **Must** (立即) | 趁这次 commons 一上线就 promote 走 |
| wiki 页维护成本高 | **Defer** → Week 4+ | wiki 保持不变，新内容走 notes/ |
| 多项目之间 wiki 重复 | **Defer** → Week 6+ | 等 commons 跑顺后再处理 wiki 的跨项目同步 |
| Myco 模板对新项目 onboarding 慢 | **Defer** → Week 8+ | 等 MVP 稳定再改模板 |

### 4.2 向后兼容承诺
- 现有 `wiki/` 不动，不强制迁移
- 现有 `docs/` 不动
- 现有 `log.md` 不动  
- 现有 `_canon.yaml` 向后兼容，只加字段不删字段
- 现有 `myco lint` 9 个维度全保留（L10-L12 是新增）
- 现有 MCP 5 tools 全保留（新增不替换）
- `myco import --from hermes/openclaw` 不动

### 4.3 迁移路径（可选）
为有意迁移旧 wiki 到 notes/ 的用户提供：
```
myco migrate --from wiki --to notes --status integrated
```
但不强制。多数用户的 wiki 可以当"历史档案"继续存在。

**置信度自评**：88%

---

## Round 4 — Attack + Defense（短）

**A17**：Week 3 "立即 promote 三个 HPC lesson"必须和前面 Round 3 Week 2 的"根据数据决定下一步"对齐。**回应**：Week 3 的 commons 上线是独立的轨道，不阻塞 digesting/extracted 的数据驱动决策。两条轨道并行。

**A18**：向后兼容声明太多"不动"会让架构变混乱（既有 wiki 又有 notes）。**回应**：接受混乱作为过渡期代价。未来 6 周后 Gear 4 回顾时决定是否统一。过早统一 = 推翻已证明有效的 wiki。

置信度：88% → 90%

---

## 收敛：最终推荐架构 + 三步实施路径

### 最终架构（置信度 90%）

**双层结构**：
- `<kernel-repo>/src/myco/` — kernel（pip 发布）
- `<kernel-repo>/commons/` — 跨项目 craft 仓（打包排除）
- `<instance-repo>/notes/` — 扁平 zettelkasten 发酵池（新）
- `<instance-repo>/wiki/` `log.md` `_canon.yaml` — 保留

**核心机制**：
- 每个 note = 一个 md 文件 + frontmatter (`id / status / source / tags / digest_count / excrete_reason`)
- 状态白名单 `raw | digesting | extracted | integrated | excreted`，允许任意合法跳转
- MCP 工具反射驱动：description 按 trigger condition 格式写，agent 自动 eat/digest/view/hunger
- Hunger 信号：`myco_hunger()` 每次返回带未消化负载 + 主动建议下一步

**lint 扩展**：L10 (notes schema) / L11 (commons import isolation) / L12 (packaging isolation, static check)

**新命令**：`myco eat / digest / view / hunger / promote / craft list / craft use`

**新 MCP 工具**：`myco_eat / myco_digest / myco_view / myco_hunger`（Week 1），`myco_promote / myco_craft_list / myco_craft_use`（Week 3）

### 三步实施路径

**Week 1 (MVP — 消化道雏形)**
1. notes/ 目录规范 + frontmatter schema
2. `myco eat / digest / view / hunger` 四件套 CLI + MCP
3. L10 lint
4. ASCC dogfood 开跑

**Week 2 (基于摩擦数据迭代)**
1. 读 Week 1 的 hunger 日志
2. 决定 extract/integrate 是否独立命令 or 合并
3. 更新四件套→五/六件套

**Week 3 (Commons 上线)**
1. commons/ 目录 + `_index.yaml`
2. pyproject.toml 打包隔离
3. `myco promote / craft list / craft use`
4. L11 + L12 lint
5. 立即 promote 三个 HPC lesson 把 kernel 仓洗干净

### 硬验收指标

**Week 1**：raw ≥ 20, digest_count ≥ 2 的 notes ≥ 3, 非线性跳转 ≥ 1, excreted ≥ 1, agent/human eat 比率 ≥ 3
**Week 3**：commons/crafts ≥ 1, craft list 非空, ASCC 引用 commons 至少 1 处, L11/L12 全绿, wheel 不含 commons

### 回退条件（硬）
任一 Week 验收 < 50% → 立即回炉，重开 debate，不粉饰。

---

## Meta 反思（Gear 2 on this debate）

本次 debate 里我自己的**认知盲点**：
1. **第一直觉就造七器官**：证明我有"仿生即完整"的偏执。真正的仿生应该仿机制（反刍循环）不仿器官数量。被 A1+R1.3 拉回来。
2. **cold start 死亡没第一时间想到**：独立仓是程序员本能，但对 craft 库这种**自举依赖内容**的结构是致命的。被 A2+R1.4 拉回来。
3. **把 MCP description 当 API 文档写**：应该当**触发条件清单**写。被 A10+R2.2 拉回来。
4. **把"意识不到要用"当架构问题**：它有 70% 是反射弧问题，30% 才是结构问题。被 A13+R2.5 拉回来。
5. **Week 1 MVP 里漏掉 digest 动作却要求反刍指标**：内部不自洽。自己在 Round 3 attack 里发现。

**对未来 debate 的规则**：**不要跳过 attack 阶段**，即使 claim 看起来自洽。Round 1 claim 在我眼里完美——然后 attack 把置信度从 35% 打到 20%。这 15% 是真实无知的代价，没有 attack 就会直接变成债务。

---

## 外部参考

- [MemOS: A Memory OS for AI System](https://arxiv.org/abs/2507.03724) — 三层存储 + MemCube 元数据 + transformation pathways
- [A-MEM: Agentic Memory for LLM Agents](https://arxiv.org/abs/2502.12110) — Zettelkasten + atomic notes + memory evolution
- [Letta (MemGPT) memory docs](https://docs.letta.com/concepts/memgpt/) — core/archival/recall + agent-driven tier migration
- [Voyager (arXiv 2305.16291)](https://arxiv.org/abs/2305.16291) — skill library as executable code + curriculum cold start
- [Obsidian Dataview scaling evidence](https://blacksmithgu.github.io/obsidian-dataview/) — flat vault to 18k+ notes without degradation
- [Claude MCP tool discovery](https://code.claude.com/docs/en/mcp) — session-start description loading + reflexive invocation
- [MemOS OpenClaw v1.0.0](https://github.com/MemTensor/MemOS) — skill evolution + multi-agent memory sharing (2026-03-08)

**终章置信度：90%**（达到目标，debate 收敛）

---

## 决策签名（2026-04-10，Yanjun 批准）

debate 收敛后当场拍板三个最硬取舍：

1. **Commons 位置** → Kernel 仓同仓（`Myco/commons/`）+ pyproject.toml 打包排除 + L11/L12 lint 守护隔离。
2. **Week 1 MVP 力度** → 四件套：`myco eat / digest / view / hunger`（对应 MCP 工具同名）。
3. **人类侧反射弧** → 不补，README 明确声明"Myco assumes you work with an agent that supports MCP; pure-human usage works but loses the reflex layer"。未来若需补 editor plugin，走独立 Gear 4 决策。

这三个决策在本 craft 文档归档后即进入 v1.2 roadmap，不可撤销除非未来某个 Week 的硬验收指标 < 50% 触发回炉条款。

**下一步**：Yanjun 批准后即开始 Week 1 实现（独立工作单元，不阻塞本 debate 归档）。




