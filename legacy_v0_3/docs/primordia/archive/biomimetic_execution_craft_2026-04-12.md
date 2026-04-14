---
type: craft
status: ARCHIVED
created: 2026-04-12
target_confidence: 0.90
current_confidence: 0.90
rounds: 3
craft_protocol_version: 1
decision_class: kernel_contract
---

# Biomimetic Execution — Wave 29 Rename Implementation (executing Wave 28 design)

> **Parent**: `docs/primordia/biomimetic_nomenclature_craft_2026-04-12.md` (Wave 28 design, 0.90 confidence)
>
> **Scope**: execute the 11 renames locked in Wave 28 §4.1 D2 across the Myco kernel, plus transition aliases, plus contract bump. NOT in scope: migration tool + examples/ascc dogfood — those split into Wave 29b because Phase A inventory revealed the combined scope exceeds single-wave capacity under marathon discipline.
>
> **Supersedes**: none. This craft re-validates Wave 28 design under implementation pressure per W28 §4.1 D5, and commits to a scope split that W28 did not anticipate.

## 0. Problem definition

Wave 28 craft §4.1 D5 explicitly mandated: *"Wave 29's own craft re-checks this design under implementation pressure and may revise."* Phase A (grep-based inventory) was run immediately before this craft and produced concrete numbers that differ materially from Wave 28's estimates.

**Wave 28 estimate** (craft §3.1): 11 renames, ~45-50 files touched, atomic bundling with migration tool and ASCC dogfood, one wave.

**Wave 29 actual Phase A inventory**:

- `_canon.yaml` alone: **609 occurrences across 100+ files**
  - Current-surface files (editable): ~45-47 files
  - Historical files (NOT editable per W28 §4.3 L7): ~53+ files (notes, log.md, contract_changelog, historical crafts, bundle.yaml files)
- `notes.py` / `notes_cmd.py` / `lint.py` module references: est. 50-80 import/mention sites (not yet gapped, but includes all src/myco/ Python files + scripts/ + tests/)
- `wiki/` directory references: est. 15-20 current-surface sites
- `system.notes_schema.*` canon key tree: est. 20-30 sites across lint.py + notes.py + canon + docs
- `myco correct` / `myco lint` CLI references: est. 40-60 sites (README examples + install scripts + pre-commit hook + agent_protocol + crafts + docs)
- Lint label strings: 3 sites (lint.py main() check list)

**Combined Wave 29 scope if all atomic**:
- ~60-80 individual file edits
- 5 file/module/directory renames (notes.py, notes_cmd.py, lint.py, wiki/, _canon.yaml)
- 2 CLI verb additions + aliases (molt, immune)
- 2 MCP tool renames
- 3 lint label string updates
- 4 canon key tree renames (nested, affects template canon too)
- 1 migration tool (`myco migrate --biomimetic`, est. 200-300 lines Python)
- 1 dogfood run against examples/ascc

**Under marathon "真正的一刻不停" mode** (no user-ack checkpoints), the migration tool + dogfood portion alone is a subsystem. Per Wave 25 Round 2 capacity constraint (1-2 subsystems max per wave, observed cadence), bundling 11 renames + migration tool + dogfood = 3 subsystems in one wave = violation.

**Wave 28 Attack L defense** argued that the three "subsystems" were actually three phases of one atomic transformation. That argument relied on the assumption that Wave 29 had enough session budget to execute all three without exhausting context. Phase A reveals that assumption was too optimistic — the rename alone is ~60-80 file edits, and the migration tool is a non-trivial new Python module with its own testing requirements.

**Revised split**: Wave 29 handles the 11 renames + transition aliases + contract bump. Wave 29b (a separate, immediately-following wave) handles the migration tool + examples/ascc dogfood. This is NOT a scope retreat — it preserves the rename atomicity (kernel stays internally consistent) while acknowledging that tool-writing is a legitimate second subsystem that deserves its own wave.

## 1. Round 1 — Phase A inventory (real numbers, grouped by current-surface vs historical)

### 1.1 Current-surface files that MUST be updated

**Core kernel source** (src/myco/):
- `cli.py` — add `molt` + `immune` verbs with transition aliases + update internal _canon.yaml refs
- `notes.py` → **rename to metabolism.py** + update internal _canon.yaml refs (26 occurrences self-contained)
- `notes_cmd.py` → **rename to metabolism_cmd.py** + internal refs (4 occurrences)
- `lint.py` → **rename to immune.py** + internal refs (22 occurrences) + label updates (L0/L7/L10)
- `mcp_server.py` — add molt + immune tool wrappers + update _canon.yaml refs (12 occurrences)
- `forage.py` — update refs (3 occurrences)
- `forage_cmd.py` — check for refs
- `upstream.py` — check for refs
- `upstream_cmd.py` — update refs (5 occurrences)
- `config_cmd.py` — update refs (6 occurrences)
- `import_cmd.py` — check for refs
- `init_cmd.py` — update refs (5 occurrences)
- `migrate.py` — update refs (8 occurrences)
- `templates.py` — check for refs

**Template canon** (src/myco/templates/):
- `_canon.yaml` → **rename to _genome.yaml** (4 self-refs + schema key renames inside)
- `MYCO.md` — prose updates (3 occurrences)
- `WORKFLOW.md` — prose updates (4 occurrences)

**Scripts**:
- `install_git_hooks.sh` — CLI verb references + canon path via inline python (2 occurrences + the inline python reads `_canon.yaml`)
- `myco_init.py` — legacy script (6 occurrences)
- `myco_migrate.py` — legacy script (8 occurrences)
- `lint_knowledge.py` — shim now points to immune.py instead of lint.py (1 occurrence)

**Root-level**:
- `_canon.yaml` → **rename to _genome.yaml** + schema key renames inside
- `MYCO.md` — prose updates (5 occurrences) + anchor #3 + §指标面板 + §任务队列 updates
- `README.md` / `README_zh.md` / `README_ja.md` — prose updates
- `pyproject.toml` — updates if references `_canon.yaml` (1 occurrence)
- `CONTRIBUTING.md` — prose updates (1 occurrence)
- `SECURITY.md` — prose updates (1 occurrence)

**Docs** (current-surface):
- `docs/agent_protocol.md` — 12 occurrences + trigger surface list in §8/reflex arc + write surface table
- `docs/craft_protocol.md` — 10 occurrences + reflex arc trigger surface list (mentions lint.py + notes.py + _canon.yaml)
- `docs/WORKFLOW.md` — 4 occurrences
- `docs/theory.md` — 3 occurrences
- `docs/architecture.md` — 9 occurrences
- `docs/reusable_system_design.md` — 12 occurrences
- `docs/biomimetic_map.md` — 4 occurrences
- `docs/evolution_engine.md` — 1 occurrence
- `docs/open_problems.md` — 2 occurrences
- `docs/adapters/gpt.yaml` — 12 occurrences
- `docs/adapters/cursor.yaml` — 9 occurrences
- `docs/adapters/mempalace.yaml` — 7 occurrences
- `docs/adapters/hermes.yaml` — 2 occurrences
- `docs/adapters/openclaw.yaml` — 1 occurrence

**Tests**:
- `tests/conftest.py` — 3 occurrences, create `_genome.yaml` instead of `_canon.yaml` in fixture
- `tests/unit/test_notes.py` → **rename to test_metabolism.py** + 3 occurrences + imports from `myco.notes` → `myco.metabolism`

**Directory READMEs**:
- `wiki/README.md` (2 occurrences) → becomes `hyphae/README.md`
- `forage/README.md` (1 occurrence)
- `notes/README.md` (1 occurrence)

**Issue templates**:
- `.github/ISSUE_TEMPLATE/adapter_submission.md` (1 occurrence)

**Examples** (treated as current-surface because examples/ serves as live verification of kernel behavior):
- `examples/ascc/README.md` (2 occurrences)
- `examples/ascc/handoff_prompt.md` (17 occurrences)
- `examples/ascc/migration_playbook.md` (5 occurrences)

**Wave 28 craft itself**:
- `docs/primordia/biomimetic_nomenclature_craft_2026-04-12.md` (18 occurrences) — mostly references the rename SOURCES by their old names as part of the design discussion. These should STAY as old names because the craft is a historical record of the design decision that preceded the rename. Only update if the reference is genuinely current-surface (e.g. cross-references to other files that have been renamed).

**Total estimated current-surface files**: ~45-47 files.

### 1.2 Historical files that MUST NOT be updated

Per W28 craft §4.3 L7 and the immutable history doctrine from W8 re-baseline:

- `log.md` — append-only historical timeline. Wave 28's log entry mentions `_canon.yaml` in its prose; that mention is historical (what W28 talked about at land-time). Leave.
- `docs/contract_changelog.md` — 72 occurrences, all in historical changelog entries. **Never rewrite.** Wave 29 adds a NEW v0.26.0 entry that uses new names; all prior entries stay.
- `notes/*.md` — all historical atomic notes. Each is immutable once written per the digestive substrate doctrine. Notes mentioning `_canon.yaml` are frozen historical artifacts.
- `docs/primordia/*_craft_*.md` pre-Wave-28 crafts — historical debate records. The Wave 28 biomimetic craft is edge case (same-day) but it's already landed; its references to old names are valid historical documentation of the pre-rename state.
- `.myco_upstream_inbox/absorbed/*.bundle.yaml` — historical friction bundles absorbed from downstream.
- The Wave 28 craft file ITSELF (`biomimetic_nomenclature_craft_2026-04-12.md`) — this is the design document. Its references to OLD names are CORRECT because they describe what was being renamed FROM. Do not rewrite the W28 craft.

**Total historical files**: ~55-60 files. These contribute ~360+ occurrences to the grep total but are zero work for Wave 29.

### 1.3 Rename surface summary table

| # | Surface | Current-surface sites | Historical sites | Wave 29 work |
|---|---|---|---|---|
| 1 | `wiki/` → `hyphae/` | 15-20 | 20-30 | directory rename + current-surface prose updates |
| 2 | `_canon.yaml` → `_genome.yaml` | 45-47 files (~150-200 occurrences) | ~55-60 files (~400+ occurrences) | file rename + current-surface updates |
| 3 | `notes.py` → `metabolism.py` | ~15 import sites | ~30 citation sites | module rename + import updates |
| 4 | `notes_cmd.py` → `metabolism_cmd.py` | ~3 import sites | ~5 citation sites | module rename + import updates |
| 5 | `lint.py` → `immune.py` | ~10 import sites + L0-L17 label strings | ~40 citation sites | module rename + label string updates |
| 6 | `myco correct` → `myco molt` | ~8 sites + CLI dispatch + MCP tool | ~12 craft references | CLI + MCP + canon + transition alias |
| 7 | `myco lint` → `myco immune` | ~15 sites + CLI dispatch + MCP tool | ~20 craft references | CLI + MCP + canon + transition alias |
| 8 | `system.notes_schema.*` → `system.metabolism_schema.*` | 3-4 files (canon + template canon + lint.py + notes.py) | — | nested canon key rename |
| 9 | `system.self_correction.*` → `system.molt.*` | 2-3 files | — | nested canon key rename |
| 10 | `system.wiki_page_types` → `system.hyphae_page_types` | 2 files (canon + template canon + lint.py ref) | — | canon key rename |
| 11 | Lint labels L0/L7/L10 | 1 file (lint.py / immune.py main() check list) | — | string literal updates |

**Total**: ~60-90 current-surface edits distributed over ~45-47 files.

## 2. Round 2 — Attack N: "Scope exceeds single-wave capacity even without migration tool"

### 2.1 The attack

Wave 25 Round 2 established observed wave capacity: 1-2 subsystems / wave, observed max 2 (Wave 23 = hook dogfood + pytest gate). Wave 29 is trying to do:

1. 11 coordinated renames across 45-47 files (~60-90 edits) — this alone is 1 major subsystem
2. Write transition alias dispatch in cli.py for 2 verbs with deprecation warnings — 0.5 subsystem (small addition)
3. Canon schema key renames with template sync — 0.5 subsystem (coupled to #1 via canon file renames)
4. Lint label string updates — 0.25 subsystem (trivial)
5. Tests update including module rename — 0.5 subsystem
6. Contract bump + changelog entry — 0.25 subsystem

Subsystem count: ~3.0. Above Wave 25 Round 2 ceiling of 2.0.

**The attack says**: even after splitting migration tool + ASCC dogfood to Wave 29b, Wave 29 itself is still 3 subsystems bundled. Either split further (29a = kernel source renames, 29b = canon + docs + tests, 29c = migration tool) or accept that marathon mode requires relaxing the capacity constraint.

### 2.2 Defense

**Defense 1 — The renames are coupled, not stackable**. The 6 items listed above are not 6 independent subsystems; they are 6 facets of ONE transformation (the rename). Splitting them across waves would leave the kernel in an inconsistent state:

- If Wave 29a does only kernel source renames without updating canon, `myco lint` on W29a's output will fail because lint.py (now immune.py) reads `_canon.yaml::system.notes_schema` which no longer exists (because it's renamed to `system.metabolism_schema` in W29b).
- If Wave 29a does canon renames without updating src/myco/, the source code still reads old canon keys and fails at runtime.
- If Wave 29a does source + canon but not docs, the docs point to non-existent files.
- If Wave 29a does source + canon + docs but not tests, pytest fails on the first run.

**The rename is atomic by physics, not by choice.** A valid intermediate state must have: renamed files + updated canon keys + updated imports + updated tests. Removing any of those leaves the kernel broken.

**Defense 2 — Subsystem counting is methodology, not dogma**. Wave 25 Round 2 capacity is a heuristic based on historical observation. It's a good default but it explicitly admits exceptions. A rename wave is genuinely different from a "add N features" wave because the unit of coupling is different: features can be independent, but a rename cannot be halfway done.

**Defense 3 — Marathon mode relaxes the capacity hurdle explicitly**. Per Wave 27-session user grant: *"真正的一刻不停 (只在 lint 红/test 红/craft 不可能时停)"*. This is a deliberate user-authorized relaxation of the capacity constraint for the duration of the biomimetic rewrite marathon. The constraint applies to normal operation; it does not apply to explicitly-authorized bulk transformations.

**Defense 4 — The scope really is split already**. Wave 29 REMOVED the migration tool + ASCC dogfood from its scope precisely because those two items ARE legitimately independent subsystems (the migration tool is a new Python module with its own behavior, testing, and interface; the dogfood is a separate verification activity). Wave 28's original bundling of those three items was the real capacity violation, and this Wave 29 craft catches it and splits. The split is already done.

**Revised position**: Wave 29 executes items 1-6 from §2.1 as ONE atomic subsystem ("the biomimetic rename transformation"). Wave 29b handles the migration tool as ONE subsystem. Wave 29c handles the dogfood (which is really just "run lint after rename, verify examples/ascc still parses").

Attack N **lands partially**: the 3-subsystem-count observation is accurate if each item is counted separately, but the items are coupled. The partial concession: Wave 29 explicitly acknowledges this is a marathon-mode exception to normal capacity discipline.

## 3. Round 3 — Execution plan + commit strategy

### 3.1 Execution phases (single commit at the end, not phase-by-phase)

**Phase A** — Preparation (done, §1.1 + §1.2)
**Phase B** — Core kernel source renames via `Edit` tool sequence:
1. Create new `src/myco/metabolism.py` with content identical to `notes.py` but self-references updated; delete old `notes.py` via git operation
2. Create new `src/myco/metabolism_cmd.py` from `notes_cmd.py` with imports updated from `from myco import notes` to `from myco import metabolism`
3. Create new `src/myco/immune.py` from `lint.py` with self-references updated
4. Delete old `notes.py`, `notes_cmd.py`, `lint.py` files (via `git rm` in the commit stage)

**Actual mechanic for file rename**: since my Edit tool edits files in place, renaming requires (a) reading old file content, (b) writing new file with new name, (c) deleting old file. Python module renames also need import updates everywhere.

For efficiency, let me structure this as:
- Step 1: Read old content (via Read tool) 
- Step 2: Write new file with new name (via Write tool) — content identical until Step 4
- Step 3: Delete old file (via bash `rm` or git rm)
- Step 4: Global find-replace of `from myco.notes` → `from myco.metabolism` across the codebase

**Phase C** — `_canon.yaml` → `_genome.yaml` rename + internal key renames
**Phase D** — Template canon mirror update
**Phase E** — cli.py: add molt + immune verbs + transition aliases + canon ref updates
**Phase F** — mcp_server.py: add molt + immune tool wrappers + canon ref updates
**Phase G** — Other src/myco/*.py updates (forage.py, upstream_cmd.py, config_cmd.py, init_cmd.py, migrate.py) for _canon.yaml → _genome.yaml + module import updates
**Phase H** — scripts/*.py and install_git_hooks.sh updates
**Phase I** — Current-surface doc updates (agent_protocol, craft_protocol, WORKFLOW, architecture, theory, reusable_system_design, biomimetic_map, open_problems, evolution_engine, adapters/*)
**Phase J** — MYCO.md + READMEs + CONTRIBUTING + SECURITY + pyproject.toml
**Phase K** — Tests: rename test_notes.py → test_metabolism.py, update conftest.py
**Phase L** — wiki/ → hyphae/ directory rename (it's empty, just mv)
**Phase M** — examples/ascc/* updates
**Phase N** — Contract bump in canon + template + new changelog entry
**Phase O** — log.md Wave 29 milestone entry
**Phase P** — Eat Wave 29 evidence + decisions notes
**Phase Q** — Verification: myco lint (now `myco immune`) 18/18 green + pytest 4/4 green
**Phase R** — Commit + push (one big commit)

### 3.2 Commit strategy

**ONE big commit** for Wave 29. Not phase-by-phase. The rationale:

- Git history should reflect "the biomimetic rename happened at this commit"
- A partial commit (e.g. just source + canon, not docs) leaves a broken intermediate state that bisect will catch as a bug
- Reviewers (future-me, future-you) want to see the full rename in one diff
- Revert capability: if the rename goes wrong, one revert undoes everything

**Commit message** format:
```
[contract:minor] Wave 29 — biomimetic rename execution (v0.25.0 → v0.26.0)
```

### 3.3 Transition aliases (per W28 D7)

In `src/myco/cli.py`, the dispatch section adds:

```python
# Wave 29 biomimetic rename — transition aliases for one wave (removed in W30).
if args.command == "correct":
    print("warning: `myco correct` was renamed to `myco molt` in Wave 29 "
          "(biomimetic rewrite). Transition alias will be removed in Wave 30.",
          file=sys.stderr)
    args.command = "molt"

if args.command == "lint":
    print("warning: `myco lint` was renamed to `myco immune` in Wave 29 "
          "(biomimetic rewrite). Transition alias will be removed in Wave 30.",
          file=sys.stderr)
    args.command = "immune"
```

### 3.4 Wave 29b preview (not in this wave's scope)

Wave 29b = migration tool `myco migrate --biomimetic` + examples/ascc dogfood
Wave 29b = exploration craft → kernel_contract implementation rhythm (so Wave 29b might itself split: W29b-craft for design, W29b-impl for execution)

Or — given that the migration tool is a relatively small Python module (maybe 150-200 lines), and the dogfood is just a verification run, Wave 29b could be a single kernel_contract wave of moderate size. Decision deferred to Wave 29b's own craft.

### 3.5 Confidence

Target: 0.90 (kernel_contract floor)
Actual: 0.90

Why not higher: Phase A was grep-based discovery only; there may be references I missed (e.g. fuzzy matches, references in .gitignore'd files, references in comments that I haven't grepped separately for each of the 11 sources yet).

Why not lower: execution plan is concrete (§3.1), commit strategy is specific (§3.2), transition aliases are designed (§3.3), single-source convention is declared (single-agent debate), and Attack N was defended with revisions.

## 4. Conclusion extraction

### 4.1 Decisions (D1-D6)

**D1** — Wave 29 executes W28 §4.1 D2's 11-item rename map. No additional renames. No retracted renames. Transition aliases per W28 D7 for `myco correct` and `myco lint` only.

**D2** — Wave 29 scope is the rename transformation alone (phases B-Q). Migration tool and examples/ascc dogfood split to Wave 29b. This is a refinement of Wave 28's original atomic-bundling claim, justified by Phase A's real inventory data.

**D3** — Historical files are NOT rewritten (per W28 §4.3 L7). The demarcation is per-file: notes/, log.md, contract_changelog.md, .myco_upstream_inbox/absorbed/, and pre-Wave-28 crafts in docs/primordia/ are historical. The Wave 28 biomimetic craft itself (`biomimetic_nomenclature_craft_2026-04-12.md`) stays with its old-name references intact as historical design documentation.

**D4** — Commit strategy: ONE atomic commit with all phases B-Q, message `[contract:minor] Wave 29 — biomimetic rename execution (v0.25.0 → v0.26.0)`.

**D5** — Contract bumps to v0.26.0 in Wave 29. Wave 29b does NOT bump (it only adds a tool + runs dogfood). Wave 30 bumps again to v0.27.0 when compress MVP lands.

**D6** — After Wave 29 commit lands, the canonical Myco names are the new biomimetic names. All subsequent waves (W30+) use new names. Transition aliases in cli.py are the only place where old names are acknowledged, and those are removed in Wave 30.

### 4.2 Landing list (Wave 29 scope, ~20 items for brevity-vs-completeness balance)

1-4. Core module renames (metabolism.py, metabolism_cmd.py, immune.py via create-new-delete-old)
5. _canon.yaml → _genome.yaml rename + internal canon key renames
6. cli.py: add molt/immune verbs + transition aliases + _genome refs
7. mcp_server.py: add molt/immune MCP tools + _genome refs
8. src/myco/*.py (forage, upstream_cmd, config_cmd, init_cmd, migrate, import_cmd): _genome refs + module rename imports
9. src/myco/templates/_canon.yaml → _genome.yaml + mirror renames
10. src/myco/templates/MYCO.md + WORKFLOW.md: prose updates
11. scripts/*.py + install_git_hooks.sh: refs + lint_knowledge.py shim
12. Current-surface docs: agent_protocol, craft_protocol, architecture, WORKFLOW, theory, reusable_system_design, biomimetic_map, open_problems, evolution_engine, adapters/*
13. MYCO.md prose updates + anchor hygiene
14. README.md + README_zh.md + README_ja.md
15. pyproject.toml + CONTRIBUTING + SECURITY + .github/ISSUE_TEMPLATE/*
16. tests/conftest.py + rename test_notes.py → test_metabolism.py
17. wiki/ → hyphae/ rename + hyphae/README.md update
18. examples/ascc/* prose updates
19. Contract bump v0.25.0 → v0.26.0 + docs/contract_changelog.md new entry
20. log.md Wave 29 milestone + eat W29 evidence + decisions + `myco immune` green + `pytest` green + commit + push

### 4.3 Known limitations

**L1** — Phase A is grep-based. Edge cases (references in rarely-grepped files, references split across lines, references in comments, references using interpolation like `{project_root}/_canon.yaml`) may be missed. Wave 29 execution is expected to run `myco immune` (formerly lint) after each phase as a tripwire; any missed references will surface as import errors or lint failures.

**L2** — Single-agent craft ceiling applies (per craft_protocol §4). No cross-agent review of the rename map before execution.

**L3** — The Wave 28 biomimetic craft file (`biomimetic_nomenclature_craft_2026-04-12.md`) stays with old names in its body. This is intentional (historical design doc) but may cause confusion for readers who read the Wave 28 craft AFTER Wave 29 lands and wonder why the doc talks about `_canon.yaml` when they see `_genome.yaml` on disk. Mitigation: the Wave 29 commit message + contract_changelog v0.26.0 entry explicitly point at the Wave 28 craft as "the pre-rename design document that uses old names by construction".

**L4** — Migration tool deferred. Downstream instances (examples/ascc or any hypothetical external instance running v0.25.0) will not have an automated path to v0.26.0 until Wave 29b lands. Wave 29 ships the kernel-side rename; Wave 29b ships the instance-side migration. In between, instances are stuck on v0.25.0 unless they manually re-init from the new kernel templates.

**L5** — examples/ascc has 24+ occurrences of `_canon.yaml` across 3 files. These WILL be rewritten in Wave 29 (examples/ascc is current-surface, not historical). If examples/ascc represents a preserved project state, the rewrite may break its internal consistency. Mitigation: run `myco immune --project-dir examples/ascc` after Wave 29 commit to verify. If ASCC fails lint post-rename, Wave 29 rolls back and re-scopes.

**L6** — Wave 29 is the biggest single wave ever (observed wave cadence was 1-2 subsystems, Wave 29 is effectively 1 coupled subsystem of ~60-90 edits, which is larger than Wave 24 at 1 subsystem of ~10 edits). If mid-execution context pressure forces a stop, the wave may need to split emergency-fashion into W29a (kernel source + canon) and W29b (docs + tests + examples + contract bump), which is NOT what this craft proposes. Emergency split would be a marathon-rule violation ("only stop on lint red / test red / craft impossible"); Wave 29 should only trigger emergency split if one of those three conditions actually fires.

### 4.4 Provenance + next step

- **Craft authored**: 2026-04-12, immediately after Wave 28 commit, same session
- **Trigger**: Wave 28 craft §4.1 D5 mandated Wave 29's own craft re-checks
- **Decision class**: kernel_contract (0.90 target, 0.90 actual)
- **Rounds executed**: 3
- **Phase A inventory**: completed via grep; 609 `_canon.yaml` occurrences across 100+ files revealed, current-surface filtered to ~45-47 files
- **L13 schema**: compliant
- **L15 reflex arc**: satisfied (craft materializes in same session as the touches)
- **Next step**: execute §4.2 landing list items 1-20 in marathon mode without user check-ins. Verification gates: `myco immune` 18/18 PASS + `pytest tests/ -q` 4/4 PASS before commit. One atomic commit at the end. Push to origin/main. Proceed immediately to Wave 29b (migration tool) OR Wave 30 (compress MVP) depending on remaining session capacity.
