# 传统手艺：Myco 自我应用设计

> **文档状态**：[ARCHIVED] | 创建：2026-04-09
> **置信度**：最终 88%
> **决策范围**：Myco 项目自身的 MYCO.md 结构、知识层划分、canon 设计
> **背景**：v0.9.0 已发布至 PyPI，Myco repo 至今没有用 Myco 自身管理——现在执行 `myco migrate .` 并从零搭建 Myco 自身的知识系统。
> **为什么需要辩论**：这是 Myco 公开展示的第一个"自我应用"示范，将直接被第一批用户看到，决策质量比普通项目高一个等级。

---

## 核心问题清单（辩论前预设）

- Q1：入口文件用 MYCO.md 还是 CLAUDE.md？
- Q2：现有 docs/ 七个文件如何分配到四层架构？
- Q3：wiki/ 里放什么，什么都不放？
- Q4：hot zone 写什么——Myco 是 framework，不是 user project？
- Q5：_canon.yaml 里的 Myco 特有规范值是什么？
- Q6：log.md 如何从 git history 重建，起点设在哪里？

---

## Round 1：入口文件——MYCO.md vs CLAUDE.md

### 立场 A（MYCO.md）

Myco repo 应该用 MYCO.md 作为入口，理由三条：

1. **品牌一致性**：Myco 的核心主张之一是"agent-agnostic"——入口文件不绑定特定 agent。CLAUDE.md 会传递"这是 Claude 专属"的错误信号。
2. **示范效果**：第一批用户克隆 repo 时，看到 MYCO.md 会立刻理解这就是 Myco 自身在用 Myco。看到 CLAUDE.md 则会困惑——"这是 CLAUDE.md 还是 MYCO.md？"
3. **template 一致性**：templates/MYCO.md 就是标准入口模板，Myco 自身用它最自然。

### 攻击 A1

**攻击**：但 Myco 的主要用户是 Claude Code 用户，CLAUDE.md 会被 Claude Code 自动加载（zero friction），MYCO.md 不会。

**防御**：这正好是一个机会——展示 Myco 可以工作在 Claude Code 自动加载体系之外。README 里的 Quick Start 已经写了 `myco init my-project --entry-point CLAUDE.md` 的用法，用户知道可以选择 CLAUDE.md。Myco 自身用 MYCO.md，不但无害，反而明确展示了"框架默认，用户可选"。

### 攻击 A2

**攻击**：如果 Myco 自身用 MYCO.md，但 WORKFLOW.md 里的会话流程写的是"自动加载 CLAUDE.md"，会产生 inconsistency。

**防御**：这正是用 lint 来检查的场景。而且 WORKFLOW.md 模板里已经用的是 `CLAUDE.md/MYCO.md/等` 这种泛写法，不是硬编码。`_canon.yaml` 里会明确写 `entry_point: MYCO.md`，lint L3 会抓住任何遗留的硬编码引用。

**Round 1 结论**：**MYCO.md** ✅ 置信度 90%。

---

## Round 2：现有 docs/ 七文件的四层归位

### 现有文件清单与初始判断

| 文件 | 内容描述 | 初始归类 |
|------|----------|---------|
| `theory.md` | Clark & Chalmers + Argyris + Polanyi 理论基础 | L2 Docs — 核心理论文档 |
| `architecture.md` | 四支柱 + 进化引擎技术细节 | L2 Docs — 技术参考 |
| `vision.md` | 愿景 + 定位 + 菌丝比喻 | L2 Docs — 方向文档 |
| `evolution_engine.md` | 四齿轮详述 (v2.1) | L2 Docs — 专题文档 |
| `reusable_system_design.md` | 通用知识系统架构 v2.1（从 ASCC 蒸馏） | L2 Docs — Gear 4 产物 |
| `research_paper_craft.md` | 科研绘图、写作技法（带 W8 格式头部） | ⚡ 争议：L2 Docs 还是 wiki？ |
| `decoupling_positioning_debate_2026-04-09.md` | 6 轮竞品分析 + 定位辩论，置信度 90% | docs/primordia/ — 活跃辩论记录 |

### 攻击 B1：research_paper_craft 该去 wiki/

**攻击**：`research_paper_craft.md` 已经有完整的 W8 格式头部（类型: craft，最后更新，非直觉盲点），结构上是 wiki 页面，应该放到 `wiki/`。

**防御考察**：
- W8 格式头部确实完整，是 wiki 规范页面的形态
- 内容是"编译后的知识"（科研绘图方法、写作技法），符合 wiki 定义
- **但**：它是 ASCC 项目 Gear 4 蒸馏产物，专属于"学术论文"项目类型。Myco 作为框架 repo，把它放在 wiki/ 会暗示"这是 Myco 框架本身的核心知识"，语义不对。

**裁决**：`research_paper_craft.md` 保留在 `docs/`，但加 lifecycle 标签 `[ACTIVE]`，并在 MYCO.md 索引里标注"来自 ASCC Gear 4 蒸馏，适用于学术项目类型"。wiki/ 暂时不放任何页面（符合"不预建空页面"原则）。

### 攻击 B2：decoupling 辩论不该在 docs/，应在 docs/primordia/

**防御**：正确。`decoupling_positioning_debate_2026-04-09.md` 的 front matter 就写了 `[ACTIVE]`，它是活跃辩论记录，标准归位是 `docs/primordia/`。执行时移动。

**Round 2 结论**：

| 文件 | 最终归位 | 生命周期 |
|------|---------|---------|
| `theory.md` | `docs/theory.md` | [ACTIVE] |
| `architecture.md` | `docs/architecture.md` | [ACTIVE] |
| `vision.md` | `docs/vision.md` | [ACTIVE] |
| `evolution_engine.md` | `docs/evolution_engine.md` | [ACTIVE] |
| `reusable_system_design.md` | `docs/reusable_system_design.md` | [ACTIVE] |
| `research_paper_craft.md` | `docs/research_paper_craft.md` | [ACTIVE] |
| `decoupling_positioning_debate_2026-04-09.md` | **移至** `docs/primordia/` | [ACTIVE] |

置信度 85%。

---

## Round 3：hot zone 内容——Myco 是框架，不是用户项目

### 核心矛盾

标准 MYCO.md hot zone 包含："当前阶段 + 最容易出错的 N 件事 + Operational Feel"。这三项都是为 user project 设计的——描述的是"项目当前的操作环境"。

**Myco 自身的 hot zone 面对的是什么 agent？**

不是在某个专项研究里工作的 agent，而是**维护和开发 Myco 框架本身的 agent**。这个 agent 需要知道：
1. Myco 框架当前处于什么阶段（v0.9，heading to v1.0）
2. 开发 Myco 时最容易踩的坑（不是 user project 的踩坑，而是 framework 开发的踩坑）
3. Myco 自身的"操作环境"（Python 打包、lint 作为 CI、模板是 src/myco/templates/）

### 攻击 C1：框架自用会形成奇怪的递归

**攻击**：MYCO.md 里写"运行 `myco lint` 检查知识一致性"，但 Myco 自身的 lint 是用来检查 user project 的。Myco 用 lint 检查自己的框架知识，会有"用锤子锤自己"的荒谬感。

**防御**：恰恰相反——这正是 dog-fooding 的价值所在。lint 会检查 `_canon.yaml` 的 schema、wiki 页面的 W8 格式、cross-reference 完整性。这些检查对框架自身的知识文档完全有效。有没有 paradox 不是问题，有没有 value 才是。而且 Myco 的 lint 运行在 `project_dir`，指向 Myco repo 根目录，和指向 user project 根目录是完全等价的操作。

### hot zone 设计草稿

```
**项目**：Myco — 可自进化的 AI 延伸认知基质（框架本身）
**当前阶段**：Phase 1 — v0.9.0 已上线 PyPI，准备 v1.0

**框架开发中最容易出错的 N 件事** ⚠️：
1. 修改 src/myco/templates/ 后忘记同步 templates/（两处模板）
2. 在 pyproject.toml 更新版本但忘记同步 src/myco/__init__.py
3. 在 MYCO.md 里写"已实现"的功能，实际上是 roadmap（见 Round 6 C9 诚实审计）
4. lint 检查 Myco repo 自身时，ROOT 指向 repo 根，不是 src/ 子目录

**🎯 Operational Feel**：
Python 打包环境（hatchling + twine）。模板有两处：`templates/`（开发源）
和 `src/myco/templates/`（打包入 wheel 的版本），改模板必须同步两处。
`pip install -e .` 后 `myco` CLI 指向 src/，不需要 build 就能测试。
```

**Round 3 结论**：hot zone 内容设计定案，置信度 87%。

---

## Round 4：_canon.yaml 规范值设计

### Myco 项目特有的规范值

标准模板有 `system` 和 `project` 两节，Myco 自身需要增加 `package` 节来固定打包相关的规范值：

```yaml
package:
  name: "myco"
  version: "0.9.0"                 # pip 版本，和 __init__.py 同步
  python_requires: ">=3.8"
  pypi_url: "https://pypi.org/project/myco/"
  github: "Battam1111/Myco"
  entry_cli: "myco"                # CLI entry point name
  build_backend: "hatchling"
  template_dirs:
    - "templates/"                 # 开发源
    - "src/myco/templates/"        # 打包版（需同步）
```

### 攻击 D1：这些值放在 _canon.yaml 而不是 pyproject.toml，是否重复？

**防御**：pyproject.toml 是打包工具读取的，_canon.yaml 是 agent/lint 读取的。两者受众不同。_canon.yaml 的 `version` 作为 SSoT 校准用——lint L2 的 stale patterns 可以检查文档里出现的"v0.8"等旧版本号。这是不重复的。

**Round 4 结论**：_canon.yaml 设计定案，置信度 85%。

---

## Round 5：log.md 重建——起点在哪里？

### 两个选项

**A. 从 git 初始 commit 开始（2026-04-08）**：完整历史，但事后重建的条目置信度低，有"伪造记录"感。

**B. 从今天（2026-04-09）开始，今天是 Myco 自我应用的第一天**：诚实，log.md 的 append-only 精神是"从这一刻开始记录"，不应该补写。

### 攻击 E1：缺少初期历史，新人看不到项目演进脉络

**防御**：git log 本身就是历史记录——每个 commit 都有日期、作者、消息。log.md 不是 git 的替代，而是**认知层面**的时间线。`architecture.md` 和 `decoupling_positioning_debate` 里已经有完整的演进叙事。log.md 从今天开始，记录"Myco 开始用 Myco 管理自身"这个里程碑，是最诚实的起点。

**裁决**：**选项 B**，今天作为 log.md 起点。在第一条 milestone 条目里写明"Myco v0.x 开发历史详见 git log 和 docs/decoupling_positioning_debate_2026-04-09.md"。

**Round 5 结论**：置信度 90%。

---

## 终局收敛

| 决策 | 结论 | 置信度 |
|------|------|--------|
| 入口文件 | MYCO.md | 90% |
| docs/ 组织 | 原地保留 + decoupling 移至 current/ | 85% |
| wiki/ | 暂不创建页面（有机生长） | 95% |
| hot zone 内容 | 框架开发视角（非 user project 视角） | 87% |
| _canon.yaml | 增加 package 节 | 85% |
| log.md 起点 | 今天（2026-04-09），诚实原则 | 90% |

**综合置信度：88%**

剩余 12% 不确定性来自：
- hot zone 里的"最容易出错的事"需要实践验证（现在是推测）
- 随着 v1.0 的推进，_canon.yaml 的 package 节结构可能需要调整
- WORKFLOW.md 是否需要框架开发专属版本，还是通用版本足够（暂定通用版本，不够再分裂）
