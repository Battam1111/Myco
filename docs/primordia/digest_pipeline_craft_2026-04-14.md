---
type: craft
status: active
wave: "W-digest"
exploration: 0.90
topic: "Digest Pipeline — from label-flipping to real nutrient absorption"
created: 2026-04-14
---

# Digest Pipeline Craft — 从标签切换到真正的营养吸收

## 0. 问题陈述

`myco_digest` 当前的全部功能：
1. 修改 frontmatter `status` 字段（raw → digesting → extracted/integrated/excreted）
2. `digest_count` +1
3. `transition_log` 追加一条记录
4. 默认模式打印 4 个反思提示（无人回答，无人验证）

**完全没做的事**：
- 没有从 note 中提取核心营养物质（nutrient）
- 没有将 nutrient 送入组织（wiki 或 MYCO.md）
- 没有验证 "extracted" 状态的 note 真的有营养被吸收到了某个组织
- 没有建立 note → 组织 的代谢溯源链接

agent_protocol.md 的 write surface 表里写了 `myco_extract`（待实现）和 `myco_integrate`（待实现），
但这两个工具**从未被创建**。结果：agent 可以无阻碍地 `digest --to extracted` 跳过所有实质工作，
只换个标签。这违反了 Myco 的核心隐喻——"消化"不是改标签，是把营养（知识）从食物（note）
转移到身体（wiki/docs/MYCO.md）。

## 1. 设计原则

### 1.1 Bitter Lesson 合规
真正的"消化智能"（理解内容、决定去向、写入总结）**必须由 agent 提供**，不由工具代劳。
工具的职责是：提供结构、强制门控、验证结果。

### 1.2 吸收门控（Absorption Gate）
状态转换不再免费。前进到 `extracted` 或 `integrated` 需要**吸收证明**：
- `absorption_site`：营养被送到了哪个组织（文件路径）
- `nutrient`：提取出来的核心营养物质（一句话）

### 1.3 Immune 背书
新增 L23 Absorption Verification：
- 每个 `extracted` note 必须有 `absorption_site`
- `absorption_site` 指向的组织必须存在
- 目标组织必须包含对该 note 的代谢溯源标记（`<!-- nutrient-from: n_xxx -->`）

### 1.4 零摩擦排泄
`excreted` 仍然只需要 `excrete_reason`，不需要吸收证明——排泄不需要证明营养去了哪。

## 2. 新的 Digest 工作流（四阶段）

```
Phase 1: DIGEST — digest(note_id) → 返回 note 内容 + 分析模板
                  agent 阅读内容，识别核心 nutrient，决定 absorption site
                  status: raw → digesting

Phase 2: ABSORB — agent 自行将 nutrient 写入 absorption site (wiki/docs/MYCO.md)
                  在目标组织中添加 <!-- nutrient-from: n_xxx --> 代谢溯源标记
                  这一步完全由 agent 执行，不经由 myco 工具

Phase 3: SEAL   — digest(note_id, to_status="extracted",
                         absorption_site="wiki/xxx.md",
                         nutrient="核心 insight 一句话")
                  工具验证：absorption site 存在 + 包含 nutrient-from 标记
                  验证通过 → status: digesting → extracted
                  验证失败 → 返回错误，不转换状态

Phase 4: VERIFY — immune L23 定期扫描所有 extracted/integrated notes
                  检测"幽灵消化"（status 改了但没有实际吸收）
```

## 3. API 变更

### 3.1 myco_digest MCP tool — 新参数

```python
async def myco_digest(
    note_id: Optional[str] = None,
    to_status: Optional[str] = None,
    excrete_reason: Optional[str] = None,
    absorption_site: Optional[str] = None,   # NEW: 吸收位点（相对路径）
    nutrient: Optional[str] = None,           # NEW: 营养物质（一句话）
    project_dir: Optional[str] = None,
) -> str:
```

**门控逻辑**：
- `to_status in ("extracted", "integrated")` 时，`absorption_site` 和 `nutrient` **必填**
- 工具验证 `absorption_site` 文件存在
- 工具验证文件中包含 `<!-- nutrient-from: {note_id} -->` 标记
- 验证通过：写入 frontmatter（absorption_site, nutrient, absorbed_at），转换状态
- 验证失败：返回 error JSON，不修改任何文件

### 3.2 CLI — 新 flags

```bash
myco digest <note_id> --to extracted \
    --site wiki/algorithms.md \
    --nutrient "ASCC actor 没有 forward()，用 select_action()"
```

### 3.3 Frontmatter 新增字段

```yaml
absorption_site: wiki/algorithms.md
nutrient: "ASCC actor API: select_action() not forward()"
absorbed_at: 2026-04-14T03:30:00+00:00
```

### 3.4 代谢溯源标记格式（写在 absorption site 里）

```markdown
<!-- nutrient-from: n_20260414T032020_53f0 -->
```

HTML 注释，不影响渲染，但 immune L23 可以检测。

## 4. Immune L23: Absorption Verification

```
对每个 status in (extracted, integrated) 的 note：
  1. frontmatter 必须包含 absorption_site（非空字符串）
  2. absorption_site 指向的组织必须存在（相对于 project root）
  3. 目标组织必须包含 <!-- nutrient-from: {note_id} --> 标记
  4. nutrient 必须非空

违规 → WARNING（不是 CRITICAL，因为历史 notes 需要迁移时间）
```

## 5. 历史兼容

已有的 extracted/integrated notes 没有 absorption_site 字段。处理方式：
- L23 首次运行时报 WARNING，不 CRITICAL
- `myco hunger` 新增 `phantom_digestion` signal：检测到无吸收证明的 extracted notes
- Agent 可以补填：`digest <id> --site <path> --nutrient <text>`（不改 status，只补字段）

## 6. 反思提示更新

旧版 4 个泛泛提示 → 新版 3 个结构化提示：

```python
_DIGEST_PROMPTS = [
    "What is the ONE core nutrient (claim/insight) in this note?",
    "Which tissue (file) should absorb this nutrient? (wiki/*.md / docs/*.md / MYCO.md)",
    "Write the nutrient there with <!-- nutrient-from: NOTE_ID --> marker, then seal.",
]
```
