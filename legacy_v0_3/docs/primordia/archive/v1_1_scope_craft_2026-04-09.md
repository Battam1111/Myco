# 传统手艺：v1.1 Scope 定义辩论
> **Status**: ARCHIVED (compiled to formal docs)
> 日期：2026-04-09 | 类型：scope-debate | 状态：[ARCHIVED]
> 前置：v1_scope_craft_2026-04-09.md（v1.0 完成）
> 目标：确定 v1.1 的核心 CLI 命令设计——最小充分、可实际交付

---

## 背景约束

**v1.1 路线图承诺（来自 adapters/ roadmap + v1_scope_craft）：**
- `myco import --from hermes ./skills/` — 自动化 hermes.yaml 手工步骤
- `myco import --from openclaw ./MEMORY.md` — 自动化 openclaw.yaml 手工步骤
- `myco config --set key value` — 写入 _canon.yaml 配置节

**核心设计问题：** `myco import` 命令的 API 应该是什么形态？

**置信度目标：** ≥85%

---

## Round 1：`myco import` 的 API 设计——source-specific vs generic

### 主张
`myco import` 应采用 `--from <tool>` 旗标（source-specific）：
```bash
myco import --from hermes ~/.hermes/skills/
myco import --from openclaw ./MEMORY.md
```
原因：不同工具的导入逻辑完全不同——Hermes 是目录扫描，OpenClaw 是单文件解析，
每个工具的层映射也不同。用同一个通用命令会导致逻辑耦合。

### 攻击
`--from <tool>` 的问题：这实际上要求 Myco 核心代码知道所有外部工具的格式。
每增加一个工具就需要修改 `myco/import_cmd.py`。违反了"adapter 由社区贡献"的设计初衷。
如果 Obsidian 用户写了 `adapters/obsidian.yaml`，他们还要提 PR 修改核心代码才能用 CLI？

更好的设计：**adapter YAML 本身驱动 CLI**：
```bash
myco import --adapter adapters/hermes.yaml --source ~/.hermes/skills/
```
这样核心代码只需要读 adapter YAML 的 `import_steps` 并执行，
新工具只需要提交 YAML，不需要改核心代码。

### 研究/证据
查看 hermes.yaml import_steps：
1. 选 top 3-5 skills
2. 分类 procedural vs operational
3. W8 header 格式
4. 运行 lint
5. 更新 _canon.yaml
6. 写 log 条目

这些步骤有两种类型：
- **机械步骤**（可自动化）：创建文件、写 W8 header、追加 log 条目、运行 lint
- **判断步骤**（无法自动化）：选哪些 skills、分类 procedural vs operational、内容摘要

结论：`import_steps` 混合了可自动化和不可自动化的步骤。
纯自动化会导致质量下降（agent 无法判断哪些 skill 值得导入）。
纯手工又回到了 v0.x 现状。

### 辩护
**修订主张：半自动化模式（Guided Import）**

`myco import --from hermes [source_dir]` 做以下事情：
1. **自动**：扫描源目录，列出候选文件（不自动选择）
2. **交互**：展示候选列表，提示用户确认导入哪些（或全部）
3. **自动**：为确认的文件创建 wiki/ 或 docs/ 目标文件，写 W8 header stub
4. **自动**：追加 log 条目，运行 lint 验证
5. **留给 agent**：填充 stub 内容（这是语义工作，CLI 不做）

这比纯手工（7步 YAML）省力 80%，比纯自动化（质量无保证）更可靠。

`--adapter` generic 模式推迟到 v1.2：先用 source-specific 验证设计，再泛化。

**置信度：80%**（half-auto 设计合理，但 interactive 模式在 headless 环境中可能出问题）

---

## Round 2：headless 环境兼容性压力测试

### 主张
半自动化 guided import 的交互模式（列出候选 + 等待用户确认）在 CI/脚本环境中会卡住。

### 攻击（快速）
这是真实场景吗？使用 `myco import` 的场景是：
- 用户在终端手动迁移（interactive 完全正确）
- CI 自动化（谁会在 CI 里跑 import？import 是一次性迁移操作）

`myco lint` 才需要 CI 兼容。`import` 是人工操作，interactive 完全合理。

### 辩护
同意。`myco import` 是一次性迁移操作，interactive 模式是正确的设计。
非交互 override：`--all` flag（自动选择所有候选，跳过确认）留给高级用户。

**置信度：84%**

---

## Round 3：`myco config` 的范围——专用配置 vs 通用 canon 编辑

### 主张
`myco config --set key value` 应该写入 _canon.yaml 的 `[config]` 节，
用于适配器配置（MemPalace endpoint、adapter 设置等）。

### 攻击
`_canon.yaml` 是 Myco 的 Single Source of Truth——它的内容通过 lint 验证。
如果 `myco config` 可以任意写入 _canon.yaml，会不会破坏 lint 期望的结构？
例如：`myco config --set project_name "my new name"` 改了 project_name，
lint 可能期望这个值与其他地方一致，而 config 命令不知道这些约束。

更安全的设计：`myco config` 只写入 `_canon.yaml` 的 `[adapters]` 节，
不触碰 lint 验证的核心字段（project_name, version, wiki_pages 等）。

### 研究/证据
查看当前 _canon.yaml 结构：核心字段（project_name, version, description, wiki_pages）
是 lint L0/L2 验证的对象。adapters 配置节尚不存在（mempalace 设计规格中提到过）。

结论：`myco config` 应操作专用的 `[adapters]` 节，与 lint 验证字段完全隔离。
这样：配置写入安全，lint 不受影响，adapter 配置有清晰的命名空间。

语法：
```bash
myco config --set adapters.mempalace.endpoint http://localhost:8765
myco config --get adapters.mempalace.endpoint
myco config --list adapters
```

### 辩护
定案：`myco config` 只操作 `_canon.yaml` 的 `[adapters]` 节。
lint 不验证 `[adapters]` 节（这是外部配置，不是知识一致性检查范围）。
`myco config --list` 展示当前所有适配器配置（方便调试）。

**置信度：89%**

---

## 最终决议（综合置信度 87%）

### v1.1 三项充分条件

| 命令 | 设计 | 实现范围 |
|------|------|---------|
| `myco import --from hermes [dir]` | 半自动：扫描→列出→确认→创建 stub→lint | 支持 hermes（SKILL.md 格式） |
| `myco import --from openclaw [file]` | 半自动：解析→分节→列出→确认→分发到 wiki/docs→lint | 支持 MEMORY.md 格式 |
| `myco config --set/get/list adapters.*` | 全自动：读写 _canon.yaml [adapters] 节 | 通用（不绑定具体工具） |

### 不在 v1.1（推迟）
- `--adapter adapters/obsidian.yaml` generic 模式（v1.2）
- `myco ingest --backend mempalace`（v1.2，依赖 MemPalace 本地服务）
- `myco import --from cursor`（Cursor 是共存，无内容导入）
- `myco import --from gpt`（GPT 是共存，无内容导入）

### 行动项
| ID | 行动 | 文件 |
|----|------|------|
| D1 | 新增 `myco config` 命令（读写 _canon.yaml [adapters] 节） | src/myco/config_cmd.py + cli.py |
| D2 | 新增 `myco import` 命令（--from hermes 半自动化） | src/myco/import_cmd.py |
| D3 | `myco import --from openclaw` 支持（MEMORY.md 解析）| src/myco/import_cmd.py |
| D4 | _canon.yaml 模板增加 [adapters] 节注释占位 | src/myco/templates/_canon.yaml |
| D5 | adapters/hermes.yaml、openclaw.yaml：roadmap v1_0 条目改为 v1_1 实现说明 | adapters/*.yaml |
| D6 | README.md、CONTRIBUTING.md：更新命令示例 | README.md |

---

*传统手艺结束。87% 置信度 ≥ 85% 阈值，进入执行阶段。*
