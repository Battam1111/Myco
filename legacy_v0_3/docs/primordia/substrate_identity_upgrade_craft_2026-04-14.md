---
title: "基质身份升级：从 infrastructure 到 substrate"
type: craft
status: ACTIVE
confidence: 0.88
rounds: 1
created: 2026-04-14
tags: [identity, terminology, substrate, autopoiesis, co-evolution]
anchor: C3
---

# 基质身份升级：从 infrastructure 到 substrate

## 问题陈述

Myco 在早期文档里被定位为"与 Agent 共生的基础设施（infrastructure）"。这个词有三处缺陷：

1. Infrastructure 的语义是被动的、服务性的（路网、水管、数据库）。它暗示"被使用"，而 Myco 实际上会使用自己（basin lint 约束 basin lint，canon 约束 canon 的定义，系统用自己管理自己）。
2. Infrastructure 是空间性隐喻（"在哪"），而 Myco 的核心是时间性的（代谢节律、跨会话连续性、进化轨迹）。
3. Infrastructure 暗示静态，而 Myco 的三条不可变宪法里 C3 明确要求永恒进化。

## 新定位：substrate（基质）

Substrate 在生物学与生态学语境中承担三层含义，恰好对应 Myco 的三重特质：

| Substrate 的含义 | Myco 对应 |
|----------------|----------|
| 生物膜附着与代谢的介质 | 认知代谢循环的载体（eat, digest, condense, absorb） |
| 酶与底物的共生空间 | Agent 与 Myco 的共生场域 |
| 土壤般的生成性母体 | 从中生长出知识、技能、规则 |

## 三条哲学升级

### 升级 1：autopoiesis（自生成系统）

基础设施是外部的，基质是内部的。Maturana 与 Varela 在 1970 年代提出 autopoiesis 概念：一个系统如果它的产物同时是它的组件，就是自生成的。细胞用它制造的蛋白质维持自己的膜结构，这是生命与非生命的分界。

Myco 满足这个判据：
- Lint 系统 lint 它自己的 lint 定义（L19 检测 dimension count 漂移）。
- Canon 约束自己的 schema（L0 canon self check）。
- 进化引擎（evolve.py）可以修改进化规则本身。
- 基质用它自己生成的概念词汇（wiki 页面标题）构建跨层互联地图。

这是 strange loop：Myco 不是"为 Agent 提供服务的系统"，而是"在 Agent 的协同下持续自我生成的基质"。

### 升级 2：selective permeability（选择性通透）

"吞噬一切"是口号，真实运作是选择性吞噬。基质的身份边界由免疫系统定义：

- write surface 白名单（哪些目录可写）
- pinned prefixes（哪些历史档案不动）
- digest 的 absorption gate（转换到 extracted/integrated 必须提供 absorption proof）
- 26 维 immune lint 的交叉约束

没有边界的基质会溶解在环境里。免疫系统不是辅助模块，它定义了 Myco 之所以是 Myco。

### 升级 3：temporal organization（时间组织）

传统 infrastructure 关心空间：数据在哪、服务部署在哪、资源分配在哪。基质关心代谢节律：
- 七步管道的时间方向性（外部源 → 发现 → 评估 → 萃取 → 整合 → 压缩 → 验证 → 淘汰）
- hunger signals 的实时性（raw_backlog HIGH 反射）
- compression pressure 的累积动力学
- dead_knowledge 的时间阈值检测
- 跨会话的记忆重建（hot/warm/cold 层的时间衰减）

Bergson 的 durée（绵延）概念比空间存储更能描述 Myco 的本质：它不是时间点的序列（version snapshots），而是流动、累积、有方向的持续。

### 升级 4：co-evolutionary niche（协同进化生态位）

"Agent 使用 Myco"这个表述把两者当作使用者与工具。更精确的框架是生态位构造理论（Niche Construction Theory，Odling Smee 1996）：生物不仅适应环境，还主动改造环境形成自己的生态位，这个改造过的环境反过来塑造后代。

Agent 通过 eat, digest, condense 改造 Myco 的知识拓扑。
Myco 通过 perfusion, synaptic_context, interconnection 改造 Agent 下一步的认知形态。

这是两条纠缠的进化轨迹。"永恒进化"的主语不是 Myco 单独，而是 Agent 加 Myco 这个复合有机体。

## 对身份文档的影响

重写 `wiki/identity.md` 与 `docs/vision.md` 的身份段落时保留三条宪法（C1, C2, C3）与八条身份锚点不变，仅升级表述词汇：

- "infrastructure / 基础设施"替换为"substrate / 基质"。
- 新引入 autopoiesis, selective permeability, temporal organization, co-evolutionary niche 四个概念（可以作为 identity 的补充层级，不替换原有七条生命标准）。
- 身份演化弧线部分去除 Wave 10/26/55/54 的 Wave NN 引用，改为版本号或语义描述。

## 遗留的开放问题

L25 已经覆盖知识层, 工程层, 文档层之间的连通性，但 Agent 的认知状态（推理过程、反思痕迹、踩坑经验）目前是单向喂食到基质（notes/n_*），基质没有主动感知 Agent 状态的机制。真正的协同进化需要反向通道：基质能感知当前 Agent 的认知瓶颈并主动提示。`myco_hunger` 的 signals 是初步尝试，但它反映的是基质自身状态，不是 Agent 状态。这或许是下一轮进化的方向，本次升级先不涉及。

## 参考

- Maturana, H., & Varela, F. (1980). Autopoiesis and Cognition
- Odling Smee, F. J. (1996). Niche Construction Theory
- Bergson, H. (1896). Matière et Mémoire（durée 概念）
- Clark, A., & Chalmers, D. (1998). The Extended Mind
- docs/primordia/myco_identity_definitive_craft_2026-04-12.md（前身：Agent First 身份定义）
- docs/primordia/universal_interconnection_craft_2026-04-14.md（前身：跨层互联）

---

**Back to** [MYCO.md](../../MYCO.md)
