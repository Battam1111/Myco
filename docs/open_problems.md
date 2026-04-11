# Open Problems（未解难题登记册）

> **类型**：持续维护的诚实清单（living registry），不是 craft，不是决策，不是承诺。
> **状态**：ACTIVE
> **更新频率**：每当新的结构性 blind spot 被发现（typically 伴随 craft 或 vision recovery）。
> **相关**：`docs/primordia/vision_recovery_craft_2026-04-10.md` §4 "盲点列表"、
> `docs/theory.md`、`docs/agent_protocol.md §8` Upstream Protocol。

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

**当前立场**：承认问题存在，v1.x 期间不解决。v2.0 设计辩论时可能需要引入
"seed knowledge manifest" 作为新原语——但这本身会成为下一个 open problem（谁维护
manifest？manifest 怎么演化？）。

**出口条件**：出现第一条**完全自主、无参数改动、无人类 seed 的**上行知识
摄取真实案例 → 从本文件移除。

---

## 2. Metabolic Inlet — 触发信号的可操作化

**身份锚点关联**：非参数进化（#2）+ 代谢管道七步含淘汰（#3）。

**问题**：假设冷启动已解，"何时触发 inlet" 仍需可操作的信号定义。目前只知道
**不能用什么**：

- 不能用日历（违背 friction-driven）。
- 不能用固定 threshold（thresholds are features, not signals）。
- 不能用"用户显式请求"（那就是 eat，不是 inlet）。
- 不能让 agent 自己说"我现在好奇"（LLM calibration ECE 0.166，self-reported
  好奇心与真实 epistemic gap 相关性未知）。

**可能可用但未验证**：
- `myco hunger` 的 dead-knowledge D 层信号（目前尚未实现，见 §6）——
  "过去 N 天被 view 但未触发新 eat 的 note 比例" 可能代表 "吸收完了，需要新料"。
- Wiki 检索 miss rate 的二阶导数（增长在加速 vs 稳定）。
- 重复 craft 到同一文件的频次（同一话题在短时间内被多次辩论 = 需要外部输入）。

**每一条都是假设，没有一条有经验数据支持。**

**出口条件**：至少一条触发信号被某个真实 instance 用过 ≥10 次并留下可审计的
friction→inlet→integration 链路 → 升级为 exploration 级 craft 进入正式辩论。

---

## 3. Metabolic Inlet — 对齐与隐含假设评估

**身份锚点关联**：mutation-selection 协作模型（#6）——人类做选择需要透明度。

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

**问题**：Inlet 的最小可行版本会让**摄取速度 >> 压缩速度**，导致 substrate
单调膨胀。目前 `compress_original.py` 是手工触发的批处理工具，没有 continuous
compression。一个真实 inlet 一周可以摄入几十份外部文档，压缩策略却还是"发现膨胀
再人工启动"，根本追不上。

**已知的约束不可放松**：
- 压缩决策必须**进化**（身份锚点 4："压缩策略本身也进化"）——不能硬编码。
- 压缩必须**保留 provenance**（身份锚点 6："透明性不可变"）——不能无损压成黑盒。
- 压缩必须是 **agent-adaptive**（32K vs 200K 策略不同）——不能 one-size-fits-all。
- 三条同时约束 → 没有现成算法能直接用。

**当前的 partial 解**：
- L5 log.md 覆盖度检查能发现 log 失控膨胀，但只报警不自动压缩。
- `docs/primordia/` 的 COMPILED/SUPERSEDED 状态机（Craft Protocol v1.3.0）是手工迁移，
  理论上可以 lint 自动建议但未实现。
- `myco hunger` 的压缩决策自省还没写。

**出口条件**：出现一个"连续压缩"的实际机制（continuous compression daemon 或
等效的 event-driven 压缩 hook），并且在至少一个真实 inlet 流量下运行一周没有
bloat 报警 → 从本文件移除。

---

## 5. Self Model C 层 — 结构性退化检测

**身份锚点关联**：四层自我模型 A/B/C/D（#5）。

**问题**：`vision_recovery_craft_2026-04-10.md` §4 已明说：C 层目前只能做
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

**当前的 non-solution**：lint 13/14 维覆盖静态 invariant，craft protocol 覆盖
决策形式，但**没有任何一环覆盖 substrate 组织模式的时间演化**。

**出口条件**：至少一个可计算的结构性退化 proxy metric（哪怕是 wiki 页面的
average in-degree、canon 的 referential depth、log 的 semantic coherence
score 等任意一个）被提议并进入 exploration 级 craft → 从本文件升级到开放
实验状态。

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

**下一道出口条件**：第一个真实的 excretion 决策基于 `dead_knowledge` 信号
而非人工判断 → 升级为 instance_contract 级 craft（目标 0.85）。

---

## 7. 登记册维护规则

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
