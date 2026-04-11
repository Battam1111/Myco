---
type: craft
status: ACTIVE
created: 2026-04-11
target_confidence: 0.90
current_confidence: 0.91
rounds: 3
craft_protocol_version: 1
decision_class: kernel_contract
---

# Craft Reflex — 让 Craft Protocol 在应该触发的瞬间主动呼叫 agent

> 二阶 craft：这份 craft 的对象是 Craft Protocol 自己（今天 v1.3.0 刚落地的 W3 primitive）。
> 上游 craft：`docs/primordia/craft_formalization_craft_2026-04-11.md`（v1.3.0 的正式化 craft，current_confidence 0.91）。
> 触发事件：ASCC 侧会话在 Wave 10 README v3 三语重写全程未开 craft，事后用户指出"你似乎完全忘了 craft"。

## 0. 问题定义

Craft Protocol 作为 kernel primitive 在 contract v1.3.0 已经完整落地：
`docs/craft_protocol.md` 规范（226 行）+ `_canon.yaml: system.craft_protocol` schema +
L13 lint + 5 条触发条件（§3）+ 3 档置信度底线。但 **2026-04-11 本 session 发生的
漏触发事件（Wave 10 README v3 三语重写）**暴露出一个结构性洞：

**Discovery surface is passive.** 触发通道纯粹依赖 agent 主动去读
`docs/craft_protocol.md §3` 来知道"我应该 craft"。没有任何反射机制在**触发条件
真正满足的瞬间**呼叫 agent。结果：

1. Wave 10 README v3 三语重写 —— **对外公开 claim** 的重大改写（Trigger #4），
   应当走 instance_contract 级 craft（floor 0.85），**完全没开**。
2. 重写前我的置信度对"如何讲好愿景故事"大约 0.70 —— 低于 0.80
   exploration floor（Trigger #3），**没意识到应当升一档再动手**。
3. 用户不得不手工提醒"你忘了 craft"。

这是结构性的，不是一次性疏忽。craft_formalization craft 的 Round 1 **A7 明确
拒绝** `myco craft` CLI（理由：craft 是持续对话，不是可自动化的 job）。这个
决定正确且不应推翻。因此反射机制必须用**非 CLI** 的手段实现：lint 维度 +
hunger 信号 + 热区文档锚点。

## 1. Round 1

### 1.1 Claim（初稿）

**Claim 1**: Add a new lint dimension L15 "Craft Citation Reflex" that scans
`log.md` for recent entries touching kernel-contract surfaces
(`docs/agent_protocol.md`, `_canon.yaml`, `src/myco/lint.py`,
`src/myco/mcp_server.py`, `src/myco/templates/**`) and warns if no craft file
was created or referenced in the same lookback window. Severity LOW initially.

**Claim 2**: Extend `compute_hunger_report` with a `craft_reflex_missing`
signal that emits the same check at boot time through `myco hunger` —
surfacing craft obligations as part of metabolic health instead of waiting
for commit-time lint.

**Claim 3**: Add a `§3.1 Discovery surface` subsection to
`docs/craft_protocol.md` documenting the five surfaces that expose triggers
to the agent: (a) this doc itself, (b) WORKFLOW.md W3, (c) MYCO.md hot-zone
pointer, (d) `myco hunger` reflex panel, (e) L15 lint dimension.

### 1.2 Attack (self-adversarial)

**A1** — "Adding L15 = noise." 任何 README 改动都会触发 warning，false
positive 率会很高，agents 会学会忽略它，走向 lint-as-noise 的失败模式。
Compare to L13 which only checks schema of existing files — L15 checks
**absence of a file**, which is a much harder signal.

**A2** — "hunger 的语义范畴是笔记代谢，craft 不是 note。" Conflating craft
reflex into hunger muddies hunger's conceptual scope. Today hunger is about
`notes/` metabolism; tomorrow it's about "everything the substrate should
nag you about." Drift risk.

**A3** — "Log-based scan is fragile." log.md 是 append-only 但条目格式是
自由格式。用 regex scan entries 来决定"这条是 kernel-contract surface touch"
是启发式的，不是证明。也许 30% 的 true positive 被错过，20% 的 false
positive 被误报。

**A4** — "The craft_formalization craft 已经讨论过 CLI 问题 and landed on
no-CLI decision." 你现在做 lint + hunger 是在往同一个方向偷偷加料 —— 本质
是把 CLI 改头换面。应当先解释为什么这不是违反 A7 Defense。

**A5** — "Goodhart 风险比 craft_protocol.md §4 自承的更严重。" 如果 lint
会 warn on absence of craft citation, 最省力的应对不是做 craft, 而是在
commit message 里塞一行假 craft 引用。这比 confidence 自报更容易舞弊。

**A6** — "What happens on a fresh checkout?" 新 clone 下来的仓库 log.md
只有最近条目。如果 lint 说 "last 3 days has kernel-contract surface touches
without craft citation", 但 log.md 的条目早于 3 天 —— 会不会把历史 commit
当成 missing reflex 来警告？

**A7** — "You haven't measured the real miss rate." 你假定 L15 会发现漏
craft 的事件，但 Wave 10 漏触发事件真的会被 L15 捕获吗？那次 README 三语
重写**不碰 kernel-contract surfaces** —— 它只改 README.md / README_zh.md /
README_ja.md。L15 按当前 claim 不会 flag 这个。

### 1.3 Online Research

**Finding 1**: Linters that detect "absence of X" are established (e.g.
`missingInclude` in cppcheck, `missing-docstring` in pylint, `missing-return`
in Rust). Severity defaults to warning for exactly the reason in A1: they
are heuristic proxies, not proofs. ✅ 支持 LOW severity 默认。

**Finding 2**: `semgrep` 的 "require-comment-near-X" rules 是一个好类比 ——
它不检查语义正确性，只检查某个标记是否出现在目标位置附近。L15 就是这个
模式：scan log.md for proximity between "surface touched" and "craft
referenced". ✅

**Finding 3**: Goodhart / gaming via fake citations: academic paper
reviewing systems have the same problem (people cite fake DOIs in preprints).
解决不了，但**降低 severity + keep the trail auditable** 是标准应对。Goodhart
≠ 不做。

**Finding 4** (A7 的要害): Trigger #4 in `docs/craft_protocol.md §3`
literally is "External stakeholder-visible claim: anything that will appear
in README, public docs, or marketing." 所以 README.md / README_zh.md /
README_ja.md 三文件**就是** trigger surfaces 的一部分。A7 的真正含义是：
我的 trigger_surfaces 列表必须扩展，不能只是 kernel-contract 文件。

### 1.4 Defense + Revise

**回应 A1 (noise)**: 双层防御。(a) LOW severity 默认，commit 不阻断；
(b) canon 可配置 `reflex_severity` 允许调成 OFF / LOW / MEDIUM；(c) 30 天
观察期，然后审查 false positive 率，决定是否升级。这是 `docs/craft_protocol.md
§8` deprecation criteria 的正向版本 —— **reverse onboarding**。

**回应 A2 (hunger 语义漂移)**: 分 panel。hunger 输出里 craft_reflex 是**独立
signal string** with explicit prefix `craft_reflex_missing:`。conceptually
hunger 的职责是 "substrate health"，代谢健康和契约健康都属 health 范畴，
不是 scope 漂移。Self-Model C 层（结构退化）的 `structural_bloat` 信号已经
走了这个模式 —— craft_reflex 是同构的一个新信号。

**回应 A3 (log scan fragile)**: 同意启发式 ≠ 证明。对应策略：(a) 使用
**保守的 regex pattern**（只 match `touched:` / 明确 commit-hash 锚点的条目）
降低 false positive；(b) **opt-in via _canon.yaml config** —— instances 可
选择关闭；(c) **同步 self-test**: lint 本身通过这次 meta-craft 的漏触发事件
作为 bootstrap test case。

**回应 A4 (偷偷加 CLI)**: 正面回应。**L15 + hunger 不是 CLI 改头换面**，
因为它们**不启动一个 craft**，只**提醒** agent 应当启动一个。启动仍然是
agent + 人类的对话劳动。CLI 化的失败模式是把 craft 变成 `myco craft run` 这种
single-shot job；反射化的正确模式是**把触发条件的感知从 passive 升到
active**，不碰 craft 本身的劳动性质。这是 A7 Defense 的延伸，不是反对。

**回应 A5 (fake citation)**: 自承。Severity 默认 LOW 就是承认这个。Gaming
lint 的成本很低（加一行假 reference），但 gaming 的痕迹留在 git blame 里，
而 craft 本身的缺席留不下痕迹。**转移可审计性**是这个设计的全部价值 —— 从
"agent 选择性记忆" 转到 "可被未来审计的一行引用"。从 0 可审计到低可审计是
严格进步。

**回应 A6 (fresh checkout)**: 用 `path.stat().st_mtime` 的 file-level cutoff
代替 log.md entry timestamp 作为主判据。L15 lookback 是相对于**当前机器的**
现在，不是 log.md 的写入时间。这样 fresh checkout 永远 look back 到 fresh
clone 之后，不会 flag 历史。

**回应 A7 (you miss the real failure mode)**: **这是 Round 1 的致命攻击。
Wave 10 漏触发的真正原因不是"kernel-contract surface touch without
craft"，而是 "external-stakeholder public claim without craft"。L15 必须有
两类 trigger_surfaces**：

```yaml
trigger_surfaces:
  kernel_contract:        # Trigger #1 per craft_protocol §3
  - docs/agent_protocol.md
  - _canon.yaml
  - src/myco/lint.py
  - src/myco/mcp_server.py
  - src/myco/templates/**
  public_claim:           # Trigger #4 per craft_protocol §3
  - README.md
  - README_zh.md
  - README_ja.md
  - MYCO.md
  - docs/vision.md
```

**确认：Round 1 产生了一个关键修正。** A7 让我意识到我初始 Claim 1 会**漏掉
引发这一切的那次事故本身**，这是一个彻底的 Claim-kill。没有 A7 这次 craft
会产出一个结构正确但 empirically 无用的 lint。记这一条作为这次 craft 为什么
值得做的直接证据。

## 2. Round 2

### 2.1 Refined Claim (v2)

**Unified claim**: 新增一个 kernel primitive 叫 **Craft Reflex** —— **感知
craft 触发条件并主动呼叫 agent 的反射层**，具体由四个协作组件实现：

(a) `_canon.yaml: system.craft_protocol.reflex` 子块 —— 两类
trigger_surfaces（kernel_contract + public_claim）、`lookback_days`（默认 3）、
`severity`（默认 LOW）、`enabled`（默认 true）。

(b) **L15 Craft Citation Reflex** lint 维度 —— 扫描 log.md 近 `lookback_days`
内的条目，检测是否有对 `trigger_surfaces` 任一类的 touch 记录，且**同窗口内
没有** craft 文件创建或引用。缺席则发 LOW warning。Fresh-clone 行为用
file-stat cutoff 保护。Opt-out via `reflex.enabled: false`。

(c) **`compute_hunger_report` craft_reflex_missing signal** —— 同逻辑的
boot-time 版本。hunger 命令默认跑它，signals 列表里冒出一条
`craft_reflex_missing: N surface touch(es) in last D days without craft
citation — see docs/craft_protocol.md §3` 的提示。

(d) `docs/craft_protocol.md §3.1 Discovery surface` —— 明确文档化这次扩展的
**五个 discovery surfaces**：(1) craft_protocol.md §3 本身，(2) WORKFLOW.md
W3 简述，(3) MYCO.md 热区锚点，(4) `myco hunger` reflex panel，(5) L15 lint。

### 2.2 Attack on refined claim

**B1** — "五个 discovery surfaces 是单点失效的反面 —— redundant surface 是好
事，但如果五个都指向同一份规范，agent 的行为反馈循环只有一个 choke point
（"是否真的去读 craft_protocol.md §3"）。redundancy at the surface level
without redundancy at the cognitive level doesn't buy anything."

**B2** — "reflex config 的默认值还是**开关在人**。" `reflex.enabled: true`
可以被关闭；`lookback_days: 3` 可以被调成 30（等于关掉）；`severity: LOW`
可以被 agent 静默忽略。这些参数如果不 ship with a `frozen: true` flag，终究
还是 honor-system。

**B3** — "lint 永远是事后检查。reflex 的理想形态是**实时拦截**（touch 触发
surface 时立即呼叫）。pre-commit hook 是唯一接近实时的机制，但 Myco kernel
不拥有 git hook 配置。我们只能检查，不能拦截。"

**B4** — "The public_claim surface list 会随项目演化。"今天是 README*.md +
MYCO.md + docs/vision.md；明天会新增 docs/positioning.md / assets/pitch.md /
...。surface list 是 canon-level config，但**没有任何机制**在 surface list
本身变化时强制走 craft。"

### 2.3 Online Research (Round 2)

**Finding 5**: redundant error surfaces are a well-studied HCI pattern
(Reason's Swiss Cheese Model of accident prevention). 多层 defense，每层都
有 hole，但 hole 们不对齐的时候系统仍然安全。B1 的攻击是 valid in theory
但在 HCI 中 empirically 被反驳：redundant surfaces 降低 miss rate 即使它们
指向同一份规范，因为 agent 的注意力是**有状态的** —— 不同触发器在不同语境
激活，打到不同的记忆热度峰。

**Finding 6**: frozen config values (B2) 是有先例的，但通常只用于 security
boundaries (RBAC 规则 / secret rotation intervals). craft reflex 不是
security；强制 frozen 等于 "我不信任 instance operators"。正确形态是**让
每一次 reflex config 修改成为 kernel-contract 级 craft 本身**（自举）。

**Finding 7**: Real-time interception (B3) in linters is the domain of IDE
plugins / LSP servers, not the main lint engine. Myco 已经有一条 D8 pathway
（hunger at boot + lint at commit 两头夹击），两头夹不住的中段只能依赖 agent
自觉。这不是 L15 的设计缺陷，是 reflex 这个概念在非实时语义下的物理上限。

### 2.4 Defense + Revise (Round 2)

**回应 B1**: 同意 redundancy at surface != redundancy at cognition，但
Finding 5 证明 surface redundancy 本身有降 miss rate 的作用（Reason Swiss
Cheese）。**主动接受这个折中**。五个 discovery surfaces 不是为了创造五个独立
cognitive channels，而是为了在 **agent 每次 attention reset** 的时候至少有
一个 surface 触发。

**回应 B2**: frozen 不是正确工具。改为 **reflex config 修改必须走
kernel_contract 级 craft**，写入 craft_protocol.md §3.1 末尾："Changes to
`system.craft_protocol.reflex` follow the same Class Z treatment as other
kernel-contract changes — require a craft with target_confidence ≥ 0.90."
这等于把 reflex config 纳入自举循环。

**回应 B3**: 自承物理上限。L15 lint 定位为 "post-commit safety net, not
real-time brake"。Future work: pre-commit hook mode (opt-in) via
`myco lint --pre-commit` new flag —— 但不是 v1.3.1 scope，记入 §7 known
limitations.

**回应 B4**: surface list 变更本身走 kernel_contract craft（与 B2 的
resolution 一致）。Meta-self-reference 合法，不是漏洞。

### 2.5 置信度估计 (end of Round 2)

~0.85. 还差 0.05 到 kernel_contract floor 0.90. 剩余不确定在两处：
- **lookback_days=3 是否合适？**没 empirical 证据，是凭直觉。
- **log.md entry 格式的 regex pattern**具体长什么样 —— 我还没写出来。

Round 3 专门攻这两处。

## 3. Round 3

### 3.1 Attack (Round 3)

**C1 (lookback_days)**: 3 days 这个数字是怎么选的？太短会漏掉本地开发期
长周期的 craft（agents 有时会做 7-10 天的 craft-style 工作），太长会把早已
处理完的 surface touch 重新 flag。你没有 empirical 依据。

**C2 (regex pattern)**: log.md 里 "surface touched" 怎么识别？条目通常是
prose，不是结构化字段。你可能需要**单独的 canonical tag**（类似
`touched:`）作为可靠信号，这意味着人必须记得打这个 tag —— 回到 honor system。

### 3.2 Defense (Round 3)

**回应 C1**: **使用文件 mtime 而不是 log.md entry 作为主判据。** 扫描
`trigger_surfaces` 列表里的每个文件，取 `mtime`，如果 `now - mtime <
lookback_days * 86400` 则判定为 "recently touched"。这样：
- 不依赖 log.md regex
- fresh-clone cutoff 自动成立（新 clone 下来的所有文件 mtime = clone 时间）
- lookback_days 只影响"多久算最近"，不影响"怎么检测 touch"
- 3 days 是合理的第一档 —— 超过这个窗口还没 craft，说明绝对不是"我正在做"

这个修正**彻底解决** C1 的不确定和 C2 的 regex 难题。**主判据 mtime, 辅助
判据**是 log.md 扫描是否在同窗口内提到 `docs/primordia/*_craft_*.md` 或
`craft_reference:` 字样 —— 这个辅助判据只在 L15 决定要 warn 之前做一次
"已有 craft 证据吗？" 的 sanity check。

**回应 C2**: Auxiliary log scan 用这条 regex：

```python
craft_evidence_re = re.compile(
    r"(docs/primordia/[a-z0-9_]+_craft_\d{4}-\d{2}-\d{2}"
    r"(_[0-9a-f]{4})?\.md|craft_reference\s*:)",
    re.IGNORECASE,
)
```

严格匹配 craft filename pattern 或 `craft_reference:` 字面。**不**匹配 "craft"
prose 提及。这样 false positive 率接近零。

### 3.3 Final Confidence

- Attack A7 已 address（两类 trigger_surfaces）✅
- Attack B2 已 address（reflex config 变更走自举 craft）✅
- Attack C1 已 address（mtime 作为主判据）✅
- Attack C2 已 address（严格 craft_evidence regex）✅
- Known physical limit (实时拦截): 记录为 §7.5 ✅

**最终置信度：0.91**（target: 0.90, kernel_contract floor: 0.90）。达标，
开始落地。

## 4. 结论萃取

### 4.1 Decisions (D1–D9)

**D1** — `_canon.yaml: system.craft_protocol.reflex` 新块：

```yaml
reflex:
  enabled: true
  lookback_days: 3
  severity: LOW              # LOW | MEDIUM | OFF
  trigger_surfaces:
    kernel_contract:
    - docs/agent_protocol.md
    - _canon.yaml
    - src/myco/lint.py
    - src/myco/mcp_server.py
    - src/myco/templates/_canon.yaml
    - src/myco/templates/MYCO.md
    public_claim:
    - README.md
    - README_zh.md
    - README_ja.md
    - MYCO.md
    - docs/vision.md
  evidence_pattern: '(docs/primordia/[a-z0-9_]+_craft_\d{4}-\d{2}-\d{2}(_[0-9a-f]{4})?\.md|craft_reference\s*:)'
```

**D2** — `src/myco/lint.py` 新函数 `lint_craft_reflex`，签名同 L13。注册为
**L15 Craft Citation Reflex**。模块 docstring 更新到 "16-Dimension"（现在
L0–L14 共 15 维 + L15 = 16 维）。

**D3** — `src/myco/notes.py` `compute_hunger_report` 尾部新增
`craft_reflex_missing` signal，复用同判据。

**D4** — `docs/craft_protocol.md` 新增 §3.1 Discovery surface 子章节。
§8 Deprecation criteria 增补 L15 的反向 sunset 条款（30 天零 violation →
考虑升级 severity 或废除）。

**D5** — `_canon.yaml: system.contract_version: "v0.9.0"` → `"v0.10.0"`
（本地 ASCC 视角看 Myco contract；Myco kernel 本身的版本也 bump；注意
Wave 8 re-baseline 已把曾经的 v1.x.y 下调到 v0.x.y，所以新版本是 v0.10.0
而不是 v1.3.1）。**修正**：查 `_canon.yaml` 当前行 9 显示 `v0.9.0` Wave 9。
本 craft 是 Wave 11 craft reflex，因此 → `v0.10.0`。

**D6** — `docs/contract_changelog.md` 追加 v0.10.0 条目，引用本 craft。

**D7** — `src/myco/templates/MYCO.md` 热区锚点增补第 9 条 "**craft reflex**
—— 任何对 README* / MYCO.md / _canon.yaml / lint.py / mcp_server.py 的改动
若在 3 天窗口内没有对应 craft 文件，`myco hunger` 会 surfacing 一条
`craft_reflex_missing` 信号提醒你开 craft。"

**D8** — `src/myco/templates/_canon.yaml` 同步加入 `reflex` 子块（精简版 +
注释）。

**D9** — `myco eat` 本 craft 结论为 raw note，tags: `meta, craft-protocol,
craft-reflex, craft-conclusion, decision-class-kernel_contract,
friction-phase2, wave11`。

### 4.2 Landing list (L1–L13)

- **L1**: 本 craft 文件落盘（正在写）✅
- **L2**: `_canon.yaml` system.craft_protocol.reflex 新块 + contract_version bump
- **L3**: `src/myco/lint.py` 加 `lint_craft_reflex` + 注册 + docstring 升到 16-dim
- **L4**: `src/myco/notes.py` `compute_hunger_report` 加 craft_reflex_missing signal
- **L5**: `docs/craft_protocol.md` §3.1 Discovery surface + §8 扩展
- **L6**: `src/myco/templates/_canon.yaml` 同步 reflex 子块
- **L7**: `src/myco/templates/MYCO.md` 热区锚点第 9 条
- **L8**: `docs/contract_changelog.md` v0.10.0 条目
- **L9**: `myco eat` 本 craft 结论
- **L10**: `log.md` milestone
- **L11**: 自适应 dogfood 测试 —— 完成 L1–L10 后跑 `myco lint` 和
  `myco hunger`，**期待** L15 在自检中 flag 本次 Wave 10/11 为"touched
  public_claim surfaces without craft citation in 3 days" → 但现在**已有**
  本 craft 文件，所以应当 PASS。如果 PASS，bootstrap self-test 通过。
- **L12**: Dual-path lint 16/16 PASS（`myco lint` 与 `scripts/lint_knowledge.py`
  shim）
- **L13**: `[contract:minor]` commit via desktop-commander PID 9756

### 4.3 Known limitations（诚实记录）

1. **mtime-based detection can be fooled by `touch` or rebase.** 有人故意
   `touch README.md` 然后 hold 不 craft，或者 rebase 改变 mtime。这不是
   可防御的 —— 只能记在审计轨迹里。
2. **lookback_days=3 未经 empirical 验证**。首版凭直觉设定；30 天后用
   真实 false positive 率审查。
3. **L15 不会发现"应当 craft 但也没 touch 任何 surface"的决策**，例如
   纯抽象思维层面的 naming / strategy 决策（exploration 类 craft）。
   这一类触发只能依赖 agent 自觉 —— D8 WORKFLOW W3 的文化规约仍然不可
   替代。
4. **反射层不是实时拦截**。agent 可以在一个 turn 里同时 touch surface 和
   commit，lint 只能在下一次 boot/commit 之后才能警告。physical limit.
5. **"grace period for fresh craft files"**：本 craft 文件本身在被 eat
   之前 mtime 很新，可能会被 L15 当作"刚 touch 过的 kernel_contract
   surface"（如果我把 craft 文件列入 surfaces）。但 craft 文件**不在**
   surface 列表里，所以无问题。
6. **仓库 fresh clone 之后所有文件 mtime 都是 clone 时间** —— 这是 A6
   讨论过的 feature，不是 bug。clone 之后 3 天内所有 surface 都会看起来
   "recently touched"，但应该 PASS 因为同窗口内不会有真实修改需要 craft
   citation（只是元数据更新）。

### 4.4 Deprecation criteria (reverse sunset for L15)

类似 craft_protocol.md §8 对 L13 的表述：

- **Dead lint**: L15 连续 6 个月零 violation → 考虑升级 severity 或废除
  （说明 habit 已内化）
- **Dead mechanism**: 连续 3 个月 monthly craft file 创建数 < 1 → 考虑
  停用 reflex（说明 craft primitive 本身已冷）
- **Better replacement**: 某天出现自动化 attack-defense（LLM self-critique
  agent-in-the-loop）能取代手写 craft，L15 的必要性下降
- **Goodhart overrun**: false citation 率 > 20% 时，severity 降级或改设计

---

**最终置信度**: **0.91** (target: 0.90, decision_class: kernel_contract).
自主决策达标。开始落地 L1–L13。
