# 传统手艺：Nuwa-Skill + Caveman 知识集成
> **Status**: ARCHIVED (compiled to formal docs)

> **日期**：2026-04-07
> **轮数**：3 轮
> **最终置信度**：~90%
> **来源项目**：[Nuwa-Skill](https://github.com/alchaincyf/nuwa-skill) + [Caveman](https://github.com/JuliusBrussee/caveman)
> **产出**：系统 v2.1 — 5 个新协议（W8-W12）+ 2 个新 log 类型 + evolution_engine 路线图更新

---

## 背景

深入研究了两个可能对系统有帮助的开源项目：

**Nuwa-Skill**：认知操作系统蒸馏器。6 通道并行研究 + 三重验证（跨域复现/预测力/独特性）提取名人思维框架。核心哲学："写不进去的部分才是护城河"。8 组件标准模板 + 矛盾分类法（temporal/domain/essential）+ 表达 DNA 量化。

**Caveman**：Token 压缩双杠杆。输出压缩 ~65% + 输入压缩 ~45%。`.original.md` 双层模式（人类编辑原始版 → 自动压缩 Agent 版 → 验证 → 失败回滚）。lite/full/ultra 三级强度。

## 提炼出 8 条可吸收改进

1. Wiki 页面标准模板（Nuwa 8 组件 → 轻量页眉页脚）
2. 矛盾分类法（Nuwa temporal/domain/essential → 简化为活跃张力标记）
3. log.md 事件类型扩展（+contradiction +validation）
4. 结构化验证标签（Nuwa 三重验证 → 简化为验证范围一维）
5. 信息密度分级加载（Caveman lite/full/ultra → 注意力提示）
6. 外部知识编译协议（Nuwa 提取方法论 → 5 步形式化）
7. .original.md 双层架构（Caveman → 暂缓，需前置条件）
8. 表达 DNA 量化（Nuwa → 暂缓，v3.0 方向）

## 辩论过程

### 攻击 1：局限标注过度
每个 wiki 都写"局限与盲点"会变成形式主义——有些局限是显而易见的事实陈述。
**修正**：改为"⚠️ 非直觉盲点"，条件触发而非必填。判断标准："新会话不知道这个会犯错吗？"

### 攻击 2：矛盾分类过复杂
技术项目大多数"矛盾"是 Bug 不是哲学张力。
**修正**：只保留 essential（活跃架构张力），temporal/domain 退化为辩论自然描述。

### 攻击 3：验证标签太重
三维验证标签让传统手艺收尾冗长，Agent 可能编造。
**修正**：三维→一维"验证范围"（在哪里验证过/没有）。

### 攻击 4：分级加载判断不准
用户第一条消息无法判断复杂度。
**修正**：退化为"注意力提示"，默认 Standard，自然升降级。

### 攻击 5：.original.md 一致性风险
无自动化工具时双层必然失同步。
**修正**：设定前置条件（压缩脚本 + Lint 时间戳检测），暂不实施。

### 攻击 6：模板一次性全改风险
**修正**：先试点 evolution_engine.md，渐进迁移。

## 最终方案

6 项立即实施（W8-W12 + log 类型），2 项记入路线图（.original v2.5 + 表达 DNA v3.0）。

**置信度**：~90%
**验证范围**：ASCC 项目单项目设计 ✅ | evolution_engine.md 模板试点 ✅ | 跨项目验证 ⚠️ 未测
