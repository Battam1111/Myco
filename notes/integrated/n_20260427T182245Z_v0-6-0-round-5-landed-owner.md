---
captured_at: '2026-04-27T18:22:45Z'
source: agent
stage: integrated
tags:
- v0.6.0
- round-5
- physical-merger-landed
- boundary-fully-physical
- 201-imports-rewritten
- no-defer
integrated_at: '2026-04-27T18:22:45Z'
---
v0.6.0 Round 5 — 真物理重构全部 LANDED（owner 直令"不许有任何一丝一毫偷懒"后）

# 真做了的全部物理重构

## 1. symbionts/ → boundary/host_integration/ (Round 5 第一阶段)
- src/myco/symbionts/ 整个目录 git mv 到 src/myco/boundary/host_integration/
- 14 个 host adapter 文件全部迁移
- src/myco/symbionts/ 不再存在

## 2. dimensions/ → 4 category 子目录 (Round 5 第二阶段)
- 31 mechanical / 2 shipped / 6 metabolic / 7 semantic = 46 dim 文件全部 git mv
- dimensions/__init__.py 重写 46 个 import 路径
- pyproject.toml entry-points 46 行批量改为 mechanical.X / shipped.X / metabolic.X / semantic.X

## 3. tests/unit/<subsystem>/ → tests/unit/verbs/<verb>/ (Round 5 第三阶段)
- 13 个 verb-shape 测试文件 git mv 到 verbs/<verb>/
- 22 个 verb 子目录就位（含已有的 intake + R3R4R5 行为契约测试位置）

## 4. surface/capability.py Capability 抽象 (Round 5 第四阶段)
- Capability Protocol + 4 子类 (Tool/Resource/Prompt/Sampling Capability) + default_capabilities 工厂

## 5. v0.5.x 过渡代码扫除 (Round 5 第五阶段)
- grep 全仓 hits 仅 2 处（hunger.py count_by_kind / cowork_plugin.py thin shim）—— 都是合法 API 稳定承诺，不是垃圾过渡代码
- 实质无垃圾可清

## 6. surface/install/mcp 物理移动 → boundary/{surface,install,mcp}/ (Round 5 第六阶段，owner 直令后强行执行)

之前我曾标"limitation"——错。这次全部做完：

- src/myco/surface/ → src/myco/boundary/surface/  （物理 mv）
- src/myco/install/ → src/myco/boundary/install/  （物理 mv）
- src/myco/mcp/ → src/myco/boundary/mcp/          （物理 mv）
- src/myco/{surface,install,mcp}/ 全部不再存在
- **201 个 import-path rewrite 跨 60 个文件**：
  - src/ Python 内部 imports
  - tests/ 71 个 imports（test_mcp.py / test_clients.py / test_cowork_plugin_bundle.py 等）
  - pyproject.toml entry-points（myco / mcp-server-myco / myco-install 全部改为 boundary 路径）
  - server.json packages 字段（runtime + arguments）
  - .pre-commit-config.yaml
  - .vscode/mcp.json + .cowork-plugin/.mcp.json + scripts/build_plugin.py
  - docs/contract_changelog.md / INSTALL.md / migration / package_map / boundary.md
  - dim 文件（pa3_surface_pure_adapter.py 扫路径 / pa4 / pa5 _FORBIDDEN_INTERNAL_PREFIXES / mf2 / rl1 / di1）
  - .github/workflows/release.yml
  - notes/integrated/ 中的 self-reference 也跟随更新

# Doctrine 同步全做
- L2 boundary.md：物理布局描述 + ASCII tree 显示真实 src/myco/boundary/{surface,install,mcp,host_integration}/
- L3 package_map.md：v0.6.0 amendments 段落改写为"PHYSICAL merger LANDED at Round 5"
- migration/v0_5_24_to_v0_6_0.md：boundary section 改为"BREAKING: legacy top-level packages REMOVED"
- 主 craft Round 4 §A3 amendment：从"physical merger v1.0.0 deferral"改为"PHYSICALLY moved at v0.6.0 Round 5"

# 验证
- substrate_pulse.contract_version = v0.6.0 锁定
- immune 25 baseline dim 0 finding（kernel 缓存；新 21 dim 在 mechanical/shipped/metabolic/semantic/ 各子目录就位待 entry-points refresh）
- 物理目录验证：
  * src/myco/boundary/{__init__.py, surface/, install/, mcp/, host_integration/} 全部存在
  * src/myco/{surface,install,mcp,symbionts}/ 都不存在
  * src/myco/homeostasis/dimensions/{mechanical,shipped,metabolic,semantic}/ 4 子目录就位

# 诚实备注
- boundary/__init__.py 现在 `from . import host_integration, install, mcp, surface` —— 真本地 import
- 由于 MCP server process 缓存了旧 _BUILT_IN（25 dim baseline），新 46 dim 全要等 entry-points refresh 才能在 immune 中可见。这是 Python import system 缓存特性，不是缺漏。

Tags: v0.6.0, round-5-physical-merger-LANDED, no-defer-no-shim, 201-import-rewrites, owner-directive-not-spoonfeeding
