# Vision Closure Craft — 兑现 README 六誓言的九项机制

> **状态**: ACTIVE · design
> **创建**: 2026-04-14
> **触发**: v0.40 substrate 落地后 self-audit，发现 README 多条承诺仍处于"愿景"状态而非"现状"
> **目标**: 为 8 项能力缺口 + 1 项发布节奏给出可实施的机制设计，闭合 substrate 四特征（autopoiesis, selective permeability, temporal organization, co-evolutionary niche）

---

## 共同原则

1. **Agent + Myco 双自动化**：每一条机制必须同时回答两个问题——"Myco 自己怎么跑"（调度/钩子）和 "Agent 怎么无感触发"（session hook / 任务上下文感知）。单侧自动化不合格。
2. **selective permeability 优先**：外部输入必须经过免疫层，不是直接吞入。
3. **可降级**：每个机制 fail 时不影响主流程，只产 signal。
4. **观测先于自动**：先让 `myco hunger` 能看见缺口，再自动处置。

---

## G1. 自主吞噬外部世界（autonomous foraging）

**现状**：`myco absorb` 必须 Agent 显式调用 URL；无外部订阅；无 opportunistic 触发。

**机制设计**：

### G1.1 订阅层（Myco 侧）
- 新文件 `.myco_state/feeds.yaml`：用户/项目配置的外部源（arxiv topic、github trending、RSS、HuggingFace paper-of-the-day、固定 blog 列表）。
- 新命令 `myco forage`：拉取所有 feed → 过滤 → 暂存到 `.myco_state/inlet/`（非 notes/，等体检）。
- 调度：通过 `schedule` skill 注册为每日任务（或每次 session 启动时的 background tick）。

### G1.2 免疫闸（selective permeability）
- `inlet/` 里每条候选进入免疫过滤链：(a) 与现有 notes/wiki 的语义去重（cosine 阈值），(b) topic 是否落在 `.myco_state/interests.yaml`（项目声明的兴趣向量），(c) 来源可信度打分。
- 通过 → 自动 `eat` 入 raw；否则直接丢弃（不进 notes，不占空间）。

### G1.3 Agent 机会主义触发（Agent 侧）
- 新 MCP 工具 `myco_scent(topic, budget)`：Agent 检测到当前任务涉及它已知 wiki 未覆盖的主题时，调用此工具。Myco 立即对该 topic 执行一次 on-demand forage（arxiv + github query），结果经 G1.2 闸门，通过的直接 `eat`。
- 这就是 Agent 自动使用 Myco 的 hook 点：Agent 不需要知道外部 API，只需声明"我想了解 X"。

### G1.4 配置入口
- `myco forage --setup`：向用户询问 3-5 个关注主题，生成初版 feeds.yaml 和 interests.yaml。
- 默认 feeds：arxiv cs.LG/cs.AI/stat.ML + Anthropic blog + HF papers，可关闭。

---

## G2. 语义缺口预测（替换词频噪声）

**现状**：`predict_knowledge_needs` 按 user turn 词频排序，返回 waiting/expectations/initiative 这类噪声。

**机制设计**：

### G2.1 信号源聚合
替换单一词频为三路信号：
- **user-turn 主题聚类**：最近 30 days user turns 抽取 noun phrase → 聚类（local embedding + HDBSCAN）→ 每簇一个 topic representative。
- **search_misses 聚类**：同样方式，权重 ×2（miss 是比词频更强的信号）。
- **raw note 悬空主题**：raw notes 里出现但未在任何 wiki 页标题/tag 覆盖的 topic。

### G2.2 覆盖度测评
- 对每个 topic representative，计算与现有 wiki pages 的最高 cosine 相似度。
- 低于阈值（默认 0.45）→ 标记为 gap。

### G2.3 输出到 hunger
- `predicted_need` 信号从词频改为 "topic cluster + miss_count + coverage_score"。
- 每条 gap 附带建议动作：`myco_scent("topic")` 或 `myco absorb <url>`。
- Agent 看到这种信号可以直接 acted on。

### G2.4 轻量化路径
如果不想拉 sentence-transformers 依赖，可用 tf-idf 过渡版：turn × wiki_page 矩阵，topic = top-tf-idf term，gap = 在 turn 高 tf-idf 但 wiki 文档库内 idf 也高的 term。精度损失，但零依赖。

---

## G3. 真值免疫（external fact-checking）

**现状**：L1-L25 全是内部自洽；无一条 lint 会问"这个 claim 在 2026 年还对吗"。

**机制设计**：

### G3.1 时敏 claim 标注
- 在 `digest` 过程中，要求 `--nutrient` 之外多一个可选字段 `--freshness {static|time_sensitive|live}`。
  - `static`：数学定理、定义式内容，永远不需要复验
  - `time_sensitive`：API 用法、库版本、研究 SOTA，默认 90 days 复验窗口
  - `live`：价格、链接可用性，默认 7 days 复验窗口
- 未标注的 integrated 条目默认 `time_sensitive`。

### G3.2 复验调度
- 新命令 `myco verify`：扫描所有 `time_sensitive`/`live` 条目，按 `last_verified` 排序，取最旧 N 条。
- 每条执行一次 LLM-judged 外部查询：Agent 侧调用 WebSearch with claim-derived query → 对比结果 → 三分类输出（still_true / contradicted / ambiguous）。

### G3.3 处置
- `contradicted` → 进入 `quarantine` 状态（新加的 status）。quarantine 条目不再被 `mycelium search` 默认返回，同时在 hunger 产 signal 要求 Agent digest forward（absorb 新版 + excrete 旧版）。
- `ambiguous` → 只更新 `last_verified`，下次复验窗口减半。
- `still_true` → 更新 `last_verified`。

### G3.4 L26 真值维度
- 在 `lint_knowledge.py` 加 L26 "Freshness Debt"：报告有多少 time_sensitive 条目过了复验窗口未验证。阈值进 hunger。

### G3.5 Agent 接入
- 新会话启动后，若 `verify` 积压 > 阈值，hunger 产 signal 建议"用 5 分钟做一次复验批次"。Agent 可在空闲步（用户思考中）silently 批量处理。

---

## G4. 更激进的排泄启发式

**现状**：`dead_threshold_days=7` 但条件太严；`colony suggest=[]`；`prune` 近乎总是 0 dead。

**机制设计**：

### G4.1 多路腐烂信号
当前只有"digest_count 低 + 超期"。扩展为：
- **孤立**：inbound_links=0 AND outbound_links ≤ 1 AND age > 14 days
- **被超越**：同 topic cluster 出现更新 integrated 条目，且新条目 nutrient 覆盖旧条目
- **quarantine 且 14 天未复活**：G3 标记后长期未重新吸收
- **低价值 raw**：raw 超过 30 天未被 digest 且 inbound=0

任何一条命中即 `prune` 候选；命中两条即自动 excrete（带 reason）。

### G4.2 supersede 关系显式化
- 新 meta 字段 `supersedes: [note_id]` 和 `superseded_by: note_id`。
- `digest --to integrated --supersedes old_id` 自动把 old_id 转 excreted，reason = "superseded by new_id"。
- 这让"被超越"信号可查询，而不是靠启发式猜。

### G4.3 condensation 重启
- `colony suggest` 空返回是因为阈值太严。当前 cluster 要求 min_size=5；先改 3，加 fallback：若全局 `raw+integrated > 200` 则降级条件，保证总是能产出至少一条建议。

### G4.4 prune --auto
- 新 flag `myco prune --auto`：把命中两条+的候选直接 excrete，不需要人确认。作为 session hook 默认每次跑。

---

## G5. 引擎自我进化（engine autopoiesis 闭环）

**现状**：editable install 让代码可改，但缺闭环。没有机制让 Myco 根据自己的 metrics 主动改自己。

**机制设计**：

### G5.1 Metabolism 指标落盘
- `.myco_state/metabolism.jsonl`：每次 `hunger` 运行追加一行（signals, counts, lint_score, miss_count, freshness_debt, excretion_rate）。
- 形成时间序列。

### G5.2 Self-critique 扫描器
- 新命令 `myco introspect`：读最近 30 days metabolism，找出**恶化趋势**：
  - 某维度 lint 反复 fire → 对应协议/代码可能不合理
  - 某类 signal 连续触发但未 resolve → 处置机制失效
  - freshness_debt 单调增 → `verify` 跑得不够
- 输出 `docs/primordia/introspect_<date>.md`：问题列表 + 可疑代码/协议文件。

### G5.3 Agent-driven code craft
- `introspect` 输出是 craft 文档的 raw material。Agent 在 session 结束或用户空闲时可触发 `craft-engine` skill：
  1. 读 `introspect` 报告
  2. 选一个最高 ROI 的问题
  3. 在 git branch 上写补丁（含测试）
  4. 跑 pytest，全绿才 PR
  5. 推送到 GitHub，等待 human gate（maintainer merge）
- 这就是"Agent 自动化"：用户无感，craft 周期从"人工发起"降到"系统发起，人工审核"。

### G5.4 安全带
- 禁止改动名单：`src/myco/contract/` 里核心 schema、`MYCO.md` identity 块。Agent 的补丁 touch 这些需要 --explicit-core flag，默认拒。
- 所有 Agent 推送的 branch 命名 `auto/introspect-<hash>`，便于审查。

---

## G6. 跨项目菌丝传导

**现状**：v0.40 全局 install 让物理上共享一个 Myco 实例，但 colony 逻辑弱，项目 A 的知识不会自动惠及项目 B。

**机制设计**：

### G6.1 Project provenance 标签
- 每个 note eat 时自动加 `project: <project_name>`（来自 CWD 或 --project）。
- 每条 integrated/extracted 同样携带。

### G6.2 全局 colony
- `myco colony --global`：跨所有 project 跑 cluster。
- 同一 topic cluster 若来自 ≥ 2 项目 → 自动 promote 为 `wiki/cross_project/<topic>.md`（新目录），nutrient 合并，每项目一段 contribution。

### G6.3 Agent 启动吸附
- session hook：Agent 在 project B 启动时，Myco 查 `cross_project/` 里与 B 的 `interests.yaml` 有交集的条目，作为"跨项目建议"注入 agent_protocol §0 的 boot 输出。
- Agent 看见 "你在做 X，项目 A 里 3 条 extracted 知识可能相关：…" 直接用。

### G6.4 隐私/隔离
- `.myco_state/project_visibility.yaml`：允许用户把某 project 标记为 private（只进 colony 匿名统计，不暴露 nutrient 文本给其他 project）。

---

## G7. Zero-touch session hooks（跨宿主可靠性）

**现状**：plugin 提供 hooks，但 Cowork/Claude Code/Cursor/VS Code 各家行为不一致，新会话启动 `myco hunger` 并非 100% 自动。

**机制设计**：

### G7.1 Host matrix
- 建 `docs/host_matrix.md`：每个 host 列 session-start / session-end / pre-tool-call 三个钩子点的支持情况 + 已知踩坑。
- 每个 host 单独写 adapter：`src/myco/hosts/cowork.py`、`claude_code.py`、`cursor.py` 等。

### G7.2 Degradation ladder
优先级：
1. 真 hook（plugin/host-native session hook）
2. 进程级守护（`myco daemon` 后台进程，监听目录变动/新会话迹象）
3. Agent protocol §0.5 的纯文本"新会话必做"协议（最后兜底）

G7.2 的关键：当真 hook 失败，Myco 要能感知并退到下一级，不是静默失效。

### G7.3 myco doctor
- 新命令 `myco doctor`：检查当前 host、hook 安装状态、最近一次 hunger 执行时间、有无 ghost 状态。
- 输出每项红绿灯 + 修复命令。
- README Quick Start 后面加一步："装完跑 `myco doctor` 一分钟确认全绿"。

### G7.4 session-end 保险
- 所有 host adapter 都尝试 session-end 触发 `myco hunger --execute --quiet`，失败不报错。
- 如果 10 个 session 都没有 end-hook 触发，doctor 第一条红。

---

## G8. Substrate → Agent 反向塑造

**现状**：Agent 用 Myco，Myco 很少改变 Agent 的行为。co-evolutionary niche 停在自述。

**机制设计**：

### G8.1 违规检测
- `lint_knowledge.py` 增加 L27 "Protocol Adherence"：扫描最近 N 个 session 的工具调用序列，与 `agent_protocol.md` §各节规则对比，标记违规模式（例：该 eat 没 eat、该 condense 没 condense、search miss 后没 absorb）。

### G8.2 协议补丁提议
- 违规模式若**集中**在某节且持续 >1 周，`introspect` 判断：可能是协议本身不合理（太繁琐/不清晰）而非 Agent 失职。
- 生成 protocol patch 草案：`docs/primordia/protocol_patch_<date>.md`，具体到行级 diff。

### G8.3 Human gate
- 协议的每一次改动必须走 craft 流程（primordia doc + commit）。Agent 只能**提议**，merge 由 maintainer。
- 这保留 substrate 的"被塑造"性，但不让 Agent 单边改行为合同。

### G8.4 反馈 loop 完整性
闭环：Agent 执行 → Myco 观察 metabolism → introspect → protocol patch 提议 → human merge → 新协议回到 Agent 行为 → metabolism 改善（或否，再迭代）。

---

## G9. PyPI 发布节奏

**现状**：迭代频繁但 PyPI 滞后，用户 `pip install myco` 拿到旧版本。

**机制设计**：

### G9.1 Semver label 驱动
- commit message 前缀约定：
  - `feat:` → minor bump
  - `fix:` / `docs:` / `refactor:` → patch bump
  - `feat!:` / `BREAKING:` → major bump
- GitHub Action 读 commit range → 计算新版本 → 更新 `pyproject.toml` 和 `src/myco/__init__.py`。

### G9.2 发布触发
- 方案 A：每次 push 到 main 即自动 release（激进）
- 方案 B：合并 `release` tag 后触发（保守，推荐）
- 推荐 B：maintainer 在认为可放出时加 `git tag v0.41.0 && git push --tags`，Action 触发 `twine upload`。

### G9.3 Pre-release check
- Action 里加 step：校验 README 的 `pip install myco` 指向的 latest 版本与待发版本号一致（或最多 patch 落后）。
- 自动同步三语 README 的 badge。

### G9.4 PyPI 版本显示在 MYCO.md
- 新 Lint 维度 L28 "PyPI Sync"：检测本地 `__version__` 与 PyPI latest 的差距 > 1 minor 则告警。
- hunger signal: `pypi_lag` when gap exceeds threshold。

### G9.5 changelog 自动化
- conventional commits 驱动 `CHANGELOG.md` 自动生成（release-please 或 git-cliff）。
- 每次 release 把当 release 的 changelog 附到 GitHub Release body。

---

## 优先级与落地顺序

按"对 README 承诺兑现度"× "实现难度" 粗排：

| 序号 | 机制 | 承诺兑现度 | 难度 | ROI |
|---|---|---|---|---|
| G9 | PyPI 发布 | 高（用户第一眼） | 低 | ⭐⭐⭐ 立即做 |
| G4 | 更激进排泄 | 中 | 低 | ⭐⭐⭐ 立即做 |
| G7 | Session hooks | 高（UX 生死线） | 中 | ⭐⭐⭐ 立即做 |
| G1 | 自主吞噬 | 最高 | 中高 | ⭐⭐ 下一轮 |
| G3 | 真值免疫 | 高 | 高 | ⭐⭐ 下一轮 |
| G2 | 语义缺口预测 | 中 | 中 | ⭐⭐ 下一轮 |
| G6 | 跨项目菌丝 | 中 | 中 | ⭐ 第三轮 |
| G8 | Substrate → Agent | 中 | 中高 | ⭐ 第三轮 |
| G5 | 引擎自进化 | 高（但 gimmick 风险） | 高 | ⭐ 第三轮 |

**第一轮（本周）**：G9 + G4 + G7 →「可发布、能丢垃圾、开箱零触」
**第二轮（两周）**：G1 + G3 + G2 →「吞噬外部 + 检查时效 + 预测准确」
**第三轮（月级）**：G6 + G8 + G5 →「跨项目 + 协议反向塑造 + 引擎自改」

---

## 与现有 contract 的兼容性

- 所有新状态（quarantine）、新字段（freshness、supersedes、project）都是 **向后兼容扩展**，旧 notes 默认值即可。
- 新命令（forage / verify / introspect / doctor / scent）都是**加法**，不改现有 CLI 语义。
- 新 MCP 工具需要在 `docs/agent_protocol.md` §0 工具清单更新；tool count 从 19 升至 ~24。
- Lint 维度从 26 升至 28，`_canon.yaml` 需要同步。

---

## 下一步

1. 本 craft doc 先 eat + integrated 入档
2. G9 先独立拆 PR（最小 scope，立即收益）
3. G4 紧随（改 prune 启发式 + supersede 字段）
4. G7 起 host_matrix + doctor 骨架
5. 按上面路线图推进

**Related**:
- [wiki/identity.md](../../wiki/identity.md) — substrate 四特征
- [docs/vision.md](../vision.md) — 愿景六誓言
- [README.md](../../README.md) — 对外承诺文本
- [docs/agent_protocol.md](../agent_protocol.md) — Agent 行为合同
