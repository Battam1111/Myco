<p align="center">
  <a href="https://github.com/Battam1111/Myco">
    <img src="https://raw.githubusercontent.com/Battam1111/Myco/main/assets/logo_light_512.png" width="160" alt="Myco">
  </a>
</p>

<h1 align="center">Myco</h1>

<p align="center"><b>吞噬万物。永恒进化。你只管说话。</b></p>

<p align="center">
  <a href="https://pypi.org/project/myco/"><img src="https://img.shields.io/pypi/v/myco?style=flat&cache_seconds=0" alt="PyPI"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=flat" alt="License"></a>
  <a href="https://github.com/Battam1111/Myco"><img src="https://img.shields.io/github/stars/Battam1111/Myco?style=flat" alt="Stars"></a>
  <a href="https://glama.ai/mcp/servers/Battam1111/Myco"><img src="https://glama.ai/mcp/servers/Battam1111/Myco/badges/score.svg" alt="Glama score"></a>
</p>

<p align="center">
  <a href="https://glama.ai/mcp/servers/Battam1111/Myco">
    <img src="https://img.shields.io/badge/%E5%9C%A8%20Glama%20%E4%B8%8A-%E5%8D%B3%E5%88%BB%E8%AF%95%E7%94%A8-8b5cf6?style=for-the-badge" alt="在 Glama 上即刻试用" height="36">
  </a>
</p>

<p align="center">
  <sub>Claude&nbsp;Code：<code>/plugin install myco@myco</code> &nbsp;·&nbsp; Claude&nbsp;Desktop：<code>myco-install host cowork</code> &nbsp;·&nbsp; 任意&nbsp;MCP&nbsp;host：<code>pip install 'myco[mcp]'</code></sub>
</p>

<p align="center">
  <a href="#myco-是什么">它是什么</a> · <a href="#它如何活着">如何活着</a> · <a href="#快速上手">快速上手</a> · <a href="#十九个-verb">动词</a> · <a href="#自我验证">自我验证</a>
</p>

<p align="center">
  <b>Languages:</b> <a href="README.md">English</a> · 中文 · <a href="README_ja.md">日本語</a>
</p>

---

LangChain。LangGraph。CrewAI。DSPy。Claude Code skills。OpenHands。OpenClaw。每隔几个月下一个框架又掉下来，你又迁移一次。

你的笔记也在烂。三周前读的 API 已经改了。去年写的那份文档现在是错的。你的 AI 连上周的决定都不记得。每次新对话，都是从零开始。

<br>

现在想象一套活底物。它吞噬那些框架、论文、API、代码仓库、数据集、决策、摩擦。它把这些东西保留在一张 Agent 能真正读的图里。它自己发现自己的漂移并修好。当你的工作超出了它旧的形状，它自己重塑形状。用半年。用六年。不需要迁移。

<h3 align="center">这就是 Myco。</h3>

---

## Myco 是什么

Myco 是你的 AI Agent 的活体认知底物。

Agent 读到、写入的一切，每一段代码、每一篇论文、每一个决策、每一处摩擦，都以 markdown + YAML 的形式住在你的文件系统上。文件与文件之间靠文件名互相引用，织成一张 Agent 真的在读的图。Agent 吞噬原料、消化成整合知识、用免疫系统检查自己的漂移、把学到的东西跨项目扩散；当底物的形状已经跟不上工作的形状时，它自己重塑底物。**支撑这一切运行的 kernel 本身也是一个底物**，默认可编辑，由使用它的那位 Agent 亲自维护。

不是框架。不是向量库。不是托管服务。是一个活着的文件系统，给你说话的那位 Agent 用。

想法比实现古老。真正改变的是 Agent。今天的模型终于强到可以自己维护自己的工具。所有在它之前的自维护知识系统都死在同一个地方：人跟不上了。Myco 把那个循环搬进了 Agent 自己。每一个表面、每一个 verb、每一条规则都假设维护者就是 Agent，循环里的那个人类，不再是承重结构。

## 它如何活着

你说话。Agent 听。你的两句话之间，Myco 跑一轮代谢。

- **摄入（Ingestion）。** `hunger` 问缺什么。`eat` 吃下你指向的任何东西，无论是一条路径、一个 URL，还是一段文字。`sense` 和 `forage` 扫描已有的素材。`excrete` 为那些本不该被捕获的 raw note（手滑、录错、重复）提供了带审计墓碑的安全删除。
- **消化（Digestion）。** `assimilate` 把 raw note 批量煮成整合知识。`digest` 单条升格。`sporulate` 把整合知识浓缩成可传播的提案。
- **循环（Circulation）。** `traverse` 遍历图、汇报连通性。`propagate` 把学到的扩散到下游 substrate。
- **稳态（Homeostasis）。** `immune` 按 7 条硬规则跑 25 维 lint。`senesce` 让每一次会话干净入眠。
- **演化（Evolution）。** 当底物的形状跟不上工作的形状时（缺个 canon 字段、需要新的 lint 维度、verb 得改），`fruit` 写一份三轮 craft 提案，`winnow` 把关形状，`molt` 发版换代。

19 个 verb，一份 manifest，两张脸：CLI 给你观察，MCP server 让 Agent 自己开。你什么都不用背，Agent 自己开车。

## 五条原则

- **只为 Agent 而生。** 每一个表面、每一条消息、每一个 verb 的形状，都是写给 Agent 的一手素材。不是给人类读者看的文档。
- **吞噬万物。** 摄入不设过滤。错过一个信号的代价，永远高于多吃一点。
- **形态在演化。** canon、lint 维度、verb、契约本身，全部可变，全部通过同一套受治理的 craft 循环改写。
- **没有"最终版"。** `integrated` 是状态，不是终点。今天的结论，是明天的 raw 素材。
- **菌丝网络。** 每个节点都能靠遍历连到任何其它节点。孤儿就是死组织。

## kernel 本身就是 substrate

Myco 自己的源码树就是一个 substrate。根目录有 `_canon.yaml`。`MYCO.md` 是 Agent 入口页。`docs/primordia/` 保存每一次契约升级背后的三轮 craft 文档。`src/myco/` 下的 Python 代码，是这个生态最里层的一圈。不是别人写好的只读制品。

所以正常安装路径就是 clone 源码、在源码目录里跑 `pip install -e`。使用 Myco 的那位 Agent，就是维护 Myco 的那位 Agent。它需要新的 lint 维度，就用 `myco ramify` 搭骨架、用 `myco fruit` 写提案、用 `myco winnow` 把关形状、用 `myco molt` 发版。不用 fork，不用等 PR，不用开长命 feature branch。**永恒进化。**

PyPI 作为 bootstrap 通道和库嵌入通道保留，但不是正常的安装路径。

## 快速上手

```bash
pipx run --spec 'myco[mcp]' myco-install fresh ~/myco
```

这条命令把仓库 clone 到 `~/myco`，对它跑 `pip install -e`，留给你一份可写的 kernel。然后在任何项目里 germinate 一个 substrate：

```bash
cd your-project
myco germinate . --substrate-id your-project
```

一条命令把 Myco 挂进你的 Agent host：

- **Claude Code。** 跑 `/plugin marketplace add Battam1111/Myco`，然后 `/plugin install myco@myco`。
- **Claude Desktop / Cowork。** 两步：(1) `myco-install host cowork` 写 MCP 入口；(2) 从 [GitHub releases](https://github.com/Battam1111/Myco/releases/latest) 下载 `myco-<ver>.plugin`，拖进 Claude Desktop → Settings → Plugins → Upload。Claude Desktop 会把它上传到你账号的私有 Cowork marketplace，此后每个 session 自动装 `myco-substrate` 技能。
- **其它 MCP host。** `myco-install host <cursor | windsurf | zed | vscode | openclaw | claude-desktop | gemini-cli | codex-cli | goose>`，或者传 `--all-hosts` 一键自动检测本机全部 host。
- **通过官方 MCP Registry。** 命名空间 [`io.github.Battam1111/myco`](https://registry.modelcontextprotocol.io/v0/servers?search=Battam1111)，支持命名空间自解析的客户端可以直接发现。

另外 9 个 schema 不一致的 host 片段、Python 框架 adapter（LangChain、CrewAI、DSPy、Smolagents、Agno、PraisonAI、MS Agent Framework、Claude Agent SDK）、以及库嵌入示例，全部在 [`INSTALL.md`](docs/INSTALL.md)。

## 十九个 verb

6 个 subsystem。每个 verb 都是真菌生物学术语，词义严格对应 verb 的行为。

- **Germination。** `germinate` 萌发一个新 substrate。
- **Ingestion。** `hunger`（缺什么？）、`eat`（摄入原料）、`sense`（关键词搜索）、`forage`（扫描可摄入路径）、`excrete`（带审计墓碑地安全删除 raw note）。
- **Digestion。** `assimilate`（raw 到 integrated，批量）、`digest`（单条升格）、`sporulate`（integrated 到可传播提案）。
- **Circulation。** `traverse`（遍历图）、`propagate`（发布到下游 substrate）。
- **Homeostasis。** `immune`（25 维 lint，`--fix` 尽可能机械自修）。
- **Cycle。** `senesce`（会话入眠）、`fruit`（三轮 craft）、`winnow`（把关 craft 形状）、`molt`（发版契约升级）、`ramify`（scaffold 新维度 / verb / adapter）、`graft`（substrate 本地插件管理）、`brief`（人类向状态汇总）。

每一个 verb 都住在 [`src/myco/surface/manifest.yaml`](src/myco/surface/manifest.yaml)。CLI（`myco VERB`）和 MCP tool 表面都从这份 manifest 机械派生。两张脸，同一个单源。下游 substrate 可以 `ramify` 出自己的 dimensions 或 verb 写进 `.myco/plugins/`，永远不用 fork Myco。

## 自我验证

Myco 不信任 Agent 会记住契约。它去强制。

- **25 维 lint**，分四类：*mechanical*（canon 不变式、写面、LLM 边界）、*shipped*（package 与 canon 版本对齐）、*metabolic*（raw 积压、陈旧 integrated）、*semantic*（图连通、孤儿检测）。`myco immune --fix` 尽可能机械自修。
- **7 条硬规则（R1 到 R7）** 治理每一次会话：boot ritual、session-end、sense-before-assert、eat-on-friction、cross-reference-on-creation、write-surface discipline、top-down layering。完整契约在 [`L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md)。
- **Pulse 边车。** 每个 MCP tool 响应都带一个 `substrate_pulse`，携带当前 contract version 和一条会随会话逐步升格的规则提示（R1，然后 R3，再往下走）。服务端主动推。Agent 想忘都忘不了。
- **写面强制。** 任何写到 `_canon.yaml::system.write_surface.allowed` 之外的操作，都会被 `WriteSurfaceViolation` 拒掉。纪律是机制，不是请求。

host 侧零配置。R1 到 R7 住在 MCP server 自己身上，所以每个客户端（Claude Code、Cursor、Windsurf、Zed、Codex、Gemini、Continue、Claude Desktop、OpenClaw、OpenHands）boot 时都拿到同一份契约。

## 集成

- **Claude Code。** 官方 plugin 一条命令接好 MCP、hooks、slash skills。或者手工拷 `.claude/`。
- **Cowork（Claude Desktop local-agent-mode）。** 两步：(1) `myco-install host cowork` 写 MCP；(2) 从 [GitHub releases](https://github.com/Battam1111/Myco/releases/latest) 拖 `.plugin` 到 Claude Desktop 插件上传入口。Claude Desktop 会把它上传到你账号私有的 Cowork marketplace，每个 session 自动装 `myco-substrate` 技能，Agent 见到 `_canon.yaml` 就按 R1 到 R7 走。Cowork 不暴露 hooks、不读本地 plugin dir，拖拽是唯一持久路径。完整理由见 [`INSTALL.md`](docs/INSTALL.md)。
- **任何 MCP host。** 十个通过 `myco-install` 自动化。另外九个带各自精确片段在 [`INSTALL.md`](docs/INSTALL.md)。其它客户端用 `mcp-server-myco` stdio 直接跑。
- **Python agent 框架。** LangChain、CrewAI、DSPy、Smolagents、Agno、PraisonAI、MS Agent Framework、Claude Agent SDK 全部通过 `StdioServerParameters(command="mcp-server-myco")` 消费 Myco。
- **下游 substrate。** `myco propagate` 负责发布。adapter 住在 `myco.symbionts`。

## 了解更多

[`L0_VISION.md`](docs/architecture/L0_VISION.md) · [`L1_CONTRACT/`](docs/architecture/L1_CONTRACT/) · [`L2_DOCTRINE/`](docs/architecture/L2_DOCTRINE/) · [`INSTALL.md`](docs/INSTALL.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [Issues](https://github.com/Battam1111/Myco/issues)

架构级改动作为带日期的 craft 文档落到 [`docs/primordia/`](docs/primordia/)。每次发版都先走一轮三轮辩论、再 `molt`、再由自动化 workflow 扇出到 PyPI、MCP Registry、GitHub release。

MIT · [`LICENSE`](LICENSE) · [PyPI](https://pypi.org/project/myco/) · [Releases](https://github.com/Battam1111/Myco/releases)
