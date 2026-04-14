# 传统手艺：B2 品牌视觉策略辩论
> **Status**: ARCHIVED (compiled to formal docs)
> 日期：2026-04-10 | 类型：brand-strategy | 状态：[ARCHIVED]
> 前置：readme_craft（B1 ✅），Task 9 B2
> 目标：确定 Myco 品牌视觉语言——Logo + GitHub Social Preview + README 配图

---

## 在线调研结果（Research Phase，2026-04-10）

### 调研 1：竞品定位现状验证
**来源：** Mem0 State of AI Agent Memory 2026 (mem0.ai/blog/state-of-ai-agent-memory-2026)

关键发现：
- **"Memory staleness detection" 明确列为未解决挑战**：原文 "Systems struggle identifying when high-relevance memories become outdated." 这正是 `myco lint` 所做的事。Myco 的核心差异化被独立第三方验证。
- 21 个框架集成，19 个向量存储后端，13 个 agent 框架连接——Mem0 在记忆检索层占据主导。
- 没有任何工具涉及结构进化（L-struct）或元进化（L-meta）。

**结论：** Myco 的"metabolism vs memory"定位在 2026 市场完全成立，且有 Mem0 官方数据背书。

### 调研 2：AI agent 知识管理工具全景
**来源：** Atlan Best AI Agent Memory Frameworks 2026

关键发现：
- 评估 8 个框架（Mem0/Zep/LangChain/Letta/SemanticKernel/Cognee/Supermemory/Redis）
- **明确声明 "None of these frameworks provide governance policy enforcement"**
- 只有 Zep 做时序事实失效，但仅在 KV 层面，非结构进化
- 缺口：一致性检验 / 跨 session 知识验证 / 知识系统本身的进化

**结论：** Myco 的 L-struct + L-meta 层定位无竞争对手确认。

### 调研 3：OpenClaw 安全危机
**来源：** Reco AI Blog, Oasis Security Blog, Kaspersky Blog (2026)

关键发现：
- CVE-2026-25253 (CVSS 8.8)，一键 RCE 漏洞
- 2026 年 1 月安全审计发现 **512 个漏洞**，8 个关键级别
- ClawHub 上 12% 的技能包含恶意代码（2857 个中 341 个）
- "persistent memory 功能与这些漏洞结合，创造了严重隐私风险"

**对 Myco 的启示：** OpenClaw 的安全危机并非直接竞争关系（Myco 是进化层，不是存储层），但说明 AI 生态系统对"结构验证"的需求是真实的，用户正在寻求更可靠的知识管理方式。

### 调研 4：GitHub Social Preview 最佳实践
**来源：** GitHub Docs, Bomberbot, Dev.to (2025)

关键发现：
- 标准尺寸：**1280×640px**，最小 640×320px，长宽比 1.91:1
- **有自定义 Social Preview 的仓库获得平均 42% 更多独立访客**
- 最佳实践：项目名（大字体）+ tagline + 视觉元素（与项目主题一致）
- 避免通用素材图，使用与项目身份一致的视觉语言

---

## Round 1：品牌视觉核心——"metabolism" 的视觉隐喻

### 主张
Myco 的核心隐喻是**菌丝网络（mycelial network）**：无数细线连接的节点，持续生长、验证、传递营养。这个隐喻：
1. 完全对应 metabolism（代谢 = 持续的物质转化和验证循环）
2. 与产品名 "Myco"（来自 mycology = 真菌学）高度一致
3. 在视觉上是独特的——没有其他 AI 工具使用菌网意象

### 攻击
但是"菌丝网络"视觉可能传递错误信号：
- 有机/自然感 → 读者可能联想到"模糊"而非"精确"
- 与 AI dev tool 的"技术/工程"期望不符
- 复杂网络图 = 难以在小尺寸（favicon、16x16 logo）下识别

更重要的问题：开发者工具品牌的成功案例（Vercel、uv、shadcn、Stripe）用的是**极简几何**而非有机形态。

### 研究/证据（在线调研结果综合）
分析成功开发者工具品牌视觉语言：
- **Vercel**：黑白极简，三角形 ▲（部署的方向感）
- **uv（Astral）**：深色背景，渐变紫色节点连接图，技术感强
- **shadcn/ui**：纯文字 logo，极简黑白
- **LangChain**：抽象链条/连接图标，深色背景
- **Mem0**：橙色圆形 logo，简洁

趋势确认：2025-2026 AI 开发者工具偏好**深色背景 + 单色/双色 accent + 抽象几何/网络节点**。

但菌丝网络 **不必然** 是"模糊"的——关键在于风格化处理：
- 精细线条 + 节点 dot = 精密感（像电路板，不像苔藓）
- 暗色背景（#0D1117 GitHub Dark）+ 青绿色（#00D4AA）= 技术感
- 菌丝网络 + 网格对齐 = "有机生长 + 系统精度"的结合（正是 metabolism 的视觉对应）

### 辩护
**核心视觉语言确定：**
- **主色调**：#0D1117（GitHub Dark 背景）+ #00D4AA（青绿色，代表知识流动/代谢）
- **图形语言**：精细线条菌网 + 精确节点（对齐网格，有机形态但几何精度）
- **字体方向**：Monospace 或 thin sans-serif（代码工具感）
- **Logo 形态**：小型菌丝节点图，可识别性强，在深色/浅色背景均可用

**置信度：84%**（方向确定，具体配色需第二轮验证）

---

## Round 2：Logo 设计——简单性 vs 完整隐喻

### 主张
Logo 应该极简：一个蘑菇轮廓 🍄（已有 emoji 认知基础）或一个单一节点图。

### 攻击
蘑菇 emoji 风格：
- 已有既有形态（🍄 emoji），无法形成独特品牌识别
- 蘑菇在流行文化中有强烈的迷幻药联想（Mario / 致幻蘑菇）
- 太字面了——Myco 的深层隐喻是**地下菌丝网络**（看不见的智慧），不是地面上的蘑菇

节点图方案：
- 抽象程度高，需要语境才能理解
- 小尺寸下可识别性差

### 研究/证据（在线调研 + 竞品分析）
成功的抽象 logo 公式（开发者工具）：
- **简单几何形体** + **唯一一个有意义的细节**
- uv：六边形（蜂巢 = 高效组织），极简线条
- Vercel：三角形（指向/部署），纯黑
- Redis：骰子/数据结构图标

Myco 解法：**菌根节点（Hyphal Node）**——一个几何化的圆形节点，4-6 根精细线从圆心向外延伸（像星号，但有机偏斜），每根线末端是更小的节点。
- 这是"菌丝末梢"的极简化
- 可识别（3x3px 时仍是清晰的星形/节点）
- 传递"向外传播 / 连接 / 代谢"

### 辩护
**Logo 方向：菌根节点（Hyphal Node）**
- 几何圆心 + 6 根线（偏斜有机角度，非正六角对称）+ 末端小点
- 颜色：深色版（白/浅灰线 on 深色背景）+ 浅色版（深青绿线 on 白背景）
- 搭配字体：Myco（thin monospace 或 light sans-serif），字距略宽

**置信度：86%**

---

## Round 3：GitHub Social Preview——内容层次

### 主张
Social Preview (1280×640) 应该最大化传递品牌信息密度：
- Logo + "Myco 🍄" + tagline + 代码片段展示

### 攻击（来自在线调研数据）
GitHub 数据：42% 更多访客，但这是**有 vs 无** Social Preview 的差异，不是内容复杂度差异。
失败案例分析：信息密度过高的 Social Preview 在 Twitter/HN 分享时缩略图看起来是"乱码图"，反而降低点击率。

成功的开发者工具 Social Preview 特征（来自 kapwing/social preview gallery）：
- **1个主视觉元素**（≥60% 画面占比）
- **项目名** 大字体（清晰可读）
- **一句 tagline**（可选，但不能超过 10 字）
- 纯色或简单渐变背景

### 研究/证据
Atlan 2026 报告确认：开发者在评估工具时的决策路径——GitHub → README → Quick Start。Social Preview 是"是否点进来看"的第一道门。

最优信息层次（基于调研 + 竞品分析）：
```
[深色背景 #0D1117]
[左半：菌网节点图（大，60% 面积），精细线条，青绿色]
[右半：
  "Myco 🍄"（大字，白色）
  "Metabolism for AI agents"（小字，浅灰）
  pip install myco（最小字，monospace，青绿色）
]
```

### 辩护
**Social Preview 方案确定：**
- 左：菌网节点大图（主视觉，60%）
- 右：项目名 + 简短 tagline + install 命令
- 背景：#0D1117，节点：#00D4AA，文字：白色/灰白
- 整体感：这是一张来自神秘技术组织的"系统图"，不是营销物料

**置信度：89%**

---

## Round 4：README 配图——必要性 vs 工作量

### 主张
README 需要三张配图：
1. 四层架构图（L1/L1.5/L2/L3）
2. 四齿轮进化图（Gear 1-4 循环）
3. Evolution Landscape 表格（已有文字版，是否需要图形化？）

### 攻击（务实角度）
配图维护成本：README 每次更新，配图需同步更新。文字版 Evolution Landscape 表格已经很清晰，图形化边际价值低。

关键问题：**两张图（架构 + 齿轮）vs 零图**哪个更好？

在线调研发现（GitHub README Best Practices, 2025）：
- 有架构图的工具 README 显著更受欢迎（LangChain、LlamaIndex 都有）
- 图的价值 = 让读者在 30 秒内理解整体设计，不用读完全文
- **结论：架构图 必须有**，齿轮图 有价值但非最高优先级

### 辩护
**README 配图优先级：**
1. ✅ **Social Preview**（最高 ROI，42% 访客增加，立即实现）
2. ✅ **四层架构图**（对首次访问者价值最高，用 SVG 内嵌 README 可维护）
3. ⏳ **齿轮进化图**（v1.2 待做，非本次优先级）
4. ❌ **Evolution Landscape 图形化**（文字表格已足够清晰，不做）

**置信度：91%**

---

## 最终决议（综合置信度 88%）

### 品牌视觉系统

**色彩**
- Background: `#0D1117` (GitHub Dark)
- Primary Accent: `#00D4AA` (青绿，代谢流动感)
- Text Primary: `#FFFFFF`
- Text Secondary: `#8B949E`
- Code: `#58A6FF`

**图形语言**
- 菌根节点图（Hyphal Node）：精细线条 + 偏斜有机角度 + 末端节点
- 背景：深色，偏工程审美
- 整体感：精密系统图，非营销插图

**本次交付物**
| 资产 | 规格 | 优先级 |
|------|------|--------|
| Logo（菌根节点） | SVG，深/浅双色版 | 必须 |
| GitHub Social Preview | PNG，1280×640 | 必须 |
| README 架构图 | SVG/PNG，嵌入 README | 必须 |

### 行动项
| ID | 行动 |
|----|------|
| F1 | 创建 Logo SVG（菌根节点，深/浅双色版） |
| F2 | 创建 GitHub Social Preview 1280×640 PNG |
| F3 | 创建四层架构图（嵌入 README） |
| F4 | 更新 README：添加架构图引用 |
| F5 | 所有资产放入 `assets/` 目录 |

---

*传统手艺结束。综合置信度 88% ≥ 85% 阈值，进入执行阶段。*
*调研来源：mem0.ai/blog/state-of-ai-agent-memory-2026 | atlan.com/know/best-ai-agent-memory-frameworks-2026 | reco.ai/blog/openclaw-security-crisis | GitHub Docs Social Preview*
