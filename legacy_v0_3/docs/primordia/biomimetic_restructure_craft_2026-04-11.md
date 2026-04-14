---
类型: craft
状态: ACTIVE
创建: 2026-04-11
目标置信度: 0.90
当前置信度: 0.92
轮次: 3
type: craft
status: ACTIVE
created: 2026-04-11
target_confidence: 0.90
current_confidence: 0.92
rounds: 3
craft_protocol_version: 1
decision_class: kernel_contract
---

# Biomimetic Restructure & Structural Compression Craft

**Author**: Claude (Myco kernel agent, autonomous run under user grant)
**Trigger**: 用户在 2026-04-11 panorama 回顾后明确指示——"Myco 的项目结构彻底
重构重组织，并且这也应该是 Myco 永恒进化的一部分，即不断优化自己的内容组织
形式，而不是越来越冗余，这也回到了压缩的那个话题，压缩也是智能的一部分"，
同时要求"整个项目的命名、结构等等都可以借鉴仿生 Myco 在生物学上的优点和特点"。
**Decision class**: `kernel_contract`（floor 0.90）——改动触及 `_canon.yaml::write_surface`
白名单（L11）、cross-reference 图（L1）、下游 instance 同步路径、命名哲学
（不可轻易反悔的身份级决策）四个维度。

---

## §0 为什么必须走 craft 而不是直接动手

四条独立的硬约束：

1. **L11 write_surface**：任何目录 rename 必须同步 `_canon.yaml::system.write_surface.allowed`，
   否则 L11 立即爆炸。
2. **L1 reference integrity**：`docs/` 内互相引用 + MYCO.md 文档索引 + README
   链接全部依赖当前路径。Rename 一个目录 = 改 N 条引用，N 未知。
3. **下游 instance drift**：ASCC 等 instance 通过 `src/myco/templates/**` 同步
   Myco 结构，不兼容的 rename 会污染所有 instance。
4. **命名哲学的不可逆性**：路径名一旦稳定就被 agent / 人类肌肉记忆锁死，
   frequent rename = 基质癌变的另一种形态。必须一次到位或不做。

用户授权"自主决定"建立在 craft 置信度 ≥0.90 的前提上——这是
`on-self-correction` 原则的应用：越大的动作越需要越严格的自我规制。

---

## §1 核心主张（Claim）

Myco 应当进行一次**克制但方向明确**的仿生重构，分为三个耦合的部分：

### Claim A · Naming（命名层）

**有选择地**把生物学 Myco 的术语应用于三类目录：
1. **身份承载**的目录（`wiki/`, `docs/open_problems.md`）——这些名字现在是
   通用词，换成生物学词汇能把 Myco 的 substrate 哲学**直接刻在路径里**。
2. **工作流阶段**的目录（旧名 `docs/current/`）——现在的名字只表达"正在活跃"，
   换成生物学词汇能表达"早期发育中的子实体"这一更准确的语义。
3. **代码核心目录不动**（`src/myco/`, `scripts/`, `notes/`, `docs/` 顶层）——
   这些被 15+ 处硬编码，rename = 高风险低收益的纯 cosmetic 改动。

### Claim B · Compression（压缩层）

借重构机会**一次性压缩** `docs/` 顶层的 14 份文档。识别出的冗余：
- `ascc_migration_v1_2.md` + `ascc_agent_handoff_prompt.md` → 定位重叠
- `research_paper_craft.md` + `reusable_system_design.md` → 定位重叠
- `architecture.md` + `evolution_engine.md` + `theory.md` → 存在语义分层但边界模糊

压缩必须严格遵守"信息保真"——不是删内容，是合并 + 去重 + 重新分层。

### Claim C · Permanent Mechanism（永恒机制层）

这次重构是一次性事件，但**防止重新 bloat** 必须是永久机制。新增：
- `docs/biomimetic_map.md`（新，永久锚点）——glossary 形式记录 biology ↔
  function 的映射，防止未来 agent 不理解生物学名字而瞎改。
- `myco hunger` 新增 `structural_bloat` 信号——当 docs/\*.md 数量超过阈值
  或 docs/primordia/\*.md 超过另一阈值时告警，驱动周期性压缩。
- 上述两项都进入 `_canon.yaml`，bump contract_version → v1.5.0。

---

## §2 Round 1 · 八条攻击 + 防御

### A1 · Legibility Attack（易读性攻击）

> "冷启动的 agent / 人类看到 `hyphae/` 目录名，第一反应是 'WTF is hyphae'。
> 你用 biological naming 换掉了 `notes/` 这种**立刻看懂**的名字，收益是什么？
> 身份锚点？agent 读 MYCO.md 前三行就知道这是 substrate，不需要目录名也能锚定。
> 这次 rename 增加了冷启动摩擦，没有换来真实的信息增益。"

**Research** (web & first principles)：
- VS Code / Linux kernel / Rust 等大型 repo 的目录命名都是**功能性英文词**
  （`src/ tests/ docs/ scripts/`），不是 metaphor。行业惯例站在攻击方。
- 但 **Rails 的 `app/controllers/app/models/`、Elixir 的 `lib/`、Clojure 的
  `resources/`** 都有意识形态命名。约定不是铁律。
- 真正的判据是"命名带来的信息 vs 学习成本"的 trade-off。

**Defense**：**攻击部分成立，Claim A 必须收窄**。
- `notes/` 被 15+ 处硬编码、被 MCP tool 名字（`myco_eat`/`myco_view`）引用、
  被用户在中英文对话里混用——rename 的成本远超 biological 重命名的身份收益。
  **`notes/` 保留原名**。
- 但是 `wiki/` 完全不同：(a) 目前是**空目录**，rename 0 代码成本；
  (b) "wiki" 这个名字在软件圈指向 "MediaWiki / Confluence"，完全错误地
  暗示 "allowed to be messy"——而 Myco 的 wiki 原意是 Karpathy LLM Wiki 的
  "高度结构化 distilled knowledge"。现名主动误导。
- `docs/current/` 同理：`current` 这个词在英语里极度通用，完全不表达"craft
  辩论产物、早期发育中"这一真实语义。rename 到更准确的名字能**减少**冷启动
  agent 的误解而不是增加。

**Revise**：Claim A 从"三类目录"缩减为——
- ✅ `wiki/` → `mycelium/`（空目录，零代码成本，语义增益最大）
- ✅ `docs/current/` → `docs/primordia/`（~28 文件，需要更新 craft_protocol.md
  里的路径 + `_canon.yaml::craft_protocol.dir`，但这是 self-contained 的改动）
- ❌ `notes/` 保留（硬编码深度太深）
- ❌ `src/`, `scripts/`, `docs/` 顶层保留（行业惯例）

### A2 · Metaphor-Forcing Attack（牵强映射攻击）

> "生物学映射听起来很美，但 `contract_changelog.md` 在生物学 Myco 里对应什么？
> `agent_protocol.md` 对应什么？如果强行塞进 'shedding/', 'cell_wall/' 这种
> 目录，你是在忠实映射还是在凹造型？后者更糟——它会让 agent 误以为有生物学
> 对应，从而做出错误的类比推理。"

**Defense**：**攻击完全成立**。
这正是 Claim A 收窄的第二个理由——**不存在清晰生物学对应物的东西，绝不
硬套**。`contract_changelog.md`、`agent_protocol.md`、`craft_protocol.md` 这三
份 contract 文档都**保留原名**，不套 `cell_wall/` 之类的名字。
解决方式：用 `docs/biomimetic_map.md`（Claim C）显式记录映射，让想了解生物学
类比的读者有一条路径，但不强加于目录结构。

**Revise**：Claim A 进一步明确——**只把生物学名字用于存在清晰对应的目录**，
不存在对应的目录保留功能性命名。这是对 user 原话"借鉴仿生"的诚实执行——
"借鉴"不等于"全盘复制"。

### A3 · L1 Cross-Reference Explosion Attack

> "你承认 rename 会触发 L1 reference integrity 爆炸。那么：
> (1) 具体有多少处引用会断？
> (2) 如果 > 50 处，grep+sed 批量改带来的次生 bug 风险有多大？
> (3) grandfather 规则能保护这次 rename 吗？"

**Research**：
```
grep -rn "wiki/" docs/ MYCO.md README.md _canon.yaml src/myco/ scripts/ → 待 Phase B 实测
grep -rn "docs/current" docs/ MYCO.md README.md _canon.yaml src/myco/ scripts/ → 待 Phase B 实测
```

**Defense**：
(1) **Phase A/B 分阶段执行** 降低爆炸半径：
    - Phase A（低风险）：只动 `wiki/→mycelium/`。因为 wiki 是空的且只在
      `_canon.yaml::write_surface` 出现一次，预估爆炸面 ≤ 5 处。
    - Phase B（中风险）：动 `docs/current/→docs/primordia/`。预估爆炸面
      15-30 处。必须在 grep 出全部引用后**原子地**改。
(2) **每一 Phase 后立即跑 14/14 lint**。L1 不 PASS 就 rollback 那一个 Phase，
    不带到下一个 Phase。
(3) **Grandfather 不适用于路径 rename**——L1 是 hard lint，不能豁免引用破损。
    但可以用 **symlink overlay** 作为过渡：在 Phase B 执行时先
    `ln -s primordia current`，让老引用继续 resolve，再逐一更新到新路径，
    最后删除 symlink。这是 Unix 世界的标准 rename 安全模式。

**Revise**：执行计划改为：
- Phase A1: `wiki/→mycelium/` + canon 更新 + 14/14 lint
- Phase A2: `docs/current/→docs/primordia/`，先建 symlink，
  再 grep + 改引用，再删 symlink，最后 14/14 lint
- 每个 Phase 独立 commit，允许 git revert 单点

### A4 · Downstream Instance Drift Attack

> "ASCC 等 instance 通过 `src/myco/templates/**` 同步 Myco 结构。如果你把
> `wiki/` rename 成 `mycelium/`，所有下游 instance 在下次 `myco init` 后
> 会得到 `mycelium/` 目录，但它们本地既有的 `wiki/` 怎么办？"

**Research**：查 `src/myco/templates/` 当前结构。

**Defense**：
- `src/myco/templates/` 是 `myco init` 生成新 instance 的模板——**只影响新
  instance**，不会覆盖既有 instance 的本地目录。
- 既有 instance 要升级到新 contract version 需要手动对比 canon diff，这是
  v1.2.0 以来的既定流程（`synced_contract_version` 机制）。
- 对下游的影响 = "下次升级时需要把本地 `wiki/` 内容移到 `mycelium/`"——
  这是一条一行的迁移指令，写进 contract_changelog 的 Migration 段即可。

**Revise**：contract_changelog v1.5.0 Migration 段必须显式列出 rename pair
供下游 agent 机械执行。

### A5 · Compression Authenticity Attack（压缩真实性攻击）

> "你说要压缩 docs/ 的 14 份文件。你怎么证明你压缩的是**冗余**而不是
> **有价值的差异**？合并 `architecture.md` + `theory.md` + `evolution_engine.md`
> 听起来很美，但如果它们实际上在不同受众 / 不同粒度 / 不同时态上工作，合并
> 就是破坏而不是压缩。"

**Defense**：
- **压缩判据必须可证伪**——每一对合并/删除都必须先写出"如果保留会损失
  什么信息"的反事实，如果反事实损失 > 0，就**不合并**。
- 本次 craft **不承诺具体合并哪几份**。只承诺：执行时用上述判据逐对评估。
  预期的保守合并候选（按信息损失风险从低到高）：
  1. `ascc_migration_v1_2.md` + `ascc_agent_handoff_prompt.md` →
     两者都是 "ASCC 如何迁移到 v1.2" 的手册，不同受众（agent vs human）
     但信息 85% 重叠。合并到 docs/instance_migration.md（proposed），保留两节区分受众。
     **风险：低**。
  2. `research_paper_craft.md` + `reusable_system_design.md` → 待读过原文
     才能判断。**本次 craft 不预先承诺合并**。
  3. `architecture.md` + `theory.md` + `evolution_engine.md` → 三份文档有
     历史分层，合并风险中等。**本次 craft 不预先承诺合并**，只登记为
     Phase C 的候选，留给后续独立 craft 决定。
- 压缩 Scope 明确为：只做 (1) 号合并，其他候选登记到 `open_problems.md §4`
  作为后续工作。

**Revise**：Claim B 从"压缩 docs/ 顶层 14 份"缩减为——
- ✅ 合并两份 ASCC 文档 → docs/instance_migration.md（proposed）
- 🔜 其他候选登记为后续工作，不在本次 craft 执行范围

### A6 · Reversibility / Young-Red-Line Attack

> "v1.4.0 才刚立 read/write 分离红线，才刚跑通第一次完整的 'open problem →
> craft → contract bump' pipeline。在红线还没干的时候立刻搞结构重组，是不是
> 太年轻？你是不是在 'contract-driven over-mutation' 上又加了一刀？"

**Defense**：这是最严肃的攻击。拆两层回应：

(1) **这次重构是否 over-mutation**：不是。因为它解决的是用户在 panorama 回顾
    中**明确指出的结构性盲点**（wiki 空 / docs 14 份 / 命名漂移），不是 Claude
    自主发明的 contract 添加。用户回灌了 selection pressure（"结构重构 + 压缩
    + 仿生"），craft 是对该选择压力的机械响应。

(2) **年轻红线是否被威胁**：不会。read/write 分离在 `notes.py::record_view`，
    这次重构**明确不动 notes/**，因此红线物理上不可能被触及。mycelium/ 和
    primordia/ 都不参与 D 层死知识 pipeline。

**Revise**：执行约束增加一条——**本次 craft 执行期间禁止修改 `src/myco/notes.py`
中与 record_view / compute_hunger_report 相关的任何代码**。这条被写进 §6
执行计划作为硬约束。

### A7 · Recurring Bloat Prevention Attack

> "你说要加一个 `structural_bloat` 信号防止未来 bloat。这个信号的**阈值**是
> 多少？30 份 docs？50 份？谁决定？如果阈值硬编码，你就是在 open_problems §4
> 复现同一个 'hard-coded threshold' 罪。"

**Defense**：**攻击完全成立**。
- 阈值必须走 `_canon.yaml::system` 作为 SSoT，instance 可覆盖。
- 默认阈值用**分布驱动**而不是绝对数字：docs/\*.md count > 1.5 * baseline
  其中 baseline 是上次 `[contract:*]` commit 时的数量。这样阈值随基质成长
  自动漂移，不会出现"基质长大了阈值没跟上"的僵化问题。
- 但本次 craft 只种下信号**种子**（类似 v1.4.0 dead_knowledge），不种
  完整的 adaptive 机制。Adaptive threshold 登记为未来工作。

**Revise**：Claim C 的 `structural_bloat` 信号采用**固定种子阈值**
（`docs_top_level_soft_limit: 20` / `docs_primordia_soft_limit: 40`），明确写
`_canon.yaml::system.structural_limits` block，并在
`contract_changelog.md v1.5.0 Known non-goals` 里明确声明"adaptive threshold
不在本次范围"。这是 grandfather + 种子哲学的一致应用。

### A8 · Biomimetic Map 永久性攻击

> "你加的 `docs/biomimetic_map.md` 也是一份新文档——它本身增加了 docs/ 的
> 数量。你解决 bloat 的方式是加更多文件，这是不是自相矛盾？"

**Defense**：部分成立。缓解方式：
- `biomimetic_map.md` 不是普通 doc，是 contract 级身份锚点文档——**必须
  存在的系统文档**，与 agent_protocol / craft_protocol / contract_changelog
  同级。这类文档不计入 `structural_bloat` 信号的分母。
- `_canon.yaml::system.structural_limits.exclude_paths` 显式列出 contract
  文档 allowlist，使它们对 bloat 信号透明。

**Revise**：canon 新增 `structural_limits` block 时包含 `exclude_paths` 字段。

---

## §3 Round 1 置信度评估

Round 1 之后，Claim 的真实形态已被攻击大幅收窄：
- **Claim A**：只改 `wiki/→mycelium/` + `docs/current/→docs/primordia/`
- **Claim B**：只合并 ASCC 两份迁移文档
- **Claim C**：新增 `biomimetic_map.md` + `structural_bloat` 固定种子信号 +
  canon `structural_limits` block

置信度自评：**0.84**（未达 0.90 kernel_contract floor，必须 Round 2）。
剩余不确定性集中在：
- Phase A2 symlink 过渡的 OS 兼容性（Windows instance 有没有 symlink 权限？）
- 合并 ASCC 文档时的 audience split 是否真的 85% 重叠（未实测）
- `structural_bloat` 信号的阈值 20/40 是否合理

---

## §4 Round 2 · 三条收尾攻击 + 防御

### R2.1 · Windows Symlink Viability Attack

> "ASCC 是 Windows 仓（用户 the creator 本地环境），Windows 的 symlink 需要管理员
> 权限或 Developer Mode。如果下游 instance 在 Windows 上跑 migration，symlink
> 会失败。你的 Phase A2 symlink 过渡方案对下游不可用。"

**Defense**：
- 本次 craft 的 symlink 方案**只用于 Myco 自身 repo 的 rename 过渡**，不要求
  下游 instance 使用 symlink。下游升级走 contract_changelog Migration 段的
  机械 rename 指令（`mv docs/current docs/primordia`）——git 识别为 rename
  不需要 symlink。
- 但 Myco 自身 repo 运行在沙箱 Linux 上，symlink 可用。Phase A2 安全。
- **Revise**：在 contract_changelog Migration 段明确写
  "下游 instance 执行 `git mv docs/current docs/primordia` 即可，无需 symlink"。

### R2.2 · ASCC Merge Authenticity Attack

> "你说 ASCC migration + handoff prompt 有 85% 重叠，但你**没有实际读过**
> 这两份文件。这是推测，不是观察。如果真实重叠只有 40%，合并就是信息损失。"

**Defense**：**攻击完全成立，必须实测**。
- 执行 Phase C 合并前，先 `wc -l` 两份文件，逐节对比，计算真实 overlap。
- 如果实测 overlap < 70%，**取消合并**，保留两份独立存在，在
  `docs/biomimetic_map.md` 里标注"两份文档定位差异已验证"。
- **Revise**：Phase C 的执行顺序改为——先读两份文件、量化 overlap、再决定
  合并与否。这条进入 §6 执行计划作为 gate。

### R2.3 · structural_bloat 信号 L 级归属攻击

> "`structural_bloat` 信号是放进 `myco hunger` 还是作为新的 L14 lint？两者
> 语义不同：hunger 是软信号（建议），lint 是硬约束（阻塞）。你选哪个？为什么？"

**Defense**：**选 hunger（软信号）**。
- Hunger 是代谢状态探针——告诉 agent"基质在这方面饿了/撑了"，驱动行为但
  不阻塞 commit。结构 bloat 是一个**渐进退化**问题，不是硬错误，硬 lint
  会让 normal development 被 bloat 警告卡死，带来摩擦负债。
- Lint 的语义是"违反 contract"。20 份 docs 本身不违反任何 contract，只是
  值得注意。语义错位。
- L13 §8 反向废弃标准提醒：**不要为了 'lint 越多越好' 而创造 lint**。
  `structural_bloat` 留在 hunger 层是对这条原则的尊重。
- **Revise**：`structural_bloat` 明确作为 `compute_hunger_report` 的新 signal，
  不新增 L14。同时这一决定本身进入 `docs/open_problems.md` 作为"L14 dead-on-arrival
  decision"的案例记录，供未来参考。

---

## §5 Round 2 置信度评估

Round 2 之后每个残留不确定性都被转化为**执行期的 gate**而非未解疑问：
- Windows symlink 风险 → 通过 contract_changelog 明确指令消除
- ASCC overlap 未实测 → 变成 Phase C 的 pre-execution gate
- L14 vs hunger 归属 → 明确选 hunger 并登记决策理由

置信度自评：**0.91**。

达到 kernel_contract floor 0.90。**craft 结论：Proceed**。

---

## §5b Round 3 · on-self-correction（Claim A1 被证伪后的紧急修正）

Round 2 结束后执行 Phase A1 前置 grep：

```
grep -rn "wiki" src/myco/ scripts/ _canon.yaml docs/ MYCO.md README.md
```

**实测 blast radius**（不是 Round 1 估计的 "≤5 refs"）：

- `src/myco/import_cmd.py`: **14 处**硬编码，包括整个 `hermes_skill_to_wiki()`
  函数（函数名本身含 "wiki"）+ `TARGET_MAP` 表里 5 处 `"wiki/"` 作为
  `target_location` 值 + `wiki_dir = project_dir / "wiki"` 的 mkdir 调用
- `_canon.yaml`: **5 处**，包括
  - `write_surface.class_y: wiki/**`（contract L11 内部分类）
  - `write_surface.allowed: wiki/`
  - `wiki_page_types:` 整个 schema block
  - `notes_schema` 注释里的 "lifted into wiki or MYCO.md"
  - `synced_structure.wiki_pages: 0` 计数器字段
- `docs/agent_protocol.md`: **4 处**概念级引用（wiki/*.md 是 write_surface
  class_y 的核心例子，`myco_extract` 未来工具的目标位置）
- `docs/architecture.md`: **6 处**架构级引用（wiki/*.md 作为 Myco 三层存储
  结构的第 1.5 层，是整个 architecture 文档的骨架概念之一）
- docs/ascc_agent_handoff_prompt.md + docs/ascc_migration_v1_2.md (since deleted): 4 处
- `README.md`: **9 处**，包括对外用户可见的 lint 输出示例、目录树图、
  Gear 3 触发条件描述、Self-Model D 层说明
- `MYCO.md`: **7 处**，包括 `§L1.5 Wiki` 行在热区文档索引里、启动 agent
  reading 顺序、"wiki/ 当前为空" 的 orient 性描述

**总计：~50 处引用，涵盖 code / canon schema / 6 个 contract 文档 /
对外 README / 热区 MYCO.md**。

---

### 为什么 Round 1 A1 的自我评估错了

Round 1 A1 防御里我写的是："wiki/ 完全不同：目前是**空目录**，rename 0
代码成本"。这句话**物理上为真**（目录确实空），但**语义上致命错误**——我把
"物理空" 和 "概念空" 混为一谈。`wiki/` 在 Myco 基质里是一个**哲学承诺**的
投影点（Karpathy LLM Wiki 血统 / Self-Model A 层的结构化部分 / class_y
write-surface 的典型 / Phase ③ Commons 的前置），它的**名字** 被 substrate
的理论文档和 onboarding 路径深度引用，目录是否有文件无关紧要。

这是一个教科书级的 "Map vs Territory 混淆"——我看了 territory（空 ls 输出）
就下了结论，没去看 map（文档 + 代码对这个名字的使用）。

---

### Revise（Claim A 第二次收窄）

Claim A 最终形态：

- ❌ **`wiki/` 不改名**——它是概念承载目录，rename 成本 50+ 处，且
  `wiki` 这个名字在 Karpathy LLM Wiki 的血统里本身就是正面语义
  （"distilled structured knowledge"），主动误导风险远低于 Round 1 估计。
  我之前说"wiki 暗示 MediaWiki 的 messy" 是过度推断。
- ✅ **`docs/current/` → `docs/primordia/`** 保留——这是 docs 内部 rename，
  只影响 docs 自身 + canon 1 处 + craft_protocol.md 1 处，blast radius
  可控（预估 10-15 处，实测前不再预承诺）。
- ✅ **生物学类比只进 `docs/biomimetic_map.md`**——所有未 rename 的目录
  （wiki/, notes/, src/, scripts/, docs/）都通过 map 文档声明其生物学
  类比 handle，**而不是** 改路径。

---

### Round 3 置信度调整

- Round 2 自评 0.91 的根基是 Phase A1 "低风险"——这个前提现在被拆除
- 但收窄后的方案（只 A2 + B + C，不 A1）**风险更低而不是更高**
- 同时这次 self-correction 本身是对 craft 质量的正面信号——craft 成功
  抓住了自己的 premise error 而不是盲目执行
- 基于更准确的 scope + 更诚实的 self-assessment：**0.92**

Round 3 的真正意义不是提高置信度数字，而是**在执行前纠正 craft 本身**。
这是 Craft Protocol §2 "Research 轮可触发 Revise" 机制的应用。

---

## §6 执行计划（v2 · Round 3 修订版）

### Phase A1 · ~~`wiki/ → mycelium/`~~ · **CANCELLED**

**原因**: Round 3 self-correction。`wiki/` 在代码 / canon schema / 6 份
contract 文档中有 ~50 处深度引用，rename 不是低成本 rename 而是高成本
cross-cutting refactor，且 `wiki` 这个名字在 Karpathy 血统里本身正向。
保留现名，通过 `docs/biomimetic_map.md` 登记其生物学类比。

### Phase A2 · `docs/current/ → docs/primordia/`（唯一的 rename Phase）

1. `grep -rn "docs/current" docs/ MYCO.md README.md _canon.yaml src/myco/ scripts/`
   → 列出全部引用点
2. `git mv docs/current docs/primordia`
3. 批量更新引用：`docs/craft_protocol.md`、`_canon.yaml::system.craft_protocol.dir`、
   MYCO.md 文档索引、README.md、所有 craft 内 cross-reference
4. 14/14 lint PASS → commit `[contract:minor] docs/current → docs/primordia rename`

### Phase B · 合并 ASCC 迁移文档（gated）

1. wc -l docs/ascc_migration_v1_2.md docs/ascc_agent_handoff_prompt.md (since deleted)
2. 读两份文件，逐节对比，量化 overlap
3. **Gate**：overlap ≥ 70% → 继续合并；< 70% → 跳过，更新 biomimetic_map 记录
4. 若合并：创建 docs/instance_migration.md（proposed），保留两份文件原有的两个 audience
   section（human onboarding / agent prompt），顶部加统一索引
5. 删除原两份，更新所有引用
6. 14/14 lint PASS → commit `docs: merge ASCC migration docs (human + agent)`

### Phase C · 永久机制（`biomimetic_map.md` + `structural_bloat` 信号）

1. 创建 `docs/biomimetic_map.md`（新，contract 级文档）：
   - §1 生物学 Myco 术语 glossary（hyphae / mycelium / primordia / sporocarp /
     rhizomorph / sclerotia / mycorrhiza / exoenzyme / spore）
   - §2 Myco substrate ↔ biology 映射表（当前已 rename 的路径 + 未 rename
     但保留生物学类比的概念）
   - §3 "为什么不全面重命名"——记录 A1/A2 攻击的结论，防止未来 agent
     重新发动相同的重命名冲动
2. `_canon.yaml::system` 新增 `structural_limits` block：
   ```yaml
   structural_limits:
     docs_top_level_soft_limit: 20
     docs_primordia_soft_limit: 40
     exclude_paths:
       - docs/agent_protocol.md
       - docs/craft_protocol.md
       - docs/contract_changelog.md
       - docs/biomimetic_map.md
       - docs/WORKFLOW.md
       - docs/vision.md
       - docs/theory.md
       - docs/architecture.md
       - docs/open_problems.md
       - docs/evolution_engine.md
   ```
3. `src/myco/notes.py::compute_hunger_report` 新增 `structural_bloat` 检测：
   - 扫描 docs/\*.md 数量（排除 exclude_paths）
   - 扫描 docs/primordia/\*.md 数量
   - 超过 soft_limit → 生成 `structural_bloat: docs/ has N files (soft limit M)` 信号
4. templates mirror sync → `synced_contract_version: v1.4.0 → v1.5.0`
5. 14/14 lint PASS + 真实 hunger smoke → commit
   `[contract:minor] Biomimetic structural overlay + structural_bloat signal — v1.5.0`

### 硬约束（Red Lines）

- ❌ **绝不修改** `notes/` 路径或 `src/myco/notes.py` 中 record_view /
  compute_hunger_report 现有逻辑（只新增 signal 函数，不改现有函数签名）
- ❌ **绝不修改** `src/`, `scripts/`, `docs/` 顶层目录名
- ❌ **绝不硬套**生物学名字到没有清晰对应的目录
- ✅ **每个 Phase 独立 commit**，允许单点 revert
- ✅ **每个 Phase 后 14/14 lint 必须 PASS** 才进入下一 Phase

---

## §7 反向废弃标准（Reverse Sunset Criteria）

本 craft 的产物（`mycelium/` 命名、`primordia/` 命名、`structural_bloat` 信号、
`biomimetic_map.md`）在以下任一条件满足时应当被重新审视：

1. **Dead naming**：`mycelium/` 或 `primordia/` 在下游 instance 或对外沟通中
   持续造成误解（累计 ≥3 次 friction-phase2 tag 的 note），触发 "rename back"
   craft。
2. **Dead signal**：`structural_bloat` 信号 90 天内未触发一次 → 阈值太松，
   需要重评或废弃。反之若 30 天内触发 ≥5 次 → 阈值太紧或基质真的在 bloat，
   需要决定是调阈值还是启动压缩 craft。
3. **Better replacement**：如果出现"adaptive threshold"或"cross-reference
   density lint"等更精确的 bloat 检测方法，`structural_bloat` 应当降级
   或废弃。
4. **Biomimetic Map 死信息**：如果 `biomimetic_map.md` 90 天内未被任何 craft /
   log / MYCO.md 引用，它就是死知识，D 层会自动标记。

这条反向废弃承诺是 L13 §8 的一贯应用——本 craft 出生就带自己的退出计划。

---

## §8 与既有 contract 的集成矩阵

- **L11 write_surface**：canon 同步更新 `wiki/ → mycelium/`
- **L1 reference integrity**：每 Phase 后 grep + lint 双验证
- **L10 notes schema**：不受影响（notes/ 不动）
- **L13 craft_protocol**：本 craft 自身满足 schema（kernel_contract class + 0.91）
- **Craft Protocol dir**：从 `docs/current/` 更新为 `docs/primordia/`，canon 同步
- **D 层 dead_knowledge**：不受影响（read/write 红线严守）
- **Upstream Protocol (L12)**：不涉及，仅 substrate 内部结构变动
- **Contract Changelog**：v1.5.0 entry + Migration 段（含 git mv 指令）

---

## §9 最终结论

本 craft（Round 3 修订后）授权以下三阶段三 commit 的结构重构：

| Phase | 动作 | Contract | 风险 |
|---|---|---|---|
| ~~A1~~ | ~~wiki/ → mycelium/~~ | — | **CANCELLED (R3)** |
| A2 | `docs/current/ → docs/primordia/` | v1.4.0 → v1.4.1 (patch) | 中 |
| B  | ASCC 文档合并（gated by overlap ≥70%） | 非 contract | 低 |
| C  | biomimetic_map + structural_bloat + v1.5.0 bump | v1.4.1 → v1.5.0 (minor) | 中 |

**置信度 0.92（Round 3 后），达到 kernel_contract floor。授权执行。**

所有 Phase 之间允许停顿接受用户 intervention，但不 require。user 授权
自主推进至 v1.5.0 commit，完成后进入下一次 panorama 或待用户信号。

---

**Dogfood commitment**: 本 craft 的结论会被
`myco eat` 成一条 note（tags: meta, biomimetic, structural-compression,
decision-class-kernel_contract, friction-phase2），进入基质的消化道。
这是本次 craft 作为 meta-conclusion 的自我吞食。
