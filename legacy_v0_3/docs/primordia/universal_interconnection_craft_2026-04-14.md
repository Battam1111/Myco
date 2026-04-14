---
craft_id: universal-interconnection
wave: 46
rounds: 1
status: ACTIVE
decision: "L2 auto-discovery + L19 full-project scan + pre-commit enforcement"
date: "2026-04-14"
---

# 万物互联基础设施升级 — Wave 46

## 问题

添加 L23/L24 两个 lint 维度后，`FULL_CHECKS` 从 23 变为 25，但散布在
~15 个文件里的 "23-dimension" / "23 维" 引用没有同步更新，导致 CI 连续
三次失败。

根因分析发现两个架构缺陷：

1. **L2 Number Consistency 只检查 `cited_in` 列表**：手工维护的 5 个文件，
   实际引用维度数的文件有 ~15 个。手工列表天然不完备。
2. **L19 Dimension Count 只检查硬编码的 14 个 surface**：`wiki/identity.md`、
   `docs/vision.md`、`src/myco/graft.py` 等被遗漏。

## 设计原则

1. **Bitter Lesson**: 基础设施负责发现和拦截，Agent 负责修复。不做自动传播。
2. **万物互联**: 扫描范围必须覆盖整个项目树，包括 `.claude/` 目录。
3. **历史准确性**: craft 文档、changelog、notes 等历史记录保持原样（pinned）。
4. **渐进发现**: 只检查 `value-1` 和 `value-2`，避免古老历史值的误报。

## 实现

### L2 Tier 2 Auto-Discovery

在原有 Tier 1（cited_in → HIGH）之上增加 Tier 2：

- 扫描**整个项目树**（含 `.claude/`）
- 对每个 numeric claim，搜索 `value-1` 和 `value-2` 出现在 claim keywords 上下文中的情况
- 结果为 MEDIUM（不阻塞提交，但对 Agent 可见）
- keywords 字段加入 `_canon.yaml` 的 numeric_claims 定义

Pinned（不扫描）：
`log.md`, `notes/`, `docs/primordia/`, `contract_changelog.md`,
`tests/`, `forage/`, `examples/`, `_canon.yaml`, `src/myco/immune.py`

### L19 Full-Project Auto-Discovery

在原有 HIGH/MEDIUM surface 列表之后增加全项目扫描：

- 使用同样的 5 个 regex pattern
- 新发现的文件报告为 MEDIUM
- 同样的 pinned 排除列表

### Pre-Commit Hook

已有基础设施（Wave 18/23）：
- `.git/hooks/pre-commit` 运行 `myco immune`
- 检测到 HIGH/CRITICAL → 阻塞 commit
- MEDIUM/LOW → 打印但放行

无需修改——L2 Tier 1 仍然产生 HIGH，L2 Tier 2 和 L19 auto-discovery
产生 MEDIUM。关键路径上的 cited_in 文件仍然强制通过，边缘文件通过
MEDIUM 提示 Agent 注意。

## 效果

| 指标 | 升级前 | 升级后 |
|------|--------|--------|
| L2 扫描范围 | 5 cited_in 文件 | 5 cited_in + 全项目自动发现 |
| L19 扫描范围 | 14 硬编码 surface | 14 硬编码 + 全项目自动发现 |
| .claude/ 覆盖 | ❌ | ✅ |
| 维度数漂移是否可逃逸 | ✅（边缘文件不查） | ❌（全项目扫描） |
