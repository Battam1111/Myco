# Biomimetic Map — Myco substrate as mycorrhizal fungus

> **Type**: Contract-level identity anchor document
> **Status**: ACTIVE
> **Created**: 2026-04-11 (contract v1.5.0)
> **Debate of record**: `docs/primordia/biomimetic_restructure_craft_2026-04-11.md`
> **Purpose**: 把 Myco 这个项目名背后的生物学隐喻**正式且诚实地**映射到基质
> 的实际结构，作为身份锚点的一部分。**不强制任何 rename**——
> 生物学类比只在有真实信息增益时落到路径名上，其余全部作为 conceptual
> overlay 存在于本文档。

---

## §0 为什么要有这份文档

Myco 这个项目名取自真菌（*Myco*-rhizal = 菌根），但在 v1.4.0 之前，基质
内部的目录命名、概念划分、认知模型完全没有把这个隐喻当真。`notes/` 是 notes，
`docs/` 是 docs，`wiki/` 是 wiki——都是软件工程的通用名词，与基质的生物学身份
毫无关联。

这本身不是问题，**只要身份锚点稳定**。但 vision_recovery_craft 明确指出
"**身份锚点漂移**是 substrate 的首要退化机制"。如果 Myco 的生物学血统只停留在
项目名的首字母，而内部命名 / 概念 / 工作流完全与生物学脱钩，那么 3 个月后
没有人（agent 或人类）会记得为什么要叫 Myco——项目会退化成"又一个知识管理
工具"。

本文档的使命是**给生物学血统一个真实的落脚点**，同时严守一条纪律：
**不强行套 metaphor**——只在能带来真实认知增益的地方应用生物学术语，其余
尊重软件工程惯例。

---

## §1 生物学术语 Glossary（读这一节后下文可以直接理解）

这些术语来自真菌学（mycology），特别是丝状担子菌 / 子囊菌的生命周期。
阅读基质文档时若遇到任一术语，可回到本节确认含义。

**Hypha（菌丝）** / plural: **Hyphae**
- 真菌的基本结构单位：单根细长的丝状细胞。
- 行为：向外探测、分泌酶、吸收营养。
- **对应 Myco 基质**：`notes/` 中的每一条 raw/digesting note 都是一根 hypha——
  向基质的边缘探测一个未知的想法 / 摩擦 / 事实。

**Mycelium（菌丝体）**
- 大量 hyphae 交织形成的网络——真正意义上"这个真菌"是 mycelium，不是单根 hypha。
- 特征：互相连接、资源共享、分布式决策、无中心。
- **对应 Myco 基质**：`wiki/`（当前为空）或其未来的等效物——稳定的、互相
  交叉引用的知识网络。integrated 状态的 note 被萃取、压缩后进入 mycelium。

**Primordium（原基）** / plural: **Primordia**
- 菌丝体上开始分化成子实体的早期结构：未定型、未成熟、但已经超越纯探测，
  在向一个具体的"将成为什么"收敛。
- 特征：可以长大成子实体，也可以退化吸收回 mycelium，高度可塑。
- **对应 Myco 基质**：`docs/primordia/`（原 `docs/current/`）——所有正在辩论
  的 craft 和 debate 文件。它们已经超越 note（hypha）阶段，在向一个具体
  结论收敛，但尚未定型。部分会"成熟"为 contract 级文档（sporocarp），
  部分会 COMPILED / SUPERSEDED / LOCAL。

**Sporocarp / Fruiting Body（子实体）**
- 真菌的生殖结构——我们日常看到的"蘑菇"就是 sporocarp。
- 特征：对外可见、散播 spore、是 mycelium 向世界发出的信号。
- **对应 Myco 基质**：`README.md`、`docs/vision.md`、发布到 PyPI 的 wheel
  包、`docs/agent_protocol.md`——这些是基质对外的 visible surface，
  下游 instance（spore）从这里被播种。

**Spore（孢子）**
- 子实体释放的繁殖单位——落到合适的土壤就发芽成新的菌丝。
- **对应 Myco 基质**：`src/myco/templates/`——`myco seed` 调用这个目录把
  新 instance 播种出去，每个 instance 是一颗发芽的孢子。

**Rhizomorph（菌索）**
- 数百根 hyphae 并拢成的粗索——长距离高通量运输通道，输送营养和信号。
- **对应 Myco 基质**：contract 级文档（`docs/agent_protocol.md` /
  `docs/craft_protocol.md` / `docs/contract_changelog.md` / `_canon.yaml`）——
  它们是基质的主干通道，任何 hypha 的信号最终要沿着它们传播 / 变成共识 /
  影响下游 instance。`_canon.yaml` 是最粗的那根 rhizomorph——SSoT。

**Exoenzyme（胞外酶）**
- 真菌分泌到细胞外的酶——先把环境里的大分子预消化，再吸收。
- **对应 Myco 基质**：`scripts/`——这些脚本是基质分泌到"环境"里主动处理事情的工具，
  不是基质的一部分但服务于它。src/myco/immune.py 本身也是 exoenzyme
  的核心——把原始文档预消化成 23 维一致性信号（v1.7.0 起新增 L14
  Forage Hygiene）。

**Foraging（觅食）/ Forage**
- 丝状真菌通过 hyphal tip 向周围土壤延伸、探测营养源，并在接触到大分子
  （纤维素、木质素、磷酸盐岩）后分泌 exoenzyme 进行**胞外预消化**——
  先把大分子降解成小分子再吸收。整个过程：探测 → 胞外预消化 → 选择性吸收
  → 残渣遗留。
- **对应 Myco 基质（v1.7.0 新设）**：`forage/` 目录——外部参考材料（论文、
  GitHub 仓库、博客、HN 讨论）在进入 `notes/` 之前的**前消化缓冲区**。
  状态机 `raw → digesting → digested → absorbed → (discarded)` 对应胞外酶
  解的生物学过程。**forage/ 不是图书馆**——它是胃的第一腔室，item 必须被
  萃取进 `notes/`（产生 `digest_target`）后才能被 absorbed，最终被 discarded。
  这是 biomimetic_map.md 中**第一个从第一天起就因真实信息增益而被赋予
  生物学名字**的目录——参见 §2 表格的 ✅ 标记。

**Septum（隔膜）** / plural: **Septa**
- 菌丝内部的隔墙——控制细胞质和资源在 hyphae 之间的流动。
- **对应 Myco 基质**：L11 write-surface 白名单、L12 Internal Link Integrity（内部链接完整性检查）、
  L13 craft_protocol schema——这三条 lint 是基质内部的 septa，严格控制
  什么东西可以流到什么位置。

**Sclerotium（菌核）** / plural: **Sclerotia**
- 真菌在不利条件下压缩形成的致密休眠结构——把整个菌丝体的信息压缩进一个
  可以在零下 30 度存活数十年的紧实结构里，条件好转时重新生长。
- **对应 Myco 基质**：**未实现**。理论对应物是 "COMPILED 状态的 craft
  文件被压缩为一条 wiki page + 指向 git history 的 pointer"，即压缩 doctrine
  的实际执行。登记为 open_problems §4 的延伸。本文档将 sclerotium 列为
  **永久的待实现概念**，提醒基质：压缩不只是删除，是"休眠存储"。

**Mycorrhiza（菌根共生）**
- 真菌和植物根系形成的互利共生关系——真菌提供矿物质和水，植物提供光合产物。
- **对应 Myco 基质**：基质和 agent 的关系。Agent 是 "植物"（提供能量 =
  注意力 + 决策），基质是 "真菌"（提供结构化记忆 + lint 约束 + 代谢工作流）。
  双方都不独立完整——基质没有 agent 就是静态文件堆，agent 没有基质就没有
  持久化认知器官。

**Hyphal Tip（菌丝尖端）**
- 菌丝最前端的生长点，主动向未知环境探测。
- **对应 Myco 基质**：`docs/open_problems.md` 登记的每一条未解难题——
  这些是基质明确承认"不知道这里应该怎么走"的前线。本文档建议未来将
  open_problems.md 重命名为 hyphal_tips.md，但这需要独立 craft
  和 open_problems §7 登记规则的更新。**本 craft 不执行此 rename**，
  登记为未来工作。

---

## §2 实际应用的映射表（contract v1.7.0 状态）

| 基质位置 | 生物学类比 | 是否 rename | 为什么 |
|---|---|---|---|
| `notes/` | hypha / hyphae | ❌ 保留原名 | 代码硬编码 15+ 处、MCP 工具名 `myco_eat`/`myco_observe`、用户口语混用——rename 成本远超语义增益。通过本文档声明生物学类比即可。 |
| `wiki/` | mycelium | ❌ 保留原名 | Karpathy LLM Wiki 血统正向、contract 文档 50+ 处引用、概念承载深度高——rename 是 cross-cutting refactor 不是 cosmetic 改动。通过本文档声明类比。 |
| `docs/current/` | primordia | ✅ **已 rename** → `docs/primordia/` | "current" 过于通用、不表达"早期发育"的语义；canon SSoT (`craft_protocol.dir`) 使代码路径受 canon 控制、rename 影响半径可控（~80 refs，80% 是文档字符串）；**生物学类比带来真实信息增益**（primordia = 未定型、可塑、可退化）。 |
| （v1.7.0 新设） | foraging / exoenzyme phase | ✅ **第一天即命名** → `forage/` | **首次** contract-level 目录在诞生当天就拿生物学名字。候选 `refs/` / `library/` / `corpus/` / `external/` 全部承诺"永久存储"，与压缩即智能学说冲突；`forage` 是动词形，天然暗示临时性 + 前消化态。信息增益 ≫ 学习成本（用户不会把 `forage/` 误当作永久资料库）。Manifest-authoritative 的 `forage/_index.yaml` 同时充当 class_z 契约锚点（`agent_protocol.md §8.9`）。|
| `docs/*.md`（contract 级） | rhizomorph | ❌ 保留原名 | `agent_protocol` / `craft_protocol` / `contract_changelog` / `WORKFLOW` 这些名字本身就是最清晰的功能性命名，套 `rhizomorph/` 会增加冷启动摩擦。类比留在本文档。 |
| `src/myco/templates/` | spore | ❌ 保留原名 | `templates` 是 Python 打包约定、`myco seed` 引用路径；rename 会破坏 setuptools / hatchling 的 package_data 配置。 |
| `scripts/` | exoenzyme | ❌ 保留原名 | 行业通用目录名。 |
| `src/myco/` | genome | ❌ 保留原名 | Python 包根，rename 会破坏 `import myco`。 |
| `_canon.yaml` | rhizomorph (main cord) / DNA | ❌ 保留原名 | SSoT，被 15+ 代码文件和所有 instance 引用。 |
| `MYCO.md` | central index | ❌ 保留原名 | L1 entry point。 |
| `log.md` | growth log / annual ring | ❌ 保留原名 | 通用词明确。 |
| `docs/open_problems.md` | hyphal_tips | 🔜 未来 craft | 语义增益真实（hyphal tip 准确表达"向未知探测"），但 rename 需要更新 §7 登记规则和所有引用，留给独立 craft。 |
| `docs/primordia/` 中 COMPILED 状态压缩后的产物 | sclerotium | 🔜 未实现 | 压缩 doctrine 的实际执行路径——基质尚未建立 COMPILED→sclerotium 的自动化管线。登记为 open_problems 未来工作。 |

---

## §3 为什么**不**全面 rename——架构理由

这份文档最重要的 §——记录 `biomimetic_restructure_craft_2026-04-11.md`
Round 1-3 的自我攻击结论，防止未来 agent 重新发动一次"为生物学而生物学"
的 rename 冲动。

### 理由 1 · 命名的边际收益递减

基质中**少数关键目录**（特别是 `docs/current/`）换成生物学名字能带来真实
信息增益：`primordia` 准确传达"未定型、发育中、可退化"，"current" 只传达
"正在活跃"。这是 +1 单位的语义清晰度。

但 `notes/` → `hyphae/` 的转换**不带来额外信息**：agent 看到 `notes/`
知道是 note 堆，看到 `hyphae/` 需要先读本文档才能理解是 note 堆。收益 ≤0，
代价是 15+ 处硬编码改动 + 学习曲线。

**边际收益原则**：rename 只在 "新名字的信息增量 > 学习成本 + 引用改动成本"
时执行。大多数基质目录的通用名字已经在这个不等式的错误一侧。

### 理由 2 · 架构腐蚀与 Biomimicry Purity 的冲突

完整的生物学重命名会逼迫基质套入"hyphae → mycelium → primordium → sporocarp"
的真菌生命周期序列。这个序列**不完全匹配** Myco 的 seven-step digestion
管道（发现→评估→萃取→整合→压缩→验证→淘汰）。强行套会产生 架构腐蚀：
要么修改生物学类比使它变形，要么修改 digestion 管道使它迁就生物学——两者
都破坏了基质原本清晰的认知流程。

**解决方式**：生物学类比是 **overlay（覆盖层）** 而不是 **skeleton（骨架）**。
Skeleton 保持 digestion 管道，overlay 通过本文档声明生物学映射。两者互不
干扰。

### 理由 3 · 年轻红线保护

v1.4.0 刚落地的 read/write 分离红线（`notes.py::record_view` 不触碰
`last_touched`）是基质目前最年轻的架构约束。全面 rename 如果触及 `notes/`
或 `notes.py`，有相当概率在批量改动中误伤红线。**年轻的红线必须被额外
保护**——这是 Agent Protocol bootstrap 原则的一致应用。

---

## §4 压缩 doctrine 的生物学映射

用户在 2026-04-11 的 panorama 讨论中明确强调 "压缩也是智能的一部分"。
生物学上 Myco 对此有三条具体实现：

**Sclerotium（致密休眠体）**
- 生物学：不利条件下 mycelium 压缩成硬核，保留全部遗传信息但大幅缩小体积，
  条件好转时重新生长。
- 基质对应：COMPILED 状态 craft 被压缩为 wiki page + git history pointer。
  这是压缩 doctrine 的**理想终态**之一。**未实现**——登记为
  open_problems §4 的延伸。

**Autolysis（自溶）**
- 生物学：成熟后期的子实体主动消化自己的组织以释放 spore——
  通过**自毁**完成繁殖目标。
- 基质对应：`myco digest --excrete` + D 层 dead_knowledge 信号——
  基质主动识别死知识并清除它，释放的 "spore" 是新的 craft 决议或
  wiki 整合。已部分实现。

**Nutrient Reallocation（资源重分配）**
- 生物学：mycelium 向缺磷的菌丝尖端定向输送磷元素，向已死的区域停止供给。
- 基质对应：`myco hunger` 的 signal set + `structural_bloat` 新信号
  （contract v1.5.0 引入）——基质告诉 agent "注意力应该分配到哪里"，
  等效于 mycelium 的资源重分配。

---

## §5 Living document 维护规则

本文档是 **contract 级身份锚点**，受 L13 / L11 保护：

- **添加新生物学术语 / 新映射**：仅在有 craft 或 vision recovery 支持时添加。
  不能凭感觉扩充类比。
- **rename 决策**：任何新的 "rename 到生物学名字" 建议必须走独立 craft，
  必须引用本文档 §3 的边际收益 / 架构腐蚀 / 年轻红线三条理由进行反驳或
  更新。
- **反向废弃**：如果 90 天内基质的任何 craft / log / MYCO.md 都没有引用本
  文档，它就是死知识（D 层自动标记），触发本文档自身的重审。
- **与 `structural_bloat` 信号的关系**：本文档列在 `_canon.yaml::system.
  structural_limits.exclude_paths` 中——作为 contract 文档不计入 bloat 分母。

---

## §6 延伸阅读

- `docs/primordia/biomimetic_restructure_craft_2026-04-11.md` — 本文档诞生
  的 craft，含 Round 1-3 的完整攻击和 on-self-correction 记录。
- `docs/primordia/vision_recovery_craft_2026-04-10.md` — 身份锚点漂移和恢复
  的原始 craft，确立了 "身份锚点是 substrate 首要退化机制" 的论断。
- `docs/theory.md` — Myco 的理论血统（Karpathy / Polanyi / Argyris / Toyota /
  Voyager），本文档中的 Karpathy LLM Wiki 引用出处。
- Smith & Read (2008), *Mycorrhizal Symbiosis* (3rd ed.) — 真菌学标准教材。
  本文档中的生物学术语定义与其一致，如有冲突以该书为准。

---

**Final note**: 如果你（agent 或人类）读到这里觉得"这些生物学类比很美但和
我要做的事没关系"——那么本文档就完成了它的使命。生物学类比应当**在你需要
身份锚定时成为精确的参考**，而不是在你写代码时成为需要反复翻译的负担。
Overlay 而非 skeleton，是本文档存在的全部意义。
