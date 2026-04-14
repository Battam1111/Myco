<p align="center">
  <a href="https://github.com/Battam1111/Myco">
    <img src="https://raw.githubusercontent.com/Battam1111/Myco/main/assets/logo_light_512.png" width="160" alt="Myco">
  </a>
</p>

<h1 align="center">Myco</h1>

<p align="center"><b>吞噬一切。永恒进化。你只管说话。</b></p>

<p align="center">
  <a href="https://pypi.org/project/myco/"><img src="https://img.shields.io/pypi/v/myco?style=flat" alt="PyPI"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=flat" alt="License"></a>
  <a href="https://github.com/Battam1111/Myco"><img src="https://img.shields.io/github/stars/Battam1111/Myco?style=flat" alt="Stars"></a>
</p>

<p align="center">
  <a href="#开始">开始</a> · <a href="#日常用法">日常</a> · <a href="#它能做什么">能力</a> · <a href="#凭什么不一样">差异</a> · <a href="#架构">架构</a> · <a href="#生态集成">生态</a>
</p>

<p align="center">
  <b>Languages:</b> <a href="README.md">English</a> · 中文 · <a href="README_ja.md">日本語</a>
</p>

---

2024 年你用 LangChain。2025 年有人说 LangGraph 更好。然后是 CrewAI。然后是 DSPy。然后是 Hermes。每个月都有人告诉你"这个才是最好的框架"。你花在挑工具上的时间，比你用任何一个工具做正事的时间都长。

不只是框架。论文、博客、最佳实践、新模型、新 API、新范式，每一天都在刷新。你关注了 50 个 repo，读了 3 个。你收藏了 200 篇文章，看完了 10 篇。你的笔记软件里有 500 条笔记，上次整理是三个月前。

你不是不努力。**是这个世界已经快过任何人能跟上的速度了。**

更扎心的是，你辛辛苦苦整理的那些笔记、那些经验、那些"上次怎么做的"，它们正在腐烂。三周前记下来的那个 API 调用方式，版本变了。上个月总结的最佳实践，社区已经推翻了。你的知识库越来越大，但里面有多少还是对的？没人知道。**没有任何东西在帮你检查。**

你的笔记不会告诉你"这条已经过时了"。你的收藏夹不会自动把重复的合并掉。你的 AI 不记得你上周做过什么决定。每开一个新对话，一切从零开始。

<br>

现在想象另一种活法。

你不整理笔记。你不比较框架。你不追论文。你不给 AI 反复讲解项目背景。你像个白痴一样只说人话。

但六个月后，你的 AI 比任何人的都聪明。它了解你所有项目的完整历史。它自动吞噬了你领域里最新的论文和工具。它自己发现了知识盲区并补上了。它自己检查了所有旧知识还对不对，不对的，已经扔了。它甚至改写了自己的工作规则，因为旧规则不够好了。

<h3 align="center">这是 Myco。</h3>

---

## 开始

**默认就是可编辑安装。** Myco 自己会变异——skill 自己改写，规则自己进化，引擎本身就是 substrate。从 PyPI 锁定版本安装 = 把自己冻结在某个快照；可编辑安装 = 每一次变异都直接落到你的工作树，零成本继承。这就是 Myco 的全部意义。两种装法都**零配置**——Myco 在首次进入新项目时**自动播种** substrate，不用你记 `myco seed`。

**第一步——clone 并可编辑安装引擎：**

```bash
git clone https://github.com/Battam1111/Myco.git
cd Myco && pip install -e ".[mcp]"
```

一条命令，所有 host 共用。引擎代码就在你的 clone 里，原地变异；`git pull` 就能拿到上游的变异，不需要重装。

**第二步——接到你的 agent 上。**

**Cowork / Claude Code**——plugin 打包文件就在 repo 里：

```bash
# clone 之后：
# - Cowork：把 plugin/myco-v0.3.3.plugin 拖进去
# - Claude Code：`/plugin install plugin/myco-v0.3.3.plugin`
```

打开任何项目。`SessionStart` hook 会触发 `myco hunger --execute`，首次运行时静默在项目目录里长出一份最小 substrate。之后每一个代谢动词——`eat` / `digest` / `reflect` / `immune`——开箱即用。

**其他任何讲 MCP 的 agent**——Cursor / Continue / Zed / Codex / Cline / Windsurf / VS Code / …：

```bash
myco seed --auto-detect my-project                  # 自动检测并一次性配好所有 host
```

`myco seed` 扫描你机器上所有支持的 host，把对应的配置文件都写好。目前支持 9 种，生态扩张会继续增加。

**想要锁定版本？** `pip install 'myco>=0.3.3'` 也行，但你放弃了"工作树里原地变异"这个特性。只在你把 Myco 当稳定依赖、而不是活 substrate 来用时才选这条路。

**逃生舱**。`MYCO_NO_AUTOSEED=1` 关闭首次接触的静默播种；`MYCO_PROJECT_DIR=/path/to/shared/substrate` 从"每项目一份 substrate"切换成"全局共享一份"。

## 日常用法

装好之后，大部分时候你不需要意识到 Myco 的存在——你的 agent 会通过 MCP 工具自己驱动它。但有六个动词值得知道：

| 你说 / 打 | 它做什么 |
|---|---|
| `myco hunger` | 健康仪表盘：raw 笔记、陈旧知识、待消化队列、信号。加 `--execute` 自动修复。 |
| `myco eat <内容>` | 把一条决策、洞见、摩擦点，或外部素材，当作 raw 笔记捕获进来。 |
| `myco digest <id>` | 把一条成熟的 raw 笔记提升为长期知识（wiki / MYCO.md / 代码）。 |
| `myco search <查询>` | 在整个 substrate 上做语义 + 结构搜索。 |
| `myco reflect` | 沉淀一次会话的学习。上下文压缩时自动运行。 |
| `myco immune --fix` | 29 维一致性 lint + 自动修复。会话结束时自动运行。 |

六个动词同时都是 MCP 工具（`myco_hunger`、`myco_eat`、……），agent 可以直接调。一共 25 个工具，完整列表见 [`docs/agent_protocol.md`](docs/agent_protocol.md)。

## 它能做什么

- 🧬 **吞噬一切**。论文、代码、博客、对话，喂给它任何东西，它消化成自己的能力，不是存成文件。
- 🛡️ **自我体检**。每次会话结束跑 29 维免疫 lint，陈旧事实、断裂交叉引用、互相矛盾——全部机械检测、机械修复。
- 💀 **该死的会死**。长期没人碰、没人读、终态状态的笔记被自动排泄。知识系统没有排泄功能 = 肿瘤。
- 🔄 **永恒进化**。不只是内容在进化，连引擎自己的规则、技能、工作流程都在变异。整个系统是活的。
- 🍄 **万物互联**。每一个文件都是菌丝图的节点，孤儿笔记被自动连接。知识不是孤立的记录，是一张越来越密的网。
- 🤖 **你只管说话**。25 个 MCP 工具、13 条操作原则、全自动。人类不需要懂任何技术细节。

## 凭什么不一样

|  | 存起来就完了 | 编译一下就完了 | **Myco** |
|---|---|---|---|
| 喂进去之后 | 存着 | 整理一下 | **消化 → 验证 → 压缩 → 连接 → 排泄** |
| 知识过时了 | 没人管 | 没人管 | **免疫 lint 捕获，自动修复** |
| 知识越来越多 | 越来越臃肿 | 越来越臃肿 | **越来越精炼——原子压缩成长期真理** |
| 新工具出来了 | 你手动切换 | 你手动迁移 | **它自动吞噬新工具的精华** |
| 打开全新项目 | 白板一块 | 白板一块 | **自动播种。会话启动时 substrate 已经活着。** |
| 时间越久 | 越乱 | 越旧 | **越聪明** |

## 架构

```
你（说人话）
  │
  ▼
AI Agent（思考、执行）        ←──────┐
  │   通过 MCP 自动连接              │
  ▼                                │
Myco substrate                     │
  ├── notes/             知识原子，有生命周期（raw → digesting → extracted → integrated → excreted）
  ├── wiki/              从原子中提纯的长期知识
  ├── _canon.yaml        所有数字、名字、路径的唯一真相
  ├── skills/            可自我进化的操作规程
  ├── src/myco/          引擎代码（可编辑、可变异——对，连这些代码都能进化）
  └── 免疫系统          29 维一致性 lint，会话结束自动修复
  │                                │
  └───────── 代谢回路 ──────────────┘
             (eat → digest → reflect → immune → prune)
```

三个角色：**你**给方向，**agent** 给智能，**Myco** 给记忆和进化。三者缺一不可。

代谢回路持续运行。`SessionStart` → `hunger --execute` 浮现需要关注的东西；你每做一个决策立刻被 `eat`；成熟的 raw 笔记 `digest` 成 wiki；`PreCompact` → `reflect` + `immune --fix` 在上下文压缩前沉淀；死知识被 `prune`。无限循环。

## 生态集成

**9 个 agent 被 `myco seed --auto-detect` 自动识别**：

| Cowork | Claude Code | Cursor | VS Code | Codex | Cline | Continue | Zed | Windsurf |
|---|---|---|---|---|---|---|---|---|

**Plugin 包**（Cowork + Claude Code）：单个 `myco-v0.3.3.plugin` 文件里打包了 MCP 服务器、8 个 skill（`myco:boot` / `:eat` / `:digest` / `:hunger` / `:reflect` / `:search` / `:observe` / `:absorb`）、两个 hook（`SessionStart`、`PreCompact`，强制执行硬合同）。文件就在 repo 里，路径 `plugin/myco-v0.3.3.plugin`——clone 一次，在 Cowork 或 Claude Code 里装上即可。

**MCP 服务器**：`python -m myco.mcp_server`——stdio 服务器，暴露全部 25 个工具。标准 MCP 协议，任何合规 host 都能用。

**硬合同**（自动强制执行）：
1. 每个会话以 `myco_hunger(execute=true)` 开始——SessionStart hook。
2. 每个会话以 `myco_reflect` + `myco_immune(fix=true)` 结束——PreCompact hook。
3. 对项目的任何事实性断言前，先 `myco_sense`。
4. 每个决策 / 洞见 / 摩擦点立刻 `myco_eat`，不攒到会话末。
5. 新建任何文件后，补上交叉引用（孤儿 = 死知识）。
6. 只写入 `_canon.yaml::system.write_surface.allowed` 里列出的路径。

第 1、2 条是机械执行。第 3-6 条是 agent 纪律，由免疫 lint L26–L28 维度浮现。

## 常见问题

**`ModuleNotFoundError: No module named 'myco'`**——plugin 的 MCP / hook 所用的 Python 环境里没装引擎。在该环境里从 Myco clone 跑 `pip install -e ".[mcp]"`（或锁定版本 `pip install 'myco>=0.3.3'`）。

**agent 说 "Myco 源码没挂载"**——agent 推理出了 bug。Myco 是 PyPI 包，不需要 clone 任何源码树。把 agent 指向 `$CLAUDE_PROJECT_DIR/_canon.yaml` 就行。

**`SessionStart` hook 超时**——substrate 特别大（1 万+ 笔记、菌丝图密集）可能超过 60s 默认。在 `hooks/hooks.json` 里调大 `timeout`，或跑 `myco hunger --fast`。

**空目录里自动播种被拒**——这是故意的。Myco 拒绝在缺少任何项目标记（`.git`、`pyproject.toml`、`package.json`、`README.md`、……）的目录里播种，以免污染 home / 系统目录。加一个标记文件，或显式 `myco seed --level 1`。

## 参与贡献

```bash
git clone https://github.com/Battam1111/Myco.git
cd Myco && pip install -e ".[mcp,dev]"
pytest tests/                # 覆盖每个动词和维度的单元测试
myco immune --project-dir .  # 用 Myco 自己的免疫系统 lint 自己
```

Issues、PR、新的 host adapter 都欢迎。Kernel 层改动怎么提案和评审见 [`CONTRIBUTING.md`](CONTRIBUTING.md)、[agent 协议](docs/agent_protocol.md)、[craft 协议](docs/craft_protocol.md)。

MIT · [`LICENSE`](LICENSE) · [PyPI](https://pypi.org/project/myco/) · [Releases](https://github.com/Battam1111/M