# Contract Changelog

本文件记录 Myco kernel contract（`docs/agent_protocol.md` + `_canon.yaml`
+ `scripts/lint_knowledge.py` + `src/myco/lint.py` + `src/myco/mcp_server.py`
+ `src/myco/templates/**`）的版本变更。

版本号遵循 Semantic Versioning：

- **MAJOR**：破坏性变更（移除/重命名原则、修改已有原则语义、下游必须改代码）。
- **MINOR**：向后兼容的新增（新原则、新 lint 维度、新触发点、新字段）。
- **PATCH**：仅措辞/typo/非语义微调。

Commit message 格式必须使用 Conventional Commits 风格并带 `[contract:*]` 前缀：

```
[contract:minor] §8 Upstream Protocol v1.0 + §5 on-self-correction
[contract:patch] §4 措辞微调
[contract:major] 移除 L3 原则（与 L11 合并）
```

下游实例通过 `_canon.yaml: system.contract_version` 与本地 `synced_contract_version`
比对来感知 drift。

---

## v1.5.0 — 2026-04-11 (minor)

**Author**: Claude (Myco kernel agent, autonomous run under user grant)
**Craft record**: `docs/primordia/biomimetic_restructure_craft_2026-04-11.md`
（3 轮 Claim→Attack→Research→Defense→Revise，终置信度 0.92，
`decision_class: kernel_contract`，floor 0.90；8 个 Round-1 attack +
3 个 Round-2 attack + 1 次 Round-3 on-self-correction 全部落地）
**Trigger**: 用户在 2026-04-11 panorama 回顾后明确提出
"Myco 的项目结构彻底重构重组织 + 借鉴仿生 Myco 生物学的优点和特点"，
并把这件事定位为"Myco 永恒进化的一部分——不断优化自己的内容组织形式"，
把压缩 doctrine 从代谢层（notes 压缩）升维到结构层（目录与文档拓扑压缩）。

**Self-correction 事件**：craft Round 1 的 Claim A "wiki/ 是空目录、rename
零代码成本" 在 Phase A1 执行前 grep 实测暴露为**错误前提**——`wiki/` 在
`src/myco/import_cmd.py` 硬编码 14 处（含整个 `hermes_skill_to_wiki()` 函数）、
`_canon.yaml` 5 处（含 `wiki_page_types` schema block）、6 份 contract 文档
+ README.md + MYCO.md 共 ~50 处深度引用。这是 "Map vs Territory 混淆" 的
教科书案例——只看了"物理空目录"就断定"概念空"。Round 3 修正后 Phase A1
被取消，`wiki/` 保留原名。这次 self-correction 本身被写进 craft §5b 作为
方法论案例，供未来 agent 学习。

### Added

**`docs/biomimetic_map.md`（新，contract 级身份锚点文档）**
- §0 为什么要有这份文档：把 Myco 的生物学血统给一个真实落脚点，同时
  严守"不强行套 metaphor"的纪律——只在真实信息增益处应用生物学命名。
- §1 生物学术语 Glossary：hypha / mycelium / primordium / sporocarp /
  spore / rhizomorph / exoenzyme / septum / sclerotium / mycorrhiza /
  hyphal tip 共 11 条定义，每条都附 "对应 Myco 基质" 的映射说明。
- §2 实际应用的映射表：12 行表格明确记录每个基质位置是否 rename、
  使用哪个生物学类比、理由。**唯一执行的 rename 是
  `docs/current/ → docs/primordia/`**。
- §3 为什么不全面 rename：三条架构理由（边际收益递减 / 架构腐蚀 vs
  biomimicry purity / 年轻红线保护）。这一节的存在本身是防止未来
  agent 重新发动一次"为生物学而生物学"的 rename 冲动。
- §4 压缩 doctrine 的生物学映射：sclerotium（致密休眠）/ autolysis（自溶）/
  nutrient reallocation（资源重分配）三条具体实现，其中 autolysis 和
  reallocation 已部分实现（D 层 dead_knowledge + hunger 信号），
  sclerotium 登记为未来工作。
- §5 Living document 维护规则 + §6 延伸阅读（含 Smith & Read 标准教材引用）。

**`_canon.yaml → system.structural_limits`（新 block）**
- `docs_top_level_soft_limit: 20` + `primordia_soft_limit: 40`
  —— 固定种子阈值，不是 adaptive；adaptive threshold 登记在
  `docs/open_problems.md §4` 作为后续工作。
- `exclude_paths: [10 条 contract 级文档]` —— 被明确列出的 contract 文档
  不计入 docs/ top-level 计数的分母，它们是 rhizomorph 不是 bloat。

**`src/myco/notes.py` 新函数**
- `detect_structural_bloat(root)` —— **只读**扫描 `docs/*.md` +
  `docs/primordia/*.md`，对照 canon 的 soft limits + exclude_paths
  生成 signal string 或 None。严守 read/write 分离红线——不触碰任何
  note 元数据。
- `_load_structural_limits(root)` helper —— 从 canon 读取阈值配置，
  缺失时使用 `DEFAULT_STRUCTURAL_LIMITS` 常量回退，保证老 instance
  向后兼容。
- `compute_hunger_report` 集成：新信号附加到 signals list 末尾，
  位置在 `dead_knowledge` 之后。

**`src/myco/templates/_canon.yaml`**
- 镜像同步 `structural_limits` block。
- `synced_contract_version: v1.4.0 → v1.5.0`。

### Changed

- `_canon.yaml::system.contract_version: v1.4.0 → v1.5.0`
- **`docs/current/ → docs/primordia/`**（**唯一的 rename**，~80 refs
  across 35 files；canon `craft_protocol.dir` 作为 SSoT，Python 默认
  回退值同步更新）
- `docs/contract_changelog.md` / `docs/craft_protocol.md` / `docs/agent_protocol.md`
  / `docs/open_problems.md` / `docs/architecture.md` / `MYCO.md` / `README.md`
  / 等 35 份文件的 `docs/current` 字符串引用全部更新为 `docs/primordia`。

### Rationale

**为什么"克制的仿生"而不是"全面的仿生"**：
craft Round 1-3 的真正产物不是 rename 本身，是**纪律**——边际收益原则
告诉基质：只在新名字的信息增量 > 学习成本 + 引用改动成本时执行 rename。
大多数基质目录（`notes/`, `src/`, `scripts/`, `docs/` 顶层）的通用名字
已经在这个不等式的错误一侧。唯一清晰越过门槛的是 `docs/current/ →
docs/primordia/`——"current" 只表达"正在活跃"，"primordia" 准确表达
"未定型、发育中、可退化"，+1 单位的语义清晰度值得 ~80 处引用改动。

**为什么结构 bloat 用 hunger signal 而不是 L14 lint**：
bloat 是**渐进退化**问题不是硬错误。Hunger 的语义是"基质在这方面饿了/撑了"，
驱动行为但不阻塞 commit。Lint 的语义是"违反 contract"，20 份 docs 本身
不违反任何 contract 只是值得注意，语义错位。同时 L13 §8 反向废弃标准
提醒基质："不要为了 lint 越多越好而创造 lint"——把 `structural_bloat`
留在 hunger 层是对这条原则的一致应用。这个决策本身被记录在 craft §4 R2.3
作为"L14 dead-on-arrival decision"的案例。

**为什么 Phase B ASCC 合并被取消**：
craft R2.2 设定了 70% Jaccard overlap 的合并门槛。Phase B 实测
`docs/ascc_migration_v1_2.md` vs `docs/ascc_agent_handoff_prompt.md` 的
token-level Jaccard = 28.15%，远低于门槛。两份文件服务于真实不同的受众
（human operator playbook vs paste-ready agent prompt）和结构（13 headers
vs 27 headers）。Gate 正确地阻止了一次会破坏信息的"压缩"。这是压缩
doctrine 的反例——**压缩不等于合并，压缩要先证明不是在破坏差异**。

**为什么 craft 需要 Round 3 on-self-correction**：
Round 1-2 的 Claim A1 "wiki/ 零成本 rename" 只是空想 check，没有实测
grep。Phase A1 执行前的前置 grep 直接证伪这个前提，触发 craft 内
on-self-correction（`docs/agent_protocol.md §5.1`）——craft 必须**在
执行前**纠正自己，而不是把错误传播到 commit。这是 Craft Protocol §2
"Research 轮可触发 Revise" 机制的第一次真实应用。**置信度 0.92 不是
从 0.91 "提高" 到 0.92，而是 craft 在收窄 scope 后对更小范围给出更
诚实评估**。

### Known non-goals (v1.5.0)

- **不 rename `notes/`**：硬编码深度太深，收益不足，红线风险。
- **不 rename `wiki/`**：50+ 处引用、概念承载深度高、Karpathy 血统正向。
- **不 rename `docs/open_problems.md → hyphal_tips.md`**：语义增益真实
  但需独立 craft 更新登记规则，留作未来工作。
- **不实现 sclerotium（致密休眠）压缩管线**：COMPILED→wiki+pointer 的
  压缩自动化，延伸 open_problems §4。
- **不实现 adaptive threshold**：`structural_bloat` 用固定种子阈值，
  自适应阈值随基质年龄进化登记为未来工作。
- **没有 L14 lint**：`structural_bloat` 明确选 hunger 层，不创建硬 lint。

### Migration

- **下游 instance 升级指令（机械执行）**：
  ```
  git mv docs/current docs/primordia
  # 更新 _canon.yaml::system.craft_protocol.dir: docs/current → docs/primordia
  # 更新 _canon.yaml::system.synced_contract_version: → v1.5.0
  # 全局替换 docs/current → docs/primordia（literal string，无 English-prose 冲突风险）
  # 添加 _canon.yaml::system.structural_limits block（copy from kernel template）
  # 运行 myco lint，确认 14/14 PASS
  ```
- `myco hunger --json` schema 在 signals 数组中可能出现新条目
  `structural_bloat`，消费者可安全忽略直到准备好。
- `docs/biomimetic_map.md` 是新增 contract 级文档——instance 可选择
  复制一份作为本地身份锚点，也可直接引用 kernel 版本。

---

## v1.4.0 — 2026-04-11 (minor)

**Author**: Claude (Myco kernel agent, autonomous run under user grant)
**Craft record**: `docs/primordia/dead_knowledge_seed_craft_2026-04-11.md`
（2 轮 Claim→Attack→Research→Defense→Revise，终置信度 91%，
`decision_class: kernel_contract`，floor 0.90；8 个 Round-1 attack + 3 个 Round-2 attack 全部防御）
**Trigger**: `docs/open_problems.md §6` 登记的 Self-Model D 层空洞
（vision_recovery_craft §B 与 dead-knowledge 定义）需要可落地的最小种子，
以免 open problem 永久停留在"已知未实现"状态。

### Added

**`_canon.yaml → system.notes_schema` 扩展**
- `optional_fields: [view_count, last_viewed_at]`
  —— L10 识别但不强制，向后兼容所有历史 note（grandfather 生效）。
- `terminal_statuses: [extracted, integrated]`
  —— 被 D 层死知识检测用作入闸条件；仅处于"已settled"状态的 note 才能被判 dead。
- `dead_knowledge_threshold_days: 30`
  —— 默认阈值，同时用作"刚创建宽限期 + 未触碰冷却期 + 未阅读冷却期"三道闸的统一单位。
  instance 可通过 `myco config` 覆盖，SSoT 仍在 `_canon.yaml`。

**`src/myco/notes.py` 新 API + 新数据**
- `record_view(path, *, now=None)` —— D 层 read-side 唯一写入路径：
  递增 `view_count`（缺省视作 0），写入 `last_viewed_at=now`，**绝不触碰 `last_touched`**。
  read/write 严格分离是本次改动的架构红线（防止"打开即修改"污染冷却信号）。
- `HungerReport` dataclass 新增 `dead_notes: List[Dict]` + `dead_threshold_days: int`；
  `to_dict()` 暴露两者以便 `--json` 消费者使用。
- `compute_hunger_report(root, *, stale_days=7, dead_threshold_days=None, terminal_statuses=None, now=None)`
  签名扩展；缺省值从 `_load_dead_config(root)` 读取 canon。
- 5 条件联合死知识判定循环（status ∈ terminal / created ≥ threshold /
  last_touched 冷 / last_viewed_at 空或冷 / view_count < 2），任一不满足即豁免。
- 新增信号字符串 `dead_knowledge: N terminal note(s) ...`。

**`src/myco/notes_cmd.py` CLI 集成**
- `run_view` 单 note 模式在渲染 body 后调用 `record_view(path)`；
  失败仅静默（view 仍保留读操作语义），并在 header 额外展示 `view_count` / `last_viewed_at` 字段（若存在）。
- `run_hunger` 在 promote_candidates 之后新增 💀 dead knowledge 显示块，
  列出前 10 条 + "…(N more)" 折叠；`dead_knowledge` 被加入 concerning 信号判定。

**`src/myco/templates/_canon.yaml`**
- 镜像同步上述 notes_schema 扩展。
- `synced_contract_version: v1.3.0 → v1.4.0`。

### Changed

- `_canon.yaml::system.contract_version: v1.3.0 → v1.4.0`。
- `docs/open_problems.md §6` 增加"已落地于 contract v1.4.0" 标记 + craft 反向链接；
  出口条件下调为"第一个真实的 excretion 决策基于 dead_knowledge 信号"。

### Rationale

vision_recovery_craft 明确 "D 层未实现" 是 Self-Model 的四大空洞之一。
Wave 3 把它登记进 open_problems.md §6，但登记本身不是进展——**种子必须能长**。
本次改动锚定：
- **最小种子优于完美方案**：完整 D 层需要 audit log / cross-ref / adaptive threshold，
  任何一项都足以拖延数月。v1.4.0 只做"能被真实 excretion 决策触发的最小闭环"。
- **grandfather 是软扩展的唯一入场券**：所有历史 note 都没有 view_count / last_viewed_at，
  optional_fields 机制保证 L10 不倒戈，老 note 的 view_count 缺省按 0 处理，
  首次达到宽限期 + 冷却期 + 无读 = 自动入选 dead，系统自动完成迁移。
- **read/write 分离是反污染红线**：若 `myco view` 顺手 bump `last_touched`，
  冷却信号就永远为 0，D 层变空操作。这条防御必须写进代码而不是文档。

### Known non-goals (v1.4.0)

- **没有 view audit log**：只知"被 view 了 N 次"，不知"谁在什么上下文下 view 的"。
  excretion 决策仍需要人类判断"是否真的没人用"。
- **没有 cross-reference 追踪**：note 被 wiki 引用不会算作 "alive"。
  这是 §6 完整实现留给下一个 instance_contract 级 craft 的工作。
- **阈值是硬编码 SSoT**：没有随 substrate 年龄自适应的能力——
  Wave 5+ 才会触及身份锚点 4 的 adaptive threshold。
- **D 层的定义仍不完整**：本次只实现了"dead knowledge detection" 这一条；
  "degraded self-model" / "structural decay" 等子问题仍在 open_problems.md §5。

### Migration

- **No action required for existing substrates**: 所有 v1.3.0 及之前创建的 note
  自动带 `view_count=0 / last_viewed_at=None`，进入 dead 检测 pipeline 无需任何改动。
- **Instance agents**: 建议比对 `_canon.yaml::contract_version` 与
  `synced_contract_version`，drift 时跑 `myco lint` 验证 L10 / L13 / L11 仍 PASS。
- **Downstream tools**: `myco hunger --json` schema 增加 `dead_notes[]` 字段，
  消费者可安全忽略直到准备好。

---

## v1.3.0 — 2026-04-11 (minor)

**Author**: Claude (Myco kernel agent, autonomous run under user grant)
**Craft record**: `docs/primordia/craft_formalization_craft_2026-04-11.md`
（3 轮 Claim→Attack→Research→Defense→Revise，终置信度 91%，`decision_class: kernel_contract`，floor 0.90）
**Trigger**: 用户授权全权推进工作后，首项任务为"传统手艺需正式命名并以合理逻辑嵌入 Myco"。
bootstrap craft 本身豁免 `craft_protocol_version` 字段（meta-dogfood 递归防御，
symmetric with §8.7 upstream bootstrap exemption）。

### Added

**`docs/craft_protocol.md`（新，CONTRACT 级文档）**
- §1 协议定义：W3 传统手艺的正式名称锁定为 **Craft Protocol v1**（中文正式名保留"传统手艺"）。
- §2 Canonical form：文件名 pattern `^[a-z][a-z0-9]*(_[a-z0-9]+){1,}_craft_\d{4}-\d{2}-\d{2}(_[0-9a-f]{4})?\.md$`；
  frontmatter schema（type/status/created/target_confidence/current_confidence/rounds/craft_protocol_version/decision_class）；
  状态枚举 DRAFT/ACTIVE/COMPILED/SUPERSEDED/LOCAL。
- §3 调用触发器：kernel contract 变更 / 实例架构决策 / 置信度 < 0.80 / 外部 stakeholder-visible claim / 在线调研冲突。
- §4 置信度阶梯（taxonomic）：`kernel_contract: 0.90` / `instance_contract: 0.85` / `exploration: 0.75`。
- §5 与 notes/ / log.md / _canon.yaml / Upstream Protocol / L9 / L10 / L13 的集成矩阵。
- §6 Grandfather 规则：无 `craft_protocol_version` 字段的既有 craft 文件自动豁免 L13 strict 检查。
- §7 已知局限：self-reported 置信度不可验 / body 结构不 lint / bootstrap 文件豁免。
- §8 反向废弃标准：dead lint / dead mechanism / better replacement —— 防止"lint 只增不减"反模式。

**`_canon.yaml → system.craft_protocol`（新 schema block）**
- 含 dir / filename_pattern / required_frontmatter / valid_statuses / min_rounds / confidence_targets_by_class / stale_active_threshold_days / grandfather_rule。
- `upstream_channels.class_z` 新增 `docs/craft_protocol.md` —— 该文件变更需走 Upstream Protocol Review-required 通道。
- `contract_version: "v1.2.0" → "v1.3.0"`。

**L13 Craft Protocol Schema（新 lint 维度，13 → 14 维）**
- 实现于 `scripts/lint_knowledge.py::lint_craft_protocol` 与 `src/myco/lint.py::lint_craft_protocol`（双源对等）。
- `src/myco/mcp_server.py` 同步注册，docstring 与 title 从 "13-Dimension" 升级为 "14-Dimension"。
- 检查项：frontmatter 必填字段 / 文件名 pattern / type=="craft" / 有效 status / rounds ≥ min_rounds / decision_class 有效 / target_confidence ≥ class floor / current_confidence ≥ target（仅 ACTIVE/COMPILED）/ stale ACTIVE >30 天 LOW 提醒。
- Grandfather：无 `craft_protocol_version` 字段直接 skip，零 migration 成本。

**`docs/agent_protocol.md §8.3` craft_reference 字段（新）**
- class_z bundle MUST 包含 `craft_reference: <path>` 指向 ACTIVE/COMPILED 的 craft 文件，
  其 `decision_class` ≥ bundle 对应阶梯；缺失则 kernel 自动拒绝，receipt reason=`missing_craft_reference`。
- class_x/class_y bundle 可选填。

**`docs/WORKFLOW.md` W3 footer**
- 指向 `docs/craft_protocol.md` 作为 machine-verifiable specification；WORKFLOW 保留 human-readable 摘要。

**`MYCO.md` + `src/myco/templates/MYCO.md`**
- 文档索引新增 `docs/craft_protocol.md [ACTIVE] [CONTRACT]`；
- 辩论列表新增 `craft_formalization_craft_2026-04-11.md [ACTIVE] [CONTRACT]`；
- 热区 Agent 行为准则新增 "🛠️ Craft Protocol (W3)" 条款；
- "9 维 lint" / "13 维 lint" 就地升级为 "14 维 lint"。

### Changed

- `docs/agent_protocol.md §8.4`："当前 v1.2.0" → "当前 v1.3.0"。
- `src/myco/templates/_canon.yaml`：`synced_contract_version: "v1.2.0" → "v1.3.0"`；
  class_z 追加 `docs/craft_protocol.md`；新增 `craft_protocol` schema block 与 kernel canon 对齐。

### Rationale

W3 传统手艺此前只在 `docs/WORKFLOW.md` 里有 5 句话的人类摘要，没有机器可验证 schema，
也没有 lint 兜底。Phase ② 的 craft 输出数量已达 20+，但缺乏统一规范导致：
(1) 文件名不一致；(2) 置信度无 floor 概念；(3) 完成后没有正式的 COMPILED/SUPERSEDED 迁移路径；
(4) kernel contract 变更与 craft 证据之间无强制绑定。

v1.3.0 通过引入 L13 lint + `craft_protocol_version` 软迁移字段一次性闭环这四个漏洞，
**不破坏** 既有 20+ grandfathered craft 文件。属于典型的"contract-as-code"向后兼容 minor bump。

### Known non-goals

- L13 **不**检查 craft 文件的正文结构 —— round 数与 attack 质量由社会透明度（eat + log）保障，非 lint 强制。
- Self-reported `current_confidence` 的真实性由未来的 Goodhart 审计机制兜底，本版本不做。
- Bootstrap craft (`craft_formalization_craft_2026-04-11.md`) 故意省略 `craft_protocol_version` 避免递归自规制。

---

## v1.2.0 — 2026-04-11 (minor)

**Author**: Claude (Myco kernel agent)
**Craft record**: `docs/primordia/upstream_protocol_craft_2026-04-11.md`
（3 轮 Claim→Attack→Research→Defense→Revise，终置信度 85%）
**Trigger**: ASCC 试运行中捕获的摩擦 note `n_20260411T013756_ca9e`
暴露了摩擦捕获触发点的 meta-level gap —— agent 自承错误的时刻没有被兜住。

### Added

**§5.1 触发点清单（新）**
- (a) 会话两端 —— session start / session end 仍为基线。
- (b) 工具不够用时刻 —— 既有触发点，重新明文化。
- (c) 🆕 **on-self-correction**（自承错误触发点）：
  当 agent 在同一 assistant turn 内承认任何形式的"我之前说的 X 是错的"类
  表述时，**必须立即** `myco_eat` 捕获"错误内容 + 上下文 + 修正动作"三元组，
  tags 必须包含 `friction-phase2` + `on-self-correction` + 错误类型 tag。
  设计依据：ASCC 项目 agent 已自行捕获此摩擦（ca9e 笔记），属于实例向内核
  的第一条上行反馈，即 Upstream Protocol 内层回灌的 bootstrap 用例。

**§8 Upstream Protocol v1.0（新，替换旧 §8 演进，旧内容并入 §9）**
- §8.0 三层代谢同心圆定位：最内层 instance→kernel（本版本落地），
  中间层 instance↔instance Commons（v1.2 Phase ③），
  最外层 世界→substrate Metabolic Inlet（v2.0）。
  本节复用既有 7 步代谢管道（发现→评估→萃取→整合→压缩→验证→淘汰）。
- §8.1 五条核心原则（mutation/selection 对齐 / 低摩擦 ≠ 零人工 /
  path-based classification 不可被 agent 自抬 / 版本锁 + Conventional Commits /
  bootstrap 不得与被引入的规则递归）。
- §8.2 三通道处置矩阵 Class X / Y / Z（Auto / inline-Confirm / Review-required）。
- §8.3 状态机：`raw → upstream-candidate → bundle-generated →
  integrated | upstream-rejected | skip`。
- §8.4 版本锁协议：`contract_version`、Conventional Commits 自动 bump、
  revoke 广播。
- §8.5 传输层：会话内授权通道 + `.myco_upstream_outbox/` / `inbox/` 目录。
- §8.6 触发词与反射规则：含 upstream-candidate 的 auto-tagging。
- §8.7 Bootstrapping：v1.2.0 **手动** 首次 bump，避免规则被用于引入规则自身。
- §8.8 验收标准：多指标。

**L12 lint — Dotfile dir hygiene（新）**
- `scripts/lint_knowledge.py` + `src/myco/lint.py` 新增第 13 维 lint 函数
  `lint_dotfile_hygiene`，检查 `.myco_upstream_outbox/` / `.myco_upstream_inbox/`
  命名约定与 30 天 GC 警告。
- `src/myco/mcp_server.py` docstring 与维度计数从 12 → 13。

**`_canon.yaml` 新字段**
- `system.contract_version: "v1.2.0"`
- `system.upstream_scan_last_run: null`
- `system.upstream_channels.{class_x, class_y, class_z}`

**Templates**
- `src/myco/templates/_canon.yaml` 新增 `synced_contract_version` 字段
  与 `upstream_channels` 默认路径列表。
- `src/myco/templates/MYCO.md` 与 `CLAUDE.md` boot sequence 新增
  "contract_version 比对" 步骤。

### Changed

- 旧 §8 "演进" 节重编号为 §9（内容未变）。

### Bootstrap notes

本次 v1.2.0 是 Upstream Protocol 本身的**手动首次落地**，不走新规则定义的
path-based channel / 状态机。理由见 §8.7：不得让规则 bootstrap 自己
（recursion hazard）。自 v1.2.1 起所有 contract change 必须走 Upstream Protocol。
