# Open Problems（未解难题登记册）

> **类型**：持续维护的诚实清单（living registry），不是 craft，不是决策，不是承诺。
> **状态**：ACTIVE
> **更新频率**：每当新的结构性 blind spot 被发现（typically 伴随 craft 或 vision recovery）。
> **上次审计**：2026-04-12（Wave A2+ codebase audit — 全部 8 条逐一对照代码验证）。
> **相关**：`docs/primordia/vision_recovery_craft_2026-04-10.md` §4 "盲点列表"、
> `docs/theory.md`、`docs/agent_protocol.md §8` Upstream Protocol、
> [`docs/contract_changelog.md`](contract_changelog.md)（版本线 v0.27–v0.45 覆盖大量 partial closes）、
> [`_canon.yaml`](../_canon.yaml) `system.inlet_triggers` / `system.notes_schema`。

---

## 0. 为什么需要这份文档

Myco 的一条诚实原则是：**不把 roadmap 写成已实现**，反过来也成立——
**不把已知的结构性未解问题掩盖成"未来 feature"**。Feature 是已经知道怎么做、
只是没做的；open problem 是**连"该怎么做"都还没想清楚**。混淆这两者会把基质变成
自欺缓存，违反 Perpetual Evolution 第一原则。

这份文档就是把 open problem 与 feature backlog 显式分开的载体。读者——包括未来的
Claude 自己——看到某项出现在这里时应当理解：这**不是**被 deprioritize 的功能，
而是**尚未收敛到可辩论阶段的根本盲点**。

登记标准：某个问题同时满足

1. 已被 craft 或 vision recovery 识别并引用过至少一次；
2. 影响基质的**结构性**行为（不是局部 bug）；
3. 当前没有清晰的第一性原理解法，即使是实验性设计也会撞墙；
4. 删除或绕开它会动摇某条**身份锚点**。

不在此登记册的其他待办项一律走 MYCO.md 任务队列或 GitHub issue。

---

## 1. Metabolic Inlet — 冷启动

**身份锚点关联**：代谢入口是外向消化系统的 v2.0 原语（MYCO.md §身份锚点 3）。
没有它，基质只是内向缓存而非代谢系统。

**Wave 35 status update（2026-04-12）**：scaffold 原语已落地（`myco inlet`，contract v0.27.0，
[`docs/primordia/inlet_mvp_craft_2026-04-12.md`](primordia/inlet_mvp_craft_2026-04-12.md)，
[`docs/primordia/metabolic_inlet_design_craft_2026-04-12.md`](primordia/metabolic_inlet_design_craft_2026-04-12.md)，
5 seed tests in `tests/unit/test_inlet.py`），但本节描述的**冷启动决策本身**
仍然 open。verb 现在能 ingest 任何 file 或 agent-fetched URL，但 "新 instance 第一次启动时该 inlet
什么内容" 仍然由 operator 决定，不由 substrate 决定。Wave 34 §2.4 显式 defer 这个问题给 operator。

**Wave 54 addendum（2026-04-12, contract v0.41.0）**：`cold_start` hunger signal 已落地
（`src/myco/notes.py` Organ 2）——当 substrate note count < `cold_start_threshold`
（default 5）且无 inlet 历史时触发，建议 `myco inlet` 或 `myco_discover` 引导。
这是冷启动的**检测**（能发现冷启动状态），但不是冷启动的**解决**（不知道该 inlet 什么）。
本节继续保留为 open problem 直到出现第一条完全自主、无 operator seed 的上行案例。

**问题**：Inlet 的核心触发信号是 `myco hunger` 累积的结构性缺口（agent 在
wiki/canon/log 里找不到答案的频次）。但是——

- 一个**全新的 instance 没有 friction 历史**，hunger 初始为空。
- 没有初始 hunger → 没有 inlet 触发 → 没有外部摄取 → agent 只能用既有知识解决问题 →
  不会产生 hunger → 永远冷启动失败。
- "用户审批种子源"（v2.0 bootstrap 约束）只是 defer 了问题：用户怎么知道该种哪些源？

**已研究过的不完美路径**：
- **Hyperagents**：每个 agent 带"初始技能库"，冷启动用预置 skill。违反 Bitter Lesson
  立场（机制必须从第一性原理浮现，不能手工设计技能）。
- **Voyager**：用 LLM 自己生成好奇心目标，不需要 friction 种子。但好奇心本身需要一个
  prior，那个 prior 又从哪来？递归落到 training data，等价于参数进化——违反
  身份锚点 2（非参数进化）。
- **Survey of self-evolving agents (2025)**：明确承认 "proactive knowledge
  acquisition from the environment" **无现有实现**。

**当前立场**：承认问题存在，v1.x 期间不解决。Wave 35 落地了**摄取机制**但没解决**摄取决策**。
v2.0 设计辩论时可能需要引入 "seed knowledge manifest" 作为新原语——但这本身会成为下一个
open problem（谁维护 manifest？manifest 怎么演化？）。

**出口条件**：出现第一条**完全自主、无参数改动、无人类 seed 的**上行知识
摄取真实案例 → 从本文件移除。

---

## 2. Metabolic Inlet — 触发信号的可操作化

**身份锚点关联**：非参数进化（#2）+ 代谢管道七步含淘汰（#3）。

**Wave 35 status update（2026-04-12）**：scaffold 原语已落地，但 "何时触发 inlet" 的信号定义
**没有变化**。Wave 34 §2.4 D5 把这个问题 defer 给 operator-as-daemon 模式（agent 周期性
检查 hunger，决定是否调用 inlet）。Wave 36+ 候选之一：把 hunger 加上
`inlet_ripe` advisory signal。

**Wave 49 status update（2026-04-12, contract v0.38.0）**：**`inlet_ripe` hunger signal 已落地。**
[`docs/primordia/proactive_discovery_craft_2026-04-12.md`](primordia/proactive_discovery_craft_2026-04-12.md)
+ `src/myco/notes.py::detect_inlet_trigger()` 实现了两条触发信号：
(1) search miss 累积 >= `search_miss_threshold`（default 5，`_canon.yaml::system.inlet_triggers`）；
(2) cohort gap count >= `gap_threshold`（default 3，由 `myco.cohorts.gap_detection` 驱动）。
任一触发 → hunger 报告包含 `inlet_ripe` advisory + `myco_discover` candidates 路径。
4 个 seed tests（`tests/unit/test_inlet_trigger.py`）覆盖 no-trigger / miss-trigger / gap-trigger / disabled 场景。
Wave 50 (v0.39.0) 进一步加了 `compression_pressure` metric + metabolic-cycle skill。
Wave 54 (v0.41.0) 加了 `myco_hunger(execute=true)` auto-execute + `cold_start` signal。
**这些构成了第一条可操作的触发信号链（search miss → inlet_ripe → myco_discover → myco_inlet）。**
本节从 "完全无信号" 升级为 "有信号但无经验数据验证"。出口条件仍未满足（需要
>=10 次真实 friction->inlet->integration 审计链）。

**问题**：假设冷启动已解，"何时触发 inlet" 仍需可操作的信号定义。目前只知道
**不能用什么**：

- 不能用日历（违背 friction-driven）。
- 不能用固定 threshold（thresholds are features, not signals）。
- 不能用"用户显式请求"（那就是 eat，不是 inlet）。
- 不能让 agent 自己说"我现在好奇"（LLM calibration ECE 0.166，self-reported
  好奇心与真实 epistemic gap 相关性未知）。

**已实现但未经验验证**：
- **search miss accumulation**（Wave 49 实现）——`record_search_miss()` 追踪
  agent 搜索零结果的频次，达到 threshold 触发 `inlet_ripe`。
- **cohort gap detection**（Wave 48/49 实现）——`gap_detection()` 找出全部
  note 都是 raw/digesting 的 tag，代表未消化的知识领域。
- `myco hunger` 的 dead-knowledge D 层信号（§6，**已实现**，见 Wave 33）——
  "terminal note 冷却 >=30 天" 可能代表 "吸收完了，需要新料"。

**可能可用但完全未实现**：
- Wiki 检索 miss rate 的二阶导数（增长在加速 vs 稳定）。
- 重复 craft 到同一文件的频次（同一话题在短时间内被多次辩论 = 需要外部输入）。

**前三条已有代码和 seed tests，但没有经验数据证明它们是有效的触发信号。**

**出口条件**：至少一条触发信号被某个真实 instance 用过 ≥10 次并留下可审计的
friction→inlet→integration 链路 → 升级为 exploration 级 craft 进入正式辩论。

---

## 3. Metabolic Inlet — 对齐与隐含假设评估

**身份锚点关联**：mutation-selection 协作模型（#6）——人类做选择需要透明度。

**Wave 35 status update（2026-04-12）**：scaffold 原语已落地（[`src/myco/inlet_cmd.py`](../src/myco/inlet_cmd.py)），
且 inlet 注入的 raw note 默认 status=raw，**强制走** `myco digest` → digesting →
extracted/integrated 七步管道（[`docs/agent_protocol.md`](agent_protocol.md) §2.2）。这意味着
任何 inlet 注入的内容都会经过 agent 的 digest gate。但 digest gate 只是一个
**结构性** 强制点（确保 review 发生），它**不解决** review *能不能识别隐含假设* 这个语义
问题——本节描述的根本盲点没变。Wave 35 把对齐问题从 "scaffold 不存在" 升级为 "scaffold
存在但 alignment 仍 open"。Wave 55 (v0.42.0) 修订了身份锚点 #6（从 "人机协作" 改为
"内化的变异-选择"，[`docs/primordia/anchor_agentfirst_revision_craft_2026-04-12.md`](primordia/anchor_agentfirst_revision_craft_2026-04-12.md)），
lint + hunger = 免疫系统 = selection pressure，但这个 selection 仍然是结构性的而非语义性的。

**问题**：假设冷启动 + 触发信号都解决，Inlet 摄取的外部知识会携带**隐含假设**——
论文的前置条件、库的 API 约定、社区 convention 的未言明前提。人类作为 selection 层，
能在 Confirm/Review 时识别这些假设吗？

**已知的失败模式**：
- **Updatebot / Dependabot** 做依赖升级 bundle，人类 merge 前检查 diff——
  但 transitive 假设（"这个 lib 默认 thread-safe 了"）极难在 diff 里看见。
- **学术文献综述 RAG**：模型能提取结论，但无法可靠提取 "limitations" 段落里那些
  足以推翻结论的前置条件（citation stacking 研究 2024）。

**Myco 当前护栏**：
- `_canon.yaml` Class Z kernel contract 强绑定 craft_reference（v1.3.0），
  强迫所有上行必须附带决策过程审计链——但这只检查**决策形式**，不检查**决策内容**
  正不正确。
- Craft Protocol §7 已承认 self-reported confidence 的 Goodhart 问题。

**当前立场**：这是 Myco mutation-selection 模型的**根本假设之一**（"透明度 → 选择
压力有效"）的已知薄弱点。如果失败，进化会变成劣汰良——典型癌变。

**出口条件**：无法单方面退出。需要跨项目多实例共同积累足够案例后才能判断
mutation-selection 是否在 inlet 场景仍成立。这可能是 Myco v2 的核心实验问题。

---

## 4. Metabolic Inlet — 压缩工程（bloat 失控）

**身份锚点关联**：压缩即认知（#4）。

**Wave 35 status update（2026-04-12）**：partial unblock。Wave 30 落地了 `myco compress`
（forward compression verb），Wave 31 落地了 `myco uncompress` (reverse)，Wave 33 落地了
`myco prune` (D-layer auto-excretion)。Wave 35 inlet 的 default tag 让 `myco compress
--tag inlet` 无需 operator 记忆约定就能压缩 inlet 累积。

**Wave 50/54 status update（2026-04-12, contract v0.39–v0.41）**：**compression_pressure
metric 已落地，且 hunger auto-execute 闭环。**
- Wave 50 (v0.39.0)：`compute_compression_pressure(root)` 计算 `(raw+digesting)/max(1, extracted+integrated)`，
  超过 `pressure_threshold`（default 2.0，`_canon.yaml::system.notes_schema.compression.pressure_threshold`）
  时 hunger 报告发出 `compression_pressure` 信号 + `compress --cohort auto` action recommendation。
  4 个 seed tests（`tests/unit/test_compression_pressure.py`）。
  `skills/metabolic-cycle.md` 定义 boot ritual 标准流程。
- Wave 54 (v0.41.0)：`myco_hunger(execute=true)` auto-execute 所有 recommended actions
  （digest + compress + prune）。agent 调一次 tool，substrate 自愈。scheduled metabolic
  cycle（daily recurring task）实现了准 daemon 效果。
**这构成了 semi-continuous compression 机制**：hunger 感知压力 → action 建议 compress →
auto-execute 执行 → 每日 scheduled task 兜底。与真正的 event-driven continuous compression
daemon 仍有差距（不是 real-time 响应，依赖 agent 调用 hunger），但端到端的
inlet→compress→prune 链路通过 `myco_hunger(execute=true)` 已经连通。
本节从 "无任何 continuous compression" 升级为 "有 scheduled semi-continuous loop 但无
event-driven daemon"。出口条件仍未满足（需要在真实 inlet 流量下运行一周无 bloat 报警）。

**问题**：Inlet 的最小可行版本会让**摄取速度 >> 压缩速度**，导致 substrate
单调膨胀。目前 `compress_original.py` 是手工触发的批处理工具，没有 continuous
compression。一个真实 inlet 一周可以摄入几十份外部文档，压缩策略却还是"发现膨胀
再人工启动"，根本追不上。

**已知的约束不可放松**：
- 压缩决策必须**进化**（身份锚点 4："压缩策略本身也进化"）——不能硬编码。
- 压缩必须**保留 provenance**（身份锚点 6："透明性不可变"）——不能无损压成黑盒。
- 压缩必须是 **agent-adaptive**（32K vs 200K 策略不同）——不能 one-size-fits-all。
- 三条同时约束 → 没有现成算法能直接用。

**当前的 partial 解**（按 Wave 顺序累积）：
- L5 log.md 覆盖度检查能发现 log 失控膨胀，但只报警不自动压缩。
- `docs/primordia/` 的 COMPILED/SUPERSEDED 状态机（Craft Protocol）是手工迁移，
  理论上可以 lint 自动建议但未实现。
- Wave 30：`myco compress`（[`docs/primordia/compress_mvp_craft_2026-04-12.md`](primordia/compress_mvp_craft_2026-04-12.md)）forward compression verb。
- Wave 31：`myco uncompress`（[`docs/primordia/uncompress_mvp_craft_2026-04-12.md`](primordia/uncompress_mvp_craft_2026-04-12.md)）reverse compression。
- Wave 33：`myco prune`（[`docs/primordia/d_layer_prune_craft_2026-04-12.md`](primordia/d_layer_prune_craft_2026-04-12.md)）dead-knowledge auto-excretion。
- Wave 48：`myco cohort suggest`（[`src/myco/cohorts.py`](../src/myco/cohorts.py)）tag-based 压缩建议。
- Wave 50：`compression_pressure` metric + `skills/metabolic-cycle.md`。
- Wave 54：`myco_hunger(execute=true)` auto-execute + scheduled daily cycle。

**出口条件**：出现一个"连续压缩"的实际机制（continuous compression daemon 或
等效的 event-driven 压缩 hook），并且在至少一个真实 inlet 流量下运行一周没有
bloat 报警 → 从本文件移除。

---

## 5. Self Model C 层 — 结构性退化检测

**身份锚点关联**：四层自我模型 A/B/C/D（#5）。

**Wave 54 status update（2026-04-12, contract v0.41.0）**：**第一个可计算的 structural
decay proxy metric 已落地。** `src/myco/notes.py` `compute_hunger_report()` 内的
"Organ 3: Structural decay metric" 实现了基于 orphan count delta 的退化检测：
- 每次 hunger 运行时调用 `myco.graph.build_link_graph()` + `find_orphans()`
  计算当前 orphan 数量。
- 与 `.myco_state/decay_baseline.yaml` 中的 baseline 对比，delta > 5 时
  发出 `structural_decay` hunger signal。
- Baseline 每次 hunger 运行自动更新（带 timestamp）。
这是出口条件要求的 "至少一个可计算的结构性退化 proxy metric" 的最小实现。
**但**：(a) 没有专属 craft doc，是 Wave 54 agent-first integration 的附带产物；
(b) orphan count 只是连通性退化的一个维度，不覆盖语义退化或组织模式变迁；
(c) threshold (delta > 5) 是硬编码的，未进入 `_canon.yaml` 作为可进化参数。
依赖链：[`src/myco/graph.py`](../src/myco/graph.py) (Wave 47, v0.36.0) +
[`docs/primordia/vision_recovery_craft_2026-04-10.md`](primordia/vision_recovery_craft_2026-04-10.md) §4。
**出口条件部分满足**：proxy metric 存在但未进入 exploration 级 craft。升级为
"有最小 metric 但未正式辩论" 状态。完整出口需要 craft 决议 + `_canon.yaml` 参数化 +
至少一次真实退化检测事件。

**问题**：[`docs/primordia/vision_recovery_craft_2026-04-10.md`](primordia/vision_recovery_craft_2026-04-10.md) §4 已明说：C 层目前只能做
**事实性** 退化检测（"某个旧事实在新 eat 里被否定"），**结构性** 退化
（"某个多年稳定的组织模式开始瓦解"）没有 metric 定义。

**为什么不能忽略**：结构性退化 = substrate 癌变的主要入口。事实性退化
L2 stale pattern scan 已经兜底，真正危险的是"基质的组织方式正在劣化但每条
local edit 都合法"。

**已知困难**：
- 没有 ground truth——"好的组织方式" 本身会进化。
- 无法用 diff 检测（局部变化都合规）。
- 无法用 lint 检测（lint 是结构检查，不是**趋势** 检查）。
- LLM self-critique 有已知的 over-confident bias。

**当前的 partial solution（Wave 47/54）**：
- [`src/myco/graph.py`](../src/myco/graph.py) 提供 link graph + orphan detection + cluster analysis。
- `compute_hunger_report()` Organ 3 用 orphan delta 检测连通性退化。
- lint 23 维覆盖静态 invariant，craft protocol 覆盖决策形式。
- **仍然没有覆盖**：语义一致性退化、组织模式时间演化趋势、知识密度下降。

**出口条件**：~~至少一个可计算的结构性退化 proxy metric 被提议并进入 exploration 级 craft。~~
**部分满足**（orphan delta metric 已落地，但未正式 craft）。剩余条件：
(a) orphan delta threshold 进入 `_canon.yaml` 成为可进化参数；
(b) 至少一个非连通性维度的 structural metric 被提议（e.g. wiki in-degree entropy,
    canon referential depth, or semantic coherence score）；
(c) 第一次真实退化检测事件被 log.md 记录 → 完全关闭。

---

## 6. Self Model D 层 — 死知识追踪（未实现）

**身份锚点关联**：四层自我模型（#5）—— "D 效能层：死知识追踪"。

**问题**：vision_recovery_craft 明确列出 D 层未实现。"死知识" 定义：
**进入 substrate 超过 N 天、从未被 view/cited/eaten 的 note 或 wiki 页面**。
这是压缩决策的首要输入，也是 inlet 触发信号的候选（§2）。

**为什么是 open problem 而不是 feature**：
- "死"的判定需要时间窗——太短会误杀慢燃 note，太长发现太晚。
- 时间窗应当随 substrate 年龄进化（身份锚点 4）——不能硬编码。
- view 事件目前没有审计日志（`myco view` 是只读命令，不记录谁在什么上下文下读了啥）。
- 没有 view audit → 没法算 dead—这是一条未铺的基础设施。

**最小可行种子** — ✅ **已落地于 contract v1.4.0**
（craft 决议：[`docs/primordia/dead_knowledge_seed_craft_2026-04-11.md`](primordia/dead_knowledge_seed_craft_2026-04-11.md)，
kernel_contract 级，置信度 0.91，L13 强制）：
- `myco view <id>` 在单 note 模式下通过 `record_view()` 写入 frontmatter 的
  `view_count` + `last_viewed_at`（read/write 分离：**不**触碰 `last_touched`）。
- `myco hunger` 新增 `dead_knowledge` 信号 + 专用显示块，5 条件联合判定：
  (1) status ∈ terminal_statuses (extracted/integrated)
  (2) created ≥ dead_threshold_days 宽限期（避免误杀新生 note）
  (3) last_touched 冷却 ≥ dead_threshold_days
  (4) last_viewed_at 为空或冷却 ≥ dead_threshold_days
  (5) view_count < 2
- 默认阈值 30 天，由 `_canon.yaml::notes_schema.dead_knowledge_threshold_days`
  SSoT 控制，instance 可覆盖。
- `notes_schema.optional_fields: [view_count, last_viewed_at]` 被 L10 识别但不强制
  （grandfather 兼容旧 note）。

**这只是最小种子，不是 D 层完整实现**——完整 D 层仍需：
view 审计日志（谁在什么上下文下读了啥）、cross-reference 图、
自适应阈值（随 substrate 年龄进化，身份锚点 4）、excretion 自动化路径。

**Wave 33/54 status update（2026-04-12, contract v0.29–v0.41）**：**`myco prune` 落地，
且 `myco_hunger(execute=true)` 闭环。** D 层种子实现已扩展为可执行的 auto-excretion 管道：
- Wave 33 (v0.29.0)：`myco prune` verb 落地（[`docs/primordia/d_layer_prune_craft_2026-04-12.md`](primordia/d_layer_prune_craft_2026-04-12.md)），
  `src/myco/notes.py::auto_excrete_dead_knowledge()` 实现 dry-run + opt-in `--apply`。
  `src/myco/notes_cmd.py::run_prune()` CLI 入口。
- Wave 34 (v0.34.0)：`myco_prune` MCP tool 落地，agent 可直接调用。
- Wave 46 (v0.35.0)：hunger action 中 `dead_notes` → `prune(apply=True)` 作为
  structured recommendation。
- Wave 54 (v0.41.0)：`myco_hunger(execute=true)` auto-execute prune。
  scheduled metabolic cycle 每日执行 hunger → 自动 prune dead notes。
**这意味着 `dead_knowledge` 信号驱动的 auto-excretion 已经端到端连通。**
出口条件 "第一个真实的 excretion 决策基于 `dead_knowledge` 信号" 在技术上已具备
（hunger execute=true 在 prune 候选存在时会自动执行），但尚无证据表明在真实
instance 中已实际触发过（substrate 年龄不足 30 天）。

**下一道出口条件**：~~第一个真实的 excretion 决策基于 `dead_knowledge` 信号
而非人工判断。~~ **技术管道已就绪**。剩余条件：substrate 运行 >=30 天后，
至少一次真实的 auto-prune 事件被 `log.md` 记录 → 升级为 instance_contract 级
craft（目标 0.85）。完整 D 层仍需：view 审计日志（谁在什么上下文下读了啥）、
cross-reference 图（已有 `myco graph`）、自适应阈值（随 substrate 年龄进化）。

---

## 7. Agent-Initiated Sensing — 心跳命令的物理限制（H-2）

**识别来源**：panorama audit note `n_20260411T231220_3fb8`（2026-04-11），
Wave 17/18/19 连续修复之后仍然剩余的结构性限制。登记为 open problem，
**不是** feature backlog 项。

**身份锚点关联**：代谢系统的感觉输入通道（MYCO.md §身份锚点 3
"外向消化系统的 metabolic inlet"）。

**问题**：Myco 所有反射弧——Wave 12 craft reflex、Wave 13 boot reflex、
Wave 14 session-end drift、Wave 16 upstream_scan_stale、Wave 17 boot
brief——都依赖 agent 主动调用 `myco hunger` 或 `myco lint` 作为心跳。
这两个命令是整个神经系统的感觉输入通道。一旦 agent 跳过它们（赶时间 /
忘了 / context 被截断 / continued conversation 没跑 boot ritual），
所有下游反射弧静默失效。

生物反射弧不需要意识决定运行感觉神经；Myco 的感觉输入是**轮询式**且
**agent-initiated** 的。这不是设计错误，而是 **CLI 工具宿主范式的物理
限制**：CLI 只能在被调用的瞬间执行，没有常驻进程能代替 agent 周期性
扫描。

**已尝试的缓解**（仍不是解决）：
- Wave 12: L15 craft reflex（[`docs/primordia/craft_reflex_craft_2026-04-11.md`](primordia/craft_reflex_craft_2026-04-11.md)）—— 依赖 `myco lint` 被运行。
- Wave 13: boot reflex arc（[`docs/primordia/boot_reflex_arc_craft_2026-04-11.md`](primordia/boot_reflex_arc_craft_2026-04-11.md)）—— 依赖 `myco_status` 被 MCP tool 调用。
- Wave 17: boot brief injector（[`docs/primordia/boot_brief_injector_craft_2026-04-11.md`](primordia/boot_brief_injector_craft_2026-04-11.md)）—— 把信号写进 MYCO.md 热区，把 "agent
  必须主动调用" 部分转成 "agent 被动读到"。**但前提仍然是** 上一次会话
  结束前有谁跑过 `myco hunger` 把 brief 写新。如果连续多次会话都没跑
  hunger，brief 就会过期，而 L6 date consistency lint 不会检测它（brief
  本身不在 L6 扫描范围内）。
- Wave 18: opt-in git pre-commit hook（[`docs/primordia/l15_surface_and_git_hooks_craft_2026-04-11.md`](primordia/l15_surface_and_git_hooks_craft_2026-04-11.md)）—— 覆盖了写路径的一部分，但
  `--no-verify` 仍可绕过，且跟读路径信号无关。
- Wave 54: hunger auto-execute + scheduled metabolic cycle —— 见上方 status update。

**为什么不能在 kernel 内完全解决**：

1. **没有常驻进程**：Myco 是 `pip install`-able 的 CLI 包，不是
   daemon。在 agent 侧启动后台进程需要宿主（Cowork / Claude
   Desktop / Cursor）支持 long-lived processes，属于 **hosting-side
   collaboration** 而非 kernel-side design。
2. **Cron / systemd 不在 scope**：即使用户手动配了 cron 每 N 分钟跑
   `myco hunger`，也无法把信号送达某个 active session；它只能刷新
   brief，改善不了"当前 session 是否读到 brief"的问题。
3. **MCP server 能部分接管**：如果宿主加载了 `myco.mcp_server`，那么
   `myco_status` tool 可以在每次 agent tool-call 时做一次 low-cost
   health check，把信号塞回 tool-result。但 MCP server 也是 agent
   voluntarily invoked —— agent 必须"选择" call 这个 tool。只是门槛
   更低，不是消失。
4. **Claude Agent SDK hooks** 理论上可以在 session start / tool
   execution 时强制运行一段代码，这会真正解决 H-1 / H-2，但属于
   Anthropic-侧 platform capability，不在 Myco kernel 可控范围。

**Wave 54 status update（2026-04-12, contract v0.41.0）**：**两条新缓解层落地。**
- `myco_hunger(execute=true)` 把 "agent 必须逐个调用 verb" 缩减为 "agent 调一次 hunger"。
  agent boot ritual 简化为单一 tool call，遗忘成本从 N 次调用降到 1 次。
- Scheduled metabolic cycle（daily recurring Claude Code task）实现了准 daemon：
  每日自动运行 `hunger(execute=true)` + `session index` + `lint`。这是 **hosting-side
  collaboration** 的第一个落地实例——Claude Code 的 scheduled-tasks 充当常驻进程。
防御层从四层升至六层：lint / hunger / boot brief / git hook / **hunger auto-execute** /
**scheduled metabolic cycle**。H-2 的残余风险从 "每次会话都可能遗忘" 收窄为
"scheduled task 被禁用 + agent 跳过 boot ritual" 的双失败场景。

**当前判决**：H-2 是 **accepted architectural limit of CLI hosting
paradigm**。kernel 已经把能做的防御层堆到了六层（lint / hunger /
boot brief / git hook / hunger auto-execute / scheduled metabolic cycle）；
更深的自动化必须靠宿主 platform 提供常驻执行能力。不符合 "登记标准 3"
（连该怎么做都还没想清楚）的部分已被 Wave 17/18/54 填补；剩余部分是
典型的 "想清楚了但做不了"，正属于 **open problem** 范畴。

**出口条件**：
- Anthropic 发布 Claude Agent SDK session-lifecycle hook（session
  start / every-N-tool-calls）允许注入代码 → 升级到 MCP server 自动
  触发 `compute_hunger_report` 并把 `[REFLEX HIGH]` 信号塞到下一个
  tool result 的 stderr channel；OR
- 某个宿主原生支持 "project watcher" 常驻进程模型，能以 file-system
  events 触发 kernel code → 升级为 daemon-based watchdog；OR
- 某个未来 Claude 模型展示出 "unprompted periodic sensing" 能力
  （周期性自发检查 substrate 状态），那样 H-2 在 agent 侧自动消失。
- 满足任一出口条件后，把本节迁移到 `docs/primordia/h2_resolved_YYYY-MM-DD.md`。

---

## 8. Dual Append Paths — MCP vs Shell HEREDOC（H-6）

**识别来源**：panorama audit note `n_20260411T231220_3fb8`（2026-04-11）。

**身份锚点关联**：`log.md` append-only 原则（MYCO.md §硬契约第 2 条
"不绕过工具"）的可观测性维度。

**问题**：Hard Contract 第 2 条（[`docs/agent_protocol.md`](agent_protocol.md) §1）规定 `log.md` 只能 append，可以通过
`myco_log` MCP tool（[`src/myco/mcp_server.py`](../src/myco/mcp_server.py)）**或** shell `>>` / HEREDOC 追加。两个路径的
*功能*等价（都是 append-only、不 rewrite），但 *可观测性* 不等价：

- **MCP tool call**：宿主 (Cowork / Claude Desktop) 会记录一次 tool
  invocation。未来的 Phase 2 meta-analysis 能统计"每个会话有多少
  个 log 条目通过 MCP 产生"。
- **Shell HEREDOC**：在 Bash tool 的 command 里以 `cat >> log.md
  << EOF` 方式追加，从宿主视角看只是一次 Bash invocation，没法
  区分它到底是跑脚本还是追加日志。

ASCC / Myco 的现实是：agent 跑在 sandbox 里，MCP server 不总是
可用（需要宿主注入 PATH 和启动参数），所以 shell HEREDOC 往往是
事实默认。这不是 bug —— append-only 语义仍然成立 —— 但它让
Phase 2 "有多少反思通过了神经通路 vs 绕过了神经通路" 这类统计
变得不可恢复。

**已尝试的缓解**：无。之前的 waves 都把这个归为"不是问题"因为功能
满足。panorama audit 第一次显式把它识别为**信号质量**问题而不是
功能问题。

**为什么不能在 kernel 内完全解决**：

1. **MCP 可用性由宿主决定**：Myco kernel 无法强制宿主加载
   `myco.mcp_server`。pip install 之后 MCP server 是 opt-in 的
   runtime component，宿主可能完全不知道它存在。
2. **Shell 是 last-resort fallback**：如果宿主没 MCP，agent 只剩
   Bash tool。禁用 HEREDOC append 等于禁用所有 log 写入路径，
   反而直接杀死 log 本身。
3. **L5 lint 无法反向推断**：lint 看 log.md 内容，看不出条目是哪
   条路径写进去的。除非 MCP tool 在每个条目上注入某种可识别的
   marker（例如 trailing comment 携带 `via: mcp`），否则两条路径
   在 on-disk 层面完全等价。
4. **加 marker 会污染 log**：把 `<!-- via: mcp -->` 加到每个 log
   条目会让 log.md 不再是人类友好格式，违反 MYCO.md §可读性锚点。

**当前判决**：H-6 是 **accepted observability gap**。功能等价；
信号质量损失仅在 Phase 2 meta-analytics 时才显现。kernel 不应该
通过污染 log 格式或禁用 shell 路径去换取这个观测能力。

**潜在缓解**（非阻塞，仅记录）：
- 如果未来 MCP server 启用率 > 80%，可以考虑在 MCP `myco_log`
  tool 内部向 `.myco_state/mcp_log_counter.json` 写一个独立的计数
  器（不污染 log.md 本身）。shell 路径没有这个 side effect，所以
  差额即"shell append 次数"。这是 **可恢复的** observability
  （通过两个数据源对冲），不破坏 log 格式。但目前 MCP 启用率未知，
  过早实现是投机。

**出口条件**：
- 某次 Phase 2 meta-analysis 明确需要"神经通路 vs 绕过"的比例，
  并且解决方案不污染 log.md → 升级为 instance_contract 级 craft；OR
- MCP server 普及到宿主默认加载的程度，shell HEREDOC 成为罕见
  fallback → 问题自动缩小到可以接受；OR
- 发现某个我们没想到的 low-footprint marker 方案 → 升级为 craft。

---

## 9. 登记册维护规则

- **新增**：craft 或 vision recovery 发现新的结构性盲点时 append，保持编号单调。
- **更新**：已登记问题的状态变化（出现新 non-solution、新失败模式、新 workaround）
  就地追加小节，不覆盖。
- **移除**：仅当满足该条的 "出口条件" 时，把整节迁移到
  `docs/primordia/<problem_name>_resolved_YYYY-MM-DD.md`，然后在本文件留一行 stub
  指向 resolved 文件。
- **锁定**：当某问题被判定为 "永不可解"（Goldbach 级）时标注 `[UNRESOLVABLE-BY-DESIGN]`，
  并在 `docs/theory.md` 对应理论段补充。目前无此类项。

未经 craft 或 vision recovery 的提议**不得**直接添加到本文件。这是防止 open
problem 通胀成焦虑清单的唯一护栏。

---

[Back to MYCO.md](../MYCO.md)
