# Project Timeline (append-only)

> 每次关键事件发生后追加一行。格式：`## [YYYY-MM-DD] type | description`
> Type: `milestone` | `decision` | `debug` | `deploy` | `debate` | `system` | `friction` | `meta` | `contradiction` | `validation` | `script`
>
> **注**：Myco v0.x 开发历史（2026-04-08 之前）详见 `git log` 和 `docs/current/decoupling_positioning_debate_2026-04-09.md`。本 log 从 Myco 开始用 Myco 管理自身这一时刻起记录（诚实原则，不事后重建）。

---

## [2026-04-09] milestone | Myco v0.9.0 发布至 PyPI，完成 pip install myco 全链路

## [2026-04-09] debate | 传统手艺：Myco 自我应用设计辩论（6 项决策，综合置信度 88%）

关键结论：入口 MYCO.md（agent-agnostic）、hot zone 框架开发视角、_canon.yaml 增加 package 节、log.md 今日为起点。详见 `docs/current/myco_self_apply_craft_2026-04-09.md`。

## [2026-04-09] system | Myco 自我应用完成：MYCO.md + _canon.yaml + log.md + docs/WORKFLOW.md 写入

## [2026-04-09] milestone | Gear 3 完成：v0.9.0 + 自我应用里程碑回顾（详见 docs/current/gear3_v090_milestone_2026-04-09.md）

Gear 3 三项发现：(1) CLI UTF-8 跨平台 bug → 已修复（sys.stdout.reconfigure）；(2) 双模板设计债务 → 用户授权删除顶层 templates/，单一化完成 → g4-candidate；(3) Windows 操作规范未文档化 → 已写入 docs/operational_narratives.md P-001。全部 5 项行动项 ✅。

## [2026-04-09] debate | 传统手艺：examples/ 设计辩论（5 轮，综合置信度 84%）

核心结论：examples/ 定位为 Gear 4 生命周期展示（不是 onboarding 教程）。每个 example 包含 Harvest 快照 + Gear 4 反向链接。社区贡献三级管线（Discussion → Battle Report → Featured Example）。详见 `docs/current/examples_design_craft_2026-04-09.md`。

## [2026-04-09] system | 升级 examples/ascc/README.md：补 Gear 4 反向链接 + Evolution Timeline + wiki 页眉展示

## [2026-04-09] system | CONTRIBUTING.md 补充 "From Battle Report to Featured Example" 三级贡献管线

## [2026-04-09] debate | 传统手艺：深度竞品定位辩论（6 轮，综合置信度 92%）

核心结论：(1) OpenClaw 346K 是市场验证信号非威胁，Myco 是进化层升级路径；(2) tagline 从 "teaches it to think" 更新为 "gives it metabolism"（准确度 70%→95%）；(3) Gear 4 已完成验证（不确定性清零）；(4) meta-evolution 可行性论证写入 README Philosophy；(5) 终极压力测试：对 OpenClaw+Hermes 用户的差异化是"反向（lint）+ 垂直（Gear 3 Double-loop）"。详见 `docs/current/positioning_craft_2026-04-09.md`。

## [2026-04-09] system | README.md + MYCO.md + decoupling debate 生命周期标签全部更新（tagline、Status、对外定位一句话、文档索引）

## [2026-04-09] debate | 传统手艺 #1：ASCC/Myco 解耦边界辩论（3轮，93%置信度）

核心结论：(1) evolution_engine.md 4处ASCC专属内容（badge/axes/消融组/Caveman）替换为通用示例（API限流/配置格式/接口设计）；(2) architecture.md header "ASCC项目" → 通用表述+examples/ascc/参考；(3) docs/current/ ASCC-era 文件保留但通过[ORIGIN]标签+README说明区分性质；不需要删除任何辩论历史记录。详见 `docs/current/decoupling_craft_2026-04-09.md`。

## [2026-04-09] system | ASCC 解耦执行完成：evolution_engine.md（4处）+ architecture.md（1处）+ docs/current/README.md（分类说明+新文档条目）；lint L0-L8全绿 ✅

## [2026-04-09] debate | 传统手艺 #3：一键采用 + 社区生态辩论（4轮，综合置信度 87%）

核心结论：(1) adapter 接口确定为 adapters/ YAML manifest，v0.x=手工协议+lint验证，v1.0=CLI自动化；(2) 社区贡献4种类型（Template/Lint Rule/Adapter/Workflow Principle）+ 三级验收标准（Adapter≥1项目，Template≥1项目，Principle≥2项目类型）；(3) 30秒采用路径：CLAUDE.md用户为首选，migrate→lint→首次发现不一致="aha moment"；(4) GitHub presence：README为何选Myco提前 + Discussions四分类 + 4种issue模板。详见 `docs/current/adoption_community_craft_2026-04-09.md`。

## [2026-04-09] system | 采用+社区执行完成：adapters/（README+hermes.yaml+openclaw.yaml+mempalace.yaml）+ CONTRIBUTING.md 四类型贡献体系 + README Quick Start重构（migration首位）；lint L0-L8全绿 ✅

## [2026-04-09] debate | 传统手艺 v1.0 scope 定义（4轮，综合置信度 89%）

核心结论：v1.0 三项充分条件——(A) migrate 输出优化（aha moment 诚实定义）；(B) adapters/cursor.yaml + adapters/gpt.yaml（coexistence guide schema，非迁移协议）；(C) WORKFLOW.md 扫描确认 agent-neutral + README v0.x→v1.0 声明升级。不在 v1.0：myco config/ingest/MemPalace CLI（推迟至 v1.1）。详见 `docs/current/v1_scope_craft_2026-04-09.md`。

## [2026-04-09] debate | 传统手艺 v1.1 scope 定义（3轮，综合置信度 87%）

核心结论：(D1) myco config --set/get/list/unset adapters.* 操作 _canon.yaml [adapters] 节（与 lint 验证字段完全隔离）；(D2/D3) myco import 半自动化——扫描→交互确认→创建 W8 stub→lint；(D4) adapters/hermes.yaml 和 openclaw.yaml roadmap v1_1 替换 v1_0。不在 v1.1：--adapter generic 模式（v1.2）、myco ingest MemPalace（v1.2）。详见 `docs/current/v1_1_scope_craft_2026-04-09.md`。

## [2026-04-09] milestone | 🎉 Myco v1.0.0 发布准备完成

v1.0 三项充分条件全部达成：(A) migrate.py aha moment 输出优化；(B) adapters/ 完整体系（Claude Code / Cursor / GPT / Hermes / OpenClaw / MemPalace 共 6 个 adapter）；(C) pyproject.toml 0.9.0→1.0.0，classifier Beta→Production/Stable，README v0.x 限制声明→v1.0 multi-agent 验证声明。lint L0-L8 全绿 ✅

## [2026-04-10] debate | 传统手艺 README 重写策略（4轮，87%置信度）

核心结论：(1) Hero = 问题→方案→tagline（不以功能列表开头）；(2) Quick Start 两阶段展示（全绿基线 + 工作后 lint 发现矛盾）；(3) 深度内容（Laws/Philosophy/W1-W12/Bootstrap/Project Adaptation）迁出 README 移入 docs/architecture.md Appendix；(4) 全英文 + 中文概念括号注释惯例。详见 `docs/current/readme_craft_2026-04-10.md`。

## [2026-04-10] system | README 重写完成：产品级 landing page（≤800字散文）+ architecture.md 五个 Appendix 新增

## [2026-04-10] debate | 传统手艺 B2 品牌视觉策略（4轮，88%置信度，含在线调研）

核心结论：(1) 设计哲学 "Metabolic Cartography"（精密菌网图，工程审美）；(2) 色彩系统 #0D1117 + #00D4AA；(3) Logo = Hyphal Node（菌根节点，6条有机射线 + 末端小点，SVG深/浅双色版）；(4) Social Preview = 菌网图（左60%）+ 项目名+tagline+pip install（右40%）；(5) README 架构图 > 齿轮图（优先级分级）。在线调研确认：Mem0 2026报告亲口将"memory staleness detection"列为未解决挑战，正是myco lint所做之事。详见 `docs/current/brand_craft_2026-04-10.md`。

## [2026-04-10] system | B2 品牌资产创建完成：assets/social_preview.png + assets/architecture.png + assets/logo_dark.svg + assets/logo_light.svg；README 嵌入架构图

## [2026-04-10] system | B5 GitHub 社区文件创建完成：.github/ISSUE_TEMPLATE/adapter_submission.md + SECURITY.md + CODE_OF_CONDUCT.md

## [2026-04-10] debate | 传统手艺 B6 发布策略（2轮，87%置信度，含在线调研）

核心结论：(1) 发布序列：Show HN（W1周二）→ r/LocalLLaMA（W1周四）→ r/ClaudeAI（W1周五）→ Twitter/X（M1）；(2) r/LocalLLaMA 社区规则"punish hype"→需具体数据+踩坑故事；(3) 首发文案以Day3三处不一致事件为hook；(4) 5个FAQ预案准备完毕。详见 `docs/current/launch_craft_2026-04-10.md`。

## [2026-04-10] deploy | Myco v1.1.0 发布至 PyPI — pip install myco 现在安装 1.1.0（含 myco config + myco import）

## [2026-04-10] milestone | 🎉 Myco v1.1.0 CLI 自动化完成

v1.1 三项交付：(D1) myco config --set/get/list/unset adapters.* ← 配置隔离至 _canon.yaml [adapters] 节；(D2) myco import --from hermes [dir] ← 半自动 W8 stub 生成；(D3) myco import --from openclaw [file] ← MEMORY.md 分节映射至 wiki/docs/MYCO.md；CLI 冒烟测试全部通过；lint L0-L8 全绿 ✅
