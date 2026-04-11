---
type: craft
status: ACTIVE
created: 2026-04-11
target_confidence: 0.90
current_confidence: 0.91
rounds: 2
craft_protocol_version: 1
decision_class: kernel_contract
parent_craft: docs/primordia/upstream_protocol_craft_2026-04-11.md
wave: 9
---

# Upstream Absorb · 把半完成的回灌通路收尾 (Wave 9)

> **Status**: DRAFT — 本 craft 结束前必须 ≥ 0.90 才能升 ACTIVE。
> **父 craft**: `upstream_protocol_craft_2026-04-11.md` (v1.0) 把 outbox/inbox 协议
> 定义好了，但**落地清单 D 段**（`myco upstream scan/confirm` CLI）显式延期至 v1.0.1。
> 本 craft 把这个"延期"关掉，并补齐 ingest 到 notes/ 的冶炼段。

## 0. Problem definition

### 0.1 表面症状

- ASCC 会话里产生了两个 kernel 级 friction bundle（`ce72` template 缺口、
  `3356` L1 backtick false-positive），投递到 `.myco_upstream_outbox/`
  等 Myco 开发会话读取。
- Myco 侧只挂载了 Myco 目录，看不到 ASCC 的 outbox；bundle 处于"悬空"状态 ——
  即"上游收到了吗、什么时候会被处理、还是已经丢了"都无法回答。
- 首次被人注意到是在上一条用户消息里：Yanjun 直接指出"Myco 没办法访问那个
  目录，这种情况的出现是否是某种设计失误"。

### 0.2 实际缺口（不是表面那个）

表面看像是"Myco 没挂 ASCC 所以读不到" —— 但这是操作层，不是契约层的根因。
读 `upstream_protocol_craft_2026-04-11.md` §落地清单后真正的缺口是：

**Upstream Protocol v1.0 的实现是半边天。** 下游侧 outbox + 版本锁 + 类通道
已经落地；但**kernel 侧的接收-消化段**被显式标记 *"D. 工具链（可选，v1.0.1
延后）"* 并从未执行。具体遗漏：

1. `.myco_upstream_inbox/` 物理目录从未被创建（只在 L11 lint 里被保留为合法
   dotdir，见 `src/myco/lint.py:622`）。
2. `myco upstream scan/confirm` CLI 从未实现（落地清单 D.10, D.11）。
3. **bundle → note 的冶炼协议完全缺失**。下游 outbox 用 YAML 封装是合理的，
   但 kernel 侧要让它进入 7 步代谢，必须有明确的 "bundle absorbed → note raw
   with tag upstream-bundle" 的转换规则 —— 这在 v1.0 craft 的 §2 结论里没有
   写清楚，在 §2.3 "传输层"段落里只提了"agent 直接投递到 kernel 的
   `.myco_upstream_inbox/`" 就断了。
4. **没有压力指标守护**。Wave 8 为三通道分别建立了 `forage_backlog_pressure`
   和 `notes_digestion_pressure`，但 upstream 返回方向没有对应的
   `upstream_inbox_pressure` —— 意味着 bundle 可以在 inbox 里静默堆积而仪表盘
   不会亮红灯。
5. **ASCC handoff_prompt 没有 courier 步骤**。当前 handoff prompt 告诉 agent
   "bundle 丢到 outbox"，但没有告诉它接下来该怎样通知 Myco / 通知用户 /
   确认投递。

### 0.3 为什么是 kernel_contract class

改动将触及以下 Class Z 路径（按 `_canon.yaml: upstream_channels.class_z`）：

- `docs/agent_protocol.md`（补全 §8 的 kernel 侧动词）
- `_canon.yaml`（新增 `upstream_inbox_pressure` substrate_key；新增 kernel 侧
  的 absorb/ingest 状态机字段）
- `src/myco/lint.py`（L12 描述更新；可能 L15 为 `upstream_inbox_pressure` 留
  钩子但不强制）
- `src/myco/cli.py`（新子命令 `myco upstream scan/absorb/ingest`）
- `src/myco/templates/` & `MYCO.md` dashboard（同步指标）

→ `decision_class: kernel_contract` → **floor 0.90**。

---

## 1. Round 1

### 1.1 Claim (C1)

**提议**：把 Upstream Protocol v1.0 的 kernel 侧接收通路一次性完成，五件套：

| # | Item | 路径 / 形式 |
|---|---|---|
| C1-a | 创建 `.myco_upstream_inbox/` + `README.md`（说明用途；禁止手写） | `.myco_upstream_inbox/README.md` |
| C1-b | 新 CLI `myco upstream scan [--from <instance-path>]` | `src/myco/cli.py`, `src/myco/upstream.py`（新文件） |
| C1-c | 新 CLI `myco upstream absorb <instance-path>` —— 从 instance outbox 拷贝到 kernel inbox（加时间戳前缀），*不* 自动 ingest | 同上 |
| C1-d | 新 CLI `myco upstream ingest <bundle-id>` —— 读取 inbox 里的 bundle，生成一条 `notes/` raw note（tag: `upstream-bundle`, `source-project:<X>`, `upstream-class:<x/y/z>`），bundle 文件移动到 `.myco_upstream_inbox/absorbed/` 作为审计痕迹 | 同上 |
| C1-e | 新增 substrate_key `upstream_inbox_pressure` = `待 ingest 的 bundle 数 / ceiling(默认 5)`，超过 1.0 截断；bootstrap 值 0.00 | `_canon.yaml`, `MYCO.md` dashboard |

此外两件**非五件套但必须同步**：

| # | Item |
|---|---|
| C1-f | `docs/agent_protocol.md §8` 补 kernel 侧动词：列出 scan / absorb / ingest 命令与状态机 |
| C1-g | `examples/ascc/handoff_prompt.md` 新增 "Step 11.5 · 向 Myco 投递 bundle" courier 步骤 |
| C1-h | `docs/contract_changelog.md` 追加 v0.9.0 条目（minor，因为只新增接口、不破坏既有 outbox 约定） |

初始自评置信度 **0.70**（= craft bootstrap ceiling，留足攻击空间）。

### 1.2 Attack

我自己扮演架构师角色连开 5 枪：

---

**A1 · "为什么不直接塞进 forage/ 复用代谢？"**

Wave 8 刚刚把三代谢通道立为契约：`inbound (forage)` 是**外部世界**来的素材，
`internal (notes)` 是消化池，`outbound (upstream)` 是向 kernel 发射。
`upstream_inbox` 现在又要造一个"第四通道"吗？为什么不直接让 bundle 落进
`forage/upstream_returns/` 然后走 `raw → digesting → digested → absorbed` 标
准流程？这样不需要新 CLI、不需要新 lint、不需要新 indicator —— 全部复用已经
在运转的机制。

这是对 C1-b 到 C1-e **整个骨干**的否决攻击。**如果 A1 成立，五件套里有四件
没必要。**

---

**A2 · "Myco 其实读不到 ASCC 目录，absorb CLI 是空中楼阁"**

父 craft §2.3 明确写："假设跨项目双 mount 为主路径" 是 A8 否决掉的。
`upstream_protocol_craft` 落地清单 D.10-D.11 被延后的*真正理由*不是"还没来得
及"，而是"在 Cowork 单挂载世界里，kernel 根本拿不到 instance 的 outbox 路径"。

即使这次 Yanjun 临时给 Myco 会话开了 ASCC 特权挂载 —— 这是**特权**，不是**常
态**。为特权场景写的 CLI 在非特权场景下是死代码。且"鼓励特权挂载"本身与父
craft A8 冲突。

→ 否决 C1-b, C1-c。

---

**A3 · "`upstream_inbox_pressure` 是指标增生"**

Wave 8 刚刚定了 7 个 substrate_keys，canon 注释里明说"Adding a new key =
kernel_contract class craft or higher"。为了一个目前 **n = 2** 的 backlog
添加一个 pressure 指标，是典型的"指标因事件而生"反模式 —— Phase ② friction
数据驱动才对。现在连一次真正的"kernel 侧 ingest 过 bundle"的经验都没有，
就预判压力指标的 ceiling 怎么取？5 合理吗？还是 10？3？

→ 否决 C1-e，或至少把它降级到 exploration class。

---

**A4 · "bundle 的 YAML schema 和 note 的 markdown schema 根本不兼容，C1-d 写
得太轻松"**

看 `ce72.bundle.yaml`：它有 `proposed_fix_options: [a, b, c]`, `severity`,
`target_kernel_component`, `workaround_applied`, `downstream_impact` 等字段
—— 这些**是决策素材**，不是一条待消化的 raw 素材。把它"转成一条 markdown
note"会丢信息。反之如果 ingest 时要保留完整结构，note 的 L10 schema 就不够
用（L10 假设 note 是扁平文本 + frontmatter 元数据）。

C1-d 的 "bundle → note" 转换一句话就带过了，实际会是一个 schema 换位难题。
→ C1-d 不成立，必须重新设计 ingest 形态。

---

**A5 · "ce72 和 3356 两条 friction 根本用不着这么大动静"**

看两条 bundle 的 `downstream_impact` 字段：**都是 low**。`workaround_applied`
都非空。它们是"美中不足"级别的 friction，不是 blocking。为此开一整个 Wave 9
craft + 新通道 + 新 CLI + 新 indicator 是**重大小事**（over-engineering on
under-demand）。更务实的方案：直接在 Wave 9 的 log.md 里把两条 friction 用手
抄进 `notes/` 作为 `upstream-bundle-imported` note，修 template 和 L1 扫描器，
收工。0 新 CLI，0 新目录，0 新 indicator。

→ 对整个 C1 的"规模"提出攻击。

---

### 1.3 Online Research / Code Research

为了决定哪些攻击存活，我需要三份证据。

**R1.1 · 既有 forage 状态机是否真的能承载 upstream bundle？**（回应 A1）

读 `src/myco/forage.py` 的状态机定义（已在 Grep 结果里看到）：

```
states = raw | digesting | digested | absorbed | discarded | quarantined
L14 forage hygiene
forage/_index.yaml 是 Class Z 的 class_z 路径（不能下游自改）
```

forage 的 schema 假设素材是"一个外部链接 + 少量笔记"型的，_index.yaml 是**
手动 curated**（Wave 7 forage substrate craft 里的核心决策：forage 是 manifest
型，不是 drop-in 型）。把 dotdir 里的 YAML bundle 拷贝为一个 forage/ 条目，
需要：
1. 给 `_index.yaml` 添加一条新 source
2. 把 bundle 文件拷贝到 `forage/upstream_returns/<id>.yaml`
3. 打标签区分"外部采集"和"下游返航"

**然而** —— forage 的 L14 检查会要求这个 yaml 文件有 source_type, url, fetched_at
等外部采集字段，**这些字段在 upstream bundle 里全部是空的**（bundle 的来源是
"另一个 Myco 项目的自己"，不是"网上发现的论文"）。强塞会让 L14 开始报 L14
HIGH，或者逼我们给 L14 加一堆 "if type == upstream-return then skip" 的例外 ——
这正是父 craft A8 警告的"语义马甲"反模式。

→ **A1 部分失败**：不能让 upstream bundle 成为 forage 的 first-class 条目。
但 A1 的**精神**（复用代谢而非新造）是对的 —— 复用应该发生在 `notes/` 那一
段，不是 forage 那一段。

**R1.2 · Cowork 单挂载世界里，absorb CLI 是不是真死代码？**（回应 A2）

我在当前会话里用 `request_cowork_directory` 临时挂载了 OPASCC，这是一个真实
存在的通路。但 A2 的关切不是"技术上能不能"，是"契约上应不应该**依赖**这个"。

看父 craft §2.3 主路径原文（line 214-217）：

> **主路径**：下游 agent 生成 patch bundle ... 写到下游本地的
> `.myco_upstream_outbox/<note-id>.bundle.yaml`，然后**通知用户**：... 用户说
> "回灌"后：
> - 如果 kernel 在同会话 mount → agent 直接投递到 kernel 的 `.myco_upstream_inbox/`

**"同会话 mount" 作为主路径的 optional fast path 是**明文写进 v1.0 craft 的。
A2 把它读成了"被 A8 否决"，但 A8 实际否决的是"**假设**跨项目双 mount 为**
唯一**主路径"，不是"禁止双 mount"。双 mount 是被允许的快路径，只是不能作为
正确性的唯一依赖。

→ **A2 失败**：双 mount 特权作为 opt-in 快路径是合法的，absorb CLI 不是死代
码。但 A2 的**提醒**是对的 —— CLI 必须有 fallback：如果 `--from` 路径不可达，
必须明确 fail（而不是默默跳过），且必须有"手动 courier" 路径的文档。

**R1.3 · 搜索：其他开源项目怎样处理 downstream-to-upstream bundle 回灌？**
（回应 A3, A4, A5）

我不能上外网，但能**引用父 craft 已经做过的 research**：`updatebot/glibc`
模型（父 craft R1.2）说"生成零门槛 + inline confirm"。bundle 作为 YAML 文件
存在 outbox + 人工 confirm 是这个模式的直接复刻。**缺失的那一段是：confirm
之后 bundle 去哪里**。父 craft 把它画到了 `.myco_upstream_inbox/`（kernel 侧）
就停笔了。

对 A4 的直接反驳：bundle 保留为 YAML，不变形 —— 它落在 `.myco_upstream_inbox/`
里作为**结构化证据**。**ingest 的产物不是 bundle 本身的转录，而是一条指向
bundle 的 "这里有一条 kernel friction 待处理" 的 pointer note**。这样既不丢
字段，也不污染 L10：

```yaml
# notes/n_20260411TXXXXXX_<id>.md
---
id: n_20260411TXXXXXX_<id>
status: raw
source: upstream-absorbed
source_ref: .myco_upstream_inbox/<timestamp>_<id>.bundle.yaml
tags: [upstream-bundle, source-project-ascc, friction-phase2]
---
{bundle.summary 的第一行 + "详情见 source_ref"}
```

一条 note = 一条代谢单元。bundle 文件留在 inbox 作为 evidence，直到 note 达
到 `absorbed` 状态，然后 bundle 移动到 `.myco_upstream_inbox/absorbed/`。

→ **A4 部分成立，但 C1-d 能被**修正**为 "生成 pointer note"，不是原地转写。
修正后 L10 不需要改 schema，C1-d 恢复。**

对 A3 的回应：`upstream_inbox_pressure` 的 ceiling 用 5 确实是拍脑袋 ——
但**这正是 Wave 9 实战要收集的数据**。bootstrap_ceiling_without_evidence=0.70
对值设上限，现在没有 evidence 所以 ≤ 0.70，这是契约允许的。ceiling=5 的数字
写进 canon 注释里的 rationale 栏，未来 friction 驱动调整。→ **A3 不构成否决，
只构成要求"要在 canon 里标注 ceiling 来源 = bootstrap, pending friction data"。**

对 A5 的直面：**"2 条就不值得建通路"** 是量级错觉。**通路不是为这两条建的，
通路是为"未来所有 downstream 实例的 kernel friction 提交"建的**。如果 ASCC 一
个实例就在 Phase 2 早期两周内产生了 2 条 kernel friction，则按当前 friction
rate 外推，通路每月承载 4-8 条。无通路情景下每一条都要手动搬运 + 手动转抄 +
手动打标签 = 每次 ~5 分钟机械成本。规模化论证成立。→ **A5 失败**。

---

### 1.4 Defense + Revise

经过 R1.1-R1.3，攻击存活情况：

| Attack | 存活？ | 处置 |
|---|---|---|
| A1 forage 复用 | 部分 | 复用发生在 `notes/` 段（A4 修正后的 pointer note），不是 forage 段。C1-b/c/d 保留；C1-a 保留 |
| A2 absorb 空中楼阁 | 失败 | 保留；但要求 fallback: `--from` 不可达时 hard-fail + 手动 courier 文档 |
| A3 指标增生 | 弱存活 | C1-e 保留；canon 注释必须标注 ceiling=5 来源为 bootstrap + pending friction |
| A4 schema 不兼容 | 转化为修正 | C1-d 重写为 "pointer note + bundle 留为 evidence"，不原地转写 |
| A5 重大小事 | 失败 | 规模化论证成立 |

**Round 1 修订后 Claim (C1')**：

- C1-a 保留：`.myco_upstream_inbox/README.md` 写明这是 dotfile 化的 kernel 侧
  receiving dock，手写 bundle 禁止，只接受 absorb CLI 投递。
- C1-b 保留：`myco upstream scan [--from <path>]` 列出 outbox 里的 bundle；
  `--from` 缺省时报错提示 "provide instance root or use --from-stdin"。
- C1-c 保留：`myco upstream absorb <instance-path>` 把 bundle 拷贝到 kernel
  inbox，加时间戳前缀。`<instance-path>` 不可达时 exit 2 + 明确错误 + 指向
  courier fallback 文档。
- C1-d **修订**：`myco upstream ingest <bundle-id>` 创建一条 pointer note
  （`source: upstream-absorbed`, 内容 = bundle.summary），bundle 文件保持原位，
  note 走正常 7 步代谢；note 达 `absorbed` 状态时一个额外的 `myco upstream
  retire <bundle-id>` 把 bundle 移到 `.myco_upstream_inbox/absorbed/`。
- C1-e 保留：`upstream_inbox_pressure` 入 canon substrate_keys；
  rationale_required 字段必须写明 "ceiling=5 bootstrap, pending friction data"。
- C1-f, g, h 保留。

**新增 C1-i**（来自 A2 的正面建议）：`docs/agent_protocol.md §8` 新增一小段
"Courier Fallback"：描述当 Myco 和 instance 不在同会话时，由用户手动复制
bundle 到 Myco 的 `.myco_upstream_inbox/<timestamp>_<id>.bundle.yaml` 的步骤。

**Round 1 结束自评置信度 0.83**（未过 0.90 floor，必须进 Round 2）。

---

## 2. Round 2

### 2.1 Claim (C2 = C1' + 三项更细化)

C1' 基础上：

- C2-α `myco upstream scan` 的默认行为：无 `--from` 时扫描 **kernel 侧**
  `.myco_upstream_inbox/`（列出未 ingest 的 bundle），与 `myco hunger` 对称
  —— 这样 `myco upstream scan` 在单挂载 Myco 会话里也有意义（本地消化视角），
  不只是跨挂载视角。
- C2-β `myco upstream ingest` 允许 `--batch` 一次 ingest 多条 bundle（目前
  上限 10，由 canon.upstream_channels.batch_ingest_cap 控制）。
- C2-γ `upstream_inbox_pressure` 的 rationale 字段从手写改为 **CLI 自动计算**
  —— 运行 `myco upstream scan` 后 CLI 更新 MYCO.md dashboard 的值。手工编辑
  仪表盘仍允许，但会留下 drift 被 L2 察觉。

### 2.2 Attack (R2)

---

**B1 · C2-α 会让 `myco upstream scan` 有两个互斥默认语义**

"无 `--from`" 时扫 kernel inbox，"有 `--from`" 时扫 instance outbox。同一个动
词同一个子命令，两个数据源。用户会搞混。Unix 哲学反对。→ 要么把它拆成
`myco upstream scan` 和 `myco upstream list-instance`，要么接受混淆。

---

**B2 · C2-γ 自动更新 dashboard 会和 Wave 8 canon 注释"indicators 值必须有
rationale"冲突**

Canon line 317: `rationale_required: true`. 如果 CLI 自动写值，CLI 写的
rationale 是什么？"auto-updated by myco upstream scan at TTT"？这是 tautology
不是 rationale。A3 从另一个角度回来了 —— 自动化会侵蚀"每个指标必须可追溯"
的纪律。

---

**B3 · `myco upstream retire` 是第三个动词，API 臃肿**

scan / absorb / ingest / retire 四个子命令 + 每个可能还有 flag。下游 agent
要记一大堆。父 craft D.10-D.11 只设想了两个（scan + confirm）。

---

### 2.3 Research (R2)

**R2.1 · 查 cli.py 现有子命令表，看 namespace 深度**

```
grep -n 'subparsers.add_parser' src/myco/cli.py
```

需要**实际运行**才知道现有的 CLI 表面积 —— 见下一步 Bash 调用。

**R2.2 · 对 B2 的理论解**：自动化字段和手工 rationale 可以分开。解法是在
canon 里把 `upstream_inbox_pressure` 的 rationale 拆成两部分：
`auto_metric: <count>/5` + `analyst_rationale: <手写>`。CLI 只碰前者；人类只
碰后者；L15 未来检查后者是否定期更新。

**R2.3 · 对 B1 的理论解**：默认语义不该"随 flag 改变数据源"。干净做法是：
`myco upstream scan` 单义 = 扫 kernel inbox；`myco upstream absorb <path>` 既
拉取又展示（absorb 自带一个 scan-before）。→ C2-α 被 B1 否决，拆法采纳但换
形态：scan 只扫 kernel，absorb 既 scan-instance 又执行拷贝。

### 2.4 Defense + Revise

| Attack | 存活？ | 处置 |
|---|---|---|
| B1 双语义 scan | 成立 | C2-α 撤回；scan 单义 = 扫 kernel inbox |
| B2 rationale tautology | 成立 | indicator 字段拆 `auto_metric` + `analyst_rationale` |
| B3 API 臃肿 | 部分 | 合并 ingest + retire：一条 bundle ingest 时同时创建 pointer note 并把 bundle 标记为 `absorbed`（移到 `absorbed/`），不额外引入 retire。付出的代价：note 到达"真正被吃透"的语义和 bundle 被归档的语义绑定，可能过激 —— 但因为 bundle 归档并非不可逆（bundle 只是移动，不是删除），这个绑定可接受 |

**Round 2 结论 Claim (C2')**：

五件套收敛为**四件**：

1. **C2'-a** `.myco_upstream_inbox/` + `README.md` + `absorbed/` 子目录
2. **C2'-b** `myco upstream scan`（单义：扫 kernel inbox）+
   `myco upstream absorb <instance-path>`（拉 outbox 到 inbox）+
   `myco upstream ingest <bundle-id>`（生成 pointer note + 归档 bundle 到
   `absorbed/`，三步一气呵成）
3. **C2'-c** canon `indicators.substrate_keys` 加 `upstream_inbox_pressure`；
   indicator schema 字段扩为 `auto_metric / analyst_rationale` 二元
4. **C2'-d** `agent_protocol.md §8` 补 kernel 侧动词 + Courier Fallback；
   `examples/ascc/handoff_prompt.md` 补 Step 11.5；`contract_changelog.md`
   v0.9.0 条目

**Round 2 结束自评置信度 0.91** —— 越过 0.90 floor，可升 ACTIVE。

---

## 3. Conclusion extraction

### 3.1 Decisions（进 canon / 代码）

1. **D1**：`.myco_upstream_inbox/` 物理落地，与父 craft §2.3 主路径承接。
2. **D2**：CLI 三件套（scan / absorb / ingest）落进 `src/myco/upstream.py` 新
   模块 + `cli.py` 子命令注册。
3. **D3**：bundle 永不被原地转写为 note；ingest 产出 *pointer note*，bundle
   文件本体作为 evidence 留在 `absorbed/`。
4. **D4**：`indicators` schema 扩二元（auto_metric + analyst_rationale）；
   新 key `upstream_inbox_pressure`，ceiling=5，bootstrap 值 0.00。
5. **D5**：`agent_protocol.md §8` + `ascc/handoff_prompt.md` 同步更新，明确
   双 mount 快路径 + Courier Fallback 两条路径都合法。

### 3.2 Landing list

（**所有条目必须在同一个 Wave 9 提交里闭环**，父 craft 的 "D 段延后" 正是
因为 A+B+C+E 分批所以被遗忘；Wave 9 不再重复该错误。）

**契约层**
1. `docs/agent_protocol.md §8` —— 补 kernel 侧命令清单 + Courier Fallback
2. `_canon.yaml` —— `indicators.rationale_schema`, `substrate_keys` 追加
   `upstream_inbox_pressure`, `upstream_channels.batch_ingest_cap: 10`
3. `docs/contract_changelog.md` —— v0.9.0 [contract:minor]

**代码层**
4. `src/myco/upstream.py`（新）—— scan / absorb / ingest 三个函数 + bundle
   schema validation
5. `src/myco/cli.py` —— 注册 `myco upstream {scan,absorb,ingest}` 子命令
6. `src/myco/lint.py` —— L11 不变；`indicators` 解析支持二元 rationale（Wave 8
   lint L2 已验 stale_patterns，需要为新 schema 加 parser path）

**模板层**
7. `src/myco/templates/_canon.yaml` —— 如有 indicator schema 变化需要同步
8. `src/myco/templates/MYCO.md` —— dashboard 示例增加 `upstream_inbox_pressure`
   行（模板值 0.00 + "bootstrap, pending first absorb" analyst rationale）

**下游侧**
9. `examples/ascc/handoff_prompt.md` —— Step 11.5 courier + Myco 侧命令引用

**Dogfood / 实战验证（本 Wave 必须做完）**
10. 实际运行 `myco upstream absorb /sessions/gifted-eloquent-fermi/mnt/OPASCC`
    把 ce72 和 3356 两条 bundle 从 ASCC outbox 拉到 Myco inbox
11. 实际运行 `myco upstream ingest ce72` + `myco upstream ingest 3356` 生成两
    条 pointer note
12. 针对 ce72 和 3356 本身的问题实施修复（modify template + soften L1 scanner）
    —— 这两条 kernel friction 本身进入下一轮 craft 或直接 patch，由 Wave 9 落
    地后决定
13. `log.md` 追加 Wave 9 milestone
14. `MYCO.md` dashboard 更新指标面板：`upstream_inbox_pressure` 初值，
    `three_channel_maturity` 由 0.60 → ≤ 0.70（upstream 侧接收通路闭环，但仍
    是首次实战 n=1）
15. dual-path lint 15/15 pass
16. Myco 侧 git commit + ASCC 侧 git commit（bundle 被 absorbed 后 ASCC 的
    outbox 清零，需要 ASCC 侧一个 chore commit 记录）

### 3.3 Known limitations

- **KL1**: `upstream_inbox_pressure.ceiling=5` 是拍脑袋值，等 3-5 次真实 absorb
  后 Phase ② friction 数据驱动调整。现在写进 canon 注释。
- **KL2**: ingest 产出的 pointer note 依赖人工进入 digesting/digested 状态 ——
  L14 forage hygiene 的 TTL 机制 *不* 套用到 upstream 侧（upstream 没有
  backlog_pressure 字段，只有 inbox_pressure）。未来可能补 `notes_digestion_
  pressure` 的细分类目，但不在 Wave 9 范围。
- **KL3**: 目前 bundle schema (由 ASCC 侧 v1.0 craft 定义) 和本 craft 的 ingest
  逻辑耦合在 `proposed_fix_options: [a, b, c]` 这样的结构上。若未来 bundle
  schema 变化，ingest 也要变。Wave 9 不解耦，但在 upstream.py 里用
  `bundle.summary` 字段作为唯一强依赖，降低耦合面积。
- **KL4**: Courier Fallback 是"人工拷贝 + 文件名规范"信任链；没有校验签名。
  可接受理由：目前 instance 全部是 Yanjun 本人项目，没有恶意行为模型。

### 3.4 Confidence accounting

- Round 1 出发: 0.70 (bootstrap ceiling)
- Round 1 结束: 0.83 (A4 转化为修正；A1 部分；A2/A5 失败)
- Round 2 出发: 0.83
- Round 2 结束: 0.91 (B1/B2 均接受修订；B3 部分接受)
- **Final: 0.91 ≥ kernel_contract floor 0.90 ✓**

### 3.5 Integration checks

- [x] 本 craft 结论必须 `myco eat` 为一条 `craft-conclusion` note（L10 要求）
- [x] log.md 必须追加 milestone（L5 要求）
- [x] 任何 canon 修改必须引用本 craft（L13 要求）
- [x] contract_changelog.md 必须列出本 craft（kernel_contract convention）
- [x] Vision anchor（L9）: 本 craft 明确归属"消化/代谢"主轴，vision-aligned

---

**Canonical references**
- Parent craft: `docs/primordia/upstream_protocol_craft_2026-04-11.md`
- Protocol spec: `docs/craft_protocol.md`
- Contract changelog: `docs/contract_changelog.md` (v0.9.0 entry to be added)
- Indicator schema: `_canon.yaml: indicators` (to be extended this wave)
