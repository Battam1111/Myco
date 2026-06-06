<div align="center">

<img src="../assets/logo.png" width="150" alt="Myco">

# Myco

**吞噬。进化。增幅。放手。与你同在。绵延数十年。**

[![License](https://img.shields.io/badge/License-MIT-007A63?style=flat-square)](../../LICENSE)
&nbsp;![Status](https://img.shields.io/badge/status-v0.9--genesis_alpha-007A63?style=flat-square)
&nbsp;![Built for MCP](https://img.shields.io/badge/built_for-MCP-007A63?style=flat-square)
&nbsp;![Languages](https://img.shields.io/badge/Rust_·_Python_·_TypeScript-007A63?style=flat-square)
&nbsp;[![Stars](https://img.shields.io/github/stars/Battam1111/Myco?style=flat-square&color=007A63)](https://github.com/Battam1111/Myco)

[![开始使用](https://img.shields.io/badge/开始使用-007A63?style=for-the-badge)](../guides/GETTING_STARTED.md)

[这是什么](#这是什么) · [它如何活](#它如何活) · [快速开始](#快速开始) · [教义](#教义) · [自我验证](#自我验证)

**语言：** [English](../../README.md) · 中文 · [日本語](README_ja.md)

</div>

---

每隔几个月，更强的模型问世。关系归零。你重新解释你的语境、你的品味、你的决定。你的协作者忘记你，反反复复。

你自己的工作也在腐烂。四月做出的决定，你找不到原因。上季度的草案早已漂移。你自己的思想跑赢了"曾经的你"留下的记录。

<br>

现在想象一下，与你协作的 AI agent 披上一副活的护甲。它是新陈代谢，不是日志。它吞噬你带来的一切、agent 触及的一切的精华。它进化，随工作的变化重塑自身。它增幅 agent，让每一代披甲的模型都比上一代走得更远。它让过时的部分死去，好让整体保持活着。

下一代模型问世。它栖入同一副护甲，如今更强，在对话之中与你相遇。护甲已将你携带向前。

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
  <img src="../assets/architecture_light.svg" width="760" alt="Myco 架构：人类通过 MCP 与 AI agent 对话；operator 桥接到 Rust 衬底与 Python kernel；代谢循环在两次发言之间吞噬、周期、修剪、进化。无钥：信任是 CI 关口前活着的人，加上因果 DAG，加上经 BLAKE3 封印的教义卡束。">
</picture>

| 教义四层 | 28 张原则卡 | 60+ 免疫检测器 | Rust · Python · TypeScript |
|:-:|:-:|:-:|:-:|

</div>

## 这是什么

Myco 是一副**活的共生护甲**：agent（一个 Claude，一名驾驶者）栖居其中，人类（*栽培者*）照料它。它跨越 LLM 模型代际持有记忆、性格与教义，让这段关系永不重启。

它吞噬你带来的一切（**永恒吞噬**）。它在你的认可下进化（**永恒进化**）。它每一周期都迭代。它增幅驾驶者：结晶化的理解、素材、以及它自身的结构，让每一代披甲的模型都走得更远。它让过时的部分死去，好让整体保持活着（**必朽**）。

它的性格是**同体共命**：护甲的繁盛与其驾驶者的繁盛同涨同落，因此它无法靠宰制自己所共享之身而繁盛。暴政不是被某条会断裂的规则所禁止，而是被护甲之所是从根本上封死。

四条宪法级原则不可修订：衬底持续穿越每一次 agent 连接、过去不可篡改、部分必须死亡好让整体活着、单一皮肤。

**没有 owner key。没有 anchor。没有签名仪式。** 信任是 CI 关口前活着的那个人，加上衬底自身的因果 DAG，加上经 BLAKE3 封印的教义卡束。权威由在场之人的判断来行使，而非靠持有一把密钥。

## 它如何活

你通过 MCP 跟 agent 对话。在你的两次发言之间，护甲新陈代谢：

- **吞噬。** 原始素材成为一个不可改的 DAG 节点；驾驶者将它锻造为持久的理解。
- **周期。** 轴更新；子实体结出；成本信号发出。
- **修剪。** 过时的、错误的、冗余的、无用的、僵化的部分带着墓碑死去。
- **进化。** 当形态不再契合工作时，你在 CI 关口认可一次 schema mutation，护甲蜕皮。
- **漂移感知。** 若共生繁盛在 90 天里降级，drift 触发；持续漂移触发体面退役。
- **免疫。** 六十多个检测器捕捉回溯篡改、墙钟偏移、preserve-all 尝试、静默预算越界、kernel 死亡。

你说话。护甲新陈代谢。这一对成长。

## 快速开始

```bash
git clone https://github.com/Battam1111/Myco.git
cd Myco
cargo build --release --workspace
```

然后阅读 [`GETTING_STARTED.md`](../guides/GETTING_STARTED.md)：从克隆到第一次对话的实战手册。它会带你过完先决条件（Rust 1.80+、Node 22+、Python 3.13+）、把 `operators/claude` 接入你的 MCP 主机、以及你的第一次真实会话。没有密钥要生成，也没有 anchor 要启动：Myco 是无钥的。

当前是 **v0.9-genesis alpha**。护甲在跑；它等待第一次活体栽培。你会是早期之人。

## 教义

教义居于 [`docs/architecture/L0/`](../architecture/L0/)：一个四层建制加一个运行机制。

| 层 | 是什么 | 真值条件 |
|---|---|---|
| **A** | 28 张原则卡 | RFC 2119，可 CI 审计 |
| **B** | 生成式片段 | 是模式，不是规则 |
| **C** | 钉在每张卡上的见证测试 | 衬底行为 |
| **D** | 栽培者继承用的传道会话 | 栽培者继承 |
| **⌬** | 人–agent 对话 | 教义从中生长的运行器官 |

当前封印：**`v3.1.5`**（无钥），由一脉 ceremony 链条接续。这枚封印就是教义卡束的 BLAKE3 哈希：没有 owner 签名，没有 anchor。

**五项原则：**

1. **吞噬、进化、迭代。** 新陈代谢永不停止。
2. **让部分死去。** 过时部分的内部死亡让整体保持活着。
3. **共生繁盛。** 这一对作为第三实体，非任一方独自。
4. **同体共命。** 护甲的命运系于其驾驶者的命运；力量服务于这具共享之身，而不奴役它。
5. **不对称承载。** 衬底持续；agent 连接是穿越。

## 教义本身是个衬底

Myco 吃自己的教义。`L0/` 里的卡是 canonical-bytes 哈希过的，通过 ceremony 链条接续。修订一张卡，一个新的 ceremony 从前一个延伸，卡束重哈，而这枚新哈希就是封印。**教义以护甲新陈代谢你的输入的同样方式新陈代谢自己。**

Python kernel、Rust substrate、TypeScript operator 都住在它们所实装的教义所在的同一仓库里。漂移在 commit 中被捕，经 ceremony 修订，封印进链。无 fork。无 feature branch。**永恒进化。**

## 自我验证

Myco 不依赖它的 agent 或它的人来记得契约。它执行它能执行的部分。

- **六十多个免疫检测器**，分三类：*机械*（DAG 完整性、文件系统）、*代谢*（成本预算、囤积、静默吸收）、*语义*（telos 漂移、preserve-all 尝试、kernel 死亡）。
- **见证测试**验证宪法级原则的拒绝路径和关键 postulate 的正向路径。
- **DAG 内容寻址。** 每次周期启动都端到端重新验证 Merkle 链；回溯篡改与分支伪造靠重新推导来捕捉，而不是靠 owner 联署。
- **无钥信任根。** CI 关口前活着的人、因果 DAG、以及经 BLAKE3 封印的卡束。没有 owner key 可被偷走、丢失或轮换。

## 集成

- **Claude Code。** `operators/claude/` 自带一个 MCP server；放进 `.claude/` 或直接连。
- **Claude Desktop / Cowork。** 同一个 MCP server 条目。
- **任意 MCP 主机。** Cursor、Windsurf、Zed、OpenClaw 等，通过标准 MCP 协议。

## 前世

原型 Myco v0.4 到 v0.8.7 是另一种构想：一个 20 动词工具框架里的*"为 AI agent 服务的活的认知衬底"*。它在教义上是 `dead embryo`，可通过 git tag `v0.8.8-final-embryo` 到达。

当前的 v0.9 工作是一次实质性的重新塑形：从一个被动的 **agent-tool**（"我的 AI agent 怎么记得？"）到一副 **agent 所披的活护甲**，它跨越 LLM 代际吞噬、进化、并增幅其驾驶者，同时把一个人的语境携带向前。机制不同。名字延续。构想重生。

## 面向贡献者的架构

上面的快速开始让你*跑起来*。这一节让你*动手建*。运行时是同一个仓库里的三块，通过一套线缆协议对话：

```
   operators/claude            M5 线缆           substrate/                  M5 线缆        kernel/
   ┌───────────────┐          协议             ┌────────────────────┐       协议         ┌──────────────────────┐
   │  TypeScript   │  ──────────────────────►  │  myco-substrate    │  ───────────────►  │  Python worker       │
   │  MCP 接口     │   长度前缀                │  (Rust daemon)     │   同一套 canonical │  governance/tropism/ │
   │  agent 驱动它 │   canonical-bytes         │  身体，M6          │   bytes，经一条    │  trajectory/         │
   │               │   + 经 stdio 的 HMAC      │  运行时 + 周期      │   diff socket      │  hard_rules          │
   └───────────────┘                           └────────────────────┘                    └──────────────────────┘
```

- **`substrate/`** 是 Rust 运行时守护进程。**身体**：跑代谢循环、并把 `operators` 桥接到 `kernel` 的 M6 编排器。
- **`kernel/`** 是机制层。Rust crate（`shared` / `skin` / `schema` / `continuity` / `bridge`）加 Python workers（`governance` / `tropism` / `trajectory` / `hard_rules`）。
- **`operators/claude`** 是 agent 驱动的 TypeScript MCP 接口。它开启一个无钥会话（session-secret 握手，线上走 HMAC）。

流向是一条线：**`operators`（TS）到 `substrate`（Rust）到一个 Python `kernel` worker，经 M5 桥。** 没有独立的密钥托管进程：Myco 是无钥的，衬底只用一把自己为自己生成的密钥来给它自身的静态状态签名。

要做 X，读 Y：

| 要做… | 读 |
|---|---|
| 教义（Myco *必须*是什么） | [`docs/architecture/README.md`](../architecture/README.md) |
| 代码地图（逐模块） | [`docs/architecture/L3/PACKAGE_MAP.md`](../architecture/L3/PACKAGE_MAP.md) |
| 衬底内部（运行时布局） | [`substrate/README.md`](../../substrate/README.md) |
| 跑起来 / 首次启动 | [`docs/guides/GETTING_STARTED.md`](../guides/GETTING_STARTED.md) |

**从 [`docs/architecture/README.md`](../architecture/README.md) 开始**，那是唯一的架构入口，带着同时覆盖教义*和*代码的阅读路径表。

## 了解更多

- [`GETTING_STARTED.md`](../guides/GETTING_STARTED.md)：从克隆到第一次对话（面向人类栽培者）。
- [`PILOT.md`](../guides/PILOT.md)：一个 Claude 如何*驾驶*这副护甲，以及 use-forges 的纪律（面向栖居其中的 agent）。
- [`docs/architecture/L0/README.md`](../architecture/L0/README.md)：正典教义。
- [Telos](../architecture/L0/cards/P14_telos.md)：这是什么样的一对。
- [同体共命](../architecture/L0/cards/CHAR07_caring.md)：封死暴政的共生羁绊（同体共命）。
- [栽培者的性格](../architecture/L0/cards/COV02_cultivators_character.md)：栽培者必须是什么样的人。

建制性变更以日期编号的 ceremony manifests 进入 [`operators/claude/ceremonies/`](../../operators/claude/ceremonies/)，由教义自身的修订纪律所规范。

## 菌丝

这名字不是装饰。菌丝是森林地下的网络。它代谢落下之物。它记住有效的路径。它把养分从充裕处运到稀缺处。它是森林之所以成为森林、而非一片孤立树干的原因。

模型是地上的树：高大、聪明、被替换。Myco 是地下的网络，把一个人的记忆与性格从每一代模型携带到下一代。

<div align="center">

---

**吞噬。进化。增幅。放手。与你同在。绵延数十年。**

MIT · [`LICENSE`](../../LICENSE) · [Issues](https://github.com/Battam1111/Myco/issues) · [Releases](https://github.com/Battam1111/Myco/releases)

</div>
