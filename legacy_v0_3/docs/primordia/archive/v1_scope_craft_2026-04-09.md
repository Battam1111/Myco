# 传统手艺：v1.0 Scope 定义辩论
> **Status**: ARCHIVED (compiled to formal docs)
> 日期：2026-04-09 | 类型：scope-debate | 状态：[ARCHIVED]
> 前置：adoption_community_craft_2026-04-09.md（任务 #3 完成）
> 目标：确定 v0.9.0 → v1.0 的最小充分条件，避免 scope creep

---

## 背景约束

**当前 v0.9.0 CLI 能力（已实现）：**
- `myco init` — 脚手架创建
- `myco migrate` — 非破坏性迁移（支持 `--entry-point CLAUDE.md`，CLAUDE.md 已在 KNOWN_PATTERNS）
- `myco lint` — 9维度一致性检查（L0-L8）
- `myco version`

**v1.0 语义承诺（来自路线图与 README）：**
- "agent-agnostic 验证 + GPT/Cursor adapter"
- adapters/mempalace.yaml 从"设计规格"升级为可执行

**置信度目标：** ≥85%（scope 定义正确）

---

## Round 1：什么使一个版本值得叫 "v1.0"？

### 主张（Claim）
v1.0 的核心语义承诺是：**Myco 不再依赖 Claude 才能工作**。
这意味着：框架文档和 WORKFLOW.md 中不得有 Claude 专属假设；
至少存在 Cursor 和 GPT 的 adapter 文档；
且"30秒采用路径"（CLAUDE.md → migrate → lint → aha moment）在代码层面真正可执行（不只是文字描述）。

### 攻击（Attack）
但 "agent-agnostic" 是一个可以无限延伸的目标。
真正的 GPT/Cursor 用户测试需要实际用户，不是写几个 adapter YAML 就能声称"验证"。
写 cursor.yaml 是协议文档，不是代码验证。
把 v1.0 绑定到"验证"会让 v1.0 永远无法发布。

另外，"migrate → lint → aha moment" 在 v0.9.0 已经能手动实现：
`myco migrate ./project && myco lint --project-dir ./project`
这是两条命令，不是真正需要 CLI 变更的场景。

### 研究/证据
查看 migrate.py：`--entry-point CLAUDE.md` 已支持，CLAUDE.md 在 KNOWN_PATTERNS 中有正确映射。
当前 migrate 流程：扫描 → 创建 scaffold → 写 migration_report.md → 打印建议。
migration_report.md 的 "Next Steps" 包含 "Run `myco lint` after a few sessions"——不是立即，是"几次会话后"。
这与"aha moment"设计背道而驰：aha moment 的定义是**迁移完成后立即看到第一个不一致**，不是"有空再跑"。

### 辩护（Defense）
修订主张：v1.0 的充分条件是**三件可量化的事**，不是模糊的"验证"：

**条件 A：** `myco migrate --entry-point CLAUDE.md` 自动执行 lint 并展示第一批结果
（即迁移完成后自动调用 lint，不需要用户再手动输入第二条命令）
实现成本：~20行代码，在 migrate.py 末尾调用 `run_lint`

**条件 B：** `adapters/cursor.yaml` + `adapters/gpt.yaml` 存在
（agent-agnostic 的最低证明：协议文档覆盖两个主流 non-Claude 系统）
实现成本：各约 300 行 YAML，1-2小时

**条件 C：** WORKFLOW.md + architecture.md + README 中无 Claude 专属假设
（framework 文档去平台化：任何 agent 读 WORKFLOW.md 都能遵守 W1-W12）
实现成本：扫描确认，可能需要小量文字调整

**不在 v1.0：** `myco config`、`myco ingest`、MemPalace CLI、真实用户测试（这些是 v1.1+）

**置信度：75%**（还需压力测试"auto-lint"设计）

---

## Round 2：migrate 自动 lint 的设计压力测试

### 主张
条件 A（migrate 完成后自动 lint）是 v1.0 最高价值改动。
具体实现：migrate 末尾追加一段 "Running lint on migrated project..." 并调用 `run_lint`。

### 攻击
自动 lint 有一个根本问题：**新迁移的项目 lint 一定全绿**。
原因：migrate 创建的是模板文件（MYCO.md、_canon.yaml、WORKFLOW.md），这些模板文件彼此内部一致，lint 不会报错。
只有当用户**开始工作并写入新内容**后，才会出现不一致。
所以 migrate + auto-lint → 全绿 → 用户误以为 "aha moment" 是"没有问题"——正好相反。

### 研究/证据
验证：新建一个空项目，迁移后立即 lint：
```bash
myco init /tmp/test-v1 --level 2
myco lint --project-dir /tmp/test-v1
```
结果：ALL CHECKS PASSED（已知行为，模板内部一致）。

再验证：在 MYCO.md 写入一个错误的 wiki 引用后再 lint：
```bash
echo "- wiki/nonexistent.md" >> /tmp/test-v1/MYCO.md
myco lint --project-dir /tmp/test-v1
```
结果：L1 Reference Integrity FAIL — 这才是 aha moment。

结论：**aha moment 不能由 auto-lint 产生**，必须由用户实际写入内容后才能出现。

### 辩护
修订条件 A：

**不做** migrate 末尾 auto-lint（它只会产生全绿，无教育价值）。

**改做：** 优化 migration_report.md 的 "Next Steps"：
- 当前：`4. Run 'myco lint' after a few sessions`
- 改为：`3. Run 'myco lint --project-dir .' immediately — it will show zero issues on a clean scaffold. Then start working. The first time lint finds something is your "aha moment" — that's Myco working for you.`

同时在 migrate 结束时的终端输出追加：
```
🍄 Migration complete. Run 'myco lint --project-dir .' to establish your baseline.
   The first inconsistency lint catches after you start working is your aha moment.
```

这比 auto-lint 更诚实：用户理解 lint 是持续检查工具，不是一次性通过/失败测试。

**置信度：82%**（条件 A 修订后设计更诚实）

---

## Round 3：adapter YAML vs "真正 agent-agnostic" 的证明力

### 主张
条件 B（cursor.yaml + gpt.yaml）足以声称"agent-agnostic"。
YAML adapter 文档定义了使用协议，这与 Hermes adapter 的性质相同。

### 攻击
cursor.yaml 和 gpt.yaml 与 hermes.yaml 有根本区别：
- Hermes 是独立工具，有自己的文件格式（~/.hermes/skills/），adapter 描述的是如何迁移内容。
- Cursor 和 GPT 的"adapter"是什么？它们没有需要迁移的专有格式。
- Cursor 读的是项目文件（CURSOR.md 或 .cursorrules），GPT 用的是 system prompt + project files。
- 这两者的 adapter 实际上是"Myco 如何配合这个 agent 工作"的说明书，而不是内容迁移协议。

用同一个 adapter YAML schema（import_steps, layer_mapping）来写 cursor.yaml，会显得格格不入。

### 研究/证据
检查 migrate.py KNOWN_PATTERNS：CURSOR.md 已在其中（entry_point 类型）。
migrate 流程已经能正确处理 Cursor 项目：检测 CURSOR.md，创建 Myco scaffold，不破坏 Cursor config。

这意味着：**Cursor 的 adapter 不是迁移协议，而是"共存指南"**：
如何让 Cursor agent 读取 MYCO.md 结构，如何配置 .cursorrules 指向 Myco 入口点。

GPT 同理：ChatGPT 没有文件系统 agent；GPT API + Code Interpreter 才有。
GPT adapter 的价值是"如何设计 system prompt 以利用 Myco 结构"。

### 辩护
条件 B 修订：

**不用相同 YAML schema** 写 cursor.yaml 和 gpt.yaml。
这两个文件的本质是"使用指南"，使用 YAML 格式但结构不同：
- `agent_type`: cursor | gpt-4o | gemini-pro
- `integration_model`: file_aware（Cursor）vs system_prompt（GPT API）
- `setup_steps`: 如何配置 agent 读取 Myco 结构
- `coexistence_notes`: 哪些文件是 agent-specific，哪些是 Myco managed
- `workflow_compatibility`: W1-W12 哪些需要 agent 有工具调用权限

这比强套 import_steps 更诚实，也更有实际指导价值。

**置信度：87%**（schema 调整后内容将更准确）

---

## Round 4：条件 C 验证——WORKFLOW.md 和框架文档去平台化程度

### 主张
需要扫描 WORKFLOW.md、architecture.md、README.md 中的 Claude 专属假设，确认或修复。

### 攻击（快速）
这个条件有可能是"打扫卫生"式的微调，也可能发现系统性问题。
如果 W1-W12 原则中有 "Claude Code" 专属假设，那才是真正需要修复的。

### 研究/证据
快速扫描关键位置：

WORKFLOW.md W1-W12 中的 agent 引用应是 "the agent" 而非 "Claude"。
architecture.md 中的 "validated with Claude" 已经加了 v0.x 括号注释。
README.md 中有 "(v0.x validated with Claude; other agent compatibility is a v1.0 goal.)"——这行需要在 v1.0 时更新。

需要检查 WORKFLOW.md 是否有任何 "Claude" 直接引用（工具名、专有格式等）。

### 辩护
条件 C 最终定义：
1. 扫描 WORKFLOW.md：任何出现 "Claude" 的地方，区分（a）示例 = 可保留，（b）协议假设 = 需通用化
2. README.md 中的 v0.x 限制声明 → 升级为 v1.0 已验证声明
3. architecture.md validation header → 更新为"多项目 + 多 agent 入口验证"
4. pyproject.toml version: 0.9.0 → 1.0.0，classifiers Beta → Production/Stable

**置信度：89%**

---

## 最终决议（综合置信度 89%）

### v1.0 三项充分条件（最小 MVP）

| 条件 | 描述 | 实现难度 |
|------|------|---------|
| **A** | `myco migrate` 终端输出 + migration_report.md Next Steps 优化：诚实定义 lint 为持续工具，明确 aha moment 时机 | ~30行代码 |
| **B** | `adapters/cursor.yaml` + `adapters/gpt.yaml`：使用"共存指南"schema（agent_type, setup_steps, coexistence_notes），非迁移协议格式 | ~600行YAML |
| **C** | WORKFLOW.md 扫描去 Claude 专属化 + README v0.x 声明升级 + pyproject.toml 版本号 0.9.0 → 1.0.0 | 扫描+小量文字 |

### 不在 v1.0（推迟）
- `myco config` 命令（v1.1）
- `myco ingest` 命令（v1.1）
- MemPalace CLI 集成（v1.1，当前保持 design spec 状态）
- 真实用户 A/B 测试（持续进行，非 release gate）

### 行动项
| ID | 行动 | 文件 |
|----|------|------|
| C1 | migrate.py：优化结尾输出 + migration_report.md Next Steps 文字 | src/myco/migrate.py |
| C2 | 创建 adapters/cursor.yaml（Cursor agent 共存指南） | adapters/cursor.yaml |
| C3 | 创建 adapters/gpt.yaml（GPT API system_prompt 集成指南） | adapters/gpt.yaml |
| C4 | 扫描 + 修复 WORKFLOW.md Claude 专属假设 | docs/WORKFLOW.md |
| C5 | README.md：v0.x 限制声明 → v1.0 已验证声明；adapters/ 链接 | README.md |
| C6 | pyproject.toml：0.9.0 → 1.0.0；Beta → Production/Stable | pyproject.toml |
| C7 | adapters/README.md：更新 adapter 列表（cursor + gpt 条目） | adapters/README.md |

---

*传统手艺结束。89% 置信度 ≥ 85% 阈值，进入执行阶段。*
