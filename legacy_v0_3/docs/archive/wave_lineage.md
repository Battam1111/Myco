# Wave 谱系档案

> **状态**: ARCHIVE
> **创建**: 2026-04-14
> **目的**: 归档 Wave 1 至 Wave 58 的版本演进轨迹。活跃文档已不再使用 Wave NN 作为版本标签；本文仅作为历史血脉的查阅索引。

---

## 为什么归档

Myco 早期用 "Wave" 作为发布计量单位，每个 Wave 对应一次契约变动或结构升级。在 v0.40+ 之后，版本号（semver）与 craft doc 已能独立承载全部语义，Wave 标签反而造成叙事耦合：活跃文档描述"当前状态"时不再需要援引 Wave NN。故将 Wave 谱系聚合为本档，供需要追溯起源时使用。

**当前状态描述的首选方式**：
- 用语义版本号（v0.29.0, v0.41.0 等）。
- 用 craft doc 的 anchor 链接（`docs/primordia/xxx_craft_<date>.md`）。
- Wave 标签仅在历史 context 里保留（contract_changelog.md、primordia/archive/ 内的旧 craft）。

---

## 四个阶段

### 阶段 I · Foundation（Wave 1-10）

初始化阶段。建立 bootstrap 模板、四支柱架构、基础 lint 维度 L0-L10。

- Wave 1-5：CLAUDE.md + MYCO.md 原型，初始 WORKFLOW 原则。
- Wave 6-8：pre-release re-baseline，将 v1.x.y 下调为 v0.x.y（见 contract_changelog.md §Wave 8）。
- Wave 9-10：vision_recovery_craft 回溯 18 项被压缩丢失的愿景元素，有机体的解剖学首次显形。

对应 craft：`docs/primordia/vision_recovery_craft_2026-04-10.md`（ANCHOR）

### 阶段 II · Contract（Wave 11-25）

契约与规范阶段。硬契约 agent_protocol.md 成型，craft protocol 落地，test infrastructure seed 落地。

- Wave 11-17：agent_protocol 硬化（write surface, tool protocol, boot-end sequence），L11-L17 lint 维度补齐。
- Wave 18-23：万物互联早期底架（graph 基础设施、link backlinks）+ craft schema L13 自动执行。
- Wave 24-25：tests/ 测试基础设施落地（v0.24.0），conftest.py 的 `_isolate_myco_project` 首次让契约可回归测试。

对应 craft：`docs/primordia/biomimetic_nomenclature_craft_2026-04-12.md`、`docs/primordia/digestive_architecture_craft_2026-04-10.md`

### 阶段 III · Metabolism（Wave 26-45）

代谢与消化阶段。七步管道完整化、hunger 信号族扩张、compression primitive 成型。

- Wave 26-29：biomimetic rename（lint→immune，metabolism→代谢），L18-L22 lint 维度。
- Wave 30-42：hunger 信号族扩张到 17+ 种，structural cleanup（删除 alias），compression_pressure 度量。
- Wave 43-45：6 个新 MCP 工具（forage / evaluate / extract / integrate / absorb / prune），Agent Surface 完整。

对应 craft：`docs/primordia/compression_primitive_craft_2026-04-12.md`、`docs/primordia/forage_substrate_craft_2026-04-11.md`

### 阶段 IV · Structural Intelligence（Wave 46-58）

结构智能阶段。万物互联成为一级概念，mutation-selection 内化，identity 锚点完全重写。

- Wave 46-48：signal-to-action wiring（hunger.actions 自动执行），link graph + 语义 cohort intelligence。
- Wave 49-52：inlet trigger policy、continuous compression、session memory FTS5 索引。
- Wave 53-55：scheduled metabolic cycle、Agent-First integration、mutation-selection 内化（`anchor_agentfirst_revision_craft_2026-04-12.md`）。
- Wave 56-58：8 身份锚点完全重写，tool trigger contract（18/18 MCP tools），identity_definitive_craft 命名共生认知有机体。

对应 craft：`docs/primordia/anchor_agentfirst_revision_craft_2026-04-12.md`、`docs/primordia/myco_identity_definitive_craft_2026-04-12.md`

### 阶段 V（现在） · Substrate Upgrade（v0.45+）

Wave 序号停止使用。2026-04-14 的基质身份升级（`docs/primordia/substrate_identity_upgrade_craft_2026-04-14.md`）将"infrastructure / 基础设施"替换为"substrate / 基质"，并引入 autopoiesis / selective permeability / temporal organization / co-evolutionary niche 四项结构特征。此后所有版本以 semver 为唯一计量。

---

## 完整 Wave 列表查询

- `docs/contract_changelog.md`：每个 Wave 的完整 changelog（作者、动机、changes、verification）。
- `docs/primordia/archive/`：被超越的早期 craft doc，按 Wave 归档。
- `src/myco/immune.py` 与 `tests/`：代码中保留的 Wave 注释仅作历史出处记录，不作为当前版本计量。

<!-- nutrient-from: n_20260414T134657_bc5a -->

**Back to** [MYCO.md](../../MYCO.md)
