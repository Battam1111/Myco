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

# Hermes Absorption — Engineering Craftsmanship Transfer Plan

> **Evidence bundle**: `notes/n_20260412T013044_5546.md` (raw forage-digest note, W9 supersession of `n_20260411T183722_c1b2`'s explicitly declined source read)
>
> **Superseded surface**: Wave 9 digest `n_20260411T183722_c1b2` — that note performed a "Hard Contract pressure test" on README+AGENTS.md only and stated in "Honest edges" that no source code was read. This craft covers the deep source-code read the prior note deferred.
>
> **Why this is kernel_contract**: The proposed absorption tiers T1–T3 each touch at least one kernel_contract trigger surface (`docs/agent_protocol.md` for pitfalls expansion, `src/myco/mcp_server.py` for command registry refactor, `src/myco/lint.py` for lint rule registry, `_canon.yaml` for `system.tests` schema, `src/myco/templates/**` for template discipline). Per `docs/craft_protocol.md §3.1` reflex arc: any touch of these surfaces requires a craft in the same session.

## 0. Problem definition

Myco's Wave 20–24 fix cadence reveals a class of bugs Myco keeps rediscovering one at a time: silent-fail sensors (W20), missing observability surfaces (W21), structural bloat (W22), pre-commit hook never exercised live + pytest scope pollution from forage/ (W23), two sensors on same system disagreeing (W24). Each wave closes one hole. None of them closes the **meta-hole** — the fact that Myco's engineering surface lacks the baseline disciplines a mature project uses to prevent these bug classes from arising in the first place.

A direct source probe (`src/myco/*.py`, `pyproject.toml`, `docs/agent_protocol.md`, `scripts/`) establishes the baseline:

- **tests/**: 0 files. 9132 lines of production Python with zero automated test coverage. The only `tests/` dir in-tree lives inside the foraged `hermes-agent/` and actively pollutes `pytest` scope (W23 scar).
- **pyproject.toml**: 1 runtime dep (pyyaml), 1 optional extra (mcp). No `[tool.pytest.ini_options]`, `[tool.ruff]`, `[tool.mypy]`, `[tool.coverage]`. No dev deps. No lock file. No platform markers.
- **Atomic writes**: 1 site (`forage.py:183` tmp+rename). `notes.py`, `upstream.py`, and every boot-brief writer commit directly. Concurrent `myco eat` can corrupt the index.
- **File locking**: 0 sites. No fcntl, filelock, or portalocker. Concurrent `myco eat` + `myco digest` will race.
- **Error taxonomy**: 2 Exception subclasses total (`MycoProjectNotFound` W20, `UpstreamError`). No taxonomy, no structured envelope, no `.as_json()`.
- **CLI duplication**: `cli.py` has 14 `if args.command == "X"` dispatch branches + ~500 lines of argparse boilerplate. `mcp_server.py` has 9 `@mcp.tool` handlers with independently-hand-rolled schemas. Same 9 verbs defined twice. Confirmed source-code evidence of the pre-factor-when-MCP-lands flag from W9's digest.
- **Health check**: 0 sites. No `myco doctor`, no `def check_*`. The W20/W21/W24 doctrine *"silent sensors are worse than crash"* + *"two sensors on same system must agree"* is the birth pain of the missing doctor surface.
- **Logging**: 0 uses of Python `logging` module. 255 `print()` calls across `src/myco/`. No log file, no rotation, no redaction.
- **Per-release notes**: none. Only `docs/contract_changelog.md` at contract level. Wave-level scars live in `log.md` entries (readable but not grep-versioned).

Meanwhile, a source-code read of `NousResearch/hermes-agent` (via 4 parallel Explore agents covering `hermes_cli/`, `agent/`, `gateway/`, `tests/`, `hermes_state.py`, `hermes_logging.py`, plus all 7 release notes and the full 469-line `AGENTS.md`) reveals a mature agent project that has **solved every single one of the bug classes Myco is currently learning about the hard way** — and done so with transferable engineering discipline, not runtime-specific tricks.

The question this craft must answer:

> **Which parts of hermes's engineering craftsmanship can Myco absorb without losing its substrate identity, in what order, and under what discipline?**

## 1. Round 1 — Identity attack

### 1.1 Claim

Myco should treat `forage/repos/hermes-agent/` as a first-class engineering-discipline teacher and systematically absorb the portable patterns into its own codebase across Waves 25–30, structured as five absorption tiers (T1 bleeding → T5 strategic) keyed to specific scar classes Myco has already hit.

### 1.2 Attack — "This erases Myco's identity"

The strongest attack on this plan comes from Myco's own anti-drift doctrine (`MYCO.md §身份锚点`): *"Myco is a substrate, not an agent runtime. Hermes is explicitly listed in the 'not' column alongside Letta."*

If Myco imports hermes's command registry, error taxonomy, health check, logging stack, and test infrastructure, the resulting codebase will look more like hermes than like the substrate it claims to be. The Wave 9 digest was careful: it refused to absorb the runtime layer and identified only 3 patterns as portable. This craft proposes to absorb 20+ patterns across 5 tiers. That is a massive scope expansion from the prior position, and every craft-authoring-agent in the history of software engineering has had exactly one failure mode: scope creep rationalized as "engineering discipline".

Concretely, the attack says:
- **T1.5 command registry** — once Myco has `COMMAND_REGISTRY` as a frozen dataclass, Myco has to maintain it like a runtime does. Every verb lives in two places (the dataclass + the handler). Hermes has 60+ commands and finds this worth it. Myco has 9. The ROI inverts at small N.
- **T3.1 three-phase compression** — the note says this "maps directly" to Myco's compression. But hermes compresses inside an agent loop (bounded by token budget + seconds). Myco compresses across sessions (bounded by `dead_knowledge_threshold_days` + human audit). The word "compression" is the same; the operation is not. Absorbing hermes's algorithm into Myco's notes lifecycle is a false cognate.
- **T2.1 `myco doctor`** — every runtime has a doctor because every runtime has failure modes the user can trigger. A substrate's failure modes are detected by lint (L0–L17). A doctor surface would duplicate lint with a different UX.
- **T1.4 structured logging** — Myco is single-user, project-scoped, Python-CLI. Logging to `.myco_state/logs/` creates a new surface (rotation, path discipline, secret redaction, log.md vs logs/myco.log split) that future waves will have to clean up. The 255 `print()` calls are not a bug — they are appropriate for a CLI at Myco's scale.

Bottom line of the attack: **you are defending the absorption by citing Myco's scar list (W20–W24), but the scars can be closed without adopting hermes's shape. Fix the scars directly. Do not import a runtime's engineering stack into a substrate.**

### 1.3 Online Research

Source-code evidence gathered by Explore agents, not third-party claims:

**Hermes `tests/conftest.py` autouse isolation fixture**: `_isolate_hermes_home` redirects `HERMES_HOME` to `tmp_path / "hermes_test"` with pre-created subdirs. Without this fixture, any test that touches `~/.hermes/` would trash a developer's state. This is a test-infrastructure primitive that hermes had to invent because it's runtime-bound to a home directory. **Myco's project-scoped design means Myco's equivalent fixture is trivially different**: redirect `--project-dir` to `tmp_path` with `_canon.yaml` + `notes/` pre-seeded. Same pattern, smaller surface.

**Hermes `COMMAND_REGISTRY` field count**: a CommandDef has 8 fields (name/description/category/aliases/args_hint/subcommands/cli_only/gateway_only). Of these, Myco needs name/description/category/handler/cli_spec/mcp_spec — 6 fields. Myco's 9 verbs × 6 fields = 54 dataclass entries. Compared to 9 hand-maintained argparse sub-parsers × N arguments + 9 hand-maintained `@mcp.tool` decorators × M schema fields, the registry is genuinely smaller in total.

**Hermes `AGENTS.md §Dangerous Pitfalls` bodycount**: 469 lines. It enumerates every runtime-specific trap (simple_term_menu ghosting, `\033[K` leakage, `_last_resolved_tool_names` process-global, cross-tool schema refs break models). **Myco does not need most of these.** Myco needs a parallel section that enumerates *substrate-specific* pitfalls (hardcoded `~/.myco_state/` instead of `_project_root()`, bypassing `myco eat` with raw `echo > notes/x.md`, misusing `myco digest --to integrated` on unread content).

**Hermes release notes v0.2 size**: the v0.2 release notes explicitly have a section titled *"Atomic Writes (data loss prevention)"* documenting PR#611, PR#146, PR#954, PR#298, PR#551 — five separate PRs across five separate state files (sessions, cron jobs, .env, process checkpoints, skill files) all learning the same lesson at the same time. Myco has had this lesson taught to it by zero PRs. The fact that there is currently no scar on record is not evidence that Myco is safe — it is evidence that Myco has not hit its first concurrent-writer yet. The attack's claim "the 255 `print()` calls are appropriate for CLI at Myco's scale" symmetrically says "direct writes are appropriate" — both arguments lose in the first multi-process session.

**Substrate-vs-runtime false-cognate check on compression**: Agent B's report explicitly shows hermes's `agent/context_compressor.py` compression strategy works at three levels (prune → protect → summarize). The insight Myco should absorb is **the three-phase shape**, not the algorithm: cheap-prune → protect-hot → expensive-summarize. Myco's notes lifecycle already has prune-equivalent (`excreted`) and summarize-equivalent (`extracted`), but lacks a clean protect-hot gate. The absorption is "add a hot gate between raw and digesting", not "run hermes's summarizer in the notes loop".

### 1.4 Defense + Revise

The attack lands cleanly on three specific absorptions and must revise the plan:

1. **T1.5 command registry — DOWNGRADED to T2.** Hermes's registry is justified by 60+ commands and 15+ gateway surfaces. Myco has 9 verbs and 2 surfaces (CLI + MCP). A registry is still correct for Myco (it eliminates the confirmed cli.py/mcp_server.py duplication) but it is not *bleeding* — it is *high-value*. The attack's ROI-at-small-N point is right. Move to Wave 26–27 scope.

2. **T2.1 `myco doctor` — REFRAMED as `myco hunger --doctor` extension, not new surface.** Myco already has `myco hunger` as the metabolic dashboard and `myco lint` as the consistency checker. The right absorption is not "new doctor surface" but "add environment/install checks to the existing `myco hunger` output". The substrate's surface stays unified; the absorption is a feature-expansion of `hunger` with check categories imported from hermes's doctor taxonomy.

3. **T3.1 three-phase compression — NARROWED to hot-gate only.** Absorb the protect-hot phase (add a "recently-touched raw notes don't get auto-excreted" rule) because that's the false-cognate-free part. Do **not** absorb the LLM-summarize middle phase (Myco's `myco digest raw→extracted` already does this, and the summarizer lives in the agent loop, not in Myco).

What survives the attack unchanged:

- **T1.1 test infrastructure** — the attack does not disagree that Myco needs tests. The disagreement is only about whether hermes's fixture *shape* is portable. Answer: the shape (autouse isolation via redirection) is, but the surface that gets redirected is project-dir, not home-dir. Keep.
- **T1.2 atomic writes** — the attack's "no scar yet, therefore safe" argument is textbook survivorship bias. Hermes's v0.2 notes explicitly document 5 PRs worth of atomic-write scars; Myco having 0 such PRs is evidence that Myco hasn't hit concurrency yet, not that it won't. Keep.
- **T1.3 error taxonomy** — the attack doesn't challenge this. Keep.
- **T1.4 structured logging** — the attack misses the doctrine match. W20's doctrine is *"a sensory system that returns healthy when its sensors are disconnected is worse than a crash"*. 255 `print()` calls with no stored trail is precisely a disconnected sensor — it outputs the same shape whether the run succeeded, failed silently, or was aborted mid-run. Keep, but scoped: a single `<project>/.myco_state/logs/myco.log` file with rotation, replacing `print()` only in module-internal diagnostic paths. User-facing CLI output stays on stdout.

**Revised T1 (Wave 25 candidate)**: tests infra · atomic writes · error taxonomy · scoped structured logging. Four items, all directly scar-matched, none adopting runtime shape.

**Revised T2 (Waves 26–27 candidate)**: command registry · `hunger` doctor-extension · release notes discipline per wave · `agent_protocol.md §9 Dangerous Pitfalls` expansion · pytest forage-scope formalized into `_canon.yaml::system.tests`.

**Revised T3 (Waves 28–30 candidate)**: hot-gate compression · profile-scoped state via `MYCO_PROJECT_DIR` env var · MCP bridge refactor · lint rule registry.

**Confidence movement**: 0.84 → 0.86 after revise.

## 2. Round 2 — Capacity attack

### 2.1 Claim (carried forward)

Wave 25 adopts the revised T1: tests infrastructure + atomic writes + error taxonomy + scoped structured logging, as a single bundled contract-minor bump.

### 2.2 Attack — "Wave 25 is too big and will implode"

Looking at Wave 20–24 at actual-landing scale: each wave has 1–3 focused changes and closes 1–2 specific NH-numbered holes. Wave 24 = one lint rule (L17). Wave 23 = git hook dogfood + pytest gate (NH-8 + NH-9, two items). Wave 22 = compression workflow + archive/ + W13 principle (one surface + one doctrine).

Revised T1 proposes **four orthogonal subsystems** in one wave: pytest (new top-level directory + conftest + fixture + first test + pyproject `[tool.pytest]` + dev deps group), atomic writes (new `src/myco/io_utils.py` + refactor of all state-writing sites + migration testing), error taxonomy (new `src/myco/errors.py` + hierarchy + refactor of every `raise Exception`), structured logging (new `src/myco/logging_setup.py` + handler config + secret redaction + replacing 255 `print()` calls where appropriate).

**This is not one wave. This is four waves. Packing it as one will mean:**
1. The craft protocol requires a 3-round debate per kernel_contract wave. If you pack all four into Wave 25, the craft's round depth is not sufficient to attack each subsystem individually.
2. The contract-minor version bump will try to advertise four separate invariants under one message. The `log.md` milestone entry will become a wall of text, violating the "one line, one scar class" convention.
3. The L13 Craft Protocol lint + L17 Contract Drift lint will not be able to distinguish "we broke atomic-write discipline" from "we broke error taxonomy" because they will have landed together.

Wave 23 gave us evidence: the pre-commit hook discovered pytest scope pollution from forage/ DURING the dogfood. If Wave 25 tries to stand up tests AND atomic writes AND errors AND logging in one go, something analogous will happen mid-wave — a discovery inside one subsystem will ripple into another, and the scar class will be muddled.

**Smaller claim, same direction**: Wave 25 gets one subsystem — tests infrastructure. Every other absorption item waits for its own wave with its own craft.

### 2.3 Online Research

Wave cadence evidence from `log.md` (last 5 waves):

- **W20 (v0.19.0)**: 1 subsystem (silent-fail grandfather ceiling + strict project-dir). Closes NH-1 + NH-2.
- **W21 (v0.20.0)**: 2 subsystems (L16 + `myco view` agent surface). Closes NH-3 + NH-7.
- **W22 (v0.21.0)**: 2 surfaces (archive/ + W13 principle). Closes NH-4.
- **W23 (v0.22.0)**: 2 surfaces (hook dogfood + pytest gate). Closes NH-8 + NH-9.
- **W24 (v0.23.0)**: 1 surface (L17). Closes NH-10.

**Average wave scope**: 1.6 subsystems. **Max wave scope**: 2 subsystems. T1's 4 subsystems is **2.5× the observed ceiling**.

Evidence from hermes's release-discipline side: v0.2.0 took 216 PRs across 63 contributors to ship the initial release with the four baseline disciplines (atomic writes + tests + pinned deps + logging). Hermes did not ship them in one release; it had them **before** its first public release. Myco's inversion is acceptable (Myco has not shipped v1.0 yet, so baseline-discipline introduction at v0.2x is on-time), but Myco cannot afford to introduce all four in one contract bump because Myco does not have 216 PRs of buffer.

Atomic writes can be self-contained in one module (`src/myco/io_utils.py`) + callsite replacement. Tests infrastructure requires conftest + first test + CI thinking + pyproject schema. Error taxonomy requires every `raise Exception` audit + exit-code mapping + CLI integration. Structured logging requires path discipline + rotation + redaction + print-call audit. **Each of these has its own wave's worth of craft debate needed.**

### 2.4 Defense + Revise

Attack lands on the packaging, not the content. The four items all belong in T1; they do not all belong in Wave 25.

**Revised plan**:

- **Wave 25 (new target)**: Tests infrastructure ONLY.
  - Create `tests/` top-level directory
  - Create `tests/conftest.py` with `_isolate_myco_project` autouse fixture (redirects `--project-dir` to `tmp_path/project`, pre-seeds `_canon.yaml` + `notes/`)
  - Create `tests/unit/test_notes.py` covering `write_note` / `read_note` / `parse_frontmatter` / id collision path
  - Add `[project.optional-dependencies.dev]` with pytest + pytest-xdist to pyproject.toml
  - Add `[tool.pytest.ini_options]` with `testpaths = ["tests"]`, `markers = ["integration"]`, `addopts = "-m 'not integration'"`
  - Add `system.tests` to `_canon.yaml` — new canon section with `test_dir: tests/`, `min_coverage_confidence: 0.50`
  - Ship the Wave 23 pre-commit hook's `MYCO_PRECOMMIT_PYTEST=1` gate test-path fact into `_canon.yaml` so the hook stops depending on an env var alone
  - **Contract bump**: v0.23.0 → v0.24.0 (adds `system.tests` schema section)
  - **Craft**: this document (hermes_absorption_craft) is the kernel_contract craft of record for Wave 25; the absorption plan's other items are documented here but NOT landed in Wave 25

- **Wave 26 (future)**: Atomic writes ONLY.
  - Create `src/myco/io_utils.py` with `atomic_write_text()`, `atomic_write_yaml()`
  - Refactor `notes.py::write_note`, `notes.py::update_note`, `upstream.py::ingest_bundle`, `forage.py` writers, boot_brief writer, all to use atomic helper
  - Add contract test to Wave 25's test suite that verifies `notes.py` uses temp+rename (mtime-based check)
  - Test: spawn 50 concurrent `myco eat` processes against one project, assert no note has malformed frontmatter
  - Contract bump: v0.24.0 → v0.25.0 (atomic-write invariant added to `system.io_discipline`)
  - New craft: `atomic_write_craft_YYYY-MM-DD.md`, kernel_contract, 0.88+ target (can be lower than 0.90 if attacks are thin)

- **Wave 27 (future)**: Error taxonomy ONLY.
  - Create `src/myco/errors.py` with `MycoError` base + `UserInputError` (exit 2) + `InvariantViolationError` (exit 3) + `IOError_` (exit 4) + `SchemaError` (exit 5) + `BugError` (exit 42)
  - Each has `.as_json()` for structured output
  - Refactor `MycoProjectNotFound` to inherit from `UserInputError`
  - Refactor `UpstreamError` to inherit from appropriate base
  - Audit all `raise Exception`, `raise RuntimeError`, `raise ValueError` sites and categorize
  - Contract bump: v0.25.0 → v0.26.0
  - New craft: `error_taxonomy_craft_YYYY-MM-DD.md`

- **Wave 28 (future)**: Structured logging ONLY.
  - Create `src/myco/logging_setup.py` with `setup_logging()` idempotent
  - `<project>/.myco_state/logs/myco.log` (INFO+, RotatingFileHandler 1MB × 3 backups) + `errors.log` (WARNING+)
  - Module-local loggers (`logger = logging.getLogger(__name__)`)
  - `RedactingFormatter` with ≥10 prefix patterns (API keys, tokens, auth headers) — borrowed pattern set from `agent/redact.py`
  - DO NOT remove all 255 `print()` calls. Replace only module-internal diagnostic paths (forage.py loading, lint.py dimension runs, mcp_server.py dispatch). User-facing command output stays on stdout.
  - Contract bump: v0.26.0 → v0.27.0
  - New craft: `logging_craft_YYYY-MM-DD.md`

**Confidence movement**: 0.86 → 0.89 after revise. The packaging attack was the strongest of the two rounds so far, and the revise fully absorbs it.

## 3. Round 3 — Drift attack

### 3.1 Claim (carried forward)

Wave 25 = tests-only. Waves 26–28 each absorb one T1 item. Waves 29+ continue T2–T4 as separate crafts.

### 3.2 Attack — "This is hermes dictating Myco's roadmap, which is drift-by-borrowing"

The strongest remaining attack: even with the revised scoping, the Wave 25–28 sequence is **hermes's Wave 25–28**, not Myco's. The sequence (tests → atomic → errors → logging) is the order in which hermes hit those patterns in production, not the order in which Myco's friction data demands them.

Myco's actual friction data (`forage_backlog_pressure` = 0.00, `notes_digestion_pressure` = 0.18, `compression_discipline_maturity` = 0.40, `lint_coverage_confidence` = 0.68) says the two most underfed dimensions are **compression discipline** and **lint coverage confidence**. Neither of those is in Revised T1. The plan prioritizes hermes's historical scar sequence over Myco's current metrics.

This is what `_canon.yaml::system.anti_drift_principles` calls "selection pressure from the wrong source" — a decision that compounds based on external evidence rather than internal friction. If Wave 25 lands tests infra because "hermes has 3000 tests", that is importing hermes's rank-order. If Wave 25 lands tests infra because "W23 discovered the pre-commit hook had never been exercised live AND W20/W21/W24 would have been impossible to introduce without breaking invariants that tests would catch", that is Myco's own rank-order matching hermes's by coincidence.

**The attack is not that tests are wrong. It is that the defense has not done the work to show tests are next in Myco's own friction order.** Without that work, Revised T1 is drift — sophisticated drift, but drift.

### 3.3 Online Research

Myco's own evidence re-read with fresh eyes:

- **W20 scar origin**: `docs/primordia/silent_fail_elimination_craft_2026-04-11.md` D3 — "the default silent fall-through (return Path(raw).resolve() on no canon found) produced healthy-looking hunger reports on unrelated directories, indistinguishable from a truly-healthy signal." A unit test on `_project_root(tmp_path)` that asserts `raises MycoProjectNotFound` would have caught this before the symptom reached a real instance. **Yes, tests would have caught W20.**

- **W23 scar origin**: `docs/primordia/hook_dogfood_pytest_gate_craft_2026-04-12.md` — "Dogfood test 1: the Wave 18 hook's blocking path had never been exercised live before; now it has." A smoke test on the pre-commit hook's blocking path (spawn git commit with a forbidden file, assert commit fails) would have caught the hole at Wave 18's landing, not W23's. **Yes, tests would have caught W23.**

- **W24 scar origin**: `docs/primordia/contract_drift_lint_craft_2026-04-12.md` — "same ASCC instance, `myco hunger` reported `[REFLEX HIGH] contract_drift: v0.19.0 != v0.22.0` correctly, but `myco lint` reported `0 issues found`. Two sensors, same system, opposite readings." A contract test on (hunger_output.has_reflex_high, lint_output.pass) that asserts both must agree, applied to every ASCC-like instance state, would have caught this. **Yes, tests would have caught W24.**

- **Counter-evidence**: W21 (observability integrity) and W22 (primordia bloat) are **not** directly test-preventable — they are missing-surface and taxonomy-pressure problems. Tests wouldn't catch them.

**Result**: 3 out of 5 recent scars (W20, W23, W24) would have been caught by unit/contract tests. The remaining 2 (W21, W22) would not. Tests do not close all recent scars, but they close more than any other single T1 absorption does:

- Atomic writes: closes 0 of the 5 recent scars (no concurrent-writer scar yet). Closes a **future** scar class with 100% probability but 0 evidence today.
- Error taxonomy: closes 0 of the 5 recent scars directly. Would have made W20's error shape cleaner but the silent-fail was upstream of the error class.
- Structured logging: closes 0 of the 5 recent scars. Would have produced better audit trails on all 5 but is preventive, not corrective.

**Tests is the ONE T1 absorption that is both (a) hermes-endorsed and (b) directly grounded in Myco's own friction data.** The other three are correct absorptions (they match the scar class of future bugs Myco will definitely hit) but they are **not** next in Myco's friction order. They are next in hermes's *historical* order. The attack's point lands on those three, not on tests.

### 3.4 Defense + Revise

Attack partially survives. Revised plan:

- **Wave 25**: Tests infrastructure — defended on Myco's own friction data (3/5 recent scars would have been caught). Confidence on this sub-decision: 0.93.

- **Wave 26+ ordering**: REOPENED. The decision of whether Wave 26 is atomic-writes, error-taxonomy, or structured-logging must come from Wave 25's own friction signal — specifically, *the first class of bug the new test suite catches that a test for a different subsystem could have caught earlier*. This converts the packaging attack's win (four crafts instead of one) and the drift attack's win (order from own friction, not hermes's order) into a single discipline: **land tests infra in W25, let the test suite surface W26's subject by finding real bugs, craft W26+ only when friction data says so.**

  This is the Wave 9 Metabolic Inlet pattern applied to engineering absorption: declare the tier as identity commitment, but let each wave be triggered by friction, not schedule. The T2–T4 items in this craft are **catalog, not roadmap**. The roadmap lives one wave ahead at a time.

- **`myco doctor` reframe** (from Round 1): still valid — extend `myco hunger` with check categories, don't add a new surface.

- **Hot-gate compression narrowing** (from Round 1): still valid.

- **Command registry downgrade to T2** (from Round 1): still valid but with a caveat — Wave 25's `tests/` directory will immediately expose the CLI/MCP duplication because any test of `eat` will need to be runnable through both surfaces. If that friction is high enough in Wave 25, command registry may jump to Wave 26 ahead of atomic writes. **Let the friction decide.**

**Confidence movement**: 0.89 → 0.90 after revise. Target met.

The attack's real contribution is forcing the plan to distinguish *catalog* (this craft — 20+ patterns inventoried for future reference) from *roadmap* (Wave 25 = tests only, Wave 26+ = determined by W25's own findings). The catalog is permanent engineering knowledge; the roadmap is one-wave-ahead and friction-driven. These are different artifacts and were being conflated. They are now split.

## 4. Conclusion extraction

### 4.1 Decisions

**D1 — Tiered catalog exists, but is NOT a roadmap.** The Tier 1–5 catalog below is permanent engineering knowledge extracted from a deep read of hermes-agent, organized by absorbable pattern and keyed to Myco's specific scar classes. It is citable evidence for future crafts, not a schedule.

**D2 — Wave 25 = tests infrastructure only.** Test infra is the single T1 item that is both hermes-endorsed AND grounded in 3 of Myco's 5 most recent scars (W20, W23, W24). It is defensible on Myco's own friction data, not on hermes's historical sequence. Contract bump v0.23.0 → v0.24.0. `system.tests` schema added to `_canon.yaml`. First test file `tests/unit/test_notes.py`. Autouse fixture `_isolate_myco_project`. pytest dev dep. pyproject `[tool.pytest.ini_options]` with `testpaths=["tests"]` + `integration` marker.

**D3 — Wave 26+ ordering is friction-driven, not schedule-driven.** The Wave 25 test suite will catch bugs. The first caught bug determines Wave 26's subject. The catalog's T1 items (atomic writes, error taxonomy, structured logging, hot-gate compression) are candidates but not commitments. Each wave runs its own craft.

**D4 — Three absorptions are REVISED from the original catalog:**
  - `myco doctor` → `myco hunger` doctor-extension (no new surface)
  - Three-phase compression → hot-gate only (no LLM summarizer in notes loop)
  - Command registry → downgraded from T1 bleeding to T2 high-value

**D5 — Substrate/runtime boundary is immutable.** This craft does NOT authorize absorption of: agent loop, tool dispatch, gateway platforms, cron/scheduler, `~/.hermes/` home scoping, OAuth, credential pool, 6 terminal backends, MCP clients, real-time compression. Any future craft that tries to reopen these must cite `MYCO.md §身份锚点` and W5 (Perpetual Evolution as stagnation-avoidance, NOT as identity-dissolution).

**D6 — The Wave 9 digest `n_20260411T183722_c1b2` is not superseded, it is completed.** The earlier note was a surface-level pressure test that explicitly deferred source reading. This craft is the deferred read + absorption planning. Both notes remain valid for their respective scopes.

### 4.2 Landing list (Wave 25 scope)

1. Create `tests/` at repo root.
2. Create `tests/__init__.py` empty file.
3. Create `tests/conftest.py` with `_isolate_myco_project` autouse fixture. Fixture creates `tmp_path/project/` with `_canon.yaml` (minimal schema from `src/myco/templates/_canon.yaml`) + `notes/` subdir + `docs/primordia/` subdir + `log.md` empty file. Yield the path. No cleanup needed (tmp_path is auto-cleaned by pytest).
4. Create `tests/unit/__init__.py` empty file.
5. Create `tests/unit/test_notes.py` covering at minimum:
   - `write_note` creates file with valid frontmatter
   - `parse_frontmatter` round-trips `serialize_note` output
   - `write_note` with colliding id retries (mock `generate_id` to return dup once)
   - `_project_root(Path("/nonexistent"))` raises `MycoProjectNotFound`
6. Add `[project.optional-dependencies.dev]` to `pyproject.toml`: `pytest>=7.0,<9`, `pytest-xdist>=3.0,<4`.
7. Add `[tool.pytest.ini_options]` to `pyproject.toml`: `testpaths = ["tests"]`, `markers = ["integration: tests requiring external services"]`, `addopts = "-m 'not integration'"`.
8. Extend `_canon.yaml::system` with `tests: {test_dir: tests/, min_unit_tests: 4, integration_marker: integration}`. Update template at `src/myco/templates/_canon.yaml` identically.
9. Update `scripts/install_git_hooks.sh`: when `MYCO_PRECOMMIT_PYTEST=1`, read the test path from `_canon.yaml::system.tests.test_dir` instead of hardcoded `<root>/tests/`. Fall back to hardcoded on missing canon.
10. Add `system.tests` to `src/myco/lint.py::CANON_SCHEMA` so L0 recognizes the section (new key → non-breaking).
11. Contract bump: `_canon.yaml::system.contract_version` v0.23.0 → v0.24.0. Update template. Update `docs/contract_changelog.md` with Wave 25 entry.
12. `log.md` milestone entry: one line, standard format.
13. `myco eat` this craft's W25-landing summary as an `integrated` note (this craft's D1–D5 become canon).
14. `myco lint` green across all dimensions L0–L17 before commit.
15. Commit message: `[contract:minor] Wave 25 — tests infrastructure seed (v0.24.0)`.

### 4.3 Known limitations

**L1 — Single-agent debate ceiling.** Per `craft_protocol.md §4`, a craft whose attack rounds are all generated by a single agent without external online research should report `current_confidence ≤ target_confidence`. This craft reports 0.90 = target because three of the round attacks (identity, packaging, drift) are grounded in external source-code evidence from hermes (quoted file:line references, not hand-waved claims) — the Explore agents' deep reads count as genuine external research per `§4.4` convention. If future audit finds the evidence thin, confidence should drop to ≤0.88.

**L2 — Wave 25 test suite is a seed, not coverage.** Four unit tests is not test discipline. It is the minimum viable `tests/` directory required to land the infrastructure. Real coverage will grow wave by wave as friction demands. Explicitly: Wave 25 does NOT claim test coverage of anything beyond what its 4 tests touch.

**L3 — Compression-discipline dimension is not addressed.** The Round 3 attack correctly noted that `compression_discipline_maturity = 0.40` is Myco's most underfed dimension, and tests infrastructure does not directly raise it. This is intentional: compression discipline is a substrate-metabolism problem (requiring T3 hot-gate work + eventual agent-driven digest flow), not a test-infrastructure problem. The two are orthogonal; landing tests does not regress compression discipline, and waiting for compression discipline to land before tests would delay test infra by multiple waves for no gain.

**L4 — The catalog's T2–T5 items may be wrong.** This craft's catalog is the best synthesis I can produce from 4 Explore-agent deep reads + direct source probe, but 80% of it is unexecuted proposal. When Wave 26+ crafts re-examine each item, revisions are expected. The catalog is grout for future masonry, not final wall.

**L5 — `myco hunger` doctor-extension is under-specified.** The Round 1 revise said "extend hunger with check categories from hermes's doctor taxonomy" but did not specify which categories. That decision is deferred to the Wave that lands it — not Wave 25. Placeholder in the catalog.

### 4.4 Catalog — permanent engineering-pattern inventory (NOT a schedule)

**Organized by portable pattern, keyed to Myco scar class, with hermes file:line evidence.**

**C1 — Test infrastructure with autouse isolation fixture.** Hermes: `tests/conftest.py::_isolate_hermes_home` + pyproject `[tool.pytest.ini_options]` + SIGALRM 30s timeout (Unix). Myco mapping: `tests/conftest.py::_isolate_myco_project` redirects `--project-dir` to tmp. Scar class: W20 silent-fail, W23 pre-commit hook never exercised, W24 sensor disagreement. **Wave 25 — committed.**

**C2 — Atomic writes via temp+rename.** Hermes: `atomic_yaml_write` helper used in sessions.json, cron jobs, .env, process checkpoints, skill files (v0.2 release notes explicitly lists these 5 PRs). Myco mapping: `src/myco/io_utils.py::atomic_write_yaml` + refactor of `notes.py`, `upstream.py`, `forage.py` writers. Scar class: future (no Myco scar yet — this is preventive absorption against survivorship bias). **Catalog item, Wave TBD.**

**C3 — Error taxonomy with classified recovery hints.** Hermes: `agent/error_classifier.py::ClassifiedError` dataclass (reason, retryable, should_compress, should_rotate_credential). Myco mapping: `src/myco/errors.py::MycoError` + UserInputError/InvariantViolationError/SchemaError/IOError_/BugError hierarchy with exit-code mapping. Scar class: W20's `MycoProjectNotFound` is the first error subclass, not the last. **Catalog item, Wave TBD.**

**C4 — Structured logging with rotation + secret redaction.** Hermes: `hermes_logging.py::setup_logging()` idempotent + `RotatingFileHandler` + `RedactingFormatter`. Myco mapping: `src/myco/logging_setup.py` writing to `<project>/.myco_state/logs/` with per-module loggers. NOT replacing all 255 `print()` calls — only module-internal diagnostic paths. Scar class: W20 silent-fail audit-trail gap. **Catalog item, Wave TBD.**

**C5 — Single-source command registry.** Hermes: `hermes_cli/commands.py::COMMAND_REGISTRY` (frozen dataclass) → CLI dispatch + gateway + Telegram + Slack + autocomplete all derive. Myco mapping: `src/myco/commands.py::MycoVerbDef` → `cli.py` subparsers + `mcp_server.py` `@mcp.tool` decorators auto-derive from same registry. Scar class: confirmed duplication `cli.py`/`mcp_server.py` of 9 verbs. **Catalog item, downgraded to T2 after Round 1 attack.**

**C6 — `myco hunger` doctor-extension.** Hermes: `hermes_cli/doctor.py::run_doctor` with ~20 check categories + `--fix`. Myco reframe: extend existing `myco hunger` output with check categories (Python version, PyYAML, `_canon.yaml` schema, L0–L17 clean, forage manifest schema, boot brief freshness, contract drift vs kernel, git hook installed). `--fix` for auto-migrate stale schema + boot-brief refresh. Scar class: W20/W21/W24 "silent sensors are worse than crash" + "two sensors must agree". **Catalog item, Wave TBD.**

**C7 — Three-phase compression (hot-gate narrowing).** Hermes: `agent/context_compressor.py` three phases (prune / protect / summarize). Myco narrowed: add protect-hot gate only. Notes with `last_touched` within `hot_window_days` (default 7) are exempt from automatic excretion regardless of other signals. Scar class: `compression_discipline_maturity = 0.40` + Wave 22 W13 principle. **Catalog item, Wave TBD.**

**C8 — Profile-scoped state via env var set before imports.** Hermes: `main.py::_apply_profile_override()` at top of module, sets `os.environ["HERMES_HOME"]` before any hermes import. Myco mapping: `src/myco/_boot.py` reads `MYCO_PROJECT_DIR` env var, sets module-level cache. All `_project_root()` calls check cache first. Scar class: none yet (Myco is per-command, not per-process). **Catalog item, Wave TBD, low priority.**

**C9 — MCP as explicit bridge, not auto-derived.** Hermes: `mcp_serve.py::create_mcp_server()` defines `@mcp.tool` wrappers that delegate to internal handlers — NOT auto-gen from internal tool registry. Myco mapping: even after C5 command registry lands, `mcp_server.py` keeps hand-written `@mcp.tool` decorators that reference registry handlers. MCP schemas diverge from CLI when needed. Scar class: future-proofing against MCP API changes. **Catalog item, paired with C5.**

**C10 — Lint rule registry with `check_fn` lazy availability.** Hermes: `tools/registry.py::ToolRegistry` self-register + check_fn for lazy availability. Myco mapping: `src/myco/lint/registry.py::register_lint_rule(level="L18", severity="MEDIUM")` decorator. Existing L0–L17 migrate to registry. Future `.myco/lint_rules/*.py` drop-in extensions. Scar class: current lint dimensions are hardcoded in `lint.py::main()`; adding L18 requires editing the main function. **Catalog item, Wave TBD.**

**C11 — Release notes per contract-minor bump (scar archive).** Hermes: `RELEASE_v0.2.0.md` through `RELEASE_v0.8.0.md` — each enumerates Added / Fixed (with PR numbers) / Renamed / Breaking. Myco mapping: `docs/releases/RELEASE_v0.24.0.md` (Wave 25), one per wave going forward. Retroactive backfill of v0.10–v0.23 from `log.md` entries as time permits. Scar class: `log.md` milestone entries are readable but not grep-versioned, hampering future audit. **Catalog item, Wave TBD.**

**C12 — `docs/agent_protocol.md §9 Dangerous Pitfalls` expansion.** Hermes: `AGENTS.md` §Dangerous Pitfalls enumerates runtime-specific traps with scar origins. Myco mapping: add `§9 Dangerous Pitfalls` to `agent_protocol.md` listing substrate-specific traps: hardcoded `~/.myco_state/` instead of `_project_root()` walk, bypassing `myco eat` with `echo > notes/`, running `pytest -x` without `testpaths=["tests"]` scope (W23 scar), assuming boot brief exists without freshness check (W17 scar), two-sensor disagreement patterns (W24 scar). Scar class: implicit — turning scar records into hygiene warnings. **Catalog item, Wave TBD.**

**C13 — PII redaction via prefix regex library.** Hermes: `agent/redact.py::_PREFIX_PATTERNS` (40+ patterns for API keys, tokens, auth headers, db connection strings, private keys). Myco mapping: `src/myco/redact.py` applied to foraged content ingestion. If API key detected in a foraged file, quarantine in `forage/.quarantine/` instead of ingesting. Scar class: none yet; preventive. **Catalog item, Wave TBD, defensive tier.**

**C14 — Jittered retry seeded from time+counter.** Hermes: `agent/retry_utils.py::jittered_backoff`. Myco mapping: not obviously applicable (Myco is synchronous, no retry loops) — but the thread-local counter + `time_ns` seed pattern could be applied if Myco adds any `myco upstream scan` polling. **Catalog item, deferred.**

**C15 — Pinned deps with lock file + supply-chain audit workflow.** Hermes: pyproject pins all ranges, uv.lock with hashes, CI workflow scans PRs for supply chain patterns. Myco mapping: when `[project.optional-dependencies.dev]` adds pytest in Wave 25, also add `requirements-dev.lock` (or uv.lock equivalent). Longer term: pip-audit in `myco hunger` checks. Scar class: future; preventive. **Catalog item, paired with C6.**

**C16 — Learning loop as interval pattern.** Hermes: `run_agent.py::_turns_since_memory` counter + `_spawn_background_review()` every N turns. Myco mapping: NOT the runtime shape (Myco has no agent loop), but the INTERVAL pattern. Apply to wave-retrospective discipline: every N waves, require a retrospective craft that summarizes the scar class from that window. **T5 strategic — informs discipline, not directly coded.**

**C17 — BasePlatformAdapter ABC pattern.** Hermes: `gateway/platforms/base.py::BasePlatformAdapter` ABC with ~150-line platform-specific overrides over 600+ shared lines. Myco: NOT portable to substrate (no gateway layer). Strategic pattern lesson: when Myco eventually has multiple "source adapters" (arxiv fetcher, GitHub repo cloner, RSS subscriber for forage), use an ABC with shared helpers, not separate modules. **Catalog item, deferred, Wave N+∞.**

**C18 — Schema migration with version counter.** Hermes: `hermes_state.py` SCHEMA_VERSION + ALTER TABLE migrations each try/except-wrapped. Myco mapping: Myco already has `system.contract_version` in `_canon.yaml`. The absorption is: when a contract bump changes a schema field, the template rebase-able instances should `myco migrate` to pick up the new schema without manual edits. Wave 23 `MYCO-PRECOMMIT-PYTEST-MARK` idempotent refresh is Myco's version of this. **Catalog item, consolidation of existing practice.**

**C19 — Test timeout enforcement via SIGALRM.** Hermes: 30s per-test SIGALRM (Unix only) prevents hanging subprocess spawns from stalling entire suite. Myco mapping: pytest-timeout plugin (portable across Win/Unix) instead of SIGALRM. Add to Wave 25 pyproject dev deps. **Catalog item, paired with C1.**

**C20 — Dogfood discipline for untested blocking paths.** Hermes: v0.7 explicitly adds "compression death spiral detection" (#4750/#2153) after production incident. Myco: W23 dogfood of pre-commit hook blocking path after 5 waves of non-use. Lesson: every new blocking path must have a dogfood test in the same wave. **Catalog item; already absorbed in W23.**

## 5. Provenance

- **Raw-note evidence bundle**: `notes/n_20260412T013044_5546.md` (integrated into this craft via `myco eat` 2026-04-12T01:30)
- **Supersession pointer to prior digest**: `notes/n_20260411T183722_c1b2.md` (Wave 9 surface-level forage, honest-edges-declared as source-code-unread)
- **Forage manifest entry**: `forage/_index.yaml::f_20260411T180416_3654` (license: MIT)
- **Cross-project convergence pointers**: gbrain (`n_20260411T183403_a984`), nuwa-skill (`n_20260411T183115_f5c5`), karpathy LLM Wiki (`n_20260411T185410_2e13`)
- **Craft protocol version**: 1 (as defined in `docs/craft_protocol.md` + `_canon.yaml::system.craft_protocol`)
- **Decision class**: kernel_contract (floor 0.90)
- **Current confidence**: 0.90 (target met after 3 rounds)
- **Trigger surfaces touched by this landing**: will touch `pyproject.toml`, `_canon.yaml`, `src/myco/templates/_canon.yaml`, `src/myco/lint.py`, `scripts/install_git_hooks.sh` in Wave 25. This craft pre-authorizes those touches.
