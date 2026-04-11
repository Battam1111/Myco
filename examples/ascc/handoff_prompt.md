# ASCC Agent Handoff Prompt — Myco contract v0.8.0 接入 / 升级指令

> **用途**：这是一条**可直接复制粘贴给 ASCC agent** 的完整任务指令，用于把
> ASCC 项目接入（首次）或升级（既有）到当前 Myco 基质 —— pre-release 包
> `myco 0.2.0`，kernel contract `v0.8.0`，15 维 lint（L0-L14），三通道代谢
> 架构 + 量化指标体系。
>
> **适用范围**：
> - (a) ASCC 尚未接入 Myco：走完 12 步。
> - (b) ASCC 已接入旧版 Myco（v1.2 / v1.7.0 及更早任何 v1.x）：走 12 步，
>   Step 4–6 会把旧 `system.write_surface` / `notes_schema` / MYCO.md 热区
>   **原地升级**到 Wave 8 状态。
>
> **使用方法**：复制 `=== BEGIN ASCC WAVE8 TASK ===` 和 `=== END ASCC WAVE8
> TASK ===` 之间的全部内容（包括两行本身），粘贴到 ASCC 会话的第一条用户
> 消息里。ASCC agent 会按 12 步自动执行，并在 Step 3 停下来等你确认 L11
> baseline 分类。
>
> **关键人机交接点**：
> - **Step 3**：L11 baseline 的 A/B/C 分类必须由用户确认，不能让 agent
>   擅自删除类 B。
> - **Step 11**：明确不 push，等你 review commit 再决定。
>
> **相关文档**（路径已对齐 Wave 8.2）：
> - `docs/agent_protocol.md` — 硬契约本体（Upstream Protocol v1, §8）
> - `docs/craft_protocol.md` — Craft Protocol v1（结构化自对抗辩论 W3）
> - `examples/ascc/migration_playbook.md` — 细致迁移包 §0-§5（本指令是它的
>   执行脚本；Wave 8.2 从 `docs/ascc_migration_v1_2.md` 迁至此）
> - `docs/contract_changelog.md` 顶部 — Wave 8 re-baseline banner（必读，
>   解释为什么包版本从 1.1.0 降到 0.2.0、contract 从 v1.7.0 降到 v0.8.0）
> - `MYCO.md` § 指标面板 — 量化指标体系 schema + 初始值（样例）
> - `_canon.yaml::system.write_surface` / `system.indicators` — 契约样例
>
> **最后更新**：2026-04-11（Wave 8.2 版）

---

## 复制以下全部内容粘贴给 ASCC agent

=== BEGIN ASCC WAVE8 TASK: Myco contract v0.8.0 接入 / 升级 ===

你现在要完成 ASCC 项目对 Myco 基质当前版本 —— pre-release package `myco
0.2.0`，kernel contract `v0.8.0`，15 维 lint (L0-L14) —— 的接入或升级。
这是硬契约对齐任务，不是可选升级。

Wave 8（2026-04-11）Myco kernel 做了一次**全方位 pre-release re-baseline**：
所有以 `v1.x.y` 命名的 contract 版本和 `1.x.y` 发布的包版本在语义完全保留
的前提下，**数字上全部下调为 `v0.x.y` / `0.x.y`**。理由：Myco 从未进行过
真正的 1.0 正式发布，继续对外叫 v1 会让用户误以为已经稳定。ASCC 侧需要做
的事在下面的 Step 0 里。

同时 Wave 8 把"系统自我量化"升级为 **schema/value/history 三层分离**的
量化指标体系：schema 在 kernel 的 `_canon.yaml::system.indicators` 定义，
value 写入 `MYCO.md` 的 `## 📊 指标面板` 段，history append 到 `log.md`
milestone。ASCC 侧可选择是否采纳 —— 不采纳也能通过 15 维 lint；采纳则会
在 Step 5.5 生成 ASCC 自己的指标面板。

## 背景（60 秒读完）

Myco kernel 截至 contract v0.8.0 已经落地的硬能力（每一条都会影响你接下来
在 ASCC 里能做什么）：

1. **消化系统**（contract v0.4.0 落地，现仍生效）：`notes/` + 四命令
   `eat` / `digest` / `view` / `hunger`，七步管道 发现→评估→萃取→整合→
   压缩→验证→**淘汰**。Self-Model D 层死知识检测种子已落地。
2. **Agent 硬契约**（Agent Protocol + L11 Write-Surface Lint）：`write
   surface` 白名单 + forbidden_top_level 黑名单自动执行。
3. **Upstream Protocol v1**（独立 spec 版本，不随包版本降级）：instance
   → kernel 通过 `.myco_upstream_{outbox,inbox}/` bundle 通道回灌。contract
   变更必须附 craft_reference（见 §8 和 Craft Protocol）。
4. **Craft Protocol v1**（W3, contract v0.3.0）：影响 kernel 契约 / 实例
   架构 / 置信度 < 0.80 的决策必须走结构化自对抗辩论 2-N 轮
   Claim→Attack→Research→Defense→Revise，产物写到
   `docs/primordia/<topic>_craft_YYYY-MM-DD.md`。由 L13 Craft Protocol
   Schema lint 强制 frontmatter。
5. **三通道代谢**（contract v0.7.0+）：inbound (`forage/`) + internal
   (`notes/`) + outbound (upstream)。每条通道各自有 lint 契约和 hunger
   信号。L14 Forage Hygiene 守护 inbound，L10 守护 internal，L12 守护
   outbound。
6. **量化指标体系**（contract v0.8.0，本 wave 新增）：`_canon.yaml::system
   .indicators` schema，区间 `[0.0, 1.0]`，合法后缀 `_progress / _confidence
   / _maturity / _saturation / _pressure`，`bootstrap_ceiling_without_
   evidence: 0.70`，rationale 必填。value 存 MYCO.md 指标面板，history
   append log.md。

如果 ASCC 不接入 Wave 8：
- 你会继续用"最像人类的方式"建 scratch / TODO / thoughts —— 这些会被
  L10/L11 判违约（写到 15 维 lint 里）
- ASCC 的 friction-phase2 摩擦数据无法喂给 Myco 进化引擎
- 上行回灌通道的 bundle 格式对不上，upstream 流程断
- 无法使用指标面板做项目健康监测

## 前置知识：在动任何手之前，按顺序读完这六份文档

**Myco kernel 在本机的位置**：`C:\Users\10350\Desktop\Myco`（Windows）
或等效的 Linux mount 路径。读文档用 Read 工具即可。

1. **`docs/agent_protocol.md`**（完整读完，尤其 §0.5、§1、§2、§3、§4、
   §6、§8 Upstream Protocol、§8.9 三通道代谢分类）
   - §0.5：CLI 和 MCP 是等价入口
   - §1：write surface 白名单
   - §2：9 个工具的触发条件
   - §3-4：session boot/end 硬流程
   - §6：给 ASCC 的铁律
   - §8：Upstream Protocol 全部（class_x/y/z、craft_reference、bundle 格式）
   - §8.9：三通道正交化

2. **`docs/craft_protocol.md`**（至少通读一次）
   - kernel_contract 类决策 floor 0.90 / instance_contract 0.85 /
     exploration 0.75
   - Claim→Attack→Research→Defense→Revise 流程
   - frontmatter 必填字段（L13 强制）

3. **`docs/contract_changelog.md` 的顶部 re-baseline banner + v0.8.0 条目**
   - 必读：为什么所有 v1.x 字符串在当前状态里都等价于 v0.x
   - 本 ASCC 接入指令里所有"v0.x"都可以读成"旧的 v1.x"的重命名

4. **`examples/ascc/migration_playbook.md`**（这是 Wave 8.2 从
   `docs/ascc_migration_v1_2.md` 迁至此的详细迁移包 §0-§5；本指令是它的
   执行脚本）

5. **`_canon.yaml` 的 `system.write_surface` + `system.indicators` 两节**
   （作为契约样例，ASCC 要写自己的对应节）

6. **`MYCO.md` 的 `## 📊 指标面板` 段**（如果要采纳量化指标，这是样例
   格式）

## 执行步骤（按顺序，不要跳步）

### Step 0 — 清理 ASCC 侧对旧 v1.x Myco 的引用（升级场景才做）

如果 ASCC 的 `_canon.yaml` 里已经有 `system.synced_contract_version:
"v1.X.Y"`（任何 v1.x 字符串），这是 Wave 8 之前的状态。现在把它改为主号
减一的对应值：

    v1.2.0 → v0.2.0
    v1.3.0 → v0.3.0
    v1.4.0 → v0.4.0
    v1.5.0 → v0.5.0
    v1.6.0 → v0.6.0
    v1.7.0 → v0.7.0

然后升级到最新：

```yaml
  synced_contract_version: "v0.8.0"
```

如果 ASCC 的 MYCO.md 或 README 里有任何 "Myco v1.x" / "kernel contract
v1.x" 的当前状态描述，也一并改到 `v0.x`。**历史 dated 条目（log.md
milestone、过去的 commit 消息、primordia craft 记录）保留 v1.x 不动**
—— 它们是 immutable history。

### Step 1 — 安装最新 Myco Python 包

```bash
pip install -e C:\Users\10350\Desktop\Myco --break-system-packages
# 或 Linux 路径：
# pip install -e /path/to/Myco --break-system-packages
```

验证：

```bash
myco --version
# 期望输出: 0.2.0（注意：是 0.2.0 不是 1.1.0；Wave 8 已下调）
```

如果 `myco` 命令找不到，用 `python -m myco` 代替。

### Step 2 — 跑完整 15 维 lint baseline，看 ASCC 现状

在 ASCC 项目根目录下：

```bash
cd <ASCC 项目根>
myco lint --project-dir .
```

期望这次会出现几类错误（都是**预期的真实 signal，不是 bug**）：

(a) **L0 报 write_surface 缺失** / 字段不对：因为 ASCC 的 `_canon.yaml`
    还没有 Wave 8 状态的 `system.write_surface` 块，或旧状态需要更新。

(b) **L10 Notes Schema** 报 CRITICAL：如果 ASCC 没有 notes/ 或 schema 未
    声明。若 ASCC 已接入旧版，schema 字段可能需要对齐 v0.4.0 的 optional
    fields (view_count / last_viewed_at)。

(c) **L11 Write Surface** 报一堆 HIGH / CRITICAL：ASCC 历史遗留的 scratch
    / TODO / 不明顶层文件。全部记下来，Step 3 处理。

(d) **L12 Upstream Dotfile Hygiene** 可能报：如果 ASCC 没有
    `.myco_upstream_{outbox,inbox}/` 或脏污。Wave 8 之前就存在此 lint。

(e) **L13 Craft Protocol Schema**：如果 ASCC 的 `docs/primordia/` 下有
    craft 文件 frontmatter 不合规。一般不会报。

(f) **L14 Forage Hygiene**：如果 ASCC 没有 `forage/` 目录——L14 会跳过
    该文件；有 `forage/` 但没有 `_index.yaml` manifest——L14 会报。如果
    ASCC 暂不需要 inbound 通道，**不建** forage/ 即可跳过。

**把 15 维报告完整保存下来**，接下来逐维处理。

### Step 3 — 分类 L11 抓到的东西（🛑 这里必须停下来和用户确认）

把 Step 2 的 L11 输出分成三类：

- **类 A（合法但未声明）**：ASCC 真实需要的顶层目录/文件（例如
  `data/` `experiments/` `runs/` `configs/` `results/` `hpc_utils.py`
  之类）。这些要加到 `write_surface.allowed`。
- **类 B（历史垃圾）**：过去会话留下的 scratch / debug / 探针脚本 /
  老 TODO。这些应该物理删除或 gitignore（不是加白名单）。
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

    请确认：
      1. [类 A] 列表是否完整？有没有我漏掉的合法目录？
      2. [类 B] 列表是否可以删除或 gitignore？
      3. [类 C] 逐条判断。

**等用户回复后再继续 Step 4**。不要擅自删除或修改任何文件。

### Step 4 — 写入 canon (`_canon.yaml`) 的 Wave 8 完整块

根据 Step 3 的用户确认，把以下三个块加到 ASCC 的 `_canon.yaml` 的
`system:` 下面。如果 ASCC 已有旧版对应块（v0.4.0 时代），**原地替换**。

```yaml
  # ── Contract 版本锁（Wave 8 re-baseline） ─────────────────────────────
  synced_contract_version: "v0.8.0"   # last kernel contract aligned with

  # ── 消化系统（contract v0.4.0，Wave 8 仍生效） ───────────────────────
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
    optional_fields:
      - view_count
      - last_viewed_at
    valid_statuses:
      - raw
      - digesting
      - extracted
      - integrated
      - excreted
    terminal_statuses:
      - extracted
      - integrated
    dead_knowledge_threshold_days: 30
    valid_sources:
      - chat
      - eat
      - promote
      - import
      - bootstrap
      - forage

  # ── Write Surface（L11 硬契约，Wave 8 版） ───────────────────────────
  write_surface:
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

  # ── 量化指标体系 schema（contract v0.8.0，Wave 8 新增；可选采纳）─────
  # 如果你要用指标面板，保留此块；不用则删除整个 indicators 节。
  indicators:
    range: [0.0, 1.0]
    bootstrap_ceiling_without_evidence: 0.70
    valid_suffixes:
      - _progress
      - _confidence
      - _maturity
      - _saturation
      - _pressure
    rationale_required: true
    stale_after_days: 90
    authoritative_value_location: MYCO.md#指标面板
    history_location: log.md
    substrate_keys: []   # ASCC 自己定义，样例见 Step 5.5
```

**不要把 `notes_schema` / `write_surface` / `indicators` 填成占位符**。
`<填入...>` 部分必须用 Step 3 用户确认的真实目录名替换。

### Step 5 — 创建 / 升级 notes/ 目录脚手架

```bash
mkdir -p notes
```

或者 `myco init --level 1 --upgrade` （如果 CLI 支持）。ASCC 已有 notes/
的情况直接跳过。

### Step 5.5 — （可选）生成 ASCC 自己的指标面板

如果 Step 4 保留了 `indicators` 块，打开 ASCC 的 `MYCO.md`，在"知识系统
架构"段之前插入：

    ## 📊 指标面板（采纳自 Myco contract v0.8.0）

    > Schema 在 `_canon.yaml::system.indicators`；本面板是 authoritative
    > value location；历史波动在 `log.md` milestone。
    > 区间 `[0.0, 1.0]`，合法后缀 `_progress / _confidence / _maturity
    > / _saturation / _pressure`，rationale 必填，stale_after_days=90。
    > 无外部证据时 bootstrap 置信度天花板 0.70。

    | 指标 | 值 | rationale | 证据锚 |
    |------|----|-----------|--------|
    | ascc_pipeline_maturity | 0.?? | <为什么这个值> | <commit/note id> |
    | ascc_experiment_progress | 0.?? | <为什么这个值> | <commit/note id> |
    | ascc_notes_digestion_pressure | 0.?? | <为什么这个值> | myco hunger |
    | ascc_friction_backlog_pressure | 0.?? | <为什么这个值> | tag: friction-phase2 |

**填写规则**：
- 没有外部独立证据的情况下，每一项初始值不得超过 0.70
- `_pressure` 类指标高意味着压力大（0.0 = 无压力，1.0 = 爆仓）
- `_maturity / _confidence / _progress` 高意味着好（1.0 = 满）
- 每一项必须有 rationale 和证据锚；没有就设 0.50 + rationale = "bootstrap,
  awaiting evidence"

然后在 `_canon.yaml::system.indicators.substrate_keys` 数组里填入对应的
key 名字（ASCC 自己定义的 key，例如 `ascc_pipeline_maturity` 等）。

**上调 vs 下调规则**：下调随意，上调任一指标都要在 log.md 追加一条
milestone + 关联 commit hash。未来 L15 Indicators Lint 会机械化此规则。

### Step 6 — 把 Hard Contract 引用粘贴进 ASCC 的 MYCO.md 热区

打开 ASCC 的 `MYCO.md`，找到"Agent 行为准则"段（如果没有就紧接身份锚点
之后），粘贴以下块（如有旧版原地替换）：

    **🔒 Myco Hard Contract（contract v0.8.0，Wave 8 版）**

    运行在 Myco 基质上的 ASCC agent 必须遵守以下 4 条铁律。违约由
    L9/L10/L11/L12/L13/L14 lint 自动检测。完整契约见 Myco kernel 的
    `docs/agent_protocol.md` 与 `docs/craft_protocol.md`。

    1. **不确定就 eat**：任何内容不知道往哪放，先 `myco eat --content "..."`
       作为 raw note，tags 标清楚来源，然后继续任务。事后再 digest。
       不要建 scratch.md / TODO.md / memo.md / thoughts/（L11 CRITICAL）。

    2. **不绕过工具**：
       - `notes/*.md` 只能通过 `myco eat` / `myco digest` 生成，不能手写
       - `notes/*.md` 的 status 字段只能通过 `myco digest` 修改
       - `log.md` 只能 append
       - `MYCO.md` 的任何修改都必须先有一条 extracted note 作为依据
       - `forage/_index.yaml` 只能通过 `myco forage` 家族命令更新（如启用）

    3. **摩擦必捕**：Myco 工具不够用/不顺手/有歧义时 →
       `myco eat --tags friction-phase2,<其他>` 捕获。格式：
       - `[friction-phase2] <症状一句话>`
       - 触发场景：<上下文>
       - 期望行为：<希望工具怎么做>
       - workaround：<临时处理>

       这些 note 直接喂给 Myco Phase ②，漏一条 = 盲设计一次。

    4. **Kernel 契约变更走 craft + upstream**：任何影响 Myco kernel
       `docs/agent_protocol.md` / `_canon.yaml` / `src/myco/lint.py` /
       `src/myco/templates/**` 的建议，**不能**在 ASCC 侧直接改 kernel
       文件。必须：
       - 先写一条 craft 记录（`docs/primordia/<topic>_craft_YYYY-MM-DD
         .md`，decision_class >= instance_contract，craft_protocol_version: 1）
       - 再通过 `.myco_upstream_outbox/<note-id>.bundle.yaml` 投递，附
         `craft_reference: <craft path>` 字段
       - kernel 侧由 L13 + §8.3 校验
       - class_z（kernel contract）bundle 缺 `craft_reference` 会被拒

    **Session boot sequence**（每次会话前必须）：
    1. 读 MYCO.md 热区 + 身份锚点 + 📊 指标面板
    2. `myco hunger` — 看三通道代谢健康度
    3. 如果 hunger 报 `raw_backlog` / `stale_raw` / `forage_backlog` /
       `structural_bloat` / `dead_knowledge` → 按严重度先处理 1-2 条
    4. 开始正式任务

    **Session end sequence**：
    1. `myco lint --project-dir .` 确认 15/15 绿灯（L0-L14）
    2. 未完成的想法 → `myco eat` 为 raw note，tags 带 followup
    3. 指标面板如有上调，记得在 log.md 追加 milestone + commit hash
    4. 不写 TODO.md / 不写 scratch.md

### Step 7 — 清理 Step 3 类 B 的历史垃圾

根据 Step 3 的确认：
- 删除可以删的历史 scratch / TODO / 探针脚本
- 或把它们加到 `.gitignore`

**重要**：删除前先 `myco eat` 一条 note 记录这次清理：

```bash
myco eat --content "ASCC Wave 8 接入 / 升级：清理 <N> 个历史 scratch/TODO/探针文件（清单见下）。这些是 pre-contract 时期或旧版 Myco 时代遗留，构成本次 L11 baseline 的第一批 signal。" --tags meta,migration,cleanup,wave8 --source eat
```

### Step 8 — 再跑一次完整 15 维 lint 验证

```bash
myco lint --project-dir .
```

期望结果：**L0-L14 共 15 维全绿**。如果仍有 HIGH/CRITICAL：

- L11 仍有 HIGH → write_surface.allowed 有漏，回 Step 3/4
- L10 有 CRITICAL → notes/ 下有非 n_*.md 文件，手动清理
- L12 有 HIGH → `.myco_upstream_*/` 格式问题，参考 kernel 样例
- L13 有 HIGH → `docs/primordia/` 下有 craft 文件 frontmatter 不合规；
  要么补 frontmatter，要么去掉 craft_protocol_version 字段让 grandfather
- L14 有 HIGH → `forage/` 存在但 `_index.yaml` 格式不对，或文件/manifest
  不一致；按报告修
- 其他 → 按报告处理

### Step 9 — Dogfood：吃下这次接入/升级本身

```bash
myco eat --content "ASCC Wave 8 接入 / 升级到 Myco contract v0.8.0 完成（2026-04-11）。变更：synced_contract_version v?.?.? → v0.8.0；write_surface Wave 8 版；notes_schema 含 optional fields；indicators 面板 <采纳 | 未采纳>；清理 <N> 个历史垃圾；Hard Contract 块已插入 MYCO.md 热区。L0-L14 lint 15/15 PASS。" --tags meta,migration,wave8,friction-phase2 --title "ASCC Wave 8 Migration Landed"
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

# 2. digest 刚才那条 note 为 integrated
myco digest --to integrated

# 3. 再看一次 hunger
myco hunger

# 4. 最终 lint
myco lint --project-dir .
```

四步都绿 = 接入/升级成功。

### Step 11 — 提交改动

```bash
git add _canon.yaml MYCO.md notes/
# 根据 Step 7 可能还有 git rm / 新的 gitignore 条目
git commit -m "chore: align ASCC to Myco contract v0.8.0 (Wave 8)

- _canon.yaml: synced_contract_version -> v0.8.0; write_surface refreshed;
  notes_schema optional fields (view_count/last_viewed_at); indicators
  schema block <adopted | not adopted>
- MYCO.md: Hard Contract v0.8.0 block in hot zone (4 rules + boot/end);
  indicators dashboard section <added | n/a>
- Cleaned up <N> legacy scratch/TODO files (L11 baseline signal)
- L0-L14 lint 15/15 PASS

Ref: Myco kernel docs/agent_protocol.md, docs/craft_protocol.md,
docs/contract_changelog.md (v0.8.0 + Wave 8 re-baseline banner),
examples/ascc/migration_playbook.md"
```

**不要 push**。先让用户 review commit 再决定是否 push。

### Step 12 — 报告回用户

最后给用户一个完整的 Wave 8 接入报告，格式：

    ✅ ASCC Wave 8 Migration 完成（contract v0.8.0）

    变更摘要：
    - _canon.yaml:
        · synced_contract_version v?.?.? → v0.8.0
        · notes_schema: 含 Wave 8 optional fields
        · write_surface: Wave 8 allowlist
        · indicators: <采纳 | 未采纳>
    - MYCO.md:
        · 热区插入 Hard Contract v0.8.0 块（4 铁律 + boot/end）
        · <指标面板段已添加 | 未采纳>
    - notes/：<X> 条 raw → <Y> 条 integrated，首条 wave8 dogfood note 已 integrated
    - 清理：删除 <N> 个历史 scratch/TODO/探针文件

    L11 baseline 发现的问题：
      [类 A 合法] 已加入白名单：<列表>
      [类 B 清理] 已删除或 gitignore：<列表>
      [类 C 不确定] 用户确认结果：<列表>

    15 维 lint 验证：
      myco lint --project-dir . → 15/15 PASS（L0-L14 全绿）
      myco hunger → <healthy | 具体信号>
      smoke test：eat → view → digest → hunger 全绿

    指标面板（如采纳）初始值：
      ascc_pipeline_maturity = 0.??  rationale: ...
      ascc_experiment_progress = 0.??  rationale: ...
      ascc_notes_digestion_pressure = 0.??  rationale: ...
      ascc_friction_backlog_pressure = 0.??  rationale: ...

    待用户决定：
      - 是否 push commit（现在是本地 staged）
      - 是否在 Cowork MCP 配置里注册 myco MCP server（可选）
      - 是否启用 forage/ inbound 通道（现状 ASCC 暂不需要）

    下一次会话起，请遵守 Session Boot Sequence：
      1. 读 MYCO.md 热区 + 指标面板
      2. myco hunger
      3. 处理 raw_backlog / stale_raw / forage_backlog（如有）
      4. 开始工作

## 红线（绝对不要做）

- ❌ 不要跳过 Step 3 的用户确认，不要擅自判断类 B 可删
- ❌ 不要为了让 L11 绿灯就往 write_surface.allowed 里塞一切
- ❌ 不要手写 `notes/n_*.md` 文件（永远经 `myco eat`）
- ❌ 不要修改 forbidden_top_level 列表让 scratch.md 合法
- ❌ 不要在 ASCC 侧直接改 Myco kernel 文件；kernel 契约变更必须走
  craft + upstream bundle
- ❌ 不要跳过 Step 9 的 dogfood — 第一条 note 必须是接入/升级本身
- ❌ 不要 push commit 除非用户明确同意
- ❌ 不要擅自把指标面板值上调到 > 0.70 或高于之前的值而不加 log milestone
- ❌ 如果任何步骤失败且你不确定原因：停下来，`myco eat` 一条
  `friction-phase2` + `wave8` note 描述问题，然后问用户

## 成功标准

- `myco --version` 返回 `0.2.0`
- `_canon.yaml` 含 Wave 8 版的 `synced_contract_version: "v0.8.0"` +
  `notes_schema` + `write_surface` 三个核心块；`indicators` 可选
- `MYCO.md` 热区含 Hard Contract v0.8.0 块
- `myco lint --project-dir .` → 15/15 PASS
- ASCC 有至少 1 条 integrated wave8 dogfood note
- 如采纳指标面板：每一项都有 value + rationale + 证据锚
- 用户 review 过 migration 报告

开始。

=== END ASCC WAVE8 TASK ===
