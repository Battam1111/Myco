---
type: craft
created: 2026-04-14
status: active
scope: knowledge-interconnection
---

# Synaptogenesis — 突触生成系统

## 问题陈述

Myco 有 mycelium 图谱查询能力（backlinks/orphans/clusters），但缺乏**编织保障**——没有机制确保新知识在写入时被正确编织进现有网络。

`_auto_link_note` 是唯一的自动编织点，但覆盖面窄（仅 eat-time，仅 tag→note 匹配，不触及 wiki↔wiki 互联）。

类比：神经元存在但不形成突触 = 孤立的知识岛。

## 设计原则

### P1: Bitter Lesson 合规
工具提供邻域上下文（"这些页面存在，它们之间的链接关系是这样"），Agent 决定在哪里建立新连接。

### P2: 利用现有触点
不加新工具。在 digest Phase 1（Agent 决策点）和 Phase 3（seal 后）注入突触上下文。

### P3: 分层保障
- **编织前**：digest Phase 1 提供邻域 → Agent 自然考虑交叉引用
- **编织后**：seal 返回 weaving hint → Agent 检查是否遗漏
- **审计**：L24 immune 检测孤立 wiki 页面
- **信号**：hunger `weak_synapses` 主动告警
- **自动**：_auto_link_note 增强为 content-based 匹配

### P4: 仿生命名
- `synaptogenesis`：突触生成——新神经元与周围网络建立连接的过程
- `synaptic_context`：突触上下文——某个节点在网络中的邻域状态
- `weak_synapses`：弱突触——连接不足的知识节点

## 架构

```
              ┌─── digest Phase 1 ───┐
              │ note content          │
              │ + synaptic_context:   │   ← Agent 看到邻域，自然编织
              │   wiki 页面及其互联   │
              │   当前 absorption_site│
              │   候选的链接关系      │
              └───────────────────────┘
                        │
                     Agent 写入
                        │
              ┌─── digest Phase 3 ───┐
              │ seal 成功             │
              │ + weaving_hint:       │   ← Agent 检查是否漏链
              │   absorption_site 的  │
              │   当前连接状态        │
              └───────────────────────┘
                        │
              ┌─── immune L24 ────────┐
              │ 扫描所有 wiki 页面    │   ← 审计层
              │ 检测孤立/弱连接页面   │
              └───────────────────────┘
                        │
              ┌─── hunger signal ─────┐
              │ weak_synapses:        │   ← 主动告警
              │ wiki 页面无跨页引用   │
              └───────────────────────┘
```

## compute_synaptic_context() 规格

**输入**: project_root
**输出**: 每个 wiki 页面的连接状态（谁链向它、它链向谁）

这个函数复用 `mycelium.build_link_graph()` 的输出，只提取 wiki 子图。
不做推荐，不排序——Agent 自己判断。

## 各注入点规格

### digest Phase 1（注入 synaptic_context）
Agent 刚拿到 note 内容，正在决定 "这个 claim 应该放哪"。
此时展示 wiki 页面的互联地图 → Agent 不仅知道"有哪些页面"（perfusion 已提供），还知道"它们之间怎么连的"。

### digest Phase 3 seal 成功后（注入 weaving_hint）
返回 absorption_site 的当前连接状态：
- 它链向哪些其他 wiki 页面
- 哪些页面链向它
- 如果它是孤立的，提示 Agent 考虑加链接

### L24 Synaptogenesis Health
扫描 wiki/*.md，对每个页面检查：
- 是否有至少 1 个到其他 wiki 页面的出链
- 是否有至少 1 个来自其他 wiki 页面的入链
- 孤立页面 → WARNING

### weak_synapses hunger signal
wiki 页面中"无跨页引用"的比例超过阈值 → 触发信号

### _auto_link_note 增强
当前：仅 tag→note 文件名匹配
增强：扫描 note body 中出现的 wiki 页面标题关键词 → 自动建立 note→wiki 链接
