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

## v1.3.0 — 2026-04-11 (minor)

**Author**: Claude (Myco kernel agent, autonomous run under user grant)
**Craft record**: `docs/current/craft_formalization_craft_2026-04-11.md`
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
**Craft record**: `docs/current/upstream_protocol_craft_2026-04-11.md`
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
