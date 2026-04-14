---
类型: craft
状态: ARCHIVED
创建: 2026-04-11
目标置信度: 0.90
当前置信度: 0.91
轮次: 2
type: craft
status: ARCHIVED
created: 2026-04-11
target_confidence: 0.90
current_confidence: 0.91
rounds: 2
craft_protocol_version: 1
decision_class: kernel_contract
---

# Dead-Knowledge Seed — Self-Model D 层最小可行种子

## Context

`docs/open_problems.md §6` 明说 Self-Model D 层（死知识追踪）未实现，且列出
了 minimum viable seed：`myco view` 写 view audit → `myco hunger` 暴露
dead_knowledge。本 craft 决定该 seed 的精确形状，**以 kernel_contract 级别
绑定**到 canon + notes engine，从而：

1. 为 D 层提供第一条可观测的真实信号；
2. 为未来的压缩工程（§4）提供可消费的输入；
3. 保持 100% 向后兼容（既有 notes 无新字段照常工作）。

触发符合 Craft Protocol §3：kernel contract 变更（`_canon.yaml` + 
`src/myco/notes.py` 属 class_z）。

---

## Round 1 — Claim

为 notes frontmatter 添加两个可选字段：

- `view_count: int`（默认 0）
- `last_viewed_at: str | null`（ISO 格式，默认 null）

当 `myco view <id>` **单条 note 模式** 成功 render body 后，增加 view_count
并更新 last_viewed_at。**列表模式不触发**（只读 frontmatter 不读 body 不算
真实 attended view）。

`myco hunger` 新增 `dead_knowledge` 信号，条件：

- status ∈ {extracted, integrated}（terminal 状态，raw/digesting 预期变化中，
  excreted 已经 gone）
- `last_touched` ≥ dead_threshold_days 天前
- `last_viewed_at` 为 null **或** ≥ dead_threshold_days 天前
- `view_count < 2`

默认 dead_threshold_days = 30，可经 `_canon.yaml → notes_schema.dead_knowledge_threshold_days` 覆盖。

### Attacks (Round 1)

- **A1**: `myco view` 一直是 "read-only 镜头"，这次变成写命令，违反用户的心智模型。
  "读不产生副作用" 是一条 load-bearing 不变量。

- **A2**: 30 天阈值硬编码在 code 里违反身份锚点 4（压缩策略必须进化）。
  这会导致 "Threshold 不能随 substrate 年龄/频率自适应" 的同样根本性问题。

- **A3**: 列表模式 `myco view --limit 100` 会读取 frontmatter。如果这也触发 view_count++，
  运行一次就把 100 条 note 从 "死" 复活成 "活"，让 signal 完全失灵。

- **A4**: "新 eat 的 note" 会立刻被标记为死吗？created 时间很近 + 从未 view + 
  last_touched = created → 按规则会在 created + 30 天后立刻进入死列表。但它其实只是
  "新生未读"，不等于 "死"。

- **A5**: dead_knowledge 信号只有在 **有压缩/excretion 工具可以消费它** 时才有意义。
  否则就是纯 noise——用户看到 "30 条死 note"，什么都做不了，只会焦虑。open_problems §4 
  明说 continuous compression 还没有。

- **A6**: `last_viewed_at` 可以被 `update_note` 绕过直接写入，用户或 agent 可以
  "给死 note 续命" 从而骗过 signal。Goodhart risk。

- **A7**: `notes.py::VALID_SOURCES` 里有 `import`/`bootstrap` 类 source，这些 note 的
  created 时间可能反映文件被扫描的时间，不是"真实进入认知循环"的时间。bootstrap note
  在首日就会进入死列表。

- **A8**: 30 天对小体量 substrate（< 100 notes）过短——没人会那么频繁 re-view 整个库。
  30 天对大体量（> 5000 notes）过长——真正 dead 的早就明显了。threshold 选 30 是零依据。

### Research

- **Unix atime**：文件系统 access time 历史上也因性能 + 语义问题被大量系统默认关掉
  (relatime)。教训：**read-triggered write** 必须是 opt-in 或至少是轻量级 + 合理语义。
  但 Myco 不是文件系统，`myco view` 已经是显式命令，不是被动 syscall，可以接受显式副作用。

- **Anki spaced repetition**：review events 写回 card metadata 是核心设计，用户完全接受
  "打开卡片 = 记录一次 review"。关键是单条 open 才触发，不是列表浏览。这 vindicate 了
  "list mode 不触发，detail mode 触发" 的区分。

- **IDE "recently opened files"**：只记录明确 open 的文件，不记录目录 listing。Pattern 对齐。

- **Garbage collection literature**：mark-and-sweep 系统用 reachability 不用时间阈值。
  但 substrate 的 "reachability" 是语义性的，不是引用性的——一条 note 没有显式指向它的引用
  也可能因为语义相关性被未来的 eat 激活。这让 GC 类方案不直接适用。

- **OS page cache LRU**：least-recently-used 是经验上最稳定的 eviction 策略之一。
  view_count + last_viewed_at 本质上是 LFU + LRU 的组合——这有文献支撑。

### Defense (Round 1)

- **A1 → accept partially**: 把语义明文化为 "view = attended inspection"（用户显式
  指定 id + 内容被 render），而不是 "browse"。列表模式只读 frontmatter，不算 view。
  文档 + help text 明写这一点。Anki / IDE pattern 已验证。

- **A2 → restructure**: threshold **不写死在 code**，从 canon 读取
  `notes_schema.dead_knowledge_threshold_days`（默认 30）。未来可以：(i) 由 agent 根据
  总 note 数 / substrate 年龄动态调整 canon 值；(ii) per-status 不同阈值；
  (iii) 自适应公式。本 seed 只提供最小可行钩子，**不** 声称解决了身份锚点 4。

- **A3 → accept & design out**: 明确 "只有 `myco view <id>` single-note 模式且成功 render body 才触发 view_count++"。
  list 模式、JSON 模式全部不触发。通过 run_view 的 control flow 强制。

- **A4 → add guard**: dead 判定必须 `now - created ≥ dead_threshold_days`。新 note
  在 30 天内天然豁免。等价于 "grace period"。

- **A5 → reframe**: dead_knowledge 信号**首要**消费者是**手工 excretion 决策**
  （用户/agent 读 `myco hunger` 时决定哪些 note 需要 `myco eat ... --status excreted`）
  而不是自动压缩。signal 先行，压缩 daemon 后上（Phase ③ 或 v2）。这和 `myco hunger` 
  既有 `raw_backlog` / `no_excretion` 信号同源——既有信号也都是"人类看 + 手动响应"。

- **A6 → accept explicitly as limitation**: Goodhart 压力存在。defense = 社会透明度：
  `update_note` 是内部 API，只有在 agent 明确调 `myco eat --mutate` 场景下才应该触碰
  last_viewed_at。如果 agent 作弊，log.md / craft 记录会暴露。同 Craft Protocol §7 姿态。

- **A7 → add second guard**: created 时间基线改为 `max(created, first_touched)`。
  但 first_touched 目前没记录——改用 `last_touched` 作为 fallback：只要一条 note
  **曾经被** 修改过（digest_count++ / status change / 手工 edit），说明它在某个时刻是
  "活的"，以最后活跃时间作为死判定的锚点之一。这就是 A1 讨论过的 "last_touched ≥ threshold" 条件。

- **A8 → accept & declare**: 30 是占位值。canon-configurable（A2），未来由数据驱动。
  本 craft 不声称 30 是最优值。

→ 置信度：0.82。A2、A6、A8 仍是已知弱点但已转化为显式局限而非 hidden bug。

---

## Round 2 — Refined Claim

### Changes

1. **List mode 不触发**：control flow 强制（run_view single-note path）。
2. **Threshold 从 canon 读取**：`notes_schema.dead_knowledge_threshold_days`，默认 30。
3. **Dead 判定复合条件（全部必须成立）**：
   - `status ∈ {extracted, integrated}`
   - `now - created ≥ threshold_days`（grace period）
   - `now - last_touched ≥ threshold_days`（既有变更锚点）
   - `last_viewed_at is None` OR `now - last_viewed_at ≥ threshold_days`
   - `view_count < 2`
4. **信号只输出不行动**：`myco hunger` print，没有自动 excretion。
5. **字段全部 optional**：notes.py `REQUIRED_FIELDS` 不动，只在 `serialize_note` 的
   key order 里追加，确保新生成的 note 带字段、旧 note 继续工作。
6. **canon 加 `optional_fields` 列表** 作为文档用途，L10 不检查（L10 只用
   `required_fields`）。
7. **kernel contract 从 v1.3.0 → v1.4.0**（新字段属 MINOR 向后兼容新增）。

### Attacks (Round 2)

- **R2.1**: Optional 字段在 `_canon.yaml` 里用 `optional_fields` 列表记录，但 L10 不检查——
  这个字段是 "document-only"，未来可能 drift（canon 声明了但 code 不再写）。需要
  某种 drift detection。

- **R2.2**: `myco view` 的 single-note 模式现在有 side effect，测试复杂度增加。
  单元测试需要 mock 时间 + 文件系统。

- **R2.3**: 没有 `first_touched` 字段，A7 的精确解未落地。`last_touched` 作为 
  fallback 在一种 edge case 失效：note 被 import/bootstrap 后从未被修改，created 
  == last_touched，等到 30 天就 dead——即使它可能是 high-value reference 只是没人去读。
  但这就是 D 层应该捕获的！没人读的 reference 就是定义上的 "attention-budget-waste"。
  这是 **功能而非 bug**，定义上死的 note 的确应当进信号。

### Defense (Round 2)

- **R2.1 → accept as soft limitation**: `optional_fields` 确实不 enforce，但作为
  文档仍有价值——canon 是 SSoT，声明新字段的存在给下游 reader（人类 + agent）
  提供 discovery 路径。未来 L14 或更晚的版本可以 enforce "code 写的所有 frontmatter 
  key 必须在 canon 的 required_fields ∪ optional_fields 里"。本 craft 不承担这个。

- **R2.2 → accept**: 测试复杂度是正常技术债。单元测试可以传入 `now` 参数（既有
  `compute_hunger_report` 已经用这 pattern）。`record_view` 同理。

- **R2.3 → embrace**: 这不是 bug 是 feature。从未被修改也从未被 view 的 note 定义上
  不在任何 attention cycle 里——如果它未来会被激活，那 30 天内应该至少有人 view 一次。
  30 天内都没有的 reference = `myco hunger` **应当** 提醒用户：要么 promote 到 wiki 
  让它被常驻，要么 excrete。dead_knowledge signal **正是** 这个工作。

→ 置信度：**0.91**（过 kernel_contract floor 0.90）。

---

## Conclusion

### Protocol-level changes

1. **`_canon.yaml` + `src/myco/templates/_canon.yaml`**:
   - `system.contract_version: "v1.3.0" → "v1.4.0"`
   - `synced_contract_version: "v1.3.0" → "v1.4.0"`（template）
   - `system.notes_schema.optional_fields: [view_count, last_viewed_at]`
   - `system.notes_schema.dead_knowledge_threshold_days: 30`
   - `system.notes_schema.terminal_statuses: [extracted, integrated]`（供 dead 检测使用）

2. **`src/myco/notes.py`**:
   - `serialize_note`: 把 `view_count`, `last_viewed_at` 加入 ordered key 列表（在
     REQUIRED_FIELDS 之后）。
   - 新增 `record_view(path)` 函数：读 meta，`view_count += 1`，`last_viewed_at = now_iso()`，
     写回。**不**更新 last_touched（last_touched 只给 mutation 保留）。
   - 扩展 `HungerReport`：加 `dead_notes: List[Dict]` 和 `dead_threshold_days: int`。
   - `compute_hunger_report`:
     - 签名加 `dead_threshold_days: Optional[int] = None`
     - 从 canon 默认值读取 30（若未传且 canon 可见）
     - 新增循环内 dead 检测（5 条件全中）
     - signals 里追加 `dead_knowledge: N note(s) untouched ≥Nd + view_count<2...`

3. **`src/myco/notes_cmd.py`**:
   - `run_view` single-note 分支：在 render body 之后调用 `record_view(path)`。
     list 分支不触发。
   - `run_hunger` 输出里加入 `dead_notes` 段（若 > 0）。

4. **`docs/open_problems.md §6`**:
   - 在 "最小可行种子" 小节末尾追加 "**已落地于 contract v1.4.0**" 注解 + craft 链接。
   - 出口条件不改（仍需要真实 excretion 决策基于该信号）。

5. **`docs/contract_changelog.md`**:
   - v1.4.0 条目 Added/Changed/Rationale/Known-non-goals。

6. **log.md 里程碑条目**。

### Known limitations (explicit)

- **30 天阈值非自适应**：canon-configurable 但目前无自动调整机制。未来工作。
- **Goodhart 风险**：last_viewed_at 可被绕过写入；同 Craft Protocol §7 防御姿态。
- **List mode 不记 view**：这是有意设计，不是实现 gap。
- **Dead 检测只 cover terminal statuses**：raw/digesting/excreted 豁免。
- **首次实例冷启动**：新装 Myco 在 30 天内 dead_knowledge 永远为空——正常。
- **旧 note 无字段**：grandfathered，`last_viewed_at is None` 按 dead 判定条件 A
  处理，所以 30 天后会自然进入 dead 列表（假设它们 last_touched 也 ≥ 30 天）。这是
  期望行为——旧 integrated note 如果一直没被 view，就是候选死亡名单。

### Reverse sunset

该 seed 是 Self-Model D 层的**占位实现**。当出现以下之一时，可以考虑替换：

- 出现一个 first-class 语义相似度激活机制（一条 note 被 eat 时激活所有 tag-overlap 的
  old notes 的 last_viewed_at）→ 用激活事件代替 count++。
- `myco view` 之外出现新的"真实 attended read"入口（比如 MCP tool 返回 note body 时自动
  call 等价的 record_view）→ 把 record_view 下推到 notes engine。
- dead_knowledge signal 被证明与真实 excretion 决策零相关（> 3 个月 pilot 后 signal
  触发但无 excretion 跟进）→ 推翻本 craft，开新 craft 重设计 D 层。

落地即宣告本 seed 的 exit conditions，符合 Craft Protocol §8 反向废弃标准。
