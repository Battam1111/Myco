# Myco Evolution Engine — Metabolic Self-Evolution (v3.0)

> **文档修订**: 3.0 (2026-04-12, Post-Metamorphosis rewrite)
> **前身**: v2.1 的四齿轮（Gear 1-4）架构已在 Metamorphosis 中被替代

## 核心哲学

Myco 是 Agent-First 的共生认知有机体。进化不是手动触发的——它是有机体的持续代谢过程。旧的四齿轮模型要求人类换挡；新的代谢模型由 Agent + Substrate 自主运转。

**三层学习**（不变）：
1. **Single-loop**（行为修正）：hunger 信号检测矛盾 → Agent 自动修复
2. **Double-loop**（假设重塑）：predict_knowledge_needs 发现模式 → 改进 skills
3. **Meta-loop**（进化规则更新）：evolve.py 变异 skills → constraint gates 选择 → 更好的规则替代旧规则

---

## 代谢循环（取代旧四齿轮）

```
Boot: hunger(execute=true)
  → 检测信号 → 自动执行 actions
  → 参考 sprint-pipeline → Think/Plan/Build/Review/Test/Ship/Reflect
  → 参考 discovery-loop → 检测知识缺口 → 搜索 → 摄入
  → 参考 learning-loop → 捕获执行学习
  → evolve.py → 变异表现不佳的 skills → 约束门检验 → 好的变异存活
```

### 旧模型 → 新模型映射

| 旧（四齿轮） | 新（代谢循环） | 自动化程度 |
|------------|-------------|-----------|
| Gear 1 摩擦感知 | `hunger signals`（17+ 种信号自动计算） | 完全自动 |
| Gear 2 会话反思 | `myco_reflect` 自动创建 execution-learning note | 完全自动 |
| Gear 3 里程碑回顾 | `predict_knowledge_needs` 分析会话历史 | 完全自动 |
| Gear 4 跨项目蒸馏 | `evolve.py` + cross-instance skill transfer | 框架就位，opt-in |

### 关键区别

**旧模型**：人类手动换挡（"现在做 Gear 2 反思"）
**新模型**：有机体自主运转（hunger 检测 → actions 推荐 → execute=true 自动执行）

**旧模型**：四个离散档位，顺序推进
**新模型**：持续代谢循环，所有阶段在每个 session 都可能触发

---

## 五个操作技能

进化引擎现在通过 `skills/` 目录的操作技能实现：

| 技能 | 职责 | 自动化 |
|------|------|-------|
| `metabolic-cycle.md` | Boot ritual: hunger → digest → compress → discover → evolve | hunger(execute=true) 自动 |
| `sprint-pipeline.md` | 开发循环: Think→Plan→Build→Review→Test→Ship→Reflect | Agent 遵循 |
| `discovery-loop.md` | 主动觅食: detect gaps → search → evaluate → ingest | hunger 信号触发 |
| `agent-routing.md` | 模型选择: task type → opus (all tasks) | Agent 读取 |
| `learning-loop.md` | 执行学习: capture what worked/failed → skill-ify | myco_reflect 自动 |

---

## 自我进化机制（evolve.py）

### 技能变异
Agent 提供 `llm_fn`，Myco 提供脚手架：
1. `parse_skill()` — 分离 YAML frontmatter（不可变）和 body（可变）
2. `mutate_skill()` — Agent 通过 llm_fn 生成变异体
3. `check_gates()` — 硬门拒绝无效变异（frontmatter 改变 / body 空 / 密钥泄漏 / 体积膨胀）
4. `evaluate_variant()` — 多维评分（clarity/completeness/conciseness/correctness）
5. 好的变异替代原 skill，git commit

### 进化后的技能管理
好的变异替代原 skill 并保存在 `skills/.evolved/` 目录。
Agent 通过 `myco_evolve_list` 查看进化历史和当前代数。

---

## 配置

```yaml
# _canon.yaml
system:
  evolution:
    enabled: false              # opt-in
    skill_success_threshold: 0.7
    min_sessions_before_evolve: 5
    max_mutations_per_cycle: 1
    require_git_clean: true
  
  skill_schema:
    required_sections: ["When to Execute", "Steps"]
    optional_sections: ["Input", "Output", "Feeds", "Constraints"]
    contracts_enabled: false     # future: validate skill-to-skill contracts
```

---

## 与旧文档的关系

本文档（v3.0）完全替代 v2.1 的四齿轮描述。v2.1 的内容保留在 git 历史中（immutable history doctrine），但不再是当前的有效架构。

进化的设计决策记录：`docs/primordia/myco_identity_definitive_craft_2026-04-12.md`（第四永久锚点）。

---

## See Also

- [skills/metabolic-cycle.md](../skills/metabolic-cycle.md) -- Boot ritual 技能：hunger -> digest -> compress -> discover -> evolve 的具体步骤
- [src/myco/evolve.py](../src/myco/evolve.py) -- 技能变异实现：parse_skill / mutate_skill / check_gates / evaluate_variant
- [docs/agent_protocol.md](agent_protocol.md) -- Agent 协议：MCP 工具契约（myco_hunger 等的形式定义）
- [docs/architecture.md](architecture.md) -- 技术架构：四支柱全景 + Appendix F 结构智能子系统
- [docs/theory.md](theory.md) -- 理论基础：三环学习（Single/Double/Meta-loop）的认知科学根基
- [docs/vision.md](vision.md) -- 愿景：从 v0.x 到 v1.0 的进化路径
- [docs/open_problems.md](open_problems.md) -- 未解难题：Inlet 冷启动、压缩工程等进化引擎相关盲点
- [_canon.yaml](../_canon.yaml) -- 进化配置：`system.evolution` 节（enabled/threshold/max_mutations）
- [docs/primordia/myco_identity_definitive_craft_2026-04-12.md](primordia/myco_identity_definitive_craft_2026-04-12.md) -- 第四永久锚点设计决策
- [docs/primordia/anchor_agentfirst_revision_craft_2026-04-12.md](primordia/anchor_agentfirst_revision_craft_2026-04-12.md) -- Agent-First mutation-selection 内化决策
