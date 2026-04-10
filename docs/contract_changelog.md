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
