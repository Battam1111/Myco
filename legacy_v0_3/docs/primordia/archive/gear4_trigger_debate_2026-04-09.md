# Gear 4 触发内化方案 — 传统手艺辩论记录
> **Status**: ARCHIVED (compiled to formal docs)

> **日期**：2026-04-09
> **状态**：[ARCHIVED]
> **置信度**：~88%
> **触发**：用户 Gear 3 观察——Gear 4 触发依赖 agent 认知自律，与 Myco "教 agent 思考"的定位矛盾

---

## 核心问题

Gear 4（跨项目蒸馏）当前触发条件 = "agent 自己识别出通用模式"。这是认知性触发，在 agent 深度工作时优先级被自然压低。ASCC 实战中，Gear 4 两次都是用户提醒后才执行。

**根因**：苛求 agent 认知自律，而不是苛求 Myco 系统结构本身创造触发条件。

---

## 在线调研

1. **Self-Evolving Agents Survey**（EvoAgentX）："when to evolve"区分 intra-task（工作中反思）vs inter-task（任务间整合）。Gear 4 当前是 inter-task at project end，需要推向 intra-task triggered by anomaly。

2. **Metacognitive Capabilities**（emergentmind.com）："并非所有认知活动都触发元认知评估——只有异常才触发。" Knowledge compilation 标准 = "expensive multi-step reasoning"。

3. **Cognitive Design Patterns**（arxiv 2505.07087）：Meta-Cognitive Layer 的职责是"观察 agent 如何思考，测量信心和风险，决定何时反思"——结构性方案，非意志力方案。

**关键洞察**：触发信号应从"agent 判断是否通用"（主观）转为"工作本身的可观测属性"（客观）。

---

## 六轮辩论摘要

### R1 初始提案
S1: Gear 1→4 耦合（每条 friction 问"通用？Y/N"）
S2: MYCO.md 热区放触发清单
S3: Session-end 必答 Gear 4 扫描

### R2 自我攻击
- S1 在认知负荷峰值追加开放判断→形式化/敷衍风险
- S2 "可见"≠"执行"，触发认知性质不变
- S3 会话结束时上下文已冷，且上下文压缩可能先于 session-end

### R3 调研交叉验证
→ 异常驱动 + 可观测属性（见上）

### R4 重构方案（anomaly-driven trigger）

**客观可观测异常信号**：
1. 迭代次数 ≥ 2（问题尝试了两次以上才解决）
2. 新模式创建（创建了之前不存在的 helper/协议/模板）
3. 同类 friction ≥ 2（同一类别本会话出现两次以上）

**三层机制**：

| 层 | 机制 | 成本 | 位置 |
|----|------|------|------|
| 层 1 | 异常标记：满足客观条件→log 条目末尾 `→ g4-candidate` | ~5 秒 | Gear 1 协议扩展 |
| 层 2 | Session-end sweep：扫描 g4-candidate，写入 Myco 或标注 g4-pass | ~2 分钟 | 会话结束 checklist |
| 层 3 | 热区一句话：被动可见性 | 0 | MYCO.md 行为准则 |

### R5 攻击重构
- ≥2 阈值武断？→ 启动阈值，Meta-loop 可调；ASCC 实战 3/3 命中
- eureka moment 不来自 friction？→ Gear 2 反思覆盖；g4-candidate 覆盖高频路径
- 上下文压缩先于 sweep？→ 标记已在 log.md 持久化，下一会话可补

### R6 最终评估
置信度 ~88%。核心差异：从"这通用吗？"（主观）→"这花了几轮？"（客观）。

---

## 被拒方案

| 方案 | 拒绝原因 |
|------|---------|
| 每条 friction 追加"通用？Y/N" | 认知负荷峰值+形式化风险 |
| 自动脚本扫描 log | v0.x 过度工程化 |
| 单独 Gear 4 日志文件 | 碎片化，统一 log.md 更佳 |
| 发现当场即时蒸馏 | 打断工作流，即时判断通用性准确率低 |

---

## 执行计划

1. `Myco/docs/evolution_engine.md` — Gear 1 协议新增异常标记规则 + Gear 4 新增 g4-candidate sweep
2. `Myco/templates/MYCO.md` — 行为准则 +1 行 Gear 4 意识 + 会话结束 +1 步 sweep
3. OPASCC 侧同步更新（CLAUDE.md / WORKFLOW.md）
4. log.md 辩论记录
