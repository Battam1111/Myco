# ASCC Agent Handoff Prompt — Myco v1.2 迁移指令

> **用途**：这是一个**可直接复制粘贴给 ASCC agent** 的完整任务指令，用于把
> ASCC 项目迁移到 Myco v1.2（Agent Protocol + L11 Write-Surface Lint）。
>
> **使用方法**：复制"BEGIN ASCC MIGRATION TASK"和"END ASCC MIGRATION TASK"
> 之间的全部内容（包括这两行本身），粘贴到 ASCC 会话的第一条用户消息里。
> ASCC agent 会自动按 12 步执行，并在 Step 3 停下来等你确认。
>
> **关键人机交接点**：Step 3 会让你确认 L11 baseline 抓到的"合法目录"
> vs "历史垃圾"分类。这是迁移最重要的一步，不要让 agent 跳过。
>
> **不要让 agent push**：Step 11 明确不 push，等你 review 完 commit。
>
> **相关文档**：
> - `docs/agent_protocol.md` — 硬契约本体
> - `docs/ascc_migration_v1_2.md` — 迁移包 §0-§5（本指令是它的执行脚本）
> - Myco kernel `_canon.yaml` 的 `system.write_surface` — 样例
>
> **最后更新**：2026-04-11

---

## 复制以下全部内容粘贴给 ASCC agent

=== BEGIN ASCC MIGRATION TASK: Myco v1.2 Agent Protocol 接入 ===

你现在要完成 ASCC 项目对 Myco 基质 v1.2 (Agent Protocol v1.0 + L11
Write-Surface Lint) 的迁移。这是一个硬契约接入任务，不是可选升级。
目的：让你（和未来的 ASCC agent 会话）能安全地使用 Myco 新的消化系统
（notes/ + eat/digest/view/hunger），而不会污染基质。

## 背景（30 秒读完）

Myco kernel 刚刚 landed 两个东西：
1. 消化系统 (Phase ①)：notes/ 目录 + 四个命令 eat/digest/view/hunger
2. Agent 硬契约 (Agent Protocol v1.0) + L11 Write-Surface Lint

契约的核心是"write surface 白名单 + lint 自动执行"。如果 ASCC 不接入，
你会默认用"最像人类的方式"操作 —— 建 scratch.md、手写 notes/*.md、
把想法塞进 wiki/ —— 这些都会被 L10/L11 判违约，且会污染 Phase ② 的
摩擦数据采集。

## 前置知识：你必须先读完这三份文档

在动任何手之前，按顺序读：

1. **Myco kernel 的 `docs/agent_protocol.md`**（完整读完，尤其 §0.5、§1、§2、§3、§4、§6）
   - §0.5 告诉你 CLI 和 MCP 是等价的两条入口
   - §1 是写入白名单
   - §2 是 9 个工具的触发条件
   - §3-4 是 session boot/end 硬流程
   - §6 是给 ASCC 的 3 条铁律

2. **Myco kernel 的 `docs/ascc_migration_v1_2.md`**（这是专门为你写的迁移包）
   - §0 告诉你 CLI vs MCP 的选择
   - §1 是要粘贴进 ASCC MYCO.md 热区的块
   - §2 是要粘贴进 ASCC _canon.yaml 的块
   - §3 是验证 checklist
   - §4 是 don'ts

3. **Myco kernel 的 `_canon.yaml`** 的 `system.write_surface` 块（作为参考样例）

Myco kernel 在本机的位置：`C:\Users\10350\Desktop\Myco`（Windows 下）或
等效的 Linux mount 路径。读文档用 Read 工具即可。

## 执行步骤（按顺序，不要跳步）

### Step 1 — 安装 Myco Python 包

```bash
pip install -e C:\Users\10350\Desktop\Myco --break-system-packages
# 或 Linux 路径：
# pip install -e /path/to/Myco --break-system-packages
```

验证：`myco --version` 应该返回版本号。如果 `myco` 命令找不到，用
`python -m myco` 代替。

### Step 2 — 跑 L11 baseline，看 ASCC 现状

在 ASCC 项目根目录下：

```bash
cd <ASCC 项目根>
myco lint --project-dir .
```

此时很可能出现两类错误（都是**预期的真实 signal，不是 bug**）：

(a) **L0 报 write_surface 缺失**：因为 ASCC 的 `_canon.yaml` 里还没有
    `system.write_surface` 块。这是你接下来要加的东西，先跳过。

(b) **L10 报 notes_schema 缺失** 或 **notes/ 目录不存在**：因为 ASCC
    还没有消化系统的 canon 声明。也是你要加的。

(c) **L11 报一堆 HIGH / CRITICAL**：ASCC 历史遗留的 scratch.md / TODO.md
    / 不明顶层文件。**全部记下来**，稍后分类处理。不要急着删。

### Step 3 — 分类 L11 抓到的东西（🛑 这里需要停下来和用户确认）

把 Step 2 输出的所有 L11 报告分成三类：

- **类 A（合法但未声明）**：ASCC 真实需要的顶层目录/文件（例如
  `data/`、`experiments/`、`runs/`、`configs/`、`results/`、`hpc_utils.py`
  之类）。这些要加到 write_surface.allowed。
- **类 B（历史垃圾）**：过去会话留下的 scratch / debug / 探针脚本 /
  老 TODO。这些应该删除或 gitignore。
- **类 C（不确定）**：看不出是哪类。

输出一份清单给用户，格式：

    L11 违约清单：
      [类 A - 合法]
        - data/
        - experiments/
        - ...（你判断合法的）
      [类 B - 建议清理]
        - scratch.md（3 天前的临时文件）
        - debug_env.py（一次性探针）
        - ...
      [类 C - 需要你确认]
        - <文件>：<为什么不确定>
        - ...

    请确认：
      1. [类 A] 列表是否完整？有没有我漏掉的合法目录？
      2. [类 B] 列表是否可以删除/gitignore？
      3. [类 C] 逐条判断。

**等用户回复后再继续 Step 4**。不要擅自删除或修改任何文件。

### Step 4 — 写入 canon（_canon.yaml）

根据用户在 Step 3 的确认，把以下两个块加到 ASCC 的 `_canon.yaml` 的
`system:` 下面（在现有内容之后追加）。

```yaml
  notes_schema:
    dir: notes
    filename_pattern: '^n_\d{8}T\d{6}_[0-9a-f]{4}\.md$'
    required_fields:
      - id
      - status
      - source
      - tags
      - created
      - last_touched
      - digest_count
      - promote_candidate
      - excrete_reason
    valid_statuses:
      - raw
      - digesting
      - extracted
      - integrated
      - excreted
    valid_sources:
      - chat
      - eat
      - promote
      - import
      - bootstrap

  write_surface:
    # L11 Write-Surface Lint — ASCC 的合法写入白名单
    # 契约：Myco kernel docs/agent_protocol.md §1
    allowed:
      # --- Myco 消化基质 ---
      - notes/
      - wiki/
      - docs/
      - log.md
      - MYCO.md
      - _canon.yaml
      # --- ASCC 代码与工具 ---
      - src/
      - scripts/
      - tests/
      # --- ASCC 项目特有（根据 Step 3 用户确认补齐）---
      - <填入用户确认的类 A 条目>
      # --- 标准仓库文件 ---
      - README.md
      - LICENSE
      - pyproject.toml
      - .gitignore
      - .github/
    forbidden_top_level:
      - scratch.md
      - scratch.txt
      - notes.md
      - TODO.md
      - MEMO.md
      - memo.md
      - ideas.md
      - draft.md
      - summary.md
      - thoughts/
      - my_notes/
      - tmp/
      - temp/
```

**不要把 `notes_schema` 或 `write_surface` 填成占位符**。`<填入...>`
部分必须用 Step 3 用户确认的真实目录名替换。

### Step 5 — 创建 notes/ 目录脚手架

```bash
mkdir -p notes
# 写一个简单 README 说明 notes/ 的用途（可选，但推荐）
```

或者直接 `myco init --level 1 --upgrade`（如果 Myco CLI 支持）。
不确定时直接 `mkdir notes` 即可，Myco 会在首次 `eat` 时自动完善。

### Step 6 — 把 agent_protocol 引用粘贴进 ASCC 的 MYCO.md 热区

打开 ASCC 的 `MYCO.md`，找到"Agent 行为准则"那段（如果没有就紧接
身份锚点之后），粘贴以下块：

    **🔒 Myco v1.2 Hard Contract**（2026-04-11 启用）:

    运行在 Myco v1.2 基质上的 agent 必须遵守以下 3 条铁律。违约由
    L9/L10/L11 lint 自动检测。完整契约见 Myco kernel 的
    `docs/agent_protocol.md`。

    1. **不确定就 eat**：任何内容不知道往哪放，先 `myco eat --content "..."`
       作为 raw note，tags 标清楚来源，然后继续任务。事后再 digest。
       不要建 scratch.md / TODO.md / memo.md / thoughts/（L11 CRITICAL）。

    2. **不绕过工具**：
       - notes/*.md 只能通过 `myco eat` / `myco digest` 生成，不能手写
       - notes/*.md 的 status 字段只能通过 `myco digest` 修改
       - log.md 只能 append
       - MYCO.md 的任何修改都必须先有一条 extracted note 作为依据

    3. **摩擦必捕**：Myco 工具不够用/不顺手/有歧义时 → `myco eat --tags
       friction-phase2,<其他>` 捕获。格式：
       - `[friction-phase2] <症状一句话>`
       - 触发场景：<上下文>
       - 期望行为：<希望工具怎么做>
       - workaround：<临时处理>

       这些 note 会直接喂给 Myco Phase ②，漏一条 = 盲设计一次。

    **Session boot sequence**（每次会话前必须）：
    1. 读 MYCO.md 热区 + 身份锚点
    2. `myco hunger` — 看消化系统健康度
    3. 如果 hunger 报 raw_backlog/stale_raw → `myco digest --to digesting`
       处理 1-2 条最老 raw note
    4. 开始正式任务

    **Session end sequence**：
    1. `myco lint --project-dir .` 确认绿灯
    2. 未完成的想法 → `myco eat` 为 raw note，tags 带 followup
    3. 不要写 TODO.md / 不要写 scratch.md

### Step 7 — 清理 Step 3 类 B 的历史垃圾

根据用户 Step 3 的确认：
- 删除可以删的历史 scratch/TODO/探针脚本
- 或把它们加到 `.gitignore`

**重要**：删除前先 `myco eat` 一条 note 记录这次清理：

```bash
myco eat --content "ASCC migration v1.2: cleaned up <N> legacy scratch/TODO files (listed below). These were from pre-contract era and served as the first L11 signal." --tags meta,migration,cleanup --source eat
```

### Step 8 — 再跑一次完整 lint 验证

```bash
myco lint --project-dir .
```

期望结果：**L0-L11 共 12 维全绿**。如果仍有 HIGH/CRITICAL：
- L11 仍有 HIGH → 说明 write_surface.allowed 还有漏的，回 Step 3
- L10 有 CRITICAL → 说明 notes/ 下有非 n_*.md 文件，手动清理
- 其他 → 按报告处理

### Step 9 — Dogfood：吃下迁移本身

```bash
myco eat --content "ASCC migrated to Myco v1.2 Agent Protocol on 2026-04-11. Write surface whitelist active. L0-L11 lint 12/12 PASS. First friction-capture test." --tags meta,migration,friction-phase2 --title "ASCC v1.2 Migration Landed"
```

然后立即：

```bash
myco hunger
myco view --status raw
```

确认刚吃的 note 出现在 raw 队列里。

### Step 10 — Smoke test 四件套

```bash
# 1. 查看所有 raw note
myco view --status raw --limit 10

# 2. digest 刚才那条 note
myco digest --to integrated

# 3. 再看一次 hunger
myco hunger

# 4. 最终 lint
myco lint --project-dir .
```

四步都绿 = 迁移成功。

### Step 11 — 提交改动

```bash
git add _canon.yaml MYCO.md notes/
# 根据 Step 7 也可能需要 git rm 一些历史垃圾
git commit -m "chore: migrate to Myco v1.2 Agent Protocol + L11 write-surface contract

- Add system.notes_schema + system.write_surface to _canon.yaml
- Insert Myco v1.2 Hard Contract block into MYCO.md hot-zone
- Clean up <N> legacy scratch/TODO files (L11 baseline signal)
- Initialize notes/ directory for digestive substrate
- L0-L11 lint 12/12 PASS

Ref: Myco kernel docs/agent_protocol.md v1.0, docs/ascc_migration_v1_2.md"
```

**不要 push**。先让用户 review commit 再决定是否 push。

### Step 12 — 报告回用户

最后给用户一个完整的 migration 报告，格式：

    ✅ ASCC Myco v1.2 Migration 完成

    变更摘要：
    - _canon.yaml：新增 system.notes_schema + system.write_surface
    - MYCO.md：热区插入 Myco v1.2 Hard Contract 块（3 铁律 + boot/end）
    - notes/：新建目录，首条 dogfood note 已 integrated
    - 清理：删除 <N> 个历史 scratch/TODO 文件（列表见 log）

    L11 baseline 发现的问题：
      [类 A 合法] 已加入白名单：<列表>
      [类 B 清理] 已删除或 gitignore：<列表>
      [类 C 不确定] 用户确认结果：<列表>

    验证：
      myco lint --project-dir . → 12/12 PASS
      myco hunger → healthy（或 <具体信号>）
      smoke test：eat → view → digest → hunger 全绿

    待用户决定：
      - 是否 push commit（现在是本地 staged）
      - 是否在 Cowork MCP 配置里注册 myco MCP server（可选，见 Step 0）

    下一次会话起，请遵守 Session Boot Sequence：
      1. 读 MYCO.md 热区
      2. myco hunger
      3. 处理 raw_backlog（如有）
      4. 开始工作

## 红线（绝对不要做）

- ❌ 不要跳过 Step 3 的用户确认，不要擅自判断类 B 可删
- ❌ 不要为了让 L11 绿灯就往 write_surface.allowed 里塞一切
- ❌ 不要手写 notes/n_*.md 文件（永远经 myco eat）
- ❌ 不要修改 forbidden_top_level 列表让 scratch.md 合法
- ❌ 不要跳过 Step 9 的 dogfood — 第一条 note 必须是迁移本身
- ❌ 不要 push commit 除非用户明确同意
- ❌ 如果任何步骤失败且你不确定原因：停下来，`myco eat` 一条
  friction-phase2 note 描述问题，然后问用户

## 成功标准

- L0-L11 lint 12/12 PASS
- ASCC 有至少 1 条 integrated note（迁移自身）
- _canon.yaml 包含 notes_schema + write_surface
- MYCO.md 热区含 Hard Contract 块
- 用户 review 过 migration 报告

开始。

=== END ASCC MIGRATION TASK ===
