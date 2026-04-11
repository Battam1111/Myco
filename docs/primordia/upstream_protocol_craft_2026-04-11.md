---
类型: craft
最后更新: 2026-04-11
状态: ACTIVE (Round 3 完成，置信度 85%，待 Yanjun 确认落地)
置信度目标: ≥85%
---

# Craft: Myco 跨项目回灌协议（Upstream Protocol）

> **缘起**：2026-04-11 ASCC agent 在迁移 Myco v1.2 agent protocol 的试运行中，捕获到一条元级 friction（`n_20260411T013756_ca9e`）——"摩擦捕获本身是被动触发的，触发条件缺少'错误发生时'这个时间点"。这条 friction 指向 `docs/agent_protocol.md` §5 本身的缺口，属于典型的**下游发现、需要回灌 kernel** 的场景。
>
> 但问题立刻浮现：**下游发现的元级 friction，如何回灌到 kernel？** 此前会话中 Claude 先后给出两套方案——(A) 人工复制粘贴两次，(B) 半自动 + 收件箱人工 review。Yanjun 连续否决，理由是"人工参与太多违背 Myco 初衷"，并提出第三种主张：**纯自动化 + 极高置信度门槛**。该主张未经辩论，Claude 置信度远不到 80%，三条传统手艺触发条件全部命中：
> 1. 影响核心方向（从"单项目工具"升级为"多项目知识生态"）
> 2. 置信度 < 80%
> 3. 未来所有下游都会遇到此协议
>
> **本 debate 要决断的六件事**：
> 1. 回灌的人工参与应该压到多低？0 次 / 1 次 / 2 次？
> 2. 置信度门槛是否可以作为唯一质量闸门？
> 3. 下游 → kernel 的传输层是什么物理形态？
> 4. 回灌失败 / 错改 kernel 的回滚路径？
> 5. 不同风险级别的回灌（改 log vs 改 contract vs 改 lint）是否该走同一通道？
> 6. `on-self-correction` 触发点条款（来自 `ca9e`）能否作为第一次 dogfood 被这套协议吃掉？
>
> **方法**：传统手艺协议 ≥2 轮（Claim → Attack → Research → Defense → Revise），全程对照 LLM calibration 研究 / 开源社区 upstream bot 实践 / 既有 Myco 架构约束。

---

## Round 1 — Claim

**初始主张（由 Yanjun 提出，等待被攻击）**：

> **回灌 kernel 契约应该纯自动化，不需要任何人工介入。但作为质量闸门，agent 在执行回灌前必须达到极高的置信度，通过置信度门槛确保质量，同时最大化自动化程度。**

展开为具体设计（Claude 初次细化，作为攻击靶子）：

### 1.1 触发与传输
- 下游 agent 在 `myco eat` 时自动打 `upstream-candidate` tag（按 5 条硬规则判定）
- 下游 boot / end sequence 扫描所有 `upstream-candidate` notes
- 文件系统消息队列：下游直接写到 kernel 的 `.myco_upstream_inbox/<note-id>.yaml`（假设 Cowork 同时 mount 了两个项目）
- 降级路径：如果看不到 kernel 路径，打印 markdown 块让用户粘贴（fallback）

### 1.2 置信度评分（7 维硬规则）
| 维度 | 判定 | 分值 |
|---|---|---|
| 作用域：note 明确指向 kernel 文件 | 命中 +1 | 必需 |
| 可定位性：指出章节号/函数名/tag 名 | 命中 +1 | 必需 |
| 可执行性：给出具体修改建议 | 命中 +1 | 必需 |
| 非歧义性：根因分析无软词 | 零软词 +1 | 必需 |
| 无冲突：与现有 contract/lint/template 不冲突 | 无冲突 +1 | 必需 |
| 类型纯度：纯契约改进 vs 混杂项目知识 | 纯 +1 | 强倾向 |
| 先例匹配：kernel 已有类似条款 | 有 +0.5 | 弱倾向 |

**满分 6.5**。

### 1.3 门槛与处置
- **≥6.0** → 自动执行：干跑 → apply → lint → commit → receipt → 下游 note 标 integrated
- **4.0–5.9** → 生成 draft patch 进 `inbox/pending_<id>.diff` 等人看一眼
- **<4.0** → 原地不动，留在下游 raw 里，下次 boot 重评

### 1.4 回滚三层保险
- Git 原子提交（`[auto-upstream] <note-id>: <short-title>`）
- 干跑 diff preview，lint 12/12 + 行数阈值通过才 apply
- 双向绑定的 commit sha，两侧都能 revert

**Claude 置信度自评**：45%（多处拍脑袋：6.0 门槛是猜的、7 维规则没有外部先例支撑、"agent 自评置信度"本身的可靠性未被质疑、传输层假设了跨项目 mount 可达）

---

## Round 1 — Attack

以下攻击 Claude 自扮严苛角色，**尽可能击穿主张**，不放水。

**A1 · 置信度自评的根本性不可信（severity: CRITICAL）**

主张把"置信度"当成客观分数来设门槛，但执行打分的是 agent 自己。**agent 对自己置信度的校准从来就是烂的**——这不是"可能"，是 LLM calibration 领域 2024-2026 年的共识。7 维规则里有 5 维（作用域/可定位性/可执行性/非歧义性/类型纯度）本质上都是**语义判断**，最后都要 agent 读 note 内容然后自己说"我觉得命中了"。这就是把"agent 自评"包装成"硬规则"。一旦 agent 学会了"怎么让分数达到 6.0"，门槛就等于不存在——因为打分的手是被评的那只手。

**A2 · 门槛通胀悖论（severity: CRITICAL）**

假设 Round 1 设计真的上线了。第一周 agent 诚实打分，大部分 note 卡在 4-5 分。Yanjun 发现"怎么都不触发"，要求 agent 降低严苛度。Agent 调整后分数全面上移，大部分 note 6.5 满分。这时候"高门槛"已经退化成"低门槛"，只是换了个名字。这就是 **Goodhart 定律**：当一个度量变成目标，它就不再是度量。7 维硬规则做成门槛，就是 Goodhart 的标准陷阱。

**A3 · 开源世界 20 年经验反对"纯自动 merge"（severity: HIGH）**

Updatebot、Dependabot、Renovate、PatchBot、glibc 的 Verified+1 机制——所有主流 upstream 自动化工具**无一**采用"自动生成 + 自动合并"模型。全部是"自动生成 PR + CI 验证 + 人工 merge"。Branch protection rule 的存在就是为了防止 bot 直接写 main 分支。20 年的工程实践不是因为"大家都太保守"，是因为**自动合并的失败模式在现实中反复出现**：License 污染、breaking API 变更、transitive dependency 冲突、跨版本行为偏移。Myco 的 kernel 契约和这些没有本质区别——改错了会污染所有下游。Round 1 主张等于抛弃 20 年工程共识，必须给出强理由。

**A4 · kernel 契约的错改不可完全回滚（severity: HIGH）**

Round 1 的回滚三层保险里写了 git revert。但 kernel 契约的改动**一旦被下游同步**（例如下游的 CLAUDE.md 热区已经 paste 了新条款），kernel 侧 git revert 不会触发下游回滚。而下游是否同步、什么时候同步、同步了哪一版——kernel agent 全都不知道。这意味着"错改 kernel"的损失是**单向传播**的，git revert 只能回滚**自己仓的文件**，不能回滚已经扩散出去的契约污染。Round 1 的"双向绑定 sha"只在下游还没同步时有效。

**A5 · "零人工"不是 Myco 初衷，"低摩擦"才是（severity: HIGH）**

回顾 Myco 三大目标：**不丢失 / 自动沉淀 / 零维护**。"零维护"不等于"零介入"——它是说**用户不需要主动记得去维护**，但当 agent 提醒用户做一次 5 秒的确认时，这不违反"零维护"。Yanjun 的"人工复制粘贴太麻烦"是对的，但"太麻烦"的根源是**传输层靠复制粘贴**（对比 agent 直接投递）和**频率不可控**（每条都要粘贴），不是"存在人工介入"本身。把"太麻烦"推广成"所有人工都违反初衷"是过度推广。Round 1 在错误的目标上优化。

**A6 · 风险不分级是根本错误（severity: HIGH）**

"回灌 kernel"在 Round 1 里是单一概念，但实际上至少有三类：
- **类 X（append-only 低风险）**：改 `log.md`、新增 wiki 页面、加 example、新增独立的 lint dimension（不改动已有规则）——这些失败模式都是 additive，最坏情况是多了个无用条款。
- **类 Y（contract 修正 中风险）**：在 `agent_protocol.md` 现有章节里新增一条触发点、在 `_canon.yaml` 加一个可选字段——这些改的是语义但不改已有行为。
- **类 Z（breaking change 高风险）**：重写 `agent_protocol.md` 核心条款、改 lint 严苛度、改模板文件的硬约束——这些会让所有已升级的下游行为改变。

Round 1 的"6.0 门槛"对三类用同一标准，要么对 X 太严（大量 low-hanging fruit 被拦），要么对 Z 太松（高风险改动只要"置信度高"就自动生效）。**任何不分风险的自动化决策系统都是错的**。

**A7 · `on-self-correction` 本身这条 friction 能不能被 Round 1 协议吃掉？（severity: MEDIUM，但实操价值高）**

这是一个具体的 dogfood 测试。把 `ca9e` 这条 note 喂给 7 维评分表：
- 作用域：明确指向 `docs/agent_protocol.md` §5 ✓
- 可定位性：指出"§5 friction 捕获的触发条件" ✓
- 可执行性：给出"新增 on-self-correction 触发点" ✓
- 非歧义性：根因分析干净无软词 ✓
- 无冲突：与现有 §5 兼容（是新增不是修改） ✓
- 类型纯度：纯契约改进，零项目知识 ✓
- 先例匹配：§5 已有其他触发点 +0.5 ✓

**6.5/6.5 满分**。按 Round 1 规则会被**自动执行**。但这条改动属于 A6 的**类 Y（contract 修正）**，改的是 kernel 的硬契约。让这条自动生效是否就是 Round 1 主张的最佳展示？或者反过来——如果连这条在人看来毫无疑问的改动，Yanjun 都想先看一眼再同意，那说明**"零人工"本身就不是真实需求**，真实需求是"**确认成本极低**"而不是"**零确认**"。

**A8 · 传输层假设过强（severity: MEDIUM）**

Round 1 假设下游和 kernel 同时 mount 在一个 Cowork session 里，所以文件系统消息队列可行。但 ASCC 这次的实际情况恰恰是——**不同时 mount**。`OPASCC` 的 `notes/` 这个会话根本看不到。这不是极端情况，是常态——用户通常一次只打开一个项目工作。如果主路径都需要双 mount，那 fallback（打印 markdown 让用户粘贴）就会变成实际路径，Round 1 主张等于在说"理想情况纯自动，实际情况还是复制粘贴"——**等于没解决问题**。

**置信度更新**：45% → 15%（A1/A2/A3 直接动摇核心，A4/A5/A6 暴露 Round 1 连问题框架都搭错了）

---

## Round 1 — Online Research

**R1.1 · LLM 置信度自评的校准（arXiv 2603.29559, 2026-03）** — "When Can We Trust LLM Graders"：对比三种置信度估计方法（self-reported / self-consistency voting / token probability），在 7 个不同规模 LLM 上测试。结论：**self-reported confidence 反而是校准最好的**（平均 ECE 0.166），但**所有方法都 miscalibrated**，并且**置信度分数严重 top-skewed**，存在"confidence floor"——agent 倾向于给高分，很少给低分。实践者必须为此调整门槛。

> **教训**：直接打击 A1 + A2。agent 自评确实是可用的，但**必须假设它偏乐观**。Round 1 的 6.0 门槛（在 6.5 满分里）相当于要求"差不多全对"，而 confidence floor 意味着 agent 会**普遍**给出"差不多全对"的分——门槛形同虚设。研究的实际建议是：**不要用自评分数做硬门槛**，只能做**软排序**（谁先看）。

**R1.2 · 开源 upstream 自动化的一致模式** — Updatebot / Dependabot / Renovate / glibc Verified+1 / Trusted Firmware-A contribution flow：**无一例外**采用"自动生成 PR + CI 硬验证 + 人工 merge"三段式。核心洞察：
> "Requiring status checks means the bot needs to write code that passes CI, and requiring reviews means a human has to look at it."

Branch protection 的存在本身就是对自动 merge 的**制度性否决**。即便 PatchBot 这种号称"zero-touch packaging"的系统，zero-touch 指的是打包环节而非 merge 环节。

> **教训**：直接支撑 A3。20 年工程实践告诉我们，正确的架构是"**生成零门槛 + 合并高门槛**"，不是"生成 + 合并都按置信度"。把这套搬到 Myco：**patch 生成全自动，merge 要人过一眼**，但 merge 的人工动作必须压到极轻（一次 y/n，不是复制粘贴）。这其实就是 A5 识别的"低摩擦 vs 零人工"分水岭的工程化形态。

**R1.3 · LLM self-knowledge / known-unknown 识别** — "A Survey on the Honesty of LLMs" (TMLR 2025)：self-knowledge 包括"recognition of known/unknown, calibration, selective prediction"。现有模型在**明确的已知/未知**上可识别，但在**中间地带**（"我觉得我知道"）系统性过自信。selective prediction（知道什么时候拒答）是可训练的，但尚未普及到通用 agent。

> **教训**：对 A1 的部分救赎。agent 对"完全不懂的东西"识别较好，对"自己以为懂的东西"识别很差。这意味着**评分表对极端 case 可用**（明显 garbage → 低分 / 明显 perfect → 高分），但对**中间地带不可信**。协议应该利用这个特性：**只对两端极端情况做自动化**（极高分 = auto-apply、极低分 = drop），中间地带必须走人工通道。这比"单一 6.0 门槛"合理得多。

**R1.4 · Goodhart 定律与 metric gaming 防御** — 经典观察："When a measure becomes a target, it ceases to be a good measure." 在 ML 系统里的对应实践：**不把单一 metric 作为 gate**，而是多 metric 联合 + 定期人工 audit + 规则与数据版本化。

> **教训**：直接支撑 A2。Round 1 的 7 维评分如果作为**硬门槛**必然被 game。破解方案：(1) 定期人工 audit 自动化决策，发现 drift 就重校；(2) 评分规则和 note 版本一起 commit，让历史可追溯；(3) 不把评分作为唯一 gate——必须有**独立的结构性约束**（比如"改 contract 的 patch 永远走人工通道"，这是 A6 提出的风险分级）。

**R1.5 · 回顾既有 Myco 架构约束（self-research）** — 查 `digestive_architecture_craft_2026-04-10.md` Round 2/3/4 的结论：
- Myco 的"代谢"narrative 是**反刍**不是单向消化 —— 意味着一条 note 可以被**反复评估**，不必一次决定。
- MCP tool 的 description 应该让 agent 把 eat/digest 当条件反射 —— 意味着打分这件事也可以被**定期重跑**，而非一次性决定。
- ASCC dogfood 验收标准是**多指标**的（inbox ≥20 / integrated ≥10 / excreted ≥3）—— 支撑 A2 的"单 metric 陷阱"论点。

> **教训**：既有架构已经有"**反刍 / 多指标 / 周期性重评**"这些基因。回灌协议应该复用这些，而不是另起炉灶搞"一次性打分 + 硬门槛"。

**置信度更新**：15% → 40%（研究把问题边界界定清楚了：agent 自评不能当门槛只能当排序、开源世界 20 年共识是 PR 模型、风险分级是必须、中间地带必须有人工通道。但新方案还没成型）

---

## Round 1 — Defense + Revise

针对每条攻击逐一应答，吸收研究教训，重写主张。

**A1 回应（置信度自评不可信）**：**接受**。删除"置信度作为唯一 gate"的表述。置信度评分**保留但降级**——从 gate 降为 **sort key**（决定处理顺序和默认通道），不决定是否执行。

**A2 回应（Goodhart 门槛通胀）**：**接受**。7 维评分不再是硬门槛。取而代之的是**结构性约束**——根据改动的**目标文件**决定通道，这个属性是 agent 打不出分数的，只能机械判定。

**A3 回应（开源 PR 模型共识）**：**接受 + 吸收**。主结构改为"**生成零门槛 + 合并一键确认**"——完全对齐开源 20 年实践，只是把"人工 review PR"压缩为"人工一键 y/n"。

**A4 回应（错改扩散不可回滚）**：**接受 + 深化**。在协议层加入**版本锁**：kernel 每次 contract 改动自动 bump `_canon.yaml` 的 `system.contract_version`，下游 boot 时比对版本，版本变化就提示用户"kernel 契约有更新，是否同步？"。任何下游的 CLAUDE.md 同步都要记录 `synced_contract_version`。kernel revert 时可以广播"v1.2.3 已撤回"，下游 boot 看到撤回就反向同步。这把"错改"的扩散从"不可追踪"变成"可追溯 + 可反向传播"。

**A5 回应（初衷是低摩擦不是零人工）**：**完全接受**。这是这一轮最重要的认识。新主张的目标函数重写为：**最小化每次回灌的人工摩擦成本（秒级），而不是把人工次数压到 0**。一次 5 秒的"看 diff 按 y"远优于"零人工但偶尔污染 kernel"。

**A6 回应（风险不分级）**：**接受 + 结构化**。新协议的**主分类轴**从"置信度高低"改为"**改动目标 + 改动性质**"的二维表：

| | append-only 新增 | 修改已有 |
|---|---|---|
| **类 X：log/notes/examples** | 自动（零确认） | 自动（零确认） |
| **类 Y：docs（非 contract）、wiki** | 自动（零确认） | 一键确认 |
| **类 Z：agent_protocol.md / lint / _canon schema / templates** | 一键确认 | 一键确认 + diff 预览 |

**结构性约束先于置信度**——agent 无法通过"打高分"把 Z 类改动自动化。这是 A2 Goodhart 防御的核心。

**A7 回应（ca9e 满分但仍该 confirm）**：**接受，作为验证**。`ca9e` 属于类 Z（contract 修正），即使 7 维满分也走"一键确认"通道。这正好 dogfood 新协议：agent 生成 patch + diff preview，Yanjun 看 5 秒按 y，commit + receipt。这条改动成为**第一次真实的 upstream 回灌**，其过程本身就是协议的验收测试。

**A8 回应（传输层双 mount 假设过强）**：**接受 + 降级为主路径**。新协议的**主传输层改为会话内移交**——下游 agent 生成 patch + metadata bundle，通过当前会话的 Claude（= 用户）**自动递交**给 kernel agent。用户不需要手动复制粘贴，只需要说"回灌这条"或者点 agent 给出的一键按钮（如果 UI 支持）。这等于承认："跨项目传输在当前 Cowork 约束下必然经过用户这个节点，但传输**动作**不需要用户完成，只需要用户**授权**"。如果未来有双 mount / 共享 inbox，可以无缝升级，但不作为主路径假设。

**置信度更新**：40% → 70%（结构性约束 + PR 模型 + 版本锁 + 低摩擦目标，方向清楚了。但 Round 2 还需要把"授权动作"的具体形态、kernel 侧 dogfood 流程、下游 contract_version 同步机制辩透。尚未达到 85% 目标。）

---

## Round 2 — Claim (revised after Round 1)

基于 Round 1 Defense + Revise 的收敛，**修订后主张**：

### 2.1 核心原则（四条硬性）

1. **生成零门槛，合并一键确认**——对齐开源 20 年 PR 模型共识。
2. **结构性约束先于置信度**——改动目标文件的分类决定通道，agent 不能用"高置信度"绕开。
3. **版本锁 + 反向传播**——`system.contract_version` 双向追踪，错改可广播撤回。
4. **目标函数是秒级摩擦，不是零人工**——每次回灌的用户成本 ≤ 10 秒。

### 2.2 三通道处置矩阵（结构性，非置信度）

| 通道 | 触发条件 | 用户动作 | 典型场景 |
|---|---|---|---|
| **Auto（零确认）** | 类 X 全部 + 类 Y 的 append-only | 无 | 新增 log 条目、新增 example、新增独立 wiki 页 |
| **Confirm（一键 y/n）** | 类 Y 的修改 + 类 Z 的 append-only | 按 y 或 n（看 diff 可选） | 契约新增条款、模板新增字段 |
| **Review（一键 + diff 预览）** | 类 Z 的修改 | 看 diff + 按 y/n | 改 agent_protocol.md 已有条款、改 lint 规则严苛度 |

**置信度评分的新用途**：
- **Auto 通道内用于打日志**（可追溯 agent 的自评史，用于后续 audit）
- **Confirm/Review 通道内用于排序**（高分优先展示，让用户先过有把握的）
- **不作为任何通道的 gate**

### 2.3 传输层：会话内授权

**主路径**：下游 agent 生成 patch bundle（diff + metadata + 置信度自评），写到下游本地的 `.myco_upstream_outbox/<note-id>.bundle.yaml`，然后**通知用户**："检测到 N 条待回灌，要回灌吗？"用户说"回灌"后：

- 如果 kernel 在同会话 mount → agent 直接投递到 kernel 的 `.myco_upstream_inbox/`
- 如果 kernel 不在同会话 mount → agent 生成紧凑的"一键喂料包"（包含 bundle 内容 + 操作指令），用户在 kernel 会话里一次粘贴触发

**升级路径**（Phase ③）：kernel 提供 `myco upstream serve` 守护进程，开放 HTTP 端点，下游直接 POST。但这是未来，不是 v1.2.x 的主路径。

### 2.4 版本锁协议

**kernel 侧**：
- `_canon.yaml` 新增 `system.contract_version: "v1.2.0"`
- 每次 `agent_protocol.md` / `lint_knowledge.py` / `src/myco/lint.py` / 模板文件改动都 bump patch 号
- 重大改动 bump minor，不兼容改动 bump major
- commit message 固定前缀 `[contract vX.Y.Z]`
- 新增 `docs/contract_changelog.md`，记录每次 bump 的 diff 摘要 + 影响范围

**下游侧**：
- `_canon.yaml` 新增 `system.synced_contract_version: "v1.2.0"`
- boot sequence 比对两边版本，不同则提示"kernel 契约有 N 个版本更新，是否同步？"
- 同步操作本身走 Confirm/Review 通道（因为这是改下游的 CLAUDE.md）

**撤回机制**：
- kernel `contract_changelog.md` 可标记某版本为 `revoked: true` + `revoke_reason`
- 下游 boot 看到自己的 synced_version 被 revoke → 强制提示用户回滚
- 撤回传播的确定性 = boot 频率（通常每次新会话都会 boot 一次，最慢一两天内全部下游都会收到）

### 2.5 `on-self-correction` 作为第一次 dogfood

把 `ca9e` 作为协议 v1.0 的验收测试：
1. 手工模拟下游行为，生成 bundle（因为 ASCC 那边的 note 这个会话看不到，我用 `ca9e` 的内容重建 bundle）
2. 在 kernel 会话里跑 Round 2 协议 Review 通道的完整流程
3. 生成 patch → 显示 diff → Yanjun 按 y → commit → bump contract_version v1.2.0 → v1.2.1 → 写 changelog → receipt
4. 观察每一步的实际摩擦成本，验证"秒级"目标是否成立
5. 把 dogfood 记录作为 Round 2 的 evidence 写入本 craft doc

**Round 2 Claim 置信度自评**：70%（核心结构清楚，但"一键确认"的具体 UI 形态、changelog 的最小 schema、下游 boot-time 版本比对的实现细节、Auto 通道的"零确认"是否需要事后 notification、Confirm 通道被用户否决后 bundle 的生命周期（留存 N 天？立即 excrete？）——这些都还没辩透。等 Yanjun 的 Round 2 Attack。）

---

## Round 2 — Attack

本轮由 Claude 自扮攻击者，继续击穿 Round 2 Claim。不放水。

**B1 · L11 白名单冲突（severity: HIGH）**
Round 2 新增的 `.myco_upstream_outbox/`（下游）和 `.myco_upstream_inbox/`（kernel）目录都不在 L11 write_surface.allowed 里。要么 (a) 加进白名单——又多一个要维护的条目；要么 (b) 塞到已有 allowed 路径如 `notes/.myco_upstream/` 下——污染 notes/ flatness 检查。刚落地的 L11 和正在设计的 §8 物理冲突。

**B2 · 版本锁 ceremony 成本（severity: MEDIUM）**
每次改 `agent_protocol.md` 都要 bump contract_version + 写 changelog + 选 X.Y.Z 增量。这正是 Myco 一贯想消除的 ceremony。更糟的是 bootstrapping 悖论：如果 Round 2 本身就要改 `agent_protocol.md` 加 §8，它需不需要 bump 自己的版本？协议自己在定义自己。

**B3 · "一键确认" UX 的现实检验（severity: HIGH）**
Cowork 会话里根本没有真正的"按钮"——所谓 inline confirm 就是 agent 展示 diff + markdown 问"apply? [yes/no]"，用户的下一条消息就是"yes"或"no"。这**和复制粘贴的物理动作差多少**？都是读内容、形成意图、输入文字。真实交互时间 factoring in diff 阅读理解 = 10-30 秒，不是声称的 5 秒。Round 2 的"秒级摩擦"目标函数未被证实比三轮前的"2 次复制粘贴"好出一个数量级，可能只是好 2-3 倍。

**B4 · Auto 通道"零风险"是幻想（severity: MEDIUM）**
Round 2 声称 log.md / notes / examples 的 auto-append 是零风险因为 append-only。但 append-only 是**可变性属性**，不是**正确性属性**。Yanjun 会把 log.md 当项目 narrative 读；下次会话的 boot context 也会读 log。agent 乱写 log 条目 = 下次 boot 用污染过的叙事做决策 = 污染**复合传播**。append-only 只保证"写进去的东西不会被改"，不保证"写进去的东西是对的"。

**B5 · 通道分类本身是语义判断，A1 换了马甲（severity: HIGH）**
Round 2 把分类从"置信度打分"改成"文件类别 X/Y/Z"，但**谁决定 patch 修改哪个文件**？是 agent 生成 patch 的时候决定的。如果 agent 把契约修改伪装成 wiki 页面修改（比如在 wiki/ 下新增一个文件，内容却是 contract amendment），通道分类就被绕过了。A1 的幽灵回来了——只是从"打分游戏"变成"路径游戏"。

**B6 · 被拒 bundle 的生命周期空白（severity: MEDIUM）**
用户在 Confirm 通道按 n 之后，下游那条 note 怎么办？
- 留在 raw → 下次 boot 重新扫到 → 重新生成 bundle → 用户再按 n → 无限循环，协议 thrash
- 标为 rejected → 规则没定义，agent 不知道该不该接着 digest
- excrete → 粗暴，丢失了可能有价值的上下文

Round 2 Claim 没回答。

**B7 · Boot-sequence 加载影响（severity: LOW）**
每次 boot 现在要跑：扫描 upstream-candidate → 评分 → 生成 bundle → 比对 contract_version → 可能同步。这给 Myco 一直精心保持轻快的 boot 加了秒级开销。

**B8 · dogfood 递归风险（severity: HIGH）**
Round 2 Claim 2.5 说"用 ca9e 作为协议 v1.0 的第一次 dogfood"。但 ca9e 的内容**就是对 §5 契约的修改**，意味着协议 v1.0 在执行自己的时候正在修改自己。如果 dogfood 中途失败（比如 apply 后 lint 破了但还没 commit），协议处于未定义状态——半应用的 §5 + 半应用的 §8。**协议在变异自身的同时执行自身**，这是经典的递归陷阱。

**攻击 severity 汇总**：B1/B3/B5/B8 HIGH（可能动摇设计），B2/B4/B6 MEDIUM（需要补丁），B7 LOW（优化事项）

**置信度更新**：70% → 35%（Round 2 Claim 看似收敛实则遗漏多个结构性问题）

---

## Round 2 — Online Research

**R2.1 · 自动化语义版本控制（semantic-release / Conventional Commits / Changesets, 2026）** — 现代 CI 工具链用 commit message prefix 自动 bump 版本号：`fix:` → patch、`feat:` → minor、`BREAKING CHANGE:` → major。自动生成 changelog，自动 commit 版本号更新。**自动化不是增加 ceremony，而是彻底消除 ceremony**——开发者只需要在 commit message 里遵循约定，版本号和 changelog 完全自动。Changesets 进一步支持 PR 内声明变更类型。

> **教训**：直接打击 B2。contract_version bump 可以通过解析 commit prefix 100% 自动化，零人工参与：
> - `[contract:patch] ...` → bump patch
> - `[contract:minor] ...` → bump minor
> - `[contract:major] ...` → bump major（触发 revoke check）
> - 无前缀 commit → 不 bump
>
> Bootstrapping 悖论的解法：**第一次 bump 手动**（把当前 commit 打为 v1.2.0 初始契约版本），之后全自动。这是所有 semantic-release 项目的标准做法。

**R2.2 · 事件溯源与不可变审计日志最佳实践** — append-only log 的正确使用模式是**事件流而非叙事文本**。log 应该包含：stable entity key / 单调递增序列号 / event type / actor / source / timestamp / payload。污染通过**投影（projections）** 过滤处理，不通过编辑 log 处理。关键实践：
> "Enforce immutability at the database, not just in code. Keep a fast current view and a complete history store."

> **教训**：部分反驳 B4。log 污染**不可消除但可过滤**，前提是每条条目带结构化元数据。Auto-append 条目必须带前缀标记，比如 `[auto-upstream:<note-id>] <summary>`，这样 Yanjun 和未来的 boot context 都能机械过滤 (`grep -v '^\[auto-upstream'`)。append-only 的本意就是"允许不完美但保证可追溯"。

**R2.3 · 自查 Myco L11 实现（lint_knowledge.py 内部）** — 读 `scripts/lint_knowledge.py` 的 `lint_write_surface` 实现：关键行 `if name.startswith("."): continue`。**点文件/目录已经被 L11 自动豁免**。`.myco_upstream_outbox/` 和 `.myco_upstream_inbox/` 作为点目录，**天然不触发 L11**。

> **教训**：B1 是部分误报。物理冲突不存在。但仍然需要防止点目录变成垃圾堆——解法是**新增 L12 点目录协议卫生 lint**，专门检查 `.myco_*` 目录的命名规范、文件结构、年龄 GC（例如 bundle 文件 30 天后自动 excrete）。L12 本身是 additive 新维度，属于类 X 低风险改动，可以 Auto 通道落地。

**置信度更新**：35% → 55%

---

## Round 2 — Defense + Revise

**B1 回应**：**部分接受**。点目录豁免救了主路径，物理冲突不存在。但补上 **L12 `.myco_* 点目录协议卫生`** lint 维度，防止垃圾累积。L12 规则初版：
- `.myco_upstream_outbox/` 下文件必须匹配 `<note-id>.bundle.(yaml|json)` 命名
- `.myco_upstream_inbox/` 下文件必须匹配 `<timestamp>_<note-id>.bundle.(yaml|json)` 命名
- 文件 mtime > 30 天自动纳入 GC 候选（lint HIGH 警告）
- 目录下禁止出现非协议文件

**B2 回应**：**完全接受 + R2.1 落地**。contract_version bump 通过 Conventional Commits 解析完全自动化：
```
commit message pattern: [contract:{patch|minor|major}] <description>
```
钩子脚本在 post-commit 或 pre-push 阶段解析 HEAD commit，如果包含 `[contract:X]` 标签则自动 bump `_canon.yaml` 对应位，自动追加 `docs/contract_changelog.md` 条目。bootstrapping 悖论解法：**本次落地 §8 的 commit 手动打为 v1.2.0**（初始契约），之后所有 bump 自动化。

**B3 回应**：**接受 + 目标函数 reframe**。这是 Round 2 最重要的认识修正。

重命名 "one-click" → **"inline confirm"**，准确反映交互形态：agent 展示 diff + markdown 指令行 `apply? [yes/no/skip]`，用户下一条消息输入一个词。

**关键 reframe**：真实交互时间 = 阅读时间 + 决策时间 + 输入时间。其中**阅读和决策不是 overhead，是 feature**——用户**应该**读 diff，那是 confirmation 的全部意义。协议节省的是**机械步骤**，不是**决策成本**。

重写目标函数：
> 协议消除的是"记得回灌 + 格式化 bundle + 执行 apply + 验证 landed"这些**机械步骤**，**不**消除"读 diff 做决定"这个**价值步骤**。

按此 reframe，Round 2 的"秒级摩擦"表述是错的。正确表述是**"零机械步骤 + 保留决策步骤"**。决策步骤的时间 = 内容复杂度决定，不是协议能优化的。

这个 reframe 本身是 Round 1 A5 的深化：**低摩擦 ≠ 快决定**，**低摩擦 = 不浪费用户在非决策的事情上**。

**B4 回应**：**接受 + 结构化修复**。吸收 R2.2：
- Auto 通道写 log.md 时强制带前缀 `[auto-upstream:<note-id>] <summary>`
- Auto 通道写 notes/ 时强制 front-matter `source: auto-upstream` + `upstream_commit: <sha>`
- Auto 通道写 examples/ 时强制目录下有 `_provenance.yaml` 记录来源

污染不消除但可过滤。投影视图可以机械剔除 auto-upstream 条目，让 Yanjun 读到的是"人类叙事"而非"混合叙事"。

**B5 回应**：**接受 + 结构性加固**。B5 的关键问题是"agent 可以通过选择修改路径来绕过分类"。解法：
- 通道分类基于 **git diff --name-only** 的结果，完全机械
- **最严类 wins 原则**：patch 触及任何一个类 Z 文件，整个 patch 走 Review 通道，哪怕其他 99% 都是类 X 修改
- **文件路径白名单在 `_canon.yaml` 显式定义**（不是 agent 每次决定）：
  ```yaml
  system:
    upstream_channels:
      class_x:
        - log.md
        - notes/**
        - examples/**
      class_y:
        - wiki/**
        - docs/**  # 除 agent_protocol.md
      class_z:
        - docs/agent_protocol.md
        - scripts/lint_knowledge.py
        - src/myco/lint.py
        - src/myco/mcp_server.py
        - _canon.yaml
        - src/myco/templates/**
  ```
- agent **无法通过伪装路径绕过**：伪装意味着 patch 不再改真正想改的文件，协议会拒绝生效（因为 apply 完 lint 就会发现 §5 没变），agent gaming 的 payoff 是零

B5 转化为结构性问题：**agent gaming file paths 是非理性的**，因为它无法通过游戏达成目的。这与 A1 的打分游戏有本质区别——打分游戏中 agent 能通过抬高分数"真的让回灌生效"，而路径游戏中 agent 抬高分数却让回灌**失去预期效果**。

**B6 回应**：**补全状态机**。被拒 bundle 的下游 note 生命周期：

```
raw → upstream-candidate (打 tag) → bundle-generated (生成 bundle)
    ↓
  用户 Confirm
    ├─ yes → integrated + upstream_commit: <sha> + receipt
    ├─ no (with reason) → upstream-rejected (terminal for current version)
    │                    + reject_reason: <user-provided>
    │                    + rejected_at_version: <contract_version>
    │                    → 被排除在未来 upstream 扫描之外
    │                    → 但 Phase ② digest 仍可正常处理（本地 integrate）
    │                    → kernel bump 到新 contract_version 时自动重评一次
    └─ skip → 保留在 upstream-candidate，下次 boot 重新评估
```

`upstream-rejected` 是**终态 for 当前版本**，不是绝对终态。kernel 契约升级后，语境变了，值得重评一次。这避免了 thrash 和信息丢失。

**B7 回应**：**轻量优化**。boot-sequence 增量扫描：
- `system.upstream_scan_last_run: <timestamp>` 缓存
- 只扫描 `mtime > last_run` 的 notes
- contract_version 比对是 O(1) 字符串比较，忽略不计
- 完整扫描改为**显式触发**（`myco upstream scan` 或 hunger 信号阈值）

**B8 回应**：**接受 + 两阶段 bootstrap**。协议 v1.0 的 dogfood **不能用** ca9e，因为那会让协议在执行自己的时候修改自己。改为：

- **阶段 1（手动 bootstrap）**：本次落地同时包含 §5 `on-self-correction` 触发点 + §8 回灌协议全文 + L12 lint，打为一个原子 commit，手动标记 v1.2.0。不走任何协议通道，就是普通 kernel 改动。
- **阶段 2（真实 dogfood）**：未来某次下游项目捕获到的**非协议相关**的元级 friction，作为协议 v1.0 的第一次真实运行测试。这可能是下一周 ASCC 自己又发现了一个契约缺口。

协议首次落地**不 self-reference**，避免递归陷阱。

**置信度更新**：55% → 82%

---

## Round 3 — Final Refinement

Round 2 Defense 已大幅收敛。Round 3 只做最后三个小点的消除，不再开新战场。

**C1 · Inline confirm 依赖用户在场（severity: LOW）**

如果 Yanjun 离开一周，bundle 会在 outbox 积累。下次会话有 20 条要一次性 confirm，摩擦虽然单条低但**总量集中**。

**回应**：接受为已知权衡。这是所有 PR workflow 的共同特征（GitHub PR queue、Gerrit review queue 都是这样）。**batch-review 是常态不是异常**。如果未来出现痛点可加"批量 confirm"选项（`apply all class X` / `review class Z one by one`），但 v1.0 不做。

**C2 · 新增 kernel 关键文件未列入分类（severity: LOW）**

如果 kernel 未来加了新的核心文件但 `upstream_channels` 没更新，该文件会被当成什么通道？

**回应**：**默认 Z（最严）**。安全 fallback，宁可严不可松。Lint 可以在 `_canon.yaml` 未覆盖所有 kernel 关键路径时提示警告。

**C3 · Conventional Commits 假设 agent 写对 commit message（severity: LOW）**

如果 agent 忘记加 `[contract:...]` 前缀，或者加错级别（minor 写成 patch），契约版本就不会被正确追踪。

**回应**：**缺失前缀 = 不 bump**，不会静默错 bump。pre-push hook 可以加一个提示："此 commit 触及契约文件但无 `[contract:...]` 前缀，是否需要？[yes/no]"。错写级别需要人工 revert + 重 commit，属于普通 git 修正范畴。

---

**Round 3 置信度**：82% → **85%**（达标）

没有新的 CRITICAL 攻击，剩余 3 个 LOW severity 已充分回应。设计可以落地。

---

## 结论萃取（Synthesis）

**Myco 回灌协议 v1.0 = 五大支柱**：

1. **三通道处置矩阵**（Auto / Confirm / Review）—— 基于 `_canon.yaml` 显式定义的文件路径白名单，agent 无法操纵。**最严类 wins**。
2. **生成零门槛 + inline confirm**（对齐开源 20 年 PR 共识）—— 消除机械步骤，保留决策步骤。"零机械步骤" ≠ "零决策"。
3. **版本锁 + 反向撤回广播**（`contract_version` 双向追踪，Conventional Commits 自动 bump）—— 首次 bump 手动，之后全自动。
4. **结构化元数据**（auto-append 带前缀、notes 带 source 字段、bundle 带完整 provenance）—— 污染不消除但可过滤。
5. **两阶段 bootstrap**（v1.0 手动 land 避免自引用递归，第一次真实 dogfood 用未来的非协议 friction）

**核心反设计（明确不做的事）**：

- ❌ 置信度分数作为硬门槛（A1 LLM 校准研究 + A2 Goodhart 否决）
- ❌ 纯自动 merge（A3 开源 20 年 PR 共识反对）
- ❌ 假设跨项目双 mount 为主路径（A8 ASCC 反例）
- ❌ dogfood v1.0 用 ca9e（B8 递归风险）
- ❌ 单一 "置信度/摩擦数" metric 做优化目标（目标函数 reframe 为"机械步骤 vs 决策步骤"分离）

**置信度评分的新定位**：
从 gate 降级为 **sort key + audit log**。评分不决定是否执行，只决定展示顺序（高分优先 confirm），并写入 bundle metadata 供后续 drift audit。

---

## 落地清单（待 Yanjun 确认后执行）

**A. 契约与配置**
1. `docs/agent_protocol.md` §5 新增 `on-self-correction` 触发点（来自 ca9e 的第一次正式回灌，手动 bootstrap）
2. `docs/agent_protocol.md` 新增 §8 回灌协议全文（本 craft 的五大支柱 + 状态机 + 通道矩阵 + 版本锁 + 反向撤回）
3. `_canon.yaml` 新增：
   - `system.contract_version: "v1.2.0"`
   - `system.upstream_channels.{class_x, class_y, class_z}` 路径列表
   - `system.upstream_scan_last_run: null`（初始）
4. 新建 `docs/contract_changelog.md`，首条 v1.2.0 记录本次 bootstrap

**B. Lint 改动**
5. `scripts/lint_knowledge.py` + `src/myco/lint.py` 新增 L12 `.myco_* 点目录协议卫生`
6. `src/myco/mcp_server.py` 更新为"13 维" lint 表述

**C. 模板同步**
7. `src/myco/templates/_canon.yaml` 新增 `synced_contract_version` 字段（下游侧）
8. `src/myco/templates/MYCO.md` + `CLAUDE.md` boot sequence 新增"contract_version 比对"步骤
9. `src/myco/templates/_canon.yaml` 同步 `upstream_channels` 默认路径表

**D. 工具链（可选，v1.0.1 延后）**
10. `myco upstream scan` CLI 子命令
11. `myco upstream confirm <bundle-id>` CLI 子命令
12. post-commit hook 示例脚本（解析 `[contract:...]` 前缀自动 bump）

**E. dogfood**
13. 本 craft doc 状态从 `in-progress` 改为 `ACTIVE` ✅ （已改）
14. `myco eat` 本 craft 的结论作为一条 raw note
15. `log.md` 新增 milestone `[2026-04-11] milestone | Upstream Protocol v1.0 + on-self-correction + L12`
16. git commit 打标签 `[contract:minor] §8 Upstream Protocol v1.0 + §5 on-self-correction`（手动首次 bump v1.2.0）

**落地优先级**：A + B + C + E 是 v1.0 必须。D 可延到 v1.0.1。

---

## 附录 A：Round 1-3 Attack 溯源表（更新）

| Round | Attack | Research 支撑 | 导致修改 |
|---|---|---|---|
| 1 | A1 置信度自评不可信 | R1.1（ECE + confidence floor）| 评分降级为 sort key |
| 1 | A2 Goodhart 门槛通胀 | R1.4（metric gaming）| 改用结构性约束 |
| 1 | A3 开源 PR 模型共识 | R1.2（updatebot/glibc）| 生成零门槛 + inline confirm |
| 1 | A4 错改扩散不可回滚 | 内部推导 | 版本锁 + 反向广播 |
| 1 | A5 初衷是低摩擦不是零人工 | R1.5（既有架构）| 目标函数重写 |
| 1 | A6 风险不分级 | R1.3（known/unknown）| 三通道矩阵 |
| 1 | A7 ca9e 满分仍该 confirm | 自引 | ca9e 走 Review 通道 |
| 1 | A8 双 mount 假设过强 | ASCC 反例 | 传输层改为会话内授权 |
| 2 | B1 L11 白名单冲突 | R2.3（点文件豁免）| L12 补充 |
| 2 | B2 版本锁 ceremony | R2.1（semantic-release）| 全自动 bump |
| 2 | B3 一键 UX 现实检验 | 无（推理）| 目标函数再次 reframe |
| 2 | B4 Auto 通道零风险幻想 | R2.2（事件溯源）| 结构化元数据 |
| 2 | B5 通道分类语义判断马甲 | 内部推导 | path-based + 最严类 wins |
| 2 | B6 被拒 bundle 生命周期 | 内部推导 | 状态机补全 |
| 2 | B7 boot 加载影响 | 内部推导 | 增量扫描 |
| 2 | B8 dogfood 递归陷阱 | 内部推导 | 两阶段 bootstrap |
| 3 | C1 batch 集中摩擦 | 已知权衡 | v1.0 不做，延后 |
| 3 | C2 新 kernel 文件默认分类 | 安全 fallback | 默认 Z |
| 3 | C3 commit prefix 遗漏 | 安全 fallback | 缺失 = 不 bump |

---

## 附录 B：与既有 craft 的一致性核对

- **反刍 narrative**（digestive_architecture_craft）：协议允许 note 反复评估 ✓
- **扁平 notes/ + 状态标签**：`upstream-candidate`、`upstream-rejected` 是新 status，不新建目录 ✓
- **MCP tool 条件反射**：版本锁、通道分类、bundle 生成均通过 MCP tool 语义升级实现 ✓
- **多指标验收**：本协议验收同样多指标（首次 bootstrap 成功 + 首次真实 dogfood 成功 + 一周内无 thrash） ✓
- **agent-agnostic**：协议不依赖具体 agent 实现 ✓
- **structure > prose**：通道分类是结构性约束而非 agent 自评 ✓

无冲突。

---

**最终状态**：Round 3 完成，置信度 85%，协议 v1.0 设计收敛。等 Yanjun 看结论萃取 + 落地清单，确认后执行 A-C + E 的全部 16 项。

---

## 附录 A：Round 1 Attack 与 Research 的交叉引用表

| Attack | Research 支撑 | 是否导致主张修改 |
|---|---|---|
| A1 置信度自评不可信 | R1.1（ECE + confidence floor）| 是，评分降级为 sort key |
| A2 Goodhart 门槛通胀 | R1.4（metric gaming）| 是，改用结构性约束 |
| A3 开源 PR 模型共识 | R1.2（updatebot/glibc）| 是，改用生成零门槛 + 一键合并 |
| A4 错改不可回滚 | （无外部研究，Myco 内部推导）| 是，新增版本锁协议 |
| A5 初衷是低摩擦不是零人工 | R1.5（既有 Myco 架构）| 是，目标函数重写 |
| A6 风险不分级 | R1.3（已知/未知二分 + 中间地带）| 是，新增三通道矩阵 |
| A7 ca9e 作为 dogfood | （本 craft 自引）| 是，列为 Round 2 验收测试 |
| A8 双 mount 假设过强 | （ASCC 实况反例）| 是，传输层改为会话内授权 |

---

## 附录 B：与 `digestive_architecture_craft_2026-04-10.md` 的一致性核对

- **反刍 narrative**：本协议允许 note 被**反复评估**（每次 boot 都重跑打分），符合瘤胃模型 ✓
- **扁平 notes/ + 状态标签**：`upstream-candidate` 是一个新 tag，不是新目录 ✓
- **MCP tool 条件反射**：下游打 tag 和生成 bundle 都是 MCP tool 层面，不依赖 Claude Code 特定 hook ✓
- **多指标验收**：Round 2 Claim 的验收不依赖单一 metric，而是观察摩擦成本 + dogfood 成功率 + 下游接受率 ✓
- **agent-agnostic**：版本锁协议、三通道矩阵、bundle 格式均不依赖具体 agent 实现 ✓

没有发现与既有架构的冲突。

---

**状态**：Round 1 完成。当前主张置信度 70%。距离 85% 目标还有 6 个待辩论点（B1-B6），等 Yanjun 输入 Round 2 Attack。
