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
  <a href="#开始">开始</a> · <a href="#它能做什么">能力</a> · <a href="#凭什么不一样">差异</a> · <a href="#架构">架构</a>
</p>

<p align="center">
  <b>Languages:</b> <a href="README.md">English</a> · 中文 · <a href="README_ja.md">日本語</a>
</p>

---

2024 年你用 LangChain。2025 年有人说 LangGraph 更好。然后是 CrewAI。然后是 DSPy。然后是 Hermes。每个月都有人告诉你"这个才是最好的框架"。你花在挑工具上的时间，比你用任何一个工具做正事的时间都长。

不只是框架。论文、博客、最佳实践、新模型、新 API、新范式——每一天都在刷新。你关注了 50 个 repo，读了 3 个。你收藏了 200 篇文章，看完了 10 篇。你的笔记软件里有 500 条笔记，上次整理是三个月前。

你不是不努力。**是这个世界已经快过任何人能跟上的速度了。**

更扎心的是——你辛辛苦苦整理的那些笔记、那些经验、那些"上次怎么做的"——它们正在腐烂。三周前记下来的那个 API 调用方式，版本变了。上个月总结的最佳实践，社区已经推翻了。你的知识库越来越大，但里面有多少还是对的？没人知道。**没有任何东西在帮你检查。**

你的笔记不会告诉你"这条已经过时了"。你的收藏夹不会自动把重复的合并掉。你的 AI 不记得你上周做过什么决定。每开一个新对话——一切从零开始。

<br>

现在想象另一种活法。

你不整理笔记。你不比较框架。你不追论文。你不给 AI 反复讲解项目背景。你像个白痴一样只说人话。

但六个月后，你的 AI 比任何人的都聪明。它了解你所有项目的完整历史。它自动吞噬了你领域里最新的论文和工具。它自己发现了知识盲区并补上了。它自己检查了所有旧知识还对不对——不对的，已经扔了。它甚至改写了自己的工作规则，因为旧规则不够好了。

<h3 align="center">这是 Myco。</h3>

---

## 开始

```bash
git clone https://github.com/Battam1111/Myco.git
cd Myco && pip install -e ".[mcp]"
myco seed --auto-detect my-project
```

三行命令。自动检测你的环境——Claude Code · Cowork · Cursor · VS Code · Codex · Cline · Continue · Zed · Windsurf——检测到哪个配哪个，一次全部配好。

可编辑安装——整个系统都能改，包括引擎本身。不改也行，它自己会进化。

## 它能做什么

- 🧬 **吞噬一切** — 论文、代码、博客、对话——喂给它任何东西，它消化成自己的能力，不是存成文件
- 🛡️ **自我体检** — 自动检查知识有没有过时、有没有矛盾、有没有遗漏，不用你操心
- 💀 **该死的会死** — 过时的知识被自动检测并清除。知识系统没有排泄功能 = 肿瘤
- 🔄 **永恒进化** — 不只是内容在进化，连引擎自己的规则都在变异。整个系统是活的
- 🍄 **万物互联** — 每一个文件都是菌丝网络的节点，知识不是一条条孤立的记录，是一张越来越密的网
- 🤖 **你只管说话** — 19 个工具全自动。人类不需要懂任何技术细节

## 凭什么不一样

|  | 存起来就完了 | 编译一下就完了 | **Myco** |
|---|---|---|---|
| 喂进去之后 | 存着 | 整理一下 | **消化、验证、压缩、连接、排泄** |
| 知识过时了 | 没人管 | 没人管 | **自动检测，自动清除** |
| 知识越来越多 | 越来越臃肿 | 越来越臃肿 | **越来越精炼** |
| 新工具出来了 | 你手动切换 | 你手动迁移 | **它自动吞噬新工具的精华** |
| 时间越久 | 越乱 | 越旧 | **越聪明** |

## 架构

```
你（说人话）
  ↓
AI Agent（思考、执行）
  ↓ 自动连接
Myco（吞噬、消化、验证、进化）
  ├── 知识原子（有生命周期，该死会死）
  ├── 精炼知识（从原子中提纯的长期知识）
  ├── 技能（可自我进化的操作规程）
  ├── 引擎代码（可编辑，可变异——对，连代码自己都能进化）
  └── 免疫系统（知识腐烂了？它自己会发现，自己会处理）
```

三个角色：你给方向，Agent 给智能，Myco 给记忆和进化。缺一不可。

## 参与贡献

```bash
git clone https://github.com/Battam1111/Myco.git
cd Myco && pip install -e ".[mcp,dev]"
pytest tests/
```

详见 [CONTRIBUTING.md](CONTRIBUTING.md) · MIT — [LICENSE](LICENSE)
