<div align="center">

<img src="../assets/logo.png" width="150" alt="Myco">

# Myco

**吞噬。进化。增幅。放手。与你同在。绵延数十年。**

[![License](https://img.shields.io/badge/License-MIT-007A63?style=flat-square)](../../LICENSE)
&nbsp;![Status](https://img.shields.io/badge/status-v0.9--genesis_alpha-007A63?style=flat-square)
&nbsp;![Built for MCP](https://img.shields.io/badge/built_for-MCP-007A63?style=flat-square)
&nbsp;![Languages](https://img.shields.io/badge/Rust_·_Python_·_TypeScript-007A63?style=flat-square)
&nbsp;[![Stars](https://img.shields.io/github/stars/Battam1111/Myco?style=flat-square&color=007A63)](https://github.com/Battam1111/Myco)

[![开始使用](https://img.shields.io/badge/开始使用-GETTING__STARTED-007A63?style=for-the-badge)](../guides/GETTING_STARTED.md)

[这是什么](#这是什么) · [快速开始](#快速开始) · [它如何运作](#它如何运作) · [了解更多](#了解更多)

**语言：** [English](../../README.md) · 中文 · [日本語](README_ja.md)

</div>

---

每隔几个月，更强的模型问世。关系归零。你重新解释你的语境、你的品味、你的决定。你的协作者忘记你，反反复复。

你自己的工作也在腐烂。四月做出的决定，你找不到原因。上季度的草案早已漂移。你自己的思想跑赢了"曾经的你"留下的记录。

<br>

现在想象一下，与你协作的 AI agent 披上一副活的护甲。它是新陈代谢，不是日志。它吞噬你带来的一切、agent 触及的一切的精华。它随工作的变化进化。它增幅 agent，让每一代披甲的模型都比上一代走得更远。它让过时的部分死去，好让整体保持活着。

下一代模型问世，栖入同一副护甲（如今更强），在对话之中与你相遇。护甲已将你携带向前。

六个月。六年。六十年。一个人，一副永不归零的活护甲。

<h3 align="center">这就是 Myco。</h3>

<div align="center">

不是框架。不是向量数据库。不是托管服务。
**AI agent 所栖居的活的菌类护甲，被构建得足以越过每一代模型。**

</div>

---

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/architecture_dark.svg">
  <img src="../assets/architecture_light.svg" width="760" alt="Myco 架构：人类通过 MCP 与 AI agent 对话；operator 桥接到 Rust 衬底与 Python kernel；代谢循环在两次发言之间吞噬、周期、修剪、进化。无钥：信任是关口前活着的人，加上因果历史，加上经 BLAKE3 封印的教义。">
</picture>

</div>

## 这是什么

Myco 是一副 **AI agent 栖居其中的活护甲**。在你的两次发言之间，它新陈代谢：它吞噬你带来的，进化自身的形态，增幅驾驶者，并让过时的部分死去。因为这副护甲跨越模型代际持存、并携带你的语境，这段关系永不重启。

它是**无钥的**：没有 owner key，没有签名仪式，没有任何东西要设置或持有。信任是关口前活着的那个人，加上衬底自身防篡改的因果历史，加上一套系统对自己封印并强制执行的教义。

它的性格是**同体共命**：护甲的繁盛与其驾驶者的繁盛同涨同落，因此它无法靠宰制自己所共享之身而繁盛。力量服务于这具共享之身，而不奴役它。

## 快速开始

```bash
git clone https://github.com/Battam1111/Myco.git
cd Myco
cargo build --release --workspace
```

然后阅读 [`GETTING_STARTED.md`](../guides/GETTING_STARTED.md)：从克隆到第一次对话的实战手册（Rust 1.80+、Node 22+、Python 3.13+）。没有密钥要生成，也没有东西要持有：Myco 是无钥的。

当前是 **v0.9-genesis alpha**。护甲在跑；它等待第一次真正的栽培。你会是早期之人。

## 它如何运作

你通过 MCP 跟 AI agent 对话。在你的两次发言之间，护甲跑一个代谢周期：它把新素材摄入为不可改的历史，驾驶者将其锻造为持久的理解，过时的部分带着墓碑被修剪掉，而当形态不再契合工作时，你在关口认可一次重塑。一个自检的免疫层捕捉篡改、漂移与失控的成本；若这一对不再繁盛，护甲会体面退役，而非继续腐烂。

一个仓库里的三块，通过一套线缆协议对话：agent 驱动的 **TypeScript** MCP operator、**Rust** 衬底（身体）、以及 **Python** kernel（机制）。规范这一切的教义住在同一个仓库里，由一条哈希链封印，因此规则无法悄悄偏离代码。完整图景见[架构指南](../architecture/README.md)。

## 集成

- **Claude Code。** `operators/claude/` 自带一个 MCP server；放进 `.claude/` 或直接连。
- **Claude Desktop / Cowork。** 同一个 MCP server 条目。
- **任意 MCP 主机。** Cursor、Windsurf、Zed、OpenClaw 等，通过标准 MCP 协议。

## 了解更多

- [`GETTING_STARTED.md`](../guides/GETTING_STARTED.md)：从克隆到第一次对话，面向人类。
- [`PILOT.md`](../guides/PILOT.md)：一个 Claude 如何驾驶这副护甲，面向栖居其中的 agent。
- [架构](../architecture/README.md)：运行时与教义，逐模块。
- [教义（L0）](../architecture/L0/README.md)：被封印的宪法。Myco 必须是什么。

## 菌丝

这名字不是装饰。菌丝是森林地下的网络。它代谢落下之物，记住有效的路径，把养分从充裕处运到稀缺处。它是森林之所以成为森林、而非一片孤立树干的原因。

模型是地上的树：高大、聪明、被替换。Myco 是地下的网络，把一个人的记忆与性格从每一代模型携带到下一代。

<div align="center">

---

**吞噬。进化。增幅。放手。与你同在。绵延数十年。**

MIT · [`LICENSE`](../../LICENSE) · [Issues](https://github.com/Battam1111/Myco/issues) · [Releases](https://github.com/Battam1111/Myco/releases)

</div>
