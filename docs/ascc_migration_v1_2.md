# ASCC Migration to Myco v1.2 — Paste-Ready Snippets

> **Purpose**: When Myco kernel upgrades to v1.2 (digestive substrate landed),
> downstream project agents (ASCC and peers) need an explicit contract update
> or they will write garbage into the new `notes/` layer.
>
> **How to use**: Paste §1 into ASCC's `MYCO.md` hot-zone. Paste §2 into
> ASCC's `_canon.yaml`. Run §3 checklist once to verify.
>
> **Why**: Without this, ASCC's agent will (a) hand-write `notes/*.md` files
> breaking L10, (b) create `scratch.md` / `TODO.md` at repo root breaking L11,
> (c) skip `myco_eat` and dump context into `wiki/`, (d) fail to tag friction
> with `friction-phase2` — losing Phase ② data.

---

## §1 — Paste into ASCC `MYCO.md` hot-zone (after 身份锚点, before 任务队列)

```markdown
**🔒 Myco v1.2 Hard Contract**（2026-04-11 启用）:

运行在 Myco v1.2 基质上的 agent 必须遵守以下 3 条铁律。违约由 L9/L10/L11 lint
自动检测。完整契约见 Myco kernel 的 `docs/agent_protocol.md`。

1. **不确定就 eat**：任何内容不知道往哪放，先 `myco_eat` 作为 raw note，tags
   标清楚来源，然后继续任务。事后再 digest。不要建 `scratch.md` / `TODO.md` /
   `memo.md` / `thoughts/`（L11 CRITICAL）。

2. **不绕过工具**：
   - `notes/*.md` **只能**通过 `myco_eat` / `myco_digest` 生成，不能手写
   - `notes/*.md` 的 `status` frontmatter 字段**只能**通过 `myco_digest` 修改
   - `log.md` **只能** append（通过 `myco_log` MCP tool）
   - `MYCO.md` 的任何修改都必须先有一条 extracted note 作为依据

3. **摩擦必捕**：Myco 工具不够用 / 不顺手 / 有歧义时 → `myco_eat` 捕获，tags
   **必须**包含 `friction-phase2`。格式：
   ```
   [friction-phase2] <症状一句话>

   触发场景：<上下文>
   期望行为：<希望工具怎么做>
   workaround：<临时处理>
   ```
   这些 note 会直接喂给 Myco Phase ②，漏一条 = 盲设计一次。

**Session boot sequence**（每次会话前 3 步，不能省略）：
1. `myco_status`  — 读 MYCO.md 热区 + 身份锚点
2. `myco_hunger`  — 看消化系统健康度；处理 raw_backlog / stale_raw
3. （如有）`myco_digest` 1-2 条最老 raw note
4. 开始正式任务

**Session end sequence**：
1. `myco_reflect` → `myco_log` → `myco_hunger` 再确认
2. 未完成的想法 → `myco_eat` 一条 raw note，tags 带 `followup`（不要写 TODO.md）
3. 改动 ≥5 文件或动了 `_canon.yaml` → `myco_lint`
```

---

## §2 — Paste into ASCC `_canon.yaml` under `system:`

**⚠️ 注意**：下面的 `allowed` 列表是**最小集**，请根据 ASCC 项目**真实的合法
顶层目录**（如 `data/`、`experiments/`、`runs/`、`configs/`、`results/` 等）补充。
L11 会把任何不在列表里的顶层条目标 HIGH。

```yaml
  write_surface:
    # L11 Write-Surface Lint — agent writes limited to this whitelist.
    # Authoritative contract: Myco kernel docs/agent_protocol.md §1.
    allowed:
      # --- Myco substrate ---
      - notes/                # via myco_eat / myco_digest ONLY
      - wiki/                 # structured knowledge pages
      - docs/                 # project docs + debate records
      - log.md                # append-only via myco_log
      - MYCO.md               # L1 index
      - _canon.yaml           # SSoT — human approval in practice
      # --- ASCC-specific (EXTEND AS NEEDED) ---
      - src/                  # code
      - scripts/              # tooling
      - configs/              # experiment configs
      - data/                 # datasets (if git-tracked)
      - experiments/          # experiment specs
      - results/              # output artifacts
      - tests/
      # --- Standard repo files ---
      - README.md
      - LICENSE
      - pyproject.toml
      - .gitignore
      - .github/
    forbidden_top_level:
      - scratch.md
      - scratch.txt
      - notes.md         # NOTE: this is the forbidden top-level file;
                         # the notes/ *directory* is allowed above
      - TODO.md
      - MEMO.md
      - memo.md
      - ideas.md
      - draft.md
      - summary.md
      - thoughts/
      - my_notes/
      - tmp/
      - temp/
```

And ensure the `notes_schema` block is present (copy from Myco kernel
`_canon.yaml` if missing after upgrade).

---

## §3 — Verification checklist (run once after paste)

1. **Lint baseline**:
   ```
   python scripts/lint_knowledge.py --project-dir .
   ```
   Expected: L11 reports 0 CRITICAL. If HIGH entries exist, inspect each:
   - If legitimate → add the path to `write_surface.allowed`
   - If garbage (scratch files from past sessions) → clean up or gitignore

2. **Smoke-test the 4 commands** (pick any small content):
   ```
   myco eat "ASCC agent hard contract activated" --tag meta --tag contract
   myco view --status raw --limit 5
   myco hunger
   myco digest --last --to integrated
   ```
   All 4 should succeed. `myco hunger` should report `healthy` or a single
   `promote_ready` signal.

3. **Eat the migration itself** (dogfood):
   ```
   myco eat "ASCC migrated to Myco v1.2 contract on $(date +%F)" \
     --tag meta --tag migration --tag friction-phase2
   ```
   This creates the first Phase ② friction-candidate note in ASCC's substrate.

4. **Brief the agent**: Start a new agent session and verify it reads
   `MYCO.md` → calls `myco_status` → calls `myco_hunger` **before** any
   other tool call. If it doesn't, the hot-zone snippet in §1 is not
   prominent enough; move it higher.

---

## §4 — What NOT to do during migration

- ❌ Do not retroactively rewrite old `log.md` entries to match the new contract
- ❌ Do not auto-ingest old `scratch.md` / `TODO.md` files into `notes/` via
  `myco eat` without first classifying them — most of them are dead weight
  and will pollute `raw_backlog`
- ❌ Do not modify the `forbidden_top_level` list to allow `scratch.md` etc.
  "just this once". The forbid list is doctrine, not configuration.
- ❌ Do not skip the L11 baseline run — discovering 47 HIGH entries three
  weeks in is worse than discovering them now.

---

## §5 — Feedback loop back to Myco kernel

Any ASCC-specific friction you hit during migration:
```
myco eat "<symptom>" --tag friction-phase2 --tag migration
```
Then **ping the Myco maintainer** (or open an issue at
https://github.com/Battam1111/Myco/issues) with a link to the note id.
These are the highest-value Phase ② data points — real downstream projects
are exactly who the contract is for.
