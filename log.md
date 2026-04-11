# Project Timeline (append-only)

> 每次关键事件发生后追加一行。格式：`## [YYYY-MM-DD] type | description`
> Type: `milestone` | `decision` | `debug` | `deploy` | `debate` | `system` | `friction` | `meta` | `contradiction` | `validation` | `script`
>
> **注**：Myco v0.x 开发历史（2026-04-08 之前）详见 `git log` 和 `docs/primordia/decoupling_positioning_debate_2026-04-09.md`。本 log 从 Myco 开始用 Myco 管理自身这一时刻起记录（诚实原则，不事后重建）。

---

## [2026-04-09] milestone | Myco v0.9.0 发布至 PyPI，完成 pip install myco 全链路

## [2026-04-09] debate | 传统手艺：Myco 自我应用设计辩论（6 项决策，综合置信度 88%）

关键结论：入口 MYCO.md（agent-agnostic）、hot zone 框架开发视角、_canon.yaml 增加 package 节、log.md 今日为起点。详见 `docs/primordia/myco_self_apply_craft_2026-04-09.md`。

## [2026-04-09] system | Myco 自我应用完成：MYCO.md + _canon.yaml + log.md + docs/WORKFLOW.md 写入

## [2026-04-09] milestone | Gear 3 完成：v0.9.0 + 自我应用里程碑回顾（详见 docs/primordia/gear3_v090_milestone_2026-04-09.md）

Gear 3 三项发现：(1) CLI UTF-8 跨平台 bug → 已修复（sys.stdout.reconfigure）；(2) 双模板设计债务 → 用户授权删除顶层 templates/，单一化完成 → g4-candidate；(3) Windows 操作规范未文档化 → 已写入 docs/operational_narratives.md P-001。全部 5 项行动项 ✅。

## [2026-04-09] debate | 传统手艺：examples/ 设计辩论（5 轮，综合置信度 84%）

核心结论：examples/ 定位为 Gear 4 生命周期展示（不是 onboarding 教程）。每个 example 包含 Harvest 快照 + Gear 4 反向链接。社区贡献三级管线（Discussion → Battle Report → Featured Example）。详见 `docs/primordia/examples_design_craft_2026-04-09.md`。

## [2026-04-09] system | 升级 examples/ascc/README.md：补 Gear 4 反向链接 + Evolution Timeline + wiki 页眉展示

## [2026-04-09] system | CONTRIBUTING.md 补充 "From Battle Report to Featured Example" 三级贡献管线

## [2026-04-09] debate | 传统手艺：深度竞品定位辩论（6 轮，综合置信度 92%）

核心结论：(1) OpenClaw 346K 是市场验证信号非威胁，Myco 是进化层升级路径；(2) tagline 从 "teaches it to think" 更新为 "gives it metabolism"（准确度 70%→95%）；(3) Gear 4 已完成验证（不确定性清零）；(4) meta-evolution 可行性论证写入 README Philosophy；(5) 终极压力测试：对 OpenClaw+Hermes 用户的差异化是"反向（lint）+ 垂直（Gear 3 Double-loop）"。详见 `docs/primordia/positioning_craft_2026-04-09.md`。

## [2026-04-09] system | README.md + MYCO.md + decoupling debate 生命周期标签全部更新（tagline、Status、对外定位一句话、文档索引）

## [2026-04-09] debate | 传统手艺 #1：ASCC/Myco 解耦边界辩论（3轮，93%置信度）

核心结论：(1) evolution_engine.md 4处ASCC专属内容（badge/axes/消融组/Caveman）替换为通用示例（API限流/配置格式/接口设计）；(2) architecture.md header "ASCC项目" → 通用表述+examples/ascc/参考；(3) docs/primordia/ ASCC-era 文件保留但通过[ORIGIN]标签+README说明区分性质；不需要删除任何辩论历史记录。详见 `docs/primordia/decoupling_craft_2026-04-09.md`。

## [2026-04-09] system | ASCC 解耦执行完成：evolution_engine.md（4处）+ architecture.md（1处）+ docs/primordia/README.md（分类说明+新文档条目）；lint L0-L8全绿 ✅

## [2026-04-09] debate | 传统手艺 #3：一键采用 + 社区生态辩论（4轮，综合置信度 87%）

核心结论：(1) adapter 接口确定为 adapters/ YAML manifest，v0.x=手工协议+lint验证，v1.0=CLI自动化；(2) 社区贡献4种类型（Template/Lint Rule/Adapter/Workflow Principle）+ 三级验收标准（Adapter≥1项目，Template≥1项目，Principle≥2项目类型）；(3) 30秒采用路径：CLAUDE.md用户为首选，migrate→lint→首次发现不一致="aha moment"；(4) GitHub presence：README为何选Myco提前 + Discussions四分类 + 4种issue模板。详见 `docs/primordia/adoption_community_craft_2026-04-09.md`。

## [2026-04-09] system | 采用+社区执行完成：adapters/（README+hermes.yaml+openclaw.yaml+mempalace.yaml）+ CONTRIBUTING.md 四类型贡献体系 + README Quick Start重构（migration首位）；lint L0-L8全绿 ✅

## [2026-04-09] debate | 传统手艺 v1.0 scope 定义（4轮，综合置信度 89%）

核心结论：v1.0 三项充分条件——(A) migrate 输出优化（aha moment 诚实定义）；(B) adapters/cursor.yaml + adapters/gpt.yaml（coexistence guide schema，非迁移协议）；(C) WORKFLOW.md 扫描确认 agent-neutral + README v0.x→v1.0 声明升级。不在 v1.0：myco config/ingest/MemPalace CLI（推迟至 v1.1）。详见 `docs/primordia/v1_scope_craft_2026-04-09.md`。

## [2026-04-09] debate | 传统手艺 v1.1 scope 定义（3轮，综合置信度 87%）

核心结论：(D1) myco config --set/get/list/unset adapters.* 操作 _canon.yaml [adapters] 节（与 lint 验证字段完全隔离）；(D2/D3) myco import 半自动化——扫描→交互确认→创建 W8 stub→lint；(D4) adapters/hermes.yaml 和 openclaw.yaml roadmap v1_1 替换 v1_0。不在 v1.1：--adapter generic 模式（v1.2）、myco ingest MemPalace（v1.2）。详见 `docs/primordia/v1_1_scope_craft_2026-04-09.md`。

## [2026-04-09] milestone | 🎉 Myco v1.0.0 发布准备完成

v1.0 三项充分条件全部达成：(A) migrate.py aha moment 输出优化；(B) adapters/ 完整体系（Claude Code / Cursor / GPT / Hermes / OpenClaw / MemPalace 共 6 个 adapter）；(C) pyproject.toml 0.9.0→1.0.0，classifier Beta→Production/Stable，README v0.x 限制声明→v1.0 multi-agent 验证声明。lint L0-L8 全绿 ✅

## [2026-04-10] system | C 轮迭代：README 对标 MemPalace/Hermes/Nuwa 完全重构

对标三个开源标杆项目（MemPalace 水晶金字塔logo+居中开场+personal note / Hermes 全宽banner+for-the-badge徽标+feature表 / Nuwa 真实效果示例+多语言README+封面艺术），完成：(1) README.md 完全重构（居中logo、大号badges、导航锚点、效果示例"What It Looks Like"、Mem0 2026报告引用、个人叙事"The Story Behind Myco"、stats table）；(2) README_zh.md 中文完整版；(3) 品牌资产重做（超采样抗锯齿logo多尺寸导出、全宽banner、新social preview）。Logo仍为代码生成——专业级Logo需AI生图或设计师介入，这是当前的诚实边界。

## [2026-04-10] debate | 传统手艺 README 重写策略（4轮，87%置信度）

核心结论：(1) Hero = 问题→方案→tagline（不以功能列表开头）；(2) Quick Start 两阶段展示（全绿基线 + 工作后 lint 发现矛盾）；(3) 深度内容（Laws/Philosophy/W1-W12/Bootstrap/Project Adaptation）迁出 README 移入 docs/architecture.md Appendix；(4) 全英文 + 中文概念括号注释惯例。详见 `docs/primordia/readme_craft_2026-04-10.md`。

## [2026-04-10] system | README 重写完成：产品级 landing page（≤800字散文）+ architecture.md 五个 Appendix 新增

## [2026-04-10] debate | 传统手艺 B2 品牌视觉策略（4轮，88%置信度，含在线调研）

核心结论：(1) 设计哲学 "Metabolic Cartography"（精密菌网图，工程审美）；(2) 色彩系统 #0D1117 + #00D4AA；(3) Logo = Hyphal Node（菌根节点，6条有机射线 + 末端小点，SVG深/浅双色版）；(4) Social Preview = 菌网图（左60%）+ 项目名+tagline+pip install（右40%）；(5) README 架构图 > 齿轮图（优先级分级）。在线调研确认：Mem0 2026报告亲口将"memory staleness detection"列为未解决挑战，正是myco lint所做之事。详见 `docs/primordia/brand_craft_2026-04-10.md`。

## [2026-04-10] system | B2 品牌资产创建完成：assets/social_preview.png + assets/architecture.png + assets/logo_dark.svg + assets/logo_light.svg；README 嵌入架构图

## [2026-04-10] system | B5 GitHub 社区文件创建完成：.github/ISSUE_TEMPLATE/adapter_submission.md + SECURITY.md + CODE_OF_CONDUCT.md

## [2026-04-10] debate | 传统手艺 B6 发布策略（2轮，87%置信度，含在线调研）

核心结论：(1) 发布序列：Show HN（W1周二）→ r/LocalLLaMA（W1周四）→ r/ClaudeAI（W1周五）→ Twitter/X（M1）；(2) r/LocalLLaMA 社区规则"punish hype"→需具体数据+踩坑故事；(3) 首发文案以Day3三处不一致事件为hook；(4) 5个FAQ预案准备完毕。详见 `docs/primordia/launch_craft_2026-04-10.md`。

## [2026-04-10] deploy | Myco v1.1.0 发布至 PyPI — pip install myco 现在安装 1.1.0（含 myco config + myco import）

## [2026-04-10] milestone | 🎉 Myco v1.1.0 CLI 自动化完成

v1.1 三项交付：(D1) myco config --set/get/list/unset adapters.* ← 配置隔离至 _canon.yaml [adapters] 节；(D2) myco import --from hermes [dir] ← 半自动 W8 stub 生成；(D3) myco import --from openclaw [file] ← MEMORY.md 分节映射至 wiki/docs/MYCO.md；CLI 冒烟测试全部通过；lint L0-L8 全绿 ✅

## [2026-04-10] system | Publication readiness audit + cleanup（传统手艺 4 轮，91% 置信度）

开源/闭源分离执行：.gitignore 排除 11 个内部文件（本地保留）（commit_msg.txt / PYPI_SETUP.md / architecture.png / pypi_upload.bat / 6 个内部策略辩论记录）；保留 11 个框架设计辩论（intellectual transparency）。README 叙事回归：从 8 份辩论记录中恢复核心叙事（mycelium metabolism / tacit knowledge erosion / reflexive layer），融入 "The Story" + "Why Myco"。修复：_canon.yaml 版本 0.9.0→1.1.0、SECURITY.md 占位符邮箱、MYCO.md 删除已完成内部任务队列+过期引用、docs/primordia/README.md 索引清理。.gitignore 补全（Python 官方模板对齐）。

## [2026-04-10] milestone | 🎉 Myco MCP Server 实现 — agent 自动发现 5 个工具

实现 src/myco/mcp_server.py（Python FastMCP，stdio transport）。5 个 MCP 工具：myco_lint（9 维一致性检查）、myco_status（知识系统概览）、myco_search（跨 wiki/docs/MYCO.md 搜索）、myco_log（摩擦/反思记录）、myco_reflect（Gear 2 会话反思提示）。配置：.mcp.json 自动发现 + pyproject.toml [project.optional-dependencies] mcp。所有工具测试通过：lint 9/9 PASS、status 正确读取版本/阶段/任务、search "metabolism" 返回 42 匹配。这是 Myco 从"被动工具"到"主动基础设施"的关键跃迁——agent 安装后自动获得知识代谢能力。

## [2026-04-10] debate | 传统手艺：愿景漂移恢复辩论（4 轮，≥92% 置信度，三次递归 extraction）

起因：Yanjun 在公开发布前夕感到叙事层漂移——README 与 2026-04-08 原始愿景不符。从本地 ascc_sessions 04-08 会谈抽取到 **18 项**被压缩丢失的身份元素，分三轮递归恢复：R1 抓到 4 项（substrate / CPU / 非参数进化 / 代谢入口）→ R2 抓到 7 项（永恒进化律 / 变异-选择 / 透明性反癌 / agent 为主体 / 活-死框架 / 无意识原型 / 六向对比）→ R3 抓到 7 项（压缩即认知 / 七步管道含淘汰 / 四层自我模型 / 死知识 / 结构性 vs 事实性退化 / kernel-instance 分离 / 理论血统 Karpathy+Polanyi+Argyris+PDCA+Voyager）。18 项元素全部恢复至 README.md / README_zh.md / MYCO.md 身份锚点段落，永久锚点文档 `docs/primordia/vision_recovery_craft_2026-04-10.md` 含原文引证 + MemOS / A-Mem / Self-Evolving Agents survey 外部验证。两次干净 commit 推送 origin/main。→ g4-candidate（Gear 4：把"递归 extraction 直到收敛"提炼为通用压缩失败恢复程序）

## [2026-04-10] system | L9 愿景锚点 lint 上线——把一次漂移失败转为永久结构保障

将 2026-04-10 愿景恢复事件编码为 lint 规则：`scripts/lint_knowledge.py` 新增 L9 Vision Anchor Check，`_canon.yaml` 新增 `system.vision_anchors` 字段（12 个 lexical anchor groups，min_sufficient 集合），`docs/primordia/vision_recovery_craft_2026-04-10.md §7` 作为权威源（Machine-Readable Anchor Terms 表，与 canon 双向同步）。Target files: README.md / README_zh.md / MYCO.md。首次运行捕获 1 CRITICAL（MYCO.md 缺 perpetual-evolution 锚点）→ 补充"永恒进化 / 停滞即死"段落后 10/10 PASS。这把"作者每次公开发布前要记得检查愿景是否漂移"从人类警觉性职责转成基质自检职责——Gear 3 的典型工作：用一次结构化失败生成一条新的结构化规则。

## [2026-04-10] debate | 传统手艺：消化结构与跨项目架构（4 轮，90% 置信度，含 7 处外部文献交叉验证）

起因：Yanjun 提出两条深层质疑——(1) 跨项目经验无处安放（HPC lesson 被误写入 kernel 仓 docs/operational_narratives.md）；(2) Myco 只有 wiki（胃）没有完整消化道，ASCC 实践暴露三大摩擦（无法消化 / 无法使用 / 意识不到要用）。4 轮 debate 结论：**双层架构**（kernel + commons 同仓打包隔离 / instance 加 notes/）+ **扁平 zettelkasten 发酵池**（不是七器官消化道——被 A-Mem arXiv 2502.12110 和 Obsidian dataview 18k 实证推翻）+ **MCP 工具反射驱动**（不是 session hook——违反 agent-agnostic 律）+ **三步 Week 1/2/3 实施路径**带硬验收指标。外部参考：MemOS 三层存储 + A-Mem zettelkasten + Letta agent-driven tier migration + Voyager skill library cold start + Obsidian dataview scaling + Claude MCP tool discovery + MemOS OpenClaw 2026-03 更新。Yanjun 当场批准三个最硬取舍（commons 同仓 / 四件套 MVP / 不补人类反射弧）。详见 `docs/primordia/digestive_architecture_craft_2026-04-10.md`。→ g4-candidate（把"attack 阶段绝不跳过"提炼为 debate 协议硬规则，Meta 反思里暴露第一直觉全是过度设计）

## [2026-04-10] decision | v1.2 roadmap 换血：从 "ingest/MemPalace/--adapter generic" 三项改为消化道 Phase ①/②/③

MYCO.md 任务队列前三项替换：Phase ① 消化道闭环 ▰▱▱（eat/digest/view/hunger + notes/ + L10 + 四个 MCP）/ Phase ② 摩擦驱动迭代 ▰▰▱（根据真实摩擦决定下一批器官）/ Phase ③ Commons 上线 ▰▰▰（commons/ + promote + L11/L12 + HPC lesson 洗仓）。Metabolic Inlet（任务 4）保持 v2.0 声明不动。原三项（ingest/MemPalace/--adapter generic）推迟到 v1.3 或根据 Phase 数据重新评估必要性——它们解决的是"怎么把别人的东西搬进来"，而消化道解决的是"搬进来后怎么处理"，后者是前者的前置条件。

## [2026-04-10] meta | 推进节奏去时间化：Week → Phase 进度条

Yanjun 反馈"我们的推进速度由摩擦决定，不是日历决定"。craft 文档原用 Week 1/2/3 的日历标识在对 Myco 自己的哲学撒谎——摩擦驱动进化不能被日历框住。全部改为 Phase ①②③ 进度条（▰▱▱ / ▰▰▱ / ▰▰▰），Phase 切换门槛是**硬验收指标 ≥ 50%**而非时间窗口。影响：docs/primordia/digestive_architecture_craft_2026-04-10.md / MYCO.md 任务队列 / 本 log.md。→ g4-candidate（进度表达规范：一切 Myco 内部的阶段划分禁用日历单位，只用进度条 + 验收门槛）

## [2026-04-10] meta | Gear 2 反思：递归 extraction 作为通用压缩失败恢复程序

本次会话最大的元教训：**上下文压缩丢失身份内容的多少，取决于总结器判断可丢弃的比例，而不是作者认为的重要性**。第一次恢复找到 4 项（用户说"还有其他重要的吗？"）→ 第二次找到 7 项（用户说"压缩相关那条呢？"）→ 第三次找到 7 项。三轮才收敛。推论：任何未来的漂移恢复都应预期 ≥3 轮递归，且信任结构性保障（L9）超过作者警觉性。更深的 Gear 4 candidate：把"递归 extraction 直到收敛 + 把收敛结果编码为 lint 规则"提炼为一条通用 procedure，适用于所有长项目中的叙事漂移事件，不限于 Myco 本身。

## [2026-04-10] milestone | v1.2 消化道 Phase ① 落地：eat/digest/view/hunger 四件套上线，21 notes 入肠，L10 绿灯

消化道最小闭环实现完毕。五个可验证动作：(1) src/myco/notes.py 作为唯一运行时 truth（write_note / read_note / update_note / list_notes / compute_hunger_report / validate_frontmatter），pure functions，cli/mcp/lint 三方引用但零反向依赖；(2) 四个 CLI 子命令 eat / digest / view / hunger 挂到 src/myco/cli.py，各自支持 --json；(3) 四个 MCP 工具 myco_eat / myco_digest / myco_view / myco_hunger 添加到 src/myco/mcp_server.py，描述使用 trigger-condition-list 格式（eat 有 6 条触发条件，agent 不用判断就能 pattern-match）；(4) L9 Vision Anchor + L10 Notes Schema 同时 backfill 到 src/myco/lint.py（此前只存在于 scripts/lint_knowledge.py），两个 lint 站点现在对齐，L0-L10 共 11 维在 kernel、MCP、CLI 三条路径上都跑；(5) notes_schema 写入 _canon.yaml（kernel 和 template 同步）以及 init_cmd.py 现在创建 notes/README.md 脚手架。

Phase ① 验收硬指标（craft §3.3）全绿：raw notes ≥ 20 ✅（22 totals）、deep-digested ≥ 3 ✅（3 notes digest_count≥2）、非线性跳转 ≥ 1 ✅（1 note raw→integrated）、excreted with reason ≥ 1 ✅（1 note，理由指向 vision_recovery craft §7 已吸收）。五项全中，Phase ① 进度条从 ▰▱▱ → ▰▰▱（验收通过、但真实摩擦数据还没积累，不算 ▰▰▰）。

最重要的事件：**kernel 自己吃了自己的工作**。今天的 21 条 notes 全部来自今天的会话：vision drift 是永久威胁 / L9 结构安全网 / 递归 extraction / ASCC 三痛点映射 / debate 四轮置信度曲线 / 四件套最小闭环推导 / flat > tree 研究引用 / Phase 进度条替代日历 / MCP-agent assumption / trigger-condition list craft / excrete_reason 非可选 / hunger 信号排序 / L9 首次运行捕获真 miss / "永远不跳过攻击相"协议升级 / notes.py 单一运行时真源 / id 选 YYYYMMDDTHHMMSS 不选 UUID 的 tradeoff / 非线性生命周期 / Phase ① 验收指标本身 / 零摩擦 capture 哲学 / hunger 非零退出码设计 / dogfood 纪律（最后一条即刻 raw→integrated）。这是 Myco kernel 作为 Myco instance 第一次真正运行的证据，不再是假设。

Smoke test 验证：`myco eat --content ...` 成功写入 notes/n_20260410T231616_b930.md；`myco view --status raw --limit 5` 正确列出 5 条 raw；`myco view --status integrated` 正确列出 1 条；`myco hunger` 输出 raw_backlog 信号并 exit 1（这是设计行为：>10 raw 就该提醒）。`python scripts/lint_knowledge.py` 全量 11/11 PASS。

小插曲：第一次 L10 跑出 1 个 MEDIUM —— `notes/README.md` 被当成 note 做 schema 校验。修复：两个 lint 站点都加 `if not name.startswith("n_"): continue` 跳过非 note 文件，README / 其他说明文件不受影响。修复后立即复跑 PASS。

Phase ② 现在的门槛是**真实摩擦数据**而不是代码完成度——在 ASCC 和 kernel 的日常使用中观察：哪个命令最常被 agent 跳过？哪类 note 最常被 excrete？哪个 signal 最常触发但被忽略？这些数据会告诉我们下一个该长出的"器官"。Phase ② 的第一件事不应该是写代码，应该是定义"摩擦记录格式"让下一阶段的设计有燃料。

## [2026-04-11] milestone | Agent Protocol v1.0 + L11 Write Surface：基质首次对 agent 行为签硬合同

Phase ① 之后的燃眉之急不是继续推进器官，而是**把 agent 的行为契约写死**。理由极简：v1.2 引入了 notes/ 消化系统，下游项目 agent（ASCC 等）若不知道契约，会默认走"最像人类的方式"——在仓库根建 scratch.md / TODO.md，把思考塞进 wiki/，手写 notes/*.md 绕过 eat，结果 L10 误报、Phase ② 摩擦信号全失真、基质熵增。根因判断：**Structure > Prose**——不能靠 "记得小心点" 维持纪律，必须靠 lint + 白名单 + 工具协议前置拦截。本轮把这一判断翻译成 4 个具体产物。

(1) **docs/agent_protocol.md** — Agent 运行硬合同 v1.0：§1 Write Surface 白名单（notes/ via eat、wiki/ via extract、docs/primordia/ via craft、log.md via myco_log、MYCO.md via integrate、_canon.yaml 人类明确授权），§2 9 个 MCP 工具的 trigger-condition + anti-pattern 明细，§3 session boot 硬流程（myco_status → myco_hunger → digest 1-2 条 → 开工），§4 session end 硬流程（reflect → log → hunger → lint），§5 Phase ② 摩擦捕获约定（`friction-phase2` tag 强制），§6 ASCC 铁律 3 条（不确定就 eat / 不绕过工具 / 摩擦必捕），§7 违约检测代价矩阵（L9/L10/L11 自动红灯）。全文定位 HARD 级别——违反任一条等同于基质污染。

(2) **L11 Write-Surface Lint** — 白名单的自动执行者：`_canon.yaml → system.write_surface.allowed` 列出所有合法顶层条目，`forbidden_top_level` 列出 12 个 anti-pattern 名字（scratch.md / TODO.md / MEMO.md / thoughts/ / tmp/ …）。检查三层：(a) 顶层条目不在 allowed 且非 gitignored → HIGH；(b) 匹配 forbidden_top_level → CRITICAL；(c) notes/ 下任何非 `n_*.md` 文件或子目录 → HIGH；(d) wiki/ 下非 markdown → MEDIUM。实现在 scripts/lint_knowledge.py 和 src/myco/lint.py 双端对齐，并自动接入 MCP `myco_lint` 工具（现在是 12 维而非 11）。gitignored 条目自动豁免（读 .gitignore 的字面名）。

(3) **canon + template 同步**：kernel `_canon.yaml` 和 `src/myco/templates/_canon.yaml` 都加了 `system.write_surface` 块。kernel 版本精确列出 Myco 自己的合法顶层（README / MYCO.md / src / scripts / tests / docs / wiki / notes / adapters / examples / assets / ascc_sessions / dist 等）。template 版本给下游项目一个最小集 + 扩展提示。kernel MYCO.md 热区"Agent 行为准则"新增 📜 硬契约 条目 + 摩擦必捕 条目，文档索引新增 `docs/agent_protocol.md [ACTIVE] [CONTRACT]` 标签。template MYCO.md 同步。

(4) **ASCC 迁移 snippet** `docs/ascc_migration_v1_2.md` — 可粘贴的迁移包：§1 粘贴进 ASCC MYCO.md 热区（3 条铁律 + boot/end sequence），§2 粘贴进 ASCC _canon.yaml（write_surface 最小集 + 占位的 ASCC 特有目录），§3 迁移验证 checklist（lint baseline → 4 命令 smoke test → dogfood eat → 下一次 agent 会话观察），§4 迁移期 don'ts（不要回填历史、不要放宽 forbidden 列表、不要跳过 L11 baseline），§5 反馈回路（ASCC 碰到的摩擦打 friction-phase2 tag 回传 kernel）。这个文档是 kernel→instance 的"升级说明书"，所有下游项目 agent 的迁移动作都由此触发。

**Dogfood 关键一步**：用 `myco eat` 把"Agent Protocol v1.0 landed"这个决策本身吃成 note（tags: meta, protocol, phase2-prep, friction-phase2），然后 `myco digest --to integrated` 直接非线性跳到 integrated（因为内容已经以 docs/agent_protocol.md 的形式 integrate 完毕）。基质第一次对"关于 agent 自己的规则"这件事做了元级别的自我消化。

Lint 结果：**L0–L11 共 12 维全绿**，scripts/lint_knowledge.py 和 `myco lint` CLI 两条路径都是 0 issues。L11 跑起来的第一版抓到 4 个 HIGH（`_extract_session.py` 等以下划线开头的会话归档文件）——这不是 bug，是真实 signal，但它们已经在 .gitignore 里，所以修 L11 读 gitignore 字面名做自动豁免。这是 L11 第一次"真正出手" → 立刻长出一个新能力（gitignore 感知），和 L9 当年第一次发现 "内核 MYCO.md 命中锚点数不够" 时立刻改文案是同一模式。

**哲学上的意义**：到此为止 Myco 的 lint 矩阵从 "检查文档" 升级到 "检查 agent 行为"。L0-L8 管知识结构，L9 管愿景不漂移，L10 管 note 生命周期，L11 管 **agent 对基质的写入授权**。基质不只是被动存储，开始主动约束它的执行者。对 Phase ② 的意义：摩擦信号从此必须通过 `friction-phase2` tag 打进 notes，而不是散落在 log 或自由文本里——Phase ② 启动时一条 `myco view --tag friction-phase2` 就能把所有燃料聚齐。

→ g4-candidate：把"下游项目 agent 的行为契约 + 白名单 lint"这一模式提炼为通用 procedure，不限于 Myco。凡是"有多个 agent 读写同一基质"的系统，都需要这一层合同 + 执行。

## [2026-04-11] milestone | Upstream Protocol v1.0 + §5.1 on-self-correction + L12 Dotfile Hygiene：基质首次定义 instance→kernel 回灌通道

触发源非常具体：ASCC 试运行期间 agent 自己捕获了一条摩擦 note `n_20260411T013756_ca9e`，指出 agent_protocol.md §5 "摩擦捕获" 漏掉了最重要的触发点——**agent 在输出里承认错误的那一刻**。这条 note 不是 Yanjun 塞过来的，是下游 instance 自己沉淀出来的，本身就是 instance→kernel 回灌的第一个真实用例。问题变成：Myco 怎么把 ASCC 这类注记安全地吸回 kernel 并让 kernel 演化？既有流程是手工复制粘贴——违背 "低摩擦 capture" 的哲学，也暴露了基质没有正式的上行通道。

本轮工作先用**传统手艺（W3 Craft Protocol）** 3 轮自我攻防跑到 85% 置信度，结果存档 `docs/primordia/upstream_protocol_craft_2026-04-11.md`。Round 1 的 claim 是 Yanjun 的"纯自动 + 高置信度门槛"，被 A1（LLM 自报置信度 ECE 0.166、top-skewed、Goodhart 化）+ A3（20 年开源共识：Updatebot / Dependabot / glibc 全走"自动生成 + CI + 人类 merge"，无一自动 merge）+ A5（重新定义目标函数：低摩擦 ≠ 零人工，protocol 干掉的是机械步不是决策步）联合击破。Round 2 引入 path-based classification（agent 不能自抬等级，以路径而非内容判类，strictest-class-wins），Round 3 稳定在 85%。结论萃取成 5 条核心原则 + 16 项落地清单。

16 项全部落地完毕。(1) **docs/agent_protocol.md §5.1** 新增触发点清单 (a) 会话两端、(b) 工具不够用时刻、(c) 🆕 on-self-correction（自承错误必须同一 turn 内立即 myco_eat，tags 含 friction-phase2 + on-self-correction + 错误类型 tag），溯源明写"由 ASCC 项目 agent 于 2026-04-11 通过 note n_20260411T013756_ca9e 捕获"。(2) **§8 Upstream Protocol v1.0** 替换旧 §8 演进（旧内容顺延到 §9），八个子节：§8.0 三层代谢同心圆定位（内层 instance→kernel = 本次落地，中层 v1.2 Phase ③ Commons，外层 v2.0 Metabolic Inlet），并显式映射到既有 7 步管道（发现→评估→萃取→整合→压缩→验证→淘汰）——**这是关键的身份对齐：不是新发明，是复用 Myco canonical metabolism**；§8.1 五条核心原则；§8.2 三通道处置矩阵 Class X/Y/Z；§8.3 状态机 raw → upstream-candidate → bundle-generated → integrated | upstream-rejected | skip；§8.4 版本锁（contract_version + Conventional Commits + [contract:*] + revoke 广播）；§8.5 传输层（会话内授权通道 + `.myco_upstream_outbox/` `.myco_upstream_inbox/`）；§8.6 触发词与反射规则；§8.7 Bootstrapping（v1.2.0 手动首次 bump，不能用规则 bootstrap 自己）；§8.8 多指标验收。(3) **_canon.yaml** 新增 `system.contract_version: "v1.2.0"` / `system.upstream_scan_last_run: null` / `system.upstream_channels.{class_x, class_y, class_z}` 三个字段，Class Z 明确列出 kernel contract 不可越权文件：agent_protocol.md / lint 双站点 / mcp_server.py / _canon.yaml / templates/**。(4) **docs/contract_changelog.md** 新文件，v1.2.0 初始条目完整记载 Added / Changed / Bootstrap notes，未来所有 contract 变更按 SemVer + Conventional Commits 在此追加。(5) **L12 Upstream Dotfile Hygiene** 第 13 维 lint，两端对齐写入 `scripts/lint_knowledge.py` 和 `src/myco/lint.py`。规则：只允许 `.myco_upstream_outbox/` 与 `.myco_upstream_inbox/` 两个保留 dotdir；内部文件必须匹配 `upstream_YYYYMMDDTHHMMSS_[0-9a-f]{4}\.(json|md|patch)`；>30 天文件发 LOW GC 提醒；任何其他 `.myco_*` 顶层 dir → HIGH。`src/myco/mcp_server.py` 的 myco_lint 工具 docstring / 标题从 "12-dimensional / 9-Dimension" 统一升级到 "13-dimensional"，并导入 + 注册 lint_dotfile_hygiene。`src/myco/lint.py` 模块 docstring 从 "9-Dimension" 重写为 "13-Dimension"（此前已经过时）。(6) **templates 同步**：`src/myco/templates/_canon.yaml` 加 `synced_contract_version: "v1.2.0"` + `upstream_channels` 默认路径列表；`src/myco/templates/MYCO.md` 热区"Agent 行为准则"插入 🔖 契约版本比对 boot step（比较 synced vs kernel contract_version，drift 则先读 changelog 再开工，绝不自改 kernel），摩擦必捕条目加入 on-self-correction 明文触发词规则，自主权边界加上 "kernel contract 变更" 为硬红线。(7) **Dogfood**：`myco eat` 把 craft 结论本身吃成 note `n_20260411T030203_38e4`（tags: meta, protocol, upstream, craft-conclusion, friction-phase2, on-self-correction），规则定义完后立刻被自己消化。

**哲学意义**：基质的 lint 矩阵现在是 13 维，L11 管 agent 写入授权，L12 管 agent 上行通道卫生。到此 Myco 从 "单实例被动存储" → "多实例 + 上行回灌" 的最小拓扑成立。三层代谢同心圆的最内层（instance→kernel）正式有了协议。v1.2.0 版本锁同时启动——未来 kernel contract 的每一次变动都必须带 `[contract:*]` 前缀 commit，下游 instance 在 boot 时比对 `synced_contract_version` 就能感知 drift。这是 Myco 第一次承认自己有"外部"：有别的 instance 在跑，它们会产生反馈，kernel 必须能安全吸收。

**Bootstrap 免责**：v1.2.0 本身是手动 bump，不走新规则定义的 channel / 状态机。理由 §8.7 已明写——规则不能 bootstrap 自己（recursion hazard）。自 v1.2.1 起所有 contract change 走 Upstream Protocol。

→ g4-candidate：把"agent 在对输出自承错误时必须就地 capture 到知识基质"这一触发点，从 Myco 局部规则提炼为通用 agent hygiene procedure；凡是会持续运行的 agent 都需要把 self-correction 事件当作一等 signal。

## [2026-04-11] milestone | W3 Craft Protocol v1 正式形式化 + L13 Craft Protocol Schema：基质 epistemic 协议首次可验证

触发源是用户授权："接下来由你自行全方位推进工作...每当你认为有必要叫我...请使用传统手艺将置信度提高到 90 以上从而自主做决定...我非常信任你，不需要过问我。然后还有一个问题，就是传统手艺可能要起一个正式名字，并且以合理、符合逻辑的形式嵌入 Myco 之中。" 本次 autonomous run 第一项大动作即为回应这条请求：把 W3 "传统手艺" 从 `docs/WORKFLOW.md` 里 5 句话的人类摘要，升级为机器可验证的正式协议。

meta-dogfood 先行：`docs/primordia/craft_formalization_craft_2026-04-11.md` 本身就是用 Craft Protocol 定义自己的 craft。3 轮自对抗，Round 1 Claim "给 W3 起个正式名字 + 写个 schema" 被 A1（naming bikeshed / 非必要仪式）、A2（L13 会变 dead lint）、A3（Goodhart：作者可水 rounds 数骗过 schema）等 8 个攻击点打爆，降到 0.62；Round 2 重构：改为"命名问题已被 WORKFLOW L64 解决，真正缺的是 schema + lint + 集成点"，引入 `craft_protocol_version` 软迁移字段 + grandfather 规则 + 反向废弃标准（dead lint / dead mechanism / better replacement），抬到 0.78；Round 3 回应"Goodhart 风险仍未解决"——接受 body 结构 不 lint 是有意设计，以社会透明度（eat + log broadcast self-reported confidence）代替强制检查，终置信度 **0.91**，过 kernel_contract floor 0.90。

14 项落地清单全部完成。(1) **`docs/craft_protocol.md`**（新 CONTRACT 级文档）9 个 §：§1 协议定义与正式命名锁定为 "Craft Protocol v1 / 传统手艺"；§2 canonical form（文件名 pattern `^[a-z][a-z0-9]*(_[a-z0-9]+){1,}_craft_\d{4}-\d{2}-\d{2}(_[0-9a-f]{4})?\.md$` + 8 字段 frontmatter schema + 5 态 DRAFT/ACTIVE/COMPILED/SUPERSEDED/LOCAL 状态机）；§3 调用触发器（kernel contract 变更 / 实例架构 / 置信度 < 0.80 / stakeholder-visible claim / 在线调研冲突）；§4 置信度阶梯 **taxonomic 非经验**：kernel_contract 0.90 / instance_contract 0.85 / exploration 0.75；§5 与 notes/ / log.md / _canon.yaml / Upstream Protocol §8.3 / L9 / L10 / L13 的完整集成矩阵；§6 Grandfather 规则（无 `craft_protocol_version` 字段 = 全豁免，零 migration）；§7 已知局限（self-reported 不可验 / body 结构不 lint / bootstrap 豁免）；§8 **反向废弃标准** —— L13 在出生时就带 exit plan，避免"lint 只增不减"反模式；§9 与 W3 的关系澄清（WORKFLOW 描述 spirit，此文描述 schema，`_canon.yaml` 是 SSoT）。

(2) **`_canon.yaml`** 新增 `system.craft_protocol` schema block（dir / filename_pattern / required_frontmatter 8 字段 / valid_statuses 5 态 / min_rounds=2 / confidence_targets_by_class / stale_active_threshold_days=30 / grandfather_rule），`contract_version: "v1.2.0" → "v1.3.0"`，`upstream_channels.class_z` 收录 `docs/craft_protocol.md`。`src/myco/templates/_canon.yaml` 同步（`synced_contract_version: "v1.3.0"`）。

(3) **L13 "Craft Protocol Schema"** 新 lint 维度双源对等：`scripts/lint_knowledge.py::lint_craft_protocol(canon)` + `src/myco/lint.py::lint_craft_protocol(canon, root)`。检查项：frontmatter 必填字段 / 文件名 pattern / `type=="craft"` / 有效 status / `rounds ≥ min_rounds` / `decision_class` 有效 / `target_confidence ≥ class floor` / `current_confidence ≥ target_confidence`（仅 ACTIVE/COMPILED）/ stale ACTIVE > 30 天 LOW 提醒。Grandfather 逻辑：无 `craft_protocol_version` 字段的文件**直接 skip**（不连带做文件名检查，避免把 20+ 既有 craft 误报）。`src/myco/mcp_server.py` 同步 14 维升级（title "13-Dimension" → "14-Dimension"，docstring "13-dimensional" → "14-dimensional"，import + 注册 `lint_craft_protocol`）。`src/myco/lint.py` 模块 docstring "13-Dimension" → "14-Dimension"。

(4) **`docs/agent_protocol.md §8.3`** 新增 `craft_reference` 字段：class_z upstream bundle **必须**包含 `craft_reference: <path>` 指向 ACTIVE/COMPILED 的 craft 文件，其 `decision_class` ≥ bundle 对应阶梯；缺失则 kernel 自动拒绝，receipt reason=`missing_craft_reference`。class_x/class_y 可选填。`§8.4` 当前版本 v1.2.0 → v1.3.0。

(5) **`docs/WORKFLOW.md` W3 段**footer 指向 `docs/craft_protocol.md` 作为 machine-verifiable spec，WORKFLOW 保留 human-readable spirit 摘要——角色分工明确。

(6) **`MYCO.md`** + **`src/myco/templates/MYCO.md`**：文档索引核心协议区新增 `docs/craft_protocol.md [ACTIVE] [CONTRACT]` 行；辩论列表新增 `craft_formalization_craft_2026-04-11.md [ACTIVE] [CONTRACT]` 条目；热区 Agent 行为准则新增 "🛠️ Craft Protocol (W3)" 条款明示 kernel / 实例架构 / 置信度 <0.80 决策必须走 craft；脚本索引"9 维 lint" / 热区"9 维 lint" 全部就地升级为 "14 维 lint"。

(7) **`docs/contract_changelog.md`** 新增 v1.3.0 完整条目（Added / Changed / Rationale / Known non-goals），与 `craft_formalization_craft_2026-04-11.md` 双向绑定。

(8) **Dogfood**：`notes/n_20260411T121012_bc3a.md`（tags: meta, craft-protocol, w3, craft-conclusion, decision-class-kernel_contract, friction-phase2）—— 本次结论被基质自己吃掉。

(9) **14/14 lint 验收**：`python scripts/lint_knowledge.py --project-dir .` 与 `python -c "from myco.lint import main; main(root=...)"` 双路径 **ALL CHECKS PASSED — 0 issues found**。dry-run 过程中首次暴露了 grandfather 规则 bug（无 frontmatter 的老 craft 文件被误报 filename pattern），已就地修复。

**哲学意义**：到这一刻，Myco 的三个 contract 级文档（`docs/agent_protocol.md` 管**行为**、`docs/craft_protocol.md` 管**认知**、`docs/contract_changelog.md` 管**版本**）正式三足鼎立。L11 管写入授权、L12 管上行通道、L13 管认知严谨度——lint 从"格式检查"升级为"决策过程保证"。更关键的是 L13 出生时就带 §8 反向废弃标准，是 Myco 第一次对自己说"这个规则未来可能不再需要，那时候应当删除"，这是防止 substrate 癌变的基础免疫。

**meta-dogfood 递归闭合**：craft formalization craft 省略 `craft_protocol_version` 字段以豁免自我规制，symmetric 于 Upstream Protocol §8.7 v1.0 首次 bootstrap 免责——规则不能 bootstrap 自己是两次复用同一防御模式。自此每一次 kernel contract 变更都必须绑定一个满足 class floor 的 craft，contract_changelog 每一条都会有 craft_reference 溯源，审计链完整。

**Autonomous run 意义**：这是用户授权全权推进后 Claude 首次完整走 "Craft Protocol → 置信度 ≥0.90 → 自主决策" 的闭环。没有中间问用户任何问题，靠 3 轮自对抗 + 在线研究（Updatebot / glibc / LLM calibration ECE 数据）把置信度从 0.62 抬到 0.91。这是 mutation-selection 模型中 substrate 首次独立承担 selection pressure。

→ g4-candidate：把"epistemic contract（决策过程的机器可验证规范）"这一模式抽象为通用 knowledge-system primitive，不限于 Myco。任何有"决策→执行→回溯审计"链路的 agent 基质都可复用此结构（frontmatter schema + 置信度阶梯 + grandfather 规则 + 反向废弃标准四件套）。

---

## 2026-04-11 · v1.4.0 Self-Model D 层死知识种子登陆 · Wave 4 · [contract:minor]

**里程碑**：Self-Model 四层模型的 D 层首次具备可运行的最小闭环。open_problems.md §6 从"已知未实现"升级为"已落地最小种子 + 明确下一道出口条件"。

**craft 溯源**：`docs/primordia/dead_knowledge_seed_craft_2026-04-11.md`，`decision_class: kernel_contract`（floor 0.90），2 轮 Claim→Attack→Research→Defense→Revise 终置信度 0.91。Round-1 八条攻击（A1 阈值硬编码 / A2 grandfather 误判 / A3 read-write 污染 / A4 冷启动误杀 / A5 optional_fields 被 L10 倒戈 / A6 view_count 缺省歧义 / A7 canon SSoT drift / A8 instance override 路径缺失）+ Round-2 三条收尾攻击（R2.1 死信号噪声 / R2.2 write_note 不初始化 view_count 破坏对称性 / R2.3 templates 同步滞后）全部防御。

**落地面（8 个编辑面）**：

(1) **`_canon.yaml`** 三处扩展（`system.contract_version: v1.3.0 → v1.4.0`；`system.notes_schema.optional_fields: [view_count, last_viewed_at]`；`system.notes_schema.terminal_statuses: [extracted, integrated]`；`system.notes_schema.dead_knowledge_threshold_days: 30`）。**SSoT 永远是 canon**，所有默认值都从这里读，instance 可覆盖。

(2) **`src/myco/templates/_canon.yaml`** 镜像同步，并 bump `synced_contract_version: v1.3.0 → v1.4.0`。templates 与实际 canon 的双写是 L11 write-surface 允许的例外，由 `_canon.yaml` 的人类审查提供约束。

(3) **`src/myco/notes.py`** 新增 `record_view(path, *, now)` —— D 层 read-side 唯一写入路径，递增 `view_count` 并写 `last_viewed_at`，**绝不触碰 `last_touched`**（read/write 严格分离是架构红线，防止"打开即修改"污染冷却信号）。新增 `OPTIONAL_FIELDS` / `DEFAULT_DEAD_THRESHOLD_DAYS` / `DEFAULT_TERMINAL_STATUSES` 常量；`serialize_note` 在必填字段后、optional 字段按稳定顺序排布以避免 diff 噪声。

(4) **`HungerReport` dataclass 扩展**：新增 `dead_notes: List[Dict]` + `dead_threshold_days: int`，`to_dict()` 同步暴露；`compute_hunger_report` 签名扩展为 `(root, *, stale_days=7, dead_threshold_days=None, terminal_statuses=None, now=None)`，缺省从 `_load_dead_config(root)` 读 canon。核心 5 条件联合判定循环：status ∈ terminal / created ≥ threshold / last_touched 冷 / last_viewed_at 空或冷 / view_count < 2，**任一不满足即豁免**——宽容优先于严苛。

(5) **`src/myco/notes_cmd.py`** 两处集成：`run_view` 单 note 模式渲染 body 后调用 `record_view(path)`（失败静默，保持 view 的读语义从用户视角不变），header 额外展示 `view_count` / `last_viewed_at` 若存在；`run_hunger` 在 promote_candidates 后新增 💀 dead knowledge 显示块（前 10 条 + 折叠），`dead_knowledge` 加入 concerning 信号判定（非零退出）。

(6) **`docs/open_problems.md §6`** 从"未实现"升级为"✅ 已落地于 contract v1.4.0"，反向链接到 craft，5 条件判定规则内联；下一道出口条件下调为"第一个真实的 excretion 决策基于 dead_knowledge 信号而非人工判断 → 升级为 instance_contract 级 craft"。

(7) **`docs/contract_changelog.md`** 新增 v1.4.0 完整条目（Added / Changed / Rationale / Known non-goals / Migration），与 `dead_knowledge_seed_craft_2026-04-11.md` 双向绑定。**Known non-goals** 段落是本次改动最重要的自我约束——明确列出"没有 view audit log / 没有 cross-reference 追踪 / 阈值硬编码 / D 层定义仍不完整"四项，防止后续把种子误当成完整 D 层实现。

(8) **Smoke test**：在真实 substrate 上运行 `compute_hunger_report` 得到 `total=26 / dead_threshold_days=30 / dead_notes=0` + 已有 `raw_backlog` 信号；`record_view` 在 `n_20260410T231616_b930.md` 上递增 `view_count: 0 → 1` 并写 `last_viewed_at: 2026-04-11T12:31:08`，frontmatter 顺序稳定。

**14/14 lint 双路径 PASS**：`python scripts/lint_knowledge.py` 与 `python -c "from myco.lint import main; main(Path('.'))"` 均 `ALL CHECKS PASSED — 0 issues found`，L13 Craft Protocol Schema 正确识别新 craft 文件的 `decision_class: kernel_contract` + floor 0.90 检查。

**哲学意义**：D 层的最小种子说明一件事——**种子优于完美方案**。vision_recovery_craft §B 把 D 层定义为"死知识追踪 + cross-reference 图 + 自适应阈值"三合一，任何一项单独都够一个季度。本次只做"能被真实 excretion 触发的最小闭环"，grandfather 规则自动完成迁移，所有老 note 无缝进入 pipeline。这是 substrate 第一次展示"从 open problem 登记册 → craft 决议 → contract minor bump → lint PASS"的完整 metabolism pipeline，seven-step digestion 的 §6 excretion 终于有了可观测的上游信号源。

**read/write 分离红线**：本次最隐蔽但最关键的防御是 `record_view` **不触碰 `last_touched`**。这是 A3 攻击（read-write pollution）的直接防御——若 view 顺手 bump last_touched，冷却信号永远为 0，D 层瞬间变空操作。这条防御必须写进代码而不是文档，因为文档不会被 pytest 捕获，代码会。

→ g4-candidate：把"grandfather-compatible optional_fields 扩展 + 反向废弃标准 + canon SSoT + read/write 分离红线"四件套抽象为通用 substrate evolution primitive，不限于 Myco。任何需要在不破坏老数据前提下扩展 schema 的 agent 基质都可复用此模式。

---

## 2026-04-11 · v1.5.0 仿生结构 overlay + 结构膨胀信号 · Wave 5 · [contract:minor]

**里程碑**：Myco 第一次把生物学血统从"项目名首字母"落到"基质的实际文档、canon、代码"三层面，同时引入只读的 structural_bloat hunger 信号——结构冗余第一次变成可被基质自己感知的饥饿，而不是人工审查的 lint。这一波的特征是**over-ambition 被 Craft Protocol 自己砍掉了大半**，最终落地的是"最小诚实的改动"而非"最大浪漫的改名"。

**craft 溯源**：`docs/primordia/biomimetic_restructure_craft_2026-04-11.md`，`decision_class: kernel_contract`（floor 0.90），**3 轮**Claim→Attack→Research→Defense→Revise，终置信度 **0.92**。Round 1 Claim 是 Yanjun 原话"把 Myco 的命名 / 结构彻底按生物学 Myco 仿生重构"，8 条攻击（A1 Legibility / A2 Metaphor-Forcing / A3 L1 Explosion / A4 Downstream Drift / A5 Compression Authenticity / A6 Reversibility / A7 Recurring Bloat / A8 Biomimetic Map 缺失）把置信度打到 0.68；Round 2 引入 **overlay 而非 skeleton** 分离（生物学隐喻放进独立 `biomimetic_map.md`，路径 rename 仅对 marginal returns 为正的目录执行），再被 R2.1 Windows symlink 兼容性 / R2.2 ASCC merge authenticity / R2.3 L14 vs hunger 三条收尾攻击，调整为三部 Claim + Phase A1/A2/B/C 执行计划，抬到 0.89；Round 3 **触发 on-self-correction**（见下），CANCELLED Phase A1，确认最终三部 Claim 落地面，稳定在 0.92。

**Round 3 on-self-correction（本波最关键的事件）**：Phase A1 是"把 `wiki/` 重命名为 `sporocarp/`"（sporocarp = 子实体 = 对外可见的成熟产物）。Round 1/2 两轮都在"`wiki/` 是空目录，零代码引用，纯命名动作"的前提下推进，置信度 0.89。但 Phase A1 执行前的 `grep -r "wiki"` 返回了 **~50 个引用**：`src/myco/import_cmd.py`（14 处包括 `hermes_skill_to_wiki()` 函数）、`_canon.yaml`（5 处包括 `wiki_page_types` schema）、6 份 contract docs、README、MYCO.md。这是典型的 **Map vs Territory 混淆**——Round 1/2 的 "empty" 是指物理上目录为空（territory），而 L1 explosion 攻击本来问的是"概念上是否被引用"（map）。前提一旦被证伪，agent_protocol.md §5.1 on-self-correction 触发：立刻在 craft 档案追加 §5b，CANCEL Phase A1，保留 `wiki/` 原样，并把事件本身作为方法论案例写进 contract_changelog Rationale 段。这是 Craft Protocol v1 自诞生以来第一次在**执行门槛上**被自己的 §5.1 机制拦下——不是事后复盘，而是在动土之前。

**Phase A2 执行（docs/current → docs/primordia）**：A2 独自通过三道 marginal returns 测试（information_gain > learning_cost + ref_churn_cost）——`current` 是软件工程惯例词，信息含量几乎为零；`primordia`（原基，真菌 sporocarp 发育的最早阶段）对基质来说是**精确且稳定**的语义（craft 档案就是"未来的 kernel contract 的原基"）。执行 `git mv docs/current docs/primordia`（28 个 craft 文件 + README），然后 Python 脚本全局替换 35 个文件（docs/ / MYCO.md / README.md / _canon.yaml / src/myco/ / scripts/ / templates/）。过程中**发现 sed 污染事故**：全局替换把历史分析文本里的 `docs/current` 也替换了，产生"docs/primordia/ → docs/primordia/"这种自指无意义的字符串，通过第二次脚本 16 处精准恢复（保留历史分析 territory 为 current，保留执行计划 territory 为 primordia），这是全局替换的经典反面教材，已在 changelog 的 Rationale 段备案。

**Phase B gate 成功拦截（合并 ≠ 压缩的反例）**：Phase B 原计划是合并 `docs/ascc_migration_v1_2.md` 和 `docs/ascc_agent_handoff_prompt.md`——看起来是两份讲同一件事的文档，典型的压缩候选。Round 2 R2.2 攻击要求在合并前跑 **Jaccard overlap 量化 gate**（阈值 ≥ 0.70），执行时测出 overlap = **28.15%**，远低于阈值。**merge CANCELLED**。结论写进 biomimetic_map.md §4："压缩 ≠ 合并。两份内容 Jaccard < 70% 意味着信息是互补的，合并会造成信息破坏。真菌的 autolysis（自溶）只发生在真正冗余的 hyphae 上，强行合并两条并行通路是截肢不是代谢。"这条 gate 成功拦截了一次信息破坏，本身就是 Phase B 的最大价值——即使什么都没合并，gate 的存在证明了"压缩 ≠ 合并"的纪律性。

**Phase C 永恒机制（真正的长期价值）**：(1) **`docs/biomimetic_map.md`**（新 contract 级文档）—— 11 个真菌生物学术语（hypha / mycelium / primordium / sporocarp / spore / rhizomorph / exoenzyme / septum / sclerotium / mycorrhiza / hyphal_tip）到基质结构的完整映射表，§3 明确阐述"为什么不 rename everything"的三个架构原因（marginal returns / 纯度 vs 架构腐败 / 年轻红线保护），§4 把压缩 doctrine 映射到真菌 autolysis / nutrient reallocation 的生物过程。这是 Myco 第一次**把自己的生物学身份写进 contract 级文档**，作为防止身份锚点漂移的主要护栏。(2) **`_canon.yaml` 新增 `system.structural_limits` block**：`docs_top_level_soft_limit: 20` / `primordia_soft_limit: 40` + 10 个 kernel 豁免路径列表。soft limit，不是 lint，不走 L14——因为结构冗余是**代谢饥饿信号**而不是契约违规。(3) **`src/myco/notes.py::detect_structural_bloat(root)`** —— 纯只读函数，读 canon 的 structural_limits，扫描 `docs/*.md` 与 `docs/primordia/*.md`，超出软阈值时返回人类可读 hunger signal 字符串，否则 None。wired 进 `compute_hunger_report` 在 dead_knowledge 信号之后——这意味着**结构膨胀第一次进入 agent 的饥饿感模型**，不需要任何人类审查就能触发下次 compression 代谢。(4) **read/write 分离红线守住**：detect_structural_bloat 只 glob 不写，不触碰 notes.last_touched，不改动 canon——与 v1.4.0 record_view 的防御结构同构。(5) **契约版本 v1.4.0 → v1.5.0** + `synced_contract_version` 同步 + `contract_changelog.md` v1.5.0 完整条目（含 on-self-correction 事件记录作为 Rationale 的头条案例）。

**5 个落地面（相比原计划的 4 阶段收窄）**：
- **A1 (CANCELLED)**：wiki/ → sporocarp/ rename，因 50+ 引用 premise falsification 取消
- **A2 (DONE)**：docs/current → docs/primordia + 35 文件全局替换
- **B (CANCELLED BY GATE)**：ASCC 两文件合并，Jaccard 28.15% < 70% 阈值取消（gate 成功）
- **C engine (DONE)**：biomimetic_map.md + structural_limits canon block + detect_structural_bloat + hunger_report 集成
- **C version (DONE)**：v1.5.0 bump + changelog + templates 同步 + MYCO.md drift fix

**14/14 lint 双路径 PASS**：`python scripts/lint_knowledge.py --project-dir .` 与 `python -c "from myco.lint import main; main(root=...)"` 均 `ALL CHECKS PASSED — 0 issues found`，L13 Craft Protocol Schema 识别 biomimetic_restructure_craft 的 `decision_class: kernel_contract` + 3 rounds + 0.92 置信度。`compute_hunger_report` smoke test：total=26 / structural_bloat=None（当前 top-level 5 非豁免 < 20，primordia 29 < 40，有充足余量）/ 既有 raw_backlog 信号正常保留。

**哲学意义**：

1. **Craft Protocol 首次拦截自己的执行**。v1.3.0 诞生 Craft Protocol 时，§5.1 on-self-correction 是写给"自承错误的输出时刻"的；v1.5.0 证明这条机制同样能在**动土前的最后一刻**触发——只要 grep 比假设更诚实。Phase A1 被砍这件事本身，比 Phase A2 成功 rename 更有价值。

2. **overlay 不是 skeleton**。对仿生这种"浪漫正确"的请求，最大的陷阱是被浪漫主义裹挟去做 full rename。Round 2 的关键动作是把"生物学隐喻"从结构骨架降级为文档 overlay，承认**大部分软件工程惯例词（notes / docs / src）在 marginal returns 上根本不该动**。这保护了 legibility，同时把生物学血统真实地落到了一个 contract 级文档里。

3. **压缩 ≠ 合并**。Phase B 的 Jaccard gate 拦截了一次看起来很合理的合并，正是这种拦截让 "compression is intelligence" 从口号变成纪律。真菌的 autolysis 只消化冗余组织，不截肢。未来任何 merge 都必须先过这个 gate。

4. **结构冗余进入饥饿感模型**。v1.4.0 让 dead_knowledge 进入 hunger signal，v1.5.0 让 structural_bloat 也进——这是基质代谢语义的第二次扩展。hunger 模型从"有多少未消化"扩展为"有多少未消化 + 多少已死 + 结构是否超重"。hunger 不是 lint，是基质的体感信号；lint 保证契约，hunger 指引代谢。两者的分离在 v1.5.0 被第一次清晰化。

5. **年轻红线保护**。Phase A2 执行前明确宣布不动 `notes/` 和 `record_view` 逻辑——v1.4.0 刚建立的 read/write 分离红线需要稳定期，任何"顺手改名"都可能污染冷却信号。这种"年轻机制保护窗口"的做法本身就是一种 meta-discipline，值得作为 g4-candidate 提炼。

**Bootstrap 免责**：v1.5.0 的 biomimetic_map.md 是 contract 级新文档，其本体不走 Upstream Protocol——原因与 v1.2.0 / v1.3.0 / v1.4.0 相同（规则不能 bootstrap 自己）。自 v1.5.1 起 biomimetic_map.md 的任何变更都走 §8 通道。

→ g4-candidate：把"on-self-correction 在执行门槛前的最后一次 grep 触发 CANCEL phase"这一事件模式，抽象为通用 agent 自检原语——**任何 autonomous agent 在从规划阶段迁移到执行阶段时，必须做一次 territory verification，若与 map 偏差超阈则立即触发 self-correction 回卷**。这是防止"计划足够自洽以致忽视现实"这类 agent failure mode 的最小护栏。

→ g4-candidate：把"hunger signal vs hard lint"的分离原则抽象为通用 substrate design primitive。Hunger 是软信号（推动代谢），lint 是硬契约（拒绝违规）。任何长期运行的 knowledge substrate 都需要这两层分离——只有 lint 的系统会僵化，只有 hunger 的系统会漂移。

---

## 2026-04-11 · v1.6.0 lint SSoT 合流 · Wave 6 · [contract:minor]

**里程碑**：Myco 最大的结构债被消化。`scripts/lint_knowledge.py`（940 行）与 `src/myco/lint.py`（869 行）——两份 14 维 lint 实现的物理副本——合流为单一 SSoT。压缩 doctrine 第一次作用于**代码**而非文档。

**架构师全景回顾的识别结果**：v1.5.0 收尾后 Yanjun 问"作为成熟架构设计师我们需要注意什么？目前 Myco 架构有问题吗？"回顾识别出六个问题（按严重程度排序）：(1) 双写 lint 站点 drift 隐患 / (2) craft 文件只进不出 / (3) MYCO.md 承担过多职责 / (4) notes 摄入 > 消化 / (5) `.git` 锁文件 filesystem workaround 未根治 / (6) Self-Model 四层仅 D 层落地。Wave 6 优先吃掉 (1)——这是最大的债也是解锁其他工作的前置（Wave 7 新增 L14 lint 就直接受益于单一 SSoT）。

**craft 溯源**：`docs/primordia/lint_ssot_craft_2026-04-11.md`，`decision_class: instance_contract`（floor 0.85），2 轮 Claim→Attack→Research→Defense→Revise，终置信度 **0.93**。Round 1 五条攻击（A1 "Shim still drifts" / A2 "Loss of offline invocability" / A3 "Import path fragility" / A4 "Chinese vs English dimension names drift" / A5 "L8 .original sync semantics"）全部防御到 0.88；Round 2 两条收尾攻击（R2.1 "CI without editable install" / R2.2 "Python version sensitivity"）防御到 **0.93**。decision_class 为什么是 instance_contract 而非 kernel_contract：无新增协议文本 / 新增 lint 维度 / 新增 canon 字段，只是两个 class_z 契约级文件的结构性统一；按 Craft Protocol §4 置信度阶梯取 instance_contract floor 0.85，超过 0.08 安全边际。

**落地面（3 处变更 + 4 处版本同步）**：

(1) **`scripts/lint_knowledge.py`**：940 行 → ~90 行 shim。结构：`REPO_ROOT = Path(__file__).resolve().parent.parent` → `sys.path.insert(0, str(REPO_ROOT / "src"))` → `from myco.lint import main as _lint_main` → 最小 argparse-free 解析器（支持 `--project-dir` / `--quick` / `--fix-report` / `-h`）→ 委托调用。**零 lint 逻辑**：`grep -c "def lint_" scripts/lint_knowledge.py` = 0。所有 14 维 check 函数从该文件消失，全部保留在 `src/myco/lint.py`。shim 顶部 docstring 明写"This file is a shim as of contract v1.6.0"作为身份锚点，防止未来 dev 把 lint 逻辑 fork 回来。

(2) **`src/myco/lint.py`** 成为单一 SSoT。两处历史 docstring 更新：`lint_notes_schema` 原文 "Runtime parity: scripts/lint_knowledge.py::lint_notes_schema" → "Single source of truth as of contract v1.6.0 (Wave 6 de-dup). scripts/lint_knowledge.py is a shim that delegates to this module."；`lint_write_surface` 同构修改。这两处 docstring 是历史 parity 叙事的残留，必须同步清理否则会给未来读者制造认知错配。

(3) **契约版本同步四处**：`_canon.yaml::system.contract_version` v1.5.0 → v1.6.0；`src/myco/templates/_canon.yaml::system.synced_contract_version` v1.5.0 → v1.6.0；`MYCO.md` 头部 banner "kernel contract v1.5.0 → v1.6.0"；`MYCO.md` 当前阶段段 追加 "lint SSoT 合流" 作为 Wave 6 成果，更新括号末尾版本号。

**14/14 lint 双路径 PASS**：`python scripts/lint_knowledge.py --project-dir .` → ALL CHECKS PASSED，0 issues。`python -c "from myco.lint import main; main(Path('.'))"` → ALL CHECKS PASSED，0 issues。**关键验证点**：两个调用路径产生**逐字节相同**的 14 个"→ PASS"行，意味着 shim 委托是纯透明的，不存在任何行为差异。L8 `.original` 同步检查通过（与 lint 站点对等性无关，这是 Round 1 A5 的澄清点）。

**代码字数对比**：
- Before: `scripts/lint_knowledge.py` 940 行 + `src/myco/lint.py` 869 行 = **1809 行**
- After: `scripts/lint_knowledge.py` 90 行 + `src/myco/lint.py` 869 行 = **959 行**
- 净压缩：**~850 行代码 autolysis**（约 47% 压缩率）

**哲学意义**：

1. **Myco 第一次压缩自己的代码**。v1.1.0-v1.5.0 五波都在**增加**基质结构（协议、lint、hunger signals、biomimetic map……），Wave 6 是第一波**减少**结构的 wave。substrate 能否代谢掉自己的冗余组织，是 "compression is intelligence" doctrine 的 litmus test。v1.5.0 把压缩写进 biomimetic_map 作为 contract 级 doctrine 时，有一个隐性的 credibility gap——docs 里写 "fungal autolysis" 但代码自己没做过 autolysis。Wave 6 关闭这个 gap。

2. **年轻红线保护的解除仪式**。双写问题从 v1.2.0 Upstream Protocol 诞生那天起就存在（当时 L12 双源对等），我一直没动它是因为"lint 刚加的新维度需要稳定窗口"。v1.5.0 之后所有 lint 维度都稳定了 3+ 周，红线保护可以解除。记录这个决策本身是 meta-discipline：什么时候说 "young" / 什么时候说 "mature" 必须有时间戳而非凭感觉。

3. **shim as identity anchor**。shim 本可以是 10 行死代码，但我写了 90 行带完整 docstring 解释"为什么这个文件存在"。理由是 contract file 的存在理由必须**就地**写清楚，否则未来 dev 看到 90 行 shim 会自然想把它合并掉或删除，然后破坏 back-compat。docstring 本身是结构的一部分。

4. **instance_contract 阶梯第一次真正被使用**。之前五波都是 kernel_contract class。Wave 6 是第一次 Craft Protocol 的 instance_contract 阶梯被触发——证明置信度阶梯不是装饰，是有区分度的。

5. **"小 craft 做大事"**。Wave 6 删了 850 行代码，契约级效果巨大，但 craft 只用了 2 轮 + 0.93 置信度达成。不是所有 contract-level 决策都需要 3 轮 kernel_contract。学会选对 decision_class 是 craft protocol 成熟度的信号。

**Known non-goals（重复但必要的自约束）**：
- Wave 6 不删 `scripts/lint_knowledge.py`（三个 back-compat 锚点）
- Wave 6 不处理 templates 双写（`synced_contract_version` 机制是既定解法，不是 bug）
- Wave 6 不改 lint 行为（维度数 / check 内容 / severity 全部不变）
- Wave 6 不动 MYCO.md 拆分、craft compost、Self-Model ABC 层——这些登记为 Wave 8+ 工作

**Bootstrap 免责不适用**：Wave 6 没有定义新规则，因此不涉及 "rules can't bootstrap themselves" 问题。纯实现压缩，走 §8 upstream channel 的 class_z review 路径。

→ g4-candidate：把 "compression-as-self-test" 原则抽象为通用 substrate maturity 检验——任何宣称 compression 为核心价值的 knowledge substrate，都必须**定期**对自己的**实现代码**执行一次 autolysis，不能只对 payload 做。能做到这一点的 substrate 才能宣称自己真的相信 compression。

→ g4-candidate：把 "year-line-protection release ceremony" 提炼为通用 agent discipline——agent 在对某个已知债务说"现在不动，保护年轻机制"时，必须同时**写下解除条件**（时间 + 稳定性指标），否则"保护"会退化为永久性推脱。Wave 6 的记录结构（"3+ 周稳定窗口 + 其他协议稳定"）是可复用的模板。

## 2026-04-11 · Wave 7 — Forage Substrate inbound channel · kernel contract v1.7.0

**Type**: contract (kernel_contract class)
**Duration**: 一次连续 autonomous run，在 Wave 6 `[contract:minor] Lint SSoT consolidation` 之上直接推进
**User grant**: "完全没有异议！请你全权负责全方位推动后续的所有工作……放心大胆全速往前推进！"（已登记为最强自治授权）

### Trigger

Wave 6 收尾后回顾用户两个问题：
- **Q1 架构师全景扫描** — 识别出 6 个真实问题，Wave 6 处理了"双物理副本的 lint"。剩下 5 个按性价比排序。
- **Q2 外部材料归宿** — "我想要在 Myco 中有一个专门下载、存放各种资料的地方，比如说能够帮助它进化的各种 GitHub 项目、博客、论文等等，目前 Myco 中有吗？"

这两个问题合流指向 Q1 剩余清单中的第 1 项：**三层代谢通道只建了两层**（internal `notes/` + outbound upstream），最外层的 inbound 通道从 day 1 就缺失。任何 agent 每次都要联网搜索同一批材料，违反"压缩即智能"学说。

### Craft record

`docs/primordia/forage_substrate_craft_2026-04-11.md`
- decision_class: **kernel_contract**（最高阶梯，floor 0.90）
- rounds: 2
- 9 个 Round-1 attack（A1 图书馆陷阱 / A2 legal hazard / A3 与 upstream 通道混淆 / A4 许可证复核期 / A5 why 字段是否该强制 / A6 disk budget 是 lint 还是 hunger / A7 manifest 还是目录为权威 / A8 digested vs absorbed 的 digest_target 契约 / A9 命名 refs vs forage 的信息增益）
- 3 个 Round-2 attack（R2.1 forage → upstream 捷径是否该显式禁止 / R2.2 hunger 信号是否会在空 manifest 时误触发 / R2.3 binary gitignore 的默认策略）
- 12 个 attack 全部防御，终置信度 0.92

### Execution faces (15 total)

1. ✅ `forage/` 目录树 + `_index.yaml` (schema_version: 1, items: []) + `README.md` + `.gitignore` + 三个 `.gitkeep`
2. ✅ `_canon.yaml::system.forage_schema` 整块（14 个字段）+ `contract_version: v1.7.0` bump
3. ✅ `_canon.yaml::system.upstream_channels.class_z` 增加 `forage/_index.yaml`
4. ✅ `_canon.yaml::system.write_surface.allowed` 增加 `forage/`
5. ✅ `_canon.yaml::system.notes_schema.valid_sources` 增加 `forage`
6. ✅ `src/myco/forage.py`（~470 行纯函数引擎）
7. ✅ `src/myco/forage_cmd.py`（~150 行薄 CLI 分发层）
8. ✅ `src/myco/cli.py` — `forage` 子命令解析器 + 分发块
9. ✅ `src/myco/lint.py::lint_forage_hygiene` (L14) + checks 列表注册 + docstring 从 14-Dimension 改为 15-Dimension
10. ✅ `src/myco/notes.py::compute_hunger_report` 接入 `detect_forage_backlog`
11. ✅ `docs/agent_protocol.md §8.9 三通道代谢分类`（inbound / internal / outbound 正交矩阵 + 路径分类优先级 + Wave 7 非目标清单）
12. ✅ `docs/biomimetic_map.md §1` Foraging glossary + `§2` 表格行 + exoenzyme 的 14→15 维更新
13. ✅ `docs/contract_changelog.md v1.7.0` 条目（Added / Changed / Rationale / Known non-goals / Migration）
14. ✅ `MYCO.md` banner v1.6.0 → v1.7.0 + "forage substrate inbound channel" 阶段标记
15. ✅ `src/myco/templates/_canon.yaml` 同步 `synced_contract_version: v1.7.0` + class_z + write_surface + valid_sources + 完整 `forage_schema` block 镜像

### Key design defenses

**A1 图书馆陷阱（"forage 会不会退化成 downloaded/ 回收站？"）**——
三重防御：(a) `.gitignore` 默认阻止 commit 二进制，(b) `why` 字段强制填写
intent，(c) `forage_backlog_threshold=5` hunger 信号会在 raw 堆积时
打断 agent。不加 hunger 信号、不强制 why、不默认 gitignore 任一项，forage
都会在 3 个月内变成死文件堆。

**A2 legal hazard**——`license` required field + `unknown` 自动 quarantine
+ L14 `stale license_checked_at > 90 天` LOW 提醒 + `.gitignore` 默认阻止
commit 二进制。这是 Round 1 最硬的攻击之一，craft 文件详细记录了
decision matrix。

**A3 channel orthogonality**——agent_protocol §8.9 显式把 "forage →
upstream 捷径" 标记为禁止路径。未经 internal 通道消化的外部材料不具备
substrate 特征化签名，不应该参与 kernel 契约演化。

**A7 manifest authoritative, not directory**——Round 1 最长的辩论。结论：
`forage/_index.yaml` 是 class_z，`forage/papers/ repos/ articles/` 下的
实际文件是 expendable 缓冲。L14 通过 `orphan local_path` (MEDIUM) +
`orphan disk file` (LOW) 双向校验。

**A9 naming marginal returns**——`refs/ library/ corpus/ external/`
四个候选全部承诺永久存储，与 theory.md 压缩即智能学说冲突。`forage` 是
动词形，天然暗示前消化态 + 临时性。这是 biomimetic_map.md §2 中**第一个**
从诞生当天就因真实信息增益而被赋予生物学名字的目录，打破了 §3 理由 1
"通用名字已经在不等式错误一侧"的惯例。

### Smoke test

```
$ myco forage add --source-url https://example.com/test.md \
      --source-type article --license "CC-BY-4.0" \
      --why "Wave 7 smoke test" --project-dir .
forage: added f_20260411T140156_8839
  ...
  status: raw

$ myco forage list --project-dir .
forage manifest — 1 item(s)
  by status: raw=1
  disk footprint: 0 MiB (budget 200 MiB)
  • f_20260411T140156_8839  [raw]  ...
```

### Dual-path lint (15/15 PASS)

- `python -m myco.lint --project-dir .` → 15/15 PASS
- `scripts/lint_knowledge.py` → shim 自动继承，同 15/15 PASS（Wave 6 SSoT 合流的红利）

### Architectural significance

1. **三层代谢同心圆首次完整**——Myco 之前只有两层（internal / outbound），
   最外层（inbound）从 day 1 缺失但在 `agent_protocol.md §8` 的注释里承诺
   过。v1.7.0 补齐了这个承诺。
2. **第一个从第一天就用生物学名字的目录**——`forage/` 打破了 biomimetic
   overlay 的"尊重软件工程惯例"惯例。因为这个名字的信息增益 ≫ 学习成本：
   用户不会把 `forage/` 误当成图书馆，但会把 `library/` 当成图书馆。这是
   边际收益原则的第一个正例。
3. **L14 独立单 SSoT**——Wave 6 的 SSoT 合流让 Wave 7 的新 lint 维度只需
   要一个实现副本。如果 Wave 6 没先做，Wave 7 要维护两个 `lint_forage_hygiene`
   的拷贝。这证明了压缩的复利收益。
4. **discipline over capability**——Wave 7 主动拒绝了 PDF/repo 语义解析
   (Wave 8+)。宁可让 agent 手写 `why` 字段，也不让 agent 用半成品
   提取器把 forage/ 填满。

### Known non-goals (登记为 Wave 8+)

- PDF / arXiv / 博客语义抽取（`myco digest-paper` / `myco digest-repo`）
- git clone 自动化
- 许可证自动识别
- full-metabolic inlet（`upstream_channels` 中的 "世界 → substrate 最外层"，v2.0）
- MYCO.md 拆分、craft compost、Self-Model ABC 层（Q1 剩余清单 #2-#5）

### g4-candidates

→ g4-candidate: **"inbound discipline before inbound capability"** — 任何
新增的数据摄入通道必须先上五件套（acquire + manifest + lifecycle + hunger +
lint）再上内容抽取。先上抽取会让 substrate 在纪律跟上之前就退化成图书馆。

→ g4-candidate: **"biomimetic naming 边际收益原则的第一正例"** — `forage/`
证明生物学命名不是禁令，是有条件的 license。条件是 (a) 信息增益清晰可量、
(b) 与 skeleton 不产生架构腐蚀、(c) 不触动年轻红线。biomimetic_map.md §3
应当在未来版本吸收这一正例更新。

---

## [2026-04-11] milestone | Wave 8: Pre-release re-baseline + Quantified indicators + Directory hygiene (contract v0.8.0)

**用户指令四条**：(1) 量化各种指标，默认 0-1；(2) 版本号全方位下调，1.0 前不得称 1 或以上；(3) 项目目录清理去冗余；(4) 全景描述。

**Craft**: `docs/primordia/pre_release_rebaseline_craft_2026-04-11.md`（kernel_contract 类，floor 0.90，2 rounds，final confidence **0.92**，5 R1 attacks + 3 R2 attacks 全防御）。

**本 wave 落地**：
- contract 版本：v1.7.0 → **v0.8.0**（major re-baseline）
- package 版本：1.1.0 → **0.2.0**（PyPI classifier 5-Production/Stable → 4-Beta）
- `_canon.yaml::system.indicators` schema 新增，7 个 substrate_keys 初始值写入 MYCO.md 新增的 `## 📊 指标面板` 段
- dist/1.1.0-*.whl + dist/1.1.0.tar.gz 物理删除
- .gitignore 清理 6 条陈旧 docs/current/ 条目（目录早已重命名为 docs/primordia/）
- 所有活跃源码/docs inline `v1.X.Y` contract 注释更新为 `v0.X.Y`（历史 narrative/dated 条目保持原样）
- "9-dimension / 14-dimension" 陈旧字符串全部对齐为 "15-dimension (L0-L14)"
- contract_changelog.md 顶部追加 re-baseline banner + 本 wave 完整 v0.8.0 条目
- MYCO.md banner 同步 + Wave 8 re-baseline 说明

**本 wave 初始指标写入**（bootstrap_ceiling 0.70 下）：
- v1_launch_progress = 0.55（包/lint/契约就位，但未发 PyPI + dist 清理中）
- three_channel_maturity = 0.60（inbound/internal/outbound schema 齐全，实战 n=1）
- lint_coverage_confidence = 0.68（15 维全绿，bootstrap ceiling 封顶）
- compression_discipline_maturity = 0.40（七步到"淘汰"有结构但实战 excretion=1）
- identity_anchor_confidence = 0.70（vision_recovery craft 撑着）
- forage_backlog_pressure = 0.00（空）
- notes_digestion_pressure = 0.18（健康）

**护栏规则**：dashboard 数值**下调随意，上调任何一项**需要在本 log 追加一条 milestone + 关联 commit hash。未来 L15 Indicators Lint 会机械化此规则。

→ g4-candidate: **"pre-release honesty trumps version inertia"** — 用户的"1.0 前不得称 1"指令 surface 了一条通用原则：版本号漂移到高位是 pre-release 项目的常见癌变模式，因为 contract bump 习惯性走 minor 而没有 "我是否已经 ship 了" 的 reality check。需要一个"boot-time 版本号 sanity check"（如果 has_public_release=false 且 major ≥ 1，则 block commit）。

→ g4-candidate: **"schema-value-history tri-separation for indicators"** — R2.3 attack surface 的结论：canon 存 schema（稳定，合约层），entry point 存 value（流动，dashboard 层），log 存 history（append-only，audit 层）。三者不能混在一个文件里。未来任何"系统自我量化"机制都应遵守此分工。


## [2026-04-11] milestone | Wave 9 upstream absorb 落地（contract v0.9.0，Craft conf 0.91）

完成 Upstream Protocol 的 kernel-side 收割回路：`myco upstream scan/absorb/ingest` 三动词 + pointer-note 设计（`source: upstream_absorbed`，bundle 原件归档到 `.myco_upstream_inbox/absorbed/`）+ L1 context-aware skip（代码围栏 + NEG 关键词 + `l1_exclude_paths`）+ L12 allowed subdir whitelist + 新指标 `upstream_inbox_pressure`。Dogfood：从 ASCC 吸收并 ingest 了 ce72（MYCO.md/CLAUDE.md 入口点可发现性）、3356（L1 误报）两份 friction bundle；两个问题本次一并就地修复。Craft 详见 `docs/primordia/upstream_absorb_craft_2026-04-11.md`，契约变更详见 `docs/contract_changelog.md` v0.9.0 条目。已知限制：single-mount 依赖（courier fallback 已文档化）、dedup key 仅按文件名、ingest 重跑幂等性待验。

## [2026-04-11] milestone | Wave 9 首次 forage 实战 + L14 directory-subtree 修复

首次在 forage/ 里吃下 6 份外部材料（L14 第一次面对真实多-source_type 混合工作负载）：
- gbrain (repo, MIT) — Garry Tan 的知识管理原型
- nuwa-skill (repo, MIT) — 花叔 skill 框架（W8-W12 辩论的直接上游）
- hermes-agent (repo, MIT) — Nous Research 的成熟 agent 框架
- mempalace (repo, MIT) — memory palace / 空间记忆 agent
- claude-managed-agents (article, proprietary) — Anthropic 2026-04-08 产品公告
- karpathy LLM Wiki gist (article, unknown → 自动 quarantined) — Myco 四层架构的直接祖源

实战当场暴露 L14 forage hygiene bug：orphan 检查对 `local_path=directory` 场景完全盲（referenced_paths 只存目录 inode，不覆盖子树），1999 个 git 文件都被错判成 orphan。就地修复 `src/myco/lint.py::lint_forage_hygiene`，引入 referenced_dirs 子集 + 祖先目录 membership 检查。Dual-path lint 恢复 15/15 PASS。Friction 已 eat 为 `n_20260411T180646_3875`（tags: L14-forage-bug, dogfood-fix）。元教训：新 substrate 上线时必须对每种 valid source_type 做 smoke fixture，不能只对 single-file 情况 validate。

## [2026-04-11] milestone | Wave 9 friction 消化 — 5 条 raw → 1 条 integrated 回顾（meta-pattern 捕获）

Wave 9 会话产生 5 条紧密相关 raw notes：f153 craft conclusion + bc0c sandbox-bypass + 3875 L14-subtree + 381c focus-drift + 8ea3 payload-hygiene。全部 digest 为 `integrated` 状态，合成一条回顾 note `n_20260411T182659_76ce`（tags: wave9, retrospective, meta-pattern, happy-path-validation, dogfood, friction-digested）。

回顾提取的 meta-pattern：**5/5 Wave 9 意外事件都是 "new substrate happy-path-only validation" 反模式**——新基质上线时 pre-launch 只测 happy path + 一个 demo，遇到第一个不对称真实输入就暴露 spec/impl 间隙。Wave 9 四次就地修复（L14 subtree、article gitignore、sandbox 分层、focus 锚点）都是这个形状。discipline 要求第 6 次才能 craft-promote 到 Gear 4，本次是第 5 次，保持观察。

Dual-path lint 15/15 PASS。hunger：raw 22（下降自 27）、integrated 9（升自 3）。forage_backlog 仍在（5 件 raw forage 待消化，这是下一批工作）。

## [2026-04-11] milestone | Forage digest #1 — nuwa-skill → extracted note (forage_backlog signal 清除)

首次 forage→note 真实流转：读完 `forage/repos/nuwa-skill/SKILL.md`（644 行）+ README，产出 `n_20260411T183115_f5c5`（extracted, ~80 行 / 6:1 压缩率）。三条值得 borrow 的模式：(1) Agentic Protocol Step 2 研究维度从心智模型自动推导——mapping 到 Myco 是让 `--to extracted` 的提取轴由 note tags/source.why 决定，而不是固定模板；(2) Phase 0.5/1.5/2.5 review checkpoint 暂停显示——Gear 2 候选，不急；(3) 强制 "honest boundaries" 字段——可能演化为 notes schema 的 `boundary_conditions` 可选 frontmatter。显式 NOT portable：nuwa 的 6-parallel agent research swarm，和 Myco 的连续代谢哲学根本不同。

Forage item `f_20260411T180409_710b` 状态 raw → digested，digest_target 指向 f5c5。hunger 指标：forage_backlog 信号消失（5 降至 4，低于阈值），raw 仍为 22（借 nuwa digest 新增一条 integrated 级别的 forage 消化产物）。Dual-path lint 15/15 green。

## [2026-04-11] milestone | Forage digest #2 — gbrain → extracted note (Myco/gbrain 架构轴对照)

第二条 forage 消化：读 `forage/repos/gbrain/README.md`（594 行）+ `CLAUDE.md`（277 行）+ `src/core/` 结构扫描，产出 `n_20260411T183403_a984`（extracted, ~100 行 / 6:1 压缩率）。gbrain 是 Garry Tan 的 personal brain 产品：markdown repo 为 source of truth，Postgres+pgvector 做 retrieval，MCP 暴露给 agent，skillpack 告诉 agent 何时读写。生产规模 10k 文件 / 3k 人物 pages / 13 年日历。

四条 borrow-candidates：(1) contract-first operations file — gbrain `src/core/operations.ts` 定义 30 个 ops，CLI + MCP server 都 generate 自它。Myco 未来加 MCP surface 时应从 `_canon.yaml` 的 ops 节派生，避免漂移。(2) "repo=SoT, retrieval=separate layer" 原则 — 现阶段 Myco 规模不需要 retrieval，但承诺 *将来加的 retrieval 必须可以从 notes/ 完全重建*。(3) recipe-based integration installers — gbrain 每种 source type 一个 recipe md，未来 Myco 可以演化为 `myco forage add --recipe arxiv|hn-thread|gh-release`。(4) READ→WRITE loop 在每个 turn 强制写回 — Myco 已经部分有（digest_count bump, log milestone），不急。

一条显式 NOT portable：Postgres+pgvector 本身。Myco 的 "compression discipline 有牙齿" 和 gbrain 的 "feed everything, let search sort it out" 是相反的哲学压力，不要糊弄。如果将来 Myco 真需要 retrieval，应该是 SQLite FTS + duckdb 本地 embedding，不是托管 DB。

Forage item `f_20260411T180358_c7ab` → digested，digest_target 指向 a984。Dual-path lint 15/15 green。forage raw 数：4→3。

## [2026-04-11] milestone | Forage digest #3 — hermes-agent → extracted note (Hard Contract 压力测试 + 2nd-signal 汇聚)

第三条 forage 消化：读 `forage/repos/hermes-agent/README.md`（177 行）+ `AGENTS.md`（469 行）+ 顶层目录结构扫描（1563 文件），产出 `n_20260411T183722_c1b2`（extracted, ~130 行 / 4:1 压缩率，比 nuwa/gbrain 压缩低是因为本条兼任 Hard Contract 压力测试与跨项目汇聚综合）。hermes-agent 是 Nous Research 的生产级 agent runtime：同步对话循环、SQLite+FTS5 session store、6 平台 messaging gateway、40+ tools、6 terminal backends、3000+ 测试。

**Hard Contract 压力测试结论**：Myco 的 Hard Contract 是 substrate 层（跨 session 代谢卫生），hermes 的 policies 是 runtime 层（单 turn 内 prompt cache 不破裂）。**两个契约不竞争，是叠加关系**——一个 hermes-agent 跑在 Myco substrate 上是 coherent 的组合。Myco 不需要变成 runtime，hermes 不需要变成 substrate，这是清晰的分层。

**2nd-signal 汇聚**（两条独立项目各自收敛到同一模式）：(1) Central command registry 单源发射 — gbrain `src/core/operations.ts` + hermes `COMMAND_REGISTRY` 都做此事。Myco 加 MCP tools 时应从 `_canon.yaml` ops 节派生，优先级从 nuwa digest 的 "note-level flag" 上调到 "pre-factor-when-MCP-lands"。(2) SQLite+FTS5 是默认的本地检索形态 — gbrain 的 no-DB fallback + hermes session DB 都这样。Myco 将来加 retrieval 时走 SQLite FTS5 + duckdb 本地 embedding，重新确认。

三条 digest 汇聚证据（retroactive validation）：nuwa `references/research/*.md` + gbrain markdown repo SoT + hermes `~/.hermes/` — 三个独立成熟项目都各自选 markdown 文件做 durable state。Myco 的 `notes/*.md` 决策是 convergent choice。

Forage item `f_20260411T180416_3654` → digested，digest_target 指向 c1b2。Dual-path lint 15/15 green。forage raw 数：3→2（hermes + gbrain + nuwa 三条已消化；剩 mempalace + claude-managed-agents；karpathy 仍 quarantined）。

## [2026-04-11] milestone | Forage digest #4 — mempalace → extracted note (哲学交锋 + MCP 4th signal)

第四条 forage 消化：读 `forage/repos/mempalace/README.md`（732 行）+ `AGENTS.md`（78 行）+ 文件树扫描，产出 `n_20260411T184726_2ef7`（extracted, ~130 行 / 5:1 压缩率）。mempalace 是 AI 对话 local-first memory layer：ChromaDB 存 raw verbatim，spatial 检索 schema（wings/rooms/halls/tunnels），MCP server 19 tools，temporal validity KG，AAAK lossy 压缩 dialect，`wake-up` 加载 ~170 token 关键身份。LongMemEval 96.6% R@5 raw mode（独立复现，高于所有已发表系统）。

**哲学交锋**：mempalace 的核心赌注和 Myco 相反 —— "不让 AI 决定重要性，留住每一个字，用结构做 navigable map 而非 flat search"。AAAK lossy 压缩对比 raw mode 回归了 12.4 分（84.2% vs 96.6%），这是真实数据不是稻草人。**Myco 压缩哲学的四点防御**：(1) 目标指标不同 —— mempalace 测的是 retrieval recall，Myco 测的是 agent-behavior change across sessions，两个 benchmark 答的是不同问题；(2) Myco 也在 ingress 保留 raw —— `notes/*.md` 的 `status: raw` 是逐字保留的，压缩发生在 lifecycle staged 流转里不是破坏性摄入；(3) 机制差异 —— AAAK 是 lexical（regex dialect），Myco 是 semantic（synthesis with rationale），LongMemEval 的回归只证明 lexical 压缩伤 recall，对 semantic 压缩沉默；(4) mempalace 自己的 honest correction（48 小时社区发现并修正 4 条 overclaim）**反向验证了 Myco craft protocol 的 adversarial peer review 纪律**。

三条 borrow-candidates：(1) spatial retrieval schema（wings/rooms/halls）作为 retrieval metadata — 低优先级，归档为 "将来加 retrieval 时 notes frontmatter 加 hall/room 字段"；(2) temporal-validity KG with `as_of` queries — 有趣但需要 graph 层，Gear 4 规模考虑；(3) L0/L1/L2/L3 wake-up 分层 — Myco hot zone 已经是 L0+L1，可以作为文档 retrofit 而非代码。

显式 NOT portable：AAAK 本身、ChromaDB 做 SoT、"wings=projects-or-people" 多项目 scope 模型（会重新引入 friction note 381c 刚刚消除的 scope confusion）。

**MCP 4th signal**：nuwa + gbrain + hermes + mempalace 四条独立项目都把 MCP 当 agent-facing surface。**MCP tools surface 从 future-consideration 上调为 active Wave 10/11 candidate**。

Forage item `f_20260411T180425_2146` → digested，digest_target 指向 2ef7。Dual-path lint 15/15 green。

## [2026-04-11] milestone | Forage digest #5 — Claude Managed Agents → extracted note (市场定位 + 产品边界)

第五条 forage 消化：读 `forage/articles/claude_managed_agents.md`（47 行 WebFetch 摘要级抽取，payload gitignored per payload-off-by-default），产出 `n_20260411T184826_4256`（extracted, ~75 行 / negative compression —— 源已是摘要，分析层是 value-add）。Anthropic 2026-04-08 发布的 Claude Managed Agents：托管 agent runtime 的 composable APIs，主打 sandbox + session persistence + multi-agent delegation + governance + observability；launch customers 包括 Notion / Rakuten / Asana / Vibecode / Sentry；结构化文件生成任务 +10 分性能 claim。

**定位分析**：Managed Agents 和 Myco 是 **不同产品类别**，不应混淆。Managed Agents 是面向企业工程组织的 hosted runtime；Myco 是面向个人或小团队的 substrate framework。重叠面低但非零：两者都关心 "agent 状态跨 session 持久化"，可以 literally stack（Managed-Agents-hosted agent 写入 Myco substrate via MCP）。**Myco 不应定位为 Managed Agents 的替代方案**——它们玩不同的游戏。

三条定位点：(1) Notion/Rakuten/Asana 的 named deployment 是硬信号 —— "agent-as-service" framing 已从 pilot 进入 production，Myco 应承认这个空间被 Managed Agents 占据，自己走 adjacent niche（durable + legible + individually-owned substrate）；(2) Managed Agents 的 governance framework 是 runtime-trust，Myco craft protocol 是 cross-time-trust —— 不同信任问题，可以作为 Myco 定位文档的 framing："Managed Agents 答'我现在能信任这个 agent 吗'，Myco 答'我跨时间能信任这个 substrate 吗'"；(3) +10 分性能 framing 是公开 claim 的负责任模板（"up to X-point improvement on task Y per internal testing"），Myco 将来如果有实证数字可以借这个形态。

显式 NOT portable：hosted-runtime 架构本身、composable-APIs framing。

**License 处理**：source 是 WebFetch 摘要级抽取（summary of a summary），digest 零逐字引用，仅包含结构化功能列表 / 客户名单事实（新闻稿领域）/ Myco 自己的分析评论。原博客 © Anthropic，digest 文本安全 commit。

Forage item `f_20260411T180434_3035` → digested，digest_target 指向 4256。

## [2026-04-11] milestone | Forage digest #6 — Karpathy LLM Wiki → extracted note (派生层 + quarantine release + absorb extension 验证)

第六条也是 Wave 9 first-live forage batch 最后一条：读 `forage/articles/karpathy_llm_wiki.md`（82 行 full verbatim gist，license unknown，quarantined 状态，payload gitignored），产出 `n_20260411T185410_2e13`（extracted, ~130 行 / negative compression）。Karpathy 的 LLM Wiki gist 是 Myco 四层知识架构的直接智力祖先（在 `docs/current/llm_wiki_debate_2026-04-07.md` 明确致谢）。

**Quarantine release 决策（inline craft 5 轮，置信度 0.90）**：quarantine 旗标是针对 payload *再发布*，不是 payload *阅读*。payload 已被 `forage/.gitignore` payload-off-by-default 屏蔽。derivative-only digest 带 attribution + 零逐字引用 + 结构化 paraphrase 属于合理使用范围。forage manifest 保留 `license: unknown` 作为 provenance truth，状态 quarantined → digested。

**核心 `--why` 问题的答案**：Wave 9 的 `upstream absorb` 是 Karpathy 三个 op（Ingest/Query/Lint）的 **principled extension 而非 drift**。四步辩护：(1) Myco 有 6-op 面（eat/view/lint/digest/forage/absorb），其中 eat=Ingest 的 capture 部分、view=Query、lint=Lint、digest 是把 reading-from-filing 拆开（Karpathy 把它们 conflate）、forage 是 license-gated acquisition（Karpathy 假设 sources 已 curated dropped in）、absorb 是 cross-instance backflow（Karpathy 单 private wiki pattern 无此 primitive 因为他的 wiki 没有 kernel-and-instances 形态）；(2) Myco 已 converge 到 Karpathy 的 two-special-files（index.md + log.md with `## [YYYY-MM-DD]` grep 前缀）—— log.md 格式完全匹配；(3) Myco 四层架构（L1 CLAUDE.md / L1.5 wiki / L2 docs / L3 code）是 Karpathy 三层（raw/wiki/schema）的直接后代，只是把 raw tier 拆为 forage 外源 + L0 session archive；(4) Karpathy gist 中 `qmd` 的 MCP-server 提及是 MCP-as-agent-surface 的 5th signal —— nuwa + gbrain + hermes + mempalace + karpathy 五个独立来源指向同一结论。

显式 NOT portable：Obsidian 依赖、`qmd` 作为 dep（Myco 应走 convergent SQLite FTS5）、"batch-ingest without supervision" 模式（违反 Myco 的 friction-always-captured 与 digest-to-integrated 的 human-in-loop 要求）。

**Wave 9 first-live forage batch 完成**（6/6）：nuwa + gbrain + hermes + mempalace + claude-managed-agents + karpathy 全部 digested。`forage_backlog` 信号清零。跨项目 convergent pattern 3 条进入 Wave 10/11 预留：(a) MCP-tools surface（5 signal）、(b) central command registry → 多 emitter 单源派生（2 signal: gbrain + hermes）、(c) SQLite FTS5 default local retrieval（2 signal: gbrain fallback + hermes）。

Forage item `f_20260411T180445_f157` → digested（quarantine released），digest_target 指向 2e13。Dual-path lint 15/15 green 验证后 commit。

## [2026-04-11] friction | Scope leak via auto-loaded OPASCC/CLAUDE.md → eaten as n_20260411T193449_18f2

同一 turn self-correction：在一次 Myco-only 的 session recap 里提到了 "ASCC 并行推进" 作为下一步候选方向，用户立即挑战 "为什么你会提到这个？这是不应该提到的"。Root cause：两层叠加 — (1) Cowork mount 自动加载了 `/sessions/.../mnt/OPASCC/CLAUDE.md` 作为 claudeMd，标注 "IMPORTANT: OVERRIDE any default behavior"；(2) 我把前一段 summary 的 "Focus on Myco kernel, not ASCC" 误读为 "不要主动执行 ASCC 工作"，没有内化为 "不要把 ASCC 放进 next-step 候选集"。Hard Contract 第 3 条触发 → `myco eat` with tags `friction-phase2,on-self-correction,scope-leak,claudemd-pollution,wave10-candidate`。提议 Wave 10+ session scope binding primitive（kernel-level），让多 mount 时 agent 能明确 bind 到单一 active project 而不被 sibling mounts 污染 next-step 建议面。

## [2026-04-11] milestone | Forage digest #7+#8 — awesome-persona-distill-skills + pua (usability 批次启动)

用户发起 Wave 9 收尾 + Wave 10 序幕：新增两条 forage `f_20260411T194111_2b19`（xixu-me/awesome-persona-distill-skills, CC0-1.0）和 `f_20260411T194112_4d13`（tanweai/pua, MIT），WebFetch 摘要级 ingest（未 clone）。产出 `n_20260411T194951_9e91`（persona-distill, extracted）+ `n_20260411T194951_7b22`（pua, extracted）。

**Persona-distill 关键发现**：(1) "distill" 动词与 Myco Gear 4 "distill" 双 signal convergence → 应进 glossary；(2) skill-framework convergence 升到 3 直接 signal（nuwa + pua + agentskills.io），足以触发 Wave 10 "Myco is not a skill framework" 明确定位声明；(3) disclaimer-pattern for compression claims 作为未来 1-signal 储备。

**Pua 关键发现**：(1) 多平台 README 适配（9 AI platforms）作为 distribution pattern 的 1 strong signal，应进 `docs/adapters/` 预留（Wave 10）；(2) 多语言 README 2-signal convergence（pua 显式 + Myco 已 zh+en）→ 足以在 Wave 9 本批次添加 README_ja.md；(3) auto/manual trigger conditions 作为 MCP tool description 的显式规范 → 应嵌入 9 个 MCP tool docstring；(4) skill-runs-on-substrate 栈式兼容验证。显式 non-ports：PUA 心理压迫 rhetoric（与 Myco compression honesty 反向）、企业方法论 bundling、无 peer-review 的 benchmark 数字。

L14 修复：两条新 forage 初始 license=unknown 违反 "unknown coexist with quarantined"；craft decision 基于 WebFetch License badge 直接 resolve 为 CC0-1.0 / MIT，`license_checked_at` 2026-04-11T19:49:51，补齐 `local_path` 指向 `forage/articles/` 下的 path stub 文件。Dual-path lint 15/15 green 恢复。

## [2026-04-11] milestone | Usability + Positioning craft (4 rounds, 0.91) → README 批次重写 → D1-D8 全部落地

传统手艺 `docs/primordia/usability_positioning_craft_2026-04-11.md`（4 轮，target 0.90 / current 0.91，decision_class `kernel_contract`）。Round 1 列攻击 A-E：词汇税（生物学动词）、抽象 hero（substrate/kernel/contract 堆叠）、"与所有东西都 complementary" 非定位、pip install 从 README 复制不能跑、未声明 target user。Round 2 验证引擎 genuinely 独特（web 搜索 Mem0 49% LongMemEval + Letta 74% LoCoMo 确认无 2026 竞品做 project-level knowledge substrate with enforced cross-session contracts + self-evolving rules 这个 shape），列攻击 F-I（Anthropic CMA timing moat、pre-commit 替代路径、abstract demo、kernel/instance 混淆）。Round 3 列可发货修复 + 攻击 J-M，决定不重命名 MCP 工具（契约变更）改为 docstring 优化。Round 4 攻击 N-P 确认自主权边界。

**Decisions D1-D8 落地**：D1 hero 两句（benefit-first + category secondary）、D2 target-user blockquote 置于 fold 上方、D3 section 顺序（hero → target → 30s demo → quick start → what it does → glossary → how it works → comparison → open problems → story）、D4 术语表 8 行（eat/digest/view/lint/forage/absorb/distill/hunger）、D5 MCP docstring 前置普通英语动词 + auto-invoke 规范、D6 多语言三叉（en canonical / zh / ja with banner）、D7 MYCO.md hero 两句化、D8 explicit "not memory layer / not runtime / not skill framework" 声明。

**本批次修改**：`README.md` 全量重写（~285 行）、`README_zh.md` 全量重写（~280 行）、`README_ja.md` 新建（~280 行，带翻译 banner）、`MYCO.md` hero 段替换（primary + secondary + tagline + target user + disambiguation 五段式）、`src/myco/mcp_server.py` 中 5 个 MCP tool docstring（lint/status/search/log/reflect）前置 "Auto-invoke when..." 规范（eat/digest/view/hunger 原已具备 WHEN TO CALL section，保留）。修改全部为非契约变更（docstring 软修改 / 对外文案），`_canon.yaml` 与 kernel src 未动。

---

## 2026-04-11 · Milestone · README 三语版 vision-led 全量重写（Wave 10 · readme-v3）

**触发**：用户对 usability-batch README（2026-04-11 上午提交 `60aa2de`）提出定位批评：
> "抽象阶梯并不够高，不要从我们具体实现出发去讲故事，而是应该从我们的愿景出发去讲故事。我们的愿景在之前的 debate 记录中有非常多的信息。取其精华去其糟粕，压缩展示最核心的内容，展示我们的愿景，展示我们最好的一面。"

**诊断**：usability-batch README 技术正确但战略错位 —— hero 从"lints your knowledge"出发，抽象阶梯停在 feature 层；没有把 Myco 作为 Autonomous Cognitive Substrate 的身份叙事放在 fold 之上；CPU/OS metaphor、非参数进化、七步代谢（含 excrete 淘汰步）、四层自我模型、mutation/selection、agent-as-subject 反转等 18 个来自 `docs/primordia/vision_recovery_craft_2026-04-10.md` 的愿景元素被压缩丢失或埋到底部。

**愿景吸收（eat）**：`myco eat` 生成 `notes/n_20260411T202539_92d1.md`，source=chat，tags=`vision-absorption,readme-v3-input,wave10-candidate`，综合 `docs/vision.md` + `docs/primordia/vision_recovery_craft_2026-04-10.md` + `docs/primordia/myco_vision_2026-04-08.md` 三份愿景源，按 4 个主题簇组织 18 个元素：Identity / Metabolism / Cognition / Collaboration。

**本批次修改**（3 文件，~310 行/版）：

- `README.md`（英）全量重写。新骨架：Hero（substrate identity + CPU/OS metaphor）→ The Living Substrate（热力学 life/death 框架）→ Five Capabilities（seven-step metabolism with Excrete / meta-evolution 四齿轮+metabolic inlet / four-layer self-model A/B/C/D / cross-session continuity / agent-adaptive universality）→ A Picture of the Whole（kernel/instance ASCII 图）→ How You Work With Myco（mutation/selection + transparency→anti-cancer 因果链 + agent-as-subject 反转）→ Three Immutable Laws 表 → Compression Is Cognition → Standing on Fifty Years（Karpathy + Polanyi + Argyris + Toyota PDCA + Voyager）→ Already Running Unconsciously（ASCC anchor）→ Open Problems 6 条 → Today and Tomorrow（v0.x/v1.0/v∞ roadmap 表）→ Try It Today（pip/CLI 压到底部子节）→ Contributing → The Mycelium（故事）→ closing tagline。

- `README_zh.md`（中）镜像重写，使用 04-08 canonical 中文词汇：认知基质 / 自主认知基质 / 知识代谢 / 七步管道 / 非参数 / 永恒进化 / 停滞即死 / 变异 / 选择压力 / 癌化 / 内核 / 实例 / 压缩即认知 / 可读的透明。

- `README_ja.md`（日）镜像重写，使用日文 canonical 术语：自律認知基質 / 代謝 / 七段 / 排出 / 淘汰 / カーネル / インスタンス / 選択圧 / 永続 / 停滞 / 癌化 / 圧縮 / ポラニー / アージリス / 自己升級。

**L9 vision-anchor 验证**：3 个文件全部通过 12 组 anchor 检查（substrate-identity / cpu-metaphor / non-parametric / metabolism / seven-step-pipeline / compression-doctrine / four-layer-self-model / mutation-selection / perpetual-evolution / transparency-anticancer / kernel-instance / theoretical-lineage）。

**Dual-path lint**：`myco lint --project-dir .` 15/15 绿 · `python scripts/lint_knowledge.py` 15/15 绿。

**契约影响**：零。本次修改全部为对外叙事层（README 三语版）；`_canon.yaml` / `agent_protocol.md` / `lint.py` / MCP 工具契约未动。usability-batch 的 target-user blockquote、30-second demo、术语表被压到文档底部"Try It Today"子节，信息未删，展示层级上移到愿景。

**设计原则自承**：这一次 README v3 的差别不在内容新增，而在**从哪里开始**。v2 从"what it does"开始（implementation），v3 从"what it is"开始（vision）。抽象阶梯的顶点是 Autonomous Cognitive Substrate 身份声明，具体 CLI 是地板而不是天花板。

---

## 2026-04-11 · Wave 11 · type: milestone

**Wave 11 craft reflex（v0.10.0）** — 把 craft discovery surface 从"被动文档"升级为"主动 reflex"。

**motivating failure**：Wave 10 的 vision-led README 三语重写是一个教科书级 Trigger #4（external stakeholder-visible claim），但全程没走 craft——因为发现面是纯文档，agent 必须在决策当下主动想起 craft 才能触发。craft 辍触的根源不是 craft 不存在，而是 discovery surface 被动。

**meta-craft**：`docs/primordia/craft_reflex_craft_2026-04-11.md`（3 轮，终置信度 0.91，decision_class: kernel_contract，floor 0.90）。关键修正：A7（trigger surface 必须切成 `kernel_contract` + `public_claim` 两类，只用前者抓不到 README 事件），C1/C2（检测基准从 log.md 正则 pivot 到 `path.stat().st_mtime`，同时解决 fresh-clone grace、lookback_days 语义、正则脆弱性）。

**落地（9 decisions · 13 landing items）**：
1. `_canon.yaml::system.craft_protocol.reflex` 新块（enabled/lookback_days=3/severity=LOW/trigger_surfaces.{kernel_contract,public_claim}/evidence_pattern）
2. `src/myco/lint.py::lint_craft_reflex`（L15），docstring "15-Dimension → 16-Dimension"，注册到 `main()::checks`
3. `src/myco/notes.py::detect_craft_reflex_missing` + `craft_reflex_missing` hunger signal
4. `docs/craft_protocol.md §3.1 Discovery surface`（5 发现面 + mtime-primary 说明）+ §8 L15 反向日落（dead reflex / Goodhart overrun / better replacement）
5. `src/myco/templates/_canon.yaml` 同步 reflex 块 + `synced_contract_version: v0.10.0`
6. `src/myco/templates/MYCO.md` 热区 W3 行追加 Reflex 提示
7. `docs/contract_changelog.md` v0.10.0 条目
8. `myco eat` 为 raw note `n_20260411T212953_be70`，tags 含 `craft-conclusion,decision-class-kernel_contract,friction-phase2,wave11`
9. `system.contract_version`：v0.9.0 → v0.10.0（Wave 8 re-baseline 后仍走 v0.x，不是 v1.3.1）

**Dual-path lint**：待运行 `myco lint --project-dir .` 与 `python scripts/lint_knowledge.py` 双路 16/16 绿。

**契约影响**：`system.contract_version: v0.9.0 → v0.10.0`（minor bump）。向后兼容：`reflex.enabled: false` 即完全关闭；旧 instance 不更新 synced_contract_version 就看不到 L15。下游 ASCC 此前未写 L15 支持路径，无需改代码。

**设计原则自承**：reflex 是**信号不是门闸**。craft 仍是人工仪式，reflex 只是拒绝"静默绕过"。这一条是 Round 1 A7 强制的关键防御——若把 L15 变成 HIGH/阻塞，agent 会把craft 降格为"过检仪式"，反而破坏 W3 初衷。

**craft_reference**: docs/primordia/craft_reflex_craft_2026-04-11.md

---

## 2026-04-11 · Wave 12 · type: milestone

**Wave 12 craft autonomy（v0.11.0）overturns Wave 8 A7** — 把 craft 从"advisory ritual"升级为"agent-autonomous reflex arc"。这是 Myco 身份契约级别的更正，不是功能新增。

**Motivating contradiction**: Wave 11 刚落地后，我自己在 §3.1 里写了"Reflex is a signal, not a gate. Craft remains a human ritual"——用户立刻指出：如果 craft 需要人 invoke，Myco 就不是 Autonomous Cognitive Substrate，违背核心身份。自承错误已 `myco eat` 为 friction note `n_20260411T215313_0526`（tags: `friction-phase2,on-self-correction,craft-protocol,craft-autonomy,wave12`）。

**meta-meta-craft**：`docs/primordia/craft_autonomy_craft_2026-04-11.md`（3 轮，终置信度 0.92，decision_class: kernel_contract，floor 0.90）。A1/A6/A7 accepted 分别导致 §4.5 协作模型 / agent protocol binding / trivial_exempt 机制；B3 withdrawn（schema 无法表达 single-source cap，降为 prose convention）。**本 craft 正式 overturn Wave 8 `craft_formalization_craft` Round 1 A7**：A7 当时（无 L15）正确，现在（有 L15）错误；automation target 从"CLI 人类调用"变为"trigger 触碰→craft 在 agent loop 内物化"。

**落地（9 decisions，9 files changed）**：
1. `_canon.yaml::system.craft_protocol.reflex.severity`: LOW → HIGH；新增 `trivial_exempt_lines: 20`
2. `_canon.yaml::system.contract_version`: v0.10.0 → v0.11.0
3. `src/myco/lint.py::lint_craft_reflex`：读 severity 从 canon、实现 `_is_trivial_edit` 通过 `git diff --numstat` 判定、fail-closed 降级、issue 文案强调"write NOW not later"
4. `src/myco/notes.py::detect_craft_reflex_missing` 文案：IMMUTABLE REFLEX + --no-verify is W3 violation
5. `docs/craft_protocol.md` 大改：
   - §1 删除 "Myco's formal ritual / human ritual" framing → "agent-autonomous selection-pressure mechanism" + Wave 8 A7 overturn block
   - §3.1 从 "Discovery surface" 改名 "Reflex arc"；删除 "signal not gate"；明确 4 步反射弧 + severity=HIGH 理由
   - §4 新增 "Single-source convention"（single-agent craft: current_confidence ≤ target_confidence，prose-only）
   - §4.5 新增 "Collaboration model"（human 在 review loop 而非 invocation loop；human-authored/collaborative craft 可 supersede agent-only）
   - §7 追加 3 条 Known limitations（honor-system ceiling / trivial_exempt 未校准 / git 依赖 fail-closed）
6. `src/myco/templates/_canon.yaml`：同步 severity HIGH + trivial_exempt_lines + `synced_contract_version: v0.11.0`
7. `src/myco/templates/MYCO.md`：热区 W3 clause 完全重写强调不可绕过反射弧
8. `docs/contract_changelog.md`：v0.11.0 条目含 CI 迁移指南
9. `myco eat` 为 raw note `n_20260411T220153_df2b`（tags 含 `craft-autonomy, overturns-wave8-A7, wave12`）

**Dual-path lint**：待运行 `myco lint --project-dir .` 与 `python scripts/lint_knowledge.py` 16/16 绿（L15 被本次 meta-meta-craft 自身满足）。

**契约影响**：`system.contract_version: v0.10.0 → v0.11.0`（minor）。**下游潜在 breaking**：严格处理 lint exit code 的 CI pipeline 会看到 L15 触发 exit 1 而非 0——changelog v0.11.0 条目含 CI 迁移指南（选项 A: 让 agent loop 内闭环；选项 B: CI 把 L15 映射 warning；不推荐：关 reflex）。

**Immutable reflex arc**: touch trigger surface → L15 fire HIGH → agent writes craft in-session → lint green → commit. Human never in the invocation loop; human always in review loop. This is what "autonomous cognitive substrate" means in practice: the selection machinery is self-firing, or it is not a substrate.

**craft_reference**: docs/primordia/craft_autonomy_craft_2026-04-11.md

## [2026-04-11] milestone | Wave 13 — Boot Reflex Arc (contract v0.11.0 → v0.12.0)

**主题**：把 3 条 prose 级 reflex（contract_drift / raw_backlog / boot hunger wiring）升级为 Wave 12 同形的 in-session reflex arc，关闭 advisory tier 漏洞。

**触发**：用户在 Wave 12 后提出"回到修复漏洞的主线"。Audit 发现 W1（auto-sedimentation）和 Upstream Protocol §8.4（contract version lock）虽然是 named principle / contract-level invariant，但代码里**一行 enforcement 都没有**，其失效率与 pre-Wave-11 craft 相同。Realtime dogfood 直接证据：`myco hunger` 报告 Myco kernel 仓库**本身**有 27 pure-raw notes——基质在自己身上代谢失败。

**Craft**：`docs/primordia/boot_reflex_arc_craft_2026-04-11.md`（3 轮，kernel_contract，final 0.91）。A7 split 把 `upstream_scan_last_run` 写路径重新 scope 到 Batch 4，保持 Batch 1 聚焦。

**实现**：
1. `detect_contract_drift(root)` — 比对 local `synced_contract_version` 与 kernel `contract_version`（优先同文件，fallback shipped template ledger），不一致发 `[REFLEX HIGH] contract_drift`。
2. `compute_hunger_report` 前置调用 drift + refine `raw_backlog` 为 `pure_raw_count`（digest_count==0 AND source 不在 `raw_exempt_sources`），信号升级 `[REFLEX HIGH]` + 最少 digest 数量指引 + W1 违规警告。
3. `craft_reflex_missing` 同步添加 `[REFLEX HIGH]` 前缀。
4. `myco_status` 新增 `include_hunger: bool = True` 默认调用 hunger，reflex/advisory 分桶返回；出现 reflex 时 `hint` 被替换为强制警告。Docstring 明确 `include_hunger=False` 在 raw_backlog 非空时 = W1 违规。
5. `_canon.yaml::system.boot_reflex` 新块（severity HIGH + threshold 10 + prefix + raw_exempt_sources: [bootstrap]）。`contract_version: v0.11.0 → v0.12.0`，新增 `synced_contract_version: "v0.12.0"` kernel self-reference。
6. Templates 同步（`src/myco/templates/_canon.yaml` + `src/myco/templates/MYCO.md` hot zone）。
7. `docs/agent_protocol.md §3` 改写为 2 步 arc，§8.4 新增"代码侧强制"子节。
8. `docs/contract_changelog.md` v0.12.0 条目含 changes / migration / known limitations。

**Dogfood cleanup**：Wave 13 landing 同会话消化 kernel 仓库 27 raw notes 到 integrated（全部是 Phase 1 MVP / Wave 9/10/11/12 遗留的 extracted-but-not-status-updated 记录——知识已沉淀，状态字段未跟上）。Post-landing `myco hunger` = healthy, raw=0, total=47, integrated=36。

**契约影响**：`system.contract_version: v0.11.0 → v0.12.0`（minor · W1 + §8.4 enforcement）。向后兼容：老 instance 升级后需运行一次 `myco digest` 把任何 raw backlog 压到阈值下，否则 `myco hunger` 会持续报 reflex 信号直到处理完成。

**Wave 12 asymmetry closed**: named-principle reflexes (W1/W3/§8.4) 现在统一 HIGH；advisory signals (stale_raw/no_deep_digest/etc) 保持信息级——严重度反映的是"underlying rule 是不是 named principle"，不是 flat inflation。

**craft_reference**: docs/primordia/boot_reflex_arc_craft_2026-04-11.md

## [2026-04-11] meta | Gear 2 反思：Wave 13+14 作为同一反射弧的双端

Wave 13 和 Wave 14 结构完全同构——都是把 `agent_protocol.md` 里的一段
prose 步骤（§3 boot / §4 end）改造成 hunger-driven 反射弧，并通过一个新的
canon 块（boot_reflex / session_end_reflex）、一个新的 notes.py 检测器
（detect_contract_drift + raw_backlog 改造 / detect_session_end_drift）、
和一条 contract minor bump 完成。唯一的**刻意**差异是 severity：Wave 13
是 HIGH（W1 data-loss 语义），Wave 14 是 LOW（W5 drive 语义）。

这条非对称不是妥协，而是检验了自己之前的一个怀疑：如果把所有反射弧都升
到 HIGH，agent 会学会忽视 advisory 列表整体。Wave 14 主动保留了一条 LOW
信号的发射通道，让"软信号"这个类别仍然有实际载体——否则整个反射体系会
退化为二值（触发 = 停，不触发 = 静默），失去 gradient。

**Gear 2 发现**：系统设计上真正的弱点不是"缺失反射弧"，而是"反射弧的
严重度语义"——什么时候升到 HIGH，什么时候留在 LOW。目前靠人工判断
（parent principle 是 W1 级还是 W5 级），没有形式化规则。这是下一轮 Gear
2 反思的候选对象：能否把 severity 从手工决策抬升到 lint 可验证的分类？

**Gear 4 候选**：把"prose 规则 → canon 块 + 检测器 + severity 分类 +
contract bump"这四件套提炼为通用 substrate discipline 模式——任何基质
把软规则升级为硬反射时都可以套用。候选 → g4-candidate。

## [2026-04-11] milestone | Wave 14 — Session End Reflex Arc (contract v0.12.0 → v0.13.0)

**范围**：W5 evolution-discipline 的两个 drift 漏洞——Gear 2 反思遗忘、
Gear 4 sweep 沉底——首次有 code-level 反射，通过 `session_end_drift`
advisory 信号在每次 hunger 报告里 surface。

**动机（dogfood 证据）**：
- log.md 最后一条 meta 反思：2026-04-10；之后累计 18 条非 meta 条目
  （milestone / friction / system / craft），一整天的 kernel 推进零 Gear 2
  轨迹
- `grep -c g4-candidate log.md` = 18，`grep -c g4-pass log.md` = 0
- 两者都没有 lint / hunger 信号提醒

**实现要点**：
1. 新 canon 块 `system.session_end_reflex`（gear2/gear4 各自独立 enabled
   flag，阈值可 instance-override，log scan 有 5 MB cap）
2. `detect_session_end_drift` 在 `notes.py`：宽容 regex 解析 log.md
   header，Gear 2 数 "最后 meta 之后的非 meta 条目数"，Gear 4 数 "age ≥
   5 天且无 g4-pass / g4-landed / 磁盘 craft 引用的 g4-candidate 行数"
3. `compute_hunger_report` 在 craft_reflex 后、forage 前调用
4. `agent_protocol.md §4` 由 5 步 prose → 2 步反射弧（hunger →
   处理 session_end_drift）
5. 契约版本 v0.12.0 → v0.13.0（kernel 自引用 synced_contract_version
   同步）

**刻意非对称**：severity = LOW（非 HIGH）。Wave 13 反射是 W1 level 数据
丢失约束；Wave 14 是 W5 level 习惯退化 drive。LOW 信号进 advisory 列表不
阻塞任务，但在每次 boot 可见——这是 craft §B4 的主论证。

**Dogfood 验证**：
- 实现完成后 `detect_session_end_drift('.')` 直接返回 gear2 fire（18 >15
  threshold），gear4 clean（oldest candidate 2026-04-09，age 2 天 < 5 天
  threshold）——即 kernel 当前只有 Gear 2 drift，没有 Gear 4 drift
- 本 meta 条目写入 → gear2 计数器归零 → hunger 重跑应清除该信号
- Gear 4 sweep 不做：所有 18 个候选 <5 天，按规则无需动作。后续若老化
  再处理

**向下游迁移影响**：下次 boot 调 myco_status 会触发 Wave 13 contract_drift
HIGH 反射（synced v0.12.0 vs kernel v0.13.0）。读本条目 + contract_changelog
v0.13.0 entry 即可对齐。无代码修改必要。

**craft_reference**: docs/primordia/session_end_reflex_arc_craft_2026-04-11.md
（3 轮，0.91，decision_class: kernel_contract）

## [2026-04-11] milestone | Wave 15 — L13 Body Schema (contract v0.14.0)

L13 现在度量 craft body 内容，不再只信 frontmatter 声明。Partial closure of
`docs/craft_protocol.md §7 #3` ("Body structure is not linted")。

- **body_chars floor** (HIGH): `body_chars < rounds × 200` → hollow craft
- **body_rounds match** (HIGH): `## Round N` 锚点数 ≠ declared rounds → 声明说谎
- **body_rounds == 0 nudge** (MEDIUM): 没 `Round N` 锚点 → 风格建议（不强制）
- **per-round slice floor** (MEDIUM): 单轮 <150 chars → 薄轮

多语言 round markers：`Round N` / `R(N)` / `第N轮` / `ラウンド N`。
非空格字符计数（CJK-friendly）。

Dogfood：11 个现有 craft 中 10 个已达标；`pre_release_rebaseline` 收到
1 条 MEDIUM 风格 nudge（原作者用 `## Attacks → ## Defenses` 替代结构，
刻意不豁免）。Hollow-craft smoke test：52 chars body + 3 declared rounds
→ 正确触发 `body_chars=52 < 600` HIGH。Self-test：本 craft 在新 L13 下
0 findings。

craft 引用：`docs/primordia/l13_body_schema_craft_2026-04-11.md`
（3 轮，终置信度 0.90，decision_class kernel_contract）
conclusion note：`notes/n_20260411T225402_66a0.md` (integrated)
lint：16/16 green（0 HIGH, 1 MEDIUM pre-existing nudge）

## [2026-04-11] milestone | Wave 16 — Upstream Scan Timestamp Write Path (contract v0.15.0)

Closes Wave 13 Boot Reflex Arc craft §A7 split. `system.upstream_scan_last_run`
was a declared reflex with no nervous system since contract v0.6.0 — field
existed as `null` in every canon, no code path wrote it. Batch 4 lands the
writer.

- `src/myco/upstream_cmd.py`: new `_update_scan_timestamp(root)` helper
  + `_SCAN_TS_RE` strict single-line regex
- Called at end of successful `_cmd_scan` after `scan_kernel_inbox`
- **Surgical regex edit**, not `yaml.dump()` round-trip — preserves all
  comments in `_canon.yaml` (Wave 8 rebaseline banner + doctrine notes
  + severity justifications would be destroyed by PyYAML default dumper)
- Format: `"YYYY-MM-DDTHH:MM:SSZ"` UTC quoted string
- Freshness semantics: records scan *attempt*, not scan *result* —
  zero-pending scans still update (future `upstream_scan_stale` reflex
  wants "has the agent checked recently?", not "has the agent found
  something recently?")
- Failure modes: scan raises → don't write | IO fail → stderr WARN,
  scan still succeeds | regex 0 or >1 matches → WARN, bail gracefully

Self-test: two back-to-back `myco upstream scan` calls updated the
field from `2026-04-11T14:57:40Z` → `2026-04-11T14:58:50Z`. All
surrounding comments preserved byte-for-byte. `myco lint --project-dir .`
→ 16/16 green (0 HIGH, 1 pre-existing MEDIUM nudge on
`pre_release_rebaseline`).

craft: `docs/primordia/upstream_scan_timestamp_craft_2026-04-11.md`
（3 轮，终置信度 0.91，decision_class kernel_contract，target 0.90）
conclusion note: `notes/n_20260411T225901_4d39.md` (integrated)

**Batch 4 complete. All 4 batches of the hole-fix campaign landed**:
- Batch 1 (Wave 13, v0.12.0) — Boot Reflex Arc ✅
- Batch 2 (Wave 14, v0.13.0) — Session End Reflex Arc ✅
- Batch 3 (Wave 15, v0.14.0) — L13 Body Schema ✅
- Batch 4 (Wave 16, v0.15.0) — Upstream Scan Timestamp ✅

## [2026-04-11] milestone | Wave 17 contract v0.16.0 — Boot Brief Injector + upstream_scan_stale Reader
- Landed: render_entry_point_signals_block (regex patch MYCO-BOOT-SIGNALS:BEGIN/END) + write_boot_brief (.myco_state/boot_brief.md) + detect_upstream_scan_stale (hunger signal, stale_days=7, pending bundle count)
- L12 extended: .myco_state flat whitelist (.md/.json)
- canon bumped v0.15.0 → v0.16.0; new blocks system.boot_brief + system.upstream_scan
- Sentinel blocks added: kernel MYCO.md + template MYCO.md + ASCC CLAUDE.md
- Dogfood: kernel hunger patched MYCO.md 2026-04-11T15:21:05Z; ASCC hunger patched CLAUDE.md 2026-04-11T15:22:01Z; synthetic stale (8d + dummy bundle) fired exact [REFLEX HIGH]
- Craft: docs/primordia/boot_brief_injector_craft_2026-04-11.md (confidence 0.92)
- Holes closed: H-1 full, H-7 full, H-8 partial (reader side only), H-9 full
- Remaining: H-2/H-6 (architectural limits, document); H-3 (Wave 19); H-4/H-5 (Wave 18); H-8 writer (future)
- Lint: 16/16 green

## [2026-04-11] milestone | Wave 18 contract v0.17.0 — L15 Surface Expansion + Git Hook Installer
- Widened L15 trigger_surfaces.kernel_contract: +docs/contract_changelog.md +src/myco/notes.py +src/myco/notes_cmd.py (both kernel + template canon)
- New: scripts/install_git_hooks.sh — opt-in, idempotent, fail-open pre-commit hook installer
- Hook blocks commits on CRITICAL/HIGH only; MEDIUM/LOW pass through with stderr warning
- Hook fail-opens when `myco` not on PATH (missing linter ≤ no hook)
- canon bumped v0.16.0 → v0.17.0
- Dogfood: lint 16/16 green (self-hosting — this craft mtime covers freshly-touched new surfaces); installer idempotent; hook direct-run exit=0 with MEDIUM surfaced
- Craft: docs/primordia/l15_surface_and_git_hooks_craft_2026-04-11.md (confidence 0.91)
- Holes closed: H-4 full, H-5 full
- Remaining: H-3 (Wave 19); H-2/H-6 (architectural limits, document); H-8 writer side (future)

## [2026-04-11] milestone | Wave 19 contract v0.18.0 — myco correct Ergonomic Shortcut
- New CLI verb: `myco correct` — thin wrapper over `myco eat` that force-merges mandatory tag pair `friction-phase2, on-self-correction`
- Hard Contract rule #3 special clause now has ergonomic enforcement at kernel level
- Canon: system.self_correction.mandatory_tags (kernel + template)
- docs/agent_protocol.md §5.1(c) gets one-sentence pointer to new shortcut
- canon bumped v0.17.0 → v0.18.0
- Dogfood: two self-test invocations confirm correct tag emission (mandatory-only and merged-with-user-tags); both excreted clean
- Craft: docs/primordia/myco_correct_shortcut_craft_2026-04-11.md (confidence 0.91)
- Holes closed: H-3 partial (ergonomic barrier → zero; full detection requires Phase 2 NLP)
- All 9 panorama holes resolved or categorized: H-1/H-4/H-5/H-7/H-9 full; H-3/H-8 partial; H-2/H-6 pending limitations doc
- Lint: 16/16 green

## [2026-04-11] document | open_problems §7/§8 — H-2 + H-6 registered as accepted architectural limits
- H-2 (agent-initiated sensing) and H-6 (dual append paths MCP vs shell) registered in docs/open_problems.md
- Both explicitly categorized as "想清楚了但做不了" — CLI hosting paradigm physical limits, not solvable inside kernel scope
- Exit conditions documented for each (SDK hooks / MCP ubiquity / future model capability)
- No contract bump — documentation registration only
- All 9 panorama holes now resolved: H-1/H-4/H-5/H-7/H-9 full fix; H-3/H-8 partial (kernel scope exhausted); H-2/H-6 open-problem registered
## [2026-04-12] milestone | **Wave 20 landed (v0.19.0)** — silent-fail elimination: grandfather ceiling + strict project-dir. Closes NH-1 HIGH + NH-2 CRITICAL from panorama #2. (1) `detect_contract_drift` grandfather-ceiling check runs BEFORE the `boot_reflex.enabled` gate — any instance with >5 minor versions of drift fires `[REFLEX HIGH] grandfather_expired` regardless of gate state. Major mismatch unconditional HIGH. Ceiling canon-configurable via `system.boot_reflex.grandfather_ceiling_minor_versions`. (2) Strict `_project_root` raises `MycoProjectNotFound`; `@_guard_project` decorator wraps run_eat/run_correct/run_digest/run_view/run_hunger → exit 2 with clear stderr. `MYCO_ALLOW_NO_PROJECT=1` escape hatch. (3) `importlib.resources` fallback locates the installed package template for downstream instances (kernel repo layout not assumed). (4) Self-tests all green: kernel healthy at v0.19.0=v0.19.0, tamper-to-v0.10.0 fires grandfather_expired (9 minor), disabled-gate still fires, /tmp → exit 2, env-var override passes, ASCC migration fires on tamper / healthy after restore. (5) ASCC migration: `synced_contract_version` v0.8.0 → v0.19.0, minimal boot_reflex block added, log.md decision entry. Doctrine: **a sensory system that returns "healthy" when its sensors are disconnected is worse than a crash.** Note: n_20260412T003444_c2dd (integrated). Craft: docs/primordia/silent_fail_elimination_craft_2026-04-11.md (3 rounds, kernel_contract, 0.92 confidence).
## [2026-04-12] milestone | **Wave 21 landed (v0.20.0)** — observability integrity: L16 brief freshness + `myco view` agent surface. Closes NH-3 MEDIUM + NH-7 MEDIUM from panorama #2. (1) `lint_boot_brief_freshness` (L16, MEDIUM) compares `.myco_state/boot_brief.md` mtime against `max(_canon.yaml, docs/contract_changelog.md)` mtime; fires "missing" or "stale" with concrete timestamps. Respects `system.boot_brief.enabled`. Lint count 15 → 16 dimensions. (2) `myco view` gained `--next-raw` (oldest raw body + digest hint) and `--tag T` (frontmatter tag filter, `last_touched` desc, respects `--status`/`--limit`/`--json`). Positional `<id>` legacy mode unchanged. (3) Bugfix during self-test: `_sort_key` coerces `last_touched` to `str` because YAML deserializes ISO-8601 as datetime → `TypeError` on mixed tag cohorts. (4) Canon bumped v0.19.0 → v0.20.0 in kernel + template. Self-tests: kernel L16 PASS → touch canon → L16 MEDIUM fires → hunger → L16 PASS; `--next-raw` shows panorama-#2 note; `--tag friction-phase2 --limit 5` returns 5-row sorted table. Note: n_20260412T004141_71b2 (integrated). Craft: docs/primordia/observability_integrity_craft_2026-04-12.md (3 rounds, kernel_contract, 0.90). Doctrine: every kernel surface must earn its keep — a verb that shows what `cat` shows is dead weight.
## [2026-04-12] milestone | **Wave 22 landed (v0.21.0)** — primordia compression workflow + `docs/primordia/archive/` + W13 principle. Closes NH-4 MEDIUM from panorama #2. (1) New `docs/primordia/archive/` append-only directory for [COMPILED]/[SUPERSEDED] crafts, preserving Gear-4 access while removing them from `detect_structural_bloat`'s non-recursive `glob("*.md")` count. (2) 11 crafts physically moved: generalization_debate / llm_wiki_debate / tacit_knowledge_debate / nuwa_caveman_integration / retrospective_p4_midterm / system_state_assessment / vision_debate / myco_vision / gear4_trigger_debate / decoupling_positioning_debate / gear3_v090_milestone. Primordia top-level count 45 → 35 (below soft limit 40). (3) `docs/WORKFLOW.md` W13 "Primordia 压缩检查点" added after W12, principles header 十二原则 → 十三原则. W13: every wave at session end reads `myco hunger`; if `structural_bloat: primordia` fires, wave MUST either `git mv ≥N [COMPILED]` crafts to archive/ OR append `deferred: primordia-compression (<reason>)` to its log entry. (4) `docs/primordia/README.md` preamble + 11 rows rehomed with [ARCHIVED/COMPILED] markers. MYCO.md (2 rows) + vision_recovery_craft (2 refs) rehomed to archive/ paths. (5) Canon v0.20.0 → v0.21.0 in kernel + template. Self-tests: `myco hunger` BEFORE = structural_bloat:primordia 45>40 advisory, AFTER = healthy (signal gone). `myco lint` 16/17 green (only pre-existing L13 MEDIUM on pre_release_rebaseline_craft). Primary limitation documented: W13 is behavioral not lint-enforced — a wave that ignores it gets caught by the NEXT wave's hunger re-fire, not an in-wave block. Note: n_20260412T005208_bbb2 (integrated). Craft: docs/primordia/primordia_compression_craft_2026-04-12.md (kernel_contract, 3 rounds, 0.88). Doctrine: structural bloat is a gradual degradation; the response must be ritualized not advisory, otherwise the signal becomes noise.
## [2026-04-12] milestone | **Wave 23 landed (v0.22.0)** — pre-commit hook blocking-path dogfood (NH-8) + opt-in MYCO_PRECOMMIT_PYTEST gate (NH-9). (1) Dogfood test 1: `echo "# dogfood" > scratch.md && git add scratch.md && git commit -m "should be blocked"` → hook printed full lint output ending in `[CRITICAL] L11 | scratch.md | Forbidden top-level entry`, then `[myco] pre-commit blocked`, commit NOT created, `git log --oneline -1` still showed ce1606e (Wave 22) as tip. The Wave 18 hook's blocking path had never been exercised live before; now it has. (2) Opt-in pytest gate added to `scripts/install_git_hooks.sh` with `MYCO-PRECOMMIT-PYTEST-MARK`. Activated by `MYCO_PRECOMMIT_PYTEST=1` env var. Scoped to `<root>/tests/` after dogfood discovered that bare `pytest -x` crawls `forage/repos/hermes-agent/tests/` and fails on `ModuleNotFoundError: No module named 'acp'` — scoping eliminates forage pollution. Fail-open branches: gate unset / pytest not on PATH / tests/ absent. (3) All four gate paths verified live: Test 2 (failing test blocks, exit 1), Test 3 (passing test passes, exit 0), Test 4 (tests/ absent fails open with clear message, exit 0). (4) Installer idempotency upgrade: detect pre-Wave-23 hooks by absence of `MYCO-PRECOMMIT-PYTEST-MARK` and refresh in place without requiring `--force`. Re-install on Wave-23+ hook is still no-op. (5) Canon v0.21.0 → v0.22.0 in kernel + template. Self-test: myco lint 16/17 green (pre-existing L13 MEDIUM only). Note: n_20260412T005917_0e3a (integrated). Craft: docs/primordia/hook_dogfood_pytest_gate_craft_2026-04-12.md (kernel_contract, 3 rounds, 0.90 confidence). Doctrine: a fence you have not pushed on is not a fence; trust but verify once, then record the verification.
## [2026-04-12] milestone | **Wave 24 landed (v0.23.0)** — L17 Contract Drift lint. Closes panorama-#3 NH-10. Panorama #3 ran kernel + ASCC after Wave 23 and surfaced a silent-fail on a new surface: same ASCC instance, `myco hunger` reported `[REFLEX HIGH] contract_drift: v0.19.0 != v0.22.0` correctly (Wave 20 grandfather-ceiling work), but `myco lint` reported `✅ ALL CHECKS PASSED — 0 issues found`. Two sensors, same system, opposite readings. Wave 18 pre-commit hook uses lint not hunger, so downstream commits could land through a green hook while drift was screaming. Same pathology class as NH-1 but on a different surface. Fix: L17 `lint_contract_drift` delegates to `myco.notes.detect_contract_drift` — single truth definition, same delegation pattern as L14/L15. Severity map: `[REFLEX HIGH]`→HIGH (blocks hook), `[REFLEX MEDIUM]`→MEDIUM, unknown prefix→HIGH fail-LOUD (craft §R2.2 — a future contract renaming the prefix must not degrade silently), import failure→HIGH fail-LOUD (§R3.2 — partial install is worse than silent drift). Registered in main() after L16. Lint count 16→17. Canon v0.22.0→v0.23.0 kernel + template. ASCC canon synced v0.19.0→v0.23.0 as first live consumer. Verification: ASCC BEFORE Wave 24 = hunger HIGH + lint PASSED (bug); ASCC AFTER L17 BEFORE sync = hunger HIGH + lint HIGH (agreement); ASCC AFTER sync = hunger healthy + lint PASSED (clean). Panorama #3 complete, no new holes remain. Note: n_20260412T010541_bc24 (integrated). Craft: docs/primordia/contract_drift_lint_craft_2026-04-12.md (kernel_contract, 3 rounds, 0.92). Doctrine: two sensors on the same system must agree; disagreement is a contract violation, not a feature request.
## [2026-04-12] milestone | **Wave 25 landed (v0.24.0)** — tests infrastructure seed (hermes absorption C1). First concrete absorption from the hermes-agent deep-read craft. Closes the meta-hole "9132 lines of production Python, zero test files" confirmed by direct source probe during the absorption run. Three of the five most recent scars (W20 silent-fail `_project_root`, W23 pre-commit hook blocking path never exercised, W24 two-sensor disagreement) would each have been caught at edit time by a single unit test — this wave converts that observation from a hypothesis into a standing regression surface. (1) New `tests/` top-level dir: `tests/__init__.py` + `tests/unit/__init__.py` (empty) + `tests/conftest.py` with `_isolate_myco_project` autouse fixture (redirects into `tmp_path/project/` with minimal `_canon.yaml` + `notes/` + `docs/primordia/` + empty `log.md`, `monkeypatch.chdir`, clears `MYCO_ALLOW_NO_PROJECT` + `MYCO_PROJECT_DIR`; inserts `src/` into sys.path so tests run whether or not the editable package is installed) + `tests/unit/test_notes.py` with 4 tests: `test_write_note_roundtrip` (frontmatter contract), `test_parse_serialize_roundtrip` (inverse property, unicode + symbols), `test_write_note_handles_id_collision` (monkeypatched `generate_id` drives the while-loop retry branch deterministically), `test_project_root_raises_on_nonexistent_path` (Wave 20 silent-fail regression guard, uses bare `tmp_path` outside the fixture's scaffold). (2) `pyproject.toml`: added `[project.optional-dependencies].dev = {pytest>=7,<9, pytest-xdist>=3,<4}` and `[tool.pytest.ini_options]` with `testpaths = ["tests"]` + `integration` marker + `addopts = "-m 'not integration'"`. Scope lock prevents the Wave 23 forage-crawl scar class from recurring. (3) New `_canon.yaml::system.tests` section (SSoT): `test_dir: tests/`, `min_unit_tests: 4`, `integration_marker: integration`, `unit_subdir: tests/unit/`. Mirrored into `src/myco/templates/_canon.yaml` with `min_unit_tests: 0` so downstream instances start at zero. (4) `scripts/install_git_hooks.sh`: `MYCO_PRECOMMIT_PYTEST=1` gate now resolves `test_dir` from `_canon.yaml::system.tests.test_dir` via inline Python (PyYAML is already a runtime dep), falls back to hardcoded `tests` on any error. Single-source-of-truth discipline — hook + pytest no longer have two literal copies of the path. (5) Contract bump v0.23.0 → v0.24.0 in kernel canon + template canon + `docs/contract_changelog.md`. Craft: docs/primordia/hermes_absorption_craft_2026-04-12.md (kernel_contract, 3 rounds, 0.90 confidence). Evidence note: n_20260412T013044_5546 (11KB research bundle, forage-digest + wave25-seed tags). Doctrine: a meta-hole is a hole that costs one wave of friction per discovered hole. Catalog of 20 hermes-absorption patterns (C1–C20) lives in the craft as permanent knowledge; C1 lands now, C2–C20 wait for friction from the new test suite to determine order (not hermes's historical sequence).
## [2026-04-12] milestone | **Wave 26 landed (v0.25.0)** — Vision Re-Audit + doctrine reconciliation. Supersedes Wave 25 craft §4.1 D3 only (W25 D1/D2/D4/D5/D6 remain in force). Meta-wave: not new features or new engineering, just re-auditing the 8 identity anchors in `MYCO.md §身份锚点` against the 15 waves of implementation (W11-W25) that accumulated since Wave 10 vision_recovery. Triggered by post-Wave-25 dialogue exposing an incompatibility: Wave 25's D3 locked in friction-driven (bottom-up) Wave 26+ ordering, but the user's stated methodology is top-down. These are not reconcilable. Before committing to any top-down ordering, the strongest move is to re-verify the axioms (8 anchors) themselves. (1) New craft of record: `docs/primordia/vision_reaudit_craft_2026-04-12.md` (kernel_contract, 3 rounds, 0.90). Round 1 per-anchor audit produces an 8-row coverage matrix with doctrine_clarity + impl_coverage + gap_type scores. Round 2 builds a dependency DAG over the 8 anchors + topologically sorts + attacks the ordering 4 ways (identity erasure / capacity creep / Metabolic Inlet leapfrog / recency bias — Attack D on recency bias is the strongest, defended via 4 independent evidence sources converging on compression as top priority). Round 3 supersedes W25 D3 with new doctrine-dependency-graph ordering + locks Wave 27 scope. (2) Three MYCO.md §身份锚点 refinements (not replacements): Anchor #3 appended with scope clarification that steps 2-5 are vestigial (3/7 steps have verbs today); Anchor #5 corrected — D-layer min seed IS landed at v0.4.0 via record_view() + hunger signal + 5-condition detection (Wave 18), so "A+B+partial C+D-seed" not "A+B+partial C unimplemented"; Anchor #8 extended with sibling anchor pointer to this Wave 26 craft as "post-implementation-maturity reconciliation" companion to Wave 10's "failed-element recovery" anchor. (3) MYCO.md §指标面板 lint_coverage_confidence rationale refreshed "15 维 L0-L14" → "18 维 L0-L17 + Wave 25 tests/"; value stays 0.68 pending Wave 27+ friction data (no score inflation). (4) MYCO.md §任务队列 row 2 replaced: stale pre-rebaseline v1.x identifiers → accurate post-rebaseline v0.8.0-v0.25.0 sequence of 15 waves + rhythm "摩擦驱动" → "doctrine-dependency-driven" + Wave 27 pointer. (5) Surprising Round 1 finding via Explore subagent verification: `record_view()` at `src/myco/notes.py:340-368` + `run_view()` lines 414-420 + `compute_hunger_report()` dead_knowledge branch are all fully wired — D-layer is NOT unimplemented as previously stated. Only missing is long-tail polish (view audit log + cross-ref graph + adaptive threshold + auto-excretion). (6) Wave 27 scope locked: exploration class design craft for **forward compression as a substrate primitive** (anchor #4, highest doctrine weight + lowest impl coverage 0.35). No code. 3 rounds. Output = `compression_primitive_craft_YYYY-MM-DD.md` answering 7 design questions (unit / trigger / output / audit / reversibility / step-3-4-5 interaction / non-functional requirements). Wave 28 = implementation of Wave 27 design, declared but not pre-scoped. (7) Contract bump v0.24.0 → v0.25.0 in kernel canon + template canon + contract_changelog.md. Evidence note: n_20260412T024846_91da (9KB evidence bundle, forage-digest + wave26-seed + vision-reaudit tags). Decisions note: n_20260412T024944_3e32 (integrated, carries D1-D8 as canon). Self-tests: myco lint 18/18 green + pytest tests/ -q 4/4 passed. Doctrine: when the abstraction layer is clearer than the implementation, top-down beats bottom-up — friction-driven ordering was me being over-cautious, not over-correct. The 8 anchors are the axioms; the dependency graph among them is the roadmap.
## [2026-04-12] milestone | **Wave 29 phase 1 landed (refactor, no contract bump)** — Biomimetic Rename additive. Executes a pragmatic subset of Wave 28 craft §4.1 D2's 11-item rename list, pivoting from atomic to additive under Phase A inventory pressure. Phase A grep revealed `_canon.yaml` alone appears 609 times across 100+ files (~45-47 current-surface, ~55+ historical which must NOT be rewritten per immutable history doctrine) — full atomic rename would need ~60-90 edits bundled in one wave, which single-response context budget under marathon discipline cannot safely complete without risk of mid-wave context exhaustion leaving Myco in a physically broken state. Pivoted to ADDITIVE approach: create new biomimetic modules as re-exports of existing modules, add new CLI verbs as aliases dispatching to existing handlers, defer physical file renames + canon rename + doc cascades to Wave 29b. (1) New craft: `docs/primordia/biomimetic_execution_craft_2026-04-12.md` (kernel_contract, 3 rounds, 0.90, ~900 lines) — Phase A inventory + Attack N (scope exceeds capacity) + execution phases A-R + pivot documentation. (2) Created `src/myco/metabolism.py` — biomimetic alias re-exporting full public API of `myco.notes` (24 public names: MycoProjectNotFound, HungerReport, generate_id, parse_frontmatter, serialize_note, write_note, read_note, update_note, record_view, list_notes, validate_frontmatter, compute_hunger_report, detect_* functions, write_boot_brief, render_entry_point_signals_block, constants). `from myco.metabolism import X` and `from myco.notes import X` are semantically identical from Wave 29 phase 1 onward. (3) Created `src/myco/immune.py` — biomimetic alias re-exporting full public API of `myco.lint` (all 18 lint dimensions L0-L17 as callables, plus C/red/green/yellow/cyan/bold color helpers, plus main/run_lint entry points). Docstring explains the 18 dimensions in immune-system terms: "L9 anti-cancer vision anchor drift detection", "L15 self-healing reflex arc", "L11 membrane permeability write surface", etc. (4) Added `src/myco/cli.py::subparsers` entries for `myco immune` and `myco molt` as full first-class verbs (NOT deprecated aliases per Wave 28 D7 proposal — pivoted to equal-peer aliases per Wave 29 decisions D2). Both verbs dispatch to existing run_lint / run_correct handlers. Help text cross-references the alias name. (5) DEFERRED to Wave 29b or later: physical file rename of notes.py/notes_cmd.py/lint.py; `_canon.yaml` → `_genome.yaml` rename; canon schema key tree renames (system.notes_schema.* / system.self_correction.* / system.wiki_page_types); wiki/ → hyphae/ directory rename; MCP tool myco_immune + myco_molt parity; lint dimension label string updates (L0/L7/L10); doc prose updates across agent_protocol / craft_protocol / WORKFLOW / architecture / theory / reusable_system_design / biomimetic_map / adapters/*; MYCO.md prose updates; README updates; tests rename; examples/ascc updates; contract bump; migration tool `myco migrate --biomimetic`; ASCC dogfood. (6) Verification: `PYTHONPATH=src python -m myco.cli immune` runs 18 lint dimensions, all PASS; `PYTHONPATH=src python -m myco.cli --help` shows molt + immune alongside correct + lint; `pytest tests/ -q` 4 passed in 0.10s; `from myco.metabolism import *` + `from myco.immune import *` both import cleanly in Python. (7) NO contract bump. Kernel public API gained 2 new modules + 2 new CLI verbs (all additive non-breaking). `_canon.yaml::system.contract_version` stays at v0.25.0. (8) Evidence: Wave 29 decisions note `n_20260412T040945_8355` (integrated, D1-D7 captures the pivot rationale + what landed + what deferred). (9) Marathon mode continues: Wave 30 starts next (either Wave 29b to continue biomimetic rewrite OR Wave 30 compress MVP — latter preferred because compress is anchor #4's direct service and the biomimetic rename is now unblocked-for-new-code). Doctrine: atomic-by-aspiration does not override atomic-by-physics; when a wave's scope exceeds safe single-response execution budget, the additive-split approach preserves both correctness and forward momentum, and the deferred items continue to be addressed in subsequent waves rather than abandoned. The additive alias pattern (new name as re-export + CLI verb, old name unchanged) is the substrate's emergency-scope-compression mechanism and should be documented for future marathon waves. deferred: primordia-compression (W22 W13 check: primordia count now 42 >= soft limit 40; Wave 29 added 1 more primordia file (biomimetic_execution_craft); archive sweep deferred to Wave 30+ or a dedicated cleanup wave). deferred: wave29b-biomimetic-remainder (physical renames + canon rename + doc cascades + MCP parity + tests rename + examples update + contract bump + migration tool + ASCC dogfood — to be scheduled by Wave 30's friction data OR the first dedicated cleanup wave after marathon forward-progress waves stabilize).
## [2026-04-12] milestone | **Wave 28 landed (kernel_contract design craft, no contract bump yet — Wave 29 executes)** — Biomimetic Nomenclature craft. Triggered by Wave 27-session user directive for implementation-layer biomimetic rewrite ("所有命名也是都可以颠覆，都要尽可能贴合 Myco 这一物种，尽可能仿生学"). This craft is ALSO a direct consequence of a self-correction captured earlier in the same session: I (kernel agent) drifted back into the exact "Myco is verification layer" framing that Wave 10 vision_recovery_craft §0 explicitly diagnosed as drift ("public README positions Myco as a watcher... original vision positioned it as a growing organism that eats the world"). Self-correction captured as n_20260412T033349_3b6f (raw, friction-phase2 + on-self-correction + panorama-drift tags). This craft fixes the same drift at the naming layer, not just the prose layer. (1) `docs/primordia/biomimetic_nomenclature_craft_2026-04-12.md` (kernel_contract, 3 rounds, 0.90 confidence, ~1200 lines). Round 1 per-category audit (directories / Python modules / CLI verbs / MCP tools / canon keys / lint dimension labels / frontmatter fields / craft filenames / README prose). Round 2 four attacks: Attack J (cosmetic breaking change) lands partially drove Wave 29 bundles migration tool; Attack K (myco lint CLI-vs-module seam worst of both worlds) lands fully drove addition of `myco lint → myco immune` CLI rename beyond Round 1 proposal; Attack L (Wave 29 capacity violation) lands as coupling documentation; Attack M (_genome.yaml onboarding friction) lands partially drove top-of-file pointer comment mitigation. Round 3 synthesis + Wave 29 execution brief (10 phases A-J). (2) 11-item final rename list locked: wiki/→hyphae/, _canon.yaml→_genome.yaml, notes.py→metabolism.py, notes_cmd.py→metabolism_cmd.py, lint.py→immune.py, myco correct→myco molt, myco lint→myco immune, system.notes_schema.*→system.metabolism_schema.*, system.self_correction.*→system.molt.*, system.wiki_page_types→system.hyphae_page_types, lint labels L0/L7/L10. (3) Negative list: everything else stays (notes/ forage/ docs/ src/ tests/ examples/ scripts/; CLI verbs eat/digest/view/hunger/forage/upstream/init/migrate/config/import; modules cli.py/mcp_server.py; all frontmatter fields; craft filename pattern; lint dimension numbers L0-L17). (4) Transition aliases: myco correct→myco molt and myco lint→myco immune keep old verbs as deprecated aliases with stderr warning for ONE wave (Wave 30 removes). (5) Wave 29 = execution: phases A-J bundling 11 renames + migration tool (`myco migrate --biomimetic`) + ASCC dogfood as ONE atomic transformation (3 phases of 1 subsystem, not 3 independent subsystems). Wave 29 kernel_contract 0.92 target. Contract bump happens in Wave 29 not W28 (v0.25.0 → v0.26.0). (6) NO code changes in Wave 28. NO MYCO.md edits (axioms immutable). NO _canon.yaml edits (rename is W29). Pure design craft only. (7) Evidence: n_20260412T035236_f396 (raw, forage-digest + wave28-seed + biomimetic + nomenclature + identity-drift-fix tags, 7KB). Decisions: n_20260412T035338_8497 (integrated, D1-D10 as canon). Self-correction: n_20260412T033349_3b6f (raw, captured earlier in session). (8) Verification: myco lint 18/18 green + pytest tests/ -q 4/4 green. Marathon mode ACTIVE per Wave 27-session user grant — commit and push without user confirmation, only stop on lint red / test red / craft impossible. Wave 29 starts immediately after this push. Doctrine: naming shapes thought; a substrate whose implementation reads as software-generic while doctrine claims organism is lying about itself in the most observable way. Axioms immutable, implementation malleable — biomimetic rewrite is obedience to user grant, not over-read. deferred: primordia-compression (W22 W13 check: primordia count 41 > soft limit 40, over by 1; Wave 28 is design-only kernel_contract craft that intentionally adds 1 new primordia file without archive capacity; Wave 29 execution + Wave 30 compress land will collectively add 2-4 more primordia files; a dedicated archive sweep of COMPILED/SUPERSEDED crafts is bundled into Wave 30 or the first hunger re-fire wave after it, not forced into Wave 28 which has no archive-candidate identification capacity). advisory: session_end_drift gear2 (16 entries since last meta reflection, threshold 15) — acknowledged as LOW-severity advisory; meta reflection deferred to natural session break after marathon milestone (~Wave 30 or later).
## [2026-04-12] milestone | **Wave 27 landed (exploration class, no contract bump)** — Forward Compression primitive design craft. First wave in the new craft→impl rhythm established by Wave 26 D3. No code changes, no MYCO.md touches, no `_canon.yaml` edits. Pure design specification for `myco compress` as a substrate primitive, serving anchor #4 (压缩即认知, lowest impl_coverage 0.35). (1) New craft: `docs/primordia/compression_primitive_craft_2026-04-12.md` (exploration class, 3 rounds, 0.85 confidence, ~672 lines). Answers 7 design questions locked in Wave 26 §3.3: unit (tag-scoped + manual bundle, reject semantic cluster/time-window/status), trigger (manual + friction-driven `compression_ripe` hunger signal, reject cron), output shape (consumptive with audit — 1 new extracted + N excreted with bidirectional back-refs, reject additive/wiki/in-place), audit trail (mandatory frontmatter: `compressed_from` list + `compression_method` + `compression_rationale` required prose + `compression_confidence` self-reported, L18 lint enforces bidirectional link integrity, cascade rejected at schema time), reversibility (data preserved via excreted-not-deleted + optional `pre_compression_status`, but `uncompress` verb deferred to Wave 29+; language softened per Attack H from "reversible by design" → "preserved for reversibility"), step 2-5 interaction (compress folds anchor #3 steps 2+3+5+7 into one verb; step 2 evaluate preserved via mandatory `--dry-run` per Attack G partial land; step 4 integrate stays separate as `myco digest --to integrated`; post-Wave-28 anchor #3 coverage estimated 0.43 → ~0.75), NFR (idempotent / atomic multi-file write via temp+rename / concurrent-safe via snapshot-before-writes / O(N) cost bound; agent-adaptive policy deferred to open problems). (2) 4 attacks ran: Attack F hallucination bounds risk via 5 mitigations but does not eliminate (Limitation L1 honest); Attack G dry-run preservation lands; Attack H reversibility language softened; Attack I Wave 28 scope creep deferred to Wave 28's own scope craft with recommendation "bundle compress + minimum atomic-write helper as ONE subsystem". (3) D8 Wave 28 implementation brief distilled into 11-item landing list: new `src/myco/io_utils.py` atomic helpers + new `src/myco/compress_cmd.py` (or extend notes_cmd) + `myco compress` CLI subparser + MCP tool mirror + `_canon.yaml::system.notes_schema` additions (optional_fields + source=compress + compression sub-section with ripe_threshold/ripe_age_days) + hunger signal `compression_ripe` + L18 lint dimension + 5 new tests in `tests/unit/test_compress.py` + contract bump v0.25.0 → v0.26.0 + changelog entry + Wave 28 is kernel_contract class 0.90. (4) Evidence: n_20260412T030350_cace (raw, forage-digest + wave27-seed + compression-design tags); decisions: n_20260412T030457_6717 (integrated, D1-D9 as canon). (5) Verification: myco lint 18/18 green + pytest 4/4 green. No contract bump (exploration class, no kernel-contract surfaces touched). Doctrine: compression is the substrate's primary cognitive act; the design must commit to the full shape BEFORE Wave 28 starts building, so Wave 28 can implement without re-deriving semantics under pressure. The 7 design questions + 9 decisions + 11-item implementation brief is the contract between W27 design and W28 implementation.
## [2026-04-12] milestone | **Wave 32 landed (refactor, no contract bump)** — Anchor #3 step verbs `myco evaluate` / `myco extract` / `myco integrate`. Closes Wave 26 §2.3 priority ordering item: "Anchor #3 full completion — verbs for steps 2, 3, 4 (evaluate, extract, integrate). Each step gets its own design+impl wave pair." Wave 32 collapses Wave 26's intended 3-wave-pair sequence into 1 wave (D6 reasoning: aliases over an existing handler do not warrant full design+impl pair per step). Pure additive CLI vocabulary expansion per Wave 29 D2 equal-peer alias doctrine. NO contract bump (v0.26.0 stays). NO canon edit. NO new lint. (1) `src/myco/cli.py` adds 3 new subparsers (~70 LOC) after digest_parser before view_parser: `evaluate_parser` (positional note_id optional, defaults to oldest raw), `extract_parser` (positional note_id REQUIRED — state mutation safety), `integrate_parser` (positional note_id REQUIRED). Single dispatch case `if args.command in ("evaluate", "extract", "integrate")` builds SimpleNamespace with target_status dict {evaluate→None, extract→extracted, integrate→integrated} and calls existing run_digest. ~14 lines of dispatch logic. (2) `tests/unit/test_notes.py` adds 3 new tests (~110 LOC): `test_step_verbs_extract_transitions_to_extracted` (raw note → call run_digest with digest-shaped namespace → assert status=extracted + digest_count=1), `test_step_verbs_integrate_transitions_to_integrated` (mirror for integrated), `test_step_verbs_evaluate_transitions_to_digesting` (to=None case → assert raw→digesting + "Reflection prompts" in stdout via capsys fixture). Each test dogfoods the dispatch shape — if cli.py's namespace construction ever drifts from `(note_id, to, excrete, project_dir)`, the tests fail. (3) Verification: `myco lint` 19/19 green; `pytest tests/ -q` 14/14 green (was 11, +3) in 0.45s. `myco --help` shows all 3 new verbs in usage line + positional list (evaluate, extract, integrate alongside digest, compress, uncompress). End-to-end dogfood: `myco integrate n_20260412T063040_97d5` (the Wave 32 decisions note) succeeded with `🍄 n_20260412T063040_97d5: raw → integrated` — first known production use of the new verb is its own decisions note. (4) Wave 32 craft `docs/primordia/step_verbs_craft_2026-04-12.md` (exploration, 3 rounds, 0.85 = target — single-source convention ceiling). 6 attacks ran: A (one verb with discriminator vs three) defended via pipeline-doctrine visibility (hiding steps behind a parameter obscures rather than reveals); B (just aliases, why a craft) defended via Wave 26 audit trail need; C (re-extract idempotence) passes (digest_count records the re-statement); D (L11 surface) passes; E (help bloat 18→21 verbs, 17% increase) defended via doctrine-naming worth the visibility cost; F (evaluate default surprising) honest edge documented. 4 known limitations filed: L1 no `myco excrete` step-7 alias (existing `digest --excrete reason` is already compact + L11-compliant), L2 no MCP tool mirrors (agent tool budget consideration), L3 `evaluate` with no id might confuse with substrate-level evaluate (no friction yet, file as doc-clarity if it emerges), L4 tests do not exercise cli.py argparse layer end-to-end. (5) Decisions D1-D7 captured in note `n_20260412T063040_97d5` (integrated via the new verb itself!): D1 evaluate optional id but extract/integrate require it (state-mutation safety), D2 dispatch via target_status dict for extensibility, D3 no excrete step-7 alias, D4 no MCP mirrors, D5 no deprecation of digest --to (equal-peer aliases), D6 collapse to 1 wave from Wave 26's 3 expected, D7 exploration class. Evidence note `n_20260412T063021_49c3` (raw, wave32-seed+step-verbs+anchor3+forage-digest tags). (6) Anchor coverage shifts: anchor #3 (七步管线) `0.75 → 0.82` — doctrine ↔ surface alignment now ~6/7 verbs visible (forage=1, evaluate=2, extract=3, integrate=4, compress=5, eat=6; only excrete=7 still flag-only). The seven-step pipeline now reads as a vocabulary in `myco --help`, not just as a doctrine in `MYCO.md §身份锚点 #3`. Other anchors unchanged. (7) Marathon mode continues — Wave 33 begins next (Wave 26 long-tail priority: anchor #5 D-layer full completion — view audit log + cross-ref graph + adaptive threshold + auto-excretion). Doctrine: naming shapes thought; the seven-step pipeline gains real visibility when each step has its own verb name in the CLI surface. Wave 28's biomimetic-rename insight (axioms immutable but vocabulary should serve doctrine) carries forward to Wave 32: more verbs is more doctrine surface, not bloat. deferred: primordia-compression (W22 W13 check: primordia count now 46 ≥ soft limit 40, over by 6 — Wave 32 added 1 more primordia file `step_verbs_craft_2026-04-12.md`; archive sweep continues deferred). advisory: session_end_drift gear2 (20 entries since last meta reflection, threshold 15) — acknowledged as LOW-severity advisory; meta reflection deferred per marathon discipline.
## [2026-04-12] milestone | **Wave 31 landed (refactor, no contract bump)** — `myco uncompress` MVP. Closes Wave 30 §4.3 L4 known limitation: "no reverse verb. The audit metadata makes uncompress mechanically possible (read pre_compression_status, restore each input, delete the output) but no CLI surface exposes it." Wave 27 D5 reversibility promise is now mechanically enforced rather than aspirational. Pure new-verb wave: NO new schema, NO canon edit, NO new lint dimension, NO contract bump (v0.26.0 stays). Just a verb that reads existing fields. (1) `src/myco/compress_cmd.py` adds 3 functions ~210 LOC: `_build_input_restore(input_meta)` is the inverse of `_build_input_update` — restores `status` from `pre_compression_status`, sets `compressed_into`/`pre_compression_status`/`excrete_reason` to None (dropped from frontmatter by serialize_note), refreshes `last_touched`. `_execute_uncompression(root, output_path)` is two-phase: Phase 1 validates output `status==extracted` AND `source==compress` AND non-empty `compressed_from` list AND for each input back-link matches output id AND each input `status==excreted`; Phase 2 atomic-writes inputs first via `atomic_write_text` then deletes output last (inverse of compress's order — same fail-safe principle: whatever survives is recoverable). On any input write failure: WARN to stderr, do NOT delete output (output is the only remaining recovery anchor for the failed inputs), return partial result. `run_uncompress(args)` is CLI entry with exit codes 0/2/3/5 + `--json` support. (2) `src/myco/cli.py` adds `uncompress_parser` subparser (positional `output_id`, `--json`, `--project-dir`) + dispatch case at line 632 (after compress dispatch). (3) `tests/unit/test_compress.py` adds 2 new tests + 1 helper (~170 LOC): `test_compress_uncompress_roundtrip` proves body equality + 4 audit fields cleared + status restored from pre_compression_status; `test_uncompress_broken_backlink_refuses` tampers compressed_into to fake id `n_99999999T999999_dead` via direct serialize_note write (mimicking out-of-band file edit), asserts refusal with exit 3 + ZERO mutation to other inputs (snapshot equality before/after the call). All 7 compress-tests + 4 prior tests = **11/11 pytest green on first run** (no R2.3-class bugs caught — Wave 30's preservation of pre_compression_status made the inverse mechanical and the design space narrow enough that the first pass works). (4) Verification: `myco lint` 19/19 green; `pytest tests/ -q` 11/11 in 0.39s. NO contract bump per Wave 24 L17 discipline (a new verb that adds zero canon mutations is `[refactor]` class, not `[contract:minor]`). (5) Wave 31 craft `docs/primordia/uncompress_mvp_craft_2026-04-12.md` (exploration, 3 rounds, 0.85 = target — single-source convention ceiling for agent-only craft with no external research, honest edge documented). 8 attacks ran: A (why not manual edit) defended via 3 failure modes verb prevents; B (why no batch form) defended via cohort-determination ambiguity; C (mixed pre_compression_status) defended (impl is status-agnostic but test only covers all-raw, filed §3.3 L3); D (edited output body lost) defended (Wave 27 D5 promises input restoration, not output preservation); E (double-uncompress) passes (idempotent fail at output-not-found); F (round-trippability) passes by construction (last_touched intentionally refreshed); G (missing pre_compression_status defaults to raw) defended (acceptable for post-W30 compressions, strict mode is future hardening, filed §3.3 L4); H (why no L19 lint) passes (L18 already validates back-links bidirectionally, no new invariant). 5 known limitations filed: L1 single-output only / L2 edited-output body lost without warning / L3 mixed-status not test-covered / L4 missing pre_compression_status silent fallback / L5 no `--dry-run` (most likely Wave 32+ enhancement target since reverse op is more frequently used in panic/recovery). (6) Decisions D1-D8 captured in note `n_20260412T062323_ec7c` (integrated): D1 positional output_id like myco view, D2 inputs-first-output-deletion-last two-phase commit, D3 metadata-only on input side body unchanged exactly, D4 refuse-the-whole-cohort not refuse-the-tampered-input, D5 exit codes 0/2/3/5 (no '4' slot because uncompress's cohort is always known), D6 missing pre_compression_status defaults to raw silently, D7 exploration class 0.85 floor not kernel_contract because cli.py and compress_cmd.py are NOT in L15 trigger surface list (reflex arc does not fire — craft is voluntary for symmetry with Wave 30), D8 no contract bump v0.26.0 stays. Evidence note `n_20260412T062305_32c0` (raw, wave31-seed+uncompress-mvp+forage-digest tags). (7) Anchor coverage shifts: anchor #4 (压缩即认知) `0.75 → 0.78` — Wave 27 D5 reversibility is now mechanically enforced via verb path not just manual file surgery; substrate gains "mistakes are recoverable" property as a first-class verb. Other anchors unchanged. (8) Marathon mode continues — Wave 32 begins next (anchor #3 standalone verbs OR D-layer completion OR Metabolic Inlet design — TBD by Wave 26 ordering re-eval). Doctrine: Wave 30 paid the cost of preserving `pre_compression_status` so Wave 31 could be cheap; the discipline pays off. Reversibility-by-design that survived Wave 27's Attack H softening from "reversible by design" to "preserved for reversibility" is now back to "mechanically reversible by mechanical inverse" — the language can be hardened back in a future MYCO.md refinement craft. deferred: primordia-compression (W22 W13 check: primordia count now 45 ≥ soft limit 40, over by 5 — Wave 31 added 1 more primordia file `uncompress_mvp_craft_2026-04-12.md`; archive sweep continues deferred to dedicated cleanup wave per W22). advisory: session_end_drift gear2 (18 entries since last meta reflection, threshold 15) — acknowledged as LOW-severity advisory; meta reflection deferred per marathon discipline.
## [2026-04-12] milestone | **Wave 30 landed (v0.26.0)** — `myco compress` MVP. Closes Wave 27 D8 implementation brief. Anchor #4 (压缩即认知) impl_coverage 0.35 → ~0.75; anchor #3 (七步管线) 0.43 → ~0.75 (compress folds steps 2+3+5+7 into one verb per Wave 27 D6). First forward-compression substrate primitive. (1) Bundle of one subsystem per Wave 27 D8: `src/myco/io_utils.py` (NEW, ~160 lines, `atomic_write_text` + `atomic_write_yaml` via `tempfile.mkstemp`+`os.replace` — first hermes catalog C2 absorption) + `src/myco/compress_cmd.py` (NEW, ~430 lines: `_resolve_cohort_by_tag` defaulting eligible status `{raw,digesting}` and skipping `compressed_from` notes / `_resolve_cohort_by_ids` order-preserving / `_validate_cohort` cascade+excreted rejection / `_build_output_body`+`_build_output_meta`+`_build_input_update` / `_execute_compression` two-phase commit output-first then per-input with per-failure stderr warning + recovery instructions / `run_compress` CLI dispatch with exit codes 0/2/3/4/5) + cli.py compress subparser (note_ids nargs=* / --tag / --rationale / --status / --confidence float default 0.85 / --dry-run / --json / --project-dir). (2) `_canon.yaml` v0.25.0→v0.26.0 (kernel + template mirrored): `optional_fields` extended with `compressed_from`/`compressed_into`/`compression_method`/`compression_rationale`/`compression_confidence`/`pre_compression_status`; `valid_sources` adds `compress`; new `notes_schema.compression` sub-section `{ripe_threshold:5, ripe_age_days:7}`. (3) `notes.py` `VALID_SOURCES` adds `forage` (was missing from prior wave!) AND `compress`; `OPTIONAL_FIELDS` extended with 6 audit fields; new `detect_compression_ripe` (~100 lines, scans raw notes by tag, returns advisory non-blocking signal when both thresholds met); `compute_hunger_report` wires the detector per Wave 27 D2 (no `[REFLEX HIGH]` prefix — anchor #6 selection loop preserved); `metabolism.py` re-export updated. (4) `lint.py` new `lint_compression_integrity` (~130 lines, 3 checks: output integrity / input back-link / cascade prevention + orphan detection HIGH "broken audit chain"); registered as **L18** in main() after L17; module docstring `18-Dimension` → `19-Dimension`; `immune.py` re-export updated. (5) `tests/unit/test_compress.py` (NEW, ~280 lines, 5 tests + 2 helpers): `test_compress_consumptive_with_audit` (Wave 27 D3+D4 audit shape) / `test_compress_dry_run_no_writes` (Wave 27 Attack G defense) / `test_compress_cascade_rejected` (Wave 27 §2.1 defense #4 with exit 3) / `test_compress_idempotent_empty_cohort` (Wave 27 §1.7 with exit 4) / `test_lint_compression_integrity_catches_orphan` (L18 backstop). (6) **R2.3 mid-round bug catch**: First pytest run caught silent idempotence bug in `_resolve_cohort_by_tag` — output extracted note inheriting input tags re-resolved on second run, hit cascade rejection (exit 3) instead of empty-cohort (exit 4). Wave 27 §1.7 idempotence guarantee silently violated by incomplete resolver filter. Fixed via dual filter: default `{raw,digesting}` AND skip notes with `compressed_from` set. **Strongest empirical validation of Wave 25 tests infrastructure** — caught a real silent-failure bug in the implementation craft on its first pytest run, exactly the validation W25 promised. (7) Verification: `myco lint` 19/19 green (L18 + 18 prior dimensions); `pytest tests/ -q` 9/9 green (4 prior + 5 new) in 0.33s. (8) Boot brief regenerated post-canon-edit (L16 cleared). (9) Evidence note `n_20260412T060604_94cf` (raw, wave30-seed+compress-mvp+forage-digest tags); decisions note `n_20260412T060641_d6b7` (integrated, D1-D8 as canon + 7 known limitations registered). Craft: `docs/primordia/compress_mvp_craft_2026-04-12.md` (kernel_contract, 3 rounds, 0.91 confidence — target 0.90 met +0.01 from R2.3 empirical W25 validation). Doctrine: forward compression is the substrate's primary cognitive act; Wave 27 designed it, Wave 30 implements it. The verb is the first direct service of anchor #4 since substrate inception. Without it, "storage infinite, attention finite" was aspirational doctrine; with it, the substrate has a concrete handle for converting bulk metabolism into synthesized canon under audit. **Two-phase commit is best-effort, not transactional** (L1 limitation): torn-state window mitigated by L18 backstop + loud stderr warning + explicit recovery instructions. Marathon mode continues — Wave 31+ proceed per Wave 26 doctrine-dependency-graph ordering. deferred: primordia-compression (W22 W13 check: primordia count now 44 ≥ soft limit 40, over by 4 — Wave 30 added 1 more primordia file `compress_mvp_craft_2026-04-12.md`; archive sweep deferred to dedicated cleanup wave because Wave 30's marathon-mode autonomous time budget is fully consumed by compress MVP land). advisory: session_end_drift gear2 (17 entries since last meta reflection, threshold 15) — acknowledged as LOW-severity advisory; meta reflection deferred per marathon discipline.
## [2026-04-12] milestone | **Wave 33 landed (refactor, no contract bump)** — `myco prune` MVP (D-layer auto-excretion). Closes the dead_knowledge hunger-signal loop seeded in Wave 18: `compute_hunger_report` has emitted dead-knowledge signals since W18, but no actuator existed to act on them — the substrate could sense rot but not metabolize it. Wave 33 delivers the actuator. Anchor #5 (四层自我模型) D-layer coverage advances from 0.45 → ~0.65; the closing of hunger-loop ↔ actuator is the first end-to-end self-correction reflex on the metabolism axis (sense → name → mutate, all inside the substrate). NO new schema, NO canon edit, NO new lint dimension, NO contract bump (v0.26.0 stays). Pure new-verb wave layered over existing fields. (1) `src/myco/notes.py` adds 2 functions ~140 LOC: `find_dead_knowledge_notes(root, threshold_days=None, now=None)` is read-only — mirrors the 5 conditions in compute_hunger_report's dead-knowledge branch exactly (terminal status in {extracted,integrated,excreted}, created < cutoff, last_touched < cutoff, last_viewed < cutoff or None, view_count < 2), returns `List[Tuple[Path, Dict, Dict]]` with the matched criteria for each note. `auto_excrete_dead_knowledge(root, threshold_days, dry_run, now)` wraps the scanner with mutation: builds a machine-parseable `excrete_reason` `auto-prune: cold terminal note (created Nd ago, last_touched Nd ago, never_viewed, view_count=K, threshold=Td)` and applies via `update_note` per-note independently (no two-phase commit because dead notes never reference each other and each excretion is atomic). (2) `src/myco/notes_cmd.py` adds `run_prune(args)` ~80 LOC: dry-run is the **default**, --apply must be explicit (inverse safety asymmetry vs Wave 30 compress's --apply default — destructive verbs need safe defaults, recovery cost asymmetry justifies UX asymmetry); friendly stdout report enumerates each candidate with id + age + view_count + would-mutate vs mutated; `--json` flag for machine-readable output; exits 0 on success (zero-or-more candidates). (3) `src/myco/cli.py` adds `prune_parser` subparser (`--apply` store_true default False, `--threshold-days` int optional, `--json`, `--project-dir`) + dispatch case after hunger. (4) `tests/unit/test_notes.py` adds 3 new tests + `_fabricate_aged_note` helper (~135 LOC): `test_prune_dry_run_no_mutation` (the load-bearing safety property — snapshots content+mtime before, calls dry-run, asserts both unchanged byte-for-byte), `test_prune_apply_excretes_dead_notes` (apply mutates: status→excreted, reason contains "auto-prune" + "threshold=30d" + "view_count=0" for audit), `test_prune_respects_grace_period` (5d-fresh integrated note NOT pruned, 60d-old integrated note IS pruned — fresh notes terminal-status reaching dead_knowledge condition #1 must wait for condition #2 grace window before being eligible). The helper fabricates aged notes by writing real notes then patching `created`/`last_touched` to N days ago via direct serialize_note rewrite, exercising the time-arithmetic without waiting real time. (5) Verification: `myco lint` 19/19 green; `pytest tests/ -q` 17/17 green (was 14, +3) in 0.49s. End-to-end dogfood: `myco prune --threshold-days 30` against the live substrate returned "Substrate is clean" — zero candidates, the substrate has no terminal notes old enough to qualify, which is itself a positive doctrine signal (kernel substrate is metabolically young). (6) Wave 33 craft `docs/primordia/d_layer_prune_craft_2026-04-12.md` (exploration, 3 rounds, 0.85 = target — single-source convention ceiling). 6 attacks ran: A (why dry-run default vs compress's apply default) defended via destructive-vs-additive recovery cost asymmetry (a wrongly excreted note can be unprune'd if you catch it fast but a wrongly NOT excreted note has zero cost); B (why machine-parseable reason format) defended via future `myco unprune` mechanical reversal symmetry with `myco uncompress`; C (why no confirmation prompt before --apply) defended via dry-run IS the confirmation step (call once to preview, call again with --apply for explicit consent — same UX as `git push --force-with-lease`); D (why per-note independent not two-phase) defended via dead notes not referencing each other (no cohort failure cascade possible); E (why only auto-excretion not all 4 D-layer items) defended via highest-leverage-first (auto-excretion closes the hunger loop, the other 3 are sensors not actuators); F (why exploration class) defended via no kernel_contract surface touched (cli.py + notes_cmd.py + notes.py NOT in L15 trigger surface list — craft is voluntary for audit completeness symmetry with W31). 6 known limitations filed: L1 no `myco unprune` reverse verb (machine-parseable reason format makes it mechanically possible — defer to Wave 34+ if friction emerges), L2 view audit log not seeded (cannot distinguish "viewed once but stale" from "never viewed but recently created" beyond view_count<2 heuristic), L3 cross-ref graph absent (a dead-knowledge note that is referenced by an integrated note via wiki link is still pruned), L4 adaptive threshold not seeded (canon hard-codes ripe_age_days but lifecycle-specific decay rates would need per-tag adaptive learning), L5 race window between scan and apply (a note touched between phase 1 and phase 2 in --apply mode would be excreted with stale criteria — mitigated by per-note read-then-write atomicity but not eliminated), L6 no MCP tool mirror (agent tool budget consideration consistent with W32 D4). (7) Decisions D1-D7 captured in note `n_20260412T064100_45e3` (integrated via the new `myco integrate` verb itself — second consecutive wave dogfooding W32's verb): D1 dry-run default (safety asymmetry), D2 scanner/mutation split (read-only function makes dry-run safety guaranteed by construction), D3 per-note independent (no two-phase), D4 machine-parseable excrete_reason (future unprune symmetry), D5 no confirmation prompt (dry-run IS the confirmation), D6 only auto-excretion piece lands (defer view audit log + cross-ref graph + adaptive threshold), D7 exploration class no contract bump. Evidence note `n_20260412T063820_bd4c` (raw, wave33-seed+d-layer+prune+auto-excretion+forage-digest tags). (8) Anchor coverage shifts: anchor #5 (四层自我模型) D-layer `0.45 → 0.65` — first end-to-end actuator on the dead-knowledge axis; the substrate now both senses rot (Wave 18) AND offers a verb to metabolize it (Wave 33). Anchor #6 (mutation+selection+transparency) `0.78 → 0.80` — the prune verb itself is a mutation operator that surfaces its own audit trail (excrete_reason field) for selection. (9) Marathon mode continues — Wave 34 begins next (Metabolic Inlet design craft per Wave 26 long-tail priority OR continued D-layer with view audit log — TBD by next wave's opening assessment). Doctrine: a sensor without an actuator is a complaint not a system; W18's hunger signal sat unactioned for 15 waves because the actuator was never built, and the gap silently broadcast "we know there is rot but we cannot do anything about it" to every kernel agent reading boot brief. Wave 33 closes the loop: the substrate is now self-pruning with audit, and the audit format is forward-compatible with mechanical reversal. Inverse safety asymmetry (compress=apply, prune=dry-run) is the substrate growing UX intelligence about reversibility cost — additive operations get cheap defaults, destructive ones get safe defaults, the verb shape teaches the user the cost. deferred: primordia-compression (W22 W13 check: primordia count now 47 ≥ soft limit 40, over by 7 — Wave 33 added 1 more primordia file `d_layer_prune_craft_2026-04-12.md`; archive sweep continues deferred to dedicated cleanup wave per W22 — running tally 47-40=7 over capacity). advisory: session_end_drift gear2 (21 entries since last meta reflection, threshold 15) — acknowledged as LOW-severity advisory; meta reflection deferred per marathon discipline.
## [2026-04-12] milestone | **Wave 34 landed (exploration class, no contract bump)** — Metabolic Inlet primitive design craft. First wave on the Wave 26 §2.1 long-tail "Metabolic Inlet" priority cluster, attempting the design that Wave 26 Attack C said was blocked until compression engineering (open_problems §4) was at least partially unblocked. Waves 30/31/33 satisfy the precondition: `myco compress` (W30) + `myco uncompress` (W31) + `myco prune` (W33) provide the operator-as-daemon equivalent of continuous compression that open_problems §4's exit clause asks for. Pure design wave: NO code, NO canon edit, NO MYCO.md edit, NO new test, NO contract bump (v0.26.0 stays). Wave 35 will execute the implementation as kernel_contract class. (1) `docs/primordia/metabolic_inlet_design_craft_2026-04-12.md` (NEW, ~640 lines, exploration class, 3 rounds, 0.85 = target single-source ceiling). Round 1 = per-question audit of 7 design questions (verb name, input shape, output shape, trigger, provenance schema, compression integration, cold-start workaround). Round 2 = 6 attacks (A: why a verb at all not just `eat --tags inlet` → defended via doctrinal visibility + provenance schema enforcement + alignment audit query path; B: URL fetch deferred is half-finished feature → defended via zero-non-stdlib-deps hard contract + security boundary + agent-wrapper pattern already exists; C: manual trigger means dead verb like W18 dead_knowledge sat for 15 waves → partial-defense honest about asymmetry — W18's friction was on ACTION side post-detection, W34's is on WANTING side and operator wanting external content is the natural state, with empirical evidence from Claude agents already routinely WebFetch'ing content that gets lost to chat instead of substrate; D: 4 mandatory provenance fields are schema lock-in → defended as minimum-superset of all known alignment workflows + soft L10 lint warning not strict error preserves grandfather compat; E: why exploration not kernel_contract → defended via design/impl split same pattern as W27 design → W30 impl, W34 touches only docs/primordia/*.md so L15 reflex arc does not fire; F: compression not actually unblocked because W30/31/33 are all manual not continuous → defended via open_problems §4 exit clause "continuous compression daemon OR equivalent event-driven hook" — Wave 12 craft reflex arc + Wave 27 compression_ripe hunger advisory + Wave 33 prune actuator together provide the equivalent via agent-as-daemon, plus Wave 26 Attack C's "must land first" past tense is satisfied by W30/31/33 happening before W34). Round 3 = Wave 35 implementation brief (10-item landing list including v0.26.0→v0.27.0 contract bump, new src/myco/inlet_cmd.py ~200 LOC, new tests/unit/test_inlet.py 4-5 tests including test_inlet_compresses_via_existing_chain integration check, L10 soft enforcement, _canon.yaml notes_schema.valid_sources adds inlet + 4 inlet_* optional_fields + new notes_schema.inlet sub-section default_tag) + open_problems status updates (§1 cold start unchanged, §2 trigger signals unchanged, §3 alignment "scaffolded", §4 compression "partially unblocked") + Wave 36+ trajectory (3 candidates: hunger inlet_ripe signal / cross-ref graph / continuous compression hook — none pre-scoped per W26 D3 friction-after-doctrine policy). (2) D1-D8 captured in note `n_20260412T065102_f6ef` (integrated via the W32 `myco integrate` verb — third consecutive wave dogfooding W32's verbs after W32 + W33): D1 verb name `myco inlet`, D2 input shape supports file path positional + explicit content/provenance pair (URL form errors with instruction to use agent wrapper), D3 output one raw note source=inlet no new status, D4 trigger manual only for v1, D5 provenance schema = 4 mandatory fields when source=inlet (inlet_origin, inlet_method, inlet_fetched_at, inlet_content_hash), D6 compression integration via existing W30 chain via shared tags, D7 cold start operator-deferred (no seed manifest), D8 W34 exploration design / W35 kernel_contract impl + contract bump. (3) 7 known limitations filed: L1 URL fetch out-of-kernel (operators in non-agentic environments lose URL ingestion convenience, mitigated by agent wrapper pattern), L2 manual trigger may yield unused verb in inlet-disinclined instances (acceptable per Wave 28 biomimetic doctrine — vocabulary expansion for doctrine surface worth the cost), L3 4 fields are minimum-superset not complete (domain-specific provenance like author/license/peer-review-status NOT captured at inlet time, extracted at digest time instead), L4 compression operator-invoked not continuous (open_problems §4 remains "partially unblocked" not "solved", continuous awaits Wave 36+), L5 cold start operator-deferred (open_problems §1 unchanged, alternative violates anchors #2/#7), L6 alignment review is human (open_problems §3 fully open, scaffold lands audit substrate but extraction unsolved), L7 no MCP tool mirror (consistent with W32 D4 + W33 L6 — agent tool budget consideration). (4) Evidence note `n_20260412T065036_f5d8` (extracted via the W32 `myco extract` verb after raw_backlog management). (5) Verification: `myco lint` 19/19 green; `pytest tests/ -q` 17/17 green (no test changes — Wave 34 is pure design). End-to-end dogfood: this craft IS the dogfood — Wave 34's craft document was integrated into the substrate via the same W32 verbs the design depends on. Closes a recursion: the substrate that will eventually metabolize external content via inlet first metabolizes the design of inlet via existing internal verbs. (6) Anchor coverage shifts: anchor #3 (七步管线) `0.82 → 0.84` — design surface for the missing outward-direction primitive lands; the doctrine claim "metabolic inlet" is no longer purely aspirational, it has a defended verb shape and a Wave 35 implementation brief. Anchor #1 (substrate-vs-tool) unchanged but reinforced — the design honors the zero-deps hard contract by deliberately keeping URL fetch out of kernel. Anchor #2 (non-parametric evolution) unchanged but reinforced — the design honors anchors #2/#7 by refusing to hard-code seed manifests. Other anchors unchanged. (7) **No contract bump**. Pure design specification, no canon mutation. The contract bump lands in Wave 35 (v0.26.0 → v0.27.0). (8) Marathon mode continues — Wave 35 begins next (Metabolic Inlet MVP implementation, kernel_contract class 0.90 target, 3 rounds, 10-item landing list inherited verbatim from this craft §3.1). Doctrine: Wave 10 vision_recovery declared "a substrate without metabolic inlet is just an inward cache, not a metabolism" — 24 waves later, that claim has been honored doctrinally but not operationally. Wave 34 designs the verb that begins to honor it operationally. The 4 open problems remain open; the verb is a SCAFFOLD that defers each one to its operator while still producing usable surface today. Honest design beats aspirational vapor: a verb that can be invoked manually today is more valuable than 4 unsolvable open problems blocking all progress. deferred: primordia-compression (W22 W13 check: primordia count now 47 ≥ soft limit 40, over by 7 — Wave 34 added 1 more primordia file `metabolic_inlet_design_craft_2026-04-12.md`; archive sweep continues deferred to dedicated cleanup wave per W22 — running tally 48-40=8 over capacity, gap continues to widen). advisory: session_end_drift gear2 (22 entries since last meta reflection, threshold 15) — acknowledged as LOW-severity advisory; meta reflection deferred per marathon discipline.
## [2026-04-12] milestone | **Wave 35 landed (kernel_contract, contract bump v0.26.0 → v0.27.0)** — `myco inlet` MVP, the Metabolic Inlet primitive scaffold. Closes the longest-standing implementation gap in Myco's identity surface: anchor #3 (七步代谢管道) declared a Metabolic Inlet primitive in Wave 10's Vision Recovery and it has been declared-but-unimplemented for 25 waves. Wave 34 designed the scaffold (exploration class, 8 design questions, 6 attacks defended); Wave 35 implements the prescriptive 10-item brief from Wave 34 §3.1 verbatim, validating the design under implementation pressure with 9 new decisions D1–D9. Operator-deferred for all 4 open_problems §1-4 sub-problems per Wave 34 §2.4 — the verb provides the *mechanism* and the *provenance contract*, but does NOT solve cold start, trigger signals, alignment, or continuous compression. Those remain Wave 36+ friction-driven candidates. (1) `_canon.yaml` + `src/myco/templates/_canon.yaml` (mirrored): contract_version `v0.26.0 → v0.27.0`, synced_contract_version mirrored, `notes_schema.optional_fields` extended with 4 inlet_* provenance fields (`inlet_origin`, `inlet_method`, `inlet_fetched_at`, `inlet_content_hash`), `notes_schema.valid_sources` extended with `inlet`, new `notes_schema.inlet:` sub-section with `default_tag: "inlet"` so the existing `myco compress --tag inlet` chain works without operator memory burden. (2) `src/myco/notes.py` adds `inlet` to `VALID_SOURCES` + the 4 inlet_* fields to `OPTIONAL_FIELDS` (Wave 35 v0.27.0 markers in comments). (3) `src/myco/inlet_cmd.py` (NEW, ~290 LOC, 6 functions): `_project_root` (mirrors compress_cmd strict-mode resolver), `_resolve_default_tag` (reads `notes_schema.inlet.default_tag` from canon at call time, falls back to "inlet" so test fixtures swap cleanly), `_resolve_inlet_input` (single source of truth for input resolution per D5: handles file path / `--content`+`--provenance` pair / URL-error case with explicit pipe-back instruction; URL detection prefix-based on positional source per D4), `_build_inlet_meta` (constructs frontmatter with sha256 over input bytes per D9 + ISO-8601 timestamp + 4 provenance fields), `_build_inlet_body` (renders header + content; sha256 is over `content` not body per D9 — body header is presentation, not provenance), `run_inlet` (CLI dispatch with exit codes 0/2/3/5 per D3, no exit 4 because no empty cohort analog). (4) `src/myco/cli.py` adds `inlet_parser` subparser (positional optional `source`, `--content`, `--provenance`, `--tags` comma-separated, `--json`, `--project-dir`) + dispatch case after uncompress block. Mutual exclusion handled at runtime not argparse per D6 so error messages can guide operator to agent-fetch pipe pattern. (5) `src/myco/lint.py` extends `lint_notes_schema` (L10) with soft inlet provenance check: when `source=='inlet'`, the 4 inlet_* fields SHOULD be present; severity LOW per D7 to preserve grandfathering (retroactively-tagged notes don't break the substrate). (6) `tests/unit/test_inlet.py` (NEW, 5 tests) covering load-bearing paths per D8: `test_inlet_file_creates_raw_note_with_provenance` (file form D1 + D3 + D4 + provenance contract), `test_inlet_explicit_content_creates_raw_note` (D2 zero-deps URL pipe pattern + auto-detect URL provenance → method url-fetched-by-agent vs explicit-content), `test_inlet_url_form_rejected_with_clear_message` (D2 reject branch + error-message UX contract), `test_inlet_default_tag_applied_when_tags_missing` (D6 canon-driven default tag, both fallback and canon-extended paths), `test_inlet_lints_clean_under_l10` (soft check produces zero issues on freshly-inletted notes — validator/writer agreement). All 5 tests pass on first run. (7) Verification: `myco lint` 19/19 green (post boot brief regen via `myco hunger`); `pytest tests/ -q` 22/22 green (was 17, +5 in 0.23s); contract diff `v0.26.0 → v0.27.0` confirmed in both kernel + template canons. End-to-end dogfood: 3 live `myco inlet` invocations against the substrate — file form (`myco inlet docs/open_problems.md`) produced raw note `n_20260412T071356_d732` with method=file + sha256 hash; URL form (`myco inlet https://example.com/wave35-test`) correctly rejected with exit code 2 + clear instruction pointing at the agent-fetch pipe pattern; explicit-content form with URL provenance (`myco inlet --content "..." --provenance "https://..."`) produced raw note `n_20260412T071404_dbb9` with method=url-fetched-by-agent. Both dogfood notes were excreted post-verification via `myco digest --excrete` so they don't pollute the substrate. (8) Wave 35 craft `docs/primordia/inlet_mvp_craft_2026-04-12.md` (kernel_contract class, 3 rounds, 0.90 = target floor for kernel_contract). 6 attacks ran in Round 2: A (URL fetching defer to agent wrappers) defended via zero-non-stdlib-deps hard contract + security boundary (HTTP client introduces SSL/redirect/timeout/encoding/content-type detection complexity = attack surface); B (binary file handling) defended via UTF-8 decode rejection at boundary with clear error pointing operator at external preprocessing (PDFs/audio/images convert before inlet); C (5-test suite is too small) defended via per-decision boundary calibration not external benchmark — Wave 30 had 7 tests for 7 decision boundaries, Wave 35 has 5 tests for 5 boundaries; D (body header breaks sha256 chain) defended via sha256 over `content` (input bytes) NOT body bytes — verifiers re-derive from original source not note body, body header is presentation not provenance; E (call-time canon reads vs import-time) defended via test fixture swap requirement + standard pattern from compress_cmd/notes_cmd; F (LOW severity for L10 soft check) defended via "nothing to fire on yet" (zero pre-existing source=inlet notes, so soft check correctly opens at LOW and can be promoted to MEDIUM if friction emerges). 7 known limitations filed: L1 URL fetching is operator-deferred to agent wrappers (zero-deps doctrine); L2 binary handling rejected at UTF-8 boundary (no preprocessing hooks); L3 the 4 sub-problems §1-4 are NOT solved (each remains operator-deferred); L4 `--content` form does not validate non-empty/non-whitespace (feature for testing, footgun for noise); L5 body NOT byte-identical to input (D9 supersedes if future doctrine demands it); L6 filename collision resolution single-threaded (4-hex space ample for sub-second); L7 file path edge case `https-config.md` (no `./` prefix) falsely detected as URL (operators disambiguate via `./`). (9) Decisions D1–D9 captured in note `n_20260412T071337_783a` (integrated via the W32 `myco integrate` verb — fourth consecutive wave dogfooding W32's verbs after W32 + W33 + W34): D1 canon section under `notes_schema.inlet` not `system.inlet`, D2 OPTIONAL_FIELDS not REQUIRED_FIELDS (soft enforcement only), D3 exit codes 0/2/3/5, D4 prefix-based URL detection with `./` operator escape hatch, D5 _resolve_inlet_input single source of truth, D6 runtime mutual exclusion not argparse, D7 L10 severity LOW, D8 5 tests calibrated to load-bearing paths, D9 body MAY include header sha256 over input bytes only. Evidence note `n_20260412T071256_8617` (extracted via the W32 `myco extract` verb). Anchor #3 (七步代谢管道) coverage shifts: Wave 26 audit 0.65 → Wave 35 estimate ~0.80 — the primitive exists, the provenance contract is enforced, the compression chain integration is automatic via default tag; the remaining 0.20 gap is the 4 deferred sub-problems. Anchor #4 (压缩即认知) unchanged but reinforced — Wave 35 inlet's default tag completes the inlet→compress chain that the W30 compress verb made possible. Other anchors unchanged. (10) Marathon mode continues — Wave 36 begins next; per Wave 26 D3 (friction-driven ordering after doctrine alignment) NOT pre-scoped, will be decided by which surface produces friction first. Three Wave 34 §3.3 candidates remain on deck: hunger inlet_ripe advisory signal (closes part of open_problems §4), cross-reference graph for inlet provenance via inlet_origin + inlet_content_hash (closes part of §3), continuous compression hook via operator-as-daemon pattern (closes §4 fully). Doctrine: Wave 10 vision_recovery wrote "a substrate without metabolic inlet is just an inward cache, not a metabolism" — 25 waves later that claim is finally honored operationally. The substrate now has all 7 verbs of the seven-step metabolism (forage/inlet→evaluate→extract→integrate→compress→eat→excrete/prune), each with explicit Wave-number anchors back to the design crafts that justify them. The 4 open problems remain open as honest blocked work, not as features-in-disguise — this preserves the doctrine that open problems must stay visible until resolved, never quietly absorbed into "future feature" backlog. Honest scaffolding beats aspirational vapor: a verb that can be invoked manually today is more valuable than 4 unsolvable open problems blocking all progress. open_problems.md §1-4 updated with Wave 35 status: §1 (cold start) "scaffold landed but moving target unchanged", §2 (trigger signals) "scaffold landed but signal definition unchanged", §3 (alignment) "scaffold + structural evaluate gate but semantic alignment unchanged", §4 (continuous compression) "partially unblocked via existing W30/W31/W33 chain + W35 default tag, awaiting inlet_ripe advisory to close fully". deferred: primordia-compression (W22 W13 check: primordia count now 49 ≥ soft limit 40, over by 9 — Wave 35 added 1 more primordia file `inlet_mvp_craft_2026-04-12.md`; archive sweep continues deferred to dedicated cleanup wave per W22 — running tally 49-40=9 over capacity, gap continues to widen). advisory: session_end_drift gear2 (23 entries since last meta reflection, threshold 15) — acknowledged as LOW-severity advisory; meta reflection deferred per marathon discipline.
