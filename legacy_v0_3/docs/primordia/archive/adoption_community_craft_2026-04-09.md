# 传统手艺：一键采用 + 社区生态设计

> **文档状态**：[ARCHIVED] | 创建：2026-04-09
> **置信度目标**：>88%
> **前置基础**：
> - positioning_craft_2026-04-09.md Round 5 已确立愿景（pip install、渐进式上手、社区贡献=进化产物）
> - 创始人核心洞察："Myco 理论上能把它们全部吃掉"——这是不可复制的护城河
> **本文档目的**：把愿景转化为**可立即执行的具体机制**。聚焦三个尚未有实现方案的问题：
> 1. Adapter 接口：v0.x 的 adapter 长什么样？（协议层面，不是 CLI）
> 2. 社区飞轮：知识贡献如何从 Gear 4 流入社区再流回 Myco？
> 3. 30 秒上手：第一个用户的"啊哈时刻"到底是什么、如何设计？

---

## Round 1：Adapter 接口设计 — v0.x 能做到什么？

### 1.1 问题的精确定义

用户有工具（OpenClaw、Hermes、MemPalace），Myco 说"我能吸收它们"。但在 v0.x 没有 CLI import 的情况下，"吸收"的具体操作路径是什么？

如果我们不给出一个**即时可操作的路径**，"生态吞噬"就只是 README 里的美好愿景，用户不会尝试。

### 1.2 初始提案

**提案 A：Adapter YAML Manifest**

每个外部工具有一个 YAML manifest，定义：
- 导入映射（哪些文件 → Myco 哪个层）
- 前置检查（验证工具输出是否符合 Myco 格式要求）
- 手动步骤说明（v0.x 不能自动化，但至少有书面协议）

```yaml
# adapters/hermes.yaml
name: Hermes Agent
version: "0.1"
description: Import Hermes skill files into Myco's evolution cycle
source_type: skill_directory     # Hermes 的 ~/.hermes/skills/
target_layer: L1.5_wiki          # 或 L2_docs，取决于 skill 性质

import_steps:
  1: "Copy skill .md files to wiki/ (procedure skills) or docs/ (operational skills)"
  2: "Run: myco lint --project-dir . to verify consistency"
  3: "For each imported skill, add a 'Last-reviewed' date entry to log.md"
  4: "Tag skills that haven't been used in 30+ days with ⚠️ for Gear 2 review"

layer_mapping:
  "SKILL.md (procedural)": "wiki/{skill_name}.md"
  "SKILL.md (operational)": "docs/operational_narratives.md (append)"
  "MEMORY.md (hermes)": "MYCO.md §Hot Zone (merge relevant context)"

lint_checks:
  - "wiki pages follow W8 template (type header + Back-to footer)"
  - "no cross-reference broken after import"
  - "_canon.yaml wiki_pages count updated"

value_proposition: |
  Your Hermes skills become mortal — Myco's Gear 2 review cycle flags
  skills that haven't been used or referenced in 30+ days.
  Gear 3 questions whether the skill's underlying assumptions still hold.
  Gear 4 distills universal patterns back into Myco templates.
```

**挑战 C1**：这个 YAML 是给谁看的？用户的 Hermes 文件夹可能有 50 个 skills——手动复制 50 次、每次都要记住这些 steps，这不是"adapter"，这是"说明书"。

**防御**：

Adapter 在 v0.x 的正确定位不是"一键工具"——那是 v1.0 的事。v0.x 的 adapter 是**协议契约**，为三个目的服务：

1. **社区贡献指南**：告诉用户"如果你有 Hermes skills 想导入，这是已验证可行的流程"
2. **v1.0 的接口规范**：将来 `myco import --from hermes` 这个 CLI 命令的实现，就是把这个 YAML 自动化
3. **"吞噬"的可信性证明**：用户看到具体的文件映射和 lint 检查，知道这不是空话

**对 Adapter 粒度的调整**：把"50 个 skills 全导入"的场景换成"精选 5 个最有价值的 skills 导入"的场景——这才是 v0.x 的正确使用方式。batch import 是 v1.0。

**挑战 C2**：同一个 YAML manifest 对不同工具需要不同的内容。是不是应该给每个工具一个单独的文件而不是一个通用格式？

**回应**：YES——每个工具一个独立文件，但共享同一个 schema。这正是 `adapters/` 目录的设计：
```
adapters/
├── README.md          # adapter schema 说明
├── openclaw.yaml      # OpenClaw → Myco
├── hermes.yaml        # Hermes → Myco
├── mempalace.yaml     # MemPalace → Myco (L0 backend)
└── letta.yaml         # Letta → Myco
```

### 1.3 MemPalace 的特殊性

MemPalace 是 L0 后端候选，不是知识内容导入。它的 adapter 逻辑完全不同：

```yaml
# adapters/mempalace.yaml
integration_type: L0_backend     # 不是内容导入，是检索后端替换
deployment: local_service        # MemPalace 是本地服务

usage_pattern:
  when: "need deep semantic search across archive"
  how: "query MemPalace → retrieve relevant context → feed into Myco's L1 hot zone"
  
value_proposition: |
  MemPalace handles the 'where did I put that?' problem (96.6% R@5).
  Myco handles the 'is that still true?' problem.
  Together: perfect recall + living metabolism.
```

### 1.4 Round 1 结论

**Adapter 设计决策**：
- v0.x：YAML manifest 作为协议契约（手动操作 + lint 验证）
- 目录结构：`adapters/` 顶级目录，每工具一文件，共享 schema
- v1.0：CLI 命令是 YAML manifest 的自动化实现
- MemPalace：特殊的 L0 backend 类型，不是内容 import 类型

**置信度：88%**

---

## Round 2：社区飞轮 — Gear 4 如何变成社区货币？

### 2.1 核心机制设计

**现有基础**（CONTRIBUTING.md 已建立）：
- Level 1：Battle report → 小故事
- Level 2：Battle report + evolution timeline → Featured example  
- Level 3：Distilled knowledge → 贡献到 Myco templates

Level 3 是关键——但"贡献 distilled knowledge"对用户来说具体意味着什么？

### 2.2 贡献类型分类

**挑战 C3**：当前 CONTRIBUTING.md 说"最有价值的贡献是知识进化产物"，但没有具体说这些产物是什么格式、提交到哪里、谁来审核。这导致用户不知道从哪里开始。

**解决方案：四种具体贡献类型**

| 类型 | 内容 | 提交位置 | 审核标准 |
|-----|------|---------|---------|
| **Template** | 新的 MYCO.md 分级模板（特定项目类型） | `src/myco/templates/` PR | 在 ≥1 个真实项目上验证过 |
| **Wiki Template** | 新的 wiki 页面类型模板 | `docs/wiki_templates/` PR | 覆盖的场景在现有 5 类之外 |
| **Lint Rule** | 新的 lint 检查维度 | `scripts/lint_knowledge.py` PR + docs | 捕获过 ≥1 次真实 bug |
| **Adapter** | 外部工具 → Myco 的 YAML manifest | `adapters/` PR | 手动测试通过，有使用示例 |
| **Workflow Principle** | 新的 W-NNN 原则 | `docs/WORKFLOW.md` PR + 传统手艺辩论 | 通用性：适用于 ≥2 种项目类型 |

### 2.3 飞轮机制

```
用户使用 Myco（任何项目）
         ↓
Gear 1-3 积累 friction + reflection
         ↓
Gear 4 session-end sweep：识别 g4-candidate
         ↓ (发现通用模式时)
用户提炼 → 选择贡献类型（Template/Lint/Adapter/Principle）
         ↓
提交 PR → 审核：≥2 种项目类型通用性检验
         ↓ (审核通过)
合入 Myco → 下一个用户安装时自动获得
         ↓
下一个用户用这个新 template/adapter 启动 → 更快的 Gear 4 → 更多贡献
```

**挑战 C4**：这个飞轮太理想化了。用户执行 Gear 4 已经有摩擦，让他们再写一个 PR——摩擦翻倍。实际用户会做这件事吗？

**回应**：

这取决于贡献成本的高低。对比开源生态：
- 代码 PR：高摩擦（需要理解代码库、写测试、应对 review）
- Myco 贡献：低摩擦（一个 YAML 文件或几行 Markdown）

Adapter YAML 的贡献成本极低：用户导入了 Hermes skills，总结了步骤，把总结写成 YAML，提交一个 400 字的文件。这比写一个 Python function 的 PR 门槛低得多。

**真正的障碍**是**可见性**——用户需要知道这种贡献是被期待和被欢迎的。解决方案：
1. CONTRIBUTING.md 把 adapter 贡献写成"最小可行贡献"（not code, just YAML）
2. README 的 Works With 表格里，每个工具旁边有"[adapter by community]"链接
3. GitHub issue 模板里有"Submit an Adapter"类型

**挑战 C5**：审核标准"≥2 种项目类型通用性"谁来判断？这需要 maintainer 专门评审——v0.x 只有一个创始人，不可扩展。

**回应**：

v0.x 阶段审核策略调整：
- **Template/Adapter**：放宽标准 → "在 ≥1 个真实项目上验证"即可（不要求 2 种类型）
- **Lint Rule**：严格标准 → 必须"捕获过 ≥1 次真实 bug"（有实证）
- **Workflow Principle**：最严格 → 保持"≥2 种项目类型"（进入核心协议）

这样：
- 低成本贡献（adapter/template）进入门槛低，社区快速成长
- 高影响力贡献（lint rule/principle）保持质量门槛

### 2.4 Round 2 结论

**社区飞轮机制**：
- 四种贡献类型（Template、Lint Rule、Adapter、Workflow Principle）
- 分级审核标准（低成本贡献宽松、高影响贡献严格）
- 贡献路径在 CONTRIBUTING.md 中有明确的"第一次贡献"引导

**置信度：87%**

---

## Round 3：30 秒上手 — "啊哈时刻"在哪里？

### 3.1 用户旅程设计

**目标用户细分**（基于 positioning_craft Round 1 的市场分层）：

| 用户类型 | 起点 | 期望的"啊哈时刻" | 进入 Myco 的动机 |
|---------|-----|--------------|--------------|
| **CLAUDE.md 用户** | 有 CLAUDE.md，遇到知识腐烂或一致性问题 | `myco migrate` 一键升级 + `myco lint` 发现第一个不一致 | "我的 CLAUDE.md 终于有质量保障了" |
| **OpenClaw 用户** | 有 MEMORY.md，但知识变多后开始乱 | `myco migrate` 把 MEMORY.md 映射进四层架构 | "我的记忆终于有结构了" |
| **全新用户** | 零基础 | `myco init` → 30 秒得到结构化项目 | "原来知识管理可以这么做" |

**最强优先级：CLAUDE.md 用户**——因为 `myco migrate --entry-point CLAUDE.md` 是 v0.x 唯一真正的代码级 adapter。

### 3.2 CLAUDE.md 用户的完整旅程

```
Step 0（10s）：pip install myco

Step 1（20s）：myco migrate ./my-project --entry-point CLAUDE.md
  → 输出：migration_report.md（做了什么 + 建议下一步）
  → 创建：_canon.yaml（从 CLAUDE.md 已有信息提取）
  → 创建：log.md（第一条 milestone 条目）
  → 保留：CLAUDE.md（不破坏已有内容）

Step 2（第一次 lint，5s）：myco lint --project-dir .
  → 概率很高：发现 1-2 个不一致（CLAUDE.md 里的数字 vs 实际文件）
  → 这就是"啊哈时刻"：用户看到 lint 报告，说"原来有这些我没意识到的不一致"

Step 3（自然发生）：下一次工作会话，遇到摩擦
  → MYCO.md 提示：记录到 log.md（Gear 1）
  → 几天后：Gear 2 会话反思

Step 4（第一个月末）：知识库开始有价值
  → lint 的 pass rate 提升（说明知识质量在提高）
  → 第一次 Gear 3：发现系统本身的问题
```

**关键设计决策**：Step 2 的"啊哈时刻"必须保证。

**挑战 C6**：如果 lint 在 Step 2 发现 0 个问题（用户 CLAUDE.md 很规范）——啊哈时刻就没了，用户感觉"Myco 没啥用"。

**回应**：

1. 用户 CLAUDE.md 里有 0 个不一致的概率很低（lint 不只检查数字，还检查引用完整性、孤儿文档等）
2. 就算 lint 全绿——migration_report.md 会说"你的 CLAUDE.md 已经是 Myco L1 了，运行第一次项目后，Gear 2 会给你真正的洞察"
3. 全绿本身也是一个积极信号（"我的知识系统是健康的"）

但为了保障更好的第一次体验，migration 可以设计一个"发现机会"的模式——除了报告发现的问题，还报告"如果你添加这些，Myco 会更强"（比如：wiki/ 目录为空 → "你有 X 个会话了，可以考虑开始你的第一个 wiki 页面了"）。

### 3.3 install → 第一个 lint 的 README 优化

当前 README 的 Quick Start 部分已经有正确内容，但顺序不够优化。最强的"第一次用户"路径应该放在最显眼位置：

**当前结构**（按我们设计的三种用户场景依次排列）：

```bash
# NEW PROJECT
myco init my-project

# MIGRATION FROM CLAUDE.md（最强 v0.x hook，应该放第一）
myco migrate ./existing-project --entry-point CLAUDE.md

# OPENCLAW USERS（第二强）
myco migrate ./existing-project
```

**建议优化顺序**：
```bash
# Already have a Claude Code project? (Most common path)
pip install myco
myco migrate . --entry-point CLAUDE.md   # Non-destructive, keeps your CLAUDE.md
myco lint --project-dir .                 # See what's inconsistent (usually something is)

# Starting fresh?
myco init my-project --level 2
```

把 "Already have a Claude Code project?" 作为最突出的路径，因为这是 v0.x 最可靠的第一次体验。

### 3.4 Round 3 结论

**30 秒上手策略**：
- 最优先目标用户：CLAUDE.md 用户（已有 Claude Code 项目的人）
- 最强啊哈路径：migrate → lint → 发现第一个不一致
- README Quick Start 重排序：migration first，init second

**置信度：90%**

---

## Round 4：GitHub 存在感 — 把访客变成用户

### 4.1 当前 README 的结构审查

当前 README 结构（顺序）：
1. Header + tagline ✅
2. What Myco Is ✅
3. Three Immutable Laws ✅
4. Why Myco? ✅（包含 Evolution Landscape 表格）
5. Works With ✅
6. Quick Start ⚠️（顺序需调整）
7. Project scaffold ✅
8. Framework-level knowledge 表格 ✅
9. Bootstrap Levels ✅
10. Five Core Capabilities ✅
11. Twelve Principles ✅
12. Evolution Engine ✅
13. Philosophy ✅
14. Status ✅
15. Project Adaptation ✅
16. License + Contributing ✅

**问题**：README 对新访客来说太长了，核心价值在前三屏，但 Twelve Principles 和 Evolution Engine 是内容"沉降区"——很多用户不会读到。

**挑战 C7**：有些用户只看前 3 屏就决定了 star/skip。当前前三屏（tagline + What Myco Is + Three Immutable Laws）是否足够吸引人？

**回应**：

当前前三屏存在一个问题：Three Immutable Laws（入口可达/透明可理解/永恒进化）对新用户太抽象。用户不知道"入口可达"是什么意思。

**建议**：把 Three Immutable Laws 移到后面（理解了 Why Myco 之后再读这个才有意义），把 **Why Myco?** 提前——让"storage vs metabolism"的对比更早出现。

新顺序建议：
```
1. Header + tagline (30 sec read)
2. Why Myco? → storage problem vs metabolism problem (2 min read)
3. Works With + Quick Start (5 min action)
4. What Myco Is (full details)
5. Three Immutable Laws
6. ...其余详细内容
```

### 4.2 GitHub 社区基础设施

**需要创建**（v0.x 准备阶段）：
- GitHub Discussions：开启，分类：Usage / Adapters / Battle Reports / Ideas
- Issue 模板：Bug Report / Feature Request / Submit Adapter / Share Battle Report
- PR 模板：强制要求说明"在什么项目类型上测试过"

**挑战 C8**：零用户的社区建设是鸡蛋问题。没有社区，也没有 Discussions 的内容；没有内容，也没有社区。创始人是否应该先自己发一些内容？

**回应**：YES，但要真实——不是伪造活跃度，而是：
1. 开启一个"Battle Reports"帖，把 ASCC 的学习历程写成一个真实案例（已有 examples/ascc/）
2. 开启一个"Adapters in Progress"帖，公开声明哪些 adapters 在 v1.0 路线图里
3. 用户的第一次互动入口：`myco init` 之后，MYCO.md 里有一行"发现了什么值得分享的？→ [GitHub Discussions link]"

### 4.3 Round 4 结论

**GitHub 存在感策略**：
- README 结构调整：Why Myco 提前，Laws 延后
- GitHub Discussions 开启：四个分类
- Issue 模板：四种类型（含 Submit Adapter）
- 创始人种子内容：ASCC battle report + adapters roadmap

**置信度：85%**

---

## 终极收敛

### 完整行动项（传统手艺 → 执行）

**立即执行（本轮）：**

| # | 操作 | 文件 | 价值 |
|---|------|------|------|
| B1 | 创建 `adapters/` 目录 + schema README + 3 个 adapter manifests | `adapters/README.md` + `openclaw.yaml` + `hermes.yaml` + `mempalace.yaml` | 让"吞噬"从愿景变成可操作的协议 |
| B2 | 更新 CONTRIBUTING.md：四种贡献类型 + 分级审核 + "第一次贡献" 引导 | `CONTRIBUTING.md` | 降低贡献摩擦 |
| B3 | README Quick Start 重排序：migration first | `README.md` | 强化最强 v0.x hook |

**下一轮（v0.9 准备阶段）：**

| # | 操作 | 理由 |
|---|------|------|
| B4 | README 结构调整（Why Myco 提前） | 提高前三屏转化率 |
| B5 | GitHub Discussions 开启 + issue 模板 | 社区基础设施 |
| B6 | `myco init` 输出的 MYCO.md 末尾加 Discussions 链接 | 用户第一次接触社区的入口 |

**v1.0 路线图（不在本轮执行）：**
- `myco import --from hermes`（adapter YAML → CLI 自动化）
- Community template registry（`myco install --template community/xxx`）
- GitHub Actions：PR 模板自动检查"≥1 种项目类型验证"

### 综合置信度

| 维度 | 置信度 |
|------|--------|
| Adapter 接口设计（YAML manifest） | 88% |
| 社区飞轮机制（四种类型 + 分级审核） | 87% |
| 30 秒啊哈时刻（migrate → lint → 发现不一致） | 90% |
| GitHub 存在感策略 | 85% |

**综合置信度：87%**

残余 13% 不确定性：
- 零真实用户，无法验证"啊哈时刻"的实际效果
- GitHub Discussions 需要创始人持续维护
- Adapter YAML 的价值需要第一批用户试用反馈

---

*传统手艺 4 轮完成。主要产出：adapter YAML manifest 设计（v0.x 可立即创建）、四种社区贡献类型、CLAUDE.md 用户优先的 30 秒上手路径。*
