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

## [2026-04-10] system | C 轮迭代：README 对标 MemPalace/Hermes/Nuwa 完全重构

对标三个开源标杆项目（MemPalace 水晶金字塔logo+居中开场+personal note / Hermes 全宽banner+for-the-badge徽标+feature表 / Nuwa 真实效果示例+多语言README+封面艺术），完成：(1) README.md 完全重构（居中logo、大号badges、导航锚点、效果示例"What It Looks Like"、Mem0 2026报告引用、个人叙事"The Story Behind Myco"、stats table）；(2) README_zh.md 中文完整版；(3) 品牌资产重做（超采样抗锯齿logo多尺寸导出、全宽banner、新social preview）。Logo仍为代码生成——专业级Logo需AI生图或设计师介入，这是当前的诚实边界。

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

## [2026-04-10] system | Publication readiness audit + cleanup（传统手艺 4 轮，91% 置信度）

开源/闭源分离执行：.gitignore 排除 11 个内部文件（本地保留）（commit_msg.txt / PYPI_SETUP.md / architecture.png / pypi_upload.bat / 6 个内部策略辩论记录）；保留 11 个框架设计辩论（intellectual transparency）。README 叙事回归：从 8 份辩论记录中恢复核心叙事（mycelium metabolism / tacit knowledge erosion / reflexive layer），融入 "The Story" + "Why Myco"。修复：_canon.yaml 版本 0.9.0→1.1.0、SECURITY.md 占位符邮箱、MYCO.md 删除已完成内部任务队列+过期引用、docs/current/README.md 索引清理。.gitignore 补全（Python 官方模板对齐）。

## [2026-04-10] milestone | 🎉 Myco MCP Server 实现 — agent 自动发现 5 个工具

实现 src/myco/mcp_server.py（Python FastMCP，stdio transport）。5 个 MCP 工具：myco_lint（9 维一致性检查）、myco_status（知识系统概览）、myco_search（跨 wiki/docs/MYCO.md 搜索）、myco_log（摩擦/反思记录）、myco_reflect（Gear 2 会话反思提示）。配置：.mcp.json 自动发现 + pyproject.toml [project.optional-dependencies] mcp。所有工具测试通过：lint 9/9 PASS、status 正确读取版本/阶段/任务、search "metabolism" 返回 42 匹配。这是 Myco 从"被动工具"到"主动基础设施"的关键跃迁——agent 安装后自动获得知识代谢能力。

## [2026-04-10] debate | 传统手艺：愿景漂移恢复辩论（4 轮，≥92% 置信度，三次递归 extraction）

起因：Yanjun 在公开发布前夕感到叙事层漂移——README 与 2026-04-08 原始愿景不符。从本地 ascc_sessions 04-08 会谈抽取到 **18 项**被压缩丢失的身份元素，分三轮递归恢复：R1 抓到 4 项（substrate / CPU / 非参数进化 / 代谢入口）→ R2 抓到 7 项（永恒进化律 / 变异-选择 / 透明性反癌 / agent 为主体 / 活-死框架 / 无意识原型 / 六向对比）→ R3 抓到 7 项（压缩即认知 / 七步管道含淘汰 / 四层自我模型 / 死知识 / 结构性 vs 事实性退化 / kernel-instance 分离 / 理论血统 Karpathy+Polanyi+Argyris+PDCA+Voyager）。18 项元素全部恢复至 README.md / README_zh.md / MYCO.md 身份锚点段落，永久锚点文档 `docs/current/vision_recovery_craft_2026-04-10.md` 含原文引证 + MemOS / A-Mem / Self-Evolving Agents survey 外部验证。两次干净 commit 推送 origin/main。→ g4-candidate（Gear 4：把"递归 extraction 直到收敛"提炼为通用压缩失败恢复程序）

## [2026-04-10] system | L9 愿景锚点 lint 上线——把一次漂移失败转为永久结构保障

将 2026-04-10 愿景恢复事件编码为 lint 规则：`scripts/lint_knowledge.py` 新增 L9 Vision Anchor Check，`_canon.yaml` 新增 `system.vision_anchors` 字段（12 个 lexical anchor groups，min_sufficient 集合），`docs/current/vision_recovery_craft_2026-04-10.md §7` 作为权威源（Machine-Readable Anchor Terms 表，与 canon 双向同步）。Target files: README.md / README_zh.md / MYCO.md。首次运行捕获 1 CRITICAL（MYCO.md 缺 perpetual-evolution 锚点）→ 补充"永恒进化 / 停滞即死"段落后 10/10 PASS。这把"作者每次公开发布前要记得检查愿景是否漂移"从人类警觉性职责转成基质自检职责——Gear 3 的典型工作：用一次结构化失败生成一条新的结构化规则。

## [2026-04-10] debate | 传统手艺：消化结构与跨项目架构（4 轮，90% 置信度，含 7 处外部文献交叉验证）

起因：Yanjun 提出两条深层质疑——(1) 跨项目经验无处安放（HPC lesson 被误写入 kernel 仓 docs/operational_narratives.md）；(2) Myco 只有 wiki（胃）没有完整消化道，ASCC 实践暴露三大摩擦（无法消化 / 无法使用 / 意识不到要用）。4 轮 debate 结论：**双层架构**（kernel + commons 同仓打包隔离 / instance 加 notes/）+ **扁平 zettelkasten 发酵池**（不是七器官消化道——被 A-Mem arXiv 2502.12110 和 Obsidian dataview 18k 实证推翻）+ **MCP 工具反射驱动**（不是 session hook——违反 agent-agnostic 律）+ **三步 Week 1/2/3 实施路径**带硬验收指标。外部参考：MemOS 三层存储 + A-Mem zettelkasten + Letta agent-driven tier migration + Voyager skill library cold start + Obsidian dataview scaling + Claude MCP tool discovery + MemOS OpenClaw 2026-03 更新。Yanjun 当场批准三个最硬取舍（commons 同仓 / 四件套 MVP / 不补人类反射弧）。详见 `docs/current/digestive_architecture_craft_2026-04-10.md`。→ g4-candidate（把"attack 阶段绝不跳过"提炼为 debate 协议硬规则，Meta 反思里暴露第一直觉全是过度设计）

## [2026-04-10] decision | v1.2 roadmap 换血：从 "ingest/MemPalace/--adapter generic" 三项改为消化道 Week 1/2/3

MYCO.md 任务队列前三项替换：Week 1（eat/digest/view/hunger + notes/ + L10 + 四个 MCP）/ Week 2（基于摩擦数据迭代 extract/integrate）/ Week 3（commons + promote + L11/L12 + HPC lesson 洗仓）。Metabolic Inlet（任务 4）保持 v2.0 声明不动。原三项（ingest/MemPalace/--adapter generic）推迟到 v1.3 或根据 Week 1-3 数据重新评估必要性——它们解决的是"怎么把别人的东西搬进来"，而消化道解决的是"搬进来后怎么处理"，后者是前者的前置条件。

## [2026-04-10] meta | Gear 2 反思：递归 extraction 作为通用压缩失败恢复程序

本次会话最大的元教训：**上下文压缩丢失身份内容的多少，取决于总结器判断可丢弃的比例，而不是作者认为的重要性**。第一次恢复找到 4 项（用户说"还有其他重要的吗？"）→ 第二次找到 7 项（用户说"压缩相关那条呢？"）→ 第三次找到 7 项。三轮才收敛。推论：任何未来的漂移恢复都应预期 ≥3 轮递归，且信任结构性保障（L9）超过作者警觉性。更深的 Gear 4 candidate：把"递归 extraction 直到收敛 + 把收敛结果编码为 lint 规则"提炼为一条通用 procedure，适用于所有长项目中的叙事漂移事件，不限于 Myco 本身。
