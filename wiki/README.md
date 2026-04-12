# wiki/ — L1.5 Refined-Knowledge Layer

> **状态**：空目录 + 章程（dormant organ）。截至 contract v0.8.0 尚无 promoted page。
> **用途**：存放从 `notes/` 提炼后进入"长期可引用"阶段的 W8 知识页面。
> **在 Myco 架构中的位置**：L1（MYCO.md 索引） → **L1.5（本目录）** → L2（docs/ 参考规格） → L3（notes/ 原始消化）
> **为什么现在是空的**：Myco 作为一个仍在 pre-release 的基质，自用 notes 还没有跑完足够多的 extract/integrate 循环达到 promote 阈值。第一个真实 wiki 页面将在 Gear 3 第一次 promote 时落地，届时 `myco digest` + 手工裁定会把那条 note 提拔到本目录。

---

## 页面契约（W8 Schema，由 L7 Wiki W8 Format lint 强制）

任何进入本目录且文件名为 `*.md`（`README.md` 除外）的文件，必须在头部 15 行内出现：

- **类型**：`entity` / `concept` / `operations` / `analysis` / `craft`（合法类型在 `_canon.yaml::system.wiki_page_types` 定义）
- **最后更新**：ISO 日期字符串

以及在最后 10 行内出现：

- **Back to**：指向 MYCO.md 或其他索引文件的返回锚

缺任何一项会触发 L7 MEDIUM issue；类型字符串不在 wiki_page_types 白名单会触发 L7 LOW issue。

## L4 Orphan Detection 约束

每一个非 README 的 `wiki/*.md` 必须在 `MYCO.md`（入口文件）里至少被引用一次——用绝对路径或文件名均可。没有引用会触发 L4 MEDIUM issue（孤儿页面）。

这条规则的动机：wiki 页面是"长期可引用"的知识，如果连入口都不指向它们，说明它们不被使用，属于死知识，应该被 excrete 而不是堆积。

## 触发"第一次 promote"的条件（roadmap，非 contract）

1. `notes/*.md` 中有一张 note 的 `digest_count ≥ 2` **且** `promote_candidate: true`
2. `myco hunger` 报告 `promote_ready: 1+`
3. 操作者运行 `myco digest --promote <note_id>`（或手工把内容裁切成 W8 格式写入 `wiki/<slug>.md`）
4. 更新 MYCO.md 索引新增条目
5. `myco lint` 应 20/20 绿

## 为什么这个目录不删

Wave 8.2 架构师审计曾短暂考虑过"空目录就是 vaporware，应当删除直到首个真实页面"。最终决定保留，理由：

- L1.5 层是 Myco 四层知识架构的结构性声明，删除等于修改 contract（需要 craft_protocol）
- 空目录 + 章程 = 明确告诉未来 agent "这里要放什么"、"放错会 lint 红"，这是架构指引而非 vaporware
- `README.md` 本身被 L4/L7 lint 明确豁免（见 `src/myco/lint.py::lint_orphans` 和 `lint_wiki_format`），所以章程本身不触发 lint 噪音

## 相关文档

- `docs/architecture.md` — 四层知识架构总览
- `src/myco/lint.py::lint_wiki_format` — L7 实现
- `src/myco/lint.py::lint_orphans` — L4 实现
- `_canon.yaml::system.wiki_page_types` — 合法类型白名单
- `docs/WORKFLOW.md` — promote/digest 流程
