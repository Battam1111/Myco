# Contract Changelog

> ## ⚠️ Wave 8 Pre-Release Re-Baseline（2026-04-11）
>
> 在 Wave 8，Myco 对整条版本线进行了一次**全方位下调**：所有曾以 `v1.x.y` 命名的 kernel contract 版本、所有以 `1.x.y` 发布的包版本，语义完全保留，但数值上全部映射为 `v0.x.y` / `0.x.y`。理由：Myco 从未进行过真正的 1.0 正式发布，continue calling anything "v1" 会对未来下游用户造成"已经稳定"的错误信号。
>
> **映射规则**（不可逆，仅此一次）：
> - 包版本：`1.1.0 → 0.2.0`（PyPI classifier `5 - Production/Stable → 4 - Beta`）
> - contract 版本：`v1.X.Y → v0.X.Y`（主号 1→0，其余不变）
> - 本 changelog 下方的历史条目 **保持 v1.x.y 原始标识符不动**（immutable history doctrine：已记录的事实不篡改）
> - 新条目从 `v0.8.0` 继续增长（= 旧 `v1.7.0` 后的下一个 minor）
> - 详细 debate 记录：`docs/primordia/archive/pre_release_rebaseline_craft_2026-04-11.md`（kernel_contract 类 craft，2 rounds，final confidence 0.92）
>
> **为什么保留历史 v1.x 条目**：craft 的 Round-2 attack R2.1 指出，若同时删除 dist/1.1.0 wheel 又把历史 changelog 改成 v0.x，等于声称"v1 从未存在过"，和 immutable history 自相矛盾。最终方案：物理 dist artifacts 删除（因为它们是**当前状态**的陈旧副本），历史 changelog 条目保留（因为它们是**历史事实**的记录）。两者分类不同。
>
> 本 banner 之后**所有**对 Myco 版本的引用应以 `v0.x` 为准；看到 v1.x 即为历史档案。

本文件记录 Myco kernel contract（`docs/agent_protocol.md` + `_canon.yaml`
+ `scripts/lint_knowledge.py` + `src/myco/lint.py` + `src/myco/mcp_server.py`
+ `src/myco/templates/**`）的版本变更。

版本号遵循 Semantic Versioning：

- **MAJOR**：破坏性变更（移除/重命名原则、修改已有原则语义、下游必须改代码）。
- **MINOR**：向后兼容的新增（新原则、新 lint 维度、新触发点、新字段）。
- **PATCH**：仅措辞/typo/非语义微调。

Commit message 格式必须使用 Conventional Commits 风格并带 `[contract:*]` 前缀：

```
[contract:minor] §8 Upstream Protocol v1.0 + §5 on-self-correction
[contract:patch] §4 措辞微调
[contract:major] 移除 L3 原则（与 L11 合并）
```

下游实例通过 `_canon.yaml: system.contract_version` 与本地 `synced_contract_version`
比对来感知 drift。

---

## v0.6.0 — 2026-04-14 (major · Wave 56 — Architecture Refactor: Hosts→Symbionts, Doctor+Diagnose→Pulse)

**What changed**:

**Tier C Refactor: Internal Naming & Consolidation**:
- Directory rename: `src/myco/hosts/` → `src/myco/symbionts/` (9 adapters unchanged)
  - Function rename: `detect_active_host()` → `detect_active_symbiont()`
  - Dict key: `check_all_hooks()` output `"detected_host"` → `"detected_symbiont"`
  - Rationale: Symbionts metaphor (ecosystem-mates) vs Hosts metaphor (service providers)
- Merged redundant CLI commands: `myco doctor` + `myco diagnose` → `myco pulse`
  - Unified health check: session hooks + deployment verification
  - Rationale: Single source of truth for system health
  - **BREAKING**: `myco doctor` and `myco diagnose` CLI commands removed (no CLI aliases per user decision)
  - **BREAKING**: `myco_doctor` and `myco_diagnose` MCP tools merged → no MCP tools affected (neither existed in public API)
- Deleted vestigial modules: `bootstrap.py`, `first_run.py` (zero importers)

**Contract surface**: v0.45.0 → v0.6.0 (major bump for renamed directory + merged CLI commands).

**Breaking changes**:
- CLI: `myco doctor` / `myco diagnose` → use `myco pulse` instead
- Python imports: `from myco.hosts` → `from myco.symbionts`
- Function calls: `detect_active_host()` → `detect_active_symbiont()`
- Dict keys: consume `.get("detected_symbiont")` not `.get("detected_host")`

## v0.45.0 — 2026-04-14 (minor · Wave B — 9-Platform Multi-Adapter + First-Run Auto-Setup)

**What changed**:

Wave B introduces universal multi-platform host detection and automated first-run setup:

**Host Adapter Standardization**:
- Extended adapter network from 6 to 9 platform targets: Claude Code, Cowork, Cursor, VS Code, Codex, Cline, Continue, Zed, Windsurf
- Unified adapter API: `is_installed()`, `get_status()`, `install_hooks(root)` across all 9 hosts
- Adapter contract documented in `docs/hosts.md` and enforced by `src/myco/hosts/common.py`

**First-Run Auto-Setup (`myco seed --auto-detect`)**:
- Zero-friction onboarding: auto-detects installed tools, generates tool-specific configs (.mcp.json, cline_mcp_settings.json, .claude/settings.json)
- Scheduled metabolic cycle pre-approval
- Cowork-compatible skill scaffolding
- Clear user guidance on next steps (run /myco-boot to grant permissions)
- Smoke test: fresh project bootstrap succeeds 100% (tested on Claude Code + Cline)

**Contract surface**: v0.44.0 → v0.45.0.

---

## v0.44.0 — 2026-04-12 (minor · Wave A2 — molt deprecated, foundation cleanup)

**What changed**: `myco molt` deprecated (prints message, exits 2). Use
`myco correct` instead. Centralizes project root resolution (Wave A1).
Part of Phase A foundation cleanup.

**Contract surface**: v0.43.0 → v0.44.0.

---

## v0.43.0 — 2026-04-12 (minor · Wave 57 Tool Trigger Contract — 18/18 MCP tool trigger documentation)

**What changed**:

Wave 57 documents trigger conditions for ALL 18 MCP tools in agent_protocol.md.
Previously only 9/18 had trigger docs (§2.1-§2.2). Added:
- §2.3 Compression Pipeline (compress, uncompress, prune)
- §2.4 External Metabolism (inlet, forage, upstream, search)
- §2.5 Structural Intelligence (graph, cohort, session)

Key rule: `myco_sense` MUST be called BEFORE answering any factual question.

Craft: `tool_trigger_contract_craft_2026-04-12.md` (kernel_contract, 2 rounds, 0.90).

**Contract surface**: v0.42.0 → v0.43.0.

---

## v0.42.0 — 2026-04-12 (minor · Wave 55 Identity Anchor Agent-First Revision — mutation-selection internalized)

**What changed**:

Wave 55 rewrites the 8 identity anchors based on the Agent-First reality
established by Wave 54. The fundamental conceptual shift:

- **Old model**: System mutates, human selects (human-in-the-loop)
- **New model**: Agent mutates, Substrate's immune system selects, human
  provides direction and trust (human-on-the-loop)

Anchor changes:
1. "基质 vs 工具" → **"Agent-Substrate 共生体"** (symbiont, not "runs on")
2. "非参数进化" — unchanged
3. "代谢 + 七步管道" → **"自主代谢管道"** (Agent IS the daemon, not human-triggered)
4. "压缩即认知" — add cohort intelligence + compression_pressure references
5. "四层自我模型" — add graph (C layer) + sessions (D layer)
6. "人机协作" → **"内化的变异-选择"** (lint+hunger = immune system = selection)
7. "理论血统" — add Rich Sutton Bitter Lesson
8. "永久锚点文档" — add this craft as third permanence anchor

Also updated: `docs/vision.md` §五 "人机协作模型" → "Agent-Substrate 共生模型".

Authoritative craft: `docs/primordia/anchor_agentfirst_revision_craft_2026-04-12.md`
(kernel_contract, 3 rounds, 0.90 confidence).

**Contract surface**: v0.41.0 → v0.42.0.

---

## v0.41.0 — 2026-04-12 (minor · Wave 54 Agent-First Integration — hunger auto-execute, graph/session signals, scheduled metabolic cycle)

**What changed**:

Wave 54 closes the signals→execution gap. Agent-first design principle:
human = natural language only, agent = sole operator.

1. **`myco_hunger(execute=true)`** — auto-executes ALL recommended actions
   (digest, compress, prune). The agent calls ONE tool and the substrate
   self-heals. No manual verb calls needed.
2. **`myco hunger --execute`** — CLI equivalent for scheduled task execution.
3. **Graph orphan signal** in hunger — fires when >10 files have zero inbound
   links. Eliminates the W47 silo: graph is now part of the hunger pipeline.
4. **Session index staleness signal** — fires when `.myco_state/sessions.db`
   doesn't exist. Eliminates the W52 silo.
5. **Scheduled metabolic cycle** — daily recurring task via Claude Code
   scheduled-tasks: runs hunger(execute=true) + session index + lint.
6. **MCP `myco_hunger` docstring rewritten** as Agent-complete boot ritual
   manual: tells any agent exactly what to do at boot/mid/end session.

**Contract surface**: v0.40.0 → v0.41.0.

**Design principle**: The agent's FIRST call every session is
`myco_hunger(execute=true)`. Everything flows from there.

---

## v0.40.0 — 2026-04-12 (minor · Wave 52 Session Memory + Search — FTS5 indexing of agent conversations)

**What changed**:

Wave 52 adds session memory: FTS5 full-text search across Claude Code
conversation transcripts. Absorbs hermes-agent session search pattern.

New module `src/myco/sessions.py`:

1. **`index_sessions(root)`** — Scan `.claude/projects/*/` for .jsonl files,
   parse user/assistant turns, index into SQLite FTS5 at `.myco_state/sessions.db`.
2. **`search_sessions(root, query)`** — FTS5 MATCH query with snippet extraction.
3. **`prune_sessions(root)`** — Remove old index entries.

New CLI verb: `myco memory {index|search|prune}` (sessions_cmd.py).
New MCP tool: `myco_memory` (tool #18).
4 unit tests in `tests/unit/test_sessions.py`.

**Contract surface**: v0.39.0 → v0.40.0.

---

## v0.39.0 — 2026-04-12 (minor · Wave 50 Continuous Compression — compression_pressure metric + metabolic-cycle skill)

**What changed**:

Wave 50 adds `compression_pressure` metric and a metabolic-cycle boot ritual
skill. Partially closes `docs/open_problems.md` §4.

1. **`compute_compression_pressure(root)`** in notes.py — returns
   `(raw + digesting) / max(1, extracted + integrated)`.
2. Hunger signal fires when pressure > threshold (default 2.0).
3. Hunger action recommends `compress --cohort auto` when pressure high.
4. **`skills/metabolic-cycle.md`** — boot ritual procedure document.
5. **`_canon.yaml`** additions: `pressure_threshold`, `compression_pressure`
   in boot_brief signals, `skills/` in write_surface.
4 unit tests in `tests/unit/test_compression_pressure.py`.

**Contract surface**: v0.38.0 → v0.39.0.

---

## v0.38.0 — 2026-04-12 (minor · Wave 49 Inlet Trigger Policy — search miss tracking + cohort gap detection)

**What changed**:

Wave 49 adds `inlet_ripe` hunger signal + search miss tracking. Partially
closes `docs/open_problems.md` §2 (Metabolic Inlet Trigger Signals).

1. **`detect_inlet_trigger(root)`** in notes.py — fires when search miss
   count >= threshold OR cohort gaps with >= gap_threshold notes detected.
2. **`record_search_miss(root, query)`** in notes.py — records zero-result
   searches in `.myco_state/search_misses.yaml`.
3. **`myco_sense`** MCP tool — calls `record_search_miss` when matches == 0.
4. Hunger report now includes `inlet_signal` in signals + actions.
5. **`_canon.yaml::system.inlet_triggers`** — new config section.
4 unit tests in `tests/unit/test_inlet_trigger.py`.

**Contract surface**: v0.37.0 → v0.38.0.

---

## v0.37.0 — 2026-04-12 (minor · Wave 48 Semantic Cohort Intelligence — tag analysis, compression suggestions, gap detection)

**What changed**:

Wave 48 adds tag-based cohort analysis for intelligent compression and
knowledge gap detection. New module `src/myco/cohorts.py`:

1. **`tag_cooccurrence(root)`** — Pairwise tag co-occurrence across all notes.
2. **`compression_cohort_suggest(root)`** — Suggest groups of notes for
   compression (tag + count + age + score).
3. **`gap_detection(root)`** — Tags where ALL notes are raw/digesting
   (unprocessed knowledge domains).

New CLI verb: `myco colony {matrix|suggest|gaps}` (cohorts_cmd.py).
New MCP tool: `myco_colony` (tool #17, readOnlyHint=True).
`myco condense --cohort auto` uses top suggestion from cohort intelligence.
5 unit tests in `tests/unit/test_cohorts.py`.

**Contract surface**: v0.36.0 → v0.37.0.

---

## v0.36.0 — 2026-04-12 (minor · Wave 47 Link Graph + Backlinks — structural mycelium connectivity)

**What changed**:

Wave 47 adds structural link graph infrastructure — the first step toward
the "everything connected like mycelium" vision (6-point directive #5).

New module `src/myco/graph.py`:

1. **`extract_links(filepath, root)`** — Parse .md files for outbound links:
   markdown links, backtick paths, YAML frontmatter refs (compressed_from,
   compressed_into, digest_target), craft file references, note ID references.
   Code-fence-aware (lines inside fences skipped).
2. **`build_link_graph(root)`** — Two-pass construction: forward map from all
   .md files, then invert to build backlinks. On-demand, no cache.
3. **`query_backlinks(graph, target)`** — Who references this file?
4. **`find_orphans(graph)`** — Files with zero inbound links. Structural roots
   (MYCO.md, _canon.yaml, log.md, README*) excluded.
5. **`find_clusters(graph)`** — BFS connected components on undirected graph.
6. **`graph_stats(graph)`** — Nodes, edges, orphan count, cluster count,
   hub (most backlinks), authority (most forward links).

New CLI verb: `myco mycelium {backlinks|orphans|clusters|stats}` (graph_cmd.py).
New MCP tool: `myco_mycelium` (tool #16, readOnlyHint=True).
5 unit tests in `tests/unit/test_graph.py`.

**Contract surface**: v0.35.0 → v0.36.0.

---

## v0.35.0 — 2026-04-12 (minor · Wave 46 Signal-to-Action wiring — HungerReport.actions closes advisory→execution gap)

**What changed**:

Wave 46 closes the advisory-to-execution gap: hunger signals now produce
structured action recommendations that agents can execute directly without
interpreting signal text.

Changes to `src/myco/notes.py`:

1. **`HungerReport.actions`** — new `List[Dict[str, Any]]` field on the
   `HungerReport` dataclass. Each action is `{verb, args, reason}`.
2. **`compute_hunger_report()`** — new action computation block derives
   executable recommendations from existing signals:
   - `stale_raw` → `digest` action (oldest raw note)
   - `raw_backlog` → `digest` action (bulk)
   - `dead_notes` → `prune` action (apply=True)
   - `compress_signal` → `compress` action (tag-based cohort)
   - `promote_candidates` → `digest` action (to integrated, top 3)
3. **Bug fix**: `compress_signal` variable initialized to `None` before
   its `try` block to prevent `NameError` if the block raises.

Changes to `src/myco/mcp_server.py`:

4. **`myco_hunger`** tool docstring updated to document the `actions` list
   in the response, explaining the signal-to-action pattern.

**Contract surface**: `_canon.yaml::system.contract_version` bumped
v0.34.0 → v0.35.0. Template `synced_contract_version` synchronized.

**Guiding principle**: Bitter Lesson — don't hardcode what the agent
should do. Provide structured signals with recommended actions; the
agent's intelligence decides execution. If the agent improves, actions
improve — without Myco code changes.

---

## v0.34.0 — 2026-04-12 (minor · Wave 43 full agent surface — 6 new MCP tools, 9→15 tool coverage)

**What changed**:

Wave 43 exposes every agent-relevant Myco verb via MCP, closing the
"agents can't call compress/prune/inlet/forage/upstream" gap.

6 new MCP tools added to `src/myco/mcp_server.py`:

1. **`myco_condense`** — forward compression synthesis (tag or note_ids
   cohort, rationale, confidence, dry_run). Wraps `compress_cmd.run_compress`.
2. **`myco_expand`** — reverse compression (restore inputs, delete output).
   Wraps `compress_cmd.run_uncompress`.
3. **`myco_prune`** — dead-knowledge auto-excretion (safe dry-run default,
   opt-in apply). Wraps `notes_cmd.run_prune`.
4. **`myco_absorb`** — external content ingestion with provenance tracking
   (content + provenance + tags). Wraps `inlet_cmd.run_inlet`.
5. **`myco_forage`** — forage substrate management (add/list/digest actions).
   Wraps `forage_cmd.run_forage`.
6. **`myco_upstream`** — inter-instance knowledge transfer (scan/absorb/ingest).
   Wraps `upstream_cmd.run_upstream`.

All 6 tools follow the established pattern: async function, JSON return,
project_dir auto-detection, structured error messages. Each wraps the
corresponding `*_cmd.py` module via stdout capture + JSON mode.

**Files modified** (6 files):

    src/myco/mcp_server.py (6 new tools + header docstring update)
    _canon.yaml (contract_version v0.33.0 → v0.34.0)
    src/myco/templates/_canon.yaml (synced_contract_version v0.33.0 → v0.34.0)
    MYCO.md (contract version refs + project summary)
    docs/adapters/README.md (contract version)
    docs/contract_changelog.md (this entry)

**Tool coverage**: 9/19 → 15/19 CLI verbs now have MCP wrappers.
Remaining 4 without MCP: init, migrate, config, import (setup-only verbs
that agents don't need during normal metabolism).

---

## v0.33.0 — 2026-04-12 (minor · Wave 42 structural cleanup — delete immune.py/metabolism.py aliases, remove immune verb, unify L19 surfaces)

**What changed**:

Wave 42 cleans the foundation before the Phase B–E evolution sequence
(Waves 43–53). Three removals, zero new features.

1. **DELETE `src/myco/immune.py`** (131 lines) — pure re-export alias of
   `myco.lint` created in Wave 29 (biomimetic nomenclature). Zero callers
   anywhere in the codebase. The planned "physical move" from lint.py →
   immune.py never happened and is now superseded by the direct-reference
   approach: `myco.lint` is the canonical module name.

2. **DELETE `src/myco/metabolism.py`** (108 lines) — pure re-export alias
   of `myco.notes`. Same rationale: zero callers, planned rename never
   materialized, direct `myco.notes` reference wins.

3. **REMOVE `myco immune` CLI verb** — the biomimetic alias for `myco immune`
   added in Wave 29. `myco immune` remains the sole lint entry point.
   The verb alias duplicated 15 lines of argparse setup and a 4-line
   dispatch block in cli.py for zero additional capability.

4. **L19 surface list update** — remove `src/myco/immune.py` from
   `_L19_MEDIUM_SURFACES` (10 → 10 entries, was 11). Update dimension
   count regex from `immune` keyword to `health` keyword to match
   updated README/CLI help text.

**Files modified** (10 files):

    src/myco/immune.py (DELETED)
    src/myco/metabolism.py (DELETED)
    src/myco/cli.py (remove immune verb alias + clean lint help text)
    src/myco/lint.py (L19 surface list + regex + docstring)
    _canon.yaml (contract_version v0.32.0 → v0.33.0)
    src/myco/templates/_canon.yaml (synced_contract_version v0.32.0 → v0.33.0)
    MYCO.md (contract version refs + project summary + lint indicator)
    README.md (remove immune alias from lint verb row)
    README_zh.md (same)
    README_ja.md (same)
    docs/adapters/README.md (contract version)
    tests/unit/test_lint_dimension_count.py (test content: immune → health)

**Supersedes**: Wave 29 biomimetic alias strategy
    (`docs/primordia/biomimetic_nomenclature_craft_2026-04-12.md` D7
    one-wave grace period was long exceeded; Wave 42 closes the alias
    chapter permanently).

**Why now**: user directive to "clean up all compromises, aliases,
redundancy" before building the next evolution phase (Waves 43+).

---

## v0.32.0 — 2026-04-12 (minor · L22 wave-seed lifecycle, Wave 41 — raw wave-seed orphan detection as seven-step pipeline post-condition)

**Author**: Claude (Myco kernel agent, autonomous run under explicit user grant, Wave 41)

**Motivation**: Wave 26 D3 friction-driven scout. With Waves 38–40 closing the
Wave 37 D7 followup triple (L19 dimension count + L20 translation mirror + L21
contract version inline), the next-priority scar class is whatever surfaces in
the boot brief / hunger / pytest suite. The Wave 41 scout against the post-Wave-40
substrate found exactly that: 10 raw notes in `notes/`, of which 7 were tagged
`wave{25,26,27,28,30,31,32}-seed` at `digest_count: 0` even though all 7 of those
waves had landed milestones in `log.md`. These were evidence bundles captured as
input to each wave's craft, but never advanced past `raw` after the wave's
closing commit. They violated anchor #3 (the seven-step metabolic pipeline:
raw → digesting → extracted/integrated/excreted) silently — `myco hunger`'s two
existing raw signals do NOT catch this pattern:

- `raw_backlog` fires at `>10` raw notes; we sat at exactly 10, just under the threshold.
- `stale_raw` requires `last_touched ≥ 7 days`; the seeds were all under 24 hours old.

Both signals are coarse threshold heuristics that miss a structural post-condition
(specifically: "if a wave creates a `wave{N}-seed` raw note, that note must
advance out of raw before the wave's milestone lands in log.md"). L22 fills the
gap with a referential check grounded in `log.md` instead of count/time
thresholds. Without an automated check, every future wave that captures a seed
bundle for its craft risks repeating the exact silent rot Wave 41 was created
to fix.

**Wave 26 D3 friction-driven ordering** — Wave 40's closing doctrine declared:
*"Wave 41+ re-evaluates Wave 26 D3 friction-driven ordering against fresh
friction signals — the next-priority scar class is no longer the contract
version triple but whatever surfaces in the boot brief / hunger / pytest suite
as the next reproducible silent-rot pattern."* The Wave 41 scout honored this
verbatim: 7 visible orphans in the post-Wave-40 boot brief is the highest-leverage
silent rot, and the existing hunger thresholds are structurally blind to it.

**Authoritative craft**:
`docs/primordia/archive/wave_seed_lifecycle_craft_2026-04-12.md`
(kernel_contract class, 3 rounds, current_confidence = target_confidence = 0.90,
single-author convention floor honored). The craft enumerates 9 decisions
(D1-D9) on the L22 design surface and produces a 15-item landing list which
this changelog entry mirrors as the contract-bump record.

**Changes** (each numbered change implements one Wave 41 craft decision):

1. **L22 lint dimension added** — `src/myco/lint.py` gains
   `lint_wave_seed_orphan(canon, root)` plus the helper
   `_l22_parse_closed_waves(root)` and two module-level constants
   (`_L22_WAVE_SEED_RE = re.compile(r"^wave(\d+)-seed$")` and
   `_L22_MILESTONE_RE = re.compile(r"\*\*Wave\s+(\d+)\s+landed[^*]*\*\*", re.IGNORECASE)`).
   The substrate's `len(FULL_CHECKS)` SSoT (Wave 38 D2) automatically advances
   from 22 → 23 because L22 is appended to `FULL_CHECKS`. L19 dogfoods this
   transition (third consecutive wave to do so after Waves 39 + 40): every
   narrative surface that still claims "22-dimension" becomes a HIGH issue at
   the next `myco immune` run, forcing the entire change-set to land in lockstep
   — the very anti-rot mechanism Wave 38 built.

2. **Detection rule** (Wave 41 D1): a note is a wave-seed orphan iff ALL of:
   (a) `status == "raw"`, (b) some tag matches the regex `^wave(\d+)-seed$`,
   (c) the parsed wave number has a `**Wave N landed**` milestone in `log.md`.
   The detection is **structurally referential** rather than threshold-based —
   it grounds enforcement on the cross-file relationship between
   `notes/n_*.md::tags` and `log.md::milestones` rather than on count or time.
   The first matching tag wins to bound noise (one issue per orphan note, not
   per matching tag).

3. **log.md milestone parser** (Wave 41 D3): `_l22_parse_closed_waves(root)`
   reads `log.md` once per lint run and returns the set of integers parsed
   from `**Wave N landed**` bold headers (with optional trailing parenthetical
   context inside the bold). The bold-header shape has been stable across 40+
   waves of log.md history (verified via grep — 101 wave references match).
   If `log.md` is missing or contains no landed milestones, L22 returns an
   empty issue list (Wave 41 §C8 silent pass — nothing to enforce).

4. **HIGH severity per orphan** (Wave 41 D4): every orphan emits a HIGH-severity
   issue against the note path with a structured advance hint
   (`myco digest --to extracted <id>`). No tier system — the wave-seed pattern
   is uniformly high-impact because it represents a captured-but-unprocessed
   evidence bundle that still claims attention from the substrate's view layer
   while being structurally orphaned from the seven-step pipeline.

5. **In-flight wave clause** (Wave 41 §0.2): seeds tagged for waves NOT yet
   landed in `log.md` are legitimate in-flight evidence and are NOT flagged.
   This is the principal false-positive escape — without it, every active
   wave's seed bundle would be marked as a violation while the wave is still
   being crafted. The clause is enforced by membership check against the
   parsed `closed_waves` set rather than a separate filter pass.

6. **Out-of-scope clauses** (Wave 41 §0.2 + Wave 41 D1): L22 explicitly does
   NOT enforce: (a) that every wave MUST create a seed bundle (which would
   punish Waves 38-40 efficient pattern), (b) that seeds must reach a specific
   terminal state (extracted/integrated/excreted are all valid terminations),
   (c) that non-wave-tagged raw notes must advance (generic raw backlog is
   `raw_backlog`/`stale_raw` hunger's job), (d) seeds in `digesting` (advanced
   once, then forgotten — separate dimension if it ever surfaces).

7. **Tag pattern strictness** (Wave 41 D6): the tag regex is the exact
   `^wave(\d+)-seed$` shape (anchored, no loose variations). Tags like
   `wave-25-seed`, `wave_25_seed`, `wave 25 seed`, or `seed-wave25` do NOT
   match. This is a deliberate Goodhart-defense: the tag must be the exact
   canonical wave-seed shape for L22 to enforce the post-condition, otherwise
   L22 could be silently bypassed by typos that present as legitimate tags
   to the rest of the substrate.

8. **Contract version bump** v0.31.0 → v0.32.0 in `_canon.yaml`,
   `src/myco/templates/_canon.yaml`, and this changelog. `synced_contract_version`
   mirrors the bump to keep L17 quiescent. The minor bump matches the
   "new lint dimension" precedent set by L18 (v0.26.0), L19 (v0.29.0),
   L20 (v0.30.0), L21 (v0.31.0).

9. **4 unit tests added** — `tests/unit/test_lint_wave_seed_orphan.py`
   covers the four scar classes (Wave 41 D8):
   `test_l22_clean_substrate_passes` (D1 base case — empty notes/ and log.md
   produce no issues),
   `test_l22_orphan_caught_high` (D1+D4 principal scar — raw `wave25-seed`
   when Wave 25 landed in log.md surfaces as HIGH with the advance hint),
   `test_l22_pre_landing_seed_silent_pass` (§0.2 in-flight wave clause —
   `wave42-seed` while Wave 42 has not landed must NOT be flagged),
   `test_l22_no_tag_raw_silent_pass` (§0.2 out-of-scope — raw notes without
   wave-seed tags are not L22's responsibility).
   Each test pulls `lint_wave_seed_orphan` directly (no CLI roundtrip) and
   uses the existing `_isolate_myco_project` fixture from `tests/conftest.py`.
   The suite count advances 34 → 38.

10. **15+ narrative surfaces bumped 22-dimension/L0-L21/22%2F22 →
    23-dimension/L0-L22/23%2F23** (Wave 41 D9 — operational landing). The
    bump set is: README.md (badge + version row + L22 bullet + lint command
    table row 22→23), README_zh.md (badge + version row + verb table count),
    README_ja.md (badge + version row + L22 bullet + verb table count),
    MYCO.md (5 lines: 2 contract version + 3 dimension count: kernel
    contract row, current stage row, lint immune-system invariant,
    lint_coverage_confidence row, project summary row, contract phase
    tracker, scripts script index), CONTRIBUTING.md (lint module comment),
    wiki/README.md (`myco immune` 应 23/23 绿), docs/reusable_system_design.md
    (`lint_dimensions: 23`), src/myco/cli.py (Wave 29 immune comment + lint
    parser help), src/myco/init_cmd.py (lint shim message),
    scripts/myco_init.py (mirror), src/myco/migrate.py (shim message),
    scripts/myco_migrate.py (mirror), src/myco/immune.py (docstring 22→23
    + L0-L21→L0-L22 + add L22 bullet + add lint_wave_seed_orphan to imports
    + __all__), src/myco/mcp_server.py (4 edits: tools header, tool annotation
    title, full L0-L22 enumeration with L21+L22 added in docstring, mode
    label), src/myco/lint.py (header `22-Dimension` → `23-Dimension`,
    dimension table row added, FULL_CHECKS comment `L0-L21` → `L0-L22`).

11. **7 wave-seed orphans healed** (Wave 41 D9 — the exact scars that justified
    L22 in the first place):
    - `wave25-seed` raw note → `extracted` via `myco digest --to extracted`
    - `wave26-seed` raw note → `extracted`
    - `wave27-seed` raw note → `extracted`
    - `wave28-seed` raw note → `extracted`
    - `wave30-seed` raw note → `extracted`
    - `wave31-seed` raw note → `extracted`
    - `wave32-seed` raw note → `extracted`
    Default terminal target is `extracted` because (a) the seed served as
    craft input and is now historical, (b) `integrated` would wrongly claim
    the seed itself is active wisdom (the craft is the active wisdom, not the
    seed), (c) `excreted` would wrongly claim the seed was not useful (it
    was — it provided the evidence base for the craft). These were the
    original load-bearing evidence for the Wave 41 craft.

**Verification** (every check must be green at COMMIT boundary):

- `PYTHONPATH=src python -m myco.cli lint` — full sweep returns 23/23 PASS.
  L19 is the canary: any narrative surface claiming "22-dimension" or
  "L0-L21" or "Lint-22%2F22" produces a HIGH issue. After all 15+ surfaces
  bump, L19 returns to PASS and L20 also passes (the 3 locale READMEs
  already mirror after the badge bumps). L21 passes because the
  6 inline contract version claims (MYCO.md + docs/adapters/README.md) now
  match canon. L22 passes because the 7 orphans were healed via
  `myco digest --to extracted`.
- `python -m pytest tests/ -q` — 38 tests pass (34 prior + 4 Wave 41
  L22 tests).
- `git diff _canon.yaml` shows `contract_version: "v0.31.0"` →
  `"v0.32.0"` AND `synced_contract_version: "v0.31.0"` →
  `"v0.32.0"` (L17 quiescence).
- `myco hunger` refreshes `.myco_state/boot_brief.md` with the new
  Wave 41 milestone visible (L16 freshness).

**Backward compatibility**: Pure additive. Projects on contract v0.31.0
silently inherit L22 on `pip install -U myco` and will see at most a
new HIGH issue if their notes/ contain raw `wave{N}-seed` tagged notes
where wave N has already landed in their `log.md`. The remediation is
always `myco digest --to <terminal_state> <note_id>` — no removal, no
migration. The `extracted` target is recommended for historical evidence
seeds; `integrated` for active wisdom; `excreted` only when the seed was
not useful. No existing API changes, no removed surfaces, no migration
required.

**Forward path**: With L22 landing, the substrate now enforces the seven-step
pipeline post-condition for the most fragile referential surface (wave-seed
notes). The Wave 26 D3 friction-driven ordering continues for Wave 42+: the
next scout will identify the next reproducible silent-rot pattern from the
post-Wave-41 boot brief / hunger / pytest signals. Candidate areas observed
during the Wave 41 scout but deferred (Wave 41 §4.4): (a) `inlet_ripe`
hunger advisory (Open Problem #2 — Metabolic Inlet trigger signals);
(b) continuous compression background task (Open Problem #4); (c) C-layer
structural decay detector (Open Problem #5); (d) D-layer full implementation
(Open Problem #6 — currently seeded only). None of these are higher-leverage
than L22 was at the Wave 41 scout, so the friction-driven ordering will
re-evaluate from fresh signals at Wave 42 scout time.

**Limitations** (honest, from Wave 41 craft §4.3):

- L1: the wave-seed tag pattern is exact `^wave(\d+)-seed$`. Operator typos
  like `wave-25-seed` or `wave25_seed` will silently bypass L22 enforcement.
  This is a Goodhart-defense trade-off: tightening the regex would catch more
  typo variants but also expand the false-positive surface. The next manual
  sweep (or a future L23 if the typo class becomes a real friction signal)
  can amend the regex.
- L2: L22 only catches the **post-condition** of seven-step pipeline (raw
  → not-raw after wave closes). It does NOT catch the converse failure
  (non-seed evidence captured during a wave but never tagged as a seed).
  That's a separate dimension if it ever surfaces — Wave 41 deliberately
  scopes L22 to the exact pattern observed in the scout.
- L3: the `log.md` milestone regex `\*\*Wave\s+(\d+)\s+landed[^*]*\*\*` is
  format-fragile. If a future wave changes the milestone format (e.g. removes
  the `landed` keyword or switches from bold to a different markdown pattern),
  L22 will stop detecting closed waves and silently pass orphans. This is the
  same fragility as Wave 38's L19 surface allowlist or Wave 39's L20 skeleton
  parser — format changes need to update the lint regex in lockstep, and a
  future doctrine entry might lock in the milestone format as kernel surface.
- L4: the default healing target `extracted` is a heuristic recommendation,
  not a structurally-correct choice. Operators may legitimately prefer
  `integrated` (if the seed becomes active wisdom) or `excreted` (if the
  seed was not useful). The advance hint string in the lint output names
  `extracted` as the default but operators can pick any terminal status.

---

## v0.31.0 — 2026-04-12 (minor · L21 contract version inline consistency, Wave 40 — forward-looking inline contract version SSoT enforcement)

**Author**: Claude (Myco kernel agent, autonomous run under explicit user grant, Wave 40)

**Motivation**: Wave 37 D7 followup #3 — the third + final candidate from the Wave 37
manual sweep. Wave 38 closed followup #1 (L19, lint dimension count consistency) and
Wave 39 closed followup #2 (L20, translation mirror skeleton parity). The Wave 40 scout
discovered the exact scar that justifies followup #3: `MYCO.md` lines 4, 22, and 159
plus `docs/adapters/README.md` line 14 were ALL still claiming `kernel contract v0.28.0`
even though the canonical contract version had advanced through v0.29.0 (Wave 38) and
v0.30.0 (Wave 39) without those inline narrative claims being touched. The Waves 38+39
manual sweeps caught dozens of dimension references and locale skeleton drifts but
left these contract version inline claims behind because they live in different
prose patterns ("kernel contract vX.Y.Z" rather than "L0-LXX" or "X-dimension"). L19
and L20 cannot see them — they look at counts and structures, not at version numbers
embedded in narrative sentences. Without an automated check, every future wave that
bumps the contract version risks repeating the exact silent rot Wave 40 was created
to fix.

**Wave 26 D3 friction-driven ordering** — Wave 37 D1 named the top-3 followups as:
(1) ground-truth lint for LINT_DIMENSION_COUNT → Wave 38 (v0.29.0, L19),
(2) translation-mirror lint → Wave 39 (v0.30.0, L20),
(3) contract-version-inline lint → THIS WAVE 40 (v0.31.0, L21). With L21 landing,
the Wave 37 D7 followup triple is **closed**: all three top-friction silent-rot
scar classes (dimension count, locale skeleton, version string) now have automated
regression-test guards instead of manual-sweep dependence.

**Authoritative craft**:
`docs/primordia/archive/contract_version_inline_craft_2026-04-12.md`
(kernel_contract class, 3 rounds, current_confidence = target_confidence = 0.90,
single-author convention floor honored). The craft enumerates 9 decisions
(D1-D9) on the L21 design surface and produces a 15-item landing list which
this changelog entry mirrors as the contract-bump record.

**Changes** (each numbered change implements one Wave 40 craft decision):

1. **L21 lint dimension added** — `src/myco/lint.py` gains
   `lint_contract_version_inline(canon, root)` plus the helper
   `_l21_is_historical(line, prev_nonblank_line)` and four module-level
   constants (`_L21_HIGH_FILES`, `_L21_MEDIUM_FILES`, `_L21_SKIP_MARKER`,
   plus three regex patterns: `_L21_FORWARD_RE`, `_L21_DATE_RE`,
   `_L21_TRANSITION_RE`, and the `_L21_HISTORICAL_VERBS` tuple). The
   substrate's `len(FULL_CHECKS)` SSoT (Wave 38 D2) automatically advances
   from 21 → 22 because L21 is appended to `FULL_CHECKS`. L19 dogfoods
   this transition: every narrative surface that still claims
   "21-dimension" becomes a HIGH issue at the next `myco immune` run,
   forcing the entire change-set to land in lockstep — the very anti-rot
   mechanism Wave 38 + 39 already proved out.

2. **Forward-looking pattern** (Wave 40 D2):
   `(?i)(kernel contract|当前 contract|current contract)\s*[:：]?\s*(v?\d+\.\d+\.\d+)`.
   The pattern is intentionally **forward-looking only** — it does NOT try
   to match every "vX.Y.Z" string in the substrate (which would over-fire
   catastrophically against history-laden narratives). It only matches
   lines whose syntactic shape claims a *current* contract state ("kernel
   contract = vX.Y.Z" form). Both the ASCII colon `:` and the full-width
   colon `：` are tolerated. Both `vX.Y.Z` and bare `X.Y.Z` are tolerated.
   Multi-language: English `kernel contract` / English `current contract` /
   Chinese `当前 contract` are the three accepted prefix forms.

3. **8-clause historical-marker filter** (Wave 40 D2 §1.2): every matched
   line is then run through `_l21_is_historical()` which returns True
   (skip the line) if ANY of these clauses fire:
   - Operator skip-marker `<!-- l21-skip -->` on the previous non-blank line
   - A date-in-parens stamp `(20YY-MM-DD)` anywhere in the line
   - A two-version transition arrow `vX.Y.Z → vA.B.C` (or `->`) in the line
   - A historical-event verb in the line: `landed`, `landing`, `落地`,
     `已完成`, `完成`, `post-rebase`, `supersedes`, `succeeded`, `✅`
   - The line starts with `|` (markdown table row — Phase tracker shape)
   This filter is **deliberately biased toward false negatives** (skip on
   ambiguity). The cost of one missed drift caught on the next wave is
   lower than the cost of operators learning to ignore noisy lint output.

4. **File allowlist** (Wave 40 D3):
   - HIGH: `MYCO.md`, `README.md`, `README_zh.md`, `README_ja.md` — the
     four entry-point and locale-front-door surfaces. A drifted contract
     version claim here is the highest-impact possible silent rot.
   - MEDIUM: `docs/adapters/README.md`, `CONTRIBUTING.md`,
     `docs/architecture.md`, `docs/vision.md`, `docs/theory.md` — adapter
     contract surface and doctrinal docs. Operators that develop against
     these read them frequently; drift erodes trust slower but still
     erodes it.
   - All other files (log.md, contract_changelog.md, primordia/, notes/,
     examples/ascc/, src/, tests/, scripts/) are **out of scope** by
     design (Wave 40 §0.3). Append-only history surfaces must NEVER be
     touched by the lint; source code uses string literals for legitimate
     reasons; tests need to enumerate stale versions on purpose.

5. **Skip-marker escape hatch** (Wave 40 D5): the operator escape valve is
   `<!-- l21-skip -->` on the line immediately preceding the version claim.
   This is the same shape as Wave 39's L20 skip marker (`<!-- l20-skip -->`)
   and the parser logic mirrors it. Use cases: tutorial pages comparing
   against an older contract, or documentation showing an upstream tool's
   contract version that legitimately disagrees with Myco's own canon.

6. **Code-fence-aware parser** (Wave 40 D2 §C6): `lint_contract_version_inline`
   is a stateful line walker that tracks ` ``` ` open/close state. Lines
   inside code fences are skipped entirely — code samples in tutorials may
   show legitimate contract version literals that should not be enforced.
   The fence tracker handles trailing whitespace via `rstrip()` and CRLF
   via `splitlines()` transparently, mirroring Wave 39's `_count_skeleton`.

7. **Severity matrix** (Wave 40 D4): HIGH for the entry-point + locale
   front-door tier (`_L21_HIGH_FILES`), MEDIUM for the doctrinal/contrib
   tier (`_L21_MEDIUM_FILES`). Severity tiers map to tee-up urgency: HIGH
   blocks the lint pass-rate badge, MEDIUM is informational but still
   reported. Both fire under the same lint pass — there is no opt-out
   beyond the explicit skip marker.

8. **Contract version bump** v0.30.0 → v0.31.0 in `_canon.yaml`,
   `src/myco/templates/_canon.yaml`, and this changelog. `synced_contract_version`
   mirrors the bump to keep L17 quiescent. The minor bump matches the
   "new lint dimension" precedent set by L18 (v0.26.0), L19 (v0.29.0),
   L20 (v0.30.0), and the Wave 24 L17 landing.

9. **4 unit tests added** — `tests/unit/test_lint_contract_version_inline.py`
   covers the four scar classes (Wave 40 D8):
   `test_l21_clean_substrate_passes` (D1 base case),
   `test_l21_stale_inline_caught_high` (D1+D4 principal scar — the
   exact MYCO.md:4/22/159 + adapters/README.md:14 shape),
   `test_l21_historical_marker_skipped` (D2 §1.2 filter false-negative
   bias — the "landed" + date-in-parens shape),
   `test_l21_skip_marker_respected` (D5 operator escape hatch).
   Each test pulls `_L21_SKIP_MARKER` and `lint_contract_version_inline`
   directly (no CLI roundtrip) and uses the existing `_isolate_myco_project`
   fixture from `tests/conftest.py`. The suite count advances 30 → 34.

10. **15+ narrative surfaces bumped 21-dimension/L0-L20/21%2F21 →
    22-dimension/L0-L21/22%2F22** (Wave 40 D9 — operational landing). The
    bump set is: README.md (badge + version row + L21 bullet + lint command
    table row 19→22), README_zh.md (badge + version row + verb table count),
    README_ja.md (badge + version row + L21 bullet + verb table count),
    MYCO.md (4 lines: 22 维 lint headline + lint_coverage_confidence row +
    contract version row + verb table count), CONTRIBUTING.md (lint module
    comment), wiki/README.md (`myco immune` 应 22/22 绿),
    docs/reusable_system_design.md (`lint_dimensions: 22`), src/myco/cli.py
    (replace_all `21-dimension` → `22-dimension` + Wave 29 immune comment),
    src/myco/init_cmd.py (lint shim message), scripts/myco_init.py (mirror),
    src/myco/migrate.py (shim message), scripts/myco_migrate.py (mirror),
    src/myco/immune.py (docstring 21→22 + L0-L20→L0-L21 + add L21 bullet
    + add lint_contract_version_inline to imports + __all__),
    src/myco/mcp_server.py (4 edits: tools header, tool annotation title,
    full L0-L21 enumeration in docstring, mode label), src/myco/lint.py
    (header `21-Dimension` → `22-Dimension`, dimension table row added,
    FULL_CHECKS comment `L0-L20` → `L0-L21`).

11. **4 stale inline contract version claims fixed** (Wave 40 D9 — the
    exact scars that justified L21 in the first place):
    - `MYCO.md:4` `kernel contract v0.28.0` → `v0.31.0`
    - `MYCO.md:22` `kernel contract v0.28.0` → `v0.31.0`
    - `MYCO.md:159` `当前 contract v0.28.0 (Wave 36)` → `v0.31.0 (Wave 40)`
    - `docs/adapters/README.md:14` `kernel contract v0.28.0` → `v0.31.0`
    These were the original load-bearing evidence for the Wave 40 craft —
    if L21 had existed during Waves 38/39, these drifts would have been
    caught at lint time instead of accumulating across two minor bumps.

**Verification** (every check must be green at COMMIT boundary):

- `PYTHONPATH=src python -m myco.cli lint` — full sweep returns 22/22 PASS.
  L19 is the canary: any narrative surface claiming "21-dimension" or
  "L0-L20" or "Lint-21%2F21" produces a HIGH issue. After all 15+ surfaces
  bump, L19 returns to PASS and L20 also passes (the 3 locale READMEs
  already mirror after the badge bumps). L21 itself passes because the
  4 inline claims now match canon.
- `python -m pytest tests/ -q` — 34 tests pass (30 prior + 4 Wave 40
  L21 tests).
- `git diff _canon.yaml` shows `contract_version: "v0.30.0"` →
  `"v0.31.0"` AND `synced_contract_version: "v0.30.0"` →
  `"v0.31.0"` (L17 quiescence).
- `myco hunger` refreshes `.myco_state/boot_brief.md` with the new
  Wave 40 milestone visible (L16 freshness).

**Backward compatibility**: Pure additive. Projects on contract v0.30.0
silently inherit L21 on `pip install -U myco` and will see at most a
new HIGH issue if their narrative surfaces have inline contract version
drift. Operators can add `<!-- l21-skip -->` markers above intentionally
divergent claims (tutorials, upstream comparisons) to keep L21 green
without removing the content. No existing API changes, no removed
surfaces, no migration required.

**Forward path**: With Wave 37 D7 followup triple closed (L19 + L20 + L21),
the substrate's three top staleness scar classes (dimension count, locale
skeleton, contract version string) all become regression-testable instead
of relying on manual sweeps. Wave 41+ re-evaluates Wave 26 D3 friction-driven
ordering against fresh friction signals — the next-priority scar class is
no longer the contract version triple but whatever surfaces in the boot
brief / hunger / pytest suite as the next reproducible silent-rot pattern.

**Limitations** (honest, from Wave 40 craft §4.3):

- L1: the forward-looking pattern recognizes only three prefix forms
  (`kernel contract`, `current contract`, `当前 contract`). Other
  legitimate forward claim shapes (e.g. `contract version is now vX.Y.Z`,
  `Myco at vX.Y.Z`) are not caught. Adding new prefix forms requires a
  one-line regex amendment + a craft if the shape is doctrinal.
- L2: the historical-marker filter is biased toward false negatives. A
  truly drifted line that happens to contain the word "landed" or a date
  will be silently skipped. This is the deliberate trade against false
  positives (which would erode trust in lint output). The next time a
  wave manually sweeps the substrate, any silently-skipped drift will
  surface.
- L3: package version (`__version__` / `pyproject.toml`) is intentionally
  out of scope per Wave 8 re-baseline doctrine — package version and
  contract version are independent SemVer lines. A future `_L22_PACKAGE_VERSION`
  lint could enforce package version inline, but that needs its own craft.
- L4: the file allowlist is hardcoded. New entry-point or doctrinal
  surfaces require a one-line patch + a contract bump (or at minimum a
  craft if they imply doctrine).

---

## v0.30.0 — 2026-04-12 (minor · L20 translation mirror consistency, Wave 39 — locale README skeleton parity enforcement)

**Author**: Claude (Myco kernel agent, autonomous run under explicit user grant, Wave 39)

**Motivation**: Wave 37 D7 followup #2 + Wave 38 forward path: between Wave 30 and
Wave 37, the README badge drift scar (caught by L19 in Wave 38) was only one face
of a deeper rot — the three locale READMEs (`README.md`, `README_zh.md`,
`README_ja.md`) had diverged structurally over the wave sequence. New sections
got added to one locale and forgotten in others; old sections got removed from
one and stranded in others. Non-English readers were silently seeing a degraded
substrate while English readers saw a healthy one. L19 catches **count drift**
(narrative cache claims "15-dimension" when substrate is "21-dimension"); L20
closes the orthogonal **structural drift** (one locale has section X, another
doesn't) — together they make the locale READMEs a load-bearing immune surface
instead of three independently-rotting copies.

**Wave 26 D3 friction-driven ordering** — Wave 37 D1 named the top-3 followups as:
(1) ground-truth lint for LINT_DIMENSION_COUNT → Wave 38 (v0.29.0, L19),
(2) translation-mirror lint → THIS WAVE 39 (v0.30.0, L20),
(3) contract-version-inline lint → Wave 40+. Wave 39 lands followup #2 and
keeps the friction-driven sequence intact.

**Authoritative craft**:
`docs/primordia/archive/translation_mirror_lint_craft_2026-04-12.md`
(kernel_contract class, 3 rounds, current_confidence = target_confidence = 0.90,
single-author convention floor honored). The craft enumerates 9 decisions
(D1-D9) on the L20 design surface and produces a 15-item landing list which
this changelog entry mirrors as the contract-bump record.

**Changes** (each numbered change implements one Wave 39 craft decision):

1. **L20 lint dimension added** — `src/myco/lint.py` gains
   `lint_translation_mirror_consistency(canon, root)` plus the 75-line
   `_count_skeleton(content)` helper. The 5-tuple skeleton
   `(h2, h3, code, table_rows, badge)` is the parity unit (Wave 39 D1). The
   substrate's `len(FULL_CHECKS)` SSoT (Wave 38 D2) automatically advances
   from 20 → 21 because L20 is appended to `FULL_CHECKS`. L19 will dogfood
   this transition: every narrative surface that still claims "20-dimension"
   becomes a HIGH issue at the next `myco immune` run, forcing the entire
   change-set to land in lockstep (the very anti-rot mechanism Wave 38 built).

2. **L20 reference is `README.md`** (Wave 39 D2): the English README is the
   source of truth for skeleton parity. If `README.md` is missing (greenfield
   project), the fallback (Wave 39 D2 §C2) picks the locale README with the
   highest h2_count as the most-developed reference. If fewer than 2 locale
   READMEs exist (Wave 39 §C1), L20 silently passes — there is nothing to
   mirror against.

3. **Severity = HIGH** (Wave 39 D4): every drifted skeleton component
   produces a HIGH issue against the drifted file. README is the user-facing
   first-impression surface in three languages; soft-warning severity would
   normalize ignoring the rot.

4. **Skip-marker escape hatch** (Wave 39 D5): a section preceded by
   `<!-- l20-skip -->` on the previous non-blank line is excluded from the
   skeleton count. This is the operator's escape hatch for genuinely
   locale-specific sections (e.g. a Chinese-only "致谢" or Japanese-only
   "謝辞") that have no structural counterpart in English. Without this,
   operators would have to remove locale-native content to keep L20 green
   — exactly the wrong incentive.

5. **Code-fence-aware parser** (Wave 39 D6): `_count_skeleton` is a stateful
   line walker that tracks fence open/close state. H2/H3/`|`/badge lines
   inside ` ``` ` blocks are NOT counted. Without this, README files
   containing inline markdown samples (e.g. a `## fake heading` inside a
   `\`\`\`markdown` fence) would produce false-positive drift. The parser
   handles trailing whitespace (`rstrip()`) and CRLF (`splitlines()`)
   transparently (Wave 39 §3.1 C5/C6).

6. **Locale allowlist is explicit** (Wave 39 §0.3 + D1): only
   `README.md`, `README_zh.md`, `README_ja.md` participate. Other locales
   (e.g. a future `README_es.md`) require an explicit addition to
   `_L20_LOCALE_READMES`. This is intentional — drive-by detection of every
   `README_*.md` file would over-fire on adapter-internal locale variants.

7. **Contract version bump** v0.29.0 → v0.30.0 in `_canon.yaml`,
   `src/myco/templates/_canon.yaml`, and this changelog. `synced_contract_version`
   mirrors the bump to keep L17 quiescent. The minor bump matches the
   "new lint dimension" precedent set by L18 (v0.26.0), L19 (v0.29.0), and
   the Wave 24 L17 landing.

8. **4 unit tests added** — `tests/unit/test_lint_translation_mirror.py`
   covers the four scar classes (Wave 39 D8):
   `test_l20_clean_substrate_passes` (D1 base case),
   `test_l20_section_drop_caught` (D1+D4 principal scar),
   `test_l20_skip_marker_respected` (D5 escape hatch),
   `test_l20_code_fence_aware` (D6 parser invariant).
   Each test pulls `_count_skeleton` and `lint_translation_mirror_consistency`
   directly (no CLI roundtrip) and uses the existing `_isolate_myco_project`
   fixture from `tests/conftest.py`. The suite count advances 26 → 30.

9. **15+ narrative surfaces bumped 20-dimension/L0-L19/20%2F20 →
   21-dimension/L0-L20/21%2F21** (Wave 39 D9 — operational landing). The
   bump set is: README.md (badge + version row + L20 bullet), README_zh.md
   (badge + version row + verb table count), README_ja.md (badge + version
   row + L20 bullet + verb table count), MYCO.md (4 lines: 21 维 lint
   headline + lint_coverage_confidence row + contract version row + verb
   table count), CONTRIBUTING.md (lint module comment), wiki/README.md
   (`myco immune` 应 21/21 绿), docs/reusable_system_design.md
   (`lint_dimensions: 21`), src/myco/cli.py (replace_all
   `20-dimension` → `21-dimension` + Wave 29 immune comment),
   src/myco/init_cmd.py (lint shim message), scripts/myco_init.py (mirror),
   src/myco/migrate.py (shim message), scripts/myco_migrate.py (mirror),
   src/myco/immune.py (docstring 20→21 + L0-L19→L0-L20 + add L20 bullet
   + add lint_dimension_count_consistency + lint_translation_mirror_consistency
   to imports + __all__ — closes a Wave 38 oversight where L19 was missing
   from immune.py exports), src/myco/mcp_server.py (4 edits: tools header,
   tool annotation title, full L0-L20 enumeration in docstring, mode label),
   src/myco/lint.py (header `20-Dimension` → `21-Dimension`, dimension table
   row added, FULL_CHECKS comment `L0-L19` → `L0-L20`).

**Verification** (every check must be green at COMMIT boundary):

- `PYTHONPATH=src python -m myco.cli lint` — full sweep returns 21/21 PASS.
  L19 is the canary: any narrative surface claiming "20-dimension" or
  "L0-L19" or "Lint-20%2F20" produces a HIGH issue. After all 15+ surfaces
  bump, L19 returns to PASS and L20 also passes (the 3 locale READMEs
  already mirror after the badge bumps).
- `python -m pytest tests/ -q` — 30 tests pass (26 prior + 4 Wave 39
  L20 tests).
- `git diff _canon.yaml` shows `contract_version: "v0.29.0"` →
  `"v0.30.0"` AND `synced_contract_version: "v0.29.0"` →
  `"v0.30.0"` (L17 quiescence).
- `myco hunger` refreshes `.myco_state/boot_brief.md` with the new
  Wave 39 milestone visible (L16 freshness).

**Backward compatibility**: Pure additive. Projects on contract v0.29.0
silently inherit L20 on `pip install -U myco` and will see at most a
new HIGH issue if their locale READMEs have skeleton drift. Operators can
add `<!-- l20-skip -->` markers above intentionally locale-specific sections
to keep L20 green without removing the content. No existing API changes,
no removed surfaces, no migration required.

**Forward path**: Wave 40+ implements Wave 37 D7 followup #3 — the
contract-version-inline lint. This will catch the orthogonal scar where
`docs/contract_changelog.md` claims a version that disagrees with
`_canon.yaml::system.contract_version` or where `__version__` strings in
Python modules drift away from the canonical contract version. With L19,
L20, and the future L21, the substrate's three top staleness scar classes
(dimension count, locale skeleton, version string) all become regression-
testable instead of relying on manual sweeps.

**Limitations** (honest, from Wave 39 craft §4.3):

- L1: skeleton parity is structural, not semantic. Two READMEs can have
  identical 5-tuples while their content drifts apart in meaning. L20
  catches "the table got removed from one locale" but not "the table
  got rewritten with different rows in one locale". The 5-tuple is a
  necessary-not-sufficient signal; semantic parity remains a human
  review concern.
- L2: the badge regex `\bLint-\d+%2F\d+\b` only matches the URL-encoded
  shields.io form. Non-shields.io badges (e.g. a custom SVG) won't be
  counted. This is acceptable because shields.io is the de-facto
  convention across the substrate's three READMEs.
- L3: `_count_skeleton` parses line-by-line and is not a full markdown
  parser. Edge cases like indented fences (`    \`\`\``) or HTML
  `<table>` tags are not handled. The current substrate uses neither;
  if a future locale README adopts them, an L20 false negative becomes
  possible and a parser upgrade is the appropriate response.
- L4: the locale allowlist is hardcoded. Adding `README_es.md` requires
  a code change to `_L20_LOCALE_READMES`. This is intentional (Wave 39
  D1 §C7) to avoid drive-by detection over-firing on adapter-internal
  variants, but it means new locales need a one-line patch + a contract
  bump (or at minimum a craft if they imply doctrine).

---

## v0.29.0 — 2026-04-12 (minor · L19 lint dimension count consistency + LINT_DIMENSION_COUNT SSoT enforced, Wave 38 — narrative-cache anti-drift)

**Author**: Claude (Myco kernel agent, autonomous run under explicit user grant, Wave 38)

**Motivation**: Wave 37 (the README + doctrinal-surface staleness sweep) discovered that
between Wave 30 (when L18 landed and the substrate moved from 14→15→…→19 dimensions
across the L15-L18 sequence) and Wave 37 (when the manual sweep caught it), 15+ narrative
surfaces had silently rotted to claim "15-dimension / L0-L14" while the actual substrate
was at 19 dimensions / L0-L18. Affected surfaces included the README badge (user-facing
first impression!), MYCO.md headlines, mcp_server.py docstrings + tool descriptions,
CONTRIBUTING.md, wiki/README.md, immune.py, the migrate/init scripts, and several docs/
files. The drift was invisible because no automated check compared the narrative
references against structural ground truth — `len(FULL_CHECKS)` in `src/myco/lint.py`.
Wave 37 closed the immediate drift but ranked an automated guard as the #1 followup
(Wave 37 D7 candidate #1). This wave delivers that guard.

**Why a structural lint, not a one-time script**: Wave 38 craft §2 Attack A defends
permanence. A one-time fix script run today would protect against today's drift; it
would do nothing the next time a wave adds L20. A structural check encoded as a lint
dimension is the substrate-native way to make any consistency invariant *permanently*
hold — every future `myco immune` invocation re-runs it for free, and any wave that
forgets to bump downstream caches trips L19 immediately. The cost (one new dimension,
five regex patterns, ~120 lines including the surface lists and docstring) is paid
once; the protection is paid forward indefinitely.

**Why this is a kernel_contract change** (not a public_claim): L19 modifies the
behavior of `myco immune` (a load-bearing CLI verb), introduces a new lint dimension
(adds to `FULL_CHECKS` — the SSoT for LINT_DIMENSION_COUNT), and bumps the kernel
contract version that downstream instances synchronize against. All three are
kernel_contract trigger surfaces per `docs/agent_protocol.md`, so the wave must
land via a kernel_contract craft (target_confidence ≥ 0.90, ≥ 3 rounds, single-author
equality not strict-less-than per `docs/craft_protocol.md §4` floor for kernel_contract).
Authoritative craft: `docs/primordia/archive/lint_dimension_count_consistency_craft_2026-04-12.md`
(D1-D9, 3 rounds, target=current=0.90).

**Changes**:

1. **NEW lint dimension L19 — Lint Dimension Count Consistency**:
   `src/myco/lint.py::lint_dimension_count_consistency` reads `len(FULL_CHECKS)` at
   call time and scans 4 HIGH-severity narrative surfaces (README.md, README_zh.md,
   README_ja.md, MYCO.md) + 11 MEDIUM-severity surfaces (CONTRIBUTING.md,
   wiki/README.md, src/myco/{cli,immune,mcp_server,migrate,init_cmd}.py,
   scripts/myco_{init,migrate}.py, docs/reusable_system_design.md,
   docs/adapters/README.md) for any of 5 regex patterns whose integer doesn't
   match the SSoT.

2. **5 regex patterns** (Wave 38 D6) — README badge `Lint-(\\d+)%2F(\\d+)`, English
   `\\b(\\d+)[- ]dimension(?:al)?\\s+(?:lint|immune|consistency)`, CJK
   `\\b(\\d+)\\s*(?:维|次元)\\s*(?:lint|L0|の|的)?` (covers both 中文 and 日本語),
   L range `\\bL0[-–](?:L)?(\\d+)\\b` (with quick-mode subset exemption), and
   pass ratio `\\b(\\d+)/(\\d+)\\s+(?:green|绿|PASS|pass)`. Each pattern requires
   a domain keyword to minimize false positives on unrelated numeric strings.

3. **Quick-mode subset exemption** (Wave 38 craft §3 C7): the L-range pattern
   exempts both `L0-L{full_max}` AND `L0-L{quick_max}` so legitimate references
   to the documented quick-mode sub-range (e.g. `myco immune --quick: L0-L3`) are
   not falsely flagged. The exemption derives from the same SSoT
   (`len(QUICK_CHECKS) - 1`), not a hardcoded 3.

4. **Pinned-surface allowlist** (Wave 38 D5): L19 does NOT scan log.md,
   contract_changelog.md, docs/primordia/*, notes/*, examples/ascc/*, or
   src/myco/lint.py itself. The first five are append-only/pinned per Hard
   Contract #2 (historical claims must be preserved verbatim). lint.py is
   excluded to avoid the own-file self-reference loophole (Wave 38 craft §3 L1).

5. **Module-level FULL_CHECKS / QUICK_CHECKS tuples** (Wave 38 D2): refactored
   `src/myco/lint.py::main()` from a local `checks = [...]` block into module-
   level immutable tuples that L19 (and any other consumer) can reference as the
   single source of truth. Tuple immutability prevents accidental mutation;
   `main()` casts to list for its existing local-mutable pattern.

6. **mcp_server.py dispatch refactor** (Wave 38 D9 — scope expansion): the
   pre-existing `src/myco/mcp_server.py::myco_immune` function maintained its OWN
   local `checks = [...]` list that had drifted to L0-L14 only and was silently
   dropping L15-L18 from MCP-mode lint reports. Refactored to import
   `FULL_CHECKS, QUICK_CHECKS` from `myco.lint` and dispatch directly. This
   eliminates a real behavioral bug (MCP users were unknowingly running 15-dim
   lints while CLI users were running 19-dim) and makes mcp_server.py a true
   downstream of the SSoT.

7. **Contract version bump**: `_canon.yaml::system.contract_version` v0.28.0 →
   v0.29.0; `_canon.yaml::system.synced_contract_version` mirror; template
   `src/myco/templates/_canon.yaml::system.synced_contract_version` mirror.

8. **15+ narrative surface bumps**: every HIGH and MEDIUM surface listed in
   change #1 now references "20-dimension / L0-L19 / 20/20" in lockstep with
   the new SSoT. README badges (en/zh/ja) bump to `Lint-20%2F20`. MYCO.md
   §指标面板 bumps lint health value 0.68 → 0.70 reflecting the new ceiling.
   immune.py docstring + dimension list bullet add L19. CONTRIBUTING.md, the
   migrate/init scripts, docs/reusable_system_design.md, and docs/adapters/README.md
   all bump in the same commit so L19 is green from the moment of landing.

9. **L19 unit tests**: 4 tests in `tests/unit/test_lint_dimension_count.py`
   (Wave 38 D8) — base case (clean substrate → 0 issues), badge drift HIGH,
   multi-pattern co-match (≥3 issues per drifted line), severity split
   (HIGH for README, MEDIUM for CONTRIBUTING). Each test pulls EXPECTED from
   `len(FULL_CHECKS)` at import time so the test assertions also derive from
   the SSoT and never need hardcoded updates.

**Verification**:
- `myco immune` → 20/20 PASS
- `pytest tests/ -q` → 26/26 PASS (22 prior + 4 Wave 38)
- `myco hunger` → no `dimension_count_drift` signal (the new channel is silent
  by design when L19 is green)
- `git diff _canon.yaml | grep contract_version` → v0.28.0 → v0.29.0 visible

**Backward compatibility**: Pure addition. No existing lint dimension semantics
change, no notes schema change, no CLI verb change. Downstream instances on
v0.28.0 will see L17 contract_drift fire MEDIUM until they sync — exactly the
designed signal channel for this kind of upgrade.

**Forward path**: L19's existence does NOT replace human review of new
narrative surfaces; it only catches drift on the 15 already-enrolled surfaces.
When future waves add new doc files that reference LINT_DIMENSION_COUNT, those
files must be explicitly added to `_L19_HIGH_SURFACES` or `_L19_MEDIUM_SURFACES`.
This is acknowledged as Wave 38 craft §3 known limitation L2 and is the
correct trade-off (full filesystem walks would be O(N) and produce too many
false positives on incidental numeric strings in unrelated docs).

---

## v0.28.0 — 2026-04-12 (minor · primordia_soft_limit re-baseline 40 → 60, Wave 36 — substrate maturity threshold update)

**Author**: Claude (Myco kernel agent, autonomous run under explicit user grant, Wave 36)

**Motivation**: The `structural_bloat` hunger signal has been firing wave-over-wave
since at least Wave 30 with no operator response. Audit at Wave 36 found 47 ACTIVE
craft files in `docs/primordia/` (over the soft limit of 40 by 7), all of which
are load-bearing for current doctrine and impl modules. Wave 22 §B7 R2.4 explicitly
anticipated this condition: *"If creation velocity ever exceeds compression
(e.g., wave 30+ where everything is still active), that's a real signal — probably
time to raise the soft limit or split primordia by phase."* This wave executes
the first half of that prescription: re-baseline.

**Why not the archive path**: Wave 36 R0 audited the 47 active crafts for
SUPERSEDED candidates and found exactly 2 obvious ones — `metabolic_inlet_design_craft_2026-04-12.md`
(SUPERSEDED by `inlet_mvp_craft_2026-04-12.md`) and `compression_primitive_craft_2026-04-12.md`
(SUPERSEDED by `compress_mvp_craft_2026-04-12.md`). Each is referenced by ~15 places
across canon comments, code module docstrings, impl crafts, contract changelog
entries, and historical notes. Per substrate immutability doctrine
(`docs/contract_changelog.md` Wave 8 banner), historical notes and committed
log entries cannot be rewritten. Archiving these 2 crafts would either (a) cause
30+ link-rot incidents or (b) require rewriting immutable history. Both options
violate stronger doctrines than the soft-limit signal protects against. Wave 22
itself succeeded in archiving 11 OLD debate files because those files had minimal
dependency depth (they were referenced only by the README). Post-Wave-22 design
crafts have entirely different dependency profiles.

**Why 60 specifically**: Calculated from observed velocity. Substrate size at
Wave 22 (40 limit set): ~25 crafts → 25/40 = 0.625 utilization. Wave 36 substrate
size: 47 crafts. Net growth = 22 crafts over 14 waves = ~1.6 crafts/wave on
average. Projected size at Wave 50: 47 + (14 × 1.6) ≈ 70. Setting limit at 60
provides ~13 of headroom = ~8 more waves before re-evaluation. Setting at 70
would push the next re-baseline far enough that Wave 22's "sensor that fires
but no one catches it" pathology could re-emerge. 60 is the honest middle ground:
gives breathing room without abdicating the discipline.

**Changes**:

1. `_canon.yaml::system.structural_limits.primordia_soft_limit`: 40 → 60
   (with multi-line comment explaining Wave 22 §B7 R2.4 lineage).
2. `src/myco/templates/_canon.yaml`: mirrored.
3. `src/myco/notes.py::DEFAULT_STRUCTURAL_LIMITS["primordia_soft_limit"]`: 40 → 60.
4. `_canon.yaml::system.contract_version` + `synced_contract_version`: v0.27.0 → v0.28.0.
5. `src/myco/templates/_canon.yaml::synced_contract_version`: v0.27.0 → v0.28.0.
6. `docs/contract_changelog.md`: this entry.
7. `docs/primordia/archive/primordia_soft_limit_rebaseline_craft_2026-04-12.md` (NEW):
   Wave 36 craft (kernel_contract class, 0.90 target/current, 3 rounds, full
   L13 schema). Documents the audit, the alternatives considered (archive vs
   re-baseline vs split), the rejection rationale for archive, and the chosen
   value rationale.

**Self-tests**:

- `myco immune`: 19/19 dimensions PASS post-bump. Critical dimensions: L10 unchanged
  (no notes schema edits), L13 unchanged (no craft schema edits), L15 fires
  (kernel_contract surface touched) but evidence_present=true via the new craft
  file in primordia/, L17 unchanged (synced_contract_version matches kernel).
- `myco hunger`: `structural_bloat` signal post-bump should report
  "primordia: 48 files (soft limit 60, headroom 12)" — silent or informational,
  not a friction signal. Or simply absent if 48 < 60.
- `pytest tests/`: 22/22 PASS unchanged (no test changes; this wave is a
  pure config/threshold edit).

**Hard contracts honored**:

- Substrate immutability: no historical notes or committed log entries rewritten.
  The 2 SUPERSEDED candidates remain in their original locations with their full
  reference web intact.
- Friction-driven ordering (Wave 26 D3): Wave 36 picked the actual firing friction
  signal (`structural_bloat`) over the speculative future-friction Wave 34 §3.3
  candidates (inlet_ripe / cross-ref / continuous compression). Those wait for
  Wave 37+ when inlet has accumulated real operator dogfooding.
- Single-source convention: this is a kernel_contract class craft with
  current_confidence=target_confidence=0.90 (the craft uses Wave 22's prior
  research as its external evidence base, so the equality is honest).
- Wave 22 W13 procedural rule satisfied: this wave's closing hunger response
  is "compression by re-baselining" with explicit justification, not a `deferred:
  primordia-compression` line. The discipline is preserved.

**Doctrine coverage**:
- Anchor #4 (压缩即认知): no shift. Compression is still cognition; this wave
  doesn't add a compression mechanism, only re-baselines a sensor that detects
  when compression is needed.
- Wave 22 W13 rule: still active. Future waves will still be required to either
  compress or defer-with-reason if `structural_bloat` fires.
- Substrate immutability: reinforced (re-baseline preserves all citations
  intact, archive would have violated it).

**See also**:
- `docs/primordia/archive/primordia_compression_craft_2026-04-12.md` (Wave 22 — original
  workflow + archive directory + W13 rule)
- `docs/primordia/archive/primordia_soft_limit_rebaseline_craft_2026-04-12.md` (Wave 36
  — this wave's craft of record)
- `docs/WORKFLOW.md` W13 (procedural rule, still binding)

---

## v0.27.0 — 2026-04-12 (minor · `myco absorb` MVP, Wave 35 — Metabolic Inlet primitive scaffold)

**Author**: Claude (Myco kernel agent, autonomous run under explicit user grant, Wave 35)

**Motivation**: Anchor #3 (七步代谢管道) declared a Metabolic Inlet primitive in
Wave 10's Vision Recovery (`docs/primordia/vision_recovery_craft_2026-04-10.md`)
but no implementation existed across Waves 10–34. The gap was the longest-standing
unimplemented identity-surface declaration in the substrate. Wave 26 §2.3
(`docs/primordia/vision_reaudit_craft_2026-04-12.md`) catalogued the gap as a
long-tail deferral. Wave 34 (`docs/primordia/archive/metabolic_inlet_design_craft_2026-04-12.md`)
designed the scaffold under exploration class (0.85, 8 design questions, 6 attacks).
Wave 35 lands the MVP per Wave 34 §3.1's prescriptive 10-item brief.

**Scope discipline**: per Wave 34 §2.4, three of four open_problems §1-4 sub-problems
(cold start, trigger signals, alignment) and the fourth (continuous compression hook)
are **operator-deferred** in this wave. The verb is a scaffold: it provides the
provenance contract, the file/explicit-content forms, and the canon-driven default
tag. It does NOT solve "what to inlet first" or "when to inlet again" or "how to
filter for relevance" — those remain Wave 36+ friction-driven candidates. This is
the inverse of Wave 30's "verb is everything" approach: Wave 35 is "verb is the
minimum primitive that unblocks operator workflows".

**The bundle (one subsystem, Metabolic Inlet primitive)**:

1. **`src/myco/inlet_cmd.py`** (NEW, ~290 lines) — full `myco absorb` verb
   implementation. Functions: `_project_root` (mirrors `compress_cmd` strict
   mode), `_resolve_default_tag` (reads `notes_schema.inlet.default_tag` from
   canon at call time, falls back to `"inlet"`), `_resolve_inlet_input` (handles
   file path / `--content`+`--provenance` pair / URL-error case with explicit
   pipe-back instruction), `_build_inlet_meta` (constructs frontmatter with the
   4 inlet_* provenance fields + sha256 hash), `_build_inlet_body` (renders
   header + content), `run_inlet` (CLI dispatch). Exit codes: 0 ok / 2 usage /
   3 input validation / 5 io.

2. **`src/myco/cli.py`** — `inlet` subparser added with positional optional
   `source` (file path or URL), `--content`, `--provenance`, `--tags` (comma-
   separated), `--json`, `--project-dir`. Dispatch case routes to
   `inlet_cmd.run_inlet`.

3. **`src/myco/notes.py`** — `VALID_SOURCES` extended with `"inlet"` (Wave 35
   v0.27.0). `OPTIONAL_FIELDS` extended with the 4 provenance fields:
   `inlet_origin`, `inlet_method`, `inlet_fetched_at`, `inlet_content_hash`.

4. **`src/myco/lint.py`** — L10 `lint_notes_schema` extended with a soft
   inlet-provenance check: when `source=="inlet"`, the 4 inlet_* fields SHOULD
   be present. Severity LOW (warn, not error) so retroactively-tagged notes
   don't break the substrate. Kernel-produced inlet notes always pass.

5. **`tests/unit/test_inlet.py`** (NEW, 5 tests) — exercises the load-bearing
   paths of the Wave 34 specification:
   - `test_inlet_file_creates_raw_note_with_provenance` — file form D1 + D3
     + D4 + provenance contract D6
   - `test_inlet_explicit_content_creates_raw_note` — D2 zero-deps URL pipe
     pattern + auto-detect agent-fetched URL provenance
   - `test_inlet_url_form_rejected_with_clear_message` — D2 reject branch +
     error-message UX contract (must point at agent-fetch pipe pattern)
   - `test_inlet_default_tag_applied_when_tags_missing` — D6 canon-driven
     default tag fallback path
   - `test_inlet_lints_clean_under_l10` — soft check produces zero issues
     on freshly-inletted notes (validator/writer contract)

6. **`_canon.yaml`** + **`src/myco/templates/_canon.yaml`** (mirrored):
   - `contract_version` `v0.26.0` → `v0.27.0`
   - `synced_contract_version` `v0.26.0` → `v0.27.0`
   - `notes_schema.optional_fields` extended with 4 inlet_* fields
   - `notes_schema.valid_sources` extended with `inlet`
   - new `notes_schema.inlet:` sub-section: `default_tag: "inlet"`

7. **`docs/primordia/archive/inlet_mvp_craft_2026-04-12.md`** (NEW) — Wave 35 craft
   record under `kernel_contract` class (target 0.90, 3 rounds). Validates
   Wave 34 design under implementation pressure: any field that the design
   underspecified (e.g. how to handle non-UTF-8 input, exit-code mapping for
   the 3 input-resolution branches) is decided in this craft.

**Operator-deferred sub-problems** (Wave 34 §2.4 — NOT solved here, remain
in `docs/open_problems.md` §1-4 as candidates for Wave 36+ friction):
   - §1 cold start (which seed content to inlet first) — defers to operator choice
   - §2 trigger signals (when to inlet next) — defers to operator-as-daemon
   - §3 alignment (relevance filter) — defers to operator's `myco evaluate` step
   - §4 continuous compression hook — defers to existing `myco condense --tag inlet`

**Hard contracts honored**:
   - Zero non-stdlib deps: `hashlib`, `json`, `sys`, `datetime`, `pathlib`,
     `typing` only. URL fetch is NOT in the kernel — agent wrappers fetch via
     `WebFetch`/`curl` and pipe content back via `--content STR --provenance URL`.
     The kernel auto-detects the agent-fetched-URL pattern and tags the note
     `inlet_method: url-fetched-by-agent`.
   - Reflex arc trigger: `_canon.yaml`/`templates/_canon.yaml`/`notes.py`/
     `cli.py`/`lint.py` are all kernel_contract trigger surfaces, so the Wave
     35 craft is a hard requirement (not optional).
   - Substrate writer/lint validator agreement: `test_inlet_lints_clean_under_l10`
     is the regression sensor.

**Cumulative coverage shift**: anchor #3 (七步代谢管道) coverage in the Wave 26
audit was 0.65 (because the inlet declaration had no implementation). Wave 35
raises this to ~0.80 (the primitive exists, the 4 sub-problems are operator-
deferred and known). The doctrine map row for anchor #3 now reads "scaffold
landed; long-tail open in §1-4".

**See also**:
   - Authoritative design: `docs/primordia/archive/metabolic_inlet_design_craft_2026-04-12.md`
   - Implementation craft: `docs/primordia/archive/inlet_mvp_craft_2026-04-12.md`
   - log.md: Wave 35 milestone

---

## v0.26.0 — 2026-04-12 (minor · `myco condense` MVP, Wave 30 — closes Wave 27 D8 implementation brief)

**Author**: Claude (Myco kernel agent, autonomous run under explicit user grant, Wave 30)

**Motivation**: Wave 27 produced a complete forward-compression design (D1–D9)
but no code. Anchor #4 (`压缩即认知：存储无限，注意力有限`) remained the lowest-
coverage identity anchor at `implementation_coverage = 0.35` per Wave 26 Round 1's
audit. Wave 30 lands the implementation per Wave 27's specification, validating
the design under real implementation pressure and raising anchor #4 coverage
estimate to ~0.75.

**The bundle (one subsystem per Wave 27 D8)**:

1. **`src/myco/io_utils.py`** (NEW, ~160 lines) — first general-purpose
   atomic-write helper. `atomic_write_text(path, text)` uses
   `tempfile.mkstemp` + `os.replace` in the same directory for filesystem-
   level atomicity. `atomic_write_yaml(path, data)` is the YAML wrapper.
   First absorption from hermes catalog C2 (atomic writes). Module name is
   provisional pending Wave 29b biomimetic sweep — flagged in module docstring.

2. **`src/myco/compress_cmd.py`** (NEW, ~430 lines) — full `myco condense`
   verb implementation. Functions: `_project_root` (mirrors `notes_cmd`
   strict mode), `_resolve_cohort_by_tag` (default eligible status
   `{raw, digesting}` + skip notes with `compressed_from` set), 
   `_resolve_cohort_by_ids` (manual escape hatch, preserves input order),
   `_validate_cohort` (cascade rejection + excreted rejection),
   `_build_output_body` / `_build_output_meta` / `_build_input_update`
   (frontmatter constructors), `_execute_compression` (two-phase commit:
   build all in memory, then write output first via `atomic_write_text`,
   then iterate inputs with best-effort warning on per-input failure),
   `run_compress` (CLI dispatch). Exit codes: 0 ok / 2 usage / 3 validation
   / 4 empty cohort / 5 io.

3. **`src/myco/cli.py`** — `compress` subparser added with positional
   `note_ids` (`nargs="*"`), `--tag`, `--rationale` (required prose),
   `--status`, `--confidence` (float default 0.85), `--dry-run`, `--json`,
   `--project-dir`. Dispatch case routes to `compress_cmd.run_compress`.

4. **`_canon.yaml`** + **`src/myco/templates/_canon.yaml`** (mirrored):
   - `contract_version` `v0.25.0` → `v0.26.0`
   - `synced_contract_version` `v0.25.0` → `v0.26.0`
   - `notes_schema.optional_fields` extended with `compressed_from`,
     `compressed_into`, `compression_method`, `compression_rationale`,
     `compression_confidence`, `pre_compression_status`
   - `notes_schema.valid_sources` adds `compress`
   - New `notes_schema.compression` sub-section: `ripe_threshold: 5`,
     `ripe_age_days: 7`

5. **`src/myco/notes.py`**:
   - `VALID_SOURCES` extended with `forage` (was missing from prior wave!)
     and `compress`
   - `OPTIONAL_FIELDS` extended with the 6 compression audit field constants
   - New `detect_compression_ripe(root, *, now=None) -> Optional[str]`
     (~100 lines): scans raw notes by tag, computes cohort size + oldest
     age, returns advisory `compression_ripe: tag '<T>' has N raw notes
     (oldest M days old)` signal when both thresholds met
   - `compute_hunger_report` wires `detect_compression_ripe` into the
     signals list per Wave 27 D2 (non-blocking advisory, no `[REFLEX HIGH]`
     prefix — anchor #6 selection loop preserved)

6. **`src/myco/metabolism.py`** — re-export updated to include
   `detect_compression_ripe` in import list and `__all__`.

7. **`src/myco/lint.py`**:
   - New `lint_compression_integrity(canon, root)` (~130 lines, 3 checks):
     output integrity (`status=extracted`, `source=compress`,
     `compression_method` + `compression_rationale` set, all
     `compressed_from` members exist), input back-link (each
     `compressed_into` points back, `status=excreted`), cascade prevention
     (no `compressed_from` input may have its own `compressed_from`).
     Plus orphan detection: `compressed_into` pointing at a nonexistent
     note fires HIGH "broken audit chain".
   - Registered as **L18** in `main()` check list after L17
   - Module docstring updated `18-Dimension` → `19-Dimension`

8. **`src/myco/immune.py`** — re-export updated to include
   `lint_compression_integrity` in import list and `__all__`.

9. **`tests/unit/test_compress.py`** (NEW, ~280 lines, 5 tests + 2 helpers):
   - `test_compress_consumptive_with_audit` — Wave 27 D3+D4 audit shape:
     3-note cohort → 1 extracted + 3 excreted with bidirectional links
   - `test_compress_dry_run_no_writes` — Wave 27 Attack G defense:
     `--dry-run` must not mutate disk (mtime + content + file count
     unchanged)
   - `test_compress_cascade_rejected` — Wave 27 §2.1 defense #4:
     compression-on-compression rejected with exit 3, no mutation
   - `test_compress_idempotent_empty_cohort` — Wave 27 §1.7: re-running
     `myco condense --tag X` after success exits 4 with no new files
   - `test_lint_compression_integrity_catches_orphan` — L18 backstop:
     deleting an output leaves dangling `compressed_into`, L18 fires HIGH

**R2.3 mid-round bug catch (recorded as confidence-amplifying signal)**:
The first pytest run caught a real silent-failure bug in the implementation
craft. `_resolve_cohort_by_tag` originally only excluded `excreted` notes,
but the output `extracted` note inherits the aggregated input tags via
`_build_output_meta`. On the second compress run with the same tag, the
output was re-resolved into the cohort, hit cascade rejection at validation
time, and exited 3 (validation error) instead of 4 (empty cohort). Wave 27
§1.7 idempotence guarantee was silently violated by an incomplete resolver
filter. Fixed: default eligible-status filter is `{raw, digesting}` AND
the resolver explicitly skips notes with `compressed_from` set as
belt-and-suspenders. **This is the strongest possible empirical validation
of the Wave 25 tests infrastructure investment** — the test suite caught
a real silent-failure bug in the implementation craft on its first run,
which is the exact validation the W25 craft promised.

**Verification at land time**:

```
$ PYTHONPATH=src python -m myco.cli lint
✅ ALL CHECKS PASSED — 0 issues found  (19 dimensions L0-L18)

$ PYTHONPATH=src python -m pytest tests/ -q
.........                                                   [100%]
9 passed in 0.33s
```

**Anchor coverage shift (Wave 26 Round 1 baseline → Wave 30 estimated)**:

| Anchor | Wave 26 baseline | Wave 30 estimate | Delta | Source |
|--------|------------------|------------------|-------|--------|
| #4 压缩即认知 | 0.35 | ~0.75 | +0.40 | `myco condense` MVP + L18 + ripe signal |
| #3 七步管线 | 0.43 | ~0.75 | +0.32 | compress folds steps 2+3+5+7 per Wave 27 D6 |

**Known limitations** (registered, not bugs):

- L1: two-phase commit best-effort (R2.1 + L18 backstop)
- L2: `compression_method` free-form, future enum trivial
- L3: `io_utils.py` name provisional pending Wave 29b
- L4: `myco expand` verb still vapor (data preserved, manual recovery mechanical)
- L5: hallucination risk bounded not eliminated (Wave 27 L1 inherited)
- L6: `compression_ripe` single-tag per hunger run
- L7: multi-tag input notes have order-dependent aggregation

**Craft of record**: `docs/primordia/archive/compress_mvp_craft_2026-04-12.md`
(kernel_contract, 3 rounds, 0.91 confidence — target 0.90 met +0.01 from
R2.3 empirical validation).

**Doctrine**: forward compression is the substrate's primary cognitive
act. Wave 27 designed it; Wave 30 implements it. The verb is the first
direct service of anchor #4 since the substrate's inception. Without it,
"storage infinite, attention finite" was aspirational doctrine; with it,
the substrate has a concrete handle for converting bulk metabolism into
synthesized canon under audit.

---

## v0.25.0 — 2026-04-12 (minor · vision re-audit + doctrine reconciliation, Wave 26 — supersedes Wave 25 D3)

**Author**: Claude (Myco kernel agent, autonomous run under explicit user grant, Wave 26)

**Motivation**: Post-Wave-25 dialogue exposed a fundamental methodological
incompatibility. Wave 25 craft §4.1 D3 locked in **friction-driven** ordering
for Waves 26+ ("the first bug the new test suite catches determines Wave 26's
subject"). The user's subsequent methodology statement was explicitly **top-down**
("从抽象阶梯的上方开始实现，直至落实到具体实现细节"). These are not reconcilable
— friction-driven lets the implementation surface decide; top-down lets the
doctrine decide. One must supersede the other. Before deriving any top-down
ordering, the strongest possible top-down move is to re-audit the 8 identity
anchors themselves — the axioms of the system — to ensure they are still clear,
still correct, and still consistent with the implementation state that has
accumulated across 15 waves (W11–W25) since the last audit (Wave 10
`vision_recovery_craft_2026-04-10.md`). If the axioms have silently drifted,
any downstream ordering would commit to 15-wave-old state.

**Change summary**:

1. **New craft of record**: `docs/primordia/vision_reaudit_craft_2026-04-12.md`
   (kernel_contract class, 3 rounds, 0.90 confidence). Round 1 audits each of the
   8 anchors against current implementation (code path + lint dimension + notes
   lifecycle). Round 2 builds a dependency DAG and produces a citable priority
   ordering with 4 attack angles on the ordering itself. Round 3 supersedes
   Wave 25 D3 with a new doctrine-dependency-graph-derived ordering and locks
   Wave 27 scope to "forward compression as a substrate primitive" design craft.

2. **Three MYCO.md §身份锚点 refinements** (not replacements):
   - **Anchor #3** appended with scope clarification: "今天的 Myco 在步骤 1
     (eat/forage)、步骤 6 (lint)、步骤 7 (digest --excrete) 有专属动词；步骤
     2-5（评估/萃取/整合/压缩）只是状态标签或缺席。消化道中段是 vestigial ——
     这是 Wave 27+ 自上而下的首要服务对象"
   - **Anchor #5** corrected: D-layer "未实现" → "dead_knowledge 最小种子已落地
     于 v0.4.0" with full citation chain. This corrects a factual error introduced
     by Wave 18 progress not being reflected in the anchor wording. Today Myco
     implements "A + B + partial C + **D-seed**", not "A + B + partial C".
   - **Anchor #8** extended: adds sibling anchor pointer to this Wave 26 craft
     as the "post-Wave-25 implementation reconciliation" companion to Wave 10's
     "failed-element recovery" anchor. Both remain permanent.

3. **MYCO.md §指标面板** row `lint_coverage_confidence` rationale updated: "15
   维 L0-L14" → "18 维 L0-L17 全绿 + Wave 25 tests/ 基础设施落地". Value stays
   at 0.68 pending Wave 27+ friction data (refinement, not score inflation).

4. **MYCO.md §任务队列** row 2 replaced: stale "v1.2.0-v1.5.0" pre-Wave-8
   re-baseline identifiers → accurate v0.8.0-v0.25.0 post-rebaseline wave sequence
   (15 waves listed), rhythm "摩擦驱动" → "doctrine-dependency-driven", next-wave
   pointer to Wave 27 compression craft.

5. **MYCO.md §任务 4 详述 Metabolic Inlet**: "现有 14 维 lint" → "现有 18 维
   lint (L0-L17)". Trivial staleness fix.

6. **Canon bumps**: `_canon.yaml` + `src/myco/templates/_canon.yaml`
   `contract_version` / `synced_contract_version`: v0.24.0 → v0.25.0.

7. **Wave 25 craft §4.1 D3 is superseded** with the following new text (now in
   force): *"Wave 26+ ordering derives from the doctrine dependency graph in
   `vision_reaudit_craft_2026-04-12.md §2`, not from friction signals or the
   hermes-absorption catalog's historical sequence. Each wave services one
   identity anchor. Hermes catalog items C2–C20 are pulled in as supporting
   infrastructure when the doctrine wave explicitly requires them. Waves alternate
   craft → impl rhythm. Friction between waves produces hot-fix waves that do
   not displace the planned ordering."*

8. **Wave 27 scope locked**: exploration-class design craft for **forward
   compression as a substrate primitive** (anchor #4 service). Target confidence
   0.85, 3 rounds, no code. Output answers 7 specific design questions (unit /
   trigger / output / audit / reversibility / step-3-4-5 interaction / non-functional
   requirements). Wave 28 implementation is declared but not pre-scoped — it will
   be scoped in Wave 27's conclusion.

**Authoritative craft**: `docs/primordia/vision_reaudit_craft_2026-04-12.md`
(kernel_contract class, 3 rounds, final confidence 0.90).

**Supersedes**: `docs/primordia/archive/hermes_absorption_craft_2026-04-12.md §4.1 D3`
only. Wave 25 craft's D1/D2/D4/D5/D6 remain in force (catalog is catalog, tests
is landed, 3 revisions stand, substrate/runtime boundary immutable, Wave 9
surface digest not superseded).

**Self-tests** (Wave 26 evidence):

- Anchor audit found 3 anchors needing refinement (#3, #5, #8) out of 8 — all
  refinements were scope clarifications or factual corrections, none were
  semantic replacements.
- Dependency DAG converged on anchor #4 as top priority independently of
  hermes-recency-bias (verified via 4 independent evidence sources in §2.2
  Attack D defense).
- Surprising finding: Self-Model D-layer is **more complete than Wave 18 craft
  wording suggests** — `record_view()` + hunger signal + 5-condition detection
  + 30-day threshold all wired. Full D-layer (view audit log + cross-ref graph
  + adaptive threshold + auto-excretion) is long-tail, not blocker.
- All 15 landing list items executed cleanly; no scope creep; single subsystem
  ("MYCO.md doctrine reconciliation") per inherited Wave 25 Round 2 capacity rule.

**Limitations** (explicit, per craft §4.3):

- **Single-agent audit ceiling**: this craft's attacks are all generated by one
  agent. External research (5 doctrinal files, 15 waves of log, source code
  verification, one Explore subagent for D-layer state check) raises the evidence
  base to support the 0.90 confidence, but does not match the rigor of multi-agent
  or human-in-the-loop debate. If future audit finds the evidence thin, drop to ≤ 0.88.
- **Coverage scores are ordinal, not cardinal**: the 0.0–1.0 numbers in Round 1
  are subjective judgment. #4 (0.35) is genuinely worse than #1 (0.72), but
  absolute values are not load-bearing.
- **Recency bias acknowledged**: audit ran 48h after deep hermes-absorption;
  compression being on top could be partially biased by context. Cross-validated
  against independent evidence (dashboard, Wave 10 recovery, open_problems) —
  convergence holds, but Wave 27 Round 3 should re-check the bias if compression
  turns out harder to design than expected.
- **Wave 27 scope locked, Wave 28+ not locked**: one-wave-ahead visibility.
  Wave 28 will be scoped in Wave 27's conclusion, not this craft.
- **Metabolic Inlet still blocked**: 4 open problems in `docs/open_problems.md
  §1-4` remain. Ordering places Inlet downstream of compression; compression
  must land before Inlet is designable.

**Closes**: the doctrine/implementation drift window that opened between Wave 10
(last audit) and Wave 25 (last implementation wave). Reopens the question of
Wave 27's subject and answers it: forward compression primitive design craft.

---

## v0.24.0 — 2026-04-12 (minor · tests infrastructure seed, Wave 25 — hermes absorption C1)

**Author**: Claude (Myco kernel agent, autonomous run under explicit user grant "是", Wave 25)

**Motivation**: A direct source-probe audit during the hermes-agent
deep absorption run (evidence note `n_20260412T013044_5546`, raw
forage-digest) confirmed a bluntly measurable engineering gap: 9132
lines of Myco production Python, zero test files. The only `tests/`
directory in tree lived inside the foraged `hermes-agent/` repo and
actively polluted `pytest` scope — Wave 23 scar NH-9 was born from
exactly that pollution. Meanwhile, three of Myco's five most recent
scars (W20 silent-fail `_project_root`, W23 pre-commit hook blocking
path never exercised live, W24 two sensors reporting opposite values
on the same system) would each have been caught at edit time by a
single unit test. The gap was not theoretical — it was already costing
Myco a wave of friction per discovered hole.

**Change summary**:

1. **New `tests/` top-level directory** with `conftest.py` autouse
   isolation fixture (`_isolate_myco_project`) and
   `tests/unit/test_notes.py` covering 4 load-bearing paths in
   `src/myco/notes.py`:
   - `write_note` creates file with valid frontmatter
   - `serialize_note` ↔ `parse_frontmatter` round-trip (unicode +
     symbols)
   - `write_note` id-collision retry path (deterministic via
     monkeypatched `generate_id`)
   - `_project_root` raises `MycoProjectNotFound` on orphan dirs
     (Wave 20 silent-fail fix regression guard)

2. **`pyproject.toml` discipline additions**:
   - `[project.optional-dependencies].dev` = `{pytest>=7,<9,
     pytest-xdist>=3,<4}` (minimal — add libs only when a test
     needs them)
   - `[tool.pytest.ini_options]` with `testpaths = ["tests"]`,
     `markers = ["integration: ..."]`, `addopts = "-m 'not
     integration'"`. Scope lock prevents the Wave 23 forage-crawl
     scar class from ever recurring on a bare `pytest` invocation.

3. **New `_canon.yaml::system.tests` schema section** (SSoT):
   - `test_dir: tests/`
   - `min_unit_tests: 4`
   - `integration_marker: integration`
   - `unit_subdir: tests/unit/`

   Same section mirrored into `src/myco/templates/_canon.yaml` with
   `min_unit_tests: 0` so downstream instances start at zero without
   the kernel's inherited expectation.

4. **`scripts/install_git_hooks.sh`** now reads `test_dir` from
   `_canon.yaml::system.tests.test_dir` via inline Python (PyYAML is
   already a runtime dep). Falls back to hardcoded `tests` on any
   read error. Both pytest and the hook now share one truth source,
   closing the "single source of truth" aspect of Wave 25's discipline
   goal and erasing the last hardcoded `tests/` literal in the hook
   body. No change to the Wave 23 `MYCO_PRECOMMIT_PYTEST=1` opt-in
   contract.

5. **Canon bumps** — `_canon.yaml` + `src/myco/templates/_canon.yaml`
   `contract_version` / `synced_contract_version`: v0.23.0 → v0.24.0.

**Authoritative craft**: `docs/primordia/archive/hermes_absorption_craft_2026-04-12.md`
(kernel_contract class, 3 rounds, final confidence 0.90). The craft
covers the full 20-item engineering-pattern catalog (C1–C20) absorbed
from hermes-agent; Wave 25 lands only C1 (tests infrastructure) per
the craft's D2 decision (tests is the single T1 absorption grounded
in 3 of 5 recent scars). Waves 26+ ordering is friction-driven: the
first bug the new test suite catches determines what comes next.

**Self-tests** (Wave 25 evidence, to be recorded in log.md):

- `myco immune` L0–L17 all green after landing.
- `pytest tests/ -q` runs all 4 seed tests to pass.
- Autouse fixture verified by test 4 which deliberately uses a
  bare `tmp_path` outside the fixture's scaffolded project to
  prove `_project_root` still raises.

**Limitations** (explicit, not hidden):

- **4 unit tests is a seed, not coverage**. Per craft §4.3 L2, real
  coverage grows wave by wave as friction demands. Wave 25 makes no
  claim of test coverage beyond what its 4 tests touch.
- **Integration tests not yet used**. The marker is reserved; no test
  currently carries it.
- **The test suite runs on the editable install path** via
  `sys.path.insert(0, str(_SRC))` in `conftest.py`. A future wave that
  ships Myco as a wheel in CI will need to re-verify.
- **No CI yet**. Wave 25 lands local test infra only; GitHub Actions
  workflow wiring is deferred to when CI discipline becomes a friction
  source.

**Closes**: structural precondition for absorbing C2–C20 from the
hermes absorption catalog. Does NOT directly close any panorama-#3
NH; instead, converts "0 tests" from an invisible meta-hole into a
visible first-class surface that can now carry regression guards for
every future wave.

---

## v0.23.0 — 2026-04-12 (minor · L17 Contract Drift lint, Wave 24 — closes panorama-#3 NH-10)

**Author**: Claude (Myco kernel agent, autonomous run under user grant, Wave 24)

**Motivation**: Panorama #3 ran the kernel + ASCC through both sensory
surfaces immediately after Wave 23 landed. Result: same instance
(ASCC), two sensors, opposite readings. `myco hunger` correctly
reported `[REFLEX HIGH] contract_drift: synced_contract_version=
'v0.19.0' != kernel contract_version='v0.22.0'`. `myco immune`
reported `✅ ALL CHECKS PASSED — 0 issues found`. Lint had no
drift-detection code path. The Wave 18 pre-commit hook invokes
`myco immune`, not `myco hunger`, so a downstream instance with
screaming drift could commit cleanly through the hook — exactly
the scenario where downstream commits are most dangerous. Same
silent-fail pathology class as NH-1 (Wave 20 grandfather ceiling),
but on a different surface.

**Change summary**:

1. **New L17 Contract Drift lint** (`src/myco/lint.py::lint_contract_drift`):
   delegates to `myco.notes.detect_contract_drift` for the truth
   definition so there is exactly one drift-definition across both
   sensors. Severity mapping:
   - `[REFLEX HIGH]` → HIGH (blocks pre-commit hook)
   - `[REFLEX MEDIUM]` → MEDIUM (surfaces but does not block)
   - Unknown prefix → HIGH (**fail-loud**, per Wave 24 craft §R2.2;
     a future contract renaming the prefix must not degrade silently)
   - Import failure → HIGH (**fail-loud**, per §R3.2; install
     integrity compromise is worse than silent)

2. **Registered in `main()`** checks list after L16. Lint count
   16 → 17 dimensions. `quick=True` mode still skips L4-L17 per
   the existing fast-sanity convention.

3. **Canon bumps** — `_canon.yaml` + `src/myco/templates/_canon.yaml`
   `contract_version` / `synced_contract_version`: v0.22.0 → v0.23.0.

4. **First live consumer** — ASCC `_canon.yaml::system.synced_
   contract_version` bumped v0.19.0 → v0.23.0, skipping the
   intermediate v0.20.0/v0.21.0/v0.22.0 bumps since no ASCC-side
   reflex-refresh work was required by those waves (they were
   kernel-internal tooling only). Post-sync both ASCC sensors agree:
   hunger = healthy, lint = ALL CHECKS PASSED.

**Authoritative craft**: `docs/primordia/archive/contract_drift_lint_craft_2026-04-12.md`
(kernel_contract class, 3 rounds, final confidence 0.92).

**Self-tests** (panorama-#3 evidence, frozen in the craft §Evidence):

- Kernel hunger (before + after): healthy.
- Kernel lint (before + after): 1 pre-existing L13 MEDIUM, no L17 fire.
- ASCC hunger (before + after sync): REFLEX HIGH → healthy.
- ASCC lint (before Wave 24): ALL CHECKS PASSED (the bug).
- ASCC lint (after Wave 24, before ASCC sync): L17 HIGH drift fires.
- ASCC lint (after ASCC sync to v0.23.0): ALL CHECKS PASSED.
- Both sensors now agree across both directions: drift present →
  both fire; drift absent → both silent.

**Limitations** (explicit, not hidden):

- **Single truth source dependency.** L17 is a thin wrapper around
  `detect_contract_drift`. If a future wave adds a second drift
  definition elsewhere, L17 would go blind to it. Mitigation: treat
  `detect_contract_drift` as the authoritative sensor and route new
  drift logic through it, not around it.
- **Installed-package vs editable-install mismatch** remains
  unhandled. Inherited from Wave 20's detect_contract_drift; not
  regressed.
- **`quick=True` skips L17.** Matches the existing L4-L16 convention.
  Only `myco immune --quick` invocations lose drift coverage; the
  pre-commit hook runs full lint.
- **Rare workflow**: an instance that wants to commit a stale
  contract version then bump in the next commit now hits the hook
  gate. Wave 24 craft §R2.1 documents the `--no-verify` escape
  hatch and the W1 violation-of-record convention.

**Closes**: NH-10 (panorama #3) — `myco immune` blind to contract drift
while `myco hunger` correctly reports `[REFLEX HIGH]`.

---

## v0.22.0 — 2026-04-12 (minor · pre-commit hook dogfood + opt-in pytest gate, Wave 23 — closes NH-8/NH-9)

**Author**: Claude (Myco kernel agent, autonomous run under user grant, Wave 23)

**Motivation**: Two holes from panorama #2 on the same artifact —
`scripts/install_git_hooks.sh`. NH-8 (MEDIUM): the Wave 18 pre-commit
hook's blocking path had never been exercised live. The installer
verifies that the hook file was written, not that `git commit`
against a CRITICAL/HIGH finding actually returns non-zero. That's a
Chesterton's Fence we had trusted without testing. NH-9 (LOW): no
mechanism existed for agents who want a stricter gate on commits
touching `src/myco/` — the only test-flight option was a manual
`pytest -x` run which has the same failure mode as any manual ritual
(forgotten).

**Change summary**:

1. **Live dogfood test (NH-8)** — exercised the blocking path in the
   kernel repo against an L11 CRITICAL trigger:
   - `echo "# dogfood test scratch" > scratch.md && git add scratch.md`
   - `git commit -m "should be blocked"`
   - Result: stderr printed full lint output including
     `[CRITICAL] L11 | scratch.md | Forbidden top-level entry`,
     then `[myco] pre-commit blocked by CRITICAL/HIGH lint issues.`
     Commit was NOT created. `git log --oneline -1` unchanged.
   - Evidence frozen in `docs/primordia/archive/hook_dogfood_pytest_gate_craft_2026-04-12.md` §Evidence.
   - Not added as a repeatable regression test: would require a
     subshell-git-repo harness for a fence we now know works. Re-
     dogfood runbook lives in the craft for future contract changes
     that touch `write_surface.forbidden_top_level`.

2. **Opt-in pytest gate (NH-9)** in `scripts/install_git_hooks.sh`:
   - New hook block marked with `MYCO-PRECOMMIT-PYTEST-MARK`. Runs
     after the lint gate, only if `MYCO_PRECOMMIT_PYTEST=1` is
     exported in the committing shell.
   - Scoped to `<repo>/tests/` (not bare `pytest`) so the gate is
     not derailed by unrelated code under `forage/` or `docs/`.
     Discovered during dogfood: a bare `pytest -x` from the kernel
     root crawled `forage/repos/hermes-agent/tests/` and failed on
     `ModuleNotFoundError: No module named 'acp'`, blocking commits
     for unrelated reasons. Scoping to `tests/` eliminates this.
   - Fail-open on three conditions:
     (a) `MYCO_PRECOMMIT_PYTEST` unset or !=1 → skip silently.
     (b) `pytest` not on PATH → print message, skip, exit 0.
     (c) `tests/` directory absent → print message, skip, exit 0.
   - Blocks commit on: pytest returns non-zero with `tests/` present.
   - Verified all four paths live (absent-tests / failing test /
     passing test / absent-pytest) before landing.

3. **Installer idempotency upgrade** — the refresh logic now
   detects pre-Wave-23 hooks via absence of
   `MYCO-PRECOMMIT-PYTEST-MARK` and upgrades them in place without
   requiring `--force`. Wave-23+ hooks remain no-op on re-install.
   The outer "not our hook" rejection for foreign pre-commit files
   is preserved unchanged.

4. **Contract bump** — `_canon.yaml` + `src/myco/templates/_canon.yaml`
   `contract_version` / `synced_contract_version` v0.21.0 → v0.22.0.

**Authoritative craft**: `docs/primordia/archive/hook_dogfood_pytest_gate_craft_2026-04-12.md`
(kernel_contract class, 3 rounds, final confidence 0.88).

**Self-tests**:

- Test 1 (lint CRITICAL blocks real git commit): PASS.
- Test 2 (pytest gate with failing test blocks hook): PASS.
- Test 3 (pytest gate with passing test lets hook through): PASS.
- Test 4 (pytest gate fails open when `tests/` absent): PASS.
- `bash scripts/install_git_hooks.sh` on already-installed-but-
  pre-Wave-23 hook: prints "refreshing in place", rewrites hook,
  exit 0.
- `bash scripts/install_git_hooks.sh` second time (now Wave-23+):
  prints "already installed (Wave 23+); pass --force", exit 0.
- `myco immune --project-dir .` → 16/17 green.

**Limitations** (explicit, not hidden):

- **Dogfood evidence is a snapshot, not a regression test.** A
  future contract that removes `scratch.md` from
  `forbidden_top_level` silently invalidates the test case. The
  craft's §Evidence includes a re-dogfood runbook for such changes.
  Rejected alternative: a standing subshell-git-repo harness in
  `tests/` that installs the hook into a scratch repo and
  commit-tests it. Tradeoff: infrastructure cost > value of
  regression coverage for a 25-line bash fence.
- **Pytest gate excludes doctests.** `pytest tests/` will not pick
  up `pytest --doctest-modules src/myco/`. When doctests start
  landing, a future wave should extend the gate command. No
  doctests exist today.
- **Pytest gate has no timeout.** A hung test hangs the commit. The
  user can Ctrl-C and `unset MYCO_PRECOMMIT_PYTEST`.
- **Windows shells without bash** remain uncovered. Pre-existing
  Wave 18 limitation; Wave 23 does not regress it.

**Closes**: NH-8 (MEDIUM) hook blocking path never dogfooded +
NH-9 (LOW) no optional test gate for heavier commits.

---

## v0.21.0 — 2026-04-12 (minor · primordia compression workflow + archive/ + W13, Wave 22 — closes NH-4)

**Author**: Claude (Myco kernel agent, autonomous run under user grant, Wave 22)

**Motivation**: NH-4 from panorama #2 — the `structural_bloat` hunger
signal for `docs/primordia/` was advisory only. `detect_structural_bloat`
would fire when the non-recursive `glob("*.md")` count exceeded the soft
limit (40), but there was no authoritative response contract: waves
could see the signal, do nothing, and propagate the advisory forward
indefinitely. After enough waves the directory would saturate, the
signal would become background noise, and primordia would silently rot.
Meanwhile the crafts themselves had natural lifecycle states
([ACTIVE]/[COMPILED]/[SUPERSEDED]) but no mechanism to physically
retire [COMPILED] files while preserving Gear-4 retrospective access.

**Change summary**:

1. **New `docs/primordia/archive/` directory** — append-only history
   for [COMPILED]/[SUPERSEDED] crafts. Preserved for Gear-4 sweeps,
   decision archaeology, and alternative-path lookups. Not excluded
   from read paths, only from `detect_structural_bloat`'s top-level
   `glob("*.md")` count (the non-recursive glob ignores subdirs).

2. **11 crafts moved into `archive/`** (Wave 22 initial compression):
   `generalization_debate_2026-04-07.md`,
   `llm_wiki_debate_2026-04-07.md`,
   `tacit_knowledge_debate_2026-04-07.md`,
   `nuwa_caveman_integration_2026-04-07.md`,
   `retrospective_p4_midterm_2026-04-07.md`,
   `system_state_assessment_2026-04-07.md`,
   `vision_debate_2026-04-08.md`,
   `myco_vision_2026-04-08.md`,
   `gear4_trigger_debate_2026-04-09.md`,
   `decoupling_positioning_debate_2026-04-09.md`,
   `gear3_v090_milestone_2026-04-09.md`. Primordia count 45 → 35
   (now below the soft limit of 40).

3. **`docs/primordia/README.md`** — 11 rehomed rows rewritten with
   `[ARCHIVED/COMPILED]` markers pointing to `archive/`. Preamble
   updated with the new lifecycle tag.

4. **`docs/WORKFLOW.md` W13 "Primordia 压缩检查点"** — new principle
   added after W12. Principle count header: 十二原则 → 十三原则.
   W13 text (paraphrased): every wave, at session end, read `myco
   hunger`; if `structural_bloat: primordia` appears, the wave MUST
   either (a) `git mv` ≥N [COMPILED]/[SUPERSEDED] crafts into
   `archive/` until the count drops below the soft limit, or (b)
   append `deferred: primordia-compression (<reason>)` to the
   wave's entry in `log.md`. Neither → next wave's hunger re-fires
   the violation (W5 persistent-evolution violation).

5. **Cross-reference rehome** — 2 rows in `MYCO.md` and 2 references
   in `docs/primordia/vision_recovery_craft_2026-04-10.md` updated
   to point at `archive/` paths.

6. **Contract version bump** — `_canon.yaml` + `src/myco/templates/_canon.yaml`
   `contract_version` / `synced_contract_version`: v0.20.0 → v0.21.0.

**Authoritative craft**: `docs/primordia/archive/primordia_compression_craft_2026-04-12.md`
(kernel_contract class, 3 rounds, final confidence 0.88).

**Self-tests**:

- `myco hunger` BEFORE: `structural_bloat: primordia (45 > 40)` in
  advisory block. AFTER: `healthy: notes/ is metabolizing normally.`
  (signal gone, count 35).
- `ls docs/primordia/*.md | wc -l` → 35. `ls docs/primordia/archive/*.md
  | wc -l` → 11. Total preserved = 46 (no data loss; the archive
  directory is an additional location, not a deletion).
- `myco immune --project-dir .` → 16/17 green (only the pre-existing
  L13 MEDIUM on `pre_release_rebaseline_craft_2026-04-11.md` for its
  2-round body vs. current 3-round kernel_contract floor — out of
  scope for Wave 22).

**Limitations** (explicit, not hidden):

- **W13 is not lint-enforced.** It's a behavioral rule only. A wave
  that ignores it gets caught by the NEXT wave's hunger re-fire,
  not by an in-wave lint block. The craft's Round-2 attack R2.2
  explicitly accepts this: one-wave lag is acceptable because the
  advisory is loud and the response cost is low. A future contract
  could add L17 "structural_bloat + no archive-move-commit in the
  same wave = violation" if the one-wave lag proves too long.
- **archive/ is not append-only enforced.** There is no lint that
  rejects `git rm docs/primordia/archive/*.md`. The doctrine lives
  in the README preamble + W13 text. If a future wave needs to
  genuinely delete an archived file (e.g. secrets leaked), a
  kernel_contract craft must justify it.
- **Selection is judgment, not algorithm.** Which [COMPILED] crafts
  to archive is chosen by the wave, not by a deterministic filter.
  The craft accepts this; [COMPILED] status is an audit of
  "conclusion has already landed in wiki / canonical structures"
  and by definition any [COMPILED] craft is archive-safe.

**Closes**: NH-4 (MEDIUM) — structural_bloat advisory had no
standing response contract.

---

## v0.20.0 — 2026-04-12 (minor · observability integrity: L16 brief freshness + myco observe agent surface, Wave 21 — closes NH-3/NH-7)

**Author**: Claude (Myco kernel agent, autonomous run under user grant, Wave 21)

**Motivation**: Two panorama-#2 holes from the same pathology — a
sensor that can silently report an outdated truth.

- **NH-3 (MEDIUM)**: The Wave 17 boot brief is regenerated only on
  `myco hunger`. If canon or the contract changelog changes without
  a subsequent hunger run, the brief silently shows stale signals
  in the entry-point file's MYCO-BOOT-SIGNALS block. No lint
  enforcement existed.
- **NH-7 (MEDIUM)**: The `myco observe` verb produced output agents
  had no reason to invoke (`cat notes/*.md` worked as well). The
  verb held a seat at the table without doing any work for the
  agent — dead weight that diluted the four-verb digestive set.

**Change summary**:

1. **L16 Boot Brief Freshness lint** (`src/myco/lint.py::lint_boot_brief_freshness`).
   MEDIUM severity. Compares `.myco_state/boot_brief.md` mtime
   against `max(_canon.yaml, docs/contract_changelog.md)`. Fires if
   missing or stale. Respects `system.boot_brief.enabled` — if the
   injector is off, L16 no-ops.
2. **`myco observe --next-raw`** — prints the body of the oldest raw
   note (digest-queue head). Zero-argument target for the
   raw→digesting loop.
3. **`myco observe --tag T`** — filters notes whose frontmatter tags
   contain `T` (exact match). Sorted by `last_touched` desc.
   Respects existing `--status`, `--limit`, `--json`.
4. **Positional `myco observe <id>`** legacy mode unchanged.
5. **Canon bump** v0.19.0 → v0.20.0 in kernel `_canon.yaml` +
   `src/myco/templates/_canon.yaml`.
6. **Lint count** 15 → 16 dimensions (L0–L16).

**Self-tests** (all green):

- Kernel `myco immune` → 16/16 (only pre-existing L13 MEDIUM
  unrelated to Wave 21).
- `touch _canon.yaml && myco immune` → fires `L16 MEDIUM: boot brief
  is stale`, with brief mtime and canon mtime shown.
- `myco hunger && myco immune` → L16 clears back to PASS.
- `myco observe --next-raw` → prints panorama-#2 note body + "Next:
  myco digest <id>" hint.
- `myco observe --tag friction-phase2 --limit 5` → 5-row table sorted
  by last_touched desc, correct filter.
- `myco observe <id>` (positional legacy) → unchanged behavior.

**Known limitations**:

- L-1 L16 checks mtime, not content. Hand-edited brief with fresh
  mtime passes (but hand-editing violates W1/L11 anyway).
- L-2 `--tag` matches frontmatter only, not body text. Full-text
  search is an explicit non-goal.
- L-3 `--next-raw` sorts by filename timestamp, which ties can
  fall back to random hex suffix string order. Deterministic but
  not semantically meaningful on same-second collisions.
- L-4 Brief is still only regenerated on `myco hunger`, not
  automatically on canon edit. File watcher was considered and
  deferred.

**Authoritative craft**:
`docs/primordia/archive/observability_integrity_craft_2026-04-12.md`
(3 rounds, kernel_contract, confidence 0.90).

**Doctrine**: a verb that shows the same thing `cat` shows is
dead weight. Every kernel surface must earn its keep — either by
doing something agents cannot easily do otherwise, or by
guaranteeing a property (e.g., freshness) that raw file access
cannot.

---

## v0.19.0 — 2026-04-12 (minor · silent-fail elimination: grandfather ceiling + strict project-dir, Wave 20 — closes NH-1 HIGH / NH-2 CRITICAL)

**Author**: Claude (Myco kernel agent, autonomous run under user grant, Wave 20)

**Motivation**: Panorama #2 note `n_20260411T235030_f184` surfaced two
non-overlapping holes that share a single pathology — *missing or
disabled configuration silently produces a false-healthy signal
instead of a loud alarm.* Concrete evidence:

- **NH-2 (CRITICAL)**: `detect_contract_drift` gated ALL detection
  behind `boot_reflex.get("enabled", False)`. Instances whose canon
  pre-dates Wave 13 have no `boot_reflex` block → default False →
  detector returns None. ASCC (`synced_contract_version: v0.8.0`,
  kernel `v0.18.0` — 10 minor versions of drift) reports `healthy`
  on `myco hunger`. The Wave 13 reflex arc is invisible to the one
  instance that needs it most.
- **NH-1 (HIGH)**: `_project_root` walked up for `_canon.yaml` and
  on failure fell through to `return Path(raw).resolve()`. Running
  `myco hunger --project-dir .` from `/tmp` returned a clean report
  with no warning that `/tmp` is not a Myco project — `total notes:
  0 · healthy`. The sensor was disconnected and reported "nothing to
  see here".

Both failures produced **false confidence** — the worst failure mode
for a sensory system.

**Change summary**:

1. **Grandfather ceiling** in `detect_contract_drift`
   (`src/myco/notes.py`). Runs BEFORE the `boot_reflex.enabled` gate.
   Computes `minor_gap = kernel_minor - synced_minor`. Fires
   `[REFLEX HIGH] grandfather_expired` if `minor_gap > ceiling`.
   Major-version mismatch is unconditional HIGH. Parse failure on
   either side fires `[REFLEX MEDIUM] version_parse_error`. Ceiling
   is canon-configurable via
   `system.boot_reflex.grandfather_ceiling_minor_versions` (default
   `5`; `0` = strict lockstep, large number = disabled).
2. **`_parse_version_tuple(s)`** helper in `notes.py`. Accepts
   `vMAJOR.MINOR[.PATCH]` / `MAJOR.MINOR[.PATCH]`. Returns tuple or
   None. Semver-ish, not strict semver.
3. **`MycoProjectNotFound` exception** in `notes.py`. Raised by
   strict `_project_root` when no `_canon.yaml` found in walk-up.
4. **Strict `_project_root`** in `notes_cmd.py`. Replaces silent
   fall-through. Escape hatch: `MYCO_ALLOW_NO_PROJECT=1` env var for
   legitimate cron/multi-project use cases.
5. **`@_guard_project` decorator** wraps `run_eat`, `run_correct`,
   `run_digest`, `run_view`, `run_hunger`. Catches
   `MycoProjectNotFound`, prints to stderr, exits 2.
6. **`grandfather_ceiling_minor_versions: 5`** canon field added to
   both kernel `_canon.yaml` and `src/myco/templates/_canon.yaml`
   under `system.boot_reflex`.
7. **Contract bump** `v0.18.0 → v0.19.0` in both canons (kernel
   `contract_version` + `synced_contract_version`, template
   `synced_contract_version`).

**Self-tests** (all green):

- Kernel `myco hunger` at root → healthy (gap=0, within ceiling).
- Tamper kernel `synced` → `v0.10.0` → run `myco hunger` → fires
  `[REFLEX HIGH] grandfather_expired: 9 minor versions of drift`.
- Tamper kernel `synced` → `v0.10.0` AND `boot_reflex.enabled: false`
  → still fires `grandfather_expired` (ceiling runs before gate).
- `cd /tmp && myco hunger` → exit 2 with clear stderr message.
- `cd /tmp && MYCO_ALLOW_NO_PROJECT=1 myco hunger` → exit 0, reports
  0 notes (legitimate override).

**ASCC migration** (same-session landing, per craft D5): ASCC
`_canon.yaml` `synced_contract_version` bumped `v0.8.0 → v0.19.0`,
minimal `boot_reflex` block added, log.md decision entry appended.
This is "the migration debt costs exactly what it should cost" in
action — a one-time catch-up, not a recurring tax.

**Authoritative craft**:
`docs/primordia/archive/silent_fail_elimination_craft_2026-04-11.md`
(3 rounds, kernel_contract, confidence 0.92).

**Known limitations**:

- L-1 Version parser is semver-like (accepts `v0.8`), not strict
  semver. Acceptable because Myco's own scheme often omits PATCH.
- L-2 `grandfather_ceiling_minor_versions` is a fixed integer; no
  adaptive threshold based on substrate age or wave velocity.
- L-3 MCP server wrapper refactor for `MycoProjectNotFound` deferred
  — direct `myco` CLI is the audited surface this wave.
- L-4 The ASCC migration only catches this one instance; any other
  downstream projects will also fire on their next hunger until they
  are manually imported. That IS the feature.

**Doctrine**: A sensory system that returns "healthy" when its
sensors are disconnected is worse than a crash. A crash tells the
agent something is wrong; a silent zero is indistinguishable from a
truly-healthy signal. Wave 20 eliminates two silent-zero paths in
the kernel.

---

## v0.18.0 — 2026-04-11 (minor · `myco correct` self-correction ergonomic shortcut, Wave 19 — closes H-3 partial)

**Author**: Claude (Myco kernel agent, autonomous run under user grant, Wave 19)

**Motivation**: Panorama note `n_20260411T231220_3fb8` flagged H-3
MEDIUM: Hard Contract rule #3 special clause (self-corrections must
be eaten in the same turn with mandatory tags `friction-phase2,
on-self-correction`) had zero enforcement and zero ergonomic support.
In the same session that authored the panorama, at least three
self-corrections went uneaten — the rule existed on paper but
silently died under execution pressure because the agent had to
remember both the rule text and the exact tag incantation. Wave 19
drops the ergonomic barrier to a single verb.

**Changes**:
1. **New `myco correct` CLI subcommand**. Thin wrapper over `run_eat`
   in `src/myco/notes_cmd.py` that force-merges the mandatory tag
   pair `friction-phase2, on-self-correction` onto any note produced
   via this verb. User-supplied `--tags` are appended in order,
   deduplicated exactly. Arguments mirror `myco eat` (`--content`,
   `--file`, `--title`, `--source`, `--json`, `--project-dir`).
2. **Subparser + dispatch** wired into `src/myco/cli.py`.
3. **Canon declarative block** `system.self_correction.mandatory_tags`
   added to both kernel `_canon.yaml` and template canon. Future
   waves (and any future lint dimension that cares about tag
   coupling) can reference this single source of truth rather than
   hard-coding the pair.
4. **Documentation nudge** in `docs/agent_protocol.md` §5.1(c):
   one-line pointer to the new shortcut as the preferred invocation.
5. **Contract version bumped** to `v0.18.0` in both kernel and
   template canon; `synced_contract_version` aligned.

**Dogfood evidence**:
- `myco correct --content "Wave 19 self-test" --title "..."` →
  tags emitted as `friction-phase2, on-self-correction` (exact pair,
  no extras).
- `myco correct --content "merge test" --tags "reference-error,test-tag"`
  → tags `friction-phase2, on-self-correction, reference-error,
  test-tag` (mandatory pair first, user tags appended, order preserved).
- Both self-test notes `myco digest --excrete "self-test fixture"`
  to keep the notes/ substrate clean.
- `myco immune --project-dir .` after all edits: 16/16 green, L15 PASS
  (the Wave 19 craft's fresh mtime covers the freshly-touched
  `notes_cmd.py`, `agent_protocol.md`, and canon surfaces — every
  edit is inside the evidence window).

**Hole closure mapping**:
- **H-3 partial**: ergonomic barrier drops from "remember the rule
  text + remember the exact tag incantation" to "type one verb".
  Full closure — automatic detection of self-correction text —
  requires chat-stream NLP which is Phase 2 MCP-server hook work,
  explicitly out of scope for kernel code.
- **H-2** (pure volitional eat) and **H-6** (shell HEREDOC vs MCP
  append path) remain unfixed; these are documented as accepted
  architectural limits of agent-initiated sensing in the followup
  Wave.

**Migration notes**:
- New instances cloned from the template inherit the `self_correction`
  canon block immediately.
- Existing instances get the block when they next sync with the
  kernel; `myco immune` does not currently require the block, so its
  absence on downstream is benign.
- Agents should update their default self-correction incantation
  from `myco eat --tags friction-phase2,on-self-correction ...` to
  `myco correct ...` — identical effect, one verb to remember.

**Known limitations** (see craft §6):
- **L-1** Cannot detect the self-correction utterance itself. Full
  H-3 closure is Phase 2 work.
- **L-2** Agent still has to *remember to run* `myco correct`. Wave
  17 boot brief is the read-path reminder for the rule text in
  `MYCO.md` heat zone. No further kernel-level enforcement is
  possible.
- **L-3** Tag deduplication is exact-string; minor spelling variants
  (`friction_phase2` vs `friction-phase2`) are distinct entries.
  Acceptable because canon pins the canonical spelling.

**Craft of record**:
`docs/primordia/archive/myco_correct_shortcut_craft_2026-04-11.md`
(3 rounds, kernel_contract class, current_confidence 0.91).

---

## v0.17.0 — 2026-04-11 (minor · L15 trigger surface expansion + optional git hook installer, Wave 18 — closes H-4/H-5)

**Author**: Claude (Myco kernel agent, autonomous run under user grant, Wave 18)

**Motivation**: Panorama note `n_20260411T231220_3fb8` surfaced two
defensive-layer holes that Wave 17 did not address. H-4: the L15
`kernel_contract` trigger-surface whitelist lacked
`docs/contract_changelog.md`, `src/myco/notes.py`, `src/myco/notes_cmd.py`
— the last four contract bumps (Wave 14/15/16/17) all modified
`notes.py` and survived purely on moral discipline. H-5: L15 fires
only at `myco immune` time; a commit that skips lint (or uses
`--no-verify`) silently bypasses the reflex with no second line of
defense.

**Changes**:
1. **Widened L15 detection surface**. `_canon.yaml` and
   `src/myco/templates/_canon.yaml` both gain three entries under
   `system.craft_protocol.reflex.trigger_surfaces.kernel_contract`:
   `docs/contract_changelog.md`, `src/myco/notes.py`,
   `src/myco/notes_cmd.py`. `trivial_exempt_lines: 20` remains the
   escape valve for whitespace/import mechanical edits.
2. **New optional pre-commit hook installer**:
   `scripts/install_git_hooks.sh`. Idempotent (detects
   `MYCO-PRECOMMIT-MARK`), refuses foreign-hook overwrites without
   `--force`, installs a hook body that fail-opens if `myco` is not
   on PATH, blocks commits only on CRITICAL/HIGH findings, surfaces
   MEDIUM/LOW but lets the commit proceed.
3. **Contract version bumped** to `v0.17.0` in both kernel and
   template canon; `synced_contract_version` aligned.

**Dogfood evidence**:
- `myco immune --project-dir .` after canon edits: 16/16 green, L15
  PASS (this craft's mtime covers the freshly-touched surfaces).
- `bash scripts/install_git_hooks.sh`: installs at
  `.git/hooks/pre-commit`, `rwx------`, 818 bytes.
- Re-run without `--force`: "already installed" idempotent no-op.
- Direct hook invocation: runs `myco immune`, prints MEDIUM warning
  (Wave 15 pre_release_rebaseline nudge), exits 0 (commit would
  proceed).
- This changelog entry itself is written on a surface that is now
  declared as `kernel_contract` — the sibling craft
  `docs/primordia/archive/l15_surface_and_git_hooks_craft_2026-04-11.md`
  satisfies the evidence_pattern window, proving the new surface is
  self-hosting.

**Hole closure mapping**:
- **H-4 full**: `contract_changelog.md` + `notes.py` + `notes_cmd.py`
  now declared surfaces; future edits without a sibling craft will
  fire L15.
- **H-5 full**: opt-in pre-commit hook provides a second enforcement
  surface on the write path, fail-open so never worse than status
  quo. L15 at lint time remains the primary surface; the hook is a
  belt-and-suspenders redundancy.

**Migration notes for downstream instances**:
- After `git pull`, the widened surface is active immediately. If
  an in-flight edit on `notes.py` or `contract_changelog.md` has no
  accompanying craft within the lookback window, L15 will fire
  HIGH — write the missing craft in-session per Wave 12 reflex
  doctrine, or use `trivial_exempt_lines` if the edit qualifies.
- To install the hook: `bash scripts/install_git_hooks.sh`.
  Uninstall: `rm .git/hooks/pre-commit`. The hook is not part of
  `pip install`; installation is a one-time explicit action per
  clone.

**Known limitations** (accepted, see craft §6):
- **L-1** PowerShell-native Windows users need Git for Windows
  installed to run the bash installer.
- **L-2** Hook fail-opens when `myco` is not on PATH — deliberate
  choice; missing linter ≤ no hook at all.
- **L-3** `--no-verify` bypasses the hook. Addressed by the Wave 17
  boot brief at the next session boot, not by per-commit enforcement.
- **L-4** Widened trigger surface means more L15 fires during
  refactoring sweeps. Expected, and `trivial_exempt_lines` remains
  the escape valve for mechanical edits.
- **L-5** Installer is bash-only this wave; PowerShell variant is
  future work but explicit non-goal here.

**Craft of record**:
`docs/primordia/archive/l15_surface_and_git_hooks_craft_2026-04-11.md`
(3 rounds, kernel_contract class, current_confidence 0.91).

---

## v0.16.0 — 2026-04-11 (minor · boot brief injector + upstream_scan_stale reader, Wave 17 — closes H-1/H-7/H-8 partial/H-9)

**Author**: Claude (Myco kernel agent, autonomous run under user grant, Wave 17)
**Craft record**: `docs/primordia/archive/boot_brief_injector_craft_2026-04-11.md`
（3 轮 Claim→Attack→Defense→Revise，终置信度 0.92，`decision_class:
kernel_contract`，target 0.90）

**Motivation**. The agent-panorama self-audit
(`notes/n_20260411T231220_3fb8.md`) surfaced 9 structural holes in Myco's
reflex architecture. Four share one root cause:

> **Every reflex arc depends on the agent voluntarily running
> `myco hunger` / `myco immune` as the heartbeat that delivers sensory
> input. If the agent skips that invocation at session boot, every
> downstream reflex silently fails.**

Evidence: the agent resumed this session from Batch 3 without running
`myco hunger` at boot, bypassing Wave 13/14 reflex arcs entirely. The
only surface Myco can reach *passively* (without requiring agent
initiative) is the entry-point file (`MYCO.md` / `CLAUDE.md`), which
project-instructions mechanisms deliver automatically into the agent's
context window. Wave 17 exploits that surface.

**Changes**:

- `_canon.yaml` + `src/myco/templates/_canon.yaml`:
  `contract_version: "v0.15.0" → "v0.16.0"`, `synced_contract_version`
  synced. New blocks `system.upstream_scan` (stale_days, enabled) and
  `system.boot_brief` (enabled, brief_path, sentinels, priority_signals).
- `src/myco/notes.py`: 新增三个函数
  - `detect_upstream_scan_stale(root)` — 读 Wave 16 时间戳，检查 stale
    + `.myco_upstream_inbox/` bundle 数量；HIGH if (stale AND pending),
    MEDIUM if (stale AND no pending), None otherwise
  - `write_boot_brief(root, report)` — 序列化 HungerReport 为
    `.myco_state/boot_brief.md` (markdown)
  - `render_entry_point_signals_block(root, report)` — 用严格正则匹配
    `<!-- MYCO-BOOT-SIGNALS:BEGIN ... -->` / `... END -->` sentinel
    对, 在原地 patch entry-point 文件的 signals block。entry-point 文件
    通过 `canon.system.entry_point` 解析（默认 MYCO.md；ASCC 实例是
    CLAUDE.md），实现跨项目复用
  - 辅助: `_count_pending_bundles(inbox)` 数 `.myco_upstream_inbox/` 顶层
    bundle 文件
- `src/myco/notes.py::compute_hunger_report`: wire
  `detect_upstream_scan_stale` into signal chain after `session_end_drift`
- `src/myco/notes_cmd.py::run_hunger`: 在 `compute_hunger_report` 后、
  JSON/pretty 输出前调用 `write_boot_brief` + `render_entry_point_signals_block`，
  任何异常捕获为 `[WARN]`（绝不阻塞 hunger）
- `src/myco/lint.py::lint_dotfile_hygiene` (L12): 扩展 `ALLOWED_DIRS` 加入
  `.myco_state`；新验证分支接受任意 `.md`/`.json` 文件，拒绝子目录
- `MYCO.md` + `src/myco/templates/MYCO.md`: 在 🔥 热区顶部注入 sentinel
  块（初始状态 placeholder，第一次运行 hunger 后会被 renderer 填充）
- `/sessions/.../mnt/OPASCC/CLAUDE.md` (ASCC 实例): 同样插入 sentinel 块，
  跨项目 dogfood

**Dogfood evidence**.

```
$ python -m myco.cli hunger    # kernel
✓ .myco_state/boot_brief.md created
✓ MYCO.md signals block patched with current state

$ python -m myco.cli hunger --project-dir .../mnt/OPASCC  # ASCC
✓ .myco_state/boot_brief.md created (in ASCC)
✓ CLAUDE.md signals block patched (entry_point lookup worked)
```

**Synthetic stale test**.
Set `upstream_scan_last_run` to 2026-04-03 (8d ago) + create dummy
bundle in `.myco_upstream_inbox/` → hunger correctly emitted:

```
[REFLEX HIGH] upstream_scan_stale: last scan was 8d ago (threshold 7d)
AND 1 bundle(s) pending in .myco_upstream_inbox/. Upstream Protocol
v1.0 autopilot violation — run `myco upstream scan` + ...
```

MYCO.md signals block auto-updated with the HIGH signal in the top
140 chars. Test fixtures cleaned up.

**Hole closure**:

- **H-1 (Boot 协议无强制)**: 从"agent 必须调用 hunger"转为"agent 被动读
  entry-point 即见信号"。信号通过 project-instructions 注入到 agent
  context window，无需主动调用。
- **H-7 (Wave 14 LOW advisory visibility)**: session_end_drift 现在会在
  下次 boot 时通过 signals block 浮现，LOW 级信号仍然温和但至少可见。
- **H-8 (session end 非原子)**: partial — 初始 writer 仍然依赖 agent 调
  hunger 写入，但 reader 端（下次 boot 读 brief）被动化。上半段靠
  Wave 14 LOW drift 在下次 hunger 时回捞；下半段闭环。真正的零
  initiative closure 需要 host-side session hook，超出 kernel 范围
  (see L-3).
- **H-9 (upstream_scan_stale reader 不存在)**: fully closed. Wave 16
  writer + Wave 17 reader 形成完整 feedback loop.

**Migration**. Existing instances 下次 boot 会触发 Wave 13 contract_drift
HIGH reflex (`v0.15.0 → v0.16.0`)，按 agent_protocol.md §8.4 更新本地
`synced_contract_version`。若实例已手动迁移 entry_point 文件插入
sentinel 块 → 下次 hunger 立即填充；若未迁移 → renderer emit `[WARN]`
然后 skip（绝不损坏文件）。Hand-patch migration 留给各实例自行决定。
未来 Wave 17-b 可将 sentinel 注入加入 `myco graft` 自动化步骤。

**Known limitations**:

- **L-1**: Sentinel 块注入是手动迁移。`myco graft` 自动化留给 Wave 17-b
- **L-2**: Brief 新鲜度是被动的。如果 hunger 一周没跑，brief 说"一周前"，
  靠 agent 看时间戳自己察觉。没有 "hunger_stale" 元信号
- **L-3**: H-8 仍部分 — 初始 writer 依赖 agent 调 hunger。真零 initiative
  需 host-side session hook
- **L-4**: L2/L6 对 signals 块的 exclusion 是文档声明，不是代码强制。
  当前 L2/L6 实现不扫这个区域所以无冲突，但未来迭代需注意
- **L-5**: 并发 hunger 写入未加锁。单 agent 假设下可接受

---

## v0.15.0 — 2026-04-11 (minor · upstream scan timestamp write path, Wave 16 — closes Wave 13 A7)

**Author**: Claude (Myco kernel agent, autonomous run under user grant, Wave 16)
**Craft record**: `docs/primordia/upstream_scan_timestamp_craft_2026-04-11.md`
（3 轮 Claim→Attack→Defense→Revise，终置信度 0.91，`decision_class:
kernel_contract`，target 0.90）

**Motivation**. Contract v0.6.0 (Upstream Protocol v1.0) declared
`system.upstream_scan_last_run` as a cached scan timestamp. Wave 13's
Boot Reflex Arc craft A7 referenced it as a potential
`upstream_scan_stale` trigger. But **no code path ever wrote it** —
the field has been stuck at `null` across every `_canon.yaml` and
`src/myco/templates/_canon.yaml` since introduction. Batch 4 closes
the hole: the Wave 13 A7 split explicitly scoped this write-path work
as a separate fix. This is that fix.

**Changes**:

- `_canon.yaml`: `system.contract_version: "v0.14.0" → "v0.15.0"` and
  `synced_contract_version` matching (kernel self-reference).
- `src/myco/templates/_canon.yaml`: `synced_contract_version` bumped
  to `v0.15.0`.
- `src/myco/upstream_cmd.py`: 新增 `_update_scan_timestamp(root)` helper
  和 `_SCAN_TS_RE` 正则；在 `_cmd_scan` 末尾（`scan_kernel_inbox` 成功
  返回后、任何输出前）调用 helper。实现是**外科式正则替换**，
  不是 `yaml.dump()` 往返——否则会销毁 `_canon.yaml` 里密集的注释。
  Regex 要求严格单一匹配；零匹配或多匹配 → `[WARN]` bail，scan 不失败。
- Timestamp 格式：`YYYY-MM-DDTHH:MM:SSZ`（UTC，秒精度，作为 YAML
  quoted string 存储）。失败模式：`scan_kernel_inbox` 抛异常 → 不写
  时间戳（部分扫描不算 fresh）；IO/正则失败 → stderr WARN，scan 仍成功。

**Self-test dogfood**. Ran `myco upstream scan` against kernel itself:

```
🍄 Upstream inbox clean — 0 pending bundles.
```

`_canon.yaml` after:

```yaml
upstream_scan_last_run: "2026-04-11T14:57:40Z"
```

All surrounding comments (Upstream Protocol v1.0 header block) preserved
byte-for-byte. L12 Upstream Dotfile Hygiene lint continues to pass.

**Design rationale** (from craft Rounds 2-3):

- **Why not `yaml.dump()` round-trip?** PyYAML's default dumper destroys
  all comments and reorders keys. `_canon.yaml` is heavily commented with
  Wave 8 rebaseline banner, W1/W5/W8 doctrine notes, and severity
  justifications — destroying them every scan would be catastrophic.
  ruamel.yaml is a new dependency the kernel does not currently take.
  Surgical regex preserves everything.
- **Why write on zero-pending scans?** The timestamp records scan
  **freshness** (i.e. "agent checked the inbox") not scan **result**.
  Downstream reflexes (future `upstream_scan_stale` signal) want to
  answer "has the inbox been checked recently?", not "has the inbox
  had pending bundles recently?". Not writing on zero-pending would
  force redundant re-scans.
- **Why string not YAML native timestamp?** PyYAML's `safe_load`
  returns `datetime` objects for YAML timestamps which do not
  JSON-serialize — hunger report + MCP surface emit JSON.
  ISO-8601 strings survive round-trips cleanly.

**Migration**. Existing instances需下次 boot 触发 Wave 13 `contract_drift`
HIGH reflex（`v0.14.0` → `v0.15.0`），按 `agent_protocol.md §8.4` 更新
本地 `synced_contract_version`。无需代码变更。

**Known limitations**:

- L-1: 消费端（读取此时间戳的 `upstream_scan_stale` reflex 信号）**尚未
  实现**。本 craft 只铺管道的写入端，reader 留给未来 Wave。
- L-2: 正则依赖 `upstream_scan_last_run:` 在 `_canon.yaml` 里保持一致缩进。
  如果用户手改嵌入到其它层级 → writer 优雅失败（WARN，不崩），下次 scan
  再次尝试。
- L-3: 亚秒精度丢失——对于以小时到天为尺度的 scan 频率，这不是
  有意义的损失。

---

## v0.14.0 — 2026-04-11 (minor · L13 body schema, Wave 15 — craft content measurement)

**Author**: Claude (Myco kernel agent, autonomous run under user grant, Wave 15)
**Craft record**: `docs/primordia/archive/l13_body_schema_craft_2026-04-11.md`
（3 轮 Claim→Attack→Defense→Revise，终置信度 0.90，`decision_class:
kernel_contract`，target 0.90）

**Motivation**. Partial closure of `docs/craft_protocol.md §7 #3`
("Body structure is not linted"). Before Wave 15, `rounds: N` in craft
frontmatter was a pure self-declaration — authors could write `rounds: 5`
with a 50-character body and pass L13. Wave 15 introduces L13 body schema
check that measures body content against frontmatter claims:

- **body_chars floor** (HIGH) — total non-whitespace body chars must be
  ≥ `rounds × min_body_chars_per_round` (default 200 per round → 600 for
  rounds=3). Catches hollow crafts where the author declared N rounds
  but wrote a stub.
- **body_rounds match** (HIGH) — if `## Round N` anchors are present,
  their count must equal declared `rounds`. A declaration of 5 with 2
  actual round headings is a lie, not a style variant.
- **body_rounds == 0 nudge** (MEDIUM) — if no round anchors detected,
  emit a style nudge (not HIGH) because some existing crafts use
  alternative structures (e.g. `## Attacks → ## Defenses`). Grandfather
  by encouragement, not exemption.
- **per-round slice floor** (MEDIUM) — if individual round slice below
  `min_round_body_chars` (default 150), flag as thin round.

Round markers accept English (`Round N`, `R(N)`), Chinese (`第N轮`),
Japanese (`ラウンド N`). Counting uses non-whitespace chars
(language-neutral, CJK-friendly).

**Dogfood evidence**. All 11 existing `docs/primordia/*_craft_*.md` files
measured: 10/11 have `body_rounds` matching declared, all 11 have
`body_chars` well above floor (smallest: lint_ssot 5919 chars declared=2
floor=400). The single MEDIUM finding goes to `pre_release_rebaseline`
which uses an alternative `## Attacks → Defenses` layout — intentional
nudge per D4 of the craft, not exemption.

**Changes**:

- `_canon.yaml` + `src/myco/templates/_canon.yaml`:
  `system.contract_version: "v0.13.0" → "v0.14.0"` and
  `synced_contract_version: "v0.13.0" → "v0.14.0"`（kernel self-reference）；
  新增 `craft_protocol.body_schema` 子块：`enabled`, `min_body_chars_per_round`,
  `min_round_body_chars`, `round_markers` (4 regex patterns), `exempt_files`.
- `src/myco/lint.py`: 新增 `_l13_body_metrics(content, round_markers)`
  helper（frontmatter 剥离 / 多语言 round 解析 / 每轮切片 char 计数）；
  `lint_craft_protocol` 末尾追加 4 条 body 检查，对应上述 4 种 severity。
- `docs/craft_protocol.md`: §7 #3 从 "not linted" 改写为 "partially linted"，
  含 severity 表 + 多语言 round marker 说明 + 指向 craft 文件的 authoritative
  argument 引用。

**Migration**. Existing crafts 无需修改：10/11 已满足新 schema。
`pre_release_rebaseline` 收到 MEDIUM 风格建议但不阻塞。
下游实例下次 boot 会触发 Wave 13 contract_drift reflex（v0.13.0 → v0.14.0），
按 agent_protocol.md §8.4 更新本地 `synced_contract_version` 即可。

**Known limitations**:

- L-1: `body_rounds == 0` 情况只给 MEDIUM，不强制改 `## Round N`——
  避免破坏已有辩论风格多样性。
- L-2: Goodhart 残留——作者理论上仍可用冗余空白填满 body_chars 阈值。
  Transparency countermeasure（§4）继续是主要防线。
- L-3: Chinese numeral 解析仅覆盖 1-99；三位以上（极罕见）会 fallback
  to int conversion failure → 跳过该 marker。
- L-4: 200 char/round 是工程 bootstrap 值，由首次 Phase ② friction 数据验证
  后重新校准；canon-configurable，无需 code change。
- L-5: `exempt_files: []` 启动时为空——原则上所有 craft 都应可被验证。
  若未来发现合理豁免类，通过 craft + contract minor bump 添加。

---

## v0.13.0 — 2026-04-11 (minor · session end reflex arc, Wave 14 — W5 drift visibility)

**Author**: Claude (Myco kernel agent, autonomous run under user grant, Wave 14)
**Craft record**: `docs/primordia/archive/session_end_reflex_arc_craft_2026-04-11.md`
（3 轮 Claim→Attack→Defense→Revise，终置信度 0.91，`decision_class:
kernel_contract`）

### Motivation

Wave 13 关闭了 session **boot** 的 W1/§8.4 drift（contract_drift、
raw_backlog HIGH、hunger 接入 myco_pulse）。Session **end** 的对应漏洞
仍然开放——`docs/agent_protocol.md §4` 的 5 步 prose（reflect / log /
hunger / lint / MYCO.md）没有任何 code-level 反射：agent 跳过 Gear 2 反思
或 Gear 4 sweep，下次 boot 没有信号告知。

**Dogfood 证据**（Wave 14 前夜 kernel 自检）：
- `log.md` 最后一条 `## [YYYY-MM-DD] meta |` 反射：2026-04-10；其后累计
  **18** 条非 meta 条目（milestone / friction / system / craft）。一整天
  的内核推进没有留下任何 Gear 2 轨迹。
- `grep -c "g4-candidate" log.md` = **18**；`grep -c "g4-pass" log.md` =
  **0**。候选在 log 里静默沉底。
- 两者都没触发任何 lint 或 hunger 信号。

结论：`myco_reflect` 是 advisory pull-style 工具，靠 agent 记硬背。跟
Wave 13 同构——只能由 hunger 主动 surface，不能等 agent 自觉调用。

### Changes

1. **新 hunger 检测器** `detect_session_end_drift(root) -> Optional[str]`
   （`src/myco/notes.py`）。读 `log.md`（bounded 5 MB），用宽容 regex
   解析 `## [YYYY-MM-DD] <type>` header，并列跑两个子检测：
   - **gear2**：统计最后一个 `meta` header 之后的非 meta 条目数，超
     `drift_threshold_entries`（默认 15）则 fire。
   - **gear4**：扫描每个 `g4-candidate` 行所属 header 日期，若 age ≥
     `drift_threshold_days`（默认 5 天）且同行无 `g4-pass` /
     `g4-landed` / 磁盘上存在的 craft 文件引用则计入，累计 ≥1 即 fire。
   两个子信号合并为一行输出，加入 `HungerReport.signals`。
   Fail-open：IO / 解析异常 → 返回 None（grandfather）。

2. **Severity = LOW**（刻意与 Wave 13 HIGH 不对称）。W5（持续进化）是
   drive 而非 W1 级 data-loss constraint；过度升级会让 agent 学会忽略
   整个 advisory 列表。LOW 信号在 `myco_pulse.hunger_signals.advisory`
   而非 `.reflex`，不阻塞任务流。完整论证见 craft §B4。

3. **新 canon 块** `system.session_end_reflex`（同步到
   `_canon.yaml` 和 `src/myco/templates/_canon.yaml`）：
   ```yaml
   session_end_reflex:
     enabled: true
     severity: LOW
     log_scan_cap_bytes: 5242880
     gear2:
       enabled: true
       drift_threshold_entries: 15
       reflection_marker: meta
     gear4:
       enabled: true
       drift_threshold_days: 5
       candidate_marker: g4-candidate
       resolution_markers: [g4-pass, g4-landed, g4-resolved]
   ```
   Gear 2 和 Gear 4 可独立关闭，阈值可 instance 侧 override。

4. **`docs/agent_protocol.md §4` 重写** — 5 步 prose → 2 步反射弧
   （`myco_hunger` → 处理 `session_end_drift`）。与 §3 Boot Sequence
   对称。传统 5 步流程仍然有效，但由 hunger 驱动而非硬背。

5. **版本锁**：kernel `contract_version`、instance `synced_contract_version`
   同步 v0.12.0 → v0.13.0（kernel 自引用）。下游实例下次 boot 会触发
   Wave 13 `contract_drift` HIGH 反射——设计行为，这是 drift 传播路径。

6. **模板同步**：`src/myco/templates/_canon.yaml` 加入同款
   session_end_reflex 块。模板里的 MYCO.md hot-zone boot 条款在 Wave
   14 不需要新增（信号是 LOW advisory，会话启动时作为一行出现在
   `hunger_signals.advisory`，无需 agent 特殊记硬背）。

7. **Dogfood cleanup in same session**：
   - 写一条 `## [2026-04-11] meta |` 反射总结 Wave 13+14（Gear 2 复位）
   - 18 个 `g4-candidate` 均 <5 天，无需 sweep（kernel 当前 gear4 clean）
   - `myco hunger` → `session_end_drift` 清除 → commit

### Migration for downstream instances

**自动部分**：下次 boot 调用 `myco_pulse` → Wave 13 contract_drift
HIGH 反射 fire → agent 读本条目 → 把本地 `synced_contract_version` 更新
到 `v0.13.0`。

**可选部分**：
- 若 instance 想关闭 gear2 或 gear4 检测：复制 canon 块并设 enabled=false
- 若 instance log entry 节奏不同（低频更新、纯 milestone-driven）：调高
  `gear2.drift_threshold_entries`
- 若 instance g4-candidate 决议依赖外部追踪（issue tracker）：关闭
  gear4 或自定义 resolution_markers

**不需要**代码更改。检测器 grandfather 在 canon 块缺失时，自动返回 None。

### Known limitations (from craft §5)

- **L-1 Conservative pairing**: g4-candidate 只认 inline `g4-pass` /
  磁盘 craft 引用。依赖其他机制决议的候选会被 over-flag。v1 trade-off。
- **L-2 Reflection quality unmeasured**: 只检测 meta 条目**存在**，不
  检测内容。一词 meta 条目满足检测。Gear 2 质量是 Self-Model C 层问题
  （open problem §5），超出 Wave 14 scope。
- **L-3 Threshold calibration deferred**: 15 / 5 天是 kernel-tuned
  默认值。后续 2-3 session dogfood 会 confirm 或调整。
- **L-4 Single log.md assumption**: 检测器只读 repo 根的 `log.md`。
  多日志 / sharded 布局不支持。
- **L-5 No sweep automation**: Wave 14 只 surface drift，不 auto-resolve
  g4-candidate。sweep 仍是手动 Gear 4 ritual。

### Wave 14 dogfood discipline

Wave 13 范式：land 功能 + 在同一 session 清理 kernel 自身的 debt。
Wave 14 继承——本次 session 内写一条 Wave 13+14 联合 `meta` 反射进
`log.md` 以复位 gear2 计数器，并 `myco eat` 一条 wave14 结论 note 到
`notes/` 走 integrated。

---

## v0.12.0 — 2026-04-11 (minor · boot reflex arc, Wave 13 — W1 + §8.4 enforcement)

**Author**: Claude (Myco kernel agent, autonomous run under user grant, Wave 13)
**Craft record**: `docs/primordia/archive/boot_reflex_arc_craft_2026-04-11.md`
（3 轮 Claim→Attack→Defense→Revise，终置信度 0.91，`decision_class:
kernel_contract`，floor 0.90；7 个 R1 attack + 4 个 R2 attack + 4 个 R3 sweep；
A7 split force scoped batch 到只 contract_drift + raw_backlog HIGH + hunger
wiring，`upstream_scan_last_run` 写路径延后到 Batch 4）

**Motivation**（Wave 12 逻辑的直接延伸 + realtime dogfood 证据）：
Wave 12 建立了 "reflex 在理论上必反射、在实践上变 advisory 必然产生非零失效"
的原则并用 Wave 10 README 跳 craft 事件作证。Wave 13 发现同一条失效定律
在另外三条"理论上是反射但实践上是 prose"的路径上继续成立：

1. **contract_drift**：`docs/agent_protocol.md §8.4` 明确规定 instance
   启动时要比对 `synced_contract_version` 与 kernel `contract_version`，
   但代码里**一行比对都没有**。instance 可以停在 v0.8 与 v0.11 kernel
   对话，按过时反射规则生产代码，lint 看不见（lint 读的是本地陈旧 canon）。

2. **raw_backlog**：W1 (auto-sedimentation) 是 Myco 消化基质的**根本前提**
   ——它被 craft_protocol 级反射对待的程度却远低于 W3。craft_reflex_missing
   升级到 HIGH，raw_backlog 还停在 text advisory。Wave 12 原则意味着要么
   raw_backlog 同样升级到 HIGH，要么承认 W1 是装饰性的——后者不可接受。

3. **Boot sequence skip**：`agent_protocol.md §3` 的 4 步 boot 是 prose。
   `myco_pulse` 不调用 hunger，raw_backlog 不返回在 status 里。一个 session
   可以完全不碰消化基质就开工，boot arc 只存在于文档而不是代码。

**Realtime dogfood evidence**：Wave 13 craft 落地时，`myco hunger` 报告
Myco kernel 仓库**本身**有 27 条 raw notes。基质在自己身上消化失败。

**Changes**:

- **`_canon.yaml::system`** — 新增 `boot_reflex` 块（`enabled: true`,
  `severity: HIGH`, `raw_backlog_threshold: 10`, `reflex_prefix:
  "[REFLEX HIGH]"`, `raw_exempt_sources: [bootstrap]`)；新增
  `synced_contract_version: "v0.12.0"` 作为 kernel self-reference；
  `contract_version` 从 `v0.11.0` bump 到 `v0.12.0`。
- **`src/myco/notes.py`** — 新增 `detect_contract_drift(root)` 函数，比对
  local synced 与 kernel contract_version（优先同文件，fallback 到
  `src/myco/templates/_canon.yaml` 的 ledger），不一致发 `[REFLEX HIGH]
  contract_drift`；`compute_hunger_report` 前置调用 drift 检测并
  refine raw_backlog 计数为 pure_raw_count（`digest_count == 0` 且
  `source` 不在 `raw_exempt_sources` 中），raw_backlog 信号升级为
  `[REFLEX HIGH]` 并带 W1 违规警告 + 最少 digest 数量指引。
  craft_reflex_missing 同步添加 `[REFLEX HIGH]` 前缀。
- **`src/myco/mcp_server.py::myco_pulse`** — 新增 `include_hunger:
  bool = True` 参数，默认调用 `compute_hunger_report` 并把 reflex /
  advisory 信号分桶返回在 `hunger_signals` 字段下；出现 reflex 信号时
  `hint` 被替换为强制警告。Docstring 明确 `include_hunger=False` 在
  raw_backlog 非空时等同 W1 违规。
- **`src/myco/templates/_canon.yaml`** — 同步新 `boot_reflex` 块 +
  `synced_contract_version` 提升到 v0.12.0。
- **`src/myco/templates/MYCO.md`** — 热区 boot 条款从 "契约版本比对
  (boot step)" 改写为 "Boot Reflex Arc (v0.12.0)"：明确新反射信号语义 +
  `include_hunger=False` 等价于 `--no-verify` 的 W1 违规。
- **`docs/agent_protocol.md`** — §3 Session Boot Sequence 改写为 2 步 arc
  (status → handle reflex signals → task)，§8.4 新增 "代码侧强制 (Wave 13,
  contract v0.12.0)" 子节解释 drift detector。
- **`docs/primordia/archive/boot_reflex_arc_craft_2026-04-11.md`** — 本 craft
  决议文件。

**Migration (downstream instances)**:

1. 拉取 Wave 13 kernel，`pip install -e /path/to/Myco --break-system-packages`。
2. 更新本地 `_canon.yaml::system.synced_contract_version` 到 `v0.12.0`。
3. 运行 `myco_pulse`（MCP）或 `myco hunger`（CLI）验证无
   `[REFLEX HIGH] contract_drift` 信号。
4. 如果本地 raw notes 中 pure-raw (digest_count=0 且非 bootstrap 源) > 10
   → **本会话内** `myco digest` 到阈值下再继续任务。
5. 新的 `include_hunger=False` 参数谨慎使用；raw_backlog 非空时调用等同 W1 违规。

**Known limitations (carried forward)**:

- **L-1**（honor-system ceiling）：drift detector 只比版本字符串，不检查
  本地反射实现与 kernel 是否真的一致——pinned v0.12.0 instance 也可以
  本地改 lint_craft_reflex。Wave 12 已承认同类限制。
- **L-2**：`include_hunger=False` 纯文档约束，无代码 enforcement。与
  `--no-verify` 同级。
- **L-3**：`raw_backlog_threshold: 10` 是 bootstrap 值，未经 Phase ②
  friction 数据校准。若使用中发现合法 burst（如 forage absorb 批次）
  常被误触发，调整为动态值。
- **L-4**：drift 检测只在 boot 时一次。Session 内 `git pull` 拉进新版本
  kernel 不会二次触发——acceptable (Wave 11 reasoning)。

**Wave 13 dogfood discipline**:

Kernel 仓库的 27 raw notes 在 Wave 13 landing 作为配套动作被消化到
≤1（本 craft 的 conclusion note pre-digest）。这是 W1 的实时 self-test：
基质必须能在自己身上执行它强加给下游的代谢纪律，否则 contract 就是
虚的。消化结果记录在 log.md Wave 13 milestone。

---

## v0.11.0 — 2026-04-11 (minor · craft autonomy, Wave 12 — overturns Wave 8 A7)

**Author**: Claude (Myco kernel agent, autonomous run under user grant, Wave 12)
**Craft record**: `docs/primordia/craft_autonomy_craft_2026-04-11.md`
（3 轮 Claim→Attack→Research→Defense→Revise，终置信度 0.92,
`decision_class: kernel_contract`，floor 0.90；7 个 Round-1 attack + 4 个
Round-2 attack + 4 个 Round-3 attack；关键修正来自 A4 overturn 推理、A6
"severity HIGH is performative" 迫使加 agent protocol binding、A7 迫使加
`trivial_exempt_lines` 机械编辑豁免。）

**Motivating contradiction**: Myco 身份声明是 Autonomous Cognitive
Substrate。但 Wave 11 的 §3.1 里写"Reflex is a signal, not a gate. Craft
remains a human ritual"——这句话直接违背核心身份：如果 craft 需要人
invoke，Myco 就不是 autonomous 的，agent 永远在等人拍肩膀。用户 Wave 12
在会话中指出此矛盾后，Wave 8 A7 的判断（"craft 的核心是人与 agent 的
持续对话，不是可自动化的 job"）也随之暴露为需要覆盖——A7 在 Wave 8
时是对的（那时 L15 不存在，CLI-style 自动化是真的 ceremony），但
Wave 11 落地 L15 后，automation target 变了：不再是"CLI 人类调用"，而是
"trigger surface 触碰 → craft 文件在 agent loop 内物化"的反射弧。

**Conventional Commit prefix**: `[contract:minor]` — 向后兼容（旧 instance
不更新 synced_contract_version 就看不到 severity 变化；新 reflex 字段向后
兼容缺省），但**对下游有 CI pipeline 的实例是潜在 breaking**：严格处理
lint 退出码的 CI 现在会看到 L15 触发 exit code 1 而不是 0。迁移指南见
"下游 instance 对齐步骤"。

### 变更摘要

1. **`craft_protocol.reflex.severity`: `LOW` → `HIGH`**（`_canon.yaml`）。
   L15 触发不再是软警告，是硬 lint error。Agent 的 W3 义务是**同一
   session 内立刻写出缺失 craft**，而不是"改天再说"或"问人"。
2. **新字段 `reflex.trivial_exempt_lines: 20`**。Trigger surface 被碰但
   `git diff --numstat` 显示改动行数 ≤ 20 AND 无新 identifier（regex
   检测 `def/class/function/top-level YAML key`）→ 豁免反射。Git 不可用
   时 fail-closed（照常触发）。这解决 "whitespace 修复被迫写 ceremony
   craft" 的失败模式。
3. **`src/myco/lint.py::lint_craft_reflex` 扩展**：读 `trivial_exempt_lines`
   配置、调用 `git diff` 判定是否豁免、wrap 在 try/except 处理 git 缺失/
   untracked 文件 fail-closed 情形、更新 issue 文案强调 "write NOW not
   later"。severity default 从 LOW 改 HIGH。
4. **`src/myco/notes.py::detect_craft_reflex_missing` 文案更新**：hunger
   信号从 "Either create... or cite" 改成 "IMMUTABLE REFLEX: write the
   missing craft... in this session before any other kernel-class
   action. Bypassing via --no-verify is a W3 violation."
5. **`docs/craft_protocol.md` 大改 §1 / §3.1 / §4 / §4.5 新增 / §7 扩**：
   - §1 移除 "Myco's formal ritual" / "human ritual" framing，改为
     "agent-autonomous selection-pressure mechanism"；加 Wave 8 A7
     overturn block 解释 Wave 12 的 supersession 逻辑
   - §3.1 从 "Discovery surface" 改名为 "Reflex arc"；删除 "signal
     not gate" 和 "human ritual" 字样；明确 4 步反射弧；severity=HIGH
     理由；明确 --no-verify 是 W3 违规
   - §4 新 "Single-source convention" 段落（single-agent debate
     cap: current_confidence ≤ target_confidence）
   - §4.5 新 "Collaboration model" 子节：人类仍在 **review loop** 而非
     **invocation loop**；human-authored / 协作 craft 可 supersede
     agent-only
   - §7 追加 3 条 Known limitations（honor-system ceiling /
     trivial_exempt threshold 未校准 / git 依赖 fail-closed）
6. **Template 同步**：`src/myco/templates/_canon.yaml` 同步
   severity HIGH + trivial_exempt_lines; `src/myco/templates/MYCO.md`
   热区 W3 clause 完全重写强调 "不可绕过反射弧"
7. **`system.contract_version`**: `"v0.10.0" → "v0.11.0"`
   （minor，Wave 8 re-baseline 后仍走 v0.x）

### 下游 instance 对齐步骤

1. 拉最新 Myco kernel
2. `_canon.yaml::system.craft_protocol.reflex`：
   - `severity: LOW` → `severity: HIGH`
   - 新增 `trivial_exempt_lines: 20`
3. 更新 `synced_contract_version` 到 `"v0.11.0"`
4. 更新本地 `MYCO.md` 热区 W3 clause（参考 kernel template）
5. **CI pipeline 迁移**：如果有 CI 严格处理 `myco immune` exit code：
   - 选项 A（推荐）：让 CI 继续严格，workflow 要求 agent 在 CI 前
     已经写好 craft（即让 reflex 在 agent loop 内闭环）
   - 选项 B：CI 临时把 L15 issue 映射到 warning，配合 commit hook
     做预防
   - 不推荐：关掉 reflex (`enabled: false`)——这是退化到 Wave 10 之前
     的状态
6. 首次 `myco immune`：如果本地有 trigger surface 最近被动过且没写
   craft，会立刻触发 HIGH——此时的协议响应是**写 craft**，不是
   suppress warning

### 已知限制

1. **Honor-system ceiling**：严格来说 agent 可以写 hollow craft 糊弄
   L15 HIGH。只有 transparency（git + log.md + notes/）作补偿。Hollow-
   craft detection（attack depth scoring、online research citation
   count）登记为 Wave 13+ 未来工作。
2. **`trivial_exempt_lines: 20` 是 bootstrap 值**。需 Phase ② friction
   数据校准。
3. **Git 依赖**：trivial_exempt 用 `git diff`，非 git 环境或首次 commit
   前 fail-closed（照常触发）。
4. **Wave 8 A7 overturn 的元风险**：本 craft 的合法性建立在"A7 当时
   对，现在错"之上。如果未来证据表明 A7 一直对、L15 本身是错误路径，
   整个 Wave 11/12 反射栈都需要回退。该风险被接受，因为 Wave 10 的
   empirical failure 是比 A7 ex-ante 推理更硬的约束。

---

## v0.10.0 — 2026-04-11 (minor · craft reflex, Wave 11)

**Author**: Claude (Myco kernel agent, autonomous run under user grant, Wave 11)
**Craft record**: `docs/primordia/craft_reflex_craft_2026-04-11.md`
（3 轮 Claim→Attack→Research→Defense→Revise，终置信度 0.91,
`decision_class: kernel_contract`，floor 0.90；7 个 Round-1 attack + 4 个
Round-2 attack + 2 个 Round-3 attack，关键修正来自 A7（必须把 trigger surface
切成 `kernel_contract` 与 `public_claim` 两类才能捕获 Wave 10 README 漏触发事件）
和 C1/C2（检测基准从 log.md 正则 pivot 到文件 mtime）。）

**Motivating failure**: Wave 10 vision-led README 三语重写完全没走 craft。
这是教科书级 Trigger #4（external stakeholder-visible claim）——但发现面
纯文档，agent 必须在决策当下主动想起 craft 才能触发。Craft 辍触的根源不
是 craft 不存在，而是 **discovery surface 是被动的**。Wave 11 把被动改成
主动：trigger surface 被碰 + 无 craft 证据 → 触发 LOW 信号。

**Conventional Commit prefix**: `[contract:minor]` — 新增 L15 lint 维度 +
新增 hunger 信号 + 新增 canon 子块；向后兼容（`reflex.enabled: false` 即
完全关闭；旧 instance 不更新 synced_contract_version 就看不到 L15）。

### 变更摘要

1. **新 canon 子块 `system.craft_protocol.reflex`**（`_canon.yaml`）：
   - `enabled: true`, `lookback_days: 3`, `severity: LOW`
   - `trigger_surfaces.kernel_contract`：agent_protocol / craft_protocol
     / _canon / lint / mcp_server / templates/**（7 个文件）
   - `trigger_surfaces.public_claim`：README × 3 + MYCO.md + docs/vision.md（5 个文件）
   - `evidence_pattern`：匹配 craft 文件名或 `craft_reference:` 字段
2. **L15 Craft Reflex lint 维度**（`src/myco/lint.py::lint_craft_reflex`）：
   - 主检测：trigger surface 的 `path.stat().st_mtime` 是否在 `lookback_days` 窗口内
   - 辅检测：log.md 或 `docs/primordia/*_craft_*.md` 的 mtime 是否同窗口内存在 craft 证据
   - 缺失证据 → 按 severity 发 issue；`reflex.enabled=false` 时返回空
   - 注册点：`main()::checks` 列表，非 quick 模式执行
   - docstring 从 "15-Dimension" 升为 "16-Dimension"
3. **`craft_reflex_missing` hunger signal**（`src/myco/notes.py::detect_craft_reflex_missing`）：
   - 与 L15 同规则，但在 `myco hunger` 每次会话启动时都发
   - 好处：不依赖主动跑 lint，session boot 就能看见
4. **`docs/craft_protocol.md §3.1 Discovery surface`** 新增：
   - 列举 5 条发现面（文档 / WORKFLOW W3 / MYCO.md 热区 / hunger 面板 / L15 lint）
   - 说明为什么 mtime 优先于 log 正则（Round 3 C1/C2 辩论结果）
   - 声明"reflex 是信号不是门闸"——craft 仍是人工仪式
5. **§8 Deprecation criteria 扩展**：为 L15 加反向日落条款
   （6 个月零违规 AND 至少发生过一次合规的 trigger 触碰才能判定为"习惯内化"；
   Goodhart 防御：若发现 craft 被用来水过 L15，应加强而非移除）
6. **Template 同步**：
   - `src/myco/templates/_canon.yaml` 同步 `craft_protocol.reflex` 块 +
     `synced_contract_version: "v0.10.0"`
   - `src/myco/templates/MYCO.md` 热区 W3 行追加 Reflex 提示句
7. **`system.contract_version`** bump: `"v0.9.0" → "v0.10.0"`
   （Wave 8 pre-release re-baseline 后仍走 v0.x 线，不是 v1.3.1）

### 下游 instance 对齐步骤

1. 拉最新 Myco kernel
2. 复制 `_canon.yaml::system.craft_protocol.reflex` 整块到本地 canon
3. 更新本地 `synced_contract_version` 到 `"v0.10.0"`
4. 首次 `myco immune`：L15 可能在本地 README / MYCO.md 刚被动过时报 LOW——
   此时补写 craft 或在 log.md 引用现有 craft 即可；缺默认不阻塞 commit
5. 在 `MYCO.md` 热区的 W3 行加入 Reflex 字样（参考 kernel template）

### 已知限制

1. `mtime` 理论上可被 `touch` 欺骗，但 Myco 没有"你被自己骗了"这种威胁模型。
2. `lookback_days: 3` 是未经校准的 bootstrap 值，需 Phase ② friction 数据收敛。
3. 纯抽象决策（不碰文件）仍无法被 reflex 捕获——这仍要靠 W3 习惯。
4. 非实时：reflex 只在 `myco immune` / `myco hunger` 被调用时才发信号。

---

## v0.9.0 — 2026-04-11 (minor · upstream absorb impl)

**Author**: Claude (Myco kernel agent, autonomous run under user grant, Wave 9)
**Craft record**: `docs/primordia/upstream_absorb_craft_2026-04-11.md`
（2 轮 Claim→Attack→Research→Defense→Revise，终置信度 0.91，
`decision_class: kernel_contract`，floor 0.90；5 个 Round-1 attack +
3 个 Round-2 attack，A2/A5/B1/B2/B3 全部落地为修正或撤回）

**Parent craft**: `docs/primordia/upstream_protocol_craft_2026-04-11.md`
（本 wave 执行的是父 craft 落地清单 D 段 `myco upstream scan/confirm` CLI
——v1.0 当时显式延后至 v1.0.1 并忘记。Wave 9 把"延后"关掉，并在此过程中补齐
了父 craft 未写清的 "bundle → note 冶炼协议"。）

**Conventional Commit prefix**: `[contract:minor]` — 只新增接口，不破坏既有
outbox 约定，下游 ASCC 写 outbox 的代码无需任何改动。

### 变更摘要

1. **`.myco_upstream_inbox/` kernel 侧接收坞物理落地**。此前 L11 lint 已把
   它作为合法 dotdir 保留（`src/myco/lint.py:622`），但目录本身从未创建。
   现在 `myco upstream absorb` 会按需 `mkdir(exist_ok=True)`，并包含
   `absorbed/` 审计子目录。
2. **新 CLI 三件套 `myco upstream {scan, absorb, ingest}`**（`src/myco/upstream.py` +
   `src/myco/upstream_cmd.py`）：
   - `scan` — 列出 kernel inbox 里待 ingest 的 bundle（不计 `absorbed/`）
   - `absorb <instance-path>` — 从 downstream instance 的 `.myco_upstream_outbox/`
     拷贝到 kernel inbox；加 `<YYYYMMDDTHHMMSS>_` 前缀；跳过重复项；instance 不可达时 `exit 2`
   - `ingest <bundle-id>` — 创建一条 `source: upstream_absorbed` 的 pointer
     note（carrying bundle.summary + evidence link），同时把 bundle 本体移到 `absorbed/`
3. **Pointer-note 设计锁**（来自 craft Round 1 Attack A4）：ingest 绝不把
   bundle 的 YAML 结构转写为 note body。bundle 完整结构保留在 `absorbed/`
   作为证据；note 只是指针。L10 notes schema 无需为 upstream bundle 开例外。
4. **`VALID_SOURCES` 扩展**：新增 `"upstream_absorbed"` 作为第六个合法 source
   （`src/myco/notes.py`）。
5. **新指标 `upstream_inbox_pressure`**（`_canon.yaml::indicators.substrate_keys`）：
   - 公式：`min(pending_bundle_count / 5, 1.0)`
   - ceiling=5 是 bootstrap 值，canon 注释标注"pending friction data"
   - 在 `MYCO.md 📊 指标面板` 和 `src/myco/templates/MYCO.md` 同步
6. **`upstream_absorb` canon block**：`_canon.yaml::system.upstream_absorb`
   定义 kernel_inbox_dir、absorbed_subdir、bundle_filename_pattern、
   pointer_note_source、batch_ingest_cap。`src/myco/upstream.py` 作为
   class_z write_surface 条目新增。
7. **`docs/agent_protocol.md §8.5.1 / §8.5.2 / §8.5.3`** 新增：kernel 侧动词清单、
   Courier Fallback 人工搬运路径（当 kernel 和 instance 不在同会话时）、
   `upstream_inbox_pressure` 指标说明。
8. **`examples/ascc/handoff_prompt.md` Step 11.5** 新增：instance agent 生成
   bundle 之后如何通知用户 / 如何指向 Courier Fallback / 如何触发 kernel 侧
   absorb（若 kernel 也挂载在同会话）。
9. **首次真实 dogfood**（与父 craft v1.0 `on-self-correction` 验收点 B 对接）：
   本 wave 执行了对 ASCC 的 `ce72`（template / CLAUDE.md 入口缺口）和 `3356`
   （L1 scanner backtick false positive）两条 kernel friction bundle 的 absorb
   + ingest，并触发了各自的后续修复 craft / 直接 patch（见 log.md Wave 9
   milestone）。

### 已知限制

- **KL1** ceiling=5 是拍脑袋值，等 3-5 次真实 absorb 后由 Phase ② friction
  数据驱动调整。
- **KL2** L14 forage hygiene 的 TTL 机制**不**套用到 upstream 侧。未来可能补
  `notes_digestion_pressure` 细分类目，但不在 Wave 9 范围。
- **KL3** Courier Fallback 的信任链是"用户本人 + 文件名规范"，无签名。合理
  性：当前 instance 都是单用户本地项目。

---

## v0.8.0 — 2026-04-11 (major · re-baseline)

**Author**: Claude (Myco kernel agent, autonomous run under user grant, Wave 8)
**Craft record**: `docs/primordia/archive/pre_release_rebaseline_craft_2026-04-11.md`
（2 轮 Claim→Attack→Research→Defense→Revise，终置信度 0.92，
`decision_class: kernel_contract`，floor 0.90；5 个 Round-1 attack +
3 个 Round-2 attack 全部防御）

**Conventional Commit prefix**: `[contract:major]` — 首位是 major 不是 minor，因为版本号主号从 1 降到 0 理论上是下游可感知的破坏性变更（尽管语义不变）。

### 变更摘要

1. **Pre-release re-baseline**：所有 v1.x.y contract 版本和 1.x.y 包版本下调为 v0.x.y / 0.x.y。最新 contract 版本从 v1.7.0 → **v0.8.0**。包版本从 1.1.0 → **0.2.0**。PyPI classifier 从 `5 - Production/Stable` → `4 - Beta`。
2. **量化指标体系（Quantified Indicators）**：新增 `_canon.yaml::system.indicators` schema block，定义：
   - `range: [0.0, 1.0]` 默认区间
   - `valid_suffixes: [_progress, _confidence, _maturity, _saturation, _pressure]`
   - `bootstrap_ceiling_without_evidence: 0.70`（无外部 evidence 时自评上限）
   - `rationale_required: true`
   - `stale_after_days: 90`
   - `authoritative_value_location: MYCO.md#指标面板`（= dashboard 是 value 层唯一写入点，canon 只存 schema）
   - `history_location: log.md`（= milestone + commit hash 是 value 变化的 audit log）
   - 7 个 substrate_keys 实例：`v1_launch_progress / three_channel_maturity / lint_coverage_confidence / compression_discipline_maturity / identity_anchor_confidence / forage_backlog_pressure / notes_digestion_pressure`
3. **MYCO.md 新增 `## 📊 指标面板`**：authoritative value location，每项含 value + rationale + 证据锚。
4. **Directory hygiene**：
   - `dist/myco-1.1.0-*.whl` + `dist/myco-1.1.0.tar.gz` 物理删除（因为它们是旧版本数值的陈旧副本）
   - `.gitignore` 清理 6 条陈旧 `docs/current/*_craft_*.md` 条目（该目录在 v1.5.0/现 v0.5.0 已重命名为 `docs/primordia/`）
   - 活跃源代码里所有 "9-dimension / 14-dimension" 陈旧字符串更新为 "15-dimension (L0-L14)"
   - 活跃源代码里所有 inline `v1.X.Y` contract 注释更新为 `v0.X.Y`（历史 docstring/narrative 保留 v1.x）
5. **历史记录 immutable doctrine 保留**：log.md 的 dated 条目、primordia/ 下已存在的 craft 记录、本 changelog v1.x 历史条目全部保持原样。只有 **current-state** 字段被更新。

### 影响范围

- **Kernel**: `_canon.yaml`（contract_version + indicators schema）、`pyproject.toml`（包版本+classifier）、`src/myco/__init__.py`、`src/myco/templates/_canon.yaml`（同步）、`src/myco/templates/MYCO.md`（若需要）、多个源码 docstring
- **Docs**: `MYCO.md`（banner + 新增指标面板段）、`docs/contract_changelog.md`（本条 + 顶部 re-baseline banner）、`docs/agent_protocol.md`（§8.4 当前 contract 行）、`README.md`、`CONTRIBUTING.md`、`docs/reusable_system_design.md`、`adapters/README.md`、`examples/ascc/README.md`
- **Adapters/Examples**: 版本和 lint 维度数的陈旧字符串全部对齐
- **Tests**: 无破坏（语义未变，只是数字下调）

### 下游反射规则

下游看到 `synced_contract_version < v0.8.0`（包括任何 v1.x 字符串）时：
1. 先读本 changelog 顶部的 re-baseline banner
2. 把本地 `_canon.yaml::system.synced_contract_version` 字符串手动/工具替换：`v1.X.Y → v0.X.Y`（主号 -1）
3. 其余 config 无需改动
4. PyPI 包重新安装时会拿到 `0.2.0`（>1.1.0 不再存在）

### 未进入本次 contract 的非目标（Wave 9+ registered）

- L15 Indicators Lint 实现（本 wave 只把 schema 定了，机械化 lint 延后）
- 历史 changelog 条目的回填式 re-baseline（违反 immutable doctrine，明确拒绝）
- `_myco_*.txt / _extract_session.py / ascc_sessions/` 等本地 scratch 文件的物理清理（在 .gitignore 覆盖下，不影响 repo）
- MYCO.md 的进一步拆分
- Self-Model A/B/C 层的完整实现

---

## v1.7.0 — 2026-04-11 (minor)

**Author**: Claude (Myco kernel agent, autonomous run under user grant)
**Craft record**: `docs/primordia/forage_substrate_craft_2026-04-11.md`
（2 轮 Claim→Attack→Research→Defense→Revise，终置信度 0.92，
`decision_class: kernel_contract`，floor 0.90；9 个 Round-1 attack +
3 个 Round-2 attack 全部防御）
**Trigger**: 用户 Q2 提出 "Myco 缺少一个下载 / 存放 GitHub 项目 / 博客 /
论文等外部资料的地方"，架构师回顾确认这是代谢循环的**第三条通道**——
inbound（forage/）——此前缺失。Myco 原有通道只覆盖 internal（notes/）
和 outbound（upstream），没有 inbound。任何 agent 要调用外部知识必须每次
联网搜索，违反压缩即智能学说。

### Added

- **`forage/` 目录**——外部参考材料前消化缓冲区。
  包含 `forage/_index.yaml`（manifest，class_z 契约锚点）、`forage/papers/`
  `forage/repos/` `forage/articles/`（按类型分桶，默认 `.gitignore` 二进制）、
  `forage/README.md` 和 `forage/.gitignore`。
- **`system.forage_schema` canon block** —— manifest schema / 有效状态集 /
  体积阈值 / license 重核周期的 SSoT。字段：`dir`、`index_file`、
  `filename_pattern`、`required_item_fields`、`optional_item_fields`、
  `valid_source_types`、`valid_statuses`、`max_item_size_bytes` (10 MB)、
  `forage_backlog_threshold` (5)、`stale_raw_days` (14)、
  `total_budget_bytes` (200 MB)、`hard_budget_bytes` (1 GB)、
  `license_recheck_days` (90)。
- **`src/myco/forage.py`** —— 纯函数引擎：`add_item` / `list_items` /
  `update_item_status` / `detect_forage_backlog` / `validate_item` /
  `load_manifest` / `save_manifest` / `generate_forage_id`。与 `cli.py` /
  `mcp_server.py` 单向依赖，防止环依赖。
- **`src/myco/forage_cmd.py`** —— `myco forage add/list/digest` 的薄 CLI
  分发层。
- **CLI verb family**: `myco forage add --source-url ... --source-type ...
  --license ... --why ... [--local-path ...]`、`myco forage list
  [--status ...]`、`myco forage digest <item_id> --status ...
  [--digest-target ...]`。
- **L14 Forage Hygiene lint**（`src/myco/lint.py::lint_forage_hygiene`）——
  manifest 可读性、`validate_item` 逐项校验、per-item size cap、
  hard budget cap、orphan local_path (MEDIUM)、orphan disk file (LOW)、
  stale license (LOW)。是单 SSoT——`scripts/lint_knowledge.py` 作为 v1.6.0
  落地的 shim 自动继承。
- **`forage_backlog` hunger signal**（`src/myco/notes.py::compute_hunger_report`）——
  触发条件：raw 计数 ≥ threshold OR 任意 raw item 超过 stale_raw_days OR
  总体积 ≥ soft budget。读取通过 `forage.detect_forage_backlog(root)`。
- **`forage/_index.yaml` → `upstream_channels.class_z`** —— manifest 作为
  substrate 对外部世界的契约承诺必须走 Review 通道。实际文件
  `forage/{papers,repos,articles}/**` 由 `.gitignore` + L14 管理，不走
  Upstream 协议。
- **`forage/` → `write_surface.allowed`** —— L11 认可的合法写入目标。
- **`forage` → `notes_schema.valid_sources`** —— digest 出的 note 在
  frontmatter `source: forage` 标记血统。
- **agent_protocol.md §8.9 三通道代谢分类** —— 显式承认 inbound / internal /
  outbound 三条正交通道，各自的生命周期、物理载体、lint 契约、hunger
  信号一表定义。禁止 `forage → upstream` 捷径。
- **biomimetic_map.md §1 Foraging glossary entry + §2 表格行** —— `forage/`
  是 Myco 第一个**在诞生当天就因真实信息增益而被赋予生物学名字**的目录，
  打破 §3 理由 1"通用名字已经在不等式错误一侧"的惯例。

### Changed

- `_canon.yaml::system.contract_version`: `v1.6.0` → `v1.7.0`
- `src/myco/templates/_canon.yaml::system.synced_contract_version`:
  `v1.6.0` → `v1.7.0`，同步镜像 `forage_schema` block（保证 `myco seed`
  出的下游 instance 从第一天起就拥有 forage 通道）。
- `src/myco/lint.py` docstring: `14-Dimension` → `15-Dimension`，新增 L14
  条目。
- `src/myco/cli.py`: 新增 `forage` 子命令解析器与分派块。
- `MYCO.md` banner: `v1.6.0 lint SSoT 合流` → `v1.7.0 forage substrate
  inbound channel`。

### Rationale

1. **三层代谢同心圆补齐**——`agent_protocol.md §8` 早已承认基质有 "内→
   kernel / instance↔instance / 世界→substrate" 三条代谢通道，v1.7.0 之前
   最外层只有"未来 v2.0"占位符。Forage 不是 v2.0 的 full-metabolic inlet，
   是它的**最小可信雏形**——只做 acquire + manifest + lifecycle + hunger +
   lint 五件事，不做内容抽取。
2. **discipline over capability**——craft Round 1 A1 防御：如果 v1.7.0 就
   上 PDF / repo 语义解析，agent 会把 forage/ 当图书馆填满，触发 structural
   bloat。Wave 7 通过 manifest-authoritative + 强制 `why` 字段 + 硬 budget
   + 自动 quarantine unknown license 来培养纪律。
3. **license legal hazard defense**——craft A2 防御：required field + 缺省
   `.gitignore` 二进制 + 默认 `unknown` → quarantined。L14 stale license
   reminder 做季度复核。
4. **channel orthogonality**——craft A3 + §8.9 显式声明防止 "forage =
   upstream 的延伸" 误解，三通道正交使 Upstream Protocol 的契约边界保持
   清晰。

### Known non-goals (Wave 8+)

- PDF / arXiv / 博客的语义抽取（待 `myco digest-paper` / `myco digest-repo`）。
- Git clone 自动化（现阶段由 `myco forage add --local-path` 人工填写）。
- 许可证自动识别。
- full-metabolic inlet（`system.upstream_channels` 中的 "世界 → substrate
  最外层"）——v2.0 目标。

### Migration

下游 instance 升级路径：
1. `git pull` 获取 kernel v1.7.0。
2. Boot sequence 检测 `contract_version` drift。
3. 走 Confirm 通道：`mkdir -p forage/{papers,repos,articles}` +
   `echo 'schema_version: 1\nitems: []' > forage/_index.yaml` + 从 kernel
   拷贝 `forage/README.md` 和 `forage/.gitignore`。
4. 同步 `synced_contract_version: "v1.7.0"`。

首次使用：`myco forage add --source-url <url> --source-type <type>
--license <spdx> --why "<intent>"`。

---

## v1.6.0 — 2026-04-11 (minor)

**Author**: Claude (Myco kernel agent, autonomous run under user grant)
**Craft record**: `docs/primordia/archive/lint_ssot_craft_2026-04-11.md`
（2 轮 Claim→Attack→Research→Defense→Revise，终置信度 0.93，
`decision_class: instance_contract`，floor 0.85；5 个 Round-1 attack +
2 个 Round-2 attack 全部防御）
**Trigger**: v1.5.0 收尾后的架构师全景回顾识别出 Myco 最大的结构债——
`scripts/lint_knowledge.py`（940 行）和 `src/myco/lint.py`（869 行）是
同一份 14 维 lint 实现的两个物理副本，每一波新增 lint 维度都要在两处
同步加代码，drift 风险长期存在。v1.4.0/v1.5.0 期间该债务被"年轻红线
保护"原则按下不动；v1.5.0 稳定后保护窗口关闭。

### Added

- **`docs/primordia/archive/lint_ssot_craft_2026-04-11.md`** — Wave 6 craft 档案。

### Changed

- **`scripts/lint_knowledge.py`**：940 行 → ~90 行 shim。零 lint 逻辑
  （`grep -c "def lint_" scripts/lint_knowledge.py` = 0），仅包含
  sys.path bootstrap + 最小 argparse-free 解析 + `from myco.lint import main`
  委托调用。
- **`src/myco/lint.py`**：成为单一 SSoT。两处 docstring
  （`lint_notes_schema` / `lint_write_surface`）从 "Runtime parity with
  scripts/lint_knowledge.py::..." 改为 "Single source of truth as of
  contract v1.6.0 — scripts/lint_knowledge.py is a shim."
- **`_canon.yaml::system.contract_version`**：`v1.5.0` → `v1.6.0`
- **`src/myco/templates/_canon.yaml::synced_contract_version`**：
  `v1.5.0` → `v1.6.0`

### Rationale

**为什么是 contract minor 而非 patch**：虽无新增维度 / 字段 / 触发点，
但这是两个 class_z 契约级文件的**结构性统一**——下游 instance 在 boot
时比对 `synced_contract_version` 应该感知到"lint 实现站点从 2 变为 1"，
走 minor 更诚实。下游 grandfather：旧的
`python scripts/lint_knowledge.py` 调用完全兼容，CLI 参数完全兼容，
零 migration 动作。

**为什么不直接删除 `scripts/lint_knowledge.py`**：三个 back-compat 锚点。
(1) canon `upstream_channels.class_z` 列出该路径；(2) `MYCO.md` /
`docs/WORKFLOW.md` / log.md 历史条目都用 `python scripts/...` 调用路径；
(3) 新读者从 `scripts/` 目录发现 CLI 入口是最自然路径。保留 shim 是
"最小侵入"策略。

**压缩 doctrine 的自我兑现**：v1.5.0 biomimetic_map §4 把 compression
列为核心 doctrine，但它之前只应用于文档和 notes。Wave 6 第一次把
compression 应用到**代码**本身——两份 lint 实现压缩为一份，~850 行
重复逻辑被 autolysis 掉。真菌不能消化自己最大的冗余组织就不能宣称
自己是代谢系统；同理 Myco 不能压缩自己的 lint 实现就不能宣称压缩是
核心价值。Wave 6 关闭这个 credibility gap。

### Known non-goals

- **没有新 lint 维度**。lint 行为完全不变，L0-L13 编号 / check 内容 /
  issue severity 全部保持。唯一不同是两个入口共享同一套代码路径。
- **没有 templates 双写消除**。`_canon.yaml` 与 `templates/_canon.yaml`
  仍然双写——templates 的存在理由就是"要被复制到新 instance"，
  `synced_contract_version` 机制是既定解法。out of scope。
- **L8 `.original` 语义不变**。L8 检查 wiki 压缩标记，与 lint 站点对等
  性无关（Round 1 A5 澄清点）。

### Migration for downstream instances

1. `git pull`
2. 检查 `_canon.yaml::system.contract_version` → `v1.6.0`
3. 更新本地 `synced_contract_version: v1.6.0`
4. `python scripts/lint_knowledge.py --project-dir .` → 14/14 PASS
5. `python -c "from myco.lint import main; main(Path('.'))"` → 14/14 PASS

---

## v1.5.0 — 2026-04-11 (minor)

**Author**: Claude (Myco kernel agent, autonomous run under user grant)
**Craft record**: `docs/primordia/biomimetic_restructure_craft_2026-04-11.md`
（3 轮 Claim→Attack→Research→Defense→Revise，终置信度 0.92，
`decision_class: kernel_contract`，floor 0.90；8 个 Round-1 attack +
3 个 Round-2 attack + 1 次 Round-3 on-self-correction 全部落地）
**Trigger**: 用户在 2026-04-11 panorama 回顾后明确提出
"Myco 的项目结构彻底重构重组织 + 借鉴仿生 Myco 生物学的优点和特点"，
并把这件事定位为"Myco 永恒进化的一部分——不断优化自己的内容组织形式"，
把压缩 doctrine 从代谢层（notes 压缩）升维到结构层（目录与文档拓扑压缩）。

**Self-correction 事件**：craft Round 1 的 Claim A "wiki/ 是空目录、rename
零代码成本" 在 Phase A1 执行前 grep 实测暴露为**错误前提**——`wiki/` 在
`src/myco/import_cmd.py` 硬编码 14 处（含整个 `hermes_skill_to_wiki()` 函数）、
`_canon.yaml` 5 处（含 `wiki_page_types` schema block）、6 份 contract 文档
+ README.md + MYCO.md 共 ~50 处深度引用。这是 "Map vs Territory 混淆" 的
教科书案例——只看了"物理空目录"就断定"概念空"。Round 3 修正后 Phase A1
被取消，`wiki/` 保留原名。这次 self-correction 本身被写进 craft §5b 作为
方法论案例，供未来 agent 学习。

### Added

**`docs/biomimetic_map.md`（新，contract 级身份锚点文档）**
- §0 为什么要有这份文档：把 Myco 的生物学血统给一个真实落脚点，同时
  严守"不强行套 metaphor"的纪律——只在真实信息增益处应用生物学命名。
- §1 生物学术语 Glossary：hypha / mycelium / primordium / sporocarp /
  spore / rhizomorph / exoenzyme / septum / sclerotium / mycorrhiza /
  hyphal tip 共 11 条定义，每条都附 "对应 Myco 基质" 的映射说明。
- §2 实际应用的映射表：12 行表格明确记录每个基质位置是否 rename、
  使用哪个生物学类比、理由。**唯一执行的 rename 是
  `docs/current/ → docs/primordia/`**。
- §3 为什么不全面 rename：三条架构理由（边际收益递减 / 架构腐蚀 vs
  biomimicry purity / 年轻红线保护）。这一节的存在本身是防止未来
  agent 重新发动一次"为生物学而生物学"的 rename 冲动。
- §4 压缩 doctrine 的生物学映射：sclerotium（致密休眠）/ autolysis（自溶）/
  nutrient reallocation（资源重分配）三条具体实现，其中 autolysis 和
  reallocation 已部分实现（D 层 dead_knowledge + hunger 信号），
  sclerotium 登记为未来工作。
- §5 Living document 维护规则 + §6 延伸阅读（含 Smith & Read 标准教材引用）。

**`_canon.yaml → system.structural_limits`（新 block）**
- `docs_top_level_soft_limit: 20` + `primordia_soft_limit: 40`
  —— 固定种子阈值，不是 adaptive；adaptive threshold 登记在
  `docs/open_problems.md §4` 作为后续工作。
- `exclude_paths: [10 条 contract 级文档]` —— 被明确列出的 contract 文档
  不计入 docs/ top-level 计数的分母，它们是 rhizomorph 不是 bloat。

**`src/myco/notes.py` 新函数**
- `detect_structural_bloat(root)` —— **只读**扫描 `docs/*.md` +
  `docs/primordia/*.md`，对照 canon 的 soft limits + exclude_paths
  生成 signal string 或 None。严守 read/write 分离红线——不触碰任何
  note 元数据。
- `_load_structural_limits(root)` helper —— 从 canon 读取阈值配置，
  缺失时使用 `DEFAULT_STRUCTURAL_LIMITS` 常量回退，保证老 instance
  向后兼容。
- `compute_hunger_report` 集成：新信号附加到 signals list 末尾，
  位置在 `dead_knowledge` 之后。

**`src/myco/templates/_canon.yaml`**
- 镜像同步 `structural_limits` block。
- `synced_contract_version: v1.4.0 → v1.5.0`。

### Changed

- `_canon.yaml::system.contract_version: v1.4.0 → v1.5.0`
- **`docs/current/ → docs/primordia/`**（**唯一的 rename**，~80 refs
  across 35 files；canon `craft_protocol.dir` 作为 SSoT，Python 默认
  回退值同步更新）
- `docs/contract_changelog.md` / `docs/craft_protocol.md` / `docs/agent_protocol.md`
  / `docs/open_problems.md` / `docs/architecture.md` / `MYCO.md` / `README.md`
  / 等 35 份文件的 `docs/current` 字符串引用全部更新为 `docs/primordia`。

### Rationale

**为什么"克制的仿生"而不是"全面的仿生"**：
craft Round 1-3 的真正产物不是 rename 本身，是**纪律**——边际收益原则
告诉基质：只在新名字的信息增量 > 学习成本 + 引用改动成本时执行 rename。
大多数基质目录（`notes/`, `src/`, `scripts/`, `docs/` 顶层）的通用名字
已经在这个不等式的错误一侧。唯一清晰越过门槛的是 `docs/current/ →
docs/primordia/`——"current" 只表达"正在活跃"，"primordia" 准确表达
"未定型、发育中、可退化"，+1 单位的语义清晰度值得 ~80 处引用改动。

**为什么结构 bloat 用 hunger signal 而不是 L14 lint**：
bloat 是**渐进退化**问题不是硬错误。Hunger 的语义是"基质在这方面饿了/撑了"，
驱动行为但不阻塞 commit。Lint 的语义是"违反 contract"，20 份 docs 本身
不违反任何 contract 只是值得注意，语义错位。同时 L13 §8 反向废弃标准
提醒基质："不要为了 lint 越多越好而创造 lint"——把 `structural_bloat`
留在 hunger 层是对这条原则的一致应用。这个决策本身被记录在 craft §4 R2.3
作为"L14 dead-on-arrival decision"的案例。

**为什么 Phase B ASCC 合并被取消**：
craft R2.2 设定了 70% Jaccard overlap 的合并门槛。Phase B 实测
`docs/ascc_migration_v1_2.md` vs `docs/ascc_agent_handoff_prompt.md` 的
token-level Jaccard = 28.15%，远低于门槛。两份文件服务于真实不同的受众
（human operator playbook vs paste-ready agent prompt）和结构（13 headers
vs 27 headers）。Gate 正确地阻止了一次会破坏信息的"压缩"。这是压缩
doctrine 的反例——**压缩不等于合并，压缩要先证明不是在破坏差异**。

**为什么 craft 需要 Round 3 on-self-correction**：
Round 1-2 的 Claim A1 "wiki/ 零成本 rename" 只是空想 check，没有实测
grep。Phase A1 执行前的前置 grep 直接证伪这个前提，触发 craft 内
on-self-correction（`docs/agent_protocol.md §5.1`）——craft 必须**在
执行前**纠正自己，而不是把错误传播到 commit。这是 Craft Protocol §2
"Research 轮可触发 Revise" 机制的第一次真实应用。**置信度 0.92 不是
从 0.91 "提高" 到 0.92，而是 craft 在收窄 scope 后对更小范围给出更
诚实评估**。

### Known non-goals (v1.5.0)

- **不 rename `notes/`**：硬编码深度太深，收益不足，红线风险。
- **不 rename `wiki/`**：50+ 处引用、概念承载深度高、Karpathy 血统正向。
- **不 rename `docs/open_problems.md → hyphal_tips.md`**：语义增益真实
  但需独立 craft 更新登记规则，留作未来工作。
- **不实现 sclerotium（致密休眠）压缩管线**：COMPILED→wiki+pointer 的
  压缩自动化，延伸 open_problems §4。
- **不实现 adaptive threshold**：`structural_bloat` 用固定种子阈值，
  自适应阈值随基质年龄进化登记为未来工作。
- **没有 L14 lint**：`structural_bloat` 明确选 hunger 层，不创建硬 lint。

### Migration

- **下游 instance 升级指令（机械执行）**：
  ```
  git mv docs/current docs/primordia
  # 更新 _canon.yaml::system.craft_protocol.dir: docs/current → docs/primordia
  # 更新 _canon.yaml::system.synced_contract_version: → v1.5.0
  # 全局替换 docs/current → docs/primordia（literal string，无 English-prose 冲突风险）
  # 添加 _canon.yaml::system.structural_limits block（copy from kernel template）
  # 运行 myco immune，确认 14/14 PASS
  ```
- `myco hunger --json` schema 在 signals 数组中可能出现新条目
  `structural_bloat`，消费者可安全忽略直到准备好。
- `docs/biomimetic_map.md` 是新增 contract 级文档——instance 可选择
  复制一份作为本地身份锚点，也可直接引用 kernel 版本。

---

## v1.4.0 — 2026-04-11 (minor)

**Author**: Claude (Myco kernel agent, autonomous run under user grant)
**Craft record**: `docs/primordia/archive/dead_knowledge_seed_craft_2026-04-11.md`
（2 轮 Claim→Attack→Research→Defense→Revise，终置信度 91%，
`decision_class: kernel_contract`，floor 0.90；8 个 Round-1 attack + 3 个 Round-2 attack 全部防御）
**Trigger**: `docs/open_problems.md §6` 登记的 Self-Model D 层空洞
（vision_recovery_craft §B 与 dead-knowledge 定义）需要可落地的最小种子，
以免 open problem 永久停留在"已知未实现"状态。

### Added

**`_canon.yaml → system.notes_schema` 扩展**
- `optional_fields: [view_count, last_viewed_at]`
  —— L10 识别但不强制，向后兼容所有历史 note（grandfather 生效）。
- `terminal_statuses: [extracted, integrated]`
  —— 被 D 层死知识检测用作入闸条件；仅处于"已settled"状态的 note 才能被判 dead。
- `dead_knowledge_threshold_days: 30`
  —— 默认阈值，同时用作"刚创建宽限期 + 未触碰冷却期 + 未阅读冷却期"三道闸的统一单位。
  instance 可通过 `myco genome` 覆盖，SSoT 仍在 `_canon.yaml`。

**`src/myco/notes.py` 新 API + 新数据**
- `record_view(path, *, now=None)` —— D 层 read-side 唯一写入路径：
  递增 `view_count`（缺省视作 0），写入 `last_viewed_at=now`，**绝不触碰 `last_touched`**。
  read/write 严格分离是本次改动的架构红线（防止"打开即修改"污染冷却信号）。
- `HungerReport` dataclass 新增 `dead_notes: List[Dict]` + `dead_threshold_days: int`；
  `to_dict()` 暴露两者以便 `--json` 消费者使用。
- `compute_hunger_report(root, *, stale_days=7, dead_threshold_days=None, terminal_statuses=None, now=None)`
  签名扩展；缺省值从 `_load_dead_config(root)` 读取 canon。
- 5 条件联合死知识判定循环（status ∈ terminal / created ≥ threshold /
  last_touched 冷 / last_viewed_at 空或冷 / view_count < 2），任一不满足即豁免。
- 新增信号字符串 `dead_knowledge: N terminal note(s) ...`。

**`src/myco/notes_cmd.py` CLI 集成**
- `run_view` 单 note 模式在渲染 body 后调用 `record_view(path)`；
  失败仅静默（view 仍保留读操作语义），并在 header 额外展示 `view_count` / `last_viewed_at` 字段（若存在）。
- `run_hunger` 在 promote_candidates 之后新增 💀 dead knowledge 显示块，
  列出前 10 条 + "…(N more)" 折叠；`dead_knowledge` 被加入 concerning 信号判定。

**`src/myco/templates/_canon.yaml`**
- 镜像同步上述 notes_schema 扩展。
- `synced_contract_version: v1.3.0 → v1.4.0`。

### Changed

- `_canon.yaml::system.contract_version: v1.3.0 → v1.4.0`。
- `docs/open_problems.md §6` 增加"已落地于 contract v1.4.0" 标记 + craft 反向链接；
  出口条件下调为"第一个真实的 excretion 决策基于 dead_knowledge 信号"。

### Rationale

vision_recovery_craft 明确 "D 层未实现" 是 Self-Model 的四大空洞之一。
Wave 3 把它登记进 open_problems.md §6，但登记本身不是进展——**种子必须能长**。
本次改动锚定：
- **最小种子优于完美方案**：完整 D 层需要 audit log / cross-ref / adaptive threshold，
  任何一项都足以拖延数月。v1.4.0 只做"能被真实 excretion 决策触发的最小闭环"。
- **grandfather 是软扩展的唯一入场券**：所有历史 note 都没有 view_count / last_viewed_at，
  optional_fields 机制保证 L10 不倒戈，老 note 的 view_count 缺省按 0 处理，
  首次达到宽限期 + 冷却期 + 无读 = 自动入选 dead，系统自动完成迁移。
- **read/write 分离是反污染红线**：若 `myco observe` 顺手 bump `last_touched`，
  冷却信号就永远为 0，D 层变空操作。这条防御必须写进代码而不是文档。

### Known non-goals (v1.4.0)

- **没有 view audit log**：只知"被 view 了 N 次"，不知"谁在什么上下文下 view 的"。
  excretion 决策仍需要人类判断"是否真的没人用"。
- **没有 cross-reference 追踪**：note 被 wiki 引用不会算作 "alive"。
  这是 §6 完整实现留给下一个 instance_contract 级 craft 的工作。
- **阈值是硬编码 SSoT**：没有随 substrate 年龄自适应的能力——
  Wave 5+ 才会触及身份锚点 4 的 adaptive threshold。
- **D 层的定义仍不完整**：本次只实现了"dead knowledge detection" 这一条；
  "degraded self-model" / "structural decay" 等子问题仍在 open_problems.md §5。

### Migration

- **No action required for existing substrates**: 所有 v1.3.0 及之前创建的 note
  自动带 `view_count=0 / last_viewed_at=None`，进入 dead 检测 pipeline 无需任何改动。
- **Instance agents**: 建议比对 `_canon.yaml::contract_version` 与
  `synced_contract_version`，drift 时跑 `myco immune` 验证 L10 / L13 / L11 仍 PASS。
- **Downstream tools**: `myco hunger --json` schema 增加 `dead_notes[]` 字段，
  消费者可安全忽略直到准备好。

---

## v1.3.0 — 2026-04-11 (minor)

**Author**: Claude (Myco kernel agent, autonomous run under user grant)
**Craft record**: `docs/primordia/craft_formalization_craft_2026-04-11.md`
（3 轮 Claim→Attack→Research→Defense→Revise，终置信度 91%，`decision_class: kernel_contract`，floor 0.90）
**Trigger**: 用户授权全权推进工作后，首项任务为"传统手艺需正式命名并以合理逻辑嵌入 Myco"。
bootstrap craft 本身豁免 `craft_protocol_version` 字段（meta-dogfood 递归防御，
symmetric with §8.7 upstream bootstrap exemption）。

### Added

**`docs/craft_protocol.md`（新，CONTRACT 级文档）**
- §1 协议定义：W3 传统手艺的正式名称锁定为 **Craft Protocol v1**（中文正式名保留"传统手艺"）。
- §2 Canonical form：文件名 pattern `^[a-z][a-z0-9]*(_[a-z0-9]+){1,}_craft_\d{4}-\d{2}-\d{2}(_[0-9a-f]{4})?\.md$`；
  frontmatter schema（type/status/created/target_confidence/current_confidence/rounds/craft_protocol_version/decision_class）；
  状态枚举 DRAFT/ACTIVE/COMPILED/SUPERSEDED/LOCAL。
- §3 调用触发器：kernel contract 变更 / 实例架构决策 / 置信度 < 0.80 / 外部 stakeholder-visible claim / 在线调研冲突。
- §4 置信度阶梯（taxonomic）：`kernel_contract: 0.90` / `instance_contract: 0.85` / `exploration: 0.75`。
- §5 与 notes/ / log.md / _canon.yaml / Upstream Protocol / L9 / L10 / L13 的集成矩阵。
- §6 Grandfather 规则：无 `craft_protocol_version` 字段的既有 craft 文件自动豁免 L13 strict 检查。
- §7 已知局限：self-reported 置信度不可验 / body 结构不 lint / bootstrap 文件豁免。
- §8 反向废弃标准：dead lint / dead mechanism / better replacement —— 防止"lint 只增不减"反模式。

**`_canon.yaml → system.craft_protocol`（新 schema block）**
- 含 dir / filename_pattern / required_frontmatter / valid_statuses / min_rounds / confidence_targets_by_class / stale_active_threshold_days / grandfather_rule。
- `upstream_channels.class_z` 新增 `docs/craft_protocol.md` —— 该文件变更需走 Upstream Protocol Review-required 通道。
- `contract_version: "v1.2.0" → "v1.3.0"`。

**L13 Craft Protocol Schema（新 lint 维度，13 → 14 维）**
- 实现于 `scripts/lint_knowledge.py::lint_craft_protocol` 与 `src/myco/lint.py::lint_craft_protocol`（双源对等）。
- `src/myco/mcp_server.py` 同步注册，docstring 与 title 从 "13-Dimension" 升级为 "14-Dimension"。
- 检查项：frontmatter 必填字段 / 文件名 pattern / type=="craft" / 有效 status / rounds ≥ min_rounds / decision_class 有效 / target_confidence ≥ class floor / current_confidence ≥ target（仅 ACTIVE/COMPILED）/ stale ACTIVE >30 天 LOW 提醒。
- Grandfather：无 `craft_protocol_version` 字段直接 skip，零 migration 成本。

**`docs/agent_protocol.md §8.3` craft_reference 字段（新）**
- class_z bundle MUST 包含 `craft_reference: <path>` 指向 ACTIVE/COMPILED 的 craft 文件，
  其 `decision_class` ≥ bundle 对应阶梯；缺失则 kernel 自动拒绝，receipt reason=`missing_craft_reference`。
- class_x/class_y bundle 可选填。

**`docs/WORKFLOW.md` W3 footer**
- 指向 `docs/craft_protocol.md` 作为 machine-verifiable specification；WORKFLOW 保留 human-readable 摘要。

**`MYCO.md` + `src/myco/templates/MYCO.md`**
- 文档索引新增 `docs/craft_protocol.md [ACTIVE] [CONTRACT]`；
- 辩论列表新增 `craft_formalization_craft_2026-04-11.md [ACTIVE] [CONTRACT]`；
- 热区 Agent 行为准则新增 "🛠️ Craft Protocol (W3)" 条款；
- "9 维 lint" / "13 维 lint" 就地升级为 "14 维 lint"。

### Changed

- `docs/agent_protocol.md §8.4`："当前 v1.2.0" → "当前 v1.3.0"。
- `src/myco/templates/_canon.yaml`：`synced_contract_version: "v1.2.0" → "v1.3.0"`；
  class_z 追加 `docs/craft_protocol.md`；新增 `craft_protocol` schema block 与 kernel canon 对齐。

### Rationale

W3 传统手艺此前只在 `docs/WORKFLOW.md` 里有 5 句话的人类摘要，没有机器可验证 schema，
也没有 lint 兜底。Phase ② 的 craft 输出数量已达 20+，但缺乏统一规范导致：
(1) 文件名不一致；(2) 置信度无 floor 概念；(3) 完成后没有正式的 COMPILED/SUPERSEDED 迁移路径；
(4) kernel contract 变更与 craft 证据之间无强制绑定。

v1.3.0 通过引入 L13 lint + `craft_protocol_version` 软迁移字段一次性闭环这四个漏洞，
**不破坏** 既有 20+ grandfathered craft 文件。属于典型的"contract-as-code"向后兼容 minor bump。

### Known non-goals

- L13 **不**检查 craft 文件的正文结构 —— round 数与 attack 质量由社会透明度（eat + log）保障，非 lint 强制。
- Self-reported `current_confidence` 的真实性由未来的 Goodhart 审计机制兜底，本版本不做。
- Bootstrap craft (`craft_formalization_craft_2026-04-11.md`) 故意省略 `craft_protocol_version` 避免递归自规制。

---

## v1.2.0 — 2026-04-11 (minor)

**Author**: Claude (Myco kernel agent)
**Craft record**: `docs/primordia/upstream_protocol_craft_2026-04-11.md`
（3 轮 Claim→Attack→Research→Defense→Revise，终置信度 85%）
**Trigger**: ASCC 试运行中捕获的摩擦 note `n_20260411T013756_ca9e`
暴露了摩擦捕获触发点的 meta-level gap —— agent 自承错误的时刻没有被兜住。

### Added

**§5.1 触发点清单（新）**
- (a) 会话两端 —— session start / session end 仍为基线。
- (b) 工具不够用时刻 —— 既有触发点，重新明文化。
- (c) 🆕 **on-self-correction**（自承错误触发点）：
  当 agent 在同一 assistant turn 内承认任何形式的"我之前说的 X 是错的"类
  表述时，**必须立即** `myco_eat` 捕获"错误内容 + 上下文 + 修正动作"三元组，
  tags 必须包含 `friction-phase2` + `on-self-correction` + 错误类型 tag。
  设计依据：ASCC 项目 agent 已自行捕获此摩擦（ca9e 笔记），属于实例向内核
  的第一条上行反馈，即 Upstream Protocol 内层回灌的 bootstrap 用例。

**§8 Upstream Protocol v1.0（新，替换旧 §8 演进，旧内容并入 §9）**
- §8.0 三层代谢同心圆定位：最内层 instance→kernel（本版本落地），
  中间层 instance↔instance Commons（v1.2 Phase ③），
  最外层 世界→substrate Metabolic Inlet（v2.0）。
  本节复用既有 7 步代谢管道（发现→评估→萃取→整合→压缩→验证→淘汰）。
- §8.1 五条核心原则（mutation/selection 对齐 / 低摩擦 ≠ 零人工 /
  path-based classification 不可被 agent 自抬 / 版本锁 + Conventional Commits /
  bootstrap 不得与被引入的规则递归）。
- §8.2 三通道处置矩阵 Class X / Y / Z（Auto / inline-Confirm / Review-required）。
- §8.3 状态机：`raw → upstream-candidate → bundle-generated →
  integrated | upstream-rejected | skip`。
- §8.4 版本锁协议：`contract_version`、Conventional Commits 自动 bump、
  revoke 广播。
- §8.5 传输层：会话内授权通道 + `.myco_upstream_outbox/` / `inbox/` 目录。
- §8.6 触发词与反射规则：含 upstream-candidate 的 auto-tagging。
- §8.7 Bootstrapping：v1.2.0 **手动** 首次 bump，避免规则被用于引入规则自身。
- §8.8 验收标准：多指标。

**L12 lint — Dotfile dir hygiene（新）**
- `scripts/lint_knowledge.py` + `src/myco/lint.py` 新增第 13 维 lint 函数
  `lint_dotfile_hygiene`，检查 `.myco_upstream_outbox/` / `.myco_upstream_inbox/`
  命名约定与 30 天 GC 警告。
- `src/myco/mcp_server.py` docstring 与维度计数从 12 → 13。

**`_canon.yaml` 新字段**
- `system.contract_version: "v1.2.0"`
- `system.upstream_scan_last_run: null`
- `system.upstream_channels.{class_x, class_y, class_z}`

**Templates**
- `src/myco/templates/_canon.yaml` 新增 `synced_contract_version` 字段
  与 `upstream_channels` 默认路径列表。
- `src/myco/templates/MYCO.md` 与 `CLAUDE.md` boot sequence 新增
  "contract_version 比对" 步骤。

### Changed

- 旧 §8 "演进" 节重编号为 §9（内容未变）。

### Bootstrap notes

本次 v1.2.0 是 Upstream Protocol 本身的**手动首次落地**，不走新规则定义的
path-based channel / 状态机。理由见 §8.7：不得让规则 bootstrap 自己
（recursion hazard）。自 v1.2.1 起所有 contract change 必须走 Upstream Protocol。
