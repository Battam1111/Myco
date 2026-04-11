# 传统手艺：README 重写策略辩论
> 日期：2026-04-10 | 类型：content-strategy | 状态：[ACTIVE]
> 前置：v1_1_scope_craft（v1.1.0 完成），MYCO.md Task 9 B1
> 目标：确定面向 Public Release 的 README 结构和内容策略

---

## 背景约束

**当前 README 的问题：**
- 以功能清单开头（"four-layer architecture", "four gears"）——对不认识 Myco 的人没有意义
- "metabolism" tagline 出现但没有被解释成具体的用户体验
- Quick Start 是命令堆砌，没有叙事
- 竞品表格有但埋得太深
- L1/L1.5/W8 等内部术语出现在面向外部用户的位置

**目标读者（按优先级）：**
1. 有 CLAUDE.md 的 Claude Code 用户——最高意图，最短转化路径
2. 用 Hermes/OpenClaw/Cursor 的 AI 开发者——中等意图，需要定位说明
3. AI agent 基础设施感兴趣的开发者——探索性，需要价值主张
4. 学术/研究背景——低优先级，不是首发目标

**置信度目标：** ≥85%

---

## Round 1：Hero Section——用问题开头还是用解决方案开头？

### 主张（解决方案优先）
直接亮出 tagline：
```
# Myco
Other tools give your AI agent memory. Myco gives it metabolism.
```
然后立刻解释 metabolism 的意思。理由：tagline 足够独特，能立刻区分。

### 攻击
但是 "metabolism" 对大多数开发者是陌生词汇，需要解释。
如果解释不够清楚，读者会带着困惑往下读。
而且 "memory vs metabolism" 这个对比，读者首先需要认可"memory 不够用"这个前提——
如果他们还不认可，tagline 就没有说服力。

更好的结构：先建立问题认知（30字），再提出方案，再说 tagline。

```
你的 AI agent 做了一个决定，三天后做了矛盾的决定。
没有人发现。
直到你花了两小时 debug。

这是 memory 问题，还是 metabolism 问题？
```

### 研究/证据
分析成功的开发者工具 README 结构（Homebrew, shadcn, uv, Astro）：
- 几乎都以一句话 pitch 开头（不是故事）
- 但 pitch 都非常具体，不是抽象概念

shadcn: "Beautifully designed components that you can copy and paste into your apps."
uv: "An extremely fast Python package and project manager, written in Rust."

这些 pitch 的共同点：**描述的是用户直接体验到的结果，不是底层机制。**

Myco 的问题：当前 tagline 描述的是隐喻（metabolism），不是用户直接体验的结果。
更好的第一句：**"myco lint 会告诉你，你的 agent 上周做的决定，和它今天写的代码矛盾了。"**

### 辩护
**修订 Hero 结构（三段式）：**

```
[1句] 最直接的用户体验价值
[2句] 为什么现有工具不够
[1句] Myco 做什么（tagline 放这里）
```

具体：
```
**Myco catches contradictions your AI agent doesn't know it made.**

Most tools give your agent memory — somewhere to put what it learned.
But memory doesn't ask: *is that still true? does it contradict this?*

Myco gives your agent metabolism — the ability to decompose, verify, 
evolve, and distill knowledge across sessions and projects.
```

**置信度：82%**（方向正确，具体措辞需第二轮压力测试）

---

## Round 2：Quick Start——"能用"展示 vs "wow"展示

### 主张
Quick Start 应该展示 aha moment：
```bash
pip install myco
myco migrate ./your-project --entry-point CLAUDE.md
myco lint --project-dir ./your-project
# → FAIL: wiki/api_design.md references "v2 endpoint" but _canon.yaml says current is v3
```
让读者在 README 里就"看到"第一次 lint 发现矛盾的感觉。

### 攻击
但这个展示有问题：读者刚迁移完，lint 会全绿（传统手艺 v1.0 Round 2 的结论）。
如果我们在 README 里展示一个 FAIL 案例，读者自己运行时看到 ALL PASSED，
会觉得"Myco 没用" 或者 "README 在说谎"。

### 研究/证据
解决方法：展示两个阶段——

**Phase 1（迁移当天）：**
```bash
$ myco lint --project-dir ./my-project
✅ ALL CHECKS PASSED — 0 issues (clean scaffold, expected)
```

**Phase 2（几次会话后）：**
```bash
$ myco lint --project-dir ./my-project  
❌ L2: wiki/api_design.md says "v2 endpoint" but _canon.yaml canonical_version = v3
❌ L4: wiki/deployment.md not referenced in MYCO.md index
→ 2 issues found — that's Myco working for you
```

这比只展示第一阶段更诚实，也更有说服力——展示"持续工作"，不是"一次性通过"。

### 辩护
Quick Start 采用**三步 + 两阶段展示**：

1. 安装（1行）
2. 迁移（1-2行）
3. 建立基线（lint，展示全绿 + 说明这是预期）
4. **[时间线跳转]** 几次会话后 lint 的输出样例（展示真实价值）

时间线跳转是合理的叙事手法，不是欺骗。Stripe、Vercel 的文档都用这种方式。

**置信度：86%**

---

## Round 3：结构完整性——哪些区块必须有，哪些可以删

### 主张
面向公开发布的 README 必须包含：
1. Hero（问题 + 方案 + tagline）
2. Quick Start（3步 + 两阶段展示）
3. 核心能力（不是功能列表，是用户故事）
4. 竞品定位（为什么不只用 OpenClaw/Hermes）
5. Works with your tools（adapter 表格，简化版）
6. Status（已验证什么，谁在用，置信度）
7. Contributing（链接到 CONTRIBUTING.md）

### 攻击（快速）
当前 README 还有：Architecture Deep Dive、Evolution Landscape 表格、Project Adaptation 表格、Three Immutable Laws、Philosophy section。
这些对于有意愿的读者有价值，但放在首页 README 会稀释焦点。

### 辩护
**删除/移出到 docs/：**
- "Three Immutable Laws" → 移入 docs/architecture.md（对已采用者有价值，不是转化工具）
- Philosophy（meta-evolution 论证）→ 移入 docs/architecture.md
- Architecture Deep Dive → 移入 docs/architecture.md（README 保留 1 段简介 + 链接）
- Project Adaptation 表格 → 移入 CONTRIBUTING.md 或 docs/

**保留但精简：**
- Evolution Landscape 表格（L-exec/L-skill/L-struct/L-meta）→ 保留，这是最强的竞品定位工具
- Works With 表格 → 简化为 4 行

**新增：**
- 真实案例一行（"Validated on a 7-day, 80+ file research project through full Gear 4 distillation"）
- Badges（PyPI version, Python versions, License）

**置信度：88%**

---

## Round 4：语言风格——中英文混排 vs 纯英文

### 主张
README 应该纯英文，因为目标用户是国际社区（GitHub 公开后）。

### 攻击
但 Myco 里有中文核心概念：传统手艺（Craft）、齿轮（Gears）等。
完全去中文化会丢失一部分设计意图的解释。

### 辩护
**全英文 README，中文概念有英文映射：**
- 传统手艺 → "Craft Protocol（传统手艺）" — 括号内保留原文，像日文工具的惯例
- 齿轮 → "Evolution Gears"（已有英文名）
- 代码示例中的注释可以有中文（符合项目真实情况，反而增加真实感）

**置信度：91%**

---

## 最终决议（综合置信度 87%）

### README 完整结构

```
[Badges: PyPI version | Python 3.8+ | License MIT]

# Myco 🍄

[Hero: 4行，问题→方案→tagline]

## Quick Start  ← 尽量靠前，开发者会跳到这里
[3步迁移 + 两阶段 lint 展示]

## Why Myco?  ← 核心价值主张
[Evolution Landscape 表格：L-exec/L-skill/L-struct/L-meta]
[2段散文解释 L-struct 和 L-meta 的独特性]

## Works With Your Tools  ← adapter 表格简化版（6行）

## How It Works  ← 极简架构介绍（4-5句 + 不超过5行的层级图）

## Real-World Validation  ← 证明力（1段，ASCC 数据）

## Status  ← 版本、兼容性声明

## Contributing  ← 链接 + 一句话邀请

## License
```

### 字数目标
- Hero: ≤100 字
- Quick Start: ≤60 字 + 代码块
- 全文：≤800 字（散文部分），代码块和表格不计入

### 行动项
| ID | 行动 |
|----|------|
| E1 | 写新 README（按上述结构）|
| E2 | 原 README 中 Philosophy / Laws / Architecture Deep Dive 段落迁移到 docs/architecture.md |
| E3 | lint 验证 + commit + push |

---

*传统手艺结束。87% 置信度 ≥ 85% 阈值，进入执行阶段。*
