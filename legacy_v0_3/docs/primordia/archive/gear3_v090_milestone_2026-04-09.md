# Gear 3 里程碑回顾 — v0.9.0 + Myco 自我应用

> **文档状态**：[ARCHIVED] | 创建：2026-04-09
> **触发里程碑**：v0.9.0 PyPI 发布 + Myco 自我应用（`myco migrate self`）完成
> **覆盖范围**：从 pip 打包设计决策到 lint 全绿 push 的完整周期
> **执行人**：Yanjun + Claude Sonnet 4.6

---

## 三个 Double-loop 问题

---

### Q1：我们的工作流假设有哪些被证伪了？

#### 假设 1（已证伪）："打包后 CLI 跨平台开箱即用"

**原始假设**：`pip install myco` 之后 `myco lint` 直接可用，无需任何额外配置。

**证伪事件**：
- Windows 默认编码 GBK 导致 `rich` 进度条的 `•`（\u2022）崩溃：`UnicodeEncodeError: 'gbk' codec can't encode character`
- 用户需要手动执行 `chcp 65001 && set PYTHONIOENCODING=utf-8` 才能正常运行

**性质**：不是边缘 case。Windows 市场份额 > 70%，这是所有 Windows 用户必然踩的坑。

**对策**：在 CLI 入口处自动设置 UTF-8，不依赖用户环境（见本次 Gear 3 行动项 A1）。

---

#### 假设 2（已证伪）："模板只有一处"

**原始假设**：`templates/` 目录是模板的唯一来源，维护一处即可。

**证伪事件**：
- 打包重构（`src/myco/templates/`）引入了第二处模板
- 现状：`templates/`（顶层）和 `src/myco/templates/`（打包入 wheel）两处共存
- Myco 自我应用的 MYCO.md 热区第一条踩坑就是这个：*"修改 src/myco/templates/ 后忘记同步 templates/"*
- 更危险的是：两处现在已经**实际存在内容差异**（`src/myco/templates/` 是真实来源，`templates/` 是历史遗留）

**性质**：设计债务，随时间会静默发酵。每次修改模板，开发者需要记住"修两处"，这违反了 DRY 原则。

**对策**：删除顶层 `templates/`，以 `src/myco/templates/` 为单一来源（见行动项 A2，需用户决策）。

---

#### 假设 3（部分证伪）："`myco migrate` 在自身 repo 上能顺畅运行"

**原始假设**：dev machine 上 `myco` CLI 随时可用，dog-fooding 无摩擦。

**证伪事件**：
- `myco` 不在 cmd 默认 PATH（editable install 的 Scripts 目录在 `%APPDATA%\Python\Python313\Scripts`，未加入系统 PATH）
- 实际执行退化为手动创建文件，跳过了 CLI

**性质**：不影响最终结果，但破坏了"自我示范"的完整性。README 缺少 Windows PATH 设置说明。

**对策**：README 补充 Windows 安装后 PATH 验证步骤（见行动项 A3）。

---

### Q2：系统内哪些知识单元变得过时或冗余？

#### 过时单元 1：MYCO.md 模板 §5 会话结束第 7 条

**现状**：
```markdown
7. 长会话 → `python scripts/lint_knowledge.py`
```

**问题**：
- 对 Myco 自身 repo：需要加 `--project-dir .`，否则 lint 找不到项目根
- 对 L1 用户项目：根本没有 `scripts/` 目录，这行会让用户困惑

**修正方案**（行动项 A4）：
```markdown
7. 长会话 → `python scripts/lint_knowledge.py --project-dir .`（L2+ 项目；L1 跳过此步）
```

---

#### 过时单元 2：`templates/` 顶层目录（冗余，与 A2 联动）

**现状**：内容落后于 `src/myco/templates/`，是打包重构前的历史遗留。

**建议**：删除（详见 A2）。

---

#### 过时单元 3：`_canon.yaml` 的 `package.template_dirs` 描述错位

**现状**：
```yaml
template_dirs:
  - "templates/"                  # 开发源（修改入口）
  - "src/myco/templates/"         # 打包版（需与 templates/ 同步）
```

**问题**：把 `templates/` 标注为"修改入口"是错误的——打包后 `src/myco/templates/` 才是真实来源。这个描述会误导未来的开发者。

**修正方案**（联动 A2）：删除顶层 `templates/` 后，`template_dirs` 改为单条：
```yaml
template_dirs:
  - "src/myco/templates/"         # 唯一模板来源（打包入 wheel）
```

---

### Q3：权限分级有没有阻碍创新？

#### 阻碍 1：Windows 工具链摩擦未被 operational_narratives 捕获

**观察**：
- `.git/index.lock` 无法从 Linux sandbox 删除，需要切换 Windows PowerShell MCP
- PowerShell MCP 60s 超时，需要改用 desktop-commander
- 多行 commit message 被 CMD 截断，需要 `-F` 文件写法

这三个 workaround 都被反复发现和重新解决，说明**知识沉淀体系没有捕获 Windows 环境下的操作摩擦**。

**对策**：在 `docs/operational_narratives.md` 建立 P-001（Windows 环境操作规范），避免下次重蹈（见行动项 A5）。

---

#### 阻碍 2：Git 操作的工具选择未形成规范

**观察**：
- 简单 git 命令（status/log）→ 可用任意工具
- 涉及中文/多行内容的 git 操作 → 必须用 `-F` 写法 + desktop-commander
- 涉及 Windows 文件删除 → 必须用 Windows-MCP PowerShell

这个选择逻辑靠会话经验传递，没有文档化。新会话开始时会重新踩坑。

**对策**：同上，纳入 operational_narratives P-001。

---

## 行动项汇总

| ID | 优先级 | 内容 | 权限级别 | 状态 |
|----|--------|------|---------|------|
| A1 | HIGH | CLI 入口自动设置 UTF-8（`sys.stdout.reconfigure`） | Agent 自主 | ✅ |
| A2 | HIGH | 删除顶层 `templates/`，单一化模板来源 | **用户决策** 🛑 | ✅ |
| A3 | MEDIUM | README 补充 Windows PATH 验证步骤 | Agent 自主 | ✅ |
| A4 | MEDIUM | MYCO.md + src/myco/templates/MYCO.md 会话结束第 7 条加条件说明 | Agent 自主 | ✅ |
| A5 | MEDIUM | operational_narratives.md 新增 P-001（Windows 环境操作规范） | Agent 自主 | ✅ |

---

## Gear 3 → Gear 4 候选

以下问题的解决方案在**跨项目层面**有通用价值，标记为 `g4-candidate`：

- **CLI UTF-8 跨平台**（A1）：任何 Python CLI 工具在 Windows 上都会遇到这个问题，解法可以提炼为通用模板 → `g4-candidate`
- **双模板同步问题**（A2）：任何带打包重构的框架项目都会遇到，可提炼为"打包后模板管理"最佳实践 → `g4-candidate`

---

## 结论

本里程碑的三个最重要的 Gear 3 发现：

1. **Windows UTF-8 问题是必须修的 bug**，不是"用户自己解决"的问题
2. **双模板设计是架构债务**，需要一个明确决策（删除顶层 `templates/`）
3. **Windows 操作摩擦需要文档化**，`operational_narratives.md` 是正确的容器

本次 Gear 3 不修改任何框架原则（W1-W12 依然有效），属于 Single-loop 级别的修正 + 一项需要用户决策的架构调整。
