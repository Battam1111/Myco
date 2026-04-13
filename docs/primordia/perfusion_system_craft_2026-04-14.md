---
type: craft
created: 2026-04-14
status: active
scope: knowledge-circulation
---

# Perfusion System — 知识循环设计

## 问题陈述

Myco 的消化管道（eat → digest → extracted → integrated）保障了知识从捕获到存储的完整性，但**存储后的知识无法自动回流到 Agent 的决策过程中**。

类比：人体消化系统将食物分解为营养并吸收进血液——但如果没有循环系统，营养就无法到达需要它的器官。

当前缺失的环节：Agent 不知道 wiki 里有什么，也不会在决策前自动查阅相关知识页。

## 设计原则

### P1: Bitter Lesson 合规
**工具提供目录，Agent 决定读什么。** 灌注系统不做智能推荐（不用 NLP/embedding），只做信息可见化。选择权完全在 Agent。

### P2: 零新工具
不增加任何新 MCP 工具。在 Agent **已经必定调用**的两个触点（`myco_pulse`、`myco_hunger`）里注入灌注数据。零新习惯，零新记忆负担。

### P3: 轻量索引
灌注信息来自文件系统元数据（文件名、首行标题、修改时间、大小），不解析全文内容。计算成本 ≈ `ls + head -1`。

### P4: 仿生命名
- `perfusion`（灌注）：血液流经组织，将营养递送到器官
- `perfusion_map`：知识血管地图——哪些组织（wiki 页面）可供灌注
- `knowledge_context`：hunger 报告中基于当前任务的上下文灌注

## 架构

```
                    ┌─────────────────────────┐
                    │   compute_perfusion()   │
                    │   (纯文件系统元数据)      │
                    └──────────┬──────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                                  ▼
     myco_pulse output                  myco_hunger output
     ┌──────────────────┐              ┌──────────────────────┐
     │ + perfusion_map: │              │ + knowledge_context:  │
     │   wiki 全页面目录  │              │   任务关键词 → wiki   │
     │   (名称+摘要+日期) │              │   页面关联度排序       │
     └──────────────────┘              └──────────────────────┘
              │                                  │
              ▼                                  ▼
     Agent 看到目录，                     Agent 看到与当前任务
     自主决定读哪些                       相关的推荐页面列表
```

## compute_perfusion() 规格

**输入**: project_root, task_context (可选，来自 task queue + recent log)
**输出**: dict with `perfusion_map` and optionally `knowledge_context`

### perfusion_map（全量目录，注入 pulse）
```json
{
  "wiki_pages": [
    {
      "path": "wiki/algorithms.md",
      "title": "12 个算法变体 + 网络架构 + API 参考",
      "last_modified": "2026-04-10",
      "size_kb": 10
    }
  ],
  "docs_active": [
    {
      "path": "docs/current/figure1_debate_2026-04-09.md",
      "title": "Figure 1 设计传统手艺",
      "status": "ACTIVE",
      "last_modified": "2026-04-09"
    }
  ]
}
```

### hunger 中的灌注（同一 perfusion_map + 任务原文）

hunger 输出中附带与 pulse 相同的 perfusion_map，外加一个 `current_tasks_raw` 字段——直接从 MYCO.md 提取的任务队列原文。

**不做关键词匹配**。原始设计曾考虑工具端做词交集排序，但这违反 P1（把判断力放进了工具）。正确做法：把任务原文和知识目录同时呈现给 Agent，让 Agent 自己关联。

## 历史兼容性

- 无 perfusion_map 的旧 pulse 输出照常工作（字段是 additive）
- 无 knowledge_context 的旧 hunger 输出照常工作
- 不修改任何现有字段的语义
