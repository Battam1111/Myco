# Research Paper Craft — Myco 通用知识模板

> **类型**：craft
> **最后更新**：2026-04-09（补充 CL1-CL7 防错清单；来源：ASCC wiki/paper_writing_craft.md Cross-Project Distillation 蒸馏）
> **适用范围**：任何使用 Myco 的研究型论文项目（NeurIPS / ICML / ICLR 及同级别会议）
> **⚠️ 非直觉盲点**：canvas-design skill 对科研图有害——它把 matplotlib 当艺术画布用，引入与学术图根本方向相悖的装饰噪声。永远不要用它创建论文图像。

---

## 1. 科研绘图工具链（实战验证，2026-04-09）

GitHub 社区调研 + ASCC 项目实战双重验证的工具选型。

### 1.1 概念图 / 架构图（Motivation Figure、Method Diagram）

| 工具 | 用途 | 优先级 |
|------|------|--------|
| `tueplots` ([pnkraemer/tueplots](https://github.com/pnkraemer/tueplots), ~700★) | NeurIPS/ICML/ICLR 官方列宽、字号预设 | **必用** |
| `matplotlib FancyBboxPatch + annotate` | 程序化框图、箭头、流程图 | **主力** |
| STIX 字体（`mathtext.fontset: stix`） | 无完整 LaTeX 时的最佳替代（≈ Computer Modern） | **沙箱 Fallback** |
| TikZ / PlotNeuralNet | 论文终稿 polish，LaTeX 原生字体 | 最终版本 |
| Draw.io → PDF/SVG | 需要 GUI 快速迭代 | 备选 |

**已知摩擦**：TeX Live 2022 不完整环境缺少 `type1ec.sty`，导致 `text.usetex=True` 报错。
解决方案：`text.usetex=False` + `font.family: STIXGeneral` + `mathtext.fontset: stix`

**标准 Bootstrap（每次创建论文图时复制使用）**：

```python
from tueplots import bundles
import matplotlib.pyplot as plt

plt.rcParams.update(bundles.neurips2024())
plt.rcParams.update({
    "text.usetex":      False,         # 若沙箱缺 type1ec.sty
    "font.family":      "STIXGeneral",
    "mathtext.fontset": "stix",
    "mathtext.default": "regular",
})
# 概念图：FancyBboxPatch + ax.annotate
# 结果图：rliable / seaborn
```

**⚠️ 多组件非重叠布局（实战验证，2026-04-09）**：

当一张图有 badge/标题区 + 数据内容区 + 图例/caption 区等多个语义层时，**不要**用 `zorder` 或坐标微调来解决重叠——这是打补丁思路，会随图高/pad 参数漂移而复发。正确方案：**三层独立 axes，物理坐标完全隔离**。

```python
# 图形坐标（figure fraction）从下到上分配，互不重叠
CAP_H   = 0.086                          # caption strip
BADGE_H = 0.090                          # badge/title strip
BADGE_BOT = 1.0 - BADGE_H - 0.010       # ≈ 0.904（顶部留白 0.010）
CONT_BOT  = CAP_H                        # ≈ 0.086
CONT_H    = BADGE_BOT - CONT_BOT        # 剩余内容区高度

fig = plt.figure(figsize=(...))
ax_badge  = fig.add_axes([left, BADGE_BOT, width, BADGE_H])   # 标题/badge
ax_content = fig.add_axes([left, CONT_BOT,  width, CONT_H])   # 数据/流程图
ax_cap    = fig.add_axes([0.00, 0.000,    1.00,  CAP_H])      # caption/legend

for ax in [ax_badge, ax_content, ax_cap]:
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
```

触发条件：FancyBboxPatch pad 超出 axes ylim、两层 patches 发生像素重叠、调整坐标数值后问题在不同 dpi 下复现。

验证方法：`fig.savefig(..., dpi=200)` 和 `dpi=72` 各保存一次，检查 badge 是否在两者中都完整可见。

### 1.2 结果图 / 学习曲线 / 性能对比图

| 工具 | 用途 | 优先级 |
|------|------|--------|
| `rliable` ([google-research/rliable](https://github.com/google-research/rliable), ~3500★) | Performance Profile + IQM + Bootstrap CI | **金标准**（NeurIPS 2021 Outstanding Paper） |
| `SciencePlots` ([garrettj403/SciencePlots](https://github.com/garrettj403/SciencePlots), ~8600★) | 学术风格一行激活：`plt.style.use('science')` | **必用** |
| `tueplots` | 格式统一（与概念图共用） | **必用** |
| `seaborn` | 置信带、分布图 | 按需 |

### 1.3 Figure 1 设计原则（10 秒测试）

- 10 秒内读者必须理解核心 insight
- 颜色 ≤ 3 种；每种颜色承载一个语义（novelty / problem / neutral）
- 文字量 ≤ 10%，图像传达 ≥ 90%
- 两面板对比（problem vs solution）是最高效的 Motivation Figure 结构
- 标题格式：`(a) 问题名称` / `(b) 方法名称`，加粗

---

## 2. 快速参考表

| 图类型 | 主工具 | 备注 |
|--------|--------|------|
| Motivation / Architecture 图 | `tueplots + FancyBboxPatch` | 不用 canvas-design |
| 学习曲线 / 性能轨迹 | `rliable + SciencePlots + tueplots` | crash filter 必须 |
| 消融实验 | `rliable performance profile` | |
| 统计分布 | `seaborn + tueplots` | |

---

## 3. 论文写作十大原则（9位大师综合，NeurIPS/ICML/ICLR 验证）

> Sources: Kenneth Landes, Simon Peyton Jones, Pat Langley, Zachary Lipton, Michael Black, Bill Freeman, Frédo Durand, Henning Schulzrinne, Andrej Karpathy

| # | 原则 | 一句话 | 来源 |
|---|------|--------|------|
| P1 | **Goal → Problem → Solution** | 每篇文章、每个章节、每段话都遵循这个节奏 | Black |
| P2 | **Inform, Don't Tease** | Abstract 是摘要不是预告——必须包含关键数字 | Landes |
| P3 | **One Story, One Nugget** | 一篇论文只讲一个故事，Nugget = 使贡献成为可能的洞见 | Black |
| P4 | **Delete the Generic First Sentence** | 第一句话如果可以放到任何 ML 论文前面，就删掉 | Lipton |
| P5 | **First Impressions Are Permanent** | Abstract + 第一页决定论文命运，投入不成比例的精力 | Black |
| P6 | **Show What It Does, Not What It Is** | 描述效果和能力，不是架构和组件 | Peyton Jones |
| P7 | **Three Explanations for One Concept** | 文字（直觉）+ 公式（精确）+ 图（视觉），三合一 | Black |
| P8 | **Write the Talk First** | 先写演讲，再写论文——演讲强制识别叙事弧线 | Freeman |
| P9 | **Read Bad Papers** | 读差论文建立质量二分类器（vague abstract, undefined variable...） | Karpathy |
| P10 | **Clear Writing = Clear Thinking** | 写不清楚说明还没想清楚；写作是思考的工具，不是包装 | Karpathy + Tao |

### 核心技法速查

**Abstract 公式（T1）**：问题(1句) → 差距(1句) → 方法-效果(1-2句) → 定量结果(1句) → 影响(0-1句)。目标 120-160 字。

**Introduction 漏斗（T2）**：Hook（具体问题）→ Gap（现有方法为何不足）→ Approach（你的关键洞见）→ Contributions（3-4条可核实的 claim）→ Results Preview

**Method 节（T3）**：先 Motivation（为何），后 Mechanism（如何）。每个关键概念文字+公式+图三重解释。

**Experiments（T4）**：假设驱动，不是比赛。必须：消融实验 + 参数敏感性 + 学习曲线。一次只改一个变量。

**Related Work（T5）**：按主题分组，分析而不是列举。说清楚你与前人的具体区别。

**Conclusion（T7）**：重申 Nugget + 含义，1-2段。不要"Future work"列表。

**语言（T8）**：用更少的词。主动语态。避免"provides/enables/allows"（模糊动词）。

---

## 4. 防错检查清单（CL1-CL7）

> 每次写对应章节前阅读，提交前执行 CL7。

### CL1. 动笔前检查

在写第一个字之前，回答这些问题：

- [ ] **Goal** 是什么？读者为什么要关心？
- [ ] **受众** 是谁？谁会使用或基于此继续工作？
- [ ] **Nugget** 是什么——使贡献成为可能的核心洞见？
- [ ] **一句话 pitch**？（≤ 3 句话）
- [ ] **Teaser Figure** 应该展示什么？
- [ ] **关键前人工作**和其局限是什么？
- [ ] **定量评估**方式是什么？
- [ ] **关键风险**有哪些？

### CL2. Abstract 检查

- [ ] ≤ 200 词（目标 120-160）
- [ ] 单段落，无换行
- [ ] 无引用、无公式、无脚注
- [ ] 不以"In this paper"或通用 ML 句子开头
- [ ] 第 1-2 句：具体描述**问题**
- [ ] 描述方法的**效果**（不是架构）
- [ ] 包含**定量结果**（如有）
- [ ] 只读 Abstract 的读者能知道核心发现
- [ ] 通过 Landes 测试：是**摘要**不是**预告**

### CL3. Introduction 检查

- [ ] 第一句话是此论文专属的（Lipton 测试）
- [ ] 第 1 段末尾问题清晰
- [ ] 第 2 段末尾现有方法的不足明确
- [ ] 第 3 段出现核心洞见 / Nugget
- [ ] Contribution list 有 3-4 条，每条是**claim** 不是**topic**
- [ ] 无"rest of the paper is organized as follows"段落
- [ ] 关键数字出现在 intro 某处

### CL4. Method 检查

- [ ] 每个设计选择在描述前先**说明动机**
- [ ] 关键概念有文字 + 公式 + 图（三重解释）
- [ ] 符号系统一致且在首次使用时定义
- [ ] 公式与代码完全对应
- [ ] 无"laundry list"式步骤（无动机说明）

### CL5. Experiments 检查（Langley 标准）

- [ ] 消融实验存在（至少移除一个组件）
- [ ] 关键超参数敏感性分析
- [ ] Baselines **公平**（相同算力、相同调参力度）
- [ ] 报告统计显著性或置信区间
- [ ] 结果支持具体 claim，不只是"我们更好"

### CL6. Figures 检查

- [ ] 每张图在正文中被引用
- [ ] Caption 自包含（不读正文也能理解）
- [ ] 图中文字在打印尺寸可读
- [ ] 坐标轴带单位标签
- [ ] 重要细节有高亮（箭头、圆圈）
- [ ] Figure 1 是有力的 teaser
- [ ] **⚠️ 工具链**：概念图用 `tueplots + FancyBboxPatch`，结果图用 `rliable + SciencePlots + tueplots`
- [ ] **⚠️ 禁用**：canvas-design skill（对科研图有害）
- [ ] `tueplots.bundles.neurips2024()` 已设置
- [ ] 字体：STIX + mathtext，或 LaTeX（需 `type1ec.sty` 可用）

### CL7. 最终提交检查（Black）

- [ ] **逐字阅读**——标题、caption、每个公式
- [ ] 搜索 PDF 中的"?"（缺失引用）
- [ ] 所有引用完整（已发表版本优先于 arXiv 预印本）
- [ ] 页数充实（7.5/8 页看起来未完成）
- [ ] 无孤儿缩写（定义但未使用，或使用但未定义）
- [ ] Supplementary 与正文承诺对应
- [ ] 至少一个非作者读过并提供反馈

---

## 5. 对 Myco 框架的改进建议（来自 ASCC 项目摩擦记录）

**Friction → Framework Improvement**：

1. **canvas-design skill 误导**：其描述"Create beautiful visual art"过宽，导致被用于论文图像创建，效果差。
   → 建议：在 Myco 的 skill 选择指引中明确标注 canvas-design 不适用于学术图，并指向本文档。

2. **工具选型知识缺失**：新 Myco 项目启动时没有图像工具的引导，会浪费 1-2 次迭代。
   → 建议：在 `src/myco/templates/WORKFLOW.md` 的 W1 或 W6 中增加"研究型项目绘图工具链"引用。

3. **LaTeX 环境变量**：沙箱 TeX Live 不完整，type1ec.sty 缺失是高频痛点。
   → 建议：在 operational_narratives 模板中增加 LaTeX fallback 标准操作。

4. **多组件布局重叠**：概念图中 badge/标题 与 数据 axes 共存时，用坐标微调修复重叠会反复复发（不同 dpi/figsize 下坐标关系不同）。
   → 建议：三层独立 axes 是唯一稳健解法（见 §1.1 "多组件非重叠布局"）。检测信号：FancyBboxPatch pad 超出 ylim=[0,1]，或两轮 patch 修复后问题仍存在。

---

> **Back to**: [MYCO.md](../MYCO.md) | [docs/evolution_engine.md](evolution_engine.md)
