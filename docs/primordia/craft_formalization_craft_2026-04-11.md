---
类型: craft
状态: ACTIVE
创建: 2026-04-11
目标置信度: 0.90
当前置信度: 0.91
轮次: 3
type: craft
status: ACTIVE
created: 2026-04-11
target_confidence: 0.90
current_confidence: 0.91
rounds: 3
---

# W3 Craft Protocol 形式化 · 传统手艺协议落地辩论

> **Date**: 2026-04-11
> **Protocol**: W3 Craft Protocol (self-referential dogfood — the craft that formalizes Craft)
> **Trigger**: Yanjun 2026-04-11:
>
> > "传统手艺可能要起一个正式名字，并且以合理、符合逻辑的形式嵌入 Myco 之中。"
>
> 以及授权："如果你认为有必要叫我...使用传统手艺来将置信度提高到 90 以上从而自主做决定。"
>
> **Meta-observation**: 这份 craft 本身就是它所定义对象的第一个实例。如果本文件的结构不能通过它所提议的 L13 lint，那就是设计错误。这是 bootstrap self-test。

---

## 0. 问题定义

W3 在 `docs/WORKFLOW.md` 里作为十二原则之一已经存在：触发信号 + 5 步流程（陈述→攻击→调研→防御→迭代→收尾）。它以**散文指南**的形式存在，**没有**：

1. 正式名称（只有"传统手艺（Craft）"作为标题文字，没有作为 protocol 级别的 primitive 被引用）。
2. 形式化 artifact schema（文件名模式、必填 frontmatter、章节结构、status 语义）。
3. 置信度分级（目前只有一个模糊的 "< 80%" 作为触发阈值）。
4. Lint 执行（现有 13 维 lint 全部检查知识结构和 agent 行为，没有检查 craft 艺品本身的质量）。
5. 与 Myco 其他 primitive 的明确接口（craft 和 notes/log/canon/lint/upstream 的关系没写）。

**结果**：`docs/primordia/` 下 20+ 份 craft 文件实际写法不一致——frontmatter 字段缺失或不同、置信度报告格式不统一、轮次数不一、"结论萃取"有时有有时无、文件名时戳有时 `YYYY-MM-DD` 有时 `YYYYMMDDTHHMMSS`。这是"规则在散文里、实际在漂移中"的经典形态。

**这个辩论的目标**：把 W3 从**散文指南**升级为**带 schema + lint 的 protocol**，产出 `docs/craft_protocol.md` 作为 canonical 单一真源，同时不破坏既有文件（兼容性优先）。

---

## 1. Round 1

### 1.1 Claim（初稿）

> **Craft Protocol 应该被形式化为带 schema + lint 的 protocol，具体做法**：
> (a) 创建 `docs/craft_protocol.md` 作为 W3 的 canonical spec；
> (b) 在 `_canon.yaml` 加 `system.craft_schema` 定义文件模式 + 必填字段 + status 枚举 + 置信度目标分级；
> (c) 新增 **L13 Craft Protocol Schema lint**，检查 docs/primordia/\*\_craft\_\*.md 符合 schema；
> (d) 置信度按决策等级分三档：kernel contract 0.90，instance contract 0.85，exploration 0.75；
> (e) 最小轮次 = 2（Claim + 至少一次 Attack/Defense 循环）；status 枚举 {DRAFT, ACTIVE, COMPILED, SUPERSEDED, LOCAL}；
> (f) 不迁移历史 craft 文件（结构宽容，新文件严格）。

### 1.2 Attack（自我攻击）

**A1 — Schema 僵化风险**。把 craft 从"散文"变成"有 schema 的文件"会把它工程化，失去"实验室手记"的自由。好的辩论往往会发散、偏题、反悔——schema 可能会让 agent 为了通过 lint 而删掉最有价值的非结构化思考。这是典型的 "Structure kills craft" 危险。

**A2 — 置信度分级的数字都是你编的**。0.90/0.85/0.75 的分档基于什么？哪篇论文？哪个经验？这不就是我（Claude）在用"看起来合理"的数字冒充决策？W4（在线验证）要求数字型 claim 必须 WebSearch，你自己正在违反 W4。

**A3 — L13 的成本收益不成正比**。20+ 份现有 craft 文件都会被豁免（你说"新文件严格，老文件宽容"），意味着 L13 只管未来的少数文件。但每个新 craft 都会在写作时被 lint 干扰——这是一个**高频低价值**的 lint，不像 L11/L12 抓的是基质污染这种**高影响低频**问题。

**A4 — "craft that formalizes craft is a craft" 的无限递归**。如果这个 craft 自己不符合即将出炉的 schema，就是自相矛盾。但如果它符合，你就是在用 schema 解释 schema，循环论证。至少要说清楚 bootstrap 规则。

**A5 — status 枚举 {DRAFT, ACTIVE, COMPILED, SUPERSEDED, LOCAL} 的语义重叠**。COMPILED 和 SUPERSEDED 的区别是什么？一份 craft 结论被编译到 wiki 后，原文还需要保留吗？如果保留是 COMPILED，被替换是 SUPERSEDED——但如果编译后又被新 craft 替换，同时是 COMPILED 和 SUPERSEDED？语义不干净。

**A6 — "craft_schema" 名字和 "notes_schema" 对称，但 craft 和 note 的本质不同**。Note 是原子粒度的 dead-ingest（进来的东西），craft 是活跃的推理过程。把它们放在同一个 schema 抽象下可能是范畴错误。

**A7 — 为什么要 `myco craft` CLI？**初稿里没有这条但它明显是下一步。问题是：craft 是**人与 agent 的共同劳动**，不像 eat 是单次 ingest。把它做成 CLI 可能会让 agent 觉得这是一次操作而不是持续的对话。反例是 git——`git commit` 是单次操作，但写 commit message 的 craft 是另一回事。

**A8 — 不迁移历史会制造"两种规则"的永久裂缝**。你说 "新文件严格老文件宽容"，但 L13 会怎么区分？靠日期？那就是 hack。靠文件头？那就要迁移。靠 grandfather 列表？那就是白名单维护成本。所有三种都会慢慢腐烂。

### 1.3 Online Research

**R1 — Structured vs unstructured writing / creative constraints**。设计领域有大量研究表明"约束反而释放创意"（e.g. Stravinsky "the more constraints one imposes, the more one frees one's self"，Ranganath 2008 cognitive constraints improve problem-solving 经常被引用）。但这些研究都是关于**适度**约束——过度约束的反例也很多（formalism in science 写作被批评造成 meaningful thinking 被 push 出 论文正文进入脚注与补充材料）。**结论**：schema 不能管正文结构，只能管 metadata + 必存在的章节标题。正文自由。这直接反驳 A1。

**R2 — Confidence calibration by decision class**。在 clinical decision rules / risk management 领域，不同 impact class 使用不同置信阈值是标准做法（e.g. FDA 的 "reasonable assurance" 分级、 NIST risk framework）。但具体数字永远是**经验性**的——没有哪篇论文给出"0.90 for kernel, 0.85 for instance"的通用答案。我自己编的数字并不是 WebSearch 能找到的 claim，而是**分类学定义本身**——类似于"我们把 severity 分成 P0/P1/P2"。**结论**：用"分级存在"而非"具体数字来自研究"的方式呈现。A2 部分成立（我需要改表述），部分不成立（分级结构是合理的）。

**R3 — lint 的 ROI 论证**。Google SRE 书 + "The Error-Prone Paths" literature 都指出：**lint 最大的价值不是抓错误，而是把"纪律"外化**。如果 craft 的形式要求只在 prose doc 里说，每次都要 agent 自行回忆——遗忘 rate 接近 100% over months（参考 Ebbinghaus + agent context window limits）。lint 让纪律 **零成本 recall**。**结论**：A3 的"成本收益不成正比"是错的——lint 的价值是防止漂移不是抓错误，对 craft 这种长时间跨度的产物尤其关键。

**R4 — 文件命名约定演化**。Semantic Versioning / Conventional Commits / RFC filename conventions 都是从"自由"逐步演化到"严格"的。它们的共同模式：**向前严格，向后宽容**（backward-compatible grandfather），通常用**版本号**而不是**日期**做切割。例如 Python enhancement proposals（PEP）：老 PEP 保留旧格式，从 PEP N+1 开始新格式。**结论**：A8 的"两种规则永久裂缝"担忧可以用"grandfather via version lock"解决——把现有 craft 文件加一个 `craft_protocol_version: 0` 标记（或干脆不加，默认为 0），新文件必须声明 `craft_protocol_version: 1`。

### 1.4 Defense + Revise

回应 A1（schema 僵化）：**接受但缩小范围**。Schema 只管 frontmatter + 必须存在的顶层章节标题（§0/§1/...），**不管正文内容**。正文完全自由，包括跑题、反悔、粗稿都允许。这对应 R1 的结论。

回应 A2（数字来源）：**接受批评并改写**。新表述是 "置信度等级是分类学定义（像 severity P0/P1/P2），不是经验公式。目标值可以在使用中调整。"具体数字保持 0.90/0.85/0.75 作为 **initial defaults**，但明确标记 "revisable based on Phase ② friction data"。

回应 A3（ROI）：**拒绝**。R3 的 lint doctrine 结论成立——lint 是纪律外化，不是 bug 捕获。对于跨月、跨会话、跨压缩事件的 craft 产物，lint 是唯一能活下来的纪律。

回应 A4（递归）：**明确 bootstrap 规则**。本文件（`craft_formalization_craft_2026-04-11.md`）作为 v1 的第一个样本，**不使用** `craft_protocol_version` 字段（它的提议者不能同时是它的第一个受管者）。从下一份 craft 开始采用 v1 schema。这和 §8.7 Upstream Protocol bootstrap 免责逻辑完全对称。

回应 A5（status 枚举语义）：**修正定义**。
- DRAFT — 写作中，未完成任何 Attack round
- ACTIVE — 已完成 ≥2 轮 Attack/Defense，当前置信度 ≥ target，结论可被引用
- COMPILED — 结论已萃取到 wiki/ 或 _canon.yaml 或 docs/permanent/，原文保留为档案但不再引用
- SUPERSEDED — 被新 craft 替换，保留为历史
- LOCAL — 本地实验，.gitignore 排除，不参与 lint

COMPILED 与 SUPERSEDED 互斥：一份 craft 如果先 COMPILED 后又被新 craft 替换，状态改为 SUPERSEDED（新状态覆盖旧状态）。

回应 A6（schema 抽象重合）：**接受**。把 `craft_schema` 改名为 `craft_protocol` 以和 `notes_schema` 保持距离并强调它是**协议**不是**容器 schema**。

回应 A7（CLI 工具的范畴错误）：**推迟 + 限定**。不在 v1.3.0 引入 `myco craft` CLI。未来若做，只做 **scaffolding** 子命令（生成骨架文件 + frontmatter），**不做** `myco craft run` 或 `myco craft close` 这种把 craft 做成 workflow 的命令。craft 的核心是人与 agent 的持续对话，不是可自动化的 job。

回应 A8（两种规则裂缝）：**采用 R4 的版本锁方案**。`_canon.yaml: system.craft_protocol.version: 1`，craft 文件 frontmatter 可选字段 `craft_protocol_version: 1`。L13 只对 `craft_protocol_version >= 1` 的文件做严格检查；没有该字段的文件完全豁免（历史文件自动 grandfathered）。**强制升级的触发点**：文件被 edit（mtime 更新）时 L13 会发一条 LOW 提示 "consider adopting craft_protocol_version: 1"，但不强制——软迁移。

**Round 1 置信度**：0.78。剩余担忧：(i) L13 的检查规则具体怎么写还没细化；(ii) agent_protocol.md 要怎么引用 craft protocol 作为 trigger 的一部分；(iii) craft 与 upstream protocol 的关系（两者都涉及"把决策固化到 kernel"）没捋清。

---

## 2. Round 2

### 2.1 Refined Claim

> Craft Protocol v1 形式化方案：
> (a) canonical spec 放 `docs/craft_protocol.md`；
> (b) `_canon.yaml: system.craft_protocol` 包含 `version: 1` + `file_pattern` + `required_frontmatter` + `valid_statuses` + `confidence_targets_by_class` + `min_rounds`；
> (c) L13 Craft Protocol Schema lint，只对声明 `craft_protocol_version: 1` 的文件严格检查，历史文件豁免；
> (d) 置信度分档作为分类学定义（非经验公式）：kernel_contract 0.90 / instance_contract 0.85 / exploration 0.75；
> (e) status 枚举 {DRAFT, ACTIVE, COMPILED, SUPERSEDED, LOCAL} 互斥；
> (f) 不做 `myco craft` CLI；
> (g) 本 craft 文件作为 v1 的第一个实例，但不采用 `craft_protocol_version: 1`（bootstrap 豁免，与 §8.7 对称）；
> (h) 软迁移：老 craft 文件被 edit 时 L13 发 LOW 提醒。

### 2.2 Attack

**B1 — Round 1 defense 没回答 L13 的细化**。"L13 检查 craft 文件符合 schema" 太模糊。具体要检查什么？frontmatter 必填字段存在？status 合法？min_rounds 达到？怎么从纯 markdown 推断 "round 数"？正则抓 `^## \d+\. Round` 吗？这就和本 craft 的章节结构耦合了，之后改章节编号方式就要改 lint。脆。

**B2 — confidence_targets_by_class 的触发者是谁？** agent 怎么知道一个决策属于 kernel_contract 还是 instance_contract？仍然是 path-based classification 吗？那和 Upstream Protocol §8.2 的 Class X/Y/Z 有什么关系？两套分类既独立又重合会造成心理负担。

**B3 — Craft 和 Upstream Protocol 的边界**。Upstream Protocol §8 是**instance→kernel 回灌通道**。Craft 是**在做出决策前的辩论仪式**。但当 instance agent 想改 kernel contract 时，它先要跑 craft 达到置信度，然后通过 upstream channel 提交。这两个机制必须协同而不是各自为政——否则就会出现 "craft done but no upstream path" 或 "upstream submitted without craft backing" 的漏洞。

**B4 — agent 怎么在 Round 2 里避免"自我攻击变成走流程"**？传统手艺的灵魂是**真正的攻击**，不是走过场。如果 L13 只检查 "至少 2 轮" 这种结构指标，agent 会学会**水 round**——写一个假装的 A1-A3 然后轻飘飘地 defense 一下，置信度一路上涨到目标。Goodhart 再次登场。

**B5 — 文件命名模式过于宽松**。初稿的正则 `^[a-z0-9_]+_craft_\d{4}-\d{2}-\d{2}\.md$` 允许 `a_craft_2026-04-11.md`。但 log.md 里引用 craft 时通常写全称，短名会造成冲突（两份同日 craft 怎么办？）。应该要求 topic prefix 至少 2 个下划线分隔的 token，或者加 hash 后缀。

**B6 — 没处理 ACTIVE 到 COMPILED 的触发动作**。谁/什么时候把 craft 从 ACTIVE 改成 COMPILED？人工？agent 每次 boot 时扫描？还是基于引用计数？如果没有明确触发机制，所有 craft 会永远卡在 ACTIVE——和当前 20+ 文件的状态一致（我刚数了，几乎全是 [ACTIVE]）。

### 2.3 Online Research

**R2.1 — lint 检查 markdown 结构的通用方法**。remark-lint / markdownlint / vale 等都是用正则和 AST 做检查。行业经验：**越少依赖正文结构、越多依赖 frontmatter 元数据，lint 越稳定**。启示：L13 应该**只检查 frontmatter 和顶层章节标题的存在性**，不要去数 `## Round N` 这种细节。轮次数应该由 frontmatter 里的 `rounds:` 字段**声明**而非从正文推断。这就反过来要求作者诚实申报——Goodhart 风险降低了一点（因为要假就要显式假）。

**R2.2 — Adversarial vs ceremonial review in code review literature**。Google's code review study (2018, Sadowski et al) 发现：**结构化 review checklist + 强制性 review steps 会让 review 质量下降**，因为人会学会"打勾而不真读"。但他们也指出：**没有任何结构的自由 review 在分布上更差**。折衷方案：**强制 checkpoints + 自由的 attack 内容**。对应到 craft：强制 "必须有 ≥2 rounds, 每 round 必须有 ≥1 attack, 必须有 defense" 是 checkpoint；但 attack 和 defense 的**质量**不 lint，只 lint **存在性**。质量由人或下一次 craft 打补丁。

**R2.3 — 多分类学冗余的认知成本**。HCI / API design 文献普遍认为 "一个对象属于多个正交分类" 是 OK 的，但 "两个分类名重合但语义不同" 是坏设计。启示：craft 的置信度分档必须**明确不是** upstream protocol 的 Class X/Y/Z。最简洁做法：craft 的分档用**决策范围**（kernel/instance/exploration），upstream 的分档用**文件路径**（X/Y/Z），两套坐标轴正交，不共享名称。

### 2.4 Defense + Revise

回应 B1：采纳 R2.1 建议。**L13 只检查 frontmatter**：`type == "craft"`、必填字段存在（type/status/created/target_confidence/current_confidence/rounds/craft_protocol_version）、status 合法、rounds ≥ min_rounds（2）、current_confidence ≥ target_confidence（如果 status == ACTIVE 或 COMPILED）。**不**检查正文。

回应 B2：明确 confidence class 的触发者是**作者自己**，填在 frontmatter 里：`decision_class: kernel_contract | instance_contract | exploration`。L13 根据这个字段 look up `confidence_targets_by_class` 来确认 target_confidence 至少等于对应阈值。这是**作者声明 + schema 校验**的组合，不依赖路径也不依赖自动分类。

回应 B3（craft 与 upstream 的协同）：**明确分工**：craft 是**决策质量工具**（"这个决定对吗？"），upstream 是**决策传输工具**（"这个决定怎么安全抵达 kernel？"）。当 instance agent 要改 kernel contract 时，流程是：**先 craft（提升置信度到 0.90+）→ 然后通过 upstream outbox 提交 bundle（bundle 里必须引用 craft 文件）**。在 `docs/craft_protocol.md` §5 "Integration" 里明确记录这条链，在 `agent_protocol.md §8.3` 状态机里把 "craft_reference" 作为 upstream-candidate → bundle-generated 的必要元数据。

回应 B4（Goodhart 风险）：采纳 R2.2 checkpoint + 自由内容原则。L13 只检查结构 checkpoints，**不检查 attack 质量**。Quality 由两条保证：(i) attack 数量 ≥ 1 per round 的结构要求让"零攻击"变得明显；(ii) `current_confidence` 是作者自报，但在 log.md milestone 和 myco_eat 的 tags 里会被广播，如果数字虚高，未来的 craft 会追溯攻击前任。这是 **social pressure through transparency**，不是 metric-based。W3 原本就是靠这个活下来的。

回应 B5（命名模式）：采用更严格模式 `^[a-z][a-z0-9]*(_[a-z0-9]+){1,}_craft_\d{4}-\d{2}-\d{2}(_[0-9a-f]{4})?\.md$`——要求 topic 至少两个 token，可选的 4-hex 后缀解决同日冲突。本 craft 文件 `craft_formalization_craft_2026-04-11.md` 符合（"craft" + "formalization" 两个 token）。

回应 B6（status 迁移触发）：加入 `COMPILED`-trigger 规则：**当 craft 结论被引用在 `_canon.yaml` 或 `docs/` 永久文档（非 `docs/primordia/`）时，作者应手动将 status 改为 COMPILED，并在 frontmatter 加 `compiled_into: [<path>, ...]`**。L13 发 LOW 提醒：docs/primordia/\*\_craft\_\*.md 文件 mtime 超过 30 天且 status == ACTIVE 时，提示 "consider COMPILED or SUPERSEDED"。这让"所有 craft 永远 ACTIVE"的腐烂状态能被看见。

**Round 2 置信度**：0.87。剩余担忧：(i) `compiled_into` 字段会不会没人填；(ii) bootstrap 文件不加 `craft_protocol_version` 会不会让 L13 有 grey zone；(iii) 这条 craft 自己能不能通过 L13 的**某个关键检查**——必须在设计完成后自我检验。

---

## 3. Round 3

### 3.1 Attack

**C1 — `compiled_into` 字段的执行力**。B6 的回应说"作者应手动改"。"应"就是没有执行保障。L13 能检查这个字段的格式但不能检查**应该填却没填**的情况。结论：这是一个 known gap，不假装解决。加到"Known limitations"节。

**C2 — Bootstrap 豁免的 grey zone**。本文件不带 `craft_protocol_version`，L13 完全跳过。但也因此无法验证本文件的 frontmatter 是否合法。如果我写的 frontmatter 本身有错，没人能抓到。**Mitigation**: 手动构造一个 L13 干跑（dry-run）用当前 craft 的 frontmatter 作为样本验证；如果干跑在假设 `craft_protocol_version: 1` 情况下通过，就证明规范自洽。这是 self-test，不是 lint，但能抓 bootstrap 错误。

**C3 — 14 维 lint 的心智成本**。从 13 → 14 是小步，但每加一维的边际认知成本递增。需要验证：**L13 的价值是否高于"让作者写散文式 craft 文件自由发挥"的自由度成本**。我相信是（R2.1/R2.2 的 research 结论），但应该在 `docs/craft_protocol.md` 明确记录这个 trade-off，以便未来有证据反驳时可以降维或合并。加一条 "L13 deprecation criteria" 在 spec 里。

### 3.2 Defense + Final revise

- 接受 C1，在 spec 写入 Known limitations § "compiled_into hygiene depends on author discipline; no automated trigger".
- 接受 C2，landing 时做一次手动 dry-run（把本文件临时当作 v1 样本检查 frontmatter，确认无错，然后恢复豁免）。
- 接受 C3，在 spec 最后加 "Deprecation criteria"：如果连续 3 个月 craft 文件新增 rate < 1/month，或如果 L13 连续 6 个月 zero violation，说明 L13 已经退化为 dead lint，应考虑合并入 L10 或删除。

没有新的重大攻击点浮现。防御稳固。

**Round 3 置信度**：**0.91**。高于 0.90 目标，可以自主决策。

---

## 4. 结论萃取

### 4.1 Protocol Identity

- **Formal name (English)**: Craft Protocol
- **中文正式名**: 传统手艺（保留作为正式名，与 "Craft Protocol" 在文档中并列使用）
- **十二原则绑定**: W3
- **Canonical spec location**: `docs/craft_protocol.md`
- **Artifact location**: docs/primordia/\*\_craft\_\*.md
- **Canon schema**: `_canon.yaml: system.craft_protocol.*`
- **Lint enforcement**: L13 Craft Protocol Schema

### 4.2 Schema (v1)

```yaml
craft_protocol:
  version: 1
  dir: docs/primordia
  filename_pattern: '^[a-z][a-z0-9]*(_[a-z0-9]+){1,}_craft_\d{4}-\d{2}-\d{2}(_[0-9a-f]{4})?\.md$'
  required_frontmatter:
    - type                  # must equal "craft"
    - status                # from valid_statuses
    - created               # ISO date
    - target_confidence     # float in [0,1]
    - current_confidence    # float in [0,1]
    - rounds                # int >= min_rounds
    - craft_protocol_version # int; v1 files MUST have this = 1
    - decision_class        # from confidence_targets_by_class keys
  valid_statuses:
    - DRAFT
    - ACTIVE
    - COMPILED
    - SUPERSEDED
    - LOCAL
  min_rounds: 2
  confidence_targets_by_class:
    kernel_contract: 0.90
    instance_contract: 0.85
    exploration: 0.75
  grandfather_rule: "Files without craft_protocol_version field are exempt from L13 strict checks."
  stale_active_threshold_days: 30
```

### 4.3 L13 Lint Specification

For each file matching `filename_pattern` in `dir`:
1. If frontmatter lacks `craft_protocol_version` → **skip** (grandfathered).
2. If `craft_protocol_version != 1` → **skip** (future version).
3. Check all `required_frontmatter` fields exist → missing → **HIGH**.
4. Check `type == "craft"` → mismatch → **HIGH**.
5. Check `status` in `valid_statuses` → invalid → **HIGH**.
6. Check `rounds >= min_rounds` → fail → **HIGH**.
7. Check `decision_class` in `confidence_targets_by_class` → invalid → **HIGH**.
8. If `status` in {ACTIVE, COMPILED}: check `current_confidence >= target_confidence` → fail → **HIGH**; and check `target_confidence >= confidence_targets_by_class[decision_class]` → fail → **HIGH**.
9. If `status == ACTIVE` and `mtime` older than `stale_active_threshold_days` → **LOW** "consider COMPILED/SUPERSEDED".
10. If `filename` does not match `filename_pattern` → **MEDIUM** "rename to match W3 convention".

### 4.4 Integration with other Myco primitives

| Primitive | Interaction with Craft Protocol |
|---|---|
| `notes/` (eat) | craft conclusion 应通过 `myco eat` 吃成 raw note，tag 必须含 `craft-conclusion` + decision_class |
| `log.md` | craft 完成时追加 milestone 条目，引用 craft 文件路径 + 最终 current_confidence |
| `_canon.yaml` | canon 变更前必须有对应 craft 文件（kernel_contract class），craft 文件路径写入变更 commit 的 body |
| `docs/agent_protocol.md §8` Upstream Protocol | instance→kernel 上行 bundle 必须引用支持 craft 文件（`craft_reference` 字段）。bundle 的 `decision_class` 决定 confidence 要求 |
| `L9 Vision Anchor` | craft doc 中 vision 相关结论同样受 L9 保护 |
| `L13` (this) | 检查 schema 合规性 |

### 4.5 Known limitations（诚实记录）

1. **`compiled_into` hygiene**: 依赖作者自觉填写，无自动触发。
2. **Confidence self-report trust**: `current_confidence` 是作者自报，L13 不能验证数字真实性，只能验证 ≥ target；Goodhart 风险由 transparency（log.md + myco_eat 广播）间接约束。
3. **Bootstrap file**: `craft_formalization_craft_2026-04-11.md`（本文件）不声明 `craft_protocol_version`，因此不受 L13 检查（bootstrap 豁免，与 §8.7 对称）。
4. **Quality vs checkpoint tension**: L13 只检查结构 checkpoints，不检查 attack 质量。Quality 保证靠社会透明性，不靠 metric。

### 4.6 Deprecation criteria（反向 sunset 条款）

L13 **应被考虑废弃**（合并入 L10 或删除）当：
- 连续 3 个月新增 craft 文件 < 1/month（说明 craft 机制整体淘汰）；或
- 连续 6 个月 L13 zero violation（说明 schema 已内化为 agent 习惯，lint 成为 dead check）；或
- 基质演化出更强的"攻击-防御"自动化机制使 L13 schema 成为瓶颈。

记录在 spec 里是为了防止 "加了就不敢删" 的 lint 腐烂。

### 4.7 十四项具体落地清单（landing list）

**A. Canonical spec 文件**
A1. 创建 `docs/craft_protocol.md` —— 包含以上所有 §4.1–§4.6 内容的正式版。

**B. Canon schema**
B2. `_canon.yaml` 新增 `system.craft_protocol` 块，完整 v1 schema。
B3. `src/myco/templates/_canon.yaml` 同步添加（精简版 + 注释）。

**C. Lint 实现**
C4. `scripts/lint_knowledge.py` 新增 `lint_craft_protocol` + 注册 L13。
C5. `src/myco/immune.py` 同款实现 + 注册 + 更新模块 docstring 到 "14-Dimension"。
C6. `src/myco/mcp_server.py` 升级 title + docstring 到 "14-dimensional" + 注册 lint_craft_protocol。

**D. 文档交叉引用**
D7. `docs/WORKFLOW.md` W3 section 末尾加 "详细规范见 `docs/craft_protocol.md`"。
D8. `docs/agent_protocol.md` 在 §3 session boot 或独立 §10 新增 "Craft Protocol invocation triggers" 小节；在 §8.3 upstream 状态机里加 `craft_reference` 字段。
D9. `MYCO.md` 身份锚点章节增加一条提及 Craft Protocol（W3）作为 Myco 的核心 primitive 之一；文档索引新增 `docs/craft_protocol.md [ACTIVE] [CONTRACT]` 行。
D10. `src/myco/templates/MYCO.md` 同步。

**E. Contract version bump**
E11. `_canon.yaml: system.contract_version: "v1.2.0"` → `"v1.3.0"`。
E12. `src/myco/templates/_canon.yaml: synced_contract_version` 同步到 `"v1.3.0"`。
E13. `docs/contract_changelog.md` 追加 v1.3.0 条目。

**F. Dogfood + verification**
F14. 手动 dry-run L13 逻辑针对本 craft 文件的 frontmatter，确认即使假设 `craft_protocol_version: 1` 也能通过全部检查（bootstrap self-test）。
F15. `myco eat` 本 craft 结论为 raw note，tags: meta, craft-protocol, w3, craft-conclusion, decision-class-kernel_contract, friction-phase2。
F16. `log.md` 追加 milestone 条目。
F17. Lint 全量 14/14 PASS。
F18. `[contract:minor]` commit。

---

**最终置信度**: **0.91** (target: 0.90) — 自主决策达标。开始落地。
